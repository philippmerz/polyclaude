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
