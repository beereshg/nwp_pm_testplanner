# Deep Analysis: CState Fast C1E: C1E disable with TjMax offset decrease_silicon

| Field | Value |
|-------|-------|
| **HSD ID** | 14020416799 |
| **Title** | CState Fast C1E: C1E disable with TjMax offset decrease_silicon |
| **Date** | 2026-05-27 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Core C-States > Fast C1E |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Fast C1E is supported on NWP with the same uCode + POWER_CTL1 interface as DMR. The C1E disable mechanism (adjust TjMax downward by the fused offset when C1E is disabled) applies identically on NWP.

### Test Intent

Verify that when C1E is disabled via `POWER_CTL1.C1E_ENABLE = 0`, the firmware correctly adjusts `GLOBAL_TEMPERATURE_TARGET` (TjMax) downward by the fused offset `PCODE_TJ_MAX_C1E_DISABLED_OFFSET`, and that thermal throttling begins at the adjusted threshold. The test calls `cf.check_c1e_tjmax_focus()` which toggles the C1E BIOS knob and reads back the resulting TjMax value from `IA32_TEMPERATURE_TARGET` (MSR 0x1A2). When C1E is disabled, thermal protection activates at a lower temperature to compensate for the higher exit latency from deeper C-states. On NWP: Fast C1E is ✅ supported. Verify across both CBBs (96 cores total) using `sv.socket0.cbb{0,1}.core[*].read_msr(0x1FC)` for the C1E enable bit and MSR 0x1A2 for TjMax.

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon at boot-complete (TjMax fuse readout required — not available on VP)
- PythonSv + namednodes loaded
- BIOS knob `ProcessorC1eEnable` accessible

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Read baseline TjMax: `IA32_TEMPERATURE_TARGET` (MSR 0x1A2) bits[23:16] | Same MSR; read via `sv.socket0.imh0.punit` or per-core |
| 2 | Read fused offset: `PCODE_TJ_MAX_C1E_DISABLED_OFFSET` from CAPID/fuse register | Same fuse mechanism on NWP |
| 3 | Disable C1E: set `POWER_CTL1.C1E_ENABLE = 0` (BIOS knob or direct MSR write) | MSR 0x1FC bit[1] = 0; verify across all 96 cores |
| 4 | Read new TjMax from MSR 0x1A2 after CPL4 | Expected: TjMax_new = TjMax_baseline − C1E_DISABLE_OFFSET |
| 5 | Verify PECI thermal reporting reflects adjusted TjMax | PECI updated from PCode variables; same on NWP |
| 6 | Re-enable C1E; verify TjMax returns to baseline | POWER_CTL1.C1E_ENABLE = 1; re-read MSR 0x1A2 |

### NWP Pass Criteria
- `POWER_CTL1.C1E_ENABLE = 0` reflected across all 96 cores within one boot cycle
- `IA32_TEMPERATURE_TARGET` TjMax field decreases by exactly `C1E_DISABLE_OFFSET` fused value
- PECI reports the adjusted TjMax value
- TjMax restores to original value when C1E is re-enabled
- Thermal throttling (TCC) activates at the adjusted threshold, not the original TjMax

---

## Section C: NWP Delta Impact Analysis

### C1E Architecture

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Fast C1E support | Yes | **Yes** | No change needed |
| C1E_ENABLE register | POWER_CTL1.bit[1] (MSR 0x1FC) | **Same** | No change |
| TjMax register | IA32_TEMPERATURE_TARGET (0x1A2) bits[23:16] | **Same** | No change |
| Fused offset | PCODE_TJ_MAX_C1E_DISABLED_OFFSET | **Same fuse name** | Verify fuse value on NWP part |
| CBBs | Up to 4 | **2** | Verify C1E state on 2 CBBs × 48 cores |

### TjMax Interaction (NWP)

When C1E is disabled on NWP:
1. PCode detects `C1E_ENABLE = 0` at CPL4
2. PCode reads fused `C1E_DISABLE_OFFSET` (typically 5–10°C)
3. PCode writes adjusted TjMax = TjMax_fused − C1E_DISABLE_OFFSET to `IA32_TEMPERATURE_TARGET`
4. TCC activates at the new (lower) temperature threshold
5. PECI reports new value via standard PCode telemetry path

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| C1E Enable | `POWER_CTL1` (MSR 0x1FC) | bit[1] `.c1e_enable` | 0 (disabled) | All 96 cores |
| TjMax | `IA32_TEMPERATURE_TARGET` (MSR 0x1A2) | bits[23:16] | Baseline − C1E_DISABLE_OFFSET | Per package |
| TCC Offset | `IA32_TEMPERATURE_TARGET` (MSR 0x1A2) | bits[7:0] `.tcc_offset` | Unchanged | Per package |
| C1 Residency | `CC1_RESIDENCY` (MSR 0x778) | full | Should decrease (cores go deeper) | Per-core |

### PythonSv Validation Commands (NWP)

```python
# Read TjMax before and after C1E disable
tjmax_reg = sv.socket0.imh0.punit.read_msr(0x1A2)
tjmax_baseline = (tjmax_reg >> 16) & 0xFF
print(f"TjMax baseline: {tjmax_baseline}°C")

# Check C1E enable state across all cores
for cbb_idx in range(2):    # NWP: 2 CBBs
    cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
    for core_idx in range(48):  # NWP: 48 cores/CBB
        power_ctl = cbb.core[core_idx].read_msr(0x1FC)
        c1e_en = (power_ctl >> 1) & 1
        if c1e_en != 0:
            print(f"FAIL: CBB{cbb_idx} Core{core_idx} C1E still enabled!")

# After disable: verify adjusted TjMax
tjmax_new_reg = sv.socket0.imh0.punit.read_msr(0x1A2)
tjmax_new = (tjmax_new_reg >> 16) & 0xFF
print(f"TjMax after C1E disable: {tjmax_new}°C (delta: {tjmax_baseline - tjmax_new}°C)")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **Fused offset value** — NWP C1E_DISABLE_OFFSET fuse may differ from DMR | Medium | Read fuse value from CAPID before asserting expected TjMax delta |
| 2 | **Silicon required** — TjMax fuse not available on VP; test is silicon-only | High | Mark as silicon-only in test plan |
| 3 | **PECI path** — PECI thermal reporting path is same interface on NWP | Low | Verify PECI endpoint accessible |
| 4 | **96 cores vs 256** — C1E state check must cover both CBBs | Low | Change loop to `range(2)` × `range(48)` |

---

## Section F: Recommendation

**Recommendation: ADOPT — Runs on NWP silicon with loop bound adaptation only.**

The Fast C1E + TjMax offset mechanism is identical between DMR and NWP at the firmware level. Only the core count loop (96 instead of 256) needs updating. Test requires silicon (not VP) for fuse readout.

Required adaptations:
1. Update loop bounds: `range(2)` CBBs, `range(48)` cores
2. Confirm C1E_DISABLE_OFFSET fuse value for NWP part number
3. Mark as silicon-only (VP not sufficient for TjMax fuse verification)

**Priority**: Medium — validates thermal safety behavior with C1E disabled.
