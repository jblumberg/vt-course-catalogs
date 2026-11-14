"""Score classification runs against the human answer key (phase3/gold/labels.csv).

Gold for a row: if the reviewer agreed (Y), the mappings shown in the sheet (model_credits); if not (N), the
reviewer's correct_credits ("ELECTIVE" or blank = no mapping). Rows with a blank agree column (CTE) are skipped.

Run:  python3 -I scripts/phase3_score.py <run_suffix> [<run_suffix> ...]
      reads phase3/pilot/<school_id>.<suffix>.json (or phase3/classified/<school_id>.json for suffix 'classified')
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = {"MATH-STATS-ALG3": "MATH-STATS-ALG2"}           # reviewer typos


def parse(text):
    out = {}
    for part in re.split(r"[;,]", text or ""):
        part = part.strip()
        if not part or part.upper() == "ELECTIVE" or part.startswith("(none"):
            continue
        rid = part.split(" (")[0].strip().upper()
        out[FIX.get(rid, rid)] = "possible" if "(possible)" in part else "strong"
    return out


def run_maps(c):
    return {m["requirement_id"]: m.get("strength", "strong") for m in c.get("credit_mappings") or []}


def load(sid, run):
    p = ROOT / "phase3/classified" / f"{sid}.json" if run == "classified" else ROOT / "phase3/pilot" / f"{sid}.{run}.json"
    return json.loads(p.read_text())["courses"]


def main():
    labels = [r for r in csv.DictReader((ROOT / "phase3/gold/labels.csv").open()) if r["agree (Y/N)"].strip()]
    for run in sys.argv[1:]:
        cache, exact, reqs, strong, misses = {}, 0, 0, 0, []
        for r in labels:
            sid, i = r["key"].split("#")
            cache.setdefault(sid, load(sid, run))
            gold = parse(r["model_credits"]) if r["agree (Y/N)"].strip().upper() == "Y" else parse(r["correct_credits"])
            got = run_maps(cache[sid][int(i)])
            e, q = got == gold, set(got) == set(gold)
            s = {k for k, v in got.items() if v == "strong"} == {k for k, v in gold.items() if v == "strong"}
            exact += e; reqs += q; strong += s
            if not e:
                misses.append(f'  {r["key"]:<36} {r["course"][:32]:<32} got {got or "-"}  gold {gold or "-"}')
        n = len(labels)
        print(f"{run}: {n} courses | exact (requirement+strength) {exact / n:.0%} | "
              f"requirements ignoring strength {reqs / n:.0%} | strong set {strong / n:.0%}")
        print("\n".join(misses))


if __name__ == "__main__":
    main()
