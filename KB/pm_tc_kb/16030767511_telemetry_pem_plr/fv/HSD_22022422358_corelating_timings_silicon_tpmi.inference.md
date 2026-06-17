# Deep Analysis: Correlating Timings Silicon TPMI

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422358 |
| **Title** | Corelating timings_silicon_TPMI |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Quality |
| **Sub-Feature** | PEM — time correlation: throttle event → PEM_STATUS bit set time ≈ TW setting, via TPMI |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same timing correlation test as TC 22022422353 but via **TPMI interface** directly.

Tags: `New_Content`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

```bash
python telemetryAPIs.py  # PEM timing via TPMI
```

| Step | Action |
|------|--------|
| 1 | Enable PEM, configure TW via TPMI |
| 2 | Introduce throttle event |
| 3 | Measure `PEM_STATUS` set time via **TPMI** |
| 4 | Verify ≈ TW setting ± 10% |

### Pass Criteria — TPMI in-band path reports `PEM_STATUS` timing matching TW ± 10%

---

## Section F: Recommendation

**Recommendation: ADOPT — TPMI primary interface for NWP; MSR deprecated → use TPMI for all PEM reads**

**Priority**: High — `New_Content`; TPMI timing path is canonical for NWP PEM telemetry
