"""Phase 4a: per-school coverage of each proposed graduation requirement, under both AOE proposals.

Reads phase2/courses/<id>.json + phase3/classified/<id>.json, data/requirements.csv.
Writes phase4/gap_by_school.csv (one row per school x proposal x requirement) and phase4/gap_summary.csv
(one row per proposal x requirement: how many schools are covered / possible-only / partial / gap / unknown).

Status per requirement (content-based mappings only; catalog_claims, FLEX-ANY and CTE-center programs never close a gap):
  covered       - strong courses offer at least the required credits (or, where credits aren't printed, at least
                  ceil(required) strong courses - flagged credits_known = no)
  short         - strong courses exist but offer fewer credits than required
  possible_only - no strong course, but at least one 'possible' course (e.g. Environmental Science for Earth/Space,
                  embedded financial literacy, equivalency credit)
  gap           - nothing maps
  unknown       - the school has no extracted course list (Oxbow) or titles only (catalog lacks descriptions)
Special rules (PLAN.md 4a): PE-HEALTH-COMBINED = PE + HEALTH credits; MATH-PATHWAY may also be filled by courses mapped
to MATH-STATS-ALG2 that are not needed for that requirement (transitional plan needs 0 STATS-ALG2 credits).
Courses whose offering_note says they are not offered in 2026-27 are excluded.

Run:  python3 -I scripts/gap_analysis.py
"""
import csv, glob, json, math, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANS = {"complete_2033": "Complete (Class of 2033+)", "transitional_2031_32": "Transitional (2031-32)"}
TITLES_ONLY = {"mill-river-union-high-school", "rivendell-academy"}   # catalogs without descriptions


def not_offered(s):
    n = (s.get("offering_note") or "").lower()
    return bool(re.search(r"not offered|offered 2027|next offered 27|2027-28 only|2027-2028", n))


def main():
    reqs = [r for r in csv.DictReader((ROOT / "data/requirements.csv").open()) if r["requirement_id"] not in ("TOTAL", "ELECTIVE")]
    out, summ = [], defaultdict(Counter)
    for f in sorted(glob.glob(str(ROOT / "phase2/courses/*.json"))):
        sid = Path(f).stem
        src = json.loads(Path(f).read_text())
        cp = ROOT / "phase3/classified" / f"{sid}.json"
        cl = json.loads(cp.read_text())["courses"] if cp.exists() else None
        # requirement -> list of (strength, credits, course_name)
        by = defaultdict(list)
        if cl:
            for s, c in zip(src["courses"], cl):
                if s.get("level") == "CTE" or c.get("other_type") in ("CTE program",) or not_offered(s):
                    continue
                for m in c.get("credit_mappings") or []:
                    rid = m.get("requirement_id")
                    if rid == "FLEX-ANY":
                        continue
                    cr = s.get("credits") if isinstance(s.get("credits"), (int, float)) else None
                    by[rid].append((m.get("strength"), cr, s.get("course_name")))
        for plan, label in PLANS.items():
            for r in reqs:
                rid = r["requirement_id"]
                need = float(r[plan]) if r[plan] else 0.0
                if need == 0:
                    continue
                if rid == "PE-HEALTH-COMBINED":
                    items = by["PE"] + by["HEALTH"]
                elif rid == "MATH-PATHWAY":
                    items = by["MATH-PATHWAY"] + (by["MATH-STATS-ALG2"] if plan == "transitional_2031_32" else by["MATH-STATS-ALG2"][1:])
                else:
                    items = by[rid]
                strong = [x for x in items if x[0] == "strong"]
                possible = [x for x in items if x[0] == "possible"]
                known = [x[1] for x in strong if x[1] is not None]
                credits_known = len(known) == len(strong)
                offered = sum(known) if known else None
                if cl is None or (sid in TITLES_ONLY and not strong):
                    status = "unknown"
                elif strong:
                    if credits_known:
                        status = "covered" if offered >= need else "short"
                    else:
                        status = "covered" if (offered or 0) >= need or len(strong) >= math.ceil(need) else "short"
                elif possible:
                    status = "possible_only"
                else:
                    status = "gap"
                summ[(plan, rid)][status] += 1
                out.append({"school_id": sid, "school_name": src.get("school_name"), "plan": label, "requirement_id": rid,
                            "required_credits": need, "status": status, "strong_courses": len(strong),
                            "strong_credits_offered": offered, "credits_known": "yes" if credits_known else "no",
                            "possible_courses": len(possible),
                            "examples": "; ".join(x[2] for x in (strong or possible)[:4])})
    (ROOT / "phase4").mkdir(exist_ok=True)
    with (ROOT / "phase4/gap_by_school.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    statuses = ["covered", "short", "possible_only", "gap", "unknown"]
    rows = [{"plan": PLANS[p], "requirement_id": rid, **{s: c[s] for s in statuses}} for (p, rid), c in summ.items()]
    with (ROOT / "phase4/gap_summary.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["plan", "requirement_id"] + statuses)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(out)} rows -> phase4/gap_by_school.csv")
    print(f"{'plan':<26}{'requirement':<20}" + "".join(f"{s:>14}" for s in statuses))
    for r in rows:
        print(f"{r['plan']:<26}{r['requirement_id']:<20}" + "".join(f"{r[s]:>14}" for s in statuses))


if __name__ == "__main__":
    main()
