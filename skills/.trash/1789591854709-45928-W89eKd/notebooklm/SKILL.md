---
name: notebooklm
description: Ingest Dobeu Tech Solutions session artifacts into the canonical NotebookLM notebook for citation-grounded retrieval. Invoke whenever the user types /notebooklm, at any session checkpoint, or when the session-exit checklist fires. Identifies new/modified checkpoint files, Implementation/ plan docs, runbooks, prompt files, and session-export markdown from the dobeu-eco workspace and uploads them to notebook 500e078b-c6a4-440c-b3ea-26b948a41d7c. This is Step 2 of the mandatory Dobeu session-exit checklist (Step 1 is Drive sync). Always trigger this skill when the user mentions "notebooklm ingest", "sync to notebook", "checkpoint NotebookLM", "session exit checklist", or "upload to NotebookLM". Do not skip even if Drive sync already ran — they serve different purposes.
---

# NotebookLM Ingest Skill

Sync material session artifacts from the Dobeu workspace into the canonical NotebookLM notebook so future sessions have citation-grounded retrieval of the latest state.

## Canonical Target

| Field | Value |
|---|---|
| Notebook ID | `500e078b-c6a4-440c-b3ea-26b948a41d7c` |
| Notebook URL | https://notebooklm.google.com/notebook/500e078b-c6a4-440c-b3ea-26b948a41d7c |
| Purpose | Citation-grounded retrieval layer (Drive is the canonical file store; these complement, not duplicate) |

## Artifacts to Ingest (priority order)

Collect these from `C:\Users\jswil\dobeu-eco\` (bash path: `/sessions/dazzling-intelligent-ritchie/mnt/dobeu-eco/`):

1. **Highest-dated checkpoint** — `checkpoint-YYYY-MM-DD.md` at root (the one superseding all others)
2. **Modified implementation docs** — any `.md` under `Implementation/` touched this session
3. **Updated runbooks** — `.md` files under `Manual-steps/` or root-level `*-instructions.md`
4. **Edited system prompts** — `*-sysprodprompt*.md` files if modified this session
5. **New session exports** — `dobeu-*session-export*.md`, `dobeu-full-session-export-*.md`
6. **CLAUDE.md** — if modified this session

**Never upload**: `.gdoc` files, binary files (`*.docx`, `*.xlsx`, `*.zip`), `dobeu-master.env`, any file containing raw secret values, files in `Chat-Transcript/`.

## Step 1 — Identify New Artifacts

Use bash to find recently modified markdown files:

```bash
# Find .md files modified in last 24h (reasonable session proxy)
find /sessions/dazzling-intelligent-ritchie/mnt/dobeu-eco/ \
  -name "*.md" -newer /sessions/dazzling-intelligent-ritchie/mnt/dobeu-eco/CLAUDE.md \
  -not -path "*/Chat-Transcript/*" \
  -not -path "*/.git/*" \
  | sort

# Or: show all checkpoint files by date to identify the canonical one
ls -t /sessions/dazzling-intelligent-ritchie/mnt/dobeu-eco/checkpoint-*.md 2>/dev/null | head -5
```

If unsure which files changed, ask the user: "Which files did we touch this session?" rather than uploading everything.

## Step 2 — Choose Upload Method

Work down this fallback chain, stopping at the first method that works:

### A. notebooklm-mcp (preferred — check for these tools)

Look for tools named `source_add`, `notebook_describe`, `source_describe`, `pipeline` in the available MCP tool list.

```
# Single file:
source_add(notebook_id="500e078b-c6a4-440c-b3ea-26b948a41d7c", source=<file_content>)

# Batch (3+ files):
pipeline(notebook_id="500e078b-c6a4-440c-b3ea-26b948a41d7c", sources=[...])

# Verify after:
notebook_describe(notebook_id="500e078b-c6a4-440c-b3ea-26b948a41d7c")
```

After each `source_add`, call `source_describe` to confirm the source appears.

### B. Composio (fallback)

If notebooklm-mcp tools are not available:

```
COMPOSIO_SEARCH_TOOLS with query "notebooklm"
```

Use any `NOTEBOOKLM_*` actions returned. Map `source_add` → the create/upload action, `notebook_describe` → the read/list action.

### C. Chrome automation (final fallback)

If neither MCP nor Composio is available, use `mcp__Claude_in_Chrome__*` tools:

1. Navigate to `https://notebooklm.google.com/notebook/500e078b-c6a4-440c-b3ea-26b948a41d7c`
2. For each artifact:
   - Click **"+ Add source"** (or the equivalent button in the current UI)
   - Choose "Paste text" or "Upload file" depending on file size
   - For files under ~20KB: read the file content and paste it
   - For larger files: upload directly if possible, otherwise summarize key sections
3. Confirm each source appears in the sources panel before moving to the next

### D. Report and defer

If all automated methods fail, report clearly:

> "NotebookLM ingest could not be completed automatically. Please manually upload these files to https://notebooklm.google.com/notebook/500e078b-c6a4-440c-b3ea-26b948a41d7c — [list of files]. This is a Stage-0 carry-over task."

## Step 3 — Report Results

After attempting ingest, always report:

```
NotebookLM Ingest Summary
=========================
Method used: [notebooklm-mcp / Composio / Chrome / deferred]

✅ Ingested:
  - checkpoint-2026-04-28.md
  - Implementation/v5-final-consolidated-plan.md

⚠️ Skipped (unchanged):
  - CLAUDE.md (not modified this session)

❌ Failed:
  - [filename] — [reason]

Verification: [confirmed via source_describe / not available / pending manual check]
```

## Context: Session-Exit Checklist

This skill is **Step 2** of the mandatory Dobeu session-exit checklist. Both steps must complete before the session ends:

1. **Drive sync** — push modified local files to `/dobeu-eco/` in Google Drive via `mcp__claude_ai_Google_Drive__create_file` or `GOOGLEDRIVE_UPLOAD_UPDATE_FILE`
2. **NotebookLM ingest** ← this skill
3. **Verify** — both layers reflect the new state

If this session has not yet run Step 1 (Drive sync), prompt the user:
> "Drive sync hasn't run yet this session. Run that first, or shall I run both together now?"

Skipping either step creates a Stage-0 carry-over task that must be queued before the next session begins.

## Error Reference

| Error | Cause | Fix |
|---|---|---|
| Auth / 401 | Google account not authenticated | Re-auth in the MCP/browser session |
| Notebook not found | Wrong ID | Confirm ID is `500e078b-c6a4-440c-b3ea-26b948a41d7c` |
| File too large | Source exceeds NotebookLM limit | Truncate to key sections or split into parts |
| Rate limit | Too many adds in quick succession | Add 2s delay between `source_add` calls |
| Duplicate source | File already ingested from a prior session | Skip silently — not an error |
