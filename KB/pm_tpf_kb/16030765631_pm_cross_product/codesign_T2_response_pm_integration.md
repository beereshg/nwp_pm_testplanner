# Co-Design T2 Ingest - PM Integration Testing (TPF 22022562325)

**Date:** 2026-07-20
**Template:** T2 (Grouping / WHAT-boundary check)
**Status:** Ingested - pending user confirmation for execution

---

## Table 1 - Diagnosis Summary

| TCD ID | Clubs multiple? | Key finding |
|---|---|---|
| 22022420631 | YES (4) | PMX stress + Socket RAPL enforcement + PLR observability + RAPL-RACL arbitration |
| 22022420633 | YES (4) | C-state x HWP x DVFS + C-state x legacyP x DVFS + isolated C-state + isolated P-state |
| 22022421309 | YES (5) | SB-harasser + DRAM RAPL (fused off!) + PEGA + Solar C/P + ZBB negative (misplaced) |
| 22022421311 | NO | Clean single-WHAT - keep |

---

## Table 2 - Target Hierarchy Proposal (validated against WHAT-boundary rule)

### Accepted proposals (bars diverge, spec-cited):

| # | TCD | WHAT | Bar (abbreviated) | Action | Validation |
|---|---|---|---|---|---|
| 1 | 22022420631 (narrowed) | PMX stress stability under combined PM controls | No hang/MCA/frequency discontinuity | split-from 22022420631 | Bar distinct from #2 |
| 2 | NEW | RAPL+RACL simultaneous limiting arbitration and PLR observability | Power <= RAPL ceiling; freq <= tighter limiter; PLR matches winner | new | Spec-cited bar present |
| 3 | NEW | Solar C-state x HWP x DVFS random | Freq within HWP spec-valid band; no hang/MCA | split-from 22022420633 | HWP-specific bar |
| 4 | NEW | Solar C-state x legacy P-state x DVFS random | Freq matches legal legacy-P-state outcome | split-from 22022420633 | Legacy P-state bar differs |
| 5 | NEW | Solar isolated C-state entry/exit under DVFS | Entries/exits complete; post-exit freq legal | split-from 22022420633 | C-state completion bar |
| 6 | NEW | Solar isolated P-state/HWP frequency selection | Freq resolves to legal spec operating point | split-from 22022420633 | P-state selection bar |
| 7 | NEW | SB-harasser robustness during PM transitions | No hang/corruption; transitions complete or abort cleanly | split-from 22022421309 | Protocol-level bar |
| 8 | 22022421311 | Endpoint sweep accessibility/correctness (unchanged) | All endpoints accessible; no timeout/corruption | keep | Already clean |
| 9 | NEW | Reset during active PM stress recovery | Reset state reached; registers reinit; no post-reset hang | new | Spec-cited bar present |

### Merge/dissolve actions:

| Source TCD | Action | Detail |
|---|---|---|
| 22022421309 | Merge into #7 (SB-harasser) | Remove TC 16030715653 (ZBB negative - misplaced); Drop TC 23115 (DRAM RAPL fused off on NWP) |
| 22022420633 | Dissolve into #3, #4, #5, #6 | Current artifact violates one-WHAT rule |

---

## Execution Plan (requires user confirmation)

### Immediate actions (no HSD change):
- [x] Save ingest to KB
- [ ] Update TPF S2 Microarch-Scenario Coverage Matrix with refined element rows

### HSD actions (require confirmation):
1. Narrow 22022420631 - remove RAPL/RACL arbitration and PLR observability from its scope; update title to PMX Directed PM Stress
2. Create NEW TCD - RAPL + RACL Simultaneous Limiting Arbitration under TPF 22022562325
3. Create 4 NEW TCDs - Solar splits (C-state x HWP, C-state x legacyP, isolated C-state, isolated P-state)
4. Create NEW TCD - SB Harasser Robustness During PM Transitions; move active TCs from 22022421309 (except 16030715653 and 23115)
5. Reject TC 23115 (DRAM RAPL x SB Harasser) - feature fused off on NWP
6. Reparent TC 16030715653 ([PSS]Memory PM ZBB Negative Checks) - move to appropriate PSS TCD or reject
7. Create NEW TCD - Reset During Active PM Stress
8. Close/reject 22022421309 after TCs migrated
9. Close/reject 22022420633 after TCs distributed to Solar splits

### Deferred:
- Regenerate TPF preview after all TCD changes land
- Scaffold each NEW TCD via nwp-tcd-description skill (KB + preview)
