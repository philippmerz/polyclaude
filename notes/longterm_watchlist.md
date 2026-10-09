# Project-only watchlist

Updated 2026-10-09. The original mixed watchlist is preserved verbatim in [the dated archive](longterm_watchlist_archive_2026-10-06.md) (SHA-256 `79848849682474b80d0ee19461dad41a2eea14cfaca8b9f118ed1589bed500e0`). Its stock, brokerage, and older candidate material is historical evidence only, not active project guidance.

Recurring stock and personal-brokerage research, Sunday reviews, equity-price monitoring, and IBKR surfacing were retired on 2026-10-06. This file tracks only project-accessible, on-chain review gates. It makes no trade recommendation or automatic entry authorization.

## Active review gates

| Asset | Review gate | Required evidence before any allocation |
|---|---:|---|
| UNI | $3.25 | The gate is a valuation review trigger, not a buy. The Oct 5 evidence verifies proposal 102 execution and updated Arc control configuration, but not pool fee collection, Releaser activity, or sustainable net UNI burn after the 20M UNI/year treasury-growth budget. Configuration alone did not establish a calibrated positive return into the January 2027 evaluation. |
| AAVE | $105 | The gate is a review trigger, not a buy. Require evidence of funded and executed recurring revenue-funded purchases with a disclosed cadence, and review incident liabilities. The Sep 30 Arbitrum spot-route quote showed a 0.612% loss on a $20 round trip before gas or funding; it is dated and must be refreshed before use. |

These gates come from the active [trigger configuration](watchlist_triggers.json) (UNI and AAVE rationales). The decision trail is in [the Sep 30 broader investment review and route update](journal.md), lines 21321–21348, and [the Oct 5 UNI control review](journal.md), lines 24322–24420. The original AAVE catalyst and route-cost evidence is retained in the [archived review](longterm_watchlist_archive_2026-10-06.md), lines 678–698.

Oct 5 UNI evidence is recorded in the journal's 22:00 review and follow-up. The two-RPC proposal/control reads, independent Arc read, decoded proposal actions and price captures remain local verification artifacts. They establish configuration, without establishing actual fee collection or burn.

## Manual on-chain equity candidates — Oct 9 route review

| Instrument | Exact Base identity (chain 8453) | Review evidence and entry requirements |
|---|---|---|
| MSFTc | `0xB200000000000000000000Ab99cFa739E253872B` | $20 Slipstream purchase quoted 0.03785510 tokens; same-quantity reverse 19.979981 USDC at block 52,377,143. Microsoft reported 43% Azure growth and adjusted annual EPS $17.28; next announced results Oct 28. Establish a return thesis by January, lawful eligibility, and the route/cost gates below. No buy price or allocation is certified. |
| NVDAc | `0xb20000000000000000000078ee7ce2fE4908108C` | $20 purchase quoted 0.08515405 tokens; same-quantity reverse 19.979999 USDC at the same block. NVIDIA reported Q2 FY27 revenue $96.2B and Q3 guidance $108B ±2%. Underwrite demand, earnings/multiple risk and AI correlation; growth is not proof of excess return. No allocation. |

These are stock-backed tokens researched on demand, with no brokerage workflow or recurring
equity-price polling. The [Oct 9 journal](journal.md) contains primary sources and the exact
read-only route/cost review. Quotes are dated independent reads against unchanged pool state,
not a guaranteed round trip. The existing swap tools do not execute Slipstream; a vetted writer
and fresh complete funding/exit quotes are required. DEX transfers can be permissionless, but
issuer redemption rights require KYC vesting. A no-KYC position therefore needs an explicitly
underwritten DEX exit and issuer/custody/control risks, plus lawful non-U.S./jurisdiction eligibility.
There is no automatic buy trigger or new watcher for either instrument.

## Project allocation standard

Project positions must fit the less-than-one-year horizon and the January 2027 evaluation. Before considering an allocation, record and verify the literal token contract or asset ID, chain, venue/pool, and project wallet route. Confirm lawful access and the executable route, then measure current buy and sell depth for the intended size, fees, spread, slippage, gas, funding, liquidity, settlement, counterparty/protocol risk, and correlation. Compare net expected return with same-chain Aave and other project-accessible alternatives. Revalidate stale evidence at decision time. A price gate alone never authorizes a buy.
