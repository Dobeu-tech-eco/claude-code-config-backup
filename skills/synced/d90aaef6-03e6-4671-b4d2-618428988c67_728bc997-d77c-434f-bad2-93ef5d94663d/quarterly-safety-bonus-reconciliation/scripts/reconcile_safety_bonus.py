#!/usr/bin/env python3
"""Quarterly Safety Bonus reconciliation for Baldor branch workbooks.

Reads one workbook per branch (tabs: Eligible / Ineligible / Terminated) plus the
HR "Employee Information - Terminated Drivers" export, then:

  1. Moves every driver on the termination report off the Eligible/Ineligible
     tabs and onto that branch's Terminated tab (row highlighted, STATUS = TERM date).
  2. Adds termed drivers that exist in no workbook to the right branch's
     Terminated tab when the HR sub-department maps cleanly to one branch.
  3. Flags (highlights + reports, never auto-resolves) duplicate IDs: same tab
     twice, Eligible+Ineligible in one branch, active tab + Terminated tab,
     and the same ID in two branches.
  4. Fills blank ELIGIBLE FOR BONUS dates on Ineligible accident rows using the
     quarter rule, skipping Workers Comp / LOA style rows.
  5. Removes empty gap rows between drivers.
  6. Writes an exceptions report workbook listing everything it did or flagged.

Usage:
  python3 reconcile_safety_bonus.py --input-dir <dir with branch xlsx files> \
      --term-report <EmployeeInformation-TerminatedDrivers.xlsx> \
      --output-dir <dir> --quarter-label Q3_2026
"""
from __future__ import annotations

import argparse
import difflib
import re
import shutil
import unicodedata
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable

import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.worksheet import Worksheet

warnings.filterwarnings("ignore", category=UserWarning)

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
ACTIVE_TABS: tuple[str, ...] = ("Eligible", "Ineligible")
TERMINATED_TAB: str = "Terminated"
HEADER_ROW: int = 1
FIRST_DATA_ROW: int = 2
TERM_REPORT_HEADER_ROW: int = 7

FILL_MOVED = PatternFill("solid", fgColor="FFFF00")      # yellow: moved/added to Terminated
FILL_DUPLICATE = PatternFill("solid", fgColor="FFC000")  # orange: duplicate flag, review needed
FILL_DATE_FILLED = PatternFill("solid", fgColor="C6EFCE")  # green: bonus date computed
FILL_UNKNOWN = PatternFill("solid", fgColor="FF9999")    # red: termed driver, branch unknown
FILL_EXCLUDED = PatternFill("solid", fgColor="D9D9D9")   # grey: excluded title (Yard Jockey), report only
FILL_HEADER = PatternFill("solid", fgColor="D9D9D9")
HIGHLIGHT_LAST_COLUMN: int = 5   # Jeremy's rule: highlight a driver row in columns A-E only

DATE_FORMAT_EXCEL: str = "m/d/yyyy"
TERM_STATUS_FORMAT: str = "TERM %m/%d/%y"
ELIG_YES: str = "Y"
ELIG_NO: str = "N"

# Filename token -> canonical branch code
BRANCH_FILENAME_TOKENS: dict[str, str] = {
    "BALDOR_FISH": "FISH", "FISH": "FISH", "BNY": "BNY", "BPA": "BPA", "BDC": "BDC", "BB": "BB",
}
# HR sub-department -> branch (only unambiguous ones; anything else is "unknown")
SUBDEPT_TO_BRANCH: dict[str, str] = {
    "BB DRIVERS": "BB", "PORTLAND DRIVERS": "BB", "BB TRANSPORTATION": "BB",
    "PHILLY DRIVERS": "BPA",
    "BDC DRIVERS": "BDC",
    "BALDOR FISH DRIVERS": "FISH",
    "HOURLY DRIVERS": "BNY", "DRIVERS IN TRAINING": "BNY", "LI DRIVERS": "BNY",
    "JOCKEYS": "BNY", "WAPPINGERS FALLS DRIVERS": "BNY",
}
BRANCH_DEFAULT_LOCATION: dict[str, str] = {
    "BB": "BOS", "BPA": "PHILLY", "BDC": "DC", "FISH": "FISH", "BNY": "NY",
}
# Reasons / note keywords that mean "leave" -> bonus date stays blank
LEAVE_KEYWORDS: tuple[str, ...] = (
    "WORKERS", "WOKERS", "WC", "LOA", "PFL", "STDB", "STD", "FMLA", "LEAVE", "LIGHT DUTY", "COMP",
)
# Temp / staffing-agency drivers are never bonus-eligible (not converted), so they
# never get an ELIGIBLE FOR BONUS date - but their accidents still belong on Ineligible.
TEMP_KEYWORDS: tuple[str, ...] = ("TEMP", "VERTEX", "AGENCY", "STAFFING")
# Job titles / HR sub-departments that are NEVER bonus-eligible: these people do not
# belong on any bonus sheet and are never added. Yard Jockeys are the main case (BNY).
EXCLUDED_TITLE_KEYWORDS: tuple[str, ...] = ("YARD JOCKEY", "JOCKEY")
EXCLUDED_SUBDEPTS: tuple[str, ...] = ("JOCKEYS",)
# Cost-center numbers (column C on the bonus sheets) that are NOT eligible employees -
# they do not belong on any sheet and their rows are removed outright (Jeremy, Q3 2026).
# Stored normalised (leading zeros stripped) so "011"/"11"/11 all match. Mostly BNY,
# the only branch whose column C is a COST CENTER column; elsewhere column C is a text
# LOCATION, which never matches a numeric cost center.
COST_CENTER_COLUMN: int = 3   # literally column C
EXCLUDED_COST_CENTERS: frozenset[str] = frozenset({"850", "250", "745", "11", "512", "499"})
ROSTER_ID_HEADERS: tuple[str, ...] = ("EMPLOYEE ID", "EMPLOYEE #", "EMPLOYEE NUMBER", "EMP ID", "ID")
ROSTER_TITLE_HEADERS: tuple[str, ...] = ("JOB TITLE", "TITLE", "POSITION", "JOB")
ROSTER_NAME_HEADERS: tuple[str, ...] = ("EMPLOYEE NAME", "NAME", "FULL NAME")
ROSTER_HEADER_SCAN_ROWS: int = 15
INCIDENT_DATE_RE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b")
INCIDENT_COUNT_RE = re.compile(r"\(\s*x?\s*(\d+)\s*\)", re.IGNORECASE)
MONTHS_PER_QUARTER: int = 3
QUARTERS_PER_YEAR: int = 4
TWO_DIGIT_YEAR_PIVOT: int = 2000
NAME_SIMILARITY_MIN: float = 0.9   # OWUSU/OWUSO, CORPORN/CORPORAN -> probably the same driver


NAME_RATIO_SAME: float = 0.75     # sorted-token strings this similar = same person (typo tolerance)
NAME_RATIO_WITH_OVERLAP: float = 0.5   # one shared token plus this much similarity = same person


def name_tokens(name: object) -> set[str]:
    text = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode()
    text = re.sub(r"\(.*?\)", "", text).upper()
    return {t for t in re.split(r"[^A-Z]+", text) if len(t) > 1}


def same_person(sheet_name: object, other_name: object) -> bool:
    """Identity is ID + name. Names 'agree' when they share two tokens, or one token
    plus overall similarity, or are near-identical overall (ARIA/ARIAS, WHTE/WHITE).
    Blank sheet names agree with anything. GARCIA QUENNEDYS vs GUZMAN RICHARD does not."""
    a, b = name_tokens(sheet_name), name_tokens(other_name)
    if not a or not b:
        return True
    overlap = len(a & b)
    if overlap >= 2 or (overlap == 1 and min(len(a), len(b)) == 1):
        return True
    ratio = difflib.SequenceMatcher(None, " ".join(sorted(a)), " ".join(sorted(b))).ratio()
    return ratio >= NAME_RATIO_SAME or (overlap >= 1 and ratio >= NAME_RATIO_WITH_OVERLAP)


def normalized_name(name: object) -> str:
    return " ".join(sorted(name_tokens(name)))


# ----------------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------------
@dataclass
class TermRecord:
    employee_id: int
    first_name: str
    last_name: str
    sub_department: str
    department_code: str
    date_terminated: datetime

    @property
    def display_name(self) -> str:
        return f"{self.last_name}, {self.first_name}".upper()

    @property
    def branch(self) -> str | None:
        return SUBDEPT_TO_BRANCH.get(self.sub_department.strip().upper())

    @property
    def is_excluded(self) -> bool:
        return is_excluded_title(self.sub_department)


def is_excluded_title(text: object) -> bool:
    """True for titles / sub-departments that are never bonus-eligible (Yard Jockey)."""
    upper = str(text or "").strip().upper()
    return upper in EXCLUDED_SUBDEPTS or any(k in upper for k in EXCLUDED_TITLE_KEYWORDS)


def normalize_cost_center(value: object) -> str | None:
    """Normalise a column-C value for comparison: all-digit values lose leading zeros
    ('011' -> '11', 11.0 -> '11'); text (e.g. 'BOS') is upper-cased as-is. Blank -> None."""
    text = str(value if value is not None else "").strip()
    if not text:
        return None
    if text.replace(".", "", 1).isdigit():
        return str(int(float(text)))
    return text.upper()


def is_excluded_cost_center(value: object) -> bool:
    return normalize_cost_center(value) in EXCLUDED_COST_CENTERS


@dataclass
class Tab:
    branch: str
    name: str
    ws: Worksheet
    headers: dict[str, int] = field(default_factory=dict)      # header -> 1-based col
    record_cols: list[int] = field(default_factory=list)       # DRIVER RECORD cols in order
    last_header_col: int = 0

    def __post_init__(self) -> None:
        for cell in self.ws[HEADER_ROW]:
            if cell.value is None:
                continue
            label = str(cell.value).strip().upper()
            self.last_header_col = max(self.last_header_col, cell.column)
            if label == "DRIVER RECORD":
                self.record_cols.append(cell.column)
            elif label not in self.headers:
                self.headers[label] = cell.column
        # Some sheets (BNY Ineligible) have unlabeled columns inside the DRIVER RECORD
        # span that still hold entries. Treat the whole span as record columns so
        # nothing is dropped when a row is moved.
        if self.record_cols:
            self.record_cols = list(range(min(self.record_cols), max(self.record_cols) + 1))

    def col(self, header: str) -> int | None:
        return self.headers.get(header.upper())

    def is_blank_row(self, row: int) -> bool:
        # values_only iteration reads the cell store without materialising cells
        values = next(self.ws.iter_rows(min_row=row, max_row=row, values_only=True), ())
        return all(v in (None, "") for v in values)

    def last_data_row(self) -> int:
        # Scan the sparse cell store directly; ws.max_row counts styled-but-empty rows.
        populated = (r for (r, _), cell in self.ws._cells.items() if cell.value not in (None, ""))
        return max(populated, default=HEADER_ROW)

    def data_rows(self) -> Iterable[int]:
        return (r for r in range(FIRST_DATA_ROW, self.last_data_row() + 1) if not self.is_blank_row(r))

    def value(self, row: int, header: str):
        col = self.col(header)
        return self.ws.cell(row=row, column=col).value if col else None

    def employee_id(self, row: int) -> int | None:
        raw = self.value(row, "ID")
        return raw if isinstance(raw, int) else None

    def row_values(self, row: int) -> dict[str, object]:
        """Header-keyed snapshot of a row, DRIVER RECORD entries as a list."""
        out: dict[str, object] = {h: self.ws.cell(row=row, column=c).value for h, c in self.headers.items()}
        out["DRIVER RECORD"] = [self.ws.cell(row=row, column=c).value for c in self.record_cols]
        return out

    def highlight(self, row: int, fill: PatternFill) -> None:
        for col in range(1, HIGHLIGHT_LAST_COLUMN + 1):
            self.ws.cell(row=row, column=col).fill = fill


@dataclass
class ReportRow:
    sheet: str
    values: list[object]
    fill: PatternFill | None = None


# ----------------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------------
def branch_from_filename(path: Path) -> str | None:
    upper = path.name.upper()
    for token, branch in BRANCH_FILENAME_TOKENS.items():
        if upper.startswith(token + "_") or f"-{token}_" in upper:
            return branch
    return None


def load_term_report(path: Path) -> dict[int, TermRecord]:
    ws = openpyxl.load_workbook(path, read_only=True)["report"]
    records: dict[int, TermRecord] = {}
    for row in ws.iter_rows(min_row=TERM_REPORT_HEADER_ROW + 1, values_only=True):
        if not isinstance(row[0], int) or not isinstance(row[7], datetime):
            continue
        records[row[0]] = TermRecord(
            employee_id=row[0], first_name=str(row[1] or ""), last_name=str(row[2] or ""),
            sub_department=str(row[5] or ""), department_code=str(row[6] or ""), date_terminated=row[7],
        )
    return records


def load_branch(path: Path) -> tuple[str, openpyxl.Workbook, dict[str, Tab]]:
    branch = branch_from_filename(path)
    if branch is None:
        raise ValueError(f"Cannot determine branch from filename: {path.name}")
    wb = openpyxl.load_workbook(path)
    tabs = {name: Tab(branch, name, wb[name]) for name in (*ACTIVE_TABS, TERMINATED_TAB) if name in wb.sheetnames}
    missing = [n for n in (*ACTIVE_TABS, TERMINATED_TAB) if n not in tabs]
    if missing:
        raise ValueError(f"{path.name} is missing tabs: {missing}")
    return branch, wb, tabs


# ----------------------------------------------------------------------------
# Row movement
# ----------------------------------------------------------------------------
def append_row(dst: Tab, values: dict[str, object], status_text: str) -> int:
    target = dst.last_data_row() + 1
    for header, col in dst.headers.items():
        if header in values and values[header] not in (None, ""):
            cell = dst.ws.cell(row=target, column=col, value=values[header])
            if isinstance(values[header], datetime):
                cell.number_format = DATE_FORMAT_EXCEL
    for src_val, col in zip(values.get("DRIVER RECORD", []), dst.record_cols):
        if src_val not in (None, ""):
            dst.ws.cell(row=target, column=col, value=src_val)
    if dst.col("STATUS"):
        dst.ws.cell(row=target, column=dst.col("STATUS"), value=status_text)
    if dst.col("ELIG"):
        dst.ws.cell(row=target, column=dst.col("ELIG"), value="N")
    dst.highlight(target, FILL_MOVED)
    return target


def richest_row(tab_rows: list[tuple[Tab, int]]) -> tuple[Tab, int]:
    """When a termed driver appears several times, keep the copy with the most data."""
    def filled(tr: tuple[Tab, int]) -> int:
        tab, row = tr
        return sum(1 for c in tab.ws[row] if c.value not in (None, ""))
    return max(tab_rows, key=filled)


def delete_rows_bottom_up(tab: Tab, rows: Iterable[int]) -> None:
    """Delete rows as contiguous blocks, bottom-up, so earlier indices stay valid
    and openpyxl shifts the cell store as few times as possible."""
    ordered = sorted(set(rows), reverse=True)
    while ordered:
        end = ordered[0]
        start = end
        while len(ordered) > 1 and ordered[1] == start - 1:
            ordered.pop(0)
            start -= 1
        ordered.pop(0)
        tab.ws.delete_rows(start, end - start + 1)


# ----------------------------------------------------------------------------
# Quarter / bonus-date rule
# ----------------------------------------------------------------------------
def quarter_index(d: datetime) -> int:
    return d.year * QUARTERS_PER_YEAR + (d.month - 1) // MONTHS_PER_QUARTER


def quarter_start(index: int) -> datetime:
    year, q = divmod(index, QUARTERS_PER_YEAR)
    return datetime(year, q * MONTHS_PER_QUARTER + 1, 1)


def bonus_payout_date(incident: datetime, bonuses_removed: int) -> datetime:
    """Incident quarter counts as the first removed quarter; after the removed
    quarters the driver must earn one clean quarter; payout is the first day of
    the quarter after that clean quarter (how the sheets record it, e.g. 10/1)."""
    first_earning = quarter_index(incident) + bonuses_removed
    return quarter_start(first_earning + 1)


def parse_incident(entry: object) -> tuple[datetime, int] | None:
    if not isinstance(entry, str):
        return None
    date_match = INCIDENT_DATE_RE.search(entry)
    count_match = INCIDENT_COUNT_RE.search(entry)
    if not date_match or not count_match:
        return None
    month, day, year = (int(x) for x in date_match.groups())
    if year < 100:
        year += TWO_DIGIT_YEAR_PIVOT
    try:
        return datetime(year, month, day), int(count_match.group(1))
    except ValueError:
        return None


def latest_incident(record_entries: list[object]) -> tuple[datetime, int] | None:
    parsed = [p for p in (parse_incident(e) for e in record_entries) if p]
    return max(parsed, key=lambda p: p[0]) if parsed else None


def looks_like_leave(reason: object, record_entries: list[object]) -> bool:
    texts = [str(reason or "")] + [str(e) for e in record_entries if isinstance(e, str)]
    latest_note = texts[-1].upper() if len(texts) > 1 else ""
    reason_up = str(reason or "").upper()
    return any(k in reason_up for k in LEAVE_KEYWORDS) or any(k in latest_note for k in ("WC", "LOA", "PFL", "STD"))


@dataclass(frozen=True)
class RosterRecord:
    employee_id: int
    name: str
    title: str

    @property
    def is_excluded(self) -> bool:
        return is_excluded_title(self.title)


def find_roster_columns(ws: Worksheet) -> tuple[int, int | None, int | None, int | None]:
    """Locate the header row and the ID / name / title columns of an HR roster export.
    Returns (header_row, id_col, name_col, title_col); cols are 0-based or None."""
    for row_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=ROSTER_HEADER_SCAN_ROWS, values_only=True), start=1):
        labels = [str(v or "").strip().upper() for v in row]
        id_col = next((i for i, l in enumerate(labels) if l in ROSTER_ID_HEADERS), None)
        if id_col is None:
            continue
        name_col = next((i for i, l in enumerate(labels) if l in ROSTER_NAME_HEADERS), None)
        title_col = next((i for i, l in enumerate(labels) if l in ROSTER_TITLE_HEADERS), None)
        return row_idx, id_col, name_col, title_col
    return 0, None, None, None


def load_active_roster(path: Path) -> dict[int, RosterRecord]:
    """HR active-driver roster -> {employee id: RosterRecord}. Tolerant of layout:
    finds the header row by its Employee ID column; title column is optional."""
    ws = openpyxl.load_workbook(path, read_only=True).worksheets[0]
    header_row, id_col, name_col, title_col = find_roster_columns(ws)
    if id_col is None:
        raise SystemExit(f"{path.name}: no Employee ID column found in the first {ROSTER_HEADER_SCAN_ROWS} rows")
    records: dict[int, RosterRecord] = {}
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        eid = row[id_col] if id_col < len(row) else None
        if not isinstance(eid, int):
            continue
        name = str(row[name_col] or "") if name_col is not None and name_col < len(row) else ""
        title = str(row[title_col] or "") if title_col is not None and title_col < len(row) else ""
        records[eid] = RosterRecord(eid, name, title)
    return records


# ----------------------------------------------------------------------------
# Reconciliation
# ----------------------------------------------------------------------------
class Reconciler:
    def __init__(self, term: dict[int, TermRecord], quarter_label: str,
                 roster: dict[int, RosterRecord] | None = None) -> None:
        self.term = term
        self.roster = roster or {}
        self.quarter_label = quarter_label
        self.branches: dict[str, tuple[openpyxl.Workbook, dict[str, Tab], Path]] = {}
        self.report: list[ReportRow] = []
        self.term_outcome: dict[int, tuple[str, str]] = {}   # id -> (branch, action)
        self.excluded_ids: set[int] = set()   # employee ids pulled for an excluded cost center

    # -- loading ------------------------------------------------------------
    def add_branch(self, path: Path) -> None:
        branch, wb, tabs = load_branch(path)
        self.branches[branch] = (wb, tabs, path)

    def all_tabs(self) -> Iterable[Tab]:
        for _, tabs, _ in self.branches.values():
            yield from tabs.values()

    # -- excluded cost centers (column C) ------------------------------------
    def remove_excluded_cost_centers(self) -> None:
        """Rows whose column-C value is an excluded cost center are not eligible
        employees; delete them from every tab and log each removal. Runs first so the
        removed rows never reach termination / duplicate / date checks."""
        for branch, (_, tabs, _) in self.branches.items():
            for tab in tabs.values():
                to_delete: list[int] = []
                for row in tab.data_rows():
                    raw = tab.ws.cell(row=row, column=COST_CENTER_COLUMN).value
                    if not is_excluded_cost_center(raw):
                        continue
                    to_delete.append(row)
                    eid = tab.employee_id(row)
                    if eid is not None:
                        self.excluded_ids.add(eid)
                    self.report.append(ReportRow("Excluded_Cost_Centers", [
                        branch, tab.name, eid, tab.value(row, "NAME"),
                        normalize_cost_center(raw), "Removed - cost center not a bonus-eligible employee",
                    ], FILL_EXCLUDED))
                delete_rows_bottom_up(tab, to_delete)

    # -- step 1 & 2: terminated drivers --------------------------------------
    def process_terminations(self) -> None:
        for branch, (_, tabs, _) in self.branches.items():
            term_tab = tabs[TERMINATED_TAB]
            already_termed = {term_tab.employee_id(r) for r in term_tab.data_rows()}
            found: dict[int, list[tuple[Tab, int]]] = defaultdict(list)
            for tab_name in ACTIVE_TABS:
                tab = tabs[tab_name]
                for row in tab.data_rows():
                    eid = tab.employee_id(row)
                    if eid in self.term:
                        found[eid].append((tab, row))
            to_delete: dict[str, list[int]] = defaultdict(list)
            for eid, locations in found.items():
                rec = self.term[eid]
                status = rec.date_terminated.strftime(TERM_STATUS_FORMAT)
                agreeing = [(t, r) for t, r in locations if same_person(t.value(r, "NAME"), rec.display_name)]
                disagreeing = [(t, r) for t, r in locations if (t, r) not in agreeing]
                for t, r in disagreeing:
                    t.highlight(r, FILL_DUPLICATE)
                    self.report.append(ReportRow("ID_Name_Mismatch", [
                        branch, eid, t.value(r, "NAME"), rec.display_name, f"{t.name} row {r}",
                        "HR term report ID found on sheet but the NAME is different - NOT moved; verify the employee number",
                    ]))
                if not agreeing:
                    self.term_outcome[eid] = (branch, "ID on sheet but name differs - NOT moved (see ID_Name_Mismatch)")
                    continue
                locations = agreeing
                keep_tab, keep_row = richest_row(locations)
                if eid in already_termed:
                    action = "Already on Terminated tab; removed from active tab(s)"
                    for r in term_tab.data_rows():
                        if term_tab.employee_id(r) == eid:
                            term_tab.highlight(r, FILL_MOVED)
                            if term_tab.col("STATUS") and term_tab.value(r, "STATUS") in (None, ""):
                                term_tab.ws.cell(row=r, column=term_tab.col("STATUS"), value=status)
                else:
                    append_row(term_tab, keep_tab.row_values(keep_row), status)
                    action = "Moved to Terminated tab"
                from_tabs = ", ".join(f"{t.name} (row {r})" for t, r in locations)
                self.report.append(ReportRow("Moved_To_Terminated", [
                    branch, eid, keep_tab.value(keep_row, "NAME"), rec.display_name, rec.sub_department,
                    rec.date_terminated.date(), from_tabs, action,
                ]))
                self.term_outcome[eid] = (branch, action)
                for tab, row in locations:
                    to_delete[tab.name].append(row)
            for tab_name, rows in to_delete.items():
                delete_rows_bottom_up(tabs[tab_name], rows)
            for eid in already_termed:
                if eid in self.term and eid not in self.term_outcome:
                    self.term_outcome[eid] = (branch, "Already on Terminated tab (no change)")

    def add_missing_terminations(self) -> None:
        for eid, rec in self.term.items():
            if eid in self.term_outcome:
                continue
            if eid in self.excluded_ids:
                self.term_outcome[eid] = ("EXCLUDED", "Pulled for an excluded cost center - not re-added to Terminated")
                continue
            if rec.is_excluded:
                self.term_outcome[eid] = ("EXCLUDED", "Not on any sheet; excluded title (Yard Jockey) - never added")
                continue
            branch = rec.branch
            if branch is None or branch not in self.branches:
                self.term_outcome[eid] = ("UNKNOWN", "Not in any workbook; branch could not be determined")
                self.report.append(ReportRow("Unknown_Branch", [
                    eid, rec.display_name, rec.sub_department, rec.department_code, rec.date_terminated.date(),
                ], FILL_UNKNOWN))
                continue
            term_tab = self.branches[branch][1][TERMINATED_TAB]
            values: dict[str, object] = {
                "NAME": rec.display_name, "ID": eid, "LOCATION": BRANCH_DEFAULT_LOCATION[branch],
                "$$": 150, "DRIVER RECORD": [f"Not on {self.quarter_label} sheets; added from HR term report"],
            }
            append_row(term_tab, values, rec.date_terminated.strftime(TERM_STATUS_FORMAT))
            self.term_outcome[eid] = (branch, "Not in any workbook; added to Terminated tab from HR report")
            self.report.append(ReportRow("Added_To_Terminated", [
                branch, eid, rec.display_name, rec.sub_department, rec.date_terminated.date(),
            ]))

    # -- excluded titles (Yard Jockey) -------------------------------------------
    def excluded_people(self) -> dict[int, tuple[str, str]]:
        """id -> (name, source) for everyone whose HR title / sub-dept is never eligible."""
        out: dict[int, tuple[str, str]] = {}
        for eid, rec in self.term.items():
            if rec.is_excluded:
                out[eid] = (rec.display_name, f"HR term report sub-dept '{rec.sub_department}'")
        for eid, rec in self.roster.items():
            if rec.is_excluded:
                out[eid] = (rec.name, f"HR roster title '{rec.title}'")
        return out

    def flag_yard_jockeys(self) -> None:
        """Yard Jockeys (and any excluded title) must not be on a bonus sheet. Rows found on
        an active tab are highlighted grey and listed for removal; people not on any sheet
        are report-only - they are never added."""
        for eid, (name, source) in sorted(self.excluded_people().items()):
            locations = [(t, r) for t in self.all_tabs() for r in t.data_rows() if t.employee_id(r) == eid]
            active = [(t, r) for t, r in locations if t.name in ACTIVE_TABS]
            for tab, row in active:
                tab.highlight(row, FILL_EXCLUDED)
            if active:
                where = "; ".join(f"{t.branch}/{t.name} row {r}" for t, r in active)
                note = "On an active bonus tab - not eligible; remove from sheet"
            elif locations:
                where = "; ".join(f"{t.branch}/{t.name} row {r}" for t, r in locations)
                note = "Only on Terminated tab - no action"
            else:
                where, note = "Not on any sheet", "Correct - never add"
            branch = active[0][0].branch if active else ""
            self.report.append(ReportRow("Yard_Jockeys", [branch, eid, name, source, where, note],
                                         FILL_EXCLUDED if active else None))

    # -- step 3: duplicates ----------------------------------------------------
    def flag_duplicates(self) -> None:
        where: dict[int, list[tuple[Tab, int]]] = defaultdict(list)
        for tab in self.all_tabs():
            for row in tab.data_rows():
                eid = tab.employee_id(row)
                if eid is not None:
                    where[eid].append((tab, row))
        for eid, locs in where.items():
            active = [(t, r) for t, r in locs if t.name in ACTIVE_TABS]
            if not active:
                continue
            issues: list[str] = []
            names = {normalized_name(t.value(r, "NAME")) for t, r in locs if name_tokens(t.value(r, "NAME"))}
            if len(names) > 1 and not all(same_person(a, b) for a in names for b in names):
                issues.append(f"ID COLLISION: same ID used for different names ({' / '.join(sorted(names))})")
            by_tab: dict[tuple[str, str], int] = defaultdict(int)
            for t, _ in locs:
                by_tab[(t.branch, t.name)] += 1
            for (b, n), count in by_tab.items():
                if count > 1 and n in ACTIVE_TABS:
                    issues.append(f"{b}: appears {count}x on {n}")
            for b in {t.branch for t, _ in active}:
                tabs_here = {t.name for t, _ in locs if t.branch == b}
                if ACTIVE_TABS[0] in tabs_here and ACTIVE_TABS[1] in tabs_here:
                    issues.append(f"{b}: on both Eligible and Ineligible")
                if TERMINATED_TAB in tabs_here and tabs_here & set(ACTIVE_TABS):
                    issues.append(f"{b}: on an active tab AND the Terminated tab (rehire or stale?)")
            if len({t.branch for t, _ in active}) > 1:
                issues.append("Cross-branch: " + ", ".join(sorted(f"{t.branch}/{t.name}" for t, _ in active)))
            if not issues:
                continue
            for t, r in locs:
                if t.name in ACTIVE_TABS or any("Terminated tab" in i for i in issues):
                    t.highlight(r, FILL_DUPLICATE)
            name = active[0][0].value(active[0][1], "NAME")
            self.report.append(ReportRow("Duplicates", [
                eid, name, "; ".join(issues),
                ", ".join(f"{t.branch}/{t.name} row {r}" for t, r in locs),
            ]))

    def flag_near_duplicate_names(self) -> None:
        """Same branch, active tabs, different (or non-numeric) IDs, names nearly identical."""
        for branch, (_, tabs, _) in self.branches.items():
            people: list[tuple[str, Tab, int, object]] = []
            for tab_name in ACTIVE_TABS:
                tab = tabs[tab_name]
                for row in tab.data_rows():
                    name = re.sub(r"[^A-Z ]", "", str(tab.value(row, "NAME") or "").upper().replace(",", " "))
                    people.append((re.sub(r"\s+", " ", name).strip(), tab, row, tab.value(row, "ID")))
            seen: set[tuple[int, int]] = set()
            for i, (na, ta, ra, ida) in enumerate(people):
                for j in range(i + 1, len(people)):
                    nb, tb, rb, idb = people[j]
                    if not na or not nb or na[0] != nb[0] or (i, j) in seen:
                        continue
                    if ida == idb and isinstance(ida, int):
                        continue  # true duplicate ID - already flagged by flag_duplicates
                    ratio = difflib.SequenceMatcher(None, na, nb).ratio()
                    if ratio < NAME_SIMILARITY_MIN:
                        continue
                    seen.add((i, j))
                    both_numeric = isinstance(ida, int) and isinstance(idb, int)
                    if na == nb and both_numeric:
                        # Same name, two real employee numbers = two different people. Info only.
                        self.report.append(ReportRow("Namesakes", [
                            branch, ida, idb, ta.value(ra, "NAME"), f"{ta.name} row {ra}", f"{tb.name} row {rb}",
                            "Two employees share this name - always use the ID to tell them apart",
                        ]))
                        continue
                    ta.highlight(ra, FILL_DUPLICATE)
                    tb.highlight(rb, FILL_DUPLICATE)
                    why = ("spelling variant, one row has no numeric ID" if not both_numeric
                           else "names nearly identical with different IDs - same person mis-keyed, or two people?")
                    self.report.append(ReportRow("Duplicates", [
                        f"{ida} / {idb}", f"{ta.value(ra, 'NAME')} / {tb.value(rb, 'NAME')}",
                        f"{branch}: possible same driver - {why}",
                        f"{branch}/{ta.name} row {ra}, {branch}/{tb.name} row {rb}",
                    ]))

    # -- step 4: bonus dates ----------------------------------------------------
    def fill_bonus_dates(self) -> None:
        for branch, (_, tabs, _) in self.branches.items():
            tab = tabs[ACTIVE_TABS[1]]  # Ineligible
            date_col = tab.col("ELIGIBLE FOR BONUS")
            if not date_col:
                continue
            for row in tab.data_rows():
                existing = tab.value(row, "ELIGIBLE FOR BONUS")
                reason = tab.value(row, "REASON")
                records = [tab.ws.cell(row=row, column=c).value for c in tab.record_cols]
                incident = latest_incident(records)
                name, eid = tab.value(row, "NAME"), tab.employee_id(row)
                if existing not in (None, ""):
                    if isinstance(existing, datetime) and incident:
                        computed = bonus_payout_date(*incident)
                        future_typo = incident[0] > datetime.now()
                        if computed.date() != existing.date() or future_typo:
                            self.report.append(ReportRow("Date_Check_Info", [
                                branch, eid, name, reason, incident[0].date(), incident[1],
                                existing.date(), computed.date(),
                                "Incident date is in the future - likely typo" if future_typo else "",
                            ]))
                    continue
                if any(k in str(reason or "").upper() for k in TEMP_KEYWORDS):
                    self.report.append(ReportRow("Dates_Left_Blank", [branch, eid, name, reason, "Temp / staffing-agency driver - never eligible, no date"]))
                    continue
                if looks_like_leave(reason, records):
                    self.report.append(ReportRow("Dates_Left_Blank", [branch, eid, name, reason, "Workers Comp / LOA type row"]))
                    continue
                if not incident:
                    self.report.append(ReportRow("Dates_Left_Blank", [branch, eid, name, reason, "No incident with a bonus count found in DRIVER RECORD"]))
                    continue
                computed = bonus_payout_date(*incident)
                cell = tab.ws.cell(row=row, column=date_col, value=computed)
                cell.number_format = DATE_FORMAT_EXCEL
                tab.highlight(row, FILL_DATE_FILLED)
                self.report.append(ReportRow("Dates_Filled", [
                    branch, eid, name, reason, incident[0].date(), incident[1], computed.date(),
                ]))

    # -- ELIG normalisation: Y on Eligible, N everywhere else -----------------------
    def normalize_elig(self) -> None:
        """Jeremy's rule: the ELIG column is Y on the Eligible tab and N on Ineligible and
        Terminated, for every row. The old NH / WC codes are replaced too (REASON holds
        that detail). Changed rows are listed, not highlighted - this is housekeeping."""
        for tab in self.all_tabs():
            col = tab.col("ELIG")
            if not col:
                continue
            wanted = ELIG_YES if tab.name == ACTIVE_TABS[0] else ELIG_NO
            changed = 0
            for row in tab.data_rows():
                current = tab.ws.cell(row=row, column=col).value
                if str(current or "").strip().upper() != wanted:
                    tab.ws.cell(row=row, column=col, value=wanted)
                    changed += 1
            if changed:
                self.report.append(ReportRow("ELIG_Normalized", [tab.branch, tab.name, wanted, changed]))

    # -- step 5: blank rows -----------------------------------------------------
    def remove_blank_rows(self) -> None:
        for tab in self.all_tabs():
            last = tab.last_data_row()
            blanks = [r for r in range(FIRST_DATA_ROW, last + 1) if tab.is_blank_row(r)]
            if blanks:
                delete_rows_bottom_up(tab, blanks)
                self.report.append(ReportRow("Blank_Rows_Removed", [tab.branch, tab.name, len(blanks)]))

    # -- output -----------------------------------------------------------------
    def save_branches(self, out_dir: Path) -> list[Path]:
        saved: list[Path] = []
        for branch, (wb, _, src) in self.branches.items():
            clean_name = re.sub(r"^[0-9a-f]{8}-", "", src.name)
            dest = out_dir / clean_name
            wb.save(dest)
            saved.append(dest)
        return saved

    def write_report(self, out_dir: Path) -> Path:
        wb = openpyxl.Workbook()
        summary = wb.active
        summary.title = "Summary"
        counts: dict[str, int] = defaultdict(int)
        for r in self.report:
            counts[r.sheet] += 1
        summary.append([f"Safety Bonus Reconciliation — {self.quarter_label}"])
        summary["A1"].font = Font(bold=True, size=13)
        summary.append(["Generated", datetime.now().strftime("%m/%d/%Y %I:%M %p")])
        summary.append([])
        summary.append(["Legend (in branch workbooks)"])
        for text, fill in (("Yellow = moved/added to Terminated tab", FILL_MOVED),
                           ("Orange = duplicate ID, needs your decision", FILL_DUPLICATE),
                           ("Green = ELIGIBLE FOR BONUS date computed by rule", FILL_DATE_FILLED),
                           ("Grey = excluded title (Yard Jockey) on an active tab - remove", FILL_EXCLUDED)):
            summary.append([text]); summary.cell(row=summary.max_row, column=1).fill = fill
        summary.append([])
        summary.append(["Section", "Rows"])
        for sheet, headers in REPORT_SHEETS.items():
            summary.append([sheet, counts.get(sheet, 0)])
        summary.append(["Terminated_Report (all HR terms)", len(self.term)])
        summary.column_dimensions["A"].width = 48

        for sheet, headers in REPORT_SHEETS.items():
            ws = wb.create_sheet(sheet)
            ws.append(headers)
            for c in ws[1]:
                c.font = Font(bold=True); c.fill = FILL_HEADER
            for r in (x for x in self.report if x.sheet == sheet):
                ws.append(r.values)
                if r.fill:
                    for c in ws[ws.max_row]:
                        c.fill = r.fill
            autosize(ws)

        ws = wb.create_sheet("Terminated_Report")
        ws.append(["Employee ID", "Name", "Sub Department", "Dept Code", "Date Terminated", "Branch", "Action Taken"])
        for c in ws[1]:
            c.font = Font(bold=True); c.fill = FILL_HEADER
        for eid, rec in sorted(self.term.items(), key=lambda kv: kv[1].date_terminated, reverse=True):
            branch, action = self.term_outcome.get(eid, ("UNKNOWN", "No action"))
            ws.append([eid, rec.display_name, rec.sub_department, rec.department_code,
                       rec.date_terminated.date(), branch, action])
            fill = FILL_UNKNOWN if branch == "UNKNOWN" else FILL_EXCLUDED if branch == "EXCLUDED" else None
            if fill:
                for c in ws[ws.max_row]:
                    c.fill = fill
        autosize(ws)
        dest = out_dir / f"{self.quarter_label}_Safety_Bonus_Reconciliation_Report.xlsx"
        wb.save(dest)
        return dest


REPORT_SHEETS: dict[str, list[str]] = {
    "Moved_To_Terminated": ["Branch", "Employee ID", "Name (sheet)", "Name (HR)", "Sub Department", "Date Terminated", "Removed From", "Action"],
    "Added_To_Terminated": ["Branch", "Employee ID", "Name (HR)", "Sub Department", "Date Terminated"],
    "Unknown_Branch": ["Employee ID", "Name (HR)", "Sub Department", "Dept Code", "Date Terminated"],
    "Yard_Jockeys": ["Branch", "Employee ID", "Name", "Source", "Where", "Note"],
    "Excluded_Cost_Centers": ["Branch", "Tab", "Employee ID", "Name", "Cost Center", "Note"],
    "Duplicates": ["Employee ID", "Name", "Issue", "Where (branch/tab row)"],
    "ID_Name_Mismatch": ["Branch", "Employee ID", "Name on sheet", "Name on HR report", "Tab / Row", "Note"],
    "Namesakes": ["Branch", "Employee ID A", "Employee ID B", "Name", "Row A", "Row B", "Note"],
    "Dates_Filled": ["Branch", "Employee ID", "Name", "Reason", "Latest Incident", "Bonuses Removed", "Eligible For Bonus (computed)"],
    "Dates_Left_Blank": ["Branch", "Employee ID", "Name", "Reason", "Why left blank"],
    "Date_Check_Info": ["Branch", "Employee ID", "Name", "Reason", "Latest Incident", "Bonuses Removed", "Date on Sheet", "Date by Rule", "Note"],
    "Blank_Rows_Removed": ["Branch", "Tab", "Blank rows removed"],
    "ELIG_Normalized": ["Branch", "Tab", "ELIG set to", "Rows changed"],
}


def autosize(ws: Worksheet) -> None:
    for col_cells in ws.columns:
        width = max(len(str(c.value)) if c.value is not None else 0 for c in col_cells)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max(10, width + 2), 70)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input-dir", required=True, type=Path, help="Folder containing the branch *_Safety_Bonus.xlsx files")
    parser.add_argument("--term-report", required=True, type=Path, help="HR EmployeeInformation-TerminatedDrivers*.xlsx")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--quarter-label", default="Quarter", help="e.g. Q3_2026 (used in report filename)")
    parser.add_argument("--active-drivers", type=Path, help="HR active-driver roster (xlsx) with a job-title column; Yard Jockeys are excluded from the sheets")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    term = load_term_report(args.term_report)
    roster = load_active_roster(args.active_drivers) if args.active_drivers else {}
    rec = Reconciler(term, args.quarter_label, roster)
    branch_files = sorted(p for p in args.input_dir.glob("*.xlsx") if branch_from_filename(p) and p.resolve() != args.term_report.resolve())
    if not branch_files:
        raise SystemExit("No branch workbooks found (expected names like BB_Q3_2026_Safety_Bonus.xlsx)")
    for path in branch_files:
        rec.add_branch(path)

    rec.remove_excluded_cost_centers()
    rec.process_terminations()
    rec.add_missing_terminations()
    rec.flag_yard_jockeys()
    rec.remove_blank_rows()
    rec.flag_duplicates()
    rec.flag_near_duplicate_names()
    rec.fill_bonus_dates()
    rec.normalize_elig()

    saved = rec.save_branches(args.output_dir)
    report = rec.write_report(args.output_dir)
    print(f"Term report drivers: {len(term)}")
    for sheet in REPORT_SHEETS:
        print(f"  {sheet}: {sum(1 for r in rec.report if r.sheet == sheet)}")
    print("Saved:")
    for p in [*saved, report]:
        print(f"  {p}")


if __name__ == "__main__":
    main()
