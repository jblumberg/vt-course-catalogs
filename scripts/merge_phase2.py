"""Validate and merge phase2/courses/*.json into phase2/courses.csv and phase2/graduation_requirements.csv.

Run:  python3 -I scripts/merge_phase2.py              (validate all + write CSVs + summary)
      python3 -I scripts/merge_phase2.py --check ID   (validate one school only, no CSV)
"""
import csv, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COURSE_FIELDS = ["school_id", "school_name", "su_sd", "catalog_school_year", "department", "course_code",
                 "course_name", "description", "grade_levels", "credits", "credits_text", "length",
                 "prerequisites", "level", "delivery", "provider", "fulfills_text", "offering_note",
                 "source_page", "notes", "source_file", "source_retrieved_on", "extracted_on"]
LEVELS = {"standard", "honors", "AP", "IB", "dual_enrollment", "early_college", "CTE", "online",
          "special_program", "other"}
LENGTHS = {"year", "semester", "quarter", "trimester", "variable", "unknown"}
REQUIRED_TOP = ["school_id", "catalog_school_year", "source_file", "source_retrieved_on", "extracted_on",
                "extraction_status", "courses"]


def check(d):
    """Return (errors, warnings) for one school's file."""
    err, warn = [], []
    for k in REQUIRED_TOP:
        if k not in d:
            err.append(f"missing top-level field {k}")
    courses = d.get("courses") or []
    if d.get("extraction_status") == "complete" and len(courses) < 25:
        warn.append(f"only {len(courses)} courses but status 'complete' - check for missed sections")
    if not (ROOT / d.get("source_file", "")).exists():
        err.append(f"source_file not found: {d.get('source_file')}")
    seen = Counter((c.get("course_name") or "").strip().lower() + "|" + str(c.get("course_code"))
                   for c in courses)
    dups = [k for k, v in seen.items() if v > 1]
    if dups:
        warn.append(f"{len(dups)} duplicate name+code pairs, e.g. {dups[:3]}")
    nodesc = sum(1 for c in courses if not c.get("description"))
    if courses and nodesc / len(courses) > 0.2:
        warn.append(f"{nodesc}/{len(courses)} courses lack descriptions")
    for i, c in enumerate(courses):
        if not c.get("course_name"):
            err.append(f"course #{i} has no course_name")
        if c.get("level") not in LEVELS:
            err.append(f"{c.get('course_name')}: bad level {c.get('level')!r}")
        if c.get("length") not in LENGTHS:
            err.append(f"{c.get('course_name')}: bad length {c.get('length')!r}")
        if c.get("credits") is not None and not isinstance(c.get("credits"), (int, float)):
            err.append(f"{c.get('course_name')}: credits must be a number or null")
        if not isinstance(c.get("grade_levels", []), list):
            err.append(f"{c.get('course_name')}: grade_levels must be a list")
        if c.get("source_page") is None:
            warn.append(f"{c.get('course_name')}: no source_page")
    return err, warn[:15]


def load(p):
    try:
        return json.loads(p.read_text()), None
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"


def main():
    if "--check" in sys.argv:
        sid = sys.argv[sys.argv.index("--check") + 1]
        d, e = load(ROOT / "phase2/courses" / f"{sid}.json")
        if e:
            sys.exit(f"{sid}: {e}")
        err, warn = check(d)
        print(f"{sid}: {len(d.get('courses', []))} courses, {len(err)} errors, {len(warn)} warnings")
        for x in err:
            print("  ERROR", x)
        for x in warn:
            print("  warn ", x)
        sys.exit(1 if err else 0)

    rows, grad_rows, summary = [], [], []
    for p in sorted((ROOT / "phase2/courses").glob("*.json")):
        d, e = load(p)
        if e:
            summary.append((p.stem, 0, "INVALID", [e], []))
            continue
        err, warn = check(d)
        summary.append((d["school_id"], len(d.get("courses", [])), d.get("extraction_status"), err, warn))
        for c in d.get("courses", []):
            row = {k: c.get(k) for k in COURSE_FIELDS}
            for k in ("school_id", "school_name", "su_sd", "catalog_school_year", "source_file",
                      "source_retrieved_on", "extracted_on"):
                row[k] = d.get(k)
            row["grade_levels"] = ",".join(str(g) for g in c.get("grade_levels") or [])
            rows.append(row)
        g = d.get("graduation_requirements") or {}
        for a in g.get("by_area") or []:
            grad_rows.append({"school_id": d["school_id"], "school_name": d.get("school_name"),
                              "total_credits": g.get("total_credits"), "area": a.get("area"),
                              "credits": a.get("credits"), "notes": a.get("notes"),
                              "other_requirements": " | ".join(g.get("other") or []),
                              "source_page": g.get("source_page")})

    with (ROOT / "phase2/courses.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COURSE_FIELDS)
        w.writeheader()
        w.writerows(rows)
    gf = ["school_id", "school_name", "total_credits", "area", "credits", "notes", "other_requirements", "source_page"]
    with (ROOT / "phase2/graduation_requirements.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=gf)
        w.writeheader()
        w.writerows(grad_rows)

    print(f"{len(rows)} courses from {len(summary)} schools -> phase2/courses.csv")
    for sid, n, st, err, warn in summary:
        flag = " <-- " + "; ".join(err[:2] + warn[:2]) if (err or warn) else ""
        print(f"  {sid:50} {n:4}  {st}{flag}")


if __name__ == "__main__":
    main()
