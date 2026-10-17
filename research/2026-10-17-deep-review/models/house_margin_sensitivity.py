"""Pure primary House margin sensitivities; no network, account, or trade path."""
import json,math
from pathlib import Path
Phi=lambda z:.5*math.erfc(-z/math.sqrt(2))
def combine(mu,sd,poll,psd):
 v=1/(1/sd**2+1/psd**2);m=v*(mu/sd**2+poll/psd**2)
 return {'mean_D_margin_pp':m,'sd_margin_pp':math.sqrt(v),'p_D_win':Phi(m/math.sqrt(v))}
cases={81:{'district':'NC11','pvi_D_share_pp':-5,'incumbency_D_margin_pp':0,'cash_context_D_adjustment_pp':1.5,'poll_D_margin_pp':3,'poll_margin_sampling_sd_pp':2*4.3/1.96,'poll_non_sampling_sd_pp':3,'age_turnout_sd_pp':2.5},116:{'district':'OH07','pvi_D_share_pp':-5,'incumbency_D_margin_pp':-2,'cash_context_D_adjustment_pp':1,'poll_D_margin_pp':8,'poll_margin_sampling_sd_pp':2*4.8/1.96,'poll_non_sampling_sd_pp':3,'age_turnout_sd_pp':5}}
out={'model':'Physical election-margin sensitivity, uncalibrated, primary coefficients. CookPVI is share relative to national baseline, so multiply by2 before comparing two-party margins.','assumptions':{'generic_D_margin_pp':8,'national_error_sd_pp':3,'local_error_sd_pp':6,'pvi_margin_transfer_coefficient':.8,'fundraising_adjustment':'Subjective context at most1.5pp, not fitted causal effect; outside spending/loans not zero.','poll_covariance':'One named poll percase used; other same-period partisan polls not independent trials.'},'cases':{}}
for i,c in cases.items():
 mu=8+2*.8*c['pvi_D_share_pp']+c['incumbency_D_margin_pp']+c['cash_context_D_adjustment_pp'];sd=math.sqrt(3**2+6**2);psd=math.sqrt(c['poll_margin_sampling_sd_pp']**2+c['poll_non_sampling_sd_pp']**2+c['age_turnout_sd_pp']**2)
 r={'inputs':c,'prior_mean_D_margin_pp':mu,'prior_sd_margin_pp':sd,'effective_poll_sd_pp':psd,'central':combine(mu,sd,c['poll_D_margin_pp'],psd),'sensitivity_grid':[]}
 for national in [4,8,12]:
  for beta in [.6,.8,1.]:
   for systematic in [-3,0,3]:
    m=national+2*beta*c['pvi_D_share_pp']+c['incumbency_D_margin_pp']+c['cash_context_D_adjustment_pp'];z=combine(m,sd,c['poll_D_margin_pp']+systematic,psd)
    r['sensitivity_grid'].append({'national_D_margin':national,'pvi_beta':beta,'poll_bias_D_margin':systematic,**z})
 out['cases'][str(i)]=r
 print(i,r['central'],min(x['p_D_win']for x in r['sensitivity_grid']),max(x['p_D_win']for x in r['sensitivity_grid']))
Path(__file__).with_name('house_margin_results.json').write_text(json.dumps(out,indent=2)+'\n')
