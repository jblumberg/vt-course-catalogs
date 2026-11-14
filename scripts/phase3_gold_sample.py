"""Build the human answer-key review sheet (CSV) from classification runs.

Picks ~N courses: every disagreement between run A and run B (if B given), every low/medium-confidence course,
the tricky types (Interdisciplinary, Other-with-mappings, Environmental/mixed science, Algebra II, financial
content, equivalency 'may fulfill' text, no description, CTE), then a random fill spread across subject areas.

Run:  python3 -I scripts/phase3_gold_sample.py <runA> [--vs <runB>] [--n 100] [--out file.csv] <school_id> [<school_id> ...]
      reads phase3/pilot/<id>.<run>.json, writes phase3/gold/review_sample.csv
"""
import csv, json, random, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fmt(c):
    return "; ".join(f'{m["requirement_id"]}{"" if m.get("strength") == "strong" else " (possible)"}'
                     for m in c.get("credit_mappings") or []) or "(none - general elective)"


def strong(c):
    return sorted(m["requirement_id"] for m in c.get("credit_mappings") or [] if m.get("strength") == "strong")


def main():
    args = sys.argv[1:]
    n = int(args[args.index("--n") + 1]) if "--n" in args else 100
    vs = args[args.index("--vs") + 1] if "--vs" in args else None
    skip = {i for k in ("--n", "--vs", "--out") if k in args for i in (args.index(k), args.index(k) + 1)}
    pos = [a for i, a in enumerate(args) if i not in skip and a != "--no-cte"]
    run, sids = pos[0], pos[1:]
    random.seed(42)
    pool = []
    for sid in sids:
        src = json.loads((ROOT / "phase2/courses" / f"{sid}.json").read_text())
        A = json.loads((ROOT / "phase3/pilot" / f"{sid}.{run}.json").read_text())["courses"]
        B = json.loads((ROOT / "phase3/pilot" / f"{sid}.{vs}.json").read_text())["courses"] if vs else None
        for i, s in enumerate(src["courses"]):
            c = A[i]
            text = f'{s.get("course_name")} {s.get("description") or ""}'.lower()
            reasons = []
            if B and (B[i]["subject_area"] != c["subject_area"] or strong(B[i]) != strong(c)):
                reasons.append("models disagree")
            if c.get("confidence") in ("low", "medium"):
                reasons.append(f'{c["confidence"]} confidence')
            if c["subject_area"] == "Interdisciplinary":
                reasons.append("interdisciplinary")
            if c["subject_area"] == "Other" and c.get("credit_mappings"):
                reasons.append("Other with credit mapping")
            if c.get("science_domain") in ("Environmental", "Other"):
                reasons.append("environmental/mixed science")
            if re.search(r"algebra (2|ii)\b", text):
                reasons.append("Algebra II")
            if c.get("finlit_type") or re.search(r"financ|budget|personal finance", text):
                reasons.append("financial content")
            if re.search(r"may (fulfill|count|satisfy)|equivalen", (s.get("fulfills_text") or "") + text):
                reasons.append("equivalency credit")
            if not s.get("description"):
                reasons.append("no description")
            if s.get("level") == "CTE":
                reasons.append("CTE")
            pool.append({"key": f"{sid}#{i}", "school": src.get("school_name"), "course": s.get("course_name"),
                         "department": s.get("department"), "grades": ",".join(map(str, s.get("grade_levels") or [])),
                         "level": s.get("level"), "description": s.get("description") or "",
                         "catalog_says_fulfills": s.get("fulfills_text") or "",
                         "model_subject": c["subject_area"] + (f' ({"+".join(c.get("bridges") or [])})' if c.get("bridges") else "")
                                          + (f' ({c["other_type"]})' if c.get("other_type") else ""),
                         "model_credits": fmt(c), "catalog_claims": "; ".join(c.get("catalog_claims") or []),
                         "model_conf": c.get("confidence"),
                         "model_reason": " | ".join(m.get("rationale", "") for m in c.get("credit_mappings") or []),
                         "why_sampled": ", ".join(reasons) or "random check",
                         "agree (Y/N)": "", "correct_subject": "", "correct_credits": "", "note": ""})
    flagged = [p for p in pool if p["why_sampled"] != "random check"]
    cte = [p for p in flagged if "CTE" in p["why_sampled"]]
    flagged = [p for p in flagged if "CTE" not in p["why_sampled"]] + ([] if "--no-cte" in args else cte[:4])   # cap CTE examples
    random.shuffle(flagged)
    flagged.sort(key=lambda p: "models disagree" not in p["why_sampled"])            # disagreements first
    pick = flagged[: int(n * 0.6)]
    rest = [p for p in pool if p not in pick and "CTE" not in p["why_sampled"]]
    by_subj = {}
    for p in rest:
        by_subj.setdefault(p["model_subject"].split(" (")[0], []).append(p)
    while len(pick) < n and any(by_subj.values()):
        for subj in sorted(by_subj):
            if by_subj[subj] and len(pick) < n:
                pick.append(by_subj[subj].pop(random.randrange(len(by_subj[subj]))))
    pick.sort(key=lambda p: (p["school"], int(p["key"].split("#")[1])))
    out = ROOT / "phase3/gold" / (args[args.index("--out") + 1] if "--out" in args else "review_sample.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pick[0]))
        w.writeheader()
        w.writerows(pick)
    print(f"{len(pick)} courses -> {out.relative_to(ROOT)} ({out.stat().st_size // 1000} KB)")
    from collections import Counter
    print(Counter(p["model_subject"].split(" (")[0] for p in pick).most_common())


if __name__ == "__main__":
    main()
