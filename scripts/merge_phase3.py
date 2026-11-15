"""Merge Phase 3 outputs into CSVs.

- phase3/classified/<id>.json -> phase3/classified.csv  (one row per course x mapping; courses with no mapping get one row)
- phase3/profiles/<id>.json   -> phase3/profiles.csv    (one row per school)
Also prints which schools are missing or out of date (phase2 extracted after classification, or old rubric).

Run:  python3 -I scripts/merge_phase3.py
"""
import csv, glob, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUBRIC = "v0.3.2"


def main():
    rows, stale, missing = [], [], []
    for f in sorted(glob.glob(str(ROOT / "phase2/courses/*.json"))):
        sid = Path(f).stem
        src = json.loads(Path(f).read_text())
        cp = ROOT / "phase3/classified" / f"{sid}.json"
        if not src["courses"]:
            continue
        if not cp.exists():
            missing.append(sid)
            continue
        cl = json.loads(cp.read_text())
        if cl.get("rubric_version") != RUBRIC or (cl.get("classified_on") or "") < (src.get("extracted_on") or ""):
            stale.append(f'{sid} ({cl.get("rubric_version")}, {cl.get("classified_on")})')
        for i, (s, c) in enumerate(zip(src["courses"], cl["courses"])):
            base = {"school_id": sid, "school_name": src.get("school_name"), "course_index": i,
                    "course_name": s.get("course_name"), "department": s.get("department"), "level": s.get("level"),
                    "credits": s.get("credits"), "grade_levels": ",".join(map(str, s.get("grade_levels") or [])),
                    "subject_area": c.get("subject_area"), "bridges": "+".join(c.get("bridges") or []),
                    "other_type": c.get("other_type"), "science_domain": c.get("science_domain"),
                    "has_lab": c.get("has_lab"), "finlit_type": c.get("finlit_type"),
                    "catalog_claims": ";".join(c.get("catalog_claims") or []), "confidence": c.get("confidence"),
                    "offering_note": s.get("offering_note"), "rubric_version": cl.get("rubric_version")}
            maps = c.get("credit_mappings") or [{}]
            for m in maps:
                rows.append({**base, "requirement_id": m.get("requirement_id", ""), "strength": m.get("strength", ""),
                             "rationale": m.get("rationale", "")})
    if rows:
        with (ROOT / "phase3/classified.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    prof = []
    for f in sorted(glob.glob(str(ROOT / "phase3/profiles/*.json"))):
        d = json.loads(Path(f).read_text())
        g, s, c, lg = (d.get(k) or {} for k in ("grading_system", "schedule", "credit_definition", "local_grad_requirements"))
        prof.append({"school_id": d.get("school_id"), "grading_system": g.get("value"), "grading_evidence": g.get("evidence"),
                     "proficiency_scale": g.get("proficiency_scale"), "min_score_to_earn_credit": g.get("min_score_to_earn_credit"),
                     "transferable_skills_required": g.get("transferable_skills_required"),
                     "schedule_type": s.get("type"), "courses_per_term": s.get("courses_per_term"),
                     "terms_per_year": s.get("terms_per_year"), "schedule_evidence": s.get("evidence"),
                     "credit_definition": c.get("text"), "credit_per_course_term": c.get("credit_per_course_term"),
                     "local_total": lg.get("total"), "local_unit": lg.get("unit"), "local_total_in_credits": lg.get("total_in_credits"),
                     "max_credits_4yr": (s["courses_per_term"] * s["terms_per_year"] * 4 * c["credit_per_course_term"]
                                         if all(isinstance(x, (int, float)) for x in (s.get("courses_per_term"), s.get("terms_per_year"),
                                                                                      c.get("credit_per_course_term"))) else None),
                     "share_of_schedule_required": None, "schedule_check": "",
                     "flexible_pathways": "; ".join(d.get("flexible_pathways_listed") or []),
                     "cte_centers": "; ".join(d.get("cte_centers") or []), "notes": d.get("notes")})
    for r in prof:
        if r["max_credits_4yr"] and isinstance(r["local_total"], (int, float)):
            r["share_of_schedule_required"] = round(r["local_total"] / r["max_credits_4yr"], 2)
            # >1 is impossible: courses_per_term was probably a minimum load or blocks/day in an A/B schedule
            r["schedule_check"] = "INCONSISTENT - verify" if r["share_of_schedule_required"] > 1 else "ok"
    if prof:
        with (ROOT / "phase3/profiles.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(prof[0]))
            w.writeheader()
            w.writerows(prof)
    print(f"{len(rows)} course-mapping rows -> phase3/classified.csv; {len(prof)} profiles -> phase3/profiles.csv")
    print(f"missing classification ({len(missing)}): {' '.join(missing)}")
    if stale:
        print(f"stale ({len(stale)}): {'; '.join(stale)}")


if __name__ == "__main__":
    main()
