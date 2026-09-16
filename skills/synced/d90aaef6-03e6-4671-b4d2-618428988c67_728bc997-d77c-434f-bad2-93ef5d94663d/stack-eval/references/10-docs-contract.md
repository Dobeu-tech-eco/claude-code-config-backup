# P10 — Docs contract (rules / system / STRATEGY)

## Goal

Establish (or refresh) the documentation contract agents must follow before / during / after work.

## Steps

1. Create or update root **`rules.md`** from [doc-templates/rules.md.template](doc-templates/rules.md.template).
2. Create or update root **`system.md`** from [doc-templates/system.md.template](doc-templates/system.md.template).
3. Invoke **`ce-strategy`** (or project equivalent) to create/update root **`STRATEGY.md`**. Do **not** duplicate a STRATEGY template in this skill.
4. Require in both docs that agents update documentation **before**, **during**, and **after** substantive work.
5. Point agents at `.agent/` for run ledgers (not ad-hoc roots).

## STOP / CONTINUE

- **STOP:** `rules.md` / `system.md` missing and STRATEGY not attempted.
- **CONTINUE:** Docs contract present; STRATEGY created/updated or failure documented with user-visible note.

## Outputs

- `rules.md`, `system.md`, `STRATEGY.md` (repo root)
- Note in `.agent/progress.md`
