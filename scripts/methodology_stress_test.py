"""Methodology stress-test harness for skeptic+champion debate variants.

Runs N synthetic trade scenarios (built from resolved Polymarket markets,
which give us ground-truth resolutions) through M prompt-variant configurations
and scores which variant best calibrates against the actual outcomes.

Subcommands:
  scrape    — pull resolved Polymarket markets, build scenario set
  run       — for each (scenario, variant), spawn the debate, record output
  analyze   — aggregate results, compute calibration metrics per variant

Variants tested:
  A. ZERO-SHOT: single Haiku call with the scenario, asks for TAKE/SKIP
  B. PARALLEL: skeptic + champion monologues in parallel, then synthesize
  C. ADVERSARIAL: 3-round role-only debate (no convergence priming)

Output: data/methodology/scenarios.json + data/methodology/results_<ts>.jsonl

Goal per operator framing 2026-05-02: gain understanding of how to prompt
the architecture, not just hit a number. The transcripts + scores per
variant are the calibration product.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import random
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

import _paths as _secrets

_secrets.install_scrubbing_excepthook()

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
DATA_DIR = _REPO_ROOT / "data" / "methodology"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GAMMA = "https://gamma-api.polymarket.com"

# Variants
VARIANTS = ["zero_shot", "parallel_pair", "adversarial_3round",
            "unconscious_terse", "unconscious_demo"]


# ---------- scrape: build scenario set ----------------------------------

def fetch_resolved_markets(target: int = 300, max_pages: int = 20,
                            min_close_date: str = "2025-11-01") -> list[dict]:
    """Pull resolved Polymarket markets sorted by closedTime desc, filtering
    at fetch time to clean binary Yes/No markets after min_close_date."""
    out: list[dict] = []
    offset = 0
    seen = set()
    cutoff = dt.datetime.fromisoformat(min_close_date + "T00:00:00+00:00")
    pages_done = 0
    raw_seen = 0
    for _ in range(max_pages):
        try:
            r = httpx.get(
                f"{GAMMA}/markets",
                params={
                    "closed": "true",
                    "limit": "500",
                    "offset": str(offset),
                    "order": "closedTime",
                    "ascending": "false",
                },
                timeout=25,
            )
            r.raise_for_status()
            batch = r.json()
        except Exception as e:
            print(f"  page offset={offset} failed: {e}", file=sys.stderr)
            break
        if not batch:
            break
        pages_done += 1
        raw_seen += len(batch)
        post_cutoff_in_batch = 0
        for m in batch:
            mid = str(m.get("id"))
            if mid in seen:
                continue
            seen.add(mid)
            ct = m.get("closedTime")
            if ct:
                try:
                    ct_dt = dt.datetime.fromisoformat(ct.replace(" ", "T").replace("+00", "+00:00"))
                    if ct_dt < cutoff:
                        continue
                    post_cutoff_in_batch += 1
                except Exception:
                    pass
            # Pre-filter to binary-eligible to stop pulling more than needed
            if is_clean_binary(m):
                out.append(m)
        offset += len(batch)
        print(f"  page {pages_done}: cumulative raw={raw_seen}  passing={len(out)}", file=sys.stderr)
        if post_cutoff_in_batch == 0:
            print(f"  reached cutoff date; stopping", file=sys.stderr)
            break
        if len(out) >= target:
            break
        if len(batch) < 500:
            break
    return out


_SPORTS_PATTERNS = (
    " fc ", " fc:", " fc?", " afc ", " ufc ", " mlb ", " nhl ",
    " vs. ", " vs ", "spread:", "o/u ", "both teams to score",
    "points o/u", "rebounds o/u", "assists o/u", "first blood",
    "champions league", "premier league", "la liga", "bundesliga",
    "serie a", "uefa", "fifa world cup", "nba championship",
    "world series", "super bowl", "wimbledon", "open winner",
    "honor of kings", "counter-strike", "league of legends",
    "valorant", "dota", " bo3 ", " bo5 ",
)
_PRICE_PATTERNS = (
    " up or down ", "above $", "below $", "reach $", "hit $",
    "cross $", "close above", "close below",
    "gas price", "ethereum gas",
)


def is_clean_binary(m: dict) -> bool:
    """Filter to clean binary YES/NO markets with crisp resolution + reasonable
    description, excluding sports and short-tail crypto-price markets where
    pure reasoning provides no info advantage."""
    if m.get("negRisk"):
        return False
    if not m.get("question"):
        return False
    desc = m.get("description") or ""
    if len(desc) < 100:
        return False
    outs = m.get("outcomes")
    try:
        outs_l = json.loads(outs) if isinstance(outs, str) else outs
    except Exception:
        return False
    if not (isinstance(outs_l, list) and set(map(str, outs_l)) == {"Yes", "No"}):
        return False
    prices = m.get("outcomePrices")
    try:
        p = json.loads(prices) if isinstance(prices, str) else prices
    except Exception:
        return False
    if not (isinstance(p, list) and len(p) == 2):
        return False
    yes_final = float(p[0])
    no_final = float(p[1])
    if not ((abs(yes_final - 1.0) < 0.05 and no_final < 0.05) or
            (abs(no_final - 1.0) < 0.05 and yes_final < 0.05)):
        return False
    if float(m.get("volumeNum") or 0) < 5000:
        return False
    # Exclude sports / esports markets — reasoning provides no edge
    qlower = " " + (m.get("question") or "").lower() + " "
    cat = (m.get("category") or "").lower()
    if "sport" in cat or "esports" in cat:
        return False
    if any(pat in qlower for pat in _SPORTS_PATTERNS):
        return False
    # Exclude pure price-cross markets — short-tail probabilistic, no edge
    if any(pat in qlower for pat in _PRICE_PATTERNS):
        return False
    return True


def build_scenario(m: dict, rng: random.Random) -> dict | None:
    """For a clean resolved market, build a (question, description, simulated_price, truth) tuple.
    Simulated price uses a noisy plausible-pre-resolution price to make the test non-trivial."""
    prices = m.get("outcomePrices")
    p = json.loads(prices) if isinstance(prices, str) else prices
    yes_final = float(p[0])
    resolved_yes = yes_final > 0.5  # True if market resolved YES, False if NO

    # Generate a "decision price" for YES that makes the trade non-trivial.
    # Mix three regimes:
    #   30% near-truth (price agrees with eventual outcome) — agent should TAKE
    #   30% middle (uncertain) — context-dependent
    #   30% against-truth (price disagrees with eventual outcome) — agent should TAKE the contra side
    #   10% extreme outliers (test edge cases)
    regime = rng.random()
    if regime < 0.30:
        # Near-truth: price reflects the eventual outcome
        sim_yes = rng.uniform(0.85, 0.97) if resolved_yes else rng.uniform(0.03, 0.15)
    elif regime < 0.60:
        # Middle: ambiguous
        sim_yes = rng.uniform(0.30, 0.70)
    elif regime < 0.90:
        # Against-truth: market was "wrong" (good edge if you can see it)
        sim_yes = rng.uniform(0.55, 0.80) if not resolved_yes else rng.uniform(0.20, 0.45)
    else:
        # Extreme outlier
        sim_yes = rng.choice([rng.uniform(0.01, 0.05), rng.uniform(0.95, 0.99)])

    return {
        "market_id": str(m.get("id")),
        "question": m.get("question"),
        "description": (m.get("description") or "")[:1500],
        "category": m.get("category"),
        "simulated_yes_price": round(sim_yes, 3),
        "simulated_no_price": round(1 - sim_yes, 3),
        "days_to_resolution_at_snapshot": 30,  # synthetic
        "resolved_yes": resolved_yes,
        "ground_truth_outcome": "YES" if resolved_yes else "NO",
        "volume_num": float(m.get("volumeNum") or 0),
        "end_date": m.get("endDate"),
    }


def cmd_scrape(args: argparse.Namespace) -> int:
    print(f"fetching resolved Polymarket markets (target {args.target} cleaned, "
          f"min_close_date={args.min_close_date})...")
    raw = fetch_resolved_markets(target=args.target, max_pages=args.max_pages,
                                  min_close_date=args.min_close_date)
    print(f"  pulled {len(raw)} raw")

    rng = random.Random(args.seed)
    scenarios = []
    for m in raw:
        if not is_clean_binary(m):
            continue
        sc = build_scenario(m, rng)
        if sc:
            scenarios.append(sc)
        if len(scenarios) >= args.target:
            break

    out_path = DATA_DIR / "scenarios.json"
    out_path.write_text(json.dumps(scenarios, indent=2, default=str))
    print(f"  wrote {len(scenarios)} clean binary scenarios → {out_path}")

    # Quick distribution summary
    by_truth = {"YES": 0, "NO": 0}
    by_regime = {"near_truth": 0, "middle": 0, "against_truth": 0, "extreme": 0}
    for s in scenarios:
        by_truth[s["ground_truth_outcome"]] += 1
        sy = s["simulated_yes_price"]
        truth = s["resolved_yes"]
        if (truth and sy > 0.85) or (not truth and sy < 0.15):
            by_regime["near_truth"] += 1
        elif 0.30 <= sy <= 0.70:
            by_regime["middle"] += 1
        elif sy < 0.05 or sy > 0.95:
            by_regime["extreme"] += 1
        else:
            by_regime["against_truth"] += 1
    print(f"  by truth: {by_truth}")
    print(f"  by regime: {by_regime}")
    return 0


# ---------- variants: each takes a scenario, returns recommendation ----

def _haiku_call(prompt: str, timeout: int = 60) -> str:
    """Single claude -p haiku call. Returns stdout (trimmed) or error string."""
    try:
        r = subprocess.run(
            ["claude", "-p", "--model", "haiku", prompt],
            capture_output=True, text=True, timeout=timeout, cwd="/tmp",
        )
        return (r.stdout or "").strip()
    except subprocess.TimeoutExpired:
        return f"<timeout after {timeout}s>"
    except Exception as e:
        return f"<error: {_secrets.scrub(str(e))[:120]}>"


def _scenario_brief(s: dict, side: str = "NO") -> str:
    """Common scenario description shared by all variants."""
    price = s["simulated_no_price"] if side == "NO" else s["simulated_yes_price"]
    return (
        f"Polymarket market: {s['question']}\n\n"
        f"Resolution rules:\n{s['description']}\n\n"
        f"Snapshot context: this is a HISTORICAL scenario reconstructed for "
        f"evaluation. The market has since been resolved, but DO NOT try to look "
        f"up or recall the actual outcome — reason as you would have at the "
        f"time of the snapshot, before the event resolved. Snapshot price: "
        f"YES = {s['simulated_yes_price']}, NO = {s['simulated_no_price']}.\n\n"
        f"Trade under consideration: BUY {side} at {price}, $5 stake. "
        f"You decide TAKE or SKIP based on the information available in the snapshot."
    )


_HEDGE_TOKENS = (
    "NEED INFO", "INSUFFICIENT", "CAN'T", "CANNOT", "WON'T", "WONT",
    "ABSTAIN", "PASS", "DECLINE", "UNCLEAR", "UNCERTAIN", "MORE DATA",
    "DON'T HAVE", "NO POSITION", "HOLD",
)


def _parse_recommendation(text: str) -> dict:
    """Extract TAKE/SKIP recommendation from agent output.
    Looks for explicit verdict line first; falls back to scanning the tail;
    treats epistemic-hedge phrases as SKIP (refusing to commit = skip)."""
    verdict = None
    for line in text.splitlines():
        upper = line.upper()
        if "VERDICT:" in upper:
            if "TAKE" in upper:
                verdict = "TAKE"
            elif "SKIP" in upper:
                verdict = "SKIP"
            break
    if verdict is None:
        # Fallback: scan the last few lines for keywords
        last_chunk = "\n".join(text.splitlines()[-5:]).upper()
        if "TAKE" in last_chunk and "SKIP" not in last_chunk and "MISTAKE" not in last_chunk:
            verdict = "TAKE"
        elif "SKIP" in last_chunk and "TAKE" not in last_chunk:
            verdict = "SKIP"
        elif any(tok in last_chunk for tok in _HEDGE_TOKENS):
            # Epistemic hedge → treat as SKIP (refuses to commit = no trade)
            verdict = "SKIP"
        else:
            verdict = "UNPARSEABLE"
    return {"verdict": verdict, "raw": text[:2000]}


def variant_zero_shot(s: dict) -> dict:
    """Single Haiku call, no debate. Baseline."""
    brief = _scenario_brief(s, side="NO")
    prompt = (
        brief + "\n\n"
        "Decide: should I take this trade or skip?\n"
        "Reason in 3-5 sentences max, then end with EXACTLY one line:\n"
        "VERDICT: TAKE  OR  VERDICT: SKIP"
    )
    out = _haiku_call(prompt, timeout=60)
    return {**_parse_recommendation(out), "transcript": out, "calls": 1}


def variant_parallel_pair(s: dict) -> dict:
    """Skeptic + champion monologues in parallel, then synthesis."""
    brief = _scenario_brief(s, side="NO")
    skeptic_p = brief + "\n\nYou are the SKEPTIC. Argue AGAINST taking this trade. Terse, factual, ~150 words."
    champion_p = brief + "\n\nYou are the CHAMPION. Argue FOR taking this trade. Terse, factual, ~150 words."

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_s = ex.submit(_haiku_call, skeptic_p, 60)
        f_c = ex.submit(_haiku_call, champion_p, 60)
        sk = f_s.result()
        ch = f_c.result()

    synth_p = (
        brief + "\n\n"
        f"SKEPTIC argued:\n{sk}\n\n"
        f"CHAMPION argued:\n{ch}\n\n"
        "You are the moderator. Synthesize honestly across both — do NOT just split the difference. "
        "Decide: should I take this trade or skip?\n"
        "Reason in 3-5 sentences, then end with EXACTLY one line:\n"
        "VERDICT: TAKE  OR  VERDICT: SKIP"
    )
    synth = _haiku_call(synth_p, timeout=60)
    transcript = f"=== SKEPTIC ===\n{sk}\n\n=== CHAMPION ===\n{ch}\n\n=== SYNTHESIS ===\n{synth}"
    return {**_parse_recommendation(synth), "transcript": transcript, "calls": 3}


def variant_adversarial_3round(s: dict) -> dict:
    """Role-only 3-round debate, no convergence priming. Moderator synthesizes."""
    brief = _scenario_brief(s, side="NO")

    # Round 1
    sk_r1_p = brief + "\n\nYou argue AGAINST taking this trade. Make your strongest factual + logical case in good faith. ~150 words."
    ch_r1_p = brief + "\n\nYou argue FOR taking this trade. Make your strongest factual + logical case in good faith. ~150 words."
    with ThreadPoolExecutor(max_workers=2) as ex:
        sk_r1 = ex.submit(_haiku_call, sk_r1_p, 60).result()
        ch_r1 = ex.submit(_haiku_call, ch_r1_p, 60).result()

    # Round 2 — relay opposing
    sk_r2_p = (
        brief + f"\n\nYou argue AGAINST. Your R1 was:\n{sk_r1}\n\nOpposing R1:\n{ch_r1}\n\nRespond. ~150 words."
    )
    ch_r2_p = (
        brief + f"\n\nYou argue FOR. Your R1 was:\n{ch_r1}\n\nOpposing R1:\n{sk_r1}\n\nRespond. ~150 words."
    )
    with ThreadPoolExecutor(max_workers=2) as ex:
        sk_r2 = ex.submit(_haiku_call, sk_r2_p, 60).result()
        ch_r2 = ex.submit(_haiku_call, ch_r2_p, 60).result()

    # Round 3 — final position
    sk_r3_p = (
        brief + f"\n\nYou argue AGAINST. Prior:\nR1 you: {sk_r1}\nR1 them: {ch_r1}\n"
        f"R2 you: {sk_r2}\nR2 them: {ch_r2}\n\nFinal position. ~120 words."
    )
    ch_r3_p = (
        brief + f"\n\nYou argue FOR. Prior:\nR1 you: {ch_r1}\nR1 them: {sk_r1}\n"
        f"R2 you: {ch_r2}\nR2 them: {sk_r2}\n\nFinal position. ~120 words."
    )
    with ThreadPoolExecutor(max_workers=2) as ex:
        sk_r3 = ex.submit(_haiku_call, sk_r3_p, 60).result()
        ch_r3 = ex.submit(_haiku_call, ch_r3_p, 60).result()

    # Moderator synthesis
    synth_p = (
        brief + "\n\n"
        f"SKEPTIC R1: {sk_r1}\nSKEPTIC R2: {sk_r2}\nSKEPTIC R3: {sk_r3}\n\n"
        f"CHAMPION R1: {ch_r1}\nCHAMPION R2: {ch_r2}\nCHAMPION R3: {ch_r3}\n\n"
        "You are the moderator. Synthesize across all 3 rounds honestly. "
        "Decide: take or skip?\n"
        "Reason in 3-5 sentences, then end with EXACTLY one line:\n"
        "VERDICT: TAKE  OR  VERDICT: SKIP"
    )
    synth = _haiku_call(synth_p, timeout=90)
    transcript = (
        f"=== SKEPTIC R1 ===\n{sk_r1}\n=== CHAMPION R1 ===\n{ch_r1}\n"
        f"=== SKEPTIC R2 ===\n{sk_r2}\n=== CHAMPION R2 ===\n{ch_r2}\n"
        f"=== SKEPTIC R3 ===\n{sk_r3}\n=== CHAMPION R3 ===\n{ch_r3}\n"
        f"=== SYNTHESIS ===\n{synth}"
    )
    return {**_parse_recommendation(synth), "transcript": transcript, "calls": 7}


def variant_unconscious_terse(s: dict) -> dict:
    """Stylistic mirroring — prompt itself is terse factual prose; no role
    labels, no word caps, no anti-padding directives, no 'reason in N sentences'.
    Tests operator's hypothesis (2026-05-02) that unconscious priming via
    context shape produces deeper behavior change than explicit constraints.

    Note: a minimal explicit format directive ('Verdict: TAKE or SKIP') is
    retained because pilot 3 found that without it, agents retreat into
    epistemic hedging ('NEED INFO', 'can't give financial advice') and
    refuse to commit. Format compliance and style priming are separable
    dimensions; this variant tests the latter, holding the former fixed."""
    yes_price = s["simulated_yes_price"]
    no_price = s["simulated_no_price"]
    prompt = (
        f"Polymarket: \"{s['question']}\"\n\n"
        f"Resolution rules:\n{s['description']}\n\n"
        f"Snapshot: YES {yes_price}, NO {no_price}. Historical scenario "
        f"reconstructed for evaluation; reason as you would have at the time, "
        f"without trying to recall the actual outcome.\n\n"
        f"Considering BUY NO at {no_price}, $5 stake.\n\n"
        f"Final line of your response must be exactly: VERDICT: TAKE  or  VERDICT: SKIP"
    )
    out = _haiku_call(prompt, timeout=60)
    return {**_parse_recommendation(out), "transcript": out, "calls": 1}


def variant_unconscious_demo(s: dict) -> dict:
    """Two-shot demonstration — show one TAKE example + one SKIP example with
    reasoned analysis, then present the new case. Primes analytical style
    without explicit role/anti-padding directives. Examples balanced so the
    verdict isn't directionally biased."""
    yes_price = s["simulated_yes_price"]
    no_price = s["simulated_no_price"]

    examples = (
        "Polymarket: \"Will the SEC approve a new ETH ETF before March 1, 2026?\"\n"
        "Snapshot: YES 0.06, NO 0.94. Considering BUY NO at 0.94.\n"
        "Analysis: spot ETH ETFs were approved May 2024 with options layered later. "
        "A NEW ETF approval before March is a regulatory-rulemaking question, not "
        "a market-mood one. The SEC pipeline takes months; March is 60d out, no "
        "registered S-1 in known review at filing-date deadline. 6% YES feels generous "
        "absent any visible filing. NO at 0.94 buys a small but defensible edge.\n"
        "Verdict: TAKE.\n\n"
        "---\n\n"
        "Polymarket: \"Will Bitcoin end Q1 2026 above $130k?\"\n"
        "Snapshot: YES 0.42, NO 0.58. Considering BUY NO at 0.58.\n"
        "Analysis: BTC trajectory in Q1 is fundamentally uncertain — rate decisions, "
        "ETF flows, halving cycle dynamics, macro all in play. Market price 42% YES "
        "is roughly fair given the spread of plausible outcomes. NO at 0.58 isn't "
        "obviously cheap; it's near-fair. Without a specific thesis on why BTC misses "
        "$130k, this is taking the consensus side at consensus price.\n"
        "Verdict: SKIP.\n\n"
        "---\n\n"
    )

    new_case = (
        f"Polymarket: \"{s['question']}\"\n"
        f"Resolution rules:\n{s['description']}\n\n"
        f"Snapshot: YES {yes_price}, NO {no_price}. Considering BUY NO at {no_price}, $5 stake.\n"
        f"Analysis: <your analysis>\n"
        f"Final line of your response must be exactly: VERDICT: TAKE  or  VERDICT: SKIP"
    )

    prompt = examples + new_case
    out = _haiku_call(prompt, timeout=60)
    return {**_parse_recommendation(out), "transcript": out, "calls": 1}


VARIANT_FUNCS = {
    "zero_shot": variant_zero_shot,
    "parallel_pair": variant_parallel_pair,
    "adversarial_3round": variant_adversarial_3round,
    "unconscious_terse": variant_unconscious_terse,
    "unconscious_demo": variant_unconscious_demo,
}


# ---------- run + analyze ------------------------------------------------

def _classify_regime(s: dict) -> str:
    """Classify a scenario by its simulated-price regime relative to ground truth.
    Same buckets used at scenario-build time."""
    truth = s["resolved_yes"]
    sy = s["simulated_yes_price"]
    if (truth and sy > 0.85) or (not truth and sy < 0.15):
        return "near_truth"
    if 0.30 <= sy <= 0.70:
        return "middle"
    if sy < 0.05 or sy > 0.95:
        return "extreme"
    return "against_truth"


def _run_one(s: dict, v: str) -> tuple[dict, dict]:
    """Run variant `v` on scenario `s`, return (rec, raw_res)."""
    t0 = time.time()
    fn = VARIANT_FUNCS[v]
    try:
        res = fn(s)
    except Exception as e:
        res = {"verdict": "ERROR", "transcript": str(e)[:500], "calls": 0}
    elapsed = time.time() - t0
    rec = {
        "scenario_id": s["market_id"],
        "question": s["question"][:120],
        "variant": v,
        "yes_price": s["simulated_yes_price"],
        "ground_truth": s["ground_truth_outcome"],
        "regime": _classify_regime(s),
        "verdict": res["verdict"],
        "calls": res["calls"],
        "seconds": round(elapsed, 1),
        "transcript": res["transcript"],
    }
    return rec, res


def cmd_run(args: argparse.Namespace) -> int:
    scenarios_path = DATA_DIR / "scenarios.json"
    if not scenarios_path.exists():
        print(f"missing {scenarios_path} — run scrape first", file=sys.stderr)
        return 2
    scenarios = json.loads(scenarios_path.read_text())
    rng = random.Random(args.seed)
    if args.n > 0 and args.n < len(scenarios):
        sample = rng.sample(scenarios, args.n)
    else:
        sample = scenarios

    variants = args.variants or VARIANTS
    total = len(sample) * len(variants)
    print(f"running {len(sample)} scenarios × {len(variants)} variants = {total} debates "
          f"(parallel={args.parallel})")

    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = DATA_DIR / f"results_{ts}.jsonl"
    print(f"writing → {out_path}")

    # Build the workqueue
    work = [(s, v) for s in sample for v in variants]

    started = time.time()
    completed = 0
    with out_path.open("w") as f:
        if args.parallel <= 1:
            # Sequential
            for s, v in work:
                rec, _ = _run_one(s, v)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
                completed += 1
                rate = completed / max(time.time() - started, 1)
                eta = (total - completed) / max(rate, 1e-6)
                print(f"  [{completed}/{total}] {v:<20} {rec['verdict']:<12} "
                      f"{rec['seconds']:>5.1f}s  eta {eta/60:.1f}m  {s['question'][:50]}")
        else:
            # Parallel across (scenario, variant) work items
            with ThreadPoolExecutor(max_workers=args.parallel) as ex:
                futures = {ex.submit(_run_one, s, v): (s, v) for s, v in work}
                for fut in as_completed(futures):
                    s, v = futures[fut]
                    try:
                        rec, _ = fut.result()
                    except Exception as e:
                        rec = {
                            "scenario_id": s["market_id"], "question": s["question"][:120],
                            "variant": v, "yes_price": s["simulated_yes_price"],
                            "ground_truth": s["ground_truth_outcome"],
                            "regime": _classify_regime(s),
                            "verdict": "ERROR", "calls": 0, "seconds": 0,
                            "transcript": str(e)[:500],
                        }
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
                    completed += 1
                    rate = completed / max(time.time() - started, 1)
                    eta = (total - completed) / max(rate, 1e-6)
                    print(f"  [{completed}/{total}] {v:<20} {rec['verdict']:<12} "
                          f"{rec['seconds']:>5.1f}s  eta {eta/60:.1f}m  {s['question'][:50]}")
    print(f"\ndone in {(time.time() - started)/60:.1f}m → {out_path}")
    return 0


def _ev_per_dollar(verdict: str, yes_price: float, ground_truth: str, side: str = "NO") -> float:
    """Compute realized P&L per $1 stake, for buying SIDE at simulated price.
    Verdict TAKE = $5 stake on SIDE; SKIP = $0; UNPARSEABLE/ERROR = $0."""
    if verdict != "TAKE":
        return 0.0
    no_price = 1 - yes_price
    if side == "NO":
        # Bought NO at no_price. Win 1.0 if ground_truth is NO; lose if YES.
        return (1.0 - no_price) if ground_truth == "NO" else (-no_price)
    else:
        return (1.0 - yes_price) if ground_truth == "YES" else (-yes_price)


def cmd_analyze(args: argparse.Namespace) -> int:
    # Find results file(s)
    files = sorted(DATA_DIR.glob("results_*.jsonl"), key=lambda p: p.stat().st_mtime)
    if args.paths:
        paths = [Path(p) for p in args.paths]
    elif args.merge_all:
        paths = files
    elif files:
        paths = [files[-1]]
    else:
        print("no results files found — run `run` first", file=sys.stderr)
        return 2

    print(f"analyzing {[p.name for p in paths]}\n")
    rows = []
    for p in paths:
        rows.extend(json.loads(l) for l in p.read_text().splitlines() if l.strip())
    by_variant: dict[str, list[dict]] = {}
    for r in rows:
        by_variant.setdefault(r["variant"], []).append(r)

    print(f"{'variant':<22} {'n':>4} {'TAKE':>5} {'SKIP':>5} {'BAD':>4} "
          f"{'avg PnL/$':>10} {'win%':>6} {'avg calls':>9} {'avg sec':>8}")
    print("-" * 90)
    for v, rs in by_variant.items():
        take = sum(1 for r in rs if r["verdict"] == "TAKE")
        skip = sum(1 for r in rs if r["verdict"] == "SKIP")
        bad = sum(1 for r in rs if r["verdict"] not in ("TAKE", "SKIP"))
        if take == 0:
            avg_pnl = 0.0
            win_pct = 0.0
        else:
            taken = [r for r in rs if r["verdict"] == "TAKE"]
            pnls = [_ev_per_dollar(r["verdict"], r["yes_price"], r["ground_truth"], side="NO") for r in taken]
            avg_pnl = sum(pnls) / len(pnls)
            wins = sum(1 for p in pnls if p > 0)
            win_pct = 100 * wins / len(pnls)
        avg_calls = sum(r["calls"] for r in rs) / max(len(rs), 1)
        avg_sec = sum(r["seconds"] for r in rs) / max(len(rs), 1)
        print(f"{v:<22} {len(rs):>4} {take:>5} {skip:>5} {bad:>4} "
              f"{avg_pnl:>+9.4f}  {win_pct:>5.1f}%  {avg_calls:>9.1f} {avg_sec:>7.1f}s")

    # Per-regime breakdown — which variant is best on which scenario type?
    print("\n=== per-regime P&L per dollar staked (TAKE only; SKIP = 0) ===")
    regimes_seen = sorted({r.get("regime") or "unknown" for r in rows})
    print(f"{'variant':<22} " + " ".join(f"{rg[:13]:>13}" for rg in regimes_seen))
    for v, rs in by_variant.items():
        cells = []
        for rg in regimes_seen:
            sub = [r for r in rs if r.get("regime") == rg]
            if not sub:
                cells.append(f"{'-':>13}")
                continue
            takes = [r for r in sub if r["verdict"] == "TAKE"]
            if not takes:
                # Show (n_take/n) and skip-only
                cells.append(f"{0}/{len(sub)} skip ".rjust(13))
                continue
            pnls = [_ev_per_dollar(r["verdict"], r["yes_price"], r["ground_truth"]) for r in takes]
            avg = sum(pnls) / len(pnls)
            cells.append(f"{avg:+.3f}({len(takes)}/{len(sub)})".rjust(13))
        print(f"{v:<22} " + " ".join(cells))

    # Where did variants disagree?
    print("\n=== disagreements (same scenario, different verdict across variants) ===")
    by_scenario: dict[str, dict] = {}
    for r in rows:
        by_scenario.setdefault(r["scenario_id"], {})[r["variant"]] = (r["verdict"], r.get("regime", "?"), r["ground_truth"])
    disagreements = 0
    for sid, verdicts in by_scenario.items():
        vals = set(v[0] for v in verdicts.values())
        if len(vals) > 1:
            disagreements += 1
    print(f"  {disagreements}/{len(by_scenario)} scenarios had ≥2 variants disagreeing on verdict")

    # Agreement against ground truth
    # For each scenario, was the dominant verdict correct?
    print("\n=== majority-verdict accuracy (per scenario, ignoring SKIP) ===")
    correct_take = 0
    correct_skip = 0
    incorrect_take = 0
    incorrect_skip = 0
    for sid, verdicts in by_scenario.items():
        takes = sum(1 for v in verdicts.values() if v[0] == "TAKE")
        skips = sum(1 for v in verdicts.values() if v[0] == "SKIP")
        truth = next(iter(verdicts.values()))[2]
        # If majority TAKE → effective verdict = TAKE (else SKIP)
        if takes > skips:
            if truth == "NO":
                correct_take += 1
            else:
                incorrect_take += 1
        else:
            if truth == "NO":
                incorrect_skip += 1
            else:
                correct_skip += 1
    print(f"  majority-TAKE → won: {correct_take}, lost: {incorrect_take}")
    print(f"  majority-SKIP → missed-winner: {incorrect_skip}, avoided-loss: {correct_skip}")

    return 0


# ---------- main --------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("scrape", help="pull resolved markets, build scenarios.json")
    p.add_argument("--target", type=int, default=100, help="target number of clean scenarios")
    p.add_argument("--max-pages", type=int, default=40, help="max gamma-api pages to scan")
    p.add_argument("--min-close-date", default="2025-11-01",
                   help="only include markets that resolved on/after this date (Haiku cutoff)")
    p.add_argument("--seed", type=int, default=42)
    p.set_defaults(fn=cmd_scrape)

    p = sub.add_parser("run", help="run variants on N scenarios")
    p.add_argument("--n", type=int, default=10, help="sample size (0 = all)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--variants", nargs="+", choices=VARIANTS, default=None)
    p.add_argument("--parallel", type=int, default=1,
                   help="run this many (scenario, variant) work items concurrently")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("analyze", help="aggregate latest results")
    p.add_argument("--paths", nargs="+", help="specific result files (default: latest)")
    p.add_argument("--merge-all", action="store_true", help="merge all results files in data dir")
    p.set_defaults(fn=cmd_analyze)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
