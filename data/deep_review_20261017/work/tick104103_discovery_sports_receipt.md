# Sports scan receipt — tick 104103

Command: `.venv/bin/python scripts/sports_pm_scan.py --hours 36 --with-consensus --consensus-top-n 3`

Terminal observations: 64 markets met scanner thresholds (24h volume ≥$30,000; liquidity ≥$5,000); top 20 output rows were within 36 hours. Consensus was attempted for three candidates. All three returned `NO_CONSENSUS`: Wild–Oilers had no verifiable non-Polymarket bookmaker odds; Barcelona’s 1X2 opponent was absent from Gamma question/rules; Napoli’s 1X2 YES side did not match the named winning team. The table also marks in-play matches `SKIP_IN_PLAY` where applicable. The scan reports no bookmaker delta for these candidates.

This receipt summarizes captured stdout; it is not a raw API response. The scanner’s endpoint/page coverage is not reported by its output, so it does not establish universe completeness. Displayed APY is win-assumed carry, not expected return.
