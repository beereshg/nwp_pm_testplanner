# Deep Analysis: [PSS]PCT - BIOS Menu

| Field | Value |
|-------|-------|
| **HSD ID** | [16030715678](https://hsdes.intel.com/appstore/article-one/#/16030715678) |
| **Title** | [PSS]PCT - BIOS Menu |
| **Segment** | PSS |
| **Target Program** | NWP (Newport) |
| **Feature** | PCT (Priority Core Turbo) |
| **Val Environment** | silicon,virtual_platform |
| **Parent TCD** | [22022420858 — PCT Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **FV Counterpart** | [22022422103 — PCT - TPMI register check](https://hsdes.intel.com/appstore/article-one/#/22022422103) |

---

## Test Case Intent

**Objective:** Verify BIOS correctly enables/disables PCT via BIOS setup knobs and that NVRAM values are pushed and reflected in TPMI after boot.

**PSS Environment:** VP (Simics) — validates BIOS flow and PCode NVRAM read at boot.

**Key distinction from FV:** This TC runs on a pre-silicon model (VP/HSLE). It finds firmware/RTL bugs before tape-out. FV confirms on real silicon. Not a duplicate.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| VP (Simics) environment | VP booted with BIOS image supporting PCT knobs | HSLE not suitable for BIOS flow test |
| CAPID4.bit29 = 1 | `sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29` reads 1 | PCT fuse not set in VP model |
| xmlcli / pysvtools available | `from pysvtools.xmlcli import nvram` succeeds | xmlcli not installed |
| PCT capable in BIOS | `PctCapableSystem` NVRAM knob exposed | BIOS does not expose PCT knobs |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read NVRAM and verify PCT knobs are exposed: `PctCapableSystem` and `PctHpModuleCount` | Both knobs present and readable; PctCapableSystem=1, PctHpModuleCount>0 | Knobs not present — BIOS does not expose PCT on VP |
| 2 | Change HP count via `pctd.pct_bios_knob_change(cores=4)` and trigger reboot | NVRAM updated to cores=4 before reboot | BIOS push failed — check xmlcli push path |
| 3 | After reboot: read `PctHpModuleCount` again | Value reflects the new setting (4) | Value not updated — PCode not reading NVRAM at boot |
| 4 | Run `pctd.generate_core_list()` and verify HP count matches NVRAM | HP_CORES count = PctHpModuleCount × cores_per_module | Mismatch — PCode CLOS programming does not reflect NVRAM value |
| 5 | Disable PCT via BIOS knob (set HP count=0) and reboot; verify `SST_CP_ENABLE=0` | SST_CP_ENABLE=0 on both CBBs after disable | SST_CP_ENABLE still 1 — PCode ignores disabled state |

### Pass / Fail Criteria

**PASS:** BIOS knob change accepted; NVRAM reflects new value; TPMI SST_CP_ENABLE and CLOS assignments updated after reboot.

**FAIL:** NVRAM not updated → BIOS push failed (xmlcli). TPMI not updated after reboot → PCode not reading NVRAM at boot.

### Post-Process

Save: NVRAM snapshot before/after, SST_CP_CONTROL/STATUS register values, TPMI CLOS assignments, boot log.

### Reference Documents

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — PCT CLOS model, HP/LP core assignment, Ordered Throttling
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_CONTROL, SST_CLOS_ASSOC, SST_TF_INFO registers
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT TPMI register definitions
- [NWP HAS PM](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) — PCT feature list and NWP applicability
- [PCT KB — pct.md](../../../pm_features/sst/pct.md) — KB architecture, CLOS model, NWP-specific deltas

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

[PSS]PCT - BIOS Menu is a PSS pre-silicon test. NWP PSS environment (VP/HSLE) supports PCT TPMI register access via namednodes. Firmware behavior validated before tape-out.

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

BIOS knob change accepted; NVRAM reflects new value; TPMI SST_CP_ENABLE and CLOS assignments updated after reboot.
