# Deep Analysis: [PSS]PCT - Default Disabled

| Field | Value |
|-------|-------|
| **HSD ID** | [16030715684](https://hsdes.intel.com/appstore/article-one/#/16030715684) |
| **Title** | [PSS]PCT - Default Disabled |
| **Segment** | PSS |
| **Target Program** | NWP (Newport) |
| **Feature** | PCT (Priority Core Turbo) |
| **Val Environment** | silicon,virtual_platform |
| **Parent TCD** | [22022420858 — PCT Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **FV Counterpart** | [16030768619 — PCT - Default Enabled](https://hsdes.intel.com/appstore/article-one/#/16030768619) |

---

## Test Case Intent

**Objective:** Verify that PCT is disabled by default when PctHpModuleCount=0 or BIOS PCT knob=Disabled. When PCT is disabled: SST_CP_ENABLE=0; all cores get the same TRL (no HP/LP differentiation).

**PSS Environment:** VP (Simics) — validates PCode default-disabled handling before silicon.

**Key distinction from FV:** This TC runs on a pre-silicon model (VP/HSLE). It finds firmware/RTL bugs before tape-out. FV confirms on real silicon. Not a duplicate.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| VP (Simics) environment | VP booted with PctHpModuleCount=0 or BIOS knob set to Disabled | HP count > 0 — test pre-condition not met |
| CAPID4.bit29 = 1 | Fuse set so PCT is capable but opt-in via BIOS knob only | Fuse not set — PCT never capable |
| xmlcli available | `from pysvtools.xmlcli import nvram` succeeds | xmlcli not installed |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read `PctHpModuleCount` from NVRAM; confirm it is 0 | PctHpModuleCount=0 (PCT disabled by default on NWP) | HP count > 0 — not default-disabled state |
| 2 | Verify `SST_CP_ENABLE=0` on both CBBs | `sst_cp_control.sst_cp_enable=0` on cbb0 and cbb1 | SST_CP_ENABLE=1 despite HP count=0 — PCode ignores NVRAM value |
| 3 | Run `pctd.generate_core_list()` and verify no HP cores assigned | HP_CORES is empty; all cores are LP | HP cores present when PCT disabled — CLOS assignment bug |
| 4 | Verify all cores get same TRL (no HP/LP frequency differentiation) | `sst_tf_info_2.ratio_0` == `sst_tf_info_2.ratio_1` on both CBBs, or LP TRL applied uniformly | HP TRL applied — PCode not clearing CLOS differentiation on disable |

### Pass / Fail Criteria

**PASS:** SST_CP_ENABLE=0 when PctHpModuleCount=0; no HP core set; all cores get same TRL (no differentiation).

**FAIL:** SST_CP_ENABLE=1 despite HP count=0 → PCode ignores NVRAM value; check PCode boot init sequence.

### Post-Process

Save: NVRAM snapshot, SST_CP_CONTROL/STATUS on both CBBs, CLOS assignments, TRL ratio values.

### Reference Documents

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — PCT CLOS model, HP/LP core assignment, Ordered Throttling
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_CONTROL, SST_CLOS_ASSOC, SST_TF_INFO registers
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT TPMI register definitions
- [NWP HAS PM](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) — PCT feature list and NWP applicability
- [PCT KB — pct.md](../../../pm_features/sst/pct.md) — KB architecture, CLOS model, NWP-specific deltas

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

[PSS]PCT - Default Disabled is a PSS pre-silicon test. NWP PSS environment (VP/HSLE) supports PCT TPMI register access via namednodes. Firmware behavior validated before tape-out.

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

SST_CP_ENABLE=0 when PctHpModuleCount=0; no HP core set; all cores get same TRL (no differentiation).
