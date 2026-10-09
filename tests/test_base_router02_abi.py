"""Regression tests for Base's Router02 and deadline-preserving call shape."""

from __future__ import annotations

import sys
from pathlib import Path

from web3 import Web3

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import emergency_swap_usdc_to_eth as emergency  # noqa: E402
import spot_swap  # noqa: E402


ROUTER = "0x2626664c2603336E57B271c5C0b26F421741e481"
TOKEN_IN = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
TOKEN_OUT = "0x4200000000000000000000000000000000000006"
RECIPIENT = "0x1111111111111111111111111111111111111111"
DEADLINE = 1_800_000_600


def _router():
    return Web3().eth.contract(
        address=Web3.to_checksum_address(ROUTER), abi=spot_swap.ROUTER02_ABI)


def _assert_base_multicall(factory, amount: int, minimum: int) -> None:
    call = factory(
        Web3(), ROUTER, 8453, TOKEN_IN, TOKEN_OUT, 500, RECIPIENT,
        DEADLINE, amount, minimum)
    outer_data = call._encode_transaction_data()
    assert outer_data[2:10] == Web3.keccak(text="multicall(uint256,bytes[])")[:4].hex()
    decoded_outer = _router().decode_function_input(outer_data)
    assert decoded_outer[0].fn_name == "multicall"
    assert decoded_outer[1]["deadline"] == DEADLINE
    assert len(decoded_outer[1]["data"]) == 1

    inner_data = "0x" + decoded_outer[1]["data"][0].hex()
    assert inner_data[2:10] == Web3.keccak(
        text="exactInputSingle((address,address,uint24,address,uint256,uint256,uint160))"
    )[:4].hex()
    decoded_inner = _router().decode_function_input(inner_data)
    assert decoded_inner[0].fn_name == "exactInputSingle"
    assert decoded_inner[1]["params"] == {
        "tokenIn": Web3.to_checksum_address(TOKEN_IN),
        "tokenOut": Web3.to_checksum_address(TOKEN_OUT),
        "fee": 500,
        "recipient": Web3.to_checksum_address(RECIPIENT),
        "amountIn": amount,
        "amountOutMinimum": minimum,
        "sqrtPriceLimitX96": 0,
    }


def test_base_uses_deployed_quoter_and_router02_deadline_multicall() -> None:
    assert spot_swap.CHAIN["base"]["quoter"] == (
        "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a")
    assert emergency.CHAIN["base"]["quoter"] == (
        "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a")
    _assert_base_multicall(spot_swap._router_swap_call, 12_345_678, 12_000_000)
    _assert_base_multicall(emergency._router_swap_call, 98_765_432, 95_000_000)


def test_non_base_keeps_v1_eight_field_exact_input_single() -> None:
    for factory, router_abi in (
        (spot_swap._router_swap_call, spot_swap.ROUTER_ABI),
        (emergency._router_swap_call, emergency.ROUTER_ABI),
    ):
        call = factory(
            Web3(), spot_swap.UNISWAP_ROUTER_V1, 42161, TOKEN_IN, TOKEN_OUT,
            3000, RECIPIENT, DEADLINE, 10_000, 9_000)
        data = call._encode_transaction_data()
        assert data[2:10] == Web3.keccak(
            text="exactInputSingle((address,address,uint24,address,uint256,uint256,uint256,uint160))"
        )[:4].hex()
        decoded = Web3().eth.contract(abi=router_abi).decode_function_input(data)
        assert decoded[0].fn_name == "exactInputSingle"
        assert tuple(decoded[1]["params"].values()) == (
            Web3.to_checksum_address(TOKEN_IN), Web3.to_checksum_address(TOKEN_OUT),
            3000, Web3.to_checksum_address(RECIPIENT), DEADLINE, 10_000, 9_000, 0)
