# Deep Analysis: [IMH Thermal Management] Verify Uncore Throttling (PID)

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421520 |
| **Title** | [IMH Thermal Management] Verify Uncore Throttling (PID) |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > IMH Thermal Management |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the PID-based IMH uncore thermal throttling path: when `IMH_DIE_TEMP_MAX >= thermal_trip_point`, PrimeCode applies PID-controlled frequency throttle to the Mem Fabric and IO Fabric domains, sets `THERMAL_MONITOR_STATUS`, and reduces uncore fabric ratios. On NWP, the PrimeCode IMH thermal PID algorithm is the same (Kp, Ki gains are NWP-specific). The test requires adapting the script from `dmr.xml` to `nwp.xml`, monitoring a single IMH (NWP) versus multiple (DMR), and verifying NWP fabric topology (Mem Fabric + IO Fabric as two independent PID loops).

**Key Justification:**
- PrimeCode IMH thermal throttling (PID-based, separate Mem Fabric and IO Fabric loops) is on NWP
- DMR replaced N-Strike with PID to reduce 5% performance dithering; NWP uses same PID architecture
- `DMR_PO` tag: silicon required; thermal excursion test
- NWP has single IMH (`imh0`); monitoring scope simplifies vs. DMR's multi-IMH

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon platform with high-bandwidth memory/IO workload capability
- `runPmx.py` with `nwp.xml` config and `emttm_thermal` profile
- PythonSv access to `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms`

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Configure `runPmx.py` for NWP | `runPmx.py -x nwp.xml -p emttm_thermal -tM 30 -M 6` |
| 2 | Apply high-bandwidth memory/IO workload to push IMH die temp above trip point | Same mechanism |
| 3 | Verify `THERMAL_MONITOR_STATUS` = 1 in `IA32_PACKAGE_THERM_STATUS` | Same package MSR |
| 4 | Verify Mem Fabric frequency reduced (PID output applied) | Single IMH; `sv.socket0.imh0` registers |
| 5 | Verify IO Fabric frequency reduced independently | Same IMH; separate PID loop |
| 6 | Verify PLR THERMAL bit set in TPMI PLR mailbox | Package-level (not per-CBB for IMH thermal) |
| 7 | Reduce workload → verify recovery (cold action) and PLR clears | Same |

### NWP Pass Criteria
- IMH die temp ≥ trip point triggers PrimeCode PID throttle on Mem Fabric + IO Fabric
- `THERMAL_MONITOR_STATUS` = 1 during throttle; `TEMPERATURE` field reflects die temp
- PLR THERMAL bit set; fabric ratios reduced proportional to PID output
- Recovery: fabric ratios return to unconstrained after temp drops below trip point

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| PID gains (Kp, Ki) | DMR: Kp=0.17, Ki=0.06 | NWP-specific values | Verify from NWP PM HAS |
| IMH count | Multiple (IMH0, IMH1) | Single (`imh0`) | Simpler monitoring |
| Script XML | `dmr.xml` | `nwp.xml` | Direct substitution |
| Fabric domains | Mem Fabric + IO Fabric (separate PIDs) | Same on NWP | No change |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
# IMH thermal throttle status on NWP (single IMH)
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms

# Package temperature and thermal status
pkg_temp = ptpcfsms.package_temperature_pmt.read()
print(f"IMH package temperature: {pkg_temp}")

# Perf limit reasons (thermal bit)
plr = ptpcfsms.perf_limit_reasons.read()
print(f"Package PLR: 0x{plr:08X} (THERMAL bit[4]: {(plr>>4)&1})")

# Thermal constrained time (RATL/thermal accum)
try:
    therm_time = ptpcfsms.thermal_constrained_time_pmt.read()
    print(f"Thermal constrained time: {therm_time}")
except Exception as e:
    print(f"Thermal constrained: {e}")

# Thermal monitor status via MSR (package MSR 0x1B1)
# Use pmutil MSR read: rdmsr -p 0 0x1B1
# THERMAL_MONITOR_STATUS = bit 0; TEMPERATURE = bits 23:16
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP PID tuning** — Kp and Ki gains are NWP-specific; test pass criterion (throttle depth vs. temperature delta) may differ | Medium | Get NWP PID params from PM HAS; update expected throttle response |
| 2 | **Silicon required** — real thermal excursion needed; VP thermal injection may be inaccurate for IMH die | Medium | Plan for silicon-only NGA execution |

---

## Section F: Recommendation

**Recommendation: ADAPT — config substitution + NWP PID constant update**

IMH PID thermal throttle is architecturally identical on NWP. Primary adaptations: `nwp.xml` config and NWP PID gain parameters. Silicon required for real thermal excursion.

Required adaptations:
1. `runPmx.py -x dmr.xml` → `-x nwp.xml`
2. Update expected throttle response with NWP PID constants (Kp, Ki from NWP PM HAS)
3. Single IMH monitoring (`sv.socket0.imh0` only)

**Priority**: High — IMH PID thermal throttle is a PO-validated, fundamental NWP uncore feature
