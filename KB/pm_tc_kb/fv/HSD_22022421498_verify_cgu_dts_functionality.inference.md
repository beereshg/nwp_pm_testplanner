# Deep Analysis: [IMH DTS & Telemetry] Verify CGU DTS Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421498 |
| **Title** | [IMH DTS & Telemetry] Verify CGU DTS Functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | DTS — CGU (Clock Generation Unit) thermal sensor; last in CATTRIP daisy chain |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **CGU DTS** functionality. From test step IP table:

| IP Stack | No. of DTS | IMH RS location | DTS location | Comment |
|----------|-----------|-----------------|--------------|---------|
| CGU | 1 | inside CGU | inside CGU | AON DTS part of stack; **last in CATTRIP daisy chain** |

Flow:
1. Read DTS temperature in CGU IP
2. Read temperature in corresponding Resource Controller — **MC_W**
3. Read temperature in PUNIT telemetry
4. Compare all — should match

Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

CGU is present in NWP IMH die. The AON DTS being "last in CATTRIP daisy chain" is a hardware safety design note — relevant for thermtrip testing but not functional DTS reading.

---

## Section B: NWP-Specific Test Procedure

### CGU DTS Chain (NWP)

| Measurement | NWP Path |
|-------------|----------|
| CGU DTS direct | `sv.socket0.imh0.<cgu_dts_path>.temperature` |
| MC_W Resource Controller | `sv.socket0.imh0.mc_w.<rc_telem_reg>` |
| PUNIT telemetry | `sv.socket0.imh0.punit.<cgu_telem_reg>` |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run dts_telemetry PMx | `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2` |
| 2 | Read CGU DTS temperature directly | `sv.socket0.imh0.<cgu_dts_reg>.temperature.read()` |
| 3 | Read MC_W RC temperature | `sv.socket0.imh0.mc_w.<telem_reg>.read()` |
| 4 | Read PUNIT telemetry | `sv.socket0.imh0.punit.<cgu_telem>.read()` |
| 5 | Compare all three — should match | DTS ≈ MC_W RC ≈ PUNIT telem |
| 6 | Verify AON DTS association (always-on) | CGU DTS should be readable in any power state |

### NWP Notes
- CGU is in iMH die (`imh0`); single CGU per socket on NWP
- MC_W is the RC for CGU DTS (memory controller west side)
- CGU DTS is "last in CATTRIP daisy chain" — important for thermtrip path ordering
- AON DTS is part of CGU stack — always-on monitoring

### Pass Criteria
- CGU DTS, MC_W RC, and PUNIT telemetry agree on temperature
- AON DTS accessible in all power states
- CGU DTS is last in CATTRIP chain (verify via thermtrip test ordering)

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; CGU DTS in imh0; MC_W RC path; last in CATTRIP chain**

1. `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2`
2. NWP: CGU DTS in `sv.socket0.imh0.*`; MC_W RC
3. Verify 3-level chain: CGU DTS → MC_W RC → PUNIT telemetry
4. Note: CGU DTS is last in CATTRIP daisy chain — cross-reference with thermtrip tests

**Priority**: Medium — `plc.feature.p1`; CGU DTS validates clock-domain thermal monitoring; CATTRIP position critical for safety path
