# Deep Analysis: [CBB Thermal Management] Verify CBB Temperature Target Handling

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421478 |
| **Title** | [CBB Thermal Management] Verify CBB Temperature Target Handling |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > CBB Thermal Management |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that CBB Pcode correctly computes and applies the effective TjMax temperature target (`eff_tj_max`) used for all CBB EMTTM PID control loops. The `eff_tj_max` is calculated from SST-PP/BF temperature levels, C1E disable offset, TCC offset from MSR/TPMI, and OC offset. On NWP, `eff_tj_max` computation is supported but is simpler because SST-BF and SST-PP are ZBB (omitted from the formula). The test requires adapting the CBB loop from 4 to 2, updating the script config, and updating the expected eff_tj_max formula to exclude SST-PP/BF paths. The `NGA_MAIN` tag indicates this is a priority automation TC.

**Key Justification:**
- `eff_tj_max` computation by CBB Pcode is present on NWP; the register `TEMPERATURE_TARGET` is in TPMI
- SST-BF and SST-PP are ZBB on NWP — eff_tj_max formula simplifies to: `fuse.TjMax - (c1e_offset + tcc_offset)`
- C1E offset path is still active on NWP (C1E is supported); must include in verification
- NWP has 2 CBBs (DMR: 4); `TEMPERATURE_TARGET` verification must cover both CBBs

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP platform (VP or silicon) with BIOS having programmed TCC_OFFSET
- PythonSv access to `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.temperature_target`
- C1E enable status readable

### NWP eff_tj_max Formula

```
# NWP eff_tj_max (simplified — no SST-PP/BF)
eff_tj_max_c1e_offset = c1e_disabled ? fuse.TJ_MAX_C1E_DISABLED_OFFSET : 0
eff_tj_max_msr_offset = max(MSR.IA32_TEMPERATURE_TARGET[TJ_MAX_TCC_OFFSET],
                            TPMI.temperature_target.tcc_offset)
eff_tj_max = fuse.HIGHEST_TJ_MAX - (eff_tj_max_c1e_offset + eff_tj_max_msr_offset)

# Note: SST_PP_T_THROTTLE and SST_BF paths are NOT used on NWP (ZBB)
```

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run `thermalManagement.py.thermTest` with NWP config | 2 CBBs, `nwp.xml` |
| 2 | Read `fuse.HIGHEST_TJ_MAX` and `fuse.TJ_MAX_C1E_DISABLED_OFFSET` | Same; read via PythonSv fuse namespace |
| 3 | Read `IA32_TEMPERATURE_TARGET[27:24]` (TCC_OFFSET from MSR) | Same MSR |
| 4 | Read C1E enable from `MSR POWER_CTL[C1E_ENABLE]` | Same |
| 5 | Compute expected `eff_tj_max` using NWP formula (no SST-PP/BF) | Update formula — omit SST_PP/BF lookup |
| 6 | Read `TEMPERATURE_TARGET` from package TPMI (`ptpcfsms.temperature_target`) | Same TPMI register |
| 7 | Verify `TEMPERATURE_TARGET.tcc_offset` reflects the programmed offset | Same acceptance criterion |
| 8 | Change TCC_OFFSET via MSR (write new value); re-read and verify eff_tj_max updates | Same |

### NWP Pass Criteria
- `eff_tj_max` computed by Pcode matches formula: `TjMax - (c1e_offset + tcc_offset)` (no SST-PP)
- `TEMPERATURE_TARGET` TPMI register reflects the effective TCC offset
- eff_tj_max updates within one Pcode slow-loop cycle (~1ms) after TCC_OFFSET change

---

## Section C: NWP Delta Impact Analysis

### eff_tj_max Formula Differences

| Component | DMR | NWP | Impact |
|-----------|-----|-----|--------|
| SST-PP T_THROTTLE base | Active (level-dependent fuse) | ZBB — use `fuse.HIGHEST_TJ_MAX` | Test must use base TjMax fuse as reference |
| SST-BF T_THROTTLE override | Active when BF enabled | ZBB — not applicable | Remove SST-BF branch from verification |
| C1E offset | Conditional on C1E enable | Same (C1E supported) | No change |
| TCC_OFFSET MSR | Active | Same | No change |
| OC offset | Active when OC enabled | Same (if OC enabled on NWP) | Check NWP OC support |

### Topology

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBBs | 4 | 2 | Verify eff_tj_max on both CBBs |
| Script XML | `dmr.xml` | `nwp.xml` | Direct substitution |

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| Temperature target | `ptpcfsms.temperature_target` | `tcc_offset` | Programmed TCC_OFFSET value | Package TPMI |
| Package DTS | `ptpcfsms.package_temperature_pmt` | — | Current package temperature | Package PMT |
| TjMax fuse | NWP fuse namespace | `HIGHEST_TJ_MAX` | Fuse-programmed TjMax | Package |
| C1E enable | `MSR POWER_CTL` | `C1E_ENABLE[1]` | 1 (enabled) | Package MSR |
| TCC offset MSR | `IA32_TEMPERATURE_TARGET` | `TJ_MAX_TCC_OFFSET[27:24]` | BIOS-programmed offset | Package MSR |

### PythonSv Validation Commands (NWP)

```python
# Read temperature target TPMI register (NWP)
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms

tcc_offset = ptpcfsms.temperature_target.tcc_offset_time_window.read()
pkg_temp = ptpcfsms.package_temperature_pmt.read()
print(f"TCC offset: {tcc_offset}")
print(f"Package temp: {pkg_temp}")

# Read per-CBB EMTTM temperature targets (NWP has 2 CBBs)
for cbb_idx in range(2):  # NWP has 2 CBBs
    try:
        cbb_tpmi = sv.socket0.getbypath(f"cbb{cbb_idx}.base.tpmi")
        cbb_temp_tgt = cbb_tpmi.getbypath("temperature_target").read()
        print(f"CBB{cbb_idx} temperature_target: 0x{cbb_temp_tgt:08X}")
    except Exception as e:
        print(f"CBB{cbb_idx}: {e}")

# Read TjMax from fuses
try:
    tj_max = sv.socket0.imh0.fuses.punit.tj_max.read()
    print(f"Fuse TjMax: {tj_max}")
except Exception as e:
    print(f"TjMax fuse: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **SST-PP ZBB changes verification reference** — test logic that reads SST_PP_T_THROTTLE as the base temperature must be updated to use fuse.HIGHEST_TJ_MAX directly | Medium | Update expected-value computation in `thermalManagement.py` |
| 2 | **OC offset on NWP** — if OC is not supported/enabled, the OC offset path (which *decrements* the offset, increasing headroom) must be excluded | Low | Verify NWP OC support in PM HAS |
| 3 | **CBB TPMI temperature_target register path** — NWP namednodes path needs bring-up validation | Low | Estimate in code above |

---

## Section F: Recommendation

**Recommendation: ADAPT — SST-PP removal from formula + NGA prioritization**

Temperature target handling is fundamentally supported on NWP. The key adaptation is removing SST-PP/BF paths from the eff_tj_max formula and using fuse TjMax directly. This is a high-priority test (NGA_MAIN) and should be among the first SoC Thermal TCs automated for NWP.

Required adaptations:
1. Update eff_tj_max formula in test: remove SST-PP/BF lookup; use `fuse.HIGHEST_TJ_MAX`
2. Change script to NWP config (`nwp.xml`); CBB loop: `range(2)`
3. Verify NWP `TEMPERATURE_TARGET` TPMI register path in namednodes

**Priority**: Critical — NGA_MAIN; eff_tj_max correctness is prerequisite for all EMTTM throttle tests
