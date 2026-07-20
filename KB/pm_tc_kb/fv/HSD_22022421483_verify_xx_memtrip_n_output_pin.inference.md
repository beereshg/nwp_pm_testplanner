# Deep Analysis: [GPIO Interface] Verify XX_MEMTRIP_N Output Pin Assertion

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421483 |
| **Title** | [GPIO Interface] Verify XX_MEMTRIP_N output pin assertion |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > GPIO Interface |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates the MEMTRIP_N output assertion on catastrophic memory temp scenario defined in [TCD 16031170071 -- MEMTRIP/THERMTRIP Package Signaling](https://hsdes.intel.com/appstore/article-one/#/16031170071) S5. Environment: NWP post-silicon, FV.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that `XX_MEMTRIP_N` (memory trip output pin, active low) is correctly asserted by the CPU when memory temperature reaches a critical level — a higher-severity condition than MemHot. `XX_MEMTRIP_N` communicates catastrophic memory temperature to the platform, which should respond by reducing power delivery or initiating a shutdown. On NWP, the MemTrip GPIO output is supported. The primary adaptation is confirming NWP board infrastructure for pin measurement and the NWP-specific MemTrip threshold values.

**Key Justification:**
- `XX_MEMTRIP_N` output GPIO is present on NWP; `ENABLE_XXMEMTRIP_N_FUSE` = 1 (from TC 22022421480)
- MemTrip is a higher severity event than MemHot; same pin assertion mechanism but different threshold
- `NGA_MAIN` tag: silicon test requiring real memory thermal stress or injection
- NWP single IMH: monitors memory temperatures and asserts MemTrip output

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon platform with MEMTRIP_N pin observable
- `ENABLE_XXMEMTRIP_N_FUSE` = 1 on `imh0`
- Controlled thermal environment (MemTrip is catastrophic — use safe thermal injection if possible)

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Confirm `ENABLE_XXMEMTRIP_N_FUSE` = 1 on `imh0` | Single IMH check |
| 2 | Configure MemTrip threshold (if programmable) to a testable value | NWP MemTrip threshold register |
| 3 | Trigger MemTrip condition (thermal injection or DIMM stress) | Same mechanism; extreme care with real DIMM heating |
| 4 | Verify `XX_MEMTRIP_N` asserts (pin goes low) | Board-level measurement; NWP platform |
| 5 | Verify `PTPCFSMS_GPIO_BUMP_STATUS[XXMEMTRIP_N_STATUS]` software status | NWP PTPCFSMS register |
| 6 | System should respond to MemTrip (platform shutdown or power reduction) | Verify platform response within expected latency |

### NWP Pass Criteria
- Memory temp ≥ MemTrip threshold → `XX_MEMTRIP_N` asserts (pin = low)
- Software status register reflects assertion
- Platform responds within specification

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| MemTrip threshold | DMR-specific fuse | NWP-specific fuse | Verify from NWP PM HAS |
| IMH count | Multiple | Single | Only imh0 monitors and asserts |
| Risk | High (catastrophic temp event) | Same | Requires controlled thermal injection |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
# Check MEMTRIP_N status on NWP
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms

try:
    memtrip_status = ptpcfsms.gpio_bump_status.xxmemtrip_n_status.read()
    print(f"MEMTRIP_N status: {memtrip_status} (0=asserted/critical)")
except Exception as e:
    print(f"MemTrip status: {e}")

# MemTrip threshold (fuse-based)
try:
    memtrip_fuse = sv.socket0.imh0.fuses.punit.pcode_memtrip_temp.read()
    print(f"MemTrip threshold fuse: {memtrip_fuse}")
except Exception as e:
    print(f"MemTrip fuse: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **Catastrophic event risk** — MemTrip represents critical DIMM overtemperature; triggering for real risks DIMM damage | High | Use thermal injection (lower threshold artificially) or VP simulation |
| 2 | **Board test point required** — same as MemHot; MEMTRIP_N pin must be observable on NWP board | High | Coordinate with platform team |

---

## Section F: Recommendation

**Recommendation: ADAPT — safety precautions required; NGA_MAIN priority**

MemTrip output assertion is the same mechanism on NWP. MemTrip threshold is a fuse value that can be temporarily lowered for test purposes. Requires board test point infrastructure.

Required adaptations:
1. Identify NWP MemTrip threshold fuse and adjust for safe test execution
2. Confirm NWP board MEMTRIP_N pin test point
3. Single IMH scope: `sv.socket0.imh0`

**Priority**: High — NGA_MAIN; critical thermal safety signal validation
