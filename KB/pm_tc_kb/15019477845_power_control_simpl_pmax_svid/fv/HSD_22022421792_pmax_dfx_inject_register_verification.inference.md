# Deep Analysis: PMAX DFX INJECT Register Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421792 |
| **Title** | [Silicon Only] PMAX DFX INJECT Register Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PMAX DFX injection — TAP-based spoof of FTPmaxDetect wire to Punit (fast threshold wire 0/1) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

The `PMAX_DFX_DETECT_INJECT` uCR provides TAP-based injection to spoof `FTPmaxDetectXXnnnH[0]` and `[1]` pulses (Fast Threshold PMAX wires). This is a DFX hook for low-level PMAX trigger simulation independent of external hardware.

Command: `pmax_pmx.py` (dedicated PMAX PMx script).

Tags: `plc.feature.p2`, `NGA_MAIN`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python pmax_pmx.py  # dedicated PMAX PMx script
```

### DFX Inject Flow

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Access `PMAX_DFX_DETECT_INJECT` uCR via TAP/GPSB | TAP network access |
| 2 | Spoof `FTPmaxDetectXXnnnH[0]` pulse (wire 0) | 100ns PMAX event |
| 3 | Verify Punit sees PMAX event via wire 0 | `pmax_log` in `package_therm_status` |
| 4 | Clear inject | `pmax_log` clears |
| 5 | Spoof `FTPmaxDetectXXnnnH[1]` pulse (wire 1) | Test second fast threshold wire |
| 6 | Verify Punit response to wire 1 | Same throttle response |

### NWP Note
- `PMAX_DFX_DETECT_INJECT` uCR accessed via NWP TAP network
- NWP single IMH0 — no IMH1 fast threshold wires

### Pass Criteria
- DFX inject via both wires triggers Punit PMAX response
- 100ns pulse duration spoofed correctly
- `pmax_log` reflects each injection
- `pmax_pmx.py` DFX inject test passes

---

## Section F: Recommendation

**Recommendation: ADOPT — NWP TAP access same; single IMH0 (no IMH1 DFX wires); `pmax_pmx.py` needs NWP target verification**

**Priority**: High — `NGA_MAIN`, `plc.feature.p2`; DFX inject is the primary PMAX verification mechanism in post-silicon test environments without external PMAX hardware
