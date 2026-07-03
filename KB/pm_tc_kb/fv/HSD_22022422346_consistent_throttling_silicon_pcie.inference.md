# Deep Analysis: Consistent Throttling Silicon PCIE

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422346 |
| **Title** | Consistent throttling_silicon_PCIE |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Quality |
| **Sub-Feature** | PEM — consistent 1-minute throttle, measured via PCIe interface |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same as TC 22022422343 but reads PEM counter via **PCIe interface** instead of I3C. Tests the PCIe telemetry path for PEM data accuracy.

Tags: `New_Content`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python telemetryAPIs.py  # PEM telemetry via PCIe interface
```

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable PEM through TPMI | Same as I3C variant |
| 2 | Enforce 1-minute continuous throttle | Same throttle injection |
| 3 | Read PEM counters via **PCIe interface** | PCIe telemetry path |
| 4 | Verify: `LPF ramp + PEM counter ≈ 1 min` | ±10% tolerance |

### Pass Criteria
- Same formula: LPF ramp + PEM counter ≈ 60 seconds
- PCIe telemetry path returns accurate PEM data

---

## Section F: Recommendation

**Recommendation: ADOPT — PCIe interface for PEM data; same throttle injection methodology; verify PCIe telemetry path configured for NWP**

**Priority**: Medium — `New_Content`; PCIe telemetry path for PEM accuracy
