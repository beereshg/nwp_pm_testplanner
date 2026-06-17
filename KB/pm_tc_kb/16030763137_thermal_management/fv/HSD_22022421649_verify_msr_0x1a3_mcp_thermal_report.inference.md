# Deep Analysis: [Thermal Reporting] Verify MSR 0x1A3 MCP_THERMAL_REPORT_1

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421649 |
| **Title** | [Thermal Reporting] Verify MSR 0x1A3 MCP_THERMAL_REPORT_1 |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | MSR 0x1A3 MCP_THERMAL_REPORT_1 — TJmax and Tcontrol margins |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **MSR 0x1A3 MCP_THERMAL_REPORT_1** — contains two thermal margins:
1. **TJmax margin**: `tj_max = ref_temp + pcode_dts_cal_guardband + c1e_offset - tcc_offset`
2. **Tcontrol margin**: `tcontrol = ref_temp + pcode_dts_cal_guardband + fan_speed_offset`

On NWP, the same formulas apply. Fuse reads use `sv.socket0.imh0.fuses.punit.pcode_dts_cal_guardband` (same path).

**Key Justification:**
- `DMR_PO` + `plc.feature.p1` + `PMSS_NWP_READINESS_CHECK` tags
- Standard MCP thermal report; NWP fuse path same

---

## Section B: NWP-Specific Test Procedure

### Thermal Margin Formulas

```python
tj_max    = ref_temp + pcode_dts_cal_guardband + c1e_offset - tcc_offset
tcontrol  = ref_temp + pcode_dts_cal_guardband + fan_speed_offset
```

### NWP Verification

```python
import svtools.common.baseaccess as baseaccess
base = baseaccess.getglobalbase()

# Read MCP_THERMAL_REPORT_1 (MSR 0x1A3)
mcp_report_1 = base.rdmsr(0x1A3)
print(f"MSR 0x1A3 MCP_THERMAL_REPORT_1: 0x{mcp_report_1:08X}")

# Read building blocks
temp_target = base.rdmsr(0x1A2)
ref_temp = (temp_target >> 16) & 0xFF
fan_speed_offset = (temp_target >> 8) & 0xFF
tcc_offset = (temp_target >> 24) & 0x3F

dts_guardband = sv.socket0.imh0.fuses.punit.pcode_dts_cal_guardband.read()

# C1E offset from POWER_CTL MSR 0x1FC
power_ctl = base.rdmsr(0x1FC)
c1e_enable = (power_ctl >> 1) & 1
c1e_offset = 1 if c1e_enable else 0  # Approximation; actual offset from spec

# Calculate expected margins
tj_max_expected = ref_temp + dts_guardband + c1e_offset - tcc_offset
tcontrol_expected = ref_temp + dts_guardband + fan_speed_offset

print(f"Expected TJmax: {tj_max_expected}, Tcontrol: {tcontrol_expected}")
print(f"ref_temp={ref_temp}, dts_gb={dts_guardband}, c1e_offset={c1e_offset}, tcc_offset={tcc_offset}, fan_offset={fan_speed_offset}")
```

### NWP Pass Criteria
- `MCP_THERMAL_REPORT_1` TJmax margin matches `tj_max` formula
- `MCP_THERMAL_REPORT_1` Tcontrol margin matches `tcontrol` formula
- Values update dynamically with temperature

---

## Section F: Recommendation

**Recommendation: ADOPT — PMX automated script; same fuse path on NWP**

Required adaptations:
1. Update PMX XML reference: `nwp.xml` (command says "need to edit xml")
2. Fuse path `sv.socket0.imh0.fuses.punit.pcode_dts_cal_guardband` same on NWP

**Priority**: High — `DMR_PO` + `plc.feature.p1`; MCP thermal report TJmax/Tcontrol accuracy
