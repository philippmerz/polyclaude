# Oil option proxy crosscheck — October 18

Primary read the correctly identified DEC26 LO put rows in the captured October16
preliminary CME bulletin. At strikes80 and85 the premiums are $0.52 and$0.99 per
barrel; the matching CL DEC26 futures settlement is99.02. Neighboring puts at
79.5/80.5 are0.49/0.56, and84.5/85.5 are0.93/1.06. The original broad page-level
extract included other contract months; use the [row correction](../../../data/deep_review_20261017/oil_terminal_data_followup_0238_correction.json),
not an unfiltered row labelled DEC26 merely because that heading appears elsewhere.

The [reproducible calculations](oil_option_proxy_crosscheck_0325.json) show:

| Strike | Single-strike total volatility | Model expiry CDF | Rough Nov2 CDF sensitivity |
|---|---:|---:|---:|
|80|15.41%|9.56%|3.27%|
|85|14.46%|16.26%|8.13%|
|100|13.96%|55.58%|55.87%|

These are derived Black76 European approximations with unit discount, not a
published CVOL observation or a physical forecast. Each strike has its own fitted
volatility, so its CDF is not the derivative of a fitted smooth smile. The
neighboring put-spread slopes are about7% and13%, with cent-rounded settlements;
their digital interpretation also requires European-style/discount assumptions.
These are American options, which can be exercised early into futures.

Official Chapter200 gives a formula-derived CLZ6 last trade of November20 under
ordinary calendar assumptions. Primary read current Chapter310 in full: monthly
options expire on the third business day before their underlying and are American.
That gives November17 under those same assumptions; no dated listed-contract
calendar row or exception was retrieved. The rough short-horizon column scales
variance by17/32 from October16 to November2 versus November17, ignoring session
times, daylight-saving details, jumps and term structure. The corresponding
32-day annualizations are about52.1%,48.8% and47.1% respectively; none is CVOL.

The earlier shared model assigns 8.466% below80 and19.06% below85 on November2.
These proxy observations make that low-oil mass worth challenging, particularly
the85 threshold. They do not directly replace it: CME CL is a different basis
from ICE Europe WTI/Pyth CLL, options embed a risk-neutral rather than physical
measure, and the old diplomacy/price/Senate dependence is a subjective joint
scenario model. A crosscheck is not a new calibrated distribution.

**Decision:** no financial action or reserve reduction. Preserve the original
dated cases. Their positive central EVs are research signals rather than entry
approval; an updated forecast must incorporate this proxy and its limitations,
with a separately dated model if weights change. Exact CLL data remains missing,
and the full post-creation CME High path for case92 is still unresolved. See the
[official rulebook follow-up](../../../data/deep_review_20261017/oil_cme_rulebook_followup_0238.json)
and [primary Chapter310 rendered capture](../../../logs/deep_review_20261017/cme310_primary_rendered_0323.json).
