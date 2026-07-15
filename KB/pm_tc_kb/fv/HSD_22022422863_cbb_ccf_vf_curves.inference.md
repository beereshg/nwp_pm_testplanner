# CBB CCF VF Curves

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422863](https://hsdes.intel.com/appstore/article-one/#/22022422863) |
| **Title** | CBB CCF VF Curves |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Fabric DVFS / CBB CCF GV / VF Curves |
| **Parent TCD** | [22022421174](https://hsdes.intel.com/appstore/article-one/#/22022421174) |
| **KB last updated** | 2026-07-08 |

---

## Test Case Intent

Verify that PCode correctly loads and applies the CBB CCF ring VF (Voltage-Frequency) curve fuse data. For each VF point in the fused curve, inject the corresponding ring ratio via PEGA and verify the observed voltage from `UFS_STATUS.CURRENT_VOLTAGE` matches the PCode-expected voltage within tolerance (50mV).

**Opens resolved:**

- **Where are the fuses defined?** — Ring VF curve fuse values are loaded by PCode into `cbb.pcode.vars.ring.vf_curve.at{N}.points.ats.{ratio, voltage}` during boot. The source fuses are part of the CBB fuse array (read at reset). Fuse override tool can substitute alternate values.
- **Which is the fuse format?** — Expected voltage: `float` (converted via `tools.convert.bin2float(val, "float")`). Observed voltage: `U3.13` fixed-point from `UFS_STATUS.CURRENT_VOLTAGE`.
- **How many VF points for ring?** — **6 VF points** per slice (`VF_TABLE_CFC_POINTS_COUNT = 6`). Multiple slices (`vf_curve.ats`) per CBB.

**Flow:**

- Ensure all ratio points in each CBB CCF VF curve are accessible via PCode vars (`pcode.vars.ring.vf_curve`)
- Inject each VF curve ratio via PEGA (`ccf_pegaPstate` with `clrgv=ratio`) and observe voltage
- Match PCode interpretation: observed voltage must be within 50mV of fused VF point voltage
- Verify per-CBB: each CBB has independent VF curves (cbb0, cbb1)

**Test script:** `pmx_ccf_cbo.py --test_ccf_vf_curve` → `ccfu.cbb_ccf_vf_curve_test(sktNum, dieName='ats', sliceName='ats')`.

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; PCode initialized with VF curve fuse data |
| VF curve data accessible | `sv.sockets.cbbs.pcode.vars.ring.vf_curve` readable and non-zero |
| TPMI `UFS_STATUS.CURRENT_VOLTAGE` readable | `cbb.base.tpmi.ufs_status.current_voltage` returns valid U3.13 value |
| PEGA available | `import diamondrapids.pm.pmutils.pega as pega` succeeds |
| Python-SV available | `import namednodes; sv = namednodes.sv` succeeds |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read VF curve data per CBB: iterate `cbb.pcode.vars.ring.vf_curve.ats`; print each point's `ratio.value_` and `voltage.val` | 6 valid VF points per slice; ratios non-zero and ascending; voltages in valid range | Zero ratios or zero voltages — fuse data not loaded by PCode |
| 2 | For each VF point ratio, inject ratio via PEGA: `ccf_pegaPstate(sktNum, dieName, clrgv=ratio_value)`. Verify `UFS_STATUS.CURRENT_RATIO` matches | Current ratio tracks injected value per CBB | Ratio not reached — PEGA not driving CCF |
| 3 | Read observed voltage from TPMI: `tools.convert.bin2float(cbb.base.tpmi.ufs_status.current_voltage, "U3.13")`. Compare to expected: `tools.convert.bin2float(point.voltage.val, "float")` | Observed voltage within 50mV of fused VF curve expected voltage for all 6 points per slice | Voltage deviation > 50mV — VF curve mismatch between fuses and silicon |
| 4 | Repeat for all slices (`cbb.pcode.vars.ring.vf_curve.ats`) and all CBBs | All slices and CBBs pass voltage verification | Any slice or CBB failing — VF curve asymmetry |
| 5 | Optional: use fuse override tool to inject a modified VF curve; reboot; re-verify voltage tracking | Modified VF point voltages observed at correct ratios | Override not applied — fuse override path broken |

---

## Pass / Fail Criteria

**PASS:** All VF curve ratio points in each CBB CCF accessible via PCode vars. For each injected ratio, observed `UFS_STATUS.CURRENT_VOLTAGE` within 50mV of fused VF curve expected voltage. PCode interpretation matches fuse data per-CBB.

**FAIL:** VF curve data not loaded (zero ratio or voltage); observed voltage deviates > 50mV from expected; PEGA ratio injection fails; any CBB shows different VF curve than fuses specify.

---

## Post-Process

Save: VF curve point dump per CBB (`pcode.vars.ring.vf_curve.ats`), observed voltage samples per ratio point, pass/fail summary per slice.

---

## References

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [CBB CCP PM Integration HAS — VF Curves Grouping](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCP%20HAS/cbb_cpp_has.html#vf-curves-grouping)
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html)
- [Architectural UFS TPMI Interface](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html#dmr-family)
- [CBB Power Event Generation Architecture (PEGA)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html)
- [pCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
