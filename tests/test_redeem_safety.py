from __future__ import annotations

import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import clob_v2  # noqa: E402


class _Call:
    def __init__(self, balance: int):
        self.balance = balance

    def call(self) -> int:
        return self.balance


class _Functions:
    def __init__(self, balance: int):
        self.balance = balance
        self.seen: tuple[str, int] | None = None

    def balanceOf(self, address: str, token_id: int) -> _Call:  # noqa: N802
        self.seen = (address, token_id)
        return _Call(self.balance)


class _Contract:
    def __init__(self, balance: int):
        self.functions = _Functions(balance)


def test_redeem_preflight_reads_archived_token_balance() -> None:
    ctf = _Contract(34_000_000)

    assert clob_v2._redeem_token_balance(ctf, "0xwallet", "123") == 34_000_000
    assert ctf.functions.seen == ("0xwallet", 123)


@pytest.mark.parametrize("token_id", [None, "", "nope", "0", "-1"])
def test_redeem_preflight_fails_closed_without_valid_token_id(token_id) -> None:
    with pytest.raises(SystemExit, match="token-id"):
        clob_v2._redeem_token_balance(_Contract(1), "0xwallet", token_id)


def test_redeem_preflight_exposes_zero_balance_noop() -> None:
    assert clob_v2._redeem_token_balance(
        _Contract(0), "0xwallet", "123"
    ) == 0


@pytest.mark.parametrize("price", [1, 1.0, "1", 0.999, "0.9999"])
def test_redeem_all_accepts_only_final_winning_rows(price) -> None:
    assert clob_v2._held_outcome_won(
        {"redeemable": True, "curPrice": price}
    )


@pytest.mark.parametrize("price", [0, 0.5, 0.998, None, "bad", float("nan")])
def test_redeem_all_rejects_losing_or_uncertain_rows(price) -> None:
    assert not clob_v2._held_outcome_won(
        {"redeemable": True, "curPrice": price}
    )


def test_redeem_all_requires_explicit_redeemable_flag() -> None:
    assert not clob_v2._held_outcome_won({"curPrice": 1})
    assert not clob_v2._held_outcome_won({"redeemable": "true", "curPrice": 1})
