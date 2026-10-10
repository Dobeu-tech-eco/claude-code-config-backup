# Branch workbook conventions (as of Q3 2026)

## Tabs
| Tab | Meaning |
|---|---|
| Eligible | Drivers who get the $150 this quarter. `ELIG = Y`. |
| Ineligible | Active drivers who do not: accident / violation in the look-back, new hire inside 90 days or without a clean quarter yet, Workers Comp / LOA / PFL / STDB > 30 days in the quarter, part-time, temp. |
| Terminated | Anyone no longer employed (fired or quit). Rows are never deleted, only appended. |
| Reference / Copy of Reference | Dropdown lists for ELIG and REASON. Leave alone. |
| All Drivers (BNY only) | Legacy master list that even contains Boston drivers. Ignore for duplicate checks. |

## Columns (header row 1)
`NAME` (LAST, FIRST, upper case) · `ID` (employee number, the join key) · `LOCATION`
(BOS / NY / PHILLY / DC / FISH / PIERLESS) · `STATUS` (free text; we write `TERM mm/dd/yy`)
· `DOH` (date of hire) · `$$` (150) · `ELIG` (**Y on Eligible, N on all other tabs** - the scripts normalise this; older NH / WC codes are replaced) · `REASON` (Accident,
New Hire, Workers Comp, PFL, STDB, LOA, Temp Driver, VERTEX, Other …) · `ELIGIBLE FOR
BONUS` (date, or WC / PFL text on BNY) · `DRIVER RECORD` × many (one incident or note per
cell, chronological left → right).

BNY Eligible/Ineligible add `COST CENTER` after `ID` — so on BNY, **column C is the
COST CENTER number** (the other branches have `LOCATION` text in column C). Cost centers
850, 250, 745, 011, 512, 499 are **not bonus-eligible employees** (`EXCLUDED_COST_CENTERS`);
their rows are deleted from every tab in step 1 and logged on `Excluded_Cost_Centers`.
BNY Terminated has a blank column
between `REASON` and `ELIGIBLE FOR BONUS`, ~40 legacy rows at the top with dates in the
ID column, and one merged cell. BNY Ineligible has unlabeled columns 14–17 inside the
DRIVER RECORD span that still hold entries — always treat the span from the first to
the last `DRIVER RECORD` header as record columns.

## DRIVER RECORD entry grammar
`M/D/YY Accident (x2)` — incident date, reason, bonuses removed. Older rows use `(2)`
instead of `(x2)`, sometimes add the eligibility date after it (`… (2) Eligible Q3
10/01/25`), and a cell can hold two incidents. Leave notes look like `Out on WC since
07/13/26 - Returned 09/01/26`; new-hire notes like `NH BONUS ELIGIBLE Q1 - 04/01/25`.
The *first* date in a cell is the incident date; later dates are eligibility/return
dates.

## Bonus-date arithmetic
quarter(incident) = removed quarter #1 … #N → next quarter must be clean → payout on the
first day of the quarter after that. `bonus_payout_date()` in `reconcile_safety_bonus.py`
implements it. About half of historical dates on the sheets follow a one-quarter-later
convention; Jeremy confirmed the rule above on 2026-10-05, so existing dates are
reported, not rewritten.

## HR term report (`EmployeeInformation-TerminatedDrivers`)
Sheet `report`; metadata rows 1–5; header row 7: Employee Id, First Name, Last Name,
Employee Status, Department, Sub Department, Department Code, Date Terminated.
Sub-department → branch map lives in `SUBDEPT_TO_BRANCH`. Sub-department "Jockeys" is an
**excluded title** (`EXCLUDED_SUBDEPTS`): Yard Jockeys are never bonus-eligible and are never
added to any tab.

## HR active-driver roster
Full roster export Jeremy supplies each quarter. Layout is detected, not fixed: the loader
looks for an **Employee ID** column (`ROSTER_ID_HEADERS`), an optional **Name** column and an
optional **Job Title / Position** column (`ROSTER_TITLE_HEADERS`) in the first 15 rows. The
title is what identifies **Yard Jockeys** (`EXCLUDED_TITLE_KEYWORDS`), who must not be on any
bonus sheet - mostly a BNY concern. Once a real export has been seen, record its exact column
names here.

## Origami incident export
First sheet; title/filter rows, then a header row containing `Occurrence Number`.
Columns used: Employee, Employee Number (often blank), Loss Date, Location (`BNYBXT -
BNY TRANSPORTATION`, `BMABXT` = Boston, `BDCBXT`, `BFSBXT` = Fish, `BPABXT` = Philly),
Incident Type, Disciplinary action? (Yes / No / Pending), Tier?, Preventable? (Yes /
Pending). Ask for the export to be re-pulled if `Preventable?` is missing or a branch
location is absent from the filter.

## Highlight extent
All driver highlights cover columns A-E only (NAME, ID, LOCATION/COST CENTER, STATUS,
DOH), per Jeremy. The ACTION ITEMS tab names the column that changed.

## Colors used by the scripts
Yellow = moved/added to Terminated · Orange = duplicate / needs decision · Green = bonus
date computed · Blue = edited in v2 · Purple = promoted Ineligible → Eligible in v2 · Grey =
excluded title (Yard Jockey) found on an active tab, remove · Red
(reports only) = termed driver, branch unknown. Unknown-branch terms never appear on a
branch workbook's ACTION ITEMS tab — only in the reconciliation report. The same holds for
Origami incidents with no driver attached (`NO DRIVER`) or no matching driver row: they
appear only on the incident review report's `Anomalies` sheet.
