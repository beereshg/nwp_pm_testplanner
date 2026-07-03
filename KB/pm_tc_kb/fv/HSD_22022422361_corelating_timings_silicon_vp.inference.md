# Deep Analysis: Correlating Timings Silicon VP

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422361 |
| **Title** | Corelating timings_silicon_vp |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Quality |
| **Sub-Feature** | PEM — time correlation: throttle event → PEM_STATUS bit set time, via VP/TPMI |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same timing test as TC 22022422353 but via VP / TPMI equivalent path.

Tags: `Ready_for_testing`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

```bash
python telemetryAPIs.py  # PEM timing via VP/TPMI
```

Same steps as I3C/PCIe/TPMI variants — introduce throttle, measure PEM_STATUS set time, verify ≈ TW ± 10%.

### Pass Criteria — VP path `PEM_STATUS` timing matches TW ± 10%

---

## Section F: Recommendation

**Recommendation: ADOPT — VP path maps to TPMI on silicon; `Ready_for_testing`**

**Priority**: Medium — `Ready_for_testing`; VP/TPMI timing path verification
