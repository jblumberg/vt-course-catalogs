"""Print a Markdown table of Phase 2 coverage per school (non-CTE courses), for report/DATA_QUALITY.md.

Run:  python3 -I scripts/coverage_table.py > report/coverage_by_school.md
"""
import csv, glob, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = [("description", "Desc"), ("grade_levels", "Grades"), ("credits", "Credits"), ("length", "Length"),
          ("prerequisites", "Prereqs"), ("fulfills_text", "Fulfills")]


def pct(a, b):
    return f"{a / b:.0%}" if b else "–"


def main():
    p1 = {r["school_id"]: r for r in csv.DictReader((ROOT / "phase1/catalogs.csv").open())}
    print("| School | Catalog year | Status | Courses | CTE | " + " | ".join(h for _, h in FIELDS) + " | Grad credits |")
    print("|---" * (6 + len(FIELDS)) + "|")
    tot = {k: 0 for k, _ in FIELDS}
    N = C = 0
    for f in sorted(glob.glob(str(ROOT / "phase2/courses/*.json"))):
        d = json.loads(Path(f).read_text())
        cs = [c for c in d["courses"] if c.get("level") != "CTE"]
        cte = len(d["courses"]) - len(cs)
        cnt = {}
        for k, _ in FIELDS:
            cnt[k] = sum(1 for c in cs if c.get(k) and c.get(k) != "unknown")
            tot[k] += cnt[k]
        N += len(cs)
        C += cte
        g = (d.get("graduation_requirements") or {}).get("total_credits")
        yr = d.get("catalog_school_year") or p1.get(d["school_id"], {}).get("school_year") or "?"
        print(f'| {d.get("school_name")} | {yr} | {d.get("extraction_status")} | {len(cs)} | {cte} | '
              + " | ".join(pct(cnt[k], len(cs)) for k, _ in FIELDS) + f' | {g if g is not None else "–"} |')
    print(f"| **All schools** | | | **{N}** | **{C}** | " + " | ".join(f"**{pct(tot[k], N)}**" for k, _ in FIELDS) + " | |")


if __name__ == "__main__":
    main()
