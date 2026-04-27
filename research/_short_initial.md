# Short-horizon sleeve — initial portfolio (2026-04-25)

> Short-horizon sleeve, 1-month eval window. Allocation framework in `strategy/01_horizon_split.md`; sizing rules in `strategy/00_philosophy.md`. **Eval checkpoint:** 2026-05-25.

## Strategy — concentrated short-tenor edge

Three sources of edge in the 7–35 day window:
1. **Decomposition arbitrage on the Iran/Hormuz timeline.** The crisis sub-markets are priced as if the conditional probability of a *permanent* peace deal in 35 days is 33% — that's calibrated for "ceasefire holds and gets formalized," not for "a permanent treaty is signed in five weeks during an active blockade."
2. **Eurovision-tail mispricing.** Eurovision-tail country markets (small, non-Big-5 broadcaster countries) consistently overprice "top 10" outcomes vs. multi-decade base rates. The structural reason: bettors who care about Eurovision tend to be national-pride longs.
3. **Bond-like primary/league carries.** Near-certain political primaries and football top-4 finishes priced at 0.97–0.99 with 1–2% yield over 9–34 days. Annualised 11–60%, ~zero risk.

I rejected:
- **Hormuz May-15 NO** (0.85 entry, 17.6% / 19 days). Same edge as the peace-deal trade but *highly correlated* — both lose on a US/Iran de-escalation event. Replaced with the higher-EV peace-deal fade alone to stay within the Iran cluster cap.
- **UK top-5 Eurovision NO** (0.96 entry, 4.2% / 20 days). Lower yield than Latvia and same model risk.
- **Atletico CL final** (0.365). Real 50/50 — no edge for me.
- **Sports markets with `feesEnabled=true`**: 3% taker fee makes near-certain fades unprofitable.

## Sizing

Sleeve cap per ticket: 15% × $23.33 = **$3.50** — but Polymarket's $5 floor binds, so the practical min/max is $5–7. Largest ticket goes to the highest-EV thesis (peace deal NO).

| # | Market | Side | Plan entry | Size | Resolves | Yield to resolution | Annualised |
|---|---|---|---|---|---|---|---|
| S1 | US x Iran permanent peace deal by May 31 | NO | 0.670 | $7 | 2026-05-31 (35d) | +49% | +514% |
| S2 | Latvia in top 10 at Eurovision 2026 | NO | 0.830 | $5 | 2026-05-16 (20d) | +20.5% | +374% |
| S3 | Atletico Madrid top 4 in La Liga 2025–26 | YES | 0.990 | $5 | 2026-05-30 (34d) | +1.0% | +11% |
| S4 | Amy Acton wins 2026 Ohio Gov Dem primary | YES | 0.987 | $5 | 2026-05-05 (9d) | +1.3% | +53% |
|   | **Total** |   |   | **$22** |   | weighted +18% | — |

If all four resolve favourably: $22 → ~$26.6 (+21%).
If only S1 wins (highest weight): $22 → $10.45 + $5 + ~$0 + ~$0 = ~$15 mark — still nets positive.
Worst-realistic case (S1 loses, others win): -$7 + $0.07 + $0.05 + $0.05 = -$6.83 (~-31% on sleeve cost). Acceptable on a sleeve sized at 33% of bankroll.

---

## Position #S1 — NO on "US x Iran permanent peace deal by May 31, 2026?"
- Slug: `us-x-iran-permanent-peace-deal-by-may-31-2026-333`
- Token (NO): `42918220085288219341491829385501246298233444593663440094436147850542032590016`
- **Resolution.** YES if "Iran and the United States agree to a permanent peace deal" using language "explicitly indicat[ing] that military hostilities … have ended or will permanently cease." Explicitly excludes temporary agreements.
- Market: NO bid 0.66 / ask 0.67 / 1¢ spread, $8.5k depth at best ask.
- **Implied YES probability: 33%.**
- **My fair-value YES probability: 8–12%.** Decomposition:
  - Current state (per Apr 22-23 reporting): brittle ceasefire just *extended* at Pakistani request, US blockade explicitly *not lifted*, Iran attacking commercial ships on April 22, Iranian FM calling the blockade "an act of war." No diplomatic infrastructure for a permanent deal.
  - The market is conflating "ceasefire extended" → "peace deal soon." But the resolution criteria require *permanent cessation* language. Even an Iran-US framework agreement modeled on JCPOA-style returning would take months of working-level talks; no such talks are in evidence.
  - Tail: Trump's deal-driven personality could produce a surprise "I just spoke with the Supreme Leader, we have a deal" moment. Non-zero. Add 3–5% for that tail.
  - Sum: ~10%.
- **Trade:** limit BUY NO at 0.67, size $7.
- Payout if NO: $10.45 (+49% over 35 days, ≈ +514% annualised).
- Risk: $7 if a permanent peace deal is signed by May 31. The most-likely path to that is a Trump-led grand bargain that I can't predict. Sized to allow for that tail.
- Cluster: Iran cluster. Long sleeve has $7 in Iran-regime-NO + ~$5 effective in Pahlavi-NO. This adds $7 short-sleeve exposure. Iran-cluster long+short combined ~$19 ≈ 27% of bankroll. Inside the global 30% cap.

## Position #S2 — NO on "Will Latvia be in the top 10 at Eurovision 2026?"
- Slug: `will-latvia-be-in-the-top-10-at-eurovision-2026`
- Token (NO): `84808556359071914967263506000259998857147664764718810872873752456867359642110`
- **Resolution.** YES if Latvia finishes top 10 in the Eurovision 2026 grand final (May 16, 2026, Vienna).
- Market: NO bid 0.78 / ask 0.83 / 5¢ spread (wider than I'd like; reflects thin retail interest), $63 depth at best ask.
- **Implied YES probability: 19.5%.**
- **My fair-value YES probability: ~7%.** Latvia historical Eurovision performance:
  - One win (2002), one runner-up (2005), one 4th place (2002 again). Otherwise consistently mid-pack or relegated to semi-final.
  - In the past 10 years (2015–2025), Latvia made the grand final only ~50% of the time and never finished higher than 12th.
  - Top-10 base rate over the past 25 years is ~12% but heavily weighted toward 2002–2005. Modern era (post-2010): ~5%.
  - Without specific 2026 song quality information, I anchor to ~7%.
- **Trade:** limit BUY NO at 0.83, size $5.
- Payout if NO: $6.02 (+20.5% over 20 days, ≈ +374% annualised).
- Risk: $5 if Latvia top 10. Depth at ask is thin; my $5 will fully fill (sweeps up to ~$63 of asks).
- Cluster: Eurovision-only. Independent of all other positions.

## Position #S3 — YES on "Atletico Madrid finish top 4 in La Liga 2025–26"
- Slug: `will-atletico-madrid-finish-in-the-top-4-of-the-la-liga-202526-standings`
- Token (YES): `100952291322678954514417231357111610948515892742954751932425813530604840075554`
- **Resolution.** YES if Atletico finishes in the top 4 (i.e., qualifies for next-season UCL) of the 2025-26 La Liga.
- Market: YES bid 0.96 / ask 0.99 / 3¢ spread, $14 depth at ask.
- **Implied YES probability: 99%.**
- **My fair-value YES probability: ≥ 99%.** Atletico is currently top 4 with a comfortable points buffer over the 5th-place team and 5 matches remaining as of late April 2026. The only way to drop out is a points-coincident collapse + a team behind them winning out — not impossible but very low probability.
- **Trade:** limit BUY YES at 0.99, size $5. Depth tight; expect partial fill at 0.99 and the rest at 0.999 if the depth has been swept by another taker.
- Payout if YES: $5.05 (+1.0% over 34 days, ≈ +11% annualised).
- Effectively a treasury-like carry. Earnings rate ≪ S1 but uncorrelated and near-zero risk.

## Position #S4 — YES on "Amy Acton wins 2026 Ohio Governor Democratic primary"
- Slug: `will-amy-acton-win-the-2026-ohio-governor-democratic-primary-election`
- Token (YES): `45282920959193141979506939608658828232463179670129495742906083036305009865038`
- **Resolution.** YES if Acton wins the May 5, 2026 Democratic primary for Ohio Governor.
- Market: YES bid 0.981 / ask 0.987 / 0.6¢ spread, $35 depth at ask.
- **Implied YES probability: 98.7%.**
- **My fair-value YES probability: 99%+.** Acton (former Ohio Department of Health director) has been the consensus Democratic frontrunner with no comparable challenger. Markets at 98.7% nine days out reflect the absence of a credible competitor. The remaining risk is a 1.3% basket of {dropout, scandal, health event, sleeper challenger}. I'm comfortable buying that fade.
- **Trade:** limit BUY YES at 0.987, size $5.
- Payout if YES: $5.07 (+1.3% over 9 days, ≈ +53% annualised).
- Effectively a 9-day money-market trade with a Dem primary pinned at 98%+.

---

## Execution plan
1. Place all 4 limit orders as **GTC** in a single script run; report receipts to `logs/`.
2. Snapshot expected fills.
3. Update `notes/journal.md`.

## Catalysts to watch over the 1-month window
- US/Iran negotiations (any joint statement, named-deal labelling, blockade lift) — moves S1 and Iran-related long-sleeve positions.
- Iranian regime stress — Khamenei health, Tehran protest scale (also moves long-sleeve Iran-regime).
- Eurovision rehearsal-week reactions (May 5–14) — moves S2 (Latvia top 10).
- La Liga matchdays 33–38 — moves S3.
- Ohio Dem primary May 5 — closes S4.
