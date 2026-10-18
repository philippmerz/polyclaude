"""Primary county sensitivity model, not fitted/backtested or execution authority.

An explicit statewide normal margin plus historical county-relative lean and
additional local uncertainty. No venue price/probability enters the model.
"""
from __future__ import annotations
import math
from statistics import NormalDist


def project(state, lean_pp, *, local_sd=5.0, local_shift=0.0,
            national_sd=3.0, other_probability=.01):
    # Preserve the source model's shared national, regional and polling errors.
    state_var = (national_sd**2 + 1.0 + state['poll_weight']**2
                 + state['idiosyncratic_sd_pp']**2)
    sd = math.sqrt(state_var + local_sd**2)
    center = state['center_pp'] + lean_pp + local_shift
    major_d = NormalDist(center, sd).cdf(0.) * -1. + 1.
    d = (1.-other_probability) * major_d
    r = (1.-other_probability) * (1.-major_d)
    assert 0 <= d <= 1 and 0 <= r <= 1
    assert abs(d+r+other_probability-1.) < 1e-12
    return {'mean_D_minus_R_pp':center, 'margin_sd_pp':sd,
            'D_winner':d, 'R_winner':r, 'other_or_fallback':other_probability,
            'local_sd_pp':local_sd, 'local_shift_pp':local_shift,
            'national_sd_pp':national_sd}


def sensitivity(state_scenarios, leans, central_lean):
    out = {'central':project(state_scenarios['central'], central_lean)}
    for name, s in state_scenarios.items():
        if name != 'central': out['state_'+name] = project(s, central_lean,
                    national_sd=5. if name=='wider_common_error' else 3.)
    for name, lean in leans.items():
        out['historical_'+name] = project(state_scenarios['central'], lean)
    for label, change in {'local_D_minus5':-5.,'local_D_plus5':5.}.items():
        out[label] = project(state_scenarios['central'],central_lean,local_shift=change)
    out['local_sd3'] = project(state_scenarios['central'],central_lean,local_sd=3.)
    out['local_sd8'] = project(state_scenarios['central'],central_lean,local_sd=8.)
    out['stacked_adverse_D'] = project(state_scenarios['stacked_adverse_D'],central_lean,local_shift=-5.)
    out['stacked_favorable_D'] = project(state_scenarios['stacked_favorable_D'],central_lean,local_shift=5.)
    return out
