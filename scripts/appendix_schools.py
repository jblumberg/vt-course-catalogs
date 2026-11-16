"""Appendix A of the report: one section per high school, generated from phase4/school_facts.json and the
phase4 tables (run scripts/gap_analysis.py and scripts/report_tables.py first).

Writes report/appendix_schools.md. Every sentence is built from the data so it can be regenerated when catalogs change.
Run:  python3 -I scripts/appendix_schools.py
"""
import csv, json, re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C, T = "Complete (Class of 2033+)", "Transitional (2031-32)"
LABEL = {"ELA-INTRO": "ELA Intro", "ELA-MASTERY": "ELA Mastery", "MATH-ALG1": "Algebra I", "MATH-GEOM": "Geometry",
         "MATH-PATHWAY": "Math Pathway", "MATH-STATS-ALG2": "Stats/Alg II", "SCI-PHYS": "Physical Sci", "SCI-LIFE": "Life Sci",
         "SCI-EARTH": "Earth/Space", "SS-USHIST": "US History", "SS-CIVICS": "Civics", "SS-WORLD": "World Studies", "ARTS": "Arts",
         "WL": "World Language", "FINLIT": "Fin Lit", "PE": "PE", "HEALTH": "Health", "PE-HEALTH-COMBINED": "PE/Health 1.5"}
NOT_ASSESSABLE = {"oxbow-union-high-school": "Oxbow's catalog is a Canva design; only graduation requirements could be read, so no course analysis is possible.",
                  "mill-river-union-high-school": "Mill River's catalog lists course titles only (descriptions are in ~150 linked syllabi), so classifications are from titles and are low-confidence.",
                  "rivendell-academy": "Rivendell lists course titles only (descriptions are on ~60 Google Site pages), so classifications are from titles and are low-confidence.",
                  "cabot-school": "Cabot's catalog on file is a 16-course partial; absences below are data gaps, not findings."}


def short(name):
    return re.sub(r"\s+(Union )?(Middle(/| and | & )High School|Middle/High School|Junior/Senior High School|Senior (Union )?High School|High School|Schools?|Middle High School|Middle & High School)$", "", name)


def first_sentences(text, n=260):
    text = (text or "").strip()
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0]
    return cut + " …"


def main():
    facts = json.loads((ROOT / "phase4/school_facts.json").read_text())
    p1 = {r["school_id"]: r for r in csv.DictReader((ROOT / "phase1/catalogs.csv").open())}
    ptyped = defaultdict(list)
    for r in csv.DictReader((ROOT / "phase4/possible_typed.csv").open()):
        ptyped[r["school_id"]].append(r)
    cte = defaultdict(list)
    for r in csv.DictReader((ROOT / "phase4/interdisciplinary.csv").open()):
        if r["kind"] == "CTE embedded credit":
            cte[r["school_id"]].append(r)
    out = ["## Appendix A — School-by-school analysis", "",
           "**One section per school, in alphabetical order.** Each section gives the school's profile, its coverage under both plans, "
           "and the implementation issues specific to it, quoting course descriptions where they illustrate a decision. "
           "\"Covered\" means at least one course clearly qualifies (*strong*). \"Possible only\" means the school's closest courses depend on an "
           "AOE definition. Counts are catalog offerings, not sections run.", ""]
    for sid in sorted(facts, key=lambda s: facts[s]["school"].get("school_name") or s):
        f = facts[sid]
        sc, pr, loc = f["school"], f["profile"], f.get("local") or {}
        name = sc.get("school_name") or sid
        yr = (p1.get(sid) or {}).get("school_year") or f.get("catalog_year") or "year not stated"
        grading = (pr.get("grading_system") or "not stated").replace("_", " ")
        tot = loc.get("local_total_std_credits") or pr.get("local_total") or "not stated"
        unit = f" ({loc['unit_note']})" if loc.get("unit_note") else ""
        out.append(f"### {name}")
        out.append(f"*{sc.get('town')} · {sc.get('su_sd')} · grades {sc.get('grades')}, {sc.get('enrollment_2024')} students (2024-25) · "
                   f"catalog {yr} · {f['n_courses']} courses listed · grading: {grading} · local total: {tot}{unit}*")
        out.append("")
        if sid in NOT_ASSESSABLE and sid == "oxbow-union-high-school":
            out.append(NOT_ASSESSABLE[sid] + f" Local requirements: {tot} credits including Health 0.5, which is short of the Complete plan's 1.0.")
            out.append("")
            continue
        g = f["gap"]
        def stat(plan):
            items = {k.split("|", 1)[1]: v for k, v in g.items() if k.startswith(plan)}
            cov = sum(1 for v in items.values() if v["status"] == "covered")
            other = [(r, v) for r, v in items.items() if v["status"] != "covered"]
            return cov, len(items), other
        cc, cn, cother = stat(C)
        tc, tn, tother = stat(T)
        def fmt(other):
            if sid in NOT_ASSESSABLE:
                unk = [r for r, v in other if v["status"] == "unknown"]
                rest = [(r, v) for r, v in other if v["status"] != "unknown"]
                return (f"{len(unk)} unknown (data incomplete)" if unk else "") + ("; " if unk and rest else "") + \
                    "; ".join(f"{LABEL.get(r, r)} \u2013 {v['status'].replace('_', ' ')}" for r, v in rest)
            return "; ".join(f"{LABEL.get(r, r)} – {v['status'].replace('_', ' ')}" + (f" ({v['examples'][:70]})" if v["examples"] else "") for r, v in other) or "none"
        out.append(f"**Coverage.** Complete plan: **{cc} of {cn}** requirements clearly covered. Not covered: {fmt(cother)}.  ")
        out.append(f"Transitional plan: **{tc} of {tn}**." + ("" if not tother else f" Not covered: {', '.join(LABEL.get(r, r) for r, v in tother)}."))
        out.append("")
        issues = []
        if sid in NOT_ASSESSABLE:
            issues.append(f"**Data incomplete.** {NOT_ASSESSABLE[sid]}")
        st = {k.split("|", 1)[1]: v for k, v in g.items() if k.startswith(C)}
        stt = {k.split("|", 1)[1]: v for k, v in g.items() if k.startswith(T)}
        poss = defaultdict(list)
        for p in ptyped[sid]:
            poss[p["requirement_id"]].append(p)
        def courses(rid, k=3):
            return ", ".join(f"*{p['course_name']}*" for p in poss[rid][:k])
        h = st.get("HEALTH", {})
        if h.get("status") == "short":
            peh = stt.get("PE-HEALTH-COMBINED", {}).get("status")
            issues.append(f"**Health.** Offers {h['examples'] or 'a Health course'} at less than 1.0 credit; the Complete plan needs a second Health semester for every student"
                          + ("; the Transitional 1.5 PE/Health is met." if peh == "covered" else "; the Transitional 1.5 PE/Health is also short."))
        elif h.get("status") == "possible_only":
            issues.append(f"**Health.** Health content sits inside combined courses ({courses('HEALTH')}); whether a Wellness course counts is undefined.")
        if st.get("PE", {}).get("status") == "short":
            issues.append(f"**PE.** Offers less than 1.5 PE credit in clearly qualifying courses ({st['PE']['examples']}).")
        e = st.get("SCI-EARTH", {})
        if e.get("status") == "possible_only":
            issues.append(f"**Earth/Space depends on the Environmental Science decision.** Closest courses: {courses('SCI-EARTH', 4)}.")
        elif e.get("status") == "short":
            issues.append(f"**Earth/Space is a semester only** ({e['examples']}); a full credit needs a second semester or a split-credit rule.")
        elif e.get("status") == "gap":
            issues.append("**No Earth/Space course.** Earth content is taught inside another course (see Theme 1); without a split-credit rule the school needs a new course and staff.")
        for t in f["thin"]:
            if t[0] == "SCI-EARTH" and re.search(r"astronom|space physics|rocket", t[1], re.I):
                issues.append(f"**Earth/Space rests on one narrow course** (*{t[1]}*), which covers space science (ESS1) but not Earth systems.")
        mrids = [rid for rid in ("MATH-ALG1", "MATH-GEOM") if st.get(rid, {}).get("status") == "possible_only"]
        if mrids:
            kinds = {p["reason"] for rid in mrids for p in poss[rid]}
            kind = "an integrated sequence" if "integrated math" in kinds else "a two-part sequence" if "split sequence" in kinds else "related courses"
            what = " and ".join(LABEL[r] for r in mrids)
            cs = "; ".join(courses(r) for r in mrids)
            issues.append(f"**{what} {'are' if len(mrids) > 1 else 'is'} taught through {kind}** ({cs}); {'they count' if len(mrids) > 1 else 'it counts'} only under an equivalency rule (Theme 6).")
        cv = st.get("SS-CIVICS", {})
        if cv.get("status") == "possible_only":
            issues.append(f"**Civics has no stand-alone course.** Closest: {courses('SS-CIVICS')}. Depends on whether embedded or action-civics courses count.")
        elif cv.get("status") == "short":
            issues.append(f"**Civics is one semester** ({cv['examples']}); covered if AOE sets Civics at 0.5, short at 1.0.")
        else:
            for t in f["thin"]:
                if t[0] == "SS-CIVICS" and re.search(r"\bAP\b|advanced placement", t[1], re.I):
                    issues.append(f"**The only Civics course is AP** (*{t[1]}*); requiring Civics of every student means AP for all or a new course.")
        if st.get("FINLIT", {}).get("status") == "possible_only":
            issues.append(f"**Financial Literacy is embedded only** ({courses('FINLIT')}); the memo asks for stand-alone content.")
        if st.get("WL", {}).get("status") == "gap":
            issues.append("**No world language offered.** The Complete plan's 1.0 would need a teacher or a VTVLC/online route.")
        for rid in ("ELA-INTRO", "ELA-MASTERY", "SS-USHIST", "SCI-LIFE", "SS-WORLD"):
            v = st.get(rid, {})
            if v.get("status") in ("possible_only", "short"):
                issues.append(f"**{LABEL[rid]} is {v['status'].replace('_', ' ')}** ({courses(rid) or v['examples']}); usually a grade-level or description question rather than a missing course.")
        alt = [LABEL.get(k.split('|', 1)[1]) for k, v in g.items() if k.startswith(C) and v.get("alt_year_only") == "yes"]
        if alt:
            issues.append(f"**Alternate-year only:** {', '.join(alt)} is met only by a course that runs every other year.")
        if f["below_alg1"]:
            issues.append(f"**Math below Algebra I:** {len(f['below_alg1'])} course(s) – " + ", ".join(f"*{b}*" for b in f["below_alg1"][:4])
                          + " (Theme 3: leaves at most one spare math year under the Complete plan).")
        le = loc.get("local_ELECTIVE")
        if le not in (None, ""):
            le = float(le)
            if le > 3.0:
                issues.append(f"**Electives.** Local requirement {le:g} elective credits vs. 3.0 (Complete) / 6.0 (Transitional); {f['electives']['pure']} listed courses count toward no requirement.")
        if loc.get("local_only_requirements"):
            issues.append(f"**Local requirements with no home in the proposals:** {loc['local_only_requirements']}.")
        inter = [c for c, k in f["interdisciplinary"] if k == "interdisciplinary"]
        if inter:
            issues.append(f"**Interdisciplinary courses** that need a fractional-credit rule: " + ", ".join(f"*{c}*" for c in inter[:4]) + ".")
        if cte[sid]:
            ex = cte[sid][0]
            issues.append(f"**CTE embedded credit** stated for {len(cte[sid])} program(s), e.g. *{ex['course_name']}*: \"{first_sentences(ex['fulfills_text'], 140)}\" These must be re-mapped to the new categories.")
        if f["claims"]:
            issues.append(f"**Catalog claims not supported by the description** ({len(f['claims'])}), e.g. *{f['claims'][0][0]}* claimed for {LABEL.get(f['claims'][0][1], f['claims'][0][1])}.")
        if grading == "proficiency":
            issues.append("**Proficiency-only school:** credit-count requirements need a proficiency translation.")
        dis = f["disclosure"]["fulfills_text"]
        if dis <= 0.05 and sid not in NOT_ASSESSABLE:
            issues.append(f"**Disclosure:** {round(dis*100)}% of courses say what requirement they fulfill.")
        elif dis >= 0.75:
            issues.append(f"**Disclosure is strong:** {round(dis*100)}% of courses say what they fulfill – a model for other catalogs.")
        if not issues:
            issues.append("No requirement depends on an open definition; the school is well placed under both plans.")
        out.append("**Implementation issues**")
        out.extend(f"- {i}" for i in issues[:8])
        # one quoted example: the most decision-relevant possible course
        for rid in ("SCI-EARTH", "SS-CIVICS", "MATH-ALG1", "FINLIT", "HEALTH", "MATH-GEOM"):
            if st.get(rid, {}).get("status") == "possible_only" and poss[rid]:
                p = poss[rid][0]
                out.append("")
                out.append(f"> *{p['course_name']}* ({LABEL[rid]}, {p['reason']}): \"{first_sentences(p['description'])}\"")
                break
        out.append("")
    (ROOT / "report/appendix_schools.md").write_text("\n".join(out))
    print(len(out), "lines ->", "report/appendix_schools.md")


if __name__ == "__main__":
    main()
