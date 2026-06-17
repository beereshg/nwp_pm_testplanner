# Deep Analysis: Inconsistent Throttling Silicon VP

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422377 |
| **Title** | Inconsistent Throttling_silicon_vp |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Quality |
| **Sub-Feature** | PEM — inconsistent throttle (5s gaps), total throttle time via VP/TPMI |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same as TC 22022422363 via VP/TPMI path. Note: steps text says I3C — use VP/TPMI interface per TC categorization.

Tags: `Ready_for_testing`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

```bash
python telemetryAPIs.py  # PEM inconsistent throttle via VP/TPMI
```

Same steps — throttle with 5s gaps, verify PEM counter = total throttle ± 10%.

### Pass Criteria — VP/TPMI PEM counter accurate under inconsistent throttle

---

## Section F: Recommendation

**Recommendation: ADOPT — VP path / TPMI; `Ready_for_testing`**

**Priority**: Medium — `Ready_for_testing`
