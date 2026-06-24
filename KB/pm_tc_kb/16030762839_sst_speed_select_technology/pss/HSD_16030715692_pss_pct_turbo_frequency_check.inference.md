# Deep Analysis: [PSS]PCT - Turbo frequency check

| Field | Value |
|-------|-------|
| **HSD ID** | [16030715692](https://hsdes.intel.com/appstore/article-one/#/16030715692) |
| **Title** | [PSS]PCT - Turbo frequency check |
| **Segment** | PSS |
| **Target Program** | NWP (Newport) |
| **Feature** | PCT (Priority Core Turbo) |
| **Val Environment** | silicon,virtual_platform |
| **Parent TCD** | [22022420858 — PCT Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **FV Counterpart** | [22022422116 — PCT - Turbo frequency check](https://hsdes.intel.com/appstore/article-one/#/22022422116) |

---

## Test Case Intent

**Objective:** Verify on PSS (HSLE XOS or VP) that HP cores are assigned to a higher SST-TF bucket than LP cores. On VP, actual frequency values are modeled; on HSLE XOS, RTL-level TRL assignment is validated.

**PSS Environment:** HSLE XOS preferred (CBB RTL validates actual TRL table application by Acode). VP validates PCode TRL table programming only.

**Key distinction from FV:** This TC runs on a pre-silicon model (VP/HSLE). It finds firmware/RTL bugs before tape-out. FV confirms on real silicon. Not a duplicate.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| PCT enabled | SST_CP_ENABLE=1; HP_CORES non-empty after generate_core_list() | PCT disabled — no HP/LP differentiation to verify |
| PSS environment booted | HSLE XOS or VP accessible via PythonSV | No PSS environment available |
| SST_TF_INFO_2 populated | `sst_tf_info_2.ratio_0` non-zero on both CBBs | TRL ratios zero — fuse propagation not modeled |
| pct_focus.py available | `import pct_focus as pctd` succeeds | Module path not set up |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read HP TRL ratio from `sst_tf_info_2.ratio_0` on both CBBs | Ratio_0 > 0 (HP SST-TF bucket non-zero) | Zero ratio — fuse not propagated on VP model |
| 2 | Read baseline ratio from `sst_tf_info_2.ratio_1` (P1 guaranteed frequency) on both CBBs | Ratio_1 ≤ ratio_0 (HP TRL ≥ guaranteed baseline) | HP TRL < P1 — TRL programming error |
| 3 | Run `pctd.generate_core_list()` and on HSLE XOS check actual HP vs LP MSR 0x198 frequencies | Average HP core frequency > average LP core frequency | HP == LP freq on HSLE → Acode not applying CLOS-differentiated TRL (RTL bug) |
| 4 | Verify SST-TF bucket assignment: HP modules use CLOS_ID 0/1; LP modules use CLOS_ID 2/3 | CLOS_ID 0 or 1 for all HP modules; CLOS_ID 2 or 3 for all LP modules | LP modules assigned CLOS 0/1 — CLOS assignment inverted |

### Pass / Fail Criteria

**PASS:** HP TRL bucket >= P1 in SST_TF_INFO_2; HP ratio > LP ratio in MSR 0x198 on HSLE XOS; CLOS assignments correct.

**FAIL:** HP == LP freq on HSLE → Acode not applying CLOS-differentiated TRL (RTL bug). SST_TF_INFO_2 ratios equal → PCode not programming different TRL per CLOS.

### Post-Process

Save: SST_TF_INFO_2 ratio values per CBB, per-core MSR 0x198 readings (HP vs LP), CLOS assignments, HSLE XOS Acode TRL trace.

### Reference Documents

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — PCT CLOS model, HP/LP core assignment, Ordered Throttling
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_CONTROL, SST_CLOS_ASSOC, SST_TF_INFO registers
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT TPMI register definitions
- [NWP HAS PM](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) — PCT feature list and NWP applicability
- [PCT KB — pct.md](../../../pm_features/sst/pct.md) — KB architecture, CLOS model, NWP-specific deltas

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

[PSS]PCT - Turbo frequency check is a PSS pre-silicon test. NWP PSS environment (VP/HSLE) supports PCT TPMI register access via namednodes. Firmware behavior validated before tape-out.

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

HP TRL bucket >= P1 in SST_TF_INFO_2; HP ratio > LP ratio in MSR 0x198 on HSLE XOS; CLOS assignments correct.
