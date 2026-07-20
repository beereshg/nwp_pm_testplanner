# TCD: C6S Behavior and MC6 Qualification

<!-- NEW 2026-07-19: Split from TCD 22022421247 per Co-Design T2 ingest.
     This TCD isolates C6S + MC6-qualification behavior from C6A and C6S-P.
     HSD TCD creation pending. -->

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170164](https://hsdes.intel.com/appstore/article-one/#/16031170164) |
| **Title** | C6S Behavior and MC6 Qualification |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [15019478559 - Core C1/C6 (Entry/Exit/Residency)](https://hsdes.intel.com/appstore/article-one/#/15019478559) |
| **Parent TCD (split-from)** | [22022421247 - CState C6 basic functionality](https://hsdes.intel.com/appstore/article-one/#/22022421247) |
| **Validation Phase** | Alpha / Beta / PRQ |
| **Feature** | Core C-States (C6S path) |
| **Child TCs** | [16031170169](https://hsdes.intel.com/appstore/article-one/#/16031170169) — C6S MC6 qualification gating<br>[16031170170](https://hsdes.intel.com/appstore/article-one/#/16031170170) — C6S MC6 negative unqualified block |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD validates the supervised C6S path where module-level preconditions drive C6S/MC6 behavior.
It owns the C6S WHAT only:
- C6S requires deeper flush path than C6A.
- MC6 qualification requires all module cores meeting deep-idle preconditions.
- Residency observability must match C6S/MC6 ownership boundaries.

This TCD does not own:
- C6A autonomous behavior (owned by TCD 22022421247).
- C6S-P/PKGC behavior (parked in TCD_NEW_c6sp_pkgc6_behavior_parked.md).

## Section 5: Pass/Fail Bar

- C6S-targeted runs (MWAIT hint `0x23`) resolve to the supervised path with expected residency behavior.
- `IA32_MC6_RESIDENCY` (`MSR 0x664`) increments only after all cores in the target module qualify for deep idle.
- `IA32_MC6_RESIDENCY` remains unchanged when qualification is intentionally broken (one core held active).
- `IA32_PKG_C6_RESIDENCY` (`MSR 0x3F9`) remains `0` for this NWP scope.
- No hang/MCA/timeout across repeated C6S entry-exit loops.

FAIL if any of the following occur:
- `MSR 0x664` increments before all-core qualification.
- C6S-targeted stimulus resolves to a policy-inconsistent state.
- `MSR 0x3F9` increments in current NWP scope.
- Any loop iteration reports hang, timeout, or MCA.

## Section 6: TC Coverage Map

| TC | Tier | Scope | Expected Result (PASS) | Status |
|----|------|-------|------------------------|--------|
| [16031170169](https://hsdes.intel.com/appstore/article-one/#/16031170169) | FV/PSS | C6S qualification and MC6 residency gating | `MSR 0x664` increments only after all-core qualification; `MSR 0x3F9` remains 0 | planned |
| [16031170170](https://hsdes.intel.com/appstore/article-one/#/16031170170) | FV/PSS | Negative path with one core held active in module | `MSR 0x664` does not increment while qualification is broken | planned |

## Section 8: References

| Reference | Link |
|-----------|------|
| Core C-States HAS | [dmr_core_state.html](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_core_state.html) |
| Split source | [22022421247](https://hsdes.intel.com/appstore/article-one/#/22022421247) |
