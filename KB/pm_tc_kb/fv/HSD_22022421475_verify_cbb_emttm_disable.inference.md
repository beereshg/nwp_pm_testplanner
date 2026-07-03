# Deep Analysis: [CBB Thermal Management] Verify CBB EMTTM Disable

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421475 |
| **Title** | [CBB Thermal Management] Verify CBB EMTTM Disable |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > CBB Thermal Management |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that CBB-level EMTTM (PCode-managed PID thermal control for CCF/Ring and cross-throttle) can be disabled via the OS/BIOS control register `IA32_MISC_ENABLE[AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE]` (bit 3). By default this is enabled; clearing it disables CBB EMTTM-triggered frequency throttling. On NWP, CBB EMTTM is supported and the `IA32_MISC_ENABLE` disable path exists. The test requires adapting the script from `dmr.xml` to `nwp.xml` and updating CBB monitoring from 4 to 2 CBBs.

**Key Justification:**
- CBB EMTTM disable via `IA32_MISC_ENABLE` bit 3 is a standard x86 MSR path present on NWP
- `runPmx.py -p emttm_thermal` reusable with NWP config; `-x dmr.xml` → `-x nwp.xml`
- NWP has 2 CBBs (not 4); CBB-level register monitoring scope changes
- Sub-feature is `No_content_required` — mechanism is straightforward register write + verify

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP platform with CBB Pcode accessible via PythonSv
- `runPmx.py` available with NWP config

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Baseline: verify CBB EMTTM enabled — `IA32_MISC_ENABLE[3]` = 1 | Same MSR; package-level read |
| 2 | Run `emttm_test.loopSetup()` | Change config to NWP (2 CBBs) |
| 3 | Disable CBB EMTTM: clear `IA32_MISC_ENABLE[AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE]` = 0 | Same MSR write; package multicast |
| 4 | Apply thermal load on CCF/Ring domain | Same mechanism |
| 5 | Verify CBB EMTTM does not throttle Ring/CCF frequency | Check CCF ratio ceiling — should remain at P1 without EMTTM floor | Loop over `range(2)` CBBs (not 4) |
| 6 | Re-enable CBB EMTTM: set `IA32_MISC_ENABLE[3]` = 1 | Same |
| 7 | Verify EMTTM resumes throttling when thermal load applied | Same acceptance criterion |

### NWP Pass Criteria
- After disabling `IA32_MISC_ENABLE[3]`: CBB EMTTM PID stops asserting CCF frequency limits even at overtemperature
- After re-enabling: CBB EMTTM PID resumes throttling
- Hardware thermtrip still active regardless of EMTTM state

---

## Section C: NWP Delta Impact Analysis

### Topology Changes

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | 4 | 2 | Monitor `range(2)` CBBs |
| Script XML | `dmr.xml` | `nwp.xml` | Direct substitution |
| `IA32_MISC_ENABLE` MSR | Package multicast | Same | No adaptation needed |

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| EMTTM enable | `IA32_MISC_ENABLE` (MSR 0x1A0) | `AUTO_THERMAL_CONTROL[3]` | 0 = disabled, 1 = enabled | Package MSR |
| Thermal status | `IA32_PACKAGE_THERM_STATUS` (MSR 0x1B1) | `THERMAL_MONITOR_STATUS[0]` | 0 when EMTTM disabled (no throttle asserted) | Package |
| CCF ratio | CBB slow limits PMA_CR | CCF ratio ceiling | Unchanged (not EMTTM-limited) | Per CBB |

### PythonSv Validation Commands (NWP)

```python
# Read IA32_MISC_ENABLE EMTTM bit (use MSR read tool or OS utility)
# MSR 0x1A0 bit 3 = AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE

# Check IA32_PACKAGE_THERM_STATUS on package
# Verify thermal throttle status bit is 0 when EMTTM disabled + thermal load applied

# Check per-CBB thermal status on NWP (2 CBBs)
for cbb_idx in range(2):  # NWP has 2 CBBs
    try:
        punit = sv.socket0.getbypath(f"cbb{cbb_idx}.base.tpmi")
        thermal_sts = punit.getbypath("thermal_status").read()
        print(f"CBB{cbb_idx} thermal status: 0x{thermal_sts:08X}")
    except Exception as e:
        print(f"CBB{cbb_idx}: {e}")

# Package-level EMTTM disable flag
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms
try:
    modes = ptpcfsms.pcode_system_modes_control.read()
    emttm_disable = (modes >> 6) & 1
    print(f"Package EMTTM_DISABLE: {emttm_disable}")
except Exception as e:
    print(f"Package modes: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **Safety risk when CBB EMTTM disabled on silicon** — disabling EMTTM on live silicon with real thermal load could cause overheating; test must use controlled thermal conditions | High | Run with thermal monitoring safety guardrail; thermtrip still active |
| 2 | **`IA32_MISC_ENABLE` multicast scope** — on NWP, verify that writing pkg MSR disables EMTTM on all 2 CBBs simultaneously (not per-CBB register) | Low | Standard x86 multicast behavior; verify on NWP bring-up |

---

## Section F: Recommendation

**Recommendation: ADAPT — config substitution + thermal safety guardrail required**

CBB EMTTM disable is the same mechanism on NWP as DMR. The primary adaptation is script config (dmr.xml → nwp.xml) and CBB monitoring scope (4→2). A thermal safety guardrail is required when running on silicon.

Required adaptations:
1. Change `runPmx.py -x dmr.xml` → `-x nwp.xml`
2. Update CBB monitoring loop to `range(2)`
3. Add thermal safety guardrail (temperature monitor + abort condition)

**Priority**: Medium — EMTTM disable is a DFx/compliance test; important for bring-up but lower priority than functional throttle tests
