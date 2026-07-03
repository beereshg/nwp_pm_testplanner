# Deep Analysis: CBB CCF VF Curves

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422863](https://hsdes.intel.com/appstore/article-one/#/22022422863) |
| **Title** | CBB CCF VF Curves |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Fabric DVFS / CBB CCF GV -- Voltage-Frequency curve validation |
| **Parent TCD** | [22022421174](https://hsdes.intel.com/appstore/article-one/#/22022421174) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Validate CBB CCF ring Voltage-Frequency (VF) curve programming and enforcement. The VF curve defines the minimum supply voltage required at each CCF frequency operating point. GVFSM (GV Finite State Machine) in CBB PCode must select the correct voltage from the fused VF table when transitioning between frequency points. Key transition rules: **V-first** (voltage raised before frequency increases); **PLL-first** (frequency reduced before voltage drops). Tests verify the complete path: fuse readback, GVFSM voltage selection, FIVR output, and transition ordering.

**VF Curve Mechanism:** CBB PCode reads SST_PP_INFO and VF fuse tables at boot. Each frequency ratio maps to a minimum voltage (U3.13 fixed-point in UFS_STATUS.CURRENT_VOLTAGE). TPMI UFS_CONTROL ratio lock (MAX=MIN) is used to force each VF operating point for measurement.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| System booted, PCode initialized | BIOS CPL4 complete; GVFSM running | System hang or reset |
| No thermal throttle (TCC inactive) | Die temperature below TCC threshold | TCC active -- FIVR voltage artificially limited |
| TPMI accessible per CBB | `ufs_control`, `ufs_status`, `sst_pp_info_*` readable | TPMI path invalid |
| CBB GPSB accessible | `sv.socket0.cbb0.compute0.pma0.gpsb` readable | GPSB not accessible |
| BIOS: no VF OC override | Default VF curves in effect | OC mode would override fused curves |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read fused turbo ratios from `SST_PP_INFO_4` and P0/P1/Pm from `SST_PP_INFO_11` per CBB | Non-zero turbo ratios; P0 ≈ 22 (2.2 GHz) on NWP; Pm ≈ 8 (800 MHz) | Zero ratios -- fuses not propagated |
| 2 | Read baseline `UFS_STATUS.CURRENT_RATIO` and `CURRENT_VOLTAGE` | Non-zero ratio and voltage; voltage in U3.13 format | Zero voltage -- FIVR not reporting |
| 3 | Lock CCF at Pm (ratio = 0x08, 800 MHz): `MAX_RATIO = MIN_RATIO = 0x08`; wait 5M cycles | CURRENT_RATIO = 0x08; voltage = VF[Pm] (minimum supply voltage) | Ratio or voltage mismatch at Pm |
| 4 | Increase to mid-point (ratio = 0x12, 1.8 GHz): first verify V ramps **before** frequency | During transition: voltage rises to VF[1.8 GHz] before GVFSM locks new ratio (V-first rule) | Frequency increased before voltage -- V-first violated |
| 5 | Read `UFS_STATUS.CURRENT_VOLTAGE` at 1.8 GHz lock | Voltage = VF table entry for 1.8 GHz; higher than at Pm | Voltage same as Pm level -- GVFSM not selecting correct VF point |
| 6 | Increase to P0 (ratio = 0x16, 2.2 GHz on NWP): verify V-first again | Voltage rises to VF[P0] before frequency step; CURRENT_RATIO = 0x16 | V-first violated on freq increase to P0 |
| 7 | Decrease to P1 (ratio = 0x12): verify **PLL-first** (frequency drops before voltage) | CURRENT_RATIO drops to 0x12 before voltage decreases; no glitch | Voltage dropped before frequency -- PLL-first violated |
| 8 | Sweep all VF points (Pm → P1 → P0 and reverse) for both CBBs | Voltage monotonically increases with ratio; each VF pair matches fused table | Non-monotonic voltage -- VF curve corruption or wrong table |
| 9 | Restore autonomous mode (`MAX_RATIO ≠ MIN_RATIO`) and verify GVFSM resumes | CURRENT_RATIO returns to BW-heuristic value; voltage tracks autonomously | GVFSM stuck after sweep |

### Pass / Fail Criteria

**PASS:** Fused VF ratios readable and non-zero; CURRENT_VOLTAGE matches VF table entry at each locked ratio; V-first observed on frequency increase; PLL-first observed on frequency decrease; voltage monotonically tracks ratio across full sweep; autonomous recovery after test.

**FAIL:** Zero fused ratios; CURRENT_VOLTAGE does not match VF table; V-first or PLL-first ordering violated; non-monotonic voltage-frequency relationship; GVFSM stuck post-test.

### Post-Process

Save: SST_PP_INFO_4/11 values, UFS_STATUS.CURRENT_RATIO and CURRENT_VOLTAGE at each VF test point (Pm, mid, P0, reverse), transition ordering timestamps, PLR_DIE_LEVEL values for both CBBs.

### Reference Documents

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#switching-between-fast-gv-drainless-gv) -- V-first/PLL-first transition rules, GVFSM states
- [CBB CCP PM Integration HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCP%20HAS/cbb_cpp_has.html#vf-curves-grouping) -- VF curve grouping, fuse layout
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html) -- UFS_STATUS.CURRENT_VOLTAGE encoding (U3.13), SST_PP_INFO fields
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details) -- CBB PMSB telemetry, GPSB voltage reporting
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- [Fabric DVFS KB](../../../pm_features/fabric_dvfs/fabric_dvfs_main.md) -- GVFSM, CCF ring context

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable -- CBB CCF VF curves present on NWP**

CBB PCode GVFSM uses the same VF curve infrastructure on NWP as DMR. NWP CCF: P0 = 2.2 GHz (ratio 22 = 0x16), Pm = 800 MHz (ratio 8 = 0x08). NWP has 2 CBBs -- sweep VF on both cbb0 and cbb1.

Tags: `CBB CCF`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### Key Register Paths (NWP)

| Register | NWP Path | Purpose |
|----------|----------|---------|
| SST_PP_INFO_4 | `sv.socket0.cbbN.base.tpmi.sst_pp_info_4` | TRL ratios (P0/turbo ratios) |
| SST_PP_INFO_11 | `sv.socket0.cbbN.base.tpmi.sst_pp_info_11` | P0, P1, Pm encoding |
| UFS_CONTROL | `sv.socket0.cbbN.base.tpmi.ufs_control` | MAX_RATIO/MIN_RATIO for VF point lock |
| UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status` | CURRENT_RATIO [6:0], CURRENT_VOLTAGE [22:7] (U3.13) |
| GPSB pma | `sv.socket0.cbbN.compute0.pma0.gpsb` | GPSB for additional voltage monitoring |

### NWP VF Test Ratios

| VF Point | Ratio | Freq | Expected |
|----------|-------|------|---------|
| Pm (min) | 0x08 | 800 MHz | Minimum FIVR voltage |
| Mid | 0x12 | 1800 MHz | Mid-range voltage |
| P1 | 0x14 | 2000 MHz | Near-max voltage |
| P0 (max) | 0x16 | 2200 MHz | Maximum voltage |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Iterate both CBBs | `for cbb in sv.sockets.cbbs:` |
| 2 | Lock to Pm | `cbb.base.tpmi.ufs_control.max_ratio.write(0x08); .min_ratio.write(0x08)` |
| 3 | Read voltage at each point | `(cbb.base.tpmi.ufs_status.read() >> 7) & 0x7FFF` (U3.13) |
| 4 | Verify monotonic | Assert voltage increases with each ratio step |
| 5 | Restore | Write original MAX/MIN values |

### Pass Criteria

Fused ratios non-zero; CURRENT_VOLTAGE increases monotonically with ratio; V-first on increase, PLL-first on decrease; autonomous recovery after sweep.
