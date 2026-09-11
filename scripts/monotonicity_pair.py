#!/usr/bin/env python3
"""Bounded execution path for a scanner-validated monotonicity pair.

For an early subset event A and later superset event B, BUY ``NO A`` and
``YES B``.  The two contracts pay at least one dollar in every outcome.  The
command is dry-run by default; ``--execute`` is an explicit opt-in.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import uuid
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pm_fees
import polyclaude_enter as entry
from event_monotonicity_scan import _parse_threshold_detail
from event_monotonicity_scan import _fetch_validated_clob_book
from gamma_market_lookup import GammaLookupError, lookup_active_market_identifier


def _list(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            return []
    return value if isinstance(value, list) else []


def _token(market: dict, outcome: str) -> str | None:
    outcomes, tokens = _list(market.get("outcomes")), _list(market.get("clobTokenIds"))
    if len(outcomes) != 2 or len(tokens) != 2:
        return None
    for name, token in zip(outcomes, tokens):
        if str(name).strip().casefold() == outcome.casefold() and str(token).strip():
            return str(token).strip()
    return None


def _criteria(market: dict) -> tuple[str, str, str]:
    description = str(market.get("description") or "").strip()
    source = str(market.get("resolutionSource") or "").strip()
    if not source:
        # Gamma commonly leaves resolutionSource empty while embedding the
        # authoritative source in the displayed criteria body.
        match = re.search(
            r"(?:^|\n)\s*(?:the\s+)?(?:primary\s+)?resolution source"
            r"(?:\s+for this market)?\s+(?:is|will be)\s+(.+?)(?:\n|$)",
            description,
            re.IGNORECASE,
        )
        source = " ".join(match.group(1).split()) if match else ""
    deadline = str(market.get("endDate") or market.get("endDateIso") or "").strip()
    detail = _parse_threshold_detail(str(market.get("question") or ""))
    if not source or not deadline or detail is None or not description:
        raise RuntimeError("missing exact resolution source/deadline/threshold criteria")
    # Threshold values are the sole intended difference; every other clause,
    # date window, fallback and source sentence must remain byte-comparable.
    template = " ".join(description.split()).casefold()
    return source.casefold(), deadline, template


def validate_pair_markets(early: dict, late: dict) -> dict:
    """Fail closed unless the two live Gamma markets are comparable siblings."""
    for label, market in (("early", early), ("late", late)):
        if (market.get("closed") is not False or market.get("active") is not True
                or market.get("enableOrderBook") is not True
                or market.get("acceptingOrders") is not True):
            raise RuntimeError(f"{label} market is not active")
        uma_status = str(market.get("umaResolutionStatus") or "").casefold()
        if uma_status in {"proposed", "disputed", "resolved"}:
            raise RuntimeError(f"{label} market has active UMA status")
        if _token(market, "YES") is None or _token(market, "NO") is None:
            raise RuntimeError(f"{label} market is not an unambiguous binary market")
    es, ed, et = _criteria(early)
    ls, ld, lt = _criteria(late)
    if es != ls:
        raise RuntimeError("resolution sources differ")
    if ed != ld:
        raise RuntimeError("resolution deadlines differ")
    if et != lt:
        raise RuntimeError("resolution criteria templates differ")
    event_sets = [entry._event_ids(early), entry._event_ids(late)]
    shared_events = set.intersection(*event_sets) if all(event_sets) else set()
    if not shared_events:
        raise RuntimeError("markets do not share a nonempty event ID")
    neg_risk = [market.get("negRisk") for market in (early, late)]
    if not all(isinstance(value, bool) for value in neg_risk) or len(set(neg_risk)) != 1:
        raise RuntimeError("markets do not share an explicit negRisk route")
    if (str(early.get("id") or "") == str(late.get("id") or "")
            or str(early.get("conditionId") or "").casefold()
            == str(late.get("conditionId") or "").casefold()):
        raise RuntimeError("pair identities are duplicated")
    ep = _parse_threshold_detail(early["question"])
    lp = _parse_threshold_detail(late["question"])
    # ``early`` is the logical subset whose NO is bought; ``late`` is the
    # superset whose YES is bought. For <= predicates that means a lower bar;
    # for >= predicates it means a higher bar. The non-threshold proposition
    # must also be identical so unrelated subjects in one event cannot pair.
    is_strict_subset = ep[1] * (ep[0] - lp[0]) > 0
    if (ep[3] != lp[3] or ep[2] != lp[2] or ep[1] != lp[1]
            or not is_strict_subset):
        raise RuntimeError("thresholds do not prove early subset / late superset order")
    return {"source": es, "deadline": ed, "template": et,
            "event_id": sorted(shared_events)[0], "neg_risk": neg_risk[0]}


def _leg_state(market: dict, outcome: str) -> dict:
    """Return fresh identity-, route-, fee-, and book-validated leg state."""
    condition = str(market.get("conditionId") or "")
    if not condition.startswith("0x"):
        raise RuntimeError("missing conditionId")
    info = entry._clob_market_info(condition)
    token = _token(market, outcome)
    clob_tokens = {str(x.get("token_id")): str(x.get("outcome") or "").casefold()
                   for x in info["full"].get("tokens", []) if isinstance(x, dict)}
    if not token or clob_tokens.get(token) != outcome.casefold():
        raise RuntimeError(f"CLOB token mismatch for {market.get('slug')}")
    if info["full"].get("neg_risk") is not market.get("negRisk"):
        raise RuntimeError(f"CLOB/Gamma negRisk mismatch for {market.get('slug')}")
    validated = _fetch_validated_clob_book(token, condition)
    if validated is None:
        raise RuntimeError(f"stale, uncrossed, or wrong-identity book for {market.get('slug')}")
    asks = sorted(
        ({"price": float(price), "size": float(size)}
         for price, size in validated["asks"]),
        key=lambda level: level["price"],
    )
    bids = sorted(
        ({"price": float(price), "size": float(size)}
         for price, size in validated["bids"]),
        key=lambda level: level["price"], reverse=True,
    )
    book = {
        "asks": asks, "bids": bids,
        "best_ask": asks[0]["price"] if asks else None,
        "best_bid": bids[0]["price"] if bids else None,
    }
    fee_market = entry._clob_fee_market(info)
    gamma_fee = pm_fees.fee_schedule(market)
    clob_fee = pm_fees.fee_schedule(fee_market)
    if (validated["min_order_size"] <= 0 or gamma_fee != clob_fee
            or not gamma_fee.authoritative):
        raise RuntimeError(f"invalid fee/book data for {market.get('slug')}")
    return {
        "market": market, "slug": market.get("slug") or "",
        "question": market.get("question") or "", "condition_id": condition,
        "token": token, "outcome": outcome, "book": book, "info": info,
        "fee_market": fee_market, "book_minimum": float(validated["min_order_size"]),
        "book_timestamp": validated["timestamp"],
        "neg_risk": market["negRisk"],
    }


def _build_leg(market: dict, outcome: str, shares: int) -> dict:
    leg = _leg_state(market, outcome)
    minimum = max(leg["book_minimum"], float(leg["info"]["minimum_order_size"]))
    if float(shares) + 1e-9 < minimum:
        raise RuntimeError(f"requested shares below CLOB minimum for {market.get('slug')}")
    ask = leg["book"]["best_ask"]
    if ask is None:
        raise RuntimeError(f"empty ask book for {market.get('slug')}")
    limit = entry._two_decimal_marketable_limit(
        ask, leg["info"]["minimum_tick_size"])
    depth = sum(float(level["size"]) for level in leg["book"]["asks"]
                if float(level["price"]) <= limit + 1e-12)
    if depth + 1e-9 < shares or not math.isfinite(depth):
        raise RuntimeError(
            f"only {depth:.2f} shares offered through {limit:.2f} for "
            f"{market.get('slug')}")
    fee_limit = pm_fees.max_taker_buy_cost_through(
        leg["fee_market"], limit) - limit
    leg.update({"ask": ask, "limit": limit, "depth": depth,
                "fee_at_limit": fee_limit})
    return leg


def _market_fingerprint(market: dict) -> tuple:
    outcomes = tuple(str(value).casefold() for value in _list(market.get("outcomes")))
    tokens = tuple(str(value) for value in _list(market.get("clobTokenIds")))
    market_id = str(market.get("id") or "")
    condition = str(market.get("conditionId") or "").casefold()
    if not market_id or not condition.startswith("0x") or len(outcomes) != 2 or len(tokens) != 2:
        raise RuntimeError("market fingerprint is incomplete")
    return market_id, condition, tuple(zip(outcomes, tokens))


def _pair_fingerprint(early: dict, late: dict) -> tuple:
    return _market_fingerprint(early), _market_fingerprint(late)


def _cap_states(legs: list[dict], positions: list[dict], pending: list[dict],
                bankroll: float, cluster: str, shares: int) -> list[dict]:
    states = []
    for leg in legs:
        state = entry._single_entry_cap_state(
            leg["market"], positions, bankroll,
            shares * (leg["limit"] + leg["fee_at_limit"]),
            0, pending, cluster_override=cluster)
        error = entry._single_entry_cap_error(state)
        if error:
            raise RuntimeError(f"{leg['slug']}: {error}")
        states.append(state)
    return states


def _refresh_pair(early_identifier: str, late_identifier: str,
                  expected_identity: dict,
                  expected_fingerprint: tuple) -> tuple[dict, dict]:
    early = lookup_active_market_identifier(early_identifier)
    late = lookup_active_market_identifier(late_identifier)
    identity = validate_pair_markets(early, late)
    if (identity != expected_identity
            or _pair_fingerprint(early, late) != expected_fingerprint):
        raise RuntimeError(
            "pair identity or resolution criteria changed during execution")
    return early, late


def _submission_leg(planned: dict, fresh_market: dict, shares: int) -> dict:
    """Refresh one leg immediately before signing without widening its limit."""
    current = _build_leg(fresh_market, planned["outcome"], shares)
    if (current["token"] != planned["token"]
            or current["condition_id"].casefold()
            != planned["condition_id"].casefold()
            or current["neg_risk"] != planned["neg_risk"]):
        raise RuntimeError("submission refresh changed leg identity or exchange route")
    if current["limit"] > planned["limit"] + 1e-12:
        raise RuntimeError(
            f"{planned['slug']} ask moved above reserved limit "
            f"{planned['limit']:.2f}")
    depth = sum(level["size"] for level in current["book"]["asks"]
                if level["price"] <= planned["limit"] + 1e-12)
    if depth + 1e-9 < shares:
        raise RuntimeError(
            f"{planned['slug']} has only {depth:.2f} fresh shares through "
            "its reserved limit")
    current["limit"] = planned["limit"]
    current["depth"] = depth
    current["fee_at_limit"] = (
        pm_fees.max_taker_buy_cost_through(
            current["fee_market"], planned["limit"])
        - planned["limit"])
    if current["fee_at_limit"] > planned["fee_at_limit"] + 1e-12:
        raise RuntimeError(
            f"{planned['slug']} fee increased above its reserved all-in cost")
    return current


def _rollback_refresh(leg: dict) -> dict:
    """Refresh a fixed filled token's metadata and book before an unwind."""
    fresh_market = lookup_active_market_identifier(leg["slug"])
    if _market_fingerprint(fresh_market) != _market_fingerprint(leg["market"]):
        raise RuntimeError("rollback refresh changed market identity")
    return _leg_state(fresh_market, leg["outcome"])


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--early", required=True, help="logical subset market slug/question")
    p.add_argument("--late", required=True, help="logical superset market slug/question")
    p.add_argument("--shares", type=int, required=True)
    p.add_argument("--max-cost", type=float, required=True,
                   help="hard signed total cost ceiling per equal-share pair")
    p.add_argument("--bankroll", type=float, default=None)
    p.add_argument("--cluster", required=True,
                   help="explicit correlation cluster for both legs")
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    if (args.shares <= 0 or not math.isfinite(args.max_cost)
            or not 0 < args.max_cost < 1):
        p.error("shares must be positive and max-cost must be finite and in (0,1)")
    if not args.cluster.strip():
        p.error("cluster must be nonempty")
    args.cluster = args.cluster.strip()
    bankroll = args.bankroll if args.bankroll is not None else entry._bankroll_default()
    if not math.isfinite(bankroll) or bankroll <= 0:
        p.error("bankroll must be finite and positive")

    try:
        early = lookup_active_market_identifier(args.early)
        late = lookup_active_market_identifier(args.late)
        identity = validate_pair_markets(early, late)
        fingerprint = _pair_fingerprint(early, late)
        legs = [_build_leg(early, "NO", args.shares),
                _build_leg(late, "YES", args.shares)]
        signed = sum(leg["limit"] + leg["fee_at_limit"] for leg in legs)
        if signed > args.max_cost + 1e-9:
            print(f"DECISION: SKIP — signed pair cost {signed:.6f} exceeds "
                  f"ceiling {args.max_cost:.6f}")
            return 0

        reader = entry._chain_reader(neg_risk=identity["neg_risk"])
        positions = entry._fetch_live_positions()
        open_buys = entry._fetch_open_buy_commitments()
        pending = entry._merge_entry_commitments(positions, open_buys)
        cap_states = _cap_states(
            legs, positions, pending, bankroll, args.cluster, args.shares)
        required = args.shares * signed
        if required > bankroll * 0.15 + 1e-9:
            print("DECISION: SKIP — combined pair exceeds 15% ticket cap")
            return 0
        cluster_before = max(state["cluster_before"] for state in cap_states)
        if cluster_before + required > bankroll * 0.30 + 1e-9:
            print("DECISION: SKIP — combined pair exceeds 30% cluster cap")
            return 0
        funds = entry._wallet_funds_state(reader, {leg["token"] for leg in legs})
        if (not funds["ctf_approved"] or funds["deployable"] + 1e-9 < required
                or funds["allowance"] + 1e-9 < funds["committed"] + required):
            print("DECISION: SKIP — pUSD funds or exchange approvals fail the "
                  "signed pair cost")
            return 0
        baselines = entry._read_token_balances(
            reader, [leg["token"] for leg in legs])
        unwind_cap = min(required * 0.20, bankroll * 0.01)
        execution_order = sorted(legs, key=lambda leg: -leg["depth"])
        entry._configure_rollback_guards(
            [execution_order[0], execution_order[0]], args.shares, unwind_cap)
        print(f"PAIR VALID: source={identity['source']} "
              f"deadline={identity['deadline']} signed_cost={signed:.6f}")
        if not args.execute:
            print("DECISION: WOULD_BUY_PAIR — dry-run; no orders sent")
            return 0

        lock = entry._acquire_entry_lock()
        try:
            # Rebuild every economic and portfolio input while holding the
            # cross-entry lock. The preview can never authorize these orders.
            fresh_early, fresh_late = _refresh_pair(
                args.early, args.late, identity, fingerprint)
            legs = [_build_leg(fresh_early, "NO", args.shares),
                    _build_leg(fresh_late, "YES", args.shares)]
            signed = sum(leg["limit"] + leg["fee_at_limit"] for leg in legs)
            if signed > args.max_cost + 1e-9:
                raise RuntimeError("final signed pair cost exceeds ceiling")
            required = args.shares * signed
            if required > bankroll * 0.15 + 1e-9:
                raise RuntimeError("final pair exceeds combined 15% ticket cap")

            positions = entry._fetch_live_positions()
            open_buys = entry._fetch_open_buy_commitments()
            pending = entry._merge_entry_commitments(positions, open_buys)
            cap_states = _cap_states(
                legs, positions, pending, bankroll, args.cluster, args.shares)
            cluster_before = max(state["cluster_before"] for state in cap_states)
            if cluster_before + required > bankroll * 0.30 + 1e-9:
                raise RuntimeError("final pair exceeds 30% cluster cap")
            funds = entry._wallet_funds_state(
                reader, {leg["token"] for leg in legs})
            if (not funds["ctf_approved"]
                    or funds["deployable"] + 1e-9 < required
                    or funds["allowance"] + 1e-9
                    < funds["committed"] + required):
                raise RuntimeError("final wallet funds/allowance/CTF gate failed")
            baselines = entry._read_token_balances(
                reader, [leg["token"] for leg in legs])
            execution_order = sorted(legs, key=lambda leg: -leg["depth"])
            unwind_cap = min(required * 0.20, bankroll * 0.01)
            entry._configure_rollback_guards(
                [execution_order[0], execution_order[0]],
                args.shares, unwind_cap)

            bundle_id = f"monotonicity-{uuid.uuid4().hex}"
            records = []
            for leg in legs:
                record = {
                    "conditionId": leg["condition_id"].lower(),
                    "slug": leg["slug"],
                    "question": leg["question"],
                    "eventIds": sorted(entry._event_ids(leg["market"])),
                    "asset": leg["token"],
                    "shares": float(args.shares),
                    "risk": float(args.shares
                                  * (leg["limit"] + leg["fee_at_limit"])),
                    "submissionState": "pending",
                    "bundleId": bundle_id,
                    "cluster": args.cluster,
                }
                record["baselineBought"] = entry._reservation_indexed_bought(
                    record, positions)
                records.append(record)
            ids = entry._add_entry_reservations(records)
            by_token = {
                leg["token"]: reservation_id
                for leg, reservation_id in zip(legs, ids, strict=True)
            }
            submitted_ids: set[str] = set()
            filled: list[dict] = []

            # Refresh each chosen book again at the last possible moment. A
            # current ask may improve, but this path never widens a reserved
            # price after cap, funds, and rollback checks.
            for planned in execution_order:
                try:
                    current_early, current_late = _refresh_pair(
                        args.early, args.late, identity, fingerprint)
                    if (planned["condition_id"].casefold()
                            == str(current_early["conditionId"]).casefold()):
                        fresh_market = current_early
                    elif (planned["condition_id"].casefold()
                          == str(current_late["conditionId"]).casefold()):
                        fresh_market = current_late
                    else:
                        raise RuntimeError("planned leg disappeared from exact pair")
                    leg = _submission_leg(planned, fresh_market, args.shares)
                    if not filled:
                        entry._configure_rollback_guards(
                            [leg, leg], args.shares, unwind_cap)
                except Exception as exc:
                    rollback_ok = (entry._rollback_bundle(
                        filled, baselines, reader,
                        refresh_leg=_rollback_refresh) if filled else True)
                    flat = (entry._wait_bundle_baselines(reader, baselines)
                            if rollback_ok else None)
                    all_flat = (flat is not None and all(
                        abs(flat[token] - expected) <= entry._BALANCE_TOL
                        for token, expected in baselines.items()))
                    cleanup = set(ids) if all_flat else set(ids) - submitted_ids
                    if cleanup:
                        entry._remove_entry_reservations(cleanup)
                    raise RuntimeError(
                        f"pre-sign refresh failed ({exc}); "
                        + ("prior leg restored to baseline" if all_flat
                           else "inspect retained filled-leg exposure"))

                reservation_id = by_token[planned["token"]]
                submitted_ids.add(reservation_id)
                state, raw_result = entry._run_clob_order(
                    "BUY", leg["token"], leg["limit"],
                    round(args.shares * leg["limit"], 2), args.shares,
                    reservation_id, neg_risk=leg["neg_risk"])
                _, parsed = entry._classify_clob_result(
                    raw_result, "BUY", args.shares)
                body = parsed.get("body") if isinstance(parsed, dict) else None
                order_id = (str(body.get("orderID") or "")
                            if isinstance(body, dict) else "")
                target = baselines[leg["token"]] + args.shares
                observed = entry._wait_token_balance(
                    reader, leg["token"], target)
                if (state == "matched" and observed is not None
                        and abs(observed - target) <= entry._BALANCE_TOL):
                    try:
                        entry._update_entry_reservation(
                            reservation_id, order_id,
                            submission_state="matched")
                    except Exception as exc:
                        try:
                            entry._remove_entry_reservations(
                                set(ids) - submitted_ids)
                        except Exception:
                            pass
                        print("CRITICAL: matched leg reservation update failed: "
                              f"{exc}", file=sys.stderr)
                        return 4
                    filled.append(leg)
                    continue

                unchanged = (observed is not None and
                             abs(observed - baselines[leg["token"]])
                             <= entry._BALANCE_TOL)
                if state == "failed" and unchanged:
                    rollback_ok = (entry._rollback_bundle(
                        filled, baselines, reader,
                        refresh_leg=_rollback_refresh) if filled else True)
                    flat = (entry._wait_bundle_baselines(reader, baselines)
                            if rollback_ok else None)
                    all_flat = (flat is not None and all(
                        abs(flat[token] - expected) <= entry._BALANCE_TOL
                        for token, expected in baselines.items()))
                    if all_flat:
                        entry._remove_entry_reservations(set(ids))
                        raise RuntimeError(
                            "pair leg definitively failed; prior leg restored")
                    filled_ids = {by_token[item["token"]] for item in filled}
                    entry._remove_entry_reservations(set(ids) - filled_ids)
                    raise RuntimeError(
                        "automatic unwind incomplete; inspect retained exposure")

                try:
                    entry._update_entry_reservation(
                        reservation_id, order_id,
                        submission_state="ambiguous")
                    entry._remove_entry_reservations(
                        set(ids) - submitted_ids)
                except Exception as cleanup_exc:
                    print("CRITICAL: ambiguous reservation update failed: "
                          f"{cleanup_exc}", file=sys.stderr)
                print("CRITICAL: ambiguous pair leg; no further orders or unwind",
                      file=sys.stderr)
                return 4

            final = entry._read_token_balances(
                reader, [leg["token"] for leg in legs])
            if any(abs(final[leg["token"]] - baselines[leg["token"]]
                       - args.shares) > entry._BALANCE_TOL for leg in legs):
                raise RuntimeError("final equal-share balance invariant failed")
            try:
                entry._merge_entry_commitments(
                    entry._fetch_live_positions(),
                    entry._fetch_open_buy_commitments(), prune=True)
            except Exception as exc:
                print(f"NOTICE: pair reservations await later reconciliation: {exc}",
                      file=sys.stderr)
            print(f"DECISION: BOUGHT_PAIR — {args.shares} equal shares; "
                  f"signed all-in ceiling {signed:.6f} per pair")
            return 0
        finally:
            lock.close()
    except (GammaLookupError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
