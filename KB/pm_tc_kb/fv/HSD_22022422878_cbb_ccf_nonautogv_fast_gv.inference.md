# CBB CCF NonAutoGV Mode - Fast GV

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422878](https://hsdes.intel.com/appstore/article-one/#/22022422878) |
| **Title** | CBB CCF NonAutoGV Mode - Fast GV |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CCF GV / NonAutoGV / Fast GV mode |
| **Parent TCD** | [22022421183](https://hsdes.intel.com/appstore/article-one/#/22022421183) |
| **KB last updated** | 2026-07-08 |

---

## Test Case Intent

Verify that CBB CCF operates in NonAutoGV mode (AutoGV is NOT POR) and correctly executes GV transitions via the CCF_WP register using Fast GV with PLLs in default PLL mode (`pll_mode=0`). Confirm that AutoGV mode is not enabled, that CCF responds to target workpoints written to CCF_WP across the full Pm→P0 range, that UFS_STATUS tracks each injected ratio, and that NonAutoGV mode persists after C-state exit. This is the **POR validation test** for the NonAutoGV Fast GV path.

> **Note:** PLL crawling (survivability mode with `pll_mode_ovrden=1 + pll_mode=1`) is validated by sibling TC [16031123820](https://hsdes.intel.com/appstore/article-one/#/16031123820) under the same TCD. This TC covers the default/POR path only.

**Test script:** `pmx_ccf_cbo.py --test_ccf_fast_gv` → calls `cbb_ccf_fast_gv_default_test()`

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; PCode and CCF PMA initialized |
| CCF in NonAutoGV mode | `ringepll_top.fusecr_ovrd_0.pll_mode == 0` (PLL mode = Fast GV) on all CBBs |
| PEGA available | `import diamondrapids.pm.pmutils.pega as pega` succeeds |
| CCF_WP readable | `cbb.base.ccf_pma.ccf_pmc_regs.ccf_wp[0].target_max_ratio` accessible |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read Ring East and Ring West PLL mode per CBB: `cbb.base.ringepll_top.fusecr_ovrd_0.pll_mode` and `ringwpll_top.fusecr_ovrd_0.pll_mode` | Both = 0 (PLL mode = Fast GV) on all CBBs — AutoGV not active | Any CBB shows `pll_mode != 0` — wrong mode |
| 2 | Verify `pll_mode_ovrden == 0` on all CBBs — no override active at boot | Override not asserted = hardware default confirmed | `pll_mode_ovrden != 0` — override unexpectedly active |
| 3 | PEGA GV sweep Pm→P0: `ccf_pegaPstate(sktNum, cbbN, clrgv=r, chkstr='ccf_wp,ufs_status')` for each ratio in fused range | `ccf_wp[0].target_max_ratio` and `ufs_status.current_ratio` match each injected ratio | Any ratio not reflected — CCF_WP or UFS_STATUS mismatch |
| 4 | Read `ccf_wp_status.ratio` after each injection | Matches injected `clrgv` — PCode interpretation correct | Mismatch — PCode not honoring CCF_WP |
| 5 | Cycle core C-state: inject c1e via PEGA, release to C0. Re-read `pll_mode` | `pll_mode` remains 0 (PLL mode) after C-state exit — NonAutoGV persists | `pll_mode` changed — mode not preserved across C-state |
| 6 | Release PEGA; verify `ufs_status.current_ratio` returns to fused P0 | Ratio returns to fused maximum — no stuck workpoint | Ratio stuck at last injected value |

---

## Pass / Fail Criteria

**PASS:** All CBBs show `pll_mode==0` and `pll_mode_ovrden==0` at boot; `ccf_wp[0].target_max_ratio` and `ufs_status.current_ratio` track each PEGA-injected ratio across full Pm→P0 sweep; `ccf_wp_status.ratio` matches; `pll_mode` unchanged after C-state cycle; ratio returns to fused P0 after PEGA release.

**FAIL:** Any CBB shows `pll_mode != 0` at boot; `pll_mode_ovrden` unexpectedly set; CCF_WP or UFS_STATUS not reflecting PEGA injection; ratio stuck after PEGA release; `pll_mode` changed after C-state.

---

## Post-Process

Save: `ringepll_top/ringwpll_top.fusecr_ovrd_0.pll_mode` per CBB (before/after C-state), `ccf_wp[0].target_max_ratio`, `ccf_wp_status.ratio`, PEGA injection log.

---

## References

- [CBB CCF Power Management HAS (Fast GV / Drainless GV)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#switching-between-fast-gv-drainless-gv)
- [CBB CCF Power Management HAS (CCF GV)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [CBB Power Event Generation Architecture (PEGA)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html)
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [CBB CCP PM Integration HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCP%20HAS/cbb_cpp_has.html#vf-curves-grouping)
- [pCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
