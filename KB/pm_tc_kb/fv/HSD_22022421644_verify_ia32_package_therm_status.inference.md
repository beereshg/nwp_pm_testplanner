# Deep Analysis: [Thermal Reporting] Verify IA32_PACKAGE_THERM_STATUS

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421644 |
| **Title** | [Thermal Reporting] Verify IA32_PACKAGE_THERM_STATUS |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | MSR 0x1B1 PACKAGE_THERM_STATUS — package-scoped thermal status bits |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **MSR 0x1B1 PACKAGE_THERM_STATUS** — package-scoped thermal status register containing:
- Current value + sticky log bits for: TM, PROCHOT, OOS, Threshold 1/2, Power Limit, Pmax, HW Feedback Notification
- Current Temperature, resolution and valid bit
- Both current status and sticky log bits must be verified

On NWP, the same package thermal status MSR is present. `dmr.xml` → `nwp.xml`.

**Key Justification:**
- `DMR_PO` + `plc.feature.p1` + `PMSS_NWP_READINESS_CHECK` tags
- Standard package thermal status; NWP direct applicability

---

## Section B: NWP-Specific Test Procedure

### MSR 0x1B1 Key Bits

| Bit | Field | Description |
|-----|-------|-------------|
| [0] | THERMAL_MONITOR_STATUS | TM currently throttling |
| [1] | THERMAL_MONITOR_LOG | Sticky: TM tripped |
| [2] | PROCHOT_EVENT | PROCHOT# asserted |
| [3] | PROCHOT_LOG | Sticky: PROCHOT seen |
| [10] | POWER_LIMIT_STATUS | Power limit triggered |
| [22:16] | TEMPERATURE | Current die temperature (°C below Tj_max) |
| [29] | RESOLUTION | Temperature reading resolution |
| [31] | VALID | Temperature reading valid |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run thermal_interrupt PMx | `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5` |
| 2 | Read MSR 0x1B1 baseline | All status bits clear; temperature valid |
| 3 | Force thermal condition (EMTTM) | Reduce cooling or force TCC assertion |
| 4 | Verify TM_STATUS and TM_LOG bits set | Bits [0] and [1] |
| 5 | Assert PROCHOT#; verify PROCHOT bits | Bits [2] and [3] |
| 6 | Clear sticky bits; verify they clear | Write 0 to log bits |

### NWP Pass Criteria
- MSR 0x1B1 accessible (package-scoped)
- All status bits update correctly when thermal events occur
- Sticky log bits set on event; clear on SW write
- Temperature field valid and changing with die temperature

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; package thermal status same on NWP**

Required adaptations:
1. `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5`
2. NWP single socket: package thermal MSR at `sv.socket0.imh0` path

**Priority**: High — `DMR_PO` + `plc.feature.p1`; package thermal status bring-up check
