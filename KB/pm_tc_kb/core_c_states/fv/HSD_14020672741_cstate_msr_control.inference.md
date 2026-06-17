# Deep Analysis: CState MSR Control

| Field | Value |
|-------|-------|
| **HSD ID** | 14020672741 |
| **Title** | CState MSR Control |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | CLOCK_CST_CONFIG_CONTROL (MSR 0xE2), C1E enable (MSR 0x1FC), MonitorMwait — enable/disable validation |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies MSR-based C-state control knobs:
- `CLOCK_CST_CONFIG_CONTROL` (MSR 0xE2): C-state feature enable/disable bits
- `C1E enable` (MSR 0x1FC): Fast C1E enable
- `MonitorMwait enable/disable` (MSR 0xE2): MWAIT instruction enable

Uses `pm.focus.cstate_focus.c6_msr_control()`. Tags: `DMR_PO`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### C-State Control MSRs (NWP)

| MSR | Name | Relevant Bits |
|-----|------|---------------|
| 0xE2 | CLOCK_CST_CONFIG_CONTROL | MonitorMwait enable, C-state promotion/demotion enable |
| 0x1FC | C1E enable | Fast C1E auto-promotion enable |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot SVOS with C-states enabled | C6 functional on NWP |
| 2 | Run cstate_focus MSR test | `import pm.focus.cstate_focus as cf; cf.c6_msr_control()` with NWP python path |
| 3 | Verify C1E enable (MSR 0x1FC) | Write 0/1; verify core C1E state changes |
| 4 | Verify MonitorMwait enable (MSR 0xE2 bit) | Enable/disable; verify MWAIT behaves correctly |
| 5 | Verify CLOCK_CST_CONFIG features | Each bit drives correct hardware behavior |

### NWP Notes
- NWP Python package path: `from newport.pm.focus import cstate_focus` (or NWP equivalent)
- No SMT: no "HT-awareness" consideration for MSR scope; per-core only
- `runPmx.py -x nwp.xml -p cstates -H 1 -M 5` for automated run

### Pass Criteria
- MSR 0xE2 MonitorMwait enable/disable: MWAIT responds correctly to enable state
- MSR 0x1FC C1E enable: C1E auto-promotion only when bit set
- CLOCK_CST_CONFIG_CONTROL features match hardware behavior per spec
- MSR writes take effect immediately (no reboot required)

---

## Section F: Recommendation

**Recommendation: ADOPT — MSR addresses the same on NWP; update Python import path to NWP package; no SMT consideration**

**Priority**: Medium — `plc.feature.p1`; MSR C-state control is used by OS power management — must work correctly
