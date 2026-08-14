# Netmiko read-only audit tool — new project scaffold

## Context

You invoked `/ecc:netmiko-ssh-automation` with no task and asked me to advise on scope. The
current working directory is a Stable Diffusion WebUI Forge install with nothing network-related
in it, and `repos/new-dobeu-net` turned out to be a Next.js marketing site for the dobeu.net
domain — not network automation. So there is no existing code to extend: this is greenfield.

**Recommendation and chosen scope: a read-only collection/audit tool.** It is the netmiko
skill's own safety default, and it is the prerequisite for everything else — you cannot safely
push config until collection against a reviewed inventory is proven and producing evidence. A
guarded config-push path is deliberately deferred to Phase 2 (see below); `send_config_set` and
`save_config` will not appear anywhere in the v1 codebase, which is a stronger guarantee than a
runtime flag.

**Outcome:** `netmiko-audit <inventory>` SSHes to an explicit list of devices, runs the `show`
commands declared per device group, and writes timestamped evidence (raw output always, TextFSM
JSON when a template matched) plus a run summary — with one device's failure never aborting the batch.

**Decisions already made:** new project folder; Python pinned to 3.12 via uv (avoids a
paramiko/cryptography source build on your default 3.14, which would need Rust + MSVC on Windows);
docs limited to `README.md` + `.env.example`.

## Target

`C:\Users\JeremyWilliams\repos\netmiko-audit`

```
.python-version              3.12
pyproject.toml               uv project; deps: netmiko, pyyaml. dev: pytest
.gitignore                   .env, evidence/, config/inventory.yaml (real inventory never committed)
.env.example                 credential contract only — placeholders, no values
README.md                    what it does, exact run commands, safety posture
config/inventory.example.yaml
src/netmiko_audit/
  __init__.py
  __main__.py                enables `python -m netmiko_audit`
  cli.py                     argparse; --inventory --dry-run --max-workers --out
  credentials.py             env -> getpass; never logged
  inventory.py               load + validate YAML
  collector.py               one device: connect, run commands, return result
  runner.py                  bounded ThreadPoolExecutor fan-out
  evidence.py                write raw/parsed output + summary.json
tests/
  test_inventory.py  test_credentials.py  test_evidence.py
```

Keeps to your repo rules: no working files at root, every module well under 500 lines, one
concern per file.

## Design — each point maps to the skill's review checklist

**Explicit inventory, never a sweep.** `--inventory` is required; there is no host/range flag.
`inventory.py` rejects any host string containing `/` (CIDR) with a clear error, so a subnet
cannot be passed in by accident. Per-device `device_type` lives in the inventory, so mixed
vendor estates work without code changes.

```yaml
defaults:
  conn_timeout: 10
  auth_timeout: 20
  banner_timeout: 15
  read_timeout: 30
groups:
  core-switches:
    device_type: cisco_ios
    commands:
      - show version
      - show ip interface brief
    devices:
      - host: 192.0.2.10        # documentation-range placeholders in the example file
      - host: 192.0.2.11
```

**Credentials.** `credentials.py` reads `NETMIKO_USERNAME`, `NETMIKO_PASSWORD`,
`NETMIKO_ENABLE_SECRET`; falls back to `input()`/`getpass()` only when stdin is a TTY; fails fast
with an actionable message when non-interactive and unset. The device dict is built inside
`collector.py` and is never logged, repr'd, or embedded in an error. Netmiko exceptions can carry
connection params, so failures are reported as `type(exc).__name__` plus a sanitized message —
the same shape the skill's batch example uses. `.env.example` documents the three vars with
placeholders; `.env` is gitignored.

**Timeouts everywhere.** `conn_timeout` / `auth_timeout` / `banner_timeout` on the device dict,
explicit `read_timeout` on every `send_command`. Defaults come from the inventory `defaults:`
block so they are tunable per estate without touching code.

**Per-device isolation.** `collector.py` returns `{host, ok, commands: {...}, error}` and catches
`NetmikoAuthenticationException`, `NetmikoTimeoutException`, `ReadTimeout`. `runner.py` collects
via `as_completed`; one dead device yields `ok: false` and the batch continues.

**Bounded concurrency.** `--max-workers` defaults to **4** and is hard-capped at 16 — a
fat-fingered `--max-workers 200` is rejected, not honored, so old gear and AAA aren't hammered.

**TextFSM is an optimization, never the only evidence.** `use_textfsm=True` with
`raise_parsing_error=False`. The raw `.txt` is written unconditionally; the parsed `.json` is
written only when netmiko returned a list. Raw output is never discarded in favor of parsed.

**Evidence layout** (`evidence/` gitignored — it will contain real device output):

```
evidence/<utc-run-id>/
  <host>/<command-slug>.txt     always
  <host>/<command-slug>.json    only when a TextFSM template matched
  summary.json                  per-host ok/fail + reason, commands run, timings
```

**`--dry-run` (safety affordance and test seam).** Resolves the inventory, confirms credentials
are *available* without printing them, and prints the exact plan — which hosts, which commands,
which timeouts, what concurrency — while opening zero connections. This is the mode to run first
against any new inventory.

**Reuse, not reinvention.** netmiko's `ConnectHandler` context manager, its exception classes,
and its bundled ntc-templates parsing do the SSH and parsing work. No hand-rolled SSH, no regex
output scraping.

## Testing

Unit tests (pytest) cover the pure logic where they earn their keep: inventory load/validate
(including CIDR rejection and missing-field errors), credential resolution across the
env / TTY / non-interactive-failure paths, evidence path construction and file writing, and
summary aggregation from mixed ok/failed results.

To be straight with you: the SSH path itself is not deeply mocked — faking paramiko transport is
high-effort, low-value, and proves little. It is verified against a real or lab device in the
live checks below. I will not claim 80% coverage over the I/O layer.

## Verification

1. `uv sync` completes on pinned 3.12 with no source builds.
2. `uv run python -m netmiko_audit --inventory config/inventory.example.yaml --dry-run` prints
   the plan and exits 0 having opened no connections.
3. `uv run pytest` green.
4. Negative paths behave: credentials unset non-interactively → clear error, non-zero exit;
   a CIDR string in the inventory → rejected; `--max-workers 50` → rejected.
5. Live, against one real device: evidence files and `summary.json` appear; a deliberately
   unreachable host in the same run comes back `ok: false` while the reachable host still
   collects.
6. Secret-leak check: grep the console log and the whole `evidence/` tree for the password
   value — zero hits.

## Phase 2 (not built now)

Guarded config push in a separate module: dry-run by default behind an explicit operator flag,
before/after `show run` capture around every change, and `save_config()` as a distinct
approval step tied to verification — never bundled with the push.
