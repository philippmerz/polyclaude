import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from scripts import deep_review_ledger as ledger
R=Path(__file__).resolve().parents[3]; M=R/'research/2026-10-17-deep-review/models'; W=R/'data/deep_review_20261017/work'
I=M/'marketcap_inputs.json'; E=W/'0260_earnings_event_history.json'; ES=W/'0260_event_exclusion_sensitivity_2026.json'
OUT=M/'apple280_rank_sensitivity_2220.json'; ARR=W/'0280_rank_sensitivity_arrays_2220.json'
N=100_000; SEED=28020261018; WINDOWS=(20,89); SIGMAS=(0,.04,.08,.15)
F=('NVDA','AAPL','MSFT','Alphabet'); ALL=(*F,'Other')
ALT=((.10,('AAPL','Alphabet','NVDA','MSFT','Other')),(.10,('NVDA','Alphabet','AAPL','MSFT','Other')),(.50,('NVDA','AAPL','MSFT','Alphabet','Other')),(.25,('AAPL','NVDA','Alphabet','MSFT','Other')),(.05,('NVDA','AAPL','Other','Alphabet','MSFT')))
sha=lambda b:hashlib.sha256(b).hexdigest()

def rankdist(change,caps):
    order=np.argsort(-(np.log(caps[-1])+change),axis=1); base=np.zeros((5,5))
    for j in range(4): base[j,:4]=np.bincount(np.argmax(order==j,axis=1),minlength=4)/N
    base[4,4]=1; uni=np.full((5,5),.2); alt=np.zeros((5,5))
    for wt,perm in ALT:
        for rank,name in enumerate(perm): alt[ALL.index(name),rank]+=wt
    out=.95*(.95*base+.05*uni)+.05*alt
    if not np.allclose(out.sum(0),1,atol=1e-12) or not np.allclose(out.sum(1),1,atol=1e-12): raise ValueError('rank mass failed')
    return {name:[float(v) for v in out[j]] for j,name in enumerate(ALL)}

def main():
    if OUT.exists() or ARR.exists(): raise FileExistsError('refuse overwrite')
    x=ledger.universe()[280]
    if (str(x['id'])!='676741' or x['conditionId'].lower()!='0x55a5a4b50b7947482e95af8f638fa0b8d9a46740c5cd04c6799443e83565176a' or x['question']!='Will Apple be the largest company in the world by market cap on December 31?' or 'largest company in the world by market cap on December 31, 2026, as of market close.' not in x['description']): raise ValueError('frozen case semantics/identity changed')
    inp=json.loads(I.read_text()); ev=json.loads(E.read_text()); es=json.loads(ES.read_text()); ih=sha(I.read_bytes()); eh=sha(E.read_bytes())
    if ih!='32dafab53f6f77deb6ef862d670824e3f9fe7b5366393d3a27f688d32f2cfca7' or eh!='1b38ea38700ac4d813c596f9e63206d913abf311b2353f847fcb7a6b60ac1ead' or es['inputs_sha256']!=ih or es['official_event_history_sha256']!=eh: raise ValueError('input/event hash linkage failed')
    p=np.asarray(inp['price_rows'],float); s=inp['fixed_shares_billions']; caps=np.column_stack((p[:,0]*s['NVDA'],p[:,1]*s['AAPL'],p[:,2]*s['MSFT'],p[:,3]*s['Alphabet_A_B']+p[:,4]*s['Alphabet_C']))/1000
    dates=np.asarray(inp['dates'][1:]); ret=np.diff(np.log(caps),axis=0)
    excluded={f"{d[5:7]}/{d[8:10]}/{d[:4]}" for e in ev['q2_events'] for d in [e['tickers']['MSFT']['next_session_close']['date'] if e['company']=='Microsoft' else e['tickers']['GOOGL']['next_session_close']['date']]}
    rng=np.random.default_rng(SEED); cells={}; meta={}
    for w in WINDOWS:
        r0=ret[-w:]; d0=dates[-w:]; keep=np.array([d not in excluded for d in d0]) if w==89 else np.ones(len(d0),bool); r=r0[keep]; d=d0[keep]
        if len(r)!=(87 if w==89 else 20): raise ValueError('window count mismatch')
        cov=np.cov(r.T); eig=np.linalg.eigvalsh(cov)
        if eig.min()<=0: raise ValueError('covariance not positive definite')
        bg=rng.standard_normal((N,4))@np.linalg.cholesky(cov).T*np.sqrt(52); z=rng.standard_normal((N,4)); v={}
        for sig in SIGMAS: v[f'{sig:.0%}']=rankdist(bg+z*sig,caps)
        t5=bg*np.sqrt(3/rng.chisquare(5,N))[:,None]; v['student_t5_bg_plus_8pct']=rankdist(t5+z*.08,caps)
        for sign in (-1,1):
            zz=z*.08; zz[:,1]+=sign*.05; v[f'apple_relative_{"plus" if sign>0 else "minus"}5pct_plus_8pct']=rankdist(bg+zz,caps)
        cells[str(w)]=v; meta[str(w)]={'input_rows':int(len(r0)),'used_rows':int(len(r)),'removed_dates':sorted(set(d0.tolist())-set(d.tolist())),'covariance_min_eigenvalue':float(eig.min()),'positive_definite':True}
    equal={}
    for variant in next(iter(cells.values())):
        mat=np.mean([np.asarray([cells[w][variant][name] for name in ALL]) for w in ('20','89')],axis=0)
        equal[variant]={name:[float(q) for q in mat[j]] for j,name in enumerate(ALL)}
    now=datetime.now(timezone.utc).isoformat(); ident={'review_index':280,'market_id':str(x['id']),'condition_id':x['conditionId'],'criteria_sha256':x['criteria_sha256'],'question':x['question'],'checked_semantics':'Apple; largest/rank 1; Dec 31 2026 market close'}
    summary={'schema':'apple280_rank_sensitivity.v1','created_utc':now,'identity':ident,'inputs_sha256':ih,'event_history_sha256':eh,'seed':SEED,'samples_per_cell':N,'horizon_sessions':52,'session_basis':'54 weekdays less Nov 26/Dec 25; early closes count full variance.','method':'Zero drift; equal 20/87 covariance windows scaled to 52 sessions; independent terminal shocks.','fork':'.95*(.95 four-firm+.05 uniform)+.05 fixed alternatives; Other=5+ only in four-firm branch.','covariance':meta,'sigma_grid':[0,.04,.08,.15],'diagnostics':['t5+8%','Apple relative +/-5%+8%'],'arrays':'data/deep_review_20261017/work/0280_rank_sensitivity_arrays_2220.json','limits':'Judgmental shocks; short/nonstationary data; residual Apple/NVDA earnings may remain; NVDA event timing unknown. Sensitivity only.'}
    ARR.write_text(json.dumps({'schema':'apple280_rank_sensitivity_arrays.v1','created_utc':now,'seed':SEED,'samples_per_cell':N,'rank_order':[1,2,3,4,'5+'],'firm_order':list(ALL),'cells_by_window':cells,'equal_window_marginals':equal},separators=(',',':'))+'\n')
    summary['model_sha256']=sha(Path(__file__).read_bytes()); summary['arrays_sha256']=sha(ARR.read_bytes())
    OUT.write_text(json.dumps(summary,separators=(',',':'))+'\n')
    if OUT.stat().st_size>4096: raise ValueError('summary size exceeded')
if __name__=='__main__': main()
