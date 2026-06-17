# Deep Analysis: [ITD] Verify VCCCFCMEM ITD

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421540 |
| **Title** | [ITD] Verify VCCCFCMEM ITD |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | VCCCFCMEM (Memory fabric FIVR) — iMH PrimeCode |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

VCCCFCMEM is the **memory fabric FIVR** — a GV-supported rail controlled by iMH PrimeCode via Dispatcher + RC `RESCTRL_CR_VOLTAGE_OFFSET.OFFSET`. On DMR, there are two domains: `VCCCFCMEM_W` (West) and `VCCCFCMEM_E` (East), each with their own DTS sensors. The DTS source is `dts_catile_a` (same adapter as CFCIO). On NWP, VCCCFCMEM is present for the memory fabric. The domain count (W/E split) and DTS configuration may differ on NWP's different die geometry. Single iMH controls both domains. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- VCCCFCMEM ITD via iMH PrimeCode is present on NWP memory fabric
- Same Dispatcher + RC V_OFFSET mechanism
- `DMR_PO` tag: silicon validation bring-up priority
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon with memory fabric active
- VCCCFCMEM ITD fuses non-zero (CFC slope fuses: same as CFCIO — `pcode_cfc_itd_slope`, `pcode_cfc_itd_slope_2`, `pcode_cfc_itd_cutoff_v`)
- PythonSv access to `sv.socket0.imh0.punit.*`

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run ITD thermal test | `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3` |
| 2 | Read VCCCFCMEM DTS (W and E domains) | NWP: confirm if W/E domain split exists; use `dts_catile_a` or equivalent |
| 3 | Verify ITD compensation: RC voltage offset for each CFCMEM domain | `sv.socket0.imh0.punit.resctrl_cr_cfcmem_{w|e}_v_offset.read()` |
| 4 | `itd.print_itd_info(0, 0)` shows VCCCFCMEM_W and _E (or NWP equivalent) | Verify domain count matches NWP topology |
| 5 | Verify dual-slope compensation via CFC ITD fuses | Same fuses as VCCCFCIO; verify cross-domain sharing |

### VCCCFCMEM DTS Source (from test steps table)

| DTS Name | Resource Adapter | RC Offset | RC Location | Index |
|----------|------------------|-----------|-------------|-------|
| `dts_catile_a` | `rsrc_adapt_dtscatile_a` | `0x7E00` | `RC_CFCIO` | 0 — repeated sensor (no push) |
| — | `rsrc_adapt_dtscatile_a` | — | Various CFCMEM RC locations | — |

Note: Test steps show `dts_catile_a` is a repeated sensor for CFCMEM; verify NWP specific DTS mapping.

### NWP Pass Criteria
- VCCCFCMEM RC voltage offset non-zero at operating temperature
- Compensation follows CFC ITD slope fuses (shared with CFCIO)
- Both W and E domains (or NWP equivalent) show correct ITD application

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| VCCCFCMEM domains | W and E (two domains) | NWP die geometry may differ | Confirm NWP CFCMEM W/E split |
| DTS source | `dts_catile_a` | Same adapter family (verify) | NWP DTS placement confirms |
| Fuses | `pcode_cfc_itd_slope` (shared with CFCIO) | Same | CFC fuses apply to both CFCMEM and CFCIO |
| Controller | iMH PrimeCode | Single iMH on NWP | Direct reuse |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
from pm.focus import itd

SockNum = 0

# Print ITD info — VCCCFCMEM domains
itd.print_itd_info(SockNum, 0)

# VCCCFCMEM W/E RC voltage offsets
for domain in ["cfcmem_w", "cfcmem_e"]:
    try:
        offset = sv.socket0.imh0.punit.getbypath(f"resctrl_cr_{domain}_v_offset").read()
        print(f"VCCCFCMEM {domain.upper()} V_OFFSET: {offset}")
    except Exception as e:
        print(f"VCCCFCMEM {domain}: {e}")

# CFC ITD fuses (shared with CFCIO)
try:
    slope = sv.socket0.imh0.fuses.punit.pcode_cfc_itd_slope.read()
    slope_2 = sv.socket0.imh0.fuses.punit.pcode_cfc_itd_slope_2.read()
    print(f"CFC ITD Slope: {slope}, Slope_2: {slope_2}")
except Exception as e:
    print(f"CFC fuses: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP W/E domain split** — confirm if NWP has VCCCFCMEM_W and _E or a single domain based on die geometry | Low | Verify from NWP CFC SoC architecture |
| 2 | **DTS repeated sensor** — test steps note `dts_catile_a` is a "repeat sensor" for CFCMEM; NWP may have different repeated sensor config | Low | Verify from NWP DTS mapping documentation |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify W/E domain count**

VCCCFCMEM ITD is architecturally the same on NWP. CFC fuses are shared with CFCIO. Confirm W/E domain topology.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`
2. Confirm NWP VCCCFCMEM W/E domain split (or single domain)
3. Verify NWP DTS sensor mapping for CFCMEM (catile repeated sensor)

**Priority**: Medium — DMR_PO; memory fabric voltage correctness
