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
