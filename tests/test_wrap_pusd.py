"""Safety regressions for the bidirectional Polymarket collateral ramp."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import wrap_pusd  # noqa: E402


@pytest.mark.parametrize(
    ("raw", "units"),
    [("0.000001", 1), ("1", 1_000_000), ("17.123456", 17_123_456)],
)
def test_amount_units_is_exact(raw: str, units: int) -> None:
    assert wrap_pusd._amount_units(raw, False, 999_999_999) == units


@pytest.mark.parametrize("raw", ["0", "-1", "nan", "inf", "1.0000001", "nope"])
def test_amount_units_rejects_ambiguous_or_invalid_money(raw: str) -> None:
    with pytest.raises(ValueError):
        wrap_pusd._amount_units(raw, False, 999_999_999)


def test_all_uses_exact_onchain_balance() -> None:
    assert wrap_pusd._amount_units("ignored", True, 17_123_456) == 17_123_456


class _Call:
    def __init__(self, value):
        self.value = value

    def call(self):
        return self.value


class _Functions:
    def __init__(self, collateral: str, paused: bool):
        self.collateral = collateral
        self.is_paused = paused

    def COLLATERAL_TOKEN(self):  # noqa: N802
        return _Call(self.collateral)

    def paused(self, _asset: str):
        return _Call(self.is_paused)


class _Eth:
    def __init__(self, code: bytes):
        self.code = code

    def get_code(self, _address: str) -> bytes:
        return self.code


class _W3:
    def __init__(self, code: bytes = b"deployed"):
        self.eth = _Eth(code)


class _Offramp:
    def __init__(self, collateral: str, paused: bool = False):
        self.functions = _Functions(collateral, paused)


class _EventsResult:
    def __init__(self, rows):
        self.rows = rows

    def process_receipt(self, _receipt):
        return self.rows


class _UnwrappedEvent:
    def __init__(self, rows):
        self.rows = rows

    def __call__(self):
        return _EventsResult(self.rows)


class _Events:
    def __init__(self, rows):
        self.Unwrapped = _UnwrappedEvent(rows)


class _Pusd:
    def __init__(self, rows):
        self.events = _Events(rows)


def test_offramp_validation_accepts_expected_live_shape() -> None:
    wrap_pusd._validate_offramp(_W3(), _Offramp(wrap_pusd.PUSD), wrap_pusd.USDCE)


def test_offramp_validation_fails_closed_on_missing_code() -> None:
    with pytest.raises(RuntimeError, match="no deployed bytecode"):
        wrap_pusd._validate_offramp(
            _W3(b""), _Offramp(wrap_pusd.PUSD), wrap_pusd.USDCE)


def test_offramp_validation_fails_closed_on_wrong_collateral() -> None:
    with pytest.raises(RuntimeError, match="token mismatch"):
        wrap_pusd._validate_offramp(
            _W3(), _Offramp(wrap_pusd.USDCE), wrap_pusd.USDCE)


def test_offramp_validation_fails_closed_when_asset_paused() -> None:
    with pytest.raises(RuntimeError, match="paused"):
        wrap_pusd._validate_offramp(
            _W3(), _Offramp(wrap_pusd.PUSD, paused=True), wrap_pusd.USDCE)


def test_onramp_validation_requires_deployed_code() -> None:
    wrap_pusd._validate_onramp(_W3())
    with pytest.raises(RuntimeError, match="no deployed bytecode"):
        wrap_pusd._validate_onramp(_W3(b""))


def test_receipt_verification_requires_exact_tx_local_event() -> None:
    exact = {"args": {
        "caller": wrap_pusd.OFFRAMP,
        "asset": wrap_pusd.USDCE,
        "to": "0x0000000000000000000000000000000000000001",
        "amount": 1_500_000,
    }}
    assert wrap_pusd._has_exact_unwrap_event(
        _Pusd([exact]), object(), wrap_pusd.USDCE,
        "0x0000000000000000000000000000000000000001", 1_500_000)

    wrong_amount = {"args": {**exact["args"], "amount": 1_499_999}}
    assert not wrap_pusd._has_exact_unwrap_event(
        _Pusd([wrong_amount]), object(), wrap_pusd.USDCE,
        "0x0000000000000000000000000000000000000001", 1_500_000)


def test_submitted_hash_is_exposed_when_receipt_times_out(
        monkeypatch, capsys) -> None:
    class Signed:
        raw_transaction = b"signed"

    class Signer:
        @staticmethod
        def sign_transaction(_tx):
            return Signed()

    class Hash:
        @staticmethod
        def hex():
            return wrap_pusd.Web3.keccak(b"signed").hex()

    class Eth:
        @staticmethod
        def send_raw_transaction(_raw):
            return Hash()

        @staticmethod
        def wait_for_transaction_receipt(_hash, timeout):
            assert timeout == 180
            raise TimeoutError("rpc unavailable")

    class W3:
        eth = Eth()

    monkeypatch.setattr(wrap_pusd.Account, "from_key", lambda _pk: Signer())
    with pytest.raises(wrap_pusd.BroadcastUncertain, match="DO NOT RETRY"):
        wrap_pusd._send_receipt(W3(), "private", {})
    assert wrap_pusd.Web3.keccak(b"signed").hex() in capsys.readouterr().out


def test_local_hash_is_available_when_submission_response_fails(
        monkeypatch, capsys) -> None:
    class Signed:
        raw_transaction = b"signed"

    class Signer:
        @staticmethod
        def sign_transaction(_tx):
            return Signed()

    class Eth:
        @staticmethod
        def send_raw_transaction(_raw):
            raise ConnectionError("response lost")

    class W3:
        eth = Eth()

    monkeypatch.setattr(wrap_pusd.Account, "from_key", lambda _pk: Signer())
    with pytest.raises(wrap_pusd.BroadcastUncertain, match="may have been submitted"):
        wrap_pusd._send_receipt(W3(), "private", {})
    assert wrap_pusd.Web3.keccak(b"signed").hex() in capsys.readouterr().out
