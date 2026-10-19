# Financial observation — October19 22:58 UTC

**Authoritative bankroll195.55 including5.84 separately funded gas; trading189.71 midpoint/187.14 indicative fee-net depth versus170 contributed.** Producer window22:58:50.210302–22:59:05.560272UTC, before Parton400 submission. Sequential rounded values are not synchronized NAV or guaranteed proceeds; VM/API costs excluded.

|Same producer field|USD|
|---|---:|
|TOTAL BANKROLL|195.55|
|Separate gas|5.84|
|PM midpoint|34.57|
|PM indicative net depth|32.00|
|Trading midpoint:195.55−5.84|189.71|
|Trading depth:195.55−5.84−34.57+32.00|187.14|
|Reported cumulative accounting residual|19.71|

- Residual19.71 is reported accounting arithmetic, not an independently audited cash-profit ledger. Displayed trading midpoint minus170 is also19.71 because displayed PM marked P&L rounds0.00. Trading depth contribution ratio+10.08% is not a time-weighted return.
- Producer warning gives midpoint/depth gap2.58 using its internal values; displayed PM34.57−32.00 gives2.57. CSV/chart use the documented formula on displayed fields, yielding187.14; this one-cent rounding difference is not a price move or corrected historical observation.
- One successful `.venv/bin/python -B scripts/bankroll.py`, rc0. Initial resolved-interpreter invocation failed on import before script work; retained privately, not a second financial observation. Successful CLI body SHA256 `65483eb5c7c76e11d4b8d4908362fcd633baaecdc34c47637b567bd78376c7eb`; SDK/CLI serialization, not raw-wire or source authentication. [Compact pre-entry proof](../data/deep_review_20261017/work/0400_preentry_2300.json).
- pUSD20.45, original three open BUY commitments6.50, available13.95 at this window. Later5NO46c Partonbid is a separately verified unfilled2.30 commitment; no new cashflow, holding or financial producer is inferred. Existing eight indexed rows include settled claims; active position count is six, excluding unfilled orders.
- CSV timestamp22:58:50Z is a `check_window` anchor. Append observation224, retaining all223 earlier rows; gas recorded from this same producer. Financial figures retain this date despite later account/config/document verification.
