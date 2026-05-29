# Capital Ledger — operator deposits in/out

> Authoritative record of EXTERNAL capital flows (operator → wallets, wallets → operator).
> NOT internal moves (bridges, swaps, Aave supply/withdraw, sleeve transfers) — those are
> not capital flows, they're relocations. Created 2026-05-29 after three operator questions
> (allocation / performance / funding) repeatedly hit reconstruction errors from scattered
> archive facts. Log every future external flow HERE, immediately, with tx ref where available.

## Deposits IN (operator → polyclaude)

| Date | Amount | Asset | Chain | Wallet | Purpose | Source |
|---|---|---|---|---|---|---|
| 2026-04-25 | 70.00 | USDC.e | Polygon | PM sleeve `0x9032…267B` | trading capital (kickoff; $60 target, slight overshoot) | journal_archive_2026-04 L11 |
| 2026-04-25 | ~53.8 | POL | Polygon | PM sleeve `0x9032…267B` | gas reserve (asked ~0.5, operator sent ~53.8) | journal_archive L23,L69 |
| 2026-04-29 | 100.00 | USDC | Arbitrum | crypto sleeve `0x83dA…3eE6` | trading capital (upsized from planned $50) | journal_archive L391 |
| 2026-04-29 | ~0.000638 | ETH | Arbitrum | crypto sleeve `0x83dA…3eE6` | gas (via Bungee, after a retry loop) | journal_archive L391 |

**Totals in:**
- Trading capital: **$170.00** ($70 PM + $100 crypto) — this IS the "$170 reference"; both deposits were week-one, NOT a later top-up.
- Gas: ~53.8 POL + ~0.001 ETH. POL USD-value at-transfer not recorded (April price unknown); ~$4.8 at $0.089 today, likely more when sent. Gas ~95% unspent (Polymarket trading is gasless EIP-712).
- **Total ≈ $170 trading + ~$5–15 gas ≈ $175–185.**

## Withdrawals OUT (polyclaude → operator)

| Date | Amount | Asset | Chain | Notes |
|---|---|---|---|---|
| (none yet) | | | | No capital returned to operator as of 2026-05-29. |

## Caveats / verification status

- Sourced from journal records, NOT an exhaustive on-chain inbound-transfer audit. No block-explorer API key configured. For an exact-to-the-cent reconciliation incl. every gas dust transfer: walk transfer logs via RPC, or add a Polygonscan/Arbiscan key to `~/.polyclaude/env`.
- No external deposits found after 2026-04-29. If a future tick/operator references a top-up, ADD A ROW HERE the same turn (executive-continuation + financial-accuracy discipline).
