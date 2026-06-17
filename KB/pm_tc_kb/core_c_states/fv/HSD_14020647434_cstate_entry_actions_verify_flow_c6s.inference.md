# Deep Analysis: CState Entry Actions: Verify Flow C6S

| Field | Value |
|-------|-------|
| **HSD ID** | 14020647434 |
| **Title** | CState Entry Actions: Verify Flow C6S |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | C6S (C6 with MLC/L2+LLC cache flush) entry flow |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **C6S entry flow**. C6S = C6 with cache flush (MLC/L2 + LLC flushed before power-down). More power-saving than C6A since LLC is also flushed. Functional on NWP.

Tags: `logs`, `cmdline`, `DMR_PO`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### C6S Entry Pass/Fail Criteria

| Signal | Expected After C6S Entry |
|--------|--------------------------|
| `core_cstate` | C6 |
| PICLET FSM | `PICLET_ENABLED` |
| SRL | `SRL_ACTIVE` |
| `BGF_RUN` | 0 |
| `CORE_PWR_GOOD` | 0 |
| `PLL_LOCK` | 0 |
| Target Volt | 0 |
| Target Freq | 0 |
| Target PS | 7 |
| Cache flush | MLC/L2 + LLC flushed (distinguishes C6S from C6A) |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot SVOS with C6 enabled | C6S functional on NWP |
| 2 | Run cstates PMx | `python runPmx.py -x nwp.xml -p cstates -H 1 -M 5` |
| 3 | OR standalone | `python /usr/lib/python3/dist-packages/newport/pm/Idle_PM/cstates/ccx_residency_test.py` |
| 4 | Idle core with hint for C6S | OS sends MWAIT with C6S hint |
| 5 | Verify register state matches C6S criteria | Same power state as C6A but with cache flush |
| 6 | Verify LLC flush occurred | Check LLC flush status/telemetry |

### C6S vs C6A Distinction (NWP)
- **C6A**: Autonomous, no cache flush requirement
- **C6S**: Cache flush (MLC/L2 + LLC) before power-down
- C6S requires OS MWAIT with C6S encoding to request flush

### Pass Criteria
- All signals match C6S expected state (same HW state as C6A, but cache flushed)
- MLC/L2 + LLC flush confirmed before power state entry
- Core exits C6S cleanly on interrupt

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; C6S functional on NWP; verify cache flush before power-down**

**Priority**: High — `plc.feature.p1`; C6S entry is critical for deep idle power — ensures LLC power is saved in addition to core
