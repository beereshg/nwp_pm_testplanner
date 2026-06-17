# Deep Analysis: Cross Products (PM × FW Sideband Harassers)

| Field | Value |
|-------|-------|
| **HSD ID** | 14022603910 |
| **Title** | Cross Products |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | (blank) |
| **Sub-Feature** | PM functional content × FW-based sideband harassers — concurrent stress |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Cross-product test: run PM functional validation content while simultaneously running firmware-based sideband harassers. Verifies PM correctness under sideband traffic stress. Generic cross-product structure; no ZBB features required.

---

## Section B: NWP-Specific Test Procedure

### NWP Approach

| Step | Action | Details |
|------|--------|---------|
| 1 | Start FW-based sideband harassers | GPSB/PMSB traffic generators |
| 2 | Simultaneously run PM functional tests | e.g., RAPL verify, C-state verify |
| 3 | Run for extended duration (30+ min) | Concurrent stress |
| 4 | Verify PM features pass despite sideband traffic | No performance regression |
| 5 | Verify no sideband errors | No timeout/MCA from harassment |

### Pass Criteria
- PM functional tests pass while sideband harassers active
- No sideband timeout or MCA during concurrent stress
- System stable for full duration

---

## Section F: Recommendation

**Recommendation: ADOPT — No specific ZBB blockers; NWP 2 CBBs + 1 IMH reduces sideband endpoint count; PM × sideband concurrency same architecture**

**Priority**: Medium — Cross-product stability important for real-world scenarios with concurrent sideband traffic
