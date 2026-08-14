# Plan: Improve the existing `CLAUDE.md`

## Context

`/init` asked for a CLAUDE.md. One already exists at the install root
(`webui_forge_cu121_torch231/CLAUDE.md`, ~11 KB) and it is **good** — I verified its
claims against the tree and every one held up:

- The stubbed-to-`pass` list in `modules/sd_models.py:413-454` — correct.
- The f1.x→f2.0 file-move table (`forge_loader` → `backend/loader.py:174`, etc.) — correct.
- Line refs `backend/memory_management.py:495`, `backend/operations.py:334`,
  `modules_forge/main_entry.py:97-117,120`, `modules/processing.py:783,785`,
  `modules/scripts.py:14,194` — all correct.
- 28 `extensions-builtin/` dirs, empty `extensions/`, 3 `repositories/`,
  `modules_forge/config.py` blocking exactly 2 extensions, ruff excludes — correct.
- No test suite; `SKIP_VENV=1` in `environment.bat`; `--api` in `webui/webui-user.bat` — correct.

So this is not a rewrite. It needs three things: **one stale fact corrected**, **one
new section** covering the API layer (which the install is actively running and has been
locally patched), and **two gotchas** that are non-obvious and cost real debugging time.

## Changes to `CLAUDE.md`

### 1. Replace the stale working-tree claim (Gotchas section)

Current text says `webui/` "is currently clean and tracking upstream `main`. The only
untracked entry is `.omc/`". That is now false, and the whole class of statement goes
stale. Replace with a durable warning:

> **`webui/` carries local patches.** As of writing, `modules/api/api.py` (adds a
> `config` field to `/sdapi/v1/sd-models`) and `webui-user.bat` (`--api`) are modified
> against upstream `main`. **`update.bat` discards tracked edits** — run
> `git -C webui diff` before updating and re-apply after. Check the current set with
> `git -C webui status --short` rather than trusting this paragraph.

### 2. New section: "The API layer" (insert after *Threading*)

Warranted because the install runs with `--api` and `modules/api/api.py` is patched.

- `modules/api/api.py` + `modules/api/models.py`; ~40 routes registered in
  `Api.__init__` (`api.py:209-247`). `--api-server-stop` gates
  `server-kill`/`server-restart`/`server-stop` (`api.py:245`).
- **`override_settings` is dead in Forge f2.** It is still *collected*
  (`api.py:406-412`, `modules/txt2img.py:16`, `modules/img2img.py:116-120`) and still a
  field on `StableDiffusionProcessing` (`processing.py:158`), but A1111's stored-opts
  apply/restore block was deleted from `process_images` (`processing.py:780`). Nothing in
  the tree reads it — `grep stored_opts` returns nothing. Per-request
  `sd_model_checkpoint` / `sd_vae` overrides **silently no-op**.
- **`POST /sdapi/v1/options` does not switch checkpoints.** The
  `onchange("sd_model_checkpoint", … reload_model_weights)` hook is commented out at
  `modules/initialize_util.py:184`, and `reload_model_weights` is one of the stubs.
  `forge_model_reload()` (`sd_models.py:474`) keys off
  `model_data.forge_loading_parameters`, which **only**
  `modules_forge/main_entry.py:120 refresh_model_loading_parameters()` writes — and that
  is called only from UI paths (`forge_main_entry`, `checkpoint_change`, `vae_change`).
  So the option changes, the hash doesn't, and the old model keeps serving. Programmatic
  switching must call `refresh_model_loading_parameters()` after setting the option.
- `sd_model_checkpoint` is declared `OptionInfo(None, "(Managed by Forge)", gr.State)`
  (`modules/shared_options.py:173`) — it is not a real settings-page control.

### 3. Two gotchas to add

- **The UI preset clobbers defaults on every page load.** The `sd`/`xl`/`flux`/`all`
  radio is wired both to `.change` *and* to `Context.root_block.load`
  (`modules_forge/main_entry.py:196-197`), so `on_preset_change` (L203-290) rewrites
  width, height, CFG, distilled CFG, sampler, scheduler, VAE, clip-skip and GPU-Weights
  on each load. Changing those defaults anywhere else appears to have no effect.
- **`webui/config.json` does not exist yet**, so all `shared.opts` run at their
  declared defaults; it is created on the first `shared.opts.save()`. Per-component UI
  defaults live separately in `ui-config.json` (present, 79 KB).

### 4. Small additions to *Commands*

- Note that the install root also holds `forge-api-restart*.log` and `docs/superpowers/`
  — operator scratch, not project content, so they should not be mistaken for source.
- Add the running-server check `curl http://127.0.0.1:7860/sdapi/v1/sd-models` under the
  "verify changes by running the app" line, since there is no test suite.

## Files

- Modify: `C:\Users\JeremyWilliams\Windows_Repair_Toolbox\Downloads\webui_forge_cu121_torch231\CLAUDE.md`
- No source files change.

## Verification

1. Re-read the edited `CLAUDE.md` end to end for internal consistency (no duplicated
   claims between the new API section and the existing *Model loading is deferred* section
   — cross-reference instead of restating).
2. Spot-check every line number newly cited:
   `modules/initialize_util.py:184`, `modules/shared_options.py:173`,
   `modules/api/api.py:209,245,406`, `modules_forge/main_entry.py:196,203`.
3. Confirm the stale-state paragraph is gone: `grep -n "currently clean" CLAUDE.md`
   returns nothing.
4. Sanity-check the `override_settings` claim once more with
   `grep -rn "stored_opts\|override_settings_restore_afterwards" --include=*.py .`
   (should show only the dataclass field).
