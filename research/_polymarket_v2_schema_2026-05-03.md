# Polymarket Exchange V2 — Order Schema (extracted 2026-05-03)

Reverse-engineered from polymarket.com's JS bundle (chunk `0oute_rtdxmew.js`)
after both py-clob-client (0.34.6) and TS @polymarket/clob-client (5.8.1) started
returning `400 order_version_mismatch` on order placement. Persisting here
because /tmp was wiped by the VM's OOM-driven reboot.

## Contract addresses (Polygon, chainId=137)

```
exchange (v1, deprecated):     0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E
exchangeV2 (active):           0xE111180000d2663C0091e4f400237545B87B996B
negRiskExchange (v1):          0xC5d563A36AE78145C45a50134d48A1215220f80a
negRiskExchangeV2 (active):    0xe2222d279d744050d28e00520010520000310F59
```

## EIP-712 domain (v2)

```
name              "Polymarket CTF Exchange"
version           "2"            (was "1" in v1)
chainId           137
verifyingContract <exchangeV2 or negRiskExchangeV2>
```

## V2 Order struct

```
salt:           uint256
maker:          address
signer:         address
tokenId:        uint256
makerAmount:    uint256
takerAmount:    uint256
side:           uint8       (0 = BUY, 1 = SELL — same as v1)
signatureType:  uint8       (0 = EOA, 1 = POLY_PROXY, 2 = POLY_GNOSIS_SAFE)
timestamp:      uint256     (Unix milliseconds — Date.now() in JS)
metadata:       bytes32     (default 0x00...0)
builder:        bytes32     (default 0x00...0)
```

## Diff vs v1 schema

| Field | v1 | v2 |
|---|---|---|
| `taker` | `address` | **REMOVED** |
| `expiration` | `uint256` | **REMOVED** |
| `nonce` | `uint256` | **REMOVED** |
| `feeRateBps` | `uint256` | **REMOVED** (likely set per-market server-side now) |
| `timestamp` | — | **NEW** uint256 (Date.now() ms) |
| `metadata` | — | **NEW** bytes32 |
| `builder` | — | **NEW** bytes32 |

## Field semantics (from JS bundle)

```js
async buildOrder({maker, tokenId, makerAmount, takerAmount, side, signer,
                  signatureType, timestamp, metadata, builder, expiration}) {
    if (!signer) signer = maker;
    if (signer !== <signer.address>) throw "signer does not match";
    return {
        salt: this.generateSalt(),     // random uint256
        maker, signer, tokenId, makerAmount, takerAmount,
        side, signatureType: signatureType ?? EOA,
        metadata: metadata ?? bytes32Zero,
        builder: builder ?? bytes32Zero,
        timestamp: timestamp ?? Date.now().toString(),
        expiration: expiration ?? "0"   // not in EIP-712 fields list, may still be tracked
    };
}
```

The `message` passed to `signTypedData`:
```js
message: { salt, maker, signer, tokenId, makerAmount, takerAmount,
           timestamp, side: +("BUY" !== side), signatureType,
           metadata, builder }
```

(Note: `expiration` exists on the OrderData but is NOT in the EIP-712 typed-data
`message` per the v2 schema — only the 11 fields above.)

## API request body (best guess, same as v1 shape)

```json
{
  "order": <signed v2 order, with signature appended>,
  "owner": "<api_key>",
  "orderType": "GTC" | "FOK" | "FAK" | "GTD",
  "postOnly": false
}
```

POST to same `/order` endpoint at `https://clob.polymarket.com`. Same HMAC
auth headers. Only the inner `order` payload changes.

## Implementation status

- [ ] Python v2 signer (using `eth_account` for EIP-712 signing)
- [ ] Wire into `scripts/polyclaude_client.py` as a fallback or replacement code path
- [ ] Test on a deeply-below-market BUY (won't fill, then cancel) to verify acceptance
- [ ] Confirm CANCEL still works on v2 orders
- [ ] Confirm balance/allowance check (USDC approval to v2 exchange contract may differ from v1)

## Open questions

1. **Token approvals**: USDC and CTF approvals were granted to v1 exchange. Need to check if v2 exchange address requires its own approvals (`USDC.allowance(eoa, exchangeV2)` — verify current state).
2. **negRisk markets**: v2 negRiskExchange is `0xe2222...`. Different exchange address, same v2 schema presumably.
3. **`expiration` field**: present in OrderData but not in the EIP-712 typed message. Server might still expect it in the JSON body. Test will tell.
4. **API key compatibility**: existing API creds derived from v1 exchange — likely still work since they're independent of order schema, but verify.

## Progress 2026-05-04

### v2 signer landed working
`scripts/clob_v2.py` signs+POSTs v2 orders directly via REST. Three iterations to find the right body shape:
- **Iteration 1** (only 11 EIP-712 typed fields): server returns `400 "Invalid order payload"`.
- **Iteration 2** (11 v2 fields + 4 v1 backward-compat fields `taker`/`expiration`/`nonce`/`feeRateBps`, salt as int): server **accepts the schema**, returns `400 "not enough balance / allowance: balance: 0, order amount: 5000000"`.
- **Verdict**: API expects BOTH v1 and v2 fields present in the body. Signature itself is what determines which exchange contract validates the order. salt is sent as JSON number (not string), side as `"BUY"/"SELL"` (not uint8). Documented in `clob_v2._signed_order_to_api_body()`.

### MAJOR: v2 collateral is no longer USDC.e
`getCollateral()` on `0xE111180000d2663C0091e4f400237545B87B996B` returns
`0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB` — a token called **"Polymarket USD"** (pUSD), 6 decimals, total supply ~$316M. This is a Polymarket-deployed transparent proxy (impl `0x6bbcef9f7ef3b6c592c99e0f206a0de94ad0925f`) with a `mint(address,uint256)` selector but no public `deposit/wrap/depositFor`. The mint is presumably restricted to a minter role.

Implications:
- v2 trading requires pUSD, NOT USDC.e. Our entire $5.05 sleeve buffer is in USDC.e.
- Existing 9 positions and their max-payout were denominated in USDC.e via the v1 exchange. They should still resolve in USDC.e since they live on v1.
- To open NEW positions (or close v1 positions early via the v2 exchange) we need to acquire pUSD. Method TBD — likely a wrap/deposit contract elsewhere, or a Polymarket-frontend-only flow.

Approvals SET 2026-05-04 (in case useful for someone with pUSD):
- USDC.e → EXCHANGE_V2 (`0xE111180000d2663C0091e4f400237545B87B996B`): MAX
- USDC.e → NEG_RISK_EXCHANGE_V2 (`0xe2222d279d744050d28e00520010520000310F59`): MAX
- pUSD → EXCHANGE_V2: not yet (no balance to approve from)

### Next steps to actually trade on v2
1. Find the pUSD mint/wrap mechanism (could require browsing Polymarket frontend for the deposit UI, or another bundle inspection round to find the wrapper contract).
2. Once a wrapper is identified and we have pUSD: approve pUSD to v2 exchanges, then `clob_v2.py buy/sell` should work end-to-end.
3. Existing v1 positions are unaffected — they remain valid and tradeable on the v1 exchange via the existing py-clob-client (which still works on v1, just not on v2).
