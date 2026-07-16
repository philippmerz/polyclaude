#!/usr/bin/env python3
"""Pass 1: mechanical strictness/looseness marker scoring of market descriptions.
Reads universe.jsonl line-by-line, emits scored.jsonl sorted by composite score desc.
Score = marker_weight_sum (len-damped) * price_room * log10(volume).
"""
import json, math, re, sys

# (name, weight, regex) — strict markers
STRICT = [
    ("conj_both",      2.0, re.compile(r"\bboth\b.{0,40}\band\b|\ball of the following\b|\beach of\b", re.I)),
    ("multi_cond",     1.5, re.compile(r"\b(and|as well as)\b.{0,25}\bmust\b|\bmust (also|both)\b|\bonly if\b|\bif and only if\b", re.I)),
    ("defined_as",     2.0, re.compile(r"\bdefined as\b|\bfor (the )?purposes? of this market\b|\bthis market defines\b", re.I)),
    ("not_count",      2.5, re.compile(r"\bwill not (count|qualify|suffice)\b|\bdoes not (count|include|qualify)\b|\bwould not (count|qualify)\b|\bnot (be )?sufficient\b|\bnot count toward\b|\bexcludes?\b|\bexcluding\b", re.I)),
    ("permanence",     2.0, re.compile(r"\bpermanent(ly)?\b|\bfor at least \d|\bremain(s|ing)? (in|as|the|open|closed|below|above)\b|\bsustained\b|\bcontinuous(ly)?\b|\bconsecutive\b|\buninterrupted\b", re.I)),
    ("official_src",   1.5, re.compile(r"\bofficial(ly)?\b|\bformal(ly)?\b|\bsigned into law\b|\baccording to (the )?[A-Z]|\bas reported by\b|\bprimary (resolution )?source\b", re.I)),
    ("territorial",    2.0, re.compile(r"\bground (forces|troops|invasion|operation)\b|\bterritorial\b|\bcontrol of\b|\boccup(y|ies|ied|ation)\b|\bannex\b|\bseiz(e|ure)\b", re.I)),
    ("threshold",      1.0, re.compile(r"\bstrictly (greater|less|above|below)\b|\bgreater than or equal\b|\bat or above\b|\bat or below\b|\bexceeds?\b", re.I)),
    ("in_full",        2.0, re.compile(r"\bin (its|their) entirety\b|\bfull(y)? (implemented|enacted|withdrawn|repealed)\b|\bcomplete(d|ly)? (withdrawal|removal|ban)\b|\ball \d+\b", re.I)),
    ("must_occur_by",  1.0, re.compile(r"\bmust (occur|happen|be (completed|announced|signed|confirmed|reached))\b|\btake effect\b|\bin effect\b|\benter(s|ed)? into force\b", re.I)),
    ("no_resolve_yes", 1.5, re.compile(r"\bwill resolve \"?no\"?\b.{0,80}\b(even if|regardless|unless)\b|\bresolve(s)? (to )?\"?no\"?\b if\b", re.I)),
    ("named_body",     1.0, re.compile(r"\b(officially|publicly) (confirmed?|announced?|declared?) by (the )?[A-Z]|\bgovernment of\b|\badministration\b.{0,30}\bconfirm", re.I)),
]
# loose markers
LOOSE = [
    ("any_part",   2.5, re.compile(r"\bany (part|portion|amount|number|of the)\b|\bin (whole or in )?part\b|\bpartial(ly)?\b", re.I)),
    ("any",        1.0, re.compile(r"\bany\b", re.I)),
    ("attempt",    2.5, re.compile(r"\battempt(s|ed)?\b|\bseek(s)? to\b|\btr(y|ies) to\b", re.I)),
    ("announce",   2.0, re.compile(r"\bannounce(s|d|ment)?\b|\bstate(s|d)? (an )?intent(ion)?\b|\bpropos(e|es|ed|al)\b|\bcall(s|ed)? for\b", re.I)),
    ("reports_of", 2.5, re.compile(r"\breports? of\b|\breported(ly)?\b|\bcredible (media )?report", re.I)),
    ("brief",      2.0, re.compile(r"\beven (if )?(briefly|temporarily|momentarily)\b|\bat any (point|time)\b|\bfor any (period|length|duration|amount)\b|\bhowever brief\b|\bregardless of (duration|whether it)", re.I)),
    ("informal",   1.5, re.compile(r"\binformal(ly)?\b|\bcolloquial(ly)?\b|\bin (spirit|substance)\b|\bwidely (viewed|reported|considered)\b|\bconsensus of\b", re.I)),
    ("verbal",     1.5, re.compile(r"\b(statement|remarks?|tweet|post|interview|speech)\b.{0,50}\b(suffic|count|qualify)", re.I)),
]

def score_one(m):
    d = m.get("description") or ""
    if len(d) < 60:
        return None
    words = max(len(d.split()), 30)
    s_hits, l_hits = {}, {}
    s_sum = l_sum = 0.0
    for name, w, rx in STRICT:
        n = len(rx.findall(d))
        if n:
            s_hits[name] = n
            s_sum += w * min(n, 3)
    for name, w, rx in LOOSE:
        n = len(rx.findall(d))
        if n:
            l_hits[name] = n
            l_sum += w * min(n, 3)
    marker = (s_sum + l_sum) / math.sqrt(words / 100.0)
    # price room
    try:
        prices = json.loads(m["outcomePrices"]) if isinstance(m.get("outcomePrices"), str) else (m.get("outcomePrices") or [])
        p = float(prices[0])
    except Exception:
        p = 0.5
    room = min(p, 1 - p)
    if room < 0.03:
        return None  # no room, kill early
    vol = max(m.get("volumeNum") or 0, 1)
    score = marker * room * math.log10(vol)
    return {
        "score": round(score, 3), "marker": round(marker, 2),
        "s_sum": round(s_sum, 1), "l_sum": round(l_sum, 1),
        "p_yes": round(p, 3), "room": round(room, 3),
        "s_hits": s_hits, "l_hits": l_hits,
    }

def main():
    src, dst = sys.argv[1], sys.argv[2]
    rows = []
    n_in = n_no_desc = n_no_room = 0
    with open(src) as f:
        for line in f:
            m = json.loads(line)
            n_in += 1
            sc = score_one(m)
            if sc is None:
                d = m.get("description") or ""
                if len(d) < 60:
                    n_no_desc += 1
                else:
                    n_no_room += 1
                continue
            m.update(sc)
            rows.append(m)
    rows.sort(key=lambda r: -r["score"])
    with open(dst, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"in={n_in} no_desc={n_no_desc} no_room(p<=0.03|>=0.97)={n_no_room} scored={len(rows)} -> {dst}")

if __name__ == "__main__":
    main()
