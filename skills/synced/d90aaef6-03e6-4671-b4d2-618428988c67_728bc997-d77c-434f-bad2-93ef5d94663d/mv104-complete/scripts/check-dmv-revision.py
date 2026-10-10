#!/usr/bin/env python3
"""Rule #1 helper: compare the live NY DMV MV-104 against the revision this skill
was built on.

Usage:
  python3 check-dmv-revision.py --live /path/to/downloaded/mv104.pdf

The shell in most sessions cannot reach dmv.ny.gov, so download the live form
with the WebFetch/browser tool first (URL in references/official-rules.md),
or — if only WebFetch text is available — compare the revision string it
reports against `expected_revision` in references/official-rules.json by hand.
Exit 0 = same revision and same field set; exit 3 = CHANGED (update the
template, field map, and official-rules files, then tell the user before filling).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

SKILL_ROOT: Path = Path(__file__).resolve().parent.parent
RULES_PATH: Path = SKILL_ROOT / "references" / "official-rules.json"
TEMPLATE_PATH: Path = SKILL_ROOT / "assets" / "mv104-template.pdf"
REVISION_PATTERN: re.Pattern[str] = re.compile(r"MV-104\s*\((\d{1,2}/\d{2})\)")
CHANGED_EXIT: int = 3


def revision_of(pdf: Path) -> str | None:
    reader = PdfReader(pdf)
    text = " ".join((page.extract_text() or "") for page in reader.pages)
    match = REVISION_PATTERN.search(text)
    return match.group(1) if match else None


def field_names(pdf: Path) -> set[str]:
    return set((PdfReader(pdf).get_fields() or {}).keys())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", required=True, type=Path, help="freshly downloaded dmv.ny.gov/forms/mv104.pdf")
    args = parser.parse_args()
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    expected: str = rules["expected_revision"]
    live_rev = revision_of(args.live)
    added = field_names(args.live) - field_names(TEMPLATE_PATH)
    removed = field_names(TEMPLATE_PATH) - field_names(args.live)
    report = {"expected_revision": expected, "live_revision": live_rev,
              "fields_added": sorted(added), "fields_removed": sorted(removed)}
    print(json.dumps(report, indent=1))
    changed = live_rev != expected or added or removed
    sys.exit(CHANGED_EXIT if changed else 0)


if __name__ == "__main__":
    main()
