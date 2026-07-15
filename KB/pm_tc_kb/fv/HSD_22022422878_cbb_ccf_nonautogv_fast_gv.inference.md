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

Verify that CBB CCF operates in NonAutoGV mode (AutoGV is NOT POR) and correctly executes GV transitions via the CCF_WP register using Fast GV (PLL mode). Confirm that AutoGV mode is not enabled, that CCF responds to target workpoints written to CCF_WP, and that NonAutoGV mode persists after reset or C-state exit.

**Open resolved — Drainless GV or Fast GV?** **Fast GV (PLL mode)** is the NonAutoGV transition method. Confirmed by `cbb_ccf_fast_gv_default_test()` in `ccf_utils.py` which verifies both Ring East and Ring West PLLs are in PLL mode (`ringepll_top.fusecr_ovrd_0.pll_mode == 0`). The `cbb_ccf_fast_gv_pll_crawling_test()` additionally exercises FLL mode (Drainless GV path) as a contrast/comparison test and restores PLL mode afterward.

**Flow (NonAutoGV mode):**

- CBB CCF AutoGV Mode does NOT enable — verify default state is NonAutoGV (PLL mode on Ring East + West PLLs)
- CBB CCF responds to target workpoint in CCF_WP register (`cbb.base.ccf_pma.ccf_pmc_regs.ccf_wp[0].target_max_ratio`) and executes Fast GV transition
- Match PCode interpretation — `ccf_wp_status.ratio` tracks the injected CCF_WP target after PEGA injection
- NonAutoGV mode remains OFF after reset or C-state exit — verify `pll_mode` is still 0 (PLL mode) after core C-state cycle
- CCF_WP can only be updated when CCF is in NonAuto Mode — verify write succeeds only in PLL mode, not FLL mode

**Test scripts:** `pmx_ccf_cbo.py --test_ccf_fast_gv` runs two tests:
1. `cbb_ccf_fast_gv_default_test()` — verifies PLL mode (Fast GV default) on all CBBs
2. `cbb_ccf_fast_gv_pll_crawling_test()` — exercises FLL/PLL mode switch (Drainless GV path)

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
| 2 | Inject CCF_WP target via PEGA: `ccf_pegaPstate(sktNum, cbbN, clrgv=target_ratio, chkstr='ccf_wp')`. Read `ccf_wp[0].target_max_ratio` | `target_max_ratio` matches injected ratio; CCF executes Fast GV transition | Ratio not reflected — CCF_WP write rejected or CCF not responding |
| 3 | Verify `ccf_wp_status.ratio` matches `ccf_wp[0].target_max_ratio` | Status tracks working point — PCode interpretation matches | Mismatch — PCode not honoring CCF_WP |
| 4 | Cycle core C-state: inject c1e via PEGA, then release to C0. Re-read `pll_mode` | `pll_mode` remains 0 (PLL mode) after C-state exit — NonAutoGV persists | `pll_mode` changed — mode not preserved across C-state |
| 5 | Write `pll_mode=1` (FLL mode = Drainless GV) on both ring PLLs; verify write accepted; restore to PLL mode | FLL mode accepted and verified; PLL mode restored cleanly | Write rejected or PLL restore fails — mode switch broken |

---

## Pass / Fail Criteria

**PASS:** `ringepll_top/ringwpll_top.fusecr_ovrd_0.pll_mode == 0` (PLL mode) on all CBBs at boot; CCF_WP `target_max_ratio` reflects PEGA-injected workpoint; `ccf_wp_status.ratio` matches; `pll_mode` unchanged after C-state cycle; FLL/PLL mode toggle succeeds.

**FAIL:** Any CBB shows `pll_mode != 0` at boot (AutoGV wrongly enabled); CCF_WP not updated; `ccf_wp_status.ratio` diverges from target; `pll_mode` changed after C-state.

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
