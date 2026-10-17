"""Primary margin sensitivities, not an automatic forecaster or a fitted model.

Observed historical counts are documented in source packets. Transfer, mixture,
error and contingency weights are explicitly primary judgments. No prices enter.
"""
import json,math
from pathlib import Path

def phi(z):return .5*math.erfc(-z/math.sqrt(2))
def update(mu,sd,poll,psd):
    v=1/(1/sd**2+1/psd**2)
    m=v*(mu/sd**2+poll/psd**2)
    return m,math.sqrt(v)

# pvi is Democratic share advantage (negative for R); inc/adj are D-margin pp.
CASES={
32:dict(district='CA06',yes='D',pvi=5,inc=-2,adj=-4,local_sd=7,poll=.2,moe=3.2,poll_bias=1.5,age=4,common=4,other=0,low=.35,high=.99),
46:dict(district='TN04',yes='R',pvi=-11,inc=-2,adj=0,other=.005,low=.45,high=.9995),
60:dict(district='WA05',yes='D',pvi=-5,inc=-2,adj=0,history=-21.2806,history_weight=.65,poll=-6,moe=5.6,poll_bias=0,age=6,common=4,other=.003,low=.01,high=.65),
74:dict(district='FL03',yes='D',pvi=-10,inc=-2,adj=0,other=.01,low=.001,high=.65),
95:dict(district='GA10',yes='R',pvi=-11,inc=0,adj=0,other=.005,low=.35,high=.9995),
102:dict(district='AL02',yes='R',pvi=-7,inc=2,adj=0,poll=0,moe=4.8,poll_bias=-2,age=5,common=4,other=.003,low=.15,high=.97),
109:dict(district='NH02',yes='D',pvi=2,inc=2,adj=0,history=5.9605,history_weight=.5,history_adjustment=1,other=.01,low=.65,high=.999),
123:dict(district='ME02',yes='D',pvi=-4,inc=0,adj=-2,local_sd=7,poll=4,moe=4.38,poll_bias=-1.5,age=1,common=4,other=.002,low=.15,high=.95),
144:dict(district='FL07',yes='D',pvi=-5,inc=0,adj=0,local_R_regime_weight=.3,local_R_regime_D_margin=-5,other=.005,low=.08,high=.92),
151:dict(district='NV04',yes='D',pvi=2,inc=2,adj=0,history=8.0868,history_weight=.45,other=.005,low=.65,high=.999),
165:dict(district='NE02',yes='R',pvi=3,inc=0,adj=0,history=-1.853,history_weight=.35,history_adjustment=2,other=.005,low=.001,high=.65),
186:dict(district='VA01',yes='R',pvi=-3,inc=-2,adj=0,history=-12.7816,history_weight=.6,other=.002,low=.10,high=.95),
193:dict(district='NC01',yes='D',pvi=-5,inc=2,adj=0,other=.003,low=.10,high=.98),
207:dict(district='NH01',yes='D',pvi=2,inc=0,adj=0,history=8.0633,history_weight=.3,history_adjustment=-2,other=.003,low=.60,high=.999),
214:dict(district='VA02',yes='R',pvi=0,inc=-2,adj=0,history=-3.8419,history_weight=.5,history_adjustment=1,other=.01,low=.01,high=.70),
221:dict(district='NY22',yes='R',pvi=4,inc=2,adj=0,history=9.112,history_weight=.5,history_adjustment=1,other=.003,low=.001,high=.40),
}

def probability(c,national=8,beta=.8,poll_shift=0,history_reference=-2.5):
    mu=national+2*beta*c['pvi']+c['inc']+c['adj']
    sd=math.hypot(3,c.get('local_sd',6))
    prior_mu=mu;poll_sd=None
    if 'poll' in c:
        poll_sd=math.sqrt((2*c['moe']/1.96)**2+c['common']**2+c['age']**2)
        mu,sd=update(mu,sd,c['poll']+c['poll_bias']+poll_shift,poll_sd)
    p=phi(mu/sd);historical=None
    if 'history' in c:
        hm=c['history']+.8*(national-history_reference)+c.get('history_adjustment',0)
        hs=8
        if poll_sd:hm,hs=update(hm,hs,c['poll']+c['poll_bias']+poll_shift,poll_sd)
        hp=phi(hm/hs);w=c['history_weight'];p=(1-w)*p+w*hp
        historical={'D_margin_mean':hm,'sd':hs,'p_D':hp,'weight':w}
    if 'local_R_regime_weight' in c:
        w=c['local_R_regime_weight'];rp=phi(c['local_R_regime_D_margin']/math.hypot(3,6))
        p=(1-w)*p+w*rp
    p=.98*p+.02*.5
    if c['district']=='CA06':
        # Pan's D label mostly persists; Kiley only contributes on a future D caucus-intent fork.
        party=p*.995+(1-p)*.02
    else:party=(1-c['other'])*(p if c['yes']=='D' else 1-p)
    return party,{'prior_D_mean':prior_mu,'updated_D_mean':mu,'updated_sd':sd,
                  'effective_poll_sd':poll_sd,'historical_component':historical,
                  'p_D_before_other_affiliation':p}

def run():
    out={'authority':'Primary judgment; not calibrated, not fitted, not a price-based screen.',
         'shared':{'national_D_margin':8,'pvi_beta':.8,'national_sd':3,'default_local_sd':6,
                   'history_reference_D_margin':-2.5,
                   'history_reference_note':'Rounded modeling reference, not a separately recounted official national popular-vote total; varied in sensitivity.',
                   'history_swing_coefficient':.8,'history_sd':8,'unmodeled_symmetric_branch':.02},'cases':{}}
    for i,c in CASES.items():
        p,detail=probability(c)
        grid=[]
        for national in [4,8,12]:
            for beta in [.6,.8,1]:
                for shift in [-3,0,3]:
                    for href in [-4.5,-2.5,-.5]:grid.append(probability(c,national,beta,shift,href)[0])
        lo,hi=min(grid),max(grid)
        assert c['low']<=lo and hi<=c['high'],(i,lo,hi)
        out['cases'][str(i)]={'inputs':c,**detail,'unrounded_p_yes':p,'primary_p_yes':round(p,2),
                              'scenario_range':[c['low'],c['high']],'grid_min':lo,'grid_max':hi}
    return out

if __name__=='__main__':print(json.dumps(run(),indent=2))
