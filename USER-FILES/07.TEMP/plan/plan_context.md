# MC → FC Parity — Shared Plan Context (parts 1–3)

> Read me first, every loop. I do not change between parts.

## Goal

Turn **Motion Conductor (MC)** into the **video-branded clone of Frame
Composer (FC)**. Same parameter system, same cold-start flow, same parser
rigor, same output/log UX. Both vehicles run on the same Engines — the
difference is almost entirely psychological. Video-specific differences, and
only these two:

1. **Duration** — per-bullet value in the markdown (integer, or a token the
   model accepts such as `auto` / `-1`), overriding the instance's default
   duration parameter.
2. **Named payload slots** — the markdown alt text names the payload key:
   `![reference_images](url)` → `reference_images: [url]` in the JSON body
   (Seedance-style multi-slot models). Empty alt → the model's primary input
   key (`image` / `start_image`).

## Repos & key paths

| What | Where |
|---|---|
| MC (this repo) | `.` |
| FC (reference implementation) | `~/Nextcloud/00-PRODUCTION/GENAI_IMG_TOOLS/frame-composer/` |
| Engine (payload builder lives here) | `~/Nextcloud/00-PRODUCTION/GAI_ENGINES/engine-replicate/` |
| Other engines | `~/Nextcloud/00-PRODUCTION/GAI_ENGINES/engine-{fal,openrouter,google}/` |
| AISL (studiolot) | `~/Nextcloud/00-DEVELOPMENT/MISC_DEV_TOOLS/studiolot/` |
| Contracts | AISL `docs/architecture/VEHICLE_CONTRACT.md`, `ENGINE_CONTRACT.md`, `PHILOSOPHY.md` |

## Verified current state (MC)

- Engine-migrated (no direct SDK import), `--platform` committed, studiolot
  mode runs. **Standalone mode is the stale half.**
- `src/engine_loader.py` still has the `TYPE_CHECKING`-only `Any`/`Callable`
  runtime-annotation bug FC fixed (NameError on Python < 3.14); missing
  `copy_standby_profiles()`; `DEFAULT_PLATFORM` lives here but belongs in
  `src/auth/` per the settled auth Q1.
- `src/auth/__init__.py` has the platform key map but no interactive wizard,
  no `SUPPORTED_PLATFORMS` (duplicated in `execution/pipeline.py`).
- `src/input/bullet_reader.py` raises `FileNotFoundError` on an empty input
  dir (FC returns `[]`); no alt-text capture; no URL validation.
- No `relative_dir` metadata (FC mirrors input structure into output),
  no per-file `.log` capture, no animated live progress, no first-run
  wizard, flat `USER-FILES/05.OUTPUT/` (no timestamped run dirs).
- `run.py` errors out if the venv is missing — no zero-setup bootstrap.
- `requirements.txt` pins `replicate==1.0.4` (dead — Engines carry their own
  SDK deps). No `rich`. No `pyproject.toml`. No tests.

## Constraints (non-negotiable)

- **Coding philosophy:** `USER-FILES/00.KB/code_manifesto_memo.md` and
  `code_quantity_memo.md` — minimalism, one tool one purpose, file-size
  limits, no dead code.
- **USER-FILES protection:** never create/modify/move files in
  `USER-FILES/04.INPUT/`; read-only input, write-only to output.
- **VEHICLE_CONTRACT §2:** CLI is `--input_dir --output_dir --profile
  --platform [--install-default-engine]`; engine discovery walks up from
  input/output dir under studiolot; standalone uses vendored `ENGINES/` or
  pip; platform precedence flag > profile > `"replicate"`.
- **No direct SDK imports** in the Vehicle — everything through
  `load_engine()`.
- **The profile is a composed artifact** — MC never writes one, only reads.
- **Branding:** this is Motion Conductor, a video tool. Keep the name and
  video framing; mirror FC's structure, not its copy.
- **FC stays regression-free.** Every datatype/contract change must be
  backward-compatible for FC (which shares the Engines).

## Part map

| Part | Scope | Repos touched |
|---|---|---|
| 1 | FC parity: cold-start flow + file-tree alignment + logs/progress/structure | MC only |
| 2 | Video input layer: duration-in-bullet + alt-text payload slots + Engine contract change | MC + engine-replicate (fal/openrouter/google deferred by author) |
| 3 | AISL `[general]` chain (binding → composed profile) + docs sweep | AISL + MC docs |

## Whole-plan acceptance criteria (printed by mult5 after the LAST part)

1. **Cold start:** fresh `git clone` of MC on a new machine → `python3 run.py`
   → venv created → first-run wizard → engine auto-install → STANDBY seeded →
   standalone generation works end-to-end.
2. **Studiolot run:** composed profile → MC `--profile` → video lands in the
   project run folder with per-file `.log` and mirrored input structure —
   unchanged CLI, unchanged Engine discovery.
3. **Video bullets:** a bullet carrying `duration: auto` and
   `![reference_images](...)` produces a Seedance-shaped payload
   (`duration` honored, URL routed into `reference_images`).
4. **No regressions:** FC runs unchanged; engine-replicate's datatype change
   is additive (fal/openrouter/google still on the old shape keep working —
   parity for them is deferred to later sessions); AISL suite gate holds
   (baseline: 740 passed / 11 pre-existing failures / 14 skipped); MC tests
   green and ruff-clean.
5. **Docs:** PHILOSOPHY §3, user-manual Markdown-input, VEHICLE_CONTRACT §4d,
   ENGINE_CONTRACT §3/§5, MC AGENTS.md all updated.
