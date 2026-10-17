"""Explicit primary Q3 FY27 non-GAAP gross-margin scenario distribution.

Official six-quarter forecast errors are context, not an IID calibrated fit.
Guidance bands are not statistical confidence intervals. All mixture weights,
spread and interpretation/fallback mass are disclosed subjective assumptions.
"""
import itertools,json,math

def phi(z):return .5*math.erfc(-z/math.sqrt(2))

def model(mu=74.1,sd=.7,down=.10,up=.05,down_mu=70.5,fallback=.005):
    components=[(1-down-up,mu,sd),(down,down_mu,3.0),(up,76.0,1.25)]
    # A tenth-of-a-point reported line is common; a more precise version wins
    # under the rule. Rounded exact boundary values enter the higher bracket.
    def below(b):
        return sum(w*(.8*phi((b-.05-m)/s)+.2*phi((b-m)/s)) for w,m,s in components)
    c=[0]+[below(b) for b in [71,73,75,77]]+[1]
    probs=[(1-fallback)*(b-a)for a,b in zip(c,c[1:])]
    probs[0]+=fallback
    assert abs(sum(probs)-1)<1e-12 and min(probs)>=0
    return probs

def run():
    central=model();labels=['<71','71<=x<73','73<=x<75','75<=x<77','77<=x']
    grids=[model(mu,s,d,u,dm,f) for mu,s,d,u,dm,f in itertools.product(
        [73.6,74.1,74.6],[.5,.7,1.1],[.05,.10,.20],[.02,.05,.15],[68,70.5,72],[0,.005,.02])]
    return {'authority':'Primary uncalibrated scenario sensitivity; no prices or screening labels are inputs.',
        'metric':'Q3 FY2027 official first-reported non-GAAP gross margin, most precise specified metric; not extra H20-excluding variant.',
        'observed_original_guidance_actual_errors_pp':[-10.0,.7,.1,.2,0.,0.],
        'history_limit':'Q1FY26H20charge is real original reported-line loss, not replaced by71.3. SBCdefinition changesFY27; later comparative restatements do not replace original first reports. Six observations are not IID tail calibration.',
        'central_inputs':{'ordinary_weight':.85,'ordinary_mu':74.1,'ordinary_sd':.7,'downside_weight':.10,'downside_mu':70.5,'downside_sd':3,'upside_weight':.05,'upside_mu':76,'upside_sd':1.25,'missing_metric_or_late_fallback':.005,'reported_precision_mix_tenths_full': [.8,.2]},
        'labels':labels,'probabilities':central,'rounded_probabilities':[round(p,2)for p in central],
        'sensitivity_grid_size':len(grids),'sensitivity_ranges':[[min(x[i]for x in grids),max(x[i]for x in grids)]for i in range(5)],
        'unmodeled_risks':['Unannounced export-control/inventory charge','Rubin product-ramp mix/cost change','Changed official non-GAAP definition or first-publication interpretation','Delayed or omitted metric with lowest-bracket fallback'],
        'execution':'No order, canonical prior or reservation authority.'}

if __name__=='__main__':print(json.dumps(run(),indent=2))
