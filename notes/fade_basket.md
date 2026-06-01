# Behavioral-Longshot Fade Basket — 2026-06-01 second-pass scan

Answer to "nothing in 1000 markets?": NOT nothing, but the harvestable systematic
edge is a *class* — **behavioral-premium longshot fades** (sell NO on overpriced
meme/lottery/fear events where YES demand >> true prob). The market is otherwise
efficient (see scan results below). Each fade is individually small (~10-27% APY);
the play is a **diversified basket** across uncorrelated tails.

## Systematic scan results (2026-06-01, ~990 mkts)
- **Monotonicity arb** (`event_monotonicity_scan.py`): 204 multi-mkt events, 8 violations,
  only 1 net-positive after costs: **Multipli.fi launch by Jul-2027 (0.615) > by Oct-2027 (0.495)**
  — buy NO-Jul + YES-Oct = guaranteed ≥+12pp gross / +5.66pp net riskless. BUT 2027-dated (>1y),
  thin DeFi mkt → ~4-5% riskless APY over lockup. Marginal; check book depth before bothering.
- **Consistency arb** (`polymarket_consistency_scan.py`): none real (every gamma-midpoint flag
  evaporated under live CLOB asks — the known midpoint-unreliability problem).
- **Sports vs bookies** (`sports_pm_scan.py --with-consensus`): only near-term *games* checked;
  small noisy single-game deltas (max Royals-Reds +9.5pp, unreliable). WC winner futures NOT
  tested (favorite-longshot fade across 48 teams = tiny per-team edge, impractical at this scale).
- **Macro** (`macro_pm_scan.py`): efficient (Fed no-change PM 0.983 vs deriv-impl 0.99, Δ-0.75pp).
- **Iran/Hormuz crisis cluster**: rich term structures, internally coherent. No edge w/o a crisis
  view I don't have. (Hormuz-normal: Jun15 4%/end-Jun 18.5%/Jul31 39%/Dec31 76.5% — monotone, fine.)

## Validated basket (gate-checked)
| Market | Side | Price | P(YES) gate | APY | Status |
|---|---|---|---|---|---|
| US confirm aliens before 2027 | NO | 0.85 | ~1% (PURSUE tranches non-confirming) | ~28% | **HELD** $10.70 (DEC-0003 $9 + DEC-0029 $1.70) |
| US acquire any part of Greenland 2026 | NO | 0.865 | ~0.05% (Denmark refuses; sovereignty-only criteria, base-access excluded) | ~21-27% | **QUEUED** (validated, criteria clean) |
| ~~GameStop acquire eBay~~ | ~~NO~~ | 0.855 | **18%** (active hostile bid — NOT a meme) | **−EV** | **DROPPED** by gate |

Greenland NO token: `104895545296438735617666172336621441242754294947987367085791779928220778311973`
(verify YES/NO index + walk book before buying; tokens[0]=60745... presumed YES).

Unvalidated candidates (gate before sizing): China-invade-Taiwan 2026 (0.066), Hantavirus pandemic (0.053),
NK-invade-SK before 2027 (0.052), Alberta-joins-US (0.043). Smaller premiums, real tails.

## Deployment playbook (NEXT CYCLE — gated by Arb gas wall)
Capital: ~$30 idle in Arb Aave (crypto sleeve ...3eE6) @ 2.5%; PM wallet (...267B) liquid only ~$0.4.
Blocker: Arb ETH gas = ~$0.10 (need ~$0.50 for withdraw+bridge).
1. Gas-unblock: `across_bridge.py --sleeve crypto --from-chain base --to-chain arbitrum --token ETH --amount 0.0004 --yes`
   (Base has ~$1.0 ETH). Verify Across ETH minimum first.
2. `aave_deposit.py withdraw --chain arbitrum --amount-usdc 12 --sleeve crypto --yes`
3. `across_bridge.py --sleeve crypto --from-chain arbitrum --to-chain polygon --token USDC --amount-usdc 12 --token-out USDC.e --recipient <PM-wallet ...267B> --yes`
4. `wrap_pusd.py wrap --amount-usdc ~12 --yes`
5. Buy: Greenland NO ~$8 + aliens NO add ~$4 (or skip aliens-add; already held). Walk books first.
Net EV ~$2-3 over 212d on ~$12-20 — small; the value is proving the basket pipeline + diversification.
Concentration fine: aliens $10.70 = ~6-7% of ~$160 bankroll; Greenland would add ~5%.
