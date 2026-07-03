# Deep Analysis: [IMH DTS & Telemetry] Verify D2D DTS Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421501 |
| **Title** | [IMH DTS & Telemetry] Verify D2D DTS Functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | DTS — D2D (Die-to-Die / UCIe adaptor) thermal sensors |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **D2D DTS** functionality. From test step IP table:

| IP Stack | No. of DTS | IMH RS location | DTS location | Comment |
|----------|-----------|-----------------|--------------|---------|
| D2D | 5 | inside UCIe adaptor in SOC | 4 one DTS per UCIe X6 module; 3 RS inside UCIe adaptor; One DTS with 6 RS | |

Flow:
1. Read DTS temperature in D2D IP
2. Read temperature in corresponding Resource Controller — **CFCMEM_EW**
3. Read temperature in PUNIT telemetry
4. Compare all — should match

Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

NWP has D2D/UCIe adaptors in iMH die (chiplet-to-chiplet interconnect between iMH and CBBs). Adapt DTS count/structure to NWP topology (NWP may differ from DMR's 5 DTS).

---

## Section B: NWP-Specific Test Procedure

### D2D DTS Architecture (NWP)

| Parameter | DMR | NWP |
|-----------|-----|-----|
| DTS count | 5 total (4 per UCIe X6 + 1 shared) | NWP D2D architecture — verify count from HAS |
| RC | CFCMEM_EW | CFCMEM_EW (same expected) |
| DTS location | Inside UCIe adaptor in SOC | Inside UCIe adaptor in iMH die |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run dts_telemetry PMx | `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2` |
| 2 | Read D2D DTS temperature for each UCIe module | `sv.socket0.imh0.<ucie_adaptor>.<dts_reg>.temperature.read()` |
| 3 | Read CFCMEM_EW RC temperature | `sv.socket0.imh0.cfcmem_ew.<rc_telem_reg>.read()` |
| 4 | Read PUNIT telemetry | `sv.socket0.imh0.punit.<d2d_telem_reg>.read()` |
| 5 | Compare all — DTS ≈ CFCMEM_EW ≈ PUNIT telem | Within calibration tolerance |
| 6 | Stress D2D link (traffic) | Verify all DTS and telemetry track |

### NWP D2D Notes
- NWP chiplet interconnect: iMH ↔ CBB0, iMH ↔ CBB1 via UCIe/D2D
- NWP D2D DTS count may differ from DMR — verify from NWP HAS before assuming 5 sensors
- CFCMEM_EW RC manages D2D thermal path (same as DMR)
- All D2D DTS in `sv.socket0.imh0.*` (single iMH)

### Pass Criteria
- All D2D DTS temperatures match CFCMEM_EW RC and PUNIT telemetry
- Telemetry updates under D2D traffic stress
- All UCIe module DTS sensors functional

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; D2D DTS in imh0; CFCMEM_EW RC; verify NWP UCIe DTS count vs DMR**

1. `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2`
2. NWP: D2D DTS in `sv.socket0.imh0.*` (iMH UCIe adaptors)
3. Verify 3-level chain: D2D DTS → CFCMEM_EW RC → PUNIT telemetry
4. Verify NWP D2D DTS count from HAS (may differ from DMR's 5)

**Priority**: Medium — `plc.feature.p1`; D2D DTS monitors the chiplet interconnect thermal — critical for NWP multi-die thermal integrity
