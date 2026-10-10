#!/usr/bin/env python3
"""Fill the NY MV-104 (5/25) fillable PDF from a JSON of VERBATIM field values.

Usage:
  python3 fill-mv104.py --values verbatim.json --out MV104_<incident>.pdf \
      [--template ../assets/mv104-template.pdf] [--report fill-report.json]

The values JSON is {"<exact PDF field name>": "<value>", ...}. Only values that
pass validation are written. Checkboxes take the state name ("Yes", "PM",
"City", ...). Choice fields must match an allowed option exactly ("1.", "NY").
The report lists what was written, what was rejected, and which REQUIRED
fields are still empty (see references/required-fields.json).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

SKILL_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE: Path = SKILL_ROOT / "assets" / "mv104-template.pdf"
FIELD_MAP_PATH: Path = SKILL_ROOT / "references" / "mv104-field-map.json"
REQUIRED_PATH: Path = SKILL_ROOT / "references" / "required-fields.json"
CHECKBOX_OFF: str = "/Off"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def unwrap_values(raw: Any) -> dict[str, str]:
    """Accept {field: "value"}, {field: {"value":..,"source":..}}, or a
    worksheet {"verbatim": {...}} and return plain {field: value}."""
    section = raw.get("verbatim", raw) if isinstance(raw, dict) else {}
    return {k: (v["value"] if isinstance(v, dict) else v) for k, v in section.items()}


def validate_value(spec: dict[str, Any], value: str) -> str | None:
    """Return an error string if value is not legal for this field, else None."""
    if spec["type"] == "choice" and value not in (spec["options"] or []):
        return f"not an allowed option; allowed: {spec['options']}"
    if spec["type"] == "checkbox" and value not in (spec["states"] or []):
        return f"not an allowed checkbox state; allowed: {spec['states']}"
    if spec["type"] == "text" and not str(value).strip():
        return "empty text"
    return None


def set_checkbox(writer: PdfWriter, field: str, state: str) -> None:
    """Turn on the widget whose appearance state matches `state`, others off."""
    target: str = f"/{state}"
    for page in writer.pages:
        for annot in page.get("/Annots", []) or []:
            obj = annot.get_object()
            name = obj.get("/T") or (obj.get("/Parent") or {}).get("/T")
            if name != field:
                continue
            states = list(obj.get("/AP", {}).get("/N", {}).keys())
            chosen: str = target if target in states else CHECKBOX_OFF
            obj[NameObject("/AS")] = NameObject(chosen)
            parent = obj.get("/Parent")
            holder = parent.get_object() if parent is not None else obj
            holder[NameObject("/V")] = NameObject(target)


DEFAULT_FONT_PT: float = 10.0
MIN_FONT_PT: float = 5.5
COURIER_WIDTH_RATIO: float = 0.6
MULTILINE_FLAG: int = 1 << 12


def fit_font_size(width: float, text: str) -> float:
    """Largest Courier size (≤ default) whose text fits the box width."""
    needed: float = width / (COURIER_WIDTH_RATIO * max(len(text), 1))
    return max(MIN_FONT_PT, min(DEFAULT_FONT_PT, needed))


def shrink_long_text(writer: PdfWriter, text_like: dict[str, str]) -> None:
    """Set a per-widget /DA so long values are not clipped when appearances render."""
    for page in writer.pages:
        for annot in page.get("/Annots", []) or []:
            obj = annot.get_object()
            parent = obj.get("/Parent")
            name = obj.get("/T") or (parent.get_object().get("/T") if parent is not None else None)
            if name not in text_like:
                continue
            flags = int(obj.get("/Ff") or (parent.get_object().get("/Ff") if parent is not None else 0) or 0)
            if flags & MULTILINE_FLAG:
                continue
            rect = [float(x) for x in obj["/Rect"]]
            size = fit_font_size(rect[2] - rect[0], text_like[name])
            obj[NameObject("/DA")] = TextStringObject(f"/Cour {size:.1f} Tf 0 g")


def apply_values(writer: PdfWriter, specs: dict[str, dict], values: dict[str, str]) -> dict:
    written: dict[str, str] = {}
    rejected: dict[str, str] = {}
    text_like: dict[str, str] = {}
    for field, value in values.items():
        spec = specs.get(field)
        if spec is None:
            rejected[field] = "unknown field name (see references/mv104-field-map.md)"
            continue
        err = validate_value(spec, str(value))
        if err:
            rejected[field] = err
            continue
        if spec["type"] == "checkbox":
            set_checkbox(writer, field, str(value))
        else:
            text_like[field] = str(value)
        written[field] = str(value)
    shrink_long_text(writer, text_like)
    for page in writer.pages:
        writer.update_page_form_field_values(page, text_like, auto_regenerate=False)
    return {"written": written, "rejected": rejected}


def required_gaps(required: list[dict], written: dict[str, str], flags: dict[str, bool]) -> list[dict]:
    """Required entries whose condition applies and whose field is still empty."""
    gaps: list[dict] = []
    for item in required:
        condition: str = item.get("when", "always")
        if condition != "always" and not flags.get(condition, False):
            continue
        if item["field"] not in written:
            gaps.append(item)
    return gaps


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--values", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--other-vehicle", action="store_true", help="another vehicle/driver was involved (Part B required)")
    parser.add_argument("--injury", action="store_true", help="someone was injured or killed (persons-involved rows required)")
    args = parser.parse_args()

    specs = {d["field"]: d for d in load_json(FIELD_MAP_PATH)}
    values: dict[str, str] = unwrap_values(load_json(args.values))
    reader = PdfReader(args.template)
    writer = PdfWriter()
    writer.append(reader)
    writer.set_need_appearances_writer(True)
    result = apply_values(writer, specs, values)
    flags = {"other_vehicle": args.other_vehicle, "injury": args.injury}
    result["missing_required"] = required_gaps(load_json(REQUIRED_PATH), result["written"], flags)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "wb") as handle:
        writer.write(handle)
    report_path: Path = args.report or args.out.with_suffix(".fill-report.json")
    report_path.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"written={len(result['written'])} rejected={len(result['rejected'])} "
          f"missing_required={len(result['missing_required'])} -> {args.out}")
    for field, why in result["rejected"].items():
        print(f"  REJECTED {field!r}: {why}")
    for gap in result["missing_required"]:
        print(f"  MISSING REQUIRED: {gap['label']}  [{gap['field']}]")


if __name__ == "__main__":
    main()
