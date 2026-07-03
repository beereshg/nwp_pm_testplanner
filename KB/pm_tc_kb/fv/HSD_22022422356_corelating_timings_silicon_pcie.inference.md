# Deep Analysis: Correlating Timings Silicon PCIE

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422356 |
| **Title** | Corelating timings_silicon_PCIE |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Quality |
| **Sub-Feature** | PEM — time correlation: throttle event → PEM_STATUS bit set time ≈ TW setting, via PCIe |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same timing correlation test as TC 22022422353 but via **PCIe interface**.

Tags: `New_Content`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python telemetryAPIs.py  # PEM timing via PCIe
```

| Step | Action |
|------|--------|
| 1 | Enable PEM, configure TW |
| 2 | Introduce throttle event |
| 3 | Measure `PEM_STATUS` set time via **PCIe** |
| 4 | Verify ≈ TW setting ± 10% |

### Pass Criteria — PCIe interface reports `PEM_STATUS` timing matching TW ± 10%

---

## Section F: Recommendation

**Recommendation: ADOPT — PCIe PEM timing path; same methodology as I3C variant**

**Priority**: Medium — `New_Content`; PCIe path for PEM timing accuracy
