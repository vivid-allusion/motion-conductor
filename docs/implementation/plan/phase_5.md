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

### R5 — VG lint baseline (verify only)

VG's lint baseline was repaired before the run: `b3f6d31` sorts the three
pre-existing `I001` import-order violations (`run.py`,
`src/engine_helpers.py`, `src/main_verbose.py`). That is baseline repair, not
plan work — no further change is expected here.

```bash
cd /home/admin/APPLICATIONS/video-generator
./venv/bin/ruff check
```

Acceptance: the command exits **0 with no findings**. If it fails, fix only
findings introduced by this plan's own changes — never broaden scope, never
edit `pyproject.toml`/`requirements.txt`. Commit only if this part changed
files (specific paths, conventional message, VG repo).

## Verification

```bash
cd /home/admin/APPLICATIONS/video-generator && ./venv/bin/python -m pytest tests/ -q && ./venv/bin/ruff check
cd /home/admin/MISC/studiolot && ./.venv/bin/python -m pytest tests/ -q && ./.venv/bin/ruff check .
```

## Not in this part

- New feature code.
- Docs (Part 6).
