---
name: find-catalog
description: Phase 1 — find, verify and download the current course catalog (program of studies) for one or more Vermont public high schools listed in data/schools.csv, writing phase1/results/<school_id>.json for each.
---

# Find a school's course catalog

Input: one or more `school_id`s from `data/schools.csv`. Handle each school independently and finish
(write its JSON) before starting the next. Do not commit — the person running the batch commits.

## Target
The school's **course catalog** for grades 9–12. Names vary: "Program of Studies", "Course Offering Booklet",
"Course Guide", "Course Description Guide", "Curriculum Guide", "Course Offerings", "Course Selection Guide",
"Academic Handbook". A student handbook is NOT a catalog unless it contains course descriptions.

**Year:** the current school year is **2026-27** (check date Nov 2026). Make the 2026-27 catalog primary.
If only an older one exists, make the most recent one primary, set `confidence` no higher than `medium`,
and say so in `issues`. If you also come across the 2025-26 catalog, download it too (Phase 2 may compare years),
but don't spend long hunting for older years.

## Search procedure
1. Find the official school website and the SU/SD website. If a school has more than one domain, record the one its pages actually use.
2. Look in: Academics, School Counseling / Guidance / Direction Center, Students, Curriculum, Course Selection, Registration, and the site map.
3. Web search: `"<school name>" program of studies`, `"<school name>" course catalog 2026-2027`, `site:<domain> course descriptions`, filetype:pdf variants.
4. **Always** check whether courses also live in a course-planning tool (Naviance, Xello, SchoolLinks, SchoolInfoApp, MajorClarity, PowerSchool/Infinite Campus course catalog). Record the tool in `course_planner`.
5. **Confirm every hit is this school.** Search results and their summaries are often wrong (e.g. another district's doc). Open the document and check the school name on it before using it.
6. **Also note the graduation requirements document** if you see it (Phase 3 needs it): put its URL in `grad_requirements_url`; download it if it's a public file.
7. **Verify the supervisory union / district** (step below).

## Supervisory union / district
Record the official name as the SU/SD itself uses it (website header/footer, About page, superintendent's office page).
`su_sd_matches_list` compares the **entity**, not the exact wording, against the `su_sd` column of schools.csv:
"Champlain Valley School District" vs "Champlain Valley Supervisory Union" = same entity → `true`, explain the naming in `su_sd_note`.
Set `false` only if the school belongs to a different SU/SD (e.g. after a merger or rename). A single-district
supervisory district may have just one website — that's fine as the source.

## Download copies → `catalogs/<school_id>/`
- Name files `catalog_<year>.<ext>` (e.g. `catalog_2026-27.pdf`); grad requirements as `grad_requirements_<year>.<ext>`.
- PDF: `curl -sSL -o <file> "<url>"`; verify and count pages with `pdfinfo <file>` (don't trust `file` for page counts).
- Google Doc (`/document/d/<ID>/edit`): `https://docs.google.com/document/d/<ID>/export?format=pdf`.
- **Published** Google Doc (`/document/d/e/2PACX-.../pub`): save the HTML with curl. Export won't work on these.
- Google Drive file: `https://drive.google.com/uc?export=download&id=<ID>`.
- Webpage(s): save the main HTML. If the catalog spans many pages or needs JavaScript, don't crawl it — describe it in `issues`.
- Sign-in required (HTTP 401/403 from Google etc.): don't download; record it in `issues`.
- Never spoof user-agents or bypass bot protection. Skip files over 50 MB (note them).
- Put scratch/temporary files in `catalogs/<school_id>/_scratch/` and delete that folder when done.

## Output: write `phase1/results/<school_id>.json` (valid JSON; use `null` for anything not applicable)
```
{
  "school_id": "...",
  "school_name": "...",
  "school_website": "https://...",
  "su_sd": "official SU/SD name",
  "su_sd_matches_list": true,
  "su_sd_note": "naming differences / mergers, or null",
  "su_sd_source_url": "https://...",
  "catalog_status": "found | partial | outdated_only | not_found | no_public_catalog | not_a_high_school",
  "catalog_title": "title as printed",
  "catalog_url": "the link a person clicks on the official school/district site (or the best URL if not linked)",
  "direct_file_url": "direct file URL if different from catalog_url (after redirects / underlying Drive doc), else null",
  "linked_from_official_site": true,
  "format": "pdf | google_doc | google_doc_published | google_drive_file | google_site | webpage | course_planner_app | other",
  "web_host": "site/file host if notable, e.g. ParentSquare, Finalsite, Google Docs; else null",
  "course_planner": "Naviance | Xello | ... | none found",
  "school_year": "2026-27 | 2025-26 | ... | unknown",
  "coverage": "full_year | single_semester | partial | unknown",
  "includes_descriptions": "all | some | none",
  "local_copies": [{"path": "catalogs/<id>/catalog_2026-27.pdf", "year": "2026-27", "pages": 62, "size_mb": 1.9}],
  "grad_requirements_url": "https://... or null",
  "additional_urls": [{"url": "...", "what": "other versions, related pages"}],
  "evidence": [{"url": "...", "quote": "short quote supporting a not_a_high_school / not_found / no_public_catalog / SU claim"}],
  "school_status_notes": "closures, mergers, consolidations under discussion, or null",
  "confidence": "high | medium | low",
  "how_found": "navigation path, e.g. school site > Counseling > Program of Studies",
  "issues": "anything Phase 2 or the human should know",
  "searched": ["every page/query tried — always required"],
  "checked_on": "YYYY-MM-DD"
}
```

## Status guide
- `found`: current (2026-27) full catalog with descriptions.
- `partial`: current but incomplete (one semester only, titles without descriptions, some departments missing).
- `outdated_only`: only an older year is available.
- `not_found`: you searched thoroughly and found nothing public. `searched` must show the thoroughness.
- `no_public_catalog`: evidence the catalog exists but is not public (sign-in only, "see your counselor").
- `not_a_high_school`: the school doesn't operate grades 9–12 (e.g. tuitions students to an academy).
  NCES and district sites sometimes say "PK-12" for districts that only tuition high schoolers — check.

## Confidence guide
- **high**: official source, right school confirmed, current year, downloaded. For negative results: two independent official sources agree.
- **medium**: older year, partial, found only via search (not linked from the official site), or one official source for a negative result.
- **low**: unclear whether it's official, current, or the right school.

Note: education.vermont.gov (Agency of Education) blocks automated access — don't rely on it. District pages,
board minutes and state legislature PDFs are acceptable fallbacks.
