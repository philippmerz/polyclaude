"""Primary, uncalibrated election-margin and common-error sensitivities.

No market prices are inputs. Do not interpret normal arithmetic as established
coverage or independent poll information. All margins are D minus R in points.
"""
import json
import math
from pathlib import Path


def phi(z):
    return .5 * math.erfc(-z / math.sqrt(2))


def combine(prior, prior_sd, poll, poll_sd):
    variance = 1 / (1/prior_sd**2 + 1/poll_sd**2)
    mu = variance * (prior/prior_sd**2 + poll/poll_sd**2)
    return mu, math.sqrt(variance), phi(mu/math.sqrt(variance))


CASES = {
    59: dict(name='Texas Senate', yes_party='R', prior=-4, prior_sd=10, poll=3.25,
             share_moe=4.9, common_sd=4, age_sd=2.5, poll_bias=0,
             surprise=.05, p_yes=.44, low=.12, high=.75),
    115: dict(name='Michigan Senate', yes_party='R', prior=4, prior_sd=8, poll=2.2,
              share_moe=3.8, common_sd=4, age_sd=3, poll_bias=0,
              surprise=.05, p_yes=.29, low=.08, high=.65),
    157: dict(name='California governor, named Hilton', yes_party='R', prior=20, prior_sd=10, poll=25,
              share_moe=2, common_sd=4, age_sd=3, poll_bias=0,
              surprise=.02, p_yes=.01, low=.001, high=.08),
    164: dict(name='Arizona governor', yes_party='D', prior=4, prior_sd=8, poll=6,
              share_moe=3.2, common_sd=4, age_sd=3, poll_bias=-1,
              surprise=.05, p_yes=.82, low=.45, high=.98),
    213: dict(name='Maine Senate', yes_party='R', prior=0, prior_sd=8, poll=2,
              share_moe=4.4, common_sd=4, age_sd=1.5, poll_bias=0,
              surprise=.05, p_yes=.40, low=.12, high=.80),
    220: dict(name='New Hampshire Senate', yes_party='D', prior=6, prior_sd=8, poll=8,
              share_moe=3.9, common_sd=4, age_sd=2, poll_bias=0,
              surprise=.05, p_yes=.91, low=.50, high=.99),
    234: dict(name='Michigan governor', yes_party='D', prior=4, prior_sd=8, poll=17,
              share_moe=4.4, common_sd=4, age_sd=3, poll_bias=0,
              surprise=.05, p_yes=.96, low=.65, high=.995),
}


def run():
    out = {'calibration': 'None; primary parameter and error-regime sensitivity, not a measured posterior.',
           'common_poll_error': 'Do not divide common error by sqrt(number of polls); conservative maximum share MoE used.',
           'cases': {}}
    for i,c in CASES.items():
        psd = math.sqrt((2*c['share_moe']/1.96)**2+c['common_sd']**2+c['age_sd']**2)
        mu, sd, pd = combine(c['prior'],c['prior_sd'],c['poll']+c['poll_bias'],psd)
        pd = (1-c['surprise'])*pd + c['surprise']*.5
        central = pd if c['yes_party']=='D' else 1-pd
        grid = []
        for prior_shift in [-4,0,4]:
            for poll_shift in [-4,0,4]:
                for extra_age_sd in [0,2]:
                    _,_,z=combine(c['prior']+prior_shift,c['prior_sd'],c['poll']+c['poll_bias']+poll_shift,
                                  math.hypot(psd,extra_age_sd))
                    z=(1-c['surprise'])*z+c['surprise']*.5
                    grid.append(z if c['yes_party']=='D' else 1-z)
        lo,hi=min(grid),max(grid)
        assert c['low'] <= min(lo,central,c['p_yes']) <= max(hi,central,c['p_yes']) <= c['high'], (i,lo,hi)
        out['cases'][str(i)]={'inputs':c,'effective_poll_margin_sd_pp':psd,
            'combined_mean_D_margin_pp':mu,'combined_sd_pp':sd,
            'unrounded_p_yes':central,'primary_p_yes':c['p_yes'],
            'scenario_range':[c['low'],c['high']], 'grid_min':lo,'grid_max':hi}
    out['cases']['178']={
        'name':'Idaho Senate','pvi_R_share_pp':18,'pvi_margin_transfer':.8,
        'national_D_margin_pp':8,'R_incumbency_margin_pp':2,'margin_sd_pp':9,
        'main_D_margin':8-2*.8*18-2,'unmodeled_symmetric_branch':.02,
        'primary_p_yes':.985,'scenario_range':[.90,.9995],
        'unrounded_p_yes':.98*phi((2*.8*18+2-8)/9)+.02*.5,
        'limitation':'No individual current district poll or complete final ballot captured; this is not an empirical tail estimate.'}
    return out


if __name__=='__main__':
    print(json.dumps(run(),indent=2))
