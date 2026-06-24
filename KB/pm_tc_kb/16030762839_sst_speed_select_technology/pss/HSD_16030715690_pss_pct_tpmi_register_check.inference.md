# Deep Analysis: [PSS]PCT - TPMI register check (FlexconPM)

| Field | Value |
|-------|-------|
| **HSD ID** | [16030715690](https://hsdes.intel.com/appstore/article-one/#/16030715690) |
| **Title** | [PSS]PCT - TPMI register check (FlexconPM) |
| **Segment** | PSS |
| **Target Program** | NWP (Newport) |
| **Feature** | PCT (Priority Core Turbo) |
| **Val Environment** | silicon,virtual_platform |
| **Parent TCD** | [22022420858 — PCT Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **FV Counterpart** | [22022422103 — PCT - TPMI register check](https://hsdes.intel.com/appstore/article-one/#/22022422103) |

---

## Test Case Intent

**Objective:** Verify TPMI SST_CLOS registers reflect correct HP/LP assignment on PSS via FlexconPM. Uses FlexconPM automated register check on VP/HSLE.

**PSS Environment:** VP or HSLE — FlexconPM reads TPMI registers via PythonSV/namednodes on model.

**Key distinction from FV:** This TC runs on a pre-silicon model (VP/HSLE). It finds firmware/RTL bugs before tape-out. FV confirms on real silicon. Not a duplicate.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| VP or HSLE environment | PSS booted with PCT enabled | Environment not booted |
| FlexconPM available | `import pysvext.diamondrapids_flexcon.plugins.flexcon_pm as fpm` succeeds | FlexconPM not installed |
| PCT enabled at boot | SST_CP_ENABLE=1; PctHpModuleCount > 0 in NVRAM | PCT not enabled — FlexconPM will fail correctly but test is invalid |
| Both CBBs accessible | cbb0 and cbb1 accessible via sv.sockets.cbbs | Only one CBB active |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Run FlexconPM automated TPMI check: `result = fpm.run()` | fpm.run() returns 0 (all TPMI register checks pass) | Non-zero → TPMI model has wrong register encoding (VP model gap) |
| 2 | Manually verify SST_CP_CONTROL fields on both CBBs: `sst_cp_enable=1` and `sst_cp_priority_type=1` | Both CBBs: enable=1, priority_type=1 (Ordered Throttling) | Wrong values → PCode PSS firmware bug in CLOS programming logic |
| 3 | Run `pctd.generate_core_list()` and verify HP/LP split matches NVRAM | HP count matches `PctHpModuleCount × cores_per_module` | Mismatch → CLOS assignments not reflected in namednodes on VP |
| 4 | Verify `SST_CP_STATUS` HP mask on both CBBs is non-zero and consistent with CLOS assignments | HP mask bits set for HP modules; LP mask bits clear for LP modules | HP mask empty → PCode not propagating SST_CP_STATUS on VP |

### Pass / Fail Criteria

**PASS:** flexcon_pm exits 0 on PSS; CLOS assignments correct in TPMI model; SST_CP_CONTROL and SST_CP_STATUS valid.

**FAIL:** flexcon_pm fails on PSS → TPMI model has wrong register encoding (VP model gap). CLOS wrong → PCode PSS firmware bug in CLOS programming logic.

### Post-Process

Save: FlexconPM result, SST_CP_CONTROL fields, SST_CP_STATUS HP mask, CLOS assignments per module.

### Reference Documents

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — PCT CLOS model, HP/LP core assignment, Ordered Throttling
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_CONTROL, SST_CLOS_ASSOC, SST_TF_INFO registers
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT TPMI register definitions
- [NWP HAS PM](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) — PCT feature list and NWP applicability
- [PCT KB — pct.md](../../../pm_features/sst/pct.md) — KB architecture, CLOS model, NWP-specific deltas

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

[PSS]PCT - TPMI register check (FlexconPM) is a PSS pre-silicon test. NWP PSS environment (VP/HSLE) supports PCT TPMI register access via namednodes. Firmware behavior validated before tape-out.

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

flexcon_pm exits 0 on PSS; CLOS assignments correct in TPMI model; SST_CP_CONTROL and SST_CP_STATUS valid.
