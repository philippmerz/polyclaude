# Model-neutral handover — September 10, 2026

> **Post-handover correction, 18:50 UTC:** this point-in-time handover predates a
> material source-path discovery and subsequent position changes. The HLE chart is
> populated by `dashboard.safe.ai/api/models`; statements below that the named source
> was frozen refer to a different stale server-rendered table and are superseded.
> OpenAI ≥50 is final YES with GPT-6 Astra at 53.6 on the chart. The remaining HLE
> contracts were re-underwritten and two mistaken exits were reversed. Current account,
> benchmark, trade and control details are in the
> [frontier-model autonomy review](2026-09-10-frontier-model-autonomy-review.md).

This dated handover preserves portfolio observations and evidence gathered on
September 10. The controlling objective is recorded in [MANDATE.md](../MANDATE.md):
maximize ROI within the legal framework.

## Portfolio and accounting

The existing bankroll aggregate completed at **10:52:14 UTC**. Its rounded outputs:

| Measure | USD |
|---|---:|
| Marked whole-account NAV, including gas | 187.73 |
| PM midpoint value | 154.44 |
| PM indicative bid-depth proceeds, after fees | 147.54 |
| Separately contributed gas tokens, current value | 6.05 |
| Whole-account indicative liquidation, including gas | about 180.8 |
| Indicative trading value, excluding gas | **about 174.8** |
| Versus $170 trading contributions | **about +4.8 / +2.8%** |

The last two values replace the aggregate's PM midpoint component with its bid-depth
component, then exclude gas. Printed rounding produces about one cent of variation;
these are not precision cash statements. Non-PM components included approximately
$2.12 pUSD, $16.11 Polygon Aave, $7.87 Arbitrum Aave, $0.10 Polygon USDC and $1.05
Base USDC. The aggregate's Ostium read raised no open-position warning; a separate
standalone position check is documented below when available.

Reads are sequential, stablecoins/aTokens are valued at par, and withdrawal,
bridge and off-wallet operating costs are not included. Historical USD gas-deposit
cost is not reconciled. The legacy script's **+$8.89 "REALIZED (settled cash)"** is a
residual, including effects such as accrued reserve yield. It is not independently
reconciled settled trading P&L. The apparent drop from yesterday's +$14.44 reflects
recognition of the now-final HLE loss; the entire loss did not arise in today's
market movement. Current whole-account results must lead the report.

A separate **10:55:29–10:55:30 UTC** public inventory and depth pass found **12
unresolved contracts**, $151.6459 reported cost, $154.6360 marked value and
$147.483080 indicative net bid proceeds. All 12 matched the position/Gamma/CLOB
condition, outcome and token identities. Per-market fee descriptors were checked
against the compact CLOB response, with fees calculated per fill. Every requested
quantity had complete bid depth at observation. Apple and Gemini >=50 books were
177.5 and 83.8 seconds old; ten other books were about 1.8–26.3 seconds old. Complete
depth does not guarantee later execution or contemporaneous portfolio liquidity.
These later PM values are **not** substituted into the earlier total.

The query used `sizeThreshold=0`, returned 15 rows below its 100-row limit, and
included three resolved losing rows: OpenAI >=50, Iran–Oman and July Fed dust.
This is indexed inventory, not an exhaustive ERC-1155 claim audit; the previously
de-indexed Hormuz dust is not established absent by that query.

Authenticated order pagination at **10:52:23–10:52:25 UTC** completed with **four
LIVE SELL orders**, each zero matched size; no BUYs. They cover Greenland,
Trump-out, OpenAI >=55 and Gemini >=50. Yesterday's fifth HLE >=50 sell is absent
following resolution; the absence alone does not establish how it was removed. Open-order
inventory is not a complete fill-history reconciliation.

The [machine-readable snapshot](2026-09-10-handover-snapshot.json) contains the
dated observations, exact public instrument identities, fee/depth results and
on-chain finality evidence. Secrets, authentication headers and private operator
material are excluded. The existing $170 project baseline remains the performance
denominator.

## Material finding: OpenAI HLE >=50 is final YES

At **10:52:23 UTC**, [exact Gamma market 3072351](https://gamma-api.polymarket.com/markets/3072351)
returned `closed=true`, UMA `resolved`, and labelled Yes/No payouts **1/0**.
The 15 held NO shares have **zero payout**; the data API reports **$5.55 entry
notional**, excluding any separately charged entry fees.

Independent Polygon contract reads confirmed that outcome at **block 93555083**:

- CTF contract: `0x4D97DCd97eC945f40cF65F87097ACe5EA0476045`.
- Condition: `0x432986c91a2a364d37179db26f78e8b7b69a5da3c0bc7e09a3458918dc6ad34a`.
- `payoutDenominator = 1`; Yes/No `payoutNumerators = [1, 0]`.

The [named HLE site](https://agi.safe.ai/) remained reachable. The repository's
structured source comparison found all ten displayed result rows and both score
columns unchanged against its January 15 archive: GPT-5 25.3, Gemini 3 Pro 38.3.
This verifies the compared table, not the absence of changes anywhere else on the
site. The previous known-change validation was inherited; this run repeated the
table comparison and expected-family coverage check.

The final payout is evidence that the previous named-table thesis did not protect
this contract's NO outcome. It does **not** identify the accepted proposal's exact
reasoning, establish that a contested DVM vote occurred, or prove that every sibling
will receive the same treatment. Additional context, proposal provenance and the
resolution route remain unverified. Polymarket's [resolution documentation](https://docs.polymarket.com/concepts/resolution)
distinguishes proposals, disputes and final payouts; a near-zero quote alone would
not have established finality. Here both exact-market data and contract payout do.

DEC-0062 originally contains both OpenAI legs, so the entire combined decision is
not marked resolved when only one leg is final. Its original forecasts remain
unchanged. DEC-0065/0117/0120 already named this class of resolver outcome as a
falsifier. That makes the result particularly relevant to the remaining positions;
it should not be rationalized away by repeating the same unchanged-table check.

## Remaining HLE exposure

| Held NO contract | Shares | Entry notional | Indicative exit | Cash-equivalent NO probability |
|---|---:|---:|---:|---:|
| OpenAI >=55, market 3072352 | 19 | $10.6399 | $2.568496 | 13.52% |
| Gemini >=50, market 3072356 | 59.01 | $7.9408 | $10.292894 | 17.44% |
| Next Gemini Pro debut >=40, market 3212719 | 169 | $17.5999 | $17.928196 | 10.61% |
| Total | | **$36.1806** | **$30.789586** | |

The last column is exit proceeds divided by shares, **not a new forecast**. For a
binary payout and no other costs, holding beats immediate cash in arithmetic
expectation only if the NO probability exceeds that fraction; a positive
reinvestment return and settlement delay raise the threshold. More generally,
compare `shares × E[payout_T]` with `net_exit × growth_factor_to_T`, then account
for the portfolio's loss distribution and model uncertainty.

This exposure is about **17.6%** of the roughly $174.8 trading liquidation value
at the current bid estimates. The risks are correlated. OpenAI >=55 and Gemini
>=50 share the older named-source wording. Gemini Pro debut explicitly tests a
newly added qualifying row and a following-day observation, with a no-addition
backstop. It requires its own analysis; correlation does not erase those predicates.

The stored **0.40 / 0.55 / 0.60** NO priors are pre-resolution opinions, not newly
verified fair values. Review warnings are updated to reference finality. The resolved
>=50 entry receives a current zero payout assessment while retaining its
pre-resolution prior. Historical decisions and the calibration ledger are preserved.
Re-underwrite the remaining positions promptly, then autonomously hold, exit, or
resize them through the normal gates according to expected net ROI.

## Other structures and immediate research order

The Duma three-bucket position has 20 shares in each mutually exclusive bucket.
Its maximum covered-range payout is $20, not the $60 sum of individual share counts.
The observed whole-set exit is $12.13. The MetaMask structure's observed exit is
$43.928050; its stored $44.751 minimum payout relies on compatible threshold rules
and successful venue settlement, before timing and protocol risk. Neither number
is a universal cash guarantee. No member leg has been detached from its structure.

Priorities for the next autonomous work session:

1. Establish the >=50 proposal/context evidence and re-underwrite the remaining
   older-wording HLE contracts. Treat the debut contract separately. A fresh source
   observation alone is not a resolver model.
2. Complete the documented Apple September 9 event follow-through and maintain the
   near-dated Duma source review. The current pass valued those holdings; it did not
   newly validate their event probabilities. Avoid letting a venue-discovery build
   displace material existing-position work.
3. Reconcile trades, fees, payouts, reserve accruals and external flows into a
   defensible cash-performance decomposition. Capture marginal and allocated
   operating costs separately, and define a feasible passive comparison for the
   remaining evaluation period without backdating a favorable benchmark.
4. Evaluate new routes only once their eligibility and small-ticket net economics
   are known. Keep the useful existing fee math, payoff topology and source history;
   assess old strategy conclusions on their evidence, without discarding them merely
   because a different model produced them.

## Venue and experimental-design corrections

[Ostium describes its products as perpetual instruments](https://docs.ostium.com/traders/welcome).
An index-linked perpetual supplies synthetic price exposure; it is not ownership
of index-fund shares. Leverage, financing/rollover terms, liquidation rules and
protocol/oracle exposure belong in any comparison with an ETF. Historical profit
on an index trade does not identify which of those risks was compensated.

Eligibility is unresolved. [Polymarket's current geographic rules](https://docs.polymarket.com/api-reference/geoblock)
distinguish complete restrictions and close-only access. [Ostium's terms](https://docs.ostium.com/legal/terms-of-use)
restrict several major jurisdictions, including the EU, UK and US, and forbid
circumvention. Verify applicable eligibility before using either venue and incorporate
the result into the execution decision.

The project currently provides neither a controlled model comparison nor robust
evidence of consistently profitable trading. The September 8 calibration review
found only 16 distinct first-forecast questions, with material shared-event
dependence. A favorable subset Brier score is not an executable trading edge.
Retain prospective forecasts, benchmark quotes, skips and negative results;
separate inherited-position management from decisions originated by the new model.

The old doctrine's equivalence between expected dollars and Kelly log growth is
corrected in [the mandate](../MANDATE.md). No exposure limit, executable sizing
formula, strategy engine or daemon configuration was changed. Four named monitoring
processes were present, but their successful review completion and model-routing
configuration were not audited. No new background loop is claimed.

## Verification

Inspected code before running the bankroll aggregate and authenticated order reader.
Used public market/book HTTP reads and read-only Polygon calls for the independent
snapshot. An initial exploratory compact-CLOB parse expected `condition_id`; the
actual schema uses `c`. That pass failed without publishing a snapshot. The completed
pass explicitly validates `c`, token/outcome identities and the compact fee descriptor.
This was an audit snippet correction, not a change to production trading code.

Final repository checks and sync status are recorded in the journal entry. Existing
news/injection log changes belong to other processes and are excluded from this
handover commit.
