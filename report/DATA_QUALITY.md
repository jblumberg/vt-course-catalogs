# Data Quality and Coverage — Vermont Public High School Course Catalogs

*Living notes for the final report's methods and limitations sections. Last updated 2026-11-15.*
*Per-school table: [`coverage_by_school.md`](coverage_by_school.md) (regenerate with `python3 -I scripts/coverage_table.py > report/coverage_by_school.md`).*

## Scope
- **57 regular public schools with grade 12** (NCES 2024-25), with their supervisory union or district. St. Johnsbury School is PK-8 and excluded, leaving **56 high schools**.
- **Out of scope:** CTE centers, independent schools and town academies. Courses that high-school catalogs list *for* CTE centers are kept, tagged `level = CTE`, and analyzed separately.

## Phase 1 — finding catalogs
| Outcome | Schools |
|---|---|
| Current (2026-27) catalog found | 44 |
| Only an older year found | 9 |
| Partial catalog | 1 |
| Nothing public | 2 (Enosburg Falls: "coming soon"; Williamstown: counseling site behind sign-in) |
| Catalog not downloadable | 1 (Oxbow: Canva design) |

- **Hand-found catalogs:** the human found several catalogs by hand: Bellows Falls, Cabot, Green Mountain, Leland & Gray, Mt. Anthony, North Country, Canaan and Poultney.
- **Every record carries a `retrieved_on` date.** Re-runs pick up newly found catalogs automatically.
- **education.vermont.gov blocks automated access.** AOE documents were supplied by the human.

## Phase 2 — course extraction (complete 2026-11-15)
- **54 schools extracted, 6,061 course records:** 5,566 school courses and programs, plus 495 CTE-center listings.
- **Not extracted:** Enosburg Falls and Williamstown, which have no catalog.
- **Oxbow:** graduation requirements only; no course list.
- **Verbatim text:** descriptions are copied verbatim from the catalog. An automatic check compares every description with the source text.

### What the catalogs tell a student (non-CTE courses, all schools)
| Field | Share of courses where the catalog states it |
|---|---|
| Description | **97%** |
| Grade levels | **71%** |
| Credits | **71%** |
| Length (semester/year) | **69%** |
| Course code | **54%** |
| Prerequisites | **46%** |
| What requirement the course fulfills | **23%** |

**Key findings for change management**
- **Fulfills statements:** only about **1 in 4 courses** says what graduation requirement it fulfills. AOE would like every catalog to include this.
  - Schools range from 0% (Cabot, Craftsbury, Poultney, Rivendell) to over 80% (Essex, Stowe, Windsor, Leland & Gray).
  - *Caveat:* `fulfills_text` captures any requirement statement the catalog makes. At U-32 it is mostly the standards (SLO) codes a course addresses, not a credit area.
- **Prerequisites:** fewer than half of courses state prerequisites. Missing prerequisite information makes it hard to plan flexible pathways and CTE schedules.
- **Credits:** 29% of courses state no credit value.
  - **0–10% of courses show credits** at 15 schools: Arlington, BFA Fairfax, Cabot, Danville, Green Mountain, Harwood, Lamoille, Mt. Abraham, Mt. Mansfield, Peoples Academy, Randolph, Richford, Rivendell, Twinfield and U-32.
  - Several of these (Mt. Mansfield, U-32, Mt. Abraham, Randolph, Twinfield) describe themselves as proficiency-based.
  - The **school profile pass** (planned) will classify each school as credit, proficiency or hybrid. Don't read "no credits printed" as "proficiency-based" until then.
- **What "a credit" means varies:**
  - Brattleboro uses a 96-point scale.
  - Danville counts semesters.
  - BFA Fairfax counts classes.
  - Several catalogs print "0.5 credit per year" or "1 credit" for a semester course.
- **Stated local graduation totals** run from 21.5 (Northfield) to 34 (Peoples Academy). 12 schools state no total.

### Schools with thin or missing data
| School | Problem | What would fix it |
|---|---|---|
| Oxbow | Catalog is a Canva design; only the school profile was downloadable | Human downloads the PDF to `catalogs/oxbow-union-high-school/` |
| Rivendell | Titles only (38); descriptions are on ~60 Google Site subpages | Download the subpages, then re-run |
| Mill River | Titles only (116); descriptions are in ~150 linked syllabi | Download the syllabi, then re-run |
| Cabot | Partial (16 courses, half without descriptions) | Fuller catalog |
| Twinfield | Google Site; the agent read the 13 section pages directly | Save the pages under `catalogs/` |
| North Country | Partial | Review |
| Woodstock | The guide has no graduation-requirements section (its table of contents lists one) | Board policy document |

### Catalog year caveats
- **Older catalogs:** Bellows Falls (2024-26), Leland & Gray (2025-26), Mt. Anthony (2025-26), Cabot, Canaan, Green Mountain and North Country (2025-26).
- **Quarry Valley district catalog:** Poultney, Proctor and West Rutland share one undated catalog, judged to be about 2025-27. It is stored once, in Proctor's folder.
  - Poultney was re-extracted from it, replacing a 2022-23 catalog.
  - Graduation requirements come from the 2026-27 district handbook.
- **Draft-quality catalogs:** Windsor's 2026-27 catalog may be a draft (its metadata says "In Progress" and some labels still say 2025-26). Montpelier's first page is a placeholder.
- **Courses offered only in alternate years:** these are kept, with an `offering_note`, and can be filtered.

### CTE listings
High-school catalogs list CTE programs very differently:
- **Full descriptions with embedded credits:** Springfield/River Valley, Twin Valley/Windham.
- **Names only:** many schools.
- **Not named at all:** e.g. Leland & Gray, Spaulding, Winooski, Vergennes.

So CTE counts per school reflect how the catalog presents them, not how many programs students can actually reach.

### Known false alarms in the verbatim check
A few schools still show "not verbatim" or "dropped text" warnings. The extraction agents traced these to PDF text-layer quirks and confirmed the descriptions by hand:
- drop-cap first letters split from their word
- two-column pages interleaving text
- running page footers inside descriptions that cross a page break
- zero-width characters used as spaces

This affects Blue Mountain, Canaan, Hartford, Leland & Gray, Mt. Mansfield, Randolph, Rutland, Stowe, Twin Valley, Windsor and Woodstock.

## Phase 3 — classification accuracy (so far)
- **Models:** courses are classified by Haiku using rubric v0.3.2 (`.claude/skills/classify-courses/SKILL.md`).
- **Human answer key:** 97 pilot courses from Danville and Lake Region.
  - Rubric v0.2: 76% exact agreement.
  - Rubric v0.3: **85% exact, 96% on strong credit mappings.** This was tuned on the same courses, so it is likely optimistic.
- **Held-out check:** 30 Montpelier courses, not used for tuning. The human agreed on **28/30 (93%)**. Both misses were flexible pathways, which led to the `FLEX-ANY` code.
- **The human's judgment:** v0.3 is about as good as possible, because AOE does not yet define each credit area precisely.
- **Catalog claims vs. course content:** schools sometimes award core credit by equivalency (e.g. Woodworking for English or Science credit; web programming for fine arts).
  - The classification records the catalog's claim separately (`catalog_claims`) from a content-based mapping.
  - The report can count where they disagree.

## Phase 3d/3e — profiles and classification (complete 2026-11-15)
- **Profiles:** 54 schools, by Haiku (`phase3/profiles.csv`).
  - Grading systems: 43 hybrid, 5 proficiency-only (Mt. Mansfield, U-32, Twinfield, BFA Fairfax, Harwood), 4 credit-only (Otter Valley, Oxbow, Peoples Academy, Stowe) and 2 not stated (Cabot, Rivendell).
  - Stowe moved from a 4-point proficiency scale to a 100-point scale in 2025-26.
- **Schedules are poorly documented:**
  - Only 19 of 54 catalogs say how many classes a student takes at once, and 20 don't describe the schedule.
  - "Share of schedule needed for local requirements" is computable for 15 schools. 4 of those give impossible results (>100%), flagged `INCONSISTENT - verify`.
  - Treat the schedule-capacity numbers as needing human verification.
- **Classification:** all 53 schools with courses (6,061 records), by Haiku with rubric v0.3.2.
  - Mill River and Rivendell were classified from titles only.
  - Cabot's catalog is a 16-course partial, so its "gaps" are data gaps.
  - South Burlington's Psychology description is garbled in the source and was classified from the name.
- **Catalog claims vs. content:** 904 courses carry an explicit claim of what they fulfill. For 77 (9%), the content-based mapping doesn't support the claim.
- **Labs:** of 664 science courses, 418 (63%) mention labs or hands-on investigation; the rest don't say.
- **Algebra I caveat:** 15 schools reach Algebra I only through "possible" courses, mostly Integrated Math 1 or Algebra I split over two courses (Part A/B).
  - This is a policy question (does Integrated Math 1 count as Algebra I?), not necessarily a gap.
  - At least one school (Essex, levelled "Algebra I 100/200") is a classifier inconsistency to correct.
