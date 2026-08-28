"""News-watcher prompts must use live position state, never stale prose."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import news_watcher  # noqa: E402


def test_ostium_summary_reports_live_zero(monkeypatch) -> None:
    monkeypatch.setattr(
        news_watcher.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout="address: 0xabc\nopen trades: 0\n",
        ),
    )

    assert news_watcher._ostium_positions_summary_blocking() == (
        "Crypto/Ostium sleeve: no open trades."
    )


def test_ostium_summary_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(
        news_watcher.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=2, stdout=""),
    )

    summary = news_watcher._ostium_positions_summary_blocking()
    assert "live status unavailable" in summary
    assert "do not infer or score any crypto position" in summary


def test_no_hard_coded_closed_xau_position() -> None:
    source = Path(news_watcher.__file__).read_text(encoding="utf-8")
    stale_phrase = "currently long " + "XAU/USD 5x"
    assert stale_phrase not in source
