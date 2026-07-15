# CBB CCF PM Cstate Wake Events Across Activeidle

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422868](https://hsdes.intel.com/appstore/article-one/#/22022422868) |
| **Title** | CBB CCF PM Cstate wake events across Activeidle |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CCF PM States / Active-Idle / Wake Events |
| **Parent TCD** | [22022421180](https://hsdes.intel.com/appstore/article-one/#/22022421180) |
| **KB last updated** | 2026-07-08 |

---

## Test Case Intent

Verify that CBB CCF correctly handles C-state wake events while the CCF is in an active-idle (low-activity) state. Specifically, inject a C-state or frequency-change request while CCF is idling, and confirm that CCF responds — updating `ia_distress` level and driving a frequency change — without hanging or missing the wake event.

**Note on original Opens:** The three opens in the original HSD (fuse format, fuse location, VF point count) are copy-paste errors from a sibling TC (VF Curves). They do not apply to this TC.

**Flow (from original):** Wake event across while CCF is in active idle state.

**Test script:** `pmx_ccf_cbo.py --test_ccf_cstate_x_wake_event` → `ccfu.cbb_ccf_cstate_x_wake_event_test(sktNum, 'cbbs')`.

**⚠️ Script implementation status:** The function `cbb_ccf_cstate_x_wake_event_test` in `ccf_utils.py` is **registered but not fully implemented**. The current body reads `ring_distress_status.ia_distress` twice and logs the path, but contains no pass/fail comparison. The test body is commented out. This TC **requires implementation** before silicon validation.

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; PCode and CCF PMA initialized |
| C-states enabled | `ProcessorC1eEnable`, `PackageCState` BIOS knobs enable C6 |
| CCF in active-idle state | CCF at low activity (cores in light workload or C0 idle) |
| PEGA available | `import diamondrapids.pm.pmutils.pega as pega` succeeds |
| `ring_distress_status` readable | `cbb.base.punit_regs.punit_pmsb.pmsb_pcu.ring_distress_status` accessible |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read baseline CCF state: `ring_distress_status.ia_distress` and `ufs_status.current_ratio` per CBB while system is at active-idle | Non-zero ratio; `ia_distress` reflects low stress level | Zero ratio — CCF not running |
| 2 | Inject a C-state wake event via PEGA: `pega.pegaCstate(sktNum, dieName, domainDict={'c1e':'all'})` then release to C0 | PEGA accepted; cores return to C0 | PEGA error; cores stuck in C-state |
| 3 | Read `ring_distress_status.ia_distress` after wake | `ia_distress` changes from sleep value — CCF responded to wake event | `ia_distress` unchanged — CCF not responding to wake |
| 4 | Inject PEGA P-state request while CCF is in active-idle: `ccfu.ccf_pegaPstate(sktNum, dieName, clrgv=target_ratio)` | `ufs_status.current_ratio` updates to target within 1s | Ratio unchanged — CCF stuck in idle |
| 5 | Repeat for all CBBs; verify each CBB independently tracks its wake events | All CBBs update `ia_distress` and `current_ratio` after wake | Any CBB frozen — per-die wake handling broken |

---

## Pass / Fail Criteria

**PASS:** `ring_distress_status.ia_distress` changes in response to C-state wake injection; `ufs_status.current_ratio` updates after PEGA P-state request while CCF is in active-idle; no CBB hangs or misses wake events.

**FAIL:** `ia_distress` unchanged after wake event injection; CCF ratio stuck at idle value; any CBB unresponsive to wake signals.

---

## Post-Process

Save: `ring_distress_status`, `ufs_status.current_ratio`, `ccf_wp_status` register dumps per CBB before and after wake event injection.

---

## Script Gap Note

`cbb_ccf_cstate_x_wake_event_test()` in `ccf_utils.py` reads `ia_distress` twice but has no comparison logic (commented out). Steps above define what the full implementation should verify. The pass/fail criteria in this TC should drive the implementation of the test function.

---

## References

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#switching-between-fast-gv-drainless-gv)
- [CBB CCF Power Management HAS (CCF GV)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [CBB Power Event Generation Architecture (PEGA)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html)
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html)
- [pCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
