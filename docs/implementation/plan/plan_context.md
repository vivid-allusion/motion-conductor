# W98 — Camera-movement presets — Shared Plan Context (parts 1–6)

> Read me first, every loop. I do not change between parts.
> Handoff (read-only input): `docs/implementation/handoffs/W98-mc-camera-presets-plan.md`
> Source issue: `vivid-allusion/video-generator` #2. Queue item:
> `~/INFRA/loops-and-goals-mgmt/queue/items/W98-mc-camera-presets.md`.
> Closure (when built): `~/PLATFORM/theia-platform/docs/handoffs/W98-mc-camera-presets-closure.md`.

## Goal

Ship the Owner-scoped six camera-movement presets (`Dolly in/out/left/right`,
`Handheld`, `Orbit`) as studiolot's bundled **video** defaults, and implement
the contract-mandated `reference_images` merge in VG so a composed profile's
preset media is never silently dropped.

This is a **cross-repo** work order (Owner Q-1): the six `.preset` files +
`presets.order` + the shipped-default/scaffold test amendments land in
**studiolot**; VG carries the `reference_images` merge (`GENERATOR_CONTRACT.md`
§2f) and the docs. M4 is in scope (Owner Q-3); the six ship words-only,
`reference_media = ""` (Owner Q-4). The Owner's wording pass over the §2 strings
happens **after** the build (Q-2), so the build starts from the §2 content
unchanged.

## Repos & key paths

| What | Path |
|---|---|
| VG repo root (the loop's GUARD path) | `/home/admin/APPLICATIONS/video-generator` |
| studiolot repo root | `/home/admin/MISC/studiolot` |
| Plan dir / pointer | `docs/implementation/plan/`, `docs/implementation/plan/current_part.txt` |
| Question log / TODO | `docs/implementation/questions.md`, `TODO.md` |
| VG `build_inputs` (M4) | `src/engine_helpers.py::build_inputs` (lines ~101–155) |
| VG merge tests | `tests/test_engine_helpers.py` |
| VG gate | `./venv/bin/python -m pytest tests/` (baseline **85 passed**) |
| VG lint | `./venv/bin/ruff check` (ruff installed into `./venv` by the build; no `pyproject.toml`/`requirements.txt` change) |
| studiolot presets | `console/studiolot/presets/*.preset` + `presets.order` |
| studiolot schema | `hc/presets.py` (`Preset`, `read_preset`, `write_preset`, `preset_stem`, `extract_reference_media`, `read_preset_order`, `write_preset_order`) |
| studiolot compose | `hc/profiles.py::compose_profile` |
| studiolot seed | `console/studiolot/screens/project_init/scaffold.py::copy_default_presets` |
| studiolot tests | `tests/test_default_presets.py`, `tests/test_project_init_scaffold.py`, `tests/test_app_profile_compose.py` |
| studiolot gate | `./.venv/bin/python -m pytest tests/` (baseline **2034 passed / 24 skipped**) |
| studiolot lint | `./.venv/bin/ruff check .` |

## Constraints (non-negotiable)

- Cross-repo: studiolot edits commit in the studiolot repo; VG edits commit in
  this repo. Never push either. Never `git add -A`; never commit `venv/` or log
  artifacts.
- The six presets ship `reference_media = ""` (words-only): do not invent
  reference assets; do not extend the schema in VG.
- Test amendments **flag, don't relax** (W212): keep strict per-media checks;
  never delete or blanket-relax an assertion to make it pass.
- `presets.order` invariants: `order[0] == "txt-img-to-img"` and
  `order[-3:] == ["16-9-to-9-16", "21-9-to-9-16", "9-16-to-16-9"]` hold.
- VG adds **no** preset parsing, no preset directory, no `--preset` flag.
- No silent drop: an unroutable `reference_images` value must fail loud.
- File-size limits: soft 250 / hard 400 lines; module-per-concern.
- Out of scope: the other ten movements on issue #2.
- `USER-FILES/` is read-only (no writes); no engine/provider logic.

## Part map

| Part | Milestone | Repo | Scope | Commits in |
|---|---|---|---|---|
| 1 | M1 | studiolot | Author the six `.preset` files + `presets.order` (18→24) | studiolot |
| 2 | M2 | studiolot | Amend the shipped-default + scaffold tests (24; per-media pinned) | studiolot |
| 3 | M3 | studiolot | Schema round-trip proof + durable regression lock | studiolot |
| 4 | M4 | VG | Implement `GENERATOR_CONTRACT.md` §2f `reference_images` merge in `build_inputs` | VG |
| 5 | M5 | VG + studiolot | Full suites + lint per repo | both |
| 6 | M6 | VG | Docs / history | VG |

Parts are sequential (1→2→3; 4 uses synthetic profiles in its tests but is
proven end-to-end once 1–3 land; 5→6 close out).

## Whole-plan acceptance criteria

1. **Six video presets exist** in `console/studiolot/presets/`; each parses with
   `media_type == "video"`; `preset_stem(name)` matches the §3 table;
   `presets.order` lists all 24 stems once with the first/last-three invariants
   held.
2. **studiolot tests amended, not relaxed:** the shipped-default + scaffold
   tests assert 24 presets (18 image + 6 video) with per-media checks pinned,
   and pass.
3. **Schema capability proven and locked:** a shipped camera preset round-trips
   `read_preset(write_preset(p)) == p`; `compose_profile` emits
   `reference_images` (authored order) for a media-bearing preset and omits it
   (and `description`) for an empty one; a regression test encodes this.
4. **VG merges preset media:** `build_inputs` appends
   `profile["reference_images"]` after each input's own references — into the
   declared `reference_images` slot when declared, else `reference_urls` — and
   fails loud when it cannot route.
5. **Gates green:** VG suite green (baseline 85 passed) + ruff clean; studiolot
   suite green (baseline 2034 passed / 24 skipped) + ruff clean.
6. **Recorded:** VG `docs/HISTORY.md` carries the W98 outcome; stale
   preset-schema prose refreshed if present.

## Branch

`master` — the plan branch in VG (resolver `branch=master`). studiolot changes
land on studiolot's current branch (`master`).

## Commit model (cross-repo)

Each part commits only the files it changed, in the repo that owns them:

- Parts 1–3 commit in `~/MISC/studiolot` (specific files, conventional message).
- Parts 4–6 commit in this repo (VG).

Never `git add -A`; never push either repo.
