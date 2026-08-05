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
  → read_bullets()                # parse .md input files (prompt + URLs + frames)
  → load_profile_standalone()     # from USER-FILES/03.PROFILES/ or 02.STANDBY/
  → authenticate()                # 4-tier auth (env → pass → .env → error)
  → find_vehicle_engines_dir()    # look in <vehicle-root>/ENGINES/
  → execute_pipeline()            # discover engine, load, build inputs, run
    → find_project_engines_dir()  # walk up looking for 00_APPLICATIONS/ENGINES/
    → load_engine()               # import engine_<platform> package
    → build_inputs()              # construct InputFile objects with metadata
    → engine.run(inputs)          # bulk video generation
```

Studiolot mode:
```
main() → _run_studiolot()
  → read_bullets()
  → load_profile_studiolot()      # from --profile path
  → authenticate()
  → execute_pipeline()
    → find_project_engines_dir()  # walk up from --output_dir
    → load_engine()
    → build_inputs()
    → engine.run(inputs)
```

### Video-Specific Input
- Bullet files carry `frames: N` optional override (line-parsed via `_FRAMES_RE`)
- `build_inputs()` reads `fps` and `duration` from profile `parameters` block
- Each `InputFile.metadata` = `{"duration": float, "fps": int}`
- Per-bullet `frames:` override converts to duration = frames / fps
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
| `run.py` | Bootstrap: venv detection, launches `src/main_verbose.py` from repo root |
| `src/main_verbose.py` | Entry point, CLI routing, both run modes, error handling |
| `src/cli.py` | argparse definition — `--input_dir`, `--output_dir`, `--profile`, `--dry-run`, `--debug`, `--install-default-engine` |
| `src/engine_loader.py` | Canonical `load_engine()` — vendored from studiolot `pipeline/engine_loader.py` |
| `src/auth/__init__.py` | 4-tier API key resolution (env → pass → .env → AuthenticationError) |
| `src/execution/pipeline.py` | `PipelineContext` dataclass, `execute_pipeline()`, engine discovery (`find_project_engines_dir`), installation (`auto_install_engine`), `build_inputs()` |
| `src/input/bullet_reader.py` | `read_bullets()`, `_parse_bullet_md()` — prompt + image URLs + frame count extraction |
| `src/config/profile_loader.py` | `load_profile_standalone()`, `load_profile_studiolot()`, `normalize_legacy_profile()` — legacy `Model`/`duration_config` → Engine-interface key mapping |
| `src/utils/logging.py` | loguru setup with `CONSOLE_FORMAT`/`FILE_FORMAT` — optional project-name log prefix |

---

## Configuration

- Profiles: YAML files in `USER-FILES/03.PROFILES/` (production) or
  `USER-FILES/02.STANDBY/` (engine-seeded backup)
- Profile format: `platform`, `endpoint`, `parameters` (with `fps`, `duration`),
  `prompt_prefix`, `prompt_suffix`, `pricing`, `paths`
- API keys: `REPLICATE_API_TOKEN` env var (primary), also `FAL_KEY`,
  `OPENROUTER_API_KEY`, `GOOGLE_API_KEY` for multi-platform
- .env file: loaded from project root on startup (standalone mode)
- Legacy profiles with `Model`/`duration_config` blocks are auto-normalized by
  `normalize_legacy_profile()`

## Session History

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

### Remaining (2026-08-05)
- No test files exist in the repo — zero test coverage
- `src/parsing/` directory is empty (leftover from pre-migration era) — safe to delete
- `build_inputs()` dynamically imports `engine_{platform}` — inherently fragile
  at module-load time (same issue as FC)

### Resolved (Session 10)
- `main_verbose.py` god-file: 417 → 143 lines (split into 3 new modules)
- Pipeline parameter explosion: 7 keyword-only params → `PipelineContext` dataclass
- Auto-install timeout risk: added `timeout=300` to git clone and pip install
