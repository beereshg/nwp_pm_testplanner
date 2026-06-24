import pathlib, textwrap

BASE = pathlib.Path(r'C:\github\nwp_testplan\KB\pm_tc_kb\16030762839_sst_speed_select_technology\pss')

TCS = {
"16030715676": {
  "title": "[PSS]PCT - All HP cores in C6",
  "slug": "pss_pct_all_hp_cores_in_c6",
  "fv_id": "22022422104", "fv_title": "PCT - All HP cores in C6",
  "env": "HSLE XOS preferred (both IMH and CBB RTL active for cross-die validation). VP cannot model Acode C6 entry accurately.",
  "objective": "Verify PCT behavior when all HP cores are in C6 on HSLE XOS. Validates that cross-die HPM protocol correctly handles the HP-idle state; MC6 entry proceeds without PCT-related blocking.",
  "preconditions": [
    ("PCT enabled", "SST_CP_ENABLE=1 on both CBBs", "PCT not active"),
    ("HSLE XOS environment", "IMH and CBB RTL both running (XOS)", "VP only — C6 model gap"),
    ("HP cores identified", "pctd.generate_core_list() returns HP_CORES non-empty", "No HP cores — check BIOS knob"),
    ("LP-only workload available", "Workload can be pinned to LP cores", "Cannot isolate HP core idle"),
  ],
  "steps": [
    ("1", "Generate HP/LP core lists via `pctd.generate_core_list()`", "HP_CORES and LP_CORES populated for both CBBs", "Empty HP_CORES — PCT not enabled"),
    ("2", "Pin sustained workload to LP cores; ensure HP cores remain idle", "HP cores enter C6 on HSLE; no workload activity on HP threads", "HP cores stuck at C0 — pin failed"),
    ("3", "Monitor `SST_CP_STATUS` on both CBBs during HP-idle window", "HP mask in SST_CP_STATUS matches HP_CORES; status stable", "SST_CP_STATUS HP mask incorrect — HPM message gap"),
    ("4", "Verify MC6 entry is not blocked by PCT state", "Platform enters MC6; no PCT-related blocking event in NLOG", "MC6 blocked — PCT holding package from MC6"),
    ("5", "Check NLOG / fw trace for PCT or C-state errors", "No MCA, no assertion, no C-state error events", "NLOG error — check HPM protocol on HSLE XOS"),
  ],
  "pass_crit": "HP cores enter C6 on HSLE XOS; SST_CP_STATUS HP mask consistent; MC6 not blocked by PCT; no NLOG or model assertion.",
  "fail_crit": "HP cores stuck in C0 → Acode C6 MWAIT flow gap on HSLE; check CBB RTL C-state enable path. SST_CP_STATUS wrong → IMH-CBB HPM message not delivered correctly on HSLE XOS.",
  "post": "Save: SST_CP_STATUS snapshots (before/during HP-idle), NLOG trace, C6 residency counters per-core, MC6 entry/exit timestamps.",
},
"16030715678": {
  "title": "[PSS]PCT - BIOS Menu",
  "slug": "pss_pct_bios_menu",
  "fv_id": "22022422103", "fv_title": "PCT - TPMI register check",
  "env": "VP (Simics) — validates BIOS flow and PCode NVRAM read at boot.",
  "objective": "Verify BIOS correctly enables/disables PCT via BIOS setup knobs and that NVRAM values are pushed and reflected in TPMI after boot.",
  "preconditions": [
    ("VP (Simics) environment", "VP booted with BIOS image supporting PCT knobs", "HSLE not suitable for BIOS flow test"),
    ("CAPID4.bit29 = 1", "`sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29` reads 1", "PCT fuse not set in VP model"),
    ("xmlcli / pysvtools available", "`from pysvtools.xmlcli import nvram` succeeds", "xmlcli not installed"),
    ("PCT capable in BIOS", "`PctCapableSystem` NVRAM knob exposed", "BIOS does not expose PCT knobs"),
  ],
  "steps": [
    ("1", "Read NVRAM and verify PCT knobs are exposed: `PctCapableSystem` and `PctHpModuleCount`", "Both knobs present and readable; PctCapableSystem=1, PctHpModuleCount>0", "Knobs not present — BIOS does not expose PCT on VP"),
    ("2", "Change HP count via `pctd.pct_bios_knob_change(cores=4)` and trigger reboot", "NVRAM updated to cores=4 before reboot", "BIOS push failed — check xmlcli push path"),
    ("3", "After reboot: read `PctHpModuleCount` again", "Value reflects the new setting (4)", "Value not updated — PCode not reading NVRAM at boot"),
    ("4", "Run `pctd.generate_core_list()` and verify HP count matches NVRAM", "HP_CORES count = PctHpModuleCount × cores_per_module", "Mismatch — PCode CLOS programming does not reflect NVRAM value"),
    ("5", "Disable PCT via BIOS knob (set HP count=0) and reboot; verify `SST_CP_ENABLE=0`", "SST_CP_ENABLE=0 on both CBBs after disable", "SST_CP_ENABLE still 1 — PCode ignores disabled state"),
  ],
  "pass_crit": "BIOS knob change accepted; NVRAM reflects new value; TPMI SST_CP_ENABLE and CLOS assignments updated after reboot.",
  "fail_crit": "NVRAM not updated → BIOS push failed (xmlcli). TPMI not updated after reboot → PCode not reading NVRAM at boot.",
  "post": "Save: NVRAM snapshot before/after, SST_CP_CONTROL/STATUS register values, TPMI CLOS assignments, boot log.",
},
"16030715680": {
  "title": "[PSS]PCT - BIOS Negative Validation",
  "slug": "pss_pct_bios_negative_validation",
  "fv_id": "16030768621", "fv_title": "PCT - TPMI runtime negative validation",
  "env": "VP (Simics) — safe to inject invalid BIOS values without risking silicon damage.",
  "objective": "Verify that BIOS correctly rejects invalid PCT BIOS knob values (non-multiple of 4, out-of-range) and that invalid values are not pushed to NVRAM or TPMI.",
  "preconditions": [
    ("VP (Simics) environment", "VP booted with BIOS image supporting PCT knobs", "HSLE not suitable for negative BIOS test"),
    ("PCT enabled baseline", "Valid HP count in NVRAM (e.g. 8) before negative tests", "No baseline value to compare against"),
    ("xmlcli available", "`from pysvtools.xmlcli import nvram` succeeds", "xmlcli not installed"),
    ("pct_focus.py available", "`import pct_focus as pctd` succeeds", "Module path not set up"),
  ],
  "steps": [
    ("1", "Attempt to set non-multiple of 4: `pctd.pct_bios_knob_change(cores=3)`", "Function prints rejection message; NVRAM not updated", "Value accepted — validation logic missing"),
    ("2", "Attempt to set value exceeding MAX_MODULES_PER_CBB: `pctd.pct_bios_knob_change(cores=0x24)`", "Function rejects; NVRAM retains previous valid value", "Value accepted — out-of-range not checked"),
    ("3", "Read `PctHpModuleCount` from NVRAM and verify it is still a valid multiple of 4 ≤ 0x20", "`val % 4 == 0 and val <= 0x20` is True", "NVRAM corrupted with invalid value — PCode receives bad HP count"),
    ("4", "Attempt to set cores=0 (disable path); verify behavior is deterministic", "Either accepted cleanly as disabled state or rejected per policy; no crash", "Exception or model crash on cores=0"),
  ],
  "pass_crit": "Invalid BIOS values rejected; NVRAM retains last valid value; no model assertion or crash on invalid input.",
  "fail_crit": "Invalid value accepted into NVRAM → pct_bios_knob_change validation not working; PCode receives corrupt HP count.",
  "post": "Save: NVRAM snapshot before/after each injection, rejection log output, final NVRAM PctHpModuleCount value.",
},
"16030715684": {
  "title": "[PSS]PCT - Default Disabled",
  "slug": "pss_pct_default_disabled",
  "fv_id": "16030768619", "fv_title": "PCT - Default Enabled",
  "env": "VP (Simics) — validates PCode default-disabled handling before silicon.",
  "objective": "Verify that PCT is disabled by default when PctHpModuleCount=0 or BIOS PCT knob=Disabled. When PCT is disabled: SST_CP_ENABLE=0; all cores get the same TRL (no HP/LP differentiation).",
  "preconditions": [
    ("VP (Simics) environment", "VP booted with PctHpModuleCount=0 or BIOS knob set to Disabled", "HP count > 0 — test pre-condition not met"),
    ("CAPID4.bit29 = 1", "Fuse set so PCT is capable but opt-in via BIOS knob only", "Fuse not set — PCT never capable"),
    ("xmlcli available", "`from pysvtools.xmlcli import nvram` succeeds", "xmlcli not installed"),
  ],
  "steps": [
    ("1", "Read `PctHpModuleCount` from NVRAM; confirm it is 0", "PctHpModuleCount=0 (PCT disabled by default on NWP)", "HP count > 0 — not default-disabled state"),
    ("2", "Verify `SST_CP_ENABLE=0` on both CBBs", "`sst_cp_control.sst_cp_enable=0` on cbb0 and cbb1", "SST_CP_ENABLE=1 despite HP count=0 — PCode ignores NVRAM value"),
    ("3", "Run `pctd.generate_core_list()` and verify no HP cores assigned", "HP_CORES is empty; all cores are LP", "HP cores present when PCT disabled — CLOS assignment bug"),
    ("4", "Verify all cores get same TRL (no HP/LP frequency differentiation)", "`sst_tf_info_2.ratio_0` == `sst_tf_info_2.ratio_1` on both CBBs, or LP TRL applied uniformly", "HP TRL applied — PCode not clearing CLOS differentiation on disable"),
  ],
  "pass_crit": "SST_CP_ENABLE=0 when PctHpModuleCount=0; no HP core set; all cores get same TRL (no differentiation).",
  "fail_crit": "SST_CP_ENABLE=1 despite HP count=0 → PCode ignores NVRAM value; check PCode boot init sequence.",
  "post": "Save: NVRAM snapshot, SST_CP_CONTROL/STATUS on both CBBs, CLOS assignments, TRL ratio values.",
},
"16030715686": {
  "title": "[PSS]PCT - Default HP core selection",
  "slug": "pss_pct_default_hp_core_selection",
  "fv_id": "22022422105", "fv_title": "PCT - Default HP core selection",
  "env": "VP or HSLE — validates PCode NVRAM read and TPMI programming logic.",
  "objective": "Verify on PSS that the default HP core selection (first N modules per CBB, ordered, first core always HP) is correctly implemented by PCode from BIOS NVRAM.",
  "preconditions": [
    ("VP or HSLE environment", "PSS environment booted with PCT enabled", "Neither VP nor HSLE available"),
    ("PctHpModuleCount > 0", "NVRAM `PctHpModuleCount` set to valid value (multiple of 4)", "PCT disabled — no HP selection to verify"),
    ("pct_focus.py available", "`import pct_focus as pctd` succeeds", "Module path not set up"),
    ("Both CBBs active", "cbb0 and cbb1 accessible in namednodes", "Only one CBB active"),
  ],
  "steps": [
    ("1", "Read `PctHpModuleCount` from NVRAM", "Valid value > 0 and multiple of 4", "Value is 0 or non-multiple — pre-condition failure"),
    ("2", "Run `pctd.generate_core_list()` to populate HP_CORES and LP_CORES", "HP_CORES non-empty; total = HP_CORES + LP_CORES = 96 cores (2 CBBs × 48)", "HP_CORES empty — PCT not active on PSS"),
    ("3", "Verify first core (cbb0, compute0, module0, core0) is in HP_CORES", "`first_core in pctd.HP_CORES` is True", "First core is LP — PCode CLOS ordering bug on VP model"),
    ("4", "Verify HP module count matches NVRAM value", "`len(pctd.HP_CORES) // cores_per_module == PctHpModuleCount`", "Count mismatch — NVRAM read failing on VP or CLOS assignment wrong"),
    ("5", "Verify HP modules are the first N consecutive modules per CBB (ordered selection)", "First N modules per CBB have CLOS_ID=0 or 1 (HP); remaining have CLOS_ID=2 or 3 (LP)", "Non-consecutive HP selection — PCode selection algorithm bug"),
  ],
  "pass_crit": "First core is HP; HP module count matches BIOS NVRAM; CLOS assignments are consecutive from module 0 on both CBBs.",
  "fail_crit": "First core is LP on PSS → PCode CLOS assignment ordering bug on model (check VP TPMI model fidelity). HP count mismatch → NVRAM read failing on VP.",
  "post": "Save: NVRAM HP count, per-module CLOS assignments on both CBBs, HP_CORES and LP_CORES lists, first core assertion result.",
},
"16030715682": {
  "title": "[PSS]PCT - DQ Rules (FlexconPM)",
  "slug": "pss_pct_dq_rules_flexconpm",
  "fv_id": "22022422118", "fv_title": "PCT - DQ Rules (FlexconPM)",
  "env": "VP (Simics) or HSLE — FlexconPM is the automated checker.",
  "objective": "Verify PCT fuse-to-TPMI propagation and DQ rule execution on PSS (VP/HSLE) via FlexconPM. FlexconPM runs DQ (Decision Queue) rule checks post-boot. On PSS: validates PCode correctly reads fuse values and programs TPMI.",
  "preconditions": [
    ("VP or HSLE environment", "PSS booted with PCT-capable fuse set", "Environment not booted"),
    ("FlexconPM available", "`import pysvext.diamondrapids_flexcon.plugins.flexcon_pm as fpm` succeeds", "FlexconPM not installed on PSS env"),
    ("PCT-capable fuses set in VP model", "SST_TF fuses present in VP model configuration", "VP model lacks SST-TF fuse modeling — gap ticket needed"),
    ("pct_focus.py available", "`import pct_focus as pctd` succeeds", "Module path not set up"),
  ],
  "steps": [
    ("1", "Run FlexconPM DQ check: `result = fpm.run()`", "fpm.run() returns 0 (all DQ rules pass)", "Non-zero return — DQ rule violation detected on PSS model"),
    ("2", "Read `PctHpModuleCount` from NVRAM", "Value > 0 and multiple of 4", "Value 0 — PCT disabled state, wrong test configuration"),
    ("3", "Run `pctd.generate_core_list()` and verify HP cores present", "HP_CORES non-empty; matches expected HP count from NVRAM", "No HP cores — PCode did not read NVRAM knob on VP"),
    ("4", "Verify fuse values reflected in `SST_TF_INFO_0/1/2` TPMI registers", "LP_CLIP_RATIO, NUM_CORE, and RATIO fields populated from fuses (non-zero)", "Zero values — PCode Phase 5 fuse propagation not modeled on VP"),
  ],
  "pass_crit": "flexcon_pm exits 0; fuse-derived HP set matches TPMI; DQ rule events in model trace.",
  "fail_crit": "flexcon_pm fails → PCode DQ rule did not execute on VP; check VP model implements DQ event dispatch. HP set empty → PCode did not read NVRAM knob on VP.",
  "post": "Save: FlexconPM result code and trace, TPMI SST_TF_INFO_0/1/2 values, HP_CORES list, fuse readback values.",
},
"16030715694": {
  "title": "[PSS]PCT - enable/disable",
  "slug": "pss_pct_enable_disable",
  "fv_id": "16030768620", "fv_title": "PCT - TPMI runtime enable/disable",
  "env": "VP or HSLE — validates PCode state machine for PCT enable/disable event handling.",
  "objective": "Verify PCT can be enabled and disabled at runtime on PSS via TPMI SST_CP_CONTROL. Validates PCode response to runtime PCT toggle on the PSS model.",
  "preconditions": [
    ("PCT enabled at boot", "SST_CP_ENABLE=1 on both CBBs; HP_CORES non-empty", "PCT not initially enabled — toggle test requires enabled baseline"),
    ("VP or HSLE environment", "PSS model running and accessible via PythonSV", "No PSS environment available"),
    ("pct_focus.py available", "`import pct_focus as pctd` succeeds", "Module path not set up"),
    ("Both CBBs accessible", "cbb0 and cbb1 reachable via sv.sockets.cbbs", "Only one CBB — topology mismatch"),
  ],
  "steps": [
    ("1", "Run `pctd.generate_core_list()` and verify HP_CORES non-empty (PCT active baseline)", "HP_CORES > 0; SST_CP_ENABLE=1 on both CBBs", "HP_CORES empty — PCT not enabled at start"),
    ("2", "Disable PCT: set `sst_cp_control.sst_cp_enable=0` on both CBBs", "Write accepted; SST_CP_ENABLE reads back 0 on both CBBs", "Write ignored — TPMI write not modeled on VP"),
    ("3", "Run `pctd.generate_core_list()` again and verify no HP cores", "HP_CORES empty after disable; all cores treated as LP", "HP cores still present — PCode not responding to TPMI toggle on PSS"),
    ("4", "Re-enable: set `sst_cp_control.sst_cp_enable=1` on both CBBs", "Write accepted; SST_CP_ENABLE reads back 1", "Write ignored — re-enable path not modeled"),
    ("5", "Run `pctd.generate_core_list()` and verify HP cores restored", "HP_CORES non-empty; matches original count", "HP set not restored → PCode state machine bug on re-enable path"),
  ],
  "pass_crit": "PCT toggle works on PSS; HP set disappears on disable; restored on re-enable; no model crash or exception.",
  "fail_crit": "Toggle ignored → PCode PSS model not handling TPMI write interrupt correctly. HP set not restored → PCode state machine bug on re-enable path.",
  "post": "Save: SST_CP_CONTROL before/after each toggle, HP_CORES counts, NLOG events, any model exceptions.",
},
"16030715690": {
  "title": "[PSS]PCT - TPMI register check (FlexconPM)",
  "slug": "pss_pct_tpmi_register_check",
  "fv_id": "22022422103", "fv_title": "PCT - TPMI register check",
  "env": "VP or HSLE — FlexconPM reads TPMI registers via PythonSV/namednodes on model.",
  "objective": "Verify TPMI SST_CLOS registers reflect correct HP/LP assignment on PSS via FlexconPM. Uses FlexconPM automated register check on VP/HSLE.",
  "preconditions": [
    ("VP or HSLE environment", "PSS booted with PCT enabled", "Environment not booted"),
    ("FlexconPM available", "`import pysvext.diamondrapids_flexcon.plugins.flexcon_pm as fpm` succeeds", "FlexconPM not installed"),
    ("PCT enabled at boot", "SST_CP_ENABLE=1; PctHpModuleCount > 0 in NVRAM", "PCT not enabled — FlexconPM will fail correctly but test is invalid"),
    ("Both CBBs accessible", "cbb0 and cbb1 accessible via sv.sockets.cbbs", "Only one CBB active"),
  ],
  "steps": [
    ("1", "Run FlexconPM automated TPMI check: `result = fpm.run()`", "fpm.run() returns 0 (all TPMI register checks pass)", "Non-zero → TPMI model has wrong register encoding (VP model gap)"),
    ("2", "Manually verify SST_CP_CONTROL fields on both CBBs: `sst_cp_enable=1` and `sst_cp_priority_type=1`", "Both CBBs: enable=1, priority_type=1 (Ordered Throttling)", "Wrong values → PCode PSS firmware bug in CLOS programming logic"),
    ("3", "Run `pctd.generate_core_list()` and verify HP/LP split matches NVRAM", "HP count matches `PctHpModuleCount × cores_per_module`", "Mismatch → CLOS assignments not reflected in namednodes on VP"),
    ("4", "Verify `SST_CP_STATUS` HP mask on both CBBs is non-zero and consistent with CLOS assignments", "HP mask bits set for HP modules; LP mask bits clear for LP modules", "HP mask empty → PCode not propagating SST_CP_STATUS on VP"),
  ],
  "pass_crit": "flexcon_pm exits 0 on PSS; CLOS assignments correct in TPMI model; SST_CP_CONTROL and SST_CP_STATUS valid.",
  "fail_crit": "flexcon_pm fails on PSS → TPMI model has wrong register encoding (VP model gap). CLOS wrong → PCode PSS firmware bug in CLOS programming logic.",
  "post": "Save: FlexconPM result, SST_CP_CONTROL fields, SST_CP_STATUS HP mask, CLOS assignments per module.",
},
"16030715692": {
  "title": "[PSS]PCT - Turbo frequency check",
  "slug": "pss_pct_turbo_frequency_check",
  "fv_id": "22022422116", "fv_title": "PCT - Turbo frequency check",
  "env": "HSLE XOS preferred (CBB RTL validates actual TRL table application by Acode). VP validates PCode TRL table programming only.",
  "objective": "Verify on PSS (HSLE XOS or VP) that HP cores are assigned to a higher SST-TF bucket than LP cores. On VP, actual frequency values are modeled; on HSLE XOS, RTL-level TRL assignment is validated.",
  "preconditions": [
    ("PCT enabled", "SST_CP_ENABLE=1; HP_CORES non-empty after generate_core_list()", "PCT disabled — no HP/LP differentiation to verify"),
    ("PSS environment booted", "HSLE XOS or VP accessible via PythonSV", "No PSS environment available"),
    ("SST_TF_INFO_2 populated", "`sst_tf_info_2.ratio_0` non-zero on both CBBs", "TRL ratios zero — fuse propagation not modeled"),
    ("pct_focus.py available", "`import pct_focus as pctd` succeeds", "Module path not set up"),
  ],
  "steps": [
    ("1", "Read HP TRL ratio from `sst_tf_info_2.ratio_0` on both CBBs", "Ratio_0 > 0 (HP SST-TF bucket non-zero)", "Zero ratio — fuse not propagated on VP model"),
    ("2", "Read baseline ratio from `sst_tf_info_2.ratio_1` (P1 guaranteed frequency) on both CBBs", "Ratio_1 ≤ ratio_0 (HP TRL ≥ guaranteed baseline)", "HP TRL < P1 — TRL programming error"),
    ("3", "Run `pctd.generate_core_list()` and on HSLE XOS check actual HP vs LP MSR 0x198 frequencies", "Average HP core frequency > average LP core frequency", "HP == LP freq on HSLE → Acode not applying CLOS-differentiated TRL (RTL bug)"),
    ("4", "Verify SST-TF bucket assignment: HP modules use CLOS_ID 0/1; LP modules use CLOS_ID 2/3", "CLOS_ID 0 or 1 for all HP modules; CLOS_ID 2 or 3 for all LP modules", "LP modules assigned CLOS 0/1 — CLOS assignment inverted"),
  ],
  "pass_crit": "HP TRL bucket >= P1 in SST_TF_INFO_2; HP ratio > LP ratio in MSR 0x198 on HSLE XOS; CLOS assignments correct.",
  "fail_crit": "HP == LP freq on HSLE → Acode not applying CLOS-differentiated TRL (RTL bug). SST_TF_INFO_2 ratios equal → PCode not programming different TRL per CLOS.",
  "post": "Save: SST_TF_INFO_2 ratio values per CBB, per-core MSR 0x198 readings (HP vs LP), CLOS assignments, HSLE XOS Acode TRL trace.",
},
}

REF_BLOCK = """### Reference Documents

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — PCT CLOS model, HP/LP core assignment, Ordered Throttling
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_CONTROL, SST_CLOS_ASSOC, SST_TF_INFO registers
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT TPMI register definitions
- [NWP HAS PM](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) — PCT feature list and NWP applicability
- [PCT KB — pct.md](../../../pm_features/sst/pct.md) — KB architecture, CLOS model, NWP-specific deltas"""

def make_pre(rows):
    lines = ["| Pre-Condition | Expected State | Failure Indication |", "|---------------|---------------|-------------------|"]
    for a,b,c in rows:
        lines.append(f"| {a} | {b} | {c} |")
    return "\n".join(lines)

def make_steps(rows):
    lines = ["| # | Action | Expected Result (PASS) | Failure Indication |", "|---|--------|------------------------|--------------------|"]
    for a,b,c,d in rows:
        lines.append(f"| {a} | {b} | {c} | {d} |")
    return "\n".join(lines)

for hsd_id, tc in TCS.items():
    fv_link = f"https://hsdes.intel.com/appstore/article-one/#/{tc['fv_id']}"
    content = f"""# Deep Analysis: {tc['title']}

| Field | Value |
|-------|-------|
| **HSD ID** | [{hsd_id}](https://hsdes.intel.com/appstore/article-one/#/{hsd_id}) |
| **Title** | {tc['title']} |
| **Segment** | PSS |
| **Target Program** | NWP (Newport) |
| **Feature** | PCT (Priority Core Turbo) |
| **Val Environment** | silicon,virtual_platform |
| **Parent TCD** | [22022420858 — PCT Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **FV Counterpart** | [{tc['fv_id']} — {tc['fv_title']}]({fv_link}) |

---

## Test Case Intent

**Objective:** {tc['objective']}

**PSS Environment:** {tc['env']}

**Key distinction from FV:** This TC runs on a pre-silicon model (VP/HSLE). It finds firmware/RTL bugs before tape-out. FV confirms on real silicon. Not a duplicate.

### Pre-Conditions

{make_pre(tc['preconditions'])}

### Test Steps

{make_steps(tc['steps'])}

### Pass / Fail Criteria

**PASS:** {tc['pass_crit']}

**FAIL:** {tc['fail_crit']}

### Post-Process

{tc['post']}

{REF_BLOCK}

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

{tc['title']} is a PSS pre-silicon test. NWP PSS environment (VP/HSLE) supports PCT TPMI register access via namednodes. Firmware behavior validated before tape-out.

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

{tc['pass_crit']}
"""
    out = BASE / f"HSD_{hsd_id}_{tc['slug']}.inference.md"
    out.write_text(content, encoding="utf-8")
    print(f"Written: {out.name}")

print("Done - 9 files written")
