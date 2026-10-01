# Part 3 — M3: Schema round-trip proof + durable lock (studiolot)

> Scope: **prove and lock** the W95 schema capability the work order relies on;
> no schema change. Depends on Part 1. Repo: `~/MISC/studiolot`. Commit in
> studiolot.

## Goal

Reproduce the handoff §6 schema proof (round-trip a shipped camera preset; an
embedded reference-image fixture; `compose_profile` emits/omits
`reference_images`) and encode it as a regression test so the capability cannot
silently regress.

## Requirements

### R1 — reproduce the handoff §6 proof

Run the three proof one-liners from the handoff §6 (the "Schema proof" block)
and capture the output for the closure:

1. round-trip a shipped camera preset (`read_preset(write_preset(p)) == p`,
   `description` carried);
2. embedded reference-image round-trip on a throwaway fixture (**not**
   shipped): `extract_reference_media` splits a plain URL + a Markdown embed,
   in authored order;
3. `compose_profile` emits `reference_images` in authored order for a
   media-bearing preset and omits it — and `description` — for an empty one.

Expected output includes `OK round-trip dolly-in`, `OK round-trip embedded
reference image`, `OK compose reference_images`.

### R2 — durable regression test

Add `tests/test_preset_reference_media.py` (or extend
`tests/test_default_presets.py` if that is the better home — pick one, do not
duplicate):

- every shipped camera preset round-trips: `read_preset(write_preset(tmp/p)) ==
  p` (`tmp_path` only);
- the six shipped video presets are `media_type == "video"` and stem-safe;
- `compose_profile` emits `reference_images` in authored order for a
  media-bearing `Preset` and omits it (and `description`) for an empty one.

No network. Reuse the existing `tests/test_app_profile_compose.py` patterns
where they fit; do not duplicate existing coverage verbatim.

### R3 — boundaries

No change to `hc/presets.py` or `hc/profiles.py`; no new schema key; consume the
W95 schema as-is.

### R4 — commit (studiolot)

Commit the new/extended test with a conventional message; specific files only;
never push.

## Verification

```bash
cd /home/admin/MISC/studiolot
./.venv/bin/python -m pytest tests/test_preset_reference_media.py tests/test_app_profile_compose.py -q
./.venv/bin/ruff check tests/
# handoff §6 proof (1): shipped round-trip
./.venv/bin/python -c "
from pathlib import Path
from hc.presets import read_preset, write_preset, preset_stem
import tempfile
p = read_preset(Path('console/studiolot/presets/dolly-in.preset'))
assert p is not None and p.media_type == 'video' and p.description, p
with tempfile.TemporaryDirectory() as d:
    f = Path(d)/'x.preset'; write_preset(f, p)
    assert read_preset(f) == p
    print('OK round-trip dolly-in', preset_stem(p.name))
"
```

Expected: all green; the proof prints `OK round-trip dolly-in dolly-in`.

## Not in this part

- Authoring the presets (Part 1).
- The VG `reference_images` merge (Part 4).
