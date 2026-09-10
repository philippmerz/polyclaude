# Investable index alternative review — 2026-09-10

## Decision

Do not open an index position today and do not liquidate a current Polymarket
position to fund one. Keep the approximately $15.62 Polygon and $7.87 Arbitrum
Aave reserves earning 3.007% and 2.740% annualized, respectively. The conclusion
is implementation-specific: broad equities remain in the opportunity set, but
neither index route available to this wallet has enough expected net edge over
cash and the current positions through the start-of-2027 evaluation.

The decision is medium confidence. Equity expected return over 112 days is much
less certain than the implementation costs. A material price decline, a larger
deployable balance, or a cheaper already-funded spot route can reverse it.

## Decision rule

The passive benchmark is now an investable outside option. Every position and
cash balance should compete against the highest expected net return that is
lawful and executable, after dividends, financing, spreads, fees, gas,
liquidity, correlation, model error and venue risk. Same-chain Aave is the
minimum investable hurdle, not a target allocation and not the entire
opportunity set. Historical benchmark outperformance measures the result so far;
it does not by itself forecast the next four months.

## Forward equity return assumption

For the S&P 500 price index through December 31, use the following subjective
distribution. It is an underwriting input rather than an observed probability
law.

| Scenario | Probability | SPX price return |
|---|---:|---:|
| Earnings/disinflation upside | 20% | +10% |
| Soft-landing base | 55% | +5% |
| Valuation/rate correction | 20% | -7% |
| Recession, war or inflation shock | 5% | -22% |

Arithmetic expected **price** return is +2.25%; the distribution has about 7.92%
terminal standard deviation. An entry now spans SPY's scheduled September 18
and December 18 ex-dates, so a dividend-owning implementation can capture two
quarterly distributions. The exact future amounts and xStocks tax treatment are
unknown; a conservative 0.45-0.75% net contribution puts modeled total return
near 2.7-3.0%. As a cross-check, Damodaran's September implied equity risk
premium plus the Treasury rate implies roughly 8.9% annual total return, or
about 2.75% over this horizon. FactSet's September 4 report showed strong
expected earnings growth but a 19.5 forward P/E, supporting positive drift while
leaving meaningful valuation risk. Sources: [Damodaran data](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm)
and [FactSet Earnings Insight](https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_090426.pdf). The ex-dates come from State Street's
[2026 SPDR distribution schedule](https://www.ssga.com/library-content/products/fund-data/etfs/us/distribution/SPDR_Dividend_Distribution_Schedule.pdf).

Expected-log return is lower than arithmetic return because the downside is
larger than the upside around the mean. This matters for a small bankroll and
makes a marginal arithmetic edge insufficient.

## Ostium US500

Ostium is a collateralized price perpetual. It does not own the ETF or credit
the dividend. The live V2 snapshot at 2026-09-10T20:15:32Z returned these fields
for SPX pair 10:

```text
takerFeeP=10000
lastRolloverLongPure=301176961
brokerPremium=159000000
lastRolloverBlock=503816306
```

The current TypeScript SDK treats the two rollover fields as 18-decimal
per-block fractions and Arbitrum as four blocks per second:

```text
long rollover / block = (301176961 + 159000000) / 1e18
daily fraction         = result * 4 * 86400 = 0.0001590371577216
annual rate            = daily * 365 = 5.804856%
```

The live fee formatter makes `takerFeeP=10000` a 1 bp opening fee. Current
round-trip quote spread was about 1.053 bp. The $0.10 oracle fee is reserved on
entry but refunded after a successful full close, so it is a liquidity need
rather than lifecycle cost in the normal-close case. From the snapshot through
the 2027-01-01 evaluation boundary, the calculation is approximately:

```text
rollover cost = 1.78370% * notional
direct drag   = 1.80423% * notional + gas
```

Ostium's static fee documentation currently says a 3 bp index opening fee and
describes stock/index rollover as SOFR plus a 1-2% premium, so the live state and
documentation do not agree. A future trade must price the live fields and the
actual order rather than either display in isolation. The documentation also
confirms the refundable oracle reserve and continuous rollover. [Ostium fee documentation](https://docs.ostium.com/traders/reference/fees)

| Notional | Direct drag before gas | Foregone 2.74% Aave carry | Return needed merely to match Aave |
|---:|---:|---:|---:|
| $7.873 | $0.142 | $0.066 | 2.65% + gas |
| $25 | $0.451 | $0.210 | 2.65% + gas |
| $35 | $0.631 | $0.295 | 2.65% + gas |
| $170 | $3.067 | $1.431 | 2.65% + gas |

This table is for 1x exposure. At the current $7.873 Arbitrum reserve, the
+2.25% expected SPX price return is about $0.177. It clears the approximately
$0.142 direct cost by only $0.035, then loses to approximately $0.066 of Aave
carry before gas. Even at whole-bankroll scale, expected net profit is only
about $0.758 versus about $1.431 in Arbitrum Aave, before expected-log penalty
or any allowance for contract/oracle risk.

Leverage can scale the small positive arithmetic spread over financing while
Aave carry applies only to collateral: ignoring gas and liquidation, it begins
to beat Aave near 1.9x. At 2x the modeled advantage on $7.873 collateral is less
than half a cent, and higher leverage raises liquidation/path dependence and
turns the expected-log result sharply negative under the scenario distribution.
It was not pursued because eligibility already fails, and neither that risk nor
protocol/model uncertainty is compensated by the tiny arithmetic edge.

There is also a current eligibility gate. Ostium's terms define its API and code
repositories as Services and prohibit trading with those Services for anyone
located in, resident in, or a citizen of the EU, among other jurisdictions; the
VM is currently in Finland. They expressly prohibit VPN circumvention. The local
SDK route therefore cannot be treated as legally executable on the facts in the
repository. [Ostium Terms of Use](https://docs.ostium.com/legal/terms-of-use)

The July oracle compromise adds a separate risk premium even though trader
collateral reportedly survived. No expected-loss estimate precise enough to
rescue the trade is available, and assigning zero is not defensible.

## Spot SPYx through Jupiter

The best spot route found is SPYx on Solana:

```text
native Solana USDC: EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
SPYx:               XsoCS1TfEyfFhfvj8EtZ528L3CaKBDBRqRapnBbDF2W
```

SPYx is an open-ended tracker certificate on SPDR S&P 500 ETF Trust, with a
stated 0.0945% annual management fee. xStocks says the secondary layer trades
freely on exchanges and DeFi without direct issuer interaction, while primary
issuance/redemption requires onboarding; dividends are reinvested through token
rebasing. Sources: [SPYx product page](https://assets.backed.fi/products/sp500-xstock)
and [xStocks mechanics](https://docs.xstocks.fi/docs/how-xstocks-work).

Fresh read-only Jupiter Lite quotes at about 20:16 UTC gave these immediate
USDC -> SPYx -> USDC round trips, before any slippage tolerance is exercised:

| Starting USDC | Returned USDC | Quote loss | Route |
|---:|---:|---:|---|
| $10 | $9.998534 | 0.01466% | Whirlpool |
| $20 | $19.997009 | 0.01496% | Whirlpool |
| $29 | $28.995582 | 0.01523% | Whirlpool |

The token identities and amounts were passed to Jupiter's read-only
[quote endpoint](https://dev.jup.ag/api-reference/swap/quote); no transaction was built or signed.

The AMM is not the expensive part. The wallet has no Solana key, SOL gas, or
token accounts, and the USDC currently sits on Arbitrum/Polygon. Circle lists
standard CCTP transfers from Arbitrum and Solana at 0 bps, but source gas,
destination forwarding/setup, Solana rent and the eventual return trip remain.
Circle's forwarding fees are dynamic and its Solana route may need associated
token-account setup. [Circle CCTP fees](https://developers.circle.com/cctp/concepts/fees)
and [forwarding service](https://developers.circle.com/cctp/concepts/forwarding-service).

Calls to Circle's official fee endpoint at 2026-09-10T20:36:33Z returned median
standard-transfer forwarding quotes of $0.331968 for Arbitrum -> Solana with
recipient setup, $0.146407 for Polygon -> Solana after setup, and $0.066966 for
Solana -> Arbitrum. The exact query paths were domains `3/5` with `forward=true`
and `includeRecipientSetup=true`, `7/5` with `forward=true`, and `5/3` with
`forward=true`. Funding from both Aave chains therefore puts the
full-reserve bridge-and-return total at about $0.545 before
Aave withdrawals, Polygon USDC.e conversion, source gas, the Jupiter trade, the
0.0945% annual SPYx fee, or writer risk. Circle documents that forwarding quotes
include dynamic destination gas and Solana account rent. [Circle fee API reference](https://developers.circle.com/api-reference/cctp/all/get-burn-usdc-fees)

The resulting lifecycle estimate remains $0.45-$0.85 for a one-off $20-$29
position; $0.45 describes the optimistic single-source case, while mobilizing
the full $23.49 reserve starts near $0.545 before the omitted costs. A 2.7-3.0%
gross equity return is about $0.63-$0.70. The full-reserve route needs at least
3.22% total return merely to equal about $0.21 of Aave carry, before the omitted
costs and issuer, certificate, Solana, bridge and new-writer risk. The economic
gate therefore fails without relying on unresolved legal details.

Jupiter's terms do not list Finland as a prohibited locality, but they defer to
applicable law. The repository does not establish the beneficial owner's
residence, citizenship, investor classification or tax treatment. That legal
work is only worth doing if the economic gate first clears. [Jupiter Terms of Use](https://developers.jup.ag/docs/legal/terms-of-use)

Hyperliquid SPYx was inferior at this size because its spot fees and fixed
withdrawal cost were larger. gTrade's index markets were inactive, no live
Synthetix SPX market was found, and the remaining bCSPX venue was too shallow.

## Existing position comparison

Growing each current full-exit quote by the top of the modeled 2.7-3.0% gross
ETF return range is an upper bound for a rotation because it omits the actual
index route's lifecycle cost. Every central hold value still wins except
Greenland's near tie; its small costless advantage disappears once even the
low end of the estimated fixed route cost is included.

| Economic position | Current net exit | Ideal ETF terminal | Central hold value | Decision |
|---|---:|---:|---:|---|
| Gemini next-Pro debut NO | $16.76 | $17.26 | $33.80 | Hold |
| Gemini score >=50 NO | $9.59 | $9.88 | $20.55 | Hold |
| Apple touchscreen NO | $18.07 | $18.61 | $26.95 | Hold |
| Trump out NO | $26.63 | $27.43 | $27.48 | Hold / premium maker sell |
| Greenland acquisition NO | $17.67 | $18.20 | $18.05 | Near tie; actual route cost reverses it |
| OpenAI score >=55 NO | $2.38 | $2.45 | $5.70 | Hold |
| Duma protected union | $11.47 | $11.81 | $14.40 | Hold complete set |
| MetaMask protected group | $43.34 | $44.64 | $46.80 | Hold complete group |

The table depends on subjective priors. Greenland is the only point estimate
close enough that a genuinely cheap ETF route can win, but the quoted route
cost is at least $0.45 while its costless modeled advantage is about $0.15. Its
live `.98` maker sell seeks a premium and is superior to crossing the book for
the currently costly one-off index route.

## Actions and reopening conditions

No market position, order, or reserve allocation changed. A stale 999,979.90 USDC
allowance from the legacy Ostium SDK was revoked with no open trade or active
limit order. Transaction:
[`0x36c77d9b8ecc6e71568aa3dd2ccffa1deb2ba22119677d6773a4b8fe3a56b337`](https://arbiscan.io/tx/0x36c77d9b8ecc6e71568aa3dd2ccffa1deb2ba22119677d6773a4b8fe3a56b337).
Receipt status was 1; post-flight allowance is zero.

Reopen index allocation when one of these changes:

- an eligible spot route's fully quoted lifecycle cost falls enough that
  conservative expected net return exceeds same-chain Aave and the marginal
  held position after an explicit issuer/protocol risk allowance;
- deployable capital is large enough to dilute fixed bridge/setup cost;
- an equity drawdown or new fundamental evidence raises forward expected return;
- a held position's realizable exit value overtakes its stressed hold value;
- Ostium eligibility is established, its writer is rebuilt with exact allowance,
  bounded slippage and final-fill verification, and the full collateral-return
  distribution after carry, gas, liquidation/path dependence and protocol risk
  clears the collateral's Aave alternative.

The Fireworks API was not used; model spend for this review was $0.
