# TC Deep Analysis: CBB CCF Fast Ring C3

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422865 |
| **Title** | CBB CCF Fast Ring C3 |
| **Date** | 2026-07-15 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | CBB CCF PM Idle Scenario |
| **Sub-Feature** | Fast Ring C3 entry/exit in PKGC0 |
| **Parent TCD** | [22022421179 — CBB CCF PM Idle Scenario](https://hsdes.intel.com/appstore/article-one/#/22022421179) |

---

## Test Case Intent

Verify that CBB CCF autonomously enters Fast Ring C3 in **PKGC0** when Fast Ring C3 is enabled and cores are driven into qualifying idle conditions. Confirm Fast Ring C3 residency increments, Ring PLL remains ON, and resolved core/D2D status match Fast Ring C3 expectations. This test excludes PKGC6 / Ring C3 validation, which is not applicable to NWP (PkgC6 fuse-disabled).

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| System booted to OS | BIOS CPL4 complete; PCode and CCF PMA initialized |
| PKGC-disabled product assumption | NWP: PkgC6 fuse-disabled; test targets PKGC0 behavior only |
| Core idle states enabled | BIOS allows core low-power idle states needed to create Fast Ring C3 opportunity |
| PEGA available | `import diamondrapids.pm.pmutils.pega as pega` succeeds |
| PythonSV available | `import namednodes; sv = namednodes.sv` succeeds |
| `fast_c3_en` accessible | `cbb.base.ccf_pma.ccf_pmc_regs.ccf_pma_fast_c3_ctrl.fast_c3_en` writable/readable |
| Fast Ring C3 not fuse-disabled | Platform fuse allows Fast Ring C3 enablement |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Enable Fast Ring C3 on each CBB: write `fast_c3_en = 1` in `ccf_pma_fast_c3_ctrl` and read back | Write succeeds; field reads back `1` on all CBBs | Register inaccessible, write rejected, or readback != 1 |
| 2 | Capture baseline: `fast_c3_residency.counter`, `ccf_pma_debug.ring_pll_ratio`, core-state, D2D/link-status | Baseline captured successfully for all CBBs | Status/register access failure |
| 3 | Create Fast Ring C3 opportunity: drive cores into idle/low-power (PEGA C-state stimulus that does NOT imply PKGC6) | Stimulus accepted; system remains in PKGC0 | Stimulus fails or attempts unsupported PkgC-state |
| 4 | Observe Fast Ring C3 entry: verify `fast_c3_residency.counter` increments | Residency counter increments — Fast Ring C3 reached | Counter not incrementing — Fast Ring C3 not entered |
| 5 | Verify Ring PLL state: `ccf_pma_debug.ring_pll_ratio != 0` | Ring PLL remains active (ON) during Fast Ring C3 | `ring_pll_ratio == 0` — incorrect ring-off for Fast Ring C3 |
| 6 | Verify core-state is compatible with Fast Ring C3 (cores in C1/C6 idle, not package-C6) | Core-state consistent with Fast Ring C3 entry | Core-state inconsistent with expected idle condition |
| 7 | Verify D2D/link state consistent with Fast Ring C3 (L0/L1 allowed, not forced ring-off) | D2D/link matches Fast Ring C3 expectation | D2D/link inconsistent |
| 8 | Remove idle stimulus / wake cores; verify clean exit | Residency stops incrementing; ring PLL valid; active behavior restored | Stuck in Fast Ring C3 or bad wake behavior |

---

### Pass / Fail Criteria

- **PASS**: Fast Ring C3 entered (residency counter increments); Ring PLL remains ON; core-state and D2D/link state consistent with Fast Ring C3 definition; clean exit on wake. All CBBs pass independently.
- **FAIL**: Fast Ring C3 not entered despite qualifying conditions; Ring PLL incorrectly off (`ring_pll_ratio == 0`); core/D2D state mismatch; stuck in Fast Ring C3 after wake; any CBB fails.

---

### Post-Process

Save per CBB: `fast_c3_residency.counter` (before/after), `ring_pll_ratio`, core-state dump, D2D link-state dump, pass/fail summary.

---

### References

- [CBB CCF Power Management HAS — Fast Ring C3](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html)
- [CBB C-States HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBBCstates/CBBC.html)
- [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [TCD 22022421179 — CBB CCF PM Idle Scenario](https://hsdes.intel.com/appstore/article-one/#/22022421179)
- [TC 22022422873 — CBB CCF Ring C3 (ZBB on NWP)](https://hsdes.intel.com/appstore/article-one/#/22022422873)
