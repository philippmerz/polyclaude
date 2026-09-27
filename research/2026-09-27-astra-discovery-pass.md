# Astra broad-market discovery pass — 2026-09-27

## Objective and anti-bias design

The operator requested one measured GPT-6 Astra discovery pass over a large,
compact market batch, specifically to surface ideas the existing process might
not originate. Astra received no journal, backlog, watchlist, prior picks or
prior rejection context.

The public Gamma event universe contained 56,031 active rows. A mechanical
execution-context filter retained 5,189 rows:

- liquidity at least $500;
- 24-hour volume at least $20;
- displayed spread at most 5 percentage points;
- resolution horizon at most 370 days.

The 2,000-row input contained the 300 highest-volume survivors plus 1,700 rows
selected by fixed SHA-256 order using seed
`astra-discovery-v1|2026-09-27`. There were zero manual exclusions. Each TSV
line carried title, outcome prices, YES bid/ask, spread, horizon, end time,
liquidity, volume, source field and a 120-character criteria cue. Exact full
criteria remained available in the paired JSON for nominated rows.

- Compact TSV: `data/snapshots/astra_discovery_20260927T2220Z_compact.tsv`
- Compact SHA-256: `2e84e32a3e314231f86433cbe06cfe1ecdbc3addfc53157e4341f0a625c5c3d5`
- Compact size: 584,700 bytes / 2,000 rows
- Full selected JSON SHA-256:
  `e19e162f85b326c0a26a5f8c93dae84ad3ebca4a288011e232f919cc234e9586`

Snapshot quotes were screening context, never execution evidence. Astra read
all 2,000 rows and inspected 21 full criteria records. It used no external web
search and made no edits or transactions.

The direct quota probe read **7% weekly Codex usage / 93% headroom** before
batch preparation and **8% / 92%** immediately after the Astra pass, before
candidate validation. The end-to-end preparation plus one pass therefore moved
the meter by **one percentage point at its displayed precision**. This is an
upper bound on the isolated Astra call because primary-agent batch preparation
occurred between the two readings.

## Astra's unfiltered top ten

These are research leads, not entry recommendations. Rankings are preserved
before root-agent validation.

1. **Kuwait recognition / Abraham Accords conditional pair** — buy market
   `2412369` recognition YES and `665471` Accords NO at a snapshot sum of
   0.958. The apparent floor exists only if a qualifying Accords signing must
   also satisfy formal recognition.
2. **Rhine first crossing in October** — buy NO in `4294627` if the Kaub gauge
   had already crossed 77 cm in September or if current hydrology made an
   October first crossing sufficiently unlikely.
3. **Trump renames AI by September 30** — buy NO in `4769494`; speeches and
   informal rebranding do not qualify without a signed presidential action.
4. **China PR–Turkmenistan draw** — market `4685134` has a cancellation clause
   resolving a complete cancellation without a makeup match to YES; verify the
   fixture rather than infer sports performance from its 0.963 price.
5. **El Niño RONI at least 2.5** — NO in `3680999`; the resolver uses NOAA's
   Relative Oceanic Niño Index across named windows, which may be confused with
   ordinary ONI or Niño-3.4 forecasts.
6. **Miami median value band** — YES in `2760534` only if Parcl dataset 47 has
   sufficient buffer. Resolution is price per square foot multiplied by 2,100,
   not an observed median home transaction.
7. **Taylor Swift album in 2026** — NO in `1686673` if the anticipated release
   is a deluxe/reissue with fewer than 50% never-released tracks.
8. **Nothing Ever Happens 2026 union** — NO in `1060714` may be cheap relative
   to the Iran-invasion leg, but the incorporated PDF definitions must be read
   before asserting an implication.
9. **Republican House odds touch 12%** — YES in `4826263` depends on four
   consecutive published hourly PredictionMarketOdds values, not the terminal
   election result; inspect the exact series for a prior or plausible run.
10. **CMI declares Navier–Stokes solved** — NO in `4412661`; a proof claim or
    community acceptance does not qualify without an official Clay Mathematics
    Institute declaration or prize award.

Items 4–10 remain preserved as unvalidated hypotheses. They are neither entry
signals nor due follow-ups.

## Independent validation of the top three

### 1. Kuwait pair — novel but not a guaranteed arb

At 22:26–22:27 UTC, both fee-free books matched the exact identities:

- recognition YES ask: 0.038 for 259.57 shares;
- Accords NO ask: 0.92 for 143.10 shares.

The simultaneous pair cost 0.958 and had 143.10-share displayed capacity. Its
per-share terminal payout is:

| Formal recognition | Accords signing | Payout |
|---|---:|---:|
| No | No | $1 |
| Yes | No | $2 |
| Yes | Yes | $1 |
| No | Yes | $0 |

The exact Accords criteria require a formally signed normalization agreement
publicly acknowledged by both governments and attributed to the Accords. The
recognition market independently requires formal state recognition. Ordinary
diplomatic meaning strongly links them, but neither contract says a future
normalization signing necessarily satisfies the other market's formal-
recognition test. The zero-payout state is therefore not excluded by the
written criteria. Cross-market execution is also non-atomic. **No trade:** this
is a useful semantic-relative-value lead, not a robust guaranteed edge.

### 2. Rhine October first crossing — source measured, probability missing

Official PegelOnline history for Kaub station 25700100 from market start
through 2026-09-28 00:15 Berlin time contained 2,046 readings, zero at or above
77 cm, a 36 cm maximum and a latest reading of 3 cm. The exact market pays YES
only if the first post-start 77 cm reading occurs during October; a single
transient reading suffices.

The fresh book showed NO at 0.62 with substantial displayed depth. Its 5%
quadratic taker fee made the top-share all-in cost about 0.6318. The observed
history is directionally favorable to NO but does not produce a defensible
October rainfall/runoff forecast or prove p(NO) above that price with an
uncertainty buffer. **No trade.** Primary source:
[PegelOnline station history](https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/1d26e504-7f9e-480a-b52c-5932be6549ab/W/measurements.json?start=2026-09-06T16%3A26%3A59%2B02%3A00&end=2026-09-28T02%3A00%3A00%2B02%3A00).

### 3. Trump AI rename — literal thesis right, price too high

The exact criteria require a signed executive order, proclamation or
presidential memorandum replacing the federal designation for the technology.
Speeches, polls, press statements, office renames and incidental alternative
wording are explicitly excluded.

Trump's September 22 address called AI “Super Intelligence,” and a September
25 fact sheet used that term, but neither is a qualifying presidential action.
The White House Presidential Actions index and Federal Register search showed
no qualifying document at validation time. The fresh NO ask was 0.69; the 4%
quadratic taker fee made the touch about 0.6986 all-in. A conservative
p(NO)=0.70–0.80 range falls to 0.60–0.70 under the required 10-point instance
stress, leaving no robust edge. **No trade.** Primary checks:
[White House speech release](https://www.whitehouse.gov/releases/2026/09/president-trump-at-the-united-nations-while-others-have-talked-i-have-acted/),
[White House fact sheet](https://www.whitehouse.gov/fact-sheets/2026/09/fact-sheet-president-donald-j-trump-advances-a-fair-and-reciprocal-relationship-with-china-while-hosting-historic-state-visit/), and
[Presidential Actions index](https://www.whitehouse.gov/presidential-actions/?s=artificial+intelligence).

## Scanner implications

The pass found a semantic pair absent from the existing research context, so broad model discovery
has value even though no top lead survived. It also exposed input-quality gaps:

- 1,194 of 2,000 compact rows had an empty structured source field even when
  their descriptions named a source;
- 215 rows lacked a displayed YES bid despite passing coarse liquidity filters;
- category labels misclassified several markets;
- metadata deadlines often differed from the operative criteria window.

A productive architecture is therefore: deterministic broad batching, one
independent model ranking, then exact-criteria/primary-source/live-book checks
on the unchanged top ranking. At the measured cost, this is suitable for
occasional broad discovery or major universe changes, not every quiet tick.
Future batching should extract sources and operative windows from criteria and
carry explicit desired-side depth; those are data-quality improvements rather
than model-based preselection.

Tempting false positives Astra rejected before validation included executable-
price failures in unemployment and FrontierMath ladders, a 1.001 Hormuz hedge,
non-equivalent Starship failure wording, and non-equivalent HLE thresholds.
