# Rewrite CLAUDE.md for webui_forge_cu121_torch231

## Context

`/init` was run on an install that already has a detailed `CLAUDE.md`. I verified it against the
live tree rather than trusting it: ~20 line references, the ruff exclude list, the API route block,
the blocked-extension list, the torch pin, and both local patches all check out. The architecture
sections are accurate and were expensive to derive — the rewrite restructures and corrects them, it
does not discard them.

What has drifted since the file was written, and what it never covered:

**Now factually wrong**
1. *".omc/ is untracked … not project content"* — 5 `.omc/state/**` files are now **staged** in the
   `webui/` git index (`A` in `git status --short`). `webui/.gitignore` has no `.omc` entry. They
   would ride along in any commit made under `webui/`, and they bury the two real local patches in
   the `git status --short` output that CLAUDE.md tells you to trust.
2. `modules/extensions.py:240` → `list_extensions()` is at **:229**.
3. **Four references name a bare `launch_utils.py`; the file is `modules/launch_utils.py`** —
   `prepare_environment()` (the commented-out `repositories/` clones), `configure_for_tests()`
   (**:499**, with the nonexistent `test/test_files/empty.pt` at :504), `TORCH_COMMAND` (**:365**),
   and `start()` (**:544**, calling `main_thread.loop()` at :554). There is no top-level
   `launch_utils.py`, so all four currently send you to a path that does not exist.
4. *"docs/superpowers/ — operator scratch, not project content"* — `docs/` now holds a real runbook
   and there is a `scripts/` directory CLAUDE.md never mentions.

**Never covered, and load-bearing**
5. **The 8GB VRAM envelope.** RTX 4060 Laptop. Every default in this install is downstream of it
   (NeverOOM UNet+VAE on, 832×1216 SDXL / 512×768 SD1.5, batch 1, LM Studio pinned to CPU). The
   memory-management section explains the machinery but never states the actual budget.
6. **The de-facto test command.** `scripts/lmstudio_to_forge_txt2img.ps1` is a health-check +
   generation harness with real exit codes (2 unreachable, 3 VRAM gate, 4 API failure). It is
   `$PSScriptRoot`-relative, so it survived the install move. Strictly better than the `curl`
   suggestion currently in the Tests section.
7. **What *does* work over the API.** CLAUDE.md spends a long section proving `override_settings`
   and `POST /options` are dead in Forge f2, then stops. The working counterpart is
   `alwayson_scripts` keyed by the Gradio accordion title — `"Never OOM Integrated"`, args
   `[UNet, VAE]`.
8. **Which engines are actually exercised**: Pony Diffusion V6 XL (SDXL) and Realistic Vision V5.1
   (SD1.5) are the only two checkpoints on disk.

Separately, `docs/HOW-TO-USE-FORGE-LM-STUDIO.md` hardcodes the pre-move install path in 6 places,
so its copy-paste commands are broken.

**Outcome:** a `CLAUDE.md` that is correct as of today and carries the operator layer, plus a
runbook whose commands actually run.

## Work

### 1. Rewrite `CLAUDE.md`

Full restructure. Target roughly the current length — the operator additions are offset by tightening
the API section, which currently spends ~25 lines proving a negative.

Section order:

- **What this is** — two-layer split (install root + `webui/` git checkout of
  `lllyasviel/stable-diffusion-webui-forge`, branch `main`), `SKIP_VENV=1` / no virtualenv, embedded
  Python 3.10 in `system/`.
- **This machine** *(new)* — RTX 4060 Laptop 8GB; the tuning envelope from
  `docs/HOW-TO-USE-FORGE-LM-STUDIO.md`; the two installed checkpoints; one GPU owner at a time.
- **Commands** — `run.bat` / `update.bat` chain and the `update.bat` discards-tracked-edits warning
  (both verified, keep); direct `python launch.py --skip-prepare-environment` dev loop; the useful
  arg set; `backend/args.py` as the separate Forge parser merged by `modules/cmd_args.py`.
  **Add** `scripts/lmstudio_to_forge_txt2img.ps1`.
- **Lint** — `ruff check .` and `npm run lint` (needs `npm install`; no `node_modules` present).
  Keep the exclude-list warning — verified at `pyproject.toml:14-21`, under `[tool.ruff.lint]`, and
  it means a clean run may not have touched the file you edited.
- **Verifying a change** *(replaces "Tests")* — still lead with "there is no test suite" and the dead
  residue (`[tool.pytest.ini_options]`, `--test-server` pointing at a nonexistent file). Then:
  - `pwsh scripts\lmstudio_to_forge_txt2img.ps1 -WhatIfHealthOnly` — probes both endpoints and
    asserts the `config` key the local `api.py` patch adds. Exits 0/2/4.
  - add `-SkipLlm` for a full generation without LM Studio running.
  - `curl http://127.0.0.1:7860/sdapi/v1/sd-models` as the bare-minimum fallback.
- **Architecture** — carry over intact; these were verified:
  - three-layer split table (`modules/` inherited · `modules_forge/` glue · `backend/` engine) and
    the moved-paths table.
  - `backend/` map: `loader.py:174` / `:146`, `memory_management.py:495`, `operations.py:334`
    monkeypatching `torch.nn.*`, `patcher/`, `diffusion_engine/`, `nn/`.
  - deferred hash-gated loading: `main_entry.py:120` writes params → `processing.py:783` →
    `sd_models.py:474` → `backend/loader.py`; the `pass` stubs at `sd_models.py:413-454`.
  - the rewiring seams (`devices.py`, `cfg_denoiser.py:185`, `kdiffusion.py:134`,
    `patch_basic.py`), memory sliders → `main_entry.py:97-117`, and the main-thread/worker split
    (`modules/launch_utils.py:544` → `main_thread.loop()` at `:554`).
  - **fix** `extensions.py:240` → `:229`, and requalify all four bare `launch_utils.py`
    references to `modules/launch_utils.py` with their verified line numbers.
- **The API layer** — keep the two dead behaviours but compress to the conclusion plus the one-line
  evidence each (`initialize_util.py:184` commented out; no `stored_opts` reader in
  `processing.py`). **Add**: 37 routes registered in `api.py:209-247`, `--api-server-stop` gates the
  last three at `:244`; the local patch adds `config` to `/sdapi/v1/sd-models`; `alwayson_scripts`
  is the working extension-control path, keyed by accordion title.
- **Extensions and scripts** — carry over: 28 `extensions-builtin/`, `extensions/` empty,
  `modules_forge/config.py:1-3` hard-blocks `sd-webui-controlnet` and
  `multidiffusion-upscaler-for-automatic1111`, the `Script` lifecycle with Forge's added
  `process_before_every_sampling` (`scripts.py:194`), and the `UnetPatcher` API list.
- **Gotchas** — carry over xformers-broken, torch pin, exact-pinned requirements, the UI-preset
  reset trap (`main_entry.py:196-197` wiring `.change` *and* `Context.root_block.load`), and
  missing `config.json` / present `ui-config.json`. **Rewrite** the local-patches bullet around the
  `.omc` staging problem. **Add** that the runbook's paths were stale pre-fix, and that the install
  root has an inert `.gitignore` (not a git repo).

### 2. Fix `docs/HOW-TO-USE-FORGE-LM-STUDIO.md`

Replace `c:\Users\JeremyWilliams\Windows_Repair_Toolbox\Downloads\webui_forge_cu121_torch231` with
`C:\Users\JeremyWilliams\repos\webui_forge_cu121_torch231` at lines **9, 60, 145, 203, 242, 243**.
Nothing else in the doc changes.

`docs/superpowers/plans/*.md` and `.omc/plans/*.md` carry the same stale path but are dated session
artifacts, not runbooks — leave them.

## Verification

1. `git -C webui status --short` → still exactly `M modules/api/api.py` + `M webui-user.bat` among
   tracked changes; confirms the rewrite describes the real patch set.
2. `grep -rn "Windows_Repair_Toolbox" docs/HOW-TO-USE-FORGE-LM-STUDIO.md` → no matches.
3. Re-check every line reference that survives into the new file, the same way they were checked
   here: `grep -n "def forge_model_reload" modules/sd_models.py` and friends. No number ships
   unverified. Already confirmed this pass: `api.py:406-412`, `txt2img.py:16`,
   `img2img.py:116-120`, zero matches for `stored_opts`, `sd_forge_freeu/scripts/forge_freeu.py`,
   and the `models/` tree.
4. `ls webui/launch_utils.py` → no such file, confirming correction #3 was real.
5. Launch `run.bat`, then `pwsh scripts\lmstudio_to_forge_txt2img.ps1 -WhatIfHealthOnly` → exit 0,
   proving the command the rewrite advertises as the health check actually is one.

## Open item (not in scope, flagging only)

The install root carries `.mcp.json` registering `claude-flow` as `ruflo@latest` with **no
`CLAUDE_FLOW_CWD`**, plus repo-local `.swarm/` and `.claude-flow/`. `repos\CLAUDE.md` calls that
exact shape out as the misconfiguration to look for (server binds System32, sees an empty memory
store) and its onboarding gate says to delete embedded `.swarm/`, `.claude-flow/`, and repo-level
`.mcp.json`. Worth a separate cleanup pass.
