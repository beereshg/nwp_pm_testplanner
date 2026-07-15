# TCD 22022421183 — CBB CCF NonAutoGV Mode

| Field | Value |
|-------|-------|
| **HSD ID** | [22022421183](https://hsdes.intel.com/appstore/article-one/#/22022421183) |
| **Title** | CBB CCF NonAutoGV Mode |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420514 — CBB CCF Ring Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) |
| **Child TCs** | [22022422878](https://hsdes.intel.com/appstore/article-one/#/22022422878) — Fast GV Default (FLL Mode / POR)<br>[16031123820](https://hsdes.intel.com/appstore/article-one/#/16031123820) — Fast GV with PLL Crawling Override |
| **KB last updated** | 2026-07-15 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**CBB CCF NonAutoGV Mode** is the **only POR frequency management mode** for the CBB ring (CCF). Unlike AutoGV (not supported in CBB), NonAutoGV does not autonomously select voltage/frequency — it executes GV transitions exclusively in response to explicit workpoint commands written to the `CCF_WP` register by PCode/PUNIT.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        CBB CCF GV Architecture                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐    CCF_WP     ┌──────────┐   VF Curve   ┌─────────────┐  │
│  │  PCode   │──────────────▶│  GVFSM   │─────────────▶│ Ring PLL/FLL│  │
│  │  (PUNIT) │               │          │              │  Frequency   │  │
│  └──────────┘               │ IDLE     │              └─────────────┘  │
│       ▲                     │ BLOCK    │                     │          │
│       │ PEGA/TPMI           │ INC_GB   │                     ▼          │
│       │ injection           │ DEC_DB   │              ┌─────────────┐  │
│  ┌──────────┐               │ RESUME   │              │ ufs_status  │  │
│  │Validation│               │ BLK_INTF │              │ current_ratio│  │
│  │(OS/SW)   │               └──────────┘              └─────────────┘  │
│  └──────────┘                                                           │
│                                                                          │
│  ═══════════════════════════════════════════════════════════════════════  │
│  Clocking Modes (determined by ringepll_top.fusecr_ovrd_0.pll_mode):    │
│                                                                          │
│  ┌─────────────────────────────┐    ┌─────────────────────────────────┐ │
│  │ pll_mode=0 (PLL) [DEFAULT]  │    │ pll_mode=1 (FLL) [SURVIVABILITY]│ │
│  │ • Fast GV (POR)             │    │ • PLL Crawling mode             │ │
│  │ • No UCLK stop              │    │ • Freq steps ≤ freq_crawl_delta_f│ │
│  │ • Rapid V/F transition      │    │ • pll_mode_ovrden=1 required    │ │
│  │ • Used by: cbb_ccf_fast_gv_ │    │ • Used by: cbb_ccf_fast_gv_    │ │
│  │   default_test()            │    │   pll_crawling_test()           │ │
│  └─────────────────────────────┘    └─────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **NonAutoGV** | CCF does NOT autonomously select V/F. Only mode for CBB. Always active at boot and after C-state exit. |
| **AutoGV** | NOT POR for CBB. CCF autonomously selects V/F from internal utilization — disabled. |
| **Fast GV (POR)** | Default POR transition method. PLLs in PLL mode (`pll_mode=0`). No clock stop during GV. Rapid frequency transition. |
| **PLL Crawling** | Survivability mode. `pll_mode_ovrden=1 + pll_mode=1` forces FLL mode. Frequency steps limited by `freq_crawl_delta_f` fuse. |
| **Drainless GV** | Legacy term sometimes used for PLL-mode GV. UCLK not stopped; PLL re-locks during transition. |
| **CCF_WP** | Workpoint register written by PCode. `ccf_wp[0].target_max_ratio` sets the target ratio for the GV transition. |
| **GVFSM** | GV Finite State Machine: IDLE → BLOCK → INC_GB → DEC_DB → RESUME → BLK_INTF. Each state must complete before advancing. |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| CCF_WP (workpoint) | `sv.socket0.cbbN.base.ccf_pma.ccf_pmc_regs.ccf_wp[0].target_max_ratio` | PCode writes target ratio for GV |
| CCF_WP Status | `sv.socket0.cbbN.base.punit_regs.punit_pmsb.pmsb_pcu.ccf_wp_status.ratio` | Current resolved workpoint (readback) |
| UFS Status | `sv.socket0.cbbN.base.tpmi.ufs_status.current_ratio` | Actual operating ratio after GV completes |
| Ring E PLL mode | `sv.socket0.cbbN.base.ringepll_top.fusecr_ovrd_0.pll_mode` | 0=PLL (default), 1=FLL (crawl) |
| Ring W PLL mode | `sv.socket0.cbbN.base.ringwpll_top.fusecr_ovrd_0.pll_mode` | Same for West ring |
| PLL override enable | `sv.socket0.cbbN.base.ringepll_top.fusecr_ovrd_0.pll_mode_ovrden` | Must be 1 to override pll_mode |
| Crawl delta_f | `sv.socket0.cbbN.base.ringepll_top.fusecr_ovrd_0.freq_crawl_delta_f` | Max frequency step per crawl transition |
| Crawl delta_t | `sv.socket0.cbbN.base.ringepll_top.fusecr_ovrd_0.freq_crawl_delta_t` | Time between crawl steps |
| Crawl disable | `sv.socket0.cbbN.base.ringepll_top.fusecr_ovrd_0.freq_crawl_disable` | 0=crawl enabled, 1=disabled |
| PEGA injection | `pega.pegaPstate(sktNum, cbbN, clrgv=ratio)` | Inject synthetic GV request bypassing OS |
| Fused min ratio (Pm) | `sv.socket0.cbbN.base.tpmi.sst_pp_info_11.pm_fabric_ratio` | Lower bound of GV sweep |
| Fused max ratio (P0) | `sv.socket0.cbbN.base.tpmi.sst_pp_info_11.p0_fabric_ratio` | Upper bound of GV sweep |

---

## Section 3: Reset / Power / Clocking

- **Cold boot / Reset**: CCF starts in NonAutoGV mode with PLLs in their default state (`pll_mode=0`, `pll_mode_ovrden=0`). Frequency set from UFS_HEADER fused caps.
- **C-state exit**: NonAutoGV mode persists. `pll_mode` remains 0 after core C-state cycle.
- **PC6 exit**: CCF resumes at last programmed workpoint. No mode change.
- **PLL crawl override**: Must be explicitly programmed at runtime. Not preserved across reset.

---

## Section 4: Programming Model

### Fast GV (POR) — Default Path
```python
# Verify default state (expected at boot)
assert dieObj.base.ringepll_top.fusecr_ovrd_0.pll_mode == 0       # PLL mode
assert dieObj.base.ringepll_top.fusecr_ovrd_0.pll_mode_ovrden == 0  # No override
assert dieObj.base.ringwpll_top.fusecr_ovrd_0.pll_mode == 0
# Inject workpoint via PEGA
ccf_pegaPstate(sktNum, cbbN, clrgv=target_ratio, chkstr='ccf_wp,ufs_status')
# Verify result
assert dieObj.base.tpmi.ufs_status.current_ratio == target_ratio
```

### PLL Crawling Override — Survivability Path
```python
# Enable override
dieObj.base.ringepll_top.fusecr_ovrd_0.pll_mode_ovrden.write(1)
dieObj.base.ringepll_top.fusecr_ovrd_0.pll_mode.write(1)  # FLL/crawl
dieObj.base.ringwpll_top.fusecr_ovrd_0.pll_mode_ovrden.write(1)
dieObj.base.ringwpll_top.fusecr_ovrd_0.pll_mode.write(1)
# GV sweep — each step limited by freq_crawl_delta_f
for r in range(r_min, r_max + 1):
    ccf_pegaPstate(sktNum, cbbN, clrgv=r, chkstr='ufs_status')
    # Verify step size <= freq_crawl_delta_f
# Restore default
dieObj.base.ringepll_top.fusecr_ovrd_0.pll_mode.write(0)
dieObj.base.ringepll_top.fusecr_ovrd_0.pll_mode_ovrden.write(0)
dieObj.base.ringwpll_top.fusecr_ovrd_0.pll_mode.write(0)
dieObj.base.ringwpll_top.fusecr_ovrd_0.pll_mode_ovrden.write(0)
```

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior |
|----------|-------------------|
| Boot default | `pll_mode=0`, `pll_mode_ovrden=0` on all CBBs. CCF_WP writable. |
| PEGA GV injection (PLL mode) | `ufs_status.current_ratio` follows injected ratio immediately (Fast GV). |
| PEGA GV injection (FLL/crawl mode) | `ufs_status.current_ratio` follows, but each step ≤ `freq_crawl_delta_f`. |
| C-state cycle (c1e) | `pll_mode` unchanged after exit. NonAutoGV persists. |
| Override assert + restore | Write `pll_mode_ovrden=1 + pll_mode=1`, verify readback. Restore to 0, verify. |
| Out-of-range GV request | CCF clamps to fused min (Pm) or fused max (P0). |

---

## Section 6: Corner Cases and Error Handling

- **No pll_mode_ovrden before writing pll_mode**: Write to `pll_mode` has no effect unless `pll_mode_ovrden=1`.
- **freq_crawl_delta_f = 0**: Treat as 1-unit step (guard in test script).
- **freq_crawl_disable = 1**: Crawl mode fuse-disabled — PLL crawl test should be skipped or expect no step constraint.
- **GV during C-state transition**: CCF_WP can only be updated while CCF is in NonAutoGV mode and awake.
- **Override not restored**: If test leaves `pll_mode=1`, subsequent Fast GV TC will fail (mode mismatch).

---

## Section 7: Test Scripts

| Script | CLI Flag | Function | Scope |
|--------|----------|----------|-------|
| `pm/Active_PM/CCF_GV/pmx_ccf_cbo.py` | `--test_ccf_fast_gv` | `cbb_ccf_fast_gv_default_test()` | POR validation — verifies default PLL mode on all CBBs |
| `pm/Active_PM/CCF_GV/pmx_ccf_cbo.py` | `--test_ccf_fast_gv_pll_crawling` | `cbb_ccf_fast_gv_pll_crawling_test()` | Survivability — override + sweep + crawl constraint + restore |

---

## Section 8: References

- [CBB CCF PM HAS — Fast GV / Drainless GV](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#switching-between-fast-gv-drainless-gv)
- [CBB CCF PM HAS — CCF GV (NonAutoGV)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [CBB PEGA Architecture](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html)
- [CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html)
- [PCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
