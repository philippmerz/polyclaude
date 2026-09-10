from __future__ import annotations

import json
import sys

import httpx
import pytest

from scripts import source_freeze_check as sfc


@pytest.fixture(autouse=True)
def _default_pattern(monkeypatch):
    monkeypatch.setattr(sfc, "PATTERN", sfc.DEFAULT_PATTERN)


def _table(rows: str) -> str:
    return ("<table><thead><tr><th>Model</th><th>Accuracy&nbsp;(%) ↑</th>"
            "<th>Calibration Error (%) ↓</th></tr></thead><tbody>"
            + rows + "</tbody></table>")


def _row(name="GPT-5", accuracy="25.3", calibration="50.0") -> str:
    return f"<tr><td>{name}</td><td>{accuracy}</td><td>{calibration}</td></tr>"


class _Client:
    def __init__(self, response: httpx.Response):
        self.response = response
        self.urls: list[str] = []

    def get(self, _url: str) -> httpx.Response:
        self.urls.append(_url)
        return self.response


def _response(status: int, body: str) -> httpx.Response:
    request = httpx.Request("GET", "https://example.test/")
    return httpx.Response(status, text=body, request=request)


def _json_response(payload: object, status: int = 200) -> httpx.Response:
    return _response(status, json.dumps(payload))


def _api_row(name="GPT-6 Astra", model_id="gpt-6-astra-high", hle=53.6,
             calibration=44.2) -> dict:
    return {
        "name": name,
        "id": model_id,
        "scores": {"hle": hle, "hle_calibration_error": calibration},
    }


def test_fetch_rejects_http_error() -> None:
    assert sfc.fetch(_Client(_response(503, "gpt-5")), "https://x", None) is None


def test_fetch_rejects_empty_inventory() -> None:
    assert sfc.fetch(_Client(_response(200, "<html>archive shell</html>")),
                     "https://x", "20260101") is None


def test_fetch_generic_nonempty_inventory() -> None:
    assert sfc.fetch(_Client(_response(200, "gpt-5")), "https://x", None) == {"gpt-5"}


def test_hle_includes_all_names_and_ignores_prose() -> None:
    body = "<p>o3-mini is mentioned here, but is not a result.</p>" + _table(
        _row() + _row("Gemini 2.5 Flash", "12.1", "80") + _row("o1", "8", "83")
        + _row("An Unfamiliar Future Model", "61", "20")
    )
    assert sfc.hle_results(body) == {
        "gpt-5": ("25.3", "50"), "gemini 2.5 flash": ("12.1", "80"),
        "o1": ("8", "83"), "an unfamiliar future model": ("61", "20"),
    }


def test_hle_live_like_ten_row_inventory() -> None:
    data = [
        ("Gemini 3 Pro", "38.3", "57.2"), ("GPT-5", "25.3", "50"),
        ("Grok 4", "24.5", "56.4"), ("Gemini 2.5 Pro", "21.6", "72"),
        ("GPT-5-mini", "19.4", "65"), ("Claude 4.5 Sonnet", "13.7", "65"),
        ("Gemini 2.5 Flash", "12.1", "80"), ("DeepSeek-R1*", "8.5", "73"),
        ("o1", "8", "83"), ("GPT-4o", "2.7", "89"),
    ]
    body = "<script>model='o3-mini';</script>" + _table("".join(
        _row(f'<a href="/model">{name}</a>', accuracy, calibration)
        for name, accuracy, calibration in data
    ))
    assert sfc.hle_results(body) == {
        name.casefold(): (accuracy, calibration) for name, accuracy, calibration in data
    }


def test_hle_chart_api_parses_actual_score_fields_and_missing_calibration() -> None:
    payload = [
        _api_row(),
        _api_row("o3", "o3-high", 20, None),
        _api_row("Gemini 3.1 Pro", "gemini-3.1-pro-preview-high", 45.90, 50.30),
    ]
    assert sfc.hle_chart_results(payload) == {
        "gpt-6 astra": ("53.6", "44.2"),
        "o3": ("20", "-"),
        "gemini 3.1 pro": ("45.9", "50.3"),
    }


@pytest.mark.parametrize("payload", [
    None,
    [],
    ["not an object"],
    [{}],
    [_api_row(name="")],
    [_api_row(model_id="")],
    [{"name": "GPT-6 Astra", "id": "x", "scores": {}}],
    [_api_row(hle=None)],
    [_api_row(hle=float("nan"))],
    [_api_row(hle=101)],
    [_api_row(), _api_row(model_id="a-duplicate-id")],
])
def test_hle_chart_api_rejects_incomplete_or_ambiguous_payloads(payload) -> None:
    with pytest.raises(ValueError):
        sfc.hle_chart_results(payload)


def test_hle_detects_score_only_change_that_regex_misses() -> None:
    old = _table(_row())
    new = _table(_row(accuracy="55.3"))
    assert sfc.tokens(old, sfc.DEFAULT_PATTERN) == sfc.tokens(new, sfc.DEFAULT_PATTERN)
    assert sfc.differences(sfc.hle_results(old), sfc.hle_results(new)) == (
        [], [], [("gpt-5", ("25.3", "50"), ("55.3", "50"))],
    )


def test_hle_detects_calibration_change_and_added_removed_models() -> None:
    old = sfc.hle_results(_table(_row() + _row("o1")))
    new = sfc.hle_results(_table(_row(calibration="49") + _row("New Model")))
    assert sfc.differences(old, new) == (
        ["new model"], ["o1"], [("gpt-5", ("25.3", "50"), ("25.3", "49"))],
    )


def test_hle_ignores_order_layout_and_numeric_formatting() -> None:
    old = _table(_row() + _row("o1", "8.0", "83.00"))
    new = _table(_row("o1", "8", "83") + _row("<b>GPT-5</b>", "25.30%", "50"))
    assert sfc.hle_results(old) == sfc.hle_results(new)


@pytest.mark.parametrize("missing", ["", "-"])
def test_hle_historical_missing_calibration_is_supported(missing) -> None:
    assert sfc.hle_results(_table(_row("DeepSeek-R1-0528*", "17.7", missing))) == {
        "deepseek-r1-0528*": ("17.7", "-"),
    }


@pytest.mark.parametrize("body", [
    "<html>gpt-5 error shell</html>",
    _table(""),
    _table(_row() + _row()),
    _table(_row()) + _table(_row()),
    _table("<tr><td>GPT-5</td><td>25.3</td></tr>"),
    _table(_row(accuracy="-")),
    _table(_row(accuracy="")),
    _table(_row(accuracy="nan")),
    _table(_row(accuracy="101")),
    _table(_row(calibration="-1")),
    _table(_row()).replace("Accuracy", "Mystery"),
    _table(_row()).replace("</table>", ""),
    _table(_row()).replace("</td>", "", 1),
    _table(_row()).replace("</td>", "</th>", 1),
    _table(_row(name="")),
])
def test_hle_rejects_invalid_or_ambiguous_results(body) -> None:
    with pytest.raises(ValueError):
        sfc.hle_results(body)
    assert sfc.fetch(_Client(_response(200, body)), "https://agi.safe.ai/", None) is None


def test_hle_fetch_is_structured_and_custom_pattern_is_explicit_fallback(monkeypatch) -> None:
    client = _Client(_json_response([_api_row()]))
    assert sfc.fetch(client, "https://agi.safe.ai/", None) == {
        "gpt-6 astra": ("53.6", "44.2")
    }
    assert client.urls == [sfc.HLE_CHART_API]
    monkeypatch.setattr(sfc, "PATTERN", r"o3-mini")
    generic = _Client(_response(200, "<p>o3-mini</p>"))
    assert sfc.fetch(generic, "https://agi.safe.ai/", None) == {"o3-mini"}
    assert generic.urls == ["https://agi.safe.ai/"]


def test_hle_archives_the_same_api_surface_with_raw_wayback_capture() -> None:
    client = _Client(_json_response([_api_row("Gemini 3.1 Pro", "gemini", 45.9, 50.3)]))
    assert sfc.fetch(client, "https://agi.safe.ai/", "20260703") == {
        "gemini 3.1 pro": ("45.9", "50.3")
    }
    assert client.urls == [
        "https://web.archive.org/web/20260703id_/https://dashboard.safe.ai/api/models"
    ]


def test_table_mode_is_limited_to_exact_source_root() -> None:
    assert sfc.uses_hle_results("https://agi.safe.ai/")
    assert not sfc.uses_hle_results("https://agi.safe.ai.evil.test/")
    assert not sfc.uses_hle_results("https://agi.safe.ai/another-board")


def test_validation_rejects_disjoint_snapshots(monkeypatch, capsys) -> None:
    values = iter(({"gpt-4o"}, {"gemini 3 pro"}))
    monkeypatch.setattr(sfc, "fetch", lambda *_args: next(values))
    monkeypatch.setattr(sys, "argv", [
        "source_freeze_check.py", "--url", "https://x",
        "--validate", "20250101", "20251201",
    ])

    assert sfc.main() == 2
    assert "share no parsed anchor" in capsys.readouterr().out


def test_validation_accepts_change_with_shared_anchor(monkeypatch, capsys) -> None:
    values = iter(({"gpt-4o", "gemini 2.5 pro"},
                   {"gpt-5", "gemini 2.5 pro"}))
    monkeypatch.setattr(sfc, "fetch", lambda *_args: next(values))
    monkeypatch.setattr(sys, "argv", [
        "source_freeze_check.py", "--url", "https://x",
        "--validate", "20250101", "20251201",
    ])

    assert sfc.main() == 0
    assert "INSTRUMENT VALID" in capsys.readouterr().out


def test_hle_cli_validation_and_live_comparison_detect_score_change(monkeypatch, capsys) -> None:
    old = {"gpt-5": ("25.3", "50")}
    new = {"gpt-5": ("55.3", "50")}
    values = iter((old, new, new, old))
    monkeypatch.setattr(sfc, "fetch", lambda *_args: next(values))
    monkeypatch.setattr(sys, "argv", [
        "source_freeze_check.py", "--url", "https://agi.safe.ai/",
        "--validate", "20250601", "20251201", "--since", "20260115",
    ])
    assert sfc.main() == 0
    out = capsys.readouterr().out
    assert "INSTRUMENT VALID" in out
    assert "UPDATING" in out
    assert "UNCHANGED" not in out


def test_hle_cli_unchanged_is_scoped_to_resolving_chart(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sfc, "fetch", lambda *_args: {"gpt-5": ("25.3", "50")})
    monkeypatch.setattr(sys, "argv", [
        "source_freeze_check.py", "--url", "https://agi.safe.ai/",
        "--since", "20260115", "--expect", "gpt",
    ])
    assert sfc.main() == 0
    out = capsys.readouterr().out
    assert "RESOLVING CHART API UNCHANGED" in out
    assert "not a whole-page claim" in out


def test_hle_cli_brief_keeps_diff_but_omits_full_inventory(monkeypatch, capsys) -> None:
    values = iter((
        {"gpt-6 astra": ("53.6", "39.8")},
        {"gpt-5.6 sol": ("45.52", "46.74")},
    ))
    monkeypatch.setattr(sfc, "fetch", lambda *_args: next(values))
    monkeypatch.setattr(sys, "argv", [
        "source_freeze_check.py", "--url", "https://agi.safe.ai/",
        "--since", "20260703", "--brief",
    ])

    assert sfc.main() == 0
    out = capsys.readouterr().out
    assert "added ['gpt-6 astra']" in out
    assert "live inventory" not in out


def test_hle_cli_missing_expected_model_still_fails(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sfc, "fetch", lambda *_args: {"gpt-5": ("25.3", "50")})
    monkeypatch.setattr(sys, "argv", [
        "source_freeze_check.py", "--url", "https://agi.safe.ai/",
        "--since", "20260115", "--expect", "claude",
    ])
    assert sfc.main() == 1
    assert "PARSER INCOMPLETE" in capsys.readouterr().out


def test_cli_regex_mode_makes_no_score_claim(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sfc, "fetch", lambda *_args: {"gpt-5"})
    monkeypatch.setattr(sys, "argv", [
        "source_freeze_check.py", "--url", "https://agi.safe.ai/",
        "--pattern", "gpt-5", "--since", "20260115",
    ])
    assert sfc.main() == 0
    out = capsys.readouterr().out
    assert "REGEX TOKEN SET UNCHANGED" in out
    assert "no claim about scores" in out
