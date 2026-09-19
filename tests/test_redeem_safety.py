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


class _RedeemCall:
    def __init__(self, gas_estimate: int = 305_922, fail_at: str | None = None):
        self.gas_estimate = gas_estimate
        self.fail_at = fail_at
        self.events: list[tuple[str, dict]] = []

    def call(self, tx: dict) -> None:
        self.events.append(("call", tx))
        if self.fail_at == "call":
            raise RuntimeError("simulation reverted")

    def estimate_gas(self, tx: dict) -> int:
        self.events.append(("estimate", tx))
        if self.fail_at == "estimate":
            raise RuntimeError("estimation failed")
        return self.gas_estimate

    def build_transaction(self, tx: dict) -> dict:
        self.events.append(("build", tx))
        return dict(tx)


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


def test_redeem_preflight_simulates_then_estimates_with_buffer() -> None:
    redeem_call = _RedeemCall(gas_estimate=305_922)
    common_tx = {"from": "0xwallet", "nonce": 7, "chainId": 137}

    tx, estimate, gas_limit = clob_v2._prepare_redeem_transaction(
        redeem_call, common_tx
    )

    assert estimate == 305_922
    assert gas_limit == 367_107
    assert tx["gas"] == gas_limit
    assert "gas" not in common_tx
    assert [event for event, _ in redeem_call.events] == [
        "call", "estimate", "build",
    ]
    assert redeem_call.events[0][1] == {"from": "0xwallet"}
    assert redeem_call.events[1][1] == {"from": "0xwallet"}


@pytest.mark.parametrize("fail_at", ["call", "estimate"])
def test_redeem_preflight_failure_never_builds_transaction(fail_at: str) -> None:
    redeem_call = _RedeemCall(fail_at=fail_at)

    with pytest.raises(RuntimeError):
        clob_v2._prepare_redeem_transaction(
            redeem_call, {"from": "0xwallet", "nonce": 7, "chainId": 137}
        )

    assert "build" not in [event for event, _ in redeem_call.events]


@pytest.mark.parametrize("estimate", [0, -1, True, "bad"])
def test_redeem_gas_buffer_rejects_invalid_estimate(estimate) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        clob_v2._buffered_redeem_gas(estimate)
