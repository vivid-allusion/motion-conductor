## Agent Behaviour Rules

### General Behavior

- MUST: Ask for clarification when requirements are ambiguous
- MUST: Verify all changes work before confirming completion
- SHOULD: Run tests before committing code
- SHOULD: Provide clear explanations for complex changes
- SHOULD NOT: Make assumptions about file locations or project structure

### Error Handling

- MUST: Report errors with full context to the user
- MUST: Continue processing other items when individual items fail
- SHOULD: Suggest solutions when errors occur
- SHOULD: Validate inputs before processing
- SHOULD NOT: Silently ignore errors or warnings

## USER-FILES Protection Rules

### ABSOLUTE FORBIDDEN - USER-FILES/04.INPUT/
- MUST NEVER: Create, delete, modify, move, or rename ANY files in USER-FILES/04.INPUT/
- CAN ONLY: Read files from USER-FILES/04.INPUT/

### General USER-FILES Rules
- MUST: Never create, delete, modify, move, or rename files in USER-FILES/ without explicit permission
- MUST: Ask before any operation in USER-FILES/
- SHOULD: Only read from USER-FILES/04.INPUT/ and write to USER-FILES/05.OUTPUT/
- SHOULD NOT: Implement any auto-cleanup or archiving features

## Project Structure Rules

- MUST: Read inputs only from USER-FILES/04.INPUT/
- MUST: Write outputs only to USER-FILES/05.OUTPUT/ with timestamps (YYMMDD_HHMMSS format)
- SHOULD: Preserve input directory structure in outputs

## Python Code Standards

- MUST: Use type hints for all function signatures
- MUST: Use pathlib.Path for file operations (not os.path)
- SHOULD: Keep functions under 50 lines
- SHOULD: Format with black and lint with ruff
- SHOULD: Add docstrings for all public functions

## Testing Standards

- MUST: Write tests for critical functionality
- SHOULD: Test happy paths and edge cases
- SHOULD: Mock external dependencies
- SHOULD: Keep tests fast and focused

## Configuration Management

- MUST: Use environment variables for sensitive data
- MUST: Validate configuration at startup
- SHOULD: Provide sensible defaults

## Dependency Management

- MUST: Pin exact versions in requirements.txt
- MUST: Use virtual environments
- SHOULD: Keep dependencies minimal

---

## Architecture: Engine Interface

### Core Concept
The Motion Conductor (Vehicle) delegates all API/provider logic to Engine plugins.
"The Vehicle orchestrates. The Engine executes. The profile configures."

MC is a **video generation Vehicle** — it reads video bullets (markdown files with
prompts + image URLs + optional frame counts), loads an Engine, and calls
`engine.run()` with `InputFile` objects carrying `metadata = {duration, fps}` per
VEHICLE_CONTRACT.md §4d.

### Engine Loading
- `src/engine_loader.py` — canonical `load_engine()` implementation, vendored
  from studiolot. Mirrors FC's loader exactly.
- Searches `search_paths` for `engine-<platform>/` directories
- Local clones take precedence over pip-installed packages (VEHICLE_CONTRACT §2b)
- Corrupted local engine falls back to pip-installed package

### Supported Platforms
`replicate`, `fal`, `openrouter`, `google` — new engines added by installing the
corresponding package.

### Processing Flow

Standalone mode (TTY):
```
main() → _run_standalone()
  → handle_first_run()            # engine check → TTY wizard → auto-install
                                  #   → STANDBY seed (empty shelf only) →
                                  #   auto-activate first STANDBY profile (Q2)
  → load_profile_standalone()     # 03.PROFILES/ only — never falls back
  → resolve_input_path()          # profile paths block or USER-FILES/04.INPUT/
  → read_bullets()                # parse .md inputs (prompt + URLs + frames)
  → _handle_preflight_checks()    # --cost-estimation / --dry-run → PreflightExit
  → create_timestamped_output_path()  # 05.OUTPUT/<YYMMDD_HHMMSS>_VID/
  → get_api_key()                 # 4-tier (env → pass → .env → wizard fallback)
  → load_engine()
  → _execute_pipeline()           # build inputs → run → report → per-file .log
```

Studiolot mode:
```
main() → _run_studiolot()
  → load_profile_studiolot()      # from --profile path
  → read_bullets()                # HEAD URL validation skipped under --dry-run
  → _handle_preflight_checks()    # before any output_dir.mkdir (Q16)
  → output_dir.mkdir()            # only after preflight passes
  → get_api_key()
  → find_project_engines_dir()    # walk up from --output_dir
  → load_engine()
  → _execute_pipeline()
```

`_execute_pipeline()` (shared): `build_inputs()` (metadata = `{duration, fps,
relative_dir}`) → rich `Progress` spinner wrapping `engine._on_progress`
(in-place task description, restored in finally) → `engine.run(inputs)` →
`_report_results()` → `write_run_logs()` writes `<file>.log` beside every
generated video (fallback `motion_conductor_<ts>.log` when nothing generated).

### Video-Specific Input
- Bullet files carry `frames: N` optional override (line-parsed via `_FRAMES_RE`)
- `build_inputs()` reads `fps` and `duration` from profile `parameters` block
- Each `InputFile.metadata` = `{"duration": float, "fps": int, "relative_dir": str}`
- Per-bullet `frames:` override converts to duration = frames / fps
- `relative_dir` mirrors the bullet's folder structure under the output dir
- Legacy profiles with `duration_config` block are normalized by `normalize_legacy_profile()`

### CLI Modes
1. **Standalone mode** (no `--profile`/`--input_dir`/`--output_dir`): reads profile
   from `USER-FILES/03.PROFILES/` (fallback `02.STANDBY/`), inputs from
   `USER-FILES/04.INPUT/`, outputs to `USER-FILES/05.OUTPUT/`
2. **Studiolot mode** (with `--profile --input_dir --output_dir`): explicit paths
   for all three, discovers Engine via `00_APPLICATIONS/ENGINES/` walking up from
   output_dir

---

## Source File Map (current)

| File | Purpose |
|------|---------|
| `run.py` | Zero-setup bootstrap: finds/repairs venv (`venv`, `venv_new`), prefers Python 3.12/3.11/3.10/3, upgrades pip + installs requirements, launches `src.main_verbose` from repo root |
| `src/main_verbose.py` | Thin entry point, CLI routing, both run modes, `_execute_pipeline()` + preflight + CLI overrides |
| `src/cli.py` | Declarative `_ARGUMENTS` list — `--input_dir`, `--output_dir`, `--profile`, `--platform`, `--dry-run`, `--debug`, `--verbose`, `--cost-estimation`, `--no-save-payloads`, `--install-default-engine` (no `--force-png`) |
| `src/constants.py` | `__version__`, `TIMESTAMP_FORMAT`, `DEFAULT_PLATFORM` (canonical home, Q3) |
| `src/datatypes.py` | `Bullet` TypedDict — path, prompt, reference_urls, frames |
| `src/exceptions.py` | `AuthenticationError`, `ConfigurationError`, `ValidationError`, `PreflightExit` |
| `src/engine_contract.py` | `EngineInputFile` protocol + `validate_input_file()` — fail fast on contract mismatch |
| `src/engine_loader.py` | Vendored canonical `load_engine()` with `EngineLoadContext`; `copy_standby_profiles()` seeds only into an EMPTY `02.STANDBY/` (Q13) |
| `src/engine_helpers.py` | Discovery (`find_project/vehicle_engines_dir`), `auto_install_engine` (timeout=300), `build_inputs()` (video metadata + relative_dir), `load_engine_or_install`, `print_engine_not_found` |
| `src/auth/__init__.py` | 4-tier `get_api_key()` (env → pass → .env → AuthenticationError), `SUPPORTED_PLATFORMS`, interactive wizard (`_prompt_platform`, `_offer_engine_install`, `_prompt_and_save_key` → repo-root `.env`) |
| `src/auth/env.py` | `.env` loading (`get_api_token_from_env`) |
| `src/processing/bullet_parser.py` | `read_bullets()`, `parse_bullet()`, `validate_image_urls()` — prompt + URLs + `frames:`, `[]` on empty dir, markdown format warnings, HEAD validation skipped on dry-run (Q15) |
| `src/processing/profiles.py` | `load_profile_standalone()` (no STANDBY fallback), `load_profile_studiolot()`, `normalize_legacy_profile()`, `activate_profile()` |
| `src/processing/first_run.py` | `handle_first_run()` — engine check, TTY wizard, auto-install, STANDBY seed, auto-activate first STANDBY profile (Q2), non-TTY guidance |
| `src/utils/logging.py` | loguru + `_TeeStream` capture (encoding is a property) + `write_run_logs()` |
| `src/utils/path_resolver.py` | Timestamped output dirs `<YYMMDD_HHMMSS>_VID` (Q14) |

## Configuration

- Profiles: YAML files in `USER-FILES/03.PROFILES/` (production) or
  `USER-FILES/02.STANDBY/` (engine-seeded backup)
- Profile format: `platform`, `endpoint`, `parameters` (with `fps`, `duration`),
  `prompt_prefix`, `prompt_suffix`, `pricing`, `paths`
- API keys: `REPLICATE_API_TOKEN` env var (primary), also `FAL_KEY`,
  `OPENROUTER_API_KEY`, `GOOGLE_API_KEY` for multi-platform
- .env file: loaded from project root on startup (standalone mode)
- Interactive wizard saves keys to repo-root `.env`; called from
  `handle_first_run()` and as a fallback in `_run_standalone()`
- requirements.txt: only python-dotenv, loguru, PyYAML, rich — Engines vendor
  their own SDK deps (no replicate pin)
- `ENGINES/` is gitignored (vendored at runtime, separate repos)
- Legacy profiles with `Model`/`duration_config` blocks are auto-normalized by
  `normalize_legacy_profile()`

## Session History

### 2026-09-03 — Part 1: FC Parity (Cold-Start + File-Tree Alignment)
- Ported FC's zero-setup `run.py` venv lifecycle (repair broken venv, prefer 3.12/3.11/3.10/3)
- Re-vendored `engine_loader.py` with `EngineLoadContext` (TYPE_CHECKING annotation bug fixed);
  `copy_standby_profiles()` seeds only an empty STANDBY (Q13 — engine ships image profiles)
- Added `engine_contract.py` (InputFile protocol + `validate_input_file`), `datatypes.py`
  (Bullet), `exceptions.py` (PreflightExit/ConfigurationError), `constants.py`
  (DEFAULT_PLATFORM per Q3)
- Auth to FC parity: `get_api_key()` / `get_api_key_interactive()` rename (Q7),
  `SUPPORTED_PLATFORMS`, wizard saves repo-root `.env`, new `auth/env.py`
- Restructured `src/` to mirror FC: `processing/{bullet_parser,profiles,first_run}.py`,
  `engine_helpers.py`, `utils/{logging,path_resolver}.py`; deleted `input/`, `config/`,
  `execution/`, `parsing/` packages
- Behavior ports: `[]` on empty input dir, URL validation + format warnings (HEAD skipped
  on dry-run, Q15), `_apply_cli_overrides`, `_handle_preflight_checks` (video cost math Q6,
  PreflightExit), `relative_dir` mirroring, per-file `.log` via `_TeeStream`, animated rich
  progress, `{timestamp}_VID` output dirs (Q14), studiolot mkdir after preflight (Q16),
  auto-activate first STANDBY profile (Q2)
- requirements.txt: 4 deps only (Q4); pyproject.toml added (ruff/black/pytest)
- 34 tests ported (parser, engine_loader, auth, path_resolver) — all green, ruff clean
- Full cold-start verified end-to-end: venv rebuild → engine auto-install → profile
  auto-activate → dry-run exit 0; real engine load + InputFile construction verified
- `main_verbose.py` at 298 lines (over 250 soft limit, mirrors FC's `main_simple.py`; OK'd
  by R5's "thin entry" scope)

### 2026-08-05 — AGENTS.md rewrite
- Replaced legacy 1094-line documentation with modern FC-pattern AGENTS.md
- Added Architecture: Engine Interface section documenting Vehicle/Engine relationship
- Added Source File Map and CLI Modes sections
- Documented video-specific processing: InputFile.metadata, fps/duration, bullet frame override

### 2026-08-04 — Session 10: Cleanup Regressions + File Split
- Extracted `bullet_reader.py`, `profile_loader.py`, `pipeline.py` from `main_verbose.py`
- Main entry point reduced from 417 → 143 lines
- Added `PipelineContext` dataclass (1 param instead of 7 keyword-only args)
- Added timeout protection to git clone and pip install subprocess calls
- All files under 200-line soft limit — largest: `pipeline.py` at 183

### 2026-08-04 — Session 9: Refactoring Execution
- 14/15 tasks complete: dead code removal, dependency cleanup, auth rework
- `authenticate()` replaces `sys.exit()` with `AuthenticationError` exception
- `load_engine()` split from 75-line monolith into `_find_engine_dir()` +
  `_import_engine_package()` + `load_engine()` orchestrator
- Pipeline deduplication: `_summarize_results()`, `_create_engine()`,
  `_execute_pipeline()` extracted from both run modes
- `_read_bullets()` split: `_parse_bullet_md()` as pure single-file parser
- Legacy profile normalization extracted: `_normalize_legacy_profile()`
- Log filename changed: `replicate_wrapper` → `motion_conductor`

### 2026-08-04 — Engine Interface Migration (Phase 6)
- Converted from direct `import replicate` to Engine interface
- Vendored `engine_loader.py` from studiolot `pipeline/engine_loader.py`
- Added `--input_dir`, `--output_dir`, `--profile` CLI flags for studiolot mode
- Added `--install-default-engine` flag for standalone first-run UX
- Dead code (api/client.py, processing/processor.py, etc.) purged in Phase 12

---

## Known Issues & Technical Debt

### Remaining (2026-09-03)
- `build_inputs()` dynamically imports `engine_{platform}` — inherently fragile
  at module-load time (same issue as FC); the real engine package must already
  be on `sys.path` (via `load_engine()`)
- Real generation paths (animated progress, `engine.run`, payload save) are
  structurally FC-identical but only verified up to the API boundary — no
  live API run in this session
- `main_verbose.py` at 298 lines — over the 250 soft limit; mirrors FC's
  `main_simple.py` and holds at the 400 hard limit

### Resolved (Part 1)
- Test coverage: 34 tests added (parser, engine_loader, auth, path_resolver)
- `src/parsing/` empty directory deleted
- Flat `USER-FILES/05.OUTPUT/`: now timestamped `<YYMMDD_HHMMSS>_VID` run dirs
- `run.py` venv-missing error: now zero-setup bootstrap
- `replicate==1.0.4` pin removed; `rich` added for animated progress

### Resolved (Session 10)
- `main_verbose.py` god-file: 417 → 143 lines (split into 3 new modules)
- Pipeline parameter explosion: 7 keyword-only params → `PipelineContext` dataclass
- Auto-install timeout risk: added `timeout=300` to git clone and pip install
