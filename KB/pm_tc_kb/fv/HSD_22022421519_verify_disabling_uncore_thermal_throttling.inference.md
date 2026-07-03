# Deep Analysis: [IMH Thermal Management] Verify Disabling Uncore Thermal Throttling

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421519 |
| **Title** | [IMH Thermal Management] Verify Disabling Uncore Thermal Throttling |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > IMH Thermal Management |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that uncore (IMH die) thermal throttling can be disabled via two software hooks: `PCODE_SYSTEM_MODES_CONTROL[EMTTM_DISABLE]` (bit 6, package-scoped DFX hook) and `FIRM_CONFIG[EMTTM_ENABLE]` (bit 4, BIOS-controlled). When either is set to disable, PrimeCode should not throttle the IMH fabric frequency for thermal reasons. On NWP, both disable paths are present. The test requires updating `thermalManagement.py` for NWP single-IMH topology and confirming the register paths are identical.

**Key Justification:**
- `PCODE_SYSTEM_MODES_CONTROL[6]` (EMTTM_DISABLE) and `FIRM_CONFIG[4]` (EMTTM_ENABLE) are package-scoped registers present on NWP
- Disabling uncore EMTTM prevents PrimeCode from throttling Mem Fabric and IO Fabric frequencies
- NWP has single IMH (`imh0`); multi-IMH looping from DMR is not needed
- `thermalManagement.py.thermTest` adapts to NWP with topology update

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP platform; BIOS has set baseline EMTTM enabled state
- PythonSv access to `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms`
- Thermal stress workload available

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Verify baseline: EMTTM enabled — read `PCODE_SYSTEM_MODES_CONTROL[6]` = 0, `FIRM_CONFIG[4]` = 1 | Package register; NWP same path |
| 2 | Test path A: Disable via `PCODE_SYSTEM_MODES_CONTROL[6]` = 1 | Same register write |
| 3 | Apply IMH thermal load; verify no fabric throttle occurs | Single IMH (`imh0`); verify fabric ratio unchanged |
| 4 | Re-enable: `PCODE_SYSTEM_MODES_CONTROL[6]` = 0 | Same |
| 5 | Test path B: Disable via BIOS `FIRM_CONFIG[4]` = 0 | Same register write (if accessible) |
| 6 | Apply IMH thermal load; verify no fabric throttle | Same verification |
| 7 | Re-enable: `FIRM_CONFIG[4]` = 1 | Same |

### NWP Pass Criteria
- With EMTTM disabled (either path): IMH fabric frequency not throttled even when temp exceeds eff_tj_max
- Hardware thermtrip still active when EMTTM disabled (catastrophic protection)
- After re-enabling: EMTTM throttles normally on thermal excursion

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| `PCODE_SYSTEM_MODES_CONTROL` scope | Package (DMR) | Package | Same |
| `FIRM_CONFIG` | BIOS register | Same path on NWP | Same |
| IMH count | Multiple | Single (`imh0`) | Simpler monitoring scope |
| Thermal safety | DMR had 4 CBBs providing redundant protection | NWP 2 CBBs | Same principle; thermtrip is last resort |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms

# Read EMTTM disable state
try:
    sys_modes = ptpcfsms.pcode_system_modes_control.read()
    emttm_disable = (sys_modes >> 6) & 1
    print(f"PCODE_SYSTEM_MODES_CONTROL[6] EMTTM_DISABLE: {emttm_disable}")
except Exception as e:
    print(f"System modes: {e}")

# Read FIRM_CONFIG EMTTM_ENABLE
try:
    firm_cfg = ptpcfsms.firm_config.read()
    emttm_enable = (firm_cfg >> 4) & 1
    print(f"FIRM_CONFIG[4] EMTTM_ENABLE: {emttm_enable}")
except Exception as e:
    print(f"FIRM_CONFIG: {e}")

# Perf limit reasons (verify no thermal limit when EMTTM disabled)
print(f"Package PLR: 0x{ptpcfsms.perf_limit_reasons.read():08X}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **Safety risk** — disabling IMH EMTTM on live silicon under thermal load risks overheating | High | Add temperature monitoring guardrail; disable only under controlled conditions |
| 2 | **`FIRM_CONFIG` accessibility** — BIOS-written register may be read-only from OS/PythonSv | Low | Test may need to boot with BIOS knob if direct write not allowed |

---

## Section F: Recommendation

**Recommendation: ADAPT — topology update + safety guardrail required**

Both EMTTM disable paths are the same on NWP. Primary adaptation: NWP single-IMH topology in `thermalManagement.py`. Add thermal safety guardrail.

Required adaptations:
1. Update `thermalManagement.py` config to NWP single-IMH
2. Add temperature monitoring safety guardrail
3. Verify `FIRM_CONFIG` is directly writable or requires BIOS knob on NWP

**Priority**: Medium — DFx disable path; important for validation infrastructure but lower than functional tests
