# IBKR / TradFi-broker connection audit — 2026-04-29

> Operator: *"considering connecting an IBKR account via API, but haven't investigated pricing or how well the api works, or alternatives if necessary, but if you expect it to be valuable, investigate that too."*
>
> **Verdict at $170 bankroll: premature. The cheapest realistic options-data subscription is ~$11.50/month = 6.8% monthly drag at our size, catastrophic.** If non-crypto / non-Polymarket exposure becomes desirable before $5k bankroll, **Alpaca** is the better path (cloud REST API, no gateway sidecar, free data tier, options + equities in 2026). IBKR becomes worth it at ~$5k+ when the data fees stop being a meaningful drag, and is genuinely useful at $10k+.

## What IBKR actually unlocks

Things we don't currently have any path to:
- **US Treasuries** (4-week T-bill ~4-5% in 2026, risk-free vs counterparty/depeg) — only meaningful at scale; $170 × 5% = $8.50/yr, irrelevant
- **Real exchange-traded equity options** (SPY/QQQ/single-name at $0.65/contract via IBKR Pro) — wildly better than Ostium's 10-20bp synthetic equity spreads when we want vega/gamma
- **VIX/vol products** (VIX futures, VXX, UVXY, SVIX) — only via real broker
- **Foreign markets** (LSE, ASX, HKEX, TSE) — IBKR is the gold standard for retail
- **Index futures** (ES/MES, NQ/MNQ — micro contracts feasible at low capital, but PDT/margin rules apply)
- **Margin lending against portfolio** (~4.6-5.8% IBKR Pro)

## API state in 2026

There is **no pure cloud REST option for IBKR**. Both paths require a local sidecar process:

- **TWS API (legacy, socket-based)**: requires Trader Workstation or IB Gateway running 24/7. Python via `ibapi` or `ib_async` (the maintained fork after `ib_insync`). High learning curve, async, full feature set. Common gotchas: stale `allOpenOrders()` (use `openTrades()`), TWS memory needs to be 4096 MB, gateway needs daily auto-restart for re-auth.
- **Client Portal Web API (REST + WebSocket)**: pure REST/WS at the surface, but **still requires a local Client Portal Gateway** (Java process). Two-tiered auth — separate "brokerage session" for trading and quotes.

**Implication for our cron-driven autonomy**: a sidecar process running 24/7 is real ops burden alongside our existing news_watcher + telegram_listener + heartbeat_watch. The "claude -p forks resumed from a session" architecture doesn't naturally include a persistent broker connection.

## Pricing in 2026

| Item | Cost | Notes |
|---|---|---|
| Account minimum | **$0** | Used to be $10k; no minimum since ~2021 |
| Inactivity fee | **$0** | Eliminated July 2021 |
| US equities (Lite) | $0 commission | PFOF-funded |
| US equities (Pro) | ~$0.0035/share, $0.35 min | Tiered |
| Options (Pro) | ~$0.65/contract |  |
| Futures (Pro) | ~$0.85 |  |
| **Free data**: Cboe One + IEX real-time (US equities) | $0 | Adequate for many bots |
| **US Securities Snapshot + Futures bundle** | **$10/month** | Waived if ≥ $30/month commissions |
| **OPRA (US options) data** | **$1.50/month** | Waived if ≥ $20/month commissions; requires the $10 bundle as prerequisite |
| Streaming add-on | $4.50/month | Real-time top-of-book |
| **Pro classification trap** | 10× rates if you accidentally check the wrong box on the questionnaire |  |

For US-equities-only with the free Cboe/IEX feed, marginal cost is **$0/month**. For real options data: **~$11.50/month** until commissions waive it. At $170 bankroll, $11.50/month = 6.8% monthly = ~80% annualized drag. Catastrophic.

## Alternatives ranked by API quality

| Broker | API quality | Equities | Options | Futures | Foreign | T-Bills | Notes |
|---|---|---|---|---|---|---|---|
| **Alpaca** | **Best** — cloud REST + WS, no gateway, paper-trade, MCP server, 200 req/min | Yes | Yes (Q4 2024+) | No | No | No | Designed for algo-traders. Options commission-free 2024+. Single + multi-leg. |
| Tradier | Solid REST API, 120 req/min | Yes | Yes ($0.35/contract) | No | No | No | Cheap options, decent #2 |
| TastyTrade | Real API (oauth + REST + streaming) | Yes | Yes | Limited | No | No | Options-trader focused |
| Schwab | Live-only API (port of TDA) | Yes | Yes | Yes | Limited | Yes | Functional but no paper-trade environment |
| Robinhood | **Crypto-only public API** (Jan 2025) | No public | No public | No | No | No | Toy for our purposes |
| **IBKR** | Sidecar-required; richest features | Yes | Yes | Yes | Yes (best) | **Yes** | Heaviest ops, best coverage |

## EU operator KYC + reporting

- IBKR routes EU operators through **IBKR Ireland or IBKR Luxembourg**.
- File **W-8BEN** (renew every 3 years) → US treaty withholding rate.
- Annual statements: **Form 1042-S** (not 1099) for US-source dividends/interest.
- IBKR Ireland/Lux **automatically reports the account to the operator's home tax authority via CRS** (Belgium/NL/etc., June 30 deadline). Operator must self-declare foreign-account holdings on local return.
- **DAC8** mainly affects crypto reporting from 2026 onward; not relevant for equity brokers.
- No FATCA filing burden for EU residents (FATCA is US-citizen).

Net new operator effort: ~30 min annual reconciliation per CRS deadline + initial KYC.

## Threshold guidance

| Bankroll | Recommendation |
|---|---|
| **< $1k** (us today) | Skip IBKR. If non-crypto exposure becomes desirable, **open Alpaca** — cloud API, free data, free options, matches our sidecar-free design. |
| **$1k-$5k** | Still Alpaca primary. IBKR only if a specific strategy *needs* T-Bills, futures, or LSE/ASX. |
| **$5k-$10k** | IBKR starts paying — $30/month commissions waive the data bundle, margin and execution quality begin to matter. |
| **$10k+** | IBKR is a no-brainer addition; Pro tier execution + T-Bills on idle cash + global markets becomes additive. |

## What I'd do if you want non-crypto exposure now

If, before the $5k threshold, we want to express a TradFi-style view (e.g., "long SPY into earnings season", "long VIX into a known catalyst", "short specific stock against a Polymarket position"), the path is:

1. **Open Alpaca paper account** (free, instant, no KYC for paper). Stand up the API integration as code. Test against paper.
2. **Open Alpaca live account** when ready to deploy real capital. KYC required (operator).
3. Treat it as a third sleeve in `scripts/`: an `alpaca_client.py` next to `polyclaude_client.py` and `ostium_client.py`.

But honestly — at $170, the cleanest answer is: **the existing Polymarket + Ostium + Limitless surface is enough to express almost any directional view we'd want**. Ostium has 22 individual US stocks, indices (SPX/DJI/NDX), commodities (gold/oil/silver), FX. The 10-20bp spread is real but at our size the alpha-per-dollar comparison favors Ostium's fee structure over a TradFi broker's data subscriptions until ~$5k.

## Recommendation

**Don't open IBKR today.** When you eventually want fee-clean US equities/options exposure (likely $1-5k bankroll), open **Alpaca** instead — it's the better fit for our cloud-first / cron-driven architecture, and our existing infrastructure patterns (`scripts/_paths.py`, `scripts/across_bridge.py`, etc.) port cleanly.

Re-evaluate IBKR specifically once: (a) bankroll passes ~$5k, AND (b) we have a strategy that genuinely needs T-Bills, futures, or foreign equities — none of which apply right now.

## Sources

- [IBKR API Solutions](https://www.interactivebrokers.com/en/trading/ib-api.php)
- [IBKR Web API v1.0 Documentation](https://www.interactivebrokers.com/campus/ibkr-api-page/cpapi-v1/)
- [IBKR Commissions & Fees](https://www.interactivebrokers.com/en/pricing/commissions-home.php)
- [IBKR Market Data Pricing](https://www.interactivebrokers.com/en/pricing/market-data-pricing.php)
- [IBKR Required Minimums](https://www.interactivebrokers.com/en/accounts/required-minimums.php)
- [IBKR T-Bills 101](https://www.interactivebrokers.com/campus/traders-insight/t-bills-101/)
- [ib_async (replaces ib_insync)](https://github.com/ib-api-reloaded/ib_async)
- [Alpaca Options Trading Docs](https://docs.alpaca.markets/docs/options-trading)
- [Alpaca CLI / MCP launch 2026](https://alpaca.markets/blog/alpaca-introduces-cli-for-trading-api/)
- [CRS / FATCA 2026 Deadlines](https://blog.transworldcompliance.com/en/crs-and-fatca-2026-deadlines-key-dates-and-what-to-watch)
