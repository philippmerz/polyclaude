"""News-watcher prompts must use live position state, never stale prose."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import news_watcher  # noqa: E402
import polyclaude_enter  # noqa: E402


def _pending_buy(**changes) -> dict:
    return {
        "orderId": "order-swift-no", "asset": "token-no", "conditionId": "0xswift",
        "question": "Will Taylor Swift release a Japanese album?", "slug": "swift-japanese-album",
        "originalShares": 10.0, "matchedShares": 4.0, "remainingShares": 6.0,
        "price": 0.56, "risk": 3.3600000000000003, **changes,
    }


def _mock_inventory(monkeypatch, tmp_path, *, positions=None, orders=None) -> None:
    wallet = tmp_path / "public_wallet.json"
    wallet.write_text(json.dumps({"address": "0xpublic"}))
    monkeypatch.setattr(news_watcher._secrets, "path", lambda _name: wallet)
    monkeypatch.setattr(news_watcher, "_POSITIONS_CACHE", {
        "text": None, "ts": 0.0, "polymarket_available": False,
    })
    monkeypatch.setattr(news_watcher.httpx, "get", lambda *_a, **_kw: SimpleNamespace(
        raise_for_status=lambda: None, json=lambda: positions or [],
    ))
    monkeypatch.setattr(polyclaude_enter, "_fetch_open_buy_commitments", lambda: orders or [])
    monkeypatch.setattr(news_watcher, "_ostium_positions_summary_blocking", lambda: "No crypto trades.")


def test_partial_buy_is_additional_to_held_and_order_duplicates_removed(monkeypatch, tmp_path):
    buy = _pending_buy()
    held = {"outcome": "NO", "curPrice": 0.55, "initialValue": 2.24,
            "title": buy["question"], "asset": buy["asset"]}
    _mock_inventory(monkeypatch, tmp_path, positions=[held], orders=[buy, dict(buy)])
    text = news_watcher._positions_summary_blocking()
    assert text.count("order=order-swift-no") == 1
    assert "remaining=6.0 shares @ 0.56" in text
    assert "capped commitment=$3.3600000000000003" in text
    assert "slug=swift-japanese-album" in text and "asset=token-no" in text
    assert "NO 0.550 ($2.24)" in text
    assert "remaining=10.0" not in text
    assert news_watcher._POSITIONS_CACHE["polymarket_available"] is True


@pytest.mark.parametrize("failed", [False, True])
def test_pending_inventory_success_and_failure_share_existing_ttl(monkeypatch, tmp_path, failed):
    _mock_inventory(monkeypatch, tmp_path)
    calls = []

    def read():
        calls.append(1)
        if failed:
            raise RuntimeError("read failed")
        return [_pending_buy()]

    monkeypatch.setattr(polyclaude_enter, "_fetch_open_buy_commitments", read)
    first = news_watcher._positions_summary_blocking()
    assert ("pending BUY inventory unavailable" in first) is failed
    assert news_watcher._positions_summary_blocking() == first
    assert calls == [1]
    assert news_watcher._POSITIONS_CACHE["polymarket_available"] is not failed


@pytest.mark.parametrize("failure", ["held", "pending"])
def test_inventory_failure_passes_alert_without_agent(monkeypatch, tmp_path, failure):
    _mock_inventory(monkeypatch, tmp_path)

    def fail(*_a, **_kw):
        raise RuntimeError("inventory read failed")

    if failure == "held":
        monkeypatch.setattr(news_watcher.httpx, "get", fail)
    else:
        monkeypatch.setattr(polyclaude_enter, "_fetch_open_buy_commitments", fail)
    monkeypatch.setattr(news_watcher, "run_agent", lambda *_a, **_kw: pytest.fail("must pass through"))
    send, reason, impacts = news_watcher._agent_filter_tier2("RSS", "Taylor Swift", "New album", "")
    assert send is True and "inventory unavailable" in reason and impacts == []


def test_pending_order_identity_conflict_fails_inventory(monkeypatch, tmp_path):
    _mock_inventory(monkeypatch, tmp_path, orders=[_pending_buy(), _pending_buy(asset="other-token")])
    text = news_watcher._positions_summary_blocking()
    assert "inconsistent duplicate order identity" in text
    assert news_watcher._POSITIONS_CACHE["polymarket_available"] is False


def test_distinct_orders_same_asset_remain_distinct_and_sell_is_not_exposure(monkeypatch, tmp_path):
    _mock_inventory(monkeypatch, tmp_path, orders=[
        _pending_buy(), _pending_buy(orderId="second-order"),
        {"side": "SELL", "orderId": "sell-order"},
    ])
    text = news_watcher._positions_summary_blocking()
    assert "order=order-swift-no" in text and "order=second-order" in text
    assert "sell-order" not in text


def test_pending_buy_only_prompt_has_cancellation_channel(monkeypatch, tmp_path):
    _mock_inventory(monkeypatch, tmp_path, orders=[_pending_buy()])
    prompts = []

    def agent(prompt, **_kwargs):
        prompts.append(prompt)
        return SimpleNamespace(returncode=0, stdout="SEND: album announcement\n")

    monkeypatch.setattr(news_watcher, "run_agent", agent)
    assert news_watcher._agent_filter_tier2("RSS", "Taylor Swift", "New album", "")[0] is True
    assert "swift-japanese-album" in prompts[0]
    assert "cancellation or re-evaluation" in prompts[0]


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
