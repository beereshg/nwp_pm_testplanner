# Deep Analysis: Inconsistent Throttling Silicon TPMI

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422374 |
| **Title** | Inconsistent Throttling_silicon_TPMI |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Quality |
| **Sub-Feature** | PEM — inconsistent throttle (5s gaps), total throttle time captured via TPMI |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same as TC 22022422363 but reads PEM counter via **TPMI** (note: steps text says I3C but interface field is TPMI — use TPMI per feature categorization).

Tags: `New_Content`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

```bash
python telemetryAPIs.py  # PEM inconsistent throttle via TPMI
```

Same steps — throttle with 5s gaps, read PEM counter via TPMI, verify = total throttle time ± 10%.

### Pass Criteria — TPMI PEM counter = total throttle time ± 10%

---

## Section F: Recommendation

**Recommendation: ADOPT — TPMI in-band PEM path; primary NWP interface; note source steps text references I3C — verify correct interface per NWP TPMI spec**

**Priority**: High — `New_Content`; TPMI inconsistent throttle accumulation
