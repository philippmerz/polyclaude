"""Focused regressions for Kelly recommendations under ticket and cluster caps."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import portfolio_kelly as kelly  # noqa: E402


def _position(
    slug: str,
    *,
    initial: float,
    fee: float,
    redeemable: bool = False,
    size: float = 10,
    mark: float = 0.10,
    avg: float = 0.10,
    condition: str | None = None,
) -> dict:
    return {
        "slug": slug,
        "outcome": "No",
        "title": f"Question {slug}",
        "conditionId": condition or f"0x{slug}",
        "eventId": f"event-{slug}",
        "size": size,
        "avgPrice": avg,
        "curPrice": mark,
        "initialValue": initial,
        "entryFeesUsdc": fee,
        "redeemable": redeemable,
    }


def test_cluster_cap_uses_entry_gate_gross_cost_and_excludes_redeemable() -> None:
    priors = {
        slug: {"p_no": 0.9, "cluster": "shared-risk"}
        for slug in ("a", "b", "settled")
    }
    positions = [
        _position("a", initial=20, fee=0.25),
        _position("b", initial=8, fee=0.75),
        _position("settled", initial=50, fee=2, redeemable=True),
    ]

    state = kelly.cluster_cap_states(positions, priors, bankroll=100)["shared-risk"]

    assert state == {
        "gross_cost": 29.0,
        "cap": 30.0,
        "headroom": 1.0,
        "fraction": 0.29,
    }


def test_cluster_gate_does_not_let_rows_double_claim_shared_headroom() -> None:
    candidates = [
        {"cluster": "shared-risk", "delta": 0.60},
        {"cluster": "shared-risk", "delta": 0.55},
    ]
    states = {
        "shared-risk": {
            "gross_cost": 29.0,
            "cap": 30.0,
            "headroom": 1.0,
            "fraction": 0.29,
        }
    }

    allowed, blocked = kelly.gate_scale_in_candidates(candidates, states)

    assert allowed == []
    assert blocked[0]["cluster"] == "shared-risk"
    assert blocked[0]["count"] == 2
    assert blocked[0]["requested"] == 1.15


def test_ticket_cap_uses_same_market_union_and_fee_inclusive_cost() -> None:
    positions = [
        _position("ticket-no", initial=20, fee=0.25, condition="0xmarket"),
        _position("ticket-yes", initial=4, fee=0.71, condition="0xmarket"),
        _position(
            "settled",
            initial=50,
            fee=2,
            condition="0xmarket",
            redeemable=True,
        ),
    ]

    states = kelly.ticket_cap_states(positions, bankroll=183.2)

    assert states["ticket-no"]["gross_cost"] == 24.96
    assert states["ticket-yes"]["gross_cost"] == 24.96
    assert states["ticket-no"]["cap"] == pytest.approx(27.48)
    assert states["ticket-no"]["headroom"] == pytest.approx(2.52)


def test_constrained_cli_suppresses_over_cap_cluster_recommendations(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    wallet = tmp_path / "wallet.json"
    wallet.write_text(json.dumps({"address": "0xabc"}))
    positions = [
        _position("risk-a", initial=0.5, fee=0, size=2, mark=0.5, avg=0.5),
        _position("risk-b", initial=0.5, fee=0, size=2, mark=0.5, avg=0.5),
        _position("risk-anchor", initial=28, fee=0, mark=0.5, avg=0.5),
    ]
    today = dt.date.today().isoformat()
    priors = {
        slug: {
            "p_no": 0.59,
            "cluster": "shared-risk",
            "rho_within": 0.50,
            "cluster_frac": 0.0,
            "verified": today,
        }
        for slug in ("risk-a", "risk-b")
    }
    priors["risk-anchor"] = {
        "p_no": 0.50,
        "cluster": "shared-risk",
        "rho_within": 0.50,
        "verified": today,
    }
    monkeypatch.setattr(kelly, "load_priors", lambda: priors)
    monkeypatch.setattr(kelly, "fetch_positions", lambda _addr: positions)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "portfolio_kelly.py",
            "--wallet",
            str(wallet),
            "--bankroll",
            "100",
            "--constrained",
        ],
    )

    assert kelly.main() == 0
    output = capsys.readouterr().out
    recommendations = output.split("Recommended actions", 1)[1].split(
        "Over-sized", 1
    )[0]
    assert "POLICY_CAP shared-risk" in recommendations
    assert "current gross $29.00, 30% cap $30.00, headroom $1.00" in recommendations
    assert "  +$" not in recommendations
    # Aggregate exposure (29%), rather than each stale 0% declaration, supplies
    # the rho discount: each candidate's Kelly target is $7.69 rather than $9.
    assert output.count("7.69") >= 2


def test_constrained_cli_suppresses_over_ticket_cap_recommendation(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    wallet = tmp_path / "wallet.json"
    wallet.write_text(json.dumps({"address": "0xabc"}))
    positions = [_position("ticket-risk", initial=24, fee=0.96)]
    priors = {
        "ticket-risk": {
            "p_no": 0.90,
            "cluster": "independent-ticket",
            "rho_within": 0.0,
            "verified": dt.date.today().isoformat(),
        }
    }
    monkeypatch.setattr(kelly, "load_priors", lambda: priors)
    monkeypatch.setattr(kelly, "fetch_positions", lambda _addr: positions)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "portfolio_kelly.py",
            "--wallet",
            str(wallet),
            "--bankroll",
            "183.2",
            "--constrained",
        ],
    )

    assert kelly.main() == 0
    output = capsys.readouterr().out
    recommendations = output.split("Recommended actions", 1)[1].split(
        "Over-sized", 1
    )[0]
    assert "TICKET_CAP ticket-risk" in recommendations
    assert "current gross $24.96, 15% cap $27.48, headroom $2.52" in recommendations
    assert "  +$" not in recommendations
