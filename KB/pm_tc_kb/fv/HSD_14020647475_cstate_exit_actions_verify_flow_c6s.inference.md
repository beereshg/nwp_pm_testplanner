# Deep Analysis: CState Exit Actions: Verify Flow C6S

| Field | Value |
|-------|-------|
| **HSD ID** | 14020647475 |
| **Title** | CState Exit Actions: verify flow C6S |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | C6S exit flow — core returns from C6S to C0 |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **C6S exit flow**. C6S exit includes reloading LLC content from memory (since LLC was flushed on entry). More complex than C6A exit due to cache reload. Functional on NWP.

Tags: `logs`, `cmdline`, `DMR_PO`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### C6S Exit Pass/Fail Criteria

| Signal | Expected After C6S Exit |
|--------|--------------------------|
| `core_cstate` | C0 |
| PICLET FSM | `PICLET_PMA_IDLE` |
| SRL | `SRL_IDLE` |
| `BGF_RUN` | 1 |
| `CORE_PWR_GOOD` | 1 |
| `PLL_LOCK` | 1 |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Place core in C6S | Core in C6S with LLC flushed |
| 2 | Send interrupt | Trigger exit |
| 3 | Verify all exit signals match | Same C0 criteria as C6A exit |
| 4 | Verify core resumes normally | No stale cache data issues |
| 5 | Run PMx | `python runPmx.py -x nwp.xml -p cstates -H 1 -M 5` |

### Pass Criteria
- Same exit signals as C6A (table above)
- No stale LLC data after cache flush/refill
- Core execution resumes without fault

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; C6S exit functional on NWP; verify LLC state after exit**

**Priority**: High — `plc.feature.p1`; C6S exit requires correct cache coherency restoration
