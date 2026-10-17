# Primary state election valuation — October 17

The primary read the entire frozen rules for Texas, Michigan, Idaho, Maine and
New Hampshire Senate and California, Arizona and Michigan governor. Seven party
nominee contracts include replacement nominees, with Senate runoffs explicitly
counted; an independent is
not a major-party nominee simply because of prior affiliation. California is
the named Steve Hilton claim with its own July 31, 2027 Other fallback. All
require AP, Fox and NBC to agree or official certification; they do not resolve
merely from the first projection or election-night share. These are not the
House district contracts' later party/caucus-at-all-calls language.

## Facts and provenance

The packet is `data/deep_review_20261017/election_extension_sources.json`, with
TX/MI Senate facts also in `macro_election_sources.json`. Poll release dates
are not field dates. Root retrieved the original YouGov NH questionnaire and
tables at 19:59; its cryptic URL filename does not replace its internal dates,
September 28–October 5. Q6 names Pappas and Sununu, shows 51–43 and residual
undecided/other, and says undecideds are asked a preference and allocated. This
is more information than an unallocated generic-ballot response, but still a
turnout/model sample rather than cast ballots.

The original packet's two Suffolk PDF URLs were guessed paths returning HTTP
200 HTML. Root checked MIME/magic bytes and did not accept those as PDFs.
The actual official index links are in the source correction packet and the
individual reports: Maine October 14 release and Michigan September 22 release
under `research-at-suffolk/suprc/polls/other-states/2026/`. The reported poll
numbers were subsequently verified from those correctly linked original files.
The URL correction preserves the retrieval failure, rather than treating it as
a contradiction in the poll result. The current source list must supersede the
earlier packet's wrong URL fields.

Load-bearing poll observations:

| Race | Field / publication | Observation and limits |
|---|---|---|
| TX Senate | Marist Oct8–11; UT Sep25–Oct5; Siena Oct5–8; YouGov through Oct5 | D leads2,3,4,6 points. Different likely-voter definitions/modes; these are selected located surveys, not four independent elections. |
| MI Senate | Marist Sep24–27; Fox Sep24–28; YouGov throughOct4 | D leads7 among Marist RV,1 and1 among the two LV surveys. RV result receives less weight. |
| CA governor | IGS Sep15–20 (field/mode metadata secondarily attributed) | Becerra58/Hilton33/U9, weighted4512LV. Large lead is not a measured tail probability. Official voter guide binds these two names/parties. |
| AZ governor | Equis Sep1–9, publishedOct6 | Hobbs49/Biggs43. n1214RV includes Latino oversample;3.2pp overall MoE is used conservatively for its reported LV result, not the4.9pp subgroup MoE. Political sponsor and older field dates retained. |
| ME Senate | Suffolk Oct8–11, publishedOct14 | Jackson49/Collins47/U4;500LV, live phone,4.4pp MoE. One close poll does not erase Collins's individual crossover appeal. |
| NH Senate | YouGov Sep28–Oct5, publishedOct7 | Pappas51/Sununu43,1520LV,3.9pp MoE; original question checked. Earlier UNH narrow-lead abstract is context, not a second numerical likelihood. |
| MI governor | Suffolk Sep16–20, publishedSep22 | Benson51/James34 with minor parties and8% undecided;500LV, live phone,4.4pp MoE. One older large lead, not a current series. |
| ID Senate | current Cook context | Risch incumbent, R+18 PVI and SolidR. No current independent matchup poll or complete final official ballot captured. |

## Primary probabilities and error structure

`state_election_model.py` reproduces every coefficient and sensitivity. These
are deliberately transparent primary judgments, **not calibrated probabilities**.
The normal update is only a tractable sensitivity for vote margin. Weak prior
D-margin means are TX−4, MI Senate+4, CA+20, AZ+4, ME0, NH+6 and MI governor+4,
with8–10pp prior SD. They express historical party environment, incumbency and
candidate context, not a fitted regression or a Cook-label-to-probability table.
The Maine zero prior explicitly allows Collins's personal vote to offset the
state's Democratic lean. The Texas prior keeps a Republican structural branch
despite every located recent poll's Democratic lead.

Poll margin uncertainty uses **twice** the candidate-share MoE divided by1.96,
then adds4pp common nonsampling error and1.5–3pp age/turnout movement in quadrature.
For multi-poll states it conservatively retains the maximum listed MoE; it does
not divide common error by the square root of the number of polls. TX's weighted
D lead is3.25 (.40×2+.25×3+.20×4+.15×6), MI Senate2.2 (.20×7+.40×1+.40×1).
Equis's AZ result is shifted1pp against D as an explicit sponsor/selection
sensitivity, not an estimated house effect. The other bias centers remain zero.

After a precision-weighted normal update, a5% unmodeled symmetric outcome branch
(2% for CA) prevents interpreting tiny normal tails as proven event frequencies.
That branch weight is itself subjective and may be too small; the ranges allow
much larger uncertainty. ID uses a separate national/PVI/incumbency margin
sensitivity with9pp SD and2% unmodeled branch, not invented polling.

Rounded YES forecasts are TX(R).44, MI Senate(R).29, CA(Hilton).01, AZ(D).82,
ID(R).985, ME(R).40, NH(D).91 and MI governor(D).96. Scenario ranges are in the
individual records and code, deliberately wider than the saved ±4pp poll/prior
sensitivity grid. They are neither confidence intervals nor guaranteed floors.
Polls can miss together; MI governor and Senate especially share turnout and
state polling error. Cross-state Democratic-wave exposures also correlate with
our House candidates. No independent Kelly addition is appropriate.

## Catalyst, horizon and economics

Early voting, October polls, nominee developments, campaign events and November3
are the next material catalysts. A resting order must have actual source/news
coverage and be pulled or repriced after a material change. FEC/candidate-list
access gaps are retained per case; a failure to find a new poll is not proof none
exists. A named-candidate replacement or new independent caucus decision cannot
be silently mapped across these different rule templates.

Each record contains both full ten-share ask walks with fees, book ages, exact
tokens, minimums, immediate exit and carry sensitivities. The55-day carry window
is a conservative working release assumption, not a deadline guarantee; normal
November/December certification fits January, but CA's long fallback can exceed
it. Maker ceiling `p-0.10` is a default uncertainty sensitivity before costs,
not evidence that its entire scenario range is above the quote. Tail K=5 and a
smaller flat reserve are not justified by these model tails. No stake is allocated
by these research reports, and no state election probability changes a held
position's canonical prior automatically.
