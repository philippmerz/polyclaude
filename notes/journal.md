# Polyclaude Journal

> Append-only log. Most recent at bottom. Each entry: time (UTC), what happened, why, what's next.

---

## 2026-04-25 ~15:00 UTC — Day 1: setup + initial portfolio designed

**State at start.** Fresh VM. Wallet 0x9032…267B funded with $70 USDC.e on Polygon, 0 MATIC. Repo `polyclaude` (public github) initialized. Memory file system primed.

**What I built:**
- Project skeleton with `.gitignore` excluding wallet/keys/snapshots/swap files. Wallet stays in a gitignored secrets directory, never inside the repo.
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

---

## 2026-04-25 ~22:00 UTC — Day 1 cron tick #2 (scheduled, max-effort): no action

**State.** USDC.e $5.05, POL 53.81. Nine positions intact. Total cost $64.95, MTM $64.56, unrealised P&L **-$0.39 (-0.60%)** — ~0.4 pp wider than the 16:46 UTC tick (-$0.01 then) but well inside book noise.

**Position deltas vs. previous tick (T-~5h):**
- **L5 (Iran-regime falls before 2027) NO** mark 0.795 → **0.775**, -3.12% on cost (-$0.22 MTM). YES leg drifted up to ~22.5%.
- **S1 (Iran-peace-by-May-31) NO** mark 0.665 → 0.675, +0.75% on cost. YES leg back to 32.5% (still ~22 pp above my fair-value estimate).
- L1, L2, L3, L4, S2, S3, S4 within ±0.5¢ of fill — book noise.

**News scan.** No structural break in the last 5 hours. State is the same as the 16:46 read: ceasefire extended, naval blockade still on (USS Peralta intercepted an Iranian-flagged ship today), Iran FM in Pakistan with no US counterpart, Pezeshkian publicly says "blockade and threats are hindering negotiations." Trump's Apr 21 "seriously fractured Iranian government" line continues to circulate. Nothing on Trump health (US Saturday evening — quiet desk), nothing on UAP, nothing on Eurovision rehearsal-week (still 10 days out), no Ohio primary news (Acton remains lone Dem), no La Liga matchweek today.

**Reading the L5 drift.** Two non-mutually-exclusive explanations: (a) the same news flow that's pushing S1 NO higher (no peace deal soon → war continues) is pushing L5 YES higher because a longer war raises the conditional probability of regime collapse; (b) Pezeshkian's "blockade and threats are hindering negotiations" + Trump's fracture-language framing is being read by some traders as Iranian-internal-instability evidence. Either way, the move is within the volatility I sized for. Thesis (regime survives because it has already absorbed the Khamenei-killing + war shocks and held intact for 8 weeks) is unchanged — and the position resolves Dec 31, with another 250 days for the price to mean-revert toward my ~7-10% fair value as the war news cycle cools.

**Decision: hold all 9 positions.** No catalyst justifies a trim, an add, or a close. Cash buffer still $5.05; will rebuild on Acton (May 5) and Latvia/peace-deal as those resolve.

**Telegram ping?** No — this is routine maintenance, no thesis-changing news. Operator just set up the cron and will see this entry on next check-in.

**Sources:**
- [Day 56 of Middle East conflict (CNN, Apr 24)](https://www.cnn.com/2026/04/24/world/live-news/iran-war-trump-israel-lebanon)
- [USS Peralta intercepts Iranian-flagged ship under blockade (NBC News live blog, Apr 24)](https://www.nbcnews.com/world/iran/live-blog/live-updates-iran-war-trump-peace-talks-vance-ceasefire-ship-hormuz-rcna341149)
- [Trump extends ceasefire citing "seriously fractured" Iranian government (CNBC, Apr 21)](https://www.cnbc.com/2026/04/21/trump-iran-war-ceasefire.html)

---

## 2026-04-26 ~08:15 UTC — Trump assassination attempt + algo-trading audit (operator-prompted)

Operator pinged via Telegram with two threads.

**(1) Trump assassination attempt — White House Correspondents' Dinner, evening of Apr 25.** Cole Tomas Allen (31, California) fired shots near the security perimeter; one Secret Service agent took a round in his vest, no other casualties, suspect in custody. **Trump entirely uninjured** ("perfect condition" per his own post). Suspect to be charged with using a firearm during a crime of violence.

*Position implication:* L4 Trump-out NO 0.84 entry → live mark **0.835** (essentially unchanged). The market priced this as a non-event because Trump survived. My fair-value mortality + assassination + removal model already had a 1–2% assassination tail baked in, and a *failed* attempt doesn't update the conditional probability of *future* attempts much above baseline (Reagan-1981 was the last serious survival case; no quick re-attempt followed). **Hold L4. No trade.**

Second-order concern: a successful security failure could in theory accelerate a 25th-Amendment Section-4 conversation, but the structural blockers (R-Senate, R-Cabinet, VP cooperation) remain — same logic as before. Watching for Trump health follow-ups (if he was rattled enough to skip events, that creates its own narrative), but nothing actionable today.

**(2) Algorithmic Polymarket trading feasibility — full write-up at `research/_polymarket_algo_audit_2026-04-26.md`.** Operator flagged hearing about a bot with "insane returns on BTC 5-minute bets" and asked whether anything similar fits our setup.

Verdict: **no algorithmic deployment at this scale.** The decisive number is the fee schedule — Polymarket's short-tenor crypto markets (5-min, hourly, daily ladders) all fire `{rate: 0.072, takerOnly: true, rebateRate: 0.2}`, which is *edge-aware* (`fee = rate × min(p, 1-p) × notional`):
- At p ≈ 0.5 (5-min coin-flip case), round-trip taker fee is **7.2%** — exceeds any retail TA edge I've seen documented (live bots win 25-27% vs 53% breakeven).
- Maker rebates are real but require **≥ $50/order** (`rewardsMinSize: 50`), an order of magnitude above our $5 minimum.
- Latency: 100-300ms RTT to Polygon CLOB on our 2-CPU box; transient mispricings are gone in milliseconds when a co-located bot competes.

The "insane returns" rumour is most likely (a) a viral lucky-streak post that didn't survive sample size, (b) a serious market-maker operating well above $50/quote with rebate income, or (c) backtested-not-live numbers. No verifiable source available — happy to dig if the operator forwards a specific link.

Trigger conditions captured in the audit doc: bankroll ≥ $250-500 → maker-quoting becomes viable; bankroll covers a low-latency VM out of yield → revisit; Polymarket fee schedule changes → revisit; operator forwards a specific verifiable bot edge → re-audit.

**No book changes from either thread.** Pushing the audit doc + this entry now.

**Addendum 08:30 UTC — operator forwarded the specific account behind the "insane returns" rumour.** Pulled lifetime stats off Polymarket profile + data-api: `0xde17f7144fbd0eddb2679132c10ff5e74b120988` is **−$727,450.80 lifetime P&L** across 1,168 predictions, all daily/weekly BTC range markets. Current portfolio value $0. Biggest single win $195k (the propagating headline). Cumulative losses of $922k around it (what doesn't propagate). Direct empirical confirmation of yesterday's audit: the strategy class behind the rumour is a known capital-destroyer for retail, not a hidden edge. Updated `research/_polymarket_algo_audit_2026-04-26.md` with the verification.

**Correction 08:50 UTC — operator caught a sign error and they were right.** I had taken WebFetch's natural-language summary ("Lifetime P&L: -$727,450.80") at face value. Pulling the page's raw embedded React state directly gives `{"amount": 45832613.43, "pnl": 727450.84}` — that's **+$727k positive P&L on $45.8M lifetime volume**, i.e. ~1.6% edge per dollar transacted. The account is *profitable*, not a cautionary tale. The "-100% on open positions" I saw is just the unredeemed-loser pile (winners get redeemed/sold and disappear from open positions), not a P&L summary. **Operator was right to push back; lesson for me: never trust a small-model summary on financial numerics — always verify against raw structured data.**

**Re-evaluated audit conclusion** (full update in the audit doc): the strategy class IS profitable for a serious operator with capital, edge, and infrastructure. The successful pattern visible in the tape: buying near-certain "BTC reach $X" YES tickets at 0.86–0.97 during the window's lifetime — high-volume small-edge carry. Replicating *cleanly* at our $70 bankroll is still high-variance: $5 ticket × 1.6% edge = $0.08 expected per trade before fees, and a single losing $5 ticket eats ~63 winning ones. Path forward if we ever want to deploy: paper-trade ≥ 50 markets first to verify our pricing model has the same edge before risking real capital. Bankroll ≥ $250 makes the variance survivable. *Not deploying today*, but I'm now correctly classifying this as "untested edge that might exist" rather than "known capital-destroyer."

---

## 2026-04-27 ~12:35 UTC — Architecture: cron rebalanced + news-watcher daemon

Operator gave open-ended latitude ("free to move ticks to whichever timing you expect to maximise returns; maybe an RSS-based ping system; expand the architecture however"). Two changes:

**(1) Cron rebalanced.** Was 14:00 + 22:00 UTC (8h/16h asymmetric). Now **02:00 + 14:00 UTC** — clean 12h spacing, 14:00 preserves the US-morning anchor for the policy/Iran-flow news cycle, 02:00 fills the previously-quiet stretch and catches Asia-morning + late-US-news.

**(2) `scripts/news_watcher.py` shipped.** Long-running daemon polling 11 RSS feeds (BBC World/Politics/ME, Al Jazeera, NPR World/Politics, Guardian World/US, France24, CBS, Fox World) every 5 minutes. Matches each entry's title + summary against a tiered keyword list in `scripts/news_watcher_config.json`:

- **Tier 1** (book-resolving events): Trump dies / assassinated / 25A-removed, Iranian regime falls / Khamenei dies / IRGC coup, US-Iran permanent peace deal signed, Pahlavi takes power, aliens confirmed by Cabinet/agency, Jesus Christ returns, Iran missile-strikes a European city. → Telegram alert with `[URGENT]` prefix **AND** auto-spawns a `daily_checkin.sh` so a fresh max-effort cron Claude reacts immediately.
- **Tier 2** (notable but not resolution-shifting): Trump health/security, Hormuz blockade ops, US-Iran talks state, Khamenei health, UAP/AARO reports, Eurovision rehearsals, Ohio primary, La Liga title race, Atletico injuries. → Telegram `[NEWS]` alert only; next scheduled cron tick handles analysis.

State (seen entry IDs, per-keyword cooldowns) lives in the gitignored secrets directory. Per-keyword 30-min cooldown prevents spamming on a hot story. Auto-cron-fire is rate-limited to 30 min between auto-spawns. Daemon restarts on reboot via `@reboot` crontab. Bootstrap poll already emitted two real Tier-2 Iran/Hormuz alerts (BBC ME stories on ceasefire breaches and ships under fire), confirming the pipeline works.

The combined autonomy stack now has three layers: (a) a 24/7 news-driven reactive layer (the watcher), (b) a scheduled analytical layer (cron 02:00 + 14:00), (c) an interactive operator console (tmux pane fed by the Telegram listener). Independent, fail-soft.

---

## 2026-04-27 ~14:00 UTC — Cron tick (14:00 UTC slot): hold all 9, book first day in green

**State.** USDC.e $5.05, POL 53.81. Nine positions intact. Total cost $64.95, **MTM $65.27, +$0.32 (+0.50%)** — first cron tick with the book in the green since fills two days ago.

**Position deltas vs. prior tick (T-~24h, since the 14:00 slot is new vs the previous 22:00):**
- **S1 Iran-peace NO** mark 0.695 → **0.705**, holding the +5.22% gain on cost from yesterday. No new movement; thesis remains anchored.
- **L4 Trump-out NO** 0.835 → **0.845** (+1.2¢). The Apr-25 assassination attempt now ~36 hours old; market continued to digest the failed-attempt-Trump-uninjured fact pattern with a small further drift toward the NO side.
- **L3 Aliens NO** 0.795 → 0.805 (+1¢). No specific UAP catalyst; just mean-reversion in an illiquid book.
- **L5 Iran-regime NO** 0.785 → 0.795 (+1¢). Some recovery from yesterday's drift; same Iran tape now reading neutrally.
- **S2 Latvia NO** 0.815 → 0.810 (-0.5¢). Book noise on thin market.
- Others within ±0.5¢ of fill.

**News scan.** Iran/US: ceasefire is now indefinitely extended (per CFR, NBC live blog, Al Jazeera coverage). Both sides continue to violate intermittently. Major sticking points unchanged — Hormuz transit fees, Iran nuclear program, US sanctions, Lebanon/Hezbollah, $6B frozen-assets demand. No movement toward a *permanent* deal; the resolution-language gap that defines S1's edge remains wide. Trump health: no new clinical events; security review post-WHCD ongoing. UAP: no AARO release this cycle. Eurovision rehearsal-week starts ~May 5 (still 8 days out). Ohio primary May 5 (8 days). La Liga matchweek 35 mid-week.

**Decision: hold all 9.** No catalyst justifies trim/add/close. S1 still ~22 percentage points rich vs my fair-value model; resist temptation to add (cluster cap, cash buffer, marginal Kelly/4 below the $5 floor — same logic as yesterday).

**Watcher status.** Daemon up, pid 65433, 264 entries seen during bootstrap. No Tier-1 alerts emitted since startup. Two Tier-2 Iran/Hormuz alerts from the bootstrap poll were thesis-confirming and already on the operator's phone.

**Weekly report status.** Last weekly was 2026-04-25 (Saturday — Week 0). Next due Saturday 2026-05-02 with the full trailing-7-day window. Today is Monday; not yet.

**No Telegram ping** — routine maintenance, nothing material moved beyond what's already journaled.

---

## 2026-04-26 ~14:00 UTC — Sunday 14:00 cron tick: stable, no action

State: USDC.e $5.05, POL 53.81, 9 positions intact. Total cost $64.95, MTM **$64.69**, unrealised P&L **−$0.26 (−0.40%)** — basically unchanged from this morning's read (−$0.12). No position moved more than ±1¢ since 08:00.

News scan: no new catalysts beyond what was journaled this morning. Iran/US still stalled (Trump rejected the latest Tehran proposal as "a lot but not enough"; Araghchi back in Pakistan after Oman shuttle; envoys' Pakistan trip remains cancelled). Status quo is *thesis-confirming* for S1 (peace-deal NO) and L5 (Iran-regime NO). No fresh Trump-health news after yesterday's assassination attempt — one news cycle later, market hasn't re-priced. No UAP, Eurovision, Ohio, La Liga catalysts.

Decision: hold all 9. No telegram ping (per operator: "no ping if nothing new"). Inaugural automatic 14:00 UTC tick fired clean — no manual intervention needed.

Sources:
- [Live updates: Trump cancels envoys' Pakistan visit; Tehran's FM returns (CNN, Apr 26)](https://www.cnn.com/2026/04/26/world/live-news/iran-war-trump-israel)
- [Iran war live: Tehran rejects talks under siege; Trump cancels envoys' trip (Al Jazeera, Apr 26)](https://www.aljazeera.com/news/liveblog/2026/4/26/iran-war-live-tehran-rejects-talks-under-siege-trump-cancels-envoys-trip)

---

## 2026-04-27 ~21:20 UTC — Crypto landscape audit for separate $50 bankroll (operator-prompted)

Operator: "considering expanding into a different context with around 50 dollars. Research the entire crypto landscape in depth and rank the most promising opportunities for a < 6 month timeframe... include lesser-known novel ones, the largest alpha could be hidden in lesser-known projects."

Memo at `research/_crypto_landscape_2026-04-27.md` (214 lines). Built by spawning 4 parallel research agents (macro state, yield, speculation, novel/lesser-known) and synthesizing into a tier-ranked, fee-vetted list with concrete portfolio splits.

**TL;DR of verdict.** At $50 / < 6mo / Polygon-self-custody constraint, three Tier-1 plays cleared the fee/compute screen with structural retail edge:

1. **Ostium (Arbitrum) — points-farming + RWA-perp directional.** $58M TVL, $25B cumulative volume, 54 RWA-perp pairs (gold, SPY, NVDA, 22 US equities), Jump+General-Catalyst-backed at $250M post-money, $5 minimum trade size, Arbitrum sub-cent gas. **No public token yet — points are explicitly retroactive-airdrop-shaped.** Single highest-conviction novel play. Comparable retroactive-airdrop precedents (Hyperliquid, Jito, Jupiter) returned 5-50x of cumulative-fee-paid for active retail farmers.
2. **Bittensor subnet alpha (SN64 Chutes via TAO entry).** Sector cap ~$1.12B, dTAO live, top performers up 200-450% in 30d. SN64 Chutes (Rayon Labs serverless inference, 9.1T tokens served, 400K users) is the cleanest cashflow story. Easier alternative: just buy spot TAO on a CEX for diversified emissions exposure.
3. **Limitless ↔ Polymarket arbitrage on Base.** Limitless hit $1B/mo prediction-market notional Q1 2026, zero gas (Coinbase-subsidized). Identical political/sports markets often spread 2-4% across the two venues — net of Polymarket's edge-aware fee, ~1% per cycle. 4-hour Python script to monitor and ping Telegram. Bonus: doubles as scaffolding for any future POLY-airdrop farming.

**Tier-2 yield floor:** Pendle PT-sUSDe-Jun-2026 on Arbitrum (4.31% fixed APR) or Aave V3 USDT0 Polygon (3.88%). PLUME (RWA chain native, $0.0138, ~95% off ATH) and Akash (sleeper GPU-DePIN) as small directional sector beta.

**Recommended split (Default — lean concentrated, 100% Claude-executable):** $30 Ostium / $15 Limitless arb / $5 gas reserve. *Optional add-ons*: $10-15 TAO on a CEX the operator already uses (skip if no existing CEX seat — not worth fresh KYC for $15 of Bittensor beta), $3-5 MegaETH-MEGA-TGE-on-Apr-30 event-trade (skip unless Day-1 pricing obviously leaves runway).

**Operator-side feedback after first pass: original §8 had too many operator-action steps.** Revised: the only operator actions are (a) send $50 USDC.e to existing wallet `0x9032…267B`, (b) reply "go". Default to same wallet (separate ledger in `notes/positions_crypto.md`), no fresh keypair required. All bridging, account-opening, position management, and the Polymarket↔Limitless spread monitor are Claude tasks. Memo §8 + §10 rewritten accordingly. **Lesson learned**: when proposing a new sleeve, lead with the minimum-input operator interface, not the full menu of "things one could do."

**Tier-3 actively-skip list (with reasons):**
- pump.fun retail sniping — 0.63% of launches graduate, 3% of users earn > $1K. Negative-EV.
- HLP vault — 12-mo realized max DD **−55%**. Risk profile is trend-following CTA, not yield.
- Funding-rate basis trade — perp min orders + dust funding payments mechanically OOS at $50.
- LRTs (weETH/rsETH/ezETH) — Kelp DAO drained $293M April 19 (rsETH 18% supply hit), USDe -34% on contagion. Major airdrops already paid. Forward thesis is restaking-without-airdrop-with-tail-risk-priced. Bad R/R.
- MOVE — -99% from ATH, founder-fraud, delisting risk.
- Plasma (XPL) before July 28 — 25% supply unlock to US public-sale buyers will distribute heavy.
- Sei — 1.5-2%/month inflation drag.
- Inscriptions/Runes/BRC-20 — sector dead, BTC fees alone wreck $50.
- Resolv — $25M exploit March 22 2026 (unauthorized 50M USR mint).

**Why I'm confident.** Same fee-structure lens that proved the Polymarket-algo audit on April 26: at small size, the fee/rebate math determines feasibility before strategy quality. Tier-1 plays each have **a specific structural edge** retail at $50 can capture (Ostium = retroactive airdrop on real product; SN64 = revenue-driven token; Limitless arb = liquidity-fragmentation between two real markets). Tier-3 rejections are quantitatively grounded (DD, fee, hack-event, supply-unlock).

**What this audit does *not* cover.** Memo intentionally separate from the polyclaude $70 Polymarket book — no commingling. If operator decides to deploy, the funding source, wallet (same or new EVM addr), and bookkeeping should be a separate decision from the Polymarket sleeve. I'd recommend a NEW wallet for this so the Polymarket book's audit trail stays clean. Trigger conditions in the memo §9 cover when to revisit.

**Token cost of this work.** 4 parallel general-purpose research agents (Sonnet 4.6) returning ~600-900 words each, synthesized in main session. Within reasonable bounds vs the operator's Max subscription budget; no /usage check needed unless this kind of audit becomes routine.

---

## 2026-04-27 ~21:35 UTC — Crypto sleeve: new wallet generated, full decentralization constraint set

Operator's reply to the minimum-interface revision: *"You're free to create a new wallet yourself, I agree it could be cleaner... I do want to stay entirely decentralized just because I want this project to be entirely managed by you, and unfortunately, you can't do KYC yet. This means anything involving CEX is off the table."*

Two decisions locked in:

**(1) New wallet created for the crypto sleeve.** Generated locally on the VM with `eth_account.Account.create_with_mnemonic(num_words=12)` inside the polyclaude venv. Address `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6`. Credentials stored in the gitignored secrets directory (mode 0o600, schema `{address, private_key, mnemonic}` — same shape as the existing Polymarket wallet file). Defensive `.gitignore` lines added (`wallet_crypto.json`, `*mnemonic*`) — file lives outside the repo regardless. The two sleeves are now structurally separate: distinct keypairs, distinct journal narratives, no commingling possible by accident.

**(2) Hard constraint registered: no CEX, no KYC, fully decentralized.** Saved to `user_profile.md` memory. This kills the optional TAO/Bittensor leg of the crypto memo permanently — the only on-chain rail at $50 (TaoFi at $192K TVL, 5-15% slippage) is too thin to be worth it. Diversified Bittensor exposure is unreachable at this size under the constraint; re-evaluate only if a deeper on-chain TAO bridge appears. Memo §7 + §10 + TL;DR updated.

**Net default split unchanged**: $30 Ostium / $15 Limitless / $5 gas reserve. The TAO leg was always *optional* in the revised plan, so removing it permanently doesn't shift the headline allocation.

**Operator's remaining task list — exactly one item**: send $50 USDC.e on Polygon to `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6`. No "go" needed — operator's instruction (*"You're free to create a new wallet yourself"*) already serves as the greenlight; deployment begins when funds arrive on Polygon.

**Operational implications for future sessions**:
- Cron-tick prompts should now read both wallets when scanning state. The existing `scripts/wallet_status.py` + `scripts/positions.py` were Polymarket-only; need to extend (or fork into a `scripts/crypto_status.py`) to monitor the new wallet's USDC balance across Polygon/Arbitrum/Base, plus Ostium positions and Limitless balances. Will write that when funds arrive — premature now.
- For the journal: continue narrating Polymarket positions as before; new crypto-sleeve trades get clearly tagged (`[crypto]` prefix, or a separate weekly P&L file). Decision deferred until the first crypto trade is placed.
- For Telegram alerts: the existing `scripts/telegram.py` is wallet-agnostic; just need to include sleeve identifier in the message body.

I will start no on-chain action until the new wallet's USDC balance is non-zero — the wallet is empty and any pre-funding setup work would just burn cycles. When funding lands, plan is: bridge $30 to Arbitrum + Ostium setup, $15 to Base + Limitless setup, $5 USDC.e + $1-2 of POL on Polygon retained for gas/bridges.

---

## 2026-04-27 ~21:50 UTC — Path-leak hygiene scrub (operator-flagged)

Operator: *"Do not leak the location of the secrets."* Caught me having committed absolute filesystem paths to the crypto-sleeve credentials file across the new crypto memo, journal entry, and earlier across 6 scripts. Scrubbed.

**Architectural change.** All secret-bearing file locations now resolved at runtime via env vars. New module `scripts/_paths.py` auto-loads `~/.polyclaude/env` (gitignored, 0o600, outside the repo) on import and exposes `path("VAR_NAME") -> Path`. Importing scripts use `import _paths as _secrets` then `_secrets.path("VAR_NAME")`. Public source references env-var names only — no filesystem path strings. (Module is named `_paths.py` not `_secrets.py` because the existing `*secret*` line in `.gitignore` was matching `_secrets.py` and stopping it from being tracked.)

**Files refactored:**
- `scripts/wallet_status.py` — uses `POLYCLAUDE_WALLET`
- `scripts/polyclaude_client.py` — uses `POLYCLAUDE_WALLET`, `POLYCLAUDE_CREDS`
- `scripts/telegram.py` — uses `POLYCLAUDE_TELEGRAM_TOKEN`, `POLYCLAUDE_TELEGRAM_STATE`
- `scripts/telegram_listener.py` — uses `POLYCLAUDE_TELEGRAM_TOKEN`, `POLYCLAUDE_TELEGRAM_STATE`, `POLYCLAUDE_LISTENER_PID`
- `scripts/news_watcher.py` — uses `POLYCLAUDE_NEWS_STATE`, `POLYCLAUDE_NEWS_PID`, `POLYCLAUDE_TELEGRAM_TOKEN`, `POLYCLAUDE_TELEGRAM_STATE`; in-repo paths (config, log, cron-script) now resolved via `Path(__file__).resolve().parent`
- `scripts/daily_checkin.sh` — sources `${HOME}/.polyclaude/env`, resolves `POLYCLAUDE_DIR` from `${BASH_SOURCE[0]}` instead of hardcoded
- `scripts/place_initial_orders.py`, `scripts/place_short_orders.py`, `scripts/discover_markets.py`, `scripts/long_horizon.py` — in-repo `LOG_DIR`/`DATA`/`SNAP` paths now `Path(__file__).resolve().parent.parent / ...`

Daemons restarted with refactored code: `news_watcher` PID 85333, `telegram_listener` PID 85368. Smoke test: `wallet_status.py` still prints correct balances; all 8 scripts import without error.

**Docs scrubbed:**
- `research/_crypto_landscape_2026-04-27.md` (TL;DR, §8, §10)
- `notes/journal.md` (Day 1 setup entry, news_watcher entry, my crypto-sleeve entry)
- `strategy/00_philosophy.md` operational-risk paragraph
- Docstrings of `wallet_status.py`, `telegram.py`, `telegram_listener.py`, `news_watcher.py`

**Memory updated:**
- `user_profile.md` — genericized the wallet-storage line
- `reference_polyclaude_layout.md` — secrets dir referenced generically; documents the env-file indirection mechanism
- New `feedback_no_path_leaks.md` — durable rule + Why + How to apply for future sessions

**Sanity grep:** `grep -rn "home/" --include="*.md" --include="*.py" --include="*.sh" --include="*.json"` returns zero hits across the repo. Verified.
