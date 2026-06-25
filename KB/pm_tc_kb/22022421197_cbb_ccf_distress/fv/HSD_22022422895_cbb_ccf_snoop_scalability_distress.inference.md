# Deep Analysis: CBB CCF Snoop Scalability / Distress

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422895](https://hsdes.intel.com/appstore/article-one/#/22022422895) |
| **Title** | CBB CCF Snoop Scalability / Distress |
| **Status** | open |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CBB CCF -- Snoop scalability under high coherency workload and distress mechanism |
| **Parent TCD** | [22022421197](https://hsdes.intel.com/appstore/article-one/#/22022421197) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Validate CBB CCF ring scalability under high snoop rates and the snoop back-pressure / distress mechanism. With 96 cores (2 CBBs x 48 cores), high-coherency workloads drive extreme snoop traffic. Tests verify: CCF ring frequency scales with snoop traffic demand; snoop back-pressure (SBO) triggers distress and frequency boost; scalability improves latency vs fixed-low-frequency baseline.

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
| 1 | Baseline: pin CCF at Pm (800 MHz) and run high-coherency workload; measure snoop latency | Snoop latency measured at 800 MHz (high, baseline) | Cannot measure snoop latency -- missing instrumentation |
| 2 | Allow autonomous CCF DVFS: run same workload; observe CCF scale to P0 (2.2 GHz) | CCF ratio rises toward P0 under snoop pressure; latency improves vs Pm baseline | CCF stays at Pm -- BW heuristic / distress not triggering scale-up |
| 3 | Verify SBO back-pressure counter increments during high snoop load | SBO occupancy counter > 0 under coherency workload | SBO counter stuck -- snoop back-pressure not detected |
| 4 | Verify distress signal fires when SBO occupancy exceeds threshold | Distress HPM message sent; CCF frequency boost observed | No distress despite high SBO -- threshold misconfigured |
| 5 | Measure peak snoop throughput at P0 (2.2 GHz) vs Pm (800 MHz) | Throughput scales ~linearly with CCF frequency (NWP CCF target: 460 GB/s at 2.2 GHz) | No throughput improvement at higher CCF freq -- CCF not the bottleneck |
| 6 | Verify snoop scalability is per-CBB: apply load to one CBB; verify other CBB not disturbed | Loaded CBB scales to P0; unloaded CBB stays at low freq | Both CBBs scale together -- loss of per-CBB independence |
| 7 | Verify PLR_DIE_LEVEL = 0x0 throughout scalability test | PLR = 0x0; no spurious power throttle limiting CCF | PLR non-zero -- power throttle interfering with scalability |

### Pass / Fail Criteria

**PASS:** CCF scales to P0 under snoop pressure; SBO counter increments; distress fires at threshold; throughput scales with frequency; per-CBB independence; PLR = 0x0.

**FAIL:** CCF stays at Pm despite snoop load; SBO stuck at 0; no distress; no throughput scaling; both CBBs scale together.

### Post-Process

Save: counter snapshots (baseline and under load), UFS_STATUS.CURRENT_RATIO trace, PLR_DIE_LEVEL for both CBBs.

### Reference Documents

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html) -- Snoop distress, SBO threshold, frequency scaling
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details) -- SBO telemetry counters
- [DMR SoC HAS](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/DMR_Overview_HAS.html#figure-hub-and-spoke) -- CCF ring topology, NWP target 460 GB/s
- [Fabric DVFS KB](../../../pm_features/fabric_dvfs/fabric_dvfs_main.md) -- CBB CCF ring DVFS context
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP CCF ring scope

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable -- CBB CCF Snoop Scalability / Distress present on NWP**

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

CCF scales to P0 under snoop pressure; SBO counter increments; distress fires at threshold; throughput scales with frequency; per-CBB independence; PLR = 0x0.
