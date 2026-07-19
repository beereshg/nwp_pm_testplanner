# TCD: MC6 Electrical Entry Sequence

<!-- NEW 2026-07-19: Split from TCD 22022421250 per Co-Design T2 ingest.
     Separate module-level electrical entry sequence from core logical entry flow. -->

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170165](https://hsdes.intel.com/appstore/article-one/#/16031170165) |
| **Title** | MC6 Electrical Entry Sequence |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [15019478562 - Module C-States (Core-Module)](https://hsdes.intel.com/appstore/article-one/#/15019478562) |
| **Parent TCD (split-from)** | [22022421250 - CState entry actions](https://hsdes.intel.com/appstore/article-one/#/22022421250) |
| **Validation Phase** | Alpha / Beta / PRQ |
| **Feature** | Core C-States (MC6 module entry sequencing) |
| **Child TCs** | [16031170171](https://hsdes.intel.com/appstore/article-one/#/16031170171) — MC6 entry phase order<br>[16031170172](https://hsdes.intel.com/appstore/article-one/#/16031170172) — MC6 entry negative phase guard |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD validates module-level MC6 electrical entry sequencing only.
It owns the sequence after all-core qualification is satisfied and excludes core-level C6 request logic.

Owned behavior:
- all-core qualification handoff to module sequence
- module electrical entry ordering
- no sequence violation under repeated transitions

## Section 5: Pass/Fail Bar

- After all-core qualification, module entry phases complete in-order: qualification -> policy/flush gate -> module electrical entry.
- `IA32_MC6_RESIDENCY` (`MSR 0x664`) increments only after sequence completion, never mid-sequence.
- Sequence ordering remains stable across repeated cycles with identical stimulus.
- No hang, timeout, or MCA during module entry path.

FAIL if any of the following occur:
- out-of-order module entry phase
- missing required phase transition
- `MSR 0x664` increments before sequence completion
- unstable sequencing across identical stimulus

## Section 6: TC Coverage Map

| TC | Tier | Scope | Expected Result (PASS) | Status |
|----|------|-------|------------------------|--------|
| [16031170171](https://hsdes.intel.com/appstore/article-one/#/16031170171) | FV/PSS | MC6 module electrical entry phase ordering | qualification -> policy/flush gate -> module electrical entry observed in-order | planned |
| [16031170172](https://hsdes.intel.com/appstore/article-one/#/16031170172) | FV/PSS | Negative perturbation during entry preconditions | sequence guard prevents invalid phase advance; no premature `MSR 0x664` increment | planned |

## Section 8: References

| Reference | Link |
|-----------|------|
| Core C-States HAS | [dmr_core_state.html](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_core_state.html) |
| Split source | [22022421250](https://hsdes.intel.com/appstore/article-one/#/22022421250) |
