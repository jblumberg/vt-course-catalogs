---
name: find-catalog
description: Phase 1 — find, verify and download the current course catalog (program of studies) for one or more Vermont public high schools listed in data/schools.csv, writing phase1/results/<school_id>.json for each.
---

# Find a school's course catalog

Input: one or more `school_id`s from `data/schools.csv`. Handle each school independently.

## Target
The school's **course catalog** for grades 9–12 — it may be called "Program of Studies", "Course Guide",
"Course Description Guide", "Curriculum Guide", "Course Offerings", "Academic Handbook", "Course Selection Guide".
Prefer the **2025-26** catalog; if the 2026-27 catalog is already published, record it as the primary and note the 2025-26 one in `additional_urls`.
A student handbook is NOT a catalog unless it actually contains course descriptions.

## Search procedure (stop when you find a strong match, but always do step 5)
1. Find the school's official website (and the SU/SD website). Note both.
2. Look in the obvious places: Academics, Counseling / School Counseling / Guidance, Students, Curriculum, "Course Selection", Registration.
3. Web search: `"<school name>" program of studies`, `"<school name>" course catalog 2025-2026`, `site:<school domain> course descriptions`, and filetype:pdf variants.
4. Check whether courses live in a course-planning tool (Naviance, Xello, SchoolLinks, SchoolInfoApp, MajorClarity, "Course Catalog" in PowerSchool/Infinite Campus, or an embedded Google Site). Record the tool name.
5. **Verify the supervisory union / supervisory district** from the school or district website (footer, "About", superintendent page). Compare with `su_sd` in schools.csv.

## Download a copy
Save into `catalogs/<school_id>/` (create it):
- PDF: download with curl (`curl -sSL -o catalogs/<id>/catalog_<year>.pdf "<url>"`), then confirm with `file` that it really is a PDF.
- Google Doc: try `https://docs.google.com/document/d/<DOC_ID>/export?format=pdf`. Google Drive file: `https://drive.google.com/uc?export=download&id=<FILE_ID>`. If it needs sign-in, note it.
- Webpage(s): save the main HTML (`catalog_<year>.html`). If the catalog spans many pages or needs JavaScript, don't crawl it all — note it in `issues` (Phase 2 will handle it).
Do not spoof user-agents or bypass bot protection. Don't download anything larger than 50 MB (note it instead).

## Output: write `phase1/results/<school_id>.json`
```json
{
  "school_id": "",
  "school_name": "",
  "school_website": "",
  "su_sd": "",                       // as verified (official name)
  "su_sd_matches_list": true,         // false if it differs from data/schools.csv
  "su_sd_source_url": "",
  "catalog_status": "found",          // found | partial | not_found | no_public_catalog | not_a_high_school
  "catalog_title": "",
  "catalog_url": "",
  "format": "pdf",                   // pdf | google_doc | google_drive_file | google_site | webpage | course_planner_app | other
  "platform": "",                     // e.g. Naviance, Xello, Finalsite, Google Sites (if relevant)
  "school_year": "2025-26",           // as stated on the document; "unknown" if not stated
  "additional_urls": [{"url": "", "what": ""}],
  "local_copy": "catalogs/<id>/catalog_2025-26.pdf",   // null if not downloaded
  "pages_or_size": "",                // e.g. "48 pages" or "1.2 MB" or "~30 web pages"
  "includes_descriptions": true,      // does it have course descriptions, not just titles?
  "confidence": "high",               // high | medium | low
  "how_found": "",                    // the path: e.g. "school site > Counseling > Program of Studies"
  "issues": "",                       // anything Phase 2 or the human should know (outdated, login needed, scanned image, partial, broken link, multiple versions)
  "searched": ["places/queries tried — required when not_found"],
  "checked_on": "YYYY-MM-DD"
}
```
(Omit the `//` comments in the real file — it must be valid JSON.)

## Confidence guide
- **high**: official school/district host, clearly the current catalog with course descriptions, downloaded.
- **medium**: right school but older year, missing descriptions, partial, or third-party host.
- **low**: unclear if current/official, or only fragments found.

## Special cases
- PK-12 / 6-12 / 7-12 schools: only the high-school (9–12) catalog matters.
- If the school doesn't actually operate a high school (e.g. students are tuitioned to an academy), use `not_a_high_school` and explain.
