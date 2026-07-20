# Deep Analysis: [GPIO Interface] Verify XX_THERMTRIP_N Input/Output Pin Assertion

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421485 |
| **Title** | [GPIO Interface] Verify XX_THERMTRIP_N input/output pin assertion |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > GPIO Interface (ThermTrip) |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates the THERMTRIP_N bidirectional assertion and cross-die wire-OR scenario defined in [TCD 16031170071 -- MEMTRIP/THERMTRIP Package Signaling](https://hsdes.intel.com/appstore/article-one/#/16031170071) S5. Environment: NWP post-silicon, FV.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the `XX_THERMTRIP_N` bidirectional GPIO pin — both as an **output** (CPU asserts to platform when catastrophic internal thermal runaway occurs) and as an **input** (platform asserts to CPU when external component trips catastrophic thermal shutdown). ThermTrip is the last-resort thermal safety mechanism: it causes immediate CPU shutdown. On NWP, the bidirectional ThermTrip GPIO is supported. Testing the output direction requires carefully triggering an internal thermtrip condition (typically via fuse override or simulated temp injection); testing the input direction requires asserting the pin from the platform side via board header.

**Key Justification:**
- `XX_THERMTRIP_N` bidirectional pin is present on NWP; ThermTrip is a silicon safety feature
- Output: CPU asserts when DTS exceeds `TJ_MAX + 10°C` or HW thermtrip threshold
- Input: platform asserts → CPU immediately asserts shutdown response
- `NGA_MAIN` tag: silicon test; extreme caution required due to system shutdown impact
- ThermTrip causes immediate power shutdown — test requires controlled infrastructure

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon platform with `XX_THERMTRIP_N` pin observable and assertable from platform side
- Controlled thermal injection capability (VP preferred for output-direction test)
- Platform power infrastructure supports controlled shutdown and restart

### Adapted Test Steps — Output Direction (CPU → Platform)

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | (VP only) Inject temperature above ThermTrip threshold | Use VP thermal injection; do NOT attempt on live silicon with real DIMMs |
| 2 | Verify `XX_THERMTRIP_N` output asserts (pin goes low) | Board measurement; NWP platform |
| 3 | Verify system powers off (ThermTrip causes immediate shutdown) | Same; verify via platform BMC or power sequencer log |
| 4 | System restart and verify ThermTrip log bit set | NWP log path |

### Adapted Test Steps — Input Direction (Platform → CPU)

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Assert `XX_THERMTRIP_N` from platform side via board header (shorting to GND) | NWP board header — confirm with platform team |
| 2 | Verify CPU responds: immediate shutdown/reset | Same; verify via BMC platform event log |
| 3 | Power cycle and verify recovery | Same |

### NWP Pass Criteria
- **Output**: CPU asserts `THERMTRIP_N` on catastrophic thermal event → platform powers off
- **Input**: Platform assertion → CPU enters immediate shutdown response
- System recovers cleanly after ThermTrip event
- ThermTrip event logged in platform event log

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Pin type | Bidirectional | Same on NWP | No change |
| ThermTrip threshold | `TJ_MAX + 10°C` (DMR) | NWP-specific; may vary by 1-2°C | Verify from NWP PM HAS |
| Board infrastructure | OKS board header | NWP AvenueCity board | Confirm header location |
| IMH count | Multiple | Single | Simpler — only imh0 thermtrip path |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms

# ThermTrip status (if readable after event, before full shutdown)
try:
    thermtrip_status = ptpcfsms.gpio_bump_status.xxthermtrip_n_status.read()
    print(f"THERMTRIP_N status: {thermtrip_status}")
except Exception as e:
    print(f"ThermTrip status: {e}")

# Note: Full ThermTrip causes system shutdown; post-event analysis via BMC SEL log
# BMC: ipmitool sel list | grep -i thermal
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **System shutdown required** — ThermTrip causes immediate shutdown; test disrupts the system; requires controlled lab environment | High | Run in isolated lab session with full system restart plan |
| 2 | **VP strongly preferred for output-direction** — triggering real thermtrip on silicon risks DIMM/board damage if infrastructure fails | High | Use VP for output; silicon for input direction only |
| 3 | **Board header location** — NWP AvenueCity board THERMTRIP_N header must be confirmed | Medium | Coordinate with platform team |

---

## Section F: Recommendation

**Recommendation: ADAPT — extreme safety precautions; NGA_MAIN priority**

ThermTrip is architecturally the same on NWP. The output-direction test is best done on VP; the input-direction test requires silicon with controlled board infrastructure. Both require system restart capability in the test harness.

Required adaptations:
1. Use VP for output-direction (CPU → platform) ThermTrip test
2. Confirm NWP board THERMTRIP_N header for input-direction test
3. Ensure NGA automation includes automatic power cycle/restart after event

**Priority**: High — NGA_MAIN; ThermTrip is the last-resort thermal safety validation
