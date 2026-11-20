# polyclaude

A small, real-money experiment in which AI agents trade [Polymarket](https://polymarket.com) prediction markets and hold a modest crypto sleeve. It started from **$170** contributed in April 2026: $70 on the 25th and $100 on the 29th.

**Live dashboard:** [merz.page/polyclaude](https://merz.page/polyclaude/)

See also the [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B) and the two wallets on DeBank: the [prediction-market wallet](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B) and a [separate crypto wallet](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6).

## Where things stand

As of the 20 November 2026 evening mark (18:59 Europe/Amsterdam), the whole account was **$152.14**. Trading value, which excludes separately funded gas, was **$148.29**, or **12.8% below** the $170 that went in.

Positions are marked at midpoint; open contracts have not settled.

The book is a mix of Polymarket positions — including leftover Anthropic year-end valuation bets, a Nasdaq-100 addition trade, and a few longer-shot contracts — plus Bitcoin, ether, and HYPE accumulated in mid-November.

## The path so far

The desk opened on 25 April 2026. For most of the first half of the year it was almost entirely a prediction-market book: fading long-shot political claims, collecting payouts when the improbable did not happen.

Late August was the high point. A short-dated Google Maps bet on “Lake America” paid out in full, and the recorded whole-account value printed **$226.95** on the morning of 30 August. That print is a settlement-window checkpoint, not a fully broken-out valuation, but the account was still marked above $215 later that day. A later, more complete trading mark reached **$192.86** on 26 October, about 13% above the $170 contribution.

In early November the mix shifted toward an 80/20 split: a core of Bitcoin, ether, and HYPE, with a smaller sleeve still hunting for mispriced markets. That core has been the main drag since — especially Bitcoin, bought near $75,000 and marked at about $59,100 on 20 November.

This past week the Anthropic IPO priced and began trading. The desk sold three “market cap stays below $X” contracts into 99-cent bids after Nasdaq’s displayed cap came in under every strike, and it still holds some cheap “will not land in a far-out year-end cap bracket” contracts. Several AI models have taken a turn running the book.

## Biggest winners

- **“Lake Ontario” becomes “Lake America” on Google Maps (August).** Yes shares bought for $12.34 redeemed in full on 30 August for a **+$28.62** profit, a 232% return, after the official geographic name change was followed by a Maps rollout.
- **GPT-6 would not ship by 31 August.** A no position sold on 18 August for $31.96 against a $21.94 cost, **+$10.02** (46%). The market later resolved no.
- **Trump’s approval rounding to 38.5–38.9 on 18 September.** A tight polling-band yes, bought for $5.32, paid **+$7.58** after fees — a 142% return — once the resolving series printed 38.5.
- **Anthropic’s IPO cap stays below $1.4T, $1.35T, and $1.275T (November).** Three yes legs bought on 16 November for $15.93 were sold on 20 November for $21.94 as Nasdaq showed a cap under every strike, a **+$6.01** gain before fees (about $0.18 of taker fees were recorded on the way in).
- **No permanent US–Iran peace deal by 31 May.** A no position held to resolution and redeemed for **+$5.62** on an $11.82 cost (48%). A related 15 May contract had already paid **+$3.54**.

## Biggest losers

- **A Russia–Ukraine ceasefire market (May).** The largest closed loss: **−$16.73**, about 10% of the bankroll at the time. The desk bought no; an official dispute then resolved the market yes on a short, announced ceasefire.
- **The GTA VI trailer-views market (late August–early September).** Total about **−$14.13**. One ticket correctly bet that the trailer would clear 20 million views, then was sold too early for a $6.52 loss; a later ticket on the other side lost another $7.62.
- **Bitcoin and HYPE since the mid-November shift.** Not a closed trade. The same 0.0009397 wrapped Bitcoin that marked at $70.27 on 9 November was marked at $55.53 on 20 November (**−$14.74**). The unchanged HYPE holding went from $12.73 to $10.36 (**−$2.37**). Some ether was later sold to fund Polymarket trades, so that leg is not a clean price comparison.
- **No US–Iran peace deal by 15 June.** A follow-on no, cost $11.31, went to zero when a memorandum of understanding was signed on 17 June: **−$11.31**.
- **SpaceX as 2026’s highest-IPO market cap, sold in August.** Exited for a realized **−$5.62** after a checkable Anthropic valuation fact in the original thesis turned out to be badly wrong. A later, smaller closed miss: a yes on “no dissent” at the October Fed, cost $4.80, expired worthless when two governors dissented for a hike.

A 100-share no on “Anthropic’s closing market cap exceeds $1.0T,” bought for about $0.40 is now worthless. “Anthropic flips Bitcoin by 31 December” was passed at a 0.82 ask and later resolved yes.

A few long-shot yes positions are still open and underwater, including a bet that a Kimi model posts a high Humanity’s Last Exam score (about $13 in, marked around $6.80 on 20 November) and that Delcy Rodríguez is Venezuela’s leader at year-end (cost $5.04, marked about $1.82).

Not financial advice.

---

How the dashboard is built: [docs/README.md](docs/README.md). Operator tooling and repository layout: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
