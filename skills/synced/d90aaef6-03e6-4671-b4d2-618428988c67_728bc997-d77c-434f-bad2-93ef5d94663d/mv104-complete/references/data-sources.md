# Data sources and how each MV-104 field is sourced

Three multi-use sources live in the claude.ai Project **"MV104 - Autofill"** (docs tab) and are refreshed by the user when they change. One single-use source (the Origami incident export) is attached per incident.

| Source | Project doc / attachment | Refresh rule |
|---|---|---|
| MV-104 template (fillable) | `mv104-template.pdf` (also bundled at `assets/`) | Only when Rule #1 finds a new revision |
| UKG employee roster (slimmed, no SSN) | `roster-slim.csv` — header line 1 is `# UKG export date: …` | **If the Employee Id on the incident is not found, stop and ask the user for a fresh UKG "Employee Information: Full-EmployeeDetails" export**, run `scripts/slim-roster.py`, replace the Project doc |
| Truck Info workbook | `YYYY-M-D-Truckinfo.xlsx` (sheets: Current Units, Old units 2013-2018, Disposed Units 2019-now, Disabled Units) | If the Unit # is not found in any sheet, ask for a fresh export |
| Fleet insurance card + sample cab card | `sample-fleet-cards-unit-99916.pdf`; values transcribed in `fleet-insurance.json` and `lessor-registry.json` | New policy term (check crash date is inside effective window) or a lessor not in the registry |
| Origami RMIS incident export (PDF) | attached by the user each time | Single use |

## Matching rules

- **Employee: match on Employee Id only** (Origami "Employee Number" → UKG "Employee Id"). Baldor has drivers with identical names; a name match is never acceptable.
- **Vehicle: match on Unit #** (Origami unit/vehicle number → Truck Info "Unit"). The sheet searched is reported; a hit outside "Current Units" means the truck was disposed/disabled after the crash — still valid, but say so.
- **Registrant = the lessor in Truck Info "Vendor"**, transcribed exactly from that lessor's cab card (`lessor-registry.json`). Baldor insures leased units in the lessor's name. Only HUB is on file today (cab card seen 2026-10-09). PENSKE, MILEA, GABRIELLI, BENTLEY, MENDON, RYDER and the two BALDOR-owned units need a cab card before their registrant block can be written.

## UKG roster → MV-104 (Part A Driver)

| MV-104 field | UKG column | Notes |
|---|---|---|
| Driver Name (Last, First, M.I.) | `Last Name`, `First Name` | **No middle-name column in UKG** → M.I. cannot be written; name is written "Last, First" and the M.I. gap is noted. Also "exactly as printed on license" cannot be verified from UKG → note that. |
| Driver Address | `Address 1` + `Address 2` (apt) | |
| Driver City or Town / State / Zip | `City`, `State`, `Zip Code` | State must be a 2-letter option |
| Driver Date of Birth | `Date Birthday` (MM/DD/YYYY) | split into month/day/year fields |
| Driver Sex | **not in UKG** | required → flagged MISSING unless another source (license copy, Samsara driver profile, DQ file) is attached |
| Driver License ID Number / State of License | **not in UKG** | required → flagged MISSING unless a license copy / DQ-file page is attached |
| Persons Involved Row 1: Age | computed from DOB and crash date | arithmetic, not inference — write it, cite both inputs |

Columns kept in `roster-slim.csv` are listed in `scripts/lookup-employee.py` (`MV104_COLUMNS`). SSN and pay columns are never copied.

## Truck Info → MV-104 (Part A Registrant / Vehicle)

| MV-104 field | Truck Info column | Notes |
|---|---|---|
| Registrant Plate Number | `Plate #` | |
| Registrant State of Registration | `Reg State` | |
| Vehicle/Unit Year/Make/Model | `Year` + `Make` + `Model` | e.g. "2019 HINO 338" |
| Vehicle/Unit Type | `Type` | e.g. "CDL TRUCK", "VAN", "T/A TRACTOR" — written as the sheet states it |
| Vehicle Identification Number | `VIN #` | 17 chars; compare to cab card when available |
| Registrant Name / Address / City / State / Zip | `Vendor` → `lessor-registry.json` | exactly as on cab card |
| Registrant Date of Birth / Sex | n/a for a corporation | write dash (-) per form instructions |
| Insurance Code / Company / Policy | `fleet-insurance.json` | verify crash date within policy term |

## Origami incident export → MV-104

See `origami-mapping.md`.
