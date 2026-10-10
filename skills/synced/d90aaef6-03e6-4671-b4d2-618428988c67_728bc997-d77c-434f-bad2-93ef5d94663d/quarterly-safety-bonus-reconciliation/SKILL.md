---
name: "quarterly-safety-bonus-reconciliation"
description: Run Jeremy's end-of-quarter Baldor driver Safety Bonus reconciliation across the branch workbooks (BB/Boston, BNY, BPA/Philly, BDC, Baldor Fish). Use this whenever he uploads the *_Q#_YYYY_Safety_Bonus.xlsx branch files with an HR "EmployeeInformation-TerminatedDrivers" export and/or an Origami "Incidents" export, or says anything like "safety bonus", "quarterly bonus", "bonus reconciliation", "terminated drivers off the bonus sheet", "preventable incidents vs bonus sheet", "eligible / ineligible tabs", or "ACTION ITEMS tab / v1 v2". Three bundled scripts do the work deterministically; the skill explains the rules, the order, and what to hand back.
---

# Quarterly Safety Bonus Reconciliation

Every quarter Baldor pays a **$150 safety bonus** to drivers who are past their 90-day
probation and went the full calendar quarter with no accident, moving violation, or
other disqualifier. Each branch keeps one workbook with tabs **Eligible / Ineligible /
Terminated** (+ a `Reference` tab of formulas). The reconciliation used to be manual;
this skill makes it a three-step scripted pass with every judgment call left to Jeremy.

Scripts live in `scripts/` and need only `openpyxl` (`pip install openpyxl`). Order:
`validate_inputs.py` → `reconcile_safety_bonus.py` → `check_incidents_vs_bonus.py` →
`build_action_items.py` → `check_incidents_vs_bonus.py` again on the `_v2` files.
Read `references/sheet-conventions.md` if a column, tab, or rule looks unfamiliar.

## Inputs Jeremy supplies

| File | What it is |
|---|---|
| `BB_Q3_2026_Safety_Bonus.xlsx`, `BNY_…`, `BPA_…`, `BDC_…`, `BALDOR_FISH_…` | One workbook per branch. Branch is read from the filename prefix. |
| `EmployeeInformation-TerminatedDrivers_*.xlsx` | HR export of drivers termed in the quarter (sheet `report`, header on row 7). |
| `YYYY-MM-DD-Incidents-Q#.xlsx` | Origami export of preventable incidents, transportation only. Needs the `Preventable?` **and** `Disciplinary action?` columns. |
| Latest **active-driver roster** (HR export, full roster with **Job Title**) | **Ask Jeremy for this before running** if he did not upload it - he did not have it on hand in Q3 2026, and he wants to be prompted every time. It is the check that every active driver is on exactly one sheet and that no sheet row belongs to someone no longer active, and it carries the **job title** used to keep **Yard Jockeys** (never eligible) off the sheets. The loader (`load_active_roster`) finds the header row by its Employee ID column and reads an optional Name and Job Title / Position column; the preflight warns if the title column is missing. When a real export arrives, confirm the column names and document them in `references/sheet-conventions.md`. |

Copy uploads into a clean working folder first (uploads are read-only and carry a hash
prefix in the filename; the scripts strip it on output).

## Step 0 – preflight (mandatory, never skip)

```bash
S=<skill>/scripts
python3 $S/validate_inputs.py --input-dir <branch files> --term-report <HR export> \
    --incidents <Origami export> --active-drivers <HR active list> \
    --start 2026-07-01 --end 2026-09-30
```

Before the preflight, check what Jeremy uploaded against the input table above and
**ask for anything missing in one message** - in particular the active-driver list and
the Origami export - rather than running on partial inputs.

Run this before anything else and **relay its BLOCKERS and WARNINGS to Jeremy verbatim
before running any other script**. It exits non-zero on a blocker, and the pipeline
must not proceed until the input is re-pulled or Jeremy explicitly says to go ahead
anyway. Things it catches, all of which happened in Q3 2026: Origami export without the
`Preventable?` column; a branch location missing from the Origami filter (Philly =
`BPABXT`); an export not date-filtered to the quarter; a missing tab or header in a
branch workbook; blank employee numbers (warning). If he uploads a new export, run the
preflight again on the new file — do not assume it is fixed.

## The three steps, in order

```bash
# 1. terminations, duplicates, blank-row cleanup, bonus dates
python3 $S/reconcile_safety_bonus.py --input-dir <branch files> \
    --term-report <HR export> --active-drivers <HR roster> \
    --output-dir out/reconciled --quarter-label Q3_2026

# 2. Origami incidents vs the reconciled sheets (read-only, produces a review workbook)
python3 $S/check_incidents_vs_bonus.py --incidents <Origami export> \
    --workbook-dir out/reconciled --output out/reconciled/Q3_2026_Incidents_vs_Bonus_Review.xlsx \
    --start 2026-07-01 --end 2026-09-30     # always pass the quarter; exports often come unfiltered

# 3 + 4. _v1 (ACTION ITEMS tab only) and _v2 (incident edits + promotions applied) per branch
python3 $S/build_action_items.py --reconciled-dir out/reconciled \
    --reconciliation-report out/reconciled/Q3_2026_Safety_Bonus_Reconciliation_Report.xlsx \
    --incident-review out/reconciled/Q3_2026_Incidents_vs_Bonus_Review.xlsx \
    --output-dir out/v1_v2 --start 2026-07-01 --end 2026-09-30 --payout-date 2026-10-01
```

Step 1 takes ~45 s (the BNY Terminated tab has ~2,000 rows). Run step 2 a second time
against the `_v2` files afterwards — it should come back with **zero** CRITICAL /
MISSING / DATE MISMATCH findings; if not, something in step 3 did not apply.

Before step 1, do a quick structural read of the workbooks (sheet names, header row,
row counts) so you can tell Jeremy up front about anything odd, e.g. a tab with a
different header layout. BNY is known to differ (extra `COST CENTER` column, blank
column on Terminated, legacy rows with dates in the ID column, unlabeled columns
inside the DRIVER RECORD span) and the scripts handle it; anything new deserves a
question before running.

## What each step does and why

### Step 1 – `reconcile_safety_bonus.py`
* **Excluded cost centers run first.** Any row whose **column C** (literally column C —
  the `COST CENTER` column on BNY, where this applies; the other branches have a text
  `LOCATION` in C that never matches a number) holds one of the excluded cost-center
  numbers is **not an eligible employee and its row is deleted from every tab**
  (Eligible, Ineligible, Terminated). The list is `EXCLUDED_COST_CENTERS` =
  **850, 250, 745, 011, 512, 499** (stored normalised, so `011`/`11`/`11.0` all match).
  Each removed row is logged on the report's `Excluded_Cost_Centers` sheet and shown as a
  4-VERIFY action item on its branch. A removed row that is *also* a termed driver is
  **not re-added** to Terminated (its ID is remembered; `Terminated_Report` marks it
  `EXCLUDED`). Add new cost centers to `EXCLUDED_COST_CENTERS` as Jeremy identifies them.
* Every driver on the HR term report whose ID **and** name agree with a sheet row is
  removed from Eligible/Ineligible and appended to that branch's Terminated tab (yellow), `STATUS = TERM mm/dd/yy`, `ELIG = N`. Rows are
  copied **by header name**, not column position, because BNY's layout differs. If the
  driver had several rows, the one with the most data is kept and the others listed.
* Termed drivers that exist in no workbook are added to the Terminated tab of the branch
  implied by the HR sub-department (BB Drivers / Portland / BB Transportation → BB;
  Philly → BPA; BDC → BDC; Baldor Fish → FISH; Hourly / Drivers In Training / LI /
  Jockeys / Wappingers → BNY). "OS Staffing Trans" and "Transportation Office" can be
  any branch, so those are **red on the report's Terminated_Report sheet (and listed on
  `Unknown_Branch`), not added** — and they are **never action items on any branch
  workbook**. The reconciliation report is their only home; Jeremy resolves them there.
* **Yard Jockeys are never eligible and never added.** Anyone whose HR job title
  contains "Jockey" (roster) or whose HR sub-department is "Jockeys" (term report) is
  excluded: a termed jockey missing from every workbook is **not** added to Terminated
  (grey on `Terminated_Report`, listed on `Yard_Jockeys` - report only); a jockey found
  on an Eligible/Ineligible tab is highlighted grey and becomes a branch ACTION ITEM to
  remove the row; one already on a Terminated tab needs no action. This is almost
  entirely a BNY matter (the yard is at the Bronx HQ).
* Duplicates are **flagged only** (orange): same ID (+ agreeing name) on both active
  tabs, twice on one tab, on an active tab *and* Terminated (rehire or stale), or in
  two branches; same ID with a *different* name is an ID collision; near-identical
  names where one row lacks a numeric ID (OWUSU/OWUSO with "Vertex") are flagged as a
  possible same driver; identical names with two numeric IDs are namesakes (info).
* Blank `ELIGIBLE FOR BONUS` on Ineligible rows is computed (green) from the latest
  DRIVER RECORD incident with a bonus count — **except** Workers Comp / LOA / PFL /
  light-duty rows and **temp / staffing-agency drivers (Temp Driver, Vertex)**, who are
  never eligible and never get a date. Dates already on the sheet are never changed;
  disagreements with the rule go to `Date_Check_Info` as information.
* Empty gap rows between drivers are deleted.
* **ELIG column** (header `ELIG`, column G on most tabs, H on BNY) is normalised on every
  row: **Y on Eligible, N on Ineligible and Terminated**. Old NH/WC codes are replaced;
  REASON keeps that detail. Counts go to `ELIG_Normalized` in the report. Steps 3-4
  keep the rule when they move rows (Y when promoted, N when moved to Ineligible).

### Step 2 – `check_incidents_vs_bonus.py`
Read-only. For each Origami incident: `Preventable? = Pending/blank` → REVIEW (yellow);
`Preventable = Yes` + `Disciplinary action? = Pending/blank` → REVIEW; `Discipline = Yes`
→ the driver must be on Ineligible with a DRIVER RECORD entry dated the loss date.
Driver still on Eligible = **CRITICAL** (would be paid). Entry missing = MISSING ENTRY.
Entry within 10 days = DATE MISMATCH — unless Origami also has a separate incident on
that nearby date, in which case it's a MISSING ENTRY for a second accident (Largacha
9/4 + 9/7 taught us this). Drivers are matched by Employee Number, falling back to fuzzy
name matching when the number is blank (common in Origami) — flagged `[matched by NAME]`.
`Sheet_Entries_Not_In_Origami` is the reverse check: quarter-dated accident entries on
the sheets with no Origami incident.
An incident with **no employee name and no employee number** is `NO DRIVER` — it stays
in the `Anomalies` sheet of the incident review report and is **never a branch action
item**; the same goes for any incident that could not be matched to a driver row on a
branch sheet (NOT FOUND, unmatched REVIEW, AMBIGUOUS with no sheet rows). Jeremy fixes
those in Origami; branch managers never see them.

### Step 3 – `build_action_items.py`
`_v1` = step-1 workbook + an **ACTION ITEMS** tab (first tab) listing every highlighted or
deliberation item for that branch with Priority, Detail, Suggested Action, Status and a
blank "Your Decision" column. `_v2` = the same plus the step-2 edits applied in blue:
critical drivers moved to Ineligible with the accident entry, missing entries added,
mismatched dates aligned to the Origami loss date. New entries use **(x2)** — the
standard on every branch sheet regardless of tier; (x1) is a rare manual exception —
and are marked "Applied in v2 - verify".

### Step 4 – promotion (inside `build_action_items.py`, applied in `_v2`)
Any Ineligible row whose `ELIGIBLE FOR BONUS` equals the **payout date** (first day of
the quarter after the one being closed, e.g. 10/1/2026 for Q3 2026) has served its
ineligible quarters and moves to Eligible: row copied by header name, `ELIG = Y`,
purple highlight, Ineligible row deleted. Three holds stay on Ineligible and go to
ACTION ITEMS instead, because the date alone does not prove eligibility:
* REASON (or ID cell) is Workers Comp / LOA / PFL / STDB / temp → "confirm returned";
  temps are never eligible regardless of date.
* A DRIVER RECORD entry is dated inside the quarter → the 10/1 date is stale (the driver
  had a new incident); recompute, do not promote. This caught FALANO, BASIT in Q3 2026.
* The ID appears on more than one active row → resolve the duplicate first.
Run step 2 again on the `_v2` files afterwards; a promoted driver showing as CRITICAL
means a hold is missing.

## Identity rule: employee ID + name, always both
Baldor has drivers who share a name, and sheets that re-use or mis-key IDs, so neither
field alone identifies a person. Every script applies this:
* **ID matches but the name does not** (typo-tolerant: ARIA/ARIAS, WHTE/WHITE agree;
  GARCIA QUENNEDYS vs GUZMAN RICHARD does not) → **ID COLLISION**. Never moved, never
  edited; it goes to `ID_Name_Mismatch` (HR terms) or `Duplicates` (sheets) or the
  incident `Anomalies` sheet, highlighted red/orange for Jeremy.
* **Same name, two different numeric IDs** → two people (`Namesakes`, info only).
  Never treated as a duplicate.
* **Multi-page duplicate** = same ID *and* agreeing name on more than one row/tab/branch.
* **Origami matching**: employee number first, confirmed by name. If the number is
  blank or not on the sheets, name-only matching requires the *full* name (both tokens
  or a near-identical spelling - OWUSU/OWUSO); a shared first name is not a match. If
  the full name still fits more than one ID → **AMBIGUOUS NAME**, no edit, Jeremy
  supplies the employee number.
* Blank names on a sheet row never identify anyone; a blank name next to a matching ID
  is accepted as that ID.

## Standing rules Jeremy has set (do not re-ask)
* Highlight a flagged driver row in **columns A-E only** (NAME through DOH), never the
  whole row. `Tab.highlight()` enforces this; the ACTION ITEMS tab says which column
  changed.
* Always prompt for the latest active-driver list before running.
* ELIG = Y on the Eligible tab, N on every other tab, every row.
* Bonus date rule: incident quarter counts as removed quarter #1; (x1) on 3/6/26 → 7/1/26,
  (x2) → 10/1/26. The sheet date is the payout date (first day after one clean quarter).
* Temps are never eligible, get no date, but their accidents still go on Ineligible.
* **Yard Jockeys are not eligible, do not appear on any bonus sheet, and are never
  added** - not to Eligible, Ineligible, or Terminated. Identify them by the Job Title
  on the full roster Jeremy will supply (or the "Jockeys" sub-department on the term
  report). Applies mostly to BNY. If one is found on an active tab, flag it for removal.
* **Excluded cost centers are never eligible and are removed from every tab.** Column C
  values 850, 250, 745, 011, 512, 499 are not employees; delete their rows outright and
  log them (`EXCLUDED_COST_CENTERS` in `reconcile_safety_bonus.py`). Mostly BNY (its
  column C is the COST CENTER column). Never re-add an excluded row via the termination
  step. Extend the list when Jeremy names more cost centers.
* Term date goes in the STATUS column as `TERM mm/dd/yy`.
* Duplicates and cross-branch conflicts are flagged, never auto-resolved.
* A termed driver whose branch cannot be reconciled is **not** an action item on any
  branch sheet; it appears only in the final reconciliation report (`Unknown_Branch`
  sheet, red rows on `Terminated_Report`).
* Likewise an Origami incident with no driver attached (blank name and number), or one
  that matches no driver row on a branch sheet, is **not** an action item on any branch
  workbook; it appears only in the incident review report's `Anomalies` sheet. Branch
  ACTION ITEMS tabs list only incidents tied to a driver row on that branch.
* Origami loss date is the system of record for incident dates.
* Deliverables keep the original filenames with `_v1` / `_v2` suffixes; the final zip
  Jeremy wants holds only the `_v2` workbooks plus the two report workbooks.

## What to tell Jeremy at the end
Lead with counts (moved, added, unknown-branch, excluded cost centers, Yard Jockeys,
duplicates, dates filled/left blank;
critical / missing / mismatch / review incidents), then the items that need *his*
decision, then source-data fixes worth making upstream (blank employee numbers in
Origami, missing Preventable column, a branch location missing from the Origami
filter — the first Q3 2026 pull was missing BPABXT/Philly). Do not recap the steps.

## Known limits
* openpyxl drops Excel "extension" conditional formatting (icon sets / data bars);
  fills, data-validation dropdowns and freeze panes survive. Say so once.
* Deleting rows does not re-point conditional-formatting ranges; cosmetic only.
* Name matching cannot resolve two different spellings when the Employee Number is
  blank *and* the names differ by more than a couple of letters — those show as NOT FOUND.
