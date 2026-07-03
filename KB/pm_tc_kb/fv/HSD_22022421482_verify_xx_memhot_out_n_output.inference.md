# Deep Analysis: [GPIO Interface] Verify XX_MEMHOT_OUT_N Output Pin Assertion

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421482 |
| **Title** | [GPIO Interface] Verify XX_MEMHOT_OUT_N output pin assertion |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > GPIO Interface |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that `XX_MEMHOT_OUT_N` (memory hot output pin, active low) is correctly asserted by the CPU when memory temperature exceeds the MemHot threshold. This output pin signals to the platform that memory is running hot. On NWP, the MemHot output GPIO is supported. The verification requires triggering a real memory thermal event (or BIOS-injected memory temperature crossing) and observing the pin assertion at the board level, combined with software-readable status registers.

**Key Justification:**
- `XX_MEMHOT_OUT_N` output pin assertion by Pcode is present on NWP
- `ENABLE_XXMEMHOT_OUT_N_FUSE` = 1 (prerequisite from TC 22022421480)
- `NGA_MAIN` tag: requires silicon-level test with board measurement capability
- NWP single IMH: monitoring is simpler than DMR's multi-IMH; same pin response logic

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon platform with board-level MEMHOT_OUT_N pin observable (oscilloscope or test point)
- Memory thermal threshold (MemHot threshold) is programmable or BIOS-injectable
- `ENABLE_XXMEMHOT_OUT_N_FUSE` = 1 on `imh0`

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Confirm fuse: `ENABLE_XXMEMHOT_OUT_N_FUSE` = 1 on `imh0` | Single IMH on NWP |
| 2 | Set up DIMM temperature monitoring | Same setup; NWP memory topology |
| 3 | Trigger MemHot condition: either heat DIMM above threshold or inject thermal status | Same triggering mechanism |
| 4 | Verify `XX_MEMHOT_OUT_N` asserts (pin goes low) at board level | Same board measurement; NWP platform test point |
| 5 | Verify `PTPCFSMS_GPIO_BUMP_STATUS[XXMEMHOT_OUT_N_STATUS]` reflects asserted state | NWP PTPCFSMS register path |
| 6 | Reduce DIMM temperature below threshold; verify pin de-asserts | Same |

### NWP Pass Criteria
- When DIMM temp exceeds MemHot threshold: `XX_MEMHOT_OUT_N` asserts (pin = low)
- Software-readable status register reflects assertion
- Pin de-asserts when DIMM temp drops below threshold

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Pin scope | Package-level output | Same on NWP | No change |
| IMH count | Multiple | Single | Simpler; only imh0 monitors DIMM temp |
| DIMM topology | DDR5 channels | NWP DDR5/HBM depending on config | Verify MemHot threshold and channel config |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
# Check MEMHOT_OUT_N status on NWP
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms

try:
    gpio_status = ptpcfsms.gpio_bump_status.read()
    memhot_out = ptpcfsms.gpio_bump_status.xxmemhot_out_n_status.read()
    print(f"MEMHOT_OUT_N status: {memhot_out} (0=asserted/hot)")
except Exception as e:
    print(f"GPIO status: {e}")

# MemHot threshold
try:
    memhot_thresh = ptpcfsms.memhot_control.read()
    print(f"MemHot control: 0x{memhot_thresh:08X}")
except Exception as e:
    print(f"MemHot control: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **Board test point for MEMHOT_OUT_N** — requires board-level probing or automated pin detection infrastructure | High | Coordinate with platform team |
| 2 | **NWP memory topology** — MemHot threshold and triggering may differ based on NWP DIMM config (DDR5 vs. HBM) | Medium | Verify NWP memory channel config before test |

---

## Section F: Recommendation

**Recommendation: ADAPT — board test point infrastructure required; NGA_MAIN priority**

Same mechanism as DMR. Board test point verification required. Primary adaptation is NWP single-IMH scope.

Required adaptations:
1. Confirm NWP board provides MEMHOT_OUT_N test point or automated detection
2. Verify NWP MemHot threshold register path
3. Single IMH scope: `sv.socket0.imh0` only

**Priority**: High — NGA_MAIN; platform thermal signaling foundational test
