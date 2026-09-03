# TODO.md — MC → FC Parity, Part 3 (AISL `[general]` Chain + Docs Sweep)

> Repos: AISL = `~/Nextcloud/00-DEVELOPMENT/MISC_DEV_TOOLS/studiolot/` (R1–R4),
> MC = this repo (R4 AGENTS.md + final gate). Settled questions drive the
> shape: Q12 nested `general:` table, Q21 whole-table flatten, Q22
> edit-and-save upgrade, Q23 implement + commit in each repo.

- [x] **MC (repo root)** Switch to branch `mc-fc-parity` if not already on it
  - Requirement: loop guard; Part 3 work lands on the parity branch
  - Action: `git branch --show-current` (already on `mc-fc-parity` — verified)
  - Effort: 1 | Priority: High

## R1 — AppWizard persists `[general]` on the binding (AISL)

- [x] **AISL: console/studiolot/models.py** Implement `Application.general` field
  - Requirement: R1 "new field" on `Application`; binding stays self-contained (part-2 Q3)
  - Type: config / datatype
  - Action: add `general: dict = {}` to `Application` (default empty dict — legacy entries load without it; dataclass-style default like `parameters`)
  - Effort: 1 | Priority: High
  - Related: depends on nothing; feeds R1 writer (config_io) and config mapping

- [x] **AISL: pipeline/config_io.py** Implement nested `general:` persistence in the canonical writer
  - Requirement: R1 "pipeline/config_io.py canonical writer (key order)" — the only writer of pipeline.yaml entries
  - Type: config / output handling
  - Action: extend `_build_entry()` (and thereby `append_pipeline_entry`/`update_pipeline_entry`) with a `general: dict | None = None` param; emit the nested `general:` table in fixed key order (after `parameters`); omit the key entirely when empty/None so legacy files stay clean
  - Effort: 2 | Priority: High
  - Related: needs the `Application.general` field (models.py); consumed by app_wizard/services.py create/update

- [x] **AISL: console/studiolot/config.py** Implement pipeline.yaml → `Application.general` mapping
  - Requirement: R1 "config.py mapping"
  - Type: config
  - Action: read `s.get("general", {})` in `load_pipeline_config()` and pass `general=...` into the `Application(...)` constructor; non-dict guard mirrors the existing `parameters` guard
  - Effort: 1 | Priority: High
  - Related: pair with models.py + config_io.py (the R1 persistence trio)

- [x] **AISL: console/studiolot/screens/app_wizard/binding.py** Implement `[general]` capture (create) + edit-mode re-capture
  - Requirement: R1 "binding capture reads the endpoint TOML's `[general]` table and writes it onto the pipeline.yaml entry"; Q22 settled: edit-and-save upgrades legacy bindings
  - Type: config / payload
  - Action: the wizard's endpoint catalog already carries `general` (param_schema.py reads `endpoint.get("general", {})`), so add a `capture_general(context)` helper returning the selected endpoint's `general` dict (empty for `__custom__`); edit-mode capture re-reads it from the re-selected endpoint TOML — legacy instances upgrade on re-save, no load-time backfill. Parameters slide untouched: `BINDING_EXCLUDES` + `general` keys already keep `[general]` out of the parameter capture
  - Effort: 2 | Priority: High
  - Related: pair with services.py `resolve_binding` threading; cross-ref Q22

- [x] **AISL: console/studiolot/screens/app_wizard/services.py** Implement `resolve_binding` → `general` threading
  - Requirement: R1 "services.py (`resolve_binding`)" — create AND edit paths must persist the captured table
  - Type: config
  - Action: `resolve_binding()` returns `(endpoint, parameters, general)`; `do_create` passes `general` to `write_app_instance(...)`, `do_update` to `_update_pipeline_entry(...)` — both delegate to the config_io canonical writer
  - Effort: 2 | Priority: High
  - Related: depends on config_io.py writer signature + binding.py capture; cross-ref R1 trio

## R2 — `compose_profile()` emits the mapping (AISL)

- [x] **AISL: console/studiolot/app/profile_compose.py** Implement `[general]` flatten into the composed profile
  - Requirement: R2 "copies the binding's `[general]` mapping into the composed profile (top-level keys)"; Q21 settled: emit the WHOLE table flattened — incl. `slots` (named-slot routing per acceptance 3) and `duration_type` (rides along)
  - Type: payload / output handling
  - Action: `profile.update(getattr(app_def, "general", None) or {})` before `yaml.safe_dump` — getattr guard so legacy bindings compose unchanged (R3); pure dict emission, still no TOML argument, still no path keys
  - Effort: 2 | Priority: High
  - Related: depends on `Application.general`; cross-ref Q21 + the R3 compose test

## R3 — AISL tests (mirror rule: one test file per touched source module)

- [x] **AISL: tests/test_app_wizard_binding.py + test_app_wizard_services_binding.py** Implement binding round-trip tests
  - Requirement: R3 "Binding round-trip: create + edit an instance → `[general]` keys survive into pipeline.yaml and back out"
  - Type: testing
  - Action: extend the existing wizard binding/service test files — create via `do_create` (or the capture functions) with an endpoint carrying `general`, assert the pipeline.yaml entry has the nested `general:` table; edit an instance (incl. a legacy one without `general`) and assert re-save persists the re-captured table (Q22)
  - Effort: 2 | Priority: High
  - Related: pair with R1 capture/threading tasks

- [x] **AISL: tests/test_app_profile_compose.py** Implement compose emission + legacy-guard tests
  - Requirement: R3 "compose_profile emission: mapping keys present; legacy entries without them compose unchanged (getattr guards)"
  - Type: testing
  - Action: assert the composed YAML carries top-level `image_url_param`, `duration_param_name`, `duration_type`, `slots` when `Application.general` is set; assert an `Application` with `general={}`/absent composes byte-identical to today's output
  - Effort: 1 | Priority: Med
  - Related: pair with profile_compose.py task; cross-ref Q21

- [x] **AISL: tests/test_config_io.py + test_config.py + test_models.py** Implement persistence/mapping round-trip tests
  - Requirement: R3 mirror rule — every touched source module gets coverage; `[general]` survives write → read → `Application.general`
  - Type: testing
  - Action: config_io: `_build_entry` emits the table in canonical key order, omits when empty; config: pipeline.yaml entry with `general:` maps into the `Application` field; models: default `{}` when absent
  - Effort: 2 | Priority: Med
  - Related: pair with the R1 persistence trio

- [x] **AISL: tests/** Implement dry-run / PREVIEW non-regression test
  - Requirement: R3 "Dry-run display unaffected; PREVIEW unaffected (read-only pane)"
  - Type: testing
  - Action: extend the existing dry-run/preview test files (test_app_*_run/header/preview) — assert dry-run output and the read-only PREVIEW pane render identically for an instance with `general` set
  - Effort: 1 | Priority: Med
  - Related: guards R2's compose change from leaking into display paths

## R4 — Docs sweep

- [x] **AISL: docs/architecture/PHILOSOPHY.md §3** Implement bullet-format docs update
  - Requirement: R4 "bullet format: `duration:` line (int/token), named alt slots; retires the `frames:` doc"
  - Type: documentation
  - Action: rewrite §3 — `duration:` (raw int or token like `auto`/`-1`, wins over legacy `frames:`), alt-text named slots (`![reference_images](url)`), empty alt → primary key; remove/retire the `frames:` documentation
  - Effort: 1 | Priority: Med
  - Related: pair with Markdown-input.md (same bullet syntax, user-facing copy)

- [x] **AISL: docs/user-manual/Markdown-input.md** Implement duration + alt-text syntax docs
  - Requirement: R4 "duration + alt-text syntax"
  - Type: documentation
  - Action: user-facing examples: `duration: 5` / `duration: auto`, named-alt routing, unknown-slot erroring when the profile declares slots
  - Effort: 1 | Priority: Med
  - Related: pair with PHILOSOPHY.md §3

- [x] **AISL: docs/architecture/VEHICLE_CONTRACT.md §4d** Implement video metadata docs update
  - Requirement: R4 "video metadata carries the raw duration value"
  - Type: documentation
  - Action: document `InputFile.metadata = {duration (verbatim int|str|float), fps, relative_dir}` — the vehicle never interprets the duration value
  - Effort: 1 | Priority: Med

- [x] **AISL: docs/architecture/ENGINE_CONTRACT.md §3/§5** Implement `[general]` consumption + references docs
  - Requirement: R4 "`[general]` consumption + structured references on `InputFile`"
  - Type: documentation
  - Action: §3: endpoint TOML `[general]` (image_url_param / duration_type / duration_param_name / slots) is consumed via the composed profile, not runtime TOML lookup; §5: additive `InputFile.references: dict[str, list[str]]` (named slots) alongside `reference_urls`
  - Effort: 1 | Priority: Med

- [x] **MC: AGENTS.md** Implement session-history + source-map update
  - Requirement: R4 "MC AGENTS.md — new source map, session history, known issues"
  - Type: documentation
  - Action: append the Part 3 session entry (AISL `[general]` chain wired, composed profiles carry slots/mapping, docs sweep), refresh the source file map + known issues (vendored engine-replicate pull note stays until pulled)
  - Effort: 2 | Priority: Med
  - Related: last — documents the finished Part 3 state

## Verification gates

- [x] **AISL repo** Run full pytest + ruff gate
  - Requirement: phase_3 "Verification (final gate)": baseline 740 passed / 11 pre-existing failures / 14 skipped — no new failures; ruff clean on touched files
  - Type: testing / validation
  - Action: `./.venv/bin/python -m pytest tests/ -v`; compare failure set against baseline; `ruff check` on models.py, config.py, pipeline/config_io.py, app_wizard/binding.py, app_wizard/services.py, app/profile_compose.py
  - Effort: 2 | Priority: High
  - Related: runs after all R1–R3 tasks

- [x] **MC repo** Run full pytest + ruff gate
  - Requirement: phase_3 verification — MC suite still green from Part 2 (60 tests)
  - Type: testing / validation
  - Action: `venv/bin/python -m pytest tests/ -v` + ruff clean
  - Effort: 1 | Priority: High

- [x] **Both repos** Verify whole-plan acceptance criteria + docs grep
  - Requirement: plan_context acceptance criteria 1–5 (cold start, studiolot composed-profile run, Seedance-shaped payload from a video bullet, FC regression-free, docs updated)
  - Type: validation
  - Action: `grep -rn "duration:" docs/architecture/PHILOSOPHY.md docs/user-manual/Markdown-input.md`; studiolot dry-run smoke with a composed profile (preflight passes, no output dir); MC dry-run/cost-estimation smoke; confirm FC tree untouched
  - Effort: 2 | Priority: High
  - Related: final gate — everything above must land first

### ⛔ STOP HERE ⛔

### DO NOT IMPLEMENT ANYTHING BELOW THIS LINE WITHOUT EXPLICIT USER REQUEST
