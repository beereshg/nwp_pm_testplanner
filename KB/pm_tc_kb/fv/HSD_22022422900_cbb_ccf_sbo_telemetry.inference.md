# Deep Analysis: CBB CCF SBO Telemetry

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422900](https://hsdes.intel.com/appstore/article-one/#/22022422900) |
| **Title** | CBB CCF SBO Telemetry |
| **Status** | open |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CBB CCF -- Snoop Back-pressure Oracle telemetry as DVFS input |
| **Parent TCD** | [22022421202](https://hsdes.intel.com/appstore/article-one/#/22022421202) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Validate CBB SBO (Snoop Back-pressure Oracle) telemetry used as input to CCF DVFS. SBO measures snoop occupancy and back-pressure in the CBO mesh; high SBO utilization is an input to the CCF ring BW heuristics that drives frequency up-decisions. Tests verify: SBO counters increment under high-coherency workload; SBO threshold triggers distress/frequency boost; SBO correctly reflects snoop pressure.

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
| 1 | Read baseline SBO telemetry counters at system idle | SBO counter near-zero at idle; no false back-pressure | Non-zero SBO at idle -- false back-pressure detection |
| 2 | Apply high-coherency workload (e.g., cache-thrashing across 96 cores) | SBO occupancy counter increments; snoop back-pressure measured | SBO counter static -- snoop traffic not detected by SBO |
| 3 | Verify SBO counter rate correlates with coherency workload intensity (compare light vs heavy load) | Heavy load shows higher SBO rate than light load; linear-ish correlation | No correlation -- SBO not measuring actual snoop pressure |
| 4 | Verify SBO threshold triggers CCF frequency boost: increase load until SBO > threshold | CCF ratio increases (distress path) when SBO exceeds configured threshold | No frequency response -- SBO not feeding BW heuristic |
| 5 | Verify SBO counter per-CBB: asymmetric load (load cbb0 only) shows cbb0 SBO > cbb1 SBO | cbb0 SBO elevated; cbb1 near baseline | Symmetric SBO -- CBBs sharing counter or cross-talk |
| 6 | Reduce workload; verify SBO counter drops and CCF frequency returns to autonomous value | SBO drops within 2 slow-loop periods (~2ms); CCF ratio reduces | SBO stays high after workload removed -- hysteresis too long or counter stuck |
| 7 | Verify PLR_DIE_LEVEL = 0x0 throughout SBO telemetry test | PLR = 0x0; no throttle from SBO monitoring | PLR non-zero -- SBO-triggered boost causing power event |

### Pass / Fail Criteria

**PASS:** SBO counters increment under coherency load; threshold triggers frequency boost; per-CBB independence; SBO drops at idle; PLR = 0x0.

**FAIL:** SBO static; no threshold response; symmetric across CBBs; SBO stuck high post-workload.

### Post-Process

Save: counter snapshots (baseline and under load), UFS_STATUS.CURRENT_RATIO trace, PLR_DIE_LEVEL for both CBBs.

### Reference Documents

- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details) -- SBO counter definitions
- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html) -- SBO threshold, DVFS heuristic
- [Fabric DVFS KB](../../../pm_features/fabric_dvfs/fabric_dvfs_main.md) -- CBB CCF ring DVFS, snoop pressure
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP CCF ring scope

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable -- CBB CCF SBO Telemetry present on NWP**

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

SBO counters increment under coherency load; threshold triggers frequency boost; per-CBB independence; SBO drops at idle; PLR = 0x0.
