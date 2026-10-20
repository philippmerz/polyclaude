from pathlib import Path
import sys,json,gzip,hashlib
sys.path.insert(0,str(Path('scripts').resolve()))
from deep_review_ledger import universe
from deep_review_economics import economics
u=universe()[440];data=Path('data/deep_review_20261017/work');qp='data/deep_review_20261017/0440_quote_0650.json'
verified=[]
for p in Path('logs/deep_review_20261017/case0440_quote_0650').rglob('*.receipt.json'):
 r=json.loads(p.read_bytes());z=Path(r['gzip_path']).read_bytes();b=gzip.decompress(z);assert hashlib.sha256(z).hexdigest()==r['gzip_sha256'];assert hashlib.sha256(b).hexdigest()==r['raw_sha256'];verified.append({'receipt':str(p),'raw_sha256':r['raw_sha256']})
assert len(verified)==4
yes=economics(440,.0001,qp,reserve=.1,days=62,quantity=100);eco=economics(440,.0001,qp,reserve=.1,days=62,quantity=5);eco.pop('hypothetical_gross_shares',None);eco['quantity_by_outcome']={'Yes':100,'No':5};eco['sides']['Yes']=yes['sides']['Yes']
carry={str(d):eco['sides']['No']['taker_cost_usd']*(1+.032035)**(d/365) for d in [7,14,21,62]}
eco['maker_and_carry']={'Yes':'YES100 meets1USDroute. At1c touch and even1milli minimumtick, centralfair0.0001fails.','No':'NO995milli maker5cost4.975:central+.02450/selected-.47550; remote<=899milli fillselectionunmeasured, no blindbid.','constant_APY':.032035,'No_taker_cost_terminal_by_days':carry,'timing_limit':'EarlyNO may follow mathematicalelimination;7/14/21daycarry clearscentral,62dayendcarrydoesnot. No automaticimmediatefinality/settlementcertificate.'}
(data/'0440_economics_0652.json').write_text(json.dumps(eco,indent=2)+'\n')
report=f'''# 440 · Tromsø, Eliteserien champion

**Valued YES0.01% / NO99.99%; no entry.** Broad YES0–2% is judgmental uncertainty, not a calibrated interval. Ordinary10pp entry reserve gives selected YES0/NO89.99%. Eligible open contract, not a factual exclusion.

Full rule: named league champion; early NO once championship is impossible; multiple champions use alphabetical order; cancellation/no champion after Dec20 23:59ET goes to Other. Official league information/credible consensus govern. Administrative and adjudication uncertainty remain.

**23 matches, not24.** Root reconstructed all184 played matches across23 complete rounds, matching all16 official table rows. Round24 is included; postponed round12 is outstanding. Adding round24 again falsely implies41/59/59 and elimination; that discarded hypothesis was corrected before any forecast/quote. Independent NFF table, remaining fixtures and2026 regulations confirm30games,3-1-0points and goal-difference-first tiebreaks. Tromsø40points/+11GD; Bodø/Glimt56/+38, Viking56/+37; seven matches remain, so not eliminated.

Four coupled games remain: Viking–Tromsø Oct25, Bodø–Viking Oct30, Tromsø–Bodø Nov8, Tromsø–Viking Nov21. Tromsø ceiling61 requires both leaders to gain at most5points; the26–27GD deficit hurts tied-point routes. Other contenders, sanctions, cancellation and playoff timing add risk.

Prequote primary model: shrink23-game GF/GA with5 league-mean pseudogames,1.12home advantage, independent Poisson W/D/L, enumerate81 joint outcomes of the four shared games, convolve other fixtures. Current/form-shock/extreme common-collapse scenarios have90/9/1% handweights and yield4.34566e-5 weighted three-contender envelope with5% tie credit. Ignoring other contenders favors Tromsø. Regime weights/tie credit are unfitted; no lineup/xG calibration or measured rare-event frequency. Primary rounds to1e-4 YES with extra model/administrative skew; broad0–2%. Seven future games prevent claiming a measured short-horizon bond tail, so no unsupported K5 exemption.

| Side / size | Captured taker cost | Central profit | Selected profit |
|---|---:|---:|---:|
| YES100 |{eco['sides']['Yes']['taker_cost_usd']:.5f}|{eco['sides']['Yes']['central_expected_profit_usd']:.5f}|{eco['sides']['Yes']['selected_stress_profit_usd']:.5f}|
| NO5 |4.98060|+.01890|−.48110|

06:46:40 capture:3%×p(1−p) taker fee,5share minimum/1milli tick. Both books568.65s old, failing180s freshness; these are dated planning observations. YES100 walks from1c through deeper asks and clears1USD route; it fails central even at the minimum tick. NO995milli maker5 gives+.02450central/−.47550selected. Remote≤899milli NO has no underwritten conditional-fill margin; no blind bid.

Early elimination may shorten holding: dated3.2035%Aave held constant turns4.98060 into{carry['7']:.5f}/{carry['14']:.5f}/{carry['21']:.5f} over7/14/21days, below4.99950central payout.62day cost{carry['62']:.5f} exceeds even5maximum. Do not automatically charge the full end window, assume immediate settlement, or omit gas/routing/venue risk. Tiny central profit fails the selected gate; Aave/known alternatives win the present allocation comparison.

Dated06:22 account195.90gas-inclusive/190.09tradingmid/185.89indicative depth,3originalunfilled bids/6.50. No Tromsø holding; NO5 would risk4.98 and share venue/sports risk. Any later entry needs fresh account/collateral/eligibility/fee/books/caps and vetted writer. No order, forecast-prior, funding or watcher change. Reopen on verified mathematical elimination/official result, material football evidence or a genuinely underwritten fresh price.

[Sources](../../../data/deep_review_20261017/work/0440_followup_facts_0640.json) · [Reconstruction](../../../data/deep_review_20261017/work/0440_results_reconstructed_0643.json) · [Prequote model](../models/0440_primary_model_0648.json) · [Economics](../../../data/deep_review_20261017/work/0440_economics_0652.json).
'''
x={'review_index':440,'market_id':u['id'],'condition_id':u['conditionId'],'criteria_sha256':u['criteria_sha256'],'token_ids':json.loads(u['clobTokenIds']) if isinstance(u['clobTokenIds'],str) else u['clobTokenIds'],'status':'valued','literal_analysis':'Fullchampion/earlyNO/OtherDec20/alphabetical/source rules read; sevenoutstandinginclround12, noteliminated.','evidence':[{'url':'https://www.eliteserien.no/resultater','observed_utc':'2026-10-20T04:59:16.927725Z','finding':'Root184match reconstruction23complete rounds;24included/12missing,all16standingsreproduce.'},{'url':'https://www.fotball.no/turneringer/eliteserien/','observed_utc':'2026-10-20T06:40:50.824476Z','finding':'IndependenttableT23/40/B23/56/V23/56.'},{'url':'https://www.eliteserien.no/terminliste','observed_utc':'2026-10-20T06:40:50.994081Z','finding':'Sevenremaininginclpostponed12;fourcoupledT/B/Vgames.'},{'url':'https://www.fotball.no/globalassets/regler-og-retningslinjer/turneringsbestemmelser/turneringsbestemmelser-eliteserien.pdf','observed_utc':'2026-10-20T06:40:51.098262Z','finding':'RootPDF1/2/4 read16clubs/homeaway/3-1-0; LovdataGD/goals/H2H/playoffcorroboration.'}],'forecast':{'p_yes':.0001,'low':0.,'high':.02,'actual_entry_reserve_pp':10,'method':'Unfittedcurrentgoal/fixturePoisson+coupledpoints/scenarios, primary prequote.','reasoning':'16pointgap/twoleaders/7games/GD26–27deficit. Threecontenderenvelope4.34566e-5,1e-4 adoptedwithextramodel/adminskew. Not calibratedtail, no falseelim.'},'economics':eco,'verdict':'NO_ENTRY: YESfailscentral;NOtinycentralprofitfailsordinaryselected,datedbooksfailfreshness. EarlycarrycanbeatAaveifpaidsoon,notguaranteed;endcarryfails. No blindremoteorder.','reopen_condition':'VerifiedmathNO/officialresult/materialfootballfacts orunderwrittenconditionalfreshprice,thenallgates.','report_markdown':report}
(data/'0440_final_0652.json').write_text(json.dumps(x,indent=2)+'\n');(data/'0440_quote_receipts_verified_0652.json').write_text(json.dumps({'verified':verified},indent=2)+'\n')
print(json.dumps({'prepared_final':True,'YES_cost':eco['sides']['Yes']['taker_cost_usd'],'NO_cost':eco['sides']['No']['taker_cost_usd'],'source_receipt_pairs':4,'report_bytes':len(report.encode())}))
