# Capital ledger — external funding

**Verified initial trading capital: $170.00 nominal stablecoin value.** The two receipts below are confirmed by successful on-chain receipts, token Transfer logs, decimals and block timestamps. Separate gas and funding costs are excluded. This is a targeted initial-funding audit, not an exhaustive lifetime cashflow reconciliation. [Audit](../research/2026-10-25-initial-funding-audit.json).

| Exact UTC receipt time | Amount | Asset / chain | Project wallet | Transaction |
|---|---:|---|---|---|
| 2026-04-25 13:12:44 | 70.000000 | USDC.e / Polygon | `0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B` | [Confirmed](https://polygonscan.com/tx/0x67cf7413e374386200be3b4f8aa1824458d67afa66642f110aa4914087e7628a) |
| 2026-04-29 19:16:57 | 100.000000 | Native USDC / Arbitrum | `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6` | [Confirmed](https://arbiscan.io/tx/0x5895b7c9545d30fd1e570c2905f4a5d253aaa6f1aed63e069cc4127b653d75e8) |

- Both token transfers came from `0x9465352feba9826f9cbe40cdb9ee9d5b5bde7448`, outside the two project wallets. Historical funding acknowledgments support the operator-contribution classification; on-chain addresses alone do not identify beneficial ownership. The Polygon transaction used a relayer; its transaction sender differs from its token sender.
- Polygon token: `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174` (bridged USDC, displayed USDC.e; contract symbol USDC). Arbitrum token: `0xaf88d065e77c8cC2239327C5EDb3A432268e5831`. Both use six decimals.
- The original April25 date-only and April29 ~19:55 acknowledgment anchors were approximate. The contribution CSV now uses the exact receipt timestamps; amounts remain $70 then $170. Existing performance observations are unchanged.

## Separate gas and other transfers

- Journal-reported gas funding: approximately **53.85 POL** on April25 (53.81 remained after approvals) and **0.000638 ETH** on Arbitrum April29. Native funding transactions and transaction-time USD values remain unverified. These amounts do not establish an all-in USD contribution total; stale gas-price estimates are not carried forward.
- The Polygon funding receipt also contains **0.007098 USDC.e** sent from the funding address to another recipient, not the project wallet. It is separate from the 70 received; its fee interpretation is an inference. Full funding/network costs are not reconciled.
- Arbitrum's **5 USDC** inbound on April29 20:50:13 is an Ostium collateral timeout refund, not new funding: [transaction](https://arbiscan.io/tx/0xd2dec6065069bb93fec524b4374704f06dfb4af4c2514586c572589a1759bcc2), matched to TradingStorage and the dated journal.
- **0.000099 USDC** arrived April29 19:17:10 from a different address. Ownership/purpose remain unknown; it is unclassified, below one nominal cent, and is not asserted to be operator funding: [transaction](https://arbiscan.io/tx/0x2b8c732e84d5119b7d020f91093d1c5e2306ffaddfce0a60a88e124fa5f5269e).

## Ongoing record

No later operator trading contribution or withdrawal is documented here. The bounded audit does not prove that no other external flow occurred. Record future verified external deposits/withdrawals immediately with transaction references. Bridges, swaps, Aave supply/withdrawals, sleeve transfers and protocol refunds relocate existing capital; do not count them as contributions.
