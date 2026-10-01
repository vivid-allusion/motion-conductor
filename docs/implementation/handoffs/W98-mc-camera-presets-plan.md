# W98 — Video Generator camera-movement presets (plan)

> **Planning pass.** No code edits, no `.preset` files, no commits, no pushes were
> made to produce this document. Written 2026-10-01.
> **Target repo (per the work order):** `~/APPLICATIONS/video-generator` (VG).
> **Schema dependency:** **W95 has landed** (studiolot) — the `.preset` schema
> already carries `description` and `reference_media`, so this plan does **not**
> wait. Recorded studiolot `master` head inspected: `7510773` (W6 `phase_8`).
> **W6 vocabulary note applied:** the headless core package `aisl/` is now
> `hc/` (dist `h-core`); `aisl/presets.py` → `hc/presets.py`, and
> `console/studiolot/preset_file.py` is a re-export aggregator over it.
> **Source issue:** `vivid-allusion/video-generator` #2 ("Feature: camera-movement
> prompt presets …", board "Video Generator (VG)"). Queue item:
> `~/INFRA/loops-and-goals-mgmt/queue/items/W98-mc-camera-presets.md`.
> **Closure (when built):** `~/PLATFORM/theia-platform/docs/handoffs/W98-mc-camera-presets-closure.md`.
>
> **Answered by the Owner, 2026-10-01 — "all three as recommended":** W98 is a
> **cross-repo** work order (Q-1 confirmed: the six `.preset` files + `presets.order`
> + test amendments land in studiolot; VG carries the `reference_images` merge +
> docs); **M4 (`reference_images` merge) is in scope** (Q-3); the six ship
> **words-only**, `reference_media = ""` (Q-4). §7 is now the answered record and
> §5 M4 is unconditional. The Owner's wording pass over the §2 strings happens
> **after** the build (Q-2), so the build starts from the §2 content unchanged.

---

## 0. Corrections to the work order's premises (read this first)

The plan is written from a direct read of both trees. Six premises are corrected
or sharpened; two of them change **where the work lands**.

1. **The schema path is `hc/presets.py`, not `aisl/presets.py`.** W6 renamed the
   core package (`aisl` → `hc`). `console/studiolot/preset_file.py` is a
   re-export aggregator; the schema and `_KNOWN_KEYS` live in
   `~/MISC/studiolot/hc/presets.py`. W95 already landed both new keys there
   (`_KNOWN_KEYS = {name, media_type, prefix, suffix, description,
   reference_media}`).
2. **"Dash" is the studiolot app; the panel is a Textual `PresetsPanel`.** There
   is no Dash/Dash-plotly code. `console/studiolot/presets.py::PresetsPanel.
   set_presets(preset_dir, media_type)` is the filter;
   `console/studiolot/app/highlights.py::on_generator_highlighted` feeds it the
   selected app's media type.
3. **The example file `console/studiolot/presets/cinematic.preset` no longer
   exists.** W95 replaced the shipped four (`vanilla`/`photoreal`/`cinematic`/
   `clean-sheet`) with **18 image defaults**. Use any of the current 18 (e.g.
   `costume-sheet.preset`) for the file shape.
4. **The shipped defaults are all `media_type = "image"`.** There is no video
   preset anywhere today (`grep -c 'media_type = "video"'` in the shipped dir →
   `0`). The panel filters by media type, so today a highlighted Video Generator
   sees an **empty** CONCAT PRESETS list. W98 is what fills it.
5. **W95 is not just the schema — it is also the preset *home*.** The 18 image
   defaults live in **studiolot** (`console/studiolot/presets/`), are seeded into
   a project's `00_APPLICATIONS/CONFIG/PRESETS/` by
   `console/studiolot/screens/project_init/scaffold.py::copy_default_presets`,
   and are read/filtered by the panel. "Mirror IG" therefore means: author the
   video defaults in **studiolot's bundled default set**, not in VG.
6. **VG (and IG) carry zero preset code** — proven, not assumed:
   `grep -rni preset src/ tests/` → **0** in each repo; the only hits anywhere are
   prose in `ARCHITECTURE.md`/`CONTRIBUTING.md`. So "if IG does none, VG must do
   none" resolves to: **the camera presets add no VG preset code.**

A seventh, load-bearing correction is a **finding**, not a premise fix: see §1.3 —
VG does not yet implement the W95/GENERATOR_CONTRACT §2f `reference_images`
merge, so a preset that embeds media would have its media silently dropped today.
The work order's stop condition ("VG consumes presets through a path that cannot
carry … media → stop and surface it") fires on exactly this point. It is
surfaced in §1.3, §4.4 and §7; it is **not** a blocker for the six presets as
proposed in §2 (all six ship prose-only), but it is contract-mandated once any
preset carries an asset.

---

## 1. Decision record (the two §3 questions)

### 1.1 Q1 — Do the camera presets land in VG's repo, or in studiolot?

**Decision: in studiolot's bundled default preset directory** —
`~/MISC/studiolot/console/studiolot/presets/` — as six `media_type = "video"`
`.preset` files, exactly the way IG's 18 image defaults ship. VG's repo holds no
preset files.

**Code evidence (all read at plan time):**

| Fact | Evidence |
|---|---|
| A project has **one** PRESETS directory, shared by all generators | `hc/profiles.py::resolve_preset_dir` → `<project>/00_APPLICATIONS/CONFIG/PRESETS/`; `PRESETS_DIR_NAME = "PRESETS"` |
| Presets are **studiolot-owned** files, not generator-owned | `console/studiolot/preset_file.py` re-exports the canonical `hc.presets` reader/writer; `GENERATOR_CONTRACT.md` §2f calls preset media "composed … in studiolot" |
| The shipped defaults are seeded from **studiolot package data** | `screens/project_init/scaffold.py::copy_default_presets` reads `resources.files("studiolot") / "presets"` and copies every `*.preset` + `presets.order` into the project |
| The panel **filters by the selected app's media type** | `app/highlights.py:31-34` → `media_type_for_generator(app_def.tool)`; `presets.py:58-67` keeps only `preset.media_type == media_type` |
| `video-generator` maps to `video` | `hc/constants.py::GENERATOR_MEDIA_TYPES = {…, "video-generator": "video", "vg": "video"}`; `screens/app_wizard/constants.py::media_type_for_generator` delegates to it |
| IG ships **no** preset code in its own repo (the mirror target) | `grep -rni preset src/ tests/` in `~/APPLICATIONS/image-generator` → **0** |
| VG ships **no** preset code either | same grep in `~/APPLICATIONS/video-generator` → **0** |

**Consequence:** the six preset files are a **studiolot** commit (a W95
follow-on in spirit, carried by W98 per W95 plan §5.6). VG is touched only for
the profile-level `reference_images` merge (§1.3), which is generator code, not
preset machinery.

> **Answered (Owner, 2026-10-01 — Q-1 confirmed):** the work order names
> `video-generator` as the target repo, but by the settled shape the preset
> *files* land in `studiolot`. W98 is therefore a **cross-repo** work order
> (studiolot: 6 preset files + `presets.order` + test amendments; VG: plan +
> `reference_images` merge). This is the same split W95 plan §5.6 recommended
> ("motion-conductor wiring → fold into W98"). The closure records both repos.

### 1.2 Q2 — How does VG consume a camera preset?

**Decision: via the composed `--profile`; VG parses no preset.** studiolot's
`hc/profiles.py::compose_profile(app_def, preset)` emits a flat profile with
`prompt_prefix = preset.prefix`, `prompt_suffix = preset.suffix`, and
`media_type = "video"`; the Dash spawn lands it at
`00_APPLICATIONS/CONFIG/generated/<instance>.yaml` and passes it via `--profile`.
VG's existing pipeline consumes it unchanged:

- `src/processing/profiles.py::load_profile_studiolot` reads the YAML;
- `src/main_verbose.py` wraps each Markdown prompt as
  `{prefix} {original} {suffix}` via the engine (unchanged contract);
- `description` is **never** composed into the profile (W95 guard:
  `tests/test_app_profile_compose.py` asserts `description`/`reference_media`
  never appear), so VG never sees it. Correct — description is author-facing.

So "mirror IG" holds a second time: IG's repo has no preset code, and the
composition path is entirely studiolot-side. **VG adds no preset parsing,
no preset directory, no `--preset` flag.**

### 1.3 Finding — the `reference_images` transport is unimplemented in VG

`GENERATOR_CONTRACT.md` §2f (landed W95 M6) requires a Generator to merge the
composed profile's top-level `reference_images` list into each input (declared
`slots` → that slot, else `image_url_param`) and to **fail loud** rather than drop
it. Today:

- `hc/profiles.py::compose_profile:122-123` **does** emit
  `profile["reference_images"] = extract_reference_media(preset.reference_media)`
  when a preset carries media.
- VG's `src/engine_helpers.py::build_inputs` reads only `profile["parameters"]`
  and each Markdown file's own `references`; it never reads
  `profile["reference_images"]`. So a preset's embedded media is **silently
  dropped** by VG. The same gap exists in IG today (W209 owns the FC half).
- The work order's stop condition ("a path that cannot carry … media") therefore
  **fires**: VG cannot yet carry preset media.

**Disposition in this plan:** the six presets proposed in §2 ship
**`reference_media = ""`** (prose-only), and the contract-mandated
`reference_images` merge is **in scope** as §5 **M4** (Owner, 2026-10-01 — Q-3),
mirroring W95 plan §5.3's MC design. No silent drop remains for the shipped six,
and no field is dropped by design: `description` is author-facing by contract,
and `reference_media` is empty.

---

## 2. Preset inventory table (all fields filled — review table)

Six presets, one per Owner-scoped movement. The composed prompt is
`"{prefix} {markdown_prompt} {suffix}"`, so the `prefix` names the move and the
`suffix` carries a stability/consistency clause. Prose is worker-improvised
(Owner rewords afterwards). Display names use the Owner's names; the issue's
"Truck left / right" is realised as the Owner's "Dolly left / right".

| # | Display `name` | file stem / id | `prefix` (proposed) | `suffix` (proposed) | `description` (proposed) | reference media |
|---|---|---|---|---|---|---|
| 1 | Dolly in | `dolly-in` | Camera dollies in: a slow, steady physical push toward the subject, tightening the framing as the move develops. | Keep the move smooth and motivated; no zoom, no handheld drift. | Dolly in — the camera travels forward on a track, closing the distance to the subject. | empty (not needed) |
| 2 | Dolly out | `dolly-out` | Camera dollies out: a slow, steady physical pull back from the subject, opening the framing to reveal more of the scene. | Keep the move smooth and motivated; no zoom, no handheld drift. | Dolly out — the camera travels backward on a track, opening up the scene. | empty (not needed) |
| 3 | Dolly left | `dolly-left` | Camera dollies left: a smooth lateral track to the left, gliding past the subject while keeping it in frame. | Maintain a constant speed and a level horizon. | Dolly left — a lateral travelling move to the left on a moving camera. | empty (not needed) |
| 4 | Dolly right | `dolly-right` | Camera dollies right: a smooth lateral track to the right, gliding past the subject while keeping it in frame. | Maintain a constant speed and a level horizon. | Dolly right — a lateral travelling move to the right on a moving camera. | empty (not needed) |
| 5 | Handheld | `handheld` | Handheld camera: a loose, human-operated feel with subtle sway and small corrective adjustments, as if the operator is walking the shot. | Keep the framing readable — the motion should feel alive, not chaotic. | Handheld — an operator-carried camera with natural sway and micro-adjustments. | empty (not needed) |
| 6 | Orbit | `orbit` | Camera orbits the subject: a smooth circular move around it, holding the subject centred as the background rotates behind. | Maintain a constant distance and height through the full arc. | Orbit — a single continuous circular move around the subject. | empty (not needed) |

**Reference-media decision (per row):** none of the six **requires** a reference
asset — a camera movement is described in prose and the model already receives the
Markdown file's start image. Two independent reasons reinforce "ship empty":

1. **Transport semantics.** Preset `reference_media` composes to the top-level
   `reference_images` key (`GENERATOR_CONTRACT.md` §2f) — an *image*-typed slot on
   the live video endpoints. A camera-movement reference would more naturally be a
   **video clip**, for which no transport precedent exists — the work order's
   explicit stop condition ("a camera movement needs a reference video and no
   precedent exists for video references → stop and ask the Owner"). No movement
   *needs* one, so we do not invent one.
2. **No invented assets.** Shipping a placeholder URL would be a dead reference;
   the W95 costume-sheet precedent shows placeholders are only used to reserve a
   slot the Owner then fills. Here the slot is genuinely unnecessary.

The **schema round-trip proof in §6 still exercises an embedded reference image**
on a throwaway fixture (not a shipped preset), so the plan demonstrates the full
schema capability the work order asks for, without shipping a fake asset.

> All six are **out-of-scope-free**: they are exactly the Owner's six; the other
> ten movements on issue #2 stay open and are not touched.

---

## 3. Naming / filename safety (the id becomes a filename)

The on-disk identity is `hc.presets.preset_stem(name)`, which lowercases and
collapses every non-`[a-z0-9]` run to `-`: `re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")`.
`write_preset` additionally **rejects** `/` and `\` in `name`. So the only
characters that ever reach a filename are `[a-z0-9-]`.

| Display name (as typed) | Chars to flag | Safe stem (`preset_stem`) | Collides with an existing stem? |
|---|---|---|---|
| `Dolly in` | space, mixed case | `dolly-in` | no |
| `Dolly out` | space, mixed case | `dolly-out` | no |
| `Dolly left` | space, mixed case | `dolly-left` | no |
| `Dolly right` | space, mixed case | `dolly-right` | no |
| `Handheld` | mixed case | `handheld` | no |
| `Orbit` | mixed case | `orbit` | no |

- **No `/` and no `:`** appear in any of the six (the issue's "Truck left / right"
  is *not* used — the Owner's "Dolly left/right" replaces it — so the `/` trap the
  work order names **does not arise**). For reference, the trap case is handled
  anyway by the slug: a hypothetical "Tracking / follow shot" →
  `tracking-follow-shot`.
- Every stem matches `^[a-z0-9-]+$` (the assertion the shipped-default tests
  already enforce for the 18 image presets).
- Stems are unique against the 18 existing image stems (`grep` of
  `console/studiolot/presets/*.preset` stems confirms no overlap).

**Decision (no Owner input required):** display `name` is preserved verbatim
(spaces/case kept, it is the panel label); the stem is `preset_stem(name)`. This
is exactly the W212/W95 convention (display name ≠ stem where the Owner orders
it), so no new mechanism is introduced.

---

## 4. Where they land (exact paths) and how they are listed

### 4.1 studiolot — the shipped camera presets (six files + order)

```
~/MISC/studiolot/console/studiolot/presets/dolly-in.preset
~/MISC/studiolot/console/studiolot/presets/dolly-out.preset
~/MISC/studiolot/console/studiolot/presets/dolly-left.preset
~/MISC/studiolot/console/studiolot/presets/dolly-right.preset
~/MISC/studiolot/console/studiolot/presets/handheld.preset
~/MISC/studiolot/console/studiolot/presets/orbit.preset
~/MISC/studiolot/console/studiolot/presets/presets.order        # 18 → 24 stems
```

File shape (exact, `hc.presets.write_preset` order — see §6 for one full file):
`# studiolot preset — TOML syntax`, `name`, `media_type = "video"`,
`description`, `reference_media = ""`, `prefix`, `suffix`.

**`presets.order` placement:** append the six video stems **after
`photo-to-faux3d` and before the three aspect-ratio stems**, so:

- the image panel's visible order is unchanged (the video stems are filtered out
  for image generators), and
- the shipped-order invariant `order[0] == "txt-img-to-img"` and
  `order[-3:] == ["16-9-to-9-16", "21-9-to-9-16", "9-16-to-16-9"]` (asserted by
  `tests/test_default_presets.py`) still holds.

The video panel's visible order then reads, top to bottom:
`dolly-in · dolly-out · dolly-left · dolly-right · handheld · orbit`.

### 4.2 How the files reach a project

`copy_default_presets` (`screens/project_init/scaffold.py`) copies **every**
`*.preset` plus `presets.order` from studiolot package data into
`<project>/00_APPLICATIONS/CONFIG/PRESETS/` at project scaffold time. No code
change is needed for the seed path (it is data-driven). `pyproject.toml`
package-data already carries `presets/*.preset` and `presets/*.order`.

### 4.3 How the Dash lists them

`on_generator_highlighted` → `PresetsPanel.set_presets(resolve_preset_dir(root),
media_type_for_generator(app_def.tool))`. For a highlighted **Video Generator**
instance `media_type == "video"`, so the panel lists exactly the six video
presets, in `presets.order` order (unknown stems still append after the listed
ones). For an Image Generator instance the six are filtered out — no visible
change to IG. `resolve_preset_dir` reads the project's single shared PRESETS dir.

### 4.4 How VG consumes them (schema keys consumed)

| Schema key | Who reads it | Effect |
|---|---|---|
| `name` | panel / preview | display label only (never a filename) |
| `media_type` | `PresetsPanel.set_presets`, `profiles_list` | `"video"` select for the VG app |
| `prefix` | `compose_profile` → `prompt_prefix` | prepended to the Markdown prompt |
| `suffix` | `compose_profile` → `prompt_suffix` | appended to the Markdown prompt |
| `description` | panel preview only | **never composed**; VG never sees it (by contract) |
| `reference_media` | `compose_profile` → `reference_images` | empty for all six; when non-empty, see §1.3 (VG merge required) |

The composed profile is passed to VG as `--profile`; VG's existing
`load_profile_studiolot` + prompt-wrap path consumes it with **no new VG code**
for these six presets.

### 4.5 studiolot test amendments (must not silently weaken)

Three existing assertions hard-code the image-only 18-default world and must be
amended (not deleted/blanket-relaxed), per the W212 "flag, don't relax" ruling:

| Test / assertion | Today | Amended to |
|---|---|---|
| `tests/test_default_presets.py::test_exactly_eighteen_default_presets` | `== 18` | a named **image** set (18) + a named **video** set (6), or a total of 24 with the media split pinned |
| `…::test_every_default_parses_with_invariants` | `media_type == "image"`, `reference_media == ""` | assert both are pinned **per stem** (image stems → `image`; the six video stems → `video`), keeping the `[a-z0-9-]+` stem, non-empty `prefix`, non-empty `description` checks for all 24 |
| `…::test_shipped_preset_order_lists_all_stems_once` / `…_none_first_aspect_last` | `len(order) == 18` | `len(order) == 24`; first/last-three invariants unchanged |
| `tests/test_project_init_scaffold.py::test_copy_default_presets_copies_shipped_files` | `copied == 18`, `media_type == "image"` for all | `copied == 24`, file list + `media_type == "image"` retained for the 18 image files and `"video"` for the 6, in a scoped way |

`test_copy_default_presets_ships_order_sidecar` also asserts `copied == 18` and
must move to 24. **No** new preset-parsing code is added anywhere — the reader
already carries the keys (W95 M0).

---

## 5. Milestones (each acceptance is a static-file fact)

> Grounded in files on disk and test results, never in "a run produced…". The
> exact commands are in §6.

| M | Repo | Scope | Acceptance (static) |
|---|---|---|---|
| **M1** | studiolot | Author the six `.preset` files (§2) + update `presets.order` (18 → 24). | `test -f` for all six paths is true; `hc.presets.read_preset(p).media_type == "video"` for each; `preset_stem` matches the §3 table; `presets.order` contains all 24 stems once. |
| **M2** | studiolot | Amend the four assertions in §4.5 (count, media whitelist, order, scaffold copy). | `./.venv/bin/python -m pytest tests/test_default_presets.py tests/test_project_init_scaffold.py -q` → all green; the image-only assertions still pass for image stems. |
| **M3** | studiolot | Schema round-trip proof (§6) on the shipped six + one throwaway embedded-reference-image fixture; assert `compose_profile` emits `reference_images` for a media-bearing preset and omits it for empty. | The `python -c` one-liners in §6 print `OK`; `read_preset(write_preset(p)) == p`. |
| **M4** | VG | Implement `GENERATOR_CONTRACT.md` §2f in `src/engine_helpers.py::build_inputs`: when `profile["reference_images"]` is present, route into the declared `reference_images` slot (appended after the input's own refs) else append to `reference_urls`; **raise/warn loud** if the Engine cannot accept it (never drop). | `./venv/bin/python -m pytest tests/` green, incl. new `tests/test_engine_helpers.py` cases: (a) declared slot → `references["reference_images"]` ends with the preset URLs after the bullet's own; (b) no slot → `reference_urls` ends with them; (c) Engine without the `references` kwarg + preset refs → the existing loud warning path fires. |
| **M5** | VG + studiolot | Full suites + lint per repo. | VG: `./venv/bin/python -m pytest tests/` green (baseline 85 passed). studiolot: `./.venv/bin/python -m pytest tests/` green; `./.venv/bin/ruff check .` clean. Ruff is installed into VG's venv by the build — see §6. |
| **M6** | VG | Docs: record the plan outcome in `docs/HISTORY.md`; note the preset home in `README.md`/`CONTRIBUTING.md` if the Owner wants the stale four-field schema line refreshed. | Files contain the new section; suite still green (doc-only). |

M1–M3 are the mission's core and land in **studiolot**. M4 is the VG code half
(the finding in §1.3), **in scope** (Owner, 2026-10-01 — Q-3). M5–M6 close it
out.

---

## 6. Verification

### Per repo — commands actually confirmed at plan time

| Repo | Test command | Plan-time result |
|---|---|---|
| VG (`~/APPLICATIONS/video-generator`) | `./venv/bin/python -m pytest tests/` | **85 passed** (0.64 s) |
| studiolot (`~/MISC/studiolot`) | `./.venv/bin/python -m pytest tests/test_default_presets.py tests/test_project_init_scaffold.py -q` | **15 passed** (1.07 s) |

- **Lint note (confirmed, not assumed):** VG configures ruff in `pyproject.toml`
  (`[tool.ruff]`) but **ruff is not installed** in `./venv` at plan time
  (`./venv/bin/python -m ruff` → *No module named ruff*; `ruff` not on `PATH`;
  no `uvx`). The build installs it — `./venv/bin/pip install ruff`, with **no**
  `pyproject.toml`/`requirements.txt` change — so `./venv/bin/ruff check` is the
  VG lint gate. Studiolot's `./.venv/bin/ruff check .` remains the authoritative
  studiolot gate. Claim VG lint only once ruff is installed.
- Studiolot suite baseline to hold: **2034 passed / 24 skipped** at W212 close;
  re-confirm at build head before/after.
- VG suite baseline to hold: **85 passed**.

### Schema proof (write → read → equal, plus embedded reference image)

> **Run at plan time against the §2 content (temp dir only, no repo file
> written):** all six proposed presets round-trip
> `read_preset(write_preset(p)) == p`, every `preset_stem(name)` matches the §3
> table, none collides with an existing stem, and `compose_profile` emitted
> `reference_images` in authored order for a media-bearing preset and omitted it
> (and `description`) for an empty one. Output: `OK dolly-in … OK orbit`,
> `ALL SIX ROUND-TRIP + STEM-SAFE + NO COLLISION`, `OK compose reference_images`.
> Re-run the commands below at build to reproduce.

Run with studiolot's core on `PYTHONPATH` (or from `~/MISC/studiolot`):

```bash
cd ~/MISC/studiolot
# (1) round-trip a shipped camera preset (description carried)
./.venv/bin/python -c "
from pathlib import Path
from hc.presets import read_preset, write_preset, Preset, preset_stem
p = read_preset(Path('console/studiolot/presets/dolly-in.preset'))
assert p is not None and p.media_type == 'video' and p.description, p
import tempfile
with tempfile.TemporaryDirectory() as d:
    f = Path(d)/'x.preset'; write_preset(f, p)
    assert read_preset(f) == p
    print('OK round-trip dolly-in', preset_stem(p.name))
"
# (2) embedded reference image round-trip (throwaway fixture — not shipped)
./.venv/bin/python -c "
from pathlib import Path
from hc.presets import Preset, write_preset, read_preset, extract_reference_media
p = Preset(name='Ref Fixture', media_type='video', prefix='p',
           description='d',
           reference_media='https://example.com/a.jpg\n![still](https://example.com/b.jpg)')
import tempfile
with tempfile.TemporaryDirectory() as d:
    f = Path(d)/'r.preset'; write_preset(f, p)
    assert read_preset(f) == p
    assert extract_reference_media(p.reference_media) == ['https://example.com/a.jpg','https://example.com/b.jpg']
    print('OK round-trip embedded reference image')
"
# (3) composition: media-bearing preset → reference_images emitted; empty → absent
./.venv/bin/python -c "
from hc.profiles import compose_profile
import yaml
class A: platform='replicate'; model_endpoint='x/y'; parameters={}; general={}
from hc.presets import Preset
m = compose_profile(A(), Preset(name='m', media_type='video', prefix='p', suffix='s', reference_media='https://example.com/a.jpg'))
assert yaml.safe_load(m)['reference_images'] == ['https://example.com/a.jpg']
e = compose_profile(A(), Preset(name='e', media_type='video', prefix='p', suffix='s'))
assert 'reference_images' not in yaml.safe_load(e)
assert 'description' not in yaml.safe_load(m)
print('OK compose reference_images')
"
```

### Static proof (paste into the closure)

```bash
cd ~/MISC/studiolot
ls -1 console/studiolot/presets/dolly-in.preset console/studiolot/presets/dolly-out.preset \
      console/studiolot/presets/dolly-left.preset console/studiolot/presets/dolly-right.preset \
      console/studiolot/presets/handheld.preset console/studiolot/presets/orbit.preset
cat console/studiolot/presets/dolly-in.preset
grep -c . console/studiolot/presets/presets.order
```

The closure must include the file inventory, one full preset file (exact bytes),
and the schema-proof output.

---

## 7. Risks / open questions

**Open questions for the Owner** — *all answered 2026-10-01
("all three as recommended"); the plan's recommendations are kept below as
rationale.*

- **Q-1 (repo boundary).** **Answered (Owner, 2026-10-01): cross-repo
  CONFIRMED** — the six `.preset` files land in studiolot
  (`console/studiolot/presets/` + `presets.order` + the test amendments); the VG
  half is the `reference_images` merge + the docs; the closure records both
  repos' commits. *Rationale (kept):* the work order targets `video-generator`,
  but the settled shape puts the six `.preset` files in **studiolot**; the
  closure names the studiolot commit (6 presets + `presets.order` + test
  amendments) as well as the VG change.
- **Q-2 (content).** **Resolved (Owner, 2026-10-01): the six §2 strings stand as
  the build's starting content; the Owner's wording pass happens after the
  build** — no change to the §2 table. *Rationale (kept):* the
  `prefix`/`suffix`/`description` strings are worker-improvised and presented as
  the review table; names are the Owner's six ("Dolly left/right", not "Truck").
- **Q-3 (`reference_images` merge scope).** **Answered (Owner, 2026-10-01): M4
  IS IN SCOPE** — implement the VG `reference_images` merge
  (`GENERATOR_CONTRACT.md` §2f) as part of W98. *Rationale (kept):* W95 plan
  §5.6 folded the MC/VG merge into W98 (M9 there); the six presets ship
  prose-only, so the merge is not *needed* for them, but it is contract-mandated
  §2f. IG is in the same state (W209 owns the FC half).
- **Q-4 (media).** **Answered (Owner, 2026-10-01): words-only CONFIRMED** —
  `reference_media = ""` for all six; per-move clips, if ever wanted, are a
  separate studiolot-side schema/transport job (W95 territory), not W98.
  *Rationale (kept):* no movement needs a reference asset, and a camera-movement
  reference would be a **video** with no transport precedent (`reference_media`
  → `reference_images`, image typed); do not extend the schema in VG.

**Risks**

- **Cross-repo drift.** The preset files live in studiolot while the plan lives
  in VG; without a clear closure record the two halves can diverge. Mitigation:
  §4.1/§4.5 name a single source of truth, and the closure lists both commits.
- **Test amendments.** Three shipped-default assertions hard-code "18 image
  presets". The amendment must keep the strict per-media checks (W212 ruling:
  amend, never blanket-relax). Called out in §4.5.
- **Order invariant.** `presets.order` placement must keep `txt-img-to-img` first
  and the aspect trio last; §4.1 satisfies it, M1/M2 assert it.
- **Silent media drop.** M4 implements the §2f fail-loud rule, so a *future*
  media-bearing video preset is no longer silent-dropped; until M4 lands, such a
  preset would be dropped. The six ship empty, so the shipped feature is safe.
- **Stale handoff references.** `cinematic.preset` (retired) and `aisl/*`
  (renamed `hc/*`) are corrected in §0; the build must use the current paths.
- **Lint availability.** VG ruff is configured and the build installs it into
  `./venv` (§6); claim VG lint green only after that install.
- **Out-of-scope creep.** The other ten movements stay open on issue #2 — do not
  author them here.

**Boundaries honoured by this pass:** planning only (no files/code/commits); no
fork or duplication of the studiolot schema (consumed as-is); `USER-FILES/`
untouched (read-only); no engine/provider logic; no `@theia/*` edits; file-size
limits respected; no secrets.
