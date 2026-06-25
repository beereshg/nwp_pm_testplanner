# Deep Analysis: PMAX Hard Throttle using DAC

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421794 |
| **Title** | [Silicon Only] PMAX Hard Throttle using DAC |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PMAX hard throttle via DAC code — verify trigger count registers and throttle mechanism |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify PMAX hard throttle triggered via DAC code correctly increments `pmax_status6.mt0_cbb_trig_count` and fires hard throttle. The DAC provides analog VccIN droop simulation independent of the digital inject path. `NGA_MAIN` priority. NWP: single IMH0. Note: DAC register paths are WIP in source TC.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Silicon setup | DAC hardware or equivalent analog inject available |
| SV session | `sv.socket0.imh0` and `sv.socket0.imh0.pmax.pmax0` reachable |
| PMx script | `python pmax_pmx.py` available |
| Baseline | `pmax_log = 0`; `mt0_cbb_trig_count = 0` before test |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read baseline state. `pmax_log = sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read(); trig = sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read(); assert pmax_log == 0` | pmax_log = 0; read trig_count baseline | pmax_log = 1 — clear state before test |
| 2 | Trigger PMAX via DAC code (external DAC hardware; set VccIN droop code to exceed Vtrip 0 threshold). | DAC code accepted; hardware generates analog droop | DAC setup fails — verify DAC board connected |
| 3 | Verify `pmax_log` and trig_count increment. `import time; time.sleep(0.5); pmax_log = sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read(); trig2 = sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read(); assert pmax_log == 1; assert trig2 > trig` | pmax_log = 1; mt0_cbb_trig_count incremented | pmax_log = 0 or trig_count unchanged — DAC not triggering PMAX |
| 4 | Remove DAC code; verify recovery. | pmax_log returns to 0; system stable | Stuck pmax_log — stale semaphore |

---

### Pass / Fail Criteria

- **PASS**: DAC trigger fires hard throttle; `pmax_log = 1`; `mt0_cbb_trig_count` increments; system stable; clean recovery.
- **FAIL**: No throttle from DAC; trig_count not incrementing; stuck state.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| pmax_log | sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log | = 1 during DAC trigger |
| mt0_cbb_trig_count | sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count | Increments on each DAC PMAX event |

---

### Post-Process

Remove DAC code. Clear PMAX state if stuck. Collect register dump on failure.

---

### References

- [DMR PMax Detector HAS](https://docs.intel.com/documents/arch_datacenter/pmax/dmr/dmr_pmax_detector_has/dmr_pmax_detector_has.html) — DAC trigger path; mt0_cbb_trig_count register
- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — hard throttle via analog droop

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test uses the DAC (Digital-to-Analog Converter) code to trigger PMAX. The test verifies `pmax_status6.mt0_cbb_trig_count` and related trigger count registers.

*Note*: The source TC has a placeholder "Need to find equivalent tap registers for DMR" — this was a work-in-progress even on DMR. The NWP version should use the same approach with IMH0 registers only.

Command: `pmax_pmx.py`.

Tags: `plc.feature.p2`, `NGA_MAIN`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python pmax_pmx.py
```

### NWP DAC Throttle Verification
```python
# NWP: verify PMAX trigger via DAC
# 1. Verify pmax_log starts at 0
pmax_log = sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read()
assert pmax_log == 0, "pmax_log should be 0 initially"

# 2. Check trigger count registers
trig_count = sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read()
print(f"Initial trig_count: {trig_count}")

# 3. If trig_count != 0, clear via TAP register (NWP equivalent)
# Note: NWP TAP register path for trigger count clear — verify with HAS

# 4. Trigger PMAX via DAC code (external DAC hardware required)
# Verify pmax_log sets after DAC trigger
```

### Pass Criteria
- `pmax_log` = 0 before inject
- `mt0_cbb_trig_count` increments on PMAX trigger
- Hard throttle fires after DAC code exceeds threshold
- System stable during DAC-triggered PMAX

---

## Section F: Recommendation

**Recommendation: ADOPT WITH CAUTION — Source TC has TBD placeholder for TAP registers; NWP TAP register path for trigger count clear must be verified against NWP HAS; single IMH0 only**

**Priority**: Medium — `NGA_MAIN`, `plc.feature.p2`; DAC-based trigger is the most realistic PMAX test scenario (closest to real hardware behavior)
