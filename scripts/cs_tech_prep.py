#!/usr/bin/env python3 -I
"""Build per-school name lists for the CS/Technology scan (names only, to minimise tokens).
Keeps only courses whose phase3 subject_area is NOT ELA / Social Studies / World Language / PE & Health.
Writes phase3/cs_tech/input/<id>.tsv : idx<TAB>course_name<TAB>department<TAB>level  (idx = position in phase2/courses/<id>.json)."""
import json, glob, os
DROP = {"ELA", "Social Studies", "World Language/ASL", "PE & Health"}
os.makedirs("phase3/cs_tech/input", exist_ok=True)
tot = kept = 0
for f in sorted(glob.glob("phase2/courses/*.json")):
    sid = os.path.basename(f)[:-5]
    p2 = json.load(open(f))["courses"]
    cf = f"phase3/classified/{sid}.json"
    sa = {c["course_index"]: c["subject_area"] for c in json.load(open(cf))["courses"]} if os.path.exists(cf) else {}
    rows = []
    for i, c in enumerate(p2):
        tot += 1
        if sa.get(i) in DROP:
            continue
        clean = lambda s: (s or "").replace("\t", " ").replace("\n", " ").strip()
        rows.append(f"{i}\t{clean(c['course_name'])}\t{clean(c.get('department'))}\t{clean(c.get('level'))}")
    kept += len(rows)
    open(f"phase3/cs_tech/input/{sid}.tsv", "w").write("\n".join(rows) + "\n")
print(f"{tot} courses -> {kept} kept for scan")
