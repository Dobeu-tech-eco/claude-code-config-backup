#!/usr/bin/env python3
"""Reduce the full UKG employee export (~190 MB, 290 columns, contains SSN)
to only the columns the MV-104 needs, so the roster can be stored in the
claude.ai Project and searched quickly. SSN and pay data are never copied.

Usage:
  python3 slim-roster.py --source "EmployeeInformation-Full-EmployeeDetails_<ts>.csv" --out roster-slim.csv
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import sys
from pathlib import Path

csv.field_size_limit(10**9)

HELPER_PATH: Path = Path(__file__).resolve().parent / "lookup-employee.py"
spec = importlib.util.spec_from_file_location("lookup_employee", HELPER_PATH)
lookup_employee = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
spec.loader.exec_module(lookup_employee)  # type: ignore[union-attr]

BANNER_LINES: int = 4


def read_export_date(path: Path) -> str:
    """UKG prints 'Date & Time: MM/DD/YYYY hh:mma' on banner line 3."""
    with open(path, encoding=lookup_employee.ROSTER_ENCODING, errors="replace") as handle:
        for _ in range(BANNER_LINES):
            line = handle.readline()
            if "Date & Time" in line:
                return line.split(":", 1)[1].strip().strip('"')
    return dt.date.today().isoformat()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    columns = list(lookup_employee.MV104_COLUMNS)
    rows = lookup_employee.open_rows(args.source)
    exported: str = read_export_date(args.source)
    seen: set[str] = set()
    count: int = 0
    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([f"# UKG export date: {exported}"])
        writer.writerow(columns)
        for row in rows:
            employee_id: str = (row.get(lookup_employee.ID_COLUMN) or "").strip()
            if not employee_id or employee_id in seen:
                continue  # UKG repeats an employee once per training record; core fields are identical
            seen.add(employee_id)
            writer.writerow([(row.get(col) or "").strip() for col in columns])
            count += 1
    print(f"{count} unique employees -> {args.out} (UKG export date {exported})")
    if count == 0:
        sys.exit("No employees written — check the source file")


if __name__ == "__main__":
    main()
