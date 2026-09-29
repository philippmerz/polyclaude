"""Emergency USDC swap must retain its external market-price gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import emergency_swap_usdc_to_eth as swap  # noqa: E402


class _Call:
    def __init__(self, value):
        self.value = value

    def call(self):
        return self.value


class _Functions:
    @staticmethod
    def balanceOf(_address):
        return _Call(1_000_000)

    @staticmethod
    def quoteExactInputSingle(_params):
        return _Call((400_000_000_000_000, 0, 0, 0))


class _Eth:
    @staticmethod
    def contract(**_kwargs):
        return SimpleNamespace(functions=_Functions())


def test_missing_both_market_sources_aborts_before_approval(
    monkeypatch, tmp_path: Path, capsys,
) -> None:
    keyfile = tmp_path / "wallet.json"
    keyfile.write_text(json.dumps({
        "address": "0x83dADaC202cd1276E985703f90d39EE31F3D3eE6",
        "private_key": "11" * 32,
    }))
    monkeypatch.setattr(swap._secrets, "path", lambda _name: keyfile)
    monkeypatch.setattr(swap, "_pick_rpc", lambda *_args: SimpleNamespace(eth=_Eth()))
    monkeypatch.setattr(swap, "_market_eth_usd", lambda: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "emergency_swap_usdc_to_eth.py",
            "--reason", "test guard",
            "--chain", "arbitrum",
            "--dry-run",
        ],
    )

    assert swap.main() == 2
    output = capsys.readouterr().out
    assert "fresh ETH/USD market cross-check unavailable from both sources" in output
    assert "would swap" not in output
