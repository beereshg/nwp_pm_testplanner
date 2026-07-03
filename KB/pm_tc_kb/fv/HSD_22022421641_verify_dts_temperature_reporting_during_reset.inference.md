# Deep Analysis: [Thermal Reporting] Verify DTS Temperature Reporting During Reset

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421641 |
| **Title** | [Thermal Reporting] Verify DTS temperature reporting during reset |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > Thermal Reporting |
| **Sub-Feature** | DTS reporting during reset (cross-product: `pm.xproducts.reset`) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This is **new content** (`New_content` sub_feature tag) testing that DTS temperature reporting correctly handles the invalid-temperature period during reset. The test uses a bootscript to halt before/after Reset Stage 3 (after DTS have been enabled but before PM flows come online). During this window, temperature should be marked as **invalid** (`valid = 0`) until PCode initializes. While invalid, the value `0x8000` (or equivalent sentinel) should be reported rather than a real temperature.

The exact NWP registers are already given in the test steps:
- `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.bios_reset_cpl_cfg.rst_cpl3`
- `sv.socket0.cbb0.compute0.cpu.module0.core0.pcu_cr_therm_status.valid`
- `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_temperature`
- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.package_temperature`

These are already NWP-specific paths (use `imh0`, `cbb0`). Command is TBD — new script needed.

**Key Justification:**
- Test steps already use NWP-compatible register paths (`sv.socket0.imh0.*`, `sv.socket0.cbb0.*`)
- `pm.xproducts.reset` cross-domain scope
- `New_content` tag: first implementation on NWP
- `PMSS_NWP_READINESS_CHECK` tag: explicitly for NWP

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon with bootscript capability
- Bootscript can halt at `rst_cpl3` (Reset Stage 3 completion)
- PythonSv access before PM flows initialize (may require special debug mode)

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Use bootscript to halt after DTS enabled but before PM flows online | Halt condition: `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.bios_reset_cpl_cfg.rst_cpl3 == 1` (detect completion) |
| 2 | Read core temperature validity flag | `sv.socket0.cbb0.compute0.cpu.module0.core0.pcu_cr_therm_status.valid` |
| 3 | Verify temperature marked as **invalid** before PCode initialization | `valid == 0` expected at this boot stage |
| 4 | Verify temperature value = `0x8000` (sentinel for invalid) | `pcu_cr_therm_status.digital_readout` should show invalid value |
| 5 | Read package temperature registers | `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_temperature` → should show invalid |
| 6 | Also read CBB-side: `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.package_temperature` | Same check; both should show invalid |
| 7 | Resume boot past PCode init; verify `valid == 1` and real temperature reported | After PM flows start, DTS valid should assert |

### DTS Validity Window

| Boot Phase | DTS State | Expected Behavior |
|------------|-----------|-------------------|
| Before RST_CPL3 | Not yet enabled | Registers may be inaccessible |
| After RST_CPL3, before PCode init | DTS enabled, `valid == 0` | Temperature = 0x8000 sentinel |
| After PCode Phase 4 (slow loop start) | DTS valid, `valid == 1` | Real temperature reported |

### NWP Pass Criteria
- **Before PCode init**: `pcu_cr_therm_status.valid == 0`; `digital_readout == 0x8000` or equivalent sentinel
- **After PCode init**: `valid == 1`; real temperature value reported
- Package temperature registers (`package_temperature`) reflect invalid state before and valid state after
- No spurious thermal events triggered during invalid temperature window

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Register paths | DMR-specific paths | Test steps already use `sv.socket0.imh0.*` and `sv.socket0.cbb0.*` — NWP-compatible | **Already NWP-adapted** |
| Core path | DMR core path | `sv.socket0.cbb0.compute0.cpu.module0.core0.*` — verify NWP hierarchy | Confirm NWP core namednodes path |
| Bootscript halt | DMR bootscript | NWP bootscript (same mechanism) | Verify NWP bootscript halt capability |
| DTS invalid sentinel | `0x8000` (DMR) | Same sentinel expected on NWP | Same x86 DTS convention |
| Command | TBD (New script) | New script to be written | NWP team must create script |

---

## Section D: Key Registers & Validation Points

```python
# NWP DTS Temperature Reporting During Reset Validation

# Step 1: Check RST_CPL3 status (bootscript halt point)
try:
    rst_cpl3 = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.bios_reset_cpl_cfg.rst_cpl3.read()
    print(f"RST_CPL3: {rst_cpl3} (1=Stage3 complete)")
except Exception as e:
    print(f"RST_CPL3: {e}")

# Step 2-4: Core DTS validity (halt before PCode init)
try:
    core_therm = sv.socket0.cbb0.compute0.cpu.module0.core0.pcu_cr_therm_status.read()
    valid = sv.socket0.cbb0.compute0.cpu.module0.core0.pcu_cr_therm_status.valid.read()
    readout = sv.socket0.cbb0.compute0.cpu.module0.core0.pcu_cr_therm_status.digital_readout.read()
    print(f"Core DTS valid: {valid} (expected 0 before PCode init)")
    print(f"Core DTS readout: 0x{readout:04X} (expected 0x8000 if invalid)")
except Exception as e:
    print(f"Core DTS: {e}")

# Step 5-6: Package temperature
try:
    imh_pkg_temp = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_temperature.read()
    cbb_pkg_temp = sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.package_temperature.read()
    print(f"iMH package_temperature: 0x{imh_pkg_temp:08X}")
    print(f"CBB0 package_temperature: 0x{cbb_pkg_temp:08X}")
except Exception as e:
    print(f"Package temp: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **New script needed** — command is TBD; NWP team must write a bootscript-based reset halt test | High | Primary blocker; coordinate with NWP bring-up team |
| 2 | **NWP core namednodes path** — `sv.socket0.cbb0.compute0.cpu.module0.core0` needs verification for NWP hierarchy | Medium | Verify during bring-up; use `sv.socket0.cbb0.search('pcu_cr_therm_status', 'r')` |
| 3 | **Bootscript halt timing** — halting after RST_CPL3 but before PCode init requires precise halt point | Medium | Work with NWP bring-up team on exact bootscript halt sequence |

---

## Section F: Recommendation

**Recommendation: ADOPT — test steps already NWP-compatible; needs new script**

Register paths in the test steps are already using NWP namednodes (`imh0`, `cbb0`). The primary work is writing the new bootscript-based test script.

Required adaptations:
1. Write new test script (TBD command) for NWP bootscript halt + DTS validity check
2. Verify NWP core namednodes path: `sv.socket0.cbb0.compute0.cpu.module0.core0.*`
3. Coordinate with NWP bring-up team for bootscript halt methodology

**Priority**: Medium — `New_content` and `pm.xproducts.reset`; important for DTS bring-up validation; needs script development
