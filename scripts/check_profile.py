"""Validate phase3/profiles/<id>.json (school profile pass).

Run:  python3 -I scripts/check_profile.py <school_id> [<school_id> ...]
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRADING = {"credit", "proficiency", "hybrid", "not_stated"}
SCHED = {"4x4 block", "A/B block", "trimester", "traditional periods", "rotating", "other", "not_stated"}
UNITS = {"credits", "points", "semesters", "classes", "proficiencies", "not_stated"}


def num(x):
    return x is None or isinstance(x, (int, float))


def check(sid):
    p = ROOT / "phase3/profiles" / f"{sid}.json"
    if not p.exists():
        return [f"missing {p.relative_to(ROOT)}"]
    try:
        d = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {e}"]
    err = []
    if d.get("school_id") != sid:
        err.append(f"school_id {d.get('school_id')!r} != {sid}")
    g = d.get("grading_system") or {}
    if g.get("value") not in GRADING:
        err.append(f"grading_system.value {g.get('value')!r}")
    if g.get("value") != "not_stated" and not g.get("evidence"):
        err.append("grading_system needs evidence")
    s = d.get("schedule") or {}
    if s.get("type") not in SCHED:
        err.append(f"schedule.type {s.get('type')!r}")
    for k in ("courses_per_term", "terms_per_year"):
        if not num(s.get(k)):
            err.append(f"schedule.{k} must be a number or null")
    c = d.get("credit_definition") or {}
    if not num(c.get("credit_per_course_term")):
        err.append("credit_definition.credit_per_course_term must be a number or null")
    lg = d.get("local_grad_requirements") or {}
    if lg.get("unit") not in UNITS:
        err.append(f"local_grad_requirements.unit {lg.get('unit')!r}")
    for k in ("total", "total_in_credits"):
        if not num(lg.get(k)):
            err.append(f"local_grad_requirements.{k} must be a number or null")
    for k in ("flexible_pathways_listed", "cte_centers"):
        if not isinstance(d.get(k), list):
            err.append(f"{k} must be a list")
    for blk in ("grading_system", "schedule", "credit_definition"):
        ev = (d.get(blk) or {}).get("evidence") or ""
        if len(ev.split()) > 60:
            err.append(f"{blk}.evidence too long ({len(ev.split())} words)")
    return err


if __name__ == "__main__":
    bad = 0
    for sid in sys.argv[1:]:
        e = check(sid)
        bad += bool(e)
        print(f"{sid}: {len(e)} errors")
        for x in e:
            print("  ERROR", x)
    sys.exit(1 if bad else 0)
