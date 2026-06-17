# Deep Analysis: Consistent Throttling Silicon VP

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422351 |
| **Title** | Consistent throttling_silicon_vp |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Quality |
| **Sub-Feature** | PEM — consistent 1-minute throttle, measured via Virtual Platform / TPMI read path |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same as TC 22022422343 but targeting virtual platform verification path. Also applicable on silicon via the VP-equivalent TPMI read path.

Tags: `Ready_for_testing`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python telemetryAPIs.py  # PEM telemetry via VP path / TPMI
```

| Step | Action |
|------|--------|
| 1 | Enable PEM through TPMI |
| 2 | Enforce 1-minute throttle (continuous) |
| 3 | Read PEM counters via VP/TPMI path |
| 4 | Verify: LPF ramp + PEM counter ≈ 1 min |

### Pass Criteria
- PEM counter accuracy verified via VP read path (TPMI equivalent on silicon)

---

## Section F: Recommendation

**Recommendation: ADOPT — VP path maps to TPMI read on silicon; `Ready_for_testing` indicates high confidence**

**Priority**: Medium — `Ready_for_testing`; VP path validation for PEM counter
