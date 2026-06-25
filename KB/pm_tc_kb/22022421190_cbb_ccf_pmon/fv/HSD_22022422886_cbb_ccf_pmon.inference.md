# Deep Analysis: CBB CCF PMON

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422886](https://hsdes.intel.com/appstore/article-one/#/22022422886) |
| **Title** | CBB CCF PMON |
| **Status** | open |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CBB CCF -- Performance Monitor counters (CCF ring activity) |
| **Parent TCD** | [22022421190](https://hsdes.intel.com/appstore/article-one/#/22022421190) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Validate CBB CCF Performance Monitor (PMON) counters that measure CCF ring activity: bandwidth utilization, stall cycles, snoop traffic, and frequency-state occupancy. Tests verify counters increment correctly under known workload, PMU programming via MSR/TPMI, and counter accuracy against expected values.

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
| 1 | Program PMON: select CCF bandwidth event in PMON control MSR | PMU accepts programming; event selector written | MSR write rejected or not reflected |
| 2 | Apply mesh-bound workload on cbb0; read PMON bandwidth counter before and after | Counter increments by expected amount proportional to traffic | Counter stuck at 0 -- PMON not connected to CCF event |
| 3 | Repeat for stall-cycle event: verify counter increments under CCF congestion | Stall counter advances; rate proportional to congestion level | Counter frozen -- stall event mux incorrect |
| 4 | Verify frequency-state occupancy counter: lock CCF to ratio 0x16 for 100ms; read occupancy | Occupancy accumulates at ratio 0x16 for ~100ms equivalent | Occupancy at wrong ratio -- state bucket mux error |
| 5 | Verify PMON counters per CBB are independent: cbb0 and cbb1 show different values under asymmetric load | cbb0 counter > cbb1 counter when only cbb0 loaded | Counters identical -- CBB mux not working |
| 6 | Reset PMON counters and verify they clear to 0 | All counters read 0 after reset | Non-zero after reset -- counter not clearable |
| 7 | Verify PLR_DIE_LEVEL = 0x0 and no unexpected DVFS changes during PMON read | PLR = 0x0; CCF ratio unchanged by PMON operations | PLR asserts -- PMON overhead affecting CCF behavior |

### Pass / Fail Criteria

**PASS:** PMON counters increment under workload; event selection correct; occupancy accurate; per-CBB independence; counter reset works; PLR = 0x0.

**FAIL:** Counter stuck at 0; wrong event counted; occupancy at wrong ratio; CBBs not independent; counter not resettable.

### Post-Process

Save: counter snapshots (baseline and under load), UFS_STATUS.CURRENT_RATIO trace, PLR_DIE_LEVEL for both CBBs.

### Reference Documents

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html) -- CCF PMON event mapping
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details) -- CBB PMON telemetry space
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP CCF ring scope

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable -- CBB CCF PMON present on NWP**

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

PMON counters increment under workload; event selection correct; occupancy accurate; per-CBB independence; counter reset works; PLR = 0x0.
