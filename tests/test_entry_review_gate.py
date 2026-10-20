from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import clob_v2  # noqa: E402
import entry_review_gate as gate  # noqa: E402
import polyclaude_client  # noqa: E402


def _condition(index: int) -> str:
    return f"0x{index:064x}"


def _make_root(tmp_path: Path, *, valued: int = 600, blocked: int = 0,
               factual: int = 0, pending: int = 0,
               selection: dict | None = None) -> tuple[Path, str, str]:
    root = tmp_path
    queue = root / gate.QUEUE_REL
    queue.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(1, valued + blocked + factual + pending + 1):
        status = (
            "valued" if i <= valued else
            "blocked_after_review" if i <= valued + blocked else
            "excluded_factual" if i <= valued + blocked + factual else
            "pending"
        )
        rows.append({"index": i, "condition_id": _condition(i), "status": status})
    with queue.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["index", "condition_id", "status"])
        writer.writeheader()
        writer.writerows(rows)

    checkpoint = {
        "schema": "polyclaude.deep_review.v1",
        "queue": gate.QUEUE_REL.as_posix(),
        "universe": len(rows),
        "completed_valuations": valued,
        "blocked_after_in_depth_review": blocked,
        "factual_exclusions": factual,
        "pending": pending,
    }
    checkpoint_path = root / gate.CHECKPOINT_REL
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")

    if selection is not None:
        report_rel = "research/primary-comparison.md"
        report_path = root / report_rel
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("Primary comparative review\n", encoding="utf-8")
        report_hash = hashlib.sha256(report_path.read_bytes()).hexdigest()
        target_condition = _condition(1)
        target_token = "12345678901234567890"
        selection.update({
            "report": report_rel,
            "report_sha256": report_hash,
            "targets": [{"condition_id": target_condition, "token_id": target_token}],
        })
        rules_path = root / gate.RULES_REL
        rules_path.parent.mkdir(parents=True, exist_ok=True)
        rule = {
            "review_index": 1,
            "conditionId": target_condition,
            "clobTokenIds": json.dumps([target_token, "99999999999999999999"]),
        }
        with gzip.open(rules_path, "wt", encoding="utf-8") as stream:
            stream.write(json.dumps(rule) + "\n")

    policy_path = root / gate.POLICY_REL
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(json.dumps({
        "schema": gate.SCHEMA,
        "minimum_completed_valuations": gate.MINIMUM,
        "selection": selection,
    }), encoding="utf-8")
    return root, _condition(1), "12345678901234567890"


def _valid_selection() -> dict:
    return {
        "reviewed_utc": datetime.now(timezone.utc).isoformat(),
        "completed_valuations": 600,
    }


def test_blocked_and_factual_records_do_not_count_toward_600(tmp_path):
    root, _, _ = _make_root(tmp_path, valued=599, blocked=600, factual=10)
    with pytest.raises(gate.EntryReviewGateError, match="599/600"):
        gate.require_new_buy_allowed(root=root)


def test_600_valuations_alone_do_not_unlock_without_primary_selection(tmp_path):
    root, _, _ = _make_root(tmp_path, valued=600, blocked=15, factual=20)
    with pytest.raises(gate.EntryReviewGateError, match="selection is required"):
        gate.require_new_buy_allowed(root=root)


def test_valid_selection_unlocks_only_exact_frozen_selected_token(tmp_path):
    root, condition, token = _make_root(
        tmp_path, valued=600, blocked=3, selection=_valid_selection())
    assert gate.require_new_buy_allowed(root=root) is None
    assert gate.require_new_buy_allowed(token, root=root) is None
    with pytest.raises(gate.EntryReviewGateError, match="not a primary-selected"):
        gate.require_new_buy_allowed("00000000000000000000", root=root)


@pytest.mark.parametrize("target_index", [601, 602, 603])
def test_unvalued_target_is_rejected_even_if_in_frozen_rules(tmp_path, target_index):
    root, _, token = _make_root(
        tmp_path, valued=600, blocked=1, factual=1, pending=1, selection=_valid_selection())
    condition = _condition(target_index)
    policy_path = root / gate.POLICY_REL
    policy = json.loads(policy_path.read_text())
    policy["selection"]["targets"][0]["condition_id"] = condition
    policy_path.write_text(json.dumps(policy))
    rules_path = root / gate.RULES_REL
    with gzip.open(rules_path, "wt", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "review_index": target_index,
            "conditionId": condition,
            "clobTokenIds": json.dumps([token, "99999999999999999999"]),
        }) + "\n")
    with pytest.raises(gate.EntryReviewGateError, match="not a currently valued"):
        gate.require_new_buy_allowed(token, root=root)


@pytest.mark.parametrize("failure", ["missing_policy", "bool_count", "count_mismatch",
                                      "missing_report", "report_hash", "blank_report"])
def test_malformed_or_missing_authority_fails_closed(tmp_path, failure):
    root, _, _ = _make_root(tmp_path, valued=600, selection=_valid_selection())
    policy_path = root / gate.POLICY_REL
    checkpoint_path = root / gate.CHECKPOINT_REL
    policy = json.loads(policy_path.read_text())
    checkpoint = json.loads(checkpoint_path.read_text())
    if failure == "missing_policy":
        policy_path.unlink()
    elif failure == "bool_count":
        checkpoint["completed_valuations"] = True
        checkpoint_path.write_text(json.dumps(checkpoint))
    elif failure == "count_mismatch":
        checkpoint["completed_valuations"] = 599
        checkpoint_path.write_text(json.dumps(checkpoint))
    elif failure == "missing_report":
        policy["selection"]["report"] = "research/missing.md"
        policy_path.write_text(json.dumps(policy))
    elif failure == "blank_report":
        report_path = root / policy["selection"]["report"]
        report_path.write_text(" \n\t", encoding="utf-8")
        policy["selection"]["report_sha256"] = hashlib.sha256(
            report_path.read_bytes()).hexdigest()
        policy_path.write_text(json.dumps(policy))
    else:
        policy["selection"]["report_sha256"] = "0" * 64
        policy_path.write_text(json.dumps(policy))
    with pytest.raises(gate.EntryReviewGateError):
        gate.require_new_buy_allowed(root=root)


@pytest.mark.parametrize("selection_change,match", [
    ({"reviewed_utc": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()}, "future"),
    ({"reviewed_utc": datetime.now().replace(tzinfo=None).isoformat()}, "timezone"),
    ({"completed_valuations": 599}, "invalid selection valuation count"),
    ({"completed_valuations": 601}, "exceeds current valued count"),
])
def test_selection_requires_aware_current_time_and_valid_valuation_count(
        tmp_path, selection_change, match):
    root, _, token = _make_root(
        tmp_path, valued=600, selection=_valid_selection())
    policy_path = root / gate.POLICY_REL
    policy = json.loads(policy_path.read_text())
    policy["selection"].update(selection_change)
    policy_path.write_text(json.dumps(policy))
    with pytest.raises(gate.EntryReviewGateError, match=match):
        gate.require_new_buy_allowed(token, root=root)


def test_duplicate_or_wrong_frozen_target_is_rejected(tmp_path):
    root, _, token = _make_root(
        tmp_path, valued=600, selection=_valid_selection())
    policy_path = root / gate.POLICY_REL
    policy = json.loads(policy_path.read_text())
    policy["selection"]["targets"].append(dict(policy["selection"]["targets"][0]))
    policy_path.write_text(json.dumps(policy))
    with pytest.raises(gate.EntryReviewGateError, match="duplicate selected target"):
        gate.require_new_buy_allowed(token, root=root)

    policy["selection"]["targets"] = [{
        "condition_id": _condition(1), "token_id": "11111111111111111111",
    }]
    policy_path.write_text(json.dumps(policy))
    with pytest.raises(gate.EntryReviewGateError, match="does not match frozen"):
        gate.require_new_buy_allowed("11111111111111111111", root=root)


def test_cmd_buy_is_blocked_before_lock_claim_or_key_loading(monkeypatch, capsys):
    def denied(_token):
        raise gate.EntryReviewGateError("policy pause")
    monkeypatch.setattr(clob_v2, "require_new_buy_allowed", denied)
    for name in ("_acquire_reservation_lock", "_claim_buy_reservation", "_load_wallet"):
        monkeypatch.setattr(clob_v2, name,
                            lambda *a, **k: pytest.fail(f"{name} ran before gate"))
    args = SimpleNamespace(token_id="token", price=0.4, usd_size=4.0)
    assert clob_v2.cmd_buy(args) == 3
    assert "BUY blocked" in capsys.readouterr().err


def test_post_order_buy_is_blocked_before_wallet_or_credentials(monkeypatch):
    monkeypatch.setattr(clob_v2, "require_new_buy_allowed",
                        lambda *_: (_ for _ in ()).throw(gate.EntryReviewGateError("pause")))
    monkeypatch.setattr(clob_v2, "_load_wallet",
                        lambda: pytest.fail("wallet loaded before BUY gate"))
    with pytest.raises(gate.EntryReviewGateError, match="pause"):
        clob_v2.post_order({"side": clob_v2.SIDE_BUY, "tokenId": "token"})


def test_post_order_sell_remains_ungated(monkeypatch):
    monkeypatch.setattr(clob_v2, "require_new_buy_allowed",
                        lambda *_: pytest.fail("SELL must not consult the BUY gate"))
    monkeypatch.setattr(clob_v2, "_load_wallet", lambda: ("0xwallet", "unused"))
    monkeypatch.setattr(clob_v2, "_load_creds", lambda: {"api_key": "key"})
    monkeypatch.setattr(clob_v2, "_signed_order_to_api_body", lambda _signed: {"side": "SELL"})
    monkeypatch.setattr(clob_v2, "_hmac_headers", lambda *_args: {})
    monkeypatch.setattr(clob_v2.httpx, "post", lambda *_args, **_kwargs:
                        SimpleNamespace(status_code=400, json=lambda: {"error": "test"}))
    result = clob_v2.post_order({"side": clob_v2.SIDE_SELL, "tokenId": "token"})
    assert result["status_code"] == 400


def test_legacy_place_blocks_buy_before_signing_and_leaves_sell_ungated(monkeypatch):
    calls = []
    client = SimpleNamespace(
        create_order=lambda args: calls.append(("create", args.side)) or {"signed": True},
        post_order=lambda signed, **kwargs: calls.append(("post", kwargs["orderType"])) or {"ok": True},
    )
    pc = polyclaude_client.Polyclaude(wallet=None, w3=None, client=client)
    monkeypatch.setattr(polyclaude_client, "require_new_buy_allowed",
                        lambda *_: (_ for _ in ()).throw(gate.EntryReviewGateError("pause")))
    with pytest.raises(gate.EntryReviewGateError, match="pause"):
        pc._place("token", price=0.4, size=10, side=polyclaude_client.BUY,
                  gtc=True, post_only=False)
    assert calls == []
    assert pc._place("token", price=0.4, size=10, side=polyclaude_client.SELL,
                     gtc=True, post_only=False) == {"ok": True}
    assert [call[0] for call in calls] == ["create", "post"]
