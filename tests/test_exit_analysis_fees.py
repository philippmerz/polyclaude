"""Focused regressions for execution-time exit fee routing and math."""

from __future__ import annotations

import sys
import json
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import exit_analysis as exits  # noqa: E402
import pm_fees  # noqa: E402


CID = "0xabc"


class _Response:
    def __init__(self, payload: object, *, error: Exception | None = None):
        self.payload = payload
        self.error = error

    def raise_for_status(self) -> None:
        if self.error is not None:
            raise self.error

    def json(self) -> object:
        return self.payload


def test_compact_v2_descriptor_overrides_stale_full_1000(monkeypatch) -> None:
    calls: list[str] = []

    def get(url: str, **_kwargs) -> _Response:
        calls.append(url)
        assert "/clob-markets/" in url
        return _Response({
            "c": CID,
            "fd": {"r": 0.04, "e": 1, "to": True},
            "tbf": 1000,
        })

    monkeypatch.setattr(exits.httpx, "get", get)

    market = exits._execution_fee_market(CID)

    assert market == {
        "feesEnabled": True,
        "feeSchedule": {"rate": 0.04, "exponent": 1, "takerOnly": True},
    }
    assert pm_fees.fee_per_share(market, 0.5) == pytest.approx(0.04 * 0.25)
    assert len(calls) == 1  # a valid fd never consults the stale full field


def test_compact_absence_accepts_only_explicit_full_zero(monkeypatch) -> None:
    def get(url: str, **_kwargs) -> _Response:
        if "/clob-markets/" in url:
            return _Response({"c": CID, "fd": None})
        return _Response({"condition_id": CID, "taker_base_fee": "0"})

    monkeypatch.setattr(exits.httpx, "get", get)

    market = exits._execution_fee_market(CID)

    assert market == {"takerBaseFee": 0}
    assert pm_fees.fee_per_share(market, 0.5) == 0.0


@pytest.mark.parametrize(
    "compact,full",
    [
        ({"c": CID, "fd": None}, {"condition_id": CID, "taker_base_fee": 1000}),
        ({"c": CID, "fd": "malformed"}, {"condition_id": CID, "taker_base_fee": 0}),
        ({"c": "0xwrong", "fd": {"r": 0, "e": 1}}, {"condition_id": CID, "taker_base_fee": 0}),
    ],
)
def test_ambiguous_metadata_fails_closed(monkeypatch, compact: dict, full: dict) -> None:
    def get(url: str, **_kwargs) -> _Response:
        return _Response(compact if "/clob-markets/" in url else full)

    monkeypatch.setattr(exits.httpx, "get", get)

    market = exits._execution_fee_market(CID)

    assert market is None
    assert pm_fees.fee_per_share(market, 0.5) == pytest.approx(0.07 * 0.25)


def test_unreachable_compact_metadata_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(
        exits.httpx,
        "get",
        lambda *_args, **_kwargs: _Response({}, error=RuntimeError("offline")),
    )

    assert exits._execution_fee_market(CID) is None


def test_book_walk_keeps_conservative_max_for_structured_exponent(monkeypatch) -> None:
    book = {
        "bids": [
            {"price": "0.40", "size": "3"},
            {"price": "0.60", "size": "2"},
        ],
        "min_order_size": "1",
    }
    monkeypatch.setattr(exits.httpx, "get", lambda *_args, **_kwargs: _Response(book))
    market = {
        "feesEnabled": True,
        "feeSchedule": {"rate": 0.25, "exponent": 2, "takerOnly": False},
    }

    gross, filled, fee = exits._walk_bids("token", 4.0, market)

    level_fee = 2 * 0.25 * (0.60 * 0.40) ** 2 + 2 * 0.25 * (0.40 * 0.60) ** 2
    aggregate_fee = 4 * 0.25 * (0.50 * 0.50) ** 2
    assert gross == pytest.approx(2.0)
    assert filled == pytest.approx(4.0)
    assert fee == pytest.approx(max(level_fee, aggregate_fee))


def test_best_sale_prefix_finds_profitable_trim_hidden_by_full_walk(monkeypatch) -> None:
    book = {
        "bids": [
            {"price": "0.40", "size": "3"},
            {"price": "0.60", "size": "2"},
        ],
        "min_order_size": "2",
    }
    monkeypatch.setattr(exits.httpx, "get", lambda *_args, **_kwargs: _Response(book))

    options = exits._walk_bid_options("token", 5.0, {"takerBaseFee": 0})
    best = exits._best_sale_prefix(options, fair=0.50)

    assert options[-1] == pytest.approx((2.4, 5.0, 0.0))
    assert best == pytest.approx((1.2, 2.0, 0.0, 0.2))


def test_best_sale_prefix_rejects_every_bid_below_fair(monkeypatch) -> None:
    monkeypatch.setattr(
        exits.httpx,
        "get",
        lambda *_args, **_kwargs: _Response({
            "bids": [{"price": "0.49", "size": "5"}],
            "min_order_size": "1",
        }),
    )

    options = exits._walk_bid_options("token", 5.0, {"takerBaseFee": 0})

    assert exits._best_sale_prefix(options, fair=0.50) is None


@pytest.mark.parametrize(
    "level",
    [
        {"price": "1.01", "size": "2"},
        {"price": "0.50", "size": "-1"},
        {"price": "nan", "size": "2"},
    ],
)
def test_book_walk_rejects_malformed_binary_levels(monkeypatch, level: dict) -> None:
    monkeypatch.setattr(
        exits.httpx,
        "get",
        lambda *_args, **_kwargs: _Response({"bids": [level], "min_order_size": "1"}),
    )

    with pytest.raises(ValueError, match="malformed binary bid level"):
        exits._walk_bids("token", 1.0, {"takerBaseFee": 0})


def test_subminimum_residue_cannot_become_a_taker_sale_prefix(monkeypatch) -> None:
    # A favorable 4.03-share residue is below this book's actual five-share
    # minimum, so it is not an executable recommendation even at a 0.99 bid.
    book = {
        "bids": [{"price": "0.99", "size": "4.03"}],
        "min_order_size": "5",
    }
    monkeypatch.setattr(exits.httpx, "get", lambda *_args, **_kwargs: _Response(book))

    options = exits._walk_bid_options("token", 4.03, {"takerBaseFee": 0})

    assert options == []
    assert exits._best_sale_prefix(options, fair=0.50) is None


def test_live_minimum_is_used_instead_of_a_hardcoded_share_floor(monkeypatch) -> None:
    book = {
        "bids": [{"price": "0.99", "size": "4.03"}],
        "min_order_size": "4",
    }
    monkeypatch.setattr(exits.httpx, "get", lambda *_args, **_kwargs: _Response(book))

    options = exits._walk_bid_options("token", 4.03, {"takerBaseFee": 0})

    assert options[-1] == pytest.approx((3.9897, 4.03, 0.0))
    assert exits._best_sale_prefix(options, fair=0.50) == pytest.approx(
        (3.9897, 4.03, 0.0, 1.9747)
    )


@pytest.mark.parametrize(
    "minimum", [None, "not-a-number", "nan", "inf", "0", "-1", True]
)
def test_missing_or_invalid_live_minimum_fails_closed(monkeypatch, minimum) -> None:
    book = {"bids": [{"price": "0.99", "size": "10"}]}
    if minimum is not None:
        book["min_order_size"] = minimum
    monkeypatch.setattr(exits.httpx, "get", lambda *_args, **_kwargs: _Response(book))

    with pytest.raises(ValueError, match="min_order_size"):
        exits._walk_bid_options("token", 10.0, {"takerBaseFee": 0})


def test_exact_minimum_boundary_inside_level_can_be_profitable(
    monkeypatch,
) -> None:
    # The 4.03-share first level alone is below min size, but a legal five-share
    # planning prefix takes only 0.97 shares from the next level. The full
    # ten-share endpoint loses to fair, so omitting the interior boundary would
    # hide a profitable minimum-sized option.
    book = {
        "bids": [
            {"price": "0.99", "size": "4.03"},
            {"price": "0.01", "size": "5.97"},
        ],
        "min_order_size": "5",
    }
    monkeypatch.setattr(exits.httpx, "get", lambda *_args, **_kwargs: _Response(book))

    options = exits._walk_bid_options("token", 10.0, {"takerBaseFee": 0})

    assert options == [
        (pytest.approx(3.9994), pytest.approx(5.0), pytest.approx(0.0)),
        (pytest.approx(4.0494), pytest.approx(10.0), pytest.approx(0.0)),
    ]
    assert exits._best_sale_prefix(options, fair=0.50) == pytest.approx(
        (3.9994, 5.0, 0.0, 1.4994)
    )


def test_exact_minimum_boundary_recomputes_fee_for_truncated_fill(monkeypatch) -> None:
    book = {
        "bids": [
            {"price": "0.99", "size": "4.03"},
            {"price": "0.01", "size": "5.97"},
        ],
        "min_order_size": "5",
    }
    market = {
        "feesEnabled": True,
        "feeSchedule": {"rate": 0.04, "exponent": 1, "takerOnly": True},
    }
    monkeypatch.setattr(exits.httpx, "get", lambda *_args, **_kwargs: _Response(book))

    options = exits._walk_bid_options("token", 10.0, market)

    assert options[0] == pytest.approx((3.9994, 5.0, 0.03202))
    assert exits._best_sale_prefix(options, fair=0.50) == pytest.approx(
        (3.9994, 5.0, 0.03202, 1.46738)
    )


def test_exit_cli_does_not_recommend_subminimum_taker_sale(
    monkeypatch, tmp_path, capsys
) -> None:
    priors_path = tmp_path / "priors.json"
    priors_path.write_text(json.dumps({
        "g4.03-residue": {"p_yes": 0.50, "verified": "2026-10-13"},
    }))
    positions = [{
        "slug": "g4.03-residue", "outcome": "Yes", "size": "4.03",
        "asset": "token", "conditionId": CID,
    }]

    def get(url: str, **_kwargs) -> _Response:
        if "data-api.polymarket.com/positions" in url:
            return _Response(positions)
        if url.endswith("/book"):
            return _Response({
                "bids": [{"price": "0.99", "size": "4.03"}],
                "min_order_size": "5",
            })
        raise AssertionError(url)

    monkeypatch.setattr(exits, "PRIORS", priors_path)
    monkeypatch.setattr(exits, "_execution_fee_market", lambda _condition: {"takerBaseFee": 0})
    monkeypatch.setattr(exits.httpx, "get", get)
    monkeypatch.setattr(sys, "argv", ["exit_analysis.py"])

    assert exits.main() == 0

    output = capsys.readouterr().out
    assert "SELL TAKER" not in output
    assert "HOLD CANDIDATE" in output


def test_exit_cli_fails_closed_when_book_minimum_is_missing(
    monkeypatch, tmp_path, capsys
) -> None:
    priors_path = tmp_path / "priors.json"
    priors_path.write_text(json.dumps({
        "g4.03-residue": {"p_yes": 0.50, "verified": "2026-10-13"},
    }))
    positions = [{
        "slug": "g4.03-residue", "outcome": "Yes", "size": "4.03",
        "asset": "token", "conditionId": CID,
    }]

    def get(url: str, **_kwargs) -> _Response:
        if "data-api.polymarket.com/positions" in url:
            return _Response(positions)
        if url.endswith("/book"):
            return _Response({"bids": [{"price": "0.99", "size": "10"}]})
        raise AssertionError(url)

    monkeypatch.setattr(exits, "PRIORS", priors_path)
    monkeypatch.setattr(exits, "_execution_fee_market", lambda _condition: {"takerBaseFee": 0})
    monkeypatch.setattr(exits.httpx, "get", get)
    monkeypatch.setattr(sys, "argv", ["exit_analysis.py"])

    assert exits.main() == 0

    captured = capsys.readouterr()
    assert "SELL TAKER" not in captured.out
    assert "min_order_size" in captured.err


def test_breakeven_solves_general_v2_exponent() -> None:
    market = {
        "feesEnabled": True,
        "feeSchedule": {"rate": 0.25, "exponent": 2, "takerOnly": True},
    }

    price = exits._taker_breakeven(0.40, market)

    assert price is not None
    assert price - pm_fees.fee_per_share(market, price) == pytest.approx(0.40)
    assert price > 0.40


def test_breakeven_refuses_nonmonotone_extreme_curve() -> None:
    market = {
        "feesEnabled": True,
        "feeSchedule": {"rate": 10.0, "exponent": 2, "takerOnly": True},
    }

    assert exits._taker_breakeven(0.05, market) is None


@pytest.mark.parametrize(
    ("fair", "expected"),
    [
        (0.18, "P(terminal $0)=82.0%"),
        (0.97, "P(terminal $0)=3.0%"),
        (0.0, "P(terminal $0)=100.0%"),
        (1.0, "P(terminal $0)=0.0%"),
    ],
)
def test_binary_risk_text_exposes_zero_payoff_branch(
    fair: float, expected: str
) -> None:
    assert exits._binary_risk_text(fair) == expected


@pytest.mark.parametrize("fair", [-0.01, 1.01, float("nan")])
def test_binary_risk_text_rejects_invalid_probability(fair: float) -> None:
    with pytest.raises(ValueError, match="fair must be between 0 and 1"):
        exits._binary_risk_text(fair)


def test_best_sale_prefix_treats_an_exact_tie_as_an_exit() -> None:
    tied = exits._best_sale_prefix([(2.5, 5.0, 0.0)], fair=0.50)

    assert tied is not None
    assert tied[3] == pytest.approx(0.0)
    assert exits._best_sale_prefix([(2.5 - 1e-6, 5.0, 0.0)], fair=0.50) is None


def test_best_sale_prefix_prefers_the_larger_tied_prefix() -> None:
    best = exits._best_sale_prefix(
        [(0.5, 1.0, 0.0), (2.5, 5.0, 0.0)], fair=0.50)

    assert best is not None
    assert best[1] == pytest.approx(5.0)


def test_exit_cli_sells_when_stressed_hold_loses_to_cash(
    monkeypatch, tmp_path, capsys
) -> None:
    priors_path = tmp_path / "priors.json"
    priors_path.write_text(json.dumps({
        "openrouter-band": {
            "p_no": 0.85, "p_no_stress": 0.70, "verified": "2026-10-26",
        },
    }))
    positions = [{
        "slug": "openrouter-band", "outcome": "No", "size": "5",
        "asset": "token", "conditionId": CID,
    }]

    def get(url: str, **_kwargs) -> _Response:
        if "data-api.polymarket.com/positions" in url:
            return _Response(positions)
        if url.endswith("/book"):
            return _Response({
                "bids": [{"price": "0.72", "size": "5"}],
                "min_order_size": "5",
            })
        raise AssertionError(url)

    monkeypatch.setattr(exits, "PRIORS", priors_path)
    monkeypatch.setattr(exits, "_execution_fee_market", lambda _condition: {"takerBaseFee": 0})
    monkeypatch.setattr(exits.httpx, "get", get)
    monkeypatch.setattr(sys, "argv", ["exit_analysis.py"])

    assert exits.main() == 0
    output = capsys.readouterr().out
    assert "SELL TAKER ALL NOW" in output
    assert "stressed" in output


def test_exit_cli_keeps_a_set_only_pair_whole_when_stress_prefers_cash(
    monkeypatch, tmp_path, capsys
) -> None:
    priors_path = tmp_path / "priors.json"
    priors_path.write_text(json.dumps({
        "clarity-leg": {
            "p_yes": 0.50, "p_yes_stress": 0.10, "verified": "2026-10-26",
            "arb_paired": "manage only as the complete pair",
        },
    }))
    positions = [{
        "slug": "clarity-leg", "outcome": "Yes", "size": "5",
        "asset": "token", "conditionId": CID,
    }]

    def get(url: str, **_kwargs) -> _Response:
        if "data-api.polymarket.com/positions" in url:
            return _Response(positions)
        if url.endswith("/book"):
            return _Response({
                "bids": [{"price": "0.90", "size": "5"}],
                "min_order_size": "5",
            })
        raise AssertionError(url)

    monkeypatch.setattr(exits, "PRIORS", priors_path)
    monkeypatch.setattr(exits, "_execution_fee_market", lambda _condition: {"takerBaseFee": 0})
    monkeypatch.setattr(exits.httpx, "get", get)
    monkeypatch.setattr(sys, "argv", ["exit_analysis.py"])

    assert exits.main() == 0
    output = capsys.readouterr().out
    assert "SELL TAKER" not in output
    assert "GROUP STRUCTURES" in output
    assert "GROUP_BROKEN" in output
