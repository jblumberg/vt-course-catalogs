"""Merge phase1/results/*.json + data/overrides.csv into phase1/catalogs.csv and print a status report.

overrides.csv columns: school_id, field, value, note   (human-maintained; later rows win)

Run:  python3 -I scripts/merge_phase1.py
"""
import csv, json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ["school_id", "school_name", "town", "grades", "su_sd", "su_sd_matches_list", "su_sd_note",
          "catalog_status", "school_year", "coverage", "includes_descriptions", "confidence",
          "catalog_title", "catalog_url", "direct_file_url", "linked_from_official_site", "format",
          "web_host", "course_planner", "local_copies", "local_copies_exist", "grad_requirements_url",
          "school_status_notes", "issues", "how_found", "additional_urls", "school_website",
          "su_sd_source_url", "checked_on", "override_note"]


def flat(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "yes" if v else "no"
    return str(v)


def main():
    schools = list(csv.DictReader((ROOT / "data/schools.csv").open()))
    overrides = {}
    ov_path = ROOT / "data/overrides.csv"
    if ov_path.exists():
        for o in csv.DictReader(ov_path.open()):
            overrides.setdefault(o["school_id"], []).append(o)

    out, status, problems = [], Counter(), []
    for s in schools:
        p = ROOT / "phase1/results" / f'{s["school_id"]}.json'
        try:
            r = json.loads(p.read_text()) if p.exists() else {"catalog_status": "not_yet_searched"}
        except json.JSONDecodeError as e:
            r = {"catalog_status": "INVALID_JSON"}
            problems.append(f'{s["school_id"]}: invalid JSON ({e})')
        row = {k: flat(r.get(k)) for k in FIELDS}
        row.update(school_id=s["school_id"], school_name=s["school_name"], town=s["town"], grades=s["grades"])
        row["su_sd"] = r.get("su_sd") or s["su_sd"]
        copies = r.get("local_copies") or []
        row["local_copies"] = " | ".join(c.get("path", "") for c in copies)
        row["local_copies_exist"] = flat(bool(copies) and all((ROOT / c.get("path", "")).exists() for c in copies))
        row["additional_urls"] = " | ".join(f'{a.get("what","")}: {a.get("url","")}'
                                            for a in r.get("additional_urls") or [] if a.get("url"))
        notes = []
        for o in overrides.get(s["school_id"], []):
            row[o["field"]] = o["value"]
            notes.append(o.get("note", ""))
        row["override_note"] = "; ".join(n for n in notes if n)
        status[row["catalog_status"]] += 1
        out.append(row)

    with (ROOT / "phase1/catalogs.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)

    print(f"{len(out)} schools -> phase1/catalogs.csv")
    for k, v in status.most_common():
        print(f"  {k}: {v}")
    for pr in problems:
        print("  PROBLEM:", pr)
    review = [r for r in out if r["catalog_status"] not in ("found", "not_yet_searched")
              or r["confidence"] == "low" or r["su_sd_matches_list"] == "no"
              or (r["catalog_status"] == "found" and r["local_copies_exist"] != "yes")]
    if review:
        print("\nNeeds human review:")
        for r in review:
            print(f'  - {r["school_name"]}: {r["catalog_status"]} ({r["school_year"]}), conf={r["confidence"]}, '
                  f'su_match={r["su_sd_matches_list"]}, copies={r["local_copies_exist"]} :: {r["issues"][:110]}')


if __name__ == "__main__":
    main()
