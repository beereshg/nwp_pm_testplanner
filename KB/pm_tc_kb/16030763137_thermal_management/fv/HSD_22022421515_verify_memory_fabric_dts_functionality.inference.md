# Deep Analysis: [IMH DTS & Telemetry] Verify Memory Fabric DTS Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421515 |
| **Title** | [IMH DTS & Telemetry] Verify Memory Fabric DTS Functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | DTS — Memory Fabric thermal sensors via CFCIO Resource Controller |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **Memory Fabric DTS** functionality. From test step IP table:

| IP Stack | No. of DTS | IMH RS location | DTS location | Comment |
|----------|-----------|-----------------|--------------|---------|
| Memory Fabric | 4 | (TBD) | (TBD) | |

Flow:
1. Read DTS temperature in Memory Fabric IP
2. Read temperature in corresponding Resource Controller — **CFCIO**
3. Read temperature in PUNIT telemetry
4. Compare all — should match
5. Increase/Decrease temperature and repeat

Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

Memory Fabric is the memory interconnect fabric in the iMH die (distinct from DDR PHY). 4 DTS instances managed by CFCIO RC. NWP has same Memory Fabric thermal monitoring path.

---

## Section B: NWP-Specific Test Procedure

### Memory Fabric DTS Chain (NWP)

| Measurement | NWP Path |
|-------------|----------|
| Memory Fabric DTS direct | `sv.socket0.imh0.<mem_fabric_dts_N>.temperature` |
| CFCIO Resource Controller | `sv.socket0.imh0.cfcio.<rc_telem_reg>` |
| PUNIT telemetry | `sv.socket0.imh0.punit.<mem_fabric_telem_reg>` |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run dts_telemetry PMx | `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2` |
| 2 | Read Memory Fabric DTS (all 4 instances) | `sv.socket0.imh0.<mem_fabric_N>.dts.temperature.read()` for N in [0..3] |
| 3 | Read CFCIO RC temperature | `sv.socket0.imh0.cfcio.<telem_reg>.read()` |
| 4 | Read PUNIT telemetry | `sv.socket0.imh0.punit.<mem_fabric_telem>.read()` |
| 5 | Compare all — DTS ≈ CFCIO RC ≈ PUNIT telem | All 4 DTS checked |
| 6 | Stress memory fabric (high-BW access) | Verify telemetry tracks |
| 7 | Decrease to idle; verify DTS drops | Telemetry follows DTS real-time |

### NWP Notes
- Memory Fabric is the fabric interconnect between DDR controllers and caches — distinct from DDR PHY
- CFCIO RC manages Memory Fabric DTS (also manages Accelerator, IO Fabric DTS on NWP)
- 4 DTS instances; specific locations TBD in HAS (test steps note "TBD")
- Single `imh0` — all Memory Fabric DTS in `sv.socket0.imh0.*`

### Pass Criteria
- All 4 Memory Fabric DTS, CFCIO RC, and PUNIT telemetry agree
- Telemetry updates under memory fabric stress
- Temperature change (increase/decrease) reflected correctly in all three levels

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; 4 Memory Fabric DTS in imh0; CFCIO RC**

1. `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2`
2. NWP: 4 Memory Fabric DTS in `sv.socket0.imh0.*`; CFCIO RC
3. Verify 3-level chain: Memory Fabric DTS (×4) → CFCIO RC → PUNIT telemetry
4. Note: RS/DTS location details TBD in HAS — verify with NWP HAS before execution

**Priority**: Medium — `plc.feature.p1`; Memory Fabric DTS validates the memory interconnect thermal path — completes the full DTS telemetry coverage suite for SoC Thermal Management
