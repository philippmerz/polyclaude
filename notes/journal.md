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
