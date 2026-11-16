"""Report tables: every number in report/REPORT.md comes from this script (plus scripts/gap_analysis.py).

Reads: data/schools.csv, data/requirements.csv, phase2/courses/<id>.json, phase3/classified/<id>.json,
       phase2/graduation_requirements.csv, phase3/profiles.csv, phase4/gap_by_school.csv
Writes (phase4/):
  possible_typed.csv        every 'possible' mapping with a reason category (why it is not 'strong')
  sensitivity_by_school.csv school x plan x requirement status under Strict / Moderate / Loose thresholds
  sensitivity_summary.csv   schools meeting each requirement / all requirements under each threshold
  missing_subjects.csv      school x area where nothing at all maps (+ nearest substitute)
  thin_coverage.csv         school x requirement met by exactly one strong course (single point of failure)
  below_alg1.csv            math courses below Algebra I level (name/description patterns)
  electives_by_school.csv   courses that map to no requirement (pure electives) by type, per school
  interdisciplinary.csv     interdisciplinary / bridging / multi-area courses
  credit_sizes.csv          share of courses offered as 0.25 / 0.5 / 1.0 credit, per subject area
  local_vs_proposed.csv     local graduation credits per area vs both proposals
  integrated_math.csv       schools using integrated math sequences and ALG1/GEOM status under 3 rules
  claims_disputed.csv       catalog claims not supported by the content mapping
  school_facts.json         per-school bundle used to draft Appendix A

Run:  python3 -I scripts/report_tables.py
"""
import csv, glob, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "phase4"
PLANS = {"complete_2033": "Complete (Class of 2033+)", "transitional_2031_32": "Transitional (2031-32)"}
NOT_ASSESSABLE = {"oxbow-union-high-school": "no course list (Canva catalog)",
                  "mill-river-union-high-school": "titles only",
                  "rivendell-academy": "titles only",
                  "cabot-school": "16-course partial catalog"}


def w(name, rows, fields=None):
    if not rows:
        return
    with (OUT / name).open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields or list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ---------- reason a mapping is 'possible' rather than 'strong' ----------
R = lambda p: re.compile(p, re.I)
REASONS = [
    ("support course", R(r"strategic (algebra|geometry|reader)|\blab or\b|support course|reteach|concurrently|read 180|writing lab|support lab")),
    ("split sequence", R(r"part [ab12]\b|part i{1,2}\b|\b1a\b|\b1b\b|algebra 1[ab]\b|by 2 years|two trimesters|algebra b\b|multi-(year|part)|two-part|first half|second half|sequence part")),
    ("integrated math", R(r"integrated (math|algebra)|\bint\. math|\bmath [12ab]\b|core math|\bags\b|math [ab] honors")),
    ("applied / technical crossover", R(r"robot|programm|coding|engineer|wood|furniture|jrotc|forensic|cnc|\bweb\b|php|python|computer|technolog|culinary|construction|welding|automotive")),
    ("below level / applied", R(r"intervention|direct (math )?instruction|iep|plan-determined|below|essentials|functional|consumer math|applied|practical|basic |fundamental|foundations|life skills|pre-vocational|skills in|direct instruction|adulting|special-program|modified")),
    ("embedded content", R(r"embedded|within|combined|civics/economics|one listed topic|unit\b|mentions|includes")),
    ("interdisciplinary / project", R(r"interdisciplinary|community-based|community based|project|flexible|pathway|place-based|cbl|humanities")),
    ("unclear description", R(r"grades not stated|title only|not described|unconfirmed|description missing|not stated|depends on")),
    ("adjacent content", R(r"environment|ecolog|anatomy|marine|forest|natural|wildlife|nutrition|narrow|elective|topic|supplement|geolog|climate|astronom|agricultur|law|film|journal|poetry|philosoph|book|yearbook|writing|culture|genocide|cartograph|sport|integrated science|unified|annex|alternative|athletic|dance|theat|acting|government|politic|econom|psycholog|fitness|yoga|outdoor|music|art\b|media|photo|lit\b|literature|speech|debate|history|geograph|mixed domains|several domains|overlap|possible")),
]
MODERATE = {"split sequence", "integrated math", "adjacent content", "unclear description", "interdisciplinary / project",
            "applied / technical crossover"}


def reason(course, cl, m):
    txt = " ".join([course.get("course_name") or "", m.get("rationale") or ""])
    if cl.get("subject_area") == "Interdisciplinary" or cl.get("bridges"):
        if not R(r"support|strategic").search(txt):
            return "interdisciplinary / project"
    if cl.get("finlit_type") == "embedded" and m.get("requirement_id") == "FINLIT":
        return "embedded content"
    for name, rx in REASONS:
        if rx.search(txt):
            return name
    return "other"


BELOW_ALG1 = R(r"pre-?algebra|essentials|foundation|fundamental|workplace|consumer|business math|applied math|math lab|"
               r"practical|functional|life skills math|basic math|general math|everyday|math skills|transition math|"
               r"math concepts|math applications|\bpre-?vocational|numeracy")
AREA_OF = {"WL": "World Language", "HEALTH": "Health", "FINLIT": "Financial Literacy", "SS-CIVICS": "Civics",
           "SCI-EARTH": "Earth/Space Science", "PE": "Physical Education", "ARTS": "Arts"}
NEAR = {"SCI-EARTH": R(r"environment|earth|geo|climate|physical science|ecolog|astronom|natural|weather|ocean"),
        "SS-CIVICS": R(r"government|civic|u\.?s\.? history|american|law|politic"),
        "WL": R(r"language|spanish|french|culture|esl|ell"),
        "HEALTH": R(r"wellness|health|nutrition|fitness"), "FINLIT": R(r"econom|finance|consumer|business"),
        "PE": R(r"fitness|wellness|sport|physical"), "ARTS": R(r"art|music|design|theat|media")}


def load():
    schools = {r["school_id"]: r for r in csv.DictReader((ROOT / "data/schools.csv").open())}
    reqs = [r for r in csv.DictReader((ROOT / "data/requirements.csv").open()) if r["requirement_id"] not in ("TOTAL", "ELECTIVE")]
    profiles = {r["school_id"]: r for r in csv.DictReader((ROOT / "phase3/profiles.csv").open())}
    gap = list(csv.DictReader((OUT / "gap_by_school.csv").open()))
    data = {}
    for f in sorted(glob.glob(str(ROOT / "phase2/courses/*.json"))):
        sid = Path(f).stem
        src = json.loads(Path(f).read_text())
        cp = ROOT / "phase3/classified" / f"{sid}.json"
        cl = json.loads(cp.read_text())["courses"] if cp.exists() else []
        data[sid] = (src, list(zip(src["courses"], cl)))
    return schools, reqs, profiles, gap, data


def band(n):
    n = num(n) or 0
    return "under 200" if n < 200 else "200-399" if n < 400 else "400-799" if n < 800 else "800+"


def main():
    schools, reqs, profiles, gap, data = load()
    facts = defaultdict(dict)

    # ---- possible_typed ----
    ptyped = []
    for sid, (src, pairs) in data.items():
        for i, (s, c) in enumerate(pairs):
            if s.get("level") == "CTE" or c.get("other_type") == "CTE program":
                continue
            for m in c.get("credit_mappings") or []:
                if m.get("strength") == "possible" and m.get("requirement_id") != "FLEX-ANY":
                    ptyped.append({"school_id": sid, "school_name": src["school_name"], "course_index": i,
                                   "course_name": s.get("course_name"), "requirement_id": m["requirement_id"],
                                   "reason": reason(s, c, m), "rationale": m.get("rationale"),
                                   "subject_area": c.get("subject_area"), "bridges": c.get("bridges") or "",
                                   "credits": s.get("credits"), "description": (s.get("description") or "")[:600]})
    w("possible_typed.csv", ptyped)
    by_sr = defaultdict(list)
    for p in ptyped:
        by_sr[(p["school_id"], p["requirement_id"])].append(p)

    # ---- sensitivity ----
    sens, summ = [], defaultdict(Counter)
    full = defaultdict(lambda: defaultdict(set))
    for g in gap:
        sid, rid, plan = g["school_id"], g["requirement_id"], g["plan"]
        if sid in NOT_ASSESSABLE:
            continue
        st = g["status"]
        ps = by_sr[(sid, rid if rid != "PE-HEALTH-COMBINED" else "HEALTH")]
        if rid == "MATH-PATHWAY":
            ps = ps + by_sr[(sid, "MATH-STATS-ALG2")]
        tiers = {}
        tiers["strict"] = st == "covered"
        tiers["moderate"] = tiers["strict"] or (st in ("possible_only", "gap") and any(p["reason"] in MODERATE for p in ps))
        tiers["loose"] = tiers["strict"] or (st in ("possible_only", "gap") and bool(ps))
        row = {"school_id": sid, "school_name": g["school_name"], "plan": plan, "requirement_id": rid, "status": st,
               **{t: "met" if v else "not met" for t, v in tiers.items()},
               "possible_reasons": "; ".join(sorted({p["reason"] for p in ps})),
               "possible_examples": "; ".join(sorted({p["course_name"] for p in ps})[:4])}
        sens.append(row)
        for t, v in tiers.items():
            summ[(plan, rid)][t] += v
            if not v:
                full[plan][t].add(sid)
    w("sensitivity_by_school.csv", sens)
    n_ass = len([s for s in data if s not in NOT_ASSESSABLE and data[s][1]])
    srows = []
    for (plan, rid), c in summ.items():
        srows.append({"plan": plan, "requirement_id": rid, "strict": c["strict"], "moderate": c["moderate"], "loose": c["loose"], "of": n_ass})
    for plan in PLANS.values():
        srows.append({"plan": plan, "requirement_id": "ALL REQUIREMENTS",
                      **{t: n_ass - len(full[plan][t]) for t in ("strict", "moderate", "loose")}, "of": n_ass})
    w("sensitivity_summary.csv", srows)

    # ---- missing subjects + thin coverage ----
    missing, thin = [], []
    gidx = {(g["school_id"], g["plan"], g["requirement_id"]): g for g in gap}
    for sid, (src, pairs) in data.items():
        if sid == "oxbow-union-high-school" or not pairs:
            continue
        for rid, area in AREA_OF.items():
            g = gidx.get((sid, PLANS["complete_2033"], rid))
            if g and g["status"] in ("gap",) or (g and g["status"] == "unknown" and sid in NOT_ASSESSABLE and g["strong_courses"] == "0" and g["possible_courses"] == "0"):
                near = [s.get("course_name") for s, c in pairs if s.get("level") != "CTE" and NEAR[rid].search((s.get("course_name") or "") + " " + (s.get("description") or "")[:200])]
                missing.append({"school_id": sid, "school_name": src["school_name"], "area": area, "requirement_id": rid,
                                "enrollment_2024": schools.get(sid, {}).get("enrollment_2024"),
                                "size_band": band(schools.get(sid, {}).get("enrollment_2024")),
                                "data_confidence": "low" if sid in NOT_ASSESSABLE else "normal",
                                "nearest_substitutes": "; ".join(near[:5])})
        for g in gap:
            if g["school_id"] == sid and g["plan"] == PLANS["complete_2033"] and g["status"] == "covered" and g["strong_courses"] == "1" \
                    and g["requirement_id"] not in ("ELA-INTRO", "ELA-MASTERY"):
                thin.append({"school_id": sid, "school_name": src["school_name"], "requirement_id": g["requirement_id"], "only_course": g["examples"]})
    w("missing_subjects.csv", missing, ["school_id", "school_name", "area", "requirement_id", "enrollment_2024", "size_band", "data_confidence", "nearest_substitutes"])
    w("thin_coverage.csv", thin)

    # ---- below algebra I ----
    below = []
    for sid, (src, pairs) in data.items():
        for s, c in pairs:
            if s.get("level") == "CTE" or c.get("subject_area") != "Mathematics":
                continue
            name = s.get("course_name") or ""
            if re.search(r"financial algebra|algebra (i|1)\b.*foundation", name, re.I):
                continue
            if BELOW_ALG1.search(name) or re.search(r"below (high school|grade)|pre-algebra|arithmetic", (s.get("description") or ""), re.I) and not re.search(r"algebra (ii|2)|geometry|calculus|statistic", name, re.I):
                strong_core = {m["requirement_id"] for m in c.get("credit_mappings") or [] if m.get("strength") == "strong"} & {"MATH-ALG1", "MATH-GEOM", "MATH-STATS-ALG2"}
                if strong_core or re.search(r"calculus|statistic|algebra (ii|2)|geometry|integrated math (ii|iv|2|3|4)", name, re.I):
                    continue
                maps = "; ".join(f'{m["requirement_id"]}:{m["strength"]}' for m in c.get("credit_mappings") or [])
                below.append({"school_id": sid, "school_name": src["school_name"], "course_name": name, "credits": s.get("credits"),
                              "grade_levels": s.get("grade_levels"), "mappings": maps, "fulfills_text": s.get("fulfills_text") or "",
                              "description": (s.get("description") or "")[:500]})
    w("below_alg1.csv", below)

    # ---- electives ----
    erows = []
    for sid, (src, pairs) in data.items():
        if not pairs:
            continue
        cnt, total, typ = 0, 0, Counter()
        names = defaultdict(list)
        for s, c in pairs:
            if s.get("level") == "CTE" or c.get("other_type") in ("CTE program", "Advisory/Support"):
                continue
            total += 1
            maps = [m for m in c.get("credit_mappings") or [] if m.get("requirement_id") != "FLEX-ANY"]
            if not maps and c.get("other_type") != "Flexible pathway":
                cnt += 1
                t = c.get("other_type") or c.get("subject_area") or "Other"
                typ[t] += 1
                names[t].append(s.get("course_name"))
        erows.append({"school_id": sid, "school_name": src["school_name"], "courses": total, "pure_electives": cnt,
                      "share": round(cnt / total, 2) if total else "",
                      **{f"n_{k}": typ[k] for k in ["Technology/Engineering", "Business", "Family & Consumer Science", "Computer Science", "Social Studies", "ELA", "Arts", "Science", "Mathematics", "PE & Health", "Other"]},
                      "examples": "; ".join(f"{k}: " + ", ".join(v[:3]) for k, v in sorted(names.items(), key=lambda kv: -len(kv[1]))[:4])})
        facts[sid]["electives"] = {"pure": cnt, "total": total, "by_type": dict(typ.most_common(6)), "examples": {k: v[:4] for k, v in names.items()}}
    w("electives_by_school.csv", erows)

    # ---- interdisciplinary + multi-area + credit sizes ----
    AREAW = R(r"\b(english|ela|math|science|social studies|history|arts?|health|physical education|world language|financial|civics)\b")
    irows, sizes = [], defaultdict(Counter)
    for sid, (src, pairs) in data.items():
        for s, c in pairs:
            if s.get("level") == "CTE" or c.get("other_type") == "CTE program":
                ft = s.get("fulfills_text") or ""
                if len({x.lower() for x in AREAW.findall(ft)}) >= 1 and re.search(r"credit", ft, re.I):
                    irows.append({"school_id": sid, "school_name": src["school_name"], "course_name": s.get("course_name"), "kind": "CTE embedded credit",
                                  "bridges": "", "requirements": "", "credits": s.get("credits"), "fulfills_text": ft, "description": (s.get("description") or "")[:400]})
                continue
            cr = num(s.get("credits"))
            if cr:
                sizes[c.get("subject_area") or "Other"][cr] += 1
            strong = sorted({m["requirement_id"] for m in c.get("credit_mappings") or [] if m.get("strength") == "strong" and m["requirement_id"] != "FLEX-ANY"})
            areas_ft = {x.lower() for x in AREAW.findall(s.get("fulfills_text") or "")}
            kind = None
            if c.get("subject_area") == "Interdisciplinary" or c.get("bridges"):
                kind = "interdisciplinary"
            elif len({r.split("-")[0] for r in strong}) >= 2:
                kind = "multi-area strong mapping"
            elif len(areas_ft) >= 2 and re.search(r"credit", s.get("fulfills_text") or "", re.I):
                kind = "catalog states credit in 2+ areas"
            if kind:
                irows.append({"school_id": sid, "school_name": src["school_name"], "course_name": s.get("course_name"), "kind": kind,
                              "bridges": c.get("bridges") or "", "requirements": "; ".join(strong), "credits": s.get("credits"),
                              "fulfills_text": s.get("fulfills_text") or "", "description": (s.get("description") or "")[:400]})
    w("interdisciplinary.csv", irows)
    srows2 = []
    for area, c in sorted(sizes.items()):
        n = sum(c.values())
        srows2.append({"subject_area": area, "courses_with_credits": n, "quarter_or_less": sum(v for k, v in c.items() if k <= 0.25),
                       "half": c[0.5], "one": c[1.0], "more_than_one": sum(v for k, v in c.items() if k > 1)})
    w("credit_sizes.csv", srows2)

    # ---- local vs proposed ----
    BUCKET = [("PEH", r"health/phys|physical education (&|and) health|wellness \(physical|pe/health"),
              ("HEALTH", r"^health|facs/health|^wellness$"), ("PE", r"^physical education$|^pe$"),
              ("ELECTIVE", r"elective|additional (choice|classes|credits)|choice courses|approved electives"),
              ("FINLIT", r"financial|personal finance"), ("WL", r"language acquisition|world lang|foreign lang|non-native"),
              ("ELA", r"english|literacy|language and literature"), ("MATH", r"^math|mathematical"),
              ("SCI", r"^science|^sciences|scientific"), ("SS", r"social|global|civics|history|government|individuals"),
              ("ARTS", r"art|music|performance|creative"),
              ("LOCAL", r"practical|technology|computer|life skills|business|consumer|capstone|senior|service|rise|theory of knowledge|transferable|pipelines|seminar")]
    PROP = {"complete_2033": {"ELA": 4, "MATH": 4, "SCI": 3, "SS": 3, "ARTS": 1.5, "WL": 1, "FINLIT": .5, "PE": 1.5, "HEALTH": 1, "PEH": 2.5, "ELECTIVE": 3},
            "transitional_2031_32": {"ELA": 4, "MATH": 3, "SCI": 3, "SS": 3, "ARTS": 1.5, "WL": 0, "FINLIT": .5, "PE": None, "HEALTH": None, "PEH": 1.5, "ELECTIVE": 6}}
    UNIT_FACTOR = {"brattleboro-union-high-school": 0.25}
    UNIT_NOTE = {"poultney-high-school": "semester block course = 1 credit", "proctor-junior-senior-high-school": "semester block course = 1 credit",
                 "west-rutland-school": "semester block course = 1 credit", "peoples-academy": "semester class = 1 credit; unit unclear",
                 "brattleboro-union-high-school": "BUHS units / 4", "danville-school": "counted in semesters (42); not converted"}
    grs = list(csv.DictReader((ROOT / "phase2/graduation_requirements.csv").open()))
    local = defaultdict(lambda: defaultdict(float))
    other_local = defaultdict(list)
    totals = {}
    for g in grs:
        sid = g["school_id"]
        p = profiles.get(sid, {})
        if sid == "green-mountain-union-high-school" and "Class of 2028" not in (g.get("notes") or ""):
            continue   # catalog prints two cohorts; keep the later one
        # Unit factors to standard (year-course) credits. Only Brattleboro is converted: 4 BUHS units = one semester
        # block course = one year of traditional seat time. Quarry Valley schools and Peoples Academy count a semester
        # course as 1 credit on block schedules; they are left as printed and flagged (UNIT_NOTE).
        fac = UNIT_FACTOR.get(sid, 1.0)
        lt = num(g["total_credits"])
        lc = lt * fac if lt else None
        totals[sid] = (num(g["total_credits"]), lc or (num(g["total_credits"]) * fac if num(g["total_credits"]) else None), fac)
        a = g["area"].strip()
        cr = num(g["credits"])
        b = next((k for k, rx in BUCKET if re.search(rx, a, re.I)), None)
        if b in ("SS",) and re.search(r"world language", a, re.I):
            b = "SS"
        if b == "LOCAL" or (b is None and cr):
            other_local[sid].append(f"{a} {g['credits']}".strip())
            continue
        if b and cr is not None:
            local[sid][b] += cr * fac
    lrows = []
    for sid in sorted(local):
        L = dict(local[sid])
        if "PE" in L or "HEALTH" in L:
            L["PEH"] = L.get("PEH", 0) + L.get("PE", 0) + L.get("HEALTH", 0)
        row = {"school_id": sid, "school_name": data.get(sid, ({"school_name": sid},))[0]["school_name"],
               "local_total_stated": totals[sid][0], "local_total_std_credits": round(totals[sid][1], 2) if totals[sid][1] else "",
               "unit_factor": round(totals[sid][2], 3), "unit_note": UNIT_NOTE.get(sid, ""), "grading": profiles.get(sid, {}).get("grading_system"),
               "local_only_requirements": "; ".join(other_local.get(sid, []))}
        for k in ["ELA", "MATH", "SCI", "SS", "ARTS", "WL", "FINLIT", "PE", "HEALTH", "PEH", "ELECTIVE"]:
            row[f"local_{k}"] = round(L[k], 2) if k in L else ""
        lrows.append(row)
        facts[sid]["local"] = row
    w("local_vs_proposed.csv", lrows)

    # ---- integrated math ----
    INTEG = R(r"integrated math|\bint\. math|^math [12ab]\b|^math [ab] honors|core math|\bags \d|^math 1 by|integrated algebra")
    im = []
    for sid, (src, pairs) in data.items():
        names = [s.get("course_name") for s, c in pairs if c.get("subject_area") == "Mathematics" and INTEG.search(s.get("course_name") or "")]
        if not names:
            continue
        st = {rid: gidx.get((sid, PLANS["complete_2033"], rid), {}).get("status") for rid in ("MATH-ALG1", "MATH-GEOM")}
        has_trad = {rid: any(R(pat).search(s.get("course_name") or "") and not INTEG.search(s.get("course_name") or "") for s, c in pairs)
                    for rid, pat in (("MATH-ALG1", r"^algebra (i|1)\b(?!i)"), ("MATH-GEOM", r"^(honors )?geometry"))}
        im.append({"school_id": sid, "school_name": src["school_name"], "integrated_courses": "; ".join(names[:6]),
                   "alg1_status": st["MATH-ALG1"], "geom_status": st["MATH-GEOM"],
                   "also_offers_traditional_alg1": has_trad["MATH-ALG1"], "also_offers_traditional_geom": has_trad["MATH-GEOM"]})
    w("integrated_math.csv", im)

    # ---- catalog claims disputed ----
    claims = []
    for sid, (src, pairs) in data.items():
        for s, c in pairs:
            cc = c.get("catalog_claims") or []
            if not cc:
                continue
            mapped = {m["requirement_id"] for m in c.get("credit_mappings") or []}
            for claim in cc:
                rid = claim if isinstance(claim, str) else claim.get("requirement_id")
                if rid and rid not in mapped and rid != "FLEX-ANY":
                    claims.append({"school_id": sid, "school_name": src["school_name"], "course_name": s.get("course_name"),
                                   "claimed": rid, "content_mapping": "; ".join(sorted(mapped)) or "(none)",
                                   "fulfills_text": s.get("fulfills_text") or "", "description": (s.get("description") or "")[:400]})
    w("claims_disputed.csv", claims)

    # ---- school facts ----
    for sid, (src, pairs) in data.items():
        f = facts[sid]
        f["school"] = schools.get(sid, {})
        f["profile"] = profiles.get(sid, {})
        f["catalog_year"] = (src.get("courses") or [{}])[0].get("catalog_school_year") if src.get("courses") else None
        f["n_courses"] = sum(1 for s, c in pairs if s.get("level") != "CTE")
        f["n_cte"] = sum(1 for s, c in pairs if s.get("level") == "CTE")
        f["gap"] = {g["plan"] + "|" + g["requirement_id"]: {k: g[k] for k in ("status", "strong_courses", "possible_courses", "examples", "alt_year_only")} for g in gap if g["school_id"] == sid}
        f["sens"] = [r for r in sens if r["school_id"] == sid and r["plan"] == PLANS["complete_2033"] and r["strict"] == "not met"]
        f["possible"] = [{k: p[k] for k in ("course_name", "requirement_id", "reason", "rationale")} for p in ptyped if p["school_id"] == sid]
        f["below_alg1"] = [b["course_name"] for b in below if b["school_id"] == sid]
        f["missing"] = [m["area"] for m in missing if m["school_id"] == sid]
        f["thin"] = [(t["requirement_id"], t["only_course"]) for t in thin if t["school_id"] == sid]
        f["interdisciplinary"] = [(r["course_name"], r["kind"]) for r in irows if r["school_id"] == sid]
        f["claims"] = [(r["course_name"], r["claimed"]) for r in claims if r["school_id"] == sid]
        f["integrated"] = next((r for r in im if r["school_id"] == sid), None)
        f["disclosure"] = {k: round(sum(1 for s, c in pairs if s.get("level") != "CTE" and s.get(k)) / max(1, f["n_courses"]), 2)
                           for k in ("fulfills_text", "prerequisites", "credits", "grade_levels")}
        f["science"] = Counter(c.get("science_domain") for s, c in pairs if c.get("subject_area") == "Science" and s.get("level") != "CTE")
        f["labs"] = [sum(1 for s, c in pairs if c.get("subject_area") == "Science" and s.get("level") != "CTE" and c.get("has_lab") in (True, "yes", "true")),
                     sum(1 for s, c in pairs if c.get("subject_area") == "Science" and s.get("level") != "CTE")]
    (OUT / "school_facts.json").write_text(json.dumps(facts, indent=1, default=str, ensure_ascii=False))

    # ---- console summary ----
    print("assessable schools:", n_ass)
    for r in srows:
        print(f'{r["plan"][:12]:<13}{r["requirement_id"]:<20}{r["strict"]:>4}{r["moderate"]:>4}{r["loose"]:>4}')
    print("possible reasons:", Counter(p["reason"] for p in ptyped).most_common())
    print("missing:", [(m["school_name"], m["area"]) for m in missing])
    print("thin:", len(thin), Counter(t["requirement_id"] for t in thin).most_common())
    print("below alg1:", len(below), Counter(b["school_name"] for b in below).most_common(12))
    print("interdisc:", Counter(r["kind"] for r in irows))
    print("integrated:", [(r["school_name"], r["alg1_status"], r["geom_status"], r["also_offers_traditional_alg1"]) for r in im])
    print("claims disputed:", len(claims), "courses:", len({(c["school_id"], c["course_name"]) for c in claims}),
          Counter(c["claimed"] for c in claims).most_common())


if __name__ == "__main__":
    main()
