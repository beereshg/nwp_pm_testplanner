# Deep Analysis: [PSS]PCT - Default HP core selection

| Field | Value |
|-------|-------|
| **HSD ID** | [16030715686](https://hsdes.intel.com/appstore/article-one/#/16030715686) |
| **Title** | [PSS]PCT - Default HP core selection |
| **Segment** | PSS |
| **Target Program** | NWP (Newport) |
| **Feature** | PCT (Priority Core Turbo) |
| **Val Environment** | silicon,virtual_platform |
| **Parent TCD** | [22022420858 — PCT Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **FV Counterpart** | [22022422105 — PCT - Default HP core selection](https://hsdes.intel.com/appstore/article-one/#/22022422105) |

---

## Test Case Intent

**Objective:** Verify on PSS that the default HP core selection (first N modules per CBB, ordered, first core always HP) is correctly implemented by PCode from BIOS NVRAM.

**PSS Environment:** VP or HSLE — validates PCode NVRAM read and TPMI programming logic.

**Key distinction from FV:** This TC runs on a pre-silicon model (VP/HSLE). It finds firmware/RTL bugs before tape-out. FV confirms on real silicon. Not a duplicate.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| VP or HSLE environment | PSS environment booted with PCT enabled | Neither VP nor HSLE available |
| PctHpModuleCount > 0 | NVRAM `PctHpModuleCount` set to valid value (multiple of 4) | PCT disabled — no HP selection to verify |
| pct_focus.py available | `import pct_focus as pctd` succeeds | Module path not set up |
| Both CBBs active | cbb0 and cbb1 accessible in namednodes | Only one CBB active |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read `PctHpModuleCount` from NVRAM | Valid value > 0 and multiple of 4 | Value is 0 or non-multiple — pre-condition failure |
| 2 | Run `pctd.generate_core_list()` to populate HP_CORES and LP_CORES | HP_CORES non-empty; total = HP_CORES + LP_CORES = 96 cores (2 CBBs × 48) | HP_CORES empty — PCT not active on PSS |
| 3 | Verify first core (cbb0, compute0, module0, core0) is in HP_CORES | `first_core in pctd.HP_CORES` is True | First core is LP — PCode CLOS ordering bug on VP model |
| 4 | Verify HP module count matches NVRAM value | `len(pctd.HP_CORES) // cores_per_module == PctHpModuleCount` | Count mismatch — NVRAM read failing on VP or CLOS assignment wrong |
| 5 | Verify HP modules are the first N consecutive modules per CBB (ordered selection) | First N modules per CBB have CLOS_ID=0 or 1 (HP); remaining have CLOS_ID=2 or 3 (LP) | Non-consecutive HP selection — PCode selection algorithm bug |

### Pass / Fail Criteria

**PASS:** First core is HP; HP module count matches BIOS NVRAM; CLOS assignments are consecutive from module 0 on both CBBs.

**FAIL:** First core is LP on PSS → PCode CLOS assignment ordering bug on model (check VP TPMI model fidelity). HP count mismatch → NVRAM read failing on VP.

### Post-Process

Save: NVRAM HP count, per-module CLOS assignments on both CBBs, HP_CORES and LP_CORES lists, first core assertion result.

### Reference Documents

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — PCT CLOS model, HP/LP core assignment, Ordered Throttling
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_CONTROL, SST_CLOS_ASSOC, SST_TF_INFO registers
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT TPMI register definitions
- [NWP HAS PM](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) — PCT feature list and NWP applicability
- [PCT KB — pct.md](../../../pm_features/sst/pct.md) — KB architecture, CLOS model, NWP-specific deltas

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

[PSS]PCT - Default HP core selection is a PSS pre-silicon test. NWP PSS environment (VP/HSLE) supports PCT TPMI register access via namednodes. Firmware behavior validated before tape-out.

Tags: `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Topology Notes

- NWP: **2 CBBs** (cbb0 + cbb1), 48 cores per CBB = 96 total cores
- Root PM path: `sv.socket0.nio.punit.*` (not `sv.socket0.cbb0.punit.*`)
- **CAPID4.bit29** on NWP: fuse gate for PCT capability (must = 1)
- Legacy MSR 0x610/0x611/0x606: **deprecated on NWP** — use TPMI only
- Always iterate **both CBBs** when checking CLOS/SST registers

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Verify CAPID4.bit29=1 | `sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29.read()` |
| 2 | Check both CBBs | `for cbb in sv.sockets.cbbs: cbb.base.tpmi.sst_cp_control.sst_cp_enable.read()` |
| 3 | Run PSS-adapted test | See Test Steps section above |

### Pass Criteria

First core is HP; HP module count matches BIOS NVRAM; CLOS assignments are consecutive from module 0 on both CBBs.
