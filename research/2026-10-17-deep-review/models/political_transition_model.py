"""Explicit primary assumptions, not calibrated election probabilities.

No market prices or earlier model screens enter these calculations. Poll
mixtures retain disagreement rather than treating surveys as independent votes.
"""
import json
import math
import random
from pathlib import Path


def cdf(x):
    return (1 + math.erf(x / math.sqrt(2))) / 2


def band(mu, sd, lo, hi):
    return cdf((hi - mu) / sd) - cdf((lo - mu) / sd)


def brazil(w=.7, bias=0, common=4, late=2.5):
    mu = w * 2 + (1 - w) * 5.6 + bias
    sampling = math.hypot(w * 4 / 1.96, (1 - w) * 2 / 1.96)
    sd = math.sqrt(sampling**2 + common**2 + late**2)
    named = .95 * band(mu, sd, 8, 12) + .05 * band(mu, 10, 8, 12)
    reversed_band = .95 * band(mu, sd, -12, -8) + .05 * band(mu, 10, -12, -8)
    # One-percent interpretation branch applies only the shared absolute wording.
    return {'mu_margin_pp': mu, 'sd_margin_pp': sd,
            'p_named_band': named, 'p_reverse_band': reversed_band,
            'p_yes': .995 * (named + .01 * reversed_band)}


ISRAEL_POLLS = [
    {'Together': 13, 'Yashar': 23, 'Likud': 20, 'Democrats': 9,
     'Joint List': 8, 'Shas': 8, 'Otzma': 8, 'UTJ': 7,
     'Yisrael Beiteinu': 9, 'Religious Zionism': 6, 'Raam': 5, 'Reservists': 4},
    {'Together': 12, 'Yashar': 20, 'Likud': 18, 'Democrats': 9,
     'Joint List': 9, 'Yisrael Beiteinu': 9, 'Otzma': 8, 'UTJ': 8,
     'Shas': 7, 'Religious Zionism': 6, 'Raam': 6, 'Reservists': 4, 'Amcha': 4},
    {'Together': 13, 'Yashar': 21, 'Likud': 18, 'Democrats': 9,
     'Yisrael Beiteinu': 8, 'Otzma': 8, 'Joint List': 8, 'UTJ': 8,
     'Shas': 7, 'Religious Zionism': 6, 'Raam': 6, 'Amcha': 4, 'Reservists': 4},
]


def together_rank(sd, n=40000):
    rng = random.Random(20261017)
    by_poll = []
    for poll in ISRAEL_POLLS:
        names = list(poll)
        wins = 0
        for _ in range(n):
            shocks = {k: poll[k] + rng.gauss(0, sd) for k in names}
            # Continuous rankings proxy seats; subtracting their shared mean
            # shock would preserve all ranks. Official tie rules remain a gap.
            wins += max(shocks, key=shocks.get) == 'Together'
        by_poll.append(wins / n)
    main = sum(by_poll) / len(by_poll)
    return {'party_error_sd_seats': sd, 'n_per_poll': n,
            'conditional_by_poll': by_poll, 'main_poll_mixture': main,
            'p_yes': .90 * main + .075 * .005 + .005 * .70 + .02 * .25}


def calculate():
    br = brazil()
    br_grid = [brazil(w, bias, common, late)['p_yes']
               for w in [.5, .7, .9] for bias in [-2, 0, 2]
               for common in [3, 4, 6] for late in [1.5, 2.5, 4]]
    sr = [(11.5, 7, .50), (-2.7, 7, .35), (-9.2, 10, .15)]
    serbia = .97 * sum(w * cdf(mu / sd) for mu, sd, w in sr) + .03 * .5
    return {
        'calibrated': False,
        'brazil': {**br, 'sensitivity_min': min(br_grid), 'sensitivity_max': max(br_grid)},
        'together': together_rank(3.5),
        'together_sensitivities': [together_rank(s) for s in [2, 5, 7]],
        'netanyahu_next': .45 * .20 + .25 * .85 + .20 * .20 + .10 * .05,
        'niculescu_next': .80 * .95 + .15 * .40 + .05 * .40,
        'bolojan_out_oct31': .80 + .04 + .08,
        'serbia_largest': {'components_margin_sd_weight': sr, 'p_yes': serbia},
        # Use rounded primary largest-list .62 consistently in the PM tree.
        'vucic_next': .62 * .90 * .98 + .38 * .15 * .85,
        'probabilities_recorded_rounded': {
            '17': .12, '24': .35, '108': .84, '166': .92,
            '171': .62, '176': .03, '192': .60},
        'limits': ['Subjective mixture weights, not fitted frequencies.',
                   'Together simulation is continuous seat-rank sensitivity, not a legal allocation model.',
                   'Serbia dominant-pair margin is a proxy for list seat rank, not a full seat model.',
                   'Neither incumbent role nor a nomination is a sworn-in successor.'],
    }


if __name__ == '__main__':
    out = calculate()
    dest = Path(__file__).with_name('political_transition_results.json')
    dest.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out, indent=2))
