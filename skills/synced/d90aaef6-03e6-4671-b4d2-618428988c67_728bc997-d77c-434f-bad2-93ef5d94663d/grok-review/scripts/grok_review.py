#!/usr/bin/env python3
"""Send an artifact + context brief to Grok for an independent review.

Backends (auto-detected in this order unless --backend is set):
  1. grok-cli   -> shells out to the locally installed Grok Build CLI (grok -p ...)
  2. xai-api    -> POSTs to https://api.x.ai/v1/chat/completions using XAI_API_KEY
  3. composio   -> prints a ready-to-run payload for your Composio xAI tool

For .docx/.xlsx/.pptx, run scripts/extract_office.py first and pass the text
output as --artifact; binaries are not reviewed well directly.

Outputs are written to .agent/reviews/<timestamp>/ to slot into a checkpoint
convention. A structured JSON verdict is extracted when Grok returns one.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

XAI_API_URL = "https://api.x.ai/v1/chat/completions"
DEFAULT_MODEL = "grok-4.3"
TEXT_SUFFIXES = {".md", ".txt", ".py", ".ts", ".tsx", ".js", ".jsx", ".json",
                 ".yaml", ".yml", ".toml", ".css", ".html", ".sql", ".sh", ".csv"}
BINARY_SUFFIXES = {".docx", ".xlsx", ".pptx", ".pdf"}
MAX_INLINE_CHARS = 60_000

RUBRIC = """You are an independent reviewer from a different model family than the
author. Your job is to find what the author missed, NOT to agree. A review that
only praises is a failed review.

Evaluate against these axes and be specific and concrete:
- Correctness: factual / logical / technical errors.
- Completeness: gaps, unhandled cases, missing steps or sections.
- Risk: what breaks, what is unsafe, what is hard to reverse.
- Simpler alternative: a cleaner path the author may have over-engineered past.
- What it missed: the single most important thing the author overlooked.

End your reply with EXACTLY this fenced JSON block and nothing after it:
```json
{
  "verdict": "approve | revise | reject",
  "confidence": 0.0,
  "top_issues": ["", "", ""],
  "one_thing_wrong": "",
  "simpler_alternative": ""
}
```"""


def parseArgs() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Send an artifact to Grok for review.")
    p.add_argument("--artifact", action="append", default=[],
                   help="Path to a file to review. Repeatable.")
    p.add_argument("--context", default="",
                   help="Context brief, or @path to read it from a file.")
    p.add_argument("--backend", choices=["auto", "grok-cli", "xai-api", "composio"],
                   default="auto")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--blind", action="store_true",
                   help="Redact the author's conclusions from the CONTEXT BRIEF so "
                        "Grok isn't anchored. The artifact itself is left intact.")
    p.add_argument("--out", default=".agent/reviews")
    return p.parse_args()


def loadContext(raw: str) -> str:
    if raw.startswith("@"):
        return Path(raw[1:]).read_text(encoding="utf-8", errors="replace")
    return raw


def readArtifact(path: str) -> str:
    f = Path(path)
    if not f.exists():
        return f"[MISSING FILE: {path}]"
    suffix = f.suffix.lower()
    if suffix in BINARY_SUFFIXES:
        return (f"[BINARY ARTIFACT: {path}] Run scripts/extract_office.py on it first "
                "and pass the text output instead for a content-level review.")
    if suffix in TEXT_SUFFIXES or suffix == "":
        return f.read_text(encoding="utf-8", errors="replace")[:MAX_INLINE_CHARS]
    return f"[UNSUPPORTED ARTIFACT TYPE: {path}]"


def buildPrompt(context: str, artifacts: list[str], blind: bool) -> str:
    if blind:
        context = re.sub(r"(?im)^.*(my conclusion|i recommend|i think|verdict)[:\-].*$",
                         "[author conclusion withheld for blind review]", context)
    blocks = [RUBRIC, "\n## Context\n" + (context or "(none provided)")]
    for path in artifacts:
        blocks.append(f"\n## Artifact: {path}\n{readArtifact(path)}")
    return "\n".join(blocks)


def hasCmd(cmd: str) -> bool:
    return any((Path(d) / cmd).exists()
               for d in os.environ.get("PATH", "").split(os.pathsep))


def runGrokCli(prompt: str) -> str | None:
    if not hasCmd("grok"):
        return None
    try:
        out = subprocess.run(["grok", "-p", prompt], capture_output=True,
                             text=True, timeout=300)
        return out.stdout.strip() or out.stderr.strip()
    except (subprocess.SubprocessError, OSError) as err:
        print(f"[grok-cli failed: {err}]", file=sys.stderr)
        return None


def runXaiApi(prompt: str, model: str) -> str | None:
    key = os.environ.get("XAI_API_KEY")
    if not key:
        return None
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(XAI_API_URL, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {key}")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except Exception as err:  # noqa: BLE001
        print(f"[xai-api failed: {err}]", file=sys.stderr)
        return None


def emitComposioPayload(prompt: str) -> str:
    return ("[composio] No direct call made. Hand this to your Composio xAI tool:\n\n"
            + json.dumps({"model": DEFAULT_MODEL,
                          "messages": [{"role": "user", "content": prompt}]}, indent=2))


def route(prompt: str, backend: str, model: str) -> tuple[str, str]:
    if backend in ("auto", "grok-cli"):
        out = runGrokCli(prompt)
        if out:
            return "grok-cli", out
        if backend == "grok-cli":
            return "grok-cli", "[grok CLI not found on PATH]"
    if backend in ("auto", "xai-api"):
        out = runXaiApi(prompt, model)
        if out:
            return "xai-api", out
        if backend == "xai-api":
            return "xai-api", "[XAI_API_KEY not set or request failed]"
    return "composio", emitComposioPayload(prompt)


def extractVerdict(review: str) -> dict | None:
    match = re.search(r"```json\s*(\{.*?\})\s*```", review, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def writeOutputs(out_dir: str, review: str, verdict: dict | None) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    target = Path(out_dir) / stamp
    target.mkdir(parents=True, exist_ok=True)
    (target / "review.md").write_text(review, encoding="utf-8")
    if verdict is not None:
        (target / "verdict.json").write_text(json.dumps(verdict, indent=2),
                                             encoding="utf-8")
    return target


def main() -> int:
    args = parseArgs()
    if not args.artifact and not args.context:
        print("Provide at least one --artifact or --context.", file=sys.stderr)
        return 1
    prompt = buildPrompt(loadContext(args.context), args.artifact, args.blind)
    backend, review = route(prompt, args.backend, args.model)
    verdict = extractVerdict(review)
    target = writeOutputs(args.out, review, verdict)
    print(f"Backend: {backend}")
    print(f"Saved:   {target}/review.md")
    if verdict:
        print(f"Verdict: {verdict.get('verdict')} "
              f"(confidence {verdict.get('confidence')})")
        for issue in verdict.get("top_issues", []):
            if issue:
                print(f"  - {issue}")
    else:
        print("No structured verdict returned; see review.md for the full text.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
