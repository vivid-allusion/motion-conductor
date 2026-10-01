# Part 4 — M4: Implement the `reference_images` merge (VG)

> Scope: **VG code + tests**. Implements `GENERATOR_CONTRACT.md` §2f (the
> finding in handoff §1.3; Owner Q-3, in scope). Depends on Parts 1–3 for a real
> composed profile, but its tests use synthetic profiles.
> Repo: `/home/admin/APPLICATIONS/video-generator`. Commit in VG.

## Goal

In `src/engine_helpers.py::build_inputs`, merge the composed profile's
top-level `reference_images` list into each input — **after** the input's own
references — into the declared `reference_images` slot when the endpoint
declares one, else the primary input key; fail loud if it cannot route (never
silently drop).

## Requirements

### R1 — read the profile

Read `profile.get("reference_images")` (a list of remote URLs; absent when the
preset carries no media) and `profile.get("slots")` (the declared named slots,
a `list[str]`, the same value `read_markdown` already receives). A
missing/empty `reference_images` leaves today's behaviour unchanged.

### R2 — merge rule

For each input, the input's own Markdown references come first, then the
preset's `reference_images` are **appended**, in composed order. Do not
deduplicate or reorder.

### R3 — routing

- If `"reference_images"` is in the declared `slots` (and the Engine's
  `InputFile` accepts `references`) → append the preset URLs to that input's
  `references["reference_images"]` (after its own).
- Otherwise → append the preset URLs to the input's `reference_urls` (the
  primary input key).

### R4 — fail loud

If a `reference_images` value is present but cannot be routed (e.g. the
endpoint declares the `reference_images` slot but the Engine's `InputFile` does
not accept `references`), **raise or warn loudly** — never silently drop
(invariant 7; contract §2f). Follow the existing Q20 loud-warning path for
engines without the `references` kwarg; raise for a declared-but-unroutable
slot.

### R5 — boundaries

No new CLI flag; no preset parsing in VG; no change to the `InputFile`
datatype; `load_profile_studiolot` stays as-is.

### R6 — tests (`tests/test_engine_helpers.py`)

Add cases (keep existing tests green):

- (a) declared slot → `references["reference_images"]` ends with the preset URLs
  after the bullet's own;
- (b) no slot → `reference_urls` ends with the preset URLs;
- (c) Engine without the `references` kwarg + preset refs → the existing loud
  warning path fires.

### R7 — commit (VG)

Commit `src/engine_helpers.py` + `tests/test_engine_helpers.py` with a
conventional message; specific files only; never push.

## Verification

```bash
cd /home/admin/APPLICATIONS/video-generator
./venv/bin/python -m pytest tests/test_engine_helpers.py -q
./venv/bin/pip install ruff   # build installs ruff into ./venv; no pyproject/requirements change
./venv/bin/ruff check src/engine_helpers.py tests/test_engine_helpers.py
```

Expected: new + existing `test_engine_helpers.py` green; ruff clean. The full
suite is Part 5's gate.

## Not in this part

- Preset files / studiolot tests (Parts 1–3).
- Docs (Part 6).
