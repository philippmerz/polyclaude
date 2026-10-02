from __future__ import annotations

import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import clob_v2  # noqa: E402


class _HttpResponse:
    def __init__(self, body, status_code: int = 200):
        self.body = body
        self.status_code = status_code

    def json(self):
        return self.body


def test_data_api_positions_accepts_a_list_of_objects(monkeypatch) -> None:
    rows = [{"conditionId": "0xabc", "redeemable": False}]
    monkeypatch.setattr(clob_v2.httpx, "get", lambda *args, **kwargs: _HttpResponse(rows))

    assert clob_v2._data_api_positions("0xWALLET") == rows


def test_data_api_positions_rejects_object_payload(monkeypatch) -> None:
    monkeypatch.setattr(clob_v2.httpx, "get", lambda *args, **kwargs: _HttpResponse({"data": []}))

    with pytest.raises(RuntimeError, match="was not a list"):
        clob_v2._data_api_positions("0xWALLET")


def test_data_api_positions_rejects_non_object_row(monkeypatch) -> None:
    monkeypatch.setattr(clob_v2.httpx, "get", lambda *args, **kwargs: _HttpResponse([{"ok": 1}, "bad"]))

    with pytest.raises(RuntimeError, match="row 1 was not an object"):
        clob_v2._data_api_positions("0xWALLET")


def test_data_api_positions_rejects_http_error_without_body_leak(monkeypatch) -> None:
    monkeypatch.setattr(clob_v2.httpx, "get", lambda *args, **kwargs: _HttpResponse("secret", 503))

    with pytest.raises(RuntimeError, match=r"HTTP 503") as exc_info:
        clob_v2._data_api_positions("0xWALLET")
    assert "secret" not in str(exc_info.value)


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


_CONDITION = bytes.fromhex("60c2c085ee8c16bc8f2419739a94971d4c9d00f637ead10fc0f540afa1be64e8")
_ARCHIVED_NO = "90869494087977018607792751230236923002303032923064138180950209430688758061828"


class _IdentityFunctions:
    def __init__(self, collateral=clob_v2.USDC_E_ADDR, denominator=1,
                 numerator=1, ambiguous=False):
        self.collateral = collateral
        self.denominator = denominator
        self.numerator = numerator
        self.ambiguous = ambiguous
        self.redeem_collaterals = []
        self.simulated_payouts = []

    def balanceOf(self, address, token):  # noqa: N802
        # Positive balance alone does not prove the condition/collateral.
        return _Call(3571)

    def getCollectionId(self, parent, condition, index_set):  # noqa: N802
        assert parent == bytes(32)
        return _Call((condition, index_set))

    def getPositionId(self, collateral, collection):  # noqa: N802
        if (collection == (_CONDITION, 2)
                and (collateral == self.collateral or self.ambiguous)):
            return _Call(int(_ARCHIVED_NO))
        return _Call(999)

    def payoutDenominator(self, condition):  # noqa: N802
        assert condition == _CONDITION
        return _Call(self.denominator)

    def payoutNumerators(self, condition, index):  # noqa: N802
        assert condition == _CONDITION and index == 1
        return _Call(self.numerator)

    def redeemPositions(self, collateral, parent, condition, index_sets):  # noqa: N802
        self.redeem_collaterals.append(collateral)
        assert parent == bytes(32) and index_sets == [1, 2]
        functions = self

        class Call(_RedeemCall):
            def call(self, tx):
                super().call(tx)
                functions.simulated_payouts.append(
                    3571 if collateral == functions.collateral else 0
                )

        return Call()


def _mock_redemption_wallet(monkeypatch, functions):
    import web3
    from eth_account import Account

    class Eth:
        gas_price = 100_000_000_000

        def contract(self, **kwargs):
            return type("Contract", (), {"functions": functions})()

        def get_transaction_count(self, address):
            return 0

        def send_raw_transaction(self, *args):
            pytest.fail("unexpected broadcast")

    class Web3:
        HTTPProvider = staticmethod(lambda *args: None)
        to_checksum_address = staticmethod(lambda address: address)

        def __init__(self, provider):
            self.eth = Eth()

    monkeypatch.setattr(web3, "Web3", Web3)
    monkeypatch.setattr(clob_v2, "_load_wallet", lambda: ("0xwallet", "unused"))
    monkeypatch.setattr(Account, "sign_transaction",
                        lambda *args: pytest.fail("unexpected signing"))


@pytest.mark.parametrize("collateral", [clob_v2.USDC_E_ADDR, clob_v2.PUSD_ADDR])
def test_redeem_one_proves_collateral_before_simulation(monkeypatch, collateral):
    functions = _IdentityFunctions(collateral=collateral)
    _mock_redemption_wallet(monkeypatch, functions)
    # Reproduce the defect: even with archived positive balance, wrong
    # collateral simulation succeeds and pays zero.
    wrong = clob_v2.PUSD_ADDR if collateral == clob_v2.USDC_E_ADDR else clob_v2.USDC_E_ADDR
    functions.redeemPositions(wrong, bytes(32), _CONDITION, [1, 2]).call({})
    assert functions.simulated_payouts == [0]
    functions.redeem_collaterals.clear()
    functions.simulated_payouts.clear()

    result = clob_v2.redeem_one(
        "0x" + _CONDITION.hex(), token_id=_ARCHIVED_NO, outcome="No", dry_run=True
    )

    assert result["ok"] is True and result["tx"] is None
    assert functions.redeem_collaterals == [collateral]
    assert functions.simulated_payouts == [3571]


@pytest.mark.parametrize("failure", ["condition", "token", "losing", "unresolved",
                                     "ambiguous", "outcome", "invalid_payout"])
@pytest.mark.parametrize("dry_run", [True, False])
def test_redeem_one_identity_failures_stop_before_prepare(monkeypatch, failure, dry_run):
    functions = _IdentityFunctions(
        denominator=0 if failure == "unresolved" else 1,
        numerator=0 if failure == "losing" else (2 if failure == "invalid_payout" else 1),
        ambiguous=failure == "ambiguous",
    )
    _mock_redemption_wallet(monkeypatch, functions)
    monkeypatch.setattr(clob_v2, "_prepare_redeem_transaction",
                        lambda *args: pytest.fail("unexpected preparation"))
    kwargs = {"token_id": "123" if failure == "token" else _ARCHIVED_NO,
              "outcome": "Yes" if failure == "outcome" else "No", "dry_run": dry_run}
    condition = bytes(32) if failure == "condition" else _CONDITION
    if dry_run:
        result = clob_v2.redeem_one("0x" + condition.hex(), **kwargs)
        assert result["ok"] is False and result["tx"] is None
    else:
        with pytest.raises(RuntimeError, match="identity/payout preflight failed"):
            clob_v2.redeem_one("0x" + condition.hex(), **kwargs)
    assert functions.redeem_collaterals == []


@pytest.mark.parametrize("collateral", [clob_v2.USDC_E_ADDR, clob_v2.PUSD_ADDR])
@pytest.mark.parametrize("outcome", ["No", "Up", "Down", "Arsenal"])
def test_redeem_all_standard_uses_same_proven_collateral(monkeypatch, collateral, outcome):
    functions = _IdentityFunctions(collateral=collateral)
    _mock_redemption_wallet(monkeypatch, functions)
    monkeypatch.setattr(clob_v2, "_data_api_positions", lambda address: [{
        "redeemable": True, "curPrice": 1, "asset": _ARCHIVED_NO,
        "oppositeAsset": "999", "conditionId": "0x" + _CONDITION.hex(),
        "outcome": outcome, "outcomeIndex": 1, "negativeRisk": False,
    }])

    def stop_after_preparation(call, tx):
        call.call({"from": tx["from"]})
        raise RuntimeError("test stops before signing")

    monkeypatch.setattr(clob_v2, "_prepare_redeem_transaction", stop_after_preparation)
    result = clob_v2.redeem_all()
    assert functions.redeem_collaterals == [collateral]
    assert functions.simulated_payouts == [3571]
    assert result["redemptions"][0]["tx"] is None


@pytest.mark.parametrize("failure", ["token", "losing", "unresolved", "ambiguous", "outcome"])
def test_redeem_all_standard_fails_closed_before_prepare(monkeypatch, failure):
    functions = _IdentityFunctions(
        denominator=0 if failure == "unresolved" else 1,
        numerator=0 if failure == "losing" else 1, ambiguous=failure == "ambiguous",
    )
    _mock_redemption_wallet(monkeypatch, functions)
    monkeypatch.setattr(clob_v2, "_data_api_positions", lambda address: [{
        "redeemable": True, "curPrice": 1,
        "asset": "123" if failure == "token" else _ARCHIVED_NO,
        "oppositeAsset": "999", "conditionId": "0x" + _CONDITION.hex(),
        "outcome": "Yes" if failure == "outcome" else "No", "negativeRisk": False,
    }])
    monkeypatch.setattr(clob_v2, "_prepare_redeem_transaction",
                        lambda *args: pytest.fail("unexpected preparation"))
    result = clob_v2.redeem_all()
    assert result["redemptions"][0]["ok"] is False
    assert result["redemptions"][0]["tx"] is None
    assert functions.redeem_collaterals == []
