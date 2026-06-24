# Deep Analysis: [PSS]PCT - All HP cores in C6

| Field | Value |
|-------|-------|
| **HSD ID** | [16030715676](https://hsdes.intel.com/appstore/article-one/#/16030715676) |
| **Title** | [PSS]PCT - All HP cores in C6 |
| **Segment** | PSS |
| **Target Program** | NWP (Newport) |
| **Feature** | PCT (Priority Core Turbo) |
| **Val Environment** | silicon,virtual_platform |
| **Parent TCD** | [22022420858 — PCT Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **FV Counterpart** | [22022422104 — PCT - All HP cores in C6](https://hsdes.intel.com/appstore/article-one/#/22022422104) |

---

## Test Case Intent

**Objective:** Verify PCT behavior when all HP cores are in C6 on HSLE XOS. Validates that cross-die HPM protocol correctly handles the HP-idle state; MC6 entry proceeds without PCT-related blocking.

**PSS Environment:** HSLE XOS preferred (both IMH and CBB RTL active for cross-die validation). VP cannot model Acode C6 entry accurately.

**Key distinction from FV:** This TC runs on a pre-silicon model (VP/HSLE). It finds firmware/RTL bugs before tape-out. FV confirms on real silicon. Not a duplicate.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| PCT enabled | SST_CP_ENABLE=1 on both CBBs | PCT not active |
| HSLE XOS environment | IMH and CBB RTL both running (XOS) | VP only — C6 model gap |
| HP cores identified | pctd.generate_core_list() returns HP_CORES non-empty | No HP cores — check BIOS knob |
| LP-only workload available | Workload can be pinned to LP cores | Cannot isolate HP core idle |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Generate HP/LP core lists via `pctd.generate_core_list()` | HP_CORES and LP_CORES populated for both CBBs | Empty HP_CORES — PCT not enabled |
| 2 | Pin sustained workload to LP cores; ensure HP cores remain idle | HP cores enter C6 on HSLE; no workload activity on HP threads | HP cores stuck at C0 — pin failed |
| 3 | Monitor `SST_CP_STATUS` on both CBBs during HP-idle window | HP mask in SST_CP_STATUS matches HP_CORES; status stable | SST_CP_STATUS HP mask incorrect — HPM message gap |
| 4 | Verify MC6 entry is not blocked by PCT state | Platform enters MC6; no PCT-related blocking event in NLOG | MC6 blocked — PCT holding package from MC6 |
| 5 | Check NLOG / fw trace for PCT or C-state errors | No MCA, no assertion, no C-state error events | NLOG error — check HPM protocol on HSLE XOS |

### Pass / Fail Criteria

**PASS:** HP cores enter C6 on HSLE XOS; SST_CP_STATUS HP mask consistent; MC6 not blocked by PCT; no NLOG or model assertion.

**FAIL:** HP cores stuck in C0 → Acode C6 MWAIT flow gap on HSLE; check CBB RTL C-state enable path. SST_CP_STATUS wrong → IMH-CBB HPM message not delivered correctly on HSLE XOS.

### Post-Process

Save: SST_CP_STATUS snapshots (before/during HP-idle), NLOG trace, C6 residency counters per-core, MC6 entry/exit timestamps.

### Reference Documents

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — PCT CLOS model, HP/LP core assignment, Ordered Throttling
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_CONTROL, SST_CLOS_ASSOC, SST_TF_INFO registers
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT TPMI register definitions
- [NWP HAS PM](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) — PCT feature list and NWP applicability
- [PCT KB — pct.md](../../../pm_features/sst/pct.md) — KB architecture, CLOS model, NWP-specific deltas

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

[PSS]PCT - All HP cores in C6 is a PSS pre-silicon test. NWP PSS environment (VP/HSLE) supports PCT TPMI register access via namednodes. Firmware behavior validated before tape-out.

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

HP cores enter C6 on HSLE XOS; SST_CP_STATUS HP mask consistent; MC6 not blocked by PCT; no NLOG or model assertion.
