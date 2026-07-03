# Deep Analysis: [GPIO Interface] Verify XX_PROCHOT_N Input Pin Assertion

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421484 |
| **Title** | [GPIO Interface] Verify XX_PROCHOT_N input pin assertion |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > GPIO Interface (PROCHOT) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that when the platform asserts `XX_PROCHOT_N` (processor hot input pin, active low), the CPU correctly detects the assertion and applies the PROCHOT response power (a BIOS-programmed power limit that forces the CPU to operate at a maximum capped power level). Platform PROCHOT is used when the platform power delivery is thermally stressed. On NWP, the platform PROCHOT input pin is supported. The primary adaptation is confirming NWP board header access for manual pin assertion and NWP-specific PROCHOT response power register paths.

**Key Justification:**
- `XX_PROCHOT_N` input pin detection and response power application is present on NWP
- `ENABLE_XXPROCHOT_N_FUSE` = 1 (from TC 22022421480)
- `NGA_MAIN` tag: silicon test; board header flip required for pin assertion
- Test steps reference flipping a board header (confirmed manual test methodology)

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon platform with accessible `XX_PROCHOT_N` pin on board header
- `ENABLE_XXPROCHOT_N_FUSE` = 1 on `imh0`
- BIOS has programmed PROCHOT response power (via `POWER_CTL[PROCHOT_RESPONSE_RATIO]` or TPMI)
- PythonSv access to `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms`

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Confirm `ENABLE_XXPROCHOT_N_FUSE` = 1 and PROCHOT response power programmed | Same; NWP single IMH |
| 2 | Read baseline PROCHOT response power setting | `ptpcfsms.power_ctl1.prochot_response_ratio` on NWP |
| 3 | Flip board header to assert `XX_PROCHOT_N` (pin goes low) | NWP board header location — confirm with platform team |
| 4 | Verify CPU detects assertion: read `PTPCFSMS_GPIO_BUMP_STATUS[PROCHOT_N_STATUS]` | NWP PTPCFSMS register |
| 5 | Verify CPU applies PROCHOT response: package power limited to PROCHOT response power | Read package power limit via TPMI/MSR |
| 6 | Verify `IA32_PACKAGE_THERM_STATUS.PROCHOT_EVENT` and `PROCHOT_LOG` set | Same package MSR |
| 7 | De-assert by flipping header back; verify PROCHOT clears | Same |

### NWP Pass Criteria
- `XX_PROCHOT_N` assertion detected by Pcode
- Package power capped to PROCHOT response power level
- `PROCHOT_EVENT` = 1 in `IA32_PACKAGE_THERM_STATUS` during assertion
- Response power applied within specification (~1 slow-loop cycle, ~1ms)

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| PROCHOT response power | BIOS-programmed power cap | Same mechanism on NWP | Verify NWP PROCHOT response power register |
| Board header | OKS/DMR board specific | NWP AvenueCity board specific | Confirm header location |
| IMH scope | Multi-IMH | Single `imh0` | Simpler register monitoring |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms

# PROCHOT status and response
try:
    prochot_status = ptpcfsms.gpio_bump_status.xxprochot_n_status.read()
    print(f"PROCHOT_N input status: {prochot_status} (0=asserted)")
except Exception as e:
    print(f"PROCHOT status: {e}")

# Package PLR - PROCHOT bit
plr = ptpcfsms.perf_limit_reasons.read()
print(f"Package PLR: 0x{plr:08X}")

# PROCHOT response power setting
try:
    power_ctl = ptpcfsms.power_ctl1.read()
    prochot_ratio = ptpcfsms.power_ctl1.prochot_response_ratio.read()
    print(f"PROCHOT response ratio: {prochot_ratio}")
except Exception as e:
    print(f"POWER_CTL1: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **Board header access** — NWP AvenueCity platform must provide header to assert PROCHOT_N; confirm with platform team | High | Required before test execution |
| 2 | **PROCHOT response power** — NWP PROCHOT response power may be a different register than DMR | Low | Check NWP PM HAS PROCHOT section |

---

## Section F: Recommendation

**Recommendation: ADAPT — board header verification + NGA_MAIN priority**

PROCHOT input detection and response is architecturally the same on NWP. Primary adaptation: confirm board header and NWP PROCHOT response power register path.

Required adaptations:
1. Confirm NWP AvenueCity board PROCHOT_N header location
2. Verify NWP PROCHOT response power register path in PTPCFSMS namednodes
3. Update test step 3 with NWP board instructions

**Priority**: High — NGA_MAIN; platform PROCHOT is a key power/thermal safety mechanism
