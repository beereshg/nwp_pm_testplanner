# Deep Analysis: [CBB DTS & Telemetry] Verify SoC DTS Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421469 |
| **Title** | [CBB DTS & Telemetry] Verify SOC DTS Functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | DTS — SoC-level thermal sensors (IMH die SoC DTS) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **SoC DTS** (die-level SoC thermal sensors, distinct from per-core DTS):
1. Read DTS temperature in SoC DTSes
2. Read temperature in PUNIT telemetry
3. Compare — should match
4. Increase/Decrease temperature and repeat

SoC DTS refers to sensors located on the SoC/IMH die (not per-core). On NWP: single `imh0` die has SoC DTS sensors; same read/compare/stress pattern applies.

Tags: `New_content`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

---

## Section B: NWP-Specific Test Procedure

### SoC DTS Location (NWP)

| Location | NWP Path |
|----------|----------|
| SoC DTS (iMH die) | `sv.socket0.imh0.<soc_dts_path>.temperature` |
| PUNIT telemetry | `sv.socket0.imh0.punit.<soc_telem_reg>` |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run dts_telemetry PMx | `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2` |
| 2 | Read SoC DTS temperature directly | `sv.socket0.imh0.<soc_dts_reg>.temperature.read()` |
| 3 | Read PUNIT telemetry for SoC DTS | `sv.socket0.imh0.punit.<soc_dts_telem>.read()` |
| 4 | Compare — values should match | Within calibration tolerance |
| 5 | Stress SoC (workload/thermal injection) | Change temperature |
| 6 | Repeat steps 2–4 under stress | Verify telemetry tracks DTS real-time |

### NWP Notes
- NWP: single `imh0` die → SoC DTS on imh0
- SoC DTS is separate from core/cluster DTS — covers IMH die hotspot
- Standard dts_telemetry PMx covers SoC DTS as part of broader telemetry test

### Pass Criteria
- SoC DTS readings match PUNIT telemetry
- Telemetry updates in real-time as temperature changes
- No stale or stuck SoC DTS values

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; SoC DTS on imh0; same read/compare/stress flow**

1. `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2`
2. NWP: SoC DTS on single `imh0` die
3. Adapt register paths from DMR SoC DTS → NWP imh0 SoC DTS paths

**Priority**: Medium — `plc.feature.p1`; SoC DTS validates IMH die thermal monitoring
