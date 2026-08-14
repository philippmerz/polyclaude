#!/usr/bin/env python3
"""Scan held positions for marginal-APY-below-hurdle (close candidates).

Long-tail NOs as resolution approaches: when mark > 0.97 with 6+ months
remaining, the marginal APY drops below stablecoin yield. Lesson source:
2026-05-08 DEC-0001 (Jesus 2027 NO) closed at 2.5% marginal APY vs Aave
hurdle 3.4% — capital was better deployed elsewhere even at near-zero
P(YES) belief.

This script reads current PM positions via positions.py-style data-api
fetch and flags any whose marginal-yield-to-resolution APY falls below
the hurdle. Prints a structured advisory; does NOT close anything.

Two gates decide a flag, and BOTH matter (2026-08-14):
  1. EXPECTED edge vs the hurdle — p/M, not the win-assumed carry (1-M)/M.
  2. EXIT-COST GATE — a flag is only actionable if acting beats not acting,
     so the depth-walked exit (net of taker fee, redeployed at the hurdle) is
     compared against holding to resolution at my own prior, with a materiality
     floor of one $0.01 tick x size. Without this the scan called CLOSE_CANDIDATE
     on a leg whose mark had converged exactly onto my prior, where leaving cost
     $2.92 to escape $0.00 of negative edge.
The hurdle itself is now fetched live rather than hard-coded — see
HURDLE_APY_FALLBACK for why the constant was retired.

Used by:
- The 02:00/14:00 UTC daily_checkin.sh cron prompt (step 3 catalyst scan).
- Manual ad-hoc invocation when reviewing the book.

Usage:
    python scripts/check_marginal_apy.py              # live hurdle
    python scripts/check_marginal_apy.py --hurdle-apy 0.034   # pin it

Exit code: 0 (always — this is informational, never errors out trades).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import httpx

# Fallback hurdle only. This constant has now gone stale TWICE — 0.034 was a
# May-08 snapshot already wrong by the 2026-07-02 audit, and the 0.05 that
# replaced it read 1.4pp above the best rate available anywhere by 2026-08-14
# (Polygon 2.88 / Base 3.59 / Arbitrum 2.38). Hand-editing it a third time is
# choosing to be wrong again by October, so the live value is fetched below and
# this is just the floor when the chain is unreachable. Deliberately kept HIGH:
# if the fetch fails, over-stating the hurdle makes the scan flag MORE, and a
# spurious flag now costs one exit-cost-gate check while a missed one costs
# real carry.
HURDLE_APY_FALLBACK = 0.05

# Benchmark chain: freed Polymarket capital is pUSD on Polygon, so the yield it
# can reach WITHOUT a bridge is Aave-Polygon USDC. Base pays more (3.59% vs
# 2.88% on 2026-08-14) but getting there costs ~$0.50 of bridge against ~$0.34
# of annual pickup on a $28 float — so the higher number is not actually
# available to this capital and using it would overstate the hurdle.
#
# HONEST CAVEAT: no pUSD->USDC.e unwrap path exists today (wrap_pusd.py is
# one-way by design), so freed PM capital cannot literally reach Aave right
# now — it waits at 0% for the next bet. That makes this a FLOOR PROXY for
# "capital has somewhere better to be", not a literal opportunity cost. The
# real alternative to a held position is almost always ANOTHER position; Aave
# is the number that answers "is this leg worth the slot at all".
HURDLE_CHAIN = "polygon"
HURDLE_CACHE = Path(__file__).resolve().parent.parent / "notes" / "aave_hurdle.json"
HURDLE_TTL_HOURS = 24


def _live_hurdle() -> tuple[float, str]:
    """(hurdle_as_fraction, provenance). Cached 24h; falls back on any failure.

    web3 is imported lazily and only on a cache miss — this runs every tick on a
    memory-constrained box, and paying ~40MB of import to re-read a number that
    moves by basis points per day would be a poor trade.
    """
    now = dt.datetime.now(dt.timezone.utc)
    try:
        cached = json.loads(HURDLE_CACHE.read_text())
        age_h = (now - dt.datetime.fromisoformat(cached["fetched"])).total_seconds() / 3600
        if age_h < HURDLE_TTL_HOURS:
            return float(cached["apy"]), f"live {cached['apy']*100:.2f}% ({cached['chain']}, {age_h:.0f}h old)"
    except Exception:
        pass
    try:
        from web3 import Web3

        from aave_deposit import CHAIN, POOL_ABI, RAY, _w3
        cfg = CHAIN[HURDLE_CHAIN]
        w = _w3(HURDLE_CHAIN)
        pool = w.eth.contract(address=Web3.to_checksum_address(cfg["pool"]), abi=POOL_ABI)
        rd = pool.functions.getReserveData(
            Web3.to_checksum_address(cfg["tokens"]["USDC"])).call()
        apy = rd[2] / RAY          # index 2 = currentLiquidityRate, RAY-scaled
        if not (0.0 <= apy < 0.50):   # sanity-bound: a RAY misread shows up as absurd
            raise ValueError(f"implausible APY {apy}")
        HURDLE_CACHE.write_text(json.dumps(
            {"apy": round(apy, 6), "chain": HURDLE_CHAIN, "fetched": now.isoformat()}, indent=2))
        return apy, f"live {apy*100:.2f}% ({HURDLE_CHAIN}, fresh)"
    except Exception as e:
        return HURDLE_APY_FALLBACK, f"FALLBACK {HURDLE_APY_FALLBACK*100:.2f}% (live fetch failed: {str(e)[:40]})"

PRIORS_PATH = Path(__file__).resolve().parent.parent / "notes" / "portfolio_kelly_priors.json"

# Polymarket taker fee: 10% of min(p, 1-p) per share. Maker is $0, but an exit
# that needs to happen is a taker exit; pricing it as free understates the cost
# of acting on a flag.
TAKER_FEE_RATE = 0.10


def _exit_net(client: httpx.Client, slug: str, outcome: str, size: float) -> float | None:
    """Depth-walk the bid book and return net proceeds of exiting the FULL size.

    2026-08-14. The flag branch below used to shout CLOSE_CANDIDATE on edge
    alone, with no notion of what closing costs — the same error class as
    pricing a position at best-bid or at the midpoint: a single number standing
    in for an executable path. It flagged the MacBook NO leg the day its mark
    converged onto my own prior (expected edge exactly +0.00%), where exiting
    meant walking 66 shares down a book that had only 5 bid at the touch —
    $39.23 net against $42.90 of hold-to-fair value. Paying $3.67 to escape
    $0.00 of negative edge is value destruction dressed as discipline.
    Unfilled remainder counts as $0, matching positions.py.
    """
    try:
        m = client.get("https://gamma-api.polymarket.com/markets",
                       params={"slug": slug}).json()[0]
        toks = json.loads(m["clobTokenIds"])
        outs = json.loads(m["outcomes"])
        bk = client.get("https://clob.polymarket.com/book",
                        params={"token_id": toks[outs.index(outcome)]}).json()
        bids = sorted(bk.get("bids", []), key=lambda x: -float(x["price"]))
        left, proceeds = float(size), 0.0
        for lvl in bids:
            if left <= 0:
                break
            take = min(left, float(lvl["size"]))
            proceeds += take * float(lvl["price"])
            left -= take
        if proceeds <= 0:
            return None
        avg_fill = proceeds / float(size)
        fee = TAKER_FEE_RATE * min(avg_fill, 1.0 - avg_fill) * float(size)
        return proceeds - fee
    except Exception:
        return None


def _resolve_wallet_address() -> str:
    """Read the polymarket wallet address from the secret-paths config.

    Mirrors the pattern in scripts/clob_v2.py / scripts/positions.py.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import _paths as _secrets
    d = json.loads(_secrets.path("POLYCLAUDE_WALLET").read_text())
    return d["address"]


def _fetch_positions(addr: str) -> list[dict]:
    """Fetch current positions from Polymarket data-api.

    Matches scripts/positions.py: lowercase address, limit=100.
    """
    url = "https://data-api.polymarket.com/positions"
    r = httpx.get(url, params={"user": addr.lower(), "limit": "100"}, timeout=20)
    r.raise_for_status()
    return r.json() or []


def _days_to_resolution(end_iso: str | None) -> float | None:
    """Parse data-api endDate (variable formats: '2026-05-15' or
    '2026-05-15T00:00:00Z') and return days from now.
    """
    if not end_iso:
        return None
    try:
        # Handle both date-only ("2026-05-15") and full datetime forms
        normalized = end_iso.replace("Z", "+00:00")
        end = dt.datetime.fromisoformat(normalized)
        # If naive (date-only input), treat as UTC midnight
        if end.tzinfo is None:
            end = end.replace(tzinfo=dt.timezone.utc)
        now = dt.datetime.now(dt.timezone.utc)
        return (end - now).total_seconds() / 86400
    except Exception:
        return None


def _load_priors() -> dict[str, float]:
    """Load per-position P(win) priors from portfolio_kelly_priors.json.

    Returns {slug_key: p_no}. Keys in the priors file are market slugs.
    2026-07-02 audit fix: the old formula (1-M)/M x 365/days was WIN-ASSUMED
    (no P(loss) term) — any NO below ~0.983 cleared a 3.4% hurdle at 180d,
    so the daily "N/N clear" line carried no information. Expected-edge math
    (p/M - 1) is what the close-candidate decision actually needs.
    """
    try:
        raw = json.loads(PRIORS_PATH.read_text())
    except Exception:
        return {}
    out = {}
    for k, v in raw.items():
        if k.startswith("_"):
            continue
        # Side-aware (2026-07-16): the book now holds YES legs too (SpaceX,
        # Prime). A p_no prior must never be applied to a Yes holding and
        # vice versa — carry the side with the probability.
        if isinstance(v, dict) and "p_no" in v:
            out[k] = ("No", float(v["p_no"]), v.get("verified"))
        elif isinstance(v, dict) and "p_yes" in v:
            out[k] = ("Yes", float(v["p_yes"]), v.get("verified"))
    return out


def _stale_suffix(verified) -> str:
    """Warning suffix when a prior wasn't re-verified within 14d (2026-07-25:
    kimi went 3-for-3 catching stale-evidence priors — flags driven by old
    priors must say so)."""
    try:
        age = (dt.date.today() - dt.date.fromisoformat(str(verified))).days if verified else None
    except Exception:
        age = None
    if age is not None and age <= 14:
        return ""
    return f" [PRIOR-STALE: {'never-dated' if age is None else f'{age}d'} — re-verify before acting]"


def _load_acked_holds() -> dict:
    """Deliberate 'hold despite the flag' acknowledgments (2026-07-22). Without
    this, a position I consciously chose to hold (mark ≈ fair, imminent
    catalyst — e.g. Marvel-SDCC through the Jul-25 panel) re-flags NEGATIVE_EDGE
    every tick, and a low-context/headless tick could re-litigate or panic-sell
    a documented hold. The acknowledgment now travels WITH the flag.
    Format: notes/acknowledged_holds.json = [{"slug": <fragment>, "reason":
    <str>, "until": "YYYY-MM-DD"}]. Expired entries are ignored."""
    import datetime as _dt
    path = PRIORS_PATH.parent / "acknowledged_holds.json"
    out = []
    try:
        today = _dt.date.today().isoformat()
        for a in json.loads(path.read_text()):
            if a.get("until", "9999") >= today:
                out.append(a)
    except Exception:
        pass
    return out


def _acked(slug: str, acks: list) -> dict | None:
    for a in acks:
        frag = a.get("slug", "")
        if frag and (frag in slug or slug in frag):
            return a
    return None


def _match_prior(slug: str, priors: dict) -> tuple[str, float] | None:
    """Exact slug match first, then containment either way (slug variants).
    Returns (side, p_win) or None."""
    if not slug:
        return None
    if slug in priors:
        return priors[slug]
    for k, p in priors.items():
        if k in slug or slug in k:
            return p
    return None


def main() -> int:
    p = argparse.ArgumentParser(description="Flag held positions whose marginal-APY-to-resolution falls below a hurdle.")
    p.add_argument("--hurdle-apy", type=float, default=None,
                   help="hurdle APY. Default: LIVE Aave-Polygon USDC supply rate "
                        f"(24h cache, falls back to {HURDLE_APY_FALLBACK*100:.2f}%%). "
                        "Pass a value to pin it.")
    p.add_argument("--drawdown-alert-pct", type=float, default=15.0,
                   help="flag positions with mtm_loss_pct >= this value as DRAWDOWN_ALERT (default 15%%). "
                        "Lesson source: 2026-05-08 DEC-0018 -40%% in 30 min would have surfaced "
                        "automatically on the next cron tick had this existed.")
    p.add_argument("--json", action="store_true",
                   help="emit machine-readable JSON instead of the human table.")
    args = p.parse_args()
    if args.hurdle_apy is None:
        args.hurdle_apy, hurdle_src = _live_hurdle()
    else:
        hurdle_src = f"pinned {args.hurdle_apy*100:.2f}% (--hurdle-apy)"

    try:
        addr = _resolve_wallet_address()
    except Exception as e:
        print(f"ERROR: cannot resolve wallet: {e}", file=sys.stderr)
        return 0  # informational; never block

    try:
        positions = _fetch_positions(addr)
    except Exception as e:
        print(f"ERROR: data-api fetch failed: {e}", file=sys.stderr)
        return 0

    priors = _load_priors()
    acked_holds = _load_acked_holds()
    flagged: list[dict] = []
    holds: list[dict] = []
    drawdowns: list[dict] = []
    # Opened once for the exit-cost gate; only touched on the flag path, so a
    # tick where everything clears makes zero book calls.
    hc = httpx.Client(timeout=20.0)
    for pos in positions:
        size = float(pos.get("size", 0) or 0)
        if size <= 0:
            continue
        # Outcome: "Yes" or "No" (Polymarket convention)
        outcome = pos.get("outcome", "")
        # Mark: data-api returns `curPrice` (current execution-style mark)
        mark = float(pos.get("curPrice", 0) or 0)
        if mark <= 0 or mark >= 1:
            continue
        # Days to resolution
        days = _days_to_resolution(pos.get("endDate"))
        if days is None or days <= 0:
            continue

        question = pos.get("title", "(unknown)")
        slug = pos.get("slug", "")
        avg_price = float(pos.get("avgPrice", 0) or 0)
        cost = avg_price * size
        mtm = mark * size
        # Drawdown check: regardless of side, flag if MTM is materially
        # below cost. This catches today's DEC-0018-style 40% drawdown
        # automatically on every cron tick / manual run, not requiring
        # the operator to be in an active turn at the moment.
        # Lesson source: 2026-05-08 Russia-Ukraine NO crashed 0.768 -> 0.456
        # in ~30 min after Trump's 3-day-ceasefire announcement.
        drawdown_pct = (mtm - cost) / cost * 100 if cost > 0 else 0
        # De-indexed-market guard: when Polymarket de-indexes a market (e.g.,
        # post-rapid-mark-movement), data-api sometimes returns mark=0.001
        # (the minimum tick) even though the position is intact on-chain.
        # Without this guard, a de-indexed market would always fire DRAWDOWN
        # ALERT at -99.9%. Lesson source: 2026-05-09 07:52 UTC Russia-Ukraine
        # NO showed -99.9% drawdown via data-api while on-chain balance was
        # 25 NO shares intact.
        if mark <= 0.005 and drawdown_pct < -50:
            # Treat as de-indexed; suppress drawdown alert but flag for review
            drawdown_pct = None  # mark unreliable
        if drawdown_pct is not None and drawdown_pct <= -args.drawdown_alert_pct:
            drawdowns.append({
                "question": question,
                "slug": slug,
                "outcome": outcome,
                "mark": round(mark, 4),
                "avg_entry": round(avg_price, 4),
                "size": round(size, 4),
                "cost": round(cost, 4),
                "mtm": round(mtm, 4),
                "drawdown_pct": round(drawdown_pct, 2),
                "days_to_resolve": round(days, 2),
                "verdict": "DRAWDOWN_ALERT" if drawdown_pct <= -args.drawdown_alert_pct else "DRAWDOWN_WATCH",
            })

        # 2026-07-02 audit fix — EXPECTATION math, not win-assumed carry.
        # Gross carry (1-M)/M assumes the position always wins; the decision
        # number is expected edge: E[value per $ held] = p/M, so
        # expected_edge_apy = (p/M - 1) x 365/days, with p from the priors
        # file. p < M means holding is NEGATIVE-EV at your own belief —
        # flag regardless of hurdle. Gross carry is kept as a column only.
        # Gross carry (win-assumed) only means anything for bond-like marks;
        # EXPECTED edge (p/M - 1) is valid at ANY mark. 2026-07-16 fix: the
        # old `continue` on mark<0.5 silently dropped sub-0.5 legs (MacBook
        # NO 0.38, Prime YES 0.47) from the guard entirely — the guard walked
        # 7 of 9 held legs and reported "all clear".
        gross_carry_apy = (1.0 - mark) / mark * 365 / days if mark >= 0.5 else None

        matched = _match_prior(slug, priors)
        prior_p = matched[1] if matched and matched[0] == outcome else None
        prior_stale = _stale_suffix(matched[2]) if matched and matched[0] == outcome else ""
        expected_edge_apy = None
        if prior_p is not None:
            expected_edge_apy = (prior_p / mark - 1.0) * 365 / days

        if prior_p is None and gross_carry_apy is None:
            # No prior AND not bond-like: the advisory has no number to offer.
            # (Add a prior to portfolio_kelly_priors.json to cover such a leg.)
            print(f"  [UNCOVERED] {outcome} {mark:.3f} | {question[:60]} — "
                  f"sub-0.5 mark with no prior; add one to {PRIORS_PATH.name}",
                  file=sys.stderr)
            continue

        record = {
            "question": question,
            "slug": slug,
            "outcome": outcome,
            "mark": round(mark, 4),
            "prior_p": round(prior_p, 4) if prior_p is not None else None,
            "size": round(size, 4),
            "cost": round(cost, 4),
            "mtm": round(mtm, 4),
            "days_to_resolve": round(days, 2),
            "gross_carry_apy_pct": round(gross_carry_apy * 100, 2) if gross_carry_apy is not None else None,
            "expected_edge_apy_pct": round(expected_edge_apy * 100, 2) if expected_edge_apy is not None else None,
            "drawdown_pct": round(drawdown_pct, 2) if drawdown_pct is not None else None,
        }
        if expected_edge_apy is not None:
            ack = _acked(slug, acked_holds)
            if prior_p < mark or expected_edge_apy < args.hurdle_apy:
                # would-flag: NEGATIVE_EDGE (mark>prior) or below-hurdle
                base = "NEGATIVE_EDGE" if prior_p < mark else "CLOSE_CANDIDATE"
                if ack:
                    # deliberate documented hold — route to holds, not flagged,
                    # so a low-context tick sees the acknowledgment inline
                    record["verdict"] = (f"ACKED_HOLD until {ack.get('until','?')} "
                                         f"({base}): {ack.get('reason','')[:80]}")
                    holds.append(record)
                else:
                    # EXIT-COST GATE (2026-08-14). A flag is only actionable if
                    # acting beats not acting. Honest comparison: exit now and
                    # redeploy the proceeds at the hurdle until this market would
                    # have resolved, versus hold to resolution at my own prior.
                    # Anything less (comparing edge to zero, or exiting at the
                    # mark) treats an illiquid book as a free door.
                    net = _exit_net(hc, slug, outcome, size)
                    record["exit_net"] = round(net, 2) if net is not None else None
                    if net is not None:
                        redeployed = net * (1.0 + args.hurdle_apy * days / 365.0)
                        hold_value = size * prior_p
                        record["exit_then_hurdle"] = round(redeployed, 2)
                        record["hold_to_prior"] = round(hold_value, 2)
                        # Materiality floor = one price tick across the size
                        # being exited. Polymarket quotes in $0.01 increments,
                        # so a book snapshot pins exit proceeds to no better
                        # than size x $0.01 — and the fill happens later than
                        # the snapshot. Greenland first tripped this: "exit
                        # clears by $0.05" on a 29-share leg, i.e. a sixth of
                        # a tick. Acting on that is acting on noise.
                        tick_noise = size * 0.01
                        if redeployed <= hold_value + tick_noise:
                            margin = redeployed - hold_value
                            detail = (f"closing costs ${-margin:.2f}" if margin < 0
                                      else f"clears by only ${margin:.2f}, under ${tick_noise:.2f} tick-noise")
                            record["verdict"] = (
                                f"HOLD (exit-cost gate): {base} on edge, but exiting nets "
                                f"${net:.2f} -> ${redeployed:.2f} at hurdle vs ${hold_value:.2f} "
                                f"held to prior — {detail}")
                            holds.append(record)
                            continue
                        record["verdict"] = (f"{base}{prior_stale} — EXIT CLEARS COST: "
                                             f"${redeployed:.2f} vs ${hold_value:.2f} held")
                        flagged.append(record)
                        continue
                    record["verdict"] = base + prior_stale
                    flagged.append(record)
            else:
                record["verdict"] = "HOLD"
                holds.append(record)
        else:
            # No prior available: gross carry is the only number we have.
            # Mark it clearly so a win-assumed figure can't masquerade as EV.
            record["verdict"] = "NO_PRIOR (gross-carry only)"
            if gross_carry_apy < args.hurdle_apy:
                flagged.append(record)
            else:
                holds.append(record)

    if args.json:
        print(json.dumps({"hurdle_apy_pct": round(args.hurdle_apy * 100, 2),
                          "drawdown_alert_pct": args.drawdown_alert_pct,
                          "drawdowns": drawdowns,
                          "flagged": flagged, "holds": holds}, indent=2))
        return 0

    if drawdowns:
        print(f"!!! DRAWDOWN ALERTS — positions down ≥{args.drawdown_alert_pct:.0f}% on cost !!!")
        for r in sorted(drawdowns, key=lambda x: x["drawdown_pct"]):
            print(f"  {r['outcome']} entry={r['avg_entry']:.3f} mark={r['mark']:.3f} | "
                  f"cost=${r['cost']:.2f} mtm=${r['mtm']:.2f} | "
                  f"{r['drawdown_pct']:+.1f}% | {r['days_to_resolve']:>5.1f}d | "
                  f"{r['question'][:60]}")
        print()

    def _apy_col(r: dict) -> str:
        gross = r.get("gross_carry_apy_pct")
        gross_s = f"gross {gross:+.1f}%" if gross is not None else "non-bond mark"
        if r.get("expected_edge_apy_pct") is not None:
            return f"E{r['expected_edge_apy_pct']:>+7.2f}% (p={r['prior_p']:.3f}, {gross_s})"
        return f"gross {gross:>+7.2f}% (NO PRIOR)"

    print(f"# marginal-APY scan (EXPECTED-edge vs prior) @ {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}")
    print(f"# hurdle: {hurdle_src}; drawdown alert: {args.drawdown_alert_pct:.0f}%; priors: {PRIORS_PATH.name}")
    n_acked = sum(1 for r in holds if str(r.get("verdict","")).startswith("ACKED_HOLD"))
    print(f"# {len(holds)} clear ({n_acked} acked-hold); {len(flagged)} flagged (NEGATIVE_EDGE / below-hurdle)")
    print()
    if flagged:
        print("=== FLAGGED (negative edge at own prior, or expected edge < hurdle) ===")
        for r in flagged:
            print(f"  [{r['verdict']}] {r['outcome']} {r['mark']:.3f} | {r['days_to_resolve']:>5.1f}d | "
                  f"{_apy_col(r)}  {r['question'][:60]}")
        print()
    print("=== HOLDS (expected edge clears hurdle, or acknowledged deliberate holds) ===")
    for r in sorted(holds, key=lambda x: (x.get("expected_edge_apy_pct") if x.get("expected_edge_apy_pct") is not None else (x.get("gross_carry_apy_pct") or 0))):
        v = str(r.get("verdict",""))
        # A gated hold is NOT a clean hold — it is a position with no edge left
        # that is retained only because the door is expensive. Printing it bare
        # among the clearing holds is how a low-context tick concludes "all
        # fine" about a leg that is dead money. Show the reason inline.
        tag = f"  [{v}]" if v.startswith(("ACKED_HOLD", "HOLD (exit-cost gate)")) else ""
        print(f"  {r['outcome']} {r['mark']:.3f} | {r['days_to_resolve']:>5.1f}d | "
              f"{_apy_col(r)}  {r['question'][:52]}{tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
