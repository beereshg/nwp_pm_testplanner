# Deep Analysis: [ACP] Verify Core EMTTM Disable

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421452 |
| **Title** | [ACP] Verify Core EMTTM Disable |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ACP (Autonomous Core Perimeter) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that Core EMTTM (Autonomous Core Perimeter thermal control) can be disabled via the Acode control register `CORE_PMA_CR_CONFIG_10[ADVANCED_THERMAL_CTRL]`. When disabled, the Core EMTTM PID stops adjusting core frequency for thermal reasons, leaving thermal protection to CBB-level EMTTM and hardware thermtrip only. On NWP, the ACP Core EMTTM disable path is supported. The test requires adapting the script XML from `dmr.xml` to `nwp.xml` and updating CBB/core loop bounds from 4×32 to 2×48.

**Key Justification:**
- Core EMTTM disable via `CORE_PMA_CR_CONFIG_10[ADVANCED_THERMAL_CTRL]` is an ACP feature present on NWP
- `runPmx.py -p emttm_thermal` script is reusable with NWP config file substitution
- NWP: 2 CBBs × 48 cores; verification scope changes accordingly (DMR: 4 CBBs × 32 cores)
- ⚠️ Disabling EMTTM on a live silicon system risks overheating; test must use controlled thermal conditions or a test harness

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP platform with thermal monitoring active (either VP with simulated DTS or silicon with thermal control)
- `runPmx.py` with `nwp.xml` config
- PythonSv access to CBB Acode registers via namednodes

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Baseline: verify Core EMTTM is enabled — read `CORE_PMA_CR_CONFIG_10[ADVANCED_THERMAL_CTRL]` | Loop over `range(2)` CBBs, `range(48)` cores (DMR: 4×32) |
| 2 | Run `emttm_test.loopSetup()` with NWP config | Change `-x dmr.xml` → `-x nwp.xml` |
| 3 | Disable Core EMTTM: write `ADVANCED_THERMAL_CTRL = 0` to all cores | Same register field, updated loop bounds |
| 4 | Verify register value reads back 0 on all 96 NWP cores | Verify across both CBBs, 48 cores each |
| 5 | Apply thermal load; verify Core EMTTM does NOT trigger frequency demotion | Same acceptance criterion — GPSS core ratio should not be throttled by Core EMTTM PID |
| 6 | Re-enable Core EMTTM: write `ADVANCED_THERMAL_CTRL = 1` | Same register field |
| 7 | Apply thermal load; verify Core EMTTM resumes throttling | Same acceptance criterion |

### NWP Pass Criteria
- `CORE_PMA_CR_CONFIG_10[ADVANCED_THERMAL_CTRL]` = 0 disables core EMTTM on all 96 NWP cores
- With EMTTM disabled, no core ratio demotion occurs from EMTTM path (hardware thermtrip still active)
- Re-enable restores EMTTM throttle behavior

---

## Section C: NWP Delta Impact Analysis

### Topology Changes

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | 4 | 2 | Verification loop: `range(2)` |
| Cores per CBB | 32 | 48 | Verification loop: `range(48)` |
| Script XML | `dmr.xml` | `nwp.xml` | Direct substitution |

### EMTTM Disable Control

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Disable fuse requirement | `THERMAL_THROTTLE_UNLOCK` (DMR edge only) | Verify NWP equivalent | If fuse-locked, test may require SP test config |
| `FIRM_CONFIG[4]` BIOS hook | Same | Same | No adaptation needed |
| `PCODE_SYSTEM_MODES_CONTROL[6]` package hook | Same | Same | No adaptation needed |

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| EMTTM disable | `CORE_PMA_CR_CONFIG_10` | `ADVANCED_THERMAL_CTRL` | 0 = disabled, 1 = enabled | All cores, both CBBs |
| EMTTM disable (pkg) | `PCODE_SYSTEM_MODES_CONTROL` | `EMTTM_DISABLE[6]` | 1 = package disable | Package |
| BIOS hook | `FIRM_CONFIG` | `EMTTM_ENABLE[4]` | 0 = disabled | Package |

### PythonSv Validation Commands (NWP)

```python
# Read ADVANCED_THERMAL_CTRL across all NWP cores
for cbb_idx in range(2):  # NWP has 2 CBBs
    cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
    for core_idx in range(48):  # NWP has 48 cores per CBB
        try:
            reg = cbb.getbypath(
                f"compute{core_idx // 8}.module{core_idx % 8}.core_pma_cr_config_10"
            )
            adv_ctrl = reg.advanced_thermal_ctrl.read()
            if adv_ctrl != 1:
                print(f"CBB{cbb_idx} core{core_idx}: ADVANCED_THERMAL_CTRL={adv_ctrl} (EMTTM DISABLED)")
        except Exception as e:
            print(f"CBB{cbb_idx} core{core_idx}: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **Overheating risk when EMTTM disabled** — silicon-level test must have thermal controls to prevent overtemp; not safe to run without thermal infrastructure | High | Add explicit test-harness temperature guardrail before disabling EMTTM |
| 2 | **NWP EMTTM disable fuse** — DMR required `THERMAL_THROTTLE_UNLOCK` fuse for SW disable on SP; NWP equivalent fuse must be confirmed | Medium | Check NWP PM HAS or run in SP-type config |
| 3 | **Acode register path** — `CORE_PMA_CR_CONFIG_10` namednodes path under NWP CBB topology needs bring-up validation | Low | Estimate above uses DMR path structure |

---

## Section F: Recommendation

**Recommendation: ADAPT — config update + fuse verification required**

Core EMTTM disable is a valid test on NWP. Primary adaptations: update script XML, update core/CBB loop bounds, and confirm the NWP EMTTM-disable fuse configuration before running on silicon. The overheating risk is a safety concern that must be addressed in the test harness.

Required adaptations:
1. Change `runPmx.py -x dmr.xml` → `-x nwp.xml`
2. Update loop bounds: 2 CBBs × 48 cores
3. Confirm NWP `THERMAL_THROTTLE_UNLOCK` equivalent or SP-config availability
4. Add thermal safety guardrail to test runner

**Priority**: Medium — EMTTM disable path is a DFx/validation hook; important but lower priority than functional thermal tests
