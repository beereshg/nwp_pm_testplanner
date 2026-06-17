# Deep Analysis: [GPIO Interface] Verify XX_MEMHOT_IN_N Input Pin Assertion

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421481 |
| **Title** | [GPIO Interface] Verify XX_MEMHOT_IN_N input pin assertion |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > GPIO Interface |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that when the platform asserts `XX_MEMHOT_IN_N` (memory hot input pin, active low), the CPU correctly detects the assertion and triggers the appropriate memory hot response. `XX_MEMHOT_IN_N` is a single package-level input pin used by the platform to signal that memory temperature is hot. On NWP, this GPIO thermal input pin is supported. The primary adaptation is confirming that the NWP board/platform has the necessary jumper/header infrastructure to assert this pin manually (as was done on OKS/DMR boards) and that the NWP-specific `flexcon_pm` or debug script is adapted for NWP.

**Key Justification:**
- `XX_MEMHOT_IN_N` input pin is a platform-level thermal GPIO present on NWP
- CPU Pcode response to MEMHOT_IN assertion (reduce memory bandwidth/frequency) is the same
- `NGA_MAIN` tag: prioritize for NGA silicon automation; requires board-level infrastructure
- Board header/jumper to assert MEMHOT_IN_N manually must be available on NWP validation platform

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon platform with accessible `XX_MEMHOT_IN_N` pin on board header
- PythonSv access to `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms`
- Platform BIOS has `ENABLE_XXMEMHOT_IN_N_FUSE` = 1 (verified in TC 22022421480)

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Confirm BIOS has MEMHOT_IN enabled (`ENABLE_XXMEMHOT_IN_N_FUSE` = 1 on `imh0`) | Same fuse check; NWP single IMH |
| 2 | Assert `XX_MEMHOT_IN_N` via board jumper/header or test infrastructure | Same board-level action; confirm NWP board has this header |
| 3 | Verify CPU detects assertion: read `PTPCFSMS_GPIO_BUMP_STATUS` or equivalent | NWP namednodes path needs validation |
| 4 | Verify Pcode response: memory bandwidth/frequency throttled (MEMHOT response power applied) | Same acceptance criterion |
| 5 | Verify `IA32_PACKAGE_THERM_STATUS.MEMHOT` bit set | Same package MSR |
| 6 | De-assert `XX_MEMHOT_IN_N`; verify response clears | Same |

### NWP Pass Criteria
- Asserting `XX_MEMHOT_IN_N` (low) detected by Pcode → memory throttle applied
- `IA32_PACKAGE_THERM_STATUS.MEMHOT` = 1 during assertion
- Throttle clears when pin de-asserted

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Pin scope | Package-level input | Same on NWP | No change |
| Board header availability | OKS/DMR board had header | NWP AvenueCity board | Confirm NWP board provides MEMHOT_IN_N access |
| Debug script | `diamondrapids_flexcon` | NWP variant needed | Adapt or use direct PythonSv |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
# Check MEMHOT_IN_N status on NWP
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms

try:
    # GPIO bump status register (check MEMHOT_IN assertion)
    gpio_status = ptpcfsms.gpio_bump_status.read()
    print(f"GPIO_BUMP_STATUS: 0x{gpio_status:08X}")
    memhot_in = ptpcfsms.gpio_bump_status.xxmemhot_in_n_status.read()
    print(f"MEMHOT_IN_N status: {memhot_in} (0=asserted)")
except Exception as e:
    print(f"GPIO status: {e}")

# Package thermal status
# IA32_PACKAGE_THERM_STATUS (MSR 0x1B1) MEMHOT bit
# Use MSR read tool: rdmsr -p 0 0x1B1
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **Board infrastructure required** — manually asserting MEMHOT_IN_N requires board jumper; NWP validation platform must provide this | High | Coordinate with platform team; required before NGA automation |
| 2 | **Automated assertion** — NGA automation may need a relay or test board to assert GPIO; manual execution first | Medium | Plan manual first; NGA automation needs HW support |

---

## Section F: Recommendation

**Recommendation: ADAPT — board infrastructure verification needed; NGA_MAIN priority**

Pin assertion mechanics are the same on NWP. Confirm NWP board has accessible MEMHOT_IN_N header/jumper. High NGA priority.

Required adaptations:
1. Confirm NWP AvenueCity board MEMHOT_IN_N pin accessibility
2. Adapt debug script for NWP namednodes path
3. For NGA: coordinate with platform team for automated GPIO assertion

**Priority**: High — NGA_MAIN; GPIO thermal input is foundational platform-CPU thermal interface
