# Part 1 — FC Parity: Cold-Start Flow + File-Tree Alignment

> Scope: **MC repo only.** No Engine changes, no AISL changes. After this part,
> MC is a structural clone of FC and a fresh clone works with zero manual
> steps. Video-specific parsing (duration line, alt slots) is Part 2 — this
> part keeps the existing flat-URL + `frames:` parser behavior working.

## R1 — Zero-setup `run.py` bootstrap (cold start)

Port FC's `run.py` venv lifecycle: find a valid venv (`venv`, `venv_new`),
repair a broken one (delete + recreate), prefer Python 3.12/3.11/3.10/3, then
`pip install --upgrade pip` + install `requirements.txt`, then launch
`src.main_verbose` from the repo root. MC's current `run.py` just errors when
`venv/bin/python` is missing.

- **Acceptance:** deleting `venv/` and running `python3 run.py --dry-run`
  rebuilds the environment and reaches argument parsing without manual steps.

## R2 — Engine-loader re-vendor + STANDBY seeding

- Re-vendor `src/engine_loader.py` from the canonical
  `studiolot/pipeline/engine_loader.py`, keeping the `EngineLoadContext`
  dataclass signature. Fixes the `TYPE_CHECKING`-only runtime-annotation bug.
- Add `copy_standby_profiles(platform, vehicle_root)` (mirror FC's
  `engine_loader.py`) — copies YAML profiles from the Engine package into
  `USER-FILES/02.STANDBY/`; called from `load_engine_or_install`.
- **Acceptance:** loader imports cleanly on Python 3.10–3.12; seeding copies
  the Engine's standby profiles once.

## R3 — `src/engine_contract.py` protocol

`EngineInputFile` protocol + `validate_input_file()` (FC's
`engine_contract.py`) — engines lacking the contract fail fast with a
descriptive `ImportError`. Used by `build_inputs()`.

## R4 — Auth completion

Extend `src/auth/__init__.py` to FC parity: `SUPPORTED_PLATFORMS` +
`DEFAULT_PLATFORM = "replicate"` move in from `engine_loader.py` /
`execution/pipeline.py`; add `get_api_key_interactive()` (`_prompt_platform`,
`_offer_engine_install`, `_prompt_and_save_key` — saves to repo-root `.env`);
keep `authenticate()` as the thin caller-facing name (MC branding) or rename
to `get_api_key()` — decide in questions.md. Add `src/auth/env.py` (.env
loading, FC-style).

## R5 — File-tree alignment to FC

Restructure `src/` to mirror FC exactly (module-per-concern), replacing
`input/`, `config/`, `execution/`:

```
src/main_verbose.py          # thin entry: routing, shared _execute_pipeline
src/cli.py                   # declarative _ARGUMENTS list (FC Session 3)
src/constants.py             # __version__, TIMESTAMP_FORMAT, DEFAULT_PLATFORM
src/datatypes.py             # Bullet TypedDict
src/exceptions.py            # PreflightExit, ConfigurationError
src/engine_loader.py         # vendored canonical + copy_standby_profiles (R2)
src/engine_helpers.py        # discovery, auto-install, build_inputs (+relative_dir),
                             #   load_engine_or_install, print_engine_not_found
src/engine_contract.py       # R3
src/processing/first_run.py  # handle_first_run() — engine check, TTY wizard,
                             #   auto-install, STANDBY seed, non-TTY guidance
src/processing/profiles.py   # load_profile_standalone/studiolot,
                             #   normalize_legacy_profile, empty-STANDBY error
src/processing/bullet_parser.py  # current bullet_reader ported: prompt,
                             #   flat URLs, frames:, [] on empty, URL validation
src/auth/__init__.py         # R4
src/auth/env.py              # R4
src/utils/logging.py         # loguru + _TeeStream capture + write_run_logs
src/utils/path_resolver.py   # timestamped output dirs (YYMMDD_HHMMSS)
```

Delete the now-empty `src/input/`, `src/config/`, `src/execution/`,
`src/parsing/` packages. Delete the `replicate==1.0.4` pin; add
`rich>=13.0.0` (used by the animated live progress line, FC Session 9).

Behavior ports bundled in here:
- `read_bullets()` returns `[]` (log a warning) on an empty input dir.
- URL validation + markdown format warnings from FC's `markdown_parser.py`.
- `_apply_cli_overrides()` merged into both run modes.
- `_handle_preflight_checks()` (cost/dry-run early exit) with `PreflightExit`.
- `relative_dir` metadata so outputs mirror the input folder structure.
- Per-file `.log` via `_TeeStream` (its `encoding` MUST stay a property) +
  `write_run_logs()` beside each generated file.
- Animated live progress line (SpinnerColumn + in-place description);
  per-event message spam removed.
- Standalone empty-STANDBY → `ConfigurationError` with engine guidance.
- `pyproject.toml` (ruff/black/pytest config, FC Session 3 style).

## R6 — Tests

Port FC's mirror tests where behavior was ported: parser tests
(empty-shotlist, URL warnings, frames), engine_loader tests (loader
precedence, pip fallback), auth tests, path_resolver tests. All use tmp
paths — no real API keys, no network.

## Verification (gate before Part 2)

```bash
# in the MC repo, using the venv run.py creates
python3 run.py --dry-run                       # cold-start path reaches parsing
venv/bin/python -m pytest tests/ -v            # all green
venv/bin/python -m ruff check src/ tests/      # clean
# studiolot-mode smoke (no API call):
venv/bin/python -m src.main_verbose --dry-run \
  --input_dir /tmp/mc_input --output_dir /tmp/mc_output \
  --profile /tmp/mc_profile.yaml
```

The studiolot smoke must list bullets from a scratch input dir and exit 0
without creating output folders beyond what dry-run prints.

## Not in this part

- `duration:` line parsing and alt-text slots (Part 2)
- Engine datatype/payload changes (Part 2)
- AISL binding/composition changes (Part 3)
