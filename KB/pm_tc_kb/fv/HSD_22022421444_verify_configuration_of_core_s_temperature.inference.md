# Deep Analysis: [ACP] Verify Configuration of Core's Temperature Target

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421444 |
| **Title** | [ACP] Verify Configuration of Core's Temperature Target |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ACP (Autonomous Core Perimeter) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test case verifies that Pcode correctly updates the Core EMTTM temperature target register `EMTTM_ALGO_MISC[CONTROL_TEMP]` with the effective TjMax value (`eff_tj_max`) whenever it changes. The effective TjMax is computed from fuse-based TjMax, C1E offset, TCC_OFFSET from MSR/TPMI, and SST-PP/BF configuration. On NWP, the ACP Core EMTTM architecture is supported and the `EMTTM_ALGO_MISC` register path exists within each CBB's per-core PMSB. The test requires adaptation for NWP's 2-CBB topology (DMR has 4) and the absence of SST-BF/SST-PP (ZBB on NWP), which simplifies the eff_tj_max computation path.

**Key Justification:**
- Core EMTTM (ACP) is supported on NWP; `CORE_*_PMSB_PMA_CR_EMTTM_ALGO_MISC` register exists per CBB
- SST-BF and SST-PP are ZBB on NWP — the eff_tj_max formula reduces to: `eff_tj_max = fuse.HIGHEST_TJ_MAX - (c1e_offset + tcc_offset)`
- NWP has 2 CBBs × 48 cores; the temperature target must be verified across all 96 cores; DMR had 4 CBBs × 32 cores
- `thermalManagement.py` test script requires NWP config; no DMR-specific XML needed for this register-check TC

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- Silicon / VP platform with NWP CBB access via PythonSv (`sv.socket0.cbb{0,1}`)
- `thermalManagement.py` available in NWP test environment
- Baseline thermal fuses readable (TJ_MAX, TJ_MAX_C1E_DISABLED_OFFSET)
- BIOS has programmed `IA32_TEMPERATURE_TARGET[TJ_MAX_TCC_OFFSET]` (or TPMI equivalent)

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Read fuse `TJ_MAX` (HIGHEST_TJ_MAX) and `TJ_MAX_C1E_DISABLED_OFFSET` | Same on NWP; read via PythonSv fuse path |
| 2 | Read `TCC_OFFSET` from `IA32_TEMPERATURE_TARGET[27:24]` or `TPMI.SST_PP_CONTROL` | Use larger of the two values; SST-PP is ZBB on NWP so TPMI path is inactive |
| 3 | Determine if C1E is enabled: read `MSR POWER_CTL[C1E_ENABLE]` | Same on NWP (C1E is supported) |
| 4 | Compute expected `eff_tj_max = TJ_MAX - (c1e_offset + tcc_offset)` | SST-BF/PP paths absent on NWP; formula is simpler |
| 5 | Read `CORE_*_PMSB_PMA_CR_EMTTM_ALGO_MISC[CONTROL_TEMP]` for all cores in both CBBs | Loop over `range(2)` CBBs × `range(48)` cores (DMR: 4 CBBs × 32 cores) |
| 6 | Verify `CONTROL_TEMP == eff_tj_max` for all cores | Same acceptance criterion |
| 7 | Trigger eff_tj_max change (e.g., write new TCC_OFFSET via MSR) | Same mechanism |
| 8 | Re-read `EMTTM_ALGO_MISC[CONTROL_TEMP]` and verify it updated | Same acceptance criterion |

### NWP Pass Criteria
- `EMTTM_ALGO_MISC[CONTROL_TEMP]` == computed `eff_tj_max` on all 96 cores across 2 CBBs
- Value updates within one slow-loop cycle (~1ms) after any change to eff_tj_max inputs

---

## Section C: NWP Delta Impact Analysis

### SST-BF/SST-PP Absence on NWP

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| SST-BF T_THROTTLE | Active fuse path for eff_tj_max | ZBB — not used | eff_tj_max formula simplifies |
| SST-PP T_THROTTLE | Active per level | ZBB — not used | Only fuse TjMax base applies |
| C1E offset | Conditional on C1E enable | Same (C1E supported) | No change needed |
| TCC_OFFSET MSR | BIOS programs `IA32_TEMPERATURE_TARGET` | Same path | No adaptation needed |

### Topology Changes

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | 4 | 2 | Loop bounds: `range(2)` not `range(4)` |
| Cores per CBB | 32 | 48 | Inner loop: `range(48)` not `range(32)` |

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| ACP control | `CORE_*_PMSB_PMA_CR_EMTTM_ALGO_MISC` | `CONTROL_TEMP[7:0]` | == computed eff_tj_max | All cores, both CBBs |
| TCC offset | `IA32_TEMPERATURE_TARGET` | `TJ_MAX_TCC_OFFSET[27:24]` | BIOS-programmed value | Package MSR |
| C1E enable | `MSR POWER_CTL` | `C1E_ENABLE[1]` | 1 (enabled by default) | Package MSR |
| Thermal status | `IA32_PACKAGE_THERM_STATUS` | `TEMPERATURE[23:16]` | TjMax - current temp | Package |

### PythonSv Validation Commands (NWP)

```python
import re

# Read effective TjMax components
# Note: NWP has no SST-BF/PP; eff_tj_max = fuse_tj_max - c1e_offset - tcc_offset
tcc_offset = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.temperature_target.tcc_offset_time_window.read()
# C1E check via MSR (use pmx or direct MSR read tool)

# Verify EMTTM_ALGO_MISC[CONTROL_TEMP] on all NWP cores
for cbb_idx in range(2):  # NWP has 2 CBBs
    cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
    for core_idx in range(48):  # NWP has 48 cores per CBB
        try:
            reg_path = f"compute{core_idx // 8}.module{core_idx % 8}.emttm_algo_misc"
            ctrl_temp = cbb.getbypath(reg_path).control_temp.read()
            print(f"CBB{cbb_idx} core{core_idx}: CONTROL_TEMP={ctrl_temp}")
        except Exception as e:
            print(f"CBB{cbb_idx} core{core_idx}: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP core path to EMTTM_ALGO_MISC** — DMR register path `CORE_*_PMSB_PMA_CR_EMTTM_ALGO_MISC` maps to NWP compute/module hierarchy; exact namednodes path needs silicon verification | Medium | Validate during bring-up; path above is estimated from NWP topology |
| 2 | **SST-PP ZBB affects eff_tj_max source** — test steps that assume SST-PP base temperature must be updated to use `fuse.HIGHEST_TJ_MAX` directly | Low | Documented in NWP KB; straightforward substitution |
| 3 | **96-core verification scope** — reading 96 registers may be slow; consider sampling strategy (e.g., 4 cores per CBB) for smoke test | Low | Full verification only needed for regression; smoke OK with sampling |

---

## Section F: Recommendation

**Recommendation: ADAPT — minor topology and SST config changes required**

This test is fundamentally checking a PM firmware register update that exists on NWP. The core adaptation needed is changing the loop from 4×32 cores to 2×48 cores, removing the SST-BF/PP paths from the expected eff_tj_max formula, and verifying the NWP PMSB register path is accessible. The test logic and acceptance criteria remain identical.

Required adaptations:
1. Update `thermalManagement.py` config to use NWP topology (2 CBBs × 48 cores)
2. Remove SST-BF/PP branches from eff_tj_max computation in test verification
3. Confirm NWP PMSB namednodes path for `EMTTM_ALGO_MISC`

**Priority**: High — Core temperature target is foundational to all EMTTM throttling correctness
