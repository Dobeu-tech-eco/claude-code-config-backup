# Origami RMIS incident export → MV-104

The Origami export is a multi-page PDF, "<Last><First><IncidentNumber>.pdf". Text extracts cleanly with `pypdf`; labels and values are on separate lines in roughly the same order, so read the whole page text, not a regex. Expect these blocks:

| Origami label | Typical value | Feeds MV-104 |
|---|---|---|
| Incident Number / Occurrence Number | 2026001358 | file naming; not on form |
| Injured Employee / Claimant | "Uceta Ortega, Jeuris" | cross-check only — the roster, matched by ID, supplies the name |
| **Employee Number** | 110828 | **the key for `lookup-employee.py`** |
| Incident Date / Incident Time | 2026/10/01, 8:15 AM | Crash Date M/D/Y, Day of Week (computed), Crash Time, AM/PM |
| Location | BNYBXT - BNY TRANSPORTATION | department context only |
| Accident Street1 / City / State / Postal | 155 FOOD CENTER DR / BRONX / New York / 10474 | Road Where Crash Occurred, Name of City/Town/Village, (County only if stated) |
| Event Description | narrative | "Briefly describe how the crash happened" — copy verbatim (truncate at field width; keep the original wording) |
| Incident Type | Damaged company vehicle / Damaged Non-Company Vehicle/Property (Auto) / Injured employee | reportability check |
| Unit / Vehicle / Truck # | e.g. 99916 | **the key for `lookup-truck.py`** — the field name varies by Origami form; if absent, ask the user |
| Was an ambulance called? / Nature / Body Part | | Number of Injured, Injury class, Describe Most Serious Injuries — only when the export states an injury |
| Police report #, precinct, other driver, other vehicle plate/insurance | often absent | Police Agency/Precinct/Crash Number, Part B — when absent they are MISSING, not "No" |
| Additional Incidents Involving this Employee | table at the end | ignore for the form; useful to confirm you have the right incident |
| Emails / Notes / Tasks | | may contain the driver statement, police report number, other party's info — read them; a value stated there is verbatim and must cite the note date/author |

## Reportability gate (run before anything else)

An incident is MV-104 material only if **all** are true: it is a motor-vehicle crash (not a slip/fall, strain, forklift-only event, or vandalism), it happened in New York State, and it caused injury, death, or >$1,000 damage to any one person's property. Example: incident 2026001004 (slip and fall pulling a pallet inside a truck at the depot) is **not** reportable even though a truck is involved; 2026001358 (sideswiped by a sanitation truck while double-parked, mirror damage) **is** — subject to the $1,000 damage question, which the export may not answer.

## What Origami never contains

Driver license number, license state, driver sex, middle initial, Part B driver license/DOB/sex, insurance of the other vehicle, crash-diagram code, roadway/traffic-control codes, number of people in the vehicle. Those come from a police report, the other party's exchange of information, the driver's statement, or the user — and are flagged MISSING otherwise.
