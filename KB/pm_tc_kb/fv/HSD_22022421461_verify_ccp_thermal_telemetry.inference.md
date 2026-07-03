# Deep Analysis: [CBB DTS & Telemetry] Verify CCP Thermal Telemetry

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421461 |
| **Title** | [CBB DTS & Telemetry] Verify CCP Thermal Telemetry |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | DTS — CCP (Core Cluster Processor) short-telemetry thermal reporting |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **CCP (Core Cluster Processor) thermal telemetry**. CCP reports thermal data to Pcode rapidly:
- Each CCP PMA pushes a packet of temperature info every **SHORT_TELEM time (~102.4µs)**
- SHORT_TELEM message format (per DCM): 16-bit packet including:
  - Byte 0: Telem ID 0, VR Domain0 (Cores) Min Temp
  - Byte 1: Telem ID 1, ...
- DMR note references "each DCM reports SHORT_TELEM message"

On NWP:
- NWP has CCP per compute die (2 CBBs)
- SHORT_TELEM format may differ slightly (NWP-specific CCP PMA design)
- Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

---

## Section B: NWP-Specific Test Procedure

### CCP Thermal Telemetry Architecture (NWP)

| Parameter | DMR | NWP |
|-----------|-----|-----|
| CBBs | 4 | 2 |
| SHORT_TELEM period | ~102.4µs | ~102.4µs (same period expected) |
| Reporting per die | Min Temp for VR domains | Same structure |
| Aggregation | Punit per CBB | imh0 Punit aggregates both CBBs |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run dts_telemetry PMx | `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2` |
| 2 | Capture SHORT_TELEM packets from CCP PMA | Per-cbb CCP PMA polling |
| 3 | Verify Telem ID fields and VR domain min temps | Check SHORT_TELEM format fields |
| 4 | Compare CCP SHORT_TELEM min temps to PUNIT telemetry | Should match after calibration |
| 5 | Verify telemetry rate (~102.4µs period) | Confirm SHORT_TELEM frequency |
| 6 | Repeat for cbb0 and cbb1 | Full NWP coverage |

### NWP Key Notes
- NWP: 2 CBBs — verify CCP SHORT_TELEM from `cbb0` and `cbb1`
- Single `imh0` Punit aggregates from both CBBs
- SHORT_TELEM rate of ~102.4µs same expected period
- VR Domain0 = Cores temp minimum

### Pass Criteria
- CCP SHORT_TELEM packets sent at ~102.4µs intervals from each CBB
- Telem ID fields correctly populated
- VR domain min temps match PUNIT telemetry
- Both cbb0 and cbb1 CCP telemetry functional

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; 2 CBBs; verify CCP SHORT_TELEM on both dies**

1. `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2`
2. NWP: 2 CBBs; verify CCP SHORT_TELEM from each die at ~102.4µs rate
3. SHORT_TELEM format: validate VR Domain0 min temp Telem IDs
4. imh0 Punit aggregates short telemetry from both CBBs

**Priority**: Medium — `plc.feature.p1`; CCP thermal telemetry is the high-frequency thermal data path for Pcode thermal management
