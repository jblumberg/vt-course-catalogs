"""Merge phase1/results/*.json + data/overrides.csv into phase1/catalogs.csv and print a status report.

overrides.csv columns: school_id, field, value, note   (human-maintained; later rows win)

Run:  python3 -I scripts/merge_phase1.py
"""
import csv, json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ["school_id", "school_name", "town", "su_sd", "su_sd_matches_list", "catalog_status",
          "catalog_url", "format", "platform", "school_year", "includes_descriptions", "confidence",
          "local_copy", "local_copy_exists", "pages_or_size", "issues", "how_found", "additional_urls",
          "school_website", "su_sd_source_url", "checked_on", "override_note"]


def main():
    schools = list(csv.DictReader((ROOT / "data/schools.csv").open()))
    overrides = {}
    ov_path = ROOT / "data/overrides.csv"
    if ov_path.exists():
        for o in csv.DictReader(ov_path.open()):
            overrides.setdefault(o["school_id"], []).append(o)

    out, status = [], Counter()
    for s in schools:
        p = ROOT / "phase1/results" / f'{s["school_id"]}.json'
        r = json.loads(p.read_text()) if p.exists() else {"catalog_status": "not_yet_searched"}
        row = {k: r.get(k, "") for k in FIELDS}
        row.update(school_id=s["school_id"], school_name=s["school_name"], town=s["town"])
        row["su_sd"] = r.get("su_sd") or s["su_sd"]
        row["additional_urls"] = " | ".join(f'{a.get("what","")}: {a.get("url","")}'
                                            for a in r.get("additional_urls") or [] if a.get("url"))
        notes = []
        for o in overrides.get(s["school_id"], []):
            row[o["field"]] = o["value"]
            notes.append(o.get("note", ""))
        row["override_note"] = "; ".join(n for n in notes if n)
        lc = row.get("local_copy")
        row["local_copy_exists"] = bool(lc) and (ROOT / lc).exists()
        status[row["catalog_status"]] += 1
        out.append(row)

    with (ROOT / "phase1/catalogs.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)

    print(f"{len(out)} schools -> phase1/catalogs.csv")
    for k, v in status.most_common():
        print(f"  {k}: {v}")
    review = [r for r in out if r["catalog_status"] not in ("found", "not_yet_searched")
              or r["confidence"] == "low" or r["su_sd_matches_list"] is False
              or (r["catalog_status"] == "found" and not r["local_copy_exists"])]
    if review:
        print("\nNeeds human review:")
        for r in review:
            print(f'  - {r["school_name"]}: {r["catalog_status"]}, conf={r["confidence"]}, '
                  f'su_match={r["su_sd_matches_list"]}, copy={r["local_copy_exists"]} :: {r["issues"][:120]}')


if __name__ == "__main__":
    main()
