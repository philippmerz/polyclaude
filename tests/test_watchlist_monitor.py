"""Offline regressions for the project-crypto watchlist monitor."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import watchlist_monitor as monitor  # noqa: E402


def _config(tmp_path: Path, triggers: list[object] | None = None) -> Path:
    path = tmp_path / "watchlist_triggers.json"
    path.write_text(json.dumps({
        "version": 7,
        "triggers": triggers if triggers is not None else [
            {
                "ticker": "MISSING-CRYPTO", "type": "crypto",
                "coingecko_id": "missing-crypto", "entry_max": 10,
                "route": "polyclaude", "currency": "USD", "horizon": "project",
                "rationale": "crypto missing",
            },
            {
                "ticker": "HIT", "type": "crypto", "coingecko_id": "hit-coin",
                "entry_max": 10, "route": "polyclaude", "horizon": "project",
                "rationale": "review this project",
            },
            {
                "ticker": "WATCH", "type": "crypto", "coingecko_id": "watch-coin",
                "entry_max": 10, "route": "polyclaude", "horizon": "project",
                "rationale": "still above threshold",
            },
        ],
    }))
    return path


@pytest.fixture(autouse=True)
def block_side_effects(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Keep tests off network, subprocesses, and the production cache."""
    monkeypatch.setattr(monitor, "REVET_CACHE", tmp_path / "revet-cache.json")
    monkeypatch.setattr(
        monitor.subprocess, "run",
        lambda *_args, **_kwargs: pytest.fail("subprocess is forbidden in monitor tests"),
    )


def _quotes(monkeypatch: pytest.MonkeyPatch, prices: dict[str, float | None] | None = None):
    seen: list[list[str]] = []

    def fetch(ids: list[str]) -> dict[str, float]:
        seen.append(ids)
        return {key: value for key, value in (prices or {}).items() if value is not None}

    monkeypatch.setattr(monitor, "fetch_crypto_prices", fetch)
    return seen


def _run(monkeypatch: pytest.MonkeyPatch, config: Path, *args: str) -> int:
    monkeypatch.setattr(sys, "argv", ["watchlist_monitor.py", "--config", str(config), *args])
    return monitor.main()


def test_only_project_crypto_rows_are_fetched_or_surfaced(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
):
    poisoned = [
        {"ticker": "EQUITY", "type": "equity", "coingecko_id": "poison-equity",
         "route": "polyclaude", "entry_max": 1},
        {"ticker": "BROKER-CRYPTO", "type": "crypto", "coingecko_id": "broker-coin",
         "route": "ibkr_surface", "entry_max": 1},
        {"ticker": "BAD-TYPE", "type": ["crypto"], "coingecko_id": "bad-type",
         "route": "polyclaude", "entry_max": 1},
        {"ticker": "BAD-THRESHOLD", "type": "crypto", "coingecko_id": "bad-threshold",
         "route": "polyclaude", "entry_max": "1"},
        {"ticker": "GOOD", "type": "crypto", "coingecko_id": "good-coin",
         "route": "polyclaude", "entry_max": 10, "rationale": "eligible"},
    ]
    seen = _quotes(monkeypatch, {"good-coin": 5})
    assert _run(monkeypatch, _config(tmp_path, poisoned)) == 0

    output = capsys.readouterr().out
    assert seen == [["good-coin"]]
    assert "ENTRY_TRIGGER_HIT [PROJECT_REVIEW]  GOOD" in output
    for forbidden in ("EQUITY", "BROKER-CRYPTO", "BAD-TYPE", "BAD-THRESHOLD", "IBKR", "BUY"):
        assert forbidden not in output


def test_valid_crypto_missing_hit_and_watch_states(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
):
    seen = _quotes(monkeypatch, {"hit-coin": 4.0, "watch-coin": 15.0})
    assert _run(monkeypatch, _config(tmp_path), "--json") == 0

    payload = json.loads(capsys.readouterr().out)
    assert seen == [["missing-crypto", "hit-coin", "watch-coin"]]
    assert [row["status"] for row in payload["results"]] == ["NO_DATA", "TRIGGER_HIT", "WATCH"]
    assert payload["results"][0] == {
        "ticker": "MISSING-CRYPTO", "status": "NO_DATA", "current": None,
        "entry_max": 10, "entry_min": None, "direction": "", "rationale": "crypto missing",
        "type": "crypto", "currency": "USD", "route": "polyclaude", "horizon": "project",
    }
    assert payload["version"] == 7


def test_hits_only_remains_silent_when_project_crypto_does_not_hit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
):
    _quotes(monkeypatch, {"missing-crypto": 11, "hit-coin": 20, "watch-coin": 15})
    assert _run(monkeypatch, _config(tmp_path), "--hits-only") == 0
    assert capsys.readouterr().out == ""


def test_unsupported_rows_do_not_fetch_or_create_actionable_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
):
    seen = _quotes(monkeypatch)
    config = _config(tmp_path, [
        {"ticker": "OLD-EQUITY", "type": "equity", "coingecko_id": "old", "route": "polyclaude", "entry_max": 1},
        {"ticker": "BROKER", "type": "crypto", "coingecko_id": "broker", "route": "ibkr_surface", "entry_max": 1},
    ])
    assert _run(monkeypatch, config, "--hits-only") == 0
    assert seen == [[]]
    assert capsys.readouterr().out == ""


def test_auto_revet_rejects_non_crypto_before_cache_or_subprocess(
    monkeypatch: pytest.MonkeyPatch,
):
    class ForbiddenCache:
        def exists(self):
            pytest.fail("non-crypto re-vet must reject before cache access")

    monkeypatch.setattr(monitor, "REVET_CACHE", ForbiddenCache())
    result = monitor.auto_revet_ticker("ACME", "equity")
    assert result["verdict"] == "ERROR"
    assert result["from_cache"] is False


def test_auto_revet_cap_stays_bounded_for_project_crypto_hits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
):
    _quotes(monkeypatch, {"hit-coin": 4.0, "watch-coin": 15.0, "missing-crypto": 4.0})
    calls: list[tuple[str, str]] = []

    def revet(ticker: str, asset_type: str) -> dict:
        calls.append((ticker, asset_type))
        return {"verdict": "WATCH", "score": "2/4", "summary": "review", "from_cache": False}

    monkeypatch.setattr(monitor, "auto_revet_ticker", revet)
    assert _run(monkeypatch, _config(tmp_path), "--auto-revet", "--max-revet", "1") == 0
    output = capsys.readouterr().out
    assert calls == [("MISSING-CRYPTO", "crypto")]
    assert "ENTRY_TRIGGER_HIT [PROJECT_REVIEW]" in output
    assert "AUTO_REVET[fresh]" in output
    assert "BUY" not in output
