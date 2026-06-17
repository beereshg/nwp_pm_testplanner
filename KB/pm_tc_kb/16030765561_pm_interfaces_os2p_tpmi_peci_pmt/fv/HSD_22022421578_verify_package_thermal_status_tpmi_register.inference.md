# Deep Analysis: [TPMI/PMT] Verify Package Thermal Status TPMI Register

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421578 |
| **Title** | [TPMI/PMT] Verify Package Thermal Status TPMI Register |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > TPMI/PMT |
| **Sub-Feature** | PMT PCS Index 20 — Package Thermal Status TPMI |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **Package Thermal Status TPMI register** (PCS index 20), which is accessible via MSR 0x1B1, PCU CR 0xfb984, and as an IO register. The register reports: Thermal Monitor Status (TM1/TM2 throttling active), Thermal Monitor Log (sticky), PROCHOT event, and related thermal status bits. On NWP, the same register and MSR exist. The TPMI interface is common to all Intel server platforms. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- `IA32_PACKAGE_THERM_STATUS` (MSR 0x1B1) is present on NWP
- TPMI `PACKAGE_THERM_STATUS` register mirrors MSR — same on NWP
- `DMR_PO` tag: silicon validation bring-up priority
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run PMT thermal test | `python runPmx.py -x nwp.xml -p pmt_thermal -tM 60 --retry_count 2` |
| 2 | Read `PACKAGE_THERM_STATUS` TPMI register | `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_therm_status.read()` |
| 3 | Read MSR 0x1B1 and compare to TPMI value | MSR and TPMI should be in sync; verify via MSR read tool |
| 4 | Trigger thermal throttle (stress workload or temp injection); verify `THERMAL_MONITOR_STATUS` = 1 | Same trigger mechanism on NWP |
| 5 | Verify `THERMAL_MONITOR_LOG` sticky bit set (stays set after throttle clears) | Same sticky behavior; clear with SW write |
| 6 | Trigger PROCHOT; verify `PROCHOT_EVENT` bit (requires board header) | Same as TC 22022421484 |

### PACKAGE_THERM_STATUS Key Bits

| Bits | Field | Description | NWP |
|------|-------|-------------|-----|
| 0 | `THERMAL_MONITOR_STATUS` | Core currently throttling | Same |
| 1 | `THERMAL_MONITOR_LOG` | Sticky throttle log | Same |
| 4 | `PROCHOT_EVENT` | Platform PROCHOT asserted | Same |
| 5 | `PROCHOT_LOG` | Sticky PROCHOT log | Same |
| 16:8 | `DIGITAL_READOUT` | Thermal margin to TJ_MAX | Same |
| 20 | `POWER_NOTIFICATION` | Package power limit exceeded | Same |

### MSR Cross-Reference

| Interface | Address/Path | NWP |
|-----------|-------------|-----|
| MSR | 0x1B1 | Same — x86 architectural MSR |
| PCU CR | 0xfb984 | Same PCU CR offset |
| TPMI IO | `ptpcioregs.ptpcioregs.package_therm_status` | Same path on NWP iMH |

### NWP Pass Criteria
- MSR 0x1B1 value matches TPMI `PACKAGE_THERM_STATUS`
- `THERMAL_MONITOR_STATUS` sets during throttle events
- `THERMAL_MONITOR_LOG` is sticky; clears only on explicit SW write
- `DIGITAL_READOUT` reflects current thermal margin

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| MSR 0x1B1 | Architectural | Same on NWP | No change |
| TPMI path | `ptpcioregs.ptpcioregs.package_therm_status` | Same on NWP | Direct reuse |
| Thermal throttle trigger | DMR workloads | NWP workloads | Same stress mechanism |

---

## Section D: Key Registers & Validation Points

```python
# NWP Package Thermal Status TPMI Validation

# TPMI register
try:
    pkg_therm_status = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_therm_status.read()
    print(f"PACKAGE_THERM_STATUS: 0x{pkg_therm_status:08X}")

    # Field breakdown
    tm_status = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_therm_status.thermal_monitor_status.read()
    tm_log = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_therm_status.thermal_monitor_log.read()
    digital_ro = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_therm_status.digital_readout.read()

    print(f"  THERMAL_MONITOR_STATUS: {tm_status}")
    print(f"  THERMAL_MONITOR_LOG: {tm_log}")
    print(f"  DIGITAL_READOUT (margin): {digital_ro} °C")
except Exception as e:
    print(f"PACKAGE_THERM_STATUS: {e}")

# Compare with MSR (if MSR read tool available)
# rdmsr -p 0 0x1B1  (Linux: sudo rdmsr 0x1B1)
```

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; no structural changes needed**

Package Thermal Status TPMI is an architectural register identical on NWP. Direct port.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p pmt_thermal -tM 60 --retry_count 2`
2. No register path changes — `ptpcioregs.package_therm_status` same on NWP

**Priority**: Medium — DMR_PO; thermal throttle status is a fundamental thermal reporting verification
