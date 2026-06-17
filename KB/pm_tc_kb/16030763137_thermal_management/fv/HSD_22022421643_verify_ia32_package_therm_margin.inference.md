# Deep Analysis: [Thermal Reporting] Verify IA32_PACKAGE_THERM_MARGIN

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421643 |
| **Title** | [Thermal Reporting] Verify IA32_PACKAGE_THERM_MARGIN |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | MSR 0x1A1 PACKAGE_THERM_MARGIN — fan speed margin in 8.8 format |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **MSR 0x1A1 PACKAGE_THERM_MARGIN**:
- Thermal margin in 8.8 fixed-point format (bits [15:0])
- Used for fan speed control by platform
- Pass/Fail: margin value congruent with formula:
  `ref_temp + dts_cal_guardband + fan_speed_offset`

On NWP, the same `pcode_dts_cal_guardband` fuse exists at `sv.socket0.imh0.fuses.punit.pcode_dts_cal_guardband` and the thermal margin formula applies.

**Key Justification:**
- `Ready_for_testing` + `plc.feature.p1` + `NGA_MAIN` + `PMSS_NWP_READINESS_CHECK` tags
- Standard thermal margin MSR; fuse path same on NWP

---

## Section B: NWP-Specific Test Procedure

### Thermal Margin Formula

```
THERM_MARGIN = ref_temp + dts_cal_guardband + fan_speed_offset
```

Where:
- `ref_temp`: from `IA32_TEMPERATURE_TARGET.REF_TEMP` bits [23:16]
- `dts_cal_guardband`: fuse `sv.socket0.imh0.fuses.punit.pcode_dts_cal_guardband`
- `fan_speed_offset`: from `IA32_TEMPERATURE_TARGET.FAN_TEMP_TARGET_OFFSET` bits [15:8]

### NWP Verification

```python
import svtools.common.baseaccess as baseaccess
base = baseaccess.getglobalbase()

# Read PACKAGE_THERM_MARGIN
pkg_therm_margin = base.rdmsr(0x1A1)
therm_margin_raw = pkg_therm_margin & 0xFFFF
therm_margin = therm_margin_raw / 256.0  # 8.8 format
print(f"PACKAGE_THERM_MARGIN: {therm_margin:.3f} degrees C (raw: 0x{therm_margin_raw:04X})")

# Read TEMPERATURE_TARGET for calculation
temp_target = base.rdmsr(0x1A2)
ref_temp = (temp_target >> 16) & 0xFF
fan_speed_offset = (temp_target >> 8) & 0xFF

# Read DTS cal guardband fuse
dts_guardband = sv.socket0.imh0.fuses.punit.pcode_dts_cal_guardband.read()

expected_margin = ref_temp + dts_guardband + fan_speed_offset
print(f"ref_temp={ref_temp}, dts_guardband={dts_guardband}, fan_speed_offset={fan_speed_offset}")
print(f"Expected margin: {expected_margin}")
print(f"PASS" if abs(therm_margin - expected_margin) < 1.0 else "FAIL")
```

### NWP Pass Criteria
- `THERM_MARGIN` value matches formula: `ref_temp + dts_cal_guardband + fan_speed_offset`
- Margin updates dynamically as die temperature changes
- Register accessible from package scope

---

## Section F: Recommendation

**Recommendation: ADOPT — thermalManagement.py script + same fuse path on NWP**

Required adaptations:
1. Use `thermalManagement.py` from NWP PythonSV repo (same script, `sv.socket0.imh0` path)
2. Verify `pcode_dts_cal_guardband` fuse name on NWP (same as DMR)

**Priority**: Medium — `plc.feature.p1` + `NGA_MAIN`; thermal margin fan control verification
