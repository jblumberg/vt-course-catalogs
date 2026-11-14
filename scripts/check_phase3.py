"""Validate a Phase 3 classification file against its Phase 2 source.

Run:  python3 -I scripts/check_phase3.py <school_id> [path/to/classified.json]
      (default path: phase3/classified/<school_id>.json)
"""
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUBJECTS = {"ELA", "Mathematics", "Science", "Social Studies", "Arts", "World Language/ASL", "Financial Literacy",
            "PE & Health", "Interdisciplinary", "Other"}
OTHER = {"Computer Science", "Business", "Technology/Engineering", "Family & Consumer Science", "CTE program",
         "Flexible pathway", "Advisory/Support", "Driver Ed", "Other"}
DOMAINS = {"Chemistry", "Physics", "Integrated Physical", "Life", "Earth & Space", "Environmental", "Other"}
REQS = {r["requirement_id"] for r in csv.DictReader((ROOT / "data/requirements.csv").open())} - {"TOTAL"}


def check(sid, path):
    src = json.loads((ROOT / "phase2/courses" / f"{sid}.json").read_text())["courses"]
    d = json.loads(Path(path).read_text())
    err = []
    cs = d.get("courses", [])
    if len(cs) != len(src):
        err.append(f"{len(cs)} classified vs {len(src)} courses in phase2")
    for i, c in enumerate(cs):
        tag = f"#{i} {c.get('course_name')}"
        if c.get("course_index") != i:
            err.append(f"{tag}: course_index {c.get('course_index')} != {i}")
        elif i < len(src) and (c.get("course_name") or "").strip() != (src[i].get("course_name") or "").strip():
            err.append(f"{tag}: name doesn't match phase2 ({src[i].get('course_name')})")
        if c.get("subject_area") not in SUBJECTS:
            err.append(f"{tag}: bad subject_area {c.get('subject_area')!r}")
        if c.get("subject_area") == "Interdisciplinary" and len(c.get("bridges") or []) < 2:
            err.append(f"{tag}: Interdisciplinary needs 2+ bridges")
        if c.get("subject_area") == "Other" and c.get("other_type") not in OTHER:
            err.append(f"{tag}: bad other_type {c.get('other_type')!r}")
        if c.get("subject_area") == "Science" and c.get("science_domain") not in DOMAINS:
            err.append(f"{tag}: bad science_domain {c.get('science_domain')!r}")
        if c.get("confidence") not in {"high", "medium", "low"}:
            err.append(f"{tag}: bad confidence")
        for rid in c.get("catalog_claims") or []:
            if rid not in REQS:
                err.append(f"{tag}: unknown catalog_claims requirement {rid!r}")
        for m in c.get("credit_mappings") or []:
            if m.get("requirement_id") not in REQS:
                err.append(f"{tag}: unknown requirement {m.get('requirement_id')!r}")
            if m.get("strength") not in {"strong", "possible"}:
                err.append(f"{tag}: bad strength {m.get('strength')!r}")
    return err


if __name__ == "__main__":
    sid = sys.argv[1]
    path = sys.argv[2] if len(sys.argv) > 2 else ROOT / "phase3/classified" / f"{sid}.json"
    e = check(sid, path)
    print(f"{sid}: {len(e)} errors")
    for x in e[:40]:
        print("  ERROR", x)
    sys.exit(1 if e else 0)
