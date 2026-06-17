# Deep Analysis: SST-PP Dynamic Fuse Checks

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422188 |
| **Title** | SST-PP Dynamic Fuse checks |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SST |
| **Sub-Feature** | SST-PP — fuse consistency and logical ordering validation |
| **NWP Disposition** | **Skip_ZBB** |

---

## Section A: NWP Disposition & Justification

**Disposition: Skip_ZBB**

**Reason**: SST-PP (Speed Select Technology – Performance Profile) is on the NWP ZBB list. This feature allows dynamic switching between multiple power/performance profiles. SST-PP is not implemented on NWP initial silicon.

Test validates SST-PP fuse ordering constraints:
- `sst_pp_{level}_{cdyn}_p1_ratio` must be decreasing at higher cdyn (longer instructions)
- `sst_pp_{level}_turbo_ratio_limit_cores_numcore{bucket}` must be increasing at higher buckets
- Cross-level consistency checks

Since SST-PP is ZBB, these fuses may not be populated.

Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section F: Recommendation

**Recommendation: SKIP — SST-PP is ZBB on NWP; fuse checks for SST-PP profiles not applicable; revisit for future NWP stepping if SST-PP is enabled**

**Priority**: N/A — ZBB blocker
