#!/usr/bin/env python3
"""Step 3 of the quarterly safety-bonus process: produce the reviewable
_v1 / _v2 branch workbooks.

  _v1 = reconciled workbook (step 1) + an "ACTION ITEMS" tab listing every
        highlighted / deliberation item for that branch from step 1 (duplicates,
        blank dates, typo dates) and step 2 (incident anomalies). Nothing else
        is changed. Unknown-branch terms are NOT listed here; they live only in
        the reconciliation report (Unknown_Branch / red Terminated_Report rows).
  _v2 = _v1 with the step-2 edits applied:
        * CRITICAL (driver still Eligible)  -> row moved to Ineligible, accident
          entry added, ELIG=N, REASON=Accident, bonus date computed
        * MISSING ENTRY                     -> accident entry added on the
          Ineligible row (+ bonus date if blank and not temp/leave)
        * DATE MISMATCH                     -> entry date aligned to the Origami
          loss date (original text kept in ACTION ITEMS)
        Edited rows are highlighted blue. ACTION ITEMS shows "Applied in v2 -
        verify" for those and "Needs decision" for everything else.

Usage:
  python3 build_action_items.py --reconciled-dir <step-1 output dir> \
      --reconciliation-report <..._Reconciliation_Report.xlsx> \
      --incident-review <..._Incidents_vs_Bonus_Review.xlsx> \
      --output-dir <dir>
"""
from __future__ import annotations

import argparse
import re
import sys
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.worksheet import Worksheet

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reconcile_safety_bonus import (  # noqa: E402
    DATE_FORMAT_EXCEL, LEAVE_KEYWORDS, TEMP_KEYWORDS, Tab, TERMINATED_TAB,
    bonus_payout_date, branch_from_filename, delete_rows_bottom_up, append_row,
)

warnings.filterwarnings("ignore", category=UserWarning)

ACTION_TAB: str = "ACTION ITEMS"
DEFAULT_BONUSES_REMOVED: int = 2          # (x2) is the standard on every branch sheet
FILL_EDITED = PatternFill("solid", fgColor="BDD7EE")   # blue: changed in v2
FILL_PROMOTED = PatternFill("solid", fgColor="E4DFEC") # purple: promoted Ineligible -> Eligible
FILL_HEADER = PatternFill("solid", fgColor="D9D9D9")
PRIORITY_FILL: dict[str, PatternFill] = {
    "1-CRITICAL": PatternFill("solid", fgColor="FF9999"),
    "2-HIGH": PatternFill("solid", fgColor="FFC000"),
    "3-REVIEW": PatternFill("solid", fgColor="FFFF00"),
    "4-VERIFY": PatternFill("solid", fgColor="E2EFDA"),
}
ACTION_HEADERS: list[str] = [
    "Priority", "Source", "Issue Type", "Employee ID", "Name", "Tab / Row", "Detail",
    "Suggested Action", "Status", "Your Decision / Notes",
]
FOUND_ON_RE = re.compile(r"(\w+)/(Eligible|Ineligible|Terminated) row (\d+)")
RECORD_DATE_RE = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")


@dataclass
class ActionItem:
    priority: str
    source: str
    issue: str
    employee_id: object
    name: object
    where: str
    detail: str
    action: str
    status: str = "Needs decision"


@dataclass
class IncidentFinding:
    finding: str
    employee_id: object
    name: str
    loss_date: datetime | None
    tier: str
    locations: list[tuple[str, str, int]] = field(default_factory=list)  # (branch, tab, row)
    entry: str = ""
    occurrence: str = ""


# ----------------------------------------------------------------------------
# Readers for the two report workbooks
# ----------------------------------------------------------------------------
def read_sheet(path: Path, sheet: str) -> list[dict[str, object]]:
    wb = openpyxl.load_workbook(path, read_only=True)
    if sheet not in wb.sheetnames:
        return []
    rows = list(wb[sheet].iter_rows(values_only=True))
    header = [str(h) for h in rows[0]]
    return [dict(zip(header, r)) for r in rows[1:] if any(v not in (None, "") for v in r)]


def step1_items(report: Path) -> dict[str, list[ActionItem]]:
    items: dict[str, list[ActionItem]] = defaultdict(list)
    for r in read_sheet(report, "Duplicates"):
        branches = {m.group(1) for m in FOUND_ON_RE.finditer(str(r["Where (branch/tab row)"]))}
        for b in branches:
            items[b].append(ActionItem("2-HIGH", "Step 1 - Reconciliation", "Duplicate ID", r["Employee ID"], r["Name"],
                                       str(r["Where (branch/tab row)"]), str(r["Issue"]),
                                       "Decide which row is correct; delete or correct the other (orange rows)."))
    for r in read_sheet(report, "ID_Name_Mismatch"):
        items[str(r["Branch"])].append(ActionItem("1-CRITICAL", "Step 1 - Reconciliation", "Termed ID on sheet but name differs", r["Employee ID"],
                                                 f"{r['Name on sheet']} (HR: {r['Name on HR report']})", str(r["Tab / Row"]), str(r["Note"]),
                                                 "Verify the employee number; if same person, move to Terminated manually."))
    for r in read_sheet(report, "Namesakes"):
        items[str(r["Branch"])].append(ActionItem("4-VERIFY", "Step 1 - Reconciliation", "Two employees share a name", f"{r['Employee ID A']} / {r['Employee ID B']}",
                                                 r["Name"], f"{r['Row A']}; {r['Row B']}", str(r["Note"]), "No action unless an incident was logged against the wrong one."))
    for r in read_sheet(report, "Yard_Jockeys"):
        # Only rows found on an active tab have a branch; "not on any sheet" rows are
        # report-only (never added, never an action item).
        if r["Branch"]:
            items[str(r["Branch"])].append(ActionItem("2-HIGH", "Step 1 - Reconciliation", "Yard Jockey on bonus sheet (never eligible)",
                                                     r["Employee ID"], r["Name"], str(r["Where"]), str(r["Source"]),
                                                     "Remove from the bonus sheet; Yard Jockeys are not eligible and should not be listed."))
    # Unknown_Branch rows are intentionally NOT turned into branch action items.
    # A termed driver whose branch cannot be reconciled is reported only in the
    # reconciliation report (Unknown_Branch sheet + red rows on Terminated_Report).
    for r in read_sheet(report, "Added_To_Terminated"):
        items[str(r["Branch"])].append(ActionItem("4-VERIFY", "Step 1 - Reconciliation", "Added to Terminated from HR report", r["Employee ID"], r["Name (HR)"],
                                                 "Terminated (yellow, bottom)", f"{r['Sub Department']}, termed {r['Date Terminated']}",
                                                 "Confirm driver belonged to this branch; add DOH/history if known."))
    for r in read_sheet(report, "Dates_Left_Blank"):
        items[str(r["Branch"])].append(ActionItem("4-VERIFY", "Step 1 - Reconciliation", "Bonus date left blank", r["Employee ID"], r["Name"],
                                                 "Ineligible", f"REASON={r['Reason']}: {r['Why left blank']}",
                                                 "Confirm blank is correct (WC/LOA/temp never get a date)."))
    for r in read_sheet(report, "Date_Check_Info"):
        if r.get("Note"):
            items[str(r["Branch"])].append(ActionItem("3-REVIEW", "Step 1 - Reconciliation", "Incident date typo", r["Employee ID"], r["Name"],
                                                     "Ineligible", f"Latest incident {r['Latest Incident']} is in the future", "Fix the year on the DRIVER RECORD entry."))
    for r in read_sheet(report, "Dates_Filled"):
        items[str(r["Branch"])].append(ActionItem("4-VERIFY", "Step 1 - Reconciliation", "Bonus date computed", r["Employee ID"], r["Name"],
                                                 "Ineligible (green)", f"{r['Latest Incident']} x{r['Bonuses Removed']} -> {r['Eligible For Bonus (computed)']}",
                                                 "Verify computed date."))
    return items


def step2_findings(review: Path) -> list[IncidentFinding]:
    out: list[IncidentFinding] = []
    for r in read_sheet(review, "Anomalies"):
        f = IncidentFinding(str(r["Finding"]), r["Employee #"], str(r["Employee"]),
                            r["Loss Date"] if isinstance(r["Loss Date"], datetime) else None,
                            str(r["Tier"] or ""), entry=str(r["Nearest Record Entry"] or ""), occurrence=str(r["Occurrence #"]))
        f.locations = [(m.group(1), m.group(2), int(m.group(3))) for m in FOUND_ON_RE.finditer(str(r["Found On"] or ""))]
        out.append(f)
    return out


# ----------------------------------------------------------------------------
# v2 edits
# ----------------------------------------------------------------------------
def entry_text(loss: datetime, count: int = DEFAULT_BONUSES_REMOVED) -> str:
    return f"{loss.month}/{loss.day}/{loss.strftime('%y')} Accident (x{count})"


def next_record_col(tab: Tab, row: int) -> int | None:
    return next((c for c in tab.record_cols if tab.ws.cell(row=row, column=c).value in (None, "")), None)


def is_temp_or_leave(tab: Tab, row: int) -> bool:
    """Temp agency drivers sometimes carry 'Vertex' in the ID cell instead of a number."""
    text = f"{tab.value(row, 'REASON') or ''} {tab.value(row, 'ID') or ''}".upper()
    return any(k in text for k in TEMP_KEYWORDS) or any(k in text for k in LEAVE_KEYWORDS)


def has_entry_for(tab: Tab, row: int, loss: datetime) -> bool:
    stamp = f"{loss.month}/{loss.day}/{loss.strftime('%y')}"
    return any(stamp in str(tab.ws.cell(row=row, column=c).value or "") for c in tab.record_cols)


def mark_ineligible(tab: Tab, row: int, loss: datetime) -> str:
    """Add the accident entry and set ELIG / REASON / bonus date on an Ineligible row."""
    notes: list[str] = []
    col = next_record_col(tab, row)
    if has_entry_for(tab, row, loss):
        notes.append("entry already present")
    elif col is None:
        notes.append("NO EMPTY DRIVER RECORD COLUMN - add entry manually")
    else:
        tab.ws.cell(row=row, column=col, value=entry_text(loss))
        notes.append(f"added '{entry_text(loss)}'")
    if tab.col("ELIG"):
        tab.ws.cell(row=row, column=tab.col("ELIG"), value="N")
    reason = tab.value(row, "REASON")
    if reason in (None, "") or str(reason).strip().upper() == "NEW HIRE":
        if tab.col("REASON"):
            tab.ws.cell(row=row, column=tab.col("REASON"), value="Accident")
    if is_temp_or_leave(tab, row):
        notes.append("temp/leave - no bonus date")
    elif tab.col("ELIGIBLE FOR BONUS"):
        cell = tab.ws.cell(row=row, column=tab.col("ELIGIBLE FOR BONUS"), value=bonus_payout_date(loss, DEFAULT_BONUSES_REMOVED))
        cell.number_format = DATE_FORMAT_EXCEL
        notes.append(f"ELIGIBLE FOR BONUS -> {cell.value.date()}")
    tab.highlight(row, FILL_EDITED)
    return "; ".join(notes)


def align_entry_date(tab: Tab, row: int, old_entry: str, loss: datetime) -> str:
    for col in tab.record_cols:
        val = tab.ws.cell(row=row, column=col).value
        if isinstance(val, str) and val.strip() == old_entry.strip():
            new_val = RECORD_DATE_RE.sub(f"{loss.month}/{loss.day}/{loss.strftime('%y')}", val, count=1)
            tab.ws.cell(row=row, column=col, value=new_val)
            tab.highlight(row, FILL_EDITED)
            return f"'{val}' -> '{new_val}'"
        if isinstance(val, datetime) and str(val) == old_entry.strip():
            tab.ws.cell(row=row, column=col, value=entry_text(loss))
            tab.highlight(row, FILL_EDITED)
            return f"'{val.date()}' -> '{entry_text(loss)}'"
    return "entry not found - edit manually"


def apply_step2(branch: str, tabs: dict[str, Tab], findings: list[IncidentFinding]) -> list[ActionItem]:
    items: list[ActionItem] = []
    eligible_rows_to_delete: list[int] = []
    for f in findings:
        mine = [(b, t, r) for b, t, r in f.locations if b == branch]
        if not mine:
            # Incidents with no driver on this branch (NO DRIVER, NOT FOUND, unmatched
            # REVIEW, AMBIGUOUS with no sheet rows) stay in the incident review
            # report only; they are never branch action items.
            continue
        where = "; ".join(f"{t} row {r}" for _, t, r in mine)
        base = dict(employee_id=f.employee_id, name=f.name, where=where)
        detail = f"Origami #{f.occurrence}, loss {f.loss_date.date() if f.loss_date else '?'}, tier {f.tier}"
        if f.finding.startswith("CRITICAL") and f.loss_date:
            elig = [r for _, t, r in mine if t == "Eligible"]
            inel = [r for _, t, r in mine if t == "Ineligible"]
            if inel:
                note = mark_ineligible(tabs["Ineligible"], inel[0], f.loss_date)
                eligible_rows_to_delete += elig
                items.append(ActionItem("1-CRITICAL", "Step 2 - Incidents", "Was on Eligible with preventable accident", **base,
                                        detail=detail, action=f"Eligible copy deleted; Ineligible row updated ({note}).", status="Applied in v2 - verify"))
            elif elig:
                src = tabs["Eligible"]
                values = src.row_values(elig[0])
                values["REASON"] = "Accident"
                new_row = append_row(tabs["Ineligible"], values, "")
                if tabs["Ineligible"].col("STATUS"):
                    tabs["Ineligible"].ws.cell(row=new_row, column=tabs["Ineligible"].col("STATUS"), value=values.get("STATUS"))
                note = mark_ineligible(tabs["Ineligible"], new_row, f.loss_date)
                eligible_rows_to_delete += elig
                items.append(ActionItem("1-CRITICAL", "Step 2 - Incidents", "Was on Eligible with preventable accident", **base,
                                        detail=detail, action=f"Moved to Ineligible row {new_row} ({note}).", status="Applied in v2 - verify"))
        elif f.finding.startswith("MISSING") and f.loss_date:
            inel = [r for _, t, r in mine if t == "Ineligible"]
            if inel:
                note = mark_ineligible(tabs["Ineligible"], inel[0], f.loss_date)
                items.append(ActionItem("2-HIGH", "Step 2 - Incidents", "Accident not on bonus sheet", **base,
                                        detail=detail, action=f"Ineligible row updated ({note}).", status="Applied in v2 - verify"))
        elif f.finding.startswith("DATE MISMATCH") and f.loss_date:
            inel = [r for _, t, r in mine if t == "Ineligible"]
            if inel:
                note = align_entry_date(tabs["Ineligible"], inel[0], f.entry, f.loss_date)
                items.append(ActionItem("2-HIGH", "Step 2 - Incidents", "Entry date differs from Origami loss date", **base,
                                        detail=f"{detail}; sheet had '{f.entry}'", action=f"Date aligned to Origami ({note}).", status="Applied in v2 - verify"))
        elif f.finding.startswith("REVIEW"):
            items.append(ActionItem("3-REVIEW", "Step 2 - Incidents", f.finding, **base, detail=detail,
                                    action="Decide preventable / discipline in Origami, then add entry to Ineligible if Yes."))
        elif f.finding.startswith("AMBIGUOUS"):
            items.append(ActionItem("1-CRITICAL", "Step 2 - Incidents", "Name matches several employees; no employee # in Origami", **base, detail=detail,
                                    action="Get the employee number from Origami/HR, then add the accident to the right driver. Nothing was edited."))
        elif f.finding.startswith("ID COLLISION"):
            items.append(ActionItem("1-CRITICAL", "Step 2 - Incidents", "Same employee ID used for two different names", **base, detail=detail,
                                    action="Verify the employee number in Origami and on the sheet; nothing was edited."))
        elif f.finding.startswith("NOT FOUND"):
            items.append(ActionItem("2-HIGH", "Step 2 - Incidents", "Driver not in any bonus workbook", **base, detail=detail,
                                    action="Add driver to the correct branch workbook (Ineligible)."))
    delete_rows_bottom_up(tabs["Eligible"], eligible_rows_to_delete)
    return items


def step2_items_v1(branch: str, findings: list[IncidentFinding]) -> list[ActionItem]:
    """Same findings, but phrased as open decisions (nothing applied yet)."""
    prio = {"CRITICAL": "1-CRITICAL", "ID": "1-CRITICAL", "AMBIGUOUS": "1-CRITICAL", "MISSING": "2-HIGH", "DATE": "2-HIGH", "REVIEW": "3-REVIEW", "NOT": "2-HIGH"}
    action = {
        "CRITICAL": "Move to Ineligible, add accident entry (x2 default), compute bonus date.",
        "MISSING": "Add accident entry to Ineligible row (x2 default).",
        "DATE": "Confirm which date is correct; Origami loss date is the system of record.",
        "REVIEW": "Decide preventable / discipline in Origami, then add entry to Ineligible if Yes.",
        "NOT": "Add driver to the correct branch workbook (Ineligible).",
        "ID": "Verify the employee number in Origami and on the sheet before any edit.",
        "AMBIGUOUS": "Get the employee number from Origami/HR; several drivers share this name.",
    }
    items: list[ActionItem] = []
    for f in findings:
        mine = [(b, t, r) for b, t, r in f.locations if b == branch]
        key = f.finding.split(" ")[0]
        if not mine:
            continue  # unmatched incidents live only in the incident review report
        detail = f"Origami #{f.occurrence}, loss {f.loss_date.date() if f.loss_date else '?'}, tier {f.tier}" + (f"; sheet entry '{f.entry}'" if f.entry else "")
        items.append(ActionItem(prio.get(key, "3-REVIEW"), "Step 2 - Incidents", f.finding, f.employee_id, f.name,
                                "; ".join(f"{t} row {r}" for _, t, r in mine), detail, action.get(key, "Review.")))
    return items


# ----------------------------------------------------------------------------
# Step 4: promote drivers whose bonus date has arrived
# ----------------------------------------------------------------------------
HOLD_LEAVE: str = "leave/temp"
HOLD_STALE: str = "stale date"
HOLD_DUP: str = "duplicate ID"
HOLD_TEXT: dict[str, str] = {
    HOLD_LEAVE: "Bonus date reached but reason is WC/LOA/temp",
    HOLD_STALE: "Bonus date reached but an incident is dated inside the quarter (date is stale)",
    HOLD_DUP: "Bonus date reached but the ID appears on more than one row",
}
HOLD_ACTION: dict[str, str] = {
    HOLD_LEAVE: "Confirm the driver is back at work (temps are never eligible), then move to Eligible manually.",
    HOLD_STALE: "Recompute the bonus date from the latest incident; do not promote.",
    HOLD_DUP: "Resolve the duplicate rows first, then promote the surviving row if its date is right.",
}


def quarter_incident_dates(tab: Tab, row: int, start: datetime, end: datetime) -> list[datetime]:
    dates: list[datetime] = []
    for col in tab.record_cols:
        val = tab.ws.cell(row=row, column=col).value
        for m in RECORD_DATE_RE.finditer(str(val or "")):
            try:
                d = datetime.strptime(m.group(0).replace("-", "/"), "%m/%d/%y" if len(m.group(0).split("/")[-1]) == 2 else "%m/%d/%Y")
            except ValueError:
                continue
            if start <= d <= end:
                dates.append(d)
        if isinstance(val, datetime) and start <= val <= end:
            dates.append(val)
    return dates


def duplicate_ids(tabs: dict[str, Tab]) -> set[int]:
    seen: dict[int, int] = {}
    for name in ("Eligible", "Ineligible"):
        for row in tabs[name].data_rows():
            eid = tabs[name].employee_id(row)
            if eid is not None:
                seen[eid] = seen.get(eid, 0) + 1
    return {eid for eid, n in seen.items() if n > 1}


def promotion_candidates(tabs: dict[str, Tab], payout: datetime, start: datetime, end: datetime) -> list[tuple[int, str | None]]:
    """Ineligible rows dated exactly the payout date, each with None (promote) or a hold reason."""
    tab = tabs["Ineligible"]
    dups = duplicate_ids(tabs)
    out: list[tuple[int, str | None]] = []
    for row in tab.data_rows():
        date = tab.value(row, "ELIGIBLE FOR BONUS")
        if not (isinstance(date, datetime) and date.date() == payout.date()):
            continue
        if is_temp_or_leave(tab, row):
            out.append((row, HOLD_LEAVE))
        elif quarter_incident_dates(tab, row, start, end):
            out.append((row, HOLD_STALE))
        elif tab.employee_id(row) in dups:
            out.append((row, HOLD_DUP))
        else:
            out.append((row, None))
    return out


def promote_to_eligible(tabs: dict[str, Tab], payout: datetime, start: datetime, end: datetime) -> list[ActionItem]:
    items: list[ActionItem] = []
    src, dst = tabs["Ineligible"], tabs["Eligible"]
    to_delete: list[int] = []
    for row, hold in promotion_candidates(tabs, payout, start, end):
        eid, name, reason = src.employee_id(row), src.value(row, "NAME"), src.value(row, "REASON")
        if hold:
            items.append(ActionItem("2-HIGH", "Step 4 - Promotion", HOLD_TEXT[hold], eid, name,
                                    f"Ineligible row {row}", f"ELIGIBLE FOR BONUS = {payout.date()}, REASON = {reason}", HOLD_ACTION[hold]))
            continue
        values = src.row_values(row)
        new_row = append_row(dst, values, "")
        if dst.col("STATUS"):
            dst.ws.cell(row=new_row, column=dst.col("STATUS"), value=values.get("STATUS"))
        if dst.col("ELIG"):
            dst.ws.cell(row=new_row, column=dst.col("ELIG"), value="Y")
        dst.highlight(new_row, FILL_PROMOTED)
        to_delete.append(row)
        items.append(ActionItem("4-VERIFY", "Step 4 - Promotion", "Promoted Ineligible -> Eligible", eid, name,
                                f"Eligible row {new_row} (was Ineligible row {row})", f"ELIGIBLE FOR BONUS = {payout.date()}, REASON was {reason}",
                                "Verify; ELIG set to Y, row highlighted purple.", status="Applied in v2 - verify"))
    delete_rows_bottom_up(src, to_delete)
    return items


def promotion_items_v1(tabs: dict[str, Tab], payout: datetime, start: datetime, end: datetime) -> list[ActionItem]:
    src = tabs["Ineligible"]
    items: list[ActionItem] = []
    for row, hold in promotion_candidates(tabs, payout, start, end):
        items.append(ActionItem("2-HIGH" if hold else "3-REVIEW", "Step 4 - Promotion",
                                HOLD_TEXT[hold] if hold else "Bonus date reached",
                                src.employee_id(row), src.value(row, "NAME"), f"Ineligible row {row}",
                                f"ELIGIBLE FOR BONUS = {payout.date()}, REASON = {src.value(row, 'REASON')}",
                                HOLD_ACTION[hold] if hold else "Move to Eligible (done automatically in v2)."))
    return items


# ----------------------------------------------------------------------------
# ACTION ITEMS tab
# ----------------------------------------------------------------------------
def write_action_tab(wb: openpyxl.Workbook, items: list[ActionItem], version: str) -> None:
    if ACTION_TAB in wb.sheetnames:
        del wb[ACTION_TAB]
    ws = wb.create_sheet(ACTION_TAB, 0)
    ws.append([f"ACTION ITEMS - {version} - generated {datetime.now().strftime('%m/%d/%Y %I:%M %p')}"])
    ws["A1"].font = Font(bold=True, size=12)
    ws.append(["Colors in other tabs: yellow = moved/added to Terminated, orange = duplicate, green = date computed, blue = edited in v2, purple = promoted to Eligible in v2."])
    ws.append([])
    ws.append(ACTION_HEADERS)
    for c in ws[4]:
        c.font = Font(bold=True)
        c.fill = FILL_HEADER
    for it in sorted(items, key=lambda i: (i.priority, i.source, str(i.name))):
        ws.append([it.priority, it.source, it.issue, it.employee_id, it.name, it.where, it.detail, it.action, it.status, ""])
        ws.cell(row=ws.max_row, column=1).fill = PRIORITY_FILL[it.priority]
    widths = [12, 24, 36, 12, 30, 28, 60, 60, 22, 30]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=5):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A5"
    ws.auto_filter.ref = f"A4:{openpyxl.utils.get_column_letter(len(ACTION_HEADERS))}{max(ws.max_row, 5)}"


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
def versioned_name(path: Path, suffix: str) -> str:
    return re.sub(r"(_v\d+)?\.xlsx$", f"{suffix}.xlsx", path.name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reconciled-dir", required=True, type=Path)
    parser.add_argument("--reconciliation-report", required=True, type=Path)
    parser.add_argument("--incident-review", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--start", required=True, type=lambda v: datetime.strptime(v, "%Y-%m-%d"), help="Quarter start, e.g. 2026-07-01")
    parser.add_argument("--end", required=True, type=lambda v: datetime.strptime(v, "%Y-%m-%d"), help="Quarter end, e.g. 2026-09-30")
    parser.add_argument("--payout-date", required=True, type=lambda v: datetime.strptime(v, "%Y-%m-%d"),
                        help="First day of the quarter after the one being closed, e.g. 2026-10-01; Ineligible rows dated this are promoted to Eligible in v2")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    s1 = step1_items(args.reconciliation_report)
    findings = step2_findings(args.incident_review)
    for path in sorted(args.reconciled_dir.glob("*Safety_Bonus*.xlsx")):
        branch = branch_from_filename(path)
        if branch is None:
            continue
        # ---- v1
        wb = openpyxl.load_workbook(path)
        tabs_v1 = {n: Tab(branch, n, wb[n]) for n in ("Eligible", "Ineligible", TERMINATED_TAB)}
        v1_items = s1.get(branch, []) + step2_items_v1(branch, findings) + promotion_items_v1(tabs_v1, args.payout_date, args.start, args.end)
        write_action_tab(wb, v1_items, "v1 (no edits applied)")
        wb.save(args.output_dir / versioned_name(path, "_v1"))
        # ---- v2
        wb = openpyxl.load_workbook(path)
        tabs = {n: Tab(branch, n, wb[n]) for n in ("Eligible", "Ineligible", TERMINATED_TAB)}
        v2_items = s1.get(branch, []) + apply_step2(branch, tabs, findings) + promote_to_eligible(tabs, args.payout_date, args.start, args.end)
        write_action_tab(wb, v2_items, "v2 (incident edits + promotions applied)")
        wb.save(args.output_dir / versioned_name(path, "_v2"))
        applied = sum(1 for i in v2_items if i.status.startswith("Applied"))
        promoted = sum(1 for i in v2_items if i.issue.startswith("Promoted"))
        print(f"{branch}: v1 action items={len(v1_items)}  v2 applied={applied} (promoted {promoted}) open={len(v2_items) - applied}")


if __name__ == "__main__":
    main()
