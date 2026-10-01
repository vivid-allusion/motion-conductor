# Part report — phase_1.md

> Per-unit report (PLAN §4.4), written by `/part-close` from actual gate and verifier results — never from memory.

- **Status:** DONE
- **Part:** phase_1.md (`phase_1.md` filename, or ticket id `Pn`)
- **Date:** 2026-10-01T18:45:00Z
- **Repo / branch:** /home/admin/APPLICATIONS/video-generator · master
- **Commit:** — (this close commit)

## Gate results

| Gate | Exact command | Exit | Result |
|---|---|---|---|
| Unit `## Verification` | `test -f` × six then `hc.presets` assert block + round-trip block (from `~/MISC/studiolot`) | 0 | pass (`OK files exist`, `OK six presets + order`, `OK round-trip dolly-in dolly-in`) |
| Resolver `verify=` | `./venv/bin/python -m pytest tests/` | 0 | pass (85 passed in 0.33s) |
| Resolver `lint=` | `./venv/bin/ruff check` | 0 | pass (All checks passed!) |
| File-size scan | `wc -l` over changed files | — | breaches: none (no changed `.py`; studiolot deliverable is data files) |

## Verifier verdict

`VERDICT: APPROVE`

- R1 (six video preset files): MET — `ac87c70` adds `console/studiolot/presets/{dolly-in,dolly-left,dolly-out,dolly-right,handheld,orbit}.preset`, each 10 lines with canonical header, correct `name`, `media_type = "video"`, verbatim `description`/`prefix`/`suffix`, `reference_media = ""`; unit gate exit 0.
- R2 (`presets.order` 18→24): MET — diff inserts `dolly-in · dolly-out · dolly-left · dolly-right · handheld · orbit` after `photo-to-faux3d`, before `16-9-to-9-16`; asserts `len(order)==24`, `order[0]=="txt-img-to-img"`, `order[-3:]==["16-9-to-9-16","21-9-to-9-16","9-16-to-16-9"]`, `order[15:21]` matches.
- R3 (boundaries): MET — diff is six new files + a 6-line order addition; no image preset touched, no added keys, no parser code, no test edits (`pytest tests/` 85 passed = baseline).
- R4 (commit in studiolot): MET — `ac87c70` "feat(presets): add six video camera-movement defaults (W98 M1)", 7 files / 66 insertions, specific files only, no push.
- Acceptance criterion 1 (plan_context): MET — gate (a) verifies `media_type=="video"`, non-empty prefix/suffix/description, `preset_stem(name)==stem`, `reference_media==""`, order length/first/last-three, and `read_preset(write_preset(p))==p`.
- Deterministic gate green: MET — 119-line/4350-byte diff; verify 85 passed; ruff clean; no size breach.
- MUST-FIX: none

## Evidence per acceptance criterion

- Six presets exist and parse as video: `test -f` × 6 and `read_preset(...).media_type == 'video'` in the unit Verification block → exit 0 `OK six presets + order`.
- Stems match the §3 table: `preset_stem(p.name) == stem` for all six → in the same passing block.
- `presets.order` holds 24 stems once with invariants: `presets.order` (`wc -l` = 25 incl. header comment); slice `order[15:21]` = the six video stems → `OK six presets + order`.
- Schema round-trip (handoff §6): `read_preset(write_preset(p)) == p` → `OK round-trip dolly-in dolly-in`.
- VG gate untouched/green: `./venv/bin/python -m pytest tests/` → `85 passed in 0.33s`; `./venv/bin/ruff check` → `All checks passed!`.
- Studiolot tree clean after commit, six files tracked: `git status --porcelain` empty; `git ls-files console/studiolot/presets/ | grep -E "dolly|handheld|orbit"` lists all six.

## Carried forward

- none

## Next pointer

- `phase`: `phase_2.md`
- Next unit Verification (Part 2, studiolot): `./.venv/bin/python -m pytest tests/test_default_presets.py tests/test_project_init_scaffold.py -q` and `./.venv/bin/ruff check tests/test_default_presets.py tests/test_project_init_scaffold.py` → expect all green, ruff clean, image-only assertions still present.
