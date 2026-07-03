# Deep Analysis: MSR 0xB2 TURBO_CONFIG

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422395 |
| **Title** | MSR 0xB2 TURBO_CONFIG |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | MSR 0xB2 turbo config register; ITD (Intel Turbo Differentiation) offset |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **MSR 0xB2** (TURBO_CONFIG register), including:
- Expected value = 0x2 for DMR — **NWP expected value may differ**
- ITD (Intel Turbo Differentiation) offset: calculated offset must = 0 after disabling ITD

The test is DMR-specific in the expected value (0x2). On NWP, the MSR 0xB2 register exists but the expected value must be determined from NWP spec/HAS.

**Key Justification:**
- MSR 0xB2 present on NWP (standard Pstate register)
- `Ready_for_testing` + `plc.feature.p1` + `PMSS_NWP_READINESS_CHECK` tags
- Expected value requires NWP-specific validation

---

## Section B: NWP-Specific Test Procedure

### MSR 0xB2 Fields

| Bit | Field | Description |
|-----|-------|-------------|
| [7:0] | Package Turbo Ratio Limit | P0n ratio at turbo |
| [15:8] | Group 1 Turbo Ratio Limit | Multi-core turbo |
| [63:32] | ITD fields | Intel Turbo Differentiation |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read MSR 0xB2 baseline | `rdmsr 0xB2` or `baseaccess.rdmsr(0xB2)` |
| 2 | Verify baseline value matches NWP spec | Expected value TBD (DMR = 0x2) |
| 3 | Disable ITD (`EETurboDisable` BIOS knob) | Set EETurboDisable = 1 |
| 4 | Verify ITD offset = 0 in MSR 0xB2 | ITD offset bits clear |
| 5 | Run turbo PMx | `python runPmx.py -x nwp.xml -p turbo -tM 60` |

### NWP Pass Criteria
- MSR 0xB2 value matches NWP specification (verify from HAS)
- ITD offset = 0 after `EETurboDisable`
- Turbo PMx passes with MSR 0xB2 configuration

---

## Section F: Recommendation

**Recommendation: ADOPT with NWP calibration — verify expected MSR 0xB2 value from NWP spec**

Required adaptations:
1. `python runPmx.py -x nwp.xml -p turbo -tM 60`
2. Query NWP HAS/spec for MSR 0xB2 expected value (may differ from DMR = 0x2)
3. Verify ITD feature availability on NWP (ITD may be EE/performance-tuning feature)

**Priority**: Medium — `plc.feature.p1`; MSR 0xB2 turbo config bring-up check
