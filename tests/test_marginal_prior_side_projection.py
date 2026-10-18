"""Main-level regressions for side-anchored binary priors in the hurdle scan."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_marginal_apy as marginal  # noqa: E402


def _held_position(outcome: str) -> dict:
    return {
        "slug": "messi-google-athletes-top-five-2026",
        "outcome": outcome,
        "size": 5.0,
        "curPrice": 0.265,
        "endDate": "2026-12-31T00:00:00Z",
        "avgPrice": 0.27,
        "initialValue": 1.35,
        "conditionId": "0xcondition",
        "asset": "token",
        "title": "Will Messi rank in the Google Global Athletes Top 5?",
        "redeemable": False,
    }


def _run_scan(monkeypatch, tmp_path: Path, capsys, *, outcome: str,
              prior: dict) -> tuple[str, str]:
    priors_path = tmp_path / "portfolio_kelly_priors.json"
    priors_path.write_text(json.dumps({
        "messi-google-athletes-top-five-2026": prior,
    }))
    monkeypatch.setattr(marginal, "PRIORS_PATH", priors_path)
    monkeypatch.setattr(marginal, "_resolve_wallet_address", lambda: "0xwallet")
    monkeypatch.setattr(marginal, "_fetch_positions", lambda _addr: [_held_position(outcome)])
    # These cases are expected to clear the hurdle. Keep the test fail-closed
    # if a future edit unexpectedly tries an external sell-book request.
    monkeypatch.setattr(
        marginal, "_exit_quote",
        lambda *_args: (_ for _ in ()).throw(AssertionError("unexpected quote request")),
    )
    monkeypatch.setattr(
        sys, "argv", ["check_marginal_apy.py", "--hurdle-apy", "0.03"]
    )
    result = marginal.main()
    captured = capsys.readouterr()
    assert result == 0
    return captured.out, captured.err


def test_yes_holding_uses_yes_probability_from_consistent_pair(
        monkeypatch, tmp_path: Path, capsys) -> None:
    out, err = _run_scan(
        monkeypatch, tmp_path, capsys, outcome="Yes",
        prior={"p_yes": 0.60, "p_no": 0.40, "verified": dt.date.today().isoformat()},
    )

    assert "p=0.600" in out
    assert "P($0)=40.0%" in out
    assert "[UNCOVERED]" not in err


def test_yes_holding_complements_no_only_prior(
        monkeypatch, tmp_path: Path, capsys) -> None:
    out, err = _run_scan(
        monkeypatch, tmp_path, capsys, outcome="Yes",
        prior={"p_no": 0.40, "verified": dt.date.today().isoformat()},
    )

    assert "p=0.600" in out
    assert "[UNCOVERED]" not in err


def test_no_holding_complements_yes_only_prior(
        monkeypatch, tmp_path: Path, capsys) -> None:
    out, err = _run_scan(
        monkeypatch, tmp_path, capsys, outcome="No",
        prior={"p_yes": 0.60, "verified": dt.date.today().isoformat()},
    )

    assert "No 0.265" in out
    assert "p=0.400" in out
    assert "P($0)=60.0%" in out
    assert "[UNCOVERED]" not in err


def test_inconsistent_pair_fails_closed_in_main(
        monkeypatch, tmp_path: Path, capsys) -> None:
    priors_path = tmp_path / "portfolio_kelly_priors.json"
    priors_path.write_text(json.dumps({
        "messi-google-athletes-top-five-2026": {
            "p_yes": 0.60, "p_no": 0.45,
            "verified": dt.date.today().isoformat(),
        },
    }))
    monkeypatch.setattr(marginal, "PRIORS_PATH", priors_path)
    monkeypatch.setattr(marginal, "_resolve_wallet_address", lambda: "0xwallet")
    monkeypatch.setattr(marginal, "_fetch_positions", lambda _addr: [_held_position("Yes")])
    monkeypatch.setattr(
        sys, "argv", ["check_marginal_apy.py", "--hurdle-apy", "0.03"]
    )

    assert marginal.main() == 0
    captured = capsys.readouterr()
    assert "p_no and p_yes are inconsistent" in captured.err
    assert "all actions suppressed" in captured.err
    assert "p=0.600" not in captured.out


def test_unknown_named_outcome_does_not_get_binary_complement(
        monkeypatch, tmp_path: Path, capsys) -> None:
    out, err = _run_scan(
        monkeypatch, tmp_path, capsys, outcome="Other",
        prior={"p_yes": 0.60, "p_no": 0.40, "verified": dt.date.today().isoformat()},
    )

    assert "[UNCOVERED] Other 0.265" in err
    assert "p=0.600" not in out
