# Deep Analysis: CState Fast C1E: Entry Flow Silicon

| Field | Value |
|-------|-------|
| **HSD ID** | 14020416803 |
| **Title** | CState Fast C1E: Entry flow_silicon |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | Fast C1E entry flow — frequency reduction, voltage setpoint, C1E period |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **Fast C1E entry flow**. When a core enters C1E:
1. Frequency reduces to C1E working point (WP)
2. Voltage reduces to Vmin
3. Frequency = 4 (for 400MHz C1E WP)
4. `acp_state.c1e_period = 1`

Uses `pm.focused.cstate_focus.check_cst_focus()`. Tags: `DMR_PO`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### C1E Entry Pass/Fail Criteria

| Signal | Expected During C1E |
|--------|---------------------|
| `pma.control_c1e.enable` | 1 (C1E enabled) |
| `pma.io_c1e_wp.core_voltage` | Vmin (varies by SKU) |
| `pma.io_c1e_wp.core_frequency` | 4 (400 MHz) |
| `pma.acp_state.core_ratio` | = C1E WP ratio |
| `pma.acp_state.core_voltage` | = C1E WP voltage |
| `pma.acp_state.c1e_period` | 1 (in C1E) |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot SVOS with C1E enabled | FastC1E BIOS knob on |
| 2 | Run cstate focus | `import pm.focused.cstate_focus as cf; cf.check_cst_focus()` |
| 3 | OR run via PMx | `python runPmx.py -x nwp.xml -p cstates -H 1 -M 5` |
| 4 | Idle core → OS requests C1E | Core enters C1 → promotes to C1E |
| 5 | Verify frequency = 400MHz | `io_c1e_wp.core_frequency = 4` |
| 6 | Verify voltage at Vmin | `io_c1e_wp.core_voltage` per SKU spec |
| 7 | Verify `c1e_period = 1` | In C1E state |

### NWP PMA Path Adaptation
```python
# DMR PMA path (from test steps):
# pma.control_c1e.enable
# pma.io_c1e_wp.core_voltage, .core_frequency
# pma.acp_state.core_ratio, .core_voltage, .c1e_period
# NWP: adapt to NWP CBB/compute/pma hierarchy
# sv.socket0.cbb0.compute0.pma0.core_pmsb_top.core_pma_pmsb.<field>
```

### Pass Criteria
- `control_c1e.enable = 1` during C1E
- Frequency = 4 (400 MHz) at C1E WP
- Voltage = Vmin at C1E WP
- `c1e_period = 1` during C1E dwell

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; adapt PMA register paths to NWP hierarchy; C1E functional on NWP**

**Priority**: High — `plc.feature.p1`; Fast C1E entry validation is critical for idle power — frequency/voltage at WP determines C1E power savings
