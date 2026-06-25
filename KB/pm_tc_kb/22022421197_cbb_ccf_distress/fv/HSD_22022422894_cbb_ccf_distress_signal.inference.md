# Deep Analysis: CBB CCF Distress Signal

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422894](https://hsdes.intel.com/appstore/article-one/#/22022422894) |
| **Title** | CBB CCF Distress Signal |
| **Status** | open |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CBB CCF -- Distress signal generation to IMH/NIO on CCF congestion |
| **Parent TCD** | [22022421197](https://hsdes.intel.com/appstore/article-one/#/22022421197) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Validate CBB CCF distress signal generation and handling. When the CCF ring is congested (snoop back-pressure, high CBO occupancy), CBB PCode asserts a distress signal to IMH/NIO Primecode via an HPM message, triggering a CCF frequency boost request. Tests verify distress asserts under congestion, is delivered to Primecode, and that CCF frequency increases in response.

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
| 1 | Read baseline distress signal state: verify no spurious distress at idle | Distress signal deasserted (0) at system idle; no false triggers | Distress asserted at idle -- false positive from low-traffic condition |
| 2 | Apply high-snoop-rate workload to induce CBO back-pressure on cbb0 | CBO occupancy rises; SBO back-pressure asserts | Workload not generating snoop traffic -- wrong workload type |
| 3 | Verify distress signal assertion: monitor HPM 0x1b UPSTREAM_CCF_DESIRED_RATIO or distress status register | Distress bit set; frequency boost request sent to IMH | No distress despite congestion -- threshold too high or signal path broken |
| 4 | Verify IMH/NIO receives distress and responds with frequency boost to CCF | UFS_STATUS.CURRENT_RATIO increases toward P0 after distress | No frequency response -- Primecode not processing CBB distress |
| 5 | Remove congestion (end workload); verify distress de-asserts and CCF frequency returns autonomously | Distress de-asserted; CCF ratio returns to BW-heuristic value within 2s | Distress stuck asserted -- hysteresis not clearing |
| 6 | Verify per-CBB: only cbb0 under load shows distress; cbb1 remains clean | cbb0 distress asserted; cbb1 deasserted | cbb1 distress also asserts -- cross-CBB distress coupling |
| 7 | Verify PLR_DIE_LEVEL = 0x0 after distress cycle | PLR = 0x0 post-recovery | PLR non-zero -- throttle event from distress-triggered boost |

### Pass / Fail Criteria

**PASS:** Distress asserts under congestion; IMH/NIO receives and responds with boost; CCF frequency increases; distress clears post-workload; per-CBB independence; PLR = 0x0.

**FAIL:** False distress at idle; no distress under congestion; IMH/NIO doesn't respond; distress stuck; cross-CBB coupling.

### Post-Process

Save: counter snapshots (baseline and under load), UFS_STATUS.CURRENT_RATIO trace, PLR_DIE_LEVEL for both CBBs.

### Reference Documents

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html) -- Distress signal generation, threshold, HPM delivery
- [CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) -- PEGA events driving distress
- [Fabric DVFS KB](../../../pm_features/fabric_dvfs/fabric_dvfs_main.md) -- CBB CCF distress -> frequency response
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP CCF ring scope

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable -- CBB CCF Distress Signal present on NWP**

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

Distress asserts under congestion; IMH/NIO receives and responds with boost; CCF frequency increases; distress clears post-workload; per-CBB independence; PLR = 0x0.
