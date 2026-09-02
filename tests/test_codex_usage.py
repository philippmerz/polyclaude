"""Pure regressions for the read-only Codex quota probe."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "codex_usage.py"
SPEC = importlib.util.spec_from_file_location("codex_usage", SCRIPT)
assert SPEC and SPEC.loader
codex_usage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(codex_usage)


def _snapshot() -> dict:
    return {
        "fetchedAt": "2026-09-02T18:34:00+00:00",
        "rateLimits": {
            "rateLimitsByLimitId": {
                "codex_bengalfox": {
                    "limitId": "codex_bengalfox",
                    "limitName": "GPT-5.3-Codex-Spark",
                    "primary": {
                        "usedPercent": 2,
                        "windowDurationMins": 300,
                        "resetsAt": 1788392097,
                    },
                    "secondary": {
                        "usedPercent": 7,
                        "windowDurationMins": 10080,
                        "resetsAt": 1788978897,
                    },
                },
                "codex": {
                    "limitId": "codex",
                    "limitName": None,
                    "primary": {
                        "usedPercent": 32,
                        "windowDurationMins": 10080,
                        "resetsAt": 1788748215,
                    },
                },
            },
            "rateLimitResetCredits": {"availableCount": 0, "credits": []},
        },
        "tokenUsage": {
            "summary": {"lifetimeTokens": 1_447_007_121},
            "dailyUsageBuckets": [
                {"startDate": "2026-09-01", "tokens": 75_135_167},
                {"startDate": "2026-09-02", "tokens": 75_499_990},
            ],
        },
    }


def test_rpc_sequence_initializes_before_read_only_account_calls() -> None:
    messages = codex_usage.rpc_messages(include_token_usage=True)

    assert messages[0]["method"] == "initialize"
    assert messages[1] == {"method": "initialized", "params": {}}
    assert [item["method"] for item in messages[2:]] == [
        "account/rateLimits/read",
        "account/usage/read",
    ]
    assert all("turn" not in item["method"].lower() for item in messages)


def test_response_parser_ignores_notifications_and_noise() -> None:
    responses: dict[int, dict] = {}
    codex_usage.accept_rpc_line(b"not-json", responses)
    codex_usage.accept_rpc_line(b'{"method":"account/rateLimits/updated","params":{}}', responses)
    codex_usage.accept_rpc_line(b'{"id":2,"result":{"rateLimits":{}}}', responses)

    assert responses == {2: {"id": 2, "result": {"rateLimits": {}}}}


def test_format_surfaces_main_and_model_specific_headroom() -> None:
    rendered = codex_usage.format_snapshot(_snapshot())

    assert "codex: 32% used / 68% headroom" in rendered
    assert "GPT-5.3-Codex-Spark: 2% used / 98% headroom" in rendered
    assert "GPT-5.3-Codex-Spark secondary: 7% used / 93% headroom" in rendered
    assert "2026-09-02 75.50M tokens" in rendered
    assert "lifetime 1.45B" in rendered


def test_main_headroom_excludes_independent_model_bucket() -> None:
    snapshot = _snapshot()
    assert codex_usage.main_codex_headroom(snapshot["rateLimits"]) == 68


def test_legacy_single_bucket_shape_is_supported() -> None:
    result = {
        "rateLimits": {
            "limitId": "codex",
            "primary": {
                "usedPercent": 81,
                "windowDurationMins": 300,
                "resetsAt": 1788392097,
            },
        }
    }

    rows = codex_usage.rate_limit_rows(result)
    assert len(rows) == 1
    assert rows[0]["headroomPercent"] == 19
