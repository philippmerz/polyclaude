"""Primary, uncalibrated joint Q3 da Vinci growth distribution.

The bridge uses approximate rounded procedure counts only for a forecast.
It never calls the derived ratio a more precise reported resolving metric.
Annual guidance is not a Q3 confidence interval or a guaranteed outcome.
"""
import itertools,json,math

def phi(z):return .5*math.erfc(-z/math.sqrt(2))
H1_2025=1507
FY_2025=3153
H1_2026=1737
H2_2025=FY_2025-H1_2025
ANNUAL_GUIDE_MIDPOINT=14.5
H2_BRIDGE=100*((FY_2025*(1+ANNUAL_GUIDE_MIDPOINT/100)-H1_2026)/H2_2025-1)

def model(annual_center=14.5,annual_sd=.5,quarter_deviation_sd=1.0,
          persistence=.20,disruption=.05,precision_integer=.85,fallback=.003):
    bridge=100*((FY_2025*(1+annual_center/100)-H1_2026)/H2_2025-1)
    # Annual-center error is amplified in H2 because H1 has already occurred.
    bridge_sd=math.sqrt((annual_sd*FY_2025/H2_2025)**2+quarter_deviation_sd**2+.2**2)
    comps=[(1-persistence-disruption,bridge,bridge_sd),
           (persistence,15.2,1.2),(disruption,11.5,3.0)]
    # Historical issuer tables state integer percentages. If a more precise
    # metric is explicitly published it governs; a count-derived ratio does not.
    def below(boundary):
        rounded_cut=math.ceil(boundary)-.5
        return sum(w*(precision_integer*phi((rounded_cut-mu)/sd)+
                      (1-precision_integer)*phi((boundary-mu)/sd))for w,mu,sd in comps)
    c=[0]+[below(b)for b in [10,12.5,15,17.5]]+[1]
    p=[(1-fallback)*(b-a)for a,b in zip(c,c[1:])]
    p[0]+=fallback
    assert min(p)>=0 and abs(sum(p)-1)<1e-12
    return p,{'annual_center':annual_center,'bridge_H2_growth_pp':bridge,
              'bridge_sd_pp':bridge_sd,'components':comps,
              'reported_integer_probability':precision_integer,'fallback_to_lowest':fallback}

def run():
    p,inputs=model()
    grid=[model(a,s,q,r,d,prec,f)[0] for a,s,q,r,d,prec,f in itertools.product(
          [14.0,14.5,15.0],[.35,.5,.75],[.6,1,1.5],[.10,.20,.35],[.02,.05,.10],[.5,.85,1],[0,.003,.01])]
    cents=[math.floor(x*100)for x in p]
    for j in sorted(range(5),key=lambda i:p[i]*100-cents[i],reverse=True)[:100-sum(cents)]:cents[j]+=1
    rounded=[x/100 for x in cents]
    return {'authority':'Primary uncalibrated scenario model; no market prices enter.',
       'metric':'Q3 2026 worldwide da Vinci procedure growth YoY as first officially reported, not Ion or combined.',
       'rounded_approximate_counts_thousands':{'H1_2025':H1_2025,'FY_2025':FY_2025,'H1_2026':H1_2026,'Q3_2025':797,'Q4_2025':849},
       'source_precision':'Counts approximate and independently rounded. Q1+Q2_2026 displayed1736 differs H1displayed1737; company growth uses unrounded estimates. Derived ratios are forecast inputs only.',
       'annual_guidance_pp':[13.5,15.5],'midpoint_bridge_pp':H2_BRIDGE,
       'central_inputs':inputs,'probabilities':p,'rounded_probabilities':rounded,
       'labels':['<10','10<=x<12.5','12.5<=x<15','15<=x<17.5','17.5<=x'],
       'grid_size':len(grid),'grid_ranges':[[min(x[i]for x in grid),max(x[i]for x in grid)]for i in range(5)],
       'limitations':['Annual guidance does not give Q3/H2 guidance or confidence coverage',
       'Quarter allocation, guidance uncertainty, persistence/disruption weights and presentation mix are primary assumptions',
       'September9 conference remarks were not reviewed; no claim all oral guidance is checked',
       'Historical rounded growth series is too short/nonstationary for tail calibration'],
       'execution':'No order, canonical prior or reservation authority.'}

if __name__=='__main__':print(json.dumps(run(),indent=2))
