# Deep Analysis: Legacy Pstate Bios Configurations

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422219 |
| **Title** | Legacy Pstate Bios cofigurations |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | Legacy P-states BIOS menu verification |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies BIOS menu options for Legacy P-states (SpeedStep/GV3):
- **SpeedStep (Legacy P-states)**: Enable → `IA32_MISC_ENABLES[ENABLE_GV3] = 1`; Disable → `= 0`
- **Single PCTL**: Enable → `MISC_PWR_MGMT[0] = 1` + PSD ACPI coord type = SW_ANY
- **EIST PSD HW_ALL**: Set PSD coord type to HW_ALL
- **SW_ALL**: Set PSD coord type to SW_ALL

On NWP, the same legacy P-state BIOS menu and MSR registers are present. `IA32_MISC_ENABLES` and `MISC_PWR_MGMT` are architectural MSRs.

**Key Justification:**
- Legacy P-state BIOS knobs (`SpeedStep`, `MISC_PWR_MGMT`) present on NWP
- Same MSR interface: `IA32_MISC_ENABLES` (0x1A0), `MISC_PWR_MGMT` (0x1AA)
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP
- No specific `DMR_PO` tag — not DMR bring-up critical; generally applicable

---

## Section B: NWP-Specific Test Procedure

### BIOS Knob Mapping

| BIOS Option | NWP Action | MSR Effect |
|-------------|------------|------------|
| SpeedStep = Enable | Same BIOS knob on NWP | `IA32_MISC_ENABLES[16] = 1` (GV3 enable) |
| SpeedStep = Disable | Same BIOS knob on NWP | `IA32_MISC_ENABLES[16] = 0` |
| Single PCTL = Enable | Same BIOS knob | `MISC_PWR_MGMT[0] = 1`, PSD coord = SW_ANY |
| EIST PSD HW_ALL | Same BIOS knob | PSD coord = HW_ALL |
| SW_ALL | Same BIOS knob | PSD coord = SW_ALL |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Set SpeedStep = Enable; reboot | Verify `IA32_MISC_ENABLES.read() & (1<<16) == (1<<16)` |
| 2 | Set SpeedStep = Disable; reboot | Verify `IA32_MISC_ENABLES.read() & (1<<16) == 0` |
| 3 | Set Single PCTL = Enable; reboot | Verify `MISC_PWR_MGMT.read() & 1 == 1`; PSD object = SW_ANY |
| 4 | Verify PSD ACPI node options (HW_ALL, SW_ALL) | Same ACPI structure on NWP |
| 5 | Run flexcon validation | `flexcon` command with NWP platform config |

### NWP Pass Criteria
- MSRs reflect BIOS knob settings after reboot
- PSD coordination type matches BIOS configuration
- No unexpected P-state behavior based on coordination type

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| `IA32_MISC_ENABLES[16]` (GV3/SpeedStep) | Present | Same x86 architectural MSR | Direct reuse |
| `MISC_PWR_MGMT[0]` (single PCTL) | Present | Same | Direct reuse |
| BIOS knob names | DMR BIOS | NWP BIOS may use same/different knob names | Verify with NWP BIOS team |
| PSD ACPI object | Standard ACPI | Same structure | Direct reuse |

---

## Section D: Key Registers & Validation Points

```python
# NWP Legacy P-state BIOS configuration verification

import pysvtools.xmlcli as xmlcli

# Check IA32_MISC_ENABLES[16] (Enhanced Intel SpeedStep = GV3)
try:
    misc_en = sv.socket0.imh0.punit.ptpcioregs.ia32_misc_enables.read()
    gv3 = (misc_en >> 16) & 1
    print(f"IA32_MISC_ENABLES: 0x{misc_en:016X}")
    print(f"  GV3 (SpeedStep): {gv3} (expected = BIOS setting)")
except Exception as e:
    print(f"IA32_MISC_ENABLES: {e}")

# Check MISC_PWR_MGMT[0] (Single PCTL)
try:
    misc_pwr = sv.socket0.imh0.punit.ptpcioregs.misc_pwr_mgmt.read()
    single_pctl = misc_pwr & 1
    print(f"MISC_PWR_MGMT: 0x{misc_pwr:08X}")
    print(f"  Single PCTL[0]: {single_pctl}")
except Exception as e:
    print(f"MISC_PWR_MGMT: {e}")
```

---

## Section F: Recommendation

**Recommendation: ADOPT — BIOS knobs and MSRs are architecturally identical on NWP**

Legacy P-state BIOS menu verification is applicable on NWP. Primary risk is BIOS knob naming differences.

Required adaptations:
1. Verify NWP BIOS knob names match DMR (SpeedStep, Single PCTL equivalent)
2. `flexcon` command may need NWP platform XML or config

**Priority**: Low — no `DMR_PO` tag; BIOS configuration baseline verification
