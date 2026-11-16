#!/usr/bin/env python3 -I
"""Merge phase3/cs_tech/results/*.tsv -> phase3/cs_tech/courses.csv and phase3/cs_tech/schools.csv."""
import csv, glob, json, os
LAB = {"CS", "TECH", "NA", "MORE_INFO"}
courses, schools = [], []
names = {r["school_id"]: r for r in csv.DictReader(open("data/schools.csv"))}
for f in sorted(glob.glob("phase3/cs_tech/input/*.tsv")):
    sid = os.path.basename(f)[:-4]
    inp = [l.rstrip("\n").split("\t") for l in open(f) if l.strip()]
    rf = f"phase3/cs_tech/results/{sid}.tsv"
    res = {}
    if os.path.exists(rf):
        for l in open(rf):
            p = l.rstrip("\n").split("\t")
            if len(p) >= 3 and p[0].isdigit() and p[1] in LAB:
                res[int(p[0])] = p
    n = {"CS": 0, "TECH": 0}
    for i, name, dept, lvl in inp:
        p = res.get(int(i))
        label = p[1] if p else "MISSING"
        note = p[3] if p and len(p) > 3 else ""
        passn = p[2] if p else ""
        if label in n: n[label] += 1
        if label in ("CS", "TECH", "MORE_INFO", "MISSING"):
            courses.append([sid, i, name, dept, label, passn, note])
    unresolved = sum(1 for r in courses if r[0] == sid and r[4] in ("MORE_INFO", "MISSING"))
    schools.append([sid, names.get(sid, {}).get("school_name", ""), len(inp), "yes" if os.path.exists(rf) else "NO", n["CS"], n["TECH"], unresolved])
with open("phase3/cs_tech/courses.csv", "w", newline="") as o:
    w = csv.writer(o); w.writerow(["school_id", "course_index", "course_name", "department", "label", "pass", "note"]); w.writerows(courses)
with open("phase3/cs_tech/schools.csv", "w", newline="") as o:
    w = csv.writer(o); w.writerow(["school_id", "school_name", "courses_scanned", "scanned", "cs_courses", "tech_courses", "unresolved"]); w.writerows(schools)
done = [s for s in schools if s[3] == "yes"]
print(f"{len(done)}/{len(schools)} schools scanned; offer CS/DS: {sum(1 for s in done if s[4]>0)}; offer Tech: {sum(1 for s in done if s[5]>0)}; "
      f"either: {sum(1 for s in done if s[4]>0 or s[5]>0)}; unresolved rows: {sum(s[6] for s in done)}")
