# HLE UMA proposal exception — 2026-09-09

Status: resolution risk review; **not a resolved outcome**.
Observed 14:19–14:26 UTC during the full check. Prior automated HOLD results
used pre-proposal probabilities and must not be called fresh underwriting.

## Verified source conflict

[OpenAI ≥50 Gamma](https://gamma-api.polymarket.com/markets/3072351) now reports
`umaResolutionStatus=proposed`, YES/NO .997/.003, closed=false and
acceptingOrders=true. Two entries in `umaResolutionStatuses` both say proposed;
that array alone does not prove two disputes, proposals or finality. Held 15 NO.
Direction, proposal transaction, challenge deadline and binding result require
independent verification; a near-YES price does not establish them.

Bounded follow-up inspected Gamma, standard/managed Polygon optimistic-oracle
contracts and the UMA subgraph without locating the matching request/event.
These details remain **unknown**, not absent. Gamma `submitted_by` and
`resolvedBy` are not proof of the UMA proposer. The official
[OOv2 interface](https://raw.githubusercontent.com/UMAprotocol/protocol/master/packages/core/contracts/optimistic-oracle-v2/interfaces/OptimisticOracleV2Interface.sol)
places proposer and expirationTimestamp in `ProposePrice`; `customLiveness=0`
alone supplies no deadline. Reported via Telegram 923; no bond,
dispute or financial write. Next scheduled/actual resolution-event check
should inspect this exact exception before relying on old cached priors.

The [named HLE board](https://agi.safe.ai/) remains reachable. The structured
live-vs-Jan-15 comparison found all ten model rows and both displayed score
columns unchanged; claude/grok/gemini coverage passed. Top OpenAI GPT-5 is
25.3 accuracy, top Gemini 3 Pro 38.3. This confirms the measurement, not the
resolver's interpretation. Earlier official tool-enabled threshold-clearing
results were already known; no new capability threshold is inferred here.

All four held criteria were read. OpenAI ≥50/≥55 and Gemini ≥50 specify the
named board, with alternate official results gated on source unavailability,
not simple staleness. A proposal while the source is reachable therefore tests
the resolver-behavior branch. It is **not yet an established precedent**.
Gemini Pro debut ≥40 instead expressly requires a newly added qualifying Pro
row, evaluates its displayed accuracy on the next ET calendar date at noon,
and defaults NO if none is added by year-end; don't collapse those predicates.

## Exact identities and observed exit depth

Numbers below are fee-adjusted hypothetical full-quantity bid walks, not
simultaneous available cash. Gamma/CLOB token and condition identity matched.
All use the compact CLOB fee descriptor: rate .04, exponent 1, taker-only.

| Held NO leg / Gamma ID | Shares | UTC | Bid / ask | Net walk | Book age |
|---|---:|---|---|---:|---:|
| OpenAI ≥50 / 3072351 | 15 | 14:26:10 | .001 / .005 | $0.0144006 | 936s; not fresh |
| OpenAI ≥55 / 3072352 | 19 | 14:25:11 | .14 / .15 | $2.568496 | 3.15s |
| Gemini ≥50 / 3072356 | 59 | 14:26:11 | .192 / .199 | $10.6832664 | 527s; not fresh |
| Gemini Pro debut ≥40 / 3212719 | 169 | 14:26:11 | .11 / .12 | $17.928196 | 207s; not fresh |

Each targeted walk had zero unfilled quantity. This does not certify all
13 positions in the account aggregate. Apple NO 49-share walk was $11.82940568,
but its book timestamp was 1600s old; do not call it a fresh exit quote.

OpenAI ≥50 condition:
`0x432986c91a2a364d37179db26f78e8b7b69a5da3c0bc7e09a3458918dc6ad34a`.
NO token:
`46758607612833917422236285013995068496804632645622273981549757589704779851841`.
OpenAI ≥55 condition:
`0xd30e3b4e2d6bf4594f44ad982b55435c3add71d3622993b0dee67354defaf598`.
NO token:
`2261859210057397360733755370829699556983953980550942465322842594827769255576`.
Book source: `https://clob.polymarket.com/book?token_id=<NO token>`;
fee source: `https://clob.polymarket.com/clob-markets/<condition>`.

## Disposition and reopen conditions

No trades, cancellations, disputes/bonds or redemptions. NO ADD / NO FLIP.
Numeric priors .35/.40/.55/.60 and original verification dates are preserved,
not newly endorsed: an unresolved proposal alone does not supply calibrated
replacement probabilities. OpenAI ≥50's indicative residual bid is only
1.4 cents for the whole position; recovering it cannot materially rescue
account performance. Prioritize determining finality and the remaining
correlated exposure, especially the same-wording ≥55 / Gemini ≥50 legs.
An exit decision needs fresh books and a current resolver assessment;
standing premium SELLs are not thesis-break exits. HLE is not an atomic group.

Separately, [Hormuz-normal Gamma 2774056](https://gamma-api.polymarket.com/markets/2774056)
is proposed at YES/NO .0005/.9995 and is economically closed except dust. Its
four pending decision grades remain ungraded until genuine finality. No gas
spend or payout assumption follows from a proposal.
