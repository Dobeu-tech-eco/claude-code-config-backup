#!/usr/bin/env python3
"""Find one employee in the UKG roster export by Employee Id (never by name —
Baldor has drivers with identical names).

Usage:
  python3 lookup-employee.py --roster <ukg-export.csv or roster-slim.csv> --id 110828 [--out employee.json]

Works on either the full UKG "Employee Information: Full-EmployeeDetails"
export (4 banner lines + blank line before the header) or the slimmed roster
produced by slim-roster.py. Prints the MV-104-relevant columns as JSON and
exits 2 when the ID is not present — in that case ask the user for a fresh
UKG export; do not fall back to a name match.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

csv.field_size_limit(10**9)

ROSTER_ENCODING: str = "cp1252"
ID_COLUMN: str = "Employee Id"
NOT_FOUND_EXIT: int = 2
MV104_COLUMNS: tuple[str, ...] = (
    "Employee Id", "Last Name", "First Name", "Last, First Name", "Nickname",
    "Date Birthday", "Address 1", "Address 2", "Address 3", "City", "State", "Zip Code",
    "Full Cell Phone", "Full Home Phone", "Primary Email",
    "Employee Status", "Department", "Cost Centers(Location)", "Payroll Job Title",
    "Default Jobs (HR)", "Supervisor Employee Id", "Manager Employee Id", "Date Hired",
)


def open_rows(path: Path) -> csv.DictReader:
    handle = open(path, newline="", encoding=ROSTER_ENCODING, errors="replace")
    reader = csv.reader(handle)
    header: list[str] = []
    for row in reader:
        if ID_COLUMN in row:
            header = row
            break
    if not header:
        sys.exit(f"Header row with '{ID_COLUMN}' not found in {path}")
    return csv.DictReader(handle, fieldnames=header)


def find_employee(path: Path, employee_id: str) -> dict[str, str] | None:
    wanted: str = employee_id.strip()
    for row in open_rows(path):
        if (row.get(ID_COLUMN) or "").strip() == wanted:
            return {col: (row.get(col) or "").strip() for col in MV104_COLUMNS if col in row}
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roster", required=True, type=Path)
    parser.add_argument("--id", required=True, help="Employee Id exactly as shown on the Origami incident report")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    record = find_employee(args.roster, args.id)
    if record is None:
        print(json.dumps({"found": False, "employee_id": args.id,
                          "action": "Employee Id not in roster export. Ask the user for a fresh UKG export; do not match by name."}))
        sys.exit(NOT_FOUND_EXIT)
    payload = {"found": True, **record}
    text = json.dumps(payload, indent=1)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
