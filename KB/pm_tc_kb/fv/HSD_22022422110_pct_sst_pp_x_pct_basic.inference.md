# Deep Analysis: PCT - SST-PP x PCT Basic Checks

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422110](https://hsdes.intel.com/appstore/article-one/#/22022422110) |
| **Title** | PCT - SST-PP x PCT Basic Checks |
| **Date** | 2026-06-23 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SST |
| **Sub-Feature** | PCT × SST-PP — dynamic performance-profile switching × PCT interaction |
| **Parent TCD** | [22022420858 — PCT - Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **NWP Disposition** | **Rejected — ZBB (SST-PP ZBB'd on NWP)** |
| **Status** | rejected |
| **Owner** | mps |
| **Tags** | plc.feature.p1, PMSS_NWP_READINESS_CHECK |

## Version History
- v1 (2025-07-24): Initial stub — Skip_ZBB only
- v2 (2026-06-23): Full rewrite — rejection rationale, DMR scenario preserved, sections A/F/G

---

## Test Case Intent

Validate interaction between **PCT** and **dynamic SST-PP switching** across performance-profile
changes: boot in SST-PP0 with PCT enabled → verify PCT functionality → switch to SST-PP1 →
verify PCT behavior again. If PCT behaves irregularly after PP switching, verify functionality
is restored after disable/re-enable.

**DMR context**: PCT may not work correctly after dynamic SST-PP switching if HP/LP core
designations are incompatible with the new PP level. Users must adjust HP/LP core assignments
or explicitly disable SST-TF if PCT should stop after PP switching. The SST-TF tool can handle
such scenarios.

**NWP status**: **REJECTED (ZBB)** — SST-PP is ZBB'd on NWP per
[HSD 22021155414](https://hsdes.intel.com/appstore/article-one/#/22021155414). This TC
requires dynamic PP level change (PP0→PP1) which cannot be exercised. TC retained for
historical traceability only.

**PCT-only coverage** on NWP provided by: 22022422103, 22022422104, 22022422105, 22022422116, 22022422117.

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP |
| Dynamic SST-PP | **Not available** — SST-PP ZBB'd on NWP |
| Status | **Rejected / ZBB — not executable on NWP** |

### Original DMR Test Steps (not executable on NWP)

| # | Action | Expected Result (DMR PASS) | NWP Status |
|---|--------|---------------------------|-----------|
| 1 | Boot to SST-PP0 with PCT enabled | Clean boot; PCT active under PP0 | ❌ SST-PP ZBB'd |
| 2 | Verify PCT: enabled → disable → re-enable | PCT toggles correctly under PP0 | ❌ SST-PP ZBB'd |
| 3 | Switch to SST-PP1 (dynamic PP level change) | PP level changes successfully | ❌ SST-PP ZBB'd |
| 4 | Verify PCT under PP1: enabled → disable → re-enable | PCT functions correctly; irregular behavior fixed after re-enable | ❌ SST-PP ZBB'd |

### Pass / Fail Criteria (NWP)

- **NWP PASS**: TC correctly marked rejected; no execution attempted
- **NWP FAIL**: TC incorrectly treated as executable; dynamic SST-PP switching assumed supported

---

## Section A: NWP Delta

**Disposition: Rejected — ZBB**

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| SST-PP dynamic switching | ✅ Active (PP0–PP4) | ❌ **ZBB'd** ([HSD 22021155414](https://hsdes.intel.com/appstore/article-one/#/22021155414)) | TC scenario not exercisable |
| PCT functionality | ✅ Active | ✅ Active | PCT itself works; SST-PP interaction N/A |
| PP0→PP1 level change | ✅ Supported | ❌ Not available | No valid cross-product trigger |
| SST-PP × PCT core compatibility | Required | ❌ N/A | Moot without SST-PP |
| Revisit condition | — | Future NWP stepping with SST-PP | — |

**ZBB reference**: [HSD 22021155414](https://hsdes.intel.com/appstore/article-one/#/22021155414) — SST-PP/BF/CP ZBB'd on NWP.

---

## Section F: Recommendations

**Keep rejected.** SST-PP ZBB'd — entire cross-product scenario has no valid trigger on NWP.
PCT-only validation is covered by TCs 22022422103–22022422117. Revisit only if SST-PP is
explicitly un-ZBB'd in a future NWP stepping.

---

## Section G: PSS Grading

| Sl No | Dimension | Value | Rationale |
|-------|-----------|-------|-----------|
| 1 | NWP Delta | Yes | SST-PP ZBB'd — entire scenario invalid |
| 2 | Applicable NWP | **No (ZBB)** | Dynamic SST-PP switching not available |
| 3 | PSS Environment | N/A | Feature not activatable |
| 4 | Silicon Only | N/A | — |
| 5 | Test Content | N/A (ZBB) | No adaptation possible |
| 6 | OS | N/A | — |

### References
- [HSD 22021155414](https://hsdes.intel.com/appstore/article-one/#/22021155414) — SST-PP ZBB on NWP
- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — PCT × SST-PP interaction
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)

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
