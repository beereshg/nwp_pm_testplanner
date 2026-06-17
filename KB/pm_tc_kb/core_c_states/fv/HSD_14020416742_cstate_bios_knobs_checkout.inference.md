# Deep Analysis: CState Bios_knobs checkout

| Field | Value |
|-------|-------|
| **HSD ID** | 14020416742 |
| **Title** | CState Bios_knobs checkout |
| **Date** | 2026-05-27 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Core C-States |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Core C-states are fully supported on NWP. The BIOS knob interface (C6Enable, C1AutoDemotion, C1AutoUnDemotion, MonitorMWait, ProcessorC1eEnable) maps directly to the same MSRs and TPMI fields on NWP, requiring only adaptation of the PythonSv register paths from DMR CBB layout (up to 4 CBBs, 64 cores) to NWP (2 CBBs, 48 cores each).

### Test Intent

Verify that all C-state BIOS knobs propagate correctly from BIOS configuration into the NWP PCode and hardware registers. The test configures each knob (C6Enable, C1AutoDemotion, C1AutoUnDemotion, MonitorMWait, ProcessorC1eEnable) and confirms the corresponding hardware control register reflects the requested state. On NWP, the knobs control identical hardware bits: `CLOCK_CST_CONFIG_CONTROL.c1_state_auto_demotion_enable` per-core, `POWER_CTL1.C1E_ENABLE` (MSR 0x1FC bit[1]) per package, and `MISC_ENABLES.enable_monitor_fsm` per-core. All five knobs are expected to work on NWP. Note: PkgC6 is ZBB on NWP, so verifying `C6Enable` must confirm C6 demotion policy stops at PC3, not PC6.

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon or VP at boot-complete state
- PythonSv + namednodes loaded (`sv.socket0.cbb{0,1}.*` accessible)
- BIOS with C-state knobs exposed (C6Enable, C1AutoDemotion, C1AutoUnDemotion, MonitorMWait, ProcessorC1eEnable)

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Set C6Enable BIOS knob ON/OFF and boot | Same knob name on NWP; verify effect via `CLOCK_CST_CONFIG_CONTROL` |
| 2 | Read `CLOCK_CST_CONFIG_CONTROL` per-core across 2 CBBs × 48 cores | Change loop bounds: `for cbb in range(2): for core in range(48)` |
| 3 | Set C1AutoDemotion ON/OFF; verify `c1_state_auto_demotion_enable` bit | Same register, same bit; 2 CBBs × 48 cores |
| 4 | Set C1AutoUnDemotion ON/OFF; verify `enc1undemotion` bit | Same field; NWP path: `sv.socket0.cbb{idx}.core[core_idx]...` |
| 5 | Set MonitorMWait ON/OFF; verify `MISC_ENABLES.enable_monitor_fsm` per-core | Same MSR 0x1A0 bit[18]; adapt path |
| 6 | Set ProcessorC1eEnable ON/OFF; verify `POWER_CTL1.C1E_ENABLE` | MSR 0x1FC bit[1]; check both CBBs |
| 7 | Confirm PkgC6 not enabled (C6Enable=ON should stop at PC3 on NWP) | PC6 is ZBB: verify PC6 residency counter (MSR 0x3F9) stays 0 |

### NWP Pass Criteria
- Each BIOS knob change is reflected in the corresponding hardware register within one boot
- `C1_AUTO_DEMOTION_ENABLE` and `enc1undemotion` match knob state across all 96 cores
- `POWER_CTL1.C1E_ENABLE` matches ProcessorC1eEnable knob state
- When C6Enable=ON, `P_CR_PC6_RCNTR` (MSR 0x3F9) remains 0 throughout test (ZBB)

---

## Section C: NWP Delta Impact Analysis

### CBB and Core Count

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | Up to 4 | **2** | Loop: `range(4)` → `range(2)` |
| Cores per CBB | 64 | **48** | Loop: `range(64)` → `range(48)` |
| IMH | Multiple iMH | **Single NIO** | Register paths remap to `imh0.*` |
| PkgC6 | Supported | **ZBB** | C6Enable test must include negative PC6 check |

### BIOS Knob Register Mapping (NWP)

| BIOS Knob | NWP Register | NWP Path |
|-----------|-------------|----------|
| C6Enable | `CLOCK_CST_CONFIG_CONTROL.c6_state_enable` | per-core, `cbb{i}.core[j]` |
| C1AutoDemotion | `CLOCK_CST_CONFIG_CONTROL.c1_state_auto_demotion_enable` | per-core |
| C1AutoUnDemotion | `CLOCK_CST_CONFIG_CONTROL.enc1undemotion` | per-core |
| MonitorMWait | `MISC_ENABLES.enable_monitor_fsm` | MSR 0x1A0[18], per-core |
| ProcessorC1eEnable | `POWER_CTL1.C1E_ENABLE` | MSR 0x1FC[1], package |

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| C6 Enable | `CLOCK_CST_CONFIG_CONTROL` | `.c6_state_enable` | Matches C6Enable knob | Per-core, 2 CBBs |
| C1 Demotion | `CLOCK_CST_CONFIG_CONTROL` | `.c1_state_auto_demotion_enable` | Matches knob | Per-core |
| C1 Un-demotion | `CLOCK_CST_CONFIG_CONTROL` | `.enc1undemotion` | Matches knob | Per-core |
| Monitor/MWait | `MISC_ENABLES` (MSR 0x1A0) | bit[18] | Matches MonitorMWait knob | Per-core |
| C1E Enable | `POWER_CTL1` (MSR 0x1FC) | `.c1e_enable` (bit[1]) | Matches C1e knob | Package |
| PC6 Counter | `P_CR_PC6_RCNTR` (MSR 0x3F9) | full register | 0 (ZBB) | Package |

### PythonSv Validation Commands (NWP)

```python
import time

# Check C1E enable across CBBs
for cbb_idx in range(2):   # NWP: 2 CBBs
    cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
    power_ctl = sv.socket0.imh0.punit.power_ctl1.read()
    c1e_en = (power_ctl >> 1) & 1
    print(f"CBB{cbb_idx} POWER_CTL1.C1E_ENABLE: {c1e_en}")

# Check C1 demotion per-core (sample first 4 cores per CBB)
for cbb_idx in range(2):
    for core_idx in range(4):
        cst_cfg = sv.socket0.getbypath(f"cbb{cbb_idx}").core[core_idx].clock_cst_config_control.read()
        print(f"CBB{cbb_idx} Core{core_idx} CST_CONFIG: {cst_cfg:#010x}")

# Verify PC6 residency = 0 (ZBB)
pc6_cnt = sv.socket0.imh0.punit.getbypath("p_cr_pc6_rcntr").read()
print(f"PC6 Residency Counter: {pc6_cnt} (must be 0 on NWP)")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **CBB count** — DMR scripts may iterate `range(4)`; NWP requires `range(2)` | Medium | Audit all loop ranges before execution |
| 2 | **PC6 ZBB** — C6Enable=ON test must verify PC6 counter stays 0 | Medium | Add explicit `P_CR_PC6_RCNTR == 0` assertion |
| 3 | **Register path changes** — DMR used `sockets.computes.uncore.*`; NWP uses `sv.socket0.cbb{i}.*` | High | Update all PythonSv paths in the test script |
| 4 | **Environment** — BIOS knob availability on NWP VP/silicon | Low | Confirm with platform team |

---

## Section F: Recommendation

**Recommendation: ADAPT — Minor NWP topology changes required before execution.**

The test logic is sound and all five BIOS knobs control the same hardware on NWP. Required adaptations are path updates (DMR → NWP namednodes) and loop bound changes (CBB/core counts). Additionally, the PC6 portion of the C6Enable test should be converted to a negative check (PC6 counter must remain 0).

Required adaptations:
1. Change CBB loop from `range(4)` to `range(2)`, core loop from `range(64)` to `range(48)`
2. Update PythonSv paths: `sockets.computes.uncore.*` → `sv.socket0.cbb{i}.punit.*`
3. Add PC6 residency counter = 0 assertion when C6Enable=ON

**Priority**: Medium — core C-state BIOS knob verification is essential for NWP bring-up.
