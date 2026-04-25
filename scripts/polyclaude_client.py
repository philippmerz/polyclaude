"""Thin wrapper around py-clob-client for the polyclaude project.

Loads the wallet privately (NEVER commits the key), creates the CLOB client,
and provides idempotent methods for:
  - on-chain allowance setup (USDC.e + CTF approvals to Exchange + NegRisk contracts)
  - L2 API credential bootstrap
  - placing/cancelling limit orders, querying balance/positions/orderbook

Usage from another script:

    from polyclaude_client import Polyclaude
    pc = Polyclaude.load()
    pc.print_status()                 # balances + allowances + positions
    pc.ensure_allowances(dry_run=True)
    pc.ensure_allowances()            # actually broadcasts approval txs
    pc.place_limit_buy(token_id, price=0.95, usd_size=5)
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
from eth_account import Account
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import (
    ApiCreds,
    AssetType,
    BalanceAllowanceParams,
    OpenOrderParams,
    OrderArgs,
    OrderType,
)
from py_clob_client.order_builder.constants import BUY, SELL
from web3 import Web3

# ----- constants ----------------------------------------------------------------

WALLET_PATH = Path("<SECRETS>/wallet.json")
CREDS_PATH = Path("<SECRETS>/polyclaude_creds.json")  # outside the repo

CHAIN_ID = 137
CLOB_HOST = "https://clob.polymarket.com"

POLYGON_RPCS = [
    "https://polygon.drpc.org",
    "https://polygon-bor-rpc.publicnode.com",
    "https://rpc.ankr.com/polygon",
    "https://polygon.api.onfinality.io/public",
]

# Polymarket / CTF contracts on Polygon
USDC_E = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
CTF = Web3.to_checksum_address("0x4D97DCd97eC945f40cF65F87097ACe5EA0476045")
EXCHANGE = Web3.to_checksum_address("0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E")
NEG_RISK_CTF_EXCHANGE = Web3.to_checksum_address("0xC5d563A36AE78145C45a50134d48A1215220f80a")
NEG_RISK_ADAPTER = Web3.to_checksum_address("0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296")

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}],
     "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}],
     "name": "allowance", "outputs": [{"name": "remaining", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}],
     "name": "approve", "outputs": [{"name": "success", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
]
CTF_ABI = [
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "operator", "type": "address"}],
     "name": "isApprovedForAll", "outputs": [{"name": "", "type": "bool"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "operator", "type": "address"}, {"name": "approved", "type": "bool"}],
     "name": "setApprovalForAll", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "id", "type": "uint256"}],
     "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
]

MAX_UINT = (1 << 256) - 1


# ----- core -----------------------------------------------------------------

@dataclass
class Wallet:
    address: str
    private_key: str

    @classmethod
    def load(cls, path: Path = WALLET_PATH) -> "Wallet":
        d = json.loads(path.read_text())
        addr = Web3.to_checksum_address(d["address"])
        pk = d["private_key"]
        if not pk.startswith("0x"):
            pk = "0x" + pk
        derived = Account.from_key(pk).address
        if derived.lower() != addr.lower():
            raise RuntimeError("wallet.json: private_key does not match address")
        return cls(address=addr, private_key=pk)


def pick_rpc() -> Web3:
    for rpc in POLYGON_RPCS:
        try:
            w = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
            if w.eth.chain_id == CHAIN_ID:
                return w
        except Exception:
            continue
    raise RuntimeError("no working polygon RPC")


class Polyclaude:
    def __init__(self, wallet: Wallet, w3: Web3, client: ClobClient):
        self.wallet = wallet
        self.w3 = w3
        self.client = client

    # ---- factory ----
    @classmethod
    def load(cls, *, ensure_creds: bool = True) -> "Polyclaude":
        wallet = Wallet.load()
        w3 = pick_rpc()
        # signature_type=0 (EOA), funder=EOA address (the EOA holds the USDC and trades directly)
        client = ClobClient(
            host=CLOB_HOST, chain_id=CHAIN_ID, key=wallet.private_key,
            signature_type=0, funder=wallet.address,
        )
        if ensure_creds:
            creds = cls._load_or_create_creds(client)
            client.set_api_creds(creds)
        return cls(wallet, w3, client)

    @staticmethod
    def _load_or_create_creds(client: ClobClient) -> ApiCreds:
        if CREDS_PATH.exists():
            d = json.loads(CREDS_PATH.read_text())
            return ApiCreds(api_key=d["api_key"], api_secret=d["api_secret"], api_passphrase=d["api_passphrase"])
        creds = client.create_or_derive_api_creds()
        CREDS_PATH.write_text(json.dumps({
            "api_key": creds.api_key,
            "api_secret": creds.api_secret,
            "api_passphrase": creds.api_passphrase,
        }))
        os.chmod(CREDS_PATH, 0o600)
        return creds

    # ---- read-only status ----
    def balances(self) -> dict[str, float]:
        addr = self.wallet.address
        matic = self.w3.eth.get_balance(addr) / 1e18
        usdce = self.w3.eth.contract(address=USDC_E, abi=ERC20_ABI).functions.balanceOf(addr).call() / 1e6
        return {"MATIC": matic, "USDC.e": usdce}

    def allowances(self) -> dict[str, dict]:
        addr = self.wallet.address
        usdc = self.w3.eth.contract(address=USDC_E, abi=ERC20_ABI)
        ctf = self.w3.eth.contract(address=CTF, abi=CTF_ABI)
        out: dict[str, dict] = {"USDC->Exchange": {}, "USDC->NegRiskExchange": {}, "USDC->NegRiskAdapter": {},
                                 "CTF->Exchange": {}, "CTF->NegRiskExchange": {}, "CTF->NegRiskAdapter": {}}
        for name, spender in [("USDC->Exchange", EXCHANGE), ("USDC->NegRiskExchange", NEG_RISK_CTF_EXCHANGE), ("USDC->NegRiskAdapter", NEG_RISK_ADAPTER)]:
            v = usdc.functions.allowance(addr, spender).call()
            out[name] = {"raw": v, "ok": v >= MAX_UINT // 2}
        for name, spender in [("CTF->Exchange", EXCHANGE), ("CTF->NegRiskExchange", NEG_RISK_CTF_EXCHANGE), ("CTF->NegRiskAdapter", NEG_RISK_ADAPTER)]:
            v = ctf.functions.isApprovedForAll(addr, spender).call()
            out[name] = {"raw": bool(v), "ok": bool(v)}
        return out

    def print_status(self) -> None:
        bals = self.balances()
        print(f"address: {self.wallet.address}")
        print(f"MATIC:  {bals['MATIC']:.6f}")
        print(f"USDC.e: {bals['USDC.e']:.4f}")
        for name, info in self.allowances().items():
            mark = "OK " if info["ok"] else "ERR"
            print(f"  [{mark}] {name}: {info['raw']}")

    # ---- allowance setup ----
    def ensure_allowances(self, *, dry_run: bool = False) -> list[str]:
        """Set any missing allowances. Returns list of tx hashes broadcast."""
        addr = self.wallet.address
        nonce = self.w3.eth.get_transaction_count(addr)
        gas_price = self.w3.eth.gas_price
        usdc = self.w3.eth.contract(address=USDC_E, abi=ERC20_ABI)
        ctf = self.w3.eth.contract(address=CTF, abi=CTF_ABI)
        actions: list[tuple[str, dict]] = []

        cur = self.allowances()
        for name, spender in [("USDC->Exchange", EXCHANGE), ("USDC->NegRiskExchange", NEG_RISK_CTF_EXCHANGE), ("USDC->NegRiskAdapter", NEG_RISK_ADAPTER)]:
            if not cur[name]["ok"]:
                tx = usdc.functions.approve(spender, MAX_UINT).build_transaction({
                    "from": addr, "nonce": nonce, "gas": 100_000, "gasPrice": gas_price, "chainId": CHAIN_ID,
                })
                actions.append((name, tx)); nonce += 1
        for name, spender in [("CTF->Exchange", EXCHANGE), ("CTF->NegRiskExchange", NEG_RISK_CTF_EXCHANGE), ("CTF->NegRiskAdapter", NEG_RISK_ADAPTER)]:
            if not cur[name]["ok"]:
                tx = ctf.functions.setApprovalForAll(spender, True).build_transaction({
                    "from": addr, "nonce": nonce, "gas": 100_000, "gasPrice": gas_price, "chainId": CHAIN_ID,
                })
                actions.append((name, tx)); nonce += 1

        if not actions:
            print("all allowances already set")
            return []
        # Estimate cost
        total_gas = sum(a[1]["gas"] for a in actions)
        cost_matic = total_gas * gas_price / 1e18
        bals = self.balances()
        print(f"plan: {len(actions)} approvals, ~{total_gas} gas, ~{cost_matic:.6f} MATIC (have {bals['MATIC']:.6f})")
        for name, _ in actions:
            print(f"  - {name}")
        if dry_run:
            return []
        if bals["MATIC"] < cost_matic * 1.5:
            raise RuntimeError(f"insufficient MATIC: need ~{cost_matic*1.5:.4f} for safety, have {bals['MATIC']:.4f}")

        hashes: list[str] = []
        for name, tx in actions:
            signed = self.w3.eth.account.sign_transaction(tx, private_key=self.wallet.private_key)
            h = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            hh = h.hex()
            print(f"sent {name}: 0x{hh}")
            hashes.append(hh)
            r = self.w3.eth.wait_for_transaction_receipt(h, timeout=180)
            print(f"  block {r['blockNumber']}, status {r['status']}")
        return hashes

    # ---- market data ----
    def orderbook(self, token_id: str) -> dict:
        ob = self.client.get_order_book(token_id)
        return {
            "bids": [(float(b.price), float(b.size)) for b in ob.bids],
            "asks": [(float(a.price), float(a.size)) for a in ob.asks],
        }

    # ---- trading ----
    def place_limit_buy(self, token_id: str, *, price: float, usd_size: float, gtc: bool = True, post_only: bool = False) -> dict:
        """Buy YES (or whichever token_id corresponds to). usd_size is dollars; shares = usd_size/price."""
        size_shares = round(usd_size / price, 4)
        return self._place(token_id, price=price, size=size_shares, side=BUY, gtc=gtc, post_only=post_only)

    def place_limit_sell(self, token_id: str, *, price: float, shares: float, gtc: bool = True, post_only: bool = False) -> dict:
        return self._place(token_id, price=price, size=round(shares, 4), side=SELL, gtc=gtc, post_only=post_only)

    def _place(self, token_id: str, *, price: float, size: float, side: str, gtc: bool, post_only: bool) -> dict:
        order_args = OrderArgs(token_id=str(token_id), price=float(price), size=float(size), side=side)
        order_type = OrderType.GTC if gtc else OrderType.FOK
        signed = self.client.create_order(order_args)
        return self.client.post_order(signed, orderType=order_type, post_only=post_only)

    def open_orders(self, market: str | None = None) -> list[dict]:
        return self.client.get_orders(OpenOrderParams(market=market) if market else None)

    def cancel(self, order_id: str) -> dict:
        return self.client.cancel(order_id)


# ----- CLI helpers ----------------------------------------------------------

def _cmd_status(_argv: list[str]) -> int:
    pc = Polyclaude.load(ensure_creds=False)
    pc.print_status()
    return 0


def _cmd_init(_argv: list[str]) -> int:
    pc = Polyclaude.load(ensure_creds=True)
    pc.print_status()
    return 0


def _cmd_approve(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    pc = Polyclaude.load(ensure_creds=False)
    pc.print_status()
    print()
    pc.ensure_allowances(dry_run=dry)
    return 0


def _cmd_orderbook(argv: list[str]) -> int:
    if not argv:
        print("usage: polyclaude_client.py orderbook <token_id>", file=sys.stderr); return 2
    pc = Polyclaude.load(ensure_creds=False)
    ob = pc.orderbook(argv[0])
    print(json.dumps(ob, indent=2))
    return 0


COMMANDS = {
    "status": _cmd_status,
    "init": _cmd_init,
    "approve": _cmd_approve,
    "orderbook": _cmd_orderbook,
}


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"usage: polyclaude_client.py <{'|'.join(COMMANDS)}> [args]", file=sys.stderr)
        sys.exit(2)
    sys.exit(COMMANDS[sys.argv[1]](sys.argv[2:]))
