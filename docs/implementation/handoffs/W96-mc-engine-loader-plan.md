# W96 — Motion Conductor `engine_loader.py` TYPE_CHECKING `Any` bug (plan)

> **Planning pass.** No code edits were made to produce this document.
> Repo under analysis: `~/APPLICATIONS/motion-conductor` (MC), plus the
> canonical `~/MISC/studiolot` and the FC vendored copy.
> Written 2026-09-28.

---

## 0. Verdict up front — W96 is **(c) obsolete** as written

The defect the work order describes **no longer exists**, and the vendoring
frame it relies on has changed. Evidence below. Recommendation: **close W96**
rather than size it. One real, *separate* gap survives inside the card's
wording (the "old minimal log pattern") and is scoped in §5 as an optional,
narrowly-bounded follow-up — it is not part of `engine_loader.py`.

| Claim in the work order / card #54 | Today's reality | Verdict |
|---|---|---|
| MC `engine_loader.py` has a `TYPE_CHECKING`-only `Any` bug | MC copy imports `Any` at top level; **no `TYPE_CHECKING` in the file** | **fixed** |
| Canonical lives at `studiolot/pipeline/engine_loader.py`; fix there then re-vendor | `pipeline/engine_loader.py` is now a 27-line re-export stub over `aisl/engines.py` | **frame changed** |
| "older minimal log pattern" on the loader | Loader is not a logging module; the minimal pattern is MC `src/utils/logging.py` | **real but separate** |

State plainly: the engine_loader half is **obsolete**; the log half is a
**genuine vehicle-parity gap** that was bundled into the card and should be its
own workstream if the Owner wants it.

---

## 1. Root cause (historical) — and why it is gone

### 1a. The bug was real when the card was written

The deferred item is `studiolot/docs/implementation/HISTORY.md:57`:

> `9. MC vehicle has the latent \`engine_loader.py\` TYPE_CHECKING-only \`Any\` bug + old minimal log pattern — upgrade when MC is next worked on.`

It was recorded in commit `c0d7061` (2026-08-17). At that date MC's loader was
the state left by `5817b38` (2026-08-05), which **did** carry the pattern:

- `~/APPLICATIONS/motion-conductor/src/engine_loader.py` @ `5817b38`:
  - `:8` `from __future__ import annotations`
  - `:13` `from typing import TYPE_CHECKING`
  - `:15-16` `if TYPE_CHECKING:` → `from typing import Any, Callable`
  - `:30` `profile: dict[str, Any]` (a runtime class-body/annotation reference to `Any`)

The studiolot canonical of the same era had the identical defect:

- `~/MISC/studiolot/pipeline/engine_loader.py` @ `4f4b664`:
  - `:7` `from __future__ import annotations`
  - `:12` `from typing import TYPE_CHECKING, Callable`
  - `:14-15` `if TYPE_CHECKING:` → `from typing import Any`
  - `:46` `profile: dict[str, Any],` in the runtime-evaluated free-function signature

MC's *earliest* vendored copy (`9de884f`, 2026-08-02) carried the same pattern
(`:7` future import, `:11` `TYPE_CHECKING`, `:13-14` `Any`, `:20`
`profile: dict[str, Any]`).

**Why "latent":** `from __future__ import annotations` makes the annotation a
string, so import succeeds; the `NameError` fires only when something resolves
annotations — e.g. `typing.get_type_hints()`, a framework that introspects
signatures, or a type-check run. Reproduced against the `4f4b664` file text
(no repo edits):

```
import ok; __annotations__ = {'profile': 'dict[str, Any]', 'return': 'None'}
typing.get_type_hints(f) -> NameError: name 'Any' is not defined
```

### 1b. The bug was fixed — before this workstream started

The fix did not come from W96; it arrived with unrelated MC→FC parity work and
was then re-vendored:

- MC `ca8b360` (2026-09-03, "Part 1 of MC→FC parity"): loader becomes
  `from typing import Any` (top level), `TYPE_CHECKING` removed.
- studiolot `51f54a1` (2026-09-17, "restore engine_loader canonical — adopt
  FC's evolved loader"): the canonical stops being the stalest of three
  snapshots; its commit message explicitly names the *"TYPE_CHECKING-only Any
  import bug"* as removed.
- MC `3b80a10` (2026-09-17, "re-vendor engine_loader from studiolot
  (canonical; was a 3rd variant)"): MC adopts the fixed copy.

### 1c. Confirmed clean today

- `~/APPLICATIONS/motion-conductor/src/engine_loader.py:9-19` — imports no
  `TYPE_CHECKING`; `:17` `from typing import Any`. File is 200 lines.
- `~/APPLICATIONS/frame-composer/src/engine_loader.py` — same, no
  `TYPE_CHECKING`.
- The only `TYPE_CHECKING` in the MC repo is
  `src/processing/bullet_parser.py:24`, `:30`, importing `Callable`; its sole
  use is the **string** annotation at `:52` (`"Callable[[str], None] | None"`),
  so it is never evaluated at runtime → safe, unrelated to this card.

**No runtime reference to a type-check-only name remains anywhere on the path
the card describes.**

---

## 2. The vendoring frame has moved (the second premise that breaks)

- `~/MISC/studiolot/pipeline/engine_loader.py:1-27` is now a **re-export stub**:
  `from aisl.engines import (EngineLoadContext, copy_standby_profiles,
  find_engine_dir, find_first_engine_dir, load_engine)`. Its docstring `:8` says
  "Vehicle re-vendoring against the core is author-side/M9."
- The loader logic now lives at `~/MISC/studiolot/aisl/engines.py` (defs
  `:60-239`), absorbed in M3.
- `~/MISC/studiolot/docs/architecture/VEHICLE_CONTRACT.md:130-135` (§2e) still
  names `pipeline/engine_loader.py` as canonical and says "All three are
  currently identical (200 lines)" — **stale** against the stub/core split.
- The live byte-identity gate is
  `~/MISC/studiolot/tests/test_aisl_packaging.py:144-163`
  (`test_vehicle_loader_vendoring_gate`): asserts **FC text == MC text**, then
  AST-normalised definition parity of every top-level def against
  `aisl/engines.py`. Re-run this pass: **`1 passed`**.

So "fix the vendored copy, then re-vendor" is no longer the frame: the vehicle
copies are frozen pre-M3 snapshots, and re-vendoring them **against the core**
is explicitly deferred to an author-side step (`W1-XREPO-1` / M9), out of W96's
stated scope and boundary ("Do not rename anything"; "Do not edit an engine").

---

## 3. Canonical fix design + regression test — already satisfied

Since the defect is gone, there is nothing to design. What *is* worth keeping
from W96 is the **regression guard that would have caught it**, because none
exists today (`grep get_type_hints` in MC `tests/` → 0 hits).

Proposed (canonical-side, only if the Owner wants belt-and-suspenders):

- **Test:** in `studiolot/tests/` (the canonical home), assert that resolving
  annotations on the loader's public surface does not raise:
  `typing.get_type_hints(load_engine)`, `EngineLoadContext`, `find_engine_dir`,
  `find_first_engine_dir`, `copy_standby_profiles`. This fails red on any
  reintroduction of a type-check-only name.
- **Where:** canonical suite, not MC, because the loader is a vendored snapshot
  and the AST-parity gate already propagates canonical shape to the vehicles.
- This test is **optional**: the current code cannot fail it. It only buys
  future protection.

No `Any`/`TYPE_CHECKING` edit is required in MC or FC.

---

## 4. Re-vendor steps for MC and FC — already done; core re-vendor is a separate ticket

- **Snapshot re-vendor (what W96 asked):** done.
  `diff motion-conductor/src/engine_loader.py frame-composer/src/engine_loader.py`
  → **exit 0** (byte-identical). Gate green (`test_aisl_packaging.py`).
- **Core re-vendor (what the contract now implies):** not W96. MC/FC import
  `src.engine_loader`; moving them onto `aisl.engines` would change their
  dependency on the `aisl-core` distribution and is the deliberately deferred
  `W1-XREPO-1` item. Touching it here would collide with that ticket and exceed
  the stated boundary.
- **Byte-identity proof, as it stands:** `fc_text == mc_text` plus AST parity
  vs `aisl/engines.py`, per `test_aisl_packaging.py:148-163`.

---

## 5. The one real survivor: "old minimal log pattern"

The card's second clause does map to a **real, current** divergence, but it is
**not in `engine_loader.py`** — that file contains no logging. The evidence
points at MC `src/utils/logging.py`, which is the older minimal variant of FC's
evolved one:

| Concern | MC `src/utils/logging.py` | FC `src/utils/logging.py` |
|---|---|---|
| Terminal capture | `_ANSI_ESCAPE` regex (`:21`) | `_TerminalCleaner` FSM (CSI/OSC/CR) |
| Run log content | raw captured text only (`write_run_logs(generated_paths, output_dir)` `:94`) | header + payload JSON + console + summary (`_build_header`, `_build_summary`) |
| Call site | `src/main_verbose.py:182`, `:167` `log_file_only` | `src/main_simple.py` (ctx/payloads/results) |

This is a **vehicle-parity** concern (MC→FC logging parity), distinct from the
vendored loader. The work order's phrase "bring the log pattern up to the
current minimal pattern" is ambiguous (FC's variant is *more* elaborate, not
minimal), so this should not be actioned without the Owner confirming which
pattern is desired.

**Recommendation:** do not fold this into W96. If wanted, open a new card
(e.g. `W96b — MC run-log parity with FC`) with its own scope, tests, and
acceptance. Force-fitting it here would manufacture scope to keep W96 "alive",
which the handoff explicitly forbids.

---

## 6. Milestones / acceptance / verification (for the close-out)

W96 as written has **no implementation milestones**. The correct close-out:

| Step | Action | Acceptance |
|---|---|---|
| M1 | Record the obsolescence finding (this doc) | Present in `motion-conductor/docs/implementation/handoffs/` |
| M2 | Update the source of truth: strike/resolve `studiolot/docs/implementation/HISTORY.md:57` item 9 | Item marked resolved with a pointer to this plan |
| M3 | (Optional) add the `get_type_hints` regression guard canonical-side | Red before / green after a deliberate reintroduction; suite green |
| M4 | (Optional) refresh `VEHICLE_CONTRACT.md` §2e stale text (stub + core, "all three identical" claim) | §2e matches `pipeline/engine_loader.py` stub + `aisl/engines.py`; gate still green |

**Verification.** Both suites must stay green *without* loader edits:
- MC: `tests/` includes `tests/test_engine_loader.py` (imports the real
  `load_engine`, `EngineLoadContext`; no annotation-resolution test today).
- Canonical: `test_aisl_packaging.py::test_vehicle_loader_vendoring_gate`
  (`1 passed` this pass).
- FC: `tests/test_engine_loader.py` mirrors MC.

**Risks.**
- *False "fix" risk:* editing the frozen vehicle loader to chase a dead bug
  would trip the AST-parity gate or, worse, fork the snapshot again (the exact
  drift `51f54a1`/`0359259`/`3b80a10` repaired). Do not touch it.
- *Contract drift:* §2e's "canonical = `pipeline/engine_loader.py`" is stale;
  leaving it invites a future session to repeat W96's false premise.
- *Scope creep:* the log-pattern clause is a different subsystem; bundling it
  would be manufactured work.

---

## 7. Post-alignment questions for the Owner

1. **Close W96** as obsolete (engine_loader defect fixed at `ca8b360` +
   re-vendored at `3b80a10`; canonical moved to `aisl.engines` in M3)? *(Recommended.)*
2. Open a separate card for MC run-log parity with FC, or drop it too?
3. Add the canonical `get_type_hints` regression guard as cheap future-proofing?

No code edits to `engine_loader.py`, MC, FC, or any engine are proposed by this
plan.
