"""Make sure every Phase 1 result has retrieval dates, so Phase 2 can tell what's new.

- each entry in local_copies gets "retrieved_on" (defaults to the file's checked_on date)
- each result gets top-level "retrieved_on" = latest retrieved_on of its copies (null if no copies)

Safe to run repeatedly.  Run:  python3 -I scripts/phase1_normalize.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    changed = 0
    for p in sorted((ROOT / "phase1/results").glob("*.json")):
        r = json.loads(p.read_text())
        before = json.dumps(r, sort_keys=True)
        copies = r.get("local_copies") or []
        for c in copies:
            c.setdefault("retrieved_on", r.get("checked_on"))
        dates = [c["retrieved_on"] for c in copies if c.get("retrieved_on")]
        r["retrieved_on"] = max(dates) if dates else None
        if json.dumps(r, sort_keys=True) != before:
            p.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n")
            changed += 1
    print(f"normalized {changed} result file(s)")


if __name__ == "__main__":
    main()
