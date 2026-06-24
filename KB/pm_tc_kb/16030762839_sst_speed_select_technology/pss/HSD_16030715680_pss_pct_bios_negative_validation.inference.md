# Deep Analysis: [PSS]PCT - BIOS Negative Validation

| Field | Value |
|-------|-------|
| **HSD ID** | [16030715680](https://hsdes.intel.com/appstore/article-one/#/16030715680) |
| **Title** | [PSS]PCT - BIOS Negative Validation |
| **Segment** | PSS |
| **Target Program** | NWP (Newport) |
| **Feature** | PCT (Priority Core Turbo) |
| **Val Environment** | silicon,virtual_platform |
| **Parent TCD** | [22022420858 — PCT Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **FV Counterpart** | [16030768621 — PCT - TPMI runtime negative validation](https://hsdes.intel.com/appstore/article-one/#/16030768621) |

---

## Test Case Intent

**Objective:** Verify that BIOS correctly rejects invalid PCT BIOS knob values (non-multiple of 4, out-of-range) and that invalid values are not pushed to NVRAM or TPMI.

**PSS Environment:** VP (Simics) — safe to inject invalid BIOS values without risking silicon damage.

**Key distinction from FV:** This TC runs on a pre-silicon model (VP/HSLE). It finds firmware/RTL bugs before tape-out. FV confirms on real silicon. Not a duplicate.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| VP (Simics) environment | VP booted with BIOS image supporting PCT knobs | HSLE not suitable for negative BIOS test |
| PCT enabled baseline | Valid HP count in NVRAM (e.g. 8) before negative tests | No baseline value to compare against |
| xmlcli available | `from pysvtools.xmlcli import nvram` succeeds | xmlcli not installed |
| pct_focus.py available | `import pct_focus as pctd` succeeds | Module path not set up |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Attempt to set non-multiple of 4: `pctd.pct_bios_knob_change(cores=3)` | Function prints rejection message; NVRAM not updated | Value accepted — validation logic missing |
| 2 | Attempt to set value exceeding MAX_MODULES_PER_CBB: `pctd.pct_bios_knob_change(cores=0x24)` | Function rejects; NVRAM retains previous valid value | Value accepted — out-of-range not checked |
| 3 | Read `PctHpModuleCount` from NVRAM and verify it is still a valid multiple of 4 ≤ 0x20 | `val % 4 == 0 and val <= 0x20` is True | NVRAM corrupted with invalid value — PCode receives bad HP count |
| 4 | Attempt to set cores=0 (disable path); verify behavior is deterministic | Either accepted cleanly as disabled state or rejected per policy; no crash | Exception or model crash on cores=0 |

### Pass / Fail Criteria

**PASS:** Invalid BIOS values rejected; NVRAM retains last valid value; no model assertion or crash on invalid input.

**FAIL:** Invalid value accepted into NVRAM → pct_bios_knob_change validation not working; PCode receives corrupt HP count.

### Post-Process

Save: NVRAM snapshot before/after each injection, rejection log output, final NVRAM PctHpModuleCount value.

### Reference Documents

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — PCT CLOS model, HP/LP core assignment, Ordered Throttling
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_CONTROL, SST_CLOS_ASSOC, SST_TF_INFO registers
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT TPMI register definitions
- [NWP HAS PM](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) — PCT feature list and NWP applicability
- [PCT KB — pct.md](../../../pm_features/sst/pct.md) — KB architecture, CLOS model, NWP-specific deltas

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

[PSS]PCT - BIOS Negative Validation is a PSS pre-silicon test. NWP PSS environment (VP/HSLE) supports PCT TPMI register access via namednodes. Firmware behavior validated before tape-out.

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

Invalid BIOS values rejected; NVRAM retains last valid value; no model assertion or crash on invalid input.
