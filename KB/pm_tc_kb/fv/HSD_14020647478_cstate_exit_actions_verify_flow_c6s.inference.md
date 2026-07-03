# Deep Analysis: CState Exit Actions: Verify Flow C6S-P

| Field | Value |
|-------|-------|
| **HSD ID** | 14020647478 |
| **Title** | CState Exit Actions: verify flow C6S-P |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | C6S-P exit flow — FIVR restoration + core returns to C0 |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **C6S-P exit flow**. C6S-P exit requires restoring the FIVR (voltage collapse → restore) before the core can execute. More complex than C6S exit. Functional on NWP.

Tags: `DMR_PO`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### C6S-P Exit Pass/Fail Criteria

| Signal | Expected After C6S-P Exit |
|--------|-----------------------------|
| `core_cstate` | C0 |
| PICLET FSM | `PICLET_PMA_IDLE` |
| SRL | `SRL_IDLE` |
| `BGF_RUN` | 1 |
| `CORE_PWR_GOOD` | 1 (FIVR restored) |
| `PLL_LOCK` | 1 |
| FIVR state | 1 (FIVR on and stable) |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Place core in C6S-P (FIVR off) | CORE_PWR_GOOD=0, FIVR=off |
| 2 | Send interrupt | Trigger C6S-P exit |
| 3 | Verify FIVR powers on first | FIVR ramp-up occurs before core resumes |
| 4 | Verify all exit signals match C0 state | Table above |
| 5 | Verify no fault on exit | No MCA or hang |
| 6 | Run PMx | `python runPmx.py -x nwp.xml -p cstates -H 1 -M 5` |

### C6S-P Exit Latency
- C6S-P exit is the slowest (FIVR restore + PLL lock + cache fill)
- Latency must be within spec limits for interrupt response SLA

### Pass Criteria
- FIVR powers on before execution resumes (`CORE_PWR_GOOD = 1`)
- All exit signals match C0 criteria
- Exit latency within spec
- No MCA during FIVR restore sequence

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; C6S-P exit functional on NWP; verify FIVR restore sequence**

**Priority**: High — `plc.feature.p1`; C6S-P exit with FIVR restore is the highest-latency C-state exit — must be verified for interrupt response compliance
