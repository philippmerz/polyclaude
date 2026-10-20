"""Offline finalization of case442; no account or financial writes."""
from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from deep_review_ledger import universe
from deep_review_economics import economics


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


u = universe()
f = u[442]
assert f['description'] == u[112]['description'] == u[352]['description']
qpath = ROOT / 'data/deep_review_20261017/0442_quote_0700.json'
q = json.loads(qpath.read_text())
c = q['cases'][0]
assert c['review_index'] == 442 and all(c['identity_checks'].values())
g = c['current_gamma']
assert g['description'] == f['description']
assert g['active'] and not g['closed'] and g['acceptingOrders']

manifest = json.loads((ROOT / 'logs/deep_review_20261017/case0442_quote_0700/capture_manifest.json').read_text())
verified = []
for item in manifest['receipts']:
    receipt = json.loads((ROOT / item['receipt_path']).read_text())
    body = (ROOT / item['gzip_path']).read_bytes()
    raw = gzip.decompress(body)
    assert hashlib.sha256(body).hexdigest() == item['gzip_sha256'] == receipt['gzip_sha256']
    assert hashlib.sha256(raw).hexdigest() == item['raw_sha256'] == receipt['raw_sha256']
    assert item['received_utc'] == receipt['received_utc']
    assert item['status_code'] == receipt['status_code'] == 200
    verified.append({'request_id': item['request_id'], 'raw_sha256': item['raw_sha256'],
                     'received_utc': item['received_utc']})

facts = json.loads((ROOT / 'data/deep_review_20261017/work/0442_facts_0500.json').read_text())
for item in facts['captures']['items']:
    rp = ROOT / item['receipt']
    receipt = json.loads(rp.read_text())
    body = (rp.parent / receipt['body_path']).read_bytes()
    raw = gzip.decompress(body)
    assert hashlib.sha256(body).hexdigest() == item['gzip_sha256'] == receipt['gzip_sha256']
    assert hashlib.sha256(raw).hexdigest() == item['raw_sha256'] == receipt['raw_sha256']
    assert receipt['response_status'] == 200
    verified.append({'request_id': item['name'], 'raw_sha256': item['raw_sha256'],
                     'received_utc': item['received_utc']})

source_path = ROOT / 'logs/tick060240_sources/openrouter.receipt.json'
sr = json.loads(source_path.read_text())
sb = (source_path.parent / sr['body_path']).read_bytes()
raw = gzip.decompress(sb)
assert hashlib.sha256(sb).hexdigest() == sr['gzip_sha256']
assert hashlib.sha256(raw).hexdigest() == sr['raw_sha256'] == '7fa78f5b31b94fdbf9a50fa4de596cf92c8684a121ab5d78932748b01976ea1e'
source = json.loads(raw)
rows = source['data']['data']
totals = {x['x']: sum(x['ys'].values()) / 1e12 for x in rows}
assert totals['2026-10-12'] == 164.043985914931
targets = ('2026-10-26', '2026-11-02', '2026-11-09', '2026-11-16')
assert not any(x in totals for x in targets)

e = economics(442, .44, str(qpath.relative_to(ROOT)), reserve=.20, days=39, quantity=5)
e['maker_and_portfolio'] = {
    'maker_touch': {'Yes': {'price': .30, 'quantity': 5, 'cost': 1.50, 'central_profit': .70, 'selected_profit': -.30},
                    'No': {'price': .68, 'quantity': 5, 'cost': 3.40, 'central_profit': -.60, 'selected_profit': -1.60}},
    'selected_fair_before_carry': {'Yes': .24, 'No': .36},
    'remote_bid': 'A23cYESmaker or35cNOmaker would clear selected unconditional carry narrowly, but sit below the29/67c current bids. No measured probability conditional on such a fill; do not place a blind order.',
    'joint_state_order': ['total<725', '725<=total<775', 'total>=775'],
    'rounded_state_probability_illustration': [.44, .12, .44],
    'existing_112_NO5_payout': [5, 0, 5],
    'existing_112_NO5_plus_new_442_YES5': [5, 0, 10],
    'existing_112_NO5_plus_new_442_NO5': [10, 5, 5],
    'limits': 'Conditional ordinary settlement only; source/venue/oracle failure can invalidate the floor. Held112prior unchanged. Kimi shares AI/source/venue exposures; no independence or hedge credit.',
    'carry': '39day constant3.2035%APY sensitivity approximates Nov27ETfallback; normalfirstNov23display roughly34days. Adjudication may delay payout. Funding/gas/monitoring are not free.',
    'known_alternative': 'Preserve cash/Aave and original small gated political bids; no new candidate passes selected conditional economics. Latest account06:22 is dated context, never a current execution certificate.'
}
save(ROOT / 'data/deep_review_20261017/work/0442_economics_0703.json', e)

report = '''# 442 · OpenRouter ≥775T, Oct26–Nov22

**Valued YES44% / NO56%; no entry.** Broad YES5–95% is judgmental uncertainty, not a calibrated interval. The20pp entry reserve gives selected YES24%/NO36%. YES has positive central economics; it fails the selected model and fill-risk case.

Full rule: sum the displayed Top Models weekly Totals for Oct26, Nov2, Nov9 and Nov16, Monday00:00UTC–Sunday23:59UTC. Each week updates until the following week first appears. Freeze all four when Nov23 first appears; if absent by Nov27 23:59ET, use that time's display. Chart rounding governs; exact775 goes YES. Operational endNov23 04:59Z does not replace the fallback or establish finality. Full descriptions are byte-identical to held112[725,775) and352<625; questions define different outcomes.

Verified06:24 source:53 points, completed Oct5=171.842502T and Oct12=164.043986T; Oct19 partial30.038851T is context only. All four target weeks are absent. The earlier browser/JS investigation establishes a separately formatted Total and a separate Weekly Pace overlay; do not sum rounded model labels, treat pace as actual usage, or assign cachedAt an undisclosed measurement cutoff. First-display history/revisions remain unknown. Dataset docs describe prompt+completion/top50+Other, but sampled category/language outputs are not substitutes for this exact resolving chart.

Pre-own-quote primary model reproduces200,000 earlier completed-Oct12-anchor paths. Five judgmental growth regimes have weights36/28/8/8/20% and weekly log drift3.5/8/20/−15/0%, volatility6.5/9.5/10/15/5%, innovation correlation.25. Simulate Oct19 plus the four target weeks, sum the latter, add unmeasured aggregate rounding/revision noise. The ≥775 frequency43.5135% rounds to44%; branch frequencies39.0/70.6/99.0/2.3/7.4% show regime dependence. Monte Carlo precision is not forecast calibration.

Competing cases matter: flat164.044T produces656.176T, well below775; approximately4.83% weekly growth reaches775 and5% gives779.523T. Summer/September adoption and release growth support renewed expansion; recent stagnation/competition/free-model mix support plateau. The completed anchor already includes the latest4.54% decline; it is not another new penalty. Future releases, usage, vendor mix and source changes remain load-bearing. Reserve20pp uses10growth/model+5display/vintage/source+5conditional-fill uncertainty, consistent with this source family; it is not the broad-low endpoint or a measured confidence bound. No short-horizon tail exemption applies.

| Side /5shares | Taker cost | Central profit | Selected profit | Maker planning |
|---|---:|---:|---:|---|
| YES |1.69422|+.50578|−.49422|30c costs1.50;+.70/−.30 |
| NO |3.59119|−.79119|−1.79119|68c costs3.40;−.60/−1.60 |

07:00:46 capture: YES29/33c, NO67/71c;5share minimum,1c tick,4%×p(1−p) taker fee. Both book ages22.42s at receipt and exact Gamma/token/fee bindings pass; this is a dated research capture, not a present entry gate.39day constant3.2035% Aave sensitivity raises taker break-even to33.999%/72.066%; ordinary firstNov23 display is roughly34days, fallback roughly39, with adjudication delay possible. Gas/funding and operations are additional costs. Takers also need an independently justified urgency exception.

A23cYES or35cNO remote maker bid would sit below current bids and have small unconditional selected margin before additional costs. Such fills can be selected by a usage or source shock; no conditional-fill model supports them. Do not equate an attractive limit with a justified order.

Joint risk with held112NO5: below725/middle725–<775/upper≥775 payouts are5/0/5. Adding442YES5 gives5/0/10: both lose in the middle and both win in the upper, so it is not a hedge. Adding442NO5 gives10/5/5 only under matching ordinary settlement; at3.59119 new cost its central incremental payout2.80 is inferior. A nominal floor does not justify buying negative expectation, and source/venue/oracle failure remains common. Kimi also shares AI/venue exposure; no independence credit. Coherent rounded44/12/44% states illustrate dependence without changing the held11212%YES prior.

Latest dated account06:22:195.90including5.81gas,190.09tradingmid/185.89indicative depth; three original unfilled bids commit6.50. No442 holding. Cash/Aave and the existing small gated bids are preferable to these selected economics. This research neither refreshes collateral nor changes priors/orders/funding/watchers. Reopen on an actual completed usage week, primary release/source change, or independently underwritten fill-conditional price. Before any action recheck exact rule/identity, lawful eligibility, source, account, commitments, fees, depth, joint risk and the vetted writer.

[Sources](../../../data/deep_review_20261017/work/0442_facts_0500.json) · [Prequote model](../models/0442_primary_0658.json) · [Display semantics](../../../data/deep_review_20261017/openrouter_chart_display_semantics_1100.json) · [Economics](../../../data/deep_review_20261017/work/0442_economics_0703.json) · [Verification](../../../data/deep_review_20261017/work/0442_verification_0705.json).
'''

record = {
    'review_index': 442, 'market_id': f['id'], 'condition_id': f['conditionId'],
    'criteria_sha256': f['criteria_sha256'],
    'token_ids': json.loads(f['clobTokenIds']) if isinstance(f['clobTokenIds'], str) else f['clobTokenIds'],
    'status': 'valued',
    'literal_analysis': 'Exactfourdisplayedweeks/firstNov23/fallbackNov27ET/rounding/higherboundary; full descriptions match112and352, different outcomes.',
    'evidence': [
        {'url': 'https://openrouter.ai/api/frontend/v1/rankings/model-rankings-chart',
         'observed_utc': sr['received_utc'], 'finding': '53points/Oct12completed164.043985914931T, four targetweeksabsent; partial/pace notsettlement.'},
        {'url': 'https://openrouter.ai/rankings#top-models', 'observed_utc': '2026-10-18T11:06:24.407Z',
         'finding': 'Savedbrowser/JSshowseparatelyformattedTotal/separateWeeklyPace;firstdisplayhistoryunknown.'},
        {'url': 'https://openrouter.ai/docs/api/api-reference/datasets/get-rankings-daily',
         'observed_utc': '2026-10-20T04:59:19.747810Z',
         'finding': 'Prompt+completion/top50+Other;sampledcategory/languagecannotreplace exactchart.'}
    ],
    'forecast': {'p_yes': .44, 'low': .05, 'high': .95, 'actual_entry_reserve_pp': 20,
                 'method': 'Primary pre-own-quote judgment using reproduced200k completed-Oct12-anchor regime paths.',
                 'reasoning': 'Flat656T vs5%growth780T; regimeweights uncalibrated, ≥775pathfrequency43.5135%rounded44. Broaduncertainty5–95;20ppactualreserve.'},
    'economics': e, 'verdict': 'NO_ENTRY: YESpositivecentralbutfailsselected/maker;NOnegativecentral. Remoteconditionalfillunmeasured; no blindbid.',
    'reopen_condition': 'Actualcompletedusageweek/primaryrelease/sourcechange or underwrittenconditionalfreshprice;alllivegatesbeforeaction.',
    'report_markdown': report
}
proof = {
    'schema': 'case442.primary_verification.v1', 'reviewed_utc': datetime.now(timezone.utc).isoformat(),
    'description_sha256_all_112_352_442': hashlib.sha256(f['description'].encode()).hexdigest(),
    'all_frozen_identity_checks': c['identity_checks'], 'fresh_capture_pairs': verified,
    'source_raw_sha256': sr['raw_sha256'], 'source_target_weeks_absent': True,
    'quote_sha256': digest(qpath),
    'model_sha256': digest(ROOT / 'research/2026-10-17-deep-review/models/0442_primary_0658.json'),
    'replay_code_sha256': digest(ROOT / 'data/deep_review_20261017/work/0442_primary_replay_0658.py'),
    'count': '7casecapturepairs plus prior06:24source verified; all exact identity/economicsbindings pass.',
    'limit': 'No financialwrites/currentaccount/CTF/conditionalfillcertificate. No own442quotes before06:56model; otherfamilypricesknown.'
}
save(ROOT / 'data/deep_review_20261017/work/0442_verification_0705.json', proof)
save(ROOT / 'data/deep_review_20261017/work/0442_final_0705.json', record)
print(json.dumps({'final': 'data/deep_review_20261017/work/0442_final_0705.json', 'report_bytes': len(report.encode()),
                  'verified_pairs': len(verified) + 1, 'p_yes': .44, 'actual_reserve_pp': 20}))
