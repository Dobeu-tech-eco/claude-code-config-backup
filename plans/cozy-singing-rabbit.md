# Plan: Create CLAUDE.md for the SD WebUI Forge install

## Context

`C:\Users\JeremyWilliams\Windows_Repair_Toolbox\Downloads\webui_forge_cu121_torch231` is the one-click portable package of **Stable Diffusion WebUI Forge** (`f2.0.1v1.10.1`). There is no existing `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, or Copilot instructions anywhere in the tree, so a future Claude Code session starts blind.

The thing that most needs documenting is non-obvious and cannot be discovered from any single file: **Forge f2.0 gutted `modules_forge/` and moved the real inference engine into a new `backend/` package**, then *stubbed out* A1111's model-loading functions in `modules/sd_models.py`. Almost every published Forge guide (and the model's own priors) describes the old f1.x layout with `modules_forge/forge_loader.py`, `forge_sampler.py`, and `unet_patcher.py` — files that no longer exist here. Without this written down, a session will confidently edit the wrong layer or invent files.

Secondary non-obvious facts worth capturing: the embedded Python 3.10 with `SKIP_VENV=1`, the deleted test suite (whose residue still sits in `pyproject.toml` and `.gitignore`), and ruff's exclusion of `modules/` and `modules_forge/`.

**Decisions (confirmed with the user):** emphasis is code architecture; the file goes at the **install root** (session cwd, and not a git repo so `update.bat` can never touch it).

## Files

- **Create:** `C:\Users\JeremyWilliams\Windows_Repair_Toolbox\Downloads\webui_forge_cu121_torch231\CLAUDE.md`
- No other files are touched. The `webui/` git tree stays pristine.

## Proposed content

````markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The one-click portable package of **Stable Diffusion WebUI Forge** (`f2.0.1v1.10.1`, based on
AUTOMATIC1111 SD-WebUI 1.10.1). Two layers:

- **Install root** (this dir) — launcher scripts plus `system/` holding an embedded **Python 3.10**
  and git. Not a git repo.
- **`webui/`** — the actual source; a git checkout of
  `https://github.com/lllyasviel/stable-diffusion-webui-forge`, branch `main`.

`environment.bat` puts `system/python` and `system/git/bin` on PATH and sets `SKIP_VENV=1`, so
**there is no virtualenv** — `webui.bat` skips its venv block entirely and runs the embedded
interpreter directly.

## Commands

Run from the install root unless noted.

```bat
run.bat            :: environment.bat -> cd webui -> webui-user.bat -> webui.bat -> launch.py
update.bat         :: git -C webui pull; falls back to `git reset --hard` + pull on conflict
```

`update.bat` will **discard tracked local edits under `webui/`**. Untracked files survive.

Pass launch args by editing `set COMMANDLINE_ARGS=` in `webui\webui-user.bat` (gitignored, so edits
are safe). `modules/paths_internal.py:12` shlex-splits that env var into `sys.argv`.

Direct invocation, for iterating without the launcher:

```bat
call environment.bat
cd webui
python launch.py --skip-prepare-environment --api --loglevel DEBUG
```

Useful args: `--skip-prepare-environment` (skip all pip/git work — the fast dev loop),
`--skip-install` (skips *only* extension `install.py` runs, not torch/requirements),
`--skip-torch-cuda-test`, `--api`, `--nowebui`, `--allow-code`, `--disable-all-extensions`,
`--forge-ref-a1111-home`. Forge's own backend args live in a separate parser, `backend/args.py`
(`--unet-in-fp8-e4m3fn`, `--attention-pytorch`, `--always-low-vram`, `--cuda-stream`,
`--pin-shared-memory`, …), merged in by `modules/cmd_args.py`.

In-app, Settings → Reload UI and the Restart button (`tmp/restart` + `modules/restart.py`)
re-import script modules without a full process restart.

### Lint

```bat
ruff check .                :: from webui/ ; config in pyproject.toml
npm run lint                :: eslint . ; `npm run fix` to autofix (needs npm install first)
```

**Ruff excludes `modules/`, `modules_forge/`, `extensions/`, `extensions-builtin/`, `ldm_patched/`**
— so it effectively only covers `backend/`, `scripts/`, `launch.py`, `webui.py`. Do not assume a
clean `ruff check` means the file you edited was checked.

### Tests

**There is no test suite.** Forge deleted A1111's `test/` directory and all `.github/` workflows.
Residue that looks like tests but is dead: `[tool.pytest.ini_options]` in `pyproject.toml`,
`/test/*` entries in `.gitignore`, and `launch_utils.configure_for_tests()` (referenced by
`--test-server`, which points at a `test/test_files/empty.pt` that does not exist). Verify changes
by running the app.

## Architecture

### The three-layer split (read this before editing anything)

Forge **f2.0** rewrote the inference stack. The layout is *not* what older Forge documentation
describes:

| Layer | Role |
|---|---|
| `modules/` | Inherited A1111 code — Gradio UI, `processing.py` pipeline, options, API. Largely unmodified, but with key functions stubbed (below). |
| `modules_forge/` | Thin **bootstrap + UI shim**. Was the engine in f1.x; is now glue. |
| `backend/` | **The actual inference engine.** A rewritten, de-ComfyUI-ified model-management stack. |

Files moved in the f2.0 rewrite — **the old paths do not exist**:

| Old (Forge f1.x, and most guides) | Actual location here |
|---|---|
| `modules_forge/forge_loader.py` | `backend/loader.py` (fn still named `forge_loader`) |
| `modules_forge/forge_sampler.py` | `backend/sampling/sampling_function.py` |
| `modules_forge/unet_patcher.py` | `backend/patcher/unet.py`, `backend/patcher/base.py` |
| `modules_forge/forge_util.py` | `modules_forge/utils.py` |
| `modules_forge/stream.py` | `backend/stream.py` |

`repositories/` holds only `stable-diffusion-webui-assets`, `huggingface_guess`, and `BLIP` — the
A1111 `stablediffusion` / `generative-models` / `k-diffusion` clones are commented out in
`launch_utils.prepare_environment()` because `backend/` and the vendored `k_diffusion/` replace them.

### `backend/` map

- `loader.py` — model construction entry. `forge_loader(sd, sd_vae)` (L174); `split_state_dict`
  (L146) uses the `huggingface_guess` package to identify the architecture and slice the state dict.
- `memory_management.py` — the whole VRAM/offload system (~1145 lines). Central entry point is
  `load_models_gpu(models, memory_required=0)` (L495). Also owns all dtype/device policy
  (`unet_dtype`, `vae_device`, `should_use_fp16`, …), which `modules/devices.py` now merely forwards to.
- `operations.py` — `ForgeOperations`: replacement `nn.Linear/Conv*/GroupNorm/LayerNorm/Embedding`
  that lazily cast weights. `using_forge_operations()` (L334) **monkeypatches `torch.nn.*` during
  model construction** so every layer becomes a Forge op. `operations_bnb.py` is the nf4/fp4 variant.
- `patcher/` — `ModelPatcher` (`base.py`), `UnetPatcher` (`unet.py`), `CLIP`, `VAE`, `controlnet.py`,
  `lora.py`. Weights are **never mutated in place**; LoRA is a patch list applied at `patch_model()`.
- `diffusion_engine/` — `ForgeDiffusionEngine` + `sd15/sd20/sdxl/flux` subclasses. These are what
  `shared.sd_model` actually is; `base.py:56 fix_for_webui_backward_compatibility()` re-exposes the
  legacy LDM attributes A1111 code and extensions poke at.
- `nn/` re-implemented networks (`unet.py`, `flux.py`, `vae.py`, `clip.py`, `t5.py`);
  `attention.py` (all attention backends); `sampling/`; `text_processing/`; `stream.py` (CUDA
  dual-stream = the "Async" swap method); `huggingface/` (config-only HF trees, no weights, used as
  the schema for building a model from a bare `.safetensors`).

### Model loading is deferred and hash-gated

Selecting a checkpoint **does not load it**. `modules_forge/main_entry.py:120
refresh_model_loading_parameters()` only writes a plain dict to
`modules.sd_models.model_data.forge_loading_parameters`. The real load happens later, from
`modules/processing.py:783` calling `sd_models.forge_model_reload()` (`modules/sd_models.py:473`),
which hashes those parameters and no-ops if unchanged, then calls `backend/loader.py forge_loader`.

**A1111's loading functions are stubbed to `pass`** at `modules/sd_models.py:413-454`: `load_model`,
`reload_model_weights`, `unload_model_weights`, `reuse_model_from_already_loaded`,
`send_model_to_cpu/device/trash`, `instantiate_from_config`, `get_empty_cond`. Editing them does
nothing. Change `forge_model_reload()` or `backend/loader.py` instead.

Other seams where `modules/` was rewired into `backend/`:

- `modules/devices.py` — every device/dtype global delegates to `memory_management`.
- `modules/sd_samplers_cfg_denoiser.py:185` — CFG combine → `backend.sampling.sampling_function`.
- `modules/sd_samplers_kdiffusion.py:134` — wraps sampling in `sampling_prepare(unet, x)` /
  `sampling_cleanup(unet)`; k-diffusion's `CompVisDenoiser` is swapped for
  `k_diffusion/external.py:41 ForgeScheduleLinker`.
- Runtime monkeypatches beyond `torch.nn.*`: `modules_forge/patch_basic.py` wraps `torch.load` and
  `safetensors.torch.load_file` to quarantine corrupt files as `*.corrupted`, and patches
  `gradio.networking.url_ok`.

### Memory management, and what the UI sliders actually do

Mapped in `modules_forge/main_entry.py:97-117`:

- **GPU Weights (MB)** → `forge_inference_memory = total_vram - value` →
  `memory_management.current_inference_memory`. The slider is "VRAM budgeted for weights"; the
  remainder is the reserved activation budget from `minimum_inference_memory()`.
- **Swap Method** Queue/Async → `backend/stream.py stream_activated` (Async copies weights on a
  separate CUDA stream).
- **Swap Location** CPU/Shared → `memory_management.PIN_SHARED_MEMORY` (offloaded modules get
  `.pin_memory()`).
- Any change sets `processing.need_global_unload = True`, consumed at `modules/processing.py:785`.

`load_models_gpu` frees memory, then per model computes `free - model - inference`; if negative it
switches to `LOW_VRAM` and places each module either on GPU or on the offload device with
`parameters_manual_cast = True`, which is what makes `ForgeOperations` cast/stream it per forward.

### Threading

`launch_utils.start()` runs the Gradio UI on a worker thread and calls
`modules_forge.main_thread.loop()` on the main thread; all txt2img/img2img work is funnelled through
that single worker so model moves stay serialized. This differs from A1111 — do not assume
generation runs on the request thread.

### Extensions and scripts

`extensions-builtin/` (28 dirs, mostly `sd_forge_*`) and `extensions/` (**empty in this install**)
are discovered by `modules/extensions.py:240`. Per-extension hooks: `install.py`, `preload.py`
(`preload(parser)` adds CLI args), `scripts/*.py`, `javascript/*.js`, `style.css`, `metadata.ini`
(canonical name + `Requires`/`Before`/`After` ordering).

`modules_forge/config.py` **hard-blocks two extensions** regardless of settings, because Forge ships
its own equivalents: `sd-webui-controlnet` and `multidiffusion-upscaler-for-automatic1111`.

`modules/scripts.py` `Script` lifecycle: `title`, `ui`, `show` (return the `AlwaysVisible` sentinel
to stay mounted every generation), `run` (dropdown-selected only), `before_process`, `process`,
`before_process_batch`, **`process_before_every_sampling` (Forge-added — where Forge extensions
patch the unet per sampling pass)**, `process_batch`, `postprocess_*`. Global (non-`Script`) hooks
live in `modules/script_callbacks.py`.

Extensions patch the model through `UnetPatcher` (`backend/patcher/unet.py`), not by touching
weights: `set_model_unet_function_wrapper`, `set_model_attn1/2_patch|replace`, `add_block_modifier`,
`add_conditioning_modifier`, `add_sampler_pre_cfg_function`, `add_patched_controlnet`,
`add_extra_preserved_memory_during_sampling`, `set_memory_peak_estimation_modifier`. All
`extensions-builtin/sd_forge_*` scripts are written against this API — read one (e.g.
`sd_forge_freeu/scripts/forge_freeu.py`) before writing a new one.

## Gotchas

- **xformers are broken in this build** (README, 2024-08-11). If you see
  `NoneType object is not iterable`, uninstall xformers. `--xformers` installs `0.0.27`.
- Torch is pinned to `2.3.1` / `torchvision 0.18.1` on cu121 by `TORCH_COMMAND` in
  `launch_utils.py` — matching this package's name. Don't upgrade torch in place.
- Requirements are exact-pinned in `requirements_versions.txt` and checked with
  `importlib.metadata` version equality; a mismatch triggers a reinstall on every launch.
- `webui/` is currently clean and tracking upstream `main`. The only untracked entry is `.omc/`
  (oh-my-claudecode session state, not project content).
- Models live under `webui/models/` (`Stable-diffusion`, `Lora`, `VAE`, `ControlNet`,
  `text_encoder`, `diffusers`, …). HF caches are redirected to `models/diffusers` by
  `modules_forge/initialization.py`.
````

## Verification

1. `Read` the created file to confirm it landed at the install root and renders as intended.
2. Spot-check the load-bearing claims against source, since a wrong pointer is worse than none:
   - `Grep` for `def forge_loader` → expect `webui/backend/loader.py`, and confirm
     `webui/modules_forge/forge_loader.py` does **not** exist.
   - `Read webui/modules/sd_models.py` around L413-480 → confirm the stubbed `pass` functions and
     `forge_model_reload`.
   - `Read webui/modules_forge/main_entry.py:97-120` → confirm the GPU-Weights → `forge_inference_memory`
     mapping.
   - `Grep -n "process_before_every_sampling" webui/modules/scripts.py` → confirm the hook exists.
3. `git -C webui status --porcelain` → must still show only `?? .omc/`; the new file is outside the
   repo and must not appear.
