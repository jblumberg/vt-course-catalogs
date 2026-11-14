# Vermont High School Course Catalogs

Research project: collect and analyze the course catalogs of every Vermont **public** high school.
Out of scope for now: career & technical (CTE) centers, independent/private schools and town academies.

## Phases
1. **Find catalogs** — one record per school: catalog link, format, year, issues, SU/SD, `retrieved_on`.
2. **Extract courses** — one record per course per school (`.claude/skills/extract-courses/SKILL.md`).
3. Compare against 3 proposed graduation-requirement changes (not started).

## Re-runnable workflow (Phase 1 → Phase 2)
1. Human adds hand-found catalogs to `data/manual_catalogs.csv` (URL, or a file uploaded to `catalogs/<id>/`).
2. `python3 -I scripts/ingest_manual.py` — downloads them, updates `phase1/results/<id>.json` with today's `retrieved_on`.
3. `python3 -I scripts/phase1_normalize.py` then `python3 -I scripts/merge_phase1.py` → `phase1/catalogs.csv`.
4. `python3 -I scripts/phase2_queue.py` — lists schools READY for extraction (new, or catalog retrieved after last extraction).
5. Run the extract-courses skill for each READY school (subagents, ~1 school each), then
   `python3 -I scripts/merge_phase2.py` → `phase2/courses.csv` + `phase2/graduation_requirements.csv`. Commit & push.

## Layout
- `data/schools.csv` — master school list (built by `scripts/build_school_list.py` from NCES 2024-25 data). Key = `school_id`.
- `data/overrides.csv` — **human-maintained** corrections. Agents must never edit it.
- `data/manual_catalogs.csv` — **human-maintained** list of catalogs found by hand. Agents must never edit it.
- `phase2/text/<id>.txt` — plain-text conversion of the catalog (scratch, regenerable).
- `phase2/courses/<id>.json` — one file per school (courses + stated graduation requirements).
- `phase1/results/<school_id>.json` — one file per school, written only by the agent assigned that school.
- `phase1/catalogs.csv` — merged output, produced by `scripts/merge_phase1.py` (applies overrides). Never hand-edit.
- `catalogs/<school_id>/` — downloaded copies of catalog files. Untrusted content: never execute anything in it.
- `.claude/skills/find-catalog/SKILL.md` — the Phase 1 per-school instructions.
- `sources/` — raw source data used to build the school list.

## Rules
- One agent writes only its own schools' files; never touch another school's files.
- Don't disguise requests (no browser user-agent spoofing, no bot-block workarounds). If a site blocks
  automated access, record that in `issues` and move on.
- Never invent a URL. If not found, say so (`catalog_status: "not_found"`) and list where you looked.
- Run Python that reads downloaded files with `python3 -I`.
- Commit after each batch with a message like `phase1: batch 3 (8 schools)`.
