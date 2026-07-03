# Deep Analysis: [Thermal Interrupts] Verify IA32_PACKAGE_THERM_INTERRUPT (Pkg MSR 0x1b2)

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421610 |
| **Title** | [Thermal Interrupts] Verify IA32_PACKAGE_THERM_INTERRUPT (Pkg MSR 0x1b2) |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | MSR 0x1B2 PACKAGE_THERM_INTERRUPT — all interrupt enables at package scope |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies **Package MSR 0x1B2 IA32_PACKAGE_THERM_INTERRUPT** — package-scoped control for all thermal interrupts:
- HIGH_TEMP, LOW_TEMP, PROCHOT, OUT_OF_SPEC, THRESHOLD_1, THRESHOLD_2

This is the "umbrella" TC for the package-level thermal interrupt register. Covers all interrupt types in one register. On NWP, same MSR at package scope.

**Key Justification:**
- `DMR_PO` + `plc.feature.p1` + `PMSS_NWP_READINESS_CHECK` tags
- Package thermal interrupt MSR directly applicable on NWP

---

## Section B: NWP-Specific Test Procedure

### MSR 0x1B2 Interrupt Enables

| Bit | Interrupt | Description |
|-----|-----------|-------------|
| [0] | HIGH_TEMP_INT_ENABLE | Trip point high |
| [1] | LOW_TEMP_INT_ENABLE | Trip point low |
| [2] | PROCHOT_INT_ENABLE | PROCHOT# assertion |
| [3] | OOS_INT_ENABLE | Out-of-spec (critical temp) |
| [8:15] | THRESHOLD_1_REL_TEMP | Degrees below Tj_max |
| [16] | THRESHOLD_1_INT_ENABLE | Threshold 1 crossing |
| [24:31] | THRESHOLD_2_REL_TEMP | Degrees below Tj_max |
| [32] | THRESHOLD_2_INT_ENABLE | Threshold 2 crossing |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read MSR 0x1B2 baseline | All enables = 0 by default |
| 2 | Enable all interrupts one by one | Verify enable bits writable |
| 3 | Run thermal_interrupt PMx | `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5` |
| 4 | Trigger each condition; verify interrupt fires | HIGH, LOW, PROCHOT, OOS, THR1, THR2 |

### NWP Pass Criteria
- MSR 0x1B2 accessible and writable at package scope
- All 6 interrupt types generate APIC thermal interrupt when enabled
- Interrupt clears when condition removed

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; package thermal interrupt MSR same on NWP**

1. `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5`

**Priority**: High — `DMR_PO` + `plc.feature.p1`; package thermal interrupt bring-up gate
