# Part 3 — AISL `[general]` Chain + Docs Sweep

> Scope: **AISL (studiolot) + MC docs.** Depends on Part 2. Today every VID
> endpoint TOML declares `[general]` (`image_url_param`, `duration_type`,
> `duration_param_name`) and **nothing consumes it**: the AppWizard drops it,
> `compose_profile()` doesn't emit it, the engine falls back to defaults.
> This part wires the chain so MC runs inside AISL get real input/duration
> mapping — and fixes the same latent gap for FC.

## R1 — AppWizard persists `[general]` on the binding

The binding stays self-contained (part-2 Q3 principle): the AppWizard's
binding capture reads the endpoint TOML's `[general]` table and writes it
onto the pipeline.yaml entry alongside `endpoint` + `parameters`. The
Parameters slide keeps excluding `[general]` keys (they are not user-editable
params) — they ride along silently.

- Touch points: `screens/app_wizard/binding.py` (capture + edit extraction),
  `services.py` (`resolve_binding`), `pipeline/config_io.py` canonical
  writer (key order), `models.py::Application` (new field), `config.py`
  mapping. Follow the canonical-home rules in AISL's AGENTS.md — no inline
  composition, no parallel writers.

## R2 — `compose_profile()` emits the mapping

`app/profile_compose.py` copies the binding's `[general]` mapping into the
composed profile (top-level keys, e.g. `image_url_param`,
`duration_param_name`, `duration_type`). Pure dict emission via
`safe_dump` — still no TOML argument, still no path keys.

## R3 — AISL tests

- Binding round-trip: create + edit an instance → `[general]` keys survive
  into pipeline.yaml and back out.
- `compose_profile` emission: mapping keys present; legacy entries without
  them compose unchanged (getattr guards).
- Dry-run display unaffected; PREVIEW unaffected (read-only pane).
- Mirror rule: one test file per touched source module.

## R4 — Docs sweep

- `PHILOSOPHY.md` §3 — bullet format: `duration:` line (int/token), named
  alt slots; retires the `frames:` doc.
- `user-manual/Markdown-input.md` — duration + alt-text syntax.
- `VEHICLE_CONTRACT.md` §4d — video metadata carries the raw duration value.
- `ENGINE_CONTRACT.md` §3/§5 — `[general]` consumption + structured
  references on `InputFile`.
- MC `AGENTS.md` — new source map, session history, known issues.

## Verification (final gate — whole-plan acceptance criteria)

```bash
# AISL repo
./.venv/bin/python -m pytest tests/ -v        # baseline: 740 passed /
                                              # 11 pre-existing failures / 14 skipped
# no new failures; ruff clean on touched files
grep -rn "duration:" docs/architecture/PHILOSOPHY.md docs/user-manual/Markdown-input.md
# MC repo — full suite still green from Part 2
venv/bin/python -m pytest tests/ -v
```

Then the whole-plan acceptance criteria from `plan_context.md` apply:
cold-start works, studiolot run unchanged, Seedance-shaped payload from a
video bullet, FC regression-free, docs updated.
