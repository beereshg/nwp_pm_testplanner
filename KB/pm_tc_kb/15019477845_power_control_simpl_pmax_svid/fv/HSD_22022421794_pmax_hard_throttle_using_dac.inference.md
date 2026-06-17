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
