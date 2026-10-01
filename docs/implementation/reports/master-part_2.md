# Part report — phase_2.md

> Per-unit report (PLAN §4.4), written by `/part-close` from actual gate and verifier results — never from memory.

- **Status:** DONE
- **Part:** phase_2.md (`phase_2.md` filename, or ticket id `Pn`)
- **Date:** 2026-10-01T18:48:00Z
- **Repo / branch:** /home/admin/APPLICATIONS/video-generator · master
- **Commit:** — (this close commit)

## Gate results

| Gate | Exact command | Exit | Result |
|---|---|---|---|
| Unit `## Verification` | `./.venv/bin/python -m pytest tests/test_default_presets.py tests/test_project_init_scaffold.py -q` + `./.venv/bin/ruff check <those two files>` | 0 | pass (15 passed in 1.20s; All checks passed!) |
| Resolver `verify=` | `./venv/bin/python -m pytest tests/` | 0 | pass (85 passed in 0.33s) |
| Resolver `lint=` | `./venv/bin/ruff check` | 0 | pass (All checks passed!) |
| File-size scan | `wc -l` over changed files | — | breaches: none (no changed `.py` in VG; the two studiolot test files are 195/145 lines, < 250) |

## Verifier verdict

`VERDICT: APPROVE`

- R1 (`tests/test_default_presets.py`): MET — adds `VIDEO_STEMS`; renames to `test_exactly_twenty_four_default_presets` asserting `len(files)==24` plus an 18/6 media split; `test_every_default_parses_with_invariants` pins `media_type` per stem and scopes `suffix` (video non-empty, image `""`), keeping stem-regex/prefix/description checks for all 24; order test now `len(order)==24`.
- R2 (`tests/test_project_init_scaffold.py`): MET — both tests assert `copied == 24`; the explicit `names == [...]` list gains the six video files; the parse loop branches per `_VIDEO_NAMES` (`media_type=="video"` + non-empty suffix) and keeps `media_type=="image"` + `suffix==""` for the rest; first/last-three assertions unchanged.
- R3 (boundaries): MET — diff hunks touch only the two test files; no parser, `hc/`, or `console/` edits.
- R4 (commit in studiolot): MET — `705a128` "test(presets): amend default and scaffold suites to 24 presets (W98 M2)", 2 files / +54 −10, specific files only, no push.
- Acceptance criterion 2 (amend not relax, W212): MET — strict per-media assertions added; no assertion deleted, no xfail/skip introduced.
- MUST-FIX: none

## Evidence per acceptance criterion

- 24-preset assertion with pinned 18/6 split: `assert len(files) == 24`, `len(stems & IMAGE_STEMS) == 18`, `len(stems & VIDEO_STEMS) == 6`, `stems == IMAGE_STEMS | VIDEO_STEMS` → `15 passed`.
- Per-media checks pinned, not relaxed: diff shows `media_type` switched from a blanket `== "image"` to per-stem branching and `suffix == ""` scoped to image stems with a new non-empty-suffix check for video stems.
- Scaffold copy list complete: `names == [...]` now lists all 24 including `dolly-in.preset` … `orbit.preset`; `copied == 24` in both copy tests → `15 passed`.
- No unrelated edits: `git show 705a128 --stat` = 2 files, both tests.
- VG gate untouched/green: `./venv/bin/python -m pytest tests/` → `85 passed in 0.33s`; `./venv/bin/ruff check` → `All checks passed!`.
- Studiolot tree clean after commit: `git status --porcelain` empty.

## Carried forward

- none

## Next pointer

- `phase`: `phase_3.md`
- Next unit Verification (Part 3, studiolot): `./.venv/bin/python -m pytest tests/test_preset_reference_media.py tests/test_app_profile_compose.py -q` and `./.venv/bin/ruff check tests/`, plus the handoff §6 shipped round-trip proof → expect all green and `OK round-trip dolly-in dolly-in`.
