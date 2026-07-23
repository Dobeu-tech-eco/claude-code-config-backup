# Install `/stack-eval`

**Source of truth (SoT):**  
`dobeutech-designsystem-weaver/.claude/skills/stack-eval/`

Write once in SoT, then sync outward. Do **not** edit copies as primary — edit SoT and re-sync.

## Local install matrix

| Ecosystem | Spot | Path |
|-----------|------|------|
| Claude Code | Project / SoT | `<repo>/.claude/skills/stack-eval/` |
| Cursor | Personal | `%USERPROFILE%\.cursor\skills\stack-eval\` (never `skills-cursor`) |
| Cursor | Project (optional) | `<repo>/.cursor/skills/stack-eval/` |
| Claude Code | User | `%USERPROFILE%\.claude\skills\stack-eval\` |
| Codex CLI | User | `%USERPROFILE%\.codex\skills\stack-eval\` |
| Agents home | User | `%USERPROFILE%\.agents\skills\stack-eval\` |

### Sync order

1. SoT (repo `.claude/skills/stack-eval`)
2. `~/.cursor/skills/stack-eval`
3. `~/.claude/skills/stack-eval`
4. `~/.codex/skills/stack-eval`
5. `~/.agents/skills/stack-eval`
6. Optional: `<repo>/.cursor/skills/stack-eval`
7. Document / perform web & Cowork & ChatGPT uploads (manual)

### Run sync

**Windows (PowerShell):**

```powershell
cd <repo>/.claude/skills/stack-eval/scripts
.\sync-installs.ps1
# optional project mirror:
.\sync-installs.ps1 -IncludeRepoCursor
# rebuild upload zip after SoT edits:
.\package-zip.ps1
```

**Unix / Git Bash / WSL:**

```bash
cd <repo>/.claude/skills/stack-eval/scripts
chmod +x sync-installs.sh package-zip.sh
./sync-installs.sh
# optional:
./sync-installs.sh --include-repo-cursor
./package-zip.sh
```

Scripts mirror the entire skill folder (SKILL.md, INSTALL.md, references/, scripts/, and `dist/` when present) into each destination.

**Upload package (prebuilt):**  
`<repo>/.claude/skills/stack-eval/dist/stack-eval.zip`  
Zip root must be the `stack-eval/` folder (so the archive contains `stack-eval/SKILL.md`, not a bare `SKILL.md`).

## Surface discovery (important)

| Surface | How skills load | Local `~/.claude/skills` enough? |
|---------|-----------------|----------------------------------|
| **Claude Code CLI** | Filesystem: personal `~/.claude/skills/` + project `.claude/skills/` | **Yes** — auto-discovered |
| **Cowork** | Skills enabled on your **claude.ai account**, synced at session start (Customize / Skills UI). Does **not** read `~/.claude/skills/` on disk. | **No** — upload/enable via Skills UI (same account as claude.ai) |
| **claude.ai** | Upload zip under Settings / Customize → Skills; enable the skill | **No** — zip upload required |
| **Cloud / remote Claude Code** | Account skills + project skills committed under the cloned repo’s `.claude/skills/` | Partial — commit project skill; personal-only skills need account enable |

Official note: Cowork and cloud sessions do **not** load personal machine skills from `~/.claude/skills/`. Enable the skill for your claude.ai account (or commit it under the repo for cloud project sessions).

## Manual upload checklist (cannot fully automate)

### 1) claude.ai (web Skills)

1. Use the prebuilt zip:  
   `.claude/skills/stack-eval/dist/stack-eval.zip`  
   Or rebuild: `.\scripts\package-zip.ps1` / `./scripts/package-zip.sh` from the skill folder.
2. Confirm zip structure: `stack-eval/SKILL.md` at the first level inside the archive (directory name must match skill `name`).
3. Open [claude.ai](https://claude.ai) → **Customize** / **Settings** → **Skills** (or Capabilities → Skills, per current UI).
4. **Upload skill** / import the zip.
5. **Enable** the skill. Confirm name `stack-eval` and that `disable-model-invocation: true` is honored (invoke only via `/stack-eval` or explicit ask).
6. Re-upload after every SoT change (rebuild zip, then upload again).

### 2) Claude Cowork

Cowork does **not** auto-discover `~/.claude/skills/stack-eval` on your machine.

1. Install/enable the skill on the **same claude.ai account** used by Cowork (step 1 above — zip upload + Enable).
2. Or open **Customize → Skills** in the Claude Desktop / Cowork sidebar and upload/enable from the same `dist/stack-eval.zip`.
3. Start a **new** Cowork session so account skills re-sync.
4. Verify `/stack-eval` appears and does not auto-invoke (`disable-model-invocation: true`).

Syncing SoT → `~/.claude/skills` still helps **Claude Code CLI** only; it does not replace the Cowork/claude.ai upload.

### 3) ChatGPT Codex (online) / Codex skill installer

1. Zip SoT `stack-eval` **or** use `$skill-installer` / Codex skill install from the repo path if available in your Codex build.
2. In ChatGPT Codex / online Codex skills UI: upload zip or install from path.
3. Confirm local CLI copy exists at `~/.codex/skills/stack-eval` (from sync script) for CLI use.
4. Re-install after SoT updates.

## Optional Drive backup

Per Codex/agent home conventions, an optional backup mirror may live at:

`G:\My Drive\claude\skills\stack-eval`

- **Not** an automatic sync target in the scripts (Drive paths vary / may be unavailable).
- After a successful local sync, optionally copy the SoT folder there manually for backup only.
- Never treat Drive as SoT — SoT remains the repo `.claude/skills/stack-eval/` path.

## Verify install

```powershell
# SoT
Test-Path <repo>\.claude\skills\stack-eval\SKILL.md
# Personal mirrors
Test-Path $env:USERPROFILE\.cursor\skills\stack-eval\SKILL.md
Test-Path $env:USERPROFILE\.claude\skills\stack-eval\SKILL.md
Test-Path $env:USERPROFILE\.codex\skills\stack-eval\SKILL.md
Test-Path $env:USERPROFILE\.agents\skills\stack-eval\SKILL.md
# Upload zip
Test-Path <repo>\.claude\skills\stack-eval\dist\stack-eval.zip
```

Confirm relative links from `SKILL.md` resolve under `references/` and that hard STOPs + Vercel default + Opsera fallback text are present.
