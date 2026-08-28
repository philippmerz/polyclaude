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

    # Equal-share negRisk range bundle (dry-run unless --execute is present)
    python scripts/polyclaude_enter.py --side YES --bundle-slug bucket-a --bundle-slug bucket-b \
        --bundle-shares 20 --max-bundle-cost 0.57 --my-p 0.76
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path

import httpx

from book_walk import maker_rest_price
import pm_fees

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


def bundle_metrics(cost_per_share: float, my_p: float, edge_haircut: float,
                   shares: float) -> dict:
    """Economics for equal YES shares across mutually exclusive event buckets.

    One covered bucket pays ``shares`` dollars and every uncovered state pays
    zero, so the bundle is economically one binary contract with price equal to
    the sum of the leg costs. Keeping this pure makes the joint robust-edge math
    regression-testable; evaluating legs independently would wrongly reject a
    useful range bundle (or, worse, leave a naked leg after partial execution).
    """
    if not math.isfinite(cost_per_share) or not 0.0 < cost_per_share < 1.0:
        raise ValueError("bundle cost per payout share must be between 0 and 1")
    if not math.isfinite(my_p) or not 0.0 <= my_p <= 1.0:
        raise ValueError("bundle probability must be between 0 and 1")
    if not math.isfinite(edge_haircut) or not 0.0 <= edge_haircut <= 1.0:
        raise ValueError("edge haircut must be between 0 and 1")
    if not math.isfinite(shares) or shares <= 0:
        raise ValueError("bundle shares must be positive")
    p_robust = max(0.0, my_p - edge_haircut)
    return {
        "cost_per_share": cost_per_share,
        "p_robust": p_robust,
        "central_ev": shares * (my_p - cost_per_share),
        "robust_ev": shares * (p_robust - cost_per_share),
        "risk_dollars": shares * cost_per_share,
        "payout_if_covered": shares,
        "profit_if_covered": shares * (1.0 - cost_per_share),
    }


def _json_list(value) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return []


def _yes_token(market: dict) -> str | None:
    outcomes = _json_list(market.get("outcomes"))
    tokens = _json_list(market.get("clobTokenIds"))
    if len(outcomes) != len(tokens):
        return None
    for outcome, token in zip(outcomes, tokens):
        if str(outcome).strip().lower() == "yes":
            return str(token)
    return None


def _event_ids(market: dict) -> set[str]:
    return {
        str(event.get("id"))
        for event in (market.get("events") or [])
        if isinstance(event, dict) and event.get("id") is not None
    }


def _book_snapshot(token: str) -> dict:
    """Return sorted live levels plus touch/depth for a token; raise on failure."""
    r = httpx.get("https://clob.polymarket.com/book",
                  params={"token_id": str(token)}, timeout=15)
    r.raise_for_status()
    raw = r.json()
    def clean_levels(value: object, name: str, reverse: bool) -> list[dict]:
        if value is None:
            value = []
        if not isinstance(value, list):
            raise RuntimeError(f"CLOB {name} side is not a list")
        levels = []
        for raw_level in value:
            try:
                price = float(raw_level["price"])
                size = float(raw_level["size"])
            except (KeyError, TypeError, ValueError):
                raise RuntimeError(f"malformed CLOB {name} level")
            if (not math.isfinite(price) or not math.isfinite(size)
                    or not 0.0 < price < 1.0 or size <= 0.0):
                raise RuntimeError(f"invalid CLOB {name} level: {raw_level!r}")
            levels.append({"price": price, "size": size})
        return sorted(levels, key=lambda level: level["price"], reverse=reverse)

    asks = clean_levels(raw.get("asks"), "ask", False)
    bids = clean_levels(raw.get("bids"), "bid", True)
    return {
        "asks": asks,
        "bids": bids,
        "best_ask": asks[0]["price"] if asks else None,
        "best_bid": bids[0]["price"] if bids else None,
    }


def _two_decimal_marketable_limit(ask: float, tick: float) -> float:
    """Marketable BUY limit that also yields exact equal shares in clob_v2.

    clob_v2 encodes BUY size as USD/limit-price. A 0.191 limit times an integer
    share count creates the amount-precision failure documented in the ordinary
    entry path, so fine-tick asks are rounded up to the next cent. The signed
    USD amount then encodes exactly the requested integer shares; fills still
    receive price improvement from resting asks.
    """
    tick = tick if tick > 0 else 0.01
    tick_dec = max(0, -int(round(math.log10(tick))))
    px = round(math.ceil(round(ask / tick, 8)) * tick, tick_dec)
    if tick_dec > 2:
        px = round(math.ceil(round(px * 100, 8)) / 100, 2)
    return min(px, 0.99)


_BALANCE_TOL = 1e-4


def _parse_clob_result(stdout: str, side: str,
                       expected_shares: float) -> tuple[bool, dict | None]:
    """Parse clob_v2 output and prove an immediate, exact exchange match.

    HTTP 200 and ``success=true`` are not fill proofs: the CLOB can return live
    or delayed orders, and a nominal match can carry the wrong amount. Bundle
    execution also reconciles the ERC-1155 balance before sending the next leg.
    """
    start = stdout.find("{")
    if start < 0:
        return False, None
    try:
        result = json.loads(stdout[start:])
    except Exception:
        return False, None
    body = result.get("body") if isinstance(result, dict) else None
    try:
        status_code = int(result.get("status_code", 999))
    except (AttributeError, TypeError, ValueError):
        return False, result if isinstance(result, dict) else None
    if not isinstance(body, dict) or status_code >= 400:
        return False, result
    if body.get("success") is not True or body.get("errorMsg") or body.get("error"):
        return False, result
    status = str(body.get("status") or "").lower()
    if status != "matched":
        return False, result
    if not str(body.get("orderID") or "").strip():
        return False, result
    txs = body.get("transactionsHashes")
    if not isinstance(txs, list) or not any(str(tx).strip() for tx in txs):
        return False, result
    amount_key = "takingAmount" if side.upper() == "BUY" else "makingAmount"
    try:
        amount = float(body[amount_key])
        expected = float(expected_shares)
    except (KeyError, TypeError, ValueError):
        return False, result
    if (not math.isfinite(amount) or not math.isfinite(expected)
            or expected <= 0.0 or abs(amount - expected) > _BALANCE_TOL):
        return False, result
    return True, result


def _classify_clob_result(stdout: str, side: str,
                          expected_shares: float) -> tuple[str, dict | None]:
    """Return ``matched``, ``failed``, or ``ambiguous`` for a response."""
    ok, result = _parse_clob_result(stdout, side, expected_shares)
    if ok:
        return "matched", result
    if result is None:
        return "ambiguous", None
    body = result.get("body") if isinstance(result, dict) else None
    if not isinstance(body, dict):
        return "ambiguous", result
    status = str(body.get("status") or "").lower()
    terminal_statuses = {"unmatched", "rejected", "cancelled", "canceled", "failed"}
    order_id = str(body.get("orderID") or "").strip()
    txs = body.get("transactionsHashes")
    has_tx = isinstance(txs, list) and any(str(tx).strip() for tx in txs)
    trade_ids = body.get("tradeIDs")
    has_trade = (isinstance(trade_ids, list)
                 and any(str(trade_id).strip() for trade_id in trade_ids))
    # These states can still execute later. Never unwind around them. An HTTP
    # error or an errorMsg alone is not terminal evidence: a proxy/429/5xx can
    # race with exchange acceptance, so treating it as a definite failure could
    # create a naked late fill while prior legs are being unwound.
    if status in {"live", "delayed", "pending", "matched"} or body.get("success") is True:
        return "ambiguous", result
    if has_tx or has_trade or (order_id and status not in terminal_statuses):
        return "ambiguous", result
    try:
        http_status = int(result.get("status_code", 999))
    except (TypeError, ValueError):
        http_status = 999
    if http_status >= 500 or http_status in {408, 409, 425, 429}:
        return "ambiguous", result
    if body.get("success") is False:
        return "failed", result
    if status in terminal_statuses:
        return "failed", result
    return "ambiguous", result


def _run_clob_order(side: str, token: str, price: float, size: float,
                    expected_shares: float) -> tuple[str, str]:
    cmd = [
        ".venv/bin/python", "scripts/clob_v2.py", side.lower(), token,
        str(price), str(size), "--order-type", "FOK", "--neg-risk", "true",
    ]
    print(f"  cmd: {' '.join(cmd)}", file=sys.stderr)
    try:
        r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        print("!! CLOB command timed out; fill state is AMBIGUOUS", file=sys.stderr)
        return "ambiguous", partial
    except Exception as exc:
        print(f"!! CLOB command failed before a parseable result: {exc}", file=sys.stderr)
        return "ambiguous", ""
    if r.stdout:
        print(r.stdout)
    if r.stderr:
        print(f"  stderr: {r.stderr[:500]}", file=sys.stderr)
    state, _ = _classify_clob_result(r.stdout, side, expected_shares)
    # A nonzero local exit with a strict matched exchange body remains ambiguous
    # until the on-chain reconciliation below.
    if r.returncode != 0 and state == "matched":
        state = "ambiguous"
    return state, r.stdout


def _clob_market_info(condition_id: str) -> dict:
    """Fetch execution-time market metadata from the CLOB, fail closed."""
    full_r = httpx.get(f"https://clob.polymarket.com/markets/{condition_id}", timeout=15)
    full_r.raise_for_status()
    compact_r = httpx.get(f"https://clob.polymarket.com/clob-markets/{condition_id}", timeout=15)
    compact_r.raise_for_status()
    full, compact = full_r.json(), compact_r.json()
    if not isinstance(full, dict) or not isinstance(compact, dict):
        raise RuntimeError("malformed CLOB market metadata")
    if str(full.get("condition_id") or "").lower() != condition_id.lower():
        raise RuntimeError("CLOB full metadata conditionId mismatch")
    if str(compact.get("c") or "").lower() != condition_id.lower():
        raise RuntimeError("CLOB compact metadata conditionId mismatch")
    if (full.get("accepting_orders") is not True or compact.get("ao") is not True
            or full.get("enable_order_book") is not True
            or full.get("active") is not True or full.get("closed") is True):
        raise RuntimeError("CLOB is not actively accepting orders")
    if "seconds_delay" not in full:
        raise RuntimeError("CLOB omitted seconds_delay")
    try:
        seconds_delay = float(full["seconds_delay"])
    except (TypeError, ValueError):
        raise RuntimeError("invalid CLOB seconds_delay")
    # Some compact schema revisions expose the delay flag as `itode`; either
    # signal blocks an equal-set execution because delayed legs can fill later.
    if not math.isfinite(seconds_delay) or seconds_delay != 0 or compact.get("itode") is True:
        raise RuntimeError(f"CLOB execution delay is nonzero ({seconds_delay:g}s)")
    try:
        minimum_order_size = float(full["minimum_order_size"])
        minimum_tick_size = float(full["minimum_tick_size"])
    except (KeyError, TypeError, ValueError):
        raise RuntimeError("invalid CLOB minimum size/tick")
    if (not math.isfinite(minimum_order_size) or not math.isfinite(minimum_tick_size)
            or minimum_order_size <= 0 or minimum_tick_size <= 0):
        raise RuntimeError("nonpositive CLOB minimum size/tick")
    return {
        "full": full,
        "compact": compact,
        "minimum_order_size": minimum_order_size,
        "minimum_tick_size": minimum_tick_size,
    }


def _clob_fee_market(info: dict) -> dict | None:
    """Translate CLOB match-time fee data into pm_fees' normalized input."""
    compact = info["compact"]
    full = info["full"]
    fd = compact.get("fd")
    if isinstance(fd, dict):
        if isinstance(fd.get("r"), bool) or isinstance(fd.get("e"), bool):
            raise RuntimeError("invalid compact CLOB fee descriptor")
        try:
            rate = float(fd["r"])
            exponent = float(fd["e"])
        except (KeyError, TypeError, ValueError):
            raise RuntimeError("malformed compact CLOB fee descriptor")
        taker_only = fd.get("to", True)
        if (not math.isfinite(rate) or not math.isfinite(exponent)
                or rate < 0.0 or exponent < 0.0 or not isinstance(taker_only, bool)):
            raise RuntimeError("invalid compact CLOB fee descriptor")
        return {
            "feesEnabled": True,
            "feeSchedule": {
                "rate": rate,
                "exponent": exponent,
                "takerOnly": taker_only,
            },
        }
    if fd is not None:
        raise RuntimeError("compact CLOB fee descriptor is not an object")
    raw = compact.get("tbf")
    if raw is None:
        raw = full.get("taker_base_fee")
    if raw is not None:
        if isinstance(raw, bool):
            raise RuntimeError("invalid legacy CLOB fee field")
        try:
            parsed = float(raw)
        except (TypeError, ValueError):
            raise RuntimeError("malformed legacy CLOB fee field")
        if not math.isfinite(parsed) or parsed < 0.0:
            raise RuntimeError("invalid legacy CLOB fee field")
        return {"feesEnabled": bool(parsed), "takerBaseFee": parsed}
    # Unknown CLOB fee state takes pm_fees' conservative fallback.
    return None


def _fetch_live_positions() -> list[dict]:
    """Fetch indexed positions; bundle mode fails closed if unavailable."""
    from polyclaude_client import Wallet
    address = Wallet.load().address
    r = httpx.get("https://data-api.polymarket.com/positions",
                  params={"user": address.lower(), "limit": "500"}, timeout=15)
    r.raise_for_status()
    rows = r.json()
    if not isinstance(rows, list):
        raise RuntimeError("data-api positions response is not a list")
    return rows


def _chain_reader() -> dict:
    """Create one Polygon reader for balance/allowance reconciliation."""
    from web3 import Web3
    from polyclaude_client import CTF, CTF_ABI, ERC20_ABI, Wallet, pick_rpc
    from clob_v2 import NEG_RISK_EXCHANGE_V2, PUSD_ADDR
    w3 = pick_rpc()
    address = Wallet.load().address
    ctf = w3.eth.contract(address=CTF, abi=CTF_ABI)
    pusd = w3.eth.contract(address=Web3.to_checksum_address(PUSD_ADDR), abi=ERC20_ABI)
    return {
        "w3": w3,
        "address": address,
        "ctf": ctf,
        "pusd": pusd,
        "exchange": Web3.to_checksum_address(NEG_RISK_EXCHANGE_V2),
    }


def _read_token_balances(reader: dict, tokens: list[str]) -> dict[str, float]:
    address, ctf = reader["address"], reader["ctf"]
    return {
        str(token): ctf.functions.balanceOf(address, int(token)).call() / 1e6
        for token in tokens
    }


def _wait_token_balance(reader: dict, token: str, expected: float,
                        attempts: int = 12, delay: float = 0.75) -> float | None:
    """Poll settlement without ever interpreting an unavailable read as zero."""
    last = None
    for attempt in range(attempts):
        try:
            last = _read_token_balances(reader, [token])[str(token)]
            if abs(last - expected) <= _BALANCE_TOL:
                return last
        except Exception as exc:
            if attempt == attempts - 1:
                print(f"!! final on-chain balance read failed: {exc}", file=sys.stderr)
        if attempt + 1 < attempts:
            time.sleep(delay)
    return last


def _wait_bundle_baselines(reader: dict, baselines: dict[str, float],
                           attempts: int = 12, delay: float = 0.75) -> dict | None:
    """Poll every bundle token until all return to their exact baselines."""
    last = None
    for attempt in range(attempts):
        try:
            last = _read_token_balances(reader, list(baselines))
            if all(abs(last[token] - expected) <= _BALANCE_TOL
                   for token, expected in baselines.items()):
                return last
        except Exception as exc:
            if attempt == attempts - 1:
                print(f"!! final bundle-baseline read failed: {exc}", file=sys.stderr)
        if attempt + 1 < attempts:
            time.sleep(delay)
    return last


def _open_buy_commitment(prohibited_tokens: set[str] | None = None) -> float:
    """Return reserved BUY collateral and reject orders touching bundle legs."""
    from clob_v2 import list_open_orders
    result = list_open_orders()
    if int(result.get("status_code", 999)) >= 400:
        raise RuntimeError(f"open-order query HTTP {result.get('status_code')}")
    body = result.get("body")
    rows = body.get("data") if isinstance(body, dict) else None
    if not isinstance(rows, list):
        raise RuntimeError("open-order query returned an unexpected shape")
    prohibited_tokens = {str(token) for token in (prohibited_tokens or set())}
    committed = 0.0
    for order in rows:
        asset = str(order.get("asset_id") or order.get("assetId") or "")
        if not asset:
            raise RuntimeError("open order omitted asset_id")
        if asset and asset in prohibited_tokens:
            raise RuntimeError(
                f"existing {order.get('side', '?')} order touches bundle token {asset[:16]}...")
        if str(order.get("side") or "").upper() != "BUY":
            continue
        try:
            original = float(order["original_size"])
            matched = float(order.get("size_matched") or 0)
            price = float(order["price"])
        except (KeyError, TypeError, ValueError):
            raise RuntimeError("open BUY has malformed size/price")
        if (not all(math.isfinite(value) for value in (original, matched, price))
                or original < 0.0 or matched < 0.0 or not 0.0 < price < 1.0):
            raise RuntimeError("open BUY has invalid size/price")
        remaining = original - matched
        if remaining < -_BALANCE_TOL:
            raise RuntimeError("open BUY has negative remaining size")
        committed += max(0.0, remaining) * price
    return committed


def _wallet_funds_state(reader: dict,
                        prohibited_tokens: set[str] | None = None) -> dict:
    """Read deployable pUSD and approvals needed for buy + emergency sell."""
    address = reader["address"]
    pusd = reader["pusd"]
    decimals = int(pusd.functions.decimals().call())
    balance = pusd.functions.balanceOf(address).call() / 10 ** decimals
    allowance = pusd.functions.allowance(address, reader["exchange"]).call() / 10 ** decimals
    ctf_approved = bool(reader["ctf"].functions.isApprovedForAll(
        address, reader["exchange"]).call())
    committed = _open_buy_commitment(prohibited_tokens)
    return {
        "balance": balance,
        "committed": committed,
        "deployable": balance - committed,
        "allowance": allowance,
        "ctf_approved": ctf_approved,
    }


def _position_number(position: dict, key: str, context: str) -> float:
    """Read a required nonnegative data-api number without NaN fail-open."""
    try:
        value = float(position[key])
    except (KeyError, TypeError, ValueError):
        raise RuntimeError(f"{context} {key} is unavailable")
    if not math.isfinite(value) or value < 0.0:
        raise RuntimeError(f"{context} {key} is invalid")
    return value


def _position_gross_cost(position: dict, context: str) -> float:
    """Gross entry collateral including separately reported entry fees."""
    return (_position_number(position, "initialValue", context)
            + _position_number(position, "entryFeesUsdc", context))


def _validate_existing_bundle(legs: list[dict], positions: list[dict],
                              balances: dict[str, float],
                              allow_add: bool) -> tuple[dict[str, float], float]:
    """Require either a completely fresh set or one indexed, equal YES set."""
    baselines = {leg["token"]: float(balances[leg["token"]]) for leg in legs}
    nonzero = [value > _BALANCE_TOL for value in baselines.values()]
    if any(nonzero) and not all(nonzero):
        raise RuntimeError(f"broken existing set on-chain: {baselines}")
    if all(nonzero):
        values = list(baselines.values())
        if max(values) - min(values) > _BALANCE_TOL:
            raise RuntimeError(f"unequal existing set on-chain: {baselines}")

    held_rows: list[dict] = []
    for leg in legs:
        cid = str(leg["condition_id"]).lower()
        matches = []
        for position in positions:
            if str(position.get("conditionId") or "").lower() != cid:
                continue
            size = _position_number(position, "size", f"position {leg['slug']}")
            if size > _BALANCE_TOL:
                matches.append(position)
        bad = [position for position in matches
               if str(position.get("outcome") or "").lower() != "yes"
               or (position.get("asset") is not None
                   and str(position.get("asset")) != leg["token"])]
        yes = [position for position in matches if position not in bad]
        if bad:
            raise RuntimeError(f"non-YES or wrong-token exposure exists in {leg['slug']}")
        if len(yes) > 1:
            raise RuntimeError(f"duplicate indexed YES positions in {leg['slug']}")
        if yes:
            held_rows.append(yes[0])
            indexed_size = _position_number(yes[0], "size", f"position {leg['slug']}")
            if abs(indexed_size - baselines[leg["token"]]) > 0.01:
                raise RuntimeError(f"data-api/on-chain size disagreement in {leg['slug']}")

    has_chain = all(nonzero)
    if has_chain and len(held_rows) != len(legs):
        raise RuntimeError("on-chain set exists but data-api has not indexed every leg")
    if not has_chain and held_rows:
        raise RuntimeError("data-api reports exposure absent from current on-chain balances")
    if has_chain and not allow_add:
        raise RuntimeError("existing equal-share set; deliberate adds require --bundle-add")
    if not has_chain and allow_add:
        raise RuntimeError("--bundle-add requested but no existing equal-share set exists")

    held_cost = 0.0
    for row in held_rows:
        held_cost += _position_gross_cost(
            row, f"existing bundle position {row.get('slug', '?')}")
    return baselines, held_cost


def _existing_cluster_cost(legs: list[dict], positions: list[dict]) -> float:
    """Infer live cost in the bundle's event and configured correlation cluster.

    Every position in the same Gamma event is perfectly dependent even when a
    prior is absent or mistagged. Configured cluster membership broadens that
    set. Each position is visited once, so overlap cannot double count it.
    Malformed matching position data fails closed.
    """
    event_sets = [set(leg.get("event_ids") or set()) for leg in legs]
    shared_event_ids = set.intersection(*event_sets) if event_sets else set()
    if not shared_event_ids:
        raise RuntimeError("bundle has no shared Gamma event ID for exposure accounting")

    cluster_slugs: set[str] = set()
    try:
        priors = json.loads((REPO_ROOT / "notes" / "portfolio_kelly_priors.json").read_text())
    except Exception as exc:
        raise RuntimeError(f"portfolio priors unavailable: {exc}")
    if not isinstance(priors, dict):
        raise RuntimeError("portfolio priors root is not an object")
    clusters = []
    for leg in legs:
        prior = priors.get(leg["slug"])
        cluster = prior.get("cluster") if isinstance(prior, dict) else None
        if not cluster:
            raise RuntimeError(f"bundle leg lacks a configured cluster: {leg['slug']}")
        clusters.append(str(cluster))
    if len(set(clusters)) != 1:
        raise RuntimeError(f"bundle priors disagree on cluster: {sorted(set(clusters))}")
    cluster = clusters[0]
    cluster_slugs = {
        slug for slug, prior in priors.items()
        if isinstance(prior, dict) and prior.get("cluster") == cluster
    }
    total = 0.0
    for position in positions:
        same_event = str(position.get("eventId") or "") in shared_event_ids
        same_cluster = position.get("slug") in cluster_slugs
        if not same_event and not same_cluster:
            continue
        context = f"cluster position {position.get('slug', '?')}"
        if _position_number(position, "size", context) <= _BALANCE_TOL:
            continue
        total += _position_gross_cost(position, context)
    return total


def _marketable_sell_plan(bids: list[dict], shares: float,
                          fee_market: dict | None) -> tuple[float, float, float]:
    """Return FOK limit, cumulative depth, and net proceeds through the book."""
    try:
        target = float(shares)
    except (TypeError, ValueError):
        raise RuntimeError("invalid rollback share count")
    if not math.isfinite(target) or target <= 0.0:
        raise RuntimeError("invalid rollback share count")
    levels: list[tuple[float, float]] = []
    for level in bids:
        try:
            price = float(level["price"])
            size = float(level["size"])
        except (KeyError, TypeError, ValueError):
            raise RuntimeError("malformed rollback bid level")
        if (not math.isfinite(price) or not math.isfinite(size)
                or not 0.0 < price < 1.0 or size <= 0.0):
            raise RuntimeError("invalid rollback bid level")
        levels.append((price, size))
    cumulative = 0.0
    remaining = target
    net_proceeds = 0.0
    for price, size in sorted(levels, key=lambda level: -level[0]):
        cumulative += size
        take = min(size, remaining)
        fee = pm_fees.fee_per_share(fee_market, price)
        if not math.isfinite(fee) or fee < 0.0 or fee >= price:
            raise RuntimeError("invalid rollback fee curve")
        net_proceeds += take * (price - fee)
        remaining -= take
        if remaining <= 1e-9:
            return price, cumulative, net_proceeds
    raise RuntimeError(f"only {cumulative:.2f} shares bid across the book")


def _marketable_sell_limit(bids: list[dict], shares: float) -> tuple[float, float]:
    """Return the lowest bid needed to FOK-sell all shares and total depth."""
    price, depth, _ = _marketable_sell_plan(
        bids, shares, {"feesEnabled": False})
    return price, depth


def _configure_rollback_guards(legs: list[dict], shares: float,
                               total_loss_cap: float) -> float:
    """Prove each possible filled leg can unwind within the total loss budget.

    At most ``len(legs)-1`` legs precede a definite failed FOK. Dividing the
    total budget across that many legs bounds any automatic prefix unwind even
    if every filled leg reaches its individual allowance.
    """
    if (not math.isfinite(total_loss_cap) or total_loss_cap <= 0.0
            or len(legs) < 2):
        raise RuntimeError("invalid automatic-unwind loss budget")
    per_leg_cap = total_loss_cap / (len(legs) - 1)
    for leg in legs:
        sell_px, depth, net_proceeds = _marketable_sell_plan(
            leg["book"]["bids"], shares, leg["fee_market"])
        max_entry_cost = shares * (leg["limit"] + leg["fee_at_limit"])
        modeled_loss = max(0.0, max_entry_cost - net_proceeds)
        if modeled_loss > per_leg_cap + 1e-9:
            raise RuntimeError(
                f"{leg['slug']} unwind loss ${modeled_loss:.2f} through bid "
                f"{sell_px:g} exceeds per-leg cap ${per_leg_cap:.2f}")
        leg.update({
            "rollback_preflight_limit": sell_px,
            "rollback_preflight_depth": depth,
            "rollback_modeled_loss": modeled_loss,
            "rollback_loss_per_share": per_leg_cap / shares,
        })
    return per_leg_cap


def _rollback_bundle(filled: list[dict], baselines: dict[str, float],
                     reader: dict) -> bool:
    """Best-effort FOK unwind of the *observed* incremental balances."""
    print("\n!! BUNDLE LEG FAILED — unwinding filled legs to avoid naked exposure",
          file=sys.stderr)
    all_ok = True
    for leg in reversed(filled):
        try:
            current = _read_token_balances(reader, [leg["token"]])[leg["token"]]
            shares = current - baselines[leg["token"]]
            if shares <= _BALANCE_TOL:
                continue
            book = _book_snapshot(leg["token"])
            # SELL amount precision is shares, so retain the exact fine-tick bid
            # rather than widening a 0.996 market to a 0.99 limit.
            sell_px, depth, net_proceeds = _marketable_sell_plan(
                book["bids"], shares, leg["fee_market"])
            max_entry_cost = shares * (leg["limit"] + leg["fee_at_limit"])
            modeled_loss = max(0.0, max_entry_cost - net_proceeds)
            loss_cap = shares * leg["rollback_loss_per_share"]
            if modeled_loss > loss_cap + 1e-9:
                raise RuntimeError(
                    f"live unwind loss ${modeled_loss:.2f} through bid {sell_px:g} "
                    f"exceeds authorized ${loss_cap:.2f}")
            state, _ = _run_clob_order(
                "SELL", leg["token"], sell_px, shares, shares)
            observed = _wait_token_balance(
                reader, leg["token"], baselines[leg["token"]])
            reconciled = (state == "matched" and observed is not None and
                          abs(observed - baselines[leg["token"]]) <= _BALANCE_TOL)
            if not reconciled:
                raise RuntimeError(
                    f"rollback {state}; on-chain balance {observed!r}, "
                    f"wanted {baselines[leg['token']]:.6f}")
        except Exception as exc:
            all_ok = False
            print(f"!! ROLLBACK FAILED for {leg['slug']}: {exc}", file=sys.stderr)
    return all_ok


def _bundle_entry(args: argparse.Namespace) -> int:
    """Gate and optionally execute equal YES shares in one negRisk event."""
    slugs = list(dict.fromkeys(args.bundle_slug or []))
    if len(slugs) < 2:
        print("ERROR: repeat --bundle-slug for at least two event buckets", file=sys.stderr)
        return 2
    if args.my_p is None:
        print("ERROR: bundle entry requires --my-p for P(any covered bucket)", file=sys.stderr)
        return 2
    if args.bundle_shares is None:
        print("ERROR: bundle entry requires positive --bundle-shares", file=sys.stderr)
        return 2
    if args.max_bundle_cost is None:
        print("ERROR: bundle entry requires --max-bundle-cost between 0 and 1", file=sys.stderr)
        return 2
    numeric_values = {
        "--my-p": args.my_p,
        "--bundle-shares": args.bundle_shares,
        "--max-bundle-cost": args.max_bundle_cost,
        "--bankroll": args.bankroll,
        "--kelly-frac": args.kelly_frac,
        "--rho": args.rho,
        "--cluster-frac": args.cluster_frac,
        "--edge-haircut": args.edge_haircut,
    }
    unwind_arg = getattr(args, "max_bundle_unwind_loss", None)
    if unwind_arg is not None:
        numeric_values["--max-bundle-unwind-loss"] = unwind_arg
    try:
        parsed_values = {name: float(value) for name, value in numeric_values.items()}
    except (TypeError, ValueError):
        print("ERROR: bundle numeric arguments must be finite numbers", file=sys.stderr)
        return 2
    bad_finite = [name for name, value in parsed_values.items() if not math.isfinite(value)]
    if bad_finite:
        print(f"ERROR: bundle numeric arguments must be finite: {', '.join(bad_finite)}",
              file=sys.stderr)
        return 2
    if args.bundle_shares <= 0:
        print("ERROR: bundle entry requires positive --bundle-shares", file=sys.stderr)
        return 2
    if int(args.bundle_shares) != args.bundle_shares:
        print("ERROR: --bundle-shares must be an integer (exact equal-leg invariant)", file=sys.stderr)
        return 2
    shares = int(args.bundle_shares)
    if not 0 < args.max_bundle_cost < 1:
        print("ERROR: bundle entry requires --max-bundle-cost between 0 and 1", file=sys.stderr)
        return 2
    if not 0.0 <= args.my_p <= 1.0:
        print("ERROR: bundle --my-p must be between 0 and 1", file=sys.stderr)
        return 2
    if args.bankroll <= 0.0:
        print("ERROR: bundle --bankroll must be positive", file=sys.stderr)
        return 2
    if not 0.0 < args.kelly_frac <= 1.0:
        print("ERROR: bundle --kelly-frac must be in (0, 1]", file=sys.stderr)
        return 2
    if not 0.0 <= args.rho <= 1.0 or not 0.0 <= args.cluster_frac <= 1.0:
        print("ERROR: bundle --rho and --cluster-frac must be between 0 and 1",
              file=sys.stderr)
        return 2
    if not 0.0 <= args.edge_haircut <= 1.0:
        print("ERROR: bundle --edge-haircut must be between 0 and 1", file=sys.stderr)
        return 2
    if unwind_arg is not None and not 0.0 < unwind_arg <= args.bankroll:
        print("ERROR: --max-bundle-unwind-loss must be positive and no larger than bankroll",
              file=sys.stderr)
        return 2
    if args.side != "YES":
        print("ERROR: bundle mode buys YES legs; pass --side YES explicitly", file=sys.stderr)
        return 2
    if args.maker or args.usd is not None or args.tail_mult is not None:
        print("ERROR: bundle mode is equal-share taker-only; --maker/--usd/--tail-mult are incompatible",
              file=sys.stderr)
        return 2

    legs: list[dict] = []
    for slug in slugs:
        print(f"# bundle: looking up '{slug}'...", file=sys.stderr)
        market = fetch_market_by_slug_or_question(slug)
        if not market:
            print(f"ERROR: bundle market not found: {slug}", file=sys.stderr)
            return 2
        token = _yes_token(market)
        if token is None:
            print(f"ERROR: no unambiguous YES token for {slug}", file=sys.stderr)
            return 2
        if market.get("closed") or market.get("active") is False:
            print(f"ERROR: bundle leg is not active: {slug}", file=sys.stderr)
            return 2
        if market.get("umaResolutionStatus") in ("proposed", "disputed"):
            print(f"ERROR: {slug} has umaResolutionStatus={market.get('umaResolutionStatus')}",
                  file=sys.stderr)
            return 2
        if not bool(market.get("negRisk")):
            print(f"ERROR: {slug} is not a negRisk event bucket", file=sys.stderr)
            return 2
        condition_id = str(market.get("conditionId") or "")
        if not condition_id.startswith("0x"):
            print(f"ERROR: no valid conditionId for {slug}", file=sys.stderr)
            return 2
        try:
            tick = float(market.get("orderPriceMinTickSize") or 0.01)
        except Exception:
            tick = 0.01
        legs.append({
            "slug": market.get("slug") or slug,
            "question": market.get("question") or slug,
            "market": market,
            "market_id": str(market.get("id")),
            "condition_id": condition_id,
            "token": token,
            "neg_risk_id": str(market.get("negRiskMarketID") or ""),
            "event_ids": _event_ids(market),
            "end": market.get("endDate") or market.get("endDateIso") or "",
            "tick": tick if tick > 0 else 0.01,
        })

    if len({leg["market_id"] for leg in legs}) != len(legs):
        print("ERROR: duplicate market IDs in bundle", file=sys.stderr)
        return 2
    if len({leg["condition_id"].lower() for leg in legs}) != len(legs):
        print("ERROR: duplicate condition IDs in bundle", file=sys.stderr)
        return 2
    if len({leg["token"] for leg in legs}) != len(legs):
        print("ERROR: duplicate YES token IDs in bundle", file=sys.stderr)
        return 2
    neg_ids = {leg["neg_risk_id"] for leg in legs}
    if "" in neg_ids or len(neg_ids) != 1:
        print(f"ERROR: legs do not share one negRiskMarketID: {sorted(neg_ids)}", file=sys.stderr)
        return 2
    known_event_ids = [leg["event_ids"] for leg in legs]
    if any(not event_ids for event_ids in known_event_ids):
        print("ERROR: a bundle leg omitted its Gamma event ID", file=sys.stderr)
        return 2
    if not set.intersection(*known_event_ids):
        print("ERROR: legs do not share a Gamma event ID", file=sys.stderr)
        return 2
    ends = {leg["end"] for leg in legs if leg["end"]}
    if len(ends) > 1:
        print(f"ERROR: legs have different end dates: {sorted(ends)}", file=sys.stderr)
        return 2

    # Two independent sources guard accidental adds: current ERC-1155 balances
    # are authoritative, while data-api indexing supplies cost basis and catches
    # a transient RPC/data disagreement. Bundle mode fails closed on either.
    try:
        reader = _chain_reader()
        live_positions = _fetch_live_positions()
        chain_balances = _read_token_balances(reader, [leg["token"] for leg in legs])
        baselines, held_set_cost = _validate_existing_bundle(
            legs, live_positions, chain_balances, args.bundle_add)
    except Exception as exc:
        print(f"ERROR: bundle exposure preflight failed: {exc}", file=sys.stderr)
        return 1

    def refresh() -> tuple[list[dict], float, float]:
        expected_total = 0.0
        signed_total = 0.0
        for leg in legs:
            info = _clob_market_info(leg["condition_id"])
            if info["minimum_order_size"] > shares + _BALANCE_TOL:
                raise RuntimeError(
                    f"{leg['slug']} minimum order is {info['minimum_order_size']:g} shares")
            clob_tokens = {str(token.get("token_id")): str(token.get("outcome") or "").lower()
                           for token in (info["full"].get("tokens") or [])
                           if isinstance(token, dict)}
            if clob_tokens.get(leg["token"]) != "yes":
                raise RuntimeError(f"CLOB YES-token mismatch: {leg['slug']}")
            if info["full"].get("neg_risk") is not True:
                raise RuntimeError(f"CLOB does not mark leg negRisk: {leg['slug']}")
            clob_neg_id = str(info["full"].get("neg_risk_market_id") or "")
            if (not clob_neg_id or
                    clob_neg_id.lower() != leg["neg_risk_id"].lower()):
                raise RuntimeError(
                    f"CLOB/Gamma negRiskMarketID mismatch: {leg['slug']}")
            leg["tick"] = info["minimum_tick_size"]
            leg["clob_info"] = info
            leg["fee_market"] = _clob_fee_market(info)
            book = _book_snapshot(leg["token"])
            ask = book["best_ask"]
            if ask is None:
                raise RuntimeError(f"empty ask side: {leg['slug']}")
            limit_px = _two_decimal_marketable_limit(ask, leg["tick"])
            depth = sum(x["size"] for x in book["asks"] if x["price"] <= limit_px + 1e-12)
            if depth + 1e-9 < shares:
                raise RuntimeError(
                    f"{leg['slug']} has only {depth:.2f} shares through limit {limit_px:.2f}"
                )
            fee_at_ask = pm_fees.fee_per_share(leg["fee_market"], ask)
            signed_leg_cost = pm_fees.max_taker_buy_cost_through(
                leg["fee_market"], limit_px)
            fee_at_limit = signed_leg_cost - limit_px
            leg.update({"book": book, "ask": ask, "limit": limit_px, "depth": depth,
                        "fee_at_ask": fee_at_ask, "fee_at_limit": fee_at_limit})
            expected_total += ask + fee_at_ask
            signed_total += signed_leg_cost
        return legs, expected_total, signed_total

    try:
        _, expected_cost, signed_cost = refresh()
    except Exception as exc:
        print(f"ERROR: bundle preflight failed: {exc}", file=sys.stderr)
        return 1

    # The ceiling applies to the worst signed limits, not merely today's touch;
    # this keeps a millisecond book move from silently changing the thesis.
    if signed_cost > args.max_bundle_cost + 1e-9:
        print(f"\nDECISION: SKIP — signed bundle ceiling {signed_cost:.4f} exceeds "
              f"--max-bundle-cost {args.max_bundle_cost:.4f}")
        return 0
    try:
        econ = bundle_metrics(signed_cost, args.my_p, args.edge_haircut, shares)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    OP_COST = 0.05
    if econ["p_robust"] <= signed_cost or econ["robust_ev"] <= OP_COST:
        print("\nDECISION: SKIP — bundle edge does not survive the joint probability haircut.")
        print(f"  central p={args.my_p:.4f}, pessimistic p={econ['p_robust']:.4f}, "
              f"signed cost={signed_cost:.4f}")
        print(f"  central EV ${econ['central_ev']:+.2f}; robust EV ${econ['robust_ev']:+.2f}")
        return 0
    hard_cap = args.bankroll * 0.15
    combined_ticket = held_set_cost + econ["risk_dollars"]
    if combined_ticket > hard_cap + 1e-9:
        print(f"\nDECISION: SKIP — bundle ticket after trade ${combined_ticket:.2f} exceeds "
              f"15% cap ${hard_cap:.2f} (held ${held_set_cost:.2f} + new "
              f"${econ['risk_dollars']:.2f})")
        return 0
    try:
        inferred_cluster_cost = _existing_cluster_cost(legs, live_positions)
    except Exception as exc:
        print(f"ERROR: cluster-cap preflight failed: {exc}", file=sys.stderr)
        return 1
    cluster_before = max(inferred_cluster_cost,
                         max(0.0, args.cluster_frac) * args.bankroll)
    cluster_after = cluster_before + econ["risk_dollars"]
    cluster_cap = args.bankroll * 0.30
    if cluster_after > cluster_cap + 1e-9:
        print(f"\nDECISION: SKIP — correlated cluster after trade ${cluster_after:.2f} "
              f"exceeds 30% cap ${cluster_cap:.2f}")
        return 0
    effective_cluster_frac = min(1.0, cluster_before / args.bankroll)
    kelly_dollar, details = kelly_size(
        signed_cost, args.my_p, args.bankroll, args.kelly_frac, args.rho,
        effective_cluster_frac)
    unwind_loss_cap = (unwind_arg if unwind_arg is not None else
                       min(econ["risk_dollars"] * 0.20, args.bankroll * 0.01))
    try:
        rollback_per_leg = _configure_rollback_guards(legs, shares, unwind_loss_cap)
    except Exception as exc:
        print(f"\nDECISION: SKIP — automatic unwind is not safely marketable: {exc}")
        return 0

    print("\n=== SYNTHETIC RANGE BUNDLE ===")
    print(f"  structure: {shares} equal YES shares across {len(legs)} mutually exclusive buckets")
    print(f"  shared negRiskMarketID: {next(iter(neg_ids))}")
    for leg in legs:
        fee_note = f" + fee {leg['fee_at_ask']:.4f}" if leg["fee_at_ask"] else " (fee-free)"
        print(f"  - {leg['question']}: ask {leg['ask']:.4f}{fee_note}; "
              f"signed limit {leg['limit']:.2f}; depth {leg['depth']:.1f}")
    print(f"  live expected cost/share: {expected_cost:.4f}; worst signed cost/share: {signed_cost:.4f} "
          f"(ceiling {args.max_bundle_cost:.4f})")
    print(f"  P(covered) central {args.my_p:.3f}; after {args.edge_haircut:.2f} haircut "
          f"{econ['p_robust']:.3f}")
    if held_set_cost:
        print(f"  existing equal set: {next(iter(baselines.values())):.6f} shares/leg, "
              f"cost basis ${held_set_cost:.2f}; this is an explicit matched add")
    print(f"  new risk <= ${econ['risk_dollars']:.2f}; ticket after <= ${combined_ticket:.2f}; "
          f"payout added ${econ['payout_if_covered']:.2f}; "
          f"profit >= ${econ['profit_if_covered']:.2f} if covered")
    print(f"  central EV ${econ['central_ev']:+.2f}; robust EV ${econ['robust_ev']:+.2f}")
    print(f"  half-Kelly recommendation ${kelly_dollar:.2f} "
          f"({details['full_kelly']*100:.1f}% full Kelly); chosen risk "
          f"{econ['risk_dollars']/args.bankroll*100:.1f}% of bankroll")
    print(f"  inferred cluster before {effective_cluster_frac*100:.1f}% of bankroll; "
          f"automatic unwind loss capped at ${unwind_loss_cap:.2f} total "
          f"(${rollback_per_leg:.2f}/possible filled leg)")

    if not args.execute:
        action = "WOULD_ADD_BUNDLE" if held_set_cost else "WOULD_BUY_BUNDLE"
        print(f"\nDECISION: {action} — {shares} equal shares, new risk <= "
              f"${econ['risk_dollars']:.2f}")
        print("  Re-run with --execute to place zero-delay FOK legs. Definite failures "
              "unwind; ambiguous exchange states stop for manual reconciliation.")
        return 0

    # Re-fetch every book immediately before the first order. No order is sent
    # unless every full leg remains executable inside the original ceiling.
    try:
        _, expected_cost, signed_cost = refresh()
    except Exception as exc:
        print(f"ERROR: final bundle preflight failed: {exc}", file=sys.stderr)
        return 1
    if signed_cost > args.max_bundle_cost + 1e-9:
        print(f"ERROR: final signed cost {signed_cost:.4f} broke ceiling "
              f"{args.max_bundle_cost:.4f}; no orders sent", file=sys.stderr)
        return 1

    # Re-run every economic and capital gate on the final signed limits. A move
    # can stay under the user's ceiling yet erase robust EV or break a portfolio
    # cap, so the earlier decision is not reusable here.
    try:
        final_econ = bundle_metrics(signed_cost, args.my_p, args.edge_haircut, shares)
    except ValueError as exc:
        print(f"ERROR: final bundle economics invalid: {exc}", file=sys.stderr)
        return 1
    final_ticket = held_set_cost + final_econ["risk_dollars"]
    final_cluster = cluster_before + final_econ["risk_dollars"]
    if (final_econ["p_robust"] <= signed_cost or final_econ["robust_ev"] <= OP_COST
            or final_ticket > hard_cap + 1e-9 or final_cluster > cluster_cap + 1e-9):
        print("ERROR: final book failed robust-EV/ticket/cluster gate; no orders sent",
              file=sys.stderr)
        return 1
    final_unwind_loss_cap = (unwind_arg if unwind_arg is not None else
                             min(final_econ["risk_dollars"] * 0.20,
                                 args.bankroll * 0.01))
    try:
        _configure_rollback_guards(legs, shares, final_unwind_loss_cap)
    except Exception as exc:
        print(f"ERROR: final rollback-liquidity gate failed: {exc}; no orders sent",
              file=sys.stderr)
        return 1

    # Nothing may have changed between the initial exposure read and order one.
    try:
        now_balances = _read_token_balances(reader, [leg["token"] for leg in legs])
        for token, baseline in baselines.items():
            if abs(now_balances[token] - baseline) > _BALANCE_TOL:
                raise RuntimeError(
                    f"token {token[:14]} balance moved {baseline:.6f} -> "
                    f"{now_balances[token]:.6f}")
        funds = _wallet_funds_state(
            reader, {leg["token"] for leg in legs})
        # Close the fill race between the first balance read and authenticated
        # open-order query: if a selected GTC disappeared by filling, this second
        # read catches the changed leg before bundle order one.
        after_order_check = _read_token_balances(
            reader, [leg["token"] for leg in legs])
        for token, baseline in baselines.items():
            if abs(after_order_check[token] - baseline) > _BALANCE_TOL:
                raise RuntimeError(
                    f"token {token[:14]} moved during open-order preflight")
    except Exception as exc:
        print(f"ERROR: final wallet preflight failed: {exc}; no orders sent", file=sys.stderr)
        return 1
    required_pusd = shares * signed_cost
    if funds["deployable"] + 1e-9 < required_pusd:
        print(f"ERROR: deployable pUSD ${funds['deployable']:.6f} is below worst bundle "
              f"cost ${required_pusd:.6f}; no orders sent", file=sys.stderr)
        return 1
    required_allowance = funds["committed"] + required_pusd
    if funds["allowance"] + 1e-9 < required_allowance:
        print(f"ERROR: pUSD allowance ${funds['allowance']:.6f} is below required "
              f"${required_allowance:.6f} including open BUY commitments; no orders sent",
              file=sys.stderr)
        return 1
    if not funds["ctf_approved"]:
        print("ERROR: CTF is not approved for emergency bundle unwind; no orders sent",
              file=sys.stderr)
        return 1
    print(f"# wallet preflight: pUSD ${funds['balance']:.6f}, open-BUY commitments "
          f"${funds['committed']:.6f}, deployable ${funds['deployable']:.6f}, "
          f"need <= ${required_pusd:.6f}", file=sys.stderr)

    # Scarce book first. A strict response is still followed by on-chain balance
    # reconciliation. Only a definite exchange failure plus an unchanged token
    # balance authorizes automatic unwind; delayed/malformed/timeout states stop
    # without creating an even worse naked leg around a possible later fill.
    filled: list[dict] = []
    for leg in sorted(legs, key=lambda x: x["depth"]):
        usd_limit = round(shares * leg["limit"], 2)
        print(f"\n# Executing bundle leg: BUY {shares} YES @ limit {leg['limit']:.2f} "
              f"(${usd_limit:.2f} max) — {leg['slug']}")
        state, _ = _run_clob_order(
            "BUY", leg["token"], leg["limit"], usd_limit, shares)
        target = baselines[leg["token"]] + shares
        observed = _wait_token_balance(reader, leg["token"], target)
        if (state == "matched" and observed is not None
                and abs(observed - target) <= _BALANCE_TOL):
            filled.append(leg)
            continue

        unchanged = (observed is not None and
                     abs(observed - baselines[leg["token"]]) <= _BALANCE_TOL)
        if state == "failed" and unchanged:
            rollback_ok = _rollback_bundle(filled, baselines, reader) if filled else True
            if not rollback_ok:
                print("CRITICAL: bundle unwind incomplete — inspect positions immediately",
                      file=sys.stderr)
                return 4
            all_observed = _wait_bundle_baselines(reader, baselines)
            all_flat = (all_observed is not None and
                        all(abs(all_observed[token] - expected) <= _BALANCE_TOL
                            for token, expected in baselines.items()))
            if not all_flat:
                print(f"CRITICAL: post-unwind bundle is not at baseline: "
                      f"live={all_observed}, wanted={baselines}. Inspect immediately.",
                      file=sys.stderr)
                return 4
            print("ERROR: bundle was not completed; prior fills were unwound", file=sys.stderr)
            return 3

        print(f"CRITICAL: {leg['slug']} exchange state={state}, on-chain balance="
              f"{observed!r}, baseline={baselines[leg['token']]:.6f}, "
              f"target={target:.6f}. No further orders or automatic unwind: "
              f"inspect the possibly pending fill immediately.", file=sys.stderr)
        return 4

    try:
        final_balances = _read_token_balances(reader, [leg["token"] for leg in legs])
    except Exception as exc:
        print(f"CRITICAL: final bundle balance read failed: {exc}", file=sys.stderr)
        return 4
    expected_balances = {
        leg["token"]: baselines[leg["token"]] + shares for leg in legs
    }
    if any(abs(final_balances[token] - expected) > _BALANCE_TOL
           for token, expected in expected_balances.items()):
        print(f"CRITICAL: final equal-set invariant failed: live={final_balances}, "
              f"expected={expected_balances}", file=sys.stderr)
        return 4

    action = "ADDED_BUNDLE" if held_set_cost else "BOUGHT_BUNDLE"
    final_per_leg = next(iter(expected_balances.values()))
    print(f"\nDECISION: {action} — added {shares} equal YES shares across {len(legs)} buckets")
    print(f"  VERIFIED ON-CHAIN: every leg now holds {final_per_leg:.6f} shares.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("question", nargs="?", default=None,
                   help="Polymarket question or slug (or omit if --slug provided)")
    p.add_argument("--slug", default=None, help="Explicit slug (alternative to question lookup)")
    p.add_argument("--bundle-slug", action="append", default=None,
                   help="Mutually exclusive negRisk bucket slug; repeat for an equal-YES-share "
                        "synthetic range bundle. Requires --my-p, --bundle-shares, and "
                        "--max-bundle-cost; bundle mode is taker-only.")
    p.add_argument("--bundle-shares", type=float, default=None,
                   help="Exact integer YES-share count to buy in every --bundle-slug leg")
    p.add_argument("--bundle-add", action="store_true",
                   help="Explicitly add equal shares to an existing, on-chain-verified equal set")
    p.add_argument("--max-bundle-cost", type=float, default=None,
                   help="Hard ceiling on the sum of signed per-share leg costs, including fees")
    p.add_argument("--max-bundle-unwind-loss", type=float, default=None,
                   help="Maximum total dollars an automatic partial-bundle unwind may lose. "
                        "Default: min(20%% of new bundle risk, 1%% of bankroll). Entry is "
                        "blocked unless every possible filled leg has sufficient live depth.")
    p.add_argument("--my-p", type=float, default=None,
                   help="My P(side wins) estimate. If omitted, will run catalyst_check.")
    p.add_argument("--side", choices=["YES", "NO"], default=None,
                   help="Which side to buy (ordinary entries default NO; bundle mode requires "
                        "explicit --side YES)")
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
    if args.bundle_slug:
        return _bundle_entry(args)
    if args.bundle_add:
        print("ERROR: --bundle-add requires --bundle-slug", file=sys.stderr)
        return 2
    if args.side is None:
        args.side = "NO"

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

    # Taker-fee awareness (2026-08-28): Gamma's structured feeSchedule is the
    # source of truth. The legacy takerBaseFee=1000 field remains populated even
    # when the actual category rate is 0.03-0.07, so using it here can reject
    # profitable entries. All economics run on ask + the actual curve fee; only
    # the CLOB limit price stays at the ask (the exchange charges fee on top).
    # Delegate to pm_fees.py; do not reconstruct the curve in this entry path.
    fee_curve = pm_fees.fee_schedule(m)
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
    if maker_px is not None:
        cost_eff, fee_per_share = maker_px, 0.0
    else:
        fee_per_share = pm_fees.fee_per_share(m, mark)
        cost_eff = mark + fee_per_share
    if maker_px is not None:
        print(f"  [maker] gate + sizing run on the POSTED rest price {maker_px:.2f} "
              f"(bid {maker_bb:.3f} / ask {maker_ba if maker_ba is not None else '—'}), maker fee $0 "
              f"— not on ask+taker cost. Fill is not guaranteed; resting-order rules govern.")
    elif fee_per_share:
        source = "feeSchedule" if fee_curve.authoritative else "legacy fee field"
        print(f"  [fee] {source}: rate={fee_curve.rate:.4f}, exponent={fee_curve.exponent:g} "
              f"→ {fee_per_share*100:.2f}c/share taker fee; effective cost {cost_eff:.4f} "
              f"(ask {mark:.4f}) — gate + sizing run on effective cost")

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
                    _ofee = pm_fees.fee_per_share(m, _oask)
                    _ocost = _oask + _ofee
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
        # number; fee_per_share is already 0 on the maker path above.
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
