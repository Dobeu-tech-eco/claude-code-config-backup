#!/usr/bin/env python3
"""Find one Baldor fleet unit in the Truck Info workbook by Unit number and
resolve its registrant (lessor) from references/lessor-registry.json.

Usage:
  python3 lookup-truck.py --workbook "<YYYY-M-D>-Truckinfo.xlsx" --unit 99916 [--out truck.json]
  python3 lookup-truck.py --workbook truckinfo.csv --unit 99916          (Project-doc text twin)

Searches every sheet (Current Units first, then Disposed/Disabled/Old) so a
unit that was retired after the crash still resolves; the sheet name is
reported so you can flag a non-current unit. Exits 2 when not found — ask the
user for a fresh Truck Info export rather than guessing.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import openpyxl

SKILL_ROOT: Path = Path(__file__).resolve().parent.parent
LESSOR_REGISTRY: Path = SKILL_ROOT / "references" / "lessor-registry.json"
SHEET_PRIORITY: tuple[str, ...] = ("Current Units", "Disabled Units", "Disposed Units from 2019 to now", "Old units from 2013 - 2018")
UNIT_HEADERS: tuple[str, ...] = ("Unit", "TRUCK")
NOT_FOUND_EXIT: int = 2


def cell_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def find_in_sheet(sheet: Any, unit: str) -> dict[str, str] | None:
    rows = sheet.iter_rows(values_only=True)
    header = [cell_text(c) for c in next(rows)]
    unit_idx = next((i for i, h in enumerate(header) if h in UNIT_HEADERS), None)
    if unit_idx is None:
        return None
    for row in rows:
        if cell_text(row[unit_idx]).upper() == unit.upper():
            return {h: cell_text(v) for h, v in zip(header, row) if h}
    return None


def find_in_csv(csv_path: Path, unit: str) -> tuple[str, dict[str, str]] | None:
    """CSV produced by truck-to-csv.py: optional '# ...' banner, then Sheet,Unit,... columns."""
    with open(csv_path, newline="", encoding="utf-8") as handle:
        first = handle.readline()
        if not first.startswith("#"):
            handle.seek(0)
        hits = [row for row in csv.DictReader(handle) if (row.get("Unit") or "").upper() == unit.upper()]
    hits.sort(key=lambda r: SHEET_PRIORITY.index(r["Sheet"]) if r["Sheet"] in SHEET_PRIORITY else len(SHEET_PRIORITY))
    if not hits:
        return None
    record = {k: v for k, v in hits[0].items() if k != "Sheet" and v}
    return hits[0]["Sheet"], record


def find_unit(workbook_path: Path, unit: str) -> tuple[str, dict[str, str]] | None:
    if workbook_path.suffix.lower() == ".csv":
        return find_in_csv(workbook_path, unit)
    book = openpyxl.load_workbook(workbook_path, read_only=True, data_only=True)
    names = [n for n in SHEET_PRIORITY if n in book.sheetnames] + [n for n in book.sheetnames if n not in SHEET_PRIORITY]
    for name in names:
        hit = find_in_sheet(book[name], unit)
        if hit:
            return name, hit
    return None


def resolve_lessor(vendor: str) -> dict[str, Any]:
    registry: dict[str, Any] = json.loads(LESSOR_REGISTRY.read_text(encoding="utf-8"))
    entry = registry.get(vendor.upper().strip())
    if entry is None:
        return {"vendor": vendor, "registrant_known": False,
                "action": f"No cab card on file for lessor '{vendor}'. Ask the user for this unit's registration cab card."}
    return {"vendor": vendor, "registrant_known": True, **entry}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", required=True, type=Path)
    parser.add_argument("--unit", required=True)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    found = find_unit(args.workbook, args.unit.strip())
    if found is None:
        print(json.dumps({"found": False, "unit": args.unit,
                          "action": "Unit not in Truck Info export. Ask the user for a fresh export; do not guess."}))
        sys.exit(NOT_FOUND_EXIT)
    sheet, record = found
    vendor = record.get("Vendor") or record.get("VENDOR") or ""
    payload = {"found": True, "sheet": sheet, "is_current_unit": sheet == "Current Units",
               "unit": record, "registrant": resolve_lessor(vendor)}
    text = json.dumps(payload, indent=1)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
