#!/usr/bin/env python3
"""Sample a market's LIQUIDITY-REWARD band: is the qualifying zone really empty?

WHY THIS EXISTS (2026-08-25). The maker-rewards check found OpenAI-HLE-50
carrying a $20/day pool with ZERO qualifying depth inside its 4.5c band — a book
quoted 0.41/0.56 around a mid of 0.485, so the reward zone is a 14c void. That
is either a structural feature (nobody will quote inside a spread that wide on a
hidden-info market) or an artifact of the one minute I happened to look. Sizing
an entry on the second would be the single-window error the lessons file already
records twice: a point observation of a fast quantity is a lie with a timestamp.

So: sample it repeatedly, cheaply, and let the DISTRIBUTION decide. One gamma
call plus one book call per sample; appends a JSONL line; holds nothing in
memory. Reused at the Aug-31 window to reconcile the actual USDC payout against
the predicted share, which is the step that turns a plausible number into a
verified one (same discipline that corrected the fee formula).

Reward mechanics that matter for reading the output (docs, 2026-08-25):
  * order score is QUADRATIC in distance from mid, S = ((v - s) / v)^2 where
    v = maxSpread and s = the order's distance — so an order at the band EDGE
    scores ZERO. `depth_in_band` therefore OVERSTATES real competition: what
    matters is depth weighted toward the middle, which is why score_weighted is
    reported alongside it.
  * single-sided liquidity scores only while mid is inside [0.10, 0.90], and is
    penalised versus two-sided (~3x).

CLI:
  reward_band_sample.py --slug <slug> [--once] [--interval-s 900] [--hours 6]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parent.parent
LOG = REPO / "notes" / "reward_band_log.jsonl"
GAMMA = "https://gamma-api.polymarket.com/markets"
BOOK = "https://clob.polymarket.com/book"


def sample(slug: str, client: httpx.Client) -> dict | None:
    """One observation of the reward band. Returns None if the market or book
    is unreadable — a failed sample must not masquerade as an empty band."""
    try:
        m = client.get(GAMMA, params={"slug": slug}).json()[0]
    except Exception as e:
        print(f"  gamma fail: {e}", file=sys.stderr)
        return None
    rewards = m.get("clobRewards") or []
    daily = sum(float(x.get("rewardsDailyRate") or 0) for x in rewards)
    v = float(m.get("rewardsMaxSpread") or 0) / 100.0     # field is in CENTS
    min_size = float(m.get("rewardsMinSize") or 0)
    try:
        tok_yes, tok_no = json.loads(m["clobTokenIds"])
        b = client.get(BOOK, params={"token_id": tok_no}).json()
    except Exception as e:
        print(f"  book fail: {e}", file=sys.stderr)
        return None
    bids = sorted(((float(x["price"]), float(x["size"])) for x in b.get("bids", [])),
                  key=lambda x: -x[0])
    asks = sorted(((float(x["price"]), float(x["size"])) for x in b.get("asks", [])),
                  key=lambda x: x[0])
    if not bids or not asks:
        return {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "slug": slug, "empty_side": True, "pool_daily": daily}
    mid = (bids[0][0] + asks[0][0]) / 2.0

    def side(levels, is_bid):
        depth = weighted = 0.0
        for px, sz in levels:
            s = (mid - px) if is_bid else (px - mid)
            if 0 <= s <= v:
                depth += sz
                weighted += sz * ((v - s) / v) ** 2 if v else 0.0
        return depth, weighted

    bd, bw = side(bids, True)
    ad, aw = side(asks, False)
    return {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "slug": slug,
        "pool_daily": daily,
        "max_spread": v,
        "min_size": min_size,
        "mid": round(mid, 4),
        "best_bid": bids[0][0],
        "best_ask": asks[0][0],
        "spread": round(asks[0][0] - bids[0][0], 4),
        "depth_in_band": {"bid": round(bd, 2), "ask": round(ad, 2)},
        # score-weighted depth is the real denominator (edge orders score ~0)
        "score_weighted": {"bid": round(bw, 3), "ask": round(aw, 3)},
        "single_sided_scores": 0.10 <= mid <= 0.90,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--interval-s", type=float, default=900)
    ap.add_argument("--hours", type=float, default=6)
    a = ap.parse_args()
    deadline = time.time() + a.hours * 3600
    n = 0
    with httpx.Client(timeout=20) as c:
        while True:
            row = sample(a.slug, c)
            if row:
                with LOG.open("a") as f:
                    f.write(json.dumps(row) + "\n")
                n += 1
                sw = row.get("score_weighted", {})
                print(f"[{row['ts']}] mid {row.get('mid')} spread {row.get('spread')} "
                      f"band depth b/a {row.get('depth_in_band', {}).get('bid')}/"
                      f"{row.get('depth_in_band', {}).get('ask')} "
                      f"score-wt {sw.get('bid')}/{sw.get('ask')}", flush=True)
            if a.once or time.time() >= deadline:
                break
            time.sleep(a.interval_s)
    print(f"# {n} sample(s) -> {LOG.name}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
