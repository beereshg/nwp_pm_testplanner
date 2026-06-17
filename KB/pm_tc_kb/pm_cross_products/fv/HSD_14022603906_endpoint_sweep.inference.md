# Deep Analysis: EndPoint Sweep

| Field | Value |
|-------|-------|
| **HSD ID** | 14022603906 |
| **Title** | EndPoint Sweep |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | (blank) |
| **Sub-Feature** | Sideband endpoint sweep — PMSB and GPSB traffic harassers on all CBB and IMH endpoints |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test runs sideband traffic harassers on all PMSB (PMC Sideband) and GPSB (General Purpose Sideband) endpoints in CBB and IMH dies. PythonSv-based content to trigger sideband access patterns.

**NWP topology**: 2 CBBs + 1 IMH (vs DMR: 4 CBBs + 2 IMHs). Endpoint count reduced accordingly.

---

## Section B: NWP-Specific Test Procedure

### NWP Endpoint Topology
```python
# NWP: 2 CBBs, 1 IMH → reduced endpoint count vs DMR
# CBB endpoints: sv.socket0.cbb[0:2].punit.* PMSB/GPSB endpoints
# IMH endpoints: sv.socket0.imh0.punit.* PMSB/GPSB endpoints
for cbb_idx in range(2):  # NWP: 2 CBBs (not 4)
    cbb = sv.socket0.cbb[cbb_idx]
    # trigger PMSB/GPSB sideband traffic on this CBB

# IMH (single on NWP)
imh = sv.socket0.imh0
# trigger PMSB/GPSB sideband traffic on IMH
```

### Steps
| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enumerate all PMSB endpoints per CBB | 2 CBBs |
| 2 | Enumerate all GPSB endpoints per CBB | 2 CBBs |
| 3 | Run sideband harasser on each endpoint | PythonSv stress |
| 4 | Repeat for IMH0 | Single IMH |
| 5 | Verify no endpoint errors | No timeout, no MCA |

### Pass Criteria
- All PMSB/GPSB endpoints respond without timeout
- No sideband errors across all 3 dies (2 CBBs + 1 IMH)
- System stable after sweep

---

## Section F: Recommendation

**Recommendation: ADOPT — NWP topology: 2 CBBs + 1 IMH (reduced from DMR's 4+2); adapt endpoint enumeration; PythonSv sideband harasser same**

**Priority**: Medium — Critical for sideband infrastructure health check on NWP
