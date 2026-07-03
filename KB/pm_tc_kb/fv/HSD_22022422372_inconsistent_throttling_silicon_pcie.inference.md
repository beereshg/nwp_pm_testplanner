# Deep Analysis: Inconsistent Throttling Silicon PCIE

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422372 |
| **Title** | Inconsistent Throttling_silicon_PCIE |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Quality |
| **Sub-Feature** | PEM — inconsistent throttle (5s gaps), total throttle time captured via PCIe |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same as TC 22022422363 but reads PEM counter via **PCIe interface**.

Tags: `New_Content`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

```bash
python telemetryAPIs.py  # PEM inconsistent throttle via PCIe
```

Same steps — throttle with 5s gaps, read PEM counter via PCIe, verify = total throttle time ± 10%.

### Pass Criteria — PCIe PEM counter = total throttle time ± 10%

---

## Section F: Recommendation

**Recommendation: ADOPT — PCIe PEM path; same methodology as I3C variant**

**Priority**: Medium — `New_Content`
