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

### Test Case Intent

Verify `PMAX_DFX_DETECT_INJECT` uCR provides valid TAP-based injection to spoof `FTPmaxDetectXXnnnH[0]` and `[1]` pulses (100 ns PMAX events) and that Punit correctly responds to each wire. Provides low-level PMAX trigger simulation independent of external hardware. NWP: single IMH0. `NGA_MAIN` priority.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| TAP access | DFX TAP/GPSB network accessible for PMAX_DFX_DETECT_INJECT uCR |
| SV session | `sv.socket0.imh0` reachable |
| PMx script | `python pmax_pmx.py` available |
| pmax_log baseline | Read and confirm = 0 before inject |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Verify pmax_log = 0 baseline. `pmax_log = sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read(); assert pmax_log == 0` | pmax_log = 0 | pmax_log = 1 — clear residual PMAX state first |
| 2 | Inject wire 0 via PMAX_DFX_DETECT_INJECT uCR (100 ns pulse on FTPmaxDetectXXnnnH[0]). Verify Punit response. `import time; # inject wire 0 via TAP; time.sleep(0.1); pmax_log = sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read(); assert pmax_log == 1` | pmax_log = 1 after wire 0 inject | pmax_log = 0 — wire 0 inject not reaching Punit |
| 3 | Clear wire 0 inject; verify pmax_log clears. | pmax_log = 0 | pmax_log stuck — stale PMAX state |
| 4 | Inject wire 1 (FTPmaxDetectXXnnnH[1]); verify same response. | pmax_log = 1 during wire 1 inject | Wire 1 not triggering Punit |
| 5 | Run `pmax_pmx.py` DFX inject test. `python pmax_pmx.py` | PMx PASS | PMx FAIL — collect run log |

---

### Pass / Fail Criteria

- **PASS**: Both wire 0 and wire 1 injections trigger `pmax_log = 1`; both clear cleanly; `pmax_pmx.py` PASS.
- **FAIL**: Either wire does not trigger Punit; pmax_log stuck after clear.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| pmax_log | sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log | = 1 during each wire inject; = 0 after clear |
| PMAX_DFX_DETECT_INJECT | TAP network uCR | Write succeeds; 100ns pulse generated |

---

### Post-Process

Clear all inject states. Verify pmax_log = 0 after test.

---

### References

- [DMR PMax Detector HAS](https://docs.intel.com/documents/arch_datacenter/pmax/dmr/dmr_pmax_detector_has/dmr_pmax_detector_has.html) — PMAX_DFX_DETECT_INJECT uCR; FTPmaxDetect wire spoof; 100ns pulse
- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — DFX fast threshold wires

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
