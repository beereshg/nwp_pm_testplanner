# Deep Analysis: RAPL IMON Addressing and Telemetry

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422042 |
| **Title** | RAPL IMON Addressing and Telemetry |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | SVID IMON addressing (ADDR_CONFIG, IFC_CONFIG, IMON_MASK) and telemetry accuracy |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **SVID IMON (current monitor) addressing and telemetry**:
1. SVID `ADDR_CONFIG[15:0]` — VR SVID address configuration
2. SVID `IFC_CONFIG[1:0]` — interface configuration
3. SVID `IMON_MASK` — current monitor enable mask
4. Telemetry accuracy: IMON telemetry from VR matches expected current at TDP

NWP uses VCCIN VR SVID address for iMH Punit current telemetry. Tags: `NGA_MAIN`, `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP SVID IMON Configuration Registers

| Register | Description |
|----------|-------------|
| `SVID_ADDR_CONFIG[15:0]` | Configures SVID slave addresses for each SVID rail |
| `SVID_IFC_CONFIG[1:0]` | Configures SVID interface (2-rail vs 4-rail, clock speed) |
| `SVID_IMON_MASK` | Bit mask enabling IMON telemetry per VR |

*Note: Exact namednodes paths for SVID registers require hardware-specific discovery; register names follow standard SVID controller interface.*

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read SVID ADDR_CONFIG | Verify VCCIN VR SVID addresses match platform BOM |
| 2 | Read SVID IFC_CONFIG | Verify interface (2-rail or 4-rail) matches NWP platform |
| 3 | Read SVID IMON_MASK | Verify IMON enabled for VCCIN (and other rails) |
| 4 | Run TDP workload | `./ptu -ct 3` across 96 NWP cores |
| 5 | Read IMON telemetry | From Punit SVID VR status or RAPL TPMI energy delta |
| 6 | Compare IMON-derived power to RAPL energy status | Should agree within tolerance |
| 7 | Verify IMON accuracy at idle | Low current reading at idle |

### NWP Platform Notes
- NWP uses a single iMH (`imh0`) Punit as the SVID master
- VCCIN VR is primary rail for current telemetry
- `NGA_MAIN` tag: this test may run under NGA automation

### Telemetry Cross-Check

```python
# NWP IMON telemetry vs RAPL energy (cross-check)
import time

# Read RAPL energy delta for power estimate
e1 = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status.read()
t1 = time.time()
# <run workload>
time.sleep(5)
e2 = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status.read()
t2 = time.time()

# Power unit from socket_rapl_power_unit
# power_W = (e2-e1) * energy_unit_J / (t2-t1)
print(f"RAPL-derived power: {(e2-e1)/(t2-t1):.2f} (raw units)")

# Cross-check vs IMON telemetry from Punit VR status registers
```

### Pass Criteria
- SVID `ADDR_CONFIG` matches expected VCCIN VR addresses for NWP platform BOM
- SVID `IFC_CONFIG` matches NWP SVID interface configuration
- SVID `IMON_MASK` enables IMON telemetry for all relevant rails
- IMON-derived current at TDP workload agrees with RAPL energy-based power (within ±5%)
- IMON telemetry at idle is low (expected idle current)

---

## Section F: Recommendation

**Recommendation: ADOPT — NWP single iMH Punit SVID master; VCCIN VR SVID addresses specific to NWP platform BOM**

1. Verify SVID ADDR_CONFIG addresses match NWP platform BOM (VCCIN VR physical addresses)
2. Verify SVID IFC_CONFIG matches NWP SVID interface (2-rail)
3. Cross-check IMON telemetry with RAPL energy status at idle and TDP
4. Tagged `NGA_MAIN` — run under NGA automation after manual checkout

**Priority**: High — `plc.feature.p2`, `NGA_MAIN`; IMON addressing errors cause incorrect RAPL power measurements leading to wrong throttle setpoints
