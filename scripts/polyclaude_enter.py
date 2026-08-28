#!/usr/bin/env python3
"""Unified entry helper — catalyst_check + Kelly sizing + execute.

Wraps the multi-step workflow used for every Polymarket entry into one command:
1. Fetch market via gamma-api → check umaResolutionStatus (skip if disputed/proposed)
2. Run catalyst_check.py to get P(YES) estimate (with multiplicative breakdown
   for conjunction questions per philosophy 00 update)
3. Compute Kelly+ρ optimal size via per-position math (default half-Kelly,
   ρ=0.6 if cluster specified, ρ=0 if independent)
4. Print decision: SIZE / DON'T_TAKE / NEED_REVIEW with reasoning
5. With --execute flag: post buy via clob_v2.py

Output is logged to notes/entries_log.md (gitignored — local-only).

Operator directive 2026-05-09: aggressive engineering to capture untapped alpha.
This compounds across every future entry decision.

Usage:
    # Discovery: dry-run with reasoning
    python scripts/polyclaude_enter.py "Will US confirm aliens by 2027?" 2026-12-31

    # Quick mode: skip catalyst_check (use --my-p directly)
    python scripts/polyclaude_enter.py --my-p 0.95 --side NO 0.874 \\
        --resolve-date 2026-05-15 --slug us-x-iran-permanent-peace-deal-by-may-15-2026 \\
        "US x Iran permanent peace deal by May 15"

    # Execute: --execute --usd <amount>
    python scripts/polyclaude_enter.py --my-p 0.95 --side NO 0.874 ... --execute
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

import httpx

from book_walk import effective_entry_cost, maker_rest_price

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = REPO_ROOT / "notes" / "entries_log.md"


def fetch_market_by_slug_or_question(slug_or_q: str) -> dict | None:
    """Try slug lookup first; if fails, search by question."""
    with httpx.Client(timeout=15) as c:
        # Slug lookup
        if "-" in slug_or_q or "_" in slug_or_q:
            r = c.get("https://gamma-api.polymarket.com/markets", params={"slug": slug_or_q})
            if r.status_code == 200:
                d = r.json()
                if isinstance(d, list) and d:
                    return d[0]
        # Question search via paginate (gamma-api ?q is broken; client-side filter).
        # gamma caps pages at 100 regardless of limit, so paginate by 100 with an
        # early exit — the old limit=500 + offset=page*500 stride skipped 80% of
        # markets, so a question-based lookup could silently miss the target market.
        offset = 0
        while offset < 6000:
            r = c.get("https://gamma-api.polymarket.com/markets", params={
                "closed": "false", "active": "true",
                "limit": 100, "offset": offset,
                "order": "volume24hr", "ascending": "false",
            })
            if r.status_code != 200:
                break
            batch = r.json() or []
            if not batch:
                break
            for m in batch:
                q = m.get("question", "")
                if slug_or_q.lower() == q.lower() or slug_or_q.lower() in q.lower():
                    return m
            offset += len(batch)
    return None


def _existing_exposure(condition_id: str | None, question: str) -> dict | None:
    """Live data-api check: do we already hold this market? (DEC-0029 lesson:
    2026-06-01 bought a market already held, found out after.) Returns the
    matching position dict or None; never raises (warn-path only)."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from polyclaude_client import Wallet
        addr = Wallet.load().address
        r = httpx.get("https://data-api.polymarket.com/positions",
                      params={"user": addr.lower(), "limit": "100"}, timeout=15)
        r.raise_for_status()
        for pos in r.json():
            if condition_id and pos.get("conditionId") == condition_id:
                return pos
            if pos.get("title") and pos["title"].strip().lower() == question.strip().lower():
                return pos
    except Exception as e:
        print(f"# existing-exposure check unavailable ({e}) — verify manually", file=sys.stderr)
    return None


def _best_ask(token_id: str, timeout: float = 12.0) -> float | None:
    """Lowest ask for a CLOB token = the price we'd actually PAY to buy it.
    Hits the CLOB book API directly (gamma midpoints are unreliable — they sit
    between stub bids and real asks). Returns None if the book is empty/unreachable
    so the caller can fall back to the gamma mark."""
    import httpx
    try:
        with httpx.Client(timeout=timeout) as c:
            r = c.get("https://clob.polymarket.com/book", params={"token_id": str(token_id)})
            r.raise_for_status()
            asks = r.json().get("asks") or []
            prices = [float(a["price"]) for a in asks if a.get("price")]
            return min(prices) if prices else None
    except Exception:
        return None



_SIB_STOP = {"will", "the", "a", "an", "in", "by", "of", "to", "be", "before",
             "on", "at", "for", "and", "or", "is", "does", "do", "any", "part",
             # date tokens: dates are exactly what differs between TRUE duplicates
             # ("by end of 2026" ≡ "before 2027"), so they must not depress similarity
             "end", "january", "february", "march", "april", "may", "june", "july",
             "august", "september", "october", "november", "december"}


def _sib_tokens(text: str) -> set:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in _SIB_STOP}


_SIB_MONTHS = ("january", "february", "march", "april", "may", "june", "july",
               "august", "september", "october", "november", "december")


def _sib_datesig(text: str) -> tuple:
    """Date signature of a question: years, month names, day numbers. Equal
    signatures → candidate TRUE duplicate; different → term-structure sibling
    (different deadline = different bet, but the term structure is informative).
    Normalization: "before YYYY" ≡ deadline Dec-31 of YYYY-1 (so "before 2027"
    matches "by end of 2026" / "in 2026" — the canonical true-dup phrasing pair)."""
    t = text.lower()
    t = re.sub(r"before (20\d\d)", lambda m2: str(int(m2.group(1)) - 1), t)
    return tuple(sorted(re.findall(r"20\d\d|\b\d{1,2}\b|" + "|".join(_SIB_MONTHS), t)))


def _sibling_markets(question: str, market_id, side: str) -> None:
    """Same-proposition sibling advisory (2026-07-15 implication study salvage).
    True duplicate markets across events ("by end of 2026" ≡ "before 2027") run
    1-2pp apart on liquid legs — routing to the cheaper book is worth more per
    trade than the whole cross-event arb class (which is dead: 0 executable
    violations in 4,575 pairs). CAUTION printed with every hit: same question
    text ≠ same proposition (event editions carry different leader lists / IPO
    definitions) — read BOTH descriptions before treating books as fungible.
    Warn-path only; never raises, never blocks. NOTE: search with content
    tokens, not the raw question — gamma search is too literal, the sibling's
    different date phrasing would exclude it."""
    try:
        toks_q = _sib_tokens(question)
        if not toks_q:
            return
        # deterministic query in question order (set order varies per process)
        seen = set()
        ordered = [w for w in re.findall(r"[a-z]+", question.lower())
                   if w in toks_q and not (w in seen or seen.add(w))]
        query = " ".join(ordered[:8])
        r = httpx.get("https://gamma-api.polymarket.com/public-search",
                      params={"q": query}, timeout=15)
        r.raise_for_status()
        hits = []
        for ev in (r.json().get("events") or [])[:10]:
            for m in ev.get("markets") or []:
                if str(m.get("id")) == str(market_id) or m.get("closed"):
                    continue
                toks2 = _sib_tokens(m.get("question") or "")
                if not toks2:
                    continue
                jac = len(toks_q & toks2) / len(toks_q | toks2)
                if jac >= 0.7:
                    try:
                        yes_p, no_p = [float(x) for x in json.loads(m.get("outcomePrices") or "[]")][:2]
                    except Exception:
                        yes_p = no_p = None
                    px = no_p if side == "NO" else yes_p
                    same_date = _sib_datesig(m.get("question") or "") == _sib_datesig(question)
                    hits.append((same_date, jac, m.get("id"), m.get("slug"), px, m.get("takerBaseFee")))
        if hits:
            print(f"\n!! SIBLING MARKET(S) FOUND (content-similarity >=0.7):")
            for same_date, jac, mid, mslug, px, fee in sorted(hits, reverse=True)[:4]:
                kind = ("CANDIDATE TRUE DUP (same deadline)" if same_date
                        else "different deadline — term-structure sibling, NOT fungible")
                print(f"!!   id={mid} {mslug} — {side} mid={px} taker_fee={fee or 0}bps | {kind}")
            print(f"!!   TRUE-DUP + cheaper book on {side} → verify criteria truly identical "
                  f"(descriptions/editions/definitions — implication-study trap), then route there.")
    except Exception:
        pass


def _bankroll_default() -> float:
    """Live bankroll from bankroll.py's cache when fresh (<24h); else 170 + warn."""
    import datetime as _dt
    try:
        cache = Path(__file__).resolve().parent.parent / "notes" / ".bankroll_cache.json"
        d = json.loads(cache.read_text())
        age_h = (_dt.datetime.now(_dt.timezone.utc)
                 - _dt.datetime.fromisoformat(d["at"])).total_seconds() / 3600
        if age_h < 24:
            print(f"# bankroll ${d['total']:.2f} from cache (age {age_h:.1f}h)", file=sys.stderr)
            return float(d["total"])
        print(f"# WARNING: bankroll cache stale ({age_h:.0f}h) — run scripts/bankroll.py; using $170 fallback", file=sys.stderr)
    except Exception:
        print("# WARNING: no bankroll cache — run scripts/bankroll.py; using $170 fallback", file=sys.stderr)
    return 170.0


def kelly_size(mark: float, p_win: float, bankroll: float, frac: float,
               rho: float, cluster_frac: float) -> tuple[float, dict]:
    """Compute Kelly-optimal $ size with details."""
    if mark >= 0.999 or p_win <= mark:
        return 0.0, {"full_kelly": 0.0, "reason": "no edge (p_win <= mark)"}
    full_k = (p_win - mark) / (1.0 - mark)
    rho_disc = max(0.0, 1.0 - rho * cluster_frac)
    kelly_dollar = full_k * rho_disc * frac * bankroll
    return kelly_dollar, {
        "full_kelly": full_k,
        "rho_disc": rho_disc,
        "frac": frac,
        "bankroll": bankroll,
        "kelly_dollar": kelly_dollar,
        "edge_pp": (p_win - mark) * 100,
    }


def robust_p(my_p: float, edge_haircut: float, tail_mult: float | None = None) -> float:
    """Pessimistic bound of my p for the robust-edge gate.

    FLAT (default): my_p - edge_haircut. Correct for instance/catalyst theses,
    where measured overconfidence is an absolute 6-23pp (see --edge-haircut).

    TAIL-MULTIPLICATIVE (bond fades, --tail-mult): 1 - K*(1 - my_p) — "the true
    tail could be K times my measured tail". A flat haircut structurally kills
    EVERY bond fade regardless of fact quality (0.10 turns p_no 0.99 into 0.89
    against a 0.95-0.99 cost), because estimation error on a 1-2pp tail is
    proportional to the tail, not an absolute 10pp. DEC-0077 (Hormuz) entered on
    exactly this: measured p_yes 0.002, K=5 -> p_no_robust 0.99 > cost 0.986,
    while the same gate rejected the Sep-30 sibling at -5pp — encoding, before
    it was articulated, that longer horizons load on regime-change probability
    (2026-08-19 lesson). Flat-equivalent haircut = (K-1)*(1-my_p), which is why
    DEC-0077's hand-computed --edge-haircut 0.01 was the same number.
    """
    if tail_mult is not None:
        return 1.0 - tail_mult * (1.0 - my_p)
    return my_p - edge_haircut


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("question", nargs="?", default=None,
                   help="Polymarket question or slug (or omit if --slug provided)")
    p.add_argument("--slug", default=None, help="Explicit slug (alternative to question lookup)")
    p.add_argument("--my-p", type=float, default=None,
                   help="My P(side wins) estimate. If omitted, will run catalyst_check.")
    p.add_argument("--side", choices=["YES", "NO"], default="NO",
                   help="Which side to buy (default NO for bond-like fades)")
    p.add_argument("--resolve-date", default=None,
                   help="Resolution date (YYYY-MM-DD). Required for catalyst_check.")
    p.add_argument("--bankroll", type=float, default=None,
                   help="default: live total from bankroll.py cache (<24h), else 170")
    p.add_argument("--kelly-frac", type=float, default=0.5)
    p.add_argument("--rho", type=float, default=0.0,
                   help="Correlation to existing cluster (0=independent, 0.7=high)")
    p.add_argument("--cluster-frac", type=float, default=0.0,
                   help="Existing cluster fraction of bankroll (for ρ-discount)")
    p.add_argument("--execute", action="store_true", help="Actually post buy order")
    p.add_argument("--maker", action="store_true",
                   help="Rest a GTC post-only bid at best_bid+tick instead of crossing: "
                        "no taker fee, bid-side price, fill NOT guaranteed. Record in "
                        "notes/resting_orders.md and re-verify each tick. NOT for "
                        "catalyst-imminent entries — cross the spread for those.")
    p.add_argument("--usd", type=float, default=None,
                   help="Override Kelly recommendation with manual $ size")
    p.add_argument("--skip-catalyst-check", action="store_true",
                   help="Skip catalyst_check (use only --my-p)")
    p.add_argument("--edge-haircut", type=float, default=0.10,
                   help="Pessimistic shift applied to p for the robust-edge gate. "
                        "DEFAULT RAISED 0.05 -> 0.10 on 2026-08-13 on measured evidence: every "
                        "INSTANCE/catalyst prior I have set drifted DOWN on later re-derivation "
                        "(MacBook 0.85->0.62, GPT-6 0.96->0.90, MacBook-add 0.70->0.62, "
                        "OpenAI-HLE 0.66->0.50 and 0.79->0.64), i.e. 6-23pp of overconfidence, "
                        "N=5 and all one direction — so a 5pp haircut was systematically "
                        "under-correcting. Meanwhile TAIL/MONITORING priors drifted the other way "
                        "(Greenland 0.95->0.98, Trump-out 0.96->0.97), so the old advice to shrink "
                        "the haircut for 'mechanical' markets was backwards: those are where I am "
                        "too PESSIMISTIC. Use 0.05 for tail/monitoring fades; keep 0.10+ for any "
                        "instance or catalyst thesis, where my first number is reliably too brave. "
                        "For BOND FADES (my_p >= 0.90) use --tail-mult instead — a flat haircut "
                        "kills every bond fade regardless of fact quality.")
    p.add_argument("--tail-mult", type=float, default=None, nargs="?", const=5.0,
                   help="Bond-fade pessimism: p_robust = 1 - K*(1-my_p), i.e. 'the true tail "
                        "could be K times my measured tail'. Bare flag = K=5 (the DEC-0077 "
                        "doctrine value; formalized 2026-08-21 from the fresh-session queue). "
                        "Replaces --edge-haircut for the gate; only accepted when my_p >= 0.90 "
                        "— below that, tail-scaling is the wrong error model (use the flat "
                        "haircut) and K=5 would be absurdly harsh anyway. Requires the tail to "
                        "be MEASURED (PortWatch-style first-hand read), not vibes: K multiplies "
                        "whatever error your measurement already carries.")
    args = p.parse_args()
    if args.bankroll is None:
        args.bankroll = _bankroll_default()

    # Resolve market
    lookup = args.slug or args.question
    if not lookup:
        print("ERROR: provide question or --slug", file=sys.stderr)
        return 2

    print(f"# polyclaude_enter: looking up '{lookup[:50]}'...", file=sys.stderr)
    m = fetch_market_by_slug_or_question(lookup)
    if not m:
        print(f"ERROR: market not found", file=sys.stderr)
        return 2

    question = m.get("question", "?")
    slug = m.get("slug", "?")
    market_id = m.get("id", "?")
    uma_status = m.get("umaResolutionStatus")
    end_iso = m.get("endDate") or m.get("endDateIso") or ""
    try:
        prices_raw = m.get("outcomePrices")
        prices = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
        yes_p, no_p = float(prices[0]), float(prices[1])
    except Exception:
        yes_p, no_p = None, None
    clob_token_ids = m.get("clobTokenIds")
    if isinstance(clob_token_ids, str):
        try:
            clob_token_ids = json.loads(clob_token_ids)
        except Exception:
            clob_token_ids = None
    yes_token = clob_token_ids[0] if clob_token_ids else None
    no_token = clob_token_ids[1] if clob_token_ids else None
    neg_risk = bool(m.get("negRisk"))
    try:
        tick = float(m.get("orderPriceMinTickSize") or 0.01)
    except Exception:
        tick = 0.01
    if tick <= 0:
        tick = 0.01

    print(f"\nMarket: {question}")
    print(f"  slug: {slug}")
    print(f"  market_id: {market_id}")
    print(f"  umaResolutionStatus: {uma_status}")
    print(f"  outcomePrices: YES={yes_p} NO={no_p}")
    print(f"  endDate: {end_iso}")
    print(f"  negRisk: {neg_risk}")

    # Permanence-near-date trap warning (00_philosophy §4.4; warn, not block).
    # A NO fade on (permanence/finality qualifier) × (near-date deadline) × (active
    # dealmaking) is a UMA-LOOSE trap: an announcement triggers loose-YES faster than
    # a strict failure confirms. Lost twice — R-U (-$16.73), DEC-0038 (-$11.31). The
    # first two conditions are mechanically detectable; the 3rd (active dealmaking) is
    # the human's to check. Fires only on NO-side near-dated permanence markets.
    _days = None
    try:
        if end_iso:
            _end = datetime.datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
            _days = (_end - datetime.datetime.now(datetime.timezone.utc)).days
        elif args.resolve_date:
            _days = (datetime.date.fromisoformat(args.resolve_date) - datetime.date.today()).days
    except Exception:
        _days = None
    _perm_kw = ("permanent", "officially", "definitive", "definitively",
                "sign", "signed", "ratif", "treaty", "ceasefire")
    _ql = question.lower()
    if (args.side == "NO" and _days is not None and _days <= 45
            and any(k in _ql for k in _perm_kw)):
        print(f"\n!! PERMANENCE-NEAR-DATE TRAP PATTERN (00_philosophy §4.4): NO fade on a "
              f"permanence/finality market resolving in {_days}d.")
        print(f"!! An ANNOUNCEMENT can trigger loose-YES before a strict failure confirms. "
              f"Lost here twice (R-U -$16.73, DEC-0038 -$11.31).")
        print(f"!! If real-world dealmaking toward the event is ACTIVE → weight loose >=0.5 "
              f"(p_no <= ~0.85, edge-haircut >= 0.10) or SKIP. A thin strict-edge will not survive it.")

    # Reject if disputed
    if uma_status in ("proposed", "disputed"):
        print(f"\nDECISION: SKIP — umaResolutionStatus={uma_status}")
        print(f"  Market is in active UMA dispute. Cannot reliably enter.")
        return 0

    # Existing-exposure guard (warn, not block — deliberate adds are fine, the
    # failure mode is UNKNOWING adds). Sums what a fill would take the ticket to.
    held = _existing_exposure(m.get("conditionId"), question)
    if held:
        held_cost = held.get("initialValue", 0.0)
        held_side = held.get("outcome", "?")
        print(f"\n!! EXISTING POSITION in this market: {held_side} "
              f"cost ${held_cost:.2f} (mark {held.get('curPrice', '?')}, "
              f"mtm ${held.get('currentValue', 0.0):.2f})")
        if args.usd:
            combined = held_cost + args.usd
            print(f"!! combined ticket after this buy: ${combined:.2f} "
                  f"= {combined / args.bankroll * 100:.1f}% of bankroll "
                  f"(15% hard cap = ${args.bankroll * 0.15:.2f}, 00_philosophy §5 model-error guardrails)")
        print(f"!! this is an ADD — confirm cluster caps + run the sizing as a "
              f"size_change decision, not a fresh entry.")

    # Same-proposition sibling routing advisory (implication study 2026-07-15)
    _sibling_markets(question, market_id, args.side)

    if yes_p is None:
        print(f"\nDECISION: NEED_REVIEW — could not parse outcomePrices")
        return 2

    side = args.side
    gamma_mark = no_p if side == "NO" else yes_p
    token = no_token if side == "NO" else yes_token
    if gamma_mark is None or token is None:
        print(f"DECISION: NEED_REVIEW — no token id for {side}")
        return 2

    # Walk the LIVE CLOB ask — do NOT trust the gamma midpoint for the gate.
    # Per the polymarket-midpoints-unreliable lesson, gamma outcomePrices sit
    # between stub bids and real asks; the robust-edge gate must evaluate EV at
    # the price we'd actually PAY (the ask), or it passes phantom edge that
    # evaporates on fill. This matters more now that the discovery funnel
    # (10x fix, 2026-05-29) surfaces thin-liquidity tail markets where the
    # mid↔ask gap is large. Falls back to the gamma mark if the book is empty.
    real_ask = _best_ask(token)
    if real_ask is not None:
        mark = real_ask
        if abs(real_ask - gamma_mark) >= 0.01:
            print(f"  [mark] gamma-mid {gamma_mark:.4f} → live ask {real_ask:.4f} "
                  f"({(real_ask-gamma_mark)*100:+.1f}pp) — using live ask for the gate")
    else:
        mark = gamma_mark
        print(f"  [mark] live ask unavailable; falling back to gamma mid {gamma_mark:.4f}")

    # Taker-fee awareness (2026-07-15 new-listing study, curve corrected
    # 2026-08-22): fee per share = rate × p × (1−p). book_walk delegates to
    # pm_fees.py, which caps the raw takerBaseFee rate at the current 0.07 while
    # preserving lower-rate and fee-free markets. All economic math (Kelly,
    # robust gate, profit) runs on the
    # EFFECTIVE per-share cost; only the CLOB limit price stays at the real ask
    # (the exchange charges the fee on top).
    try:
        taker_bps = int(float(m.get("takerBaseFee") or 0))
    except Exception:
        taker_bps = 0
    maker_px = None
    if args.maker:
        # Gate on the price actually being POSTED (2026-08-18 gap): --maker used
        # to change only the execution price, so the robust gate judged maker
        # entries on ask + taker fee — economics a post-only order never pays —
        # and spuriously SKIPped MacBook at effective 0.55 when the rest at 0.45
        # cleared by +10pp. Fetch the book ONCE here so the gated price and the
        # posted price cannot diverge within the run.
        try:
            bk = httpx.get("https://clob.polymarket.com/book",
                           params={"token_id": token}, timeout=15).json()
            maker_bb = max((float(x["price"]) for x in bk.get("bids", [])), default=None)
            maker_ba = min((float(x["price"]) for x in bk.get("asks", [])), default=None)
        except Exception as e:
            print(f"  book fetch failed ({e}) — maker entry aborted")
            return 1
        if maker_bb is None:
            print("  empty bid side — maker entry aborted (use the taker path)")
            return 1
        maker_px = maker_rest_price(maker_bb, maker_ba, tick)
    cost_eff, fee_per_share = effective_entry_cost(mark, taker_bps, maker_px)
    if maker_px is not None:
        print(f"  [maker] gate + sizing run on the POSTED rest price {maker_px:.2f} "
              f"(bid {maker_bb:.3f} / ask {maker_ba if maker_ba is not None else '—'}), maker fee $0 "
              f"— not on ask+taker cost. Fill is not guaranteed; resting-order rules govern.")
    elif fee_per_share:
        print(f"  [fee] takerBaseFee={taker_bps}bps → {fee_per_share*100:.2f}c/share taker fee; "
              f"effective cost {cost_eff:.4f} (ask {mark:.4f}) — gate + sizing run on effective cost")

    # Resolve P(side wins)
    my_p = args.my_p
    if my_p is None and not args.skip_catalyst_check:
        if not args.resolve_date:
            print(f"\nDECISION: NEED_REVIEW — provide --my-p or --resolve-date for catalyst_check")
            return 2
        print(f"\n# Running catalyst_check.py for P estimate...", file=sys.stderr)
        try:
            cc_cmd = [".venv/bin/python", "scripts/catalyst_check.py", question, args.resolve_date,
                      "--no-log"]
            # Window-start guard (2026-07-18 Beirut miss): for "by DATE" markets
            # created mid-stream, pre-creation events must not count toward YES.
            if m.get("createdAt"):
                cc_cmd += ["--window-start", str(m["createdAt"])[:19]]
            r = subprocess.run(
                cc_cmd,
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=600,
            )
            cc_out = r.stdout
            print(cc_out)
            # Extract central P(YES) from "Central: X%" line
            m_central = re.search(r"Central:\s*(\d+(?:\.\d+)?)%", cc_out)
            if m_central:
                p_yes = float(m_central.group(1)) / 100
                my_p = (1 - p_yes) if side == "NO" else p_yes
                print(f"\n# catalyst_check central P(YES)={p_yes:.4f} → P({side} win)={my_p:.4f}", file=sys.stderr)
            else:
                print(f"\nDECISION: NEED_REVIEW — couldn't parse central P from catalyst_check")
                return 2
        except subprocess.TimeoutExpired:
            print(f"DECISION: NEED_REVIEW — catalyst_check timed out")
            return 3

    if my_p is None:
        print(f"DECISION: NEED_REVIEW — no P estimate provided")
        return 2

    # Kelly sizing (on effective cost — fee-adjusted when the market charges one)
    kelly_dollar, details = kelly_size(cost_eff, my_p, args.bankroll, args.kelly_frac,
                                        args.rho, args.cluster_frac)

    deploy_dollar = args.usd if args.usd is not None else kelly_dollar
    if deploy_dollar < 1.0:
        print(f"\nDECISION: SKIP — Kelly size ${deploy_dollar:.2f} < $1 (no edge or marginal)")
        return 0

    shares = deploy_dollar / cost_eff
    profit_if_win = shares * (1.0 - cost_eff)

    # Robust-edge gate (2026-05-29: replaces the retired flat 10pp edge bar).
    # The edge bar was relaxed to "positive EV after op-cost" — but EV computed
    # on the CENTRAL p estimate is fragile: my p is itself uncertain, and Kelly
    # punishes overbetting a believed-but-wrong edge. So gate on the PESSIMISTIC
    # bound of the estimate, not the point estimate. This self-scales: a
    # confident mechanical-market estimate (small --edge-haircut) clears thin
    # edges; a fuzzy estimate (large haircut) demands a fat edge. Reproduces a
    # margin-of-safety proportional to estimation uncertainty rather than a flat
    # phantom floor. op_cost ≈ haiku catalyst_check (~$0.02) + gas + slippage.
    OP_COST = 0.05
    if args.tail_mult is not None and my_p < 0.90:
        print(f"\nDECISION: NEED_REVIEW — --tail-mult is for bond fades (my_p >= 0.90); "
              f"my_p={my_p:.4f}. Use --edge-haircut for instance/catalyst theses.")
        return 2
    p_robust = robust_p(my_p, args.edge_haircut, args.tail_mult)
    if args.tail_mult is not None:
        print(f"  [tail-mult] pessimistic bound = 1 - {args.tail_mult:g}x tail: "
              f"p_robust {p_robust:.4f} (flat-equivalent haircut "
              f"{(args.tail_mult - 1) * (1 - my_p):.4f})")
    ev_robust = shares * (p_robust - cost_eff)  # EV at pessimistic p, fee-adjusted cost
    ev_central = shares * (my_p - cost_eff)
    if p_robust <= cost_eff or ev_robust <= OP_COST:
        print(f"\nDECISION: SKIP — edge not robust to estimation error.")
        _hc_desc = (f"tail-mult {args.tail_mult:g}x" if args.tail_mult is not None
                    else f"haircut {args.edge_haircut:.2f}")
        print(f"  central p={my_p:.4f} → EV ${ev_central:+.2f}; "
              f"pessimistic p={p_robust:.4f} ({_hc_desc}) → EV ${ev_robust:+.2f}")
        print(f"  Need EV > ${OP_COST:.2f} at the pessimistic bound. "
              f"Thin point-estimate edge dominated by estimation noise.")
        print(f"  Override with a smaller --edge-haircut only if the p estimate is "
              f"genuinely high-confidence (mechanical resolution, tight catalyst_check band).")

        # FLIP-THE-KILL CHECK (2026-08-13). The rule has been doctrine since
        # 2026-07-17 (00_philosophy §3) and was NEVER mechanised — and grading
        # the skip ledger today measured what that costs: 2 of 9 graded rows are
        # flip misses. On DC Studios and Lucasfilm I evaluated NO at 0.80,
        # correctly skipped it, and never ran the gate on YES at 0.59, which won
        # (+69% each). The ledger even scores those skips as CORRECT, because it
        # grades the side I looked at — so the failure is invisible in my own
        # records. A skip means "not this side", never "not this market".
        try:
            # market dict is `m` in this scope, not `market` — first version used
            # the latter and the try/except swallowed the NameError as "flip
            # check unavailable", i.e. the mechanisation for a rule I built
            # BECAUSE it silently fails would itself have silently failed.
            _toks = json.loads(m.get("clobTokenIds") or "[]")
            _outs = json.loads(m.get("outcomes") or "[]")
            _other = "No" if side == "Yes" else "Yes"
            if _other in _outs and len(_toks) == len(_outs):
                _oask = _best_ask(_toks[_outs.index(_other)])
                if _oask:
                    _op = 1.0 - my_p
                    _ocost, _ofee = effective_entry_cost(_oask, taker_bps)
                    _oedge = (_op - _ocost) * 100
                    print(f"\n  FLIP-THE-KILL CHECK — a skip rejects THIS SIDE, not this market:")
                    print(f"    opposite side {_other} asks {_oask:.4f} (eff {_ocost:.4f}); "
                          f"your p implies P({_other})={_op:.3f} → edge {_oedge:+.1f}pp")
                    if _op - args.edge_haircut > _ocost:
                        print(f"    >> THE FLIP CLEARS THE GATE at haircut {args.edge_haircut:.2f}. "
                              f"Re-run with --side {_other} before walking away.")
                    else:
                        print(f"    (flip does not clear either — this market is genuinely skippable)")
        except Exception as _e:
            print(f"  (flip check unavailable: {str(_e)[:50]})")
        return 0

    # EXIT LIQUIDITY (2026-08-13). Entry has always priced what I PAY and never
    # what it would cost to LEAVE. Measuring the book that day found 22% of
    # holdings sit where <50% could be sold within 5% of mark — MacBook at a
    # 20pp spread with ZERO bid depth inside 5% — which quietly makes its
    # written thesis-break rule unactionable. Entry is the only moment that
    # information can change anything, so surface it here. NOT a block:
    # capacity is explicitly not a filter in this project, and thin markets are
    # where mispricings persist longest. Just never enter blind to the exit.
    try:
        _bk = httpx.get("https://clob.polymarket.com/book",
                        params={"token_id": token}, timeout=15).json()
        _bids = sorted(_bk.get("bids", []), key=lambda x: -float(x["price"]))
        _asks = sorted(_bk.get("asks", []), key=lambda x: float(x["price"]))
        if _bids and _asks:
            _bb, _ba = float(_bids[0]["price"]), float(_asks[0]["price"])
            # Measure depth against the MID, not against cost_eff. First version
            # used cost_eff — which includes the taker fee and therefore sits
            # ABOVE the ask, so no bid could ever clear it and a 1pp-spread book
            # reported 0% exitable. Caught only by testing on a market I already
            # knew was liquid; the same assert-against-a-known-truth habit that
            # caught the empty-list parse. A plausible formula returning a
            # confident wrong number is the recurring shape here.
            _mid = (_bb + _ba) / 2
            _floor = _mid * 0.95
            _depth = sum(float(x["size"]) for x in _bids if float(x["price"]) >= _floor)
            _cover = min(100.0, _depth / shares * 100) if shares else 0.0
            print(f"\n=== EXIT LIQUIDITY (what leaving would cost) ===")
            print(f"  best bid {_bb:.3f} / ask {_ba:.3f} — spread {(_ba-_bb)*100:.1f}pp")
            print(f"  {_depth:.0f} shares bid within 5% of your entry = {_cover:.0f}% of this position")
            if _cover < 50:
                print(f"  !! THIN EXIT: a thesis-break rule on this leg is aspirational, not actionable.")
                print(f"     Size it as hold-to-resolution — entry size is the only loss control you get.")
    except Exception as _e:
        print(f"\n(exit-liquidity check unavailable: {str(_e)[:50]})")

    print(f"\n=== KELLY ANALYSIS ===")
    print(f"  Buying {side} @ ${mark:.4f}"
          + (f" (effective {cost_eff:.4f} incl. taker fee)" if fee_per_share else "")
          + f", P({side} wins) = {my_p:.4f}")
    print(f"  Edge: {details['edge_pp']:+.2f}pp")
    print(f"  Full Kelly: {details['full_kelly']*100:.1f}% of bankroll")
    print(f"  ρ-discount: {details['rho_disc']:.4f} (ρ={args.rho}, cluster_frac={args.cluster_frac})")
    print(f"  × Kelly fraction: {args.kelly_frac}")
    print(f"  Kelly $: ${kelly_dollar:.2f}")
    if args.usd is not None:
        print(f"  Manual override: ${args.usd:.2f}")
    print(f"  → Deploy: ${deploy_dollar:.2f} ({shares:.2f} shares)")
    print(f"  Profit if win: +${profit_if_win:.2f} (= {profit_if_win/deploy_dollar*100:.1f}%)")

    # Sensitivity: ±5% misestimate of p
    print(f"\n  Sensitivity (full-Kelly under p ±0.05):")
    for delta_p in (-0.10, -0.05, +0.05):
        p_alt = max(0.001, min(0.999, my_p + delta_p))
        if p_alt > cost_eff:
            full_alt = (p_alt - cost_eff) / (1.0 - cost_eff)
            size_alt = full_alt * details['rho_disc'] * args.kelly_frac * args.bankroll
            print(f"    p={p_alt:.4f} ({delta_p:+.2f}): full_K={full_alt*100:.1f}% → ${size_alt:.2f}")
        else:
            print(f"    p={p_alt:.4f} ({delta_p:+.2f}): NO EDGE → $0")

    if not args.execute:
        if maker_px is not None:
            print(f"\nDECISION: WOULD_REST ${deploy_dollar:.2f} of {side} @ {maker_px:.2f} "
                  f"post-only (ask {mark:.4f}; fill not guaranteed)")
        else:
            print(f"\nDECISION: WOULD_BUY ${deploy_dollar:.2f} of {side} @ {mark:.4f}")
        print(f"  Re-run with --execute to actually post the order.")
        return 0

    # EXECUTE path
    # Round the limit price UP to the market's tick grid (to lift the ask). The
    # raw gamma midpoint is often off-grid (e.g. 0.935 on a 0.01-tick market) and
    # gets rejected with "breaks minimum tick size rule". Lesson: 2026-05-31
    # Satoshi entry bounced on the 0.935 midpoint. Buying → round UP so the limit
    # is marketable against the resting ask.
    import math
    tick_dec = max(0, -int(round(math.log10(tick))))  # 0.01 → 2 decimals
    buy_price = round(math.ceil(round(mark / tick, 6)) * tick, tick_dec)
    # CLOB amount-precision rule: maker (USD) max 2 decimals. On fine-tick markets
    # (0.001), a 3-dec limit price × integer shares gives a 3-dec maker → 400
    # "invalid amounts" (bit the DEC-0038 entry 2026-06-12). Round the LIMIT up to
    # the next 0.01 regardless of tick — still on-grid, FAK fills at the book's
    # better resting prices, and integer shares × 2-dec price keeps maker/taker clean.
    if tick_dec > 2:
        buy_price = round(math.ceil(round(buy_price * 100, 6)) / 100, 2)
    buy_price = min(buy_price, 0.99)  # never post above 0.99
    order_flags = ["--order-type", "FAK"]
    if args.maker:
        # Maker-first entry (operator 2026-07-24: limit orders are everyday
        # repertoire). Rest at best_bid+tick, capped 1 tick under the ask, so
        # the order is passive: zero taker fee (1000bps markets charge takers
        # rate x p x (1-p)/share, true curve) and the bid-side price. A resting bid fills
        # under FUTURE information — allowed only with per-tick re-verification
        # and news_watcher coverage of the market's info channel (rules in
        # notes/resting_orders.md). The price was computed BEFORE the robust
        # gate (single book fetch) so the gated and posted prices are the same
        # number; fee_per_share is already 0 from effective_entry_cost.
        buy_price = maker_px
        order_flags = ["--post-only"]  # GTC default; post-only rejects if it would cross
    # Integer shares × on-grid 2-dec price → clean maker (2-dec) / taker (int).
    # Fee-bearing markets: size shares off (price + fee) so the CASH outlay
    # (notional + exchange fee) stays within the deploy budget.
    target_shares = max(1, round(deploy_dollar / (buy_price + fee_per_share)))
    clean_usd = round(target_shares * buy_price, 2)
    mode = "RESTING post-only BID (record in notes/resting_orders.md)" if args.maker else "taker FAK"
    print(f"\n# Executing BUY {target_shares} shares ({side}) @ {buy_price} (tick {tick}) for ${clean_usd} [{mode}]")

    cmd = [".venv/bin/python", "scripts/clob_v2.py",
           "buy" if side in ("YES", "NO") else "sell",
           token, str(buy_price), str(clean_usd), *order_flags]
    if neg_risk:
        cmd.extend(["--neg-risk", "true"])
    print(f"  cmd: {' '.join(cmd)}", file=sys.stderr)
    r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
    print(r.stdout)
    if r.returncode != 0:
        print(f"  stderr: {r.stderr[:500]}", file=sys.stderr)
        return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
