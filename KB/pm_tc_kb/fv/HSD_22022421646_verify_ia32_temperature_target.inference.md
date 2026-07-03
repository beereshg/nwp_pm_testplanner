# Deep Analysis: [Thermal Reporting] Verify IA32_TEMPERATURE_TARGET

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421646 |
| **Title** | [Thermal Reporting] Verify IA32_TEMPERATURE_TARGET |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | MSR 0x1A2 TEMPERATURE_TARGET — TJ_MAX, fan offset, ref_temp fields |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **MSR 0x1A2 TEMPERATURE_TARGET** — a legacy discovery register with three key fields:
1. `TJ_MAX_TCC_OFFSET` (bits [6:0]): Customer-programmable TCC offset (default 0)
2. `FAN_TEMP_TARGET_OFFSET` (bits [15:8]) = `FUSE_TEMP_TARGET` — fan speed target
3. `REF_TEMP` (bits [23:16]) = `EFFECTIVE_TJMAX - FUSE_DTS_CAL_GUARDBAND`

Additional field: `TCC_OFFSET_TIME_WINDOW` (bits [6:0]) for RATL averaging.

On NWP, same MSR with same field definitions. `pcode_dts_cal_guardband` fuse at same path.

**Key Justification:**
- `Ready_for_testing` + `plc.feature.p1` + `NGA_MAIN` + `PMSS_NWP_READINESS_CHECK` tags
- Standard temperature target register; NWP direct applicability

---

## Section B: NWP-Specific Test Procedure

### MSR 0x1A2 Fields

| Bits | Field | Formula/Source |
|------|-------|---------------|
| [6:0] | `TCC_OFFSET_TIME_WINDOW` | RATL averaging window |
| [6:0] | `TJ_MAX_TCC_OFFSET` | Platform programmable; default = 0 |
| [15:8] | `FAN_TEMP_TARGET_OFFSET` | = `FUSE_TEMP_TARGET` fuse |
| [23:16] | `REF_TEMP` | = `EFFECTIVE_TJMAX - FUSE_DTS_CAL_GUARDBAND` |

### NWP Verification

```python
import svtools.common.baseaccess as baseaccess
base = baseaccess.getglobalbase()

temp_target = base.rdmsr(0x1A2)
tcc_offset = (temp_target >> 24) & 0x3F
fan_offset = (temp_target >> 8) & 0xFF
ref_temp = (temp_target >> 16) & 0xFF

print(f"MSR 0x1A2 TEMPERATURE_TARGET: 0x{temp_target:08X}")
print(f"  TCC_OFFSET (TJ_MAX_TCC_OFFSET): {tcc_offset}")
print(f"  FAN_TEMP_TARGET_OFFSET: {fan_offset}")
print(f"  REF_TEMP: {ref_temp}")

# Verify REF_TEMP = EFFECTIVE_TJMAX - FUSE_DTS_CAL_GUARDBAND
dts_guardband = sv.socket0.imh0.fuses.punit.pcode_dts_cal_guardband.read()
effective_tjmax = ref_temp + dts_guardband
print(f"  Derived EFFECTIVE_TJMAX: {effective_tjmax} (= REF_TEMP {ref_temp} + DTS_GB {dts_guardband})")
```

### NWP Pass Criteria
- `REF_TEMP = EFFECTIVE_TJMAX - FUSE_DTS_CAL_GUARDBAND`
- `FAN_TEMP_TARGET_OFFSET = FUSE_TEMP_TARGET` fuse value
- `TJ_MAX_TCC_OFFSET` defaults to 0 (no customer offset applied)

---

## Section F: Recommendation

**Recommendation: ADOPT — thermalManagement.py + same fuse path on NWP**

Required adaptations:
1. Use `thermalManagement.py` from NWP PythonSV repo
2. Verify `pcode_dts_cal_guardband` fuse name on NWP (expected same)

**Priority**: Medium — `plc.feature.p1` + `NGA_MAIN`; temperature target bring-up check
