---
name: classify-courses
description: Phase 3 — classify every course of one school (phase2/courses/<id>.json) by subject area and by which statewide graduation-requirement credits it could satisfy, writing phase3/classified/<id>.json. Rubric v0.1 (draft, to be calibrated against human labels).
---

# Classify courses against Vermont's proposed graduation requirements

Rubric version: **v0.1 (draft)**. Requirement IDs and credit amounts: `data/requirements.csv`
(AOE memo 2026-10-20: "Complete Recommendation" Class of 2033+ and "Transitional Flexibility" Classes of 2031–32).
Source standards documents (for judgment calls): `sources/policy/standards/*.md` and `standards_mapping_all_content.xlsx`.

Input: `phase2/courses/<id>.json`. Output: `phase3/classified/<id>.json`. Do not commit.
Judge from the course **name, department, description, grade levels, level, credits and `fulfills_text`** only.
Never assume content that isn't described. If the description is missing, classify from the name but cap `confidence` at `medium`.

## Output per course
```
{"course_index": 0,                       // position in the phase2 courses list
 "course_name": "...",                     // copied, for readability
 "subject_area": "ELA | Mathematics | Science | Social Studies | Arts | World Language/ASL | Financial Literacy | PE & Health | Interdisciplinary | Other",
 "bridges": [],                            // only for Interdisciplinary: e.g. ["ELA","Social Studies"]
 "other_type": null,                       // only for Other: Computer Science | Business | Technology/Engineering | Family & Consumer Science | CTE program | Advisory/Support | Driver Ed | Other
 "credit_mappings": [                      // requirements this course could satisfy; [] if only a general elective
   {"requirement_id": "SCI-PHYS", "strength": "strong | possible", "rationale": "one short sentence citing the catalog wording"}
 ],
 "science_domain": null,                   // Science only: Chemistry | Physics | Integrated Physical | Life | Earth & Space | Environmental | Other
 "has_lab": "yes | no | unknown",          // Science only: 'yes' only if the catalog mentions labs/laboratory/hands-on investigations
 "finlit_type": null,                      // Financial content only: "stand-alone" | "embedded"
 "confidence": "high | medium | low"}
```
File: `{"school_id", "rubric_version": "v0.1", "classified_on", "model_note", "courses": [...]}` — one entry for **every** course in the phase2 file, same order.

`strength`: **strong** = the catalog clearly shows this is the course for that requirement (e.g. "Biology", "Algebra I",
"fulfills civics requirement"). **possible** = could plausibly count but depends on content not shown, or on an unsettled policy question.

## Rubric by requirement
**ELA-INTRO / ELA-MASTERY** — core English courses. Grades 9–10 English → INTRO; grades 11–12 English, AP Language/Literature,
college composition → MASTERY. English electives (creative writing, film as literature, journalism) → MASTERY `possible`
if grades 11–12 and reading/writing is the central work; otherwise general elective. Reading/ELL support classes → Other/Advisory-Support unless credit-bearing English.

**MATH-ALG1** — Algebra I, Integrated Math 1, multi-year Algebra I sequences (each part `possible`).
**MATH-GEOM** — Geometry, Integrated Math 2 (`possible` unless geometry content is described).
**MATH-STATS-ALG2** — Statistics, AP Statistics, Data Science → `strong`. Algebra II → `strong` only if the description mentions
statistics/probability/data; otherwise `possible`. Science or CTE courses with substantial statistics content → `possible`.
**MATH-PATHWAY** (math elective) — courses where mathematical reasoning is the central, sustained work: Pre-Calculus, Calculus,
Algebra II, Trigonometry, Discrete Math, Consumer/Financial Math with real math content, rigorous Computer Science (AP CSA/CSP) → `possible` for CS.
Courses where math is incidental do NOT map.

**SCI-PHYS** — Chemistry, Physics, Physical Science, integrated physical science (any one counts). **SCI-LIFE** — Biology,
Life Science, AP Biology, Anatomy & Physiology (`possible`). **SCI-EARTH** — Earth Science, Earth & Space, Astronomy, Geology (`strong` if broad
Earth/space systems content; narrow electives `possible`). **Environmental Science** → `science_domain: Environmental`,
map SCI-EARTH `possible` and SCI-LIFE `possible` (AOE's own model lists it as "1 Credit of ??"). Forensics, Marine Bio, etc. → domain + `possible`.
Always set `has_lab`.

**SS-USHIST** — US History, AP US History. **SS-CIVICS** — Civics, US/American Government, AP Gov. **SS-WORLD** — World History,
Global Studies, World Cultures, AP World/European History; World Geography → `possible`. Economics, Psychology, Sociology → general SS elective (no mapping), except
a course combining civics content → SS-CIVICS `possible`.

**ARTS** — visual art, music (ensembles, theory, technology), theatre, dance, media arts. Digital photography/film/graphic design → `strong` if
artistic creating/responding is central; CTE graphic-design programs → `possible`.

**WL** — any world language level or ASL. Heritage/AP language → `strong`.

**FINLIT** — stand-alone personal finance / financial literacy course → `strong`, `finlit_type: stand-alone`.
Financial content embedded in another course (Consumer Math, Economics, Life Skills, Business) → `possible`, `finlit_type: embedded`
(the memo requires stand-alone content, so embedded mappings are reported but don't satisfy the requirement).

**PE / HEALTH** — PE, fitness, lifetime sports, unified PE → PE. Health, wellness with health content → HEALTH.
Combined "PE & Health"/"Wellness" courses → both, each `possible`.

**Interdisciplinary** — a course that is explicitly two subjects (Humanities = ELA + Social Studies; STEM blocks; "counts for English and SS credit")
→ `subject_area: Interdisciplinary`, list `bridges`, and add a mapping for each requirement it could serve.

**CTE programs** (`level: CTE`) → `subject_area: Other`, `other_type: CTE program`; map academic requirements only where
`fulfills_text` states embedded credit (e.g. "1 science credit" → SCI-* `possible` with the domain if stated).

**Programs** (dual enrollment, early college, independent study, work-based learning, online platforms) → `Other`, no mappings
unless the entry names specific academic credit.

## Process
1. Read the phase2 file. Work through courses in order; keep rationales short (≤ 20 words).
2. Write the output with a small script (valid JSON), then validate: `python3 -I scripts/check_phase3.py <id>`.
