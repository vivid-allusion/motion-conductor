# Part 2 — Video Input Layer: Duration + Named Payload Slots

> Scope: **MC + engine-replicate.** No AISL changes (the `[general]`
> chain is Part 3 — until then the engine still falls back to defaults, but
> the profile can carry the mapping keys manually for standalone/testing).
> Depends on Part 1's tree alignment.
>
> **Deferred by author:** engine-fal, engine-openrouter, engine-google stay
> on the old flat-`reference_urls` datatype. They are brought to parity one
> by one in later sessions — the back-compat design below is what makes that
> possible (an Engine without `references` support keeps working).

## R1 — Bullet parser: duration line

Extend `src/processing/bullet_parser.py` to parse a `duration:` line carrying
a raw value — integer (`duration: 5`) or any token (`duration: auto`,
`duration: -1`). Passed through **verbatim** into `InputFile.metadata`
(`{"duration": 5}` / `{"duration": "auto"}`) — the vehicle never interprets
it; the model's TOML documents its own tokens (the `duration` select already
carries `-1` labeled Auto). Legacy `frames: N` stays parseable (converted via
fps) — see Q1.

## R2 — Bullet parser: alt-text slots

Capture markdown alt text: `![reference_images](url)` → URL routed to the
named slot `reference_images`; empty alt `![](url)` → primary slot. Port FC's
format-warning battery (`_check_line`). Unknown alt handling per Q2.

## R3 — Engine contract: structured references

`InputFile` gains a named-slot map while keeping `reference_urls` (primary
slot) back-compat — exact shape per Q3. `datatypes.py` is deliberately
duplicated per Engine; **this part updates engine-replicate only** (fal,
openrouter, google follow in later sessions). FC must run unchanged (it only
sets `reference_urls`), and an Engine still on the old datatype keeps working
because the new field is additive.

## R4 — Engine payload builder: slot routing + duration override

`_build_replicate_input()` (equivalents in the other engines land with their
own later parity sessions):
- Empty-alt URLs → the profile's primary input key (`image_url_param` from
  the TOML `[general]` when present, fallback `reference_param`, fallback
  `image_input`).
- Named-alt URLs → their own payload keys (e.g. `reference_images`,
  `reference_videos`, `reference_audios`; Kling `start_image`/`end_image`).
- Per-bullet `metadata["duration"]` overrides `parameters.duration` under
  `duration_param_name`.
- Empty named lists: emit or omit per Q4.

## R5 — Slot declarations in endpoint TOMLs

Extend the VID-model TOMLs' `[general]` with the declared slot schema the
vehicle/engine need (exact keys per Q2/Q4). The existing
`image_url_param`/`duration_type`/`duration_param_name` keys stay.

## Open questions (settle during the mult2 loop; proposals given)

- **Q1 — `frames:` vs `duration:`:** keep `frames:` back-compat (converted
  via fps) or drop? *Proposal:* accept both, `duration:` wins, `frames:`
  deprecated-but-parsed.
- **Q2 — unknown alt text:** `![foo](url)` with undeclared `foo` — error the
  bullet or fall back to the primary key? *Proposal:* error when the profile
  declares slots (fails loudly), primary-key fallback only when no slot
  schema exists.
- **Q3 — InputFile shape:** `reference_urls` (primary) + `references:
  dict[str, list[str]]` (named), or one dict with a reserved key? *Proposal:*
  the two-field shape — zero breakage for FC and the other engines.
- **Q4 — empty named lists:** emit declared-but-unused slots as `[]` always,
  or omit? *Proposal:* omit unless the TOML marks them required.
- **Q5 — "auto" tokens:** verbatim passthrough or normalize `auto` →
  model-specific value? *Proposal:* verbatim.

## Verification (gate before Part 3)

```bash
# MC repo
venv/bin/python -m pytest tests/ -v            # parser + payload-shape tests
venv/bin/python -m ruff check src/ tests/
# engine-replicate repo
python -m pytest tests/ -v                     # slot routing, duration override
# studiolot-mode dry-run with a video bullet:
venv/bin/python -m src.main_verbose --dry-run \
  --input_dir /tmp/mc_input --output_dir /tmp/mc_output --profile /tmp/mc_profile.yaml
```

A bullet containing `duration: auto` and `![reference_images](...)` must
parse to the expected structured input; unit tests must assert the exact
Seedance-shaped payload dict (`prompt`, `duration`, `reference_images: [url]`,
…). FC regression: run FC's suite unchanged (no edits to FC expected).

## Not in this part

- AISL `[general]` → binding → composed-profile chain (Part 3)
- Docs sweeps (Part 3)
