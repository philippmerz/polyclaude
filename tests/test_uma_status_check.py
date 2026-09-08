"""Regressions for directional UMA price-move reporting."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import uma_status_check as uma  # noqa: E402


@pytest.fixture(autouse=True)
def isolate_side_effects(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Never let monitor tests touch the repository cache, wallet, or ledger."""
    production_cache = uma.CACHE_PATH
    production_decisions = uma.DECISIONS_PATH
    production_ledger = REPO_ROOT / "notes" / "shortdated_ledger.json"

    def snapshot(path: Path):
        return (path.exists(), path.read_bytes() if path.exists() else None)

    cache_before = snapshot(production_cache)
    decisions_before = snapshot(production_decisions)
    ledger_before = snapshot(production_ledger)

    cache_path = tmp_path / "uma_status_cache.json"
    decisions_path = tmp_path / "decisions.json"
    wallet_path = tmp_path / "wallet.json"
    cache_path.write_text("{}\n")
    decisions_path.write_text('{"decisions": []}\n')
    wallet_path.write_text('{"address": "0xabc"}\n')
    monkeypatch.setattr(uma, "CACHE_PATH", cache_path)
    monkeypatch.setattr(uma, "DECISIONS_PATH", decisions_path)
    monkeypatch.setattr(uma._secrets, "path", lambda _name: str(wallet_path))

    def deny_network(*_args, **_kwargs):
        raise AssertionError("real HTTP is forbidden in uma monitor tests")

    monkeypatch.setattr(httpx.Client, "send", deny_network)
    yield wallet_path

    assert snapshot(production_cache) == cache_before
    assert snapshot(production_decisions) == decisions_before
    assert snapshot(production_ledger) == ledger_before


def test_yes_price_move_message_preserves_direction() -> None:
    assert "(-7.2pp)" in uma._yes_price_move_message(0.835, 0.763)
    assert "(+7.2pp)" in uma._yes_price_move_message(0.763, 0.835)


def test_status_change_surfaces_resolution_and_dedupes_it() -> None:
    assert uma._status_change_alert_type(None, "resolved", visible=True) == "UMA_RESOLVED"
    assert (
        uma._status_change_alert_type("proposed", "resolved", visible=False)
        == "INVISIBLE_BUT_RESOLVED"
    )
    assert uma._status_change_alert_type("resolved", "resolved", visible=True) is None


def test_status_change_preserves_dispute_visibility_class() -> None:
    assert (
        uma._status_change_alert_type("proposed", "disputed", visible=True)
        == "UMA_STATUS_CHANGE"
    )
    assert (
        uma._status_change_alert_type("proposed", "disputed", visible=False)
        == "INVISIBLE_BUT_DISPUTED"
    )
    assert (
        uma._status_change_alert_type("proposed", "proposed", visible=False)
        == "INVISIBLE_BUT_PROPOSED"
    )
    assert (
        uma._status_change_alert_type("disputed", "disputed", visible=False)
        == "INVISIBLE_BUT_DISPUTED"
    )


def test_invalid_optional_quote_context_does_not_hide_price_move() -> None:
    alert = uma._price_move_alert(
        "market", "1", {"volume24hr": "bad", "bestBid": "bad", "bestAsk": "bad"},
        [0.8, 0.2], [0.6, 0.4], 5.0,
    )
    assert alert is not None
    assert alert["type"] == "PRICE_MOVE"
    assert "spread n/a" in alert["msg"]
    assert "vol24 n/a" in alert["msg"]
    assert "vol24 $0" not in alert["msg"]
    assert "quote context incomplete" in alert["msg"]


def test_nan_price_move_does_not_emit_alert() -> None:
    assert uma._price_move_alert(
        "market", "1", {}, [float("nan"), 0.2], [0.6, 0.4], 5.0
    ) is None
    assert uma._price_move_alert(
        "market", "1", {}, [0.8, 0.2], [float("nan"), 0.4], 5.0
    ) is None


def test_market_id_survives_slug_index_delisting_via_cache() -> None:
    cache = {"held-market": {"market_id": "3943918"}}
    assert uma._market_id_with_cache(None, cache, "held-market") == "3943918"
    assert uma._market_id_with_cache("fresh-id", cache, "held-market") == "fresh-id"
    assert uma._market_id_with_cache(None, cache, "unknown") is None


def test_transient_fetch_failure_preserves_direct_id_and_last_good_state() -> None:
    previous = {
        "market_id": "3943918",
        "umaResolutionStatus": "proposed",
        "outcomePrices": (0.7, 0.3),
    }
    retained = uma._cache_entry_after_fetch_failure(previous, "3943918")
    assert retained == previous
    assert retained is not previous

    first_failure = uma._cache_entry_after_fetch_failure(None, "new-id")
    assert first_failure == {"market_id": "new-id"}


class _PositionResponse:
    status_code = 200

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class _PositionClient:
    def __init__(self, payload):
        self.response = _PositionResponse(payload)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def get(self, *_args, **_kwargs):
        return self.response


@pytest.mark.parametrize(
    "payload, reason",
    [
        ({"slug": "not-a-list"}, "not a list"),
        (None, "not a list"),
        (["not-an-object"], "non-object"),
        ([{"size": 1}], "missing usable slug"),
        ([{"slug": "missing-size"}], "not numeric"),
        ([{"slug": "bool-size", "size": True}], "boolean"),
        ([{"slug": "nan-size", "size": float("nan")}], "non-finite"),
        ([{"slug": "inf-size", "size": float("inf")}], "non-finite"),
        ([{"slug": "negative-size", "size": -1}], "non-finite or negative"),
    ],
)
def test_positions_schema_failures_are_not_empty_success(
    monkeypatch: pytest.MonkeyPatch, payload, reason: str
) -> None:
    monkeypatch.setattr(uma.httpx, "Client", lambda **_kwargs: _PositionClient(payload))
    positions, ok, error = uma._fetch_positions_checked("0xABC")
    assert positions == []
    assert ok is False
    assert reason in error


def test_empty_positions_is_distinct_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(uma.httpx, "Client", lambda **_kwargs: _PositionClient([]))
    assert uma._fetch_positions_checked("0xABC") == ([], True, None)


@pytest.mark.parametrize("failure", [httpx.ReadTimeout("offline"), ValueError("bad JSON")])
def test_request_or_decode_failure_is_not_empty_success(monkeypatch, failure):
    class FailedClient(_PositionClient):
        def get(self, *_args, **_kwargs):
            raise failure

    monkeypatch.setattr(uma.httpx, "Client", lambda **_kwargs: FailedClient(None))
    positions, ok, error = uma._fetch_positions_checked("0xABC")
    assert positions == []
    assert ok is False
    assert error


def test_capped_positions_are_retained_but_visibility_is_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = [{"slug": f"market-{i}", "size": 1} for i in range(100)]
    monkeypatch.setattr(uma.httpx, "Client", lambda **_kwargs: _PositionClient(payload))
    positions, ok, error = uma._fetch_positions_checked("0xABC")
    assert len(positions) == 100
    assert ok is False
    assert "100-row cap" in error


def _run_main(
    monkeypatch: pytest.MonkeyPatch,
    wallet_path: Path,
    capsys: pytest.CaptureFixture[str],
    *extra_args: str,
) -> str:
    monkeypatch.setattr(sys, "argv", ["uma_status_check.py", "--wallet", str(wallet_path), *extra_args])
    assert uma.main() == 0
    return capsys.readouterr().out


def test_position_api_failure_is_explicit_and_keeps_cached_no_id(
    monkeypatch: pytest.MonkeyPatch,
    isolate_side_effects: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    previous = {
        "held": {
            "market_id": "3943918",
            "umaResolutionStatus": "proposed",
            "outcomePrices": [0.7, 0.3],
            "custom_metadata": "retain",
        },
        "without-id": {
            "umaResolutionStatus": "resolved",
            "outcomePrices": [1.0, 0.0],
            "custom_metadata": "also-retain",
        },
    }
    uma.CACHE_PATH.write_text(json.dumps(previous))
    checked_ids = []
    monkeypatch.setattr(uma, "_fetch_positions_checked", lambda _addr: ([], False, "offline"))

    def gamma(market_id):
        checked_ids.append(market_id)
        return {"umaResolutionStatus": "disputed", "outcomePrices": [0.4, 0.6]}

    monkeypatch.setattr(uma, "fetch_market", gamma)
    output = _run_main(monkeypatch, isolate_side_effects, capsys)

    assert "POSITION_API_UNAVAILABLE" in output
    assert "positions_fetch_ok=False" in output
    assert "(all clean)" not in output
    assert checked_ids == ["3943918"]
    saved = json.loads(uma.CACHE_PATH.read_text())
    assert saved["without-id"] == previous["without-id"]
    assert saved["held"]["custom_metadata"] == "retain"
    assert saved["held"]["umaResolutionStatus"] == "disputed"
    assert saved["held"]["outcomePrices"] == [0.4, 0.6]
    assert "data_api_visible" not in saved["held"]


def test_position_api_failure_json_reports_transition_without_invisible_claim(
    monkeypatch: pytest.MonkeyPatch,
    isolate_side_effects: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    uma.CACHE_PATH.write_text(json.dumps({
        "held": {"market_id": "7", "umaResolutionStatus": "proposed", "outcomePrices": [0.8, 0.2]},
    }))
    monkeypatch.setattr(uma, "_fetch_positions_checked", lambda _addr: ([], False, "timeout"))
    monkeypatch.setattr(
        uma, "fetch_market",
        lambda _market_id: {"umaResolutionStatus": "disputed", "outcomePrices": [0.6, 0.4]},
    )
    raw = _run_main(monkeypatch, isolate_side_effects, capsys, "--json")
    report = json.loads(raw)
    assert report["positions_fetch_ok"] is False
    assert "POSITION_API_UNAVAILABLE" in {a["type"] for a in report["alerts"]}
    assert "UMA_STATUS_CHANGE" in {a["type"] for a in report["alerts"]}
    assert "PRICE_MOVE" in {a["type"] for a in report["alerts"]}
    assert not any(a["type"].startswith("INVISIBLE") for a in report["alerts"])


def test_successful_empty_inventory_can_classify_invisible_cached_row(
    monkeypatch: pytest.MonkeyPatch,
    isolate_side_effects: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    uma.CACHE_PATH.write_text(json.dumps({
        "gone": {"market_id": "8", "umaResolutionStatus": "proposed", "outcomePrices": [0.8, 0.2]},
    }))
    monkeypatch.setattr(uma, "_fetch_positions_checked", lambda _addr: ([], True, None))
    monkeypatch.setattr(
        uma, "fetch_market",
        lambda _market_id: {"umaResolutionStatus": "proposed", "outcomePrices": [0.8, 0.2]},
    )
    report = json.loads(_run_main(monkeypatch, isolate_side_effects, capsys, "--json"))
    assert report["positions_fetch_ok"] is True
    assert "INVISIBLE_BUT_PROPOSED" in {a["type"] for a in report["alerts"]}
    assert json.loads(uma.CACHE_PATH.read_text())["gone"]["data_api_visible"] is False


def test_gamma_failure_during_unknown_visibility_does_not_overwrite_state(
    monkeypatch: pytest.MonkeyPatch,
    isolate_side_effects: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    previous = {"gone": {
        "market_id": "9", "umaResolutionStatus": "disputed",
        "outcomePrices": [0.2, 0.8], "custom_metadata": "retain",
    }}
    uma.CACHE_PATH.write_text(json.dumps(previous))
    monkeypatch.setattr(uma, "_fetch_positions_checked", lambda _addr: ([], False, "offline"))
    monkeypatch.setattr(uma, "fetch_market", lambda _market_id: None)
    report = json.loads(_run_main(monkeypatch, isolate_side_effects, capsys, "--json"))
    assert "GAMMA_FETCH_FAILED_UNKNOWN_VISIBILITY" in {
        a["type"] for a in report["alerts"]
    }
    assert json.loads(uma.CACHE_PATH.read_text())["gone"] == previous["gone"]


def test_capped_inventory_saves_newly_learned_market_ids(
    monkeypatch: pytest.MonkeyPatch,
    isolate_side_effects: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    positions = [{"slug": f"new-{i}", "size": 1} for i in range(100)]
    monkeypatch.setattr(
        uma, "_fetch_positions_checked", lambda _addr: (positions, False, "response reached the 100-row cap")
    )

    class LookupClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def get(self, _url, *, params):
            return _PositionResponse({"id": params["slug"]})

    monkeypatch.setattr(uma.httpx, "Client", lambda **_kwargs: LookupClient())
    monkeypatch.setattr(
        uma, "fetch_market",
        lambda market_id: {"umaResolutionStatus": "proposed", "outcomePrices": [0.5, 0.5]},
    )
    report = json.loads(_run_main(monkeypatch, isolate_side_effects, capsys, "--json"))
    saved = json.loads(uma.CACHE_PATH.read_text())
    assert report["positions_fetch_ok"] is False
    assert report["tracked_count"] == 100
    assert report["gamma_refreshed_count"] == 100
    assert len(saved) == 100


def test_failed_inventory_with_empty_cache_is_not_clean_and_does_not_write(
    monkeypatch, isolate_side_effects, capsys,
):
    monkeypatch.setattr(uma, "_fetch_positions_checked", lambda _addr: ([], False, "offline"))

    def unexpected(*_args):
        raise AssertionError("empty failed coverage must not fetch or replace cache")

    monkeypatch.setattr(uma, "fetch_market", unexpected)
    monkeypatch.setattr(uma, "save_cache", unexpected)
    report = json.loads(_run_main(monkeypatch, isolate_side_effects, capsys, "--json"))
    assert report["positions_fetch_ok"] is False
    assert report["checked_count"] == report["tracked_count"] == 0
    assert [a["type"] for a in report["alerts"]] == ["POSITION_API_UNAVAILABLE"]


def test_refresh_count_is_unique_ids_not_retained_cache_rows(
    monkeypatch, isolate_side_effects, capsys,
):
    previous = {
        "first-alias": {"market_id": "1", "umaResolutionStatus": "resolved"},
        "second-alias": {"market_id": "1", "umaResolutionStatus": "resolved"},
        "unfetched": {"market_id": "2", "umaResolutionStatus": "proposed"},
        "no-id": {"custom_metadata": "retain"},
    }
    uma.CACHE_PATH.write_text(json.dumps(previous))
    monkeypatch.setattr(uma, "_fetch_positions_checked", lambda _addr: ([], False, "offline"))
    monkeypatch.setattr(uma, "fetch_market", lambda mid:
                        {"umaResolutionStatus": "resolved", "outcomePrices": [1, 0]}
                        if mid == "1" else None)
    report = json.loads(_run_main(monkeypatch, isolate_side_effects, capsys, "--json"))
    assert report["checked_count"] == report["gamma_refreshed_count"] == 1
    assert report["tracked_count"] == 4
    saved = json.loads(uma.CACHE_PATH.read_text())
    assert saved["unfetched"] == previous["unfetched"]
    assert saved["no-id"] == previous["no-id"]
