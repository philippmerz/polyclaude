# patch remaining parts of join_gamma.py: store negRiskRequestID; attach via both ids
import re
src = open('join_gamma.py').read()
src = src.replace("""                'negRisk': m.get('negRisk'),""",
"""                'negRisk': m.get('negRisk'),
                'negRiskRequestID': (m.get('negRiskRequestID') or '').lower(),""")
src = src.replace("""    for qid, meta in markets.items():
        evs = by_qid.get(qid, [])""",
"""    for qid, meta in markets.items():
        evs = by_qid.get((meta.get('questionID') or '').lower(), []) + \\
              [e for e in by_qid.get(meta.get('negRiskRequestID') or '', [])
               if e not in by_qid.get((meta.get('questionID') or '').lower(), [])]""")
open('join_gamma.py','w').write(src)
print('patched')
