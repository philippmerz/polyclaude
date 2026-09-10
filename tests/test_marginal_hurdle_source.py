"""The marginal-return hurdle must follow the actually reachable Aave asset."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import aave_deposit  # noqa: E402
import check_marginal_apy as marginal  # noqa: E402


def test_matching_usdce_cache_is_used_without_rpc(tmp_path, monkeypatch) -> None:
    cache = tmp_path / "hurdle.json"
    cache.write_text(json.dumps({
        "apy": 0.03007,
        "chain": "polygon",
        "token": "USDC.e",
        "fetched": dt.datetime.now(dt.timezone.utc).isoformat(),
    }))
    monkeypatch.setattr(marginal, "HURDLE_CACHE", cache)
    monkeypatch.setattr(
        aave_deposit, "_w3",
        lambda _chain: (_ for _ in ()).throw(AssertionError("RPC should not run")),
    )

    apy, source = marginal._live_hurdle()

    assert apy == 0.03007
    assert "polygon/USDC.e" in source


def test_old_untagged_cache_is_rejected_and_usdce_is_queried(
        tmp_path, monkeypatch) -> None:
    cache = tmp_path / "hurdle.json"
    cache.write_text(json.dumps({
        "apy": 0.02876,
        "chain": "polygon",
        "fetched": dt.datetime.now(dt.timezone.utc).isoformat(),
    }))
    seen: dict[str, str] = {}

    class Call:
        @staticmethod
        def call():
            return [None, None, int(0.031 * aave_deposit.RAY)]

    class Functions:
        @staticmethod
        def getReserveData(asset):  # noqa: N802
            seen["asset"] = asset
            return Call()

    class Pool:
        functions = Functions()

    class Eth:
        @staticmethod
        def contract(**_kwargs):
            return Pool()

    class W3:
        eth = Eth()

    monkeypatch.setattr(marginal, "HURDLE_CACHE", cache)
    monkeypatch.setattr(aave_deposit, "_w3", lambda chain: W3())

    apy, source = marginal._live_hurdle()

    assert apy == pytest.approx(0.031)
    assert source.endswith("(polygon/USDC.e, fresh)")
    assert seen["asset"].lower() == (
        aave_deposit.CHAIN["polygon"]["tokens"]["USDC.e"].lower())
    saved = json.loads(cache.read_text())
    assert saved["chain"] == "polygon"
    assert saved["token"] == "USDC.e"
