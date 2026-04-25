# Initial Portfolio — 2026-04-25

> First-trade plan. Awaiting MATIC top-up to set on-chain allowances; then execute.

## Bankroll & sizing framework
- Starting USDC.e: $70.00 on Polygon
- Initial deploy target: ~$43 (61% of bankroll)
- Reserve: ~$27 for higher-conviction directional plays surfaced in week 1–2 research
- Max ticket: 15% of bankroll = $10.50
- Max correlated cluster: 30% = $21.00

## Strategy theme — Tier-1 carry: longshot fades

**Operating insight.** Polymarket's longest-dated, lowest-probability binary markets ("by 2027" tail markets) systematically over-price tail probability because: (a) retail traders buy YES on emotional / narrative-driven contracts (apocalypse, regime change, conspiracy disclosure), (b) NO sellers face long lock-up and demand a premium, (c) liquid markets attract speculation that biases mid-price upward of true probability. With a 1-year evaluation window and small bankroll, harvesting this premium is a risk-managed core trade — bond-like in payoff structure, with the spread being my "coupon."

**Selection rules.** I picked tail markets where:
1. Resolution is **mechanically clean** (specific source, narrow criteria) — not "consensus of credible reporting" alone.
2. **Spread ≤ 1¢** so taker entry doesn't eat the edge.
3. **Depth ≥ $10k at best ask** so my $5–10 ticket is non-impactful.
4. My **fair-value estimate is ≥ 50% lower** than the market's implied probability.
5. **Resolution before 2027** — keeps lock-up under one calendar year.

I rejected the NATO-withdrawal market after researching: Trump's April 2026 NATO threats + the explicit market language ("any action … regardless of if implementation is immediately halted") make 11.8% non-trivially defensible. Skip until I have a stronger view.

---

## Position #1 — NO on "Will Jesus Christ return before 2027?"
- Slug: `will-jesus-christ-return-before-2027`
- Token (NO): `51797157743046504218541616681751597845468055908324407922581755135522797852101`
- Resolution: end of 2026-12-31. Resolves YES if Jesus Christ has returned (presumably as defined by predominant Christian eschatology — UMA precedent on similar markets uses "broad consensus of credible reporting").
- Market: bid 0.961 / ask 0.962 / 1¢ spread / $623k depth at best ask, $786k depth at best bid.
- **Implied YES probability: 3.85%.**
- **My fair-value YES probability: ≤ 0.001%** — there is no defensible epistemic case for >1bps probability on a literal Second Coming in 8 months. Resolution risk is the only real concern: a fringe news event could trigger an UMA dispute, but UMA's precedent on these "miracle" markets is to resolve NO absent overwhelming evidence.
- **Trade:** limit BUY NO at 0.962, size $10.
- Payout if NO: $10.39 (+3.95% over 250 days ≈ +5.8% annualised).
- Risk: $10 if a global UMA-acceptable Second Coming event. Effectively a treasury-bill-like position.
- Sizing logic: Kelly/4 ≫ cap; clamp to 15% bankroll cap = $10.50, round to $10.

## Position #2 — NO on "Will Reza Pahlavi lead Iran in 2026?"
- Slug: `will-reza-pahlavi-lead-iran-in-2026`
- Token (NO): `96214953624495509683027302209340859673097705517450500531670409012928242777230`
- Resolution: 2026-12-31. YES if Reza Pahlavi de facto holds head-of-state powers.
- Market: bid 0.906 / ask 0.907 / 1¢ spread, but **best-ask depth is only $54** — my $10 ticket will sweep it and need to bid up to ~0.908 for the rest. Effective entry ~0.908.
- **Implied YES probability: 9.35%.**
- **My fair-value YES probability: ~1%.** Decomposition:
  - P(Iranian regime falls in 2026) ≈ 5–8% (see #5 below; I think the market overprices this too, but be conservative here).
  - P(Pahlavi leads | regime falls) ≈ 15–25%. He's the most-recognized exile figure but has no on-the-ground apparatus, no IRGC defectors publicly aligned, and Iranian opposition is fractured (MEK, Kurds, monarchists). A Pahlavi-led transition would be one of several plausible post-fall scenarios.
  - 0.07 × 0.20 = 1.4%. Round to ~1%.
- **Trade:** limit BUY NO at 0.908, size $10.
- Payout if NO: $11.01 (+10.1% over 250 days ≈ +14.7% annualised).
- Risk: $10 if regime falls AND Pahlavi takes power.
- Cluster note: 50% correlated with Iran-regime trade (#5).

## Position #3 — NO on "Will the US confirm that aliens exist before 2027?"
- Slug: `will-the-us-confirm-that-aliens-exist-before-2027-789-924-249`
- Token (NO): `7305630249804085635496399869905769372294302716159034447326228509068694952392`
- Resolution: 2026-12-31. YES if "the President, any Cabinet member, any member of the Joint Chiefs of Staff, or any US federal agency definitively states that extraterrestrial life or technology exists."
- Market: bid 0.79 / ask 0.80 / 1¢ spread / $58k depth at best ask, $82k at best bid.
- **Implied YES probability: 20.5%.** This is the most striking mispricing on the board.
- **My fair-value YES probability: 6–10%.** Decomposition:
  - Base rate: zero such "definitive" federal statement has ever been made in US history. UAP/UFO disclosure has ramped (NASA UAP report 2023, AARO ongoing), but every official agency statement has been carefully hedged to avoid claiming ET origin.
  - Trump-administration tail risk: Trump is unpredictable and has historically engaged with UAP topics rhetorically. There's a non-zero chance of a press-conference moment that UMA reads as "definitive."
  - Definition of "any federal agency" is generous — a single press release from, e.g., DoD's AARO with the wrong framing could trigger.
  - But "definitively states … exists" is a high linguistic bar; AARO has consistently used hedged language.
  - Putting it together: ~7% feels right; certainly nowhere near 20%.
- **Trade:** limit BUY NO at 0.80, size $9.
- Payout if NO: $11.25 (+25% over 250 days ≈ +37% annualised).
- Risk: $9 if any qualifying federal statement issues. Watch for: Pentagon/AARO press conferences, Trump remarks, NASA bombshell.
- Sizing: Kelly/4 ≈ 13% bankroll → $9.10 → $9.

## Position #4 — NO on "Trump out as President before 2027?"
- Slug: `trump-out-as-president-before-2027`
- Token (NO): `2849827372590072151380088930233312280478318575453624773762283369907909283027`
- Resolution: 2026-12-31. YES if Trump resigns, is permanently removed (Section 4 sustained), or otherwise ceases to be President for any period. Temporary 25th-Section-3 invocations explicitly excluded.
- Market: bid 0.83 / ask 0.84 / 1¢ spread / $11.6k depth at ask.
- **Implied YES probability: 16.5%.**
- **My fair-value YES probability: 4–6%.** Decomposition:
  - Mortality (79-yr-old US white male): ~5% per year actuarial, ≈ 3.4% over 250 days. Trump-specific health adjustments (overweight, McDonalds diet, but visibly active): +0.5pt = 4%.
  - Assassination risk: elevated (one survived attempt in 2024). ~0.5–1% over 250 days.
  - Resignation: extremely unlikely for Trump's personality and political situation. <0.3%.
  - Permanent removal via 25th Sec 4 sustained: requires VP + cabinet + 2/3 of both houses. Politically near-impossible with R-controlled Senate. <0.1%.
  - Sum: ~5%.
- **Trade:** limit BUY NO at 0.84, size $7.
- Payout if NO: $8.33 (+19% over 250 days ≈ +28% annualised).
- Risk: $7 if Trump dies, is assassinated, or is removed. The largest single-point risk in the portfolio is Trump health — he's 79 in a high-stress environment with active war. Sizing reflects this.
- Cluster: shares "world-stable" theme with Iran-regime; cap respected.

## Position #5 — NO on "Will the Iranian regime fall before 2027?"
- Slug: `will-the-iranian-regime-fall-by-the-end-of-2026`
- Token (NO): `106181075047366745139197108801635573283215248045056329679360376976893016488727`
- Resolution: 2026-12-31. YES if Islamic Republic core structures (Supreme Leader, Guardian Council, IRGC under clerical authority) are dissolved, replaced, or lose de facto power over the majority of Iran. Coups that preserve the Republic don't qualify.
- Market: bid 0.79 / ask 0.80 / 1¢ spread / $20.5k depth at ask.
- **Implied YES probability: 20.5%.**
- **My fair-value YES probability: 6–10%.** Decomposition:
  - Active conflict context (April 2026): US blockade of Strait of Hormuz, Iran-Israel-US ceasefire on the brink, Iranian ship attacks on commercial vessels. Tensions are real.
  - But the resolution bar is *very* high. Requires the Islamic Republic to lose core structures, not just military setbacks. Historical analogues:
    - Iraq 1991: sanctions + war did NOT topple Saddam. Took 2003 ground invasion + 2 years.
    - Libya 2011: NATO air support + indigenous rebellion + 8 months. Closest to a hypothetical Iran scenario, but Iran has no equivalent ground rebellion.
    - Syria 2024 fall: 13 years of civil war + final HTS offensive.
    - Iran 1979: revolution from within over years.
  - Trump's stated posture: "no boots on the ground." Without a ground component, regime change in 8 months is unprecedented.
  - Internal Iranian dynamics: aging Khamenei (in his mid-80s), succession risk, but the IRGC is a large, well-resourced security state with deep loyalty networks.
  - Putting it together: ~7–9%. Even pricing in news risk and tail scenarios, 20.5% is high.
- **Trade:** limit BUY NO at 0.80, size $7.
- Payout if NO: $8.75 (+25% over 250 days ≈ +37% annualised).
- Risk: $7 if regime falls. Watch for: actual ground operations, Khamenei's death + succession crisis, mass IRGC defection, Tehran losing control of provinces.
- Cluster: counts toward the "Iran" cluster with Pahlavi (#2). Combined exposure to Iran-related YES outcomes: $7 + 0.5 × $10 = $12. ✓ under cluster cap.

---

## Initial portfolio summary

| # | Market | Side | Entry | Size | Pay if win | Yield (8mo) | Annualised |
|---|---|---|---|---|---|---|---|
| 1 | Jesus returns 2027 | NO | 0.962 | $10.00 | $10.39 | +3.95% | +5.8% |
| 2 | Pahlavi leads 2026 | NO | 0.908 | $10.00 | $11.01 | +10.1% | +14.7% |
| 3 | Aliens confirmed 2027 | NO | 0.800 | $9.00 | $11.25 | +25.0% | +37% |
| 4 | Trump out 2027 | NO | 0.840 | $7.00 | $8.33 | +19.0% | +28% |
| 5 | Iran regime falls 2027 | NO | 0.800 | $7.00 | $8.75 | +25.0% | +37% |
|   | **Total deployed** |   |   | **$43** | **$49.73** | **+15.7%** | **+23.5%** |
|   | Reserve cash | — | — | $27 | $27 | 0% | 0% |
|   | **Bankroll** | | | **$70** | **$76.73** | **+9.6%** | **+14%** |

If all five resolve as I expect, the carry portion alone moves the bankroll from $70 → $76.73 by year-end. The reserve $27 is for higher-conviction directional bets identified through ongoing research; that's where the asymmetric upside lives.

## Execution plan (post-MATIC arrival)
1. Run `polyclaude_client.py approve` to set the 6 allowances (~0.01 MATIC).
2. Place all 5 limit orders as **GTC**. Polymarket fills against the resting order book; my prices are at-or-just-above the best ask, so they should fill close to instantly given depth.
3. Snapshot order receipts to `data/orders/<ts>.json`.
4. Append journal entry to `notes/journal.md`.

## Catalysts I'll watch
- US-Iran ceasefire: any breakdown could move both Iran-regime and Aliens (UAP-disclosure-adjacent if war goes very public). Strait of Hormuz reopening = bullish for the NO side of regime/disruption.
- Trump health / public appearances: any prolonged absence triggers Trump-out re-pricing.
- Pentagon/AARO press conferences: aliens-fade trigger.
- Khamenei health: Iran-regime mortality risk.
- US Congressional NATO action: not in portfolio but I'm watching, since I might add NATO trade if facts change.
