#!/usr/bin/env python3
"""Fail-closed calibration for ``notes/shortdated_ledger.json``.

Resolution uses only an exact stored numeric ``market_id`` or exact stored
``slug``. Every supplied identity is checked against Gamma. A market is final
only when closed, UMA-resolved, and exactly binary YES/NO with complementary
0/1 outcome prices.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import httpx

LEDGER = Path(__file__).resolve().parent.parent / "notes" / "shortdated_ledger.json"
GAMMA = "https://gamma-api.polymarket.com/markets"
_ID = re.compile(r"^[0-9]+$")
_EPS = 1e-6


def _load_document() -> tuple[Any, list[Any]]:
    document = json.loads(LEDGER.read_text())
    if isinstance(document, list):
        return document, document
    if isinstance(document, dict) and isinstance(document.get("records"), list):
        return document, document["records"]
    raise ValueError("ledger must be a list or an object with a records list")


def _load() -> list[Any]:
    return _load_document()[1]


def _write_document(document: Any) -> None:
    LEDGER.write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n")


def _stored_id(rec: Mapping[str, Any]) -> str | None:
    values = [rec[k] for k in ("market_id", "marketId") if k in rec]
    if not values:
        return None
    if len(values) == 2 and str(values[0]) != str(values[1]):
        raise ValueError("conflicting market identifiers")
    value = values[0]
    if isinstance(value, bool):
        raise ValueError("market_id must be numeric")
    if isinstance(value, int):
        if value <= 0:
            raise ValueError("market_id must be positive")
        return str(value)
    if isinstance(value, str) and _ID.fullmatch(value.strip()):
        if int(value.strip()) <= 0:
            raise ValueError("market_id must be positive")
        return value.strip()
    raise ValueError("market_id must be a positive integer")


def _stored_condition(rec: Mapping[str, Any]) -> str | None:
    values = [rec[k] for k in ("condition_id", "conditionId") if k in rec]
    if not values:
        return None
    if len(values) == 2 and str(values[0]).lower() != str(values[1]).lower():
        raise ValueError("conflicting condition identifiers")
    value = values[0]
    if not isinstance(value, str) or not value.strip():
        raise ValueError("condition_id must be a nonempty string")
    return value.strip().lower()


def _stored_slug(rec: Mapping[str, Any]) -> str | None:
    if "slug" not in rec or rec.get("slug") is None:
        return None
    slug = rec.get("slug")
    if not isinstance(slug, str) or not slug.strip():
        raise ValueError("slug must be a nonempty string")
    return slug


def _market_for_record(rec: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str]:
    market_id = _stored_id(rec)
    slug = _stored_slug(rec)
    condition = _stored_condition(rec)
    if market_id is None and slug is None:
        return None, "no_identifier"
    if market_id is not None:
        response = httpx.get(f"{GAMMA}/{market_id}", timeout=20)
        if getattr(response, "status_code", None) == 404:
            return None, "missing"
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            if len(payload) != 1:
                return None, "ambiguous"
            payload = payload[0]
        if not isinstance(payload, dict):
            return None, "malformed"
        if str(payload.get("id")) != market_id:
            return None, "identity_mismatch"
    else:
        # The exact-by-slug endpoint works for closed markets; public search and
        # fuzzy question matching are intentionally never used.
        response = httpx.get(f"{GAMMA}/slug/{slug}", timeout=20)
        if getattr(response, "status_code", None) == 404:
            return None, "missing"
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            if len(payload) != 1:
                return None, "ambiguous" if len(payload) > 1 else "missing"
            payload = payload[0]
        if not isinstance(payload, dict):
            return None, "malformed"
    if slug is not None and payload.get("slug") != slug:
        return None, "identity_mismatch"
    returned_condition = payload.get("conditionId")
    if condition is not None and (
        not isinstance(returned_condition, str) or returned_condition.lower() != condition
    ):
        return None, "identity_mismatch"
    return payload, "ok"


def _final_outcome(market: Mapping[str, Any]) -> tuple[str | None, str]:
    if market.get("closed") is not True:
        return None, "unresolved"
    if market.get("umaResolutionStatus") != "resolved":
        return None, "unresolved"
    outcomes, prices = market.get("outcomes"), market.get("outcomePrices")
    try:
        if isinstance(outcomes, str):
            outcomes = json.loads(outcomes)
        if isinstance(prices, str):
            prices = json.loads(prices)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None, "malformed"
    if not isinstance(outcomes, list) or not isinstance(prices, list):
        return None, "malformed"
    if len(outcomes) != 2 or len(prices) != 2:
        return None, "malformed"
    labels = [x.casefold() if isinstance(x, str) else "" for x in outcomes]
    if sorted(labels) != ["no", "yes"]:
        return None, "malformed"
    parsed: list[float] = []
    for value in prices:
        if isinstance(value, bool):
            return None, "malformed"
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            return None, "malformed"
        if not math.isfinite(number) or not 0.0 <= number <= 1.0:
            return None, "malformed"
        parsed.append(number)
    if sorted(parsed) != [0.0, 1.0]:
        return None, "unresolved"
    return outcomes[parsed.index(1.0)].upper(), "ok"


def cmd_resolve(args: argparse.Namespace) -> int:
    document, recs = _load_document()
    counts: Counter[str] = Counter()
    for rec in recs:
        if not isinstance(rec, dict):
            counts["malformed"] += 1
            continue
        if rec.get("outcome") is not None:
            counts["already_outcome"] += 1
            continue
        if rec.get("side") not in ("YES", "NO"):
            counts["not_candidate"] += 1
            continue
        try:
            market, status = _market_for_record(rec)
        except (httpx.HTTPError, httpx.RequestError, OSError) as exc:
            counts["fetch_failed"] += 1
            print(f"  fetch failed: {str(exc)[:100]}", file=sys.stderr)
            continue
        except (TypeError, ValueError, KeyError):
            counts["malformed"] += 1
            continue
        if market is None:
            counts[status] += 1
            continue
        outcome, status = _final_outcome(market)
        if outcome is None:
            counts[status] += 1
            continue
        if not args.dry_run:
            rec["outcome"] = outcome
        counts["filled"] += 1
        print(f"  RESOLVED {outcome}: {rec.get('question') or rec.get('slug')}")
    if counts["filled"] and not args.dry_run:
        _write_document(document)
        print(f"wrote {LEDGER.name}")
    keys = ("filled", "already_outcome", "not_candidate", "no_identifier", "missing",
            "ambiguous", "identity_mismatch", "unresolved", "malformed", "fetch_failed")
    print("resolve: " + ", ".join(f"{key}={counts[key]}" for key in keys)
          + (" (dry-run; no write)" if args.dry_run else ""))
    return 0


def _probability(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) and 0.0 <= number <= 1.0 else None


def _market_p_yes(rec: Mapping[str, Any]) -> float | None:
    ask = _probability(rec.get("ask"))
    side = rec.get("side")
    if ask is None or side not in ("YES", "NO"):
        return None
    return ask if side == "YES" else 1.0 - ask


def _losses(p: float, y: float) -> tuple[float, float]:
    return (p - y) ** 2, -(y * math.log(max(p, _EPS))
                              + (1.0 - y) * math.log(max(1.0 - p, _EPS)))


def _score_records(recs: list[Any]) -> dict[str, Any]:
    own: list[dict[str, Any]] = []
    matched: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for rec in recs:
        if not isinstance(rec, dict):
            counts["malformed_row"] += 1
            continue
        p = _probability(rec.get("catalyst_p_yes_central"))
        if p is None:
            counts["missing_or_bad_forecast"] += 1
            continue
        out = rec.get("outcome")
        if out == "YES":
            y = 1.0
        elif out == "NO":
            y = 0.0
        elif out is None:
            counts["pending"] += 1
            continue
        elif isinstance(out, str) and out.startswith("PENDING"):
            counts["pending"] += 1
            continue
        else:
            counts["invalid_outcome"] += 1
            continue
        brier, log_loss = _losses(p, y)
        base = {"q": str(rec.get("question") or rec.get("slug") or "")[:48],
                "date": rec.get("date", ""), "my_p": p, "y": y,
                "brier_my": brier, "ll_my": log_loss}
        own.append(base)
        mp = _market_p_yes(rec)
        if mp is None:
            counts["missing_or_bad_market_baseline"] += 1
            continue
        mb, ml = _losses(mp, y)
        base.update({"mkt_p": mp, "brier_mkt": mb, "ll_mkt": ml})
        matched.append(base)
    return {"own": own, "matched": matched, "counts": counts}


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)


def cmd_score(_args: argparse.Namespace) -> int:
    _, recs = _load_document()
    result = _score_records(recs)
    own, matched, counts = result["own"], result["matched"], result["counts"]
    print(f"{'date':<11}{'my_p':>6}{'mkt_p':>7}{'out':>4}{'Bmy':>7}{'Bmkt':>7}  question")
    for row in own:
        market = f"{row['mkt_p']:.2f}" if "mkt_p" in row else "  n/a"
        bmkt = f"{row['brier_mkt']:>7.3f}" if "brier_mkt" in row else "    n/a"
        print(f"{str(row['date']):<11}{row['my_p']:>6.2f}{market:>7}{int(row['y']):>4}"
              f"{row['brier_my']:>7.3f}{bmkt}  {row['q']}")
    print(f"\nOwn cohort N={len(own)}; market-matched subset N={len(matched)}")
    print("Counts: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    if own:
        print(f"Own Brier {_mean(own, 'brier_my'):.4f}  log-loss {_mean(own, 'll_my'):.4f}")
    else:
        print("Own cohort: no valid forecast + final-outcome rows")
    if matched:
        bm, bk = _mean(matched, "brier_my"), _mean(matched, "brier_mkt")
        lm, lk = _mean(matched, "ll_my"), _mean(matched, "ll_mkt")
        print(f"Market comparison (matched only): Brier mine {bm:.4f} vs market {bk:.4f}"
              f"  skill {bk - bm:+.4f}")
        print(f"Market comparison (matched only): log-loss mine {lm:.4f} vs market {lk:.4f}"
              f"  skill {lk - lm:+.4f}")
    else:
        print("Market comparison: no valid historical ask/side baseline")
    print("NOTE: row count is not an independent-sample count; repeated updates and shared events can cluster outcomes.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    resolver = sub.add_parser("resolve", help="backfill only exact, finalized Gamma markets")
    resolver.add_argument("--dry-run", action="store_true")
    sub.add_parser("score", help="Brier/log-loss with separate own and market cohorts")
    args = ap.parse_args()
    return cmd_resolve(args) if args.cmd == "resolve" else cmd_score(args)


if __name__ == "__main__":
    sys.exit(main())
