---
name: extract-courses
description: Phase 2 — extract every course from one Vermont high school's downloaded catalog into phase2/courses/<school_id>.json (one record per course, plus the catalog's stated graduation requirements).
---

# Extract courses from one school's catalog

Input: a `school_id` that `python3 -I scripts/phase2_queue.py` lists as READY. Do not commit — the batch runner commits.

## Steps
1. Read `phase1/results/<id>.json` (catalog status, year, issues) and the school's row in `data/schools.csv`.
2. Run `python3 -I scripts/extract_text.py <id>`. It writes `phase2/text/<id>.txt` with `=== PAGE n ===` markers and prints
   which source file(s) it used (there may be several, e.g. a main catalog plus a 9th-grade guide — extract from all; if the same course appears in both, keep one record), `source_retrieved_on`, and `low_text_units` (pages with almost no text).
   - If low-text pages look like they hold courses (scanned images), read those pages straight from the PDF with the Read tool (`pages: "12-15"`).
   - If the text is garbled (multi-column layout mixing two courses), re-read those pages from the PDF with the Read tool.
   - If Phase 1 said the catalog is spread over many webpages, follow the links from the saved page and fetch each course/department page (no crawling beyond the catalog).
3. Read the whole text in chunks. Extract **every course offered to grades 9–12** — including electives, AP, honors,
   dual enrollment / early college, online (VTVLC etc.), special education/alternative program courses, and courses at a
   CTE center **only if the catalog lists them with descriptions as part of the school's offerings** (mark `level: "CTE"`).
   Skip middle-school-only courses (grades 6–8).
4. Also capture the catalog's **graduation requirements** as stated (credits by subject, proficiencies, other requirements) — Phase 3 needs them.
5. Write `phase2/courses/<id>.json` (format below), then run `python3 -I scripts/merge_phase2.py --check <id>` and fix anything it flags.

## Rules
- **Phase 1 `issues` are instructions for you.** If they say to use only certain pages (e.g. a doc that contains an old duplicate copy), do that and say so in `extraction_notes`.
- **Shared district catalogs** (one document covering several high schools, e.g. Quarry Valley: Poultney / Proctor / West Rutland, courses tagged WRS/PrHS/PoHS): include only courses offered at THIS school. Put the school tag(s) in `notes`. If the catalog doesn't say which school offers a course, include it and set `offering_note: "district catalog - school not specified"`.
- **Combined middle/high catalogs** (grades 6–12 or 7–12): skip courses only for grades 6–8.
- **Consistency rules** (so counts are comparable across schools):
  - One heading covering two levels ("Chemistry (Standard & Honors)", "honors option available") → ONE record, `level` = the base level, `honors_option: true`.
  - One description shared by several named courses ("Math 1, Math 2, Math 3"; "Math A and B Honors") → split into one record per course, same description.
  - Credits: if the catalog gives only a general rule (e.g. "1 credit per year course, 0.5 per semester"), apply it: fill `credits` and set `credits_text` to `"derived: <rule>"`.
  - Grade levels / length stated in prose ("designed for juniors and seniors", "this semester course") count as stated.
  - `delivery`: default `in_person` for the school's own courses; only use other values when the catalog says so.
  - Programs with descriptions (dual enrollment, early college, work-based learning, independent study) → one record each, `notes: "program"`.
  - CTE center programs listed in the catalog → one record each, `level: "CTE"`, `provider` = center name, `description` if given (else null), and put any academic credit they earn ("earns 1 science credit") in `fulfills_text`. Phase 3 needs this.
  - "Description TBA" → include the course, `description: null`, `notes: "description TBA"`.
  - Labelled lines inside an entry (Grading:, Lab component:, Summer work:, Honors option:) → `notes`, not `description`.
  - Department-level requirement statements ("Civics is required", science sequence) → `graduation_requirements.other` AND the related course's `fulfills_text`.
  - Sub-headings within a department (Arts > Vocal Music) → `department` = top level, sub-heading in `notes`.
  - Strip leading labels ("Prerequisite:") from `prerequisites`.
  - `school_name` and `su_sd`: take from `data/schools.csv`.
- **Work efficiently:** don't retype long descriptions. Write a small helper script in your scratchpad that pulls text by line ranges from `phase2/text/<id>.txt` and builds the JSON, then fix up fields. `mkdir -p phase2/courses` first.
- **Copy text, don't write it.** `course_name` and `description` are taken from the catalog (fix only hyphenation/line-break artifacts). Never summarize, invent, or fill gaps from general knowledge. Missing → `null`.
- One record per distinct course. If a course has levels as separate entries (e.g. "English 10" and "English 10 Honors"), make separate records. If a year-long course is listed as A/B semesters with one description, make one record with `length: "year"`.
- A course listed in two departments → one record, `department` = first, note the other in `notes`.
- Keep `source_page` (the PAGE number from the text file) so a human can check.
- Field values that the catalog states in a structured way go in the structured fields; anything else useful goes in `notes`.

## Output: `phase2/courses/<school_id>.json`
```
{
  "school_id": "...",
  "school_name": "...",
  "su_sd": "...",
  "catalog_school_year": "2026-27",
  "source_files": ["catalogs/<id>/catalog_2026-27.pdf"],   // copy from extract_text.py output
  "source_retrieved_on": "YYYY-MM-DD",       // copy from extract_text.py output (this is how reruns detect new catalogs)
  "extracted_on": "YYYY-MM-DD",
  "extraction_status": "complete | partial | failed",
  "extraction_notes": "what was hard, pages skipped, scanned pages read visually, etc.",
  "graduation_requirements": {
    "total_credits": 24,                     // number or null
    "by_area": [{"area": "English", "credits": 4, "notes": "..."}],
    "other": ["e.g. Personal Learning Plan, proficiency-based requirements, community service"],
    "source_page": 5,
    "raw_text": "the requirements section copied verbatim (trim to the requirements themselves)"
  },
  "courses": [
    {
      "course_name": "Chemistry",
      "course_code": "SCI301",               // null if none
      "department": "Science",               // as the catalog names it
      "description": "verbatim",
      "grade_levels": [10, 11, 12],          // list of ints; [] if not stated
      "credits": 1.0,                        // number; null if not stated
      "credits_text": "1 credit",            // as printed, or null
      "length": "year | semester | quarter | trimester | variable | unknown",
      "prerequisites": "verbatim or null",
      "level": "standard | honors | AP | IB | dual_enrollment | early_college | CTE | online | special_program | other",
      "honors_option": false,                // true if an honors option exists within this same course
      "delivery": "in_person | online | hybrid | off_site | unknown",
      "provider": "school | VTVLC | college name | CTE center name | other; null if the school itself",
      "fulfills_text": "what requirement the catalog says it meets, e.g. 'Fulfills lab science credit' — verbatim, or null",
      "offering_note": "e.g. 'offered alternate years', 'offered 2026-27 only', or null",
      "source_page": 23,
      "source_file": "catalogs/<id>/catalog_2026-27.pdf",   // which file (matters when there are several)
      "notes": null
    }
  ]
}
```
(Remove the `//` comments — the file must be valid JSON.)

## When the catalog is incomplete
- Titles only, no descriptions → still list the courses (`description: null`), `extraction_status: "partial"`, explain.
- Single-semester or rotating offering list (e.g. Cabot) → extract what's there, `partial`, explain.
- Can't read the file → `extraction_status: "failed"`, `courses: []`, explain.
