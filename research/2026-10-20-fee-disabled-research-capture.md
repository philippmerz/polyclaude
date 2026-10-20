# Fee-disabled public research capture

**Repaired a reader limitation encountered during case438; no financial writer changed.** The original05:40 capture had exact Gamma/books but failed because the compact CLOB response omitted `fd`. Gamma explicitly supplied `feesEnabled=false`; full CLOB metadata separately reported numeric zero fees. This was a schema/evidence gap, not an inaccessible contract or rejected opportunity.

- Missing/null `fd` now requires exact frozen/Gamma identity, strict boolean fee-disable, an absent/null or valid zero Gamma schedule, exact duplicate-free compact mapping, and a newly captured full CLOB response with the exact condition/outcome/token mapping and numeric zero `taker_base_fee`.
- Descriptor and structured-schedule parity remain null. A separate evidence label binds the corroborating full response's receipt/hash/time; no compact descriptor or verified structured parity is invented.
- Missing, nonzero, malformed, nonfinite, boolean or contradictory fee evidence fails closed. Fee-enabled markets retain their descriptor/parity checks. Duplicate/extra/malformed outcome-token rows cannot collapse into a seemingly correct map.
- The original partial capture remains unchanged. Fresh case438 capture05:53:31UTC returned exact Gamma, two books, one fee-free corroboration, zero descriptors and zero errors. Root verified all five raw/gzip response pairs. See [quote](../data/deep_review_20261017/0438_quote_repair_0556.json) and [costs/receipt hashes](../data/deep_review_20261017/work/0438_economics_0557.json).
- Validation: `.venv/bin/python -m pytest -q tests/test_deep_review_public_snapshot.py` —24 passed, including integration success, inconsistent/missing fees, identity duplicates and the original enabled-fee path. `git diff --check` passed.

This verifies dated research inputs. It does not prove current executability, future fees, eligibility or any account gate. [Case438](2026-10-17-deep-review/evaluations/0438.md) remains no-entry after both-side, maker, carry and portfolio review. The finite review continues; no global methodology block was established.
