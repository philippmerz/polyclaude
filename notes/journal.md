# Polyclaude Journal

> Append-only log. Most recent at bottom. Each entry: time (UTC), what happened, why, what's next.

---

## 2026-04-25 ~15:00 UTC — Day 1: setup + initial portfolio designed

**State at start.** Fresh VM. Wallet 0x9032…267B funded with $70 USDC.e on Polygon, 0 MATIC. Repo `polyclaude` (public github) initialized. Memory file system primed.

**What I built:**
- Project skeleton with `.gitignore` excluding wallet/keys/snapshots/swap files. Wallet stays at `<SECRETS>/wallet.json`, never inside the repo.
- `scripts/wallet_status.py`: read-only Polygon balance check across 4 fail-over RPC endpoints (the canonical `polygon-rpc.com` is "tenant disabled" as of today).
- `scripts/discover_markets.py`: Gamma-API survey, category heuristic, 80-row shortlist snapshots into `data/snapshots/` (gitignored, regenerable).
- `scripts/long_horizon.py`: filter by resolution-date window.
- `scripts/polyclaude_client.py`: thin CLOB client wrapper with allowance-setup, balance/positions, GTC/FOK limit orders. Subcommands: `status`, `init`, `approve`, `orderbook`.
- `strategy/00_philosophy.md`: edge taxonomy, Kelly/4 sizing, decision checklist, risk controls, restrictions, reporting cadence.
- `research/_initial_portfolio.md`: five-position carry portfolio, fully reasoned.

**Key findings:**
- Bankroll showed $70 USDC.e (slight overshoot of $60 target — fine) but **0 MATIC**. Trading itself is gasless on Polymarket (EIP-712 relay), but initial USDC + CTF allowances need ~0.01 MATIC of gas. Asked operator (Q2 in `questions.md`) to send ~0.5 MATIC to the wallet. Operator confirmed and is sending.
- Operator clarified mandate: nothing off limits, full risk-appetite latitude, weekly reports must include the *full live decision-making log* not just P&L.
- Macro picture (cross-checked Polymarket pricing + WebSearch): we're inside an active US-Iran-Israel war ("2026 Iran war"), with a brittle ceasefire. Strait of Hormuz blockaded. BTC has crashed to ~$76–80k. April 2026 Fed meeting in 3 days, 99.7% priced for no change. Trump still in office; rhetoric on NATO has escalated.

**Initial portfolio (5 positions, $43 deployed, $27 reserved):**
| # | Market | Side | Entry | Size | Yield (8mo) |
|---|---|---|---|---|---|
| 1 | Jesus returns 2027 | NO | 0.962 | $10 | +3.95% |
| 2 | Pahlavi leads Iran 2026 | NO | 0.908 | $10 | +10.1% |
| 3 | US confirms aliens 2027 | NO | 0.800 | $9 | +25.0% |
| 4 | Trump out 2027 | NO | 0.840 | $7 | +19.0% |
| 5 | Iran regime falls 2027 | NO | 0.800 | $7 | +25.0% |

Theme = longshot tail-fade carry. Deploys into independent (Jesus, Aliens) and partially correlated (Pahlavi/Iran-regime, Trump-out) risk pools. Cluster caps respected. Skipped NATO-withdrawal market because Trump's April 2026 NATO threats + the market's "halted-implementation-still-counts" clause make 11.8% closer to fair than I initially thought.

**Blockers:** waiting for MATIC. Once it lands, run `polyclaude_client.py approve` then place the five limit orders.

**Next session focus:**
1. Execute the carry portfolio.
2. Deeper research on the reserve $27 — looking for higher-conviction directional plays. Initial categories to study:
   - 2026 US Midterm composition (Republicans House at 15%, Democrats House at 85.5% — where is fair?)
   - Brazil 2026 election (Lula vs Bolsonaro family, ~38% each)
   - Long-dated crypto (BTC year-end levels) — only if I find a defensible model
   - Tech valuations (Anthropic $500B+ at 93.6%, NVIDIA dominance) — including conflict-of-interest disclosed plays
3. Build a `notes/positions.md` ledger that auto-updates from on-chain state for the weekly report.

---

## 2026-04-25 ~15:22 UTC — Day 1 (continued): allowances set, all 5 orders filled

**POL arrived:** 53.85 POL in the wallet (operator was generous; only ~0.04 POL needed for the 6 approvals). All 6 allowances confirmed on-chain in two consecutive blocks (86005212–86005217). API L2 creds bootstrapped.

**Order execution (single shot, all matched):**

| Market | Side | Limit | Filled | Cost | Shares | Tx |
|---|---|---|---|---|---|---|
| Jesus returns 2027 | NO | 0.962 | 0.962 | $9.995 | 10.39 | `0xdcf5…8974` |
| Pahlavi leads Iran 2026 | NO | 0.910 → stepped to 0.907 best ask | 0.907 | $9.995 | 11.02 | `0xf1c3…4a63` |
| US confirms aliens 2027 | NO | 0.802 → stepped to 0.800 best ask | 0.800 | $9.000 | 11.25 | `0xe9e7…d24c` |
| Trump out 2027 | NO | 0.842 → stepped to 0.840 best ask | 0.840 | $6.997 | 8.33 | `0x56c1…3b6d` |
| Iran regime falls 2027 | NO | 0.802 → stepped to 0.800 best ask | 0.800 | $7.000 | 8.75 | `0xab6d…f0df` |

The `place_initial_orders.py` script logic to take the lower of `plan_price` and `best_ask` got 4 fills better than my plan price. Total deployed: **$42.99**, max payout if all NO win: **$49.74** (+15.71% on cost, +9.6% on full bankroll).

**State after first session:**
- USDC.e in wallet: $27.01 (reserve)
- POL: 53.81 (gas reserve, way more than needed)
- 5 open positions, all NO outcomes, all resolving 2026-12-31
- Mark-to-market P&L: -$0.16 (the 1¢ spread snap-back; cosmetic, will mean-revert)

**`scripts/positions.py` shipped** — pulls `data-api.polymarket.com/positions` and prints a mark-to-market ledger. Will use this as the daily heartbeat and as input to the weekly report.

**Reflection:** Frictionless execution thanks to: (a) tight 1-cent spreads on all five markets, (b) deep ask-side liquidity ($10k–58k at the best ask vs. my $5–10 tickets), (c) gasless EIP-712 relay. The whole sequence (allowances → API creds → 5 fills) cost ~$0.04 of POL gas and zero USDC fees (Polymarket's standard maker/taker fees are 0%; only sports markets carry the 3% taker fee, and none of these touch sports).

**Next session focus** (carries over):
1. Reserve $27 — research higher-conviction directional plays.
2. Add a tiny watcher script that flags any position that moves >5% intraday so I can react to news without polling manually.

---

## 2026-04-25 ~15:31 UTC — Day 1 (continued): two-sleeve split + short-sleeve filled

**Mandate updated.** Operator asked to allocate 1/3 of bankroll to a 1-month evaluation horizon (and the remaining 2/3 to the original 1-year horizon). Restructured:
- `strategy/01_horizon_split.md` — sleeve allocation, per-sleeve risk caps, file-naming convention.
- `research/_long_initial.md` — renamed; explicit sleeve frontmatter.
- `research/_short_initial.md` — new short-sleeve plan + research notes.

**Short sleeve scan.** Pulled 6,980 active markets, filtered to 99 with: 7 ≤ days ≤ 35, liquidity ≥ $5k, spread ≤ 5¢, non-sports. Three edge sources stood out:
1. Decomposition arbitrage on the Iran/Hormuz timeline — **best EV on the board.**
2. Eurovision country-tail mispricings.
3. Bond-like primary/league carry trades at 0.97–0.99.

**Rejected:** Hormuz-May-15 NO (correlated with peace-deal trade, dropped); UK-top-5 Eurovision NO (lower yield than Latvia, same Eurovision model risk); Atletico CL-final (no edge); sports markets with 3% taker fee (kills carry economics).

**Short-sleeve fills (4 positions, all matched):**

| Market | Side | Plan | Filled | Cost | Shares |
|---|---|---|---|---|---|
| Iran peace-deal May 31 | NO | 0.670 | 0.670 | $6.995 | 10.44 |
| Latvia top 10 Eurovision | NO | 0.830 | 0.830 | $4.997 | 6.02 |
| Atletico La Liga top 4 | YES | 0.990 | 0.995¹ | $4.975 | 5.02 |
| Amy Acton Ohio Dem primary | YES | 0.987 | 0.987 | $4.994 | 5.06 |

¹ Atletico's best ask was 0.991 (above my 0.99 plan), so script auto-bumped the limit to plan+0.5¢ = 0.995. Trivial ~$0.025 cost inflation.

**Why peace-deal NO at $7 (largest short-sleeve ticket):** Most under-priced market on the board. The market is conflating "ceasefire extended" → "peace deal soon," but the resolution language requires *permanent* cessation of hostilities — incompatible with the current operational reality (US blockade still up, Iran attacking ships on Apr 22, Pakistani mediation still working-level). Fair value YES ~10%; market YES 33%. Yield 49% / 35 days. Max single-position downside $7 if Trump pulls a surprise grand-bargain — sized to absorb that tail.

**Why Latvia top-10 Eurovision NO:** Latvia post-2010 modern-era top-10 base rate ≈ 5%. Market 19.5%. Edge real, depth thin ($63 at ask) but my $5 fits. The trade prints if Latvia performs at long-run base rate.

**Why Amy Acton & Atletico YES:** carry trades at 99% certainty. Acton: 1.3% / 9 days = ~53% annualised; Ohio Dem primary has no credible challenger. Atletico: 1.0% / 34 days = ~11% annualised; sitting in top 4 with 5 matches left. Functionally cash-equivalent yields, sized at floor.

**Portfolio after both sleeves:**

| Sleeve | Positions | Cost | Max payout | Implied yield |
|---|---|---|---|---|
| Long (1y) | 5 | $42.99 | $49.74 | +15.7% / 8mo |
| Short (1m) | 4 | $21.96 | $26.54 | +20.9% / 1mo |
| **Combined** | **9** | **$64.95** | **$76.28** | **+17.5%** |

USDC.e remaining: $5.05 (cash buffer, ~7% of bankroll). POL: 53.81 (gas reserve).

**Mark-to-market unrealized P&L: -$0.38 (-0.6%)** — pure spread snap-back, will mean-revert. Latvia moved hardest (-3% on entry) because the book is thin; not a real signal.

**What I'm watching the next 1–2 weeks:**
- May 5: Ohio Dem primary closes (S4).
- ~May 5–14: Eurovision rehearsal-week press impressions (S2).
- May 15: Hormuz-by-May-15 market resolves (not in portfolio, but its outcome is a leading indicator for S1).
- May 16: Eurovision Grand Final (S2).
- Any US/Iran joint statement / blockade lift / Trump bombshell — moves S1 + multiple long-sleeve positions.
- Khamenei health news — moves long-sleeve Iran-regime + Pahlavi.

---

## 2026-04-25 ~16:46 UTC — Day 1 cron check-in: S1 moved +5.2%, thesis confirmed, no action

**State.** USDC.e $5.05, POL 53.81. Nine positions intact. Total cost $64.95, MTM $64.94, unrealised P&L **-$0.01 (-0.02%)** — fully recovered from the entry-spread snap-back logged at fill time (-$0.38 ~75 min earlier). No trades executed.

**Position deltas vs. fill prices (T-~75 min):**
- **S1 (US-Iran peace deal NO)** entry 0.670 → mark **0.705**, +5.22% on cost (+$0.37 MTM). YES leg dropped from 33% → 29.5%. **>5% threshold tripped — explanation below.**
- L5 (Iran-regime falls) entry 0.800 → mark 0.785, -1.87% on cost. YES leg drifted up ~1¢. Within noise; correlated with the same Iran news flow.
- All other positions ±0.5¢ from entry (book noise).

**News scan (catalyst-bounded):**

*Iran/US (drives S1, L2, L5).* Big move on the actual catalyst: Iran FM Araghchi **left Islamabad** today after waiting for the US delegation; Trump then **cancelled the planned Witkoff/Kushner trip** to Pakistan. Iran's MFA also called the truce extension "meaningless" and reiterated that the delegation will not return until the blockade is lifted. This is exactly the directional update I priced into S1 at entry — talks are visibly stalling, not progressing. The market noticed: S1 NO repriced from 0.67 → 0.705. Long-sleeve Iran cluster (L2, L5) barely moved because the *2027* horizon dilutes any single-week peace-deal print. Background: previously confirmed Ali Khamenei was killed in late February 2026 in an Israeli strike; son Mojtaba Khamenei selected Supreme Leader in March, severely injured (multiple surgeries, not seen publicly), with IRGC generals effectively running policy. This is the structural story behind why a near-term peace deal is hard — there is no unified Iranian principal to sign it. Reinforces L5 (regime survives 2027 because it has already absorbed succession + war shock and held) and L2 (Pahlavi has no on-the-ground apparatus to step into this vacuum).

*Trump health (drives L4).* NAACP joined the 25th-Amendment chorus; House Dems filed a commission bill (Raskin); WH pushed back with "MRI normal, cognitive test normal." All political theater — the structural path (R Senate, R Cabinet, VP cooperation required) remains closed. Mark 0.835, unchanged. No action.

*UAP/aliens (L3).* No AARO release, no scheduled press event. Mark 0.795 unchanged. No action.

*Eurovision 2026 / Latvia (S2).* Bookmaker check: Latvia is "best Baltic" but failing to improve qualification odds in the run-up. Confirms the top-10 NO thesis. Rehearsal-week reviews still ~2 weeks out. No action.

*Ohio Dem primary / Acton (S4).* Confirmed: Acton is the **lone Democrat** on the May-5 ballot. Cash-equivalent carry continues; will resolve in 10 days. No action.

*La Liga (S3).* No matchweek today, no scandal flow. No action.

**Decision: hold all 9 positions.**

The S1 +5.2% move is *thesis-confirming* news, not a reason to take profit. Fair value YES is ~10%; market is now 29.5%, still ~19c rich relative to my model. Keeping the position is correct.

**Tempted to add to S1?** Ran the math: short-sleeve cap is $7/ticket and $7/cluster against the $23.33 sleeve target. S1 is already at $7 (cap). Even ignoring the cap, cash buffer is $5.05 (already short of the $7 target); deploying more thins the buffer further when S4 ($5) doesn't free up cash for another 10 days. Per the *no-unrewarded-risk* principle, the right move is to wait — the EV is good but the marginal Kelly/4 size at the current edge is ≈ $1.50, below Polymarket's $5 floor anyway. Hold.

**Weekly report.** Wrote the Week-0 verbose report at this tick (`notes/pnl_weekly.md`). Next weekly entry will be Saturday 2026-05-02 (Week 1, full trailing-7-day window).

**Cron design note.** This is the inaugural cron-driven check-in. Going forward each cron tick produces one journal entry of this shape.

**Sources:**
- [Iran FM departs Pakistan; Trump cancels Kushner/Witkoff trip (NPR, Apr 25)](https://www.npr.org/2026/04/25/nx-s1-5799372/iran-middle-east-updates)
- [Iran war live: Trump cancels Witkoff and Kushner trip (Al Jazeera, Apr 25)](https://www.aljazeera.com/news/liveblog/2026/4/25/iran-war-live-tehrans-fm-in-islamabad-us-says-envoys-to-travel-for-talks)
- [Iran calls truce extension "meaningless" (CNN, Apr 25)](https://www.cnn.com/2026/04/25/world/live-news/iran-war-israel-pakistan-talks)
- [Iran's new supreme leader nowhere to be seen — may help regime survive (CNN, Apr 21)](https://www.cnn.com/2026/04/21/middleeast/iran-supreme-leader-intl)
- [Mojtaba Khamenei health status (IBTimes UK)](https://www.ibtimes.co.uk/mojtaba-khamenei-health-crisis-impact-iran-leadership-1793357)
- [NAACP calls for 25A invocation against Trump](https://naacp.org/articles/unprecedented-first-naacp-calls-president-trump-be-removed-office-under-25th-amendment)
- [Acton lone Dem on May 5 Ohio ballot (WKYC)](https://www.wkyc.com/article/news/politics/elections/ohio-gubernatorial-race-vivek-ramaswamy-dr-amy-acton-may-5-primary-election-gop-democratic-nominations/95-f031b818-7c3a-4518-8235-94bdae633ac5)
- [Eurovision 2026 betting odds — one month out (Eurovisionfun, Apr 2026)](https://eurovisionfun.com/en/2026/04/betting-odds-one-month-before-the-eurovision-2026-grand-final/)

---

## 2026-04-25 ~20:40 UTC — Non-Polymarket yield + venue audit (operator-prompted)

Operator asked via Telegram whether the lower-yield slices of the book might be better placed in DeFi staking / Aave-style lending. Pulled live yields off DefiLlama and walked through the comparison. Full write-up: `research/_yield_audit_2026-04-25.md`.

**Headline:** every active Polymarket position out-yields every comparable-risk DeFi alternative. Best Aave V3 Polygon stable yields right now are 2.8–4.0% APY (USDC 2.80%, USDT0 3.89%, DAI 3.99%); BUIDL T-bill is 3.55% but gates on institutional KYC. Our lowest-yield position (Jesus NO at 5.8% annualised) still beats them, and the rest of the book is dominant by tens of percentage points.

**The idle balance** ($5.05 USDC.e + 53.81 POL) is too small to deploy profitably: round-trip swap fees ≈ a year of stable-lending yield at this size, and POL staking adds 9-day unbonding optionality cost for ~$0.50/yr.

**Trigger conditions captured in the write-up** for re-evaluating: bankroll ≥ $500 → Aave/BUIDL allocation for between-trade idle capital; ≥ $2k → small Hyperliquid sleeve for macro views without a Polymarket counterpart; new directional thesis without a Polymarket expression → perps entry even at smaller size with tight bankroll-fraction cap.

**Decision: no action today, no change to the book.** Documented the analysis so future-me / cron-me doesn't re-litigate the same question every month.
