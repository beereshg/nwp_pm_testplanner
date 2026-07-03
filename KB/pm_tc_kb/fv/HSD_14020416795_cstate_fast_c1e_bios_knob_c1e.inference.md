# Deep Analysis: CState Fast C1E: BIOS Knob C1E Autopromotion

| Field | Value |
|-------|-------|
| **HSD ID** | 14020416795 |
| **Title** | CState Fast C1E: bios_knob C1E autopromotion_silicon |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | Fast C1E BIOS knob — enable/disable C1E auto-promotion |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **Fast C1E BIOS knob**: Fast C1E auto-promotion is always enabled when FastC1E is enabled. Uses `flexconPM.xml` to set/verify the BIOS knob.

Pass/fail criteria (from test steps):
```
sv.socket0.cbb0.compute3.core_pma4.core_pmsb_top.core_pma_pmsb.control_c1e.show()
```
And:
```
sv.socket0.cbb0.compute3.core_pma7.core_pmsb_top.core_pma_pmsb.telemetry_pcode_2.show()
io_telemetry_pcode_2[6] → C1E enable bit
```

Tags: `DMR_PO`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot SVOS | Boot with FastC1E BIOS knob = enabled |
| 2 | Run flexconPM | `flexconPM.py -c NWPSV.ini` (not `flexconPM.xml` directly) |
| 3 | Verify `control_c1e.enable = 1` via PythonSV | NWP path (adapt from DMR hierarchy) |
| 4 | Check `telemetry_pcode_2[6]` (io_telemetry_pcode_2) | C1E enable bit = 1 when FastC1E enabled |
| 5 | Disable FastC1E BIOS knob (NVRAM write + reboot) | BIOS knob = disabled |
| 6 | Verify `control_c1e.enable = 0` | C1E auto-promotion disabled |

### NWP Register Path Adaptation

```python
# DMR path (from test steps):
# sv.socket0.cbb0.compute3.core_pma4.core_pmsb_top.core_pma_pmsb.control_c1e.show()
# NWP equivalent (hierarchy may differ — verify via NWP PythonSV package):
# sv.socket0.cbb0.<compute>.<pma>.core_pmsb_top.core_pma_pmsb.control_c1e.show()
```

### NWP Notes
- `flexconPM.xml` → `flexconPM.py -c NWPSV.ini`
- NWP: no SMT; single thread per core, so C1E applies per physical core
- Fast C1E: hardware frequency reduction during C1 (before OS requests deeper C-state)

### Pass Criteria
- With FastC1E BIOS knob enabled: `control_c1e.enable = 1`; `io_telemetry_pcode_2[6] = 1`
- With FastC1E BIOS knob disabled: `control_c1e.enable = 0`
- Flexcon verification passes for C1E knob

---

## Section F: Recommendation

**Recommendation: ADOPT — `flexconPM.xml` → `flexconPM.py -c NWPSV.ini`; adapt core PMSB path to NWP hierarchy; C1E functional on NWP**

**Priority**: Medium — `DMR_PO`; Fast C1E is a key frequency reduction mechanism for light-load scenarios — BIOS knob must work correctly
