from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import httpx
import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import google_maps_label_check as maps_check
import opportunity_watch as watch


def _response(
    body: str,
    *,
    status: int = 200,
    content_type: str = "text/html; charset=UTF-8",
    url: str = "https://www.google.com/maps/search/Lake+Ontario?hl=en&gl=us",
) -> httpx.Response:
    request = httpx.Request("GET", url)
    return httpx.Response(
        status,
        text=body,
        headers={"content-type": content_type},
        request=request,
    )


def _maps_html(labels: str) -> str:
    return (
        "<html>Google Maps<script>APP_INITIALIZATION_STATE=[];"
        "window.APP_FLAGS={};</script>" + labels + "</html>"
    )


def test_checker_returns_no_signal_with_control_label(monkeypatch) -> None:
    monkeypatch.setattr(
        maps_check.httpx,
        "get",
        lambda *_args, **_kwargs: _response(_maps_html("Lake Ontario Lake Ontario")),
    )

    result = maps_check.check_google_maps_label(
        query="Lake Ontario",
        target_label="Lake America",
        control_label="Lake Ontario",
    )

    assert result.rollout_signal is False
    assert result.target_count == 0
    assert result.control_count == 2


def test_checker_requires_exact_case_sensitive_target(monkeypatch) -> None:
    monkeypatch.setattr(
        maps_check.httpx,
        "get",
        lambda *_args, **_kwargs: _response(
            _maps_html("Lake Ontario lake america Lake America")
        ),
    )

    result = maps_check.check_google_maps_label(
        query="Lake Ontario",
        target_label="Lake America",
        control_label="Lake Ontario",
    )

    assert result.rollout_signal is True
    assert result.target_count == 1


@pytest.mark.parametrize(
    "response,match",
    [
        (_response("Before you continue to Google"), "consent/interstitial"),
        (_response("<html>Lake Ontario</html>"), "response schema"),
        (_response(_maps_html("unrelated result")), "neither target nor control"),
        (_response(_maps_html("Lake Ontario"), content_type="application/json"), "content type"),
        (_response("unavailable", status=503), "request failed"),
    ],
)
def test_checker_fails_closed_on_uninterpretable_response(
    monkeypatch, response: httpx.Response, match: str
) -> None:
    monkeypatch.setattr(maps_check.httpx, "get", lambda *_args, **_kwargs: response)

    with pytest.raises(maps_check.LabelCheckError, match=match):
        maps_check.check_google_maps_label(
            query="Lake Ontario",
            target_label="Lake America",
            control_label="Lake Ontario",
        )


def _write_trigger(path: Path, expires_at: str = "2026-09-01T04:00:00Z") -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "key": "lake-america-maps-rollout",
                    "kind": "google_maps_label",
                    "query": "Lake Ontario",
                    "target_label": "Lake America",
                    "control_label": "Lake Ontario",
                    "region": "us",
                    "language": "en",
                    "expires_at": expires_at,
                    "actionable": True,
                    "note": "review only",
                }
            ]
        )
    )


def test_watch_alerts_and_fires_only_on_first_observation(monkeypatch, tmp_path) -> None:
    triggers = tmp_path / "triggers.json"
    _write_trigger(triggers)
    monkeypatch.setattr(watch, "TRIGGERS_PATH", triggers)
    monkeypatch.setattr(watch, "_now", lambda: 1_787_940_000)
    monkeypatch.setattr(
        watch,
        "check_google_maps_label",
        lambda **_kwargs: maps_check.LabelObservation(
            query="Lake Ontario",
            target_label="Lake America",
            control_label="Lake Ontario",
            target_count=1,
            control_count=1,
            region="us",
            language="en",
            final_url="https://www.google.com/maps/search/Lake+Ontario?hl=en&gl=us",
        ),
    )
    alerts: list[tuple[str, str, bool]] = []
    monkeypatch.setattr(
        watch,
        "_alert",
        lambda _state, key, text, actionable: (
            alerts.append((key, text, actionable)) or True
        ),
    )
    state: dict = {}

    watch.check_google_maps_labels(state)
    watch.check_google_maps_labels(state)

    assert len(alerts) == 1
    assert alerts[0][0] == "lake-america-maps-rollout"
    assert alerts[0][2] is True
    assert "majority-US rollout" in alerts[0][1]
    assert "NOT proof that the label rendered on the map" in alerts[0][1]
    assert state["google_maps_label_hits"]["lake-america-maps-rollout"]["target_count"] == 1
    assert state["google_maps_label_hits"]["lake-america-maps-rollout"][
        "review_tick_pending"
    ] is False


def test_watch_retries_review_tick_after_shared_cooldown(monkeypatch, tmp_path) -> None:
    triggers = tmp_path / "triggers.json"
    _write_trigger(triggers)
    monkeypatch.setattr(watch, "TRIGGERS_PATH", triggers)
    monkeypatch.setattr(watch, "_now", lambda: 1_787_940_000)
    fetches: list[str] = []

    def observe(**_kwargs) -> maps_check.LabelObservation:
        fetches.append("fetch")
        return maps_check.LabelObservation(
            query="Lake Ontario",
            target_label="Lake America",
            control_label="Lake Ontario",
            target_count=1,
            control_count=1,
            region="us",
            language="en",
            final_url="https://www.google.com/maps/search/Lake+Ontario?hl=en&gl=us",
        )

    monkeypatch.setattr(watch, "check_google_maps_label", observe)
    alerts: list[str] = []
    monkeypatch.setattr(
        watch,
        "_alert",
        lambda _state, key, _text, _actionable: alerts.append(key) or False,
    )
    retry_results = iter([False, True])
    retry_calls: list[str] = []
    monkeypatch.setattr(
        watch,
        "_fire_tick",
        lambda _state, key: retry_calls.append(key) or next(retry_results),
    )
    state: dict = {}

    watch.check_google_maps_labels(state)  # first alert; tick suppressed
    watch.check_google_maps_labels(state)  # still inside shared cooldown
    watch.check_google_maps_labels(state)  # cooldown cleared; tick dispatched
    watch.check_google_maps_labels(state)  # fully deduped

    hit = state["google_maps_label_hits"]["lake-america-maps-rollout"]
    assert fetches == ["fetch"]
    assert alerts == ["lake-america-maps-rollout"]
    assert retry_calls == [
        "lake-america-maps-rollout",
        "lake-america-maps-rollout",
    ]
    assert hit["review_tick_pending"] is False
    assert hit["review_tick_dispatched"] == 1_787_940_000


def test_daemon_stop_pattern_cannot_match_invoking_shell() -> None:
    pattern = watch._daemon_process_pattern()
    canonical = f"{watch.PY} {Path(watch.__file__).resolve()} start"

    assert re.fullmatch(pattern, canonical)
    assert not re.search(pattern, f"/bin/bash -lc 'restart {canonical}'")


def test_watch_expires_without_fetch_or_alert(monkeypatch, tmp_path) -> None:
    triggers = tmp_path / "triggers.json"
    _write_trigger(triggers, expires_at="2026-08-28T17:00:00Z")
    monkeypatch.setattr(watch, "TRIGGERS_PATH", triggers)
    monkeypatch.setattr(watch, "_now", lambda: 1_787_940_000)
    monkeypatch.setattr(
        watch,
        "check_google_maps_label",
        lambda **_kwargs: pytest.fail("expired watch must not fetch"),
    )
    monkeypatch.setattr(
        watch,
        "_alert",
        lambda *_args, **_kwargs: pytest.fail("expired watch must not alert"),
    )
    state: dict = {}

    watch.check_google_maps_labels(state)

    assert state["google_maps_label_expired"]["lake-america-maps-rollout"] == (
        "2026-08-28T17:00:00Z"
    )


def test_watch_request_failure_never_becomes_positive(monkeypatch, tmp_path) -> None:
    triggers = tmp_path / "triggers.json"
    _write_trigger(triggers)
    monkeypatch.setattr(watch, "TRIGGERS_PATH", triggers)
    monkeypatch.setattr(watch, "_now", lambda: 1_787_940_000)
    monkeypatch.setattr(
        watch,
        "check_google_maps_label",
        lambda **_kwargs: (_ for _ in ()).throw(maps_check.LabelCheckError("consent")),
    )
    monkeypatch.setattr(
        watch,
        "_alert",
        lambda *_args, **_kwargs: pytest.fail("first failed poll must not alert"),
    )
    state: dict = {}

    watch.check_google_maps_labels(state)

    assert state["trig_fails"]["lake-america-maps-rollout"] == 1
    assert state["google_maps_label_hits"] == {}


def test_consistency_hit_requests_revalidation_not_execution(monkeypatch) -> None:
    class Result:
        returncode = 0
        stdout = (
            "2 PROVISIONAL consistency candidates exceed 2.0% modeled net; "
            "REVALIDATION REQUIRED\n"
        )
        stderr = ""

    alerts = []
    monkeypatch.setattr(watch.subprocess, "run", lambda *_a, **_k: Result())
    monkeypatch.setattr(
        watch, "_alert",
        lambda _state, key, text, actionable: alerts.append(
            (key, text, actionable)
        ),
    )

    watch.run_consistency({})

    assert len(alerts) == 1
    assert alerts[0][0] == "consistency-arb"
    assert alerts[0][2] is True  # dispatches a review tick only
    assert "REVALIDATION REQUEST" in alerts[0][1]
    assert "sequential, non-atomic" in alerts[0][1]
    assert "Do not execute" in alerts[0][1]
    assert "act now" not in alerts[0][1]


def test_consistency_nonzero_exit_never_alerts(monkeypatch) -> None:
    class Result:
        returncode = 1
        stdout = (
            "2 PROVISIONAL consistency candidates exceed 2.0% modeled net; "
            "REVALIDATION REQUIRED\n"
        )
        stderr = "failed"

    alerts = []
    monkeypatch.setattr(watch.subprocess, "run", lambda *_a, **_k: Result())
    monkeypatch.setattr(watch, "_alert", lambda *_a, **_k: alerts.append(True))

    watch.run_consistency({})

    assert alerts == []
