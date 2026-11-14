"""Compare two classification runs of the same school(s) and build a human review sheet.

Run:  python3 -I scripts/phase3_review_sheet.py <runA_suffix> <runB_suffix> <school_id> [<school_id> ...]
      reads phase3/pilot/<school_id>.<suffix>.json, writes phase3/pilot/review_<A>_vs_<B>.csv
      and prints agreement stats. Disagreements come first in the sheet; the human fills in
      the 'human_*' columns (subject area and the requirement IDs they think apply).
"""
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def strong(c):
    return sorted(m["requirement_id"] for m in c.get("credit_mappings") or [] if m.get("strength") == "strong")


def allm(c):
    return sorted(f'{m["requirement_id"]}{"" if m.get("strength") == "strong" else "?"}' for m in c.get("credit_mappings") or [])


def main():
    a, b, sids = sys.argv[1], sys.argv[2], sys.argv[3:]
    rows, n, same_subj, same_strong = [], 0, 0, 0
    for sid in sids:
        src = json.loads((ROOT / "phase2/courses" / f"{sid}.json").read_text())["courses"]
        A = json.loads((ROOT / "phase3/pilot" / f"{sid}.{a}.json").read_text())["courses"]
        B = json.loads((ROOT / "phase3/pilot" / f"{sid}.{b}.json").read_text())["courses"]
        for i, s in enumerate(src):
            ca, cb = A[i], B[i]
            n += 1
            ss = ca["subject_area"] == cb["subject_area"]
            sm = strong(ca) == strong(cb)
            same_subj += ss
            same_strong += sm
            rows.append({"agree": "yes" if ss and sm else "NO", "school_id": sid, "course_index": i,
                         "course_name": s.get("course_name"), "department": s.get("department"),
                         "grades": ",".join(map(str, s.get("grade_levels") or [])), "level": s.get("level"),
                         "description": (s.get("description") or "")[:600], "fulfills_text": s.get("fulfills_text"),
                         f"{a}_subject": ca["subject_area"], f"{a}_mappings": " ".join(allm(ca)), f"{a}_conf": ca.get("confidence"),
                         f"{b}_subject": cb["subject_area"], f"{b}_mappings": " ".join(allm(cb)), f"{b}_conf": cb.get("confidence"),
                         f"{b}_rationale": " | ".join(m.get("rationale", "") for m in cb.get("credit_mappings") or []),
                         "human_subject": "", "human_mappings": "", "human_note": ""})
    rows.sort(key=lambda r: (r["agree"] == "yes", r["school_id"], r["course_index"]))
    out = ROOT / "phase3/pilot" / f"review_{a}_vs_{b}.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{n} courses: subject agreement {same_subj / n:.0%}, strong-mapping agreement {same_strong / n:.0%}")
    print(f"disagreements: {sum(r['agree'] == 'NO' for r in rows)} -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
