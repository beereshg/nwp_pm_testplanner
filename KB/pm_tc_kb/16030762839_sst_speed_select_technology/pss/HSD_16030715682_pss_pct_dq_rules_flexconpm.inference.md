# Deep Analysis: [PSS]PCT - DQ Rules (FlexconPM)

| Field | Value |
|-------|-------|
| **HSD ID** | [16030715682](https://hsdes.intel.com/appstore/article-one/#/16030715682) |
| **Title** | [PSS]PCT - DQ Rules (FlexconPM) |
| **Segment** | PSS |
| **Target Program** | NWP (Newport) |
| **Feature** | PCT (Priority Core Turbo) |
| **Val Environment** | silicon,virtual_platform |
| **Parent TCD** | [22022420858 — PCT Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **FV Counterpart** | [22022422118 — PCT - DQ Rules (FlexconPM)](https://hsdes.intel.com/appstore/article-one/#/22022422118) |

---

## Test Case Intent

**Objective:** Verify PCT fuse-to-TPMI propagation and DQ rule execution on PSS (VP/HSLE) via FlexconPM. FlexconPM runs DQ (Decision Queue) rule checks post-boot. On PSS: validates PCode correctly reads fuse values and programs TPMI.

**PSS Environment:** VP (Simics) or HSLE — FlexconPM is the automated checker.

**Key distinction from FV:** This TC runs on a pre-silicon model (VP/HSLE). It finds firmware/RTL bugs before tape-out. FV confirms on real silicon. Not a duplicate.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| VP or HSLE environment | PSS booted with PCT-capable fuse set | Environment not booted |
| FlexconPM available | `import pysvext.diamondrapids_flexcon.plugins.flexcon_pm as fpm` succeeds | FlexconPM not installed on PSS env |
| PCT-capable fuses set in VP model | SST_TF fuses present in VP model configuration | VP model lacks SST-TF fuse modeling — gap ticket needed |
| pct_focus.py available | `import pct_focus as pctd` succeeds | Module path not set up |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Run FlexconPM DQ check: `result = fpm.run()` | fpm.run() returns 0 (all DQ rules pass) | Non-zero return — DQ rule violation detected on PSS model |
| 2 | Read `PctHpModuleCount` from NVRAM | Value > 0 and multiple of 4 | Value 0 — PCT disabled state, wrong test configuration |
| 3 | Run `pctd.generate_core_list()` and verify HP cores present | HP_CORES non-empty; matches expected HP count from NVRAM | No HP cores — PCode did not read NVRAM knob on VP |
| 4 | Verify fuse values reflected in `SST_TF_INFO_0/1/2` TPMI registers | LP_CLIP_RATIO, NUM_CORE, and RATIO fields populated from fuses (non-zero) | Zero values — PCode Phase 5 fuse propagation not modeled on VP |

### Pass / Fail Criteria

**PASS:** flexcon_pm exits 0; fuse-derived HP set matches TPMI; DQ rule events in model trace.

**FAIL:** flexcon_pm fails → PCode DQ rule did not execute on VP; check VP model implements DQ event dispatch. HP set empty → PCode did not read NVRAM knob on VP.

### Post-Process

Save: FlexconPM result code and trace, TPMI SST_TF_INFO_0/1/2 values, HP_CORES list, fuse readback values.

### Reference Documents

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — PCT CLOS model, HP/LP core assignment, Ordered Throttling
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_CONTROL, SST_CLOS_ASSOC, SST_TF_INFO registers
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT TPMI register definitions
- [NWP HAS PM](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) — PCT feature list and NWP applicability
- [PCT KB — pct.md](../../../pm_features/sst/pct.md) — KB architecture, CLOS model, NWP-specific deltas

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

[PSS]PCT - DQ Rules (FlexconPM) is a PSS pre-silicon test. NWP PSS environment (VP/HSLE) supports PCT TPMI register access via namednodes. Firmware behavior validated before tape-out.

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

flexcon_pm exits 0; fuse-derived HP set matches TPMI; DQ rule events in model trace.
