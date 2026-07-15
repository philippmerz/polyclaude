# New-listing mispricing study — 2026-07-15

**VERDICT: FALSE as a taker-entry population edge** (decisive, mechanism identified). Real as a
statistical artifact on quote midpoints; UNKNOWABLE (structurally doubtful) as an instance-gate
edge without a forward paper ledger. **Do not build the buy-side monitor.**

Background research agent, ~34min. Data: listings cohort Apr 1–May 26 2026 (200k closed vol≥$1k
markets, gamma keyset crawl), N=833 non-series binary decisively-resolved, life ≥120h, paths
anchored at `acceptingOrdersTimestamp` (CLOB prices-history, 10min fidelity); +170 series
controls; 260-market early-trades pull (data-api); 60 live young-listing books; full listing
censuses Apr 1-7 (61,708) and Jul 8-15 (97,356). Small artifacts preserved here; bulk crawls
(~330MB jsonl) were ephemeral in /tmp/listing_study/.

## The hypothesis was TRUE on mids…

ECE (weighted |empirical−implied|) by age: T+1h **22.4pp** → 6h 13.5 → 24h 10.5 → 72h **9.0** →
mid-life 7-9 → close−24h 3.4. Matched-market bootstrap ECE(1h)−ECE(72h) = **+13.3pp
[+9.4,+16.9]**. One-directional: at 1h, [0.3,0.5) implied 46% → resolved 17% YES; [0.5,0.7)
implied 51% → resolved 35%. Thin-volume tercile worst (31pp at 1h); high-volume converges by 72h.

## …and untradeable for three independent reasons

1. **The early "price" is a phantom.** prices-history = sampled quote MIDPOINTS, not trades.
   80% of first prints in [0.45,0.55]; 69% of 1h mids still in the placeholder zone; placeholder
   mids "imply" 49.5%, resolve 23.7% YES. The miscalibration ≈ stub-mid artifact + base rate —
   the midpoints-unreliable house lesson at population scale.
2. **No counterparty.** Mid-priced subset (N=260): 95% had ZERO trades in hour 1, 82% in 6h,
   62% in 24h. Live young one-off books: 17/60 spread ≤5c; 15/60 absorb $15 within 3c.
3. **Where fills existed, takers lost.** Early YES-takers (0-24h): paid 0.55 avg, won 38% →
   **−16.8c/share** (N=58). Early NO-takers (0-6h, ≤0.70): −13c/share — cheap early NO was
   adversely selected (seeders aren't naive). Only +EV cells are sign-flipping hindsight noise.

## Salvage (kept)

- **Base-rate prior:** one-off "Will X happen?" listings (vol≥$1k) resolve YES only **23%**
  (survivorship-bounded ≤34%). A new listing's 0.5 placeholder mid carries ZERO information —
  instance gates on newsworthy-longshot phrasings should start from a ~3:1 NO prior.
- **Early repricing is 3-4× denser** (|p1h−p72h|≥10pp in 63% of markets vs 18% baseline) — more
  gate-relevant divergence per market-day early, IF the gate can out-estimate seeders (the 0-6h
  adverse-selection result says that's hard).
- **The profitable seat is the MAKER's** (early YES FOMO donates ~17c/share to quoters).
  Different strategy: two-sided quoting, inventory risk, competition with pro seeds. Untested —
  needs book-history sim before any capital. Flagged, not queued.
- **2026 fee regime:** ALL new listings carry taker fees = (takerBaseFee bps) × min(p,1−p)/share
  (observed 1000bps on sports/crypto series; politics ~4% / sports 5% / crypto 7% effective).
  Our legacy book (4 Dec-31 legs + US-invade, all 2025/early-2026 vintage) is fee-free —
  verified takerBaseFee=None on all 5. **polyclaude_enter.py made fee-aware same day** (gate +
  Kelly + sizing on effective cost; verified live: 0.579 ask → 0.6211 effective at 1000bps).

## What would reopen this

(a) forward paper-ledger (N≥50) of gate p̂ vs actual young-book asks netting the 4-7% fees;
(b) maker-seat pilot with strict inventory caps (book-history sim first);
(c) a subclass with real depth AND provably naive seeds (none found in this sample).
