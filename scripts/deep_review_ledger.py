#!/usr/bin/env python3
"""Persist primary-authored evaluations and rebuild a resumable index. No network/trading."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,csv,gzip,hashlib,io,json,os
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'research/2026-10-17-deep-review'
RULES=ROOT/'research/2026-10-17-primary-market-review-rules.jsonl.gz'
POINTER=ROOT/'notes/deep_review_checkpoint.json'
STATES={'valued','blocked_after_review','excluded_factual'}
def now():return datetime.now(timezone.utc).isoformat()
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp')
 with tmp.open('w') as f:f.write(data);f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)
def dump(path,value):atomic(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def universe():
 with gzip.open(RULES,'rt') as f:return {int(x['review_index']):x for x in map(json.loads,f)}
def rebuild(active=None):
 u=universe();records={}
 for p in sorted((RUN/'evaluations').glob('*.json')):
  x=json.loads(p.read_text());i=x['review_index'];assert i not in records;assert p.with_suffix('.md').exists();assert hashlib.sha256(p.with_suffix('.md').read_bytes()).hexdigest()==x['report_sha256'];records[i]=x
 counts={s:sum(x['status']==s for x in records.values()) for s in STATES};pending=[i for i in u if i not in records]
 old=json.loads((RUN/'progress.json').read_text()) if (RUN/'progress.json').exists() else {}
 active=old.get('active_indices',[]) if active is None else active
 active=[i for i in active if i not in records]
 progress={'schema':'polyclaude.deep_review.v1','updated_utc':now(),'scope':'All3000 frozen conditions; original screens do not reject. First100 completed valuations is operator inspection milestone; blocked reviews and factual exclusions are separate and do not count.','universe':len(u),'completed_in_depth_reviews':counts['valued']+counts['blocked_after_review'],'completed_valuations':counts['valued'],'blocked_after_in_depth_review':counts['blocked_after_review'],'factual_exclusions':counts['excluded_factual'],'pending':len(pending),'active_indices':active,'next_pending_indices':pending[:30],'milestone':100,'milestone_notified':old.get('milestone_notified',False),'execution_authority':'Research records are observations, never later execution authorization.'}
 rows=[]
 for i,r in u.items():
  v=records.get(i,{});rows.append({'index':i,'condition_id':r['conditionId'],'market_id':r['id'],'question':r['question'],'status':v.get('status','in_progress' if i in active else 'pending'),'evaluated_utc':v.get('evaluated_utc',''),'p_yes':v.get('forecast',{}).get('p_yes',''),'verdict':v.get('verdict',''),'report':f'evaluations/{i:04d}.md' if v else ''})
 buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows);atomic(RUN/'index.csv',buf.getvalue())
 lines=['# In-depth market review — live index','',f"Updated: {progress['updated_utc']}",'',f"**{progress['completed_valuations']}/100 first-milestone valuations saved:** {counts['valued']} valued; {counts['blocked_after_review']} blocked after in-depth review. {counts['excluded_factual']} factual exclusions separately; {len(pending)} pending.",'','Full queue: [index.csv](index.csv). Machine resume: [progress.json](progress.json). Protocol: [PROTOCOL.md](PROTOCOL.md). Prior screens carry no rejection authority.','', 'Each report below is written before moving to the next evaluation. Related contracts may share evidence, but each probability, literal binding and economic evaluation is explicit. Observations are dated; orders need fresh execution checks.','', '| Index | Market | Status | Verdict |','|---:|---|---|---|']
 for i,v in sorted(records.items()):
  title=u[i]['question'].replace('|','/');verdict=v['verdict'].replace('|','/');lines.append(f"|{i}|[{title}](evaluations/{i:04d}.md)|{v['status']}|{verdict}|")
 if active:lines+=['', 'Active indices: '+', '.join(map(str,active))]
 atomic(RUN/'INDEX.md','\n'.join(lines)+'\n');dump(RUN/'progress.json',progress)
 ledger=(RUN/'evaluations.jsonl')
 pointer={**progress,'run_directory':str(RUN.relative_to(ROOT)),'index':'research/2026-10-17-deep-review/INDEX.md','progress':'research/2026-10-17-deep-review/progress.json','queue':'research/2026-10-17-deep-review/index.csv','protocol':'research/2026-10-17-deep-review/PROTOCOL.md','original_frozen_rules':str(RULES.relative_to(ROOT)),'original_rules_sha256':hashlib.sha256(RULES.read_bytes()).hexdigest(),'evaluations_written':len(records),'ledger_sha256':hashlib.sha256(ledger.read_bytes()).hexdigest() if ledger.exists() else None,'resume':'Read PROTOCOL and progress; validate index/record identities. Resume active work first, then next pending. Preserve all prior case records; append explicit revisions for changed evidence. Never turn blocked/unpriced into rejected.'}
 dump(POINTER,pointer);return progress

def record(path):
 x=json.loads(Path(path).read_text());u=universe();i=int(x['review_index']);r=u[i];assert x['status'] in STATES
 assert x['condition_id'].lower()==r['conditionId'].lower()
 assert x['criteria_sha256']==r['criteria_sha256'] or x.get('criteria_change_explained')
 for field in ['literal_analysis','evidence','forecast','economics','verdict','reopen_condition','report_markdown']:
  assert x.get(field),field
 assert isinstance(x['evidence'],list) and all(e.get('url') and e.get('observed_utc') and e.get('finding') for e in x['evidence'])
 if x['status']=='valued':
  f=x['forecast'];assert 0<=f['p_yes']<=1 and 0<=f['low']<=f['p_yes']<=f['high']<=1 and f.get('reasoning') and f.get('method')
  assert x['economics'].get('both_sides_considered') is True
 x['evaluated_utc']=x.get('evaluated_utc',now());x['question']=r['question'];x['market_id']=r['id'];x['valuation_author']='primary_operator';x['original_index']=i
 dest=RUN/'evaluations'/f'{i:04d}.json';assert not dest.exists(),f'already recorded {i}; revisions must be explicit'
 report=x.pop('report_markdown').rstrip()+'\n';x['report_sha256']=hashlib.sha256(report.encode()).hexdigest();atomic(dest.with_suffix('.md'),report);dump(dest,x)
 with (RUN/'evaluations.jsonl').open('a') as f:f.write(json.dumps(x,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
 return rebuild()

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['init','start','record','rebuild']);p.add_argument('--index',type=int);p.add_argument('--input');a=p.parse_args()
 (RUN/'evaluations').mkdir(parents=True,exist_ok=True)
 if a.command=='record':out=record(a.input)
 elif a.command=='start':
  assert a.index in universe();old=json.loads((RUN/'progress.json').read_text());out=rebuild(sorted(set(old.get('active_indices',[])+[a.index])))
 else:out=rebuild()
 print(json.dumps(out))
if __name__=='__main__':main()
