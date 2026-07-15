# CBB CCF GV PEGA Injection

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422851](https://hsdes.intel.com/appstore/article-one/#/22022422851) |
| **Title** | CBB CCF GV PEGA Injection |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Fabric DVFS / CBB CCF GV / PEGA |
| **Parent TCD** | [22022421168](https://hsdes.intel.com/appstore/article-one/#/22022421168) |
| **KB last updated** | 2026-07-08 |

---

## Test Case Intent

Induce CBB CCF ring frequency changes via PEGA P-state injection and verify frequency tracks via TPMI `UFS_STATUS.CURRENT_RATIO`. Covers uncore p-state randomization and p-state hold (single-shot) across the full fused [Pm, P0] CCF frequency range.

**CBB CCF PEGA support:** YES — `pega.py:issuePegaReq_CBB()` sets `CMD1.ring_ratio = clrgv` and writes to CBB PEGA mailbox (`cbb.pcode.vars.pega`). Verification reads `cbb.base.tpmi.ufs_status.current_ratio` and `cbb.base.punit_regs.punit_pmsb.pmsb_pcu.ccf_wp_status.ratio`.

**Flow:**

- Uncore p-state randomization with PEGA — inject random CCF ring ratios via `pega.uncoreRatioSingleShot()` or `clrgv='rand'`; verify `UFS_STATUS.CURRENT_RATIO` tracks
- Uncore p-state hold with PEGA — inject fixed CCF ring ratio via `pega.allCoreUncoreRatioSingleShot()` or `ccf_pegaPstate_test()`; verify ratio held across full [Pm, P0] range
- Verify via TPMI — use `cbb.base.tpmi.ufs_status.current_ratio` as primary check; corroborate with `ccf_wp_status.ratio` and `ccf_pma.ccf_pmc_regs.ccf_wp[0].target_max_ratio`

**Test script:** `pmx_ccf_cbo.py --test_ccf_pega_pstate` → `ccf_utils.ccf_pegaPstate_test(sktNum, 'cbbs', clrgv=<ratio>)`. Manual use: `pega.allCoreUncoreRatioSingleShot(0, 'all', coreFreq, meshFreq)` or `pega.ping_pong_pstates(duration, low, high, imesh0=<low>, imesh1=<high>)`.

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; PCode initialized; CCF GV enabled (`UFS_HEADER.AUTONOMOUS_UFS_DISABLED=0`) |
| PEGA available | `import diamondrapids.pm.pmutils.pega as pega` succeeds |
| TPMI accessible per CBB | `sv.sockets.cbbs.base.tpmi.ufs_status` readable |
| BIOS knobs | Default; `UncoreFreqCtrlCbb=1` (Clamp), `UncoreFreqRatioCbb=0` (dynamic) |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read fused CCF [Pm, P0] range per CBB: `cbb.base.tpmi.sst_pp_info_11.pm_fabric_ratio` and `.p0_fabric_ratio` | Non-zero Pm and P0; P0 > Pm | Zero or inverted range — fuse read failure |
| 2 | Inject fixed ring ratio at P0 via PEGA: `pega.uncoreRatioSingleShot(skt, 'cbb0', p0_ratio)`. Sleep 1s. Read `ufs_status.current_ratio` and `ccf_wp_status.ratio` | Both match injected ratio | Ratio not updated — PEGA injection not reaching CCF |
| 3 | Sweep full CCF range [Pm..P0] using `ccf_pegaPstate_test(sktNum, 'cbbs', clrgv=i)` for each ratio | Each ratio reflected in `ufs_status.current_ratio`; no error logged | Any ratio mismatch — GVFSM not following PEGA request |
| 4 | Inject random ring ratio (`clrgv='rand'`): `pega.pegaPstate(sktNum=0, dieName='cbb0', clrgv=-1, rearmTimems=100)`. Let run 10s. Sample `ufs_status.current_ratio` multiple times | Ratio varies across samples; stays within [Pm, P0] bounds | Fixed ratio despite random injection; ratio out of fused range |
| 5 | Ping-pong between low (Pm) and high (P0) ratios: `pega.ping_pong_pstates(duration=60, low=1, high=1, imesh0=pm_ratio, imesh1=p0_ratio)`. Sample `ufs_status.current_ratio` during each phase | Ratio alternates between Pm and P0 with each interval | No alternation; ratio stuck at one value |

---

## Pass / Fail Criteria

**PASS:** CCF ring frequency can be set across the full fused [Pm, P0] range via PEGA on all CBBs. `UFS_STATUS.CURRENT_RATIO` reflects injected values within 1 tick. Random injection keeps ratio within fused bounds. Ping-pong alternation observed.

**FAIL:** Any injected ratio not reflected in `UFS_STATUS.CURRENT_RATIO` or `CCF_WP_STATUS.ratio`; ratio outside [Pm, P0] fused range; no variation during random injection.

---

## Post-Process

Save: per-CBB ratio traces during sweep and ping-pong, fused P0/Pm from `sst_pp_info_11`, PEGA mailbox register dumps (`pcode.vars.pega`).

---

## References

- [CBB Power Event Generation Architecture (PEGA)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html)
- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [Architectural UFS TPMI Interface](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html#dmr-family)
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html)
- [Uncore Frequency Scaling in a Hierarchical SoC](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/Hierarchical%20UFS/HPM_UFS.html#bios-control)
- [pCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
- [Power Event Generation Architecture (PEGA) wiki](https://wiki.ith.intel.com/display/ServerPcode/PEGA)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html)
