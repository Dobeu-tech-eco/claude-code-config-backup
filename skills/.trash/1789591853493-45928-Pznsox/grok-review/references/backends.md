# Backends

The core script `scripts/grok_review.py` routes to Grok through one of three
backends. With `--backend auto` it tries them top to bottom and uses the first
that works. For Office files, pre-process with `scripts/extract_office.py` first
(see "Office files" below).

## 1. grok-cli (preferred — you already run Grok Build)

If the `grok` CLI (Grok Build) is on PATH, the script shells out to it headlessly
(`grok -p "<prompt>"`). No extra config — it reuses your logged-in SuperGrok
Heavy session. Verify:

```bash
grok --version && which grok
```

If your Grok Build version uses different headless flags, run `grok --help` and
adjust the `runGrokCli` call in `grok_review.py` (one line).

## 2. xai-api (portable fallback)

```bash
export XAI_API_KEY="xai-..."
```

- Endpoint: `https://api.x.ai/v1/chat/completions`
- Default model: `grok-4.3` (override with `--model`, e.g. `grok-build-0.1`)
- The API bills separately from your SuperGrok Heavy subscription — the
  subscription does not include API credits.

## 3. composio (routes through your existing bridge)

With `--backend composio` the script prints a ready-to-run payload for your
Composio xAI tool instead of calling Grok directly, so you keep one auth surface.

## Office files (.docx / .xlsx / .pptx)

Don't pass binaries to `grok_review.py` directly — neither model critiques them
well. Convert to reviewable text first:

```bash
python scripts/extract_office.py report.docx > /tmp/report.txt
python scripts/grok_review.py --artifact /tmp/report.txt --context "@brief.md"
```

`extract_office.py` emits headings/paragraphs and tables for docx, bounded cell
grids (formulas preserved) for xlsx, and slide text + notes for pptx. It needs
`python-docx`, `openpyxl`, or `python-pptx` respectively.

## Bring-Your-Own-MCP: let Grok Build reach Composio directly

Grok Build supports Bring-Your-Own-MCP, so point it at your Composio MCP endpoint
instead of leaning on Grok's thin native connector catalog. One MCP connection
exposes everything Composio already brokers (Gmail, Linear, Supabase, Exa, ...)
inside Grok Build — the highest-leverage fix for the weak-connector gap. Exact
config path varies by Grok Build beta release; check current docs.
