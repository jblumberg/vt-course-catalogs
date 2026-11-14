---
name: classify-courses
description: Phase 3 — classify every course of one school (phase2/courses/<id>.json) by subject area and by which statewide graduation-requirement credits it could satisfy, writing phase3/classified/<id>.json. Rubric v0.2 (draft, to be calibrated against human labels).
---

# Classify courses against Vermont's proposed graduation requirements

Rubric version: **v0.2 (draft)**. Requirement IDs and credit amounts: `data/requirements.csv`
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
File: `{"school_id", "rubric_version": "v0.2", "classified_on", "model_note", "courses": [...]}` — one entry for **every** course in the phase2 file, same order.

`strength`: **strong** = the catalog clearly shows this is the course for that requirement. **Every standard course named for the
requirement is `strong` by default, at any level (standard, honors, AP, IB, dual enrollment, summer)**: Algebra I, Geometry,
Pre-Calculus/Calculus (→ MATH-PATHWAY), Chemistry, Physics, Biology, Earth Science, US History, Civics/Government, World History,
French/Spanish/any language level, Health, PE, art/music/theatre courses. **possible** = could plausibly count but depends on content
not shown, on an "equivalency"/"may fulfill" statement, or on an unsettled policy question.

## General rules (v0.2)
- **Labs do not change `strength`.** Record `has_lab` separately (`null` for non-science courses). `yes` if the catalog mentions labs,
  laboratory, lab investigations, experiments, or field investigations with data collection; `no` only if it says there is no lab; else `unknown`.
- **Equivalency credit outside CTE** ("may fulfill a science/fine arts/math credit", "counts as English or elective") → keep the course's
  own subject area (e.g. Woodworking = Other/Technology), add a `possible` mapping to the stated requirement; if the science domain isn't
  stated, choose the closest domain and say so in the rationale.
- **Mixed/integrated science** covering several domains → `science_domain: "Other"`, `possible` mappings to each domain covered.
- **Paired "Humanities" courses** (separate English and Social Studies course records that run together) → classify each record in its
  own subject (English → ELA, history → Social Studies). Use Interdisciplinary only when ONE course record awards both subjects' credit.
- **Arts courses with a social-studies "equivalency" note** → subject Arts, ARTS `strong`, plus the SS mapping `possible`.
- **Dual-enrollment / college courses** are classified by their subject (only the program-level entries are Other).
- **Stand-alone Financial Literacy / Personal Finance courses** → subject `Financial Literacy` whatever department lists them.
  Accounting and general business courses are NOT financial literacy (no FINLIT mapping).
- **Public Speaking / Speech / Debate / Journalism** → subject ELA, ELA-MASTERY `possible` (if grades 9–10 only, ELA-INTRO `possible`).
- **Missing grade levels** don't block an ELA mapping — use `possible` and say "grades not stated".
- **Credit size** (0.25, 0.5, 1) does not affect mappings; the gap analysis adds credits up later.
- **Local-only requirements** (a school's own required courses like "Technology Applications", "Senior Project") → map only to
  statewide requirements they genuinely fit; otherwise no mapping.
- **PE-HEALTH-COMBINED** is computed later from PE + HEALTH mappings — never assign it directly.

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

**SCI-PHYS** — Chemistry, Physics, Physical Science, integrated physical science (any one counts; all `strong`). **SCI-LIFE** — Biology,
Life Science, AP Biology (`strong`); Anatomy & Physiology, Ecology, Zoology (`possible`). **SCI-EARTH** — Earth Science, Earth & Space, Astronomy, Geology (`strong` if broad
Earth/space systems content; narrow electives `possible`). **Environmental Science** → `science_domain: Environmental`,
map SCI-EARTH `possible` and SCI-LIFE `possible` (AOE's own model lists it as "1 Credit of ??"). Forensics, Marine Bio, etc. → domain + `possible`.
Always set `has_lab`.

**SS-USHIST** — US History, AP US History. **SS-CIVICS** — Civics, US/American Government, AP Gov. **SS-WORLD** — World History,
Global Studies, World Cultures, AP World/European History; World Geography → `possible`. Economics, Psychology, Sociology → general SS elective (no mapping), except
a course combining civics content → SS-CIVICS `possible`.

**ARTS** — visual art, music (ensembles, theory, technology), theatre, dance, media arts. Digital photography/film/graphic design → `strong` if
artistic creating/responding is central; CTE graphic-design programs → `possible`.

**WL** — any world language course at any level, ASL, heritage or AP language → `strong`. Language culture-only courses → `possible`.

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
