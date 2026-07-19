# TCD: C6S-P and PKGC Behavior (Parked)

<!-- NEW 2026-07-19: Split from TCD 22022421247 per Co-Design T2 ingest.
     Parked by policy because current Newport scope treats PKGC as non-target/ZBB.
     Keep as a spec-backed placeholder; do not schedule execution until scope change. -->

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170168](https://hsdes.intel.com/appstore/article-one/#/16031170168) |
| **Title** | C6S-P and PKGC Behavior (Parked) |
| **Status** | parked |
| **Owner** | bg3 |
| **Parent TPF** | [15019478559 - Core C1/C6 (Entry/Exit/Residency)](https://hsdes.intel.com/appstore/article-one/#/15019478559) |
| **Parent TCD (split-from)** | [22022421247 - CState C6 basic functionality](https://hsdes.intel.com/appstore/article-one/#/22022421247) |
| **Validation Phase** | parked |
| **Feature** | Core C-States (C6S-P / PKGC path) |
| **Child TCs** | [16031170178](https://hsdes.intel.com/appstore/article-one/#/16031170178) — C6S-P resolve and restore (parked)<br>[16031170183](https://hsdes.intel.com/appstore/article-one/#/16031170183) — PKGC residency observe (parked) |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD isolates the C6S-P/PKGC-allowed architectural path as a separate WHAT with a distinct bar.
It is intentionally parked for current NWP scope.

Scope policy note:
- Current Newport plan treats PKGC as non-target/ZBB.
- This file preserves spec traceability so the scope can be activated later without rediscovery.

## Section 5: Pass/Fail Bar

When scope is enabled:
- C6S-P-targeted runs (MWAIT hint `0x20`) resolve to C6S-P behavior with state-restore correctness.
- `IA32_PKG_C6_RESIDENCY` (`MSR 0x3F9`) becomes observable per enabled architecture contract.
- C6S-P exit completes without architectural-state corruption.

Current execution rule:
- Do not execute in current TP scope.
- Keep as parked proposal unless product scope changes.

## Section 6: TC Coverage Map

| TC | Tier | Scope | Expected Result (PASS) | Status |
|----|------|-------|------------------------|--------|
| [16031170178](https://hsdes.intel.com/appstore/article-one/#/16031170178) | FV/PSS | C6S-P resolve/exit path and state restore | C6S-P resolves correctly; exit completes without architectural-state corruption | parked |
| [16031170183](https://hsdes.intel.com/appstore/article-one/#/16031170183) | FV/PSS | PKGC residency observability when scope enabled | `MSR 0x3F9` behavior matches enabled architecture contract | parked |

## Section 8: References

| Reference | Link |
|-----------|------|
| Core C-States HAS | [dmr_core_state.html](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_core_state.html) |
| Split source | [22022421247](https://hsdes.intel.com/appstore/article-one/#/22022421247) |
