# Deep Analysis: CState Fast C1E: Exit Flow Silicon

| Field | Value |
|-------|-------|
| **HSD ID** | 14020416804 |
| **Title** | CState Fast C1E: Exit flow_silicon |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | Fast C1E exit flow — return to C0 operating frequency/voltage |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **Fast C1E exit flow**. When an interrupt or work arrives while core is in C1E, the core should return to C0 with full operating frequency/voltage. Uses `pm.focused.cstate_focus.check_cst_focus()`.

Tags: `DMR_PO`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### C1E Exit Pass/Fail Criteria

| Signal | Expected After C1E Exit |
|--------|--------------------------|
| `core_cstate` | C0 |
| PICLET FSM | `PICLET_PMA_IDLE` |
| SRL | `SRL_IDLE` |
| `BGF_RUN` | 1 |
| `CORE_PWR_GOOD` | 1 |
| `PLL_LOCK` | 1 |
| Frequency | Returned to operating frequency |
| Voltage | Returned to operating voltage |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Place core in C1E (per entry TC 14020416803) | Core in C1E at 400MHz/Vmin |
| 2 | Send interrupt | Trigger C1E exit |
| 3 | Verify core returns to C0 | All exit signals match above |
| 4 | Verify frequency ramps back up | Full operating ratio restored |
| 5 | Verify voltage restored | Returns from Vmin to operating voltage |
| 6 | Run via PMx | `python runPmx.py -x nwp.xml -p cstates -H 1 -M 5` |

### C1E Exit Considerations
- C1E exit is faster than C6 exit (no PLL relock needed if PLL stayed active)
- Voltage ramp from Vmin to operating voltage must complete before full-speed execution

### Pass Criteria
- All C0 exit signals correct
- Frequency restored to pre-C1E ratio
- Voltage restored from Vmin
- `c1e_period = 0` after exit

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; C1E exit functional on NWP; verify frequency/voltage restoration**

**Priority**: High — `plc.feature.p1`; C1E exit correctness affects performance recovery after light-load idle periods
