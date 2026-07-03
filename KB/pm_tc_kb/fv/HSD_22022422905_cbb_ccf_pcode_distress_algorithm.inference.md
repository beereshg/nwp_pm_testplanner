# Deep Analysis: CBB CCF PCODE Algorithm for Distress Input

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422905](https://hsdes.intel.com/appstore/article-one/#/22022422905) |
| **Title** | CBB CCF PCODE Algorithm for Distress Input |
| **Status** | open |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CBB CCF -- PCode distress-input to CCF frequency-boost algorithm |
| **Parent TCD** | [22022421205](https://hsdes.intel.com/appstore/article-one/#/22022421205) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Validate the CBB PCode algorithm that processes distress inputs (SBO back-pressure, CBO occupancy) and converts them into CCF frequency up-decisions. The algorithm uses threshold-based hysteresis: distress above threshold triggers GVFSM frequency boost; below threshold for N slow-loops, boost is removed. Tests verify: correct threshold behavior; hysteresis prevents oscillation; frequency response magnitude and timing.

**NWP topology:** 2 CBBs (cbb0/cbb1) x 48 cores = 96 cores total. CCF ring managed autonomously by CBB PCode GVFSM. CCF target = 2.2 GHz (ratio 0x16) for full bandwidth (460 GB/s). MC6 is the deepest idle state (PkgC6 fused off).

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| System booted to XOS/SVOS | BIOS CPL4 complete; PCode running | System not booted |
| TPMI accessible per CBB | `sv.socket0.cbbN.base.tpmi.*` readable | TPMI path invalid |
| PythonSV namednodes loaded | `import namednodes; sv = namednodes.sv` succeeds | PythonSV not connected |
| Workload available | CPU stress or coherency workload can be launched | No workload -- cannot stimulate counters |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read configured distress threshold from TPMI or BIOS (UFS_ADV_CONTROL or vendor-specific register) | Threshold readable; non-zero value confirming BIOS programmed it | Threshold = 0 -- BIOS did not configure distress threshold |
| 2 | Apply moderate load (SBO below threshold); verify no distress-triggered boost | CCF ratio stays at BW-heuristic-driven value; no boost from distress path | Spurious boost below threshold -- algorithm triggering too early |
| 3 | Apply high load (SBO above threshold for 2+ slow-loops); verify distress boost fires | CCF ratio increases toward P0 after distress threshold exceeded for hysteresis window | No boost -- threshold not crossed or algorithm not running |
| 4 | Remove load: verify hysteresis holds boost for N slow-loop periods before reducing ratio | CCF stays at boosted ratio for N x 1ms after distress clears; then ramps down | Instant drop after load removed -- no hysteresis; oscillation risk |
| 5 | Verify oscillation prevention: rapid load changes (on/off at 10 Hz) do not cause frequency thrashing | CCF frequency stable during rapid load oscillation; hysteresis smooths transitions | CCF oscillates at load frequency -- hysteresis not working |
| 6 | Verify frequency response magnitude: boost at maximum distress reaches P0 (0x16 = 2.2 GHz) | At full distress, CCF boosted to P0; no intermediate cap | CCF capped below P0 -- algorithm limiting boost magnitude |
| 7 | Verify algorithm operates independently per-CBB: distress on cbb0 does not trigger cbb1 boost | cbb0 boosts; cbb1 stays at autonomous value | cbb1 also boosts -- distress not scoped to per-CBB |
| 8 | Verify PLR_DIE_LEVEL = 0x0 throughout distress algorithm test | PLR = 0x0; power events from CCF boost are clean | PLR non-zero -- unexpected power event from distress boost |

### Pass / Fail Criteria

**PASS:** Threshold behavior correct; boost fires only above threshold; hysteresis holds boost N slow-loops; no oscillation under rapid load; boost reaches P0; per-CBB independence; PLR = 0x0.

**FAIL:** Spurious boost below threshold; no boost above threshold; no hysteresis; oscillation; boost capped below P0; cross-CBB coupling.

### Post-Process

Save: counter snapshots (baseline and under load), UFS_STATUS.CURRENT_RATIO trace, PLR_DIE_LEVEL for both CBBs.

### Reference Documents

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html) -- Distress algorithm, threshold, hysteresis
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details) -- Distress input counters
- [Fabric DVFS KB](../../../pm_features/fabric_dvfs/fabric_dvfs_main.md) -- CBB CCF DVFS, distress -> frequency
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP CCF ring scope

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable -- CBB CCF PCODE Algorithm for Distress Input present on NWP**

CBB CCF telemetry and DVFS algorithm are inherited from DMR CBB shared source. NWP: 2 CBBs; iterate both cbb0 and cbb1. CCF P0 = 2.2 GHz; test under full 96-core coherency load for maximum signal.

Tags: `CBB CCF`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### Key Namednodes Paths (NWP)

| Register | NWP Path | Purpose |
|----------|----------|---------|
| UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status` | CURRENT_RATIO |
| PLR_DIE_LEVEL | `sv.socket0.cbbN.base.tpmi.plr_die_level` | Perf Limit Reason |
| UFS_ADV_CONTROL_1 | `sv.socket0.cbbN.base.tpmi.ufs_adv_control_1` | RAPL/distress slopes |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Iterate both CBBs | `for cbb in sv.sockets.cbbs:` |
| 2 | Read telemetry | Per-CBB TPMI or GPSB path |
| 3 | Apply workload | `pega_mailbox.pega_pstate()` or OS-level stress tool |
| 4 | Verify response | `cbb.base.tpmi.ufs_status.current_ratio.read()` |

### Pass Criteria

Threshold behavior correct; boost fires only above threshold; hysteresis holds boost N slow-loops; no oscillation under rapid load; boost reaches P0; per-CBB independence; PLR = 0x0.
