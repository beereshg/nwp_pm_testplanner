# Deep Analysis: CBB CCF CBO Telemetry

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422889](https://hsdes.intel.com/appstore/article-one/#/22022422889) |
| **Title** | CBB CCF CBO Telemetry |
| **Status** | open |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CBB CCF -- CBO traffic counters as CCF DVFS BW heuristics input |
| **Parent TCD** | [22022421194](https://hsdes.intel.com/appstore/article-one/#/22022421194) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Validate CBB CBO (Cache Box) telemetry used as input to the CCF DVFS bandwidth heuristics. CBO traffic counts (CMS/CRS read/write BW) drive the CCF ring frequency selection via the BW threshold LUT walk in the PCode slow loop (~1 ms period). Tests verify CBO counters increment under mesh-bound workload, the slow-loop correctly reads CBO telemetry, and the CCF frequency responds to high CBO traffic.

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
| 1 | Read baseline CBO telemetry counters via HPM 0x35 (`MEM_BOUND_CYCLES`) or TPMI telemetry | Non-zero baseline; counters accessible | Zero or inaccessible -- CBO telemetry not initialized |
| 2 | Apply memory-bandwidth workload (memcpy / stream benchmark); read CBO traffic counters after 100ms | CBO BW counters increment significantly; MEM_BOUND_CYCLES increase | Counters static -- workload not driving CBO traffic |
| 3 | Verify CCF ring frequency increases in response to high CBO BW: read `UFS_STATUS.CURRENT_RATIO` | CCF ratio increases toward P0 (2.2 GHz) under high CBO traffic | Ratio unchanged -- CBO telemetry not feeding BW heuristic |
| 4 | Reduce load to idle; verify CBO counters stop incrementing and CCF frequency returns to low-power | Counters plateau; CCF ratio drops toward ELC Low floor (~800 MHz) | Counters still incrementing at idle -- CBO not quiescing |
| 5 | Verify per-CBB independence: apply load to cbb0 only; verify cbb0 CBO counters > cbb1 | cbb0 telemetry shows activity; cbb1 near-zero | Identical values -- CBB not isolated in telemetry |
| 6 | Verify PLR_DIE_LEVEL = 0x0 during all CBO telemetry read operations | PLR = 0x0; no spurious throttle from telemetry overhead | PLR non-zero -- CBO telemetry reads causing interference |

### Pass / Fail Criteria

**PASS:** CBO counters increment under workload; CCF frequency responds to BW demand; per-CBB independence; counters quiesce at idle; PLR = 0x0.

**FAIL:** Counters static; CCF doesn't respond to CBO traffic; CBBs not independent; PLR non-zero.

### Post-Process

Save: counter snapshots (baseline and under load), UFS_STATUS.CURRENT_RATIO trace, PLR_DIE_LEVEL for both CBBs.

### Reference Documents

- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details) -- CBO BW counters, HPM 0x35
- [Fabric DVFS KB](../../../pm_features/fabric_dvfs/fabric_dvfs_main.md) -- BW heuristics, CBO slow-loop
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP CCF ring scope

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable -- CBB CCF CBO Telemetry present on NWP**

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

CBO counters increment under workload; CCF frequency responds to BW demand; per-CBB independence; counters quiesce at idle; PLR = 0x0.
