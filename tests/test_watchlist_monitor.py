"""Offline regressions for watchlist monitor output and missing quotes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import watchlist_monitor as monitor  # noqa: E402


def _config(tmp_path: Path) -> Path:
    path = tmp_path / "watchlist_triggers.json"
    path.write_text(json.dumps({
        "version": 7,
        "triggers": [
            {
                "ticker": "MISSING-CRYPTO",
                "type": "crypto",
                "coingecko_id": "missing-crypto",
                "entry_max": 10,
                "route": "ibkr_surface",
                "currency": "USD",
                "horizon": "long",
                "rationale": "crypto missing",
            },
            {
                "ticker": "MISSING-EQUITY",
                "type": "equity",
                "yfinance_symbol": "MISSING",
                "entry_max": 20,
                "route": "polyclaude",
                "horizon": "near-term",
                "rationale": "equity missing",
            },
            {
                "ticker": "HIT",
                "type": "equity",
                "yfinance_symbol": "HIT",
                "entry_max": 10,
                "route": "polyclaude",
                "horizon": "near-term",
                "rationale": "hit",
            },
            {
                "ticker": "WATCH",
                "type": "equity",
                "yfinance_symbol": "WATCH",
                "entry_max": 10,
                "route": "ibkr_surface",
                "horizon": "long",
                "rationale": "watch",
            },
        ],
    }))
    return path


@pytest.fixture(autouse=True)
def block_side_effects(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Keep tests off network, subprocesses, production cache, and Telegram."""
    monkeypatch.setattr(
        monitor,
        "REVET_CACHE",
        tmp_path / "revet-cache.json",
    )
    monkeypatch.setattr(
        monitor.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("subprocess is forbidden in monitor tests"),
    )
    monkeypatch.setattr(
        monitor,
        "auto_revet_ticker",
        lambda *_args, **_kwargs: pytest.fail("auto-revet is forbidden in these tests"),
    )


def _patch_quotes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(monitor, "fetch_crypto_prices", lambda ids: {})

    def equity(symbol: str) -> float | None:
        return {"HIT": 4.0, "WATCH": 15.0}.get(symbol)

    monkeypatch.setattr(monitor, "fetch_equity_price", equity)


def _run(monkeypatch: pytest.MonkeyPatch, config: Path, *args: str) -> int:
    monkeypatch.setattr(
        sys,
        "argv",
        ["watchlist_monitor.py", "--config", str(config), *args],
    )
    return monitor.main()


def test_plain_mixed_missing_quotes_do_not_hide_later_hit_or_watch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
):
    _patch_quotes(monkeypatch)
    result = _run(monkeypatch, _config(tmp_path))

    output = capsys.readouterr().out
    assert result == 0
    assert "4 candidates  (1 HIT, 2 NO_DATA)" in output
    assert "NO_DATA   [IBKR_SURFACE]  MISSING-CRYPTO" in output
    assert "NO_DATA   [POLYCLAUDE]  MISSING-EQUITY" in output
    assert "ENTRY_TRIGGER_HIT [POLYCLAUDE_BUY]  HIT" in output
    assert "WATCH     [IBKR_SURFACE]  WATCH" in output


def test_json_no_data_has_full_renderer_metadata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
):
    _patch_quotes(monkeypatch)
    assert _run(monkeypatch, _config(tmp_path), "--json") == 0

    payload = json.loads(capsys.readouterr().out)
    missing = next(row for row in payload["results"] if row["ticker"] == "MISSING-CRYPTO")
    assert missing == {
        "ticker": "MISSING-CRYPTO",
        "status": "NO_DATA",
        "current": None,
        "entry_max": 10,
        "entry_min": None,
        "direction": "",
        "rationale": "crypto missing",
        "type": "crypto",
        "currency": "USD",
        "route": "ibkr_surface",
        "horizon": "long",
    }
    assert payload["version"] == 7


def test_hits_only_filters_no_data_and_watch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                                             capsys: pytest.CaptureFixture[str]):
    _patch_quotes(monkeypatch)
    assert _run(monkeypatch, _config(tmp_path), "--hits-only") == 0

    output = capsys.readouterr().out
    assert "ENTRY_TRIGGER_HIT [POLYCLAUDE_BUY]  HIT" in output
    assert "NO_DATA" not in output
    assert "WATCH" not in output
