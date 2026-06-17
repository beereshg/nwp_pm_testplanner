# Deep Analysis: [IMH DTS & Telemetry] Verify IO Fabric DTS Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421504 |
| **Title** | [IMH DTS & Telemetry] Verify IO Fabric DTS Functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | DTS — IO Fabric (CA tile) thermal sensor via CFCIO Resource Controller |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **IO Fabric DTS** functionality. From test step IP table:

| IP Stack | No. of DTS | IMH RS location | DTS location | Comment |
|----------|-----------|-----------------|--------------|---------|
| IO Fabric | 1 | inside CA tile block in SOC | 1 RS in each CA tile; DTS could be shared opportunistically (floorplan-dependent) | |

Flow:
1. Read DTS temperature in IO Fabric IP
2. Read temperature in corresponding Resource Controller — **CFCIO**
3. Read temperature in PUNIT telemetry
4. Compare all — should match

Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

NWP IO Fabric (CA tile) is in the iMH die. CFCIO is the RC. Same 3-level chain: DTS → CFCIO → PUNIT.

---

## Section B: NWP-Specific Test Procedure

### IO Fabric DTS Chain (NWP)

| Measurement | NWP Path |
|-------------|----------|
| IO Fabric DTS direct | `sv.socket0.imh0.<ca_tile>.<dts_reg>.temperature` |
| CFCIO Resource Controller | `sv.socket0.imh0.cfcio.<rc_telem_reg>` |
| PUNIT telemetry | `sv.socket0.imh0.punit.<io_fabric_telem_reg>` |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run dts_telemetry PMx | `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2` |
| 2 | Read IO Fabric DTS (CA tile block) | `sv.socket0.imh0.<ca_tile_dts_path>.temperature.read()` |
| 3 | Read CFCIO RC temperature | `sv.socket0.imh0.cfcio.<telem_reg>.read()` |
| 4 | Read PUNIT telemetry | `sv.socket0.imh0.punit.<io_telem_reg>.read()` |
| 5 | Compare all three — should match | Within calibration tolerance |
| 6 | Stress IO fabric (PCIe/accelerator traffic) | Verify telemetry tracks DTS under IO load |

### NWP Notes
- IO Fabric (CA tile) DTS shared opportunistically depending on floorplan — verify NWP CA tile DTS count
- CFCIO RC manages both IO Fabric DTS and Accelerator DTS on NWP
- Single `imh0` — all IO Fabric DTS sensors in `sv.socket0.imh0.*`
- `runPmx.py -x nwp.xml` (not `dmr.xml`)

### Pass Criteria
- IO Fabric DTS, CFCIO RC, and PUNIT telemetry agree
- Telemetry tracks under IO fabric traffic stress
- All CA tile DTS sensors (NWP count) functional

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; IO Fabric DTS in imh0; CFCIO RC path; verify NWP CA tile DTS count**

1. `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2`
2. NWP: IO Fabric DTS in `sv.socket0.imh0.*`; CFCIO RC
3. Verify 3-level chain: CA tile DTS → CFCIO RC → PUNIT telemetry
4. Confirm floorplan-specific DTS sharing on NWP CA tile

**Priority**: Medium — `plc.feature.p1`; IO Fabric DTS monitors PCIe/accelerator connectivity thermal path
