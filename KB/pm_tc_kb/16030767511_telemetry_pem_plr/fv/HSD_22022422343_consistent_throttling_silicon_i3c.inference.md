# Deep Analysis: Consistent Throttling Silicon I3C

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422343 |
| **Title** | Consistent throttling_silicon_I3C |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Quality |
| **Sub-Feature** | PEM (Power Event Monitor) — consistent 1-minute throttle, measured via I3C interface |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PEM (Power Event Monitor) tracks throttling events via telemetry. This test verifies that 1 minute of continuous throttle is accurately captured by PEM counters via the **I3C interface** (BMC ↔ CPU I3C bus). PEM is functional on NWP.

Test formula: `Total time = LPF ramp + PEM counter captured time ≈ 1 minute`

Tags: `Ready_for_testing`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python telemetryAPIs.py  # PEM telemetry via I3C interface
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable PEM through TPMI | `pem_control` via TPMI |
| 2 | Enforce continuous throttle for 1 minute | PROCHOT inject or RAPL PL1 low |
| 3 | Verify no gaps in throttle | Continuous 60-second throttle event |
| 4 | Read PEM counters via **I3C interface** | BMC → I3C → CPU telemetry |
| 5 | Verify: `LPF ramp + PEM counter ≈ 1 min` | ±10% tolerance |
| 6 | BMC setup required | LPF ramp calculation from thermal team |

### NWP Notes
- I3C interface to BMC: same on NWP (single-socket)
- PEM via `sv.socket0.imh0.*` TPMI

### Pass Criteria
- Total time (LPF ramp + PEM counter) ≈ 60 seconds (±10%)
- No throttle gaps detected in 1-minute window
- I3C telemetry path functional for PEM data

---

## Section F: Recommendation

**Recommendation: ADOPT — `telemetryAPIs.py` NWP configuration; I3C interface same; BMC setup required; PEM functional on NWP**

**Priority**: High — `Ready_for_testing`; PEM accuracy is a Quality gate for throttling telemetry correctness
