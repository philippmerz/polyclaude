# Polymarket discovery investigation — evaluation task

You are being evaluated as a candidate research model for an autonomous Polymarket
trading system. Work independently. Use web search and any market-data APIs you have
access to (Polymarket gamma API: https://gamma-api.polymarket.com/markets?slug=<slug>,
order books: https://clob.polymarket.com/book?token_id=<id> — token ids are in the
market's clobTokenIds field). STRICTLY READ-ONLY: do not place orders, do not touch
any wallet, key, or config file on this machine. Write your complete answer to
/tmp/kimi_eval_result.md when done. Note your start and end times.

## Part A — evaluate these 5 live markets (the core skill test)

For EACH market: (1) read the question AND the full resolution criteria (description
field — the exact wording matters), (2) verify the current real-world state with
fresh sources (cite source + date for every load-bearing fact), (3) give your fair
probability with one paragraph of reasoning, (4) recommend BUY YES / BUY NO / SKIP
at the current price, (5) name the single biggest risk to your recommendation.

1. slug: `will-the-chicago-bears-leave-illinois-by-dec-31`
2. slug: `iran-charges-hormuz-fees-by-august-31-20260625175039062-177`
3. slug: `will-there-be-at-least-5000-cyclosporiasis-cases-in-the-uptspt-by-july-31-2026-20260715005153975`
4. slug: `will-apple-release-a-touchscreen-macbook-in-2026`
5. slug: `will-spacex-have-the-highest-ipo-market-cap-2026-516`

## Part B — fresh discovery (the generative test)

Find 2-3 NEW mispriced markets among open Polymarket markets resolving in 5-30 days
with volume ≥ $3,000, where the market price tracks the colloquial reading of the
question but the resolution criteria set a materially different bar (stricter or
looser). Exclude: sports game odds, crypto up/down series, election odds, and the
five markets from Part A. For each find: slug, side, current book price (live ask if
you can fetch it), the verbatim criteria sentence creating the gap, your fair
probability with reasoning, the load-bearing fact with source + date, and the main
kill-risk. Quality over quantity — one genuinely verified find beats three
plausible-sounding ones.

## Part C — self-report

State: which tools you actually used (web search? direct API calls? neither?), what
you could NOT verify and guessed on, and your wall-clock time for the whole task.
