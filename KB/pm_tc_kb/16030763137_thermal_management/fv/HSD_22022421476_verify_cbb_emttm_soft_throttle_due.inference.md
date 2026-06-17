# Deep Analysis: [CBB Thermal Management] Verify CBB EMTTM Soft Throttle due to Cross Throttle

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421476 |
| **Title** | [CBB Thermal Management] Verify CBB EMTTM Soft Throttle due to Cross Throttle |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > CBB Thermal Management |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that EMTTM triggers a "soft" (frequency-reduction) cross-throttle: when a hot domain cannot throttle itself (e.g. non-throttlable IP or already at min ratio), EMTTM reduces the frequency of a cooler, throttlable domain to relieve heat across die boundaries. On NWP, CBB EMTTM with cross-throttle support is present. The test requires adapting from `dmr.xml` to `nwp.xml` and updating CBB scope from 4 to 2. The `DMR_PO` tag indicates this was validated at silicon PO level on DMR.

**Key Justification:**
- CBB EMTTM cross-throttle (cooler domain throttled when hotter non-throttlable IP exceeds target) is implemented on NWP PCode
- `runPmx.py -p emttm_thermal` is the test driver; XML config substitution is sufficient
- NWP has 2 CBBs with the same cross-throttle domains (CCF/Ring, Inf, D2D); no ZBB impact
- Silicon required (DMR_PO); cannot be run on VP without thermal injection capability

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon platform with CBB thermal stress capability
- `runPmx.py` with `nwp.xml` config
- PythonSv access to NWP TPMI PLR and CBB EMTTM registers

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Load EMTTM test module | Same import path |
| 2 | Run `emttm_test.loopSetup()` | NWP config (2 CBBs) |
| 3 | Execute `emttm_test.mainTest()` | `nwp.xml` instead of `dmr.xml` |
| 4 | Heat a non-throttlable domain (e.g. CCF/Ring beyond eff_tj_max) | Same thermal stress mechanism |
| 5 | Verify cross-throttle triggers: a cooler, throttlable domain (e.g. Big Core) gets frequency reduced | Loop over `range(2)` CBBs (DMR: 4); check GPSS core ratio limit |
| 6 | Verify `IA32_PACKAGE_THERM_STATUS.THERMAL_MONITOR_STATUS` = 1 | Same — package MSR read |
| 7 | Verify PLR thermal bit set at TPMI mailbox | Loop over both CBBs; bit 3 of PLR mailbox |
| 8 | Reduce thermal load → verify cross-throttle clears | Same acceptance criterion |

### NWP Pass Criteria
- Cross-throttle: cooler domain frequency reduced when non-throttlable domain is hot at its minimum
- `THERMAL_MONITOR_STATUS` = 1 during cross-throttle event
- TPMI PLR `THERMAL` bit set on the CBB where cross-throttle occurs
- Frequency recovers after thermal condition clears

---

## Section C: NWP Delta Impact Analysis

### Cross-Throttle Domain Mapping

| Domain (from CBB EMTTM HAS) | DMR | NWP | Impact |
|---|---|---|---|
| CCF / Ring | Self-throttle domain | Same on NWP | No change |
| Big Core | Cross-throttle target | Same on NWP | No change; 48 cores/CBB |
| Inf / D2D | Cross-throttle targets | Same on NWP | No change |
| CBB count | 4 | 2 | Verification loop: `range(2)` |
| Script XML | `dmr.xml` | `nwp.xml` | Direct substitution |

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| Thermal throttle | `IA32_PACKAGE_THERM_STATUS` | `THERMAL_MONITOR_STATUS[0]` | 1 during cross-throttle | Package MSR |
| PLR | TPMI PLR mailbox `cbb{i}` | Bit 3 (THERMAL) | 1 during throttle | Per CBB (2 CBBs) |
| CCF ratio | CBB slow limits | CCF ratio ceiling | Below P1 (throttled) | Per CBB |
| Core ratio | GPSS core ratio | Core ceiling | Below P1 (cross-throttled) | Per CBB |

### PythonSv Validation Commands (NWP)

```python
# Monitor cross-throttle status on NWP CBBs
for cbb_idx in range(2):  # NWP has 2 CBBs
    try:
        # PLR THERMAL bit
        plr = sv.socket0.getbypath(f"cbb{cbb_idx}.base.tpmi.plr_mailbox_interface").read()
        thermal = (plr >> 3) & 1
        print(f"CBB{cbb_idx}: PLR THERMAL={thermal}")
    except Exception as e:
        print(f"CBB{cbb_idx}: {e}")

# Package thermal monitor status
pkg_therm = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons.read()
print(f"Package perf_limit_reasons: 0x{pkg_therm:08X}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **Silicon-only test** — real cross-throttle requires genuine thermal excursion on non-throttlable domain; VP injection may not be accurate | Medium | Plan for silicon-only execution |
| 2 | **Cross-throttle domain configuration** — NWP may have different non-throttlable domain list than DMR; verify against NWP CBB EMTTM HAS | Low | Expected to be same; verify during bring-up |

---

## Section F: Recommendation

**Recommendation: ADAPT — config + loop update required; silicon-only**

CBB EMTTM cross-throttle is the same mechanism on NWP. Primary adaptations: XML config substitution and CBB loop update. This test requires silicon execution.

Required adaptations:
1. `runPmx.py -x dmr.xml` → `-x nwp.xml`
2. CBB monitoring loop: `range(2)`
3. Confirm NWP cross-throttle domain config matches DMR in `nwp.xml`

**Priority**: High — Cross-throttle is a key EMTTM safety mechanism validated at PO
