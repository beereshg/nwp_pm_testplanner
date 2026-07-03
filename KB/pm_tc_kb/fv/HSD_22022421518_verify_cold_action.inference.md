# Deep Analysis: [IMH Thermal Management] Verify Cold Action

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421518 |
| **Title** | [IMH Thermal Management] Verify Cold Action |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > IMH Thermal Management |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that PrimeCode IMH thermal management correctly performs a "cold action" — the recovery sequence when all thermal throttle conditions have cleared. After the conditions `THERMAL_STRIKES_LEFT == 0`, `IMH_DIE_TEMP_MAX > (eff_tj_max - EARLY_THROTTLE_OFFSET + OFFSET_AT_MAX_THROTTLE)`, and `IMH_DIE_TEMP_MAX >= (eff_tj_max - EARLY_THROTTLE_OFFSET)` all become false, PrimeCode must release the IMH throttle ceiling and restore nominal fabric frequency. On NWP, the IMH PrimeCode PID-based thermal management (Mem Fabric + IO Fabric loops) is supported. The primary adaptation is updating `thermalManagement.py` for NWP topology and confirming NWP-specific thermal trip constants.

**Key Justification:**
- IMH PrimeCode thermal management (PID-based cold/warm/hot N-strike→PID) is present on NWP
- Cold action recovery (`THERMAL_STRIKES_LEFT` counter, `EARLY_THROTTLE_OFFSET`, `OFFSET_AT_MAX_THROTTLE`) is the same algorithmic path on NWP
- NWP has a single IMH (`sv.socket0.imh0`); DMR had multiple; path scope changes but logic is identical
- `thermalManagement.py.thermTest` adapts to NWP with updated topology config

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP platform with IMH thermal stress capability (high-bandwidth memory/IO workload)
- PythonSv access to `sv.socket0.imh0` PTPCFSMS/PMSB registers
- `thermalManagement.py` with NWP config

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run `thermalManagement.py.thermTest` with NWP config | NWP IMH topology; single IMH (`imh0`) |
| 2 | Apply high-bandwidth workload to push IMH temp above thermal trip conditions | Same mechanism |
| 3 | Verify PrimeCode thermal throttle triggers: `THERMAL_STRIKES_LEFT` decrements; fabric throttle asserts | Read NWP IMH registers via PythonSv |
| 4 | Reduce workload → IMH temp drops below `eff_tj_max - EARLY_THROTTLE_OFFSET` | Same |
| 5 | Verify cold action: PrimeCode releases fabric frequency ceiling | Read fabric ratio limit; verify returns to P0 |
| 6 | Verify `IA32_PACKAGE_THERM_STATUS.THERMAL_MONITOR_STATUS` clears after recovery | Same package MSR |

### NWP Pass Criteria
- After all thermal trigger conditions clear, PrimeCode releases the IMH thermal throttle
- Fabric frequency (Mem Fabric + IO Fabric) returns to unconstrained limit
- `THERMAL_MONITOR_STATUS` = 0 after recovery
- `THERMAL_STRIKES_LEFT` counter returns to maximum after sufficient cold dwell time

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| IMH count | Multiple (IMH0, IMH1) | Single (`imh0`) | Only one IMH to monitor |
| Thermal PID | Kp=0.17, Ki=0.06 (DMR-specific) | NWP-specific PID constants | Verify NWP PID tuning in PM HAS |
| Script XML | `dmr.xml` / `thermalManagement.py` | NWP config | Update config |
| `EARLY_THROTTLE_OFFSET`, `OFFSET_AT_MAX_THROTTLE` | DMR-specific fuse values | NWP-specific | Verify from NWP PM HAS |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
# Monitor IMH thermal state on NWP (single IMH)
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms

# Package thermal monitor status
pkg_therm = ptpcfsms.perf_limit_reasons.read()
print(f"Package PLR: 0x{pkg_therm:08X}")

# IMH die temperature (PMT)
pkg_temp = ptpcfsms.package_temperature_pmt.read()
print(f"IMH package temp: {pkg_temp}")

# Thermal status flag
try:
    therm_status = ptpcfsms.thermal_constrained_time_pmt.read()
    print(f"Thermal constrained time: {therm_status}")
except Exception as e:
    print(f"Thermal status: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP PID tuning constants** — `EARLY_THROTTLE_OFFSET` and `OFFSET_AT_MAX_THROTTLE` may differ from DMR fuse values | Medium | Verify from NWP PM HAS; update expected values in test |
| 2 | **Cold dwell time** — duration required for `THERMAL_STRIKES_LEFT` to replenish may differ on NWP | Low | Read from NWP config; same algorithmic approach |

---

## Section F: Recommendation

**Recommendation: ADAPT — NWP constant verification required**

IMH cold action recovery is the same mechanism on NWP. Adapt `thermalManagement.py` for NWP single-IMH topology and verify NWP-specific thermal constants.

Required adaptations:
1. Update `thermalManagement.py` config to NWP (single IMH)
2. Verify NWP `EARLY_THROTTLE_OFFSET` and `OFFSET_AT_MAX_THROTTLE` fuse values
3. Update expected cold action trigger conditions with NWP-specific values

**Priority**: Medium — Cold action recovery is a functional correctness test for thermal throttle lifecycle
