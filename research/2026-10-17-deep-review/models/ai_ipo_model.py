"""Primary scenario arithmetic, not a fitted/calibrated IPO forecast.

Inputs are dated October 17, 2026. No market price enters these probabilities.
Capitalization is trillions USD at the official first-day close, not proceeds,
opening price, current market cap, fully diluted value or the private mark.
"""
from statistics import NormalDist
from itertools import product
from pathlib import Path
import json, math

N = NormalDist()
SPACEX_FIRST_DAY = (7380196910 + 5695668265) * 160.95 / 1e12

REGIMES = [
    dict(name='Orderly offering with some valuation concession', weight=.45,
         completion=.95, offer_cap=1.75, first_day_multiple=1.12, log_sd=.23),
    dict(name='Weak demand, substantial price concession or delay', weight=.40,
         completion=.65, offer_cap=1.50, first_day_multiple=1.05, log_sd=.25),
    dict(name='Market, safety or governance interruption', weight=.15,
         completion=.15, offer_cap=1.25, first_day_multiple=1.00, log_sd=.35),
]

def calculate(regimes=REGIMES, rival_survival=.94, technical_trading=.01):
    ipo = 0.; beats_spacex = 0.; rows = []
    for row in regimes:
        close_median = row['offer_cap'] * row['first_day_multiple']
        tail = 1 - N.cdf(math.log(SPACEX_FIRST_DAY / close_median) / row['log_sd'])
        mass = row['weight'] * row['completion']
        ipo += mass
        beats_spacex += mass * tail
        rows.append(dict(row, close_cap_median=close_median,
                         conditional_exceeds_spacex=tail,
                         ipo_mass=mass, exceeds_spacex_mass=mass*tail))
    # One percent of remaining paths are nonstandard publicly tradable listing
    # routes that can satisfy case199 without satisfying case28's issuer-sale
    # or merger clauses. This is an explicit legal/wording uncertainty mass,
    # not an observed incidence or a proof of deterministic non-implication.
    listed = ipo + (1-ipo) * technical_trading
    return dict(anthropic_ipo=ipo, anthropic_listed_and_tradable=listed,
                anthropic_highest_ipo_cap=beats_spacex*rival_survival,
                spacex_base_first_day_cap_trillion=SPACEX_FIRST_DAY,
                rival_survival=rival_survival, regimes=rows)

def results():
    central = calculate()
    grid=[]
    # Common completion and capitalization errors are varied together. These
    # are sensitivity cases, never confidence intervals or guaranteed floors.
    for completion_shift, cap_scale, pop_scale, rival in product(
            [-.20,0,.10], [.80,1,1.20], [.90,1,1.15], [.80,.94,1]):
        regimes=[dict(r, completion=max(0,min(1,r['completion']+completion_shift)),
                      offer_cap=r['offer_cap']*cap_scale,
                      first_day_multiple=r['first_day_multiple']*pop_scale)
                 for r in REGIMES]
        grid.append(calculate(regimes,rival))
    return dict(author='primary', calibrated=False,
                inputs_asof='2026-10-17', central=central,
                primary_rounded_p_yes={'28':.71,'199':.71,'175':.05,'158':.18},
                openai_components={'executive_timing_reversal':.06,
                                   'timely_completion_given_reversal':.75,
                                   'other_eligibility_or_missed_event_mass':.005,
                                   'p_yes':.06*.75+.005},
                sensitivity_cases=len(grid),
                sensitivity_ranges={key:[min(r[key]for r in grid),max(r[key]for r in grid)]
                                    for key in ['anthropic_ipo','anthropic_listed_and_tradable',
                                                'anthropic_highest_ipo_cap']},
                caveat='Subjective regimes and price distributions. No measured tail, sample calibration, or universal current-listing absence proof.')

if __name__=='__main__':
    out=results()
    dest=Path(__file__).with_name('ai_ipo_results.json')
    dest.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
