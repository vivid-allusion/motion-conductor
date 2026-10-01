# Part 6 — M6: Docs / history (VG)

> Scope: **VG docs only**. Depends on Parts 1–5. Repo: VG. Commit in VG.

## Goal

Record the W98 outcome and refresh stale preset prose.

## Requirements

### R1 — `docs/HISTORY.md`

Add a W98 section recording the plan outcome: the six video presets +
`presets.order` (18→24) + the shipped-default/scaffold test amendments in
studiolot; the `reference_images` merge (`GENERATOR_CONTRACT.md` §2f) in VG; the
cross-repo commit model; and the closure path
(`~/PLATFORM/theia-platform/docs/handoffs/W98-mc-camera-presets-closure.md`).

### R2 — stale prose

If `README.md` or `CONTRIBUTING.md` carries a stale preset-schema line (the old
four-field shape / `cinematic.preset` / `aisl/*`), refresh it (the presets are
studiolot-owned; the schema is W95). If no stale line is found, state that in
the HISTORY entry instead.

### R3 — boundaries

Doc-only. No code change. The suite must still be green.

### R4 — commit (VG)

Commit `docs/HISTORY.md` (+ `README.md`/`CONTRIBUTING.md` if changed) with a
conventional message; specific files only; never push.

## Verification

```bash
cd /home/admin/APPLICATIONS/video-generator
grep -n "W98" docs/HISTORY.md
./venv/bin/python -m pytest tests/ -q
```

Expected: the W98 section is present; suite green.

## Not in this part

- Any code change.
- Closure publication (the closure doc lives outside this repo).
