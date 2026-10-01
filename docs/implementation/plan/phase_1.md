# Part 1 — M1: Author the six camera-movement presets (studiolot)

> Scope: **six new `.preset` files + `presets.order`** in studiolot. No test or
> code changes (that is Part 2). Depends on nothing.
> Repo: `~/MISC/studiolot`. Commit in studiolot.

## Goal

Add six `media_type = "video"` preset files to studiolot's bundled default
preset directory and extend `presets.order` from 18 to 24 stems, so a
highlighted Video Generator instance lists exactly these six (today it lists
none). Content is the handoff §2 table, verbatim (the Owner rewords after the
build, Q-2).

## Requirements

### R1 — the six files

Create exactly these files under `console/studiolot/presets/`, each authored so
its bytes match `hc.presets.write_preset` output (header line
`# studiolot preset — TOML syntax`, then `name`, `media_type = "video"`,
`description`, `reference_media = ""`, `prefix`, `suffix`):

| File stem | `name` | `prefix` | `suffix` | `description` |
|---|---|---|---|---|
| `dolly-in` | Dolly in | Camera dollies in: a slow, steady physical push toward the subject, tightening the framing as the move develops. | Keep the move smooth and motivated; no zoom, no handheld drift. | Dolly in — the camera travels forward on a track, closing the distance to the subject. |
| `dolly-out` | Dolly out | Camera dollies out: a slow, steady physical pull back from the subject, opening the framing to reveal more of the scene. | Keep the move smooth and motivated; no zoom, no handheld drift. | Dolly out — the camera travels backward on a track, opening up the scene. |
| `dolly-left` | Dolly left | Camera dollies left: a smooth lateral track to the left, gliding past the subject while keeping it in frame. | Maintain a constant speed and a level horizon. | Dolly left — a lateral travelling move to the left on a moving camera. |
| `dolly-right` | Dolly right | Camera dollies right: a smooth lateral track to the right, gliding past the subject while keeping it in frame. | Maintain a constant speed and a level horizon. | Dolly right — a lateral travelling move to the right on a moving camera. |
| `handheld` | Handheld | Handheld camera: a loose, human-operated feel with subtle sway and small corrective adjustments, as if the operator is walking the shot. | Keep the framing readable — the motion should feel alive, not chaotic. | Handheld — an operator-carried camera with natural sway and micro-adjustments. |
| `orbit` | Orbit | Camera orbits the subject: a smooth circular move around it, holding the subject centred as the background rotates behind. | Maintain a constant distance and height through the full arc. | Orbit — a single continuous circular move around the subject. |

All six: `reference_media = ""` (Owner Q-4, words-only). Prefer generating the
files via `write_preset` (in-memory `Preset` → `write_preset(path, p)`) so the
byte format is canonical.

### R2 — `presets.order`

Append the six stems **after `photo-to-faux3d` and before `16-9-to-9-16`**, in
the order `dolly-in · dolly-out · dolly-left · dolly-right · handheld · orbit`.
Result: 24 stems; `order[0] == "txt-img-to-img"`;
`order[-3:] == ["16-9-to-9-16", "21-9-to-9-16", "9-16-to-16-9"]`. Use
`hc.presets.write_preset_order` (it preserves the file's shape).

### R3 — boundaries

Do not touch the 18 image presets. Do not add keys. Do not add parser code. Do
not touch tests (Part 2).

### R4 — commit (studiolot)

Commit the six `.preset` files + `presets.order` in `~/MISC/studiolot` with a
conventional message; specific files only; never `git add -A`; never push.

## Verification

```bash
cd /home/admin/MISC/studiolot
test -f console/studiolot/presets/dolly-in.preset
test -f console/studiolot/presets/dolly-out.preset
test -f console/studiolot/presets/dolly-left.preset
test -f console/studiolot/presets/dolly-right.preset
test -f console/studiolot/presets/handheld.preset
test -f console/studiolot/presets/orbit.preset
./.venv/bin/python -c "
from pathlib import Path
from hc.presets import read_preset, read_preset_order, preset_stem
d = Path('console/studiolot/presets')
want = {'Dolly in':'dolly-in','Dolly out':'dolly-out','Dolly left':'dolly-left',
        'Dolly right':'dolly-right','Handheld':'handheld','Orbit':'orbit'}
for name, stem in want.items():
    p = read_preset(d / f'{stem}.preset')
    assert p is not None and p.media_type == 'video' and p.prefix.strip() and p.suffix.strip(), stem
    assert p.description.strip(), stem
    assert preset_stem(p.name) == stem, (p.name, stem)
    assert p.reference_media == '', stem
order = read_preset_order(d)
assert len(order) == 24, len(order)
assert order[0] == 'txt-img-to-img'
assert order[-3:] == ['16-9-to-9-16', '21-9-to-9-16', '9-16-to-16-9']
assert list(want.values()) == order[15:21], order[15:21]
print('OK six presets + order')
"
# round-trip a shipped camera preset (description carried) — handoff §6 (1)
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

Expected: `OK six presets + order` and `OK round-trip dolly-in dolly-in`.
(The `order[15:21]` slice assumes the six land after the 15 image stems and
before the aspect trio; confirm against `presets.order` and adjust the slice if
the authored order differs — the three invariants above are the hard gate.)

## Not in this part

- Test amendments (Part 2).
- A durable schema-proof test (Part 3).
- Any VG change (Parts 4–6).
