# CBB CCF GV TPMI Request

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422859](https://hsdes.intel.com/appstore/article-one/#/22022422859) |
| **Title** | CBB CCF GV TPMI Request |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Fabric DVFS / CBB CCF GV / TPMI interface |
| **Parent TCD** | [22022421171](https://hsdes.intel.com/appstore/article-one/#/22022421171) |
| **KB last updated** | 2026-07-08 |

---

## Test Case Intent

Verify that CBB CCF GV UFS features are controlled exclusively through TPMI registers (`UFS_CONTROL`, `UFS_STATUS`, `UFS_HEADER`) with per-die scoping — one independent TPMI instance per CBB. Legacy MSR 0x620, 0x621 and BIOS_SPARE2 interfaces are deprecated on DMR; TPMI is the only SW interface.

**Open #1 resolved — CCF GV TPMI entries in LUT:** YES. Each CBB has its own TPMI PFS entry and LUT offset for the UFS register bank. Confirmed via `ccf_utils.py:ccf_tpmi_gv_sweep()` which accesses `cbb.base.tpmi.ufs_control` per-die, and `TpmiIpLib.c:TpmiSetUfsControlRegPerHub()` which writes per-CBB via TPMI indexed access.

**Flow:**

- Ensure control of UFS features through TPMI registers — read `UFS_HEADER`, `UFS_CONTROL`, `UFS_STATUS` on each CBB via `sv.sockets.cbbs.base.tpmi.*`
- Verify per-die scoping — write different ratios to cbb0 and cbb1 independently; confirm each CBB holds its own value
- Sweep CCF frequency range via in-band TPMI write to `UFS_CONTROL.MAX_RATIO/MIN_RATIO`; verify `UFS_STATUS.CURRENT_RATIO` responds per-die

**Test script:** `pmx_ccf_cbo.py --test_ccf_tpmi_gv` → `ccf_utils.ccf_tpmi_gv_sweep_test(sktNum, 'cbbs', 'fu', cs=True)`.

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; PCode initialized |
| TPMI accessible per CBB | `sv.sockets.cbbs.base.tpmi.ufs_header` readable; `AUTONOMOUS_UFS_DISABLED=0` |
| Python-SV available | `import namednodes; sv = namednodes.sv` succeeds |
| BIOS knobs | Default (`UncoreFreqCtrlCbb=1`, `UncoreFreqRatioCbb=0`) |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read `UFS_HEADER` per CBB: `cbb.base.tpmi.ufs_header.interface_version` and `.autonomous_ufs_disabled` | `interface_version=0x2`; `autonomous_ufs_disabled=0` on all CBBs | Non-zero disable bit — CCF GV TPMI not initialized |
| 2 | Read `UFS_CONTROL` per CBB: `.ufs_throttle_mode`, `.max_ratio`, `.min_ratio`, `.efficiency_latency_ctrl_ratio` | All fields readable; non-garbage values; throttle_mode=1 (default Clamp) | Read error or all-zero fields — TPMI not enumerated for this CBB |
| 3 | Verify per-die scoping: write `max_ratio=10` to cbb0 and `max_ratio=14` to cbb1 via TPMI; read both back | cbb0 reads 10; cbb1 reads 14 — independent per-die | Writes bleed across CBBs — per-die scoping broken |
| 4 | Sweep full fused [Pm..P0] range via in-band TPMI: `ccf_tpmi_gv_sweep_test(skt, 'cbbs', 'fu', cs=True)` | Each requested ratio reflected in `UFS_STATUS.CURRENT_RATIO`; no ratio mismatch logged | Any mismatch — TPMI write not reaching CCF GVFSM |
| 5 | Read fused P0 and Pm from TPMI SST: `cbb.base.tpmi.sst_pp_info_11.p0_fabric_ratio` and `.pm_fabric_ratio`; confirm GVFSM clamps to fused range | Ratios outside [Pm, P0] are clipped to fused boundary | No clipping — TPMI enforcement not active |

---

## Pass / Fail Criteria

**PASS:** All `UFS_CONTROL` and `UFS_STATUS` fields accessible per CBB via TPMI. Per-die scoping confirmed (independent writes to cbb0 and cbb1 hold separate values). Full [Pm..P0] frequency sweep completed with CURRENT_RATIO tracking injected value. GVFSM clamps out-of-range requests to fused boundary.

**FAIL:** Any TPMI UFS register unreadable or returning zero; per-die isolation broken (write to one CBB affects another); CURRENT_RATIO does not track TPMI write; no fused-range clipping.

---

## Post-Process

Save: `UFS_HEADER`, `UFS_CONTROL`, `UFS_STATUS` register dumps for all CBBs; per-die sweep pass/fail ratio list; fused P0/Pm from `sst_pp_info_11`.

---

## References

- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html)
- [Architectural UFS TPMI Interface](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html#dmr-family)
- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [Uncore Frequency Scaling in a Hierarchical SoC](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/Hierarchical%20UFS/HPM_UFS.html#bios-control)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [DMR SoC HAS](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/DMR_Overview_HAS.html#figure-hub-and-spoke)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html)
- [pCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
