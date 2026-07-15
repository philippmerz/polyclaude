#!/usr/bin/env python3
"""Cross-event implication pair discovery over the open-universe crawl.

Classes:
  D  date-chain    : same stem, different deadlines, different events  (by-Mar => by-Dec)
  A_thr threshold  : same asset stem, monotone numeric threshold +/- deadline (hit $200k => hit $150k)
  A_nom nomination : person wins election => person wins nomination/primary (soft implication)
  B  conjunction   : explicit "A and B"/"both" market vs component markets
  C  union         : explicit "A or B" market vs component markets

Emits pairs.jsonl rows:
  {cls, sub, narrow:{...}, broad:{...}, note, mid_n, mid_b, viol_mid_pp, bid_n, ask_b, viol_quote_pp}
For subset semantics: implication narrow => broad, so require P(narrow) <= P(broad).
Violation trade = BUY NO(narrow) + BUY YES(broad), min payout $1.
Conjunction lower bound & union upper bound emitted as 3-leg baskets (cls B_lo / C_hi).
"""
import json, re, sys, unicodedata, datetime, itertools, collections

MONTHS = {m.lower(): i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"])}
MON_RE = "|".join(MONTHS)

STOP = set("will the a an be to of in on at by for and or is are was were do does "
           "did have has had it its this that with as from".split())


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    s = s.lower()
    s = re.sub(r"[^a-z0-9$%.+\- ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load(path):
    rows = []
    for l in open(path):
        m = json.loads(l)
        if not m.get("acceptingOrders"):
            continue
        us = m.get("umaStatuses")
        try:
            us = json.loads(us) if isinstance(us, str) else (us or [])
        except Exception:
            us = []
        if any(x in ("proposed", "disputed", "resolved") for x in us):
            continue
        try:
            op = m.get("outcomePrices")
            op = json.loads(op) if isinstance(op, str) else op
            mid = float(op[0])
        except Exception:
            mid = None
        try:
            toks = json.loads(m["clobTokenIds"]) if isinstance(m.get("clobTokenIds"), str) else m.get("clobTokenIds")
        except Exception:
            toks = None
        rows.append({
            "id": m["id"], "q": m["q"] or "", "slug": m["slug"], "ev": m.get("event_slug") or "",
            "end": m.get("endDate"), "mid": mid,
            "bid": m.get("bestBid"), "ask": m.get("bestAsk"),
            "tok_yes": toks[0] if toks and len(toks) == 2 else None,
            "tok_no": toks[1] if toks and len(toks) == 2 else None,
            "fee": m.get("takerBaseFee") or 0,
            "vol24": m.get("vol24") or 0, "vol": m.get("volumeNum") or 0,
            "liq": m.get("liquidityNum") or 0, "series": m.get("series"),
        })
    return rows


# ---------- deadline parsing ----------
def parse_deadline(qn, end_iso):
    """Return (deadline_date, stem, kind) or None. kind in {'by','in_year'}."""
    end_year = None
    if end_iso:
        try:
            end_year = int(end_iso[:4])
        except Exception:
            pass
    # by/before Month D, YYYY | by Month D | by Month YYYY | by Month
    pat = re.compile(r"\b(by|before|prior to)( the end of)? ((" + MON_RE + r")( (\d{1,2}))?(,? (\d{4}))?|(20\d{2}))\b")
    m = pat.search(qn)
    if m:
        mon, day, yr, bare_yr = m.group(4), m.group(6), m.group(8), m.group(9)
        if bare_yr:  # "by 2027" / "before 2027" => end of prior day-ish; treat as Dec 31 (yr-1) for 'before', Dec 31 yr for 'by'
            y = int(bare_yr)
            if not (2024 <= y <= 2036):
                return None
            d = datetime.date(y - 1, 12, 31) if m.group(1) != "by" else datetime.date(y, 12, 31)
        else:
            y = int(yr) if yr else end_year
            if not y or not (2024 <= y <= 2036):
                return None
            mo = MONTHS[mon]
            if day:
                try:
                    d = datetime.date(y, mo, int(day))
                except ValueError:
                    return None
            else:
                # "by July" = end of July; "before July" = June 30
                if m.group(1) == "before" or m.group(1) == "prior to":
                    prev = mo - 1 or 12
                    d = datetime.date(y - (1 if mo == 1 else 0), prev, 28)
                else:
                    nxt = datetime.date(y + (1 if mo == 12 else 0), (mo % 12) + 1, 1)
                    d = nxt - datetime.timedelta(days=1)
        stem = (qn[:m.start()] + " " + qn[m.end():]).strip()
        return d, stem, "by"
    # by (the) end of YYYY / in YYYY
    m = re.search(r"\b(by|before)( the)? end of (\d{4})\b", qn)
    if m:
        y = int(m.group(3))
        stem = (qn[:m.start()] + " " + qn[m.end():]).strip()
        return datetime.date(y, 12, 31), stem, "by"
    m = re.search(r"\bin (\d{4})\b", qn)
    if m:
        y = int(m.group(1))
        stem = (qn[:m.start()] + " " + qn[m.end():]).strip()
        return datetime.date(y, 12, 31), stem, "in_year"
    return None


def stem_key(stem):
    toks = [t for t in stem.split() if t not in STOP]
    return " ".join(toks)


NEG_RE = re.compile(r"\b(not|no|never|fail to|fails to|without)\b")
# market-level negation only: "will X not IPO", "will no X happen", "never".
# NOT embedded negation: "agrees not to join" (not+to), "no longer under control".
NEG_FLIP_RE = re.compile(r"\bnot\b(?!\s+to\b)|\bnever\b|\bfails? to\b|^(will )?no\b(?! longer)")


def strip_neg(stem):
    """Return (stem_without_negation, negated?). Flip only market-level negations."""
    if "no longer" in stem:
        return stem, False
    m = NEG_FLIP_RE.search(stem)
    if m:
        s2 = NEG_FLIP_RE.sub(" ", stem, count=1)
        return re.sub(r"\s+", " ", s2).strip(), True
    return stem, False


def class_D(rows):
    """Date chains WITH polarity: canonical event stem; negated market's YES == positive market's NO.
    For two positive rows: (A by T1) => (A by T2), T1<T2.
    Mixed polarity valid box: YES(A by T2) + YES(not-A by T1), T1<=T2 (includes T1==T2 complement).
    Represent every row by its effective-YES on the POSITIVE proposition; negated rows flip prices/tokens.
    """
    groups = collections.defaultdict(list)
    for r in rows:
        qn = norm(r["q"])
        pd = parse_deadline(qn, r["end"])
        if not pd:
            continue
        d, stem, kind = pd
        stem2, neg = strip_neg(stem)
        key = stem_key(stem2)
        if len(key) < 8:
            continue
        groups[key].append((d, kind, neg, r))
    pairs = []
    for key, mem in groups.items():
        if len(mem) < 2:
            continue
        for (d1, k1, g1, r1), (d2, k2, g2, r2) in itertools.combinations(mem, 2):
            # order by deadline; on tie (mixed polarity complement) either order works
            (dn, kn, gn, rn), (db, kb, gb, rb) = ((d1, k1, g1, r1), (d2, k2, g2, r2)) if (d1, not g1) <= (d2, not g2) else ((d2, k2, g2, r2), (d1, k1, g1, r1))
            if dn == db:
                # equal effective deadline: duplicate market (same polarity) or complement (mixed)
                sub = "dup" if gn == gb else "compl"
                pairs.append(("D", sub, dict(rn, flip=gn), dict(rb, flip=gb), f"{dn}{'(neg)' if gn else ''}=={db}{'(neg)' if gb else ''}", key))
                continue
            # "in YYYY" windows are calendar buckets: disjoint across years, and a
            # repeatable event breaks in_year=>by-later nesting (window starts differ).
            if kn == "in_year" and kb == "in_year":
                continue  # different years => disjoint, no implication
            if kn == "in_year" and kb == "by":
                continue  # conservative: window-start mismatch for repeatable events
            if kn == "by" and kb == "in_year" and dn.year != db.year:
                continue
            sub = "date" if not (gn or gb) else "date_neg"
            pairs.append(("D", sub, dict(rn, flip=gn), dict(rb, flip=gb), f"{dn}{'(neg)' if gn else ''}->{db}{'(neg)' if gb else ''}", key))
    return pairs


# ---------- numeric threshold ----------
NUM_RE = re.compile(r"\$ ?([0-9][0-9,\.]*) ?(k|m|b|t|thousand|million|billion|trillion)?\b")
UP_WORDS = r"(hit|hits|reach|reaches|touch|touches|close above|closes above|be above|above|exceed|exceeds|surpass|surpasses|at least)"
DOWN_WORDS = r"(dip to|dips to|fall to|falls to|drop to|drops to|close below|closes below|be below|below|less than)"
POINT_WORDS = re.compile(r"\b(close[sd]? (above|below)|at market close|on (" + MON_RE + r")|be (above|below) .* on\b)")


def parse_num(s, suf):
    x = float(s.replace(",", ""))
    mult = {"k": 1e3, "thousand": 1e3, "m": 1e6, "million": 1e6, "b": 1e9,
            "billion": 1e9, "t": 1e12, "trillion": 1e12}.get(suf or "", 1)
    return x * mult


def class_thr(rows):
    groups = collections.defaultdict(list)
    for r in rows:
        qn = norm(r["q"])
        mnum = NUM_RE.search(qn)
        if not mnum:
            continue
        up = re.search(UP_WORDS, qn)
        down = re.search(DOWN_WORDS, qn)
        # explicit (HIGH)/(LOW) markers override the verb (gamma "hit (LOW) $56" = dip to 56)
        if "(low)" in (r["q"] or "").lower() or " low " in qn[:40] and "hit" in qn:
            direction = "down"
        elif "(high)" in (r["q"] or "").lower():
            direction = "up"
        elif up and down:
            continue
        elif up:
            direction = "up"
        elif down:
            direction = "down"
        else:
            continue
        val = parse_num(mnum.group(1), mnum.group(2))
        pd = parse_deadline(qn, r["end"])
        if pd:
            d, stem, kind = pd
        else:
            try:
                d = datetime.date.fromisoformat((r["end"] or "")[:10])
            except Exception:
                continue
            stem, kind = qn, "by"
        point = bool(POINT_WORDS.search(qn))
        # stem: remove the number and direction words for blocking key
        s2 = NUM_RE.sub(" ", stem)
        s2 = re.sub(UP_WORDS if direction == "up" else DOWN_WORDS, " ", s2)
        key = stem_key(re.sub(r"\s+", " ", s2))
        if len(key) < 3:
            continue
        groups[(key, direction)].append((val, d, point, r))
    pairs = []
    for (key, direction), mem in groups.items():
        if len(mem) < 2:
            continue
        for (v1, d1, p1, r1), (v2, d2, p2, r2) in itertools.combinations(mem, 2):
            if v1 == v2 and d1 == d2:
                if p1 == p2 and r1["ev"] != r2["ev"]:
                    # cross-event duplicate threshold market: equality constraint
                    pairs.append(("A_thr", "dup", r1, r2, f"{v1:g}@{d1} == dup", key))
                    pairs.append(("A_thr", "dup", r2, r1, f"{v1:g}@{d1} == dup [rev]", key))
                continue
            # unit-mismatch guard: "$250" vs "$165B" style omissions
            if max(v1, v2) / max(min(v1, v2), 1e-9) > 25:
                continue
            # narrow = harder: higher thr (up) / lower thr (down), earlier-or-equal deadline
            def implies(va, da, pa, vb, db, pb):
                # touch-style a => b if (a harder threshold or equal) and (a deadline <= b) with kinds compatible
                if pa and pb and da != db:
                    return False  # two point-in-time on different dates: no relation
                if pb and not pa:
                    return False  # continuous does not imply point
                if direction == "up":
                    ok_v = va >= vb
                else:
                    ok_v = va <= vb
                ok_d = da <= db
                strict = (va != vb) or (da != db) or (pa and not pb)
                return ok_v and ok_d and strict
            if implies(v1, d1, p1, v2, d2, p2):
                pairs.append(("A_thr", direction, r1, r2, f"{v1:g}@{d1}{'pt' if p1 else ''} => {v2:g}@{d2}{'pt' if p2 else ''}", key))
            elif implies(v2, d2, p2, v1, d1, p1):
                pairs.append(("A_thr", direction, r2, r1, f"{v2:g}@{d2}{'pt' if p2 else ''} => {v1:g}@{d1}{'pt' if p1 else ''}", key))
    return pairs


# ---------- nomination / presidency ----------
def class_nom(rows):
    noms, elecs = {}, {}
    for r in rows:
        qn = norm(r["q"])
        m = re.match(r"^will (.+?) win the (\d{4}) (democratic|republican) (presidential )?nomination", qn)
        if not m:
            m = re.match(r"^will (.+?) be the (\d{4}) (democratic|republican) (presidential )?nominee", qn)
        if m:
            noms[(m.group(1), m.group(2))] = r
            continue
        m = re.match(r"^will (.+?) win the (\d{4}) (us |u\.s\. )?president(ial election|ency)", qn)
        if m:
            elecs.setdefault((m.group(1), m.group(2)), []).append(r)
        # primary => general (same person, same office/state/year)
    pairs = []
    for (person, yr), rl in elecs.items():
        rn = noms.get((person, yr))
        if rn:
            for re_ in rl:
                pairs.append(("A_nom", "pres", re_, rn, f"{person} {yr}: presidency => nomination", person))
    # generic primary->general: person + 'primary' vs person + 'election' minus primary
    prim, gen = collections.defaultdict(list), collections.defaultdict(list)
    for r in rows:
        qn = norm(r["q"])
        m = re.match(r"^will (.+?) win the (\d{4}) (.+?) (primary|primary election)\??$", qn)
        if m:
            prim[(m.group(1), m.group(2))].append((m.group(3), r))
            continue
        m = re.match(r"^will (.+?) win the (\d{4}) (.+?) election\??$", qn)
        if m and "primary" not in m.group(3):
            gen[(m.group(1), m.group(2))].append((m.group(3), r))
    for k in set(prim) & set(gen):
        for (off_p, rp), (off_g, rg) in itertools.product(prim[k], gen[k]):
            # require office overlap (e.g. 'south dakota governor republican' vs 'south dakota governor')
            op = set(off_p.split()) - {"republican", "democratic", "party"}
            og = set(off_g.split())
            if len(op & og) >= max(1, len(og) - 1) and rp["ev"] != rg["ev"]:
                pairs.append(("A_nom", "primary", rg, rp, f"{k[0]} {k[1]}: general({off_g}) => primary({off_p})", k[0]))
    return pairs


# ---------- conjunction / union ----------
def content_toks(qn):
    return frozenset(t for t in qn.split() if t not in STOP and len(t) > 2)


def class_bool(rows):
    # explicit A-and-B / A-or-B questions vs component markets, blocked on rare token overlap
    idx = collections.defaultdict(list)
    for i, r in enumerate(rows):
        for t in content_toks(norm(r["q"])):
            idx[t].append(i)
    pairs = []
    seen = set()
    for r in rows:
        qn = norm(r["q"])
        is_and = bool(re.search(r"\b(and|both|double|all (three|3))\b", qn))
        is_or = bool(re.search(r"\b(either|or)\b", qn))
        # skip numeric-range and/or ("between 5 and 10"), "X or more/greater", "up or down"
        if re.search(r"(between .+ and|or (more|greater|higher|fewer|less|below|above|later|earlier|worse|better|lower)|up or down|\bo/u\b)", qn):
            is_and = is_or = False
        if NEG_RE.search(qn):
            is_and = is_or = False  # negated compounds: semantics flip, punt to manual classes
        if not (is_and or is_or):
            continue
        toks = content_toks(qn)
        if len(toks) < 3:
            continue
        # candidates: markets sharing >=3 content tokens, tokens strictly ~subset of compound's
        cand = collections.Counter()
        for t in toks:
            if len(idx[t]) < 400:
                for i in idx[t]:
                    cand[i] += 1
        comps = []
        for i, n_sh in cand.most_common(40):
            r2 = rows[i]
            if r2["id"] == r["id"] or r2["ev"] == r["ev"]:
                continue
            qn2 = norm(r2["q"])
            if NEG_RE.search(qn2):
                continue
            t2 = content_toks(qn2)
            if not t2 or len(t2 & toks) / len(t2) < 0.92 or len(t2 & toks) < 3:
                continue
            comps.append(r2)
        if not comps:
            continue
        cls = "B" if is_and else "C"
        for r2 in comps[:6]:
            k = (r["id"], r2["id"])
            if k in seen:
                continue
            seen.add(k)
            if cls == "B":
                # A_and_B => component: narrow=compound, broad=component
                pairs.append(("B", "and_sub", r, r2, "conj => component", "bool"))
            else:
                # component => A_or_B: narrow=component, broad=compound
                pairs.append(("C", "or_sup", r2, r, "component => union", "bool"))
    return pairs


def eff(r):
    """Effective-YES view of the canonical positive proposition.
    flip=True: this market's YES is the canonical NO -> mirror prices and tokens."""
    o = dict(r)
    if r.get("flip"):
        o["mid"] = None if r["mid"] is None else 1 - r["mid"]
        o["bid"] = None if r.get("ask") is None else 1 - r["ask"]
        o["ask"] = None if r.get("bid") is None else 1 - r["bid"]
        o["tok_yes"], o["tok_no"] = r["tok_no"], r["tok_yes"]
    return o


def emit(pairs, out):
    n_v = 0
    # complements/duplicates are symmetric: add reversed orientation
    extra = [(cls, sub, rb, rn, note + " [rev]", key) for cls, sub, rn, rb, note, key in pairs
             if sub == "compl" or (sub == "dup" and cls == "D")]
    with open(out, "w") as f:
        for cls, sub, rn0, rb0, note, key in pairs + extra:
            rn, rb = eff(rn0), eff(rb0)
            row = {
                "cls": cls, "sub": sub, "note": note, "key": key,
                "n_id": rn["id"], "n_q": rn["q"], "n_ev": rn["ev"], "n_slug": rn["slug"],
                "b_id": rb["id"], "b_q": rb["q"], "b_ev": rb["ev"], "b_slug": rb["slug"],
                "n_flip": bool(rn0.get("flip")), "b_flip": bool(rb0.get("flip")),
                "mid_n": rn["mid"], "mid_b": rb["mid"],
                "bid_n": rn["bid"], "ask_n": rn["ask"], "bid_b": rb["bid"], "ask_b": rb["ask"],
                "fee_n": rn["fee"], "fee_b": rb["fee"],
                "vol24_n": rn["vol24"], "vol24_b": rb["vol24"],
                "tok_yes_n": rn["tok_yes"], "tok_no_n": rn["tok_no"],
                "tok_yes_b": rb["tok_yes"], "tok_no_b": rb["tok_no"],
                "end_n": rn["end"], "end_b": rb["end"],
                "cross_event": rn["ev"] != rb["ev"],
            }
            if rn["mid"] is not None and rb["mid"] is not None:
                row["viol_mid_pp"] = round((rn["mid"] - rb["mid"]) * 100, 2)
            if rn.get("bid") is not None and rb.get("ask") is not None:
                # crossable on gamma quotes iff (effective) bid_n > ask_b
                row["viol_quote_pp"] = round((rn["bid"] - rb["ask"]) * 100, 2)
            f.write(json.dumps(row) + "\n")
            if row.get("viol_mid_pp", -1) > 0:
                n_v += 1
    return n_v


def main():
    rows = load("/tmp/implication_study/open_universe.jsonl")
    print(f"# loaded {len(rows)} live orderable binary markets", file=sys.stderr)
    all_pairs = []
    for fn, name in [(class_D, "D"), (class_thr, "A_thr"), (class_nom, "A_nom"), (class_bool, "B/C")]:
        ps = fn(rows)
        cx = sum(1 for p in ps if p[2]["ev"] != p[3]["ev"])
        print(f"# class {name}: {len(ps)} pairs ({cx} cross-event)", file=sys.stderr)
        all_pairs.extend(ps)
    nv = emit(all_pairs, "/tmp/implication_study/pairs.jsonl")
    print(f"# total {len(all_pairs)} pairs, {nv} with mid violation > 0 -> pairs.jsonl", file=sys.stderr)


if __name__ == "__main__":
    main()
