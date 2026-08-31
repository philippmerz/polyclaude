from __future__ import annotations

import sys

import httpx

from scripts import source_freeze_check as sfc


class _Client:
    def __init__(self, response: httpx.Response):
        self.response = response

    def get(self, _url: str) -> httpx.Response:
        return self.response


def _response(status: int, body: str) -> httpx.Response:
    request = httpx.Request("GET", "https://example.test/")
    return httpx.Response(status, text=body, request=request)


def test_fetch_rejects_http_error() -> None:
    assert sfc.fetch(_Client(_response(503, "gpt-5")), "https://x", None) is None


def test_fetch_rejects_empty_inventory() -> None:
    assert sfc.fetch(_Client(_response(200, "<html>archive shell</html>")),
                     "https://x", "20260101") is None


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
