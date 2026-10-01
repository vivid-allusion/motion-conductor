## phase_1.md

No blocking questions.

## phase_2.md

No blocking questions.

## phase_3.md

1. Where does the durable regression test live — a new `tests/test_preset_reference_media.py`, or an extension of `tests/test_default_presets.py`?
2. Which `compose_profile` should the regression test exercise — the canonical `hc.profiles.compose_profile`, or the console re-export `studiolot.app.profile_compose.compose_profile`?
3. R2's third bullet overlaps existing coverage in `tests/test_app_profile_compose.py` (emit/omit/`reference_images` order, `description` omission). How do we avoid duplicating it verbatim?

**AGENT ANSWER:** 1 — new file `tests/test_preset_reference_media.py`; phase_3 `## Verification` names that path, so it is the intended home and keeps the schema lock separate from the shipped-default count/split test (phase_3 R2 "pick one, do not duplicate").
**AGENT ANSWER:** 2 — canonical `hc.profiles.compose_profile`; the handoff §6 proof and `tests/test_default_presets.py` already import `hc.*` directly, and the console path is only a re-export aggregator over `hc.profiles`.
**AGENT ANSWER:** 3 — give the new file a distinct angle: prove each of the *six shipped* camera presets round-trips and composes without `reference_images` (empty `reference_media`), and use one throwaway media-bearing fixture with a different URL shape than the existing test; assert combinations (authored order + no `description`) rather than copying its cases verbatim.

**USER RESPONSE:**
```
```
