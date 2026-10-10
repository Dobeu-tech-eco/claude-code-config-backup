#!/usr/bin/env python3
"""Flatten the Truck Info workbook (all sheets) into one UTF-8 CSV so it can be
stored as a claude.ai Project doc (Project docs are text-only).

Usage:
  python3 truck-to-csv.py --workbook "2026-10-9-Truckinfo.xlsx" --out truckinfo.csv

Output columns: Sheet, Unit, then every header found on that sheet. Line 1 is
'# Truck Info export: <workbook file name>' so the export date stays visible.
lookup-truck.py reads this CSV the same way it reads the workbook.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Any

import openpyxl

UNIT_HEADERS: tuple[str, ...] = ("Unit", "TRUCK")


def cell_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def sheet_records(sheet: Any) -> list[dict[str, str]]:
    rows = sheet.iter_rows(values_only=True)
    header = [cell_text(c) for c in next(rows)]
    unit_idx = next((i for i, h in enumerate(header) if h in UNIT_HEADERS), None)
    if unit_idx is None:
        return []
    records: list[dict[str, str]] = []
    for row in rows:
        unit = cell_text(row[unit_idx]) if unit_idx < len(row) else ""
        if not unit:
            continue
        rec = {h: cell_text(v) for h, v in zip(header, row) if h}
        rec["Unit"] = unit
        records.append(rec)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    book = openpyxl.load_workbook(args.workbook, read_only=True, data_only=True)
    all_rows: list[dict[str, str]] = []
    for name in book.sheetnames:
        for rec in sheet_records(book[name]):
            all_rows.append({"Sheet": name, **rec})
    columns = ["Sheet", "Unit"] + sorted({k for r in all_rows for k in r} - {"Sheet", "Unit"})
    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        handle.write(f"# Truck Info export: {args.workbook.name}\n")
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"{len(all_rows)} unit rows from {len(book.sheetnames)} sheets -> {args.out}")


if __name__ == "__main__":
    main()
