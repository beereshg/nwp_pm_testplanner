# Deep Analysis: CState dfx_ctrl_unprotected.core_cstate_limit Checkout

| Field | Value |
|-------|-------|
| **HSD ID** | 14020416757 |
| **Title** | CState dfx_ctrl_unprotected.core_cstate_limit checkout_silicon |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | dfx_ctrl_unprotected CORE_CSTATE_LIMIT field — fuse verification and runtime adjustment |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that:
1. The `dfx_ctrl_unprotected.core_cstate_limit` register is driven from fuses
2. Adjusting the field at runtime changes the maximum allowed C-state depth for cores

NWP has functional core-level C-states (C6A, C6S, C6S-P). The `core_cstate_limit` field is in an unprotected DFX register accessible via PythonSV. Tags: `DMR_PO`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### NWP DFX C-State Limit Register

| Field | Description |
|-------|-------------|
| `CORE_CSTATE_LIMIT [2:0]` | Max C-state depth for IA threads: 0=C0, 1=C1, 2=C1E, 6=C6, 7=No limit |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run cstates PMx | `python runPmx.py -x nwp.xml -p cstates -H 1 -M 5` |
| 2 | Read fuse-driven value of `core_cstate_limit` | `sv.socket0.imh0.punit.<dfx_ctrl>.core_cstate_limit.read()` |
| 3 | Verify core C-states enter up to fuse-allowed depth | Check C6 residency at idle |
| 4 | Adjust `core_cstate_limit` to C1 (value=1) | `sv.socket0.imh0.punit.<dfx_ctrl_unprotected>.core_cstate_limit.write(1)` |
| 5 | Verify cores can no longer enter C6 | Residency counter for C6 = 0 |
| 6 | Restore `core_cstate_limit` to max | Write original fuse value |
| 7 | Verify C6 residency resumes | C6 residency counter increments again |

### NWP Notes
- `dmr.xml` → `nwp.xml`
- Exact NWP register path for `dfx_ctrl_unprotected` to be confirmed via PythonSV hierarchy for NWP
- NWP: 2 CBBs × 48 cores = 96 cores; core_cstate_limit applies globally

### Pass Criteria
- `core_cstate_limit` reset value matches fuse-driven default
- Setting limit to C1 prevents C6 entry (C6 residency = 0)
- Restoring limit enables C6 entry again

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; core C6 functional on NWP; confirm `dfx_ctrl_unprotected` path in NWP PythonSV package**

**Priority**: Medium — `plc.feature.p1`; CORE_CSTATE_LIMIT is a key DFX debug lever for controlling C-state depth during bringup
