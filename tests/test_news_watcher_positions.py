"""News-watcher prompts must use live position state, never stale prose."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import news_watcher  # noqa: E402


def test_title_dedup_state_survives_daily_guid_refresh(monkeypatch, tmp_path) -> None:
    """An unchanged headline must not re-enter on the next two daily polls."""
    state_path = tmp_path / "news_state.json"
    now = time.time()
    monkeypatch.setattr(news_watcher, "STATE_PATH", state_path)
    monkeypatch.setattr(news_watcher.time, "time", lambda: now)

    news_watcher.save_state({
        "seen_ids": [],
        "seen_titles": {
            "same daily-refreshed story": now - (48 * 60 * 60),
            "expired story": now - (96 * 60 * 60),
        },
    })

    saved = json.loads(state_path.read_text())
    assert "same daily-refreshed story" in saved["seen_titles"]
    assert "expired story" not in saved["seen_titles"]


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


def test_broadly_deployed_model_release_matches_tier1() -> None:
    """A safety-titled launch must not evade the explicit release phrases."""
    config_path = Path(news_watcher.__file__).with_name("news_watcher_config.json")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    rss_blob = (
        "Safety overview: GPT-6 Astra. GPT-6 Astra is our most capable "
        "broadly deployed model and our first to reach the Critical level."
    )

    assert news_watcher.match_keywords(rss_blob, config["tier1_keywords"]) == (
        "most capable broadly deployed model"
    )


def test_introducing_named_gpt6_variants_matches_tier2() -> None:
    """Named releases must match even when a title avoids release verbs."""
    config_path = Path(news_watcher.__file__).with_name("news_watcher_config.json")
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert news_watcher.match_keywords(
        "Introducing GPT-6 Sol and GPT-6 Luna",
        config["tier2_keywords"],
    ) == "gpt-6 sol"
