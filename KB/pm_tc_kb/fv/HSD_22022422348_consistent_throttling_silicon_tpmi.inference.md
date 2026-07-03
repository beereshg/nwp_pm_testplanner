# Deep Analysis: Consistent Throttling Silicon TPMI

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422348 |
| **Title** | Consistent throttling_silicon_TPMI |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Quality |
| **Sub-Feature** | PEM — consistent 1-minute throttle, measured via TPMI interface |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same as TC 22022422343 but reads PEM counter via **TPMI interface** directly. TPMI is the primary in-band interface for PEM on NWP.

Tags: `New_Content`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python telemetryAPIs.py  # PEM telemetry via TPMI
```

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable PEM through TPMI | `pem_control` register |
| 2 | Enforce 1-minute continuous throttle | PROCHOT/RAPL inject |
| 3 | Read PEM counters via **TPMI** | In-band TPMI read |
| 4 | Verify: `LPF ramp + PEM counter ≈ 1 min` | ±10% tolerance |

### Pass Criteria
- Same formula; TPMI in-band path returns accurate PEM counter data

---

## Section F: Recommendation

**Recommendation: ADOPT — TPMI in-band PEM access; primary interface for NWP in-band telemetry; MSR deprecated → TPMI only**

**Priority**: High — `New_Content`; TPMI is the primary PEM interface on NWP (MSR-based access deprecated)
