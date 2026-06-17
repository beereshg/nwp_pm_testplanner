# Deep Analysis: Correlating Timings Silicon I3C

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422353 |
| **Title** | Corelating timings_silicon_I3C |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Quality |
| **Sub-Feature** | PEM — time correlation: throttle event → PEM_STATUS bit set time ≈ TW setting, via I3C |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that after introducing a throttle event, the **time taken to set `PEM_STATUS` bit** via I3C matches the configured TW (Time Window) setting (±10% tolerance). Tests PEM event response latency accuracy.

Tags: `Ready_for_testing`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python telemetryAPIs.py  # PEM timing via I3C
```

| Step | Action | Details |
|------|--------|---------|
| 1 | Enable PEM through TPMI | Configure TW setting |
| 2 | Introduce throttle event | PROCHOT or RAPL PL1 low |
| 3 | Measure time to `PEM_STATUS` bit set | Via I3C interface |
| 4 | Compare to TW setting | ±10% tolerance |

### Pass Criteria
- Time from throttle event to `PEM_STATUS` bit = TW setting ± 10%
- I3C interface reports timing accurately

---

## Section F: Recommendation

**Recommendation: ADOPT — I3C timing path; BMC setup required; PEM TW timing functional on NWP**

**Priority**: High — `Ready_for_testing`; PEM timing accuracy is a Quality gate for event reporting latency
