# Deep Analysis: [PSS]PCT - enable/disable

| Field | Value |
|-------|-------|
| **HSD ID** | [16030715694](https://hsdes.intel.com/appstore/article-one/#/16030715694) |
| **Title** | [PSS]PCT - enable/disable |
| **Segment** | PSS |
| **Target Program** | NWP (Newport) |
| **Feature** | PCT (Priority Core Turbo) |
| **Val Environment** | silicon,virtual_platform |
| **Parent TCD** | [22022420858 — PCT Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **FV Counterpart** | [16030768620 — PCT - TPMI runtime enable/disable](https://hsdes.intel.com/appstore/article-one/#/16030768620) |

---

## Test Case Intent

**Objective:** Verify PCT can be enabled and disabled at runtime on PSS via TPMI SST_CP_CONTROL. Validates PCode response to runtime PCT toggle on the PSS model.

**PSS Environment:** VP or HSLE — validates PCode state machine for PCT enable/disable event handling.

**Key distinction from FV:** This TC runs on a pre-silicon model (VP/HSLE). It finds firmware/RTL bugs before tape-out. FV confirms on real silicon. Not a duplicate.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| PCT enabled at boot | SST_CP_ENABLE=1 on both CBBs; HP_CORES non-empty | PCT not initially enabled — toggle test requires enabled baseline |
| VP or HSLE environment | PSS model running and accessible via PythonSV | No PSS environment available |
| pct_focus.py available | `import pct_focus as pctd` succeeds | Module path not set up |
| Both CBBs accessible | cbb0 and cbb1 reachable via sv.sockets.cbbs | Only one CBB — topology mismatch |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Run `pctd.generate_core_list()` and verify HP_CORES non-empty (PCT active baseline) | HP_CORES > 0; SST_CP_ENABLE=1 on both CBBs | HP_CORES empty — PCT not enabled at start |
| 2 | Disable PCT: set `sst_cp_control.sst_cp_enable=0` on both CBBs | Write accepted; SST_CP_ENABLE reads back 0 on both CBBs | Write ignored — TPMI write not modeled on VP |
| 3 | Run `pctd.generate_core_list()` again and verify no HP cores | HP_CORES empty after disable; all cores treated as LP | HP cores still present — PCode not responding to TPMI toggle on PSS |
| 4 | Re-enable: set `sst_cp_control.sst_cp_enable=1` on both CBBs | Write accepted; SST_CP_ENABLE reads back 1 | Write ignored — re-enable path not modeled |
| 5 | Run `pctd.generate_core_list()` and verify HP cores restored | HP_CORES non-empty; matches original count | HP set not restored → PCode state machine bug on re-enable path |

### Pass / Fail Criteria

**PASS:** PCT toggle works on PSS; HP set disappears on disable; restored on re-enable; no model crash or exception.

**FAIL:** Toggle ignored → PCode PSS model not handling TPMI write interrupt correctly. HP set not restored → PCode state machine bug on re-enable path.

### Post-Process

Save: SST_CP_CONTROL before/after each toggle, HP_CORES counts, NLOG events, any model exceptions.

### Reference Documents

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — PCT CLOS model, HP/LP core assignment, Ordered Throttling
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_CONTROL, SST_CLOS_ASSOC, SST_TF_INFO registers
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT TPMI register definitions
- [NWP HAS PM](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) — PCT feature list and NWP applicability
- [PCT KB — pct.md](../../../pm_features/sst/pct.md) — KB architecture, CLOS model, NWP-specific deltas

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

[PSS]PCT - enable/disable is a PSS pre-silicon test. NWP PSS environment (VP/HSLE) supports PCT TPMI register access via namednodes. Firmware behavior validated before tape-out.

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

PCT toggle works on PSS; HP set disappears on disable; restored on re-enable; no model crash or exception.
