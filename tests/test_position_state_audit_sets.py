"""Focused regressions for set-only live-position integrity."""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import httpx
import pytest


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


def test_unresolved_deindexed_claim_is_retained() -> None:
    row = {
        "slug": "deindexed",
        "outcome": "No",
        "asset": "123",
        "conditionId": "0xabc",
    }
    cache = {
        "deindexed": {
            "data_api_visible": False,
            "umaResolutionStatus": None,
            "outcomePrices": [0.0005, 0.9995],
        }
    }

    retained = audit.deindexed_claim_rows([row], set(), cache)

    assert retained[0]["slug"] == "deindexed"
    assert retained[0]["deindexed"] is True


def test_resolved_winning_deindexed_claim_is_retained_but_loser_is_pruned() -> None:
    yes = {"slug": "yes", "outcome": "Yes", "asset": "1"}
    no = {"slug": "no", "outcome": "No", "asset": "2"}
    cache = {
        slug: {
            "data_api_visible": False,
            "umaResolutionStatus": "resolved",
            "outcomePrices": [1, 0],
        }
        for slug in ("yes", "no")
    }

    retained = audit.deindexed_claim_rows([yes, no], set(), cache)

    assert [row["slug"] for row in retained] == ["yes"]


def test_indexed_or_untracked_snapshot_row_is_not_preserved_as_deindexed() -> None:
    rows = [
        {"slug": "live", "outcome": "No"},
        {"slug": "closed", "outcome": "No"},
    ]
    cache = {"live": {"data_api_visible": False}}

    assert audit.deindexed_claim_rows(rows, {"live"}, cache) == []


def test_main_returns_non_clean_when_set_is_broken(monkeypatch, capsys) -> None:
    today = dt.date.today().isoformat()
    live = [
        {
            "slug": slug,
            "size": size,
            "outcome": "Yes",
            "curPrice": 0.3,
            "asset": f"asset-{slug}",
            "endDate": "2027-12-31",
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


def test_short_dated_rotation_is_silent_for_fresh_lake_agreement_and_duma() -> None:
    today = dt.date(2026, 8, 28)
    duma_slugs = ("duma-295", "duma-310", "duma-325")
    positions = [
        {"slug": "lake-america", "endDate": "2026-08-31"},
        {"slug": "iran-oman-agreement", "endDate": "2026-09-01T00:00:00Z"},
        *({"slug": slug, "endDate": "2026-09-20"} for slug in duma_slugs),
    ]
    priors = {
        "lake-america": {"verified": "2026-08-28"},
        "iran-oman-agreement": {"verified": "2026-08-28"},
        **{
            slug: {
                "verified": "2026-08-28",
                "cluster": "duma-range",
                "set_only": SET_LABEL,
            }
            for slug in duma_slugs
        },
    }

    assert audit.short_dated_prior_issues(priors, positions, today=today) == []


def test_short_dated_rotation_groups_stale_set_only_legs_once() -> None:
    today = dt.date(2026, 8, 28)
    duma_slugs = ("duma-295", "duma-310", "duma-325")
    positions = [
        {"slug": slug, "endDate": "2026-09-20"}
        for slug in duma_slugs
    ]
    priors = {
        slug: {
            "verified": "2026-08-27",
            "cluster": "duma-range",
            "set_only": SET_LABEL,
        }
        for slug in duma_slugs
    }

    issues = audit.short_dated_prior_issues(priors, positions, today=today)

    assert len(issues) == 1
    assert "3 live row(s), 1 economic position(s)" in issues[0]
    assert issues[0].count("set-only duma-range") == 1
    assert "[3 set-only legs]" in issues[0]
    assert "23d remaining" in issues[0]
    assert "verified 1d ago" in issues[0]


def test_short_dated_rotation_flags_missing_prior_but_ignores_far_date() -> None:
    today = dt.date(2026, 8, 28)
    positions = [
        {"slug": "near-without-prior", "endDate": "2026-09-02"},
        {"slug": "far-stale-prior", "endDate": "2026-12-31"},
    ]
    priors = {"far-stale-prior": {"verified": "2026-01-01"}}

    issues = audit.short_dated_prior_issues(priors, positions, today=today)

    assert len(issues) == 1
    assert "near-without-prior" in issues[0]
    assert "verified=None (missing/malformed)" in issues[0]
    assert "far-stale-prior" not in issues[0]


def test_short_dated_rotation_fails_safely_on_bad_live_dates() -> None:
    positions = [
        {"slug": "bad-date", "endDate": "soon-ish"},
        {"slug": "missing-date"},
    ]

    issues = audit.short_dated_prior_issues(
        {}, positions, today=dt.date(2026, 8, 28)
    )

    assert len(issues) == 1
    assert "SHORT-DATED PRIOR CHECK DEGRADED" in issues[0]
    assert "bad-date='soon-ish'" in issues[0]
    assert "missing-date=None" in issues[0]
    assert "cannot prove" in issues[0]


def _response(status: int, payload: object, **headers: str) -> httpx.Response:
    request = httpx.Request("GET", audit.POSITIONS_URL)
    return httpx.Response(
        status,
        json=payload,
        headers=headers,
        request=request,
    )


def test_live_positions_retries_rate_limit_then_validates_success(monkeypatch) -> None:
    responses = [
        _response(429, "rate limited", **{"Retry-After": "0"}),
        _response(200, [
            {"slug": "live", "size": "2.5", "outcome": "Yes"},
            {
                "slug": "resolved",
                "size": "3.0",
                "outcome": "No",
                "curPrice": "0",
                "redeemable": True,
            },
            {"slug": "dust", "size": "0.1"},
        ]),
    ]
    sleeps: list[float] = []

    monkeypatch.setattr(audit.httpx, "get", lambda *_args, **_kwargs: responses.pop(0))
    monkeypatch.setattr(audit.time, "sleep", sleeps.append)

    assert audit._live_positions() == [
        {"slug": "live", "size": "2.5", "outcome": "Yes"}
    ]
    assert sleeps == [0.0]
    assert responses == []


def test_live_positions_rejects_error_payload_shape_without_attribute_error(
    monkeypatch,
) -> None:
    calls = 0

    def get(*_args, **_kwargs) -> httpx.Response:
        nonlocal calls
        calls += 1
        return _response(200, "rate limited")

    monkeypatch.setattr(audit.httpx, "get", get)
    monkeypatch.setattr(audit.time, "sleep", lambda _seconds: None)

    with pytest.raises(audit.LivePositionsUnavailable) as excinfo:
        audit._live_positions()

    assert calls == audit.POSITION_FETCH_ATTEMPTS
    assert "unexpected JSON shape (str, expected list)" in str(excinfo.value)


@pytest.mark.parametrize(
    "row,match",
    [
        ({"size": "2.5", "outcome": "Yes"}, "missing/invalid slug"),
        ({"slug": "live", "size": "2.5"}, "missing/invalid outcome"),
        ({"slug": "live", "size": "NaN", "outcome": "Yes"}, "invalid size"),
        (
            {"slug": "live", "size": "2.5", "outcome": "Yes", "curPrice": "NaN"},
            "invalid curPrice",
        ),
    ],
)
def test_live_positions_rejects_malformed_live_rows(
    monkeypatch, row: dict, match: str
) -> None:
    monkeypatch.setattr(
        audit.httpx,
        "get",
        lambda *_args, **_kwargs: _response(200, [row]),
    )
    monkeypatch.setattr(audit.time, "sleep", lambda _seconds: None)

    with pytest.raises(audit.LivePositionsUnavailable, match=match):
        audit._live_positions()


def test_main_fails_closed_before_fix_writes_when_positions_unavailable(
    monkeypatch, capsys
) -> None:
    def unavailable() -> list[dict]:
        raise audit.LivePositionsUnavailable(
            "data-api positions unavailable after 3 attempts (HTTP 429)"
        )

    monkeypatch.setattr(audit, "_live_positions", unavailable)
    monkeypatch.setattr(
        audit,
        "_load",
        lambda *_args, **_kwargs: pytest.fail("state reads must not start"),
    )
    monkeypatch.setattr(sys, "argv", ["position_state_audit.py", "--fix"])

    assert audit.main() == 2
    captured = capsys.readouterr()
    assert "AUDIT DEGRADED" in captured.err
    assert "HTTP 429" in captured.err
    assert "no state files were changed" in captured.err
