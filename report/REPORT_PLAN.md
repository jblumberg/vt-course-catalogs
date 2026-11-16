# Report Plan — Vermont High School Course Catalogs vs. Proposed Graduation Requirements

*Written 2026-11-16, before compacting the context. A new session should read this, then `PLAN.md` and
`report/DATA_QUALITY.md`, and work from the files listed here. Status: all data phases are done and the
report is not started.*

## 0. Purpose and framing (from the human — keep this voice)
- **The reason for this report is to expose the tough issues** that AOE and the SBE must resolve in each subject area.
  It should also show how each possible decision would affect Vermont's high schools.
  - It is **not** a compliance audit, and it doesn't pick a winner on contested definitions.
  - For each issue it shows: what the catalogs show today, what the decision is, the options, and how many schools each option affects.
- **Catalogs show what a school offers, not what it actually runs.** We don't know how many sections run, or whether a course runs at all.
  - Future work: join with **Ed-Fi** data (sections and enrollment). Say this in the methods section and wherever a finding depends on it.
- **Audience:** AOE (Dr. Erin Davis's team), the SBE, and content specialists (math, science, social studies).
- **Proposals:**
  - AOE memo of 2026-10-20 (Erin Davis), the most important source document.
  - "Complete Recommendation" (Class of 2033+) and "Transitional Flexibility" (Classes of 2031–32).
  - Credit amounts: `data/requirements.csv`. Ignore the 2025 survey benchmark column.
- **Not in this report:** schools awarding multiple credits for one course (a possible weakening of rigor). That is a later project; at most mention it as one.

## 1. Data inventory (all committed on `main`)
| File | What it is |
|---|---|
| `data/schools.csv` | 57 schools (56 high schools; St. Johnsbury is PK-8). SU/SD, enrollment 2024-25, NCES ids |
| `data/requirements.csv` | Requirement IDs and credits for both proposals |
| `phase1/catalogs.csv` | Catalog link, year, format, issues and `retrieved_on` per school |
| `phase2/courses.csv` / `phase2/courses/<id>.json` | 6,061 course records from 54 schools (5,566 non-CTE): description, grades, credits, length, prerequisites, `fulfills_text`, `offering_note`, level (CTE etc.) |
| `phase2/graduation_requirements.csv` | Local graduation requirements by area (454 rows), with totals and other requirements |
| `phase3/profiles.csv` / `phase3/profiles/<id>.json` | 54 school profiles: grading system with evidence, schedule, credit definition, local totals, flexible pathways, CTE centers. `schedule_check` flags impossible capacity |
| `phase3/classified.csv` / `phase3/classified/<id>.json` | One row per course × mapping (6,470 rows). subject_area, bridges, other_type, credit mappings (strong/possible, with a rationale), science_domain, has_lab, finlit_type, catalog_claims, confidence. Rubric v0.3.2 |
| `phase4/gap_by_school.csv`, `phase4/gap_summary.csv` | Coverage status for each school × plan × requirement: covered / short / possible_only / gap / unknown |
| `phase3/gold/labels.csv`, `phase3/gold/montpelier_labels.csv` | The human's answer keys: 97 pilot courses + 30 held-out courses |
| `report/DATA_QUALITY.md`, `report/coverage_by_school.md` | Methods/limitations notes and the per-school coverage table |
| `sources/policy/` | AOE memo, SBE draft v8, AOE recommendations (Jan 2026) and standards documents (`standards/*.md`, `standards_mapping_all_content.xlsx`) |

**Scripts:**
- `scripts/merge_phase3.py`, `scripts/gap_analysis.py`, `scripts/coverage_table.py`
- `scripts/phase3_score.py`: model accuracy against the answer keys
- `scripts/phase3_gold_sample.py`: builds review sheets, with `--n`, `--out`, `--no-cte`

**Google Sheets** (the human prefers Sheets for review): pilot answer key `1Q-grm7L2jiT9P973gsT75nBqwqJHxzgJal_Uk-RROyc`; Montpelier spot-check `19nHEialU0fZyoBNCViYmuNIuLMH2IYurcAn7T4gCZcY`.
Create Sheets with Drive `create_file` from a CSV, using a file reference `sha256:<hex>:<abs path>`. Then format them with the Sheets connector: freeze the header, wrap text, widen the description column.

## 2. Headline numbers already computed (re-verify when writing)
- **Coverage:**
  - Complete plan: **6 of 54** schools already offer every requirement as `strong`; **30** have at least one gap or shortfall.
  - Transitional plan: 13 offer everything; 12 have at least one gap or shortfall.
- **HEALTH 1.0:** 22 schools offer only 0.5 credit (Craftsbury 0.25). This is the biggest shortfall in the Complete plan, and it mostly goes away under the Transitional combined PE/Health 1.5.
- **PE 1.5:** 9 schools are short.
- **SCI-EARTH:**
  - True gaps: Spaulding, Winooski and Cabot (Cabot's data is partial).
  - **13 schools reach it only through `possible` courses** (Environmental Science / APES, integrated science, ecology, forestry).
- **SS-CIVICS:** Montpelier has no civics course; 5 schools have only `possible` courses.
- **MATH-ALG1:** **15 schools reach it only through `possible` courses**, mostly Integrated Math 1 or Algebra I split into Part A/B.
  - Essex's "Algebra I 100/200" is a classifier error and should be strong; fix it before publishing. See §5.
- **FINLIT:** stand-alone courses are nearly universal. Embedded-only: Fair Haven, Mt. Mansfield and Randolph.
- **WL:** Canaan has no world language.
- **Grading:** 43 hybrid, 5 proficiency-only (Mt. Mansfield, U-32, Twinfield, BFA Fairfax, Harwood), 4 credit-only (Otter Valley, Oxbow, Peoples, Stowe) and 2 not stated. Stowe moved from a 4-point proficiency scale to a 100-point scale in 2025-26.
- **What catalogs disclose (non-CTE courses):** fulfills 23%, prerequisites 46%, credits 71%, grade levels 71%, length 69%, description 97%.
- **Catalog claims:** 904 courses carry them. For 77 (9%), the content-based mapping doesn't support the claim (e.g. Woodworking for English or Science credit; HTML/CSS for fine arts).
- **Labs:** 418 of 664 science courses (63%) mention labs or hands-on investigation; the rest don't say. No AOE document defines "lab".
- **Model accuracy:**
  - Pilot answer key: v0.3 85% exact, 96% strong-set.
  - Held-out Montpelier: 28/30 (93%). Both misses were flexible pathways, which led to the FLEX-ANY code.
  - The human's judgment: about as good as possible without precise AOE credit definitions.

## 3. Report structure — organized around the human's seven themes
Each theme section follows the same pattern:
- **What the catalogs show** (a statistic and a chart)
- **Why it matters**
- **The decision AOE/SBE faces**
- **Options and how many schools each would affect** (a sensitivity table)
- **Caveats** (sections unknown; Ed-Fi needed)

### Executive summary (1 page)
- The 3–5 issues that most need a decision.
- A Complete vs. Transitional comparison table.
- "What we can and can't know from catalogs."

### Theme 1 — Subjects completely missing from a school
- **Definition:** for each school × content area, the school has **no course at all** (any strength, excluding CTE-center listings and FLEX-ANY) mapped to that requirement, and **no course whose subject_area is that area**.
- **Areas:** WL, HEALTH, FINLIT, SS-CIVICS, SCI-EARTH, ARTS sub-areas, plus PE.
- **New script** `scripts/missing_subjects.py`: reads `phase3/classified.csv`, writes `phase4/missing_subjects.csv`, and also lists the "nearest substitute" course.
- **Reporting:**
  - Count of schools, by enrollment size band. Small schools are the expected hot spot: join `enrollment_2024` from `data/schools.csv`.
  - Exclude Oxbow (no course list) and treat Cabot, Mill River and Rivendell as low-confidence.
- **Already known:** Canaan has no WL; Montpelier has no civics; Spaulding, Winooski and Cabot have no Earth/Space.

### Theme 2 — Today's local graduation requirements vs. the proposals
- **Source:** `phase2/graduation_requirements.csv`, which covers 54 schools.
  - The human did this comparison before. Now add context from the course offerings and profiles.
- **New script** `scripts/compare_local_reqs.py`:
  - Normalize each area to the requirement IDs.
  - Map local area names: English/ELA/Literacy → ELA; Global Citizenship/Social Studies → SS; Wellness → PE/HEALTH; etc.
  - For each school and area, compute local credits minus proposed credits.
  - Totals compared with 22.5. Local totals run from 21.5 (Northfield) to 34 (Peoples); Brattleboro's 96 is BUHS units, about 24 standard; Danville counts semesters.
  - 12 schools state no total; proficiency-only schools have no credit counts.
- **Show:**
  - The distribution of local totals.
  - Per area, how many schools require more, the same or less than each proposal. Examples: Health 0.5 locally vs. 1.0 proposed; Social Studies 3–4 locally vs. 3 split into USHIST/CIVICS/WORLD.
  - Which local requirements disappear: community service, senior project, PLP, local tech/CS requirements (Milton's Technology 0.5; Richford's Computer Science 1 and Practical Arts 1).
- **Context from profiles:** hybrid vs. credit vs. proficiency (credit counts mean different things); and what one credit means (Brattleboro's semester course = 4 BUHS; Quarry Valley's credit = one semester course, so its 28 is about 14 standard).

### Theme 3 — The "possible" courses: where AOE sets the qualifying threshold
- **This is the core policy theme.** If thresholds are too loose, standards don't rise; if too tight, students who can't reach the more rigorous courses may not graduate.
- **New script** `scripts/possible_sensitivity.py`. For each requirement, recompute coverage under three thresholds:
  - **strict:** strong only (current "covered")
  - **moderate:** strong, plus `possible` courses in the named disputed categories (Environmental Science → EARTH; Integrated Math 1 → ALG1; Integrated Math 2 → GEOM; Anatomy/Ecology → LIFE)
  - **loose:** strong plus any `possible`
- **Output:** the number of schools covered under each threshold, per plan. This is the impact table the human wants.
- **Below-Algebra-I math:** list every school's courses that sit below Algebra I, using regex and classification on names and descriptions: Pre-Algebra, Essentials of Math, Foundations, Math in the Workplace, Consumer/Business/Applied Math, Math Lab.
  - Count per school. Lake Region has Pre-Algebra, Essentials of Mathematics II and Consumer Mathematics; Danville has Pre-Algebra and Math in the Workplace. The human remembers a school with **3–4 below-Algebra-I courses**: check Lake Region first, then Danville.
  - Note that the human ruled Pre-Algebra counts as a math elective (MATH-PATHWAY strong), and flagged Consumer/Essentials math as possibly below high-school level, for review by a math specialist.
  - **The number of sections is unknown:** Ed-Fi is needed to tell how many students take these courses.
- **Also:**
  - The catalog-claims-vs-content table (77 disputed equivalencies).
  - Labs (63% mention them; no AOE lab definition).

### Theme 4 — Electives: the proposals leave less room than many schools offer today
- **Elective room:** the proposals leave **3.0** (Complete) or **6.0** (Transitional) open elective credits.
- **Computation:**
  - Per school, count courses and offered credits with **no mapping, or only FLEX-ANY** (pure electives), plus courses in areas beyond the requirement (e.g. the 12th arts course).
  - Compare with local elective requirements (e.g. Leland & Gray 7.5, Northfield 5.5).
  - Report by subject_area / other_type: Business, FCS, Tech/Engineering, Computer Science, Psychology/Sociology/Economics, journalism, etc.
- **Message:** these courses are at risk of being cut, along with courses that "don't fit the neat square peg" of a requirement.
  - Show examples of distinctive electives (e.g. Montpelier's place-based courses, Lake Region's half-credit ELA electives).
- **Ed-Fi caveat:** catalogs list offerings, not sections run.
- **New script** `scripts/elective_landscape.py`.

### Theme 5 — Interdisciplinary courses and fractional (0.5 / 0.25) credit
- **What to count:**
  - Interdisciplinary courses (`subject_area = Interdisciplinary`, `bridges`): count and list the bridge pairs (ELA+SS humanities, STEM, FinLit+SS...).
  - Half-credit and quarter-credit courses by area.
  - Multi-area courses: e.g. Spaulding's "1 credit Math + 1 elective credit"; Lake Region's equivalency credits; CTE embedded credits stated in `fulfills_text` (e.g. Carpentry's math credit; Springfield RVTC and Twin Valley/Windham give full descriptions).
  - Integrated/mixed science counted as partial credit.
- **The policy gap:** AOE hasn't defined how a course counts as a fraction of several areas. Allowing it would enable creative and CTE courses.
- **Current state:** how many schools already do this, and how they describe it.
- **New script** `scripts/interdisciplinary_fractional.py`.

### Theme 6 — Integrated Math 1/2 as the equivalent of Algebra I and Geometry
- **Who:** the schools that use Integrated/Core/Math 1–2 sequences (Burlington, Harwood, Mt. Abraham, Richford, Rutland, Vergennes, South Burlington, Arlington's "Math A/1", BFA Fairfax, CVU Core Math, Randolph AGS).
- **The human's opinion:** each course might count as 0.5 Algebra I + 0.5 Geometry. Their note said "0.5 credit of Algebra II", probably meant Geometry; **confirm with the human**. This is still to be defined.
- **Show:**
  - How coverage of ALG1 and GEOM changes if Integrated Math 1/2 count in full, count 0.5 + 0.5, or don't count.
  - Algebra I split over two years (Part A/B: Hartford, Leland & Gray, South Burlington "Math 1 by 2 Years").
- **Recommendation:** AOE should publish an equivalency rule.

### Theme 7 — Content-specialist questions per subject
One subsection per area, with a list of the decisions that need a specialist.
- **Science (science specialist):**
  - Does Environmental Science cover Earth/Space? AOE's own model says "1 Credit of ??". The human thinks yes, but is unsure.
  - Lab definition.
  - Integrated science as partial credit.
  - Show the 13 schools that depend on the answer.
- **Social Studies (social studies specialist):**
  - Civics as its own course vs. embedded in US History or Government.
  - World Geography / Cultural Geography as World Studies (the human ruled Cultural Geography strong).
  - Show the schools that depend on the answer.
- **Math (math specialist):**
  - Algebra II always counts for STATS-ALG2 (the human's ruling).
  - Integrated math.
  - Below-level courses.
  - CS as a math elective, with and without CS standards.
- **ELA:** what counts as Intro vs. Mastery when grade levels aren't stated (29% of courses); half-credit electives; Speech/Journalism.
- **Health/PE:** Health 1.0 vs. today's typical 0.5; combined Wellness courses.
- **FINLIT:** stand-alone vs. embedded.
- **WL:** small schools; online (VTVLC) as the only access.
- **Arts:** design/CTE equivalency.

### Systems context (supporting section)
- **What catalogs disclose:** the change-management baseline (fulfills 23%, prerequisites 46%), plus the best and worst schools.
- **Grading systems:** the list of proficiency-only and hybrid schools, which the human called critical.
- **Schedules:** "courses per term" is stated in only 19 of 54 catalogs. The meaning of a credit varies.
  - **Don't publish the schedule-capacity numbers** without human verification (4 impossible values are flagged).
- **CTE and flexible pathways:**
  - How catalogs list CTE (full descriptions vs. names only vs. absent).
  - Count of FLEX-ANY pathways per school.

### Methods and limitations
Summarize `report/DATA_QUALITY.md`:
- Sources: catalogs and model classification, with the human-calibrated accuracy.
- Offerings, not sections (Ed-Fi).
- Older or district catalogs; thin schools.
- Content-based mapping vs. what catalogs claim.

### Appendix
- A one-row scorecard per school (both plans), as a Google Sheet.
- Links to every CSV.

## 4. Deliverable format
- **Main report:** a shareable document. Before creating one, check which document/page tools this session offers. Prefer a document the human can comment on (Claude Docs, or Google Docs if requested).
- **Charts:** follow the dataviz skill (load it first).
- **Data appendix:** Google Sheets. One tab each for the scorecard, gaps, missing subjects, sensitivity, below-Algebra-I courses, electives, interdisciplinary courses and profiles.
- **Workflow:** keep `report/` as the source of truth. Draft section by section, then share the outline with the human first.

## 5. Before writing: fix / verify list
1. **Essex "Algebra I 100/200":** classified ALG1 `possible`, but it should be strong. Re-check every ALG1/GEOM `possible` mapping with a quick rule-based pass:
   - names "Algebra I"/"Algebra 1" without Part/A/B/"by 2 years" → strong
   - Integrated Math 1 → keep possible, but tag as the `integrated` category
   - Then rerun `scripts/gap_analysis.py`.
2. **Winooski Environmental Science** shows a SCI-EARTH **gap**, not possible_only. Find out why (offering_note filter?) and fix.
3. **Cabot:** treat as "data incomplete" everywhere, not as gaps. Possibly add Cabot to TITLES_ONLY-style handling in `gap_analysis.py`.
4. **Spot-check sheet (offered to the human; awaiting their answer):** about 30 courses that drive the headline findings (Health, Earth, Civics, ALG1), in Google Sheets.
5. **Confirm with the human:**
   - Theme 6 wording: Algebra I + Geometry.
   - Whether to name schools in the report or anonymize them by size band.
6. **Respect `offering_note`:** gap_analysis already excludes "not offered 2026-27". Keep that, and state it.

## 6. Open questions to put to the human (and possibly to specialists)
- Name individual schools in the report, or aggregate?
- The threshold options in Theme 3: are strict/moderate/loose the right tiers?
- Does Integrated Math count as 0.5 + 0.5?
- Should Environmental Science count for Earth/Space? (Science specialist.)
- Civics embedded vs. stand-alone. (Social studies specialist.)
- Timing and process for the Ed-Fi section/enrollment join (out of scope now).
