"""Exact Gamma identity lookup and criteria fail-closed regressions."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import catalyst_check as catalyst  # noqa: E402
import gamma_market_lookup as gamma  # noqa: E402


class _Client:
    def close(self) -> None:
        pass


def _market(market_id: int, question: str) -> dict:
    return {
        "id": str(market_id),
        "question": question,
        "slug": f"market-{market_id}",
        "description": f"Literal criteria for {market_id}",
        "active": True,
        "closed": False,
    }


def test_question_fallback_reaches_lower_ranked_keyset_market(monkeypatch) -> None:
    question = "Will the lower-ranked exact market resolve Yes?"
    calls: list[tuple[str, dict[str, str]]] = []

    def request(_client, path: str, params: dict[str, str]):
        calls.append((path, dict(params)))
        if path == "/public-search":
            return {"events": []}
        if path == "/markets/keyset":
            page = int(params.get("after_cursor", "0"))
            if page < 21:
                return {
                    "markets": [
                        _market(page * 100 + i, f"Noise {page}-{i}?")
                        for i in range(100)
                    ],
                    "next_cursor": str(page + 1),
                }
            return {"markets": [_market(2151, question)], "next_cursor": None}
        if path == "/markets" and params == {"id": "2151"}:
            return [_market(2151, question)]
        raise AssertionError((path, params))

    monkeypatch.setattr(gamma, "_request_json", request)
    result = gamma.lookup_active_market(question=question, client=_Client())

    assert result["id"] == "2151"
    assert sum(path == "/markets/keyset" for path, _ in calls) == 22
    assert not any("offset" in params for _, params in calls)


def test_public_search_hit_is_canonically_refetched(monkeypatch) -> None:
    question = "Will exact identity survive search noise?"
    canonical = _market(77, question)

    def request(_client, path: str, params: dict[str, str]):
        if path == "/public-search":
            return {"events": [{"markets": [
                _market(1, "Near but different?"),
                {**canonical, "description": "stale search copy"},
            ]}]}
        if path == "/markets" and params == {"id": "77"}:
            return [canonical]
        raise AssertionError((path, params))

    monkeypatch.setattr(gamma, "_request_json", request)
    result = gamma.lookup_active_market(question=question, client=_Client())
    assert result["description"] == "Literal criteria for 77"


def test_repeated_keyset_cursor_is_partial_coverage_error(monkeypatch) -> None:
    keyset_calls = 0

    def request(_client, path: str, _params: dict[str, str]):
        nonlocal keyset_calls
        if path == "/public-search":
            return {"events": []}
        keyset_calls += 1
        return {"markets": [_market(keyset_calls, "Noise?")], "next_cursor": "same"}

    monkeypatch.setattr(gamma, "_request_json", request)
    with pytest.raises(gamma.GammaLookupError, match="repeated a cursor.*partial"):
        gamma.lookup_active_market(question="Missing?", client=_Client())


def test_duplicate_exact_question_is_rejected_as_ambiguous(monkeypatch) -> None:
    question = "Duplicate exact question?"

    def request(_client, path: str, _params: dict[str, str]):
        assert path == "/public-search"
        return {"events": [{"markets": [_market(1, question), _market(2, question)]}]}

    monkeypatch.setattr(gamma, "_request_json", request)
    with pytest.raises(gamma.GammaMarketAmbiguous, match="2 exact-question"):
        gamma.lookup_active_market(question=question, client=_Client())


def test_catalyst_requires_literal_description_and_cross_checks_slug(monkeypatch) -> None:
    question = "Will the criteria be present?"
    monkeypatch.setattr(
        catalyst,
        "lookup_active_market",
        lambda **_kwargs: {**_market(5, question), "description": ""},
    )
    with pytest.raises(gamma.GammaLookupError, match="no literal resolution"):
        catalyst._fetch_resolution_description(question, "market-5")

    monkeypatch.setattr(
        catalyst,
        "lookup_active_market",
        lambda **_kwargs: _market(6, "A different market?"),
    )
    with pytest.raises(gamma.GammaLookupError, match="different question"):
        catalyst._fetch_resolution_description(question, "market-6")


def test_catalyst_main_never_downgrades_to_question_only_analysis(
        monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        catalyst,
        "_fetch_resolution_description",
        lambda *_args: (_ for _ in ()).throw(
            gamma.GammaLookupError("complete exact miss")
        ),
    )
    monkeypatch.setattr(
        catalyst,
        "run_agent",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("model must not run without literal criteria")
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["catalyst_check.py", "Missing exact market?", "2099-12-31"],
    )

    assert catalyst.main() == 2
    assert "lookup failed closed" in capsys.readouterr().err
