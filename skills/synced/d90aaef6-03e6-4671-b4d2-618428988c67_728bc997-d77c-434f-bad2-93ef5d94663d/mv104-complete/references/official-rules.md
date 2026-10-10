# NY MV-104 — official rules on file (Rule #1 record)

Machine-readable twin: `official-rules.json` (the scripts read that one; keep both in sync).

| Item | Value on file | Verified |
|---|---|---|
| Form | REPORT OF MOTOR VEHICLE CRASH, **MV-104 (5/25)**, 2 pages | 2026-10-09 |
| Official URL | https://dmv.ny.gov/forms/mv104.pdf | 2026-10-09 |
| Who files | Each driver involved in a crash in NYS (Part A = your vehicle; Part B = other vehicle / pedestrian / bicyclist / unoccupied vehicle) | |
| Threshold | Fatality, personal injury, **or** damage over **$1,000** to the property of any one person | |
| Deadline | **10 days** from the crash. Failure = misdemeanor; license/registration may be suspended | |
| Submit | Mail original to **Crash Records Center, 6 Empire State Plaza, PO Box 2925, Albany, NY 12220-0925** | |
| Signature | Driver signs. Representative may sign only for injury/death (check the box, give unit #, give reason). Unsigned = not filed | |
| Do NOT file | Vehicle was vandalized (call local police) · Crash was not in New York State | |
| Conventions | Dash (-) = not applicable · X = unknown · black ink · driver info EXACTLY as on license · registrant info EXACTLY as on registration · >2 vehicles or >5 people → extra forms marked #2, #3… | |

## How to re-verify (every run)

1. `WebFetch https://dmv.ny.gov/forms/mv104.pdf` and ask for: form title, revision code "MV-104 (m/yy)", threshold, deadline, mailing address.
2. Compare with the table above. Also skim https://dmv.ny.gov/ for any notice about the crash report form (search "MV-104").
3. Same revision and same rules → proceed. Different → download the new PDF, run `scripts/check-dmv-revision.py --live <new.pdf>`, regenerate `references/mv104-field-map.*` from the new template, replace `assets/mv104-template.pdf`, update this file and the JSON twin, bump `last_verified`, and **tell the user what changed before filling anything**.
4. If the site cannot be reached at all, say so and ask the user whether to proceed on the 5/25 revision on file; do not silently continue.

## Code tables printed on the form

The numeric codes for Traffic Control (3), Roadway Surface (6), Direction of Travel (23–24), Pre-Crash Action (25–26), Type of Crash (28–30), Position in/on Unit (9), Safety Equipment (10), Injury (15) and the crash-diagram codes are in `mv104-page1-text.txt` and `mv104-page2-instructions.txt` (verbatim text extracted from the official form). Read the relevant table before choosing a code; a code chosen from the narrative is an **inference** and belongs in the inferred list, not on the PDF, unless the source states it.
