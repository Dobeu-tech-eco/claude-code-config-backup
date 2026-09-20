---
name: local-ai-stack-forge-lmstudio-2026-08
description: Local uncensored AI stack on this machine — Stable Diffusion WebUI Forge 2.0.1 + LM Studio, launch commands, ports, and gotchas.
metadata:
  node_type: memory
  type: project
  originSessionId: migrated-from-omc-2026-09-19
  modified: 2026-09-19T00:00:00.000Z
---

Portable **Stable Diffusion WebUI Forge 2.0.1** (A1111 1.10.1) is installed on this machine.
Launch with `run.bat`. It bundles its own Python 3.10.6 + Torch 2.3.1+cu121 under
`system\python` — `SKIP_VENV=1`, no `npm install` needed. First start downloads
`realisticVisionV51_v51VAE.safetensors` into `webui\models\Stable-diffusion` if that folder is
empty.

**Operator guide:** `docs\HOW-TO-USE-FORGE-LM-STUDIO.md` (pointer at
`.omc\HOW-TO-FORGE-LM-STUDIO.md`). Stack shape: LM Studio running Dolphin with `--gpu off` on
port `:1234`, plus Forge with `--api` on port `:7860`. `NeverOOM` setting is the alwayson
"Never OOM Integrated" toggle, set `[true, true]`. Checkpoint switching only works through the
Forge UI (`f2`) — not via API. **`update.bat` wipes the `api.py` config patch** — reapply it
after any Forge update. Smoke-test images live at `webui\outputs\stack-smoke\pony-smoke.png`
and `rv-smoke.png`.

**How to apply:** if asked to work with or troubleshoot this local image-generation stack, use
these exact launch commands/ports rather than guessing; check the smoke-test outputs first to
confirm the stack was last known working before assuming a regression.
