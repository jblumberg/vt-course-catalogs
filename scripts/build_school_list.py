"""Build data/schools.csv: Vermont public schools serving grade 12, excluding CTE centers.

Inputs (in sources/):
  urban_g12_2024.json  - NCES Common Core of Data 2024-25 directory for VT via Urban Institute
                         Education Data API (educationdata.urban.org)
SU/SD mapping is hand-set below from Wikipedia "List of school districts in Vermont"
(sources/wiki_districts.txt); Phase 1 agents re-verify it from each school's own website.

Run:  python3 -I scripts/build_school_list.py
"""
import csv, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "sources" / "urban_g12_2024.json"
OUT = ROOT / "data" / "schools.csv"

# NCES LEA id -> supervisory union / supervisory district
SU_BY_LEAID = {
    "5000402": "Addison Central Supervisory Union",
    "5000398": "Addison Northwest Supervisory Union",
    "5001830": "Southwest Vermont Supervisory Union",
    "5000445": "Barre Supervisory Union",
    "5008246": "Windham Northeast Supervisory Union",
    "5008224": "Orange East Supervisory Union",
    "5002820": "Burlington Supervisory District",
    "5002850": "Caledonia Central Supervisory Union",
    "5002940": "Essex North Supervisory Union",
    "5000396": "Champlain Valley Supervisory Union",
    "5003240": "Colchester Supervisory District",
    "5003390": "Orleans Southwest Supervisory Union",
    "5003450": "Caledonia Central Supervisory Union",
    "5000448": "Lamoille South Supervisory Union",
    "5000444": "Franklin Northeast Supervisory Union",
    "5000395": "Essex Westford Supervisory Union",
    "5003930": "Franklin West Supervisory Union",
    "5000427": "Two Rivers Supervisory Union",
    "5004590": "Hartford Supervisory District",
    "5000403": "Harwood Supervisory District",
    "5008243": "Orleans Southwest Supervisory Union",
    "5005050": "Orleans Central Supervisory Union",
    "5000397": "Lamoille North Supervisory Union",
    "5000399": "Maple Run Supervisory Union",
    "5000393": "Mill River Supervisory Union",
    "5005610": "Milton Supervisory District",
    "5000433": "Franklin Northwest Supervisory Union",
    "5000410": "Montpelier-Roxbury Supervisory Union",
    "5005810": "Southwest Vermont Supervisory Union",
    "5000442": "Windsor Southeast Supervisory Union",
    "5000443": "Chittenden East Supervisory Union",
    "5000450": "Windsor Central Supervisory Union",  # may now be "Mountain Views Supervisory Union" - verify
    "5000425": "Mount Abraham Unified School District (supervisory district)",
    "5009600": "North Country Supervisory Union",
    "5000400": "Orange Southwest Supervisory Union",
    "5000392": "Rutland Northeast Supervisory Union",
    "5000437": "Orange East Supervisory Union",
    "5000408": "Central Vermont Supervisory Union",
    "5000411": "Greater Rutland County Supervisory Union",
    "5000024": "Rivendell Interstate School District",
    "5007050": "Rutland City Supervisory District",
    "5007650": "St. Johnsbury Supervisory District",
    "5000440": "Addison Rutland Supervisory Union",
    "5007470": "South Burlington Supervisory District",
    "5007530": "Springfield Supervisory District",
    "5007800": "Lamoille South Supervisory Union",
    "5000418": "Windham Southwest Supervisory Union",
    "5008225": "Caledonia Central Supervisory Union",
    "5000439": "Washington Central Supervisory Union",
    "5000432": "Windham Central Supervisory Union",
    "5000426": "White River Valley Supervisory Union",
    "5000431": "Windham Southeast Supervisory Union",
    "5009360": "Winooski Supervisory District",
}

NOTES = {
    "St. Johnsbury School": "NCES lists PK-12, but St. Johnsbury students typically attend St. Johnsbury "
                            "Academy (independent). Likely no public HS catalog - verify, probably exclude.",
    "Rivendell Academy": "Interstate VT/NH district; school is in Orford, NH but serves VT towns.",
    "Woodstock Union Middle/High School": "SU may have been renamed Mountain Views Supervisory Union - verify.",
}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def grade(g):
    return "PK" if g == -1 else ("K" if g == 0 else str(g))


def main():
    rows = json.loads(SRC.read_text())["results"]
    keep = [r for r in rows
            if r["highest_grade_offered"] == 12
            and r["school_type"] == 1          # 1 = regular school (excludes type 3 = career/technical)
            and r["school_status"] in (1, 3, 4, 5, 8)]  # open / new / added / changed / reopened
    out = []
    for r in sorted(keep, key=lambda r: r["school_name"]):
        leaid = str(r["leaid"])
        out.append({
            "school_id": slug(r["school_name"]),
            "school_name": r["school_name"],
            "town": r["city_location"].title(),
            "grades": f'{grade(r["lowest_grade_offered"])}-{grade(r["highest_grade_offered"])}',
            "enrollment_2024": r["enrollment"],
            "su_sd": SU_BY_LEAID.get(leaid, "UNMAPPED"),
            "school_district": r["lea_name"],
            "nces_school_id": r["ncessch"],
            "state_school_id": r["seasch"],
            "notes": NOTES.get(r["school_name"], ""),
        })
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    unmapped = [o["school_name"] for o in out if o["su_sd"] == "UNMAPPED"]
    print(f"wrote {len(out)} schools to {OUT}; unmapped SU: {unmapped}")


if __name__ == "__main__":
    main()
