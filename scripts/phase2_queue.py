"""List schools ready for Phase 2 (course extraction).

A school is READY if Phase 1 has a usable catalog copy (status found / partial / outdated_only, local copy exists) AND
  - it has no phase2/courses/<id>.json yet  -> "new", or
  - its Phase 1 retrieved_on is later than the source_retrieved_on recorded in Phase 2 -> "updated".
Everything else is listed as WAITING with the reason (e.g. not found yet - for you to chase down).

Run:  python3 -I scripts/phase2_queue.py           (human-readable)
      python3 -I scripts/phase2_queue.py --ids     (just the ready school_ids, one per line)
"""
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USABLE = {"found", "partial", "outdated_only"}


def main():
    ready, waiting, done = [], [], []
    for s in csv.DictReader((ROOT / "data/schools.csv").open()):
        sid = s["school_id"]
        p1 = ROOT / "phase1/results" / f"{sid}.json"
        if not p1.exists():
            waiting.append((sid, "phase 1 not run"))
            continue
        r = json.loads(p1.read_text())
        status = r.get("catalog_status")
        copies = [c for c in r.get("local_copies") or [] if (ROOT / c.get("path", "")).exists()]
        if status not in USABLE:
            waiting.append((sid, f"phase 1 status: {status}"))
            continue
        if not copies:
            waiting.append((sid, "no downloaded copy (add one via data/manual_catalogs.csv)"))
            continue
        retrieved = r.get("retrieved_on") or r.get("checked_on") or ""
        p2 = ROOT / "phase2/courses" / f"{sid}.json"
        if not p2.exists():
            ready.append((sid, "new"))
            continue
        m = json.loads(p2.read_text())
        if retrieved > (m.get("source_retrieved_on") or ""):
            ready.append((sid, f"updated catalog ({m.get('source_retrieved_on')} -> {retrieved})"))
        else:
            done.append(sid)

    if "--ids" in sys.argv:
        print("\n".join(sid for sid, _ in ready))
        return
    print(f"READY ({len(ready)}):")
    for sid, why in ready:
        print(f"  {sid}  [{why}]")
    print(f"\nWAITING ({len(waiting)}):")
    for sid, why in waiting:
        print(f"  {sid}  [{why}]")
    print(f"\nDONE ({len(done)})")


if __name__ == "__main__":
    main()
