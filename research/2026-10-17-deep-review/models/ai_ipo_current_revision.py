"""Dated primary revision; preserve the earlier18% scenario model unchanged."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).parent))
import ai_ipo_model as old

regimes=[dict(r,weight=r['weight']*.85)for r in old.REGIMES]
regimes.append(dict(name='Stronger first-day demand scenario',weight=.15,
                    completion=.71,offer_cap=1.80,first_day_multiple=2.35/1.80,log_sd=.20))
# Do not lower YES for an unmeasured global-rival survival assumption when
# underwriting a NO purchase. Additional rivals can only help this NO.
z=old.calculate(regimes,rival_survival=1.0)
out=dict(author='primary',calibrated=False,created='2026-10-17',
    previous_p_yes=.18,current_p_yes=.24,current_p_no=.76,scenario_range_yes=[.01,.80],
    calculation=z,
    source_price_status='Yahoo secondary daily unadjusted close corroborates160.95; Nasdaq narrative~2.1T agrees, exact exchange table unavailable. Literal reliable-source fallback accepted by primary.',
    reason='New contrary investor outlook receives15% scenario weight; other regimes retain85%. Removing favorable but unmeasured rival-survival discount gives a conservative NO-entry value.',
    prior_timing_cases_28_199='Rounded71% unchanged; new branch has71% completion so total completion remains71%.',
    action='No order/prior/reservation yet; small passive candidate requires fresh gates and monitoring.')
Path(__file__).with_name('ai_ipo_current_revision.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'p_joint_yes_before_rounding':z['anthropic_highest_ipo_cap'],
                  'completion':z['anthropic_ipo'],'current_p_yes':.24,'current_p_no':.76}))
