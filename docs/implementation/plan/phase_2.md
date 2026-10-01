# Part 2 — M2: Amend the shipped-default and scaffold tests (studiolot)

> Scope: **tests only**, studiolot. Amend, never blanket-relax (W212).
> Depends on Part 1. Repo: `~/MISC/studiolot`. Commit in studiolot.

## Goal

Bring the shipped-default and project-init scaffold tests from the image-only
18-preset world to the 24-preset world (18 image + 6 video), keeping every
strict per-media check.

## Requirements

### R1 — `tests/test_default_presets.py`

- Add a `VIDEO_STEMS = {"dolly-in", "dolly-out", "dolly-left", "dolly-right",
  "handheld", "orbit"}` set; keep `AUTHORED_STEMS` as the image stems.
- `test_exactly_eighteen_default_presets` → assert **24** total and pin the
  media split (18 image, 6 video); rename the test to match (e.g.
  `test_exactly_twenty_four_default_presets`) and update any reference.
- `test_every_default_parses_with_invariants` → pin `media_type` **per stem**
  (image stems → `"image"`, the six video stems → `"video"`); keep the
  `^[a-z0-9-]+$` stem, non-empty `prefix`, and non-empty `description` checks
  for all 24. Scope the existing `assert preset.suffix == ""` to image stems
  (the six video presets carry a non-empty `suffix`); assert video stems have a
  non-empty `suffix`. Do not drop the check.
- `test_shipped_preset_order_lists_all_stems_once` → `len(order) == 24`.
- `test_shipped_preset_order_none_first_aspect_last` → first/last-three
  invariants unchanged (no count change needed).
- `test_no_unknown_keys`, `test_authored_stems_present`,
  `test_costume_sheet_present_and_marked_placeholder` stay green unchanged.

### R2 — `tests/test_project_init_scaffold.py`

- `test_copy_default_presets_copies_shipped_files` → `copied == 24`; extend the
  explicit `names == [...]` list with the six video files; keep
  `media_type == "image"` for the 18 image files and assert
  `media_type == "video"` for the six, scoped (do not replace the image
  assertion with a blanket one). Scope `suffix == ""` to image files; assert
  the video files have a non-empty `suffix`.
- `test_copy_default_presets_ships_order_sidecar` → `copied == 24`;
  first/last-three assertions unchanged.

### R3 — boundaries

No new parsing code. No edits to `hc/` or `console/`. No unrelated test edits.

### R4 — commit (studiolot)

Commit the two test files with a conventional message; specific files only;
never push.

## Verification

```bash
cd /home/admin/MISC/studiolot
./.venv/bin/python -m pytest tests/test_default_presets.py tests/test_project_init_scaffold.py -q
./.venv/bin/ruff check tests/test_default_presets.py tests/test_project_init_scaffold.py
```

Expected: all green; ruff clean. The image-only assertions must still be
present and passing for the 18 image stems (not removed).

## Not in this part

- New preset files (Part 1).
- A durable schema-proof test (Part 3).
- Any VG change.
