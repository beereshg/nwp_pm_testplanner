# Deep Analysis: Multiple B2B C-States on Same Core

| Field | Value |
|-------|-------|
| **HSD ID** | 14020416764 |
| **Title** | Multiple B2B cstates on same core |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | Back-to-back C-state cycles — stability and residency correctness |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test runs many back-to-back C-state cycles on the same core to verify stability and correct residency counter behavior. Core-level C-states (C6A, C6S, C6S-P) are functional on NWP.

Two execution paths per test steps:
1. PMx: `runPmx.py -x dmr.xml -p cstates -H 1 -M 5` → adapt to `nwp.xml`
2. Standalone: `python /usr/lib/python3/dist-packages/diamondrapids/pm/Idle_PM/cstates/ccx_residency_test.py` → NWP package path

Tags: `DMR_PO`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable C-states via BIOS/fuses | Boot with `core_cstate_limit` = C6 |
| 2 | Run B2B cstates via PMx | `python runPmx.py -x nwp.xml -p cstates -H 1 -M 5` |
| 3 | OR run standalone residency test | `python /usr/lib/python3/dist-packages/newport/pm/Idle_PM/cstates/ccx_residency_test.py` |
| 4 | Repeat overnight | Verify no hangs, MCAs, or incorrect residency |
| 5 | Check C6 residency counters | Counters should monotonically increase |

### NWP Notes
- `dmr.xml` → `nwp.xml`
- Standalone script path: replace `diamondrapids` → `newport` in Python package path
- NWP: No SMT — no thread pairs, single thread per core
- 96 cores total; run on subset or all cores

### Pass Criteria
- No hangs during overnight B2B C-state cycling
- No MCAs or system crashes
- C6 residency counters increase monotonically
- System remains functional after run

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; standalone script path `diamondrapids` → `newport`; no SMT on NWP**

**Priority**: High — `plc.feature.p1`; B2B C-state stability is fundamental — catches entry/exit FSM bugs that only manifest after repeated cycles
