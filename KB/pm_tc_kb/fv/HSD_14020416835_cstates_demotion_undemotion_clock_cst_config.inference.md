# Deep Analysis: CStates Demotion/Undemotion CLOCK_CST_CONFIG_CONTROL (0xE2)

| Field | Value |
|-------|-------|
| **HSD ID** | 14020416835 |
| **Title** | CStates: Demotion/Undemotion: CLOCK_CST_CONFIG_CONTROL_MSR(0XE2) silicon |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | Demotion/Undemotion MSR bits (0xE2 bit25-28) — C1/C3 auto-demotion enable/disable |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **C-state demotion/undemotion** via `CLOCK_CST_CONFIG_CONTROL` (MSR 0xE2):
- Bit 25: `C3_STATE_AUTO_DEMOTION_ENABLE` — demote C6/C7 → C3 based on uncore hint
- Bit 26: `C1_STATE_AUTO_DEMOTION_ENABLE` — demote C3 → C1 based on uncore hint
- Bit 27: `C3_STATE_AUTO_UNDEMOTION_ENABLE`
- Bit 28: `C1_STATE_AUTO_UNDEMOTION_ENABLE`

Uses `pm.focus.cstate_focus.c6_demotion_focus()`. Tags: `NGA_MAIN`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### Demotion MSR Bits (NWP)

| Bit | Field | When Set |
|-----|-------|----------|
| 25 | C3_STATE_AUTO_DEMOTION | Pcode may demote C6/C7 → C3 |
| 26 | C1_STATE_AUTO_DEMOTION | Pcode may demote C3 → C1 |
| 27 | C3_STATE_AUTO_UNDEMOTION | Undo C3 demotion |
| 28 | C1_STATE_AUTO_UNDEMOTION | Undo C1 demotion |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot SVOS with C6 enabled | Demotion algorithm active |
| 2 | Run demotion focus test | `import pm.focus.cstate_focus as cf; cf.c6_demotion_focus()` (NWP package) |
| 3 | Enable C3 demotion (bit 25 = 1) | Set MSR 0xE2 bit 25 |
| 4 | Verify core demoted from C6→C3 | C-state in register = C3 instead of C6 |
| 5 | Enable C1 demotion (bit 26 = 1) | Set MSR 0xE2 bit 26 |
| 6 | Verify core demoted to C1 | C-state in register = C1 |
| 7 | Enable undemotion bits | Verify core returns to requested C6 |

### NWP Notes
- NWP has no C7 (only C6A/C6S/C6S-P)
- Demotion targets: C6 → C3 → C1
- `NGA_MAIN`: automate via NGA after manual checkout

### Pass Criteria
- With `C3_STATE_AUTO_DEMOTION_ENABLE=1`: cores demoted to C3 when uncore hint triggers
- With `C1_STATE_AUTO_DEMOTION_ENABLE=1`: further demotion to C1
- Undemotion bits allow return to requested C-state depth
- No system instability during demotion/undemotion cycles

---

## Section F: Recommendation

**Recommendation: ADOPT — MSR address 0xE2 unchanged on NWP; adapt Python import to NWP package; no C7 on NWP (demotion targets C6→C3→C1)**

**Priority**: Medium — `NGA_MAIN`, `plc.feature.p1`; demotion validation ensures OS-requested deep C-states are correctly handled when uncore is not ready
