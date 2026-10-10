---
name: mv104-complete
description: Complete the New York State MV-104 "Report of Motor Vehicle Crash" for a Baldor Specialty Foods fleet incident from an Origami RMIS incident export, matching the driver by Employee Id in the UKG roster and the truck by Unit
---

# mv104-complete

Fill the NYS MV-104 (Report of Motor Vehicle Crash) for a Baldor fleet incident so the driver can sign and mail it inside the 10-day window. The form is a legal filing: every value written must be traceable to a document, and anything that is not goes to the user as a flagged gap or a clearly separated inference.

## The five standing rules (from Jeremy — do not relax them)

1. **Check NY DMV first, every run.** Before touching the incident, verify the official form and rules (`references/official-rules.md`, "How to re-verify"). If the revision or rules changed, update the skill's references/template, then tell the user what changed **before** filling.
2. **Never guess a field.** The PDF receives only values a source states verbatim. Anything you believe but cannot cite goes in the *Inferred-Fields* report (form order, legal field label, value) with the WHY in its appendix — never on the PDF.
3. **A missing REQUIRED field is called out in the chat reply and bold + highlighted in both reports.** The required list is `references/required-fields.json`; `fill-mv104.py` computes the gaps.
4. **Match employees by Employee Id only.** Baldor has drivers with identical names. The Origami "Employee Number" is the key into the UKG roster.
5. **The insurance card is a fleet card; registration mirrors the Truck Info sheet.** Company, NY code and policy number apply to every unit (`references/fleet-insurance.json`); plate/VIN/year/make/type come from Truck Info by Unit #; the registrant block comes from the lessor's cab card (`references/lessor-registry.json`).

## Inputs

| Input | Where | Multi/single use |
|---|---|---|
| Origami incident export (PDF) | attached by the user | single use |
| `mv104-template.pdf` (fillable, MV-104 5/25) | `assets/` in this skill bundle. Project docs cannot hold binaries; if the bundle is missing it, ask the user to attach the template or download https://dmv.ny.gov/forms/mv104.pdf in the browser | multi |
| `roster-slim.csv` (UKG, deduplicated, no SSN) | Project "MV104 - Autofill" doc `mv104/roster-slim.csv` → `project_read`, save locally. Line 1 carries the UKG export date | multi; refresh when an ID is missing |
| `truckinfo.csv` (all 4 sheets flattened) | Project doc `mv104/truckinfo.csv` (made by `scripts/truck-to-csv.py` from the `*-Truckinfo.xlsx` export; the lookup accepts either) | multi; refresh when a unit is missing |
| Fleet cards | `assets/sample-fleet-cards-unit-99916.pdf` + `references/fleet-insurance.json` + `references/lessor-registry.json` | multi; refresh on new policy term / new lessor |

If any multi-use file is absent or stale (ID or unit not found, crash date outside the policy term, lessor not in the registry), stop and ask the user for the refreshed export or card. Do not substitute a name match, an older unit, or a guessed registrant.

**Bootstrap when only SKILL.md is installed:** every script and reference file is mirrored as text in the Project docs under `mv104/skill/scripts/` and `mv104/skill/references/`. `project_read` each one into a local `mv104-complete/{scripts,references}/` folder (same file names) before running the workflow. Python needs `pypdf`, `openpyxl`, `python-docx`.

## Workflow

Create a task list for the run (steps below) so the user can follow progress.

### 1. Rule #1 — verify the official form
Follow `references/official-rules.md` → "How to re-verify". Record the outcome in one line of the final reply ("DMV check: MV-104 (5/25) unchanged as of <date>").

### 2. Read the incident and gate reportability
Extract the full text of the Origami PDF (`pypdf`, all pages, including Notes/Emails — statements and police numbers hide there). Apply the reportability gate in `references/origami-mapping.md`. If the incident is not a NYS motor-vehicle crash with injury/death/>$1,000 damage, say so and stop; offer to proceed as a dry run only if the user insists.

### 3. Look up the driver and the truck
```
python3 scripts/lookup-employee.py --roster roster-slim.csv --id <Employee Number> --out employee.json
python3 scripts/lookup-truck.py   --workbook truckinfo.csv  --unit <Unit #>          --out truck.json   # or the .xlsx
```
Exit code 2 = not found → ask for a fresh export (Rule 4 / data-sources.md). Read `truck.json["registrant"]["registrant_known"]`; `false` means the lessor's cab card is needed.

### 4. Build the worksheet
Write `worksheet.json` with two sections. The exact field names are in `references/mv104-field-map.md`; choice fields take only the listed options (codes keep the trailing period, e.g. `"1."`), checkboxes take the listed state name.

```json
{
  "incident_id": "2026001358",
  "verbatim": {
    "Crash Date Month": {"value": "10", "source": "Origami p.1 Incident Date 2026/10/01"},
    "(PART A: Your Vehicle/Unit) Registrant Plate Number": {"value": "75436PC", "source": "Truck Info Current Units, Unit 99916, 'Plate #'"}
  },
  "inferred": {
    "25. PRE-CRASH VEHICLE/UNIT ACTION (Unit 1)": {"value": "10.", "why": "Event Description says the truck was double parked; code 10 = Parked. The export does not state a code."}
  }
}
```

What counts as **verbatim** (goes on the PDF): a value printed in a source (Origami field, UKG column, Truck Info cell, cab card, insurance card, police report, driver statement) copied as-is; a pure transformation of such a value (splitting a date into month/day/year, Day of Week from the date, age from DOB and crash date, "Last, First" from two name columns, "2019 HINO 338" from three cells) — cite every input in `source`; the form's own conventions (dash for a registrant DOB/Sex when the registrant is a corporation; page-2 Yes/No answers that restate facts the export gives, such as "in New York State" when the address is a NY address).

What counts as **inferred** (report only): any code chosen from a narrative (traffic control, roadway surface, pre-crash action, type of crash, direction, position, safety equipment, injury class); counts not stated (Number of People in Vehicle, Number of Vehicles when the other vehicle is only implied); "Police Responded" when the export is silent; a Part B value taken from an unstructured note that does not clearly identify the other vehicle. When in doubt, it is inferred.

What is **missing**: a required field with no verbatim source. Do not fill it with "-" or "X" on the user's behalf; leave it empty so the gap is visible. The user may later instruct you to write "X" (unknown) or "-" (n/a) — then it becomes verbatim with the user as source.

Known structural gaps you will hit every time until another source is supplied: driver license number and state, driver sex, middle initial (UKG has none of these — see `references/data-sources.md`).

### 5. Fill the PDF
```
python3 scripts/fill-mv104.py --values worksheet.json --out out/MV104_<incident>_<Last>_<First>.pdf [--other-vehicle] [--injury]
```
Pass `--other-vehicle` when another driver/vehicle is involved (makes Part B required) and `--injury` when anyone was hurt. The script rejects unknown fields and illegal option values and writes `*.fill-report.json` with `written`, `rejected`, `missing_required`. Fix every `rejected` entry (usually a code written without its period or a state written in full) and re-run.

### 6. Produce the two Word reports
```
python3 scripts/make-field-report.py --worksheet worksheet.json --fill-report out/<pdf>.fill-report.json --incident <incident> --out-dir out
```
→ `MV104_<incident>_Verbatim-Fields.docx` (Section 1 verbatim values in form order; Section 2 missing REQUIRED, bold + yellow) and `MV104_<incident>_Inferred-Fields.docx` (Section 1 inferred values in form order; Section 2 missing REQUIRED; Appendix A the WHY per field).

### 7. Verify before delivering
Rasterize page 1 of the filled PDF (`pdftoppm -r 80 -png -f 1 -l 1`) and look at it: values in the right boxes, nothing truncated badly, checkboxes rendered. Open the fill report and confirm `rejected` is empty. Spot-check three values against their sources.

### 8. Deliver
Send the PDF and both .docx files. The reply contains, in this order:
1. DMV check result (one line).
2. **MISSING REQUIRED fields** — a bold list, each by its MV-104 label (Rule 3), with what source would close it (e.g. "driver license copy or DQ file", "police report number from the driver").
3. Filing facts: crash date, **10-day deadline date** (crash date + 10 days), mailing address, who must sign (driver; representative only for injury/death).
4. One line on what was inferred and that none of it is on the PDF.
5. Any staleness notice (roster export date, truck export date, policy term).

Do not claim the form is complete if `missing_required` is non-empty; call it "filled with all verifiable fields; N required fields outstanding".

## Maintenance

- New DMV revision → replace `assets/mv104-template.pdf`, regenerate the field map (see `references/official-rules.md`), update `required-fields.json` if fields were renamed, update both official-rules files.
- New lessor cab card seen → add the registrant block to `references/lessor-registry.json` exactly as printed, with the source and date.
- New policy term → update `references/fleet-insurance.json`.
- New UKG export → `scripts/slim-roster.py --source <export.csv> --out roster-slim.csv`, then `project_write` it to `mv104/roster-slim.csv`. New Truck Info → `scripts/truck-to-csv.py`, then `project_write` to `mv104/truckinfo.csv`.
- Any change to a script or reference → also `project_write` the mirror under `mv104/skill/…`.
- Record each refresh (export dates, policy term, lessors on file) in the Project memory so the next run knows what is current.

## Files

- `scripts/check-dmv-revision.py` — compares a downloaded live MV-104 with the template (revision string + field set)
- `scripts/lookup-employee.py` — UKG roster lookup by Employee Id (full export or slim)
- `scripts/slim-roster.py` — full UKG export → `roster-slim.csv` (MV-104 columns only, no SSN)
- `scripts/lookup-truck.py` — Truck Info lookup by Unit # across all sheets (xlsx or csv) + lessor registrant resolution
- `scripts/truck-to-csv.py` — Truck Info workbook → `truckinfo.csv` text twin for the Project docs
- `scripts/fill-mv104.py` — validated PDF fill + fill report with missing-required list
- `scripts/make-field-report.py` — the two .docx reports
- `references/official-rules.{md,json}` — Rule #1 record and re-verification steps
- `references/mv104-field-map.{md,json}` — all 158 fields in form order with allowed values
- `references/required-fields.json` — what counts as required, and when
- `references/data-sources.md`, `references/origami-mapping.md` — column maps and extraction notes
- `references/lessor-registry.json`, `references/fleet-insurance.json` — registrant and insurance blocks as printed
- `references/mv104-page1-text.txt`, `references/mv104-page2-instructions.txt` — code tables and instructions verbatim from the form
- `assets/mv104-template.pdf`, `assets/sample-fleet-cards-unit-99916.pdf`
