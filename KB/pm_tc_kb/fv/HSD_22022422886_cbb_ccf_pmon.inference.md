# CBB CCF PMON

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422886](https://hsdes.intel.com/appstore/article-one/#/22022422886) |
| **Title** | CBB CCF PMON |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CCF PMON / Ring Scalability Telemetry |
| **Parent TCD** | [22022421186](https://hsdes.intel.com/appstore/article-one/#/22022421186) |
| **KB last updated** | 2026-07-08 |

---

## Test Case Intent

Verify post-silicon extraction of CBB CCF ring scalability telemetry via PMON (Performance Monitoring Unit) counters. Ensure that PMON CLR (Compute Ring Scalability) counters can be enabled, programmed with RING_SCALE_EVENTS, and produce non-zero counts during CCF activity. Also verify PMON Fast C3 residency counter increments during Fast Ring C3 events.

**Open resolved — PMON POR?** YES. CLR PMON is implemented in hardware at `cbb.base.i_ccf_env{N}.egress_{00-77}.pmoncounter[0-3]` with event selection, freeze/unfreeze, and counter-control registers. Test infrastructure exists in `ccf_utils.py` (`ccf_pmon_clr_*` functions). Fast C3 residency is at `cbb.base.ccf_pma.ccf_pmc_regs.fast_c3_residency.counter`.

**Flow:** Post-silicon telemetry extraction — verify ring scalability PMON counters and Fast C3 residency counter are accessible and produce non-zero counts during CCF activity.

**Note on existing script vs TC intent:** `--test_ccf_pmon` calls `ccf_pmon_clr_disable_test()` which tests the FREEZE mechanism (frozen counters stay zero = PASS). The TC intent (counters are NON-ZERO during activity) requires enabling counting with a workload and verifying increment. Both aspects are needed.

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; PCode initialized |
| CCF PMON accessible | `cbb.base.i_ccf_env0.egress_00.pmoncountercontrol[0]` readable/writable |
| Fast C3 residency accessible | `cbb.base.ccf_pma.ccf_pmc_regs.fast_c3_residency.counter` readable |
| PEGA available | For injecting CCF activity to drive PMON counts |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | For each CBB, reset CLR PMON: `ccf_pmon_clr_unitcontrol_op(skt, cbb, 'i_ccf_envs', 'egresss', op='w', w_dict={'frz':1,'rst_ctrl':1,'rst_ctrs':1})` | All counters reset to 0; no error | Reset fails — PMON registers inaccessible |
| 2 | Program RING_SCALE_EVENTS: `ccf_pmon_clr_countercontrol_op(..., op='w', w_dict={'ev_sel':0x24,'umask':0x3f})` | Event select written; `ev_sel=0x24` reads back | Write rejected — counter control not programmable |
| 3 | Enable counting (unfreeze): `ccf_pmon_clr_unitcontrol_op(..., op='c')`. Inject CCF activity via PEGA: `pega.uncoreRatioSingleShot(skt, cbb, target_ratio)`. Wait 15s. Freeze again. Read counters | At least one `pmoncounter[N].event_count > 0` — ring scale events counted | All counters stay 0 — no CCF activity counted; PMON not functional |
| 4 | Verify PMON CLR freeze: freeze and verify counters do NOT change: `ccf_pmon_clr_disable_test(skt, 'cbbs', 'i_ccf_envs', 'egresss', 'all', rtime=100)` | PASS (diff==0) — frozen counters stable | FAIL (diff>0) — frozen counters changed; freeze mechanism broken |
| 5 | Verify Fast C3 residency: read baseline `fast_c3_residency.counter`; inject Fast C3 via PEGA C-state; re-read | `fast_c3_residency.counter` incremented — Fast C3 residency tracked | Counter unchanged — Fast C3 PMON not functional |

---

## Pass / Fail Criteria

**PASS:** CLR PMON counters accessible and programmable per CBB; at least one `pmoncounter[N].event_count > 0` after RING_SCALE_EVENTS programming and CCF activity; freeze mechanism works (frozen counters stay stable); `fast_c3_residency.counter` increments after Fast C3 injection.

**FAIL:** Any PMON counter register inaccessible; all counters remain 0 after activity; freeze mechanism broken (counters change while frozen); `fast_c3_residency.counter` does not increment.

---

## Post-Process

Save: PMON counter values (all CBBs, all i_ccf_env, all egress) before/after activity, `fast_c3_residency.counter` before/after Fast C3 injection.

---

## References

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#switching-between-fast-gv-drainless-gv)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [CBB Power Event Generation Architecture (PEGA)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html)
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html)
- [pCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
