# Deep Analysis: CStates C1 residency counter

| Field | Value |
|-------|-------|
| **HSD ID** | 14020416782 |
| **Title** | CStates C1 residency counter |
| **Date** | 2026-05-27 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Core C-States |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

C1/C1E residency counters are supported on NWP with the same per-core MSR interface (0x778). The test requires only CBB/core count adaptation (2 CBBs × 48 cores = 96 total).

### Test Intent

Verify that the per-core C1 residency counter (MSR 0x778, `CC1_RESIDENCY`) increments monotonically when cores are placed in the C1 (halt) or C1E (enhanced halt) state. The test exercises C1 dwell via the MWAIT instruction (EAX[7:4]=0x0, sub-state=0x0 for C1; sub-state=0x1 for C1E) and reads back the residency counter before and after to confirm positive increment. On NWP, C1 and C1E are fully supported. The test uses `pm.focused.cstate_focus` module and measures KPI thresholds (minimum expected C1 residency percentage during idle). All 96 cores (2 CBBs × 48) must show increasing counters when placed in C1 state.

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon or VP at boot-complete with minimal background load
- PythonSv + namednodes accessible
- `pm.focused.cstate_focus` module available

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Read baseline CC1 counter (MSR 0x778) per-core | 2 CBBs × 48 cores = 96 reads |
| 2 | Trigger C1 dwell (OS idle or explicit MWAIT C1) | Same stimulus; applies to all 96 cores |
| 3 | Wait defined dwell period (e.g., 1 second) | Same timing |
| 4 | Re-read CC1 counter on all cores | Verify positive delta on all 96 cores |
| 5 | Verify C1E residency also captured (sub-state 1) | Check with C1E enabled (POWER_CTL1.C1E_ENABLE=1) |
| 6 | Confirm C6 residency NOT inflated (cores stayed in C1) | CC6 counter (MSR 0x3FD) should not increase significantly |

### NWP Pass Criteria
- CC1 residency counter (MSR 0x778) increases on all 96 cores after C1 dwell
- C1 residency KPI threshold met (expected percentage configured in test plan)
- CC6 counter stays low during C1-only dwell sequence
- No core shows CC1 = 0 after a sustained idle period

---

## Section C: NWP Delta Impact Analysis

### Core Count

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Total cores | Up to 256 | **96** | Smaller sample; all cores must still pass |
| CBB count | Up to 4 | **2** | `range(4)` → `range(2)` |
| Cores per CBB | 64 | **48** | `range(64)` → `range(48)` |
| C1 / C1E support | Yes | **Yes** | No change |

---

## Section D: Key Registers & Validation Points

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| C1 Residency | MSR 0x778 (`CC1_RESIDENCY`) | full 64-bit | Monotonic increase | Per-core, 96 cores |
| C1E Enable | MSR 0x1FC (`POWER_CTL1`) | bit[1] | 1 (enabled for C1E sub-test) | Package |
| C6 Residency | MSR 0x3FD (`CC6_RESIDENCY`) | full | Minimal increase during C1 dwell | Per-core |

### PythonSv Validation Commands (NWP)

```python
import time

before_cc1 = {}
for cbb_idx in range(2):    # NWP: 2 CBBs
    for core_idx in range(48):  # NWP: 48 cores/CBB
        cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
        before_cc1[(cbb_idx, core_idx)] = cbb.core[core_idx].read_msr(0x778)

time.sleep(2)   # Dwell period

fails = 0
for cbb_idx in range(2):
    for core_idx in range(48):
        cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
        after = cbb.core[core_idx].read_msr(0x778)
        delta = after - before_cc1[(cbb_idx, core_idx)]
        if delta == 0:
            print(f"WARN: CBB{cbb_idx} Core{core_idx} CC1 did not increment")
            fails += 1

print(f"C1 residency check complete. Failures: {fails}/96")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **Background load** — any active core prevents C1 dwell | Medium | Ensure minimal OS activity during test |
| 2 | **C1E vs C1** — test should cover both sub-states separately | Low | Run with C1E enabled and disabled |
| 3 | **KPI threshold** — NWP C1 residency threshold may differ from DMR | Low | Calibrate for 96-core NWP topology |

---

## Section F: Recommendation

**Recommendation: ADOPT — Trivial adaptation needed (loop bounds only).**

C1 residency counter test runs directly on NWP. Only change needed is core/CBB loop bounds.

Required adaptations:
1. `range(4)` → `range(2)` for CBBs; `range(64)` → `range(48)` for cores
2. Update KPI threshold to NWP-appropriate value

**Priority**: High — C1 residency is a fundamental bring-up validation checkpoint.
