# CBB CCF Fast Ring C3

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422865](https://hsdes.intel.com/appstore/article-one/#/22022422865) |
| **Title** | CBB CCF Fast Ring C3 |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CCF PM States / Fast Ring C3 / Ring C3 |
| **Parent TCD** | [22022421177](https://hsdes.intel.com/appstore/article-one/#/22022421177) |
| **KB last updated** | 2026-07-08 |

---

## Test Case Intent

Verify CBB entry into Fast Ring C3 (during PkgC0) and Ring C3 (during PkgC6), and confirm the correct status of Ring PLL, Global CLK Gating, Core state, and D2D state for each.

**CCF PM States (from original description):**
- **Fast Ring C3** — quickly closes main Global drivers for the Uclk tree; fully controlled by CCF PMA; allowed during PkgC0; does NOT require PUnit involvement
- **Ring C3** — drives D2D into L1, drains CCF, shuts down Ring PLLs; prerequisite to PkgC6 entry

**Open resolved — enable/disable option:** YES. Fast C3 is controlled by register `ccf_pma_fast_c3_ctrl.fast_c3_en` (bit 32, RW, runtime writable). No dedicated BIOS knob — it is a PMA register configurable at runtime. The field `fast_c3_en` defaults to 1 (enabled). C-state enable and PkgCx BIOS knobs control whether cores enter C6sp/C6s/C6a to trigger Ring C3.

**Flow:**

1. **Fast Ring C3:** Set `fast_c3_en=1`. Inject core C-state (c1e/c6sp/c6s/c6a) via PEGA. Verify: `fast_c3_residency.counter` increments; `ring_pll_ratio != 0` (PLL stays ON during Fast C3); `resolved_cores_state` matches injected state
2. **Ring C3:** Set `fast_c3_en=1`. Inject PkgC6 (c6sp) via PEGA. Verify: `ring_pll_ratio == 0` (PLL gated during Ring C3); `resolved_cores_state=0x3` (C6)

**Test scripts:**
- Fast Ring C3: `pmx_ccf_cbo.py --test_ccf_fast_ring_c3` → `ccfu.ccf_fast_ring_c3_test(sktNum, 'cbbs')`
- Ring C3: `pmx_ccf_cbo.py --test_ccf_ring_c3` → `ccfu.ccf_ring_c3_test(sktNum)`

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; PCode and CCF PMA initialized |
| C-states enabled | `PackageCState` BIOS knob = C6 or Auto; C1E enabled |
| PkgCx enabled | BIOS knobs: `PackageCState`, `ProcessorC1eEnable` set to allow C6sp entry |
| PEGA available | `import diamondrapids.pm.pmutils.pega as pega` succeeds |
| `fast_c3_en` accessible | `cbb.base.ccf_pma.ccf_pmc_regs.ccf_pma_fast_c3_ctrl.fast_c3_en` writable |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Enable Fast C3: `cbb.base.ccf_pma.ccf_pmc_regs.ccf_pma_fast_c3_ctrl.fast_c3_en.write(1)` on all CBBs | Write succeeds; field reads back 1 | Write fails — PMA register inaccessible |
| 2 | **Fast Ring C3:** Read baseline `fast_c3_residency.counter`. Inject C-state via PEGA (randomly chosen from c1e/c6sp/c6s/c6a): `pega.pegaCstate(sktNum, dieName, domainDict={op:'all'})` | C-state injection accepted (PEGA returns 0) | PEGA C-state injection error |
| 3 | Verify Fast Ring C3 status: check `resolved_cores_state` matches injected state; `fast_c3_residency.counter` incremented; `ccf_pma_debug.ring_pll_ratio != 0` (Ring PLL remains active) | All 3 checks pass per CBB | `ring_pll_ratio=0` during Fast C3 — PLL incorrectly gated; or residency counter stuck |
| 4 | **Ring C3:** Inject PkgC6 (c6sp) via PEGA: `pega.pegaCstate(sktNum, dieName, domainDict={'c6sp':'all'})` | C-state injection accepted | PEGA error |
| 5 | Verify Ring C3 status: `resolved_cores_state=0x3` (C6); `resolved_cores_sub_state=0x0` (c6sp); `ccf_pma_debug.ring_pll_ratio == 0` (Ring PLL gated) | PLL gated; cores in C6 | `ring_pll_ratio != 0` — Ring PLL not shutting down for Ring C3; or wrong core state |

---

## Pass / Fail Criteria

**PASS:** Fast Ring C3 — cores enter target C-state; `fast_c3_residency.counter` increments; `ring_pll_ratio != 0` (PLL active). Ring C3 — cores in C6sp; `ring_pll_ratio == 0` (PLL gated). Both verified per CBB.

**FAIL:** Any C-state injection fails; `fast_c3_residency.counter` does not increment; `ring_pll_ratio` wrong for either state (active during Ring C3, or gated during Fast C3); `resolved_cores_state` does not match injected C-state.

---

## Post-Process

Save: `ccf_pma_fast_c3_ctrl`, `fast_c3_residency`, `ccf_pma_debug`, `ccp_status` register dumps per CBB for both Fast Ring C3 and Ring C3 scenarios.

---

## References

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#switching-between-fast-gv-drainless-gv)
- [CBB CCF Power Management HAS (CCF GV)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [CBB Power Event Generation Architecture (PEGA)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html)
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html)
- [pCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
