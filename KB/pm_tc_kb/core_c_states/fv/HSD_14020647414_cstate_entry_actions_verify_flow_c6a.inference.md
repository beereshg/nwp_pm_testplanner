# Deep Analysis: CState Entry Actions: Verify Flow C6A

| Field | Value |
|-------|-------|
| **HSD ID** | 14020647414 |
| **Title** | CState Entry Actions: Verify Flow C6A |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | C6A (Autonomous C6) entry flow — register state verification |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **C6A (Autonomous C6) entry flow** by checking key registers after core enters C6A. C6A = hardware-autonomous entry (no OS involvement), minimal power state. Functional on NWP.

Tags: `logs`, `cmdline`, `DMR_PO`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### C6A Entry Pass/Fail Criteria (from test steps)

| Signal | Expected After C6A Entry |
|--------|--------------------------|
| `core_cstate` | C6 |
| PICLET FSM | `PICLET_ENABLED` |
| SRL | `SRL_ACTIVE` |
| `BGF_RUN` | 0 (bypassed) |
| `CORE_PWR_GOOD` | 0 (power off) |
| `PLL_LOCK` | 0 (PLL off) |
| Target Volt | 0 (voltage collapsed) |
| Target Freq | 0 |
| Target PS | 7 (deepest power state) |

*C6A: Autonomous — core decides to enter C6 based on hardware idle detection.*

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot SVOS with C6 enabled via fuses/BIOS | C6A functional on NWP |
| 2 | Run cstates PMx | `python runPmx.py -x nwp.xml -p cstates -H 1 -M 5` |
| 3 | OR standalone | `python /usr/lib/python3/dist-packages/newport/pm/Idle_PM/cstates/ccx_residency_test.py` |
| 4 | Idle a specific core (no workload on that thread) | Core should autonomously enter C6A |
| 5 | Sample core state registers (fast polling or trace) | Check all signals above match C6A criteria |
| 6 | Trigger work to exit C6A | Resume C0; verify exit signals |

### NWP PythonSV Register Paths
```python
# NWP C6A entry verification (path structure needs NWP package validation)
# Example for one core in cbb0:
core_pma = sv.socket0.cbb0.compute0.pma0
core_pma.core_pmsb_top.core_pma_pmsb.gvctrl_status_core.show()  # core_cstate, BGF_RUN
# Verify PICLET, SRL, PLL_LOCK via appropriate NWP PMSB registers
```

### Pass Criteria
- All signals match expected C6A state table above
- No premature exit from C6A without work trigger
- Entry is autonomous (no explicit OS C-state request needed)

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; adapt core PMSB paths to NWP hierarchy; verify C6A entry signals**

**Priority**: High — `plc.feature.p1`; C6A entry flow verification is fundamental to idle power validation on NWP
