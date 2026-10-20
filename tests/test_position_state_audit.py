"""Pending BUYs explain a prior only with immutable, exact market identity."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import position_state_audit as audit
import polyclaude_enter as enter


PRIOR = {"swift-album": {"condition_id": "0xcondition", "asset": "no-token"}}
BUY = {"slug": "swift-album", "conditionId": "0xcondition", "asset": "no-token",
       "orderId": "live-order", "remainingShares": 6.0}


def test_exact_live_partial_buy_explains_unheld_prior(monkeypatch):
    monkeypatch.setattr(enter, "_fetch_open_buy_commitments", lambda: [BUY])
    assert audit.orphan_prior_issues(PRIOR, set(), set()) == []


@pytest.mark.parametrize("changes", [
    {"slug": "swift-album-other"}, {"conditionId": "0xother"},
    {"asset": "yes-token"}, {"side": "SELL"},
])
def test_mismatch_or_sell_does_not_explain_prior(monkeypatch, changes):
    monkeypatch.setattr(enter, "_fetch_open_buy_commitments", lambda: [{**BUY, **changes}])
    assert any("PRIOR orphan" in issue for issue in audit.orphan_prior_issues(PRIOR, set(), set()))


def test_no_pending_order_retains_orphan(monkeypatch):
    monkeypatch.setattr(enter, "_fetch_open_buy_commitments", lambda: [])
    assert audit.orphan_prior_issues(PRIOR, set(), set()) == [
        "PRIOR orphan (no live position, no closure note): swift-album"
    ]


def test_complete_explicit_retirement_preserves_prior_without_orphan_warning(monkeypatch):
    retired = {"swift-album": {
        **PRIOR["swift-album"],
        "p_yes": 0.42,
        "retired": True,
        "retired_utc": "2026-10-20T09:47:42Z",
        "retired_reason": "Canceled with zero fills; no holding.",
    }}
    monkeypatch.setattr(
        enter, "_fetch_open_buy_commitments",
        lambda: pytest.fail("a fully retired historical prior needs no inventory read"),
    )
    assert audit.orphan_prior_issues(retired, set(), set()) == []


@pytest.mark.parametrize("retirement", [
    {"retired": True, "retired_reason": "closed"},
    {"retired": True, "retired_utc": "not-a-date", "retired_reason": "closed"},
    {"retired": True, "retired_utc": "2026-10-20T09:47:42", "retired_reason": "closed"},
    {"retired": True, "retired_utc": "2026-10-20T09:47:42Z", "retired_reason": "  "},
    {"retired": False, "retired_utc": "2026-10-20T09:47:42Z", "retired_reason": "closed"},
])
def test_incomplete_retirement_metadata_does_not_hide_orphan(monkeypatch, retirement):
    prior = {"swift-album": {**PRIOR["swift-album"], **retirement}}
    monkeypatch.setattr(enter, "_fetch_open_buy_commitments", lambda: [])
    assert any("PRIOR orphan" in issue
               for issue in audit.orphan_prior_issues(prior, set(), set()))


@pytest.mark.parametrize("retirement", [{}, {"retired": True}])
def test_null_note_does_not_abort_unretired_or_incomplete_prior(monkeypatch, retirement):
    prior = {"swift-album": {**PRIOR["swift-album"], "note": None, **retirement}}
    monkeypatch.setattr(enter, "_fetch_open_buy_commitments", lambda: [])
    assert any("PRIOR orphan" in issue
               for issue in audit.orphan_prior_issues(prior, set(), set()))


@pytest.mark.parametrize("bad_value", [True, "not-a-date", "2026-02-30"])
def test_criteria_read_bad_metadata_is_unknown_not_comparable(bad_value):
    date, issue = audit._criteria_read_date(bad_value)
    assert date == "1970-01-01"
    assert issue and "invalid criteria_read" in issue


def test_malformed_criteria_read_does_not_abort_claim_insurance_audit(
    monkeypatch, capsys
):
    today = audit.dt.date.today().isoformat()
    live = [
        {"slug": "held-a", "size": 2, "outcome": "Yes", "curPrice": 0.4,
         "asset": "asset-a", "endDate": "2027-12-31"},
        {"slug": "held-b", "size": 3, "outcome": "No", "curPrice": 0.6,
         "asset": "asset-b", "endDate": "2027-12-31"},
    ]
    priors = {
        "held-a": {"criteria_read": True},
        "held-b": {"criteria_read": today},
    }

    def load(name, default):
        return {
            "position_condition_ids.json": {"positions": []},
            ".uma_status_cache.json": {},
            "opportunity_triggers.json": [],
            "portfolio_kelly_priors.json": priors,
            "acknowledged_holds.json": [],
        }.get(name, default)

    monkeypatch.setattr(audit, "_live_positions", lambda: live)
    monkeypatch.setattr(audit, "_load", load)
    monkeypatch.setattr(sys, "argv", ["position_state_audit.py"])

    assert audit.main() == 1
    output = capsys.readouterr().out
    assert "invalid criteria_read value (bool)" in output
    assert "CRITERIA RE-READ due" in output
    assert "SNAPSHOT missing (no claim insurance!): held-a" in output
    assert "SNAPSHOT missing (no claim insurance!): held-b" in output


@pytest.mark.parametrize("changes", [
    {"remainingShares": 0}, {"remainingShares": float("nan")},
    {"orderId": ""}, {"side": "UNKNOWN"},
])
def test_invalid_inventory_never_partially_clears_orphan(monkeypatch, changes):
    monkeypatch.setattr(enter, "_fetch_open_buy_commitments", lambda: [BUY, {**BUY, **changes}])
    issues = audit.orphan_prior_issues(PRIOR, set(), set())
    assert any("inventory unavailable" in issue for issue in issues)
    assert any("PRIOR orphan" in issue for issue in issues)


def test_reader_failure_reports_unavailability_and_preserves_gap(monkeypatch):
    def unavailable():
        raise RuntimeError("mock unavailable / incomplete pagination")
    monkeypatch.setattr(enter, "_fetch_open_buy_commitments", unavailable)
    issues = audit.orphan_prior_issues(PRIOR, set(), set())
    assert len(issues) == 2
    assert "inventory unavailable" in issues[0]
    assert "PRIOR orphan" in issues[1]


@pytest.mark.parametrize("prior", [{}, {"condition_id": "0xcondition"}, {"asset": "no-token"}])
def test_prior_missing_immutable_identity_is_not_cleared(monkeypatch, prior):
    monkeypatch.setattr(enter, "_fetch_open_buy_commitments", lambda: [BUY])
    assert any("PRIOR orphan" in issue for issue in audit.orphan_prior_issues(
        {"swift-album": prior}, set(), set()))


@pytest.mark.parametrize("priors,tracked,inactive", [
    (PRIOR, {"swift-album-live-suffix"}, set()),
    (PRIOR, set(), {"swift-album"}),
    ({"swift-album": {"note": "closed"}}, set(), set()),
    ({"swift-album": {"note": "deliberate re-entry"}}, set(), set()),
    ({"_meta": {}}, set(), set()),
])
def test_existing_exemptions_do_not_read_authenticated_inventory(monkeypatch, priors, tracked, inactive):
    monkeypatch.setattr(enter, "_fetch_open_buy_commitments",
                        lambda: pytest.fail("unnecessary authenticated read"))
    assert audit.orphan_prior_issues(priors, tracked, inactive) == []
