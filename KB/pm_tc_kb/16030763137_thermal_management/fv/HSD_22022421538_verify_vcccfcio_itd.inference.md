# Deep Analysis: [ITD] Verify VCCCFCIO ITD

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421538 |
| **Title** | [ITD] Verify VCCCFCIO ITD |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | VCCCFCIO (IO fabric FIVR) — iMH PrimeCode |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

VCCCFCIO is the IO fabric FIVR controlled by **iMH PrimeCode**. This is a GV-supported FIVR rail. ITD compensation is applied via the Dispatcher + RC `RESCTRL_CR_VOLTAGE_OFFSET.OFFSET` register (the DMR-specific ITD mechanism where voltage-only changes go directly to the RC register instead of creating a new WP). The DTS source is `dts_catile_a` (based on the test step table: `rsrc_adapt_dtscatile_a 0x7E00`, `RC_CFCIO`). On NWP, VCCCFCIO is present as the IO fabric FIVR controlled by single iMH. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- VCCCFCIO ITD via iMH PrimeCode is present on NWP IO fabric
- Same Dispatcher + RC V_OFFSET mechanism (DMR-specific ITD path)
- `DMR_PO` tag: silicon validation bring-up priority
- NWP single IMH simplifies: one VCCCFCIO controller (vs. potentially multiple on larger packages)

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon with IO fabric active
- VCCCFCIO ITD fuses non-zero (CFC slope fuses from TC 22022421521: `pcode_cfc_itd_slope`, `pcode_cfc_itd_slope_2`, `pcode_cfc_itd_cutoff_v`)
- PythonSv access to `sv.socket0.imh0.punit.*`

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run ITD thermal test | `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3` |
| 2 | Read VCCCFCIO DTS: `dts_catile_a` resource adapter at RC_CFCIO | `sv.socket0.imh0.punit.getbypath("dts_catile_a")` or via `rsrc_adapt_dtscatile_a` path |
| 3 | Verify ITD compensation applied: read RC voltage offset for CFCIO | `sv.socket0.imh0.punit.resctrl_cr_cfcio_v_offset.read()` |
| 4 | `itd.print_itd_info(0, 0)` shows VCCCFCIO domain | Verify VCCCFCIO compensation is non-zero at operating temp |
| 5 | Verify dual-slope: voltage at different temps follows 2-slope algorithm | Use CFC slope fuses to calculate expected compensation; compare to actual |

### VCCCFCIO DTS Source (from test steps table)

| DTS Name | Resource Adapter | RC Offset | RC Location | Index |
|----------|------------------|-----------|-------------|-------|
| `dts_catile_a` | `rsrc_adapt_dtscatile_a` | `0x7E00` | `RC_CFCIO` | 0,1,2 |

NWP: Confirm RC_CFCIO index count; DMR shows indices 0,1,2 (3 DTS sensors for CFCIO).

### NWP Pass Criteria
- VCCCFCIO RC voltage offset non-zero at operating temperature
- Compensation follows 2-slope ITD calculation based on `pcode_cfc_itd_slope/slope_2/cutoff_v`
- ITD updates within slow-loop interval when temperature changes

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| VCCCFCIO controller | iMH PrimeCode | Same — single iMH on NWP | Direct reuse |
| DTS source | `dts_catile_a` at RC_CFCIO | Same DTS on NWP (verify) | Confirm NWP CATILE DTS mapping |
| RC V_OFFSET mechanism | `RESCTRL_CR_VOLTAGE_OFFSET.OFFSET` | Same on NWP | Direct reuse |
| GV support | Yes (variable-frequency) | Same on NWP | Same compensation path |
| XML config | `dmr.xml` | `nwp.xml` | **Must update** |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
from pm.focus import itd

SockNum = 0

# Print ITD info — VCCCFCIO domain
itd.print_itd_info(SockNum, 0)

# VCCCFCIO RC voltage offset (NWP single IMH)
try:
    cfcio_offset = sv.socket0.imh0.punit.resctrl_cr_cfcio_v_offset.read()
    print(f"VCCCFCIO V_OFFSET: {cfcio_offset}")
except Exception as e:
    print(f"VCCCFCIO V_OFFSET: {e}")

# VCCCFCIO DTS (catile sensors)
try:
    dts_catile = sv.socket0.imh0.punit.getbypath("rsrc_adapt_dtscatile_a").read()
    print(f"DTS CATILE_A: 0x{dts_catile:08X}")
except Exception as e:
    print(f"DTS CATILE_A: {e}")

# CFC ITD fuses used for CFCIO
try:
    slope = sv.socket0.imh0.fuses.punit.pcode_cfc_itd_slope.read()
    slope_2 = sv.socket0.imh0.fuses.punit.pcode_cfc_itd_slope_2.read()
    cutoff_v = sv.socket0.imh0.fuses.punit.pcode_cfc_itd_cutoff_v.read()
    print(f"CFC ITD Slope: {slope}, Slope_2: {slope_2}, Cutoff_V: {cutoff_v}")
except Exception as e:
    print(f"CFC ITD fuses: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP CATILE DTS layout** — DTS sensor placement for CFCIO may differ on NWP SoC vs DMR | Low | Verify from NWP CFC HAS |
| 2 | **RC register name** — `resctrl_cr_cfcio_v_offset` path needs NWP namednodes validation | Low | Search via `sv.socket0.imh0.search('cfcio', 'r')` |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify DTS sensor layout**

VCCCFCIO ITD via iMH PrimeCode is architecturally the same. Single IMH on NWP simplifies monitoring.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`
2. Confirm NWP CATILE DTS sensor indices for CFCIO
3. Verify NWP `resctrl_cr_cfcio_v_offset` namednodes path

**Priority**: Medium — DMR_PO; IO fabric voltage correctness
