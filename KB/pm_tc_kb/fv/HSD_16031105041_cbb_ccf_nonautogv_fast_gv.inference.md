# TC Deep Analysis: CBB CCF NonAutoGV Mode — Fast GV

| Field | Value |
|-------|-------|
| **HSD ID** | 16031105041 |
| **Title** | CBB CCF NonAutoGV Mode - Fast GV |
| **Date** | 2026-07-15 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | CBB CCF GV Control Interface |
| **Sub-Feature** | NonAutoGV Mode — Fast GV (FLL mode, PLL crawling variant) |
| **Parent TCD** | [22022421168 — CBB CCF PM GV Control Interface](https://hsdes.intel.com/appstore/article-one/#/22022421168) |

---

## Test Case Intent

Verify that the CBB CCF ring operates correctly in **NonAutoGV mode** (the POR reset-default GV mode for CBB) using the **Fast GV in FLL mode** execution path. In NonAutoGV mode, CCF does not autonomously choose its target working point; instead it responds to `CCF_WP` register writes from PCode and executes the GV transition to the requested ratio. This TC validates two execution sub-modes: (1) **Fast GV default** — CCF PMA in FLL mode (`CCF_UCLK_GV_CFG.legacy_gv_enable=0`), GV step without UCLK stop, POR path for CBB; and (2) **PLL crawling** — CCF PMA in FLL mode with PLL fuse override (`pll_mode=1, pll_mode_ovrden=1`), survivability option. AutoGV and Drainless GV (UCLK stop) are NOT POR for CBB since D2D does not support UCLK stop.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| System booted to OS | BIOS CPL4 complete; PCode running CCF GV |
| CCF in NonAutoGV mode | `CCF_WP` register writable (reset default after cold boot or C-state exit) |
| PEGA available | `import diamondrapids.pm.pmutils.pega as pega` succeeds; PEGA released before test |
| PythonSV namednodes accessible | `sv.sockets.socketN.cbbs.cbbX` paths readable |
| Fuse PLL override (PLL crawling sub-test only) | `pll_mode=1, pll_mode_ovrden=1` set via fuse override register or BIOS knob |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Confirm CCF is in NonAutoGV mode at baseline: read `UFS_STATUS.CURRENT_RATIO` per CBB | Ratio matches PCode-assigned working point; register accessible | Register read failure — CCF not initialized |
| 2 | **Fast GV default test:** call `cbb_ccf_fast_gv_default_test(skt_num, 'cbbs')` — injects `CCF_WP` targets across the fused [Pm..P0] range and verifies GV execution | For each injected ratio: `UFS_STATUS.CURRENT_RATIO` converges to target within timeout; GVFSM completes (busy→done) | Ratio mismatch or GVFSM stuck — Fast GV execution broken |
| 3 | **PLL crawling test:** call `cbb_ccf_fast_gv_pll_crawling_test(skt_num, 'cbbs')` — with PLL fuse override, verifies ratio change via PLL crawling path | Ratio changes correctly via PLL crawling mechanism; `CURRENT_RATIO` matches target | Ratio stuck — PLL crawl config not applied or fuse override ineffective |
| 4 | Verify both CBBs (cbb0, cbb1) independently complete GV transitions without interference | Each CBB shows correct ratio independently; no cross-CBB interference | One CBB stalls while other succeeds — per-CBB GVFSM issue |

---

### Pass / Fail Criteria

- **PASS**: Fast GV default: all injected ratios reflected in `UFS_STATUS.CURRENT_RATIO` within timeout; GVFSM completes for all CBBs. PLL crawling: ratio changes correctly via PLL crawl path with fuse override applied. No GVFSM hang, no cross-CBB interference.
- **FAIL**: Any ratio mismatch between injected `CCF_WP` and `UFS_STATUS.CURRENT_RATIO`; GVFSM stuck busy; PLL crawl not responding to fuse override.

---

### Post-Process

Save `UFS_STATUS.CURRENT_RATIO` per CBB at each GV step; GVFSM busy/done timing; fuse override register values for PLL crawling sub-test.

---

### References

- [CBB CCF Power Management HAS — CCF GV section](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [TCD 22022421168 — CBB CCF PM GV Control Interface](https://hsdes.intel.com/appstore/article-one/#/22022421168)
- [TC 22022422851 — CBB CCF GV PEGA Injection](https://hsdes.intel.com/appstore/article-one/#/22022422851)
- [TC 22022422859 — CBB CCF GV TPMI Request](https://hsdes.intel.com/appstore/article-one/#/22022422859)
