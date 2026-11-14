# Vermont High School Course Catalog Analysis — Plan

Living plan for this project. Last updated 2026-11-14. Read this first in any new session, along with `CLAUDE.md`.

**Goal:** For every Vermont public high school, find out which courses could satisfy the proposed statewide graduation
requirements (AOE memo of 2026-10-20 to the SBE), and where the gaps are. Support AOE's change management with evidence:
what catalogs disclose today, which schools will need to add courses, and how their credit and schedule systems differ.

**Scope:** 57 public schools that serve grade 12 (NCES 2024-25). St. Johnsbury School is PK-8 only, which leaves **56**.
CTE centers, independent schools and town academies are out of scope. CTE center programs that appear in a high school's
catalog are kept but tagged.

---

## 1. Status

| Phase | Status | Output |
|---|---|---|
| 1. Find catalogs | **Done** (57/57) | `phase1/catalogs.csv`, `phase1/results/*.json`, `catalogs/<id>/` |
| 2. Extract courses | **Paused at 22 schools** (2,604 records) | `phase2/courses/*.json` → `phase2/courses.csv`, `phase2/graduation_requirements.csv` |
| 3a. Requirements table | **Done** | `data/requirements.csv` |
| 3b. Classification rubric | **v0.3**, scored against the human answer key | `.claude/skills/classify-courses/SKILL.md`, `phase3/pilot/` |
| 3c. Human calibration | **With the human**: Google Sheet review of 100 courses | [Review sheet](https://docs.google.com/spreadsheets/d/1Q-grm7L2jiT9P973gsT75nBqwqJHxzgJal_Uk-RROyc/edit) (Drive id `1Q-grm7L2jiT9P973gsT75nBqwqJHxzgJal_Uk-RROyc`); local copy `phase3/gold/review_sample.csv` |
| 3d. School profile pass | Planned | — |
| 3e. Classify all schools | Planned | `phase3/classified/*.json` |
| 4. Gap analysis + report | Planned | `phase4/` |

**Phase 1 results:** 44 schools have a current (2026-27) catalog, 9 only an older year, 1 is partial, 2 have nothing public
(Enosburg Falls: "coming soon"; Williamstown: counseling site needs sign-in), and Oxbow's catalog is a Canva design no tool
could download. The human is chasing these (`data/manual_catalogs.csv` → `scripts/ingest_manual.py`).

**Phase 2 schools done (22):** arlington, bfa-fairfax, bfa-st-albans, blue-mountain, brattleboro, burlington, cabot, canaan,
cvu, colchester, craftsbury, danville, essex, fair-haven, green-mountain, hartford, harwood, hazen, lake-region, lamoille,
mill-river (titles only), north-country. **Remaining 32:** `python3 -I scripts/phase2_queue.py`.

---

## 2. Decisions made (with the human)

- **Requirements:** two proposals from the AOE memo of 2026-10-20 (Dr. Erin Davis), which is the authoritative source.
  The **Complete Recommendation** applies to the Class of 2033 and beyond; **Transitional Flexibility** applies to the Classes of 2031–32. Both total 22.5 credits.
  The 2025 survey benchmark column is ignored. ELA's "2 Intro / 2 Mastery" belongs to ELA.
- **Credit** is defined by proficiency, not seat time (SBE draft v8). One course can count toward more than one credit, and partial
  credit is allowed. So a course can map to several requirements.
- **Subject areas** are the memo's content areas (ELA, Mathematics, Science, Social Studies, Arts, World Language/ASL, Financial Literacy,
  PE & Health), plus **Interdisciplinary** (with the `bridges` it covers) and **Other** (with an `other_type`).
- **Credit mapping:** each course gets 0 or more `{requirement_id, strength: strong|possible, rationale}` entries, plus science domain,
  `has_lab` and `finlit_type`.
- **Standards documents** guide the rubric: science (NGSS mapping), math (Stats/Data Science, with and without CS), ELA
  (coverage and threshold models), and the all-content mapping spreadsheet, all in `sources/policy/standards/`.
- **Models:** Sonnet for extraction (it matched Opus on Arlington; a verbatim check catches its page-break slips). **Haiku for
  classification** (95% subject and 90% strong-mapping agreement with Sonnet on 214 pilot courses; disagreements were caused by
  rubric wording, not model skill).
- **One catalog year per school:** 2026-27, or the latest available. Only Cabot is semester-only.
- **Review artifacts go to Google Sheets**, because that is easier for the human. The repo CSV/JSON files stay the source of truth.

**Later project (out of scope):** schools "stacking" several credits on one course (multiple-credit options). The data supports it
because every course lists all its mappings.

---

## 3. Phase 3 in detail

### 3a. Requirements table — done
`data/requirements.csv`: one row per requirement ID with credits under each proposal, plus notes from the standards documents.

| ID | Complete 2033+ | Transitional 2031–32 |
|---|---|---|
| ELA-INTRO / ELA-MASTERY | 2.0 / 2.0 | 2.0 / 2.0 |
| MATH-ALG1, MATH-GEOM, MATH-PATHWAY | 1.0 each | 1.0 each |
| MATH-STATS-ALG2 | 1.0 | 0 (moves to electives) |
| SCI-PHYS (Chem, Physics or integrated), SCI-LIFE, SCI-EARTH | 1.0 each | 1.0 each |
| SS-USHIST, SS-CIVICS, SS-WORLD | 1.0 each (assumed split) | same |
| ARTS | 1.5 | 1.5 |
| WL (World Language or ASL) | 1.0 | 0 |
| FINLIT (stand-alone) | 0.5 | 0.5 |
| PE / HEALTH | 1.5 / 1.0 | 1.5 combined |
| ELECTIVE | 3.0 | 6.0 |

### 3b. Classification rubric — v0.2
- **Pilot:** Danville (64 courses) and Lake Region (150), with Haiku and Sonnet on v0.1. v0.2 fixed the wording problems and added rules for
  equivalency credit, mixed science, paired Humanities courses, dual enrollment, the Financial Literacy department, Speech/Debate, and labs.
- **Verification:** Haiku on v0.2 (`*.haiku2.json`) vs Sonnet: **99% subject, 99% strong-mapping agreement** (214 courses).
- **Reading the human's answers back:** export the Sheet as CSV with Drive `download_file_content` (`exportMimeType: text/csv`), save it as `phase3/gold/labels.csv`.
  This session has only the Drive connector, so the Sheet can't be edited in place.
- **Validator:** `scripts/check_phase3.py <id> [file]`. **Comparison:** `scripts/phase3_review_sheet.py A B <ids...>`.

### 3c. Human calibration — first round done (2026-11-14)
- Answer key: `phase3/gold/labels.csv` (97 scored, 3 CTE skipped). Scorer: `python3 -I scripts/phase3_score.py <run...>`.
- **Haiku v0.2: 76% exact, 82% strong-set match. Haiku v0.3 (`*.haiku3.json`): 85% exact, 96% strong-set match.**
  Caveat: v0.3 was tuned on the same 97 courses, so the true accuracy is probably lower. Check it on a new school before running at scale.
- What the human taught us: be generous (descriptions undersell courses). Use the school's core sequence to infer grade levels.
  Algebra II always counts for STATS-ALG2, and Pre-Algebra counts as a math elective. Don't trust catalog equivalency claims
  (Woodworking for English) — record them in `catalog_claims`. Forensics isn't life science. Programming may be a math elective.
- **Holdout spot-check:** Montpelier (not used for tuning), 30 courses, CTE excluded: [sheet](https://docs.google.com/spreadsheets/d/19nHEialU0fZyoBNCViYmuNIuLMH2IYurcAn7T4gCZcY/edit), local `phase3/gold/montpelier_spotcheck.csv`. Classified with v0.3.1 (`phase3/pilot/montpelier-high-school.haiku3.json`). Score with `--labels montpelier_labels.csv`.
- v0.3.1 tweaks were made after scoring and are untested: CAD/welding keep ARTS `possible`, GPS independent studies keep their
  English `possible` mapping, Business Math that is mostly personal finance → FINLIT `strong`.

#### Original plan
1. Build a **Google Sheet** of about 100 courses from the pilot schools. It includes every model disagreement, plus a stratified
   sample across subject areas and the tricky types: Interdisciplinary, equivalency credit, CTE, Environmental Science,
   Algebra II, financial content, and courses without descriptions.
2. Columns: course, department, grades, description, the model's subject and mappings, then human columns:
   **agree? / correct subject / correct mappings / note**.
3. The human's answers become the **answer key** (`phase3/gold/labels.csv`, synced from the Sheet).
4. Score models against it: subject accuracy, strong-mapping precision and recall per requirement.
   **Target:** at least 90% subject accuracy and at least 90% strong-mapping precision on core requirements.
5. Revise the rubric (v0.3, v0.4 and so on) until the target is met. Re-score on the answer key only (cheap), and spot-check one new school.
6. Low-confidence courses at scale go to a review queue, not to a person one by one: a Sheet tab of `confidence = low`
   courses plus a random 3% audit.

### 3d. School profile pass (all 56 schools, Haiku)
This pass reads only the catalog's front matter (about the first 15 pages, or the policies section). It can run before the Phase 2 backlog is finished.
Output `phase3/profiles/<id>.json`:
- `grading_system`: credit | proficiency | hybrid, plus a supporting quote. The human expects hybrids. Our earlier count of
  "no credits printed" overstated how many are purely proficiency-based.
- `schedule`: 4x4 block / A-B day / trimester / traditional periods / other; `courses_per_term`; `terms_per_year`.
- `credit_definition`: what one credit means (e.g. a full-year course, two semesters, or two trimesters). This flags schools where a
  "credit" is another school's 0.5.
- `max_credits_4yr` (computed as courses per term × terms × 4 × credits per course) versus `local_required_credits`: how much room each
  schedule leaves for the new requirements.
- `local_grad_requirements` normalized to credits (Brattleboro's 96-point scale, BFA Fairfax's class counts, Danville's semesters).
- `catalog_discloses`: shows fulfills/requirement info? prerequisites? credits? grade levels? (Also computed from Phase 2 coverage.)
- `cte_center` the school sends students to; `flexible_pathways_listed` (dual enrollment, early college, VTVLC, work-based learning).

### 3e. Classify all schools
- Haiku, about one school per agent, at most 4 in parallel (to limit damage when a usage limit hits). Output `phase3/classified/<id>.json`
  with `rubric_version`.
- Merge to `phase3/classified.csv` (one row per course × mapping).
- Re-run only schools whose rubric version or Phase 2 data changed.

---

## 4. Gap analysis and report (Phase 4)

### 4a. Metrics per school, under each proposal (complete and transitional)
For each requirement:
- **Covered** — at least 1 `strong` course, with enough offered credits to meet the amount (e.g. ARTS needs ≥1.5 credits offered).
- **Covered only via `possible`** — e.g. Environmental Science for Earth/Space, or an equivalency-credit elective.
- **Covered only via a pathway** — CTE embedded credit, dual enrollment, online (VTVLC).
- **Gap** — nothing found.
- **Unknown** — the catalog lacks descriptions (Mill River), or the school hasn't been extracted.

Rules from the human's review (v0.3):
- **Algebra II** is mapped only to MATH-STATS-ALG2. Under the Transitional plan (which needs 0 STATS-ALG2 credits) it may fill MATH-PATHWAY.
  In general, a course mapped to a more specific math requirement may also fill MATH-PATHWAY, but each course counts once.
- **Integrated/mixed science** (and similar, e.g. CAD with geometry content) may count as **partial credit** toward each domain it covers.
  Report these separately from full coverage.
- **Catalog claims vs. content:** `catalog_claims` records what the school says a course fulfills (e.g. Woodworking for English or
  Science). Coverage uses content-based mappings only. A separate statistic counts courses where the claim and the content disagree.
- **Flexible pathways** (`other_type: Flexible pathway`) could count as any credit. List them per school but don't use them to close gaps.
- **Below high-school-level math** (Consumer Math, Essentials of Math, Workplace Math) stays `possible`. Flag it for review by a math specialist.

Also per school:
- count of requirement gaps
- list of new courses needed
- whether the schedule has room (profile `max_credits_4yr` minus 22.5)

### 4b. Statewide statistics
- Share of schools with a gap, per requirement and per proposal. Expected hot spots: stand-alone FINLIT, HEALTH 1.0,
  MATH-STATS-ALG2, SCI-EARTH, WL at small schools, SS-CIVICS as its own course.
- **Disclosure statistics for change management:** % of courses (and of schools) whose catalog states what the course *fulfills*
  (currently 23% of courses), states prerequisites (54%), credits (70%) and grade levels (74%); and % of schools whose catalogs mention labs.
- Grading systems (credit / proficiency / hybrid) and schedule types, with the schools in each.
- Credit-meaning differences and courses per term, with the "room to add requirements" distribution.
- CTE and flexible-pathway visibility: which catalogs list their CTE center's programs, and how embedded credit is described.
- Breakdowns by school size (enrollment), SU/SD and county.

### 4c. Report
Audience: AOE, the SBE and stakeholders. Format: a shareable doc or page, with charts, plus a downloadable data appendix (Google Sheets).
1. **Executive summary** — the headline gaps under each proposal; the transitional vs. complete difference.
2. **Methods and limits** — catalogs as evidence (they describe offerings, not enrollment or quality); model classification with
   human calibration; the accuracy figures; unknowns.
3. **What catalogs disclose today** — the fulfills / prerequisites / credits statistics (the change-management baseline).
4. **School systems** — grading systems, schedules, what a credit means, room in the schedule.
5. **Coverage by requirement** — one section per content area, with schools at risk and the policy questions
   (Environmental Science, labs, Algebra II stats coverage, stand-alone FINLIT, Health 1.0).
6. **Pathways** — CTE, dual enrollment, online, equivalency credit.
7. **School-by-school appendix** — a one-row scorecard per school, linked to the data.
8. **Recommendations / open policy questions.**

---

## 5. Order of work and cost control

1. Finish v0.2 verification, then build the Google Sheet answer-key review (human).
2. Calibrate the rubric to target on the 2 pilot schools, then spot-check 1–2 more (e.g. Burlington, Hazen).
3. **Run the school profile pass** on all 56 (Haiku, front matter only — cheap).
4. Classify the 22 extracted schools, then produce a **draft gap analysis and report on those 22** to test the whole pipeline.
5. Fix whatever the draft reveals (missing fields and so on), then **finish Phase 2 for the remaining 32 more cheaply**:
   - Re-export Google Doc catalogs as **Markdown** (keeps the heading structure, avoids PDF column and page-break problems).
   - Use **block labeling**: a script splits the catalog into course blocks; the model labels only the fields and the block line range;
     the script copies descriptions verbatim. This cuts output tokens severalfold and makes Haiku viable. Test against existing Sonnet extractions first.
6. Classify the remaining schools, then produce the final report.

Cost notes:
- Each Sonnet extraction cost about 100–250k tokens, mostly spent retyping descriptions. Classification on Haiku costs about 140k per school.
- Run at most about 4 agents in parallel. Commit after each school.

---

## 6. Open questions for the human

1. **Labs:** does "with labs" apply to all three sciences? Most catalogs don't mention labs even for core courses. Is that a finding in itself?
2. **Environmental Science:** does it count toward Earth/Space, Life or neither? (AOE's science model: "1 Credit of ??".)
3. **Social Studies:** is it 1.0 each for US History, Civics and World Studies? Does World Geography count as World Studies?
4. **FINLIT stand-alone:** is a semester Personal Finance course required, and does content embedded in Consumer Math not count?
5. **Equivalency credits** ("Horticulture may fulfill a science credit"): count them in the gap analysis or report them separately?
6. **CTE:** report it only as a pathway, or also collect the career centers' own catalogs (a separate project)?
7. **Mill River:** fetch its ~150 linked syllabi for descriptions, or treat it as titles-only?

---

## 7. Lessons learned (for future sessions)

- `education.vermont.gov` blocks automated access with HTTP 403. Don't try to get around it; ask the human to upload documents.
- Many search hits belong to other states' schools with the same name (Lake Region ME, Milton MA, Danville VA, Twin Valley PA). Always confirm the school.
- Several schools' old domains now serve spam (lelandandgray.org, ovuhs.org).
- Google Doc catalogs: export instead of printing to PDF. Published `/pub` docs can't be exported; save the HTML instead.
- PDF text: use both the layout and reading-order versions (`extract_text.py` writes both). The verbatim check in `merge_phase2.py` accepts either.
- Parallel agents share one scratchpad, so give each agent its own subfolder. Never let agents run `merge_phase2.py` without `--check`.
- A usage limit can kill every running agent at once. Keep waves small and commit after every school. `phase2_queue.py` picks up anything unfinished.
