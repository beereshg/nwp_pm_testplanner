# CBB CCF NonAutoGV Mode - Fast GV with PLL Crawling Override

| Field | Value |
|-------|-------|
| **HSD ID** | [16031123820](https://hsdes.intel.com/appstore/article-one/#/16031123820) |
| **Title** | CBB CCF NonAutoGV Mode - Fast GV with PLL Crawling Override |
| **Date** | 2026-07-15 |
| **Target Program** | NWP (Newport) |
| **Segment** | FV |
| **TCD** | CBB CCF NonAutoGV Mode |
| **TCD ID** | 22022421183 |
| **Status** | open |
| **Val Environment** | silicon,virtual_platform |
| **Owner Team** | soc.pm |
| **Automation** | pmx_ccf_cbo.py --test_ccf_fast_gv_pll_crawling |
| **Feature** | CBB CCF |
| **Sub-Feature** | NonAutoGV / PLL Crawl |
| **NWP Disposition** | Runnable_On_NWP |

---

## Test Case Intent

Verify that CBB CCF ring frequency GV transitions work correctly when PLL crawl mode is forced via `pll_mode_ovrden=1` + `pll_mode=1`. This is a survivability / alternate clocking-path test, not the POR path. Validates that GV sweeps complete within fuse-defined crawl constraints (`freq_crawl_delta_f`), and that the system restores to default PLL mode cleanly after the override. Sibling to POR Fast GV TC [22022422878](https://hsdes.intel.com/appstore/article-one/#/22022422878).

---

## Section A: NWP Delta

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | Up to 4 | **2** | Loop: range(4) to range(2) |
| Ring instances | E+W per CBB | **E+W per CBB** | Same per-CBB ring structure |
| PLL crawl registers | ringepll_top.fusecr_ovrd_0 | **same path** | No path change |
| PEGA interface | pega.release(1) | **same** | No change |

---

## Section B: NWP Test Procedure

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP silicon or VP; SVOS booted to CPL4 |
| CCF default PLL mode | pll_mode==0 and pll_mode_ovrden==0 on all CBBs before test |
| PEGA imported | pega.release(1) before sweep |
| Fused crawl params readable | freq_crawl_disable, freq_crawl_delta_f, freq_crawl_delta_t via ringepll_top.fusecr_ovrd_0 |

### Test Steps

| Step | Action | Expected Result (PASS) | Failure Indication |
|------|--------|------------------------|-------------------|
| 1 | Save baseline pll_mode and pll_mode_ovrden per CBB | Both == 0 (default) | Non-zero baseline; prior test left override asserted |
| 2 | Read fused crawl params: freq_crawl_disable, freq_crawl_delta_f, freq_crawl_delta_t from ringepll_top.fusecr_ovrd_0 | Values readable; freq_crawl_disable==0 | Registers unreadable or freq_crawl_disable==1 |
| 3 | Assert crawl override: write pll_mode_ovrden=1 then pll_mode=1 on Ring E and W per CBB; verify readback | pll_mode_ovrden==1 and pll_mode==1 on both rings of all CBBs | Override not accepted; readback mismatch |
| 4 | PEGA GV sweep Pm to P0 in 1-ratio steps: ccf_pegaPstate(clrgv=r) | Each step <= freq_crawl_delta_f; current_ratio tracks each ratio | Step exceeds freq_crawl_delta_f; ratio stuck or jumps |
| 5 | Reverse sweep P0 to Pm with same per-step crawl constraint check | Each down-step <= freq_crawl_delta_f; no large frequency jumps | Reverse step exceeds constraint |
| 6 | Release PEGA; restore pll_mode=0 then pll_mode_ovrden=0 on all CBBs; verify readback | pll_mode==0 and pll_mode_ovrden==0 confirmed | Restore fails; readback still shows override asserted |
| 7 | Post-restore: inject PEGA P0; verify current_ratio reaches P0 directly (no crawl) | Ratio reaches P0 in one step without crawl delay | Post-restore sweep still crawls; override not fully cleared |

### Health Checks

- No MCA or IERR during any step.
- current_ratio readable throughout sweep via ufs_status register.
- freq_crawl_disable==0 confirmed before override.
- After restore: both rings of all CBBs show pll_mode==0 and pll_mode_ovrden==0.

### Pass / Fail Criteria

- **PASS**: pll_mode_ovrden=1 accepted on all CBBs; each GV step <= freq_crawl_delta_f; no stuck frequency; pll_mode==0 and pll_mode_ovrden==0 confirmed after restore; post-restore P0 reached directly without crawl.
- **FAIL**: Override not accepted; any step > freq_crawl_delta_f; ratio stuck after PEGA release; restore to pll_mode=0 fails; post-restore sweep crawls instead of stepping directly.

---

## Section D: Spec Refs

- [CBB CCF NonAutoGV Mode TCD 22022421183](https://hsdes.intel.com/appstore/article-one/#/22022421183)
- [POR Fast GV TC 22022422878](https://hsdes.intel.com/appstore/article-one/#/22022422878)

---

## Section E: Risk Assessment

| Risk / Open Item | Likelihood | Severity | Mitigation |
|-----------------|------------|----------|-----------|
| NWP CBB count loop must use range(2) not range(4) | High | Medium | Hardcode num_cbbs=2 in script |
| freq_crawl_delta_f fuse value may differ per QDF | Medium | Medium | Read from hardware before sweep; log value |
