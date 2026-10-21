"""Exact Michigan marginal of the saved Gaussian model; offline, no prices.

Assumptions remain uncalibrated. This is a management review, not a new case.
"""
import copy
import hashlib
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'research/2026-10-17-deep-review/models/senate_IA_revision_0059_inputs.json'
PREVIOUS = ROOT / 'data/deep_review_20261017/work/tick012937_mi_rederived_0154.json'
OUTPUT = ROOT / 'data/deep_review_20261017/work/tick003800_mi_rederived.json'


def marginal(polls, state, national_pres, generic=8., bias=-1.5, national_sd=3.):
    precisions = [1 / ((2*p['share_moe_pp']/1.96)**2
                       + p['source_extra_sd_pp']**2 + (.08*p['age_days'])**2)
                  for p in polls]
    total = sum(precisions)
    poll_center = sum(q*(p['margin_pp']+p.get('sponsor_adjustment_pp', 0.))
                      for p, q in zip(polls, precisions)) / total
    poll_var = 1/total + 1.5**2
    weight = min(7.**2 / (7.**2+poll_var), state.get('maximum_poll_weight', 1.))
    prior = (state['pres2024_d_minus_r_allvote_pp']
             + .8*(generic-national_pres) + state['candidate_adjustment_pp'])
    center = (1-weight)*prior + weight*(poll_center+bias)
    variance = (1-weight)**2*7.**2 + weight**2*poll_var + 2.**2 + national_sd**2 + 1.**2 + weight**2
    sd = math.sqrt(variance)
    return dict(p_D=NormalDist().cdf(center/sd), center_pp=center,
                total_margin_sd_pp=sd, poll_center_pp=poll_center, poll_weight=weight)


if __name__ == '__main__':
    inputs = json.loads(SOURCE.read_text())
    state = next(x for x in inputs['seats'] if x['seat'] == 'MI')
    previous = json.loads(PREVIOUS.read_text())
    national = inputs['national_pres2024_d_minus_r_allvote_pp']
    reproduced = marginal(previous['polls'], state, national)
    assert abs(reproduced['p_D']-previous['scenarios']['central']['p_D']) < 1e-12
    polls = copy.deepcopy(previous['polls'])
    field_ends = ['2026-10-04', '2026-10-14', '2026-10-10']
    for poll, field_end in zip(polls, field_ends):
        poll['age_days'] = (date(2026, 10, 21)-date.fromisoformat(field_end)).days
    scenarios = {
        'central_G8_biasMinus1_5': {}, 'G8_bias0': {'bias': 0.},
        'G8_biasMinus3': {'bias': -3.}, 'G6_biasMinus3': {'generic': 6., 'bias': -3.},
        'G10_bias0': {'generic': 10., 'bias': 0.},
        'G12_biasMinus1_5': {'generic': 12.},
        'G12_bias0': {'generic': 12., 'bias': 0.},
        'G8_wideCommon5': {'national_sd': 5.},
    }
    result = dict(schema='primary_MI_daily_rederivation.v2',
                  computed_utc=datetime.now(timezone.utc).isoformat(), index=1838,
                  method='Exact analytic marginal of saved Gaussian model; reproduce Oct20 then recompute Oct21 ages17/7/11. No quote or venue probability in inputs.',
                  input_file=str(SOURCE.relative_to(ROOT)),
                  input_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  model_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  reproduced_Oct20=reproduced, polls=polls,
                  scenarios={name:marginal(polls, state, national, **kw) for name, kw in scenarios.items()},
                  constants=dict(prior_sd_pp=7, national_sd_pp=3, regional_sd_pp=1,
                                 shared_poll_bias_sd_pp=1, future_residual_sd_pp=2,
                                 generic_D_margin_pp=8, mean_poll_bias_pp=-1.5),
                  limitations=['Generic D8 was judgment from original Fox certain-vote D6 and YouGov loose/strict D8/D11, not a trained aggregate.',
                               'Ipsos Oct16-19 national RV D47/R35 is newer D+12, not Michigan LV data or an independent state likelihood; explicitly test G12.',
                               'InsiderAdvantage Michigan mode, full instrument/sponsor/overlap remain unknown; extra SD4.5 retained.',
                               'Ordinary D/R model omits explicit minor-party winner probability; NO means any non-D winner. Broad range retains specification risk.',
                               'Assumed covariance, candidate adjustment and bias are unfitted; scenarios are not confidence intervals.'])
    OUTPUT.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'result':str(OUTPUT.relative_to(ROOT)), 'sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
                      'scenarios':{k:v['p_D'] for k,v in result['scenarios'].items()}}))
