# Deep Analysis: Inconsistent Throttling Silicon I3C

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422363 |
| **Title** | Inconsistent Throttling_silicon_I3C |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Quality |
| **Sub-Feature** | PEM — inconsistent throttle (gaps of 5s), total throttle time captured via I3C |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Tests PEM accuracy with **gaps in throttle events** (5-second gaps between throttle periods). PEM must correctly accumulate only the actual throttle time, not the gaps.

Formula: `PEM counter (ms) = total induced throttle time ± 10%`

Tags: `Ready_for_testing`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

```bash
python telemetryAPIs.py  # PEM inconsistent throttle via I3C
```

| Step | Action | Details |
|------|--------|---------|
| 1 | Enable PEM | TPMI PEM control |
| 2 | Introduce throttle events with 5s gaps | Cycle: throttle ON, 5s OFF, repeat |
| 3 | Read PEM counters via **I3C** | BMC → I3C → CPU |
| 4 | Verify: PEM counter = total throttle time ± 10% | Gaps NOT counted |

### Pass Criteria
- PEM counter equals sum of throttle-ON intervals (not gaps)
- 10% variance tolerance
- I3C interface accurately reports cumulative counter

---

## Section F: Recommendation

**Recommendation: ADOPT — I3C inconsistent throttle; PEM gap-handling functional on NWP; BMC setup required**

**Priority**: High — `Ready_for_testing`; gap handling in PEM is critical for accurate throttle accounting in production
