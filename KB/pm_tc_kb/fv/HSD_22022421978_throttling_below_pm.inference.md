# TC Description: Throttling Below Pm

| Field | Value |
|-------|-------|
| **HSD ID** | [22022421978](https://hsdes.intel.com/appstore/article-one/#/22022421978) |
| **Title** | Throttling below Pm |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL throttling below Pm (minimum operating frequency) |
| **Parent TCD** | [16031169418 -- Socket RAPL - Below-Pm / Fast Throttle](https://hsdes.intel.com/appstore/article-one/#/16031169418) |
| **Owner** | mps |
| **Status** | open / ready_for_content_review |
| **Priority** | 2-high |
| **Tags** | `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK` |
| **Val Environment** | silicon, virtual_platform |
| **Val Framework** | os-svos, python-sv |
| **Automation** | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Cache version** | 3 |

---

## Test Case Intent

Validates the **below-Pm fast_throttle** scenario defined in [TCD 16031169418 -- Socket RAPL - Below-Pm / Fast Throttle](https://hsdes.intel.com/appstore/article-one/#/16031169418) §5, row "Below-Pm fast_throttle". Environment: NWP post-silicon (SVOS + PythonSV) or virtual platform. When Socket RAPL PL1 forces the NN-PID resolved frequency output (RAPL_PID_FREQ_OUTPUT) below Pm (the fused minimum operating ratio), PrimeCode asserts the fast_throttle wire to CBB PCode. CBB PCode applies clock division and architectural throttle on all active cores, causing effective frequency to drop below Pm. When the PID output recovers above Pm, fast_throttle de-asserts and frequency recovers. This TC harasses PL1/PL2 limits via TPMI and verifies that the throttle/recovery cycle executes correctly on both NWP CBBs. Flags: -tM 6 (verify throttle status + counters), -M 3 (harass PL1 + PL2).

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon system (2 CBBs, single NIO die) or VP (Simics) |
| OS / Driver | SVOS with PythonSV environment; ptu available for workload generation |
| BIOS knobs | Socket RAPL PL1 enabled (default); PL1 limit unlocked (LOCK bit = 0) or programmable via TPMI |
| Feature state | Socket RAPL active (PL1 enabled by default at TDP); no external Pmax injection |
| Tool | runPmx.py accessible; diamondrapids.pm.pmutils.cpu_rapl importable; PEGA available |
| Starting state | System booted to SVOS; cores active at P1 or below; no prior RAPL throttle condition |
| Register access | TPMI path: sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control |
| Pm ratio | Read from pcudata_global_pm_ratio_ia(0) or MSR IA32_PLATFORM_INFO [55:48] |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Import cpu_rapl utilities and read Pm ratio. PythonSV imports diamondrapids.pm.pmutils.cpu_rapl as cr. Read PM_RATIO from pcudata_global_pm_ratio_ia(0). | PM_RATIO is a valid integer (typically 4-8 for NWP; minimum guaranteed ratio x 100 MHz). | PM_RATIO read fails or returns 0. |
| 2 | Read and save current PL1/PL2 limits via crmsr_pkg_rapl_limit. Record baseline package_energy_status (TPMI) and pkg_rapl_perf_status. | PL1 = TDP (fused); PL2 = 1.2 x TDP. Energy status non-zero and progressing. | Registers unreadable or energy status stale. |
| 3 | Enumerate active cores across both CBBs. Iterate die.core_pmsb.core_pmsbs; check pma_debug2.acp_enabled per core. | Active cores identified on CBB0 and CBB1 (NWP: up to 48 cores per CBB, 96 total). | No active cores found on one or both CBBs. |
| 4 | Start TDP workload — launch ptu -ct 1 or equivalent all-core AVX workload. | Cores running at P1 frequency; power draw near TDP. | Workload fails to start or power draw remains near idle. |
| 5 | Harass PL1 — set aggressively low limit via TPMI. Program socket_rapl_pl1_control.pwr_lim well below current power draw (forcing PID output below Pm). use_tpmi = 1. | PrimeCode NN-PID resolves RAPL_PID_FREQ_OUTPUT < PM_RATIO; fast_throttle wire asserted to both CBBs. | PID output remains above Pm despite low PL1 limit. |
| 6 | Verify throttle status (_VERIFY_THROTTLED_ bit1). Read: socket.nio.pcudata.socket_rapl_pid_output (PID output), per-core target_wp1.core_frequence (effective freq), plr_die_level (PLR bits), pkg_therm_status.power_limitation_status/log. | PID output <= PM_RATIO. Core ratios converge to ~Pm (within 1 bin). Mesh ratio converges to Pm. PLR bit set. power_limitation_status and power_limitation_log set. | Core ratios above Pm during throttle; PLR = 0; power_limitation_log not set. |
| 7 | Verify counters (_VERIFY_COUNTERS_ bit2). Read: dfo_primary_plane_rapl_perf_status, dfo_pkg_rapl_perf_status, package_energy_status (TPMI). | All counters progressing (non-stale); energy counter incremented from baseline. | Any counter stale or package_energy_status not changing. |
| 8 | Verify TPMI resolved limits match programmed values. Cross-check cr.read_programmed_val(sktNum, method=tpmi, limit=1/2) against resolved values. | Resolved limits match programmed TPMI values (PL2 within 0.9x target factor). | Resolved limit does not match MSR or TPMI interface. |
| 9 | Harass PL2 — repeat aggressive limit programming for PL2 via TPMI. | Same throttle/counter behavior as PL1 harass. | PL2 throttle not observed or counters not progressing. |
| 10 | Restore original PL1/PL2 limits. Write saved baseline values back to TPMI socket_rapl_pl1_control and socket_rapl_pl2_control. | fast_throttle de-asserts; frequency recovers above Pm. | Frequency does not recover; fast_throttle remains asserted. |
| 11 | Verify throttle released. Wait ~5 seconds, re-check throttle status. | Core ratios recover above PM_RATIO. fast_throttle de-asserted. Fast RAPL throttling not in progress. No MCA, no hang. | Core ratios remain at Pm; MCA or system hang. |
| 12 | Poll final coverage registers via pmx_coverage.poll_all_registers(). | All measured registers captured; test exits cleanly (exit code 0). | Script exits with non-zero code or print_and_exit error. |

### Pass / Fail Criteria

- **PASS**: Per TCD 16031169418 §5 — fast_throttle asserted when PID output < Pm; clock div + arch throttle applied; freq drops below Pm on both CBBs; recovery when PID output >= Pm after PL1/PL2 restore. All perf status counters progressing. PLR attributed. Energy counter monotonically increasing. No MCA or hang. Script exit code 0.
- **FAIL**: Core ratios remain above Pm during throttle phase (mean_core_ratio - PM_RATIO > 1); PLR = 0 across all compute dies during throttle; package_energy_status stale; frequency does not recover after restore; script exits with non-zero code or print_and_exit error; MCA or system hang at any point.

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| socket_rapl_pid_output | sv.socket0.nio.pcudata.socket_rapl_pid_output | <= PM_RATIO during throttle; > PM_RATIO after restore |
| target_wp1.core_frequence | Per-core via die.core_pmsb path | Converges to ~Pm during throttle; recovers after restore |
| plr_die_level | Per compute die pcudata + TPMI fallback | Non-zero during throttle |
| dfo_pkg_rapl_perf_status | sv.socket0.nio.dfo_pkg_rapl_perf_status | Progressing (not stale) during throttle |
| dfo_primary_plane_rapl_perf_status | sv.socket0.nio.dfo_primary_plane_rapl_perf_status | Progressing (not stale) during throttle |
| package_energy_status (TPMI) | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status | Monotonically increasing throughout test |
| pkg_therm_status.power_limitation_log | MSR or CSR | Set during throttle phase |
| die.pcudata.min_mesh_ratio | Per compute die | Converges to Pm during throttle |

### Post-Process

N/A

### Notes

- NWP uses single NIO die as RAPL root (vs dual-IMH on DMR). fast_throttle fans out to 2 CBBs instead of 4. Same PrimeCode NN-PID algorithm; same TPMI programming model.
- Command line adaptation: dmr.xml -> nwp.xml. Script auto-detects NIO topology.
- NWP: 2 CBBs x 48 cores; DMR: 4 CBBs x 32 cores.
- TPMI root path: sv.socket0.nio.punit (NWP) vs sv.socket0.imh0.punit (DMR).

### References

- [TCD 16031169418 -- Socket RAPL - Below-Pm / Fast Throttle](https://hsdes.intel.com/appstore/article-one/#/16031169418)
- [Wave 3 Common HAS — Throttling Below Pm](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html#throttling-below-pm-spr-onwards)
- [DMR RAPL Simplification](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_rapl_simplification.html)
- [PrimeCode RAPL DMR](https://docs.intel.com/documents/primecode/primecode_one/firmware%20architecture/ip%20drivers%20and%20libraries/rapl_dmr.html)

---

## Section A: NWP Delta

NWP carries forward DMR Socket RAPL below-Pm behavior with topology change: single NIO replaces dual IMH (1 PrimeCode root, 2 CBBs instead of 4). No bounded NWP Socket RAPL delta clause was retrieved from Co-Design specs — safe working assumption is DMR carry-forward.

| Aspect | DMR | NWP |
|--------|-----|-----|
| Command line | python runPmx.py -x dmr.xml -p cpu_rapl -tM 6 -M 3 | python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3 |
| Root die | IMH-P (dual IMH: IMH0 root, IMH1 leaf) | NIO (single root die) |
| CBB count | 4 CBBs | 2 CBBs |
| Cores per CBB | up to 32 | up to 48 |
| fast_throttle path | IMH-P -> IMH-S -> CBBx4 (HPM 0x14) | NIO -> CBBx2 (HPM 0x14) |
| TPMI root path | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control |
| PID output path | socket.imh0.pcudata.socket_rapl_pid_output | socket.nio.pcudata.socket_rapl_pid_output |

## Section F: Recommendations

Recommendation: ADOPT — dmr.xml -> nwp.xml; read NWP Pm from fuse/MSR; below-Pm behavior per Wave 3 HAS. Priority: Medium — plc.feature.p2; below-Pm RAPL throttle validates an extreme boundary condition of the power management control loop.
