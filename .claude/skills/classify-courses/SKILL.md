---
name: classify-courses
description: Phase 3 — classify every course of one school (phase2/courses/<id>.json) by subject area and by which statewide graduation-requirement credits it could satisfy, writing phase3/classified/<id>.json. Rubric v0.3 (calibrated once against 97 human labels).
---

# Classify courses against Vermont's proposed graduation requirements

Rubric version: **v0.3**. Requirement IDs and credit amounts: `data/requirements.csv`
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
 "other_type": null,                       // only for Other: Computer Science | Business | Technology/Engineering | Family & Consumer Science | CTE program | Flexible pathway | Advisory/Support | Driver Ed | Other
 "credit_mappings": [                      // requirements this course could satisfy; [] if only a general elective
   {"requirement_id": "SCI-PHYS", "strength": "strong | possible", "rationale": "one short sentence citing the catalog wording"}
 ],
 "science_domain": null,                   // Science only: Chemistry | Physics | Integrated Physical | Life | Earth & Space | Environmental | Other
 "has_lab": "yes | no | unknown",          // Science only: 'yes' only if the catalog mentions labs/laboratory/hands-on investigations
 "catalog_claims": [],                     // requirement_ids the CATALOG says this course fulfills/may fulfill (from fulfills_text or description), whether or not you agree
 "finlit_type": null,                      // Financial content only: "stand-alone" | "embedded"
 "confidence": "high | medium | low"}
```
File: `{"school_id", "rubric_version": "v0.3", "classified_on", "model_note", "courses": [...]}` — one entry for **every** course in the phase2 file, same order.

`strength`: **be generous — the reviewer is.** Course descriptions are written hastily and undersell the course; judge
what the course is, not whether every standard is listed. **strong** = the catalog clearly shows this is the course for that requirement. **Every standard course named for the
requirement is `strong` by default, at any level (standard, honors, AP, IB, dual enrollment, summer)**: Algebra I, Geometry,
Pre-Calculus/Calculus (→ MATH-PATHWAY), Chemistry, Physics, Biology, Earth Science, US History, Civics/Government, World History,
French/Spanish/any language level, Health, PE, art/music/theatre courses. **possible** = could plausibly count but depends on content
not shown, on an "equivalency"/"may fulfill" statement, or on an unsettled policy question. Use `possible` only for real doubt,
never just because grades are missing or the course is a half-credit elective.

## Read the whole school first (v0.3)
Before classifying, skim the entire phase2 file (all courses + `graduation_requirements`) and note the school's **core sequence**:
which courses are required at each grade (e.g. "American Literature — all 9th graders", "World Literature — all 10th graders").
Use it to fill in missing grade levels: if grades 9 and 10 English are named core courses, the other English electives are
upper-level → ELA-MASTERY `strong`. Mention it in the rationale ("9/10 core = Am Lit/World Lit").

## Catalog claims vs. content (v0.3)
Record every requirement the catalog says a course fulfills in `catalog_claims`, but **map by content**. A school's
equivalency statement alone does not make a course count: Woodworking listed for "English, Science" credit → `catalog_claims`
["ELA-INTRO","SCI-PHYS"], mappings only what the content supports (ARTS `possible` for design/craft). Web programming (HTML/CSS)
listed as fine arts → no ARTS mapping. But design/craft courses with a fine-arts claim (CAD, welding art, creative
woodworking) keep ARTS `possible`, and independent studies that may be taken "for English credit" keep that `possible` mapping.
The report compares claims with content-based mappings.

## General rules (v0.2)
- **Labs do not change `strength`.** Record `has_lab` separately (`null` for non-science courses). `yes` if the catalog mentions labs,
  laboratory, lab investigations, experiments, or field investigations with data collection; `no` only if it says there is no lab; else `unknown`.
- **Equivalency credit outside CTE** ("may fulfill a science/fine arts/math credit") → keep the course's own subject area, put the
  claim in `catalog_claims`, and add a `possible` mapping only if the described content genuinely fits that requirement
  (Horticulture with plant biology → SCI-LIFE `possible`; Accounting → MATH-PATHWAY `possible`).
- **Mixed/integrated science** covering several domains (incl. Climate Science) → `science_domain: "Other"`, `possible` mappings to each
  domain covered (the gap analysis treats these as partial credit).
- **One primary requirement.** Map a course to the single requirement it is built for. Add a second mapping only when the course
  genuinely serves two (Interdisciplinary, combined PE/Health, Consumer Math = MATH-PATHWAY + FINLIT embedded). Algebra II maps
  to MATH-STATS-ALG2 only (the gap analysis lets it fill MATH-PATHWAY under the Transitional plan). A course `strong` for FINLIT
  does not also map to MATH-PATHWAY.
- **Flexible pathways** (independent study / independent learning / personalized projects that "can count as any credit") →
  Other, `other_type: "Flexible pathway"`, no mappings (the report counts them as "could count as any credit").
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
college composition → MASTERY. English electives where reading/writing is the
central work (composition, creative writing, film as literature, themed literature, screenwriting, nature writing), at grades 11–12
or upper-level by the school's core sequence → MASTERY `strong`, any credit size. Journalism/Yearbook/Public Speaking → `possible`. Reading/ELL support classes → Other/Advisory-Support unless credit-bearing English.

**MATH-ALG1** — Algebra I, Integrated Math 1, multi-year Algebra I sequences (each part `possible`).
**Pre-Algebra** → MATH-PATHWAY `strong` (not ALG1; it comes before Algebra I and counts as a math elective).
**MATH-GEOM** — Geometry, Integrated Math 2 (`possible` unless geometry content is described).
**MATH-STATS-ALG2** — Statistics, AP Statistics, Data Science, **Algebra II at any level → `strong`** (whether or not the
description mentions statistics — the stats unit is small and schools can easily ensure it). Science or CTE courses with substantial statistics content → `possible`.
**MATH-PATHWAY** (math elective) — courses where mathematical reasoning is the central, sustained work: Pre-Calculus, Calculus,
Trigonometry, Discrete Math, Pre-Algebra, Consumer/Workplace/Essentials Math (`possible` — may be below high-school level),
Accounting (`possible`), rigorous programming courses (AP CSA/CSP, C++, Java, Python, robotics programming) → `possible`
(more likely if Vermont adopts CS standards). Web page markup (HTML/CSS) and app-use courses → no math mapping.
Courses where math is incidental do NOT map.

**SCI-PHYS** — Chemistry, Physics, Physical Science, integrated physical science (any one counts; all `strong`). **SCI-LIFE** — Biology,
Life Science, AP Biology, Anatomy & Physiology, Botany (`strong`); Ecology, Zoology, Wildlife (`possible`). Forensics is NOT life
science unless biology content (DNA, anatomy) is described; criminal-justice content → SS-CIVICS `possible`. **SCI-EARTH** — Earth Science, Earth & Space, Astronomy, Geology (`strong` if broad
Earth/space systems content; narrow electives `possible`). **Environmental Science** → `science_domain: Environmental`,
map SCI-EARTH `possible` and SCI-LIFE `possible` (AOE's own model lists it as "1 Credit of ??"). Forensics, Marine Bio, etc. → domain + `possible`.
Always set `has_lab`.

**SS-USHIST** — US History, AP US History. **SS-CIVICS** — Civics, US/American Government, AP Gov. **SS-WORLD** — World History,
Global Studies, World Cultures, AP World/European History, Cultural/World Geography covering world regions and cultures → `strong`. Economics, Psychology, Sociology → general SS elective (no mapping), except
a course combining civics content → SS-CIVICS `possible`.

**ARTS** — visual art, music (ensembles, theory, technology), theatre, dance, media arts. Digital photography/film/graphic design → `strong` if
artistic creating/responding is central; CTE graphic-design programs → `possible`.

**WL** — any world language course at any level, ASL, heritage or AP language → `strong`. Language culture-only courses → `possible`.

**FINLIT** — stand-alone personal finance / financial literacy course → `strong`, `finlit_type: stand-alone` — including
"Business Math" or similar when the description is mainly personal finance (budgeting, banking, credit, taxes, insurance).
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
