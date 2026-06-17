# Deep Analysis: [Thermal Reporting] Verify MSR 0x1A4 MCP_THERMAL_REPORT_2

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421650 |
| **Title** | [Thermal Reporting] Verify MSR 0x1A4 MCP_THERMAL_REPORT_2 |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | MSR 0x1A4 MCP_THERMAL_REPORT_2 — package temperature (supersedes GNR ZBB) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **MSR 0x1A4 MCP_THERMAL_REPORT_2** — the replacement for "Package Temperature" which was ZBB on GNR. This MSR reports:
- `temp_tj_max = ref_temp + pcode_dts_cal_guardband + [additional offsets]`

On NWP (like DMR), `MCP_THERMAL_REPORT_2` is the authoritative package temperature register. Same fuse path.

**Key Justification:**
- `Ready_for_testing` + `plc.feature.p1` + `NGA_MAIN` + `PMSS_NWP_READINESS_CHECK` tags
- MCP_THERMAL_REPORT_2 supersedes GNR ZBB package_temperature; fully applicable on NWP

---

## Section B: NWP-Specific Test Procedure

### TJmax Formula from MSR 0x1A4

```python
temp_tj_max = ref_temp + pcode_dts_cal_guardband + [additional_offset]
```

### NWP Verification

```python
import svtools.common.baseaccess as baseaccess
base = baseaccess.getglobalbase()

# Read MCP_THERMAL_REPORT_2 (MSR 0x1A4)
mcp_report_2 = base.rdmsr(0x1A4)
print(f"MSR 0x1A4 MCP_THERMAL_REPORT_2: 0x{mcp_report_2:08X}")

# Decode temperature fields (bits depend on spec)
pkg_temp = mcp_report_2 & 0xFF  # Approximation; check spec for exact bits
print(f"Package Temperature margin: {pkg_temp}°C below Tj_max")

# Read DTS calibration guardband fuse
dts_guardband = sv.socket0.imh0.fuses.punit.pcode_dts_cal_guardband.read()

# Read REF_TEMP
temp_target = base.rdmsr(0x1A2)
ref_temp = (temp_target >> 16) & 0xFF

temp_tj_max_expected = ref_temp + dts_guardband
print(f"Expected temp_tj_max base: {temp_tj_max_expected}")
print(f"pcode_dts_cal_guardband={dts_guardband}, ref_temp={ref_temp}")
```

### NWP Pass Criteria
- `MCP_THERMAL_REPORT_2` reports valid package temperature
- Value consistent with `temp_tj_max` formula
- Register updated dynamically with die temperature
- Confirms GNR ZBB package_temperature is correctly replaced by this MSR

---

## Section F: Recommendation

**Recommendation: ADOPT — thermalManagement.py; same formula and fuse path on NWP**

Required adaptations:
1. Use `thermalManagement.py` from NWP PythonSV repo
2. Verify `pcode_dts_cal_guardband` fuse at `sv.socket0.imh0.fuses.punit.*` on NWP

**Priority**: Medium — `plc.feature.p1` + `NGA_MAIN`; package temperature reporting verification
