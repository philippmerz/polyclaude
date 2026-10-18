"""Coherent common rank marginals for frozen market-cap cases 154/196/260/268."""
from __future__ import annotations
import gzip,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; DATA=ROOT/'data/deep_review_20261017/work'
RULES=ROOT/'research/2026-10-17-primary-market-review-rules.jsonl.gz'
RANKS=DATA/'0260_event_exclusion_rank_marginals_2026.json'
OLD=DATA/'0260_joint_diagnostic.json'
OUT=DATA/'marketcap_shared_rank_fork_2125.json'; ARR=DATA/'marketcap_shared_rank_fork_arrays_2125.json'
FIRMS=('NVDA','AAPL','MSFT','Alphabet','Other')
PERMS=((.10,('AAPL','Alphabet','NVDA','MSFT','Other')),(.10,('NVDA','Alphabet','AAPL','MSFT','Other')),(.50,('NVDA','AAPL','MSFT','Alphabet','Other')),(.25,('AAPL','NVDA','Alphabet','MSFT','Other')),(.05,('NVDA','AAPL','Other','Alphabet','MSFT')))
FROZEN_CASES={
 154:('5180413','0xe09c250c2d5ba126bb97b417c55185419600555e9679c9b78cc1a9a4b6e8d151','NVIDIA','largest'),
 196:('5166967','0x27802b8b0d6d500d6ccaf122c1efbc542b8473c765782bfe6d9b5cb425f76232','Microsoft','third-largest'),
 260:('5166969','0x0f5fcde4109ac8d2672d822d50b8768696833baaf8959884c6016e2b0ad3e4a5','Alphabet','third-largest'),
 268:('5180417','0xb4401733eed8e257ceba7f6133de1793bb7d409d1e44864a789c31824460a374','Apple','largest'),
}
RESOLUTION_SOURCE='The resolution source for this market will be a consensus of credible reporting.'
def sha(b):return hashlib.sha256(b).hexdigest()
def validate_frozen_rank_case(index,market):
 """Bind a frozen case to its exact company/rank/date description and title."""
 market_id,condition_id,entity,rank=FROZEN_CASES[index]
 description=f'This market will resolve to the {rank} company in the world by market cap on October 31, 2026, as of market close.\n\n{RESOLUTION_SOURCE}'
 prefix=f'Will {entity} be the {rank} company in the world by market cap on October 31'
 accepted_questions={prefix+'?',prefix+', 2026?'}
 if str(market.get('id'))!=market_id:raise ValueError(f'frozen market id mismatch {index}')
 if str(market.get('conditionId','')).lower()!=condition_id.lower():raise ValueError(f'frozen condition id mismatch {index}')
 if market.get('question') not in accepted_questions:raise ValueError(f'frozen question entity/rank/date mismatch {index}')
 if market.get('description')!=description:raise ValueError(f'frozen full description mismatch {index}')
 return True
def main():
 if OUT.exists() or ARR.exists():raise FileExistsError('refuse output overwrite')
 frozen={}
 with gzip.open(RULES,'rt',encoding='utf-8') as f:
  for line in f:
   x=json.loads(line); i=int(x['review_index'])
   if i in (154,196,260,268):frozen[i]=x
 if set(frozen)!={154,196,260,268}:raise ValueError('identity coverage mismatch')
 identities={}
 for i in (154,196,260,268):
  x=frozen[i]; validate_frozen_rank_case(i,x)
  _,_,firm,rank=FROZEN_CASES[i]; desc=x['description']
  identities[str(i)]={'market_id':str(x['id']),'condition_id':str(x['conditionId']),'criteria_sha256':x['criteria_sha256'],'description_sha256':sha(desc.encode()),'question':x['question'],'descriptor_checked':{'entity':firm,'rank':rank,'date':'October 31, 2026'}}
 src=json.loads(RANKS.read_text()); old=json.loads(OLD.read_text())
 if src['schema']!='polyclaude.marketcap_event_exclusion_rank_marginals.v1':raise ValueError('unexpected rank source schema')
 base={firm:[sum(src['rank_1_to_4'][w]['8%']['rank_1_to_4'][firm][r] for w in ('20','89'))/2 for r in range(4)] for firm in FIRMS[:-1]}
 base['Other']=[0,0,0,0]
 # Assign the residual to Other at rank 5 for the four-firm path.
 base['Other'].append(1.0)
 # Add fifth-rank zeros for companies in the four-firm path.
 for firm in FIRMS[:-1]:base[firm].append(0.0)
 uniform={firm:[.2]*5 for firm in FIRMS}
 alternative={firm:[0.0]*5 for firm in FIRMS}
 for weight,order in PERMS:
  for rank,firm in enumerate(order):alternative[firm][rank]+=weight
 if not all(abs(sum(alternative[f][r] for f in FIRMS)-1)<1e-12 for r in range(5)):raise ValueError('alternative rank mass not normalized')
 # Check the requested permutation fork retains the prior exact-third consensus vector.
 expected={'NVDA':.10,'AAPL':.10,'MSFT':.50,'Alphabet':.25,'Other':.05}
 if any(abs(alternative[f][2]-expected[f])>1e-12 for f in FIRMS):raise ValueError('rank-3 fork no longer matches previous consensus')
 final={f:[.95*(.98*base[f][r]+.02*uniform[f][r])+.05*alternative[f][r] for r in range(5)] for f in FIRMS}
 for r in range(5):
  if abs(sum(final[f][r] for f in FIRMS)-1)>1e-12:raise ValueError(f'rank {r+1} marginal sum failure')
 for f in FIRMS:
  if final[f][0]+final[f][2]>1+1e-12:raise ValueError(f'rank1/rank3 event overlap for {f}')
 prior=old['third_place_fork']['consensus_branch']['distribution']
 if any(abs(alternative[f][2]-prior[j])>1e-12 for j,f in enumerate(('NVDA','AAPL','MSFT','Alphabet','Other'))):raise ValueError('alternative rank3 vector differs from prior fork')
 summary={'schema':'polyclaude.marketcap_shared_rank_fork.v1','created_utc':datetime.now(timezone.utc).isoformat(),'input_path':str(RANKS.relative_to(ROOT)),'input_sha256':sha(RANKS.read_bytes()),'prior_fork_sha256':sha(OLD.read_bytes()),'rank_source':'8% paired event-shock marginals, equal-weighted 20-day and 87-row event-excluded 89-day windows','frozen_identities':identities,'fork':{'formula':'.95*(.98*four_firm_base + .02*uniform_permutation_5) + .05*weighted_alternative_permutations','outside_company_note':'Other is an aggregate residual: rank >=5 in the four-firm base path and exactly one of five uniformly/alternative permuted outcomes in the 5% branches.','alternative_rank3_matches_previous_consensus':True,'rank1_and_rank3_marginals_path':str(ARR.relative_to(ROOT))},'rank1_marginal':{f:final[f][0] for f in FIRMS},'rank3_marginal':{f:final[f][2] for f in FIRMS},'rank1_plus_rank3_by_company':{f:final[f][0]+final[f][2] for f in FIRMS},'rank1_sum':sum(final[f][0] for f in FIRMS),'rank3_sum':sum(final[f][2] for f in FIRMS),'scope':'Normalized shared-rank marginal fork only; not a selected probability or an empirical distribution for Other.'}
 arrays={'schema':'polyclaude.marketcap_shared_rank_arrays.v1','created_utc':summary['created_utc'],'input_sha256':summary['input_sha256'],'rank_order':[1,2,3,4,'5+'],'firms':list(FIRMS),'base_four_firm_path':base,'uniform_five_permutation_branch':uniform,'alternative_weighted_permutation_branch':alternative,'final_rank_marginals':final}
 OUT.write_text(json.dumps(summary,separators=(',',':'))+'\n'); ARR.write_text(json.dumps(arrays,indent=2)+'\n')
 if OUT.stat().st_size>4096:raise ValueError(f'summary too large: {OUT.stat().st_size}')
 print(json.dumps({'summary':str(OUT.relative_to(ROOT)),'bytes':OUT.stat().st_size,'arrays':str(ARR.relative_to(ROOT)),'array_bytes':ARR.stat().st_size,'rank1':summary['rank1_marginal'],'rank3':summary['rank3_marginal'],'rank_sums':[summary['rank1_sum'],summary['rank3_sum']],'rank1plus3':summary['rank1_plus_rank3_by_company']}))
if __name__=='__main__': main()
