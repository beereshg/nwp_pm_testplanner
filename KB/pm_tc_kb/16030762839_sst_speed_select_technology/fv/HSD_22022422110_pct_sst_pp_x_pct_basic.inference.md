# Deep Analysis: PCT - SST-PP x PCT Basic Checks

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422110 |
| **Title** | PCT - SST-PP x PCT Basic Checks |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SST |
| **Sub-Feature** | PCT × SST-PP interaction — dynamic PP switching with PCT enabled |
| **NWP Disposition** | **Skip_ZBB** |

---

## Section A: NWP Disposition & Justification

**Disposition: Skip_ZBB**

**Reason**: This TC explicitly tests the interaction between **PCT and SST-PP** (dynamic Performance Profile switching). SST-PP is on the NWP ZBB list — it is not implemented on NWP. The test steps include:
- "Boot to SST-PP0 w/ PCT enabled"
- "Switch to SST-PP1"
- Dynamic SST-PP switching with PCT functionality checks

Since SST-PP is ZBB on NWP, this test cannot be run. The PCT-only baseline checks are covered separately by TCs 22022422103, 22022422104, 22022422105, 22022422116, 22022422117.

Tags: `NGA_MAIN`, `plc.feature.p1`, `pm.xproducts.pm`, `PMSS_NWP_READINESS_CHECK`.

---

## Section F: Recommendation

**Recommendation: SKIP — SST-PP is ZBB on NWP; PCT × SST-PP interaction test not executable; PCT-only validation covered by other PCT TCs (22022422103-22022422117)**

**Priority**: N/A — ZBB blocker; revisit for future NWP stepping if SST-PP is enabled
