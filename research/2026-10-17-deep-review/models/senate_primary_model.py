"""Primary-authored explicit sensitivity, not a fitted election forecaster.

Inputs are original-source facts plus separately labelled subjective assumptions.
No venue probabilities or prices enter this model. Output is research only.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np

HERE = Path(__file__).resolve().parent


def simulate(inputs, *, draws=60000, seed=17102259, generic=8., national_sd=3.,
             poll_bias=-1.5, prior_sd=7., personal_retention=.75,
             ne_d=.35, ne_r=.10, protem_d=.45, protem_other=.10,
             all_independent_d=None, house_loading=.70,
             id_regime_weights=None, mt_consolidation_override=None):
    rng = np.random.default_rng(seed)
    common = rng.normal(size=draws)
    regions = {r: rng.normal(size=draws) for r in sorted({x['region'] for x in inputs['seats']})}
    assert inputs['fixed_nonballot'] == {'D_aligned': 34, 'R': 31}
    d = np.full(draws, inputs['fixed_nonballot']['D_aligned'], dtype=np.int16)
    r = np.full(draws, inputs['fixed_nonballot']['R'], dtype=np.int16)
    ind = np.zeros(draws, dtype=np.int16)
    bias_draw = rng.normal(size=draws)
    state_outputs = []
    assert len(inputs['seats']) == 35
    assert len({x['seat'] for x in inputs['seats']}) == 35
    assert sum(x['defending_party'] == 'D' for x in inputs['seats']) == 13
    assert sum(x['kind'] == 'regular' for x in inputs['seats']) == 33
    assert {x['seat'] for x in inputs['seats'] if x['kind'] == 'special'} == {'OH', 'FL'}

    def independent_credit(win, state):
        nonlocal d, r, ind
        if state['seat'] == 'NE':
            pd, pr = ne_d, ne_r
        else:
            pd = state['independent_caucus']['D']
            pr = state['independent_caucus']['R']
        if all_independent_d is not None:
            pd, pr = all_independent_d, 0.
        assert 0 <= pd <= 1 and 0 <= pr <= 1 and pd + pr <= 1
        u = rng.uniform(size=draws)
        d += win & (u < pd)
        r += win & (u >= pd) & (u < pd + pr)
        ind += win & (u >= pd + pr)

    for state in inputs['seats']:
        if state.get('direct_poll_regimes'):
            # Conflicting instruments remain alternative regimes; no source is
            # silently discarded or averaged into a spuriously precise poll.
            regimes = state['direct_poll_regimes']
            assert abs(sum(x['weight'] for x in regimes) - 1.) < 1e-9
            weights = ([x['weight'] for x in regimes] if state['seat'] != 'ID' or
                       id_regime_weights is None else id_regime_weights)
            which = rng.choice(len(regimes), draws, p=weights)
            means = np.array([x['margin_pp'] for x in regimes])[which]
            scales = np.array([x['residual_sd_pp'] for x in regimes])[which]
            loading = state.get('national_loading', .5)
            bias_scale = state.get('poll_bias_scale', .5)
            margin = (means + bias_scale * poll_bias + loading * .5 * (generic - 8.)
                      + loading * national_sd * common + regions[state['region']]
                      + bias_scale * bias_draw + rng.normal(size=draws) * scales)
            win = margin > 0
            r += ~win
            independent_credit(win, state)
            state_outputs.append({'seat': state['seat'], 'model': 'explicit_poll_regime_mixture',
                                  'regimes': regimes, 'challenger_party': 'I',
                                  'non_republican_win_probability': float(win.mean())})
            continue
        if state.get('field_model') == 'montana_multicandidate':
            # Relative margin/utility approximation, not a forecast of vote shares.
            # Primary local report has R45.1/I26.1/D18.9, unknown remainder.
            # A declared 10% consolidation regime is NOT empirical frequency.
            tail_share = (state.get('consolidation_regime', .10) if mt_consolidation_override is None
                          else mt_consolidation_override)
            tail = rng.uniform(size=draws) < tail_share
            common_r = rng.normal(0., 3., draws)
            opposition = national_sd * common + regions[state['region']]
            im = (np.where(tail, -4., -17.) + .5 * opposition + common_r
                  + rng.normal(0., 8., draws))
            dm = (np.where(tail, -40., -29.) + opposition + common_r
                  + rng.normal(0., 8.5, draws))
            lm = -40. + .25 * opposition + common_r + rng.normal(0., 5., draws)
            winner = np.argmax(np.stack([np.zeros(draws), im, dm, lm]), axis=0)
            r += winner == 0
            d += winner == 2
            independent_credit(winner == 1, state)
            ind += winner == 3  # Libertarian is not an independent-caucus credit.
            state_outputs.append({'seat': state['seat'], 'model': state['field_model'],
                                  'non_republican_win_probability': float((winner != 0).mean()),
                                  'candidate_probabilities': {
                                      k: float((winner == j).mean()) for j, k in
                                      enumerate(['Alme_R', 'Bodnar_I', 'Bankhead_D', 'Austin_L'])}})
            continue
        prior = (state['pres2024_d_minus_r_allvote_pp']
                 + .80 * (generic - inputs['national_pres2024_d_minus_r_allvote_pp'])
                 + state.get('candidate_adjustment_pp', 0.)
                 + personal_retention * state.get('observed_2024_personal_overperformance_pp', 0.))
        polls = state.get('polls', [])
        if polls:
            precisions = []
            for poll in polls:
                # A candidate-share MOE is not a D-R margin MOE: conservatively double it.
                var = ((2. * poll['share_moe_pp'] / 1.96) ** 2
                       + poll.get('source_extra_sd_pp', 2.) ** 2
                       + (.08 * poll['age_days']) ** 2)
                precisions.append(1. / var)
            total_precision = sum(precisions)
            poll_margin = sum(q * (p['margin_pp'] + p.get('sponsor_adjustment_pp', 0.))
                              for p, q in zip(polls, precisions)) / total_precision
            # Shared pollster/method uncertainty is not removed by two releases.
            poll_var = 1. / total_precision + 1.5 ** 2
            weight = prior_sd ** 2 / (prior_sd ** 2 + poll_var)
            weight = min(weight, state.get('maximum_poll_weight', 1.))
            center = (1. - weight) * prior + weight * (poll_margin + poll_bias)
            # Keep uncertainty implied by capping weak-source polling weight.
            posterior_var = ((1. - weight) ** 2 * prior_sd ** 2
                             + weight ** 2 * poll_var)
        else:
            weight, poll_margin, center, posterior_var = 0., None, prior, prior_sd ** 2
        residual_sd = math.sqrt(posterior_var + 2. ** 2)
        margin = (center + national_sd * common + regions[state['region']]
                  + weight * bias_draw
                  + rng.normal(0., residual_sd, draws))
        state_outputs.append({'seat': state['seat'], 'prior_center_pp': prior,
                              'poll_center_before_cycle_bias_pp': poll_margin,
                              'poll_weight': weight, 'center_pp': center,
                              'idiosyncratic_sd_pp': residual_sd,
                              'challenger_party': state.get('challenger_party', 'D')})
        win = margin > 0
        state_outputs[-1]['non_republican_win_probability'] = float(win.mean())
        if state['seat'] == 'NE' or state.get('challenger_party') == 'I':
            r += ~win
            independent_credit(win, state)
        else:
            d += win
            r += ~win
    assert np.all(d + r + ind == 100)
    d_control = (d >= 51)
    r_control = (r >= 51) | ((r == 50) & ~d_control)
    ambiguous = ~d_control & ~r_control
    assert 0 <= protem_d <= 1 and 0 <= protem_other <= 1 and protem_d + protem_other <= 1
    # More than one unassigned independent can leave both parties below 50.
    # First-ProTem party is endogenous and uncertain; expose all three branches.
    fallback = rng.uniform(size=draws)
    d_control |= ambiguous & (fallback < protem_d)
    other_control = ambiguous & (fallback >= protem_d) & (fallback < protem_d + protem_other)
    r_control = ~d_control & ~other_control
    threshold = NormalDist().inv_cdf(.20)  # preserves case10's 80% House marginal in expectation
    h_conditional = np.array([NormalDist().cdf((house_loading * z - threshold)
                                              / math.sqrt(1. - house_loading ** 2))
                              for z in common])
    joint = {
        'D_senate_D_house': float((d_control * h_conditional).mean()),
        'D_senate_R_house': float((d_control * (1. - h_conditional)).mean()),
        'R_senate_D_house': float((r_control * h_conditional).mean()),
        'R_senate_R_house': float((r_control * (1. - h_conditional)).mean()),
        'other_senate_D_house': float((other_control * h_conditional).mean()),
        'other_senate_R_house': float((other_control * (1. - h_conditional)).mean()),
    }
    assert abs(sum(joint.values()) - 1.) < 1e-12
    return {
        'draws': draws, 'seed': seed,
        'assumptions': {'generic_d_margin_pp': generic, 'national_sd_pp': national_sd,
                        'poll_bias_mean_pp': poll_bias, 'structural_prior_sd_pp': prior_sd,
                        'personal_retention': personal_retention, 'NE_caucus_D': ne_d,
                        'NE_caucus_R': ne_r, 'no_pledge_protem_D': protem_d,
                        'no_pledge_protem_other': protem_other,
                        'all_independent_D_override': all_independent_d,
                        'ID_source_regime_weights_override': id_regime_weights,
                        'MT_consolidation_override': mt_consolidation_override,
                        'house_loading': house_loading},
        'D_senate_control': float(d_control.mean()), 'R_senate_control': float(r_control.mean()),
        'other_senate_control': float(other_control.mean()),
        'D_house_marginal': float(h_conditional.mean()),
        'no_pledge_control_fallback_mass': float(ambiguous.mean()),
        'D_aligned_seats_mean': float(d.mean()),
        'unassigned_seats_mean': float(ind.mean()),
        'D_aligned_seats_10_50_90': [float(x) for x in np.quantile(d, [.1, .5, .9])],
        'joint': joint, 'seat_outputs': state_outputs,
    }


def main():
    inputs = json.loads((HERE / 'senate_primary_inputs.json').read_text())
    variations = {
        'central': {}, 'no_mean_poll_bias': {'poll_bias': 0.},
        'adverse_mean_poll_bias': {'poll_bias': -3.},
        'generic_D6': {'generic': 6.}, 'generic_D10': {'generic': 10.},
        'stronger_structural_prior': {'prior_sd': 5.},
        'weaker_structural_prior': {'prior_sd': 10.},
        'wider_common_error': {'national_sd': 5.},
        'NE_no_D_credit': {'ne_d': 0.}, 'NE_all_D_credit': {'ne_d': 1., 'ne_r': 0.},
        'no_new_independent_D_credit': {'all_independent_d': 0.},
        'all_new_independents_D_credit': {'all_independent_d': 1.},
        'all_ambiguous_protem_R': {'protem_d': 0., 'protem_other': 0.},
        'all_ambiguous_protem_D': {'protem_d': 1., 'protem_other': 0.},
        'ID_ATR_only': {'id_regime_weights': [1., 0.]},
        'ID_Peak_attribution_only': {'id_regime_weights': [0., 1.]},
        'MT_no_consolidation': {'mt_consolidation_override': 0.},
        'MT_quarter_consolidation': {'mt_consolidation_override': .25},
        'house_lower_correlation': {'house_loading': .35},
        'house_higher_correlation': {'house_loading': .85},
        'no_personal_retention': {'personal_retention': 0.},
        'full_personal_retention': {'personal_retention': 1.},
        'stacked_adverse_D': {'generic': 6., 'poll_bias': -3., 'personal_retention': 0.,
                              'all_independent_d': 0., 'protem_d': 0., 'protem_other': 0.},
        'stacked_favorable_D': {'generic': 10., 'poll_bias': 0., 'personal_retention': 1.,
                                'all_independent_d': 1., 'protem_d': 1., 'protem_other': 0.},
    }
    result = {'model_status': inputs.get('primary_review_status', 'DRAFT; not fitted/backtested or calibrated'),
              'generated_utc': datetime.now(timezone.utc).isoformat(),
              'source': str(HERE / 'senate_primary_inputs.json'),
              'scenarios': {name: simulate(inputs, **kwargs) for name, kwargs in variations.items()}}
    dest = HERE / 'senate_primary_results.json'
    dest.write_text(json.dumps(result, indent=2) + '\n')
    for name, r in result['scenarios'].items():
        print(name, round(r['D_senate_control'], 4),
              {k: round(v, 4) for k, v in r['joint'].items()})


if __name__ == '__main__':
    main()
