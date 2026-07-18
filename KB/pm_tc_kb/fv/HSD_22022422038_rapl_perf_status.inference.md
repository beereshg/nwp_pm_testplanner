# TC Description: RAPL Perf Status

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422038](https://hsdes.intel.com/appstore/article-one/#/22022422038) |
| **Title** | RAPL Perf status |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL PERF_STATUS throttle accounting counter |
| **Parent TCD** | [16031169448 -- Socket RAPL - Reporting / Observability](https://hsdes.intel.com/appstore/article-one/#/16031169448) |
| **Owner** | mps |
| **Status** | open / ready_for_content_review |
| **Priority** | 2-high |
| **Tags** | `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK` |
| **Val Environment** | silicon, virtual_platform |
| **Val Framework** | PMX, os-svos, python-sv |
| **Automation** | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Cache version** | 3 |

---

## Test Case Intent

Validates the **PERF_STATUS throttle accounting counter** scenario defined in [TCD 16031169448 -- Socket RAPL - Reporting / Observability](https://hsdes.intel.com/appstore/article-one/#/16031169448) §5-A: "PERF_STATUS throttle counter increments during active RAPL limiting; counter does NOT increment when frequency is unconstrained by RAPL; counter increment rate is proportional to throttle duration." The PERF_STATUS counter (pwr_limit_throttle_ctr) is the primary OS-visible indicator of RAPL throttle activity. It is accessible via both CSR (package_rapl_perf_status) and TPMI (socket_rapl_perf_status). This TC triggers PL1 and PL2 throttle conditions, verifies the counter increments during throttle and stops when limits are released, and confirms CSR and TPMI interfaces report consistent values.

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon system (2 CBBs, single NIO die) or VP (Simics) |
| OS / Driver | SVOS with PythonSV environment; ptu or equivalent workload available |
| BIOS knobs | Socket RAPL PL1 enabled (default); PL1/PL2 limits unlocked or programmable via TPMI |
| Feature state | RAPL active at TDP; no prior throttle condition |
| Tool | runPmx.py accessible; diamondrapids.pm.pmutils.cpu_rapl importable; PEGA available |
| Starting state | System booted to SVOS; cores active at P1 or below |
| CSR register | sv.socket0.nio.punit.ptpcioregs.ptpcioregs.package_rapl_perf_status |
| TPMI register | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_perf_status (field: pwr_limit_throttle_ctr) |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Read baseline PERF_STATUS counter from both CSR and TPMI interfaces. CSR: package_rapl_perf_status. TPMI: socket_rapl_perf_status.pwr_limit_throttle_ctr. Record values as baseline_csr and baseline_tpmi. | Both registers readable; baseline values recorded. CSR and TPMI agree (same counter value). | Register read failure or CSR/TPMI mismatch at baseline. |
| 2 | Verify counter is stable at idle (no throttle). Wait 1 second and re-read both registers. | Counter values unchanged from baseline (delta = 0). Counter does NOT increment when frequency is unconstrained by RAPL. | Counter incrementing at idle — spurious throttle condition active. |
| 3 | Start sustained all-core workload (ptu -ct 1) to establish power draw near TDP. | Cores running at P1 frequency; power draw near TDP. | Workload fails to start. |
| 4 | Set PL1 to aggressive low value via TPMI (socket_rapl_pl1_control.pwr_lim) to force PL1 throttle. Wait for RAPL convergence (~3-5x tau). | RAPL PID output drops; core frequencies throttled; power converges toward PL1 limit. | RAPL does not engage; frequencies remain at P1. |
| 5 | Read PERF_STATUS counter (TPMI: pwr_limit_throttle_ctr) at time t0. Wait 1 second. Read again at time t1. Compute delta = t1 - t0. | Delta > 0: counter is incrementing during active PL1 throttle. Counter increment rate proportional to throttle duration. | Delta = 0: counter not incrementing during active throttle (check_rapl_perf_status would flag this). |
| 6 | Read CSR package_rapl_perf_status and compare to TPMI socket_rapl_perf_status.pwr_limit_throttle_ctr. | CSR and TPMI counter values agree (same value or within 1 tick due to read timing). | CSR/TPMI mismatch exceeds 1 tick — interface desync. |
| 7 | Read additional reporting registers: dfo_pkg_rapl_perf_status and dfo_primary_plane_rapl_perf_status. | Both registers progressing (non-stale) during throttle. | Either register stale (not changing). |
| 8 | Verify PLR (Perf Limit Reasons) attribution during PL1 throttle. Read plr_die_level per compute die. | PLR SktPL1 reason bit set. Other reason bits clear (unless those conditions also exist). | PLR = 0 during active throttle or wrong reason bit set. |
| 9 | Restore PL1 to TDP. Use PEGA to re-assert high ratios (pegaPstate iagv=4). Wait 5 seconds for convergence. Clear PLR mailbox. | Core frequencies recover above throttle point. PLR reason bits clear (no limiter active). | Frequency does not recover; PLR remains set. |
| 10 | Verify counter stops after throttle release. Read PERF_STATUS at t0, wait 1 second, read at t1. Compute delta. | Delta = 0: counter stops incrementing when RAPL is no longer constraining. (check_rapl_perf_status verifies this with expect_change=False.) | Counter still incrementing despite no active throttle — residual throttle or counter bug. |
| 11 | Set PL2 to aggressive low value to trigger PL2 throttle during burst workload. Wait for PL2 timer convergence. | PL2 throttle engages; RAPL PID output drops during burst. | PL2 throttle does not engage. |
| 12 | Read PERF_STATUS counter during PL2 throttle. Verify delta > 0. Then restore PL2 to default (1.2 x TDP). Verify counter stops. Restore all registers. | Counter increments during PL2 throttle. Counter stops after PL2 release. Test exits cleanly (exit code 0). No MCA or hang. | Counter not incrementing during PL2 throttle; counter continues after release; script error or system hang. |

### Pass / Fail Criteria

- **PASS**: Per TCD 16031169448 §5-A — PERF_STATUS throttle counter (pwr_limit_throttle_ctr) increments during active PL1 throttle (delta > 0 over 1s sampling window). Counter increments during PL2 throttle. Counter does NOT increment at idle or after throttle release (delta = 0). CSR (package_rapl_perf_status) and TPMI (socket_rapl_perf_status) report consistent values. dfo_pkg_rapl_perf_status and dfo_primary_plane_rapl_perf_status also progressing during throttle. PLR reason bits correctly attributed. No MCA or hang. Script exit code 0.
- **FAIL**: Counter does not increment during active RAPL throttle (delta = 0). Counter increments at idle or after throttle release. CSR and TPMI counter values disagree beyond 1-tick tolerance. dfo counters stale during throttle. PLR reason bits incorrect. MCA or system hang at any point.

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| socket_rapl_perf_status.pwr_limit_throttle_ctr (TPMI) | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_perf_status | Increments during throttle; stable when unconstrained |
| package_rapl_perf_status (CSR) | sv.socket0.nio.punit.ptpcioregs.ptpcioregs.package_rapl_perf_status | Matches TPMI counter value |
| dfo_pkg_rapl_perf_status | sv.socket0.nio.dfo_pkg_rapl_perf_status | Progressing during throttle |
| dfo_primary_plane_rapl_perf_status | sv.socket0.nio.dfo_primary_plane_rapl_perf_status | Progressing during throttle |
| socket_rapl_pid_output | sv.socket0.nio.pcudata.raplVars.socket_rapl_pid_output | Confirms PID output drop during throttle |
| plr_die_level | Per compute die pcudata | SktPL1 or SktPL2 reason bit set during corresponding throttle |
| Per-core frequency | die.computes.pmas.pmsb.io_core_operating_point.core_ratio_16p67 | Reduced during throttle; recovers after release |

### Post-Process

N/A

### References

- [TCD 16031169448 -- Socket RAPL - Reporting / Observability](https://hsdes.intel.com/appstore/article-one/#/16031169448)
- [Wave 3 Common HAS -- Socket RAPL](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html)
- [DMR RAPL Simplification](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_rapl_simplification.html)

---

## Section A: NWP Delta

NWP carries forward DMR PERF_STATUS reporting. NIO replaces IMH as the root die hosting the PERF_STATUS registers.

| Aspect | DMR | NWP |
|--------|-----|-----|
| TPMI perf status | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_perf_status | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_perf_status |
| CSR perf status | sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_rapl_perf_status | sv.socket0.nio.punit.ptpcioregs.ptpcioregs.package_rapl_perf_status |
| PID output | socket.imh0.pcudata.raplVars.socket_rapl_pid_output | socket.nio.pcudata.raplVars.socket_rapl_pid_output |
| CBB count | 4 | 2 |

## Section F: Recommendations

Recommendation: ADOPT — imh0 -> nio register paths; verify counter on both CSR and TPMI; confirm counter starts/stops correctly with throttle transitions. Priority: High — plc.feature.p2; RAPL perf status is the primary OS-visible throttle counter used by Linux/Windows power management monitoring.
