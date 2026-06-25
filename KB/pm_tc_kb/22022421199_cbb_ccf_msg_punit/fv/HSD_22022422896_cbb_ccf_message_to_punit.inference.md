# Deep Analysis: CBB CCF Message to Punit

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422896](https://hsdes.intel.com/appstore/article-one/#/22022422896) |
| **Title** | CBB CCF Message to Punit |
| **Status** | open |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CBB CCF -- HPM messages from CBB PCode to IMH/NIO Primecode |
| **Parent TCD** | [22022421199](https://hsdes.intel.com/appstore/article-one/#/22022421199) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Validate CBB CCF HPM (Hierarchical Power Management) messages sent from CBB PCode to IMH/NIO Primecode: HPM 0x1b (CBB_CCF_FREQUENCY: UPSTREAM_CCF_DESIRED_RATIO), HPM 0x35 (ACTIVE_CYCLES_TELEMETRY: MEM_BOUND_CYCLES), HPM 0x36 (MOST_ACTIVE_CORE_C0_TELEMETRY). Tests verify messages are sent with correct content, Primecode correctly decodes and acts on them, and the CBB-IMH HPM coordination works end-to-end.

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
| 1 | Verify HPM 0x1b is sent after CCF GV decision: pin CCF at 0x12 (NonAutoGV) and check UPSTREAM_CCF_DESIRED_RATIO in HPM 0x1b | HPM 0x1b sent with UPSTREAM_CCF_DESIRED_RATIO = 0x12 within one slow-loop period (~1ms) | HPM message not sent or wrong ratio -- CBB-to-IMH CCF freq coordination broken |
| 2 | Apply memory-bound workload; verify HPM 0x35 MEM_BOUND_CYCLES increments and is delivered to Primecode | MEM_BOUND_CYCLES increases under workload; Primecode slow-loop receives updated value | HPM 0x35 not updating -- CBB not sending memory-bound telemetry |
| 3 | Apply high CPU utilization; verify HPM 0x36 CORE_C0_TIME increases in proportion to cores active | MOST_ACTIVE_CORE_C0_TELEMETRY reflects fraction of total_time; value correlates with load | HPM 0x36 stale or wrong -- ELC C0 utilization input broken |
| 4 | Verify Primecode ELC decision uses HPM 0x36: set CPU to 100% load; verify ELC High mode activated via UFS_CONTROL | ELC High threshold crossed; UFS_CONTROL.ELC_HIGH_RATIO applied to fabric freq | ELC does not activate -- HPM 0x36 not reaching Primecode ELC handler |
| 5 | Verify HPM 0x1b Uniform mode: enable UNIFORM_CBB_FABRIC_FREQ_MODE; check both CBBs send coordinated desired ratios | Both CBBs send same desired ratio; Primecode resolves min and distributes | CBBs disagree in Uniform mode -- HPM aggregation not working |
| 6 | Verify PLR_DIE_LEVEL = 0x0 during all HPM message tests | PLR = 0x0; no spurious throttle from HPM coordination | PLR non-zero -- HPM message caused unintended state |

### Pass / Fail Criteria

**PASS:** HPM 0x1b/0x35/0x36 all sent with correct content; Primecode ELC responds to HPM 0x36; Uniform mode coordination works; PLR = 0x0.

**FAIL:** HPM message not sent or stale; Primecode ELC doesn't respond; Uniform mode CBBs disagree; PLR non-zero.

### Post-Process

Save: counter snapshots (baseline and under load), UFS_STATUS.CURRENT_RATIO trace, PLR_DIE_LEVEL for both CBBs.

### Reference Documents

- [HPM Message Specification](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html) -- HPM 0x1b, 0x35, 0x36 message formats
- [Fabric DVFS KB](../../../pm_features/fabric_dvfs/fabric_dvfs_main.md) -- HPM 0x1b CCF freq, 0x35/0x36 ELC inputs
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP CCF ring scope

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable -- CBB CCF Message to Punit present on NWP**

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

HPM 0x1b/0x35/0x36 all sent with correct content; Primecode ELC responds to HPM 0x36; Uniform mode coordination works; PLR = 0x0.
