#!/usr/bin/env python3
"""Step 2 of the quarterly safety-bonus process: cross-check the Origami
"Incidents" export (preventable incidents, transportation personnel) against
the reconciled branch bonus workbooks.

For every incident row:
  * Preventable? blank/Pending          -> REVIEW bucket (yellow). Nothing is
    decided yet, so Jeremy needs to look at it.
  * Preventable = Yes, discipline Pending/blank -> REVIEW (yellow).
  * Disciplinary action? = Yes          -> the driver must be on the branch's
    Ineligible tab with a DRIVER RECORD entry dated the loss date.
      - driver on Eligible tab                 -> CRITICAL (red)
      - on Ineligible but no entry for date    -> MISSING ENTRY (orange)
      - entry exists but date differs (+/- N)  -> DATE MISMATCH (orange)
      - driver on Terminated tab               -> INFO (grey)
      - driver not found in any workbook       -> NOT FOUND (grey)
      - no employee name or number on incident -> NO DRIVER (grey, report-only)
  * Disciplinary action? = No           -> INFO only.

Output: one review workbook. Branch workbooks are not modified.

Usage:
  python3 check_incidents_vs_bonus.py --incidents <Origami export.xlsx> \
      --workbook-dir <dir with reconciled branch workbooks> \
      --output <review.xlsx>
"""
from __future__ import annotations

import argparse
import difflib
import re
import unicodedata
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.worksheet import Worksheet

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reconcile_safety_bonus import same_person  # noqa: E402

warnings.filterwarnings("ignore", category=UserWarning)

TABS: tuple[str, ...] = ("Eligible", "Ineligible", "Terminated")
HEADER_ROW: int = 1
INCIDENT_HEADER_MARKER: str = "Occurrence Number"
DATE_TOLERANCE_DAYS: int = 10
NAME_SIMILARITY_MIN: float = 0.85
INCIDENT_WORDS: tuple[str, ...] = ("ACCIDENT", "INCIDENT", "VIOLATION", "TAILSTRIKE", "STRIKE", "HANDHELD", "SPEEDING", "TAMPER", "DAMAGE")
LEAVE_WORDS: tuple[str, ...] = ("WC", "LOA", "PFL", "STD", "RETURN", "OUT ON", "OUT SINCE", "LIGHT DUTY", "NH ", "NEW HIRE", "ELIGIBLE")   # catches OWUSU/OWUSO, MEIJA/MEJIA style spellings

FILL_CRITICAL = PatternFill("solid", fgColor="FF9999")   # red: discipline Yes but driver Eligible
FILL_MISSING = PatternFill("solid", fgColor="FFC000")    # orange: no matching record entry / date mismatch
FILL_REVIEW = PatternFill("solid", fgColor="FFFF00")     # yellow: discipline blank or Pending
FILL_INFO = PatternFill("solid", fgColor="D9D9D9")       # grey: terminated / not found / discipline No
FILL_HEADER = PatternFill("solid", fgColor="BDD7EE")

LOCATION_TO_BRANCH: dict[str, str] = {
    "BNYBXT": "BNY", "BMABXT": "BB", "BDCBXT": "BDC", "BFSBXT": "FISH", "BPABXT": "BPA",
}
BRANCH_FILENAME_TOKENS: dict[str, str] = {
    "BALDOR_FISH": "FISH", "FISH": "FISH", "BNY": "BNY", "BPA": "BPA", "BDC": "BDC", "BB": "BB",
}
RECORD_DATE_RE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b")
TWO_DIGIT_YEAR_PIVOT: int = 2000

FINDING_ORDER: dict[str, int] = {
    "CRITICAL - on Eligible tab": 0,
    "MISSING ENTRY - on Ineligible, no record for loss date": 1,
    "DATE MISMATCH - record entry near loss date": 2,
    "REVIEW - preventable pending/blank": 3,
    "REVIEW - preventable Yes, discipline pending/blank": 3,
    "ID COLLISION - same ID, different name on sheet": 1,
    "AMBIGUOUS NAME - no usable employee #, several drivers share this name": 1,
    "NOT FOUND - driver in no workbook": 4,
    "NO DRIVER - incident has no employee attached": 4,
    "INFO - on Terminated tab": 5,
    "INFO - discipline No": 6,
    "INFO - location has no bonus workbook": 7,
}


@dataclass(frozen=True)
class DriverRow:
    branch: str
    tab: str
    row: int
    name: str
    employee_id: int | None
    record_dates: tuple[datetime, ...]
    record_text: tuple[str, ...]


@dataclass
class Incident:
    values: list[object]
    occurrence: str
    employee_name: str
    employee_id: int | None
    loss_date: datetime | None
    location: str
    incident_type: str
    discipline: str
    tier: str
    preventable: str

    @property
    def branch(self) -> str | None:
        code = self.location.split(" ")[0].strip().upper()
        return LOCATION_TO_BRANCH.get(code)


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def normalize_name(name: object) -> str:
    text = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode()
    text = re.sub(r"\(.*?\)", "", text)           # drop "(PART-TIME)" style suffixes
    text = re.sub(r"[^A-Z, ]", "", text.upper())
    return re.sub(r"\s+", " ", text).strip()


def name_tokens(name: object) -> set[str]:
    return {t for t in re.split(r"[ ,]+", normalize_name(name)) if len(t) > 1}


STRICT_NAME_RATIO: float = 0.85


def names_match(a: object, b: object) -> bool:
    """Name-ONLY matching (no usable employee #). Much stricter than the ID+name
    agreement rule: the full name must match (every token of the shorter name present
    in the longer, or the whole sorted-name strings nearly identical - OWUSU/OWUSO).
    A shared first name alone never matches. Blank names never match."""
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return False
    small, big = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    if len(small) >= 2 and small <= big:
        return True
    ratio = difflib.SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()
    return ratio >= STRICT_NAME_RATIO


def id_name_agree(sheet_name: object, origami_name: object) -> bool:
    """Used only when the employee # already matched: typo-tolerant (shared with step 1)."""
    return same_person(sheet_name, origami_name)


def parse_record_dates(entry: object) -> list[datetime]:
    """All dates in one DRIVER RECORD cell (a cell can hold two incidents)."""
    if isinstance(entry, datetime):
        return [entry]
    if not isinstance(entry, str):
        return []
    found: list[datetime] = []
    for month, day, year in ((int(a), int(b), int(c)) for a, b, c in RECORD_DATE_RE.findall(entry)):
        if year < 100:
            year += TWO_DIGIT_YEAR_PIVOT
        try:
            found.append(datetime(year, month, day))
        except ValueError:
            continue
    return found


def to_int(value: object) -> int | None:
    try:
        return int(str(value).strip()) if value not in (None, "") else None
    except ValueError:
        return None


def branch_from_filename(path: Path) -> str | None:
    upper = path.name.upper()
    for token, branch in BRANCH_FILENAME_TOKENS.items():
        if upper.startswith(token + "_") or f"-{token}_" in upper:
            return branch
    return None


# ----------------------------------------------------------------------------
# loading
# ----------------------------------------------------------------------------
def load_drivers(workbook_dir: Path) -> list[DriverRow]:
    drivers: list[DriverRow] = []
    for path in sorted(workbook_dir.glob("*.xlsx")):
        branch = branch_from_filename(path)
        if branch is None:
            continue
        wb = openpyxl.load_workbook(path, read_only=True)
        for tab in TABS:
            if tab not in wb.sheetnames:
                continue
            ws = wb[tab]
            rows = ws.iter_rows(values_only=True)
            header = [str(h).strip().upper() if h else "" for h in next(rows)]
            id_col = header.index("ID") if "ID" in header else 1
            name_col = header.index("NAME") if "NAME" in header else 0
            labeled = [i for i, h in enumerate(header) if h == "DRIVER RECORD"]
            rec_cols = list(range(min(labeled), max(labeled) + 1)) if labeled else []  # span incl. unlabeled gaps
            for idx, row in enumerate(rows, start=HEADER_ROW + 1):
                if not any(v not in (None, "") for v in row):
                    continue
                entries = [row[c] for c in rec_cols if c < len(row) and row[c] not in (None, "")]
                dated: list[tuple[datetime, str]] = [(d, str(e)) for e in entries for d in parse_record_dates(e)]
                drivers.append(DriverRow(
                    branch, tab, idx, str(row[name_col] or ""), to_int(row[id_col]) if isinstance(row[id_col], (int, str)) else None,
                    tuple(d for d, _ in dated), tuple(t for _, t in dated),
                ))
    return drivers


def load_incidents(path: Path) -> tuple[list[str], list[Incident]]:
    ws = openpyxl.load_workbook(path, read_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    header_idx = next(i for i, r in enumerate(rows) if r and INCIDENT_HEADER_MARKER in r)
    header = [str(h) if h is not None else "" for h in rows[header_idx]]
    col = {h: i for i, h in enumerate(header)}
    incidents: list[Incident] = []
    for r in rows[header_idx + 1:]:
        if not r or r[col["Occurrence Number"]] in (None, ""):
            continue
        get = lambda h: r[col[h]] if h in col and col[h] < len(r) else None
        loss = get("Loss Date")
        incidents.append(Incident(
            values=list(r), occurrence=str(get("Occurrence Number")),
            employee_name=str(get("Employee") or ""), employee_id=to_int(get("Employee Number")),
            loss_date=loss if isinstance(loss, datetime) else None,
            location=str(get("Location") or ""), incident_type=str(get("Incident Type") or ""),
            discipline=str(get("Disciplinary action?") or "").strip(), tier=str(get("Tier?") or ""),
            preventable=str(get("Preventable?") or "").strip(),
        ))
    return header, incidents


# ----------------------------------------------------------------------------
# matching
# ----------------------------------------------------------------------------
def find_driver(inc: Incident, drivers: list[DriverRow]) -> tuple[list[DriverRow], str]:
    """Return matching driver rows and how they were matched (ID / NAME / none)."""
    if inc.employee_id is not None:
        by_id = [d for d in drivers if d.employee_id == inc.employee_id]
        agreeing = [d for d in by_id if not normalize_name(d.name) or id_name_agree(d.name, inc.employee_name)]
        if agreeing:
            return agreeing, "ID"
        if by_id:
            return by_id, "ID-COLLISION"
    by_name = [d for d in drivers if names_match(d.name, inc.employee_name)]
    if inc.branch:
        same_branch = [d for d in by_name if d.branch == inc.branch]
        by_name = same_branch or by_name
    distinct_ids = {d.employee_id for d in by_name if d.employee_id is not None}
    if len(distinct_ids) > 1:
        return by_name, "AMBIGUOUS"   # namesakes: name alone cannot pick the driver
    return by_name, "NAME" if by_name else "none"


def closest_entry(driver: DriverRow, loss: datetime) -> tuple[int | None, str]:
    best: tuple[int, str] | None = None
    for d, text in zip(driver.record_dates, driver.record_text):
        delta = abs((d - loss).days)
        if best is None or delta < best[0]:
            best = (delta, text)
    return (best[0], best[1]) if best else (None, "")


def incident_key(inc: Incident) -> str:
    return str(inc.employee_id) if inc.employee_id is not None else normalize_name(inc.employee_name)


def evaluate(inc: Incident, drivers: list[DriverRow], claimed: set[tuple[str, datetime]]) -> tuple[str, str, str]:
    """Returns (finding, where_found, matched_entry). `claimed` = (driver key, loss date)
    for every incident in the export, so a nearby entry that belongs to a *different*
    incident of the same driver is not mistaken for a date typo."""
    if inc.employee_id is None and not normalize_name(inc.employee_name):
        # Report-only: an incident with no employee attached cannot be placed on any
        # branch sheet, so it never becomes a branch action item.
        return "NO DRIVER - incident has no employee attached", "", ""
    matches, how = find_driver(inc, drivers)
    where = "; ".join(f"{d.branch}/{d.tab} row {d.row} ({d.name})" for d in matches)
    if how == "NAME":
        where += " [matched by NAME - no employee # in export]" if inc.employee_id is None else " [ID not found; matched by NAME]"
    if how == "ID-COLLISION":
        return "ID COLLISION - same ID, different name on sheet", where, ""
    if how == "AMBIGUOUS" and inc.discipline.upper() == "YES":
        return "AMBIGUOUS NAME - no usable employee #, several drivers share this name", where, ""
    if inc.preventable and inc.preventable.upper() != "YES":
        return "REVIEW - preventable pending/blank", where, ""
    if inc.discipline.upper() == "NO":
        return "INFO - discipline No", where, ""
    if inc.discipline.upper() != "YES":
        return "REVIEW - preventable Yes, discipline pending/blank", where, ""
    if not matches:
        if inc.branch is None:
            return "INFO - location has no bonus workbook", where, ""
        return "NOT FOUND - driver in no workbook", where, ""
    eligible = [d for d in matches if d.tab == "Eligible"]
    ineligible = [d for d in matches if d.tab == "Ineligible"]
    if eligible:
        # Still on Eligible = would be paid. Even if an Ineligible copy also exists,
        # the Eligible row is the one that pays out, so this stays CRITICAL.
        return "CRITICAL - on Eligible tab", where, ""
    if ineligible:
        if inc.loss_date is None:
            return "MISSING ENTRY - on Ineligible, no record for loss date", where, ""
        best = min((closest_entry(d, inc.loss_date) for d in ineligible), key=lambda x: (x[0] is None, x[0]))
        delta, text = best
        if delta == 0:
            return "OK", where, text
        if delta is not None and delta <= DATE_TOLERANCE_DAYS:
            entry_dates = [d for drv in ineligible for d, t in zip(drv.record_dates, drv.record_text) if t == text]
            other_incident = any((incident_key(inc), d) in claimed and d != inc.loss_date for d in entry_dates)
            if not other_incident:
                return "DATE MISMATCH - record entry near loss date", where, text
        return "MISSING ENTRY - on Ineligible, no record for loss date", where, ""
    return "INFO - on Terminated tab", where, ""


FINDING_FILL: dict[str, PatternFill | None] = {
    "CRITICAL - on Eligible tab": FILL_CRITICAL,
    "MISSING ENTRY - on Ineligible, no record for loss date": FILL_MISSING,
    "DATE MISMATCH - record entry near loss date": FILL_MISSING,
    "REVIEW - preventable pending/blank": FILL_REVIEW,
    "REVIEW - preventable Yes, discipline pending/blank": FILL_REVIEW,
    "ID COLLISION - same ID, different name on sheet": FILL_CRITICAL,
    "AMBIGUOUS NAME - no usable employee #, several drivers share this name": FILL_CRITICAL,
    "NOT FOUND - driver in no workbook": FILL_INFO,
    "NO DRIVER - incident has no employee attached": FILL_INFO,
    "INFO - on Terminated tab": FILL_INFO,
    "INFO - discipline No": FILL_INFO,
    "INFO - location has no bonus workbook": FILL_INFO,
    "OK": None,
}


# ----------------------------------------------------------------------------
# output
# ----------------------------------------------------------------------------
def autosize(ws: Worksheet, cap: int = 60) -> None:
    for col_cells in ws.columns:
        width = max((len(str(c.value)) for c in col_cells if c.value is not None), default=8)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max(10, width + 2), cap)


def style_header(ws: Worksheet) -> None:
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = FILL_HEADER
    ws.freeze_panes = "A2"


def sheet_entries_not_in_origami(drivers: list[DriverRow], incidents: list[Incident]) -> list[list[object]]:
    """Reverse check: quarter-dated DRIVER RECORD entries on active tabs with no Origami incident."""
    dated = [i.loss_date for i in incidents if i.loss_date]
    if not dated:
        return []
    start, end = min(dated), max(dated)
    claimed_ids = {(i.employee_id, i.loss_date) for i in incidents if i.loss_date and i.employee_id is not None}
    by_name = [(i.employee_name, i.loss_date) for i in incidents if i.loss_date]
    rows: list[list[object]] = []
    seen: set[tuple[str, int, datetime]] = set()
    for d in drivers:
        if d.tab == "Terminated":
            continue
        for date, text in zip(d.record_dates, d.record_text):
            upper = text.upper()
            first_dates = parse_record_dates(text)
            if not (start <= date <= end) or not first_dates or first_dates[0] != date:
                continue  # only the incident date itself, not eligibility/return dates
            if not any(w in upper for w in INCIDENT_WORDS) or any(w in upper for w in LEAVE_WORDS):
                continue
            if (d.branch, d.row, date) in seen:
                continue
            seen.add((d.branch, d.row, date))
            if (d.employee_id, date) in claimed_ids or any(dt == date and names_match(n, d.name) for n, dt in by_name):
                continue
            rows.append([d.branch, d.tab, d.row, d.employee_id, d.name, date.date(), text])
    return rows


def write_review(path: Path, header: list[str], results: list[tuple[Incident, str, str, str]],
                 reverse_rows: list[list[object]] | None = None) -> None:
    wb = openpyxl.Workbook()
    summary = wb.active
    summary.title = "Summary"
    counts: dict[str, int] = {}
    for _, finding, _, _ in results:
        counts[finding] = counts.get(finding, 0) + 1
    summary.append(["Incident export vs. Safety Bonus sheets"])
    summary["A1"].font = Font(bold=True, size=13)
    summary.append(["Generated", datetime.now().strftime("%m/%d/%Y %I:%M %p")])
    summary.append(["Incidents reviewed", len(results)])
    summary.append([])
    summary.append(["Finding", "Count", "Color"])
    for finding in sorted(counts, key=lambda f: FINDING_ORDER.get(f, 99)):
        summary.append([finding, counts[finding]])
        fill = FINDING_FILL.get(finding)
        if fill:
            summary.cell(row=summary.max_row, column=3).fill = fill
    summary.append([])
    summary.append(["REVIEW = Preventable? is Pending/blank, or Preventable = Yes but Disciplinary action? is Pending/blank."])
    summary.append(["If the export lacks a 'Preventable?' column, all rows are treated as preventable and only discipline is checked."])
    summary.column_dimensions["A"].width = 60

    extra = ["Branch", "Finding", "Found On (branch/tab row)", "Matching Record Entry"]
    full = wb.create_sheet("Incidents_Reviewed")
    full.append(header + extra)
    style_header(full)
    for inc, finding, where, entry in sorted(results, key=lambda x: (FINDING_ORDER.get(x[1], 99), x[0].loss_date or datetime.min)):
        full.append(inc.values + [inc.branch or "", finding, where, entry])
        fill = FINDING_FILL.get(finding)
        if fill:
            for c in full[full.max_row]:
                c.fill = fill
    for col in ("G", "H"):
        for cell in full[col][1:]:
            cell.number_format = "m/d/yyyy"
    autosize(full)

    anomalies = wb.create_sheet("Anomalies")
    anomalies.append(["Occurrence #", "Employee", "Employee #", "Loss Date", "Location", "Incident Type", "Tier", "Discipline", "Finding", "Found On", "Nearest Record Entry"])
    style_header(anomalies)
    for inc, finding, where, entry in sorted(results, key=lambda x: (FINDING_ORDER.get(x[1], 99), x[0].loss_date or datetime.min)):
        if finding == "OK" or finding.startswith("INFO"):
            continue
        anomalies.append([inc.occurrence, inc.employee_name, inc.employee_id, inc.loss_date.date() if inc.loss_date else None,
                          inc.location, inc.incident_type, inc.tier, inc.discipline, finding, where, entry])
        for c in anomalies[anomalies.max_row]:
            c.fill = FINDING_FILL[finding]
    autosize(anomalies)

    rev = wb.create_sheet("Sheet_Entries_Not_In_Origami")
    rev.append(["Branch", "Tab", "Row", "Employee ID", "Name", "Entry Date", "DRIVER RECORD entry", "Note"])
    style_header(rev)
    for r in reverse_rows or []:
        rev.append(r + ["Dated inside the export window but no matching Origami incident - verify it was reported"])
    autosize(rev)
    summary.append(["Sheet entries with no Origami incident (info)", len(reverse_rows or [])])

    wb.save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--incidents", required=True, type=Path)
    parser.add_argument("--workbook-dir", required=True, type=Path, help="Folder with the (reconciled) branch workbooks")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--start", type=lambda v: datetime.strptime(v, "%Y-%m-%d"), help="Quarter start (YYYY-MM-DD); incidents with an earlier loss date are ignored")
    parser.add_argument("--end", type=lambda v: datetime.strptime(v, "%Y-%m-%d"), help="Quarter end (YYYY-MM-DD); later loss dates are ignored")
    args = parser.parse_args()

    drivers = load_drivers(args.workbook_dir)
    header, all_incidents = load_incidents(args.incidents)
    incidents = [i for i in all_incidents if i.loss_date and (not args.start or i.loss_date >= args.start) and (not args.end or i.loss_date <= args.end)]
    if len(incidents) != len(all_incidents):
        print(f"Window {args.start.date() if args.start else '...'} to {args.end.date() if args.end else '...'}: "
              f"{len(all_incidents) - len(incidents)} of {len(all_incidents)} incidents outside the quarter were ignored")
    claimed = {(incident_key(i), i.loss_date) for i in incidents if i.loss_date}
    results = [(inc, *evaluate(inc, drivers, claimed)) for inc in incidents]
    reverse_rows = sheet_entries_not_in_origami(drivers, incidents)
    write_review(args.output, header, results, reverse_rows)
    print(f"  Sheet entries not in Origami (info): {len(reverse_rows)}")

    counts: dict[str, int] = {}
    for _, finding, _, _ in results:
        counts[finding] = counts.get(finding, 0) + 1
    print(f"Incidents: {len(incidents)}  Driver rows indexed: {len(drivers)}")
    for finding in sorted(counts, key=lambda f: FINDING_ORDER.get(f, 99)):
        print(f"  {finding}: {counts[finding]}")
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
