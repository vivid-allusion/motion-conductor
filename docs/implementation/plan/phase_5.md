# Part 5 — M5: Full suites + lint per repo

> Scope: **gates only**. Depends on Parts 1–4. Repos: VG + studiolot.

## Goal

Hold both baselines with all W98 changes in place: VG suite green (baseline 85
passed) + ruff clean; studiolot suite green (baseline 2034 passed / 24 skipped)
+ ruff clean.

## Requirements

### R1 — VG gate

```bash
cd /home/admin/APPLICATIONS/video-generator
./venv/bin/python -m pytest tests/
./venv/bin/ruff check
```

Expected: all green (≥85 passed); ruff clean. If ruff is missing, install it
into `./venv` (`./venv/bin/pip install ruff`) — no `pyproject.toml`/
`requirements.txt` change.

### R2 — studiolot gate

```bash
cd /home/admin/MISC/studiolot
./.venv/bin/python -m pytest tests/
./.venv/bin/ruff check .
```

Expected: all green (≥2034 passed / 24 skipped); ruff clean. Re-confirm the
head baseline before/after; zero new failures.

### R3 — fixes

If a gate fails, fix the owning repo (studiolot or VG), re-run both gates, and
commit the fix in that repo (specific files, conventional message).

### R4 — commit (VG, if any)

If this part changed VG files, commit them; otherwise record the green gates in
the unit report and commit nothing.

### R5 — VG lint baseline

`./venv/bin/ruff check` is **not** clean on the untouched tree: three
pre-existing `I001` import-order violations fail the gate, and no earlier part
owns `run.py` or `src/main_verbose.py`, so the plan cannot go green as
scaffolded. Making VG's lint clean is **in scope for this unit** (mechanical
import reordering only, zero behaviour change):

- `run.py` — sort the stdlib imports (`shutil`, `subprocess`, `sys`).
- `src/engine_helpers.py` — the relative imports: `from .constants import
  MEDIA_TYPE` belongs before `.datatypes`.
- `src/main_verbose.py` — `from .processing.first_run import handle_first_run`
  belongs before `.processing.markdown_parser`.

```bash
cd /home/admin/APPLICATIONS/video-generator
./venv/bin/ruff check --fix
./venv/bin/ruff check
```

Acceptance: the bare re-run exits **0 with no findings**. No `pyproject.toml`/
`requirements.txt` change.

**Commit:** the three files (`run.py`, `src/engine_helpers.py`,
`src/main_verbose.py`) with a conventional message, specific paths only, in the
VG repo.

## Verification

```bash
cd /home/admin/APPLICATIONS/video-generator && ./venv/bin/python -m pytest tests/ -q && ./venv/bin/ruff check
cd /home/admin/MISC/studiolot && ./.venv/bin/python -m pytest tests/ -q && ./.venv/bin/ruff check .
```

## Not in this part

- New feature code.
- Docs (Part 6).
