"""Focused regressions for set-only live-position integrity."""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import position_state_audit as audit  # noqa: E402


SET_LABEL = "DEC-test equal-share range"


def _priors(*slugs: str) -> dict:
    return {
        slug: {
            "p_yes": 0.3,
            "set_only": SET_LABEL,
            "criteria_read": dt.date.today().isoformat(),
        }
        for slug in slugs
    }


def _positions(**sizes: float) -> list[dict]:
    return [{"slug": slug, "size": size} for slug, size in sizes.items()]


def test_equal_complete_set_is_clean_with_small_fill_dust() -> None:
    issues = audit.set_only_issues(
        _priors("range-a", "range-b", "range-c"),
        _positions(**{"range-a": 20, "range-b": 20.009, "range-c": 20.001}),
    )

    assert issues == []

    # The boundary itself is inside the documented absolute tolerance; binary
    # float representation must not turn 20.01 into a false alert.
    assert audit.set_only_issues(
        _priors("range-a", "range-b"),
        _positions(**{"range-a": 20, "range-b": 20.01}),
    ) == []


def test_missing_configured_leg_is_set_broken() -> None:
    issues = audit.set_only_issues(
        _priors("range-a", "range-b", "range-c"),
        _positions(**{"range-a": 20, "range-c": 20}),
    )

    assert len(issues) == 1
    assert issues[0].startswith("SET_BROKEN")
    assert "missing range-b" in issues[0]


def test_unequal_live_sizes_are_set_broken() -> None:
    issues = audit.set_only_issues(
        _priors("range-a", "range-b", "range-c"),
        _positions(**{"range-a": 20, "range-b": 19.989, "range-c": 20}),
    )

    assert len(issues) == 1
    assert "SET_BROKEN" in issues[0]
    assert "unequal live shares" in issues[0]
    assert "range-b=19.989" in issues[0]


def test_malformed_or_single_leg_set_configuration_fails_closed() -> None:
    malformed = {"range-a": {"p_yes": 0.3, "set_only": "  "}}
    singleton = _priors("range-a")

    assert "SET_BROKEN malformed" in audit.set_only_issues(
        malformed, _positions(**{"range-a": 20})
    )[0]
    assert "SET_BROKEN" in audit.set_only_issues(
        singleton, _positions(**{"range-a": 20})
    )[0]


def test_legacy_overlapping_arb_is_not_misclassified_as_equal_share_set() -> None:
    # MetaMask's live legacy structure consists of two overlapping pairs plus a
    # directional crumb; unequal totals are intentional and need topology-aware
    # monitoring rather than this equal-share invariant.
    priors = {
        slug: {"p_yes": 0.3, "arb_paired": "legacy metamask arb"}
        for slug in ("700m", "3b", "4b")
    }

    assert audit.set_only_issues(
        priors, _positions(**{"700m": 47.72, "3b": 29.72, "4b": 15.03})
    ) == []


def test_main_returns_non_clean_when_set_is_broken(monkeypatch, capsys) -> None:
    today = dt.date.today().isoformat()
    live = [
        {
            "slug": slug,
            "size": size,
            "outcome": "Yes",
            "curPrice": 0.3,
            "asset": f"asset-{slug}",
        }
        for slug, size in (("range-a", 20), ("range-b", 19), ("range-c", 20))
    ]
    priors = _priors("range-a", "range-b", "range-c")
    snapshot = {
        "positions": [
            {"slug": p["slug"], "size": p["size"], "asset": p["asset"]}
            for p in live
        ]
    }

    def fake_load(name: str, default):
        return {
            "position_condition_ids.json": snapshot,
            "portfolio_kelly_priors.json": priors,
            "opportunity_triggers.json": [],
            "acknowledged_holds.json": [],
        }.get(name, default)

    monkeypatch.setattr(audit, "_live_positions", lambda: live)
    monkeypatch.setattr(audit, "_load", fake_load)
    monkeypatch.setattr(sys, "argv", ["position_state_audit.py"])

    assert audit.main() == 1
    output = capsys.readouterr().out
    assert "SET_BROKEN" in output
    assert "position state CLEAN" not in output
