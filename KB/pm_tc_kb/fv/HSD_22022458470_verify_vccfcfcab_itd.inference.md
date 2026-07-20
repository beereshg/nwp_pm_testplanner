# Deep Analysis: [ITD] Verify VCCFCFCAB ITD

| Field | Value |
|-------|-------|
| **HSD ID** | 22022458470 |
| **Title** | [ITD] Verify VCCFCFCAB ITD |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) / NWP-native |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | VCCFCFCAB (CAB — Customer Accelerator Block FIVR) — NWP-native new domain |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates the VCCFCFCAB (NWP-native CAB domain) ITD compensation scenario defined in [TCD 16031170073 — Fabric/IO Rail ITD](https://hsdes.intel.com/appstore/article-one/#/16031170073) §5. Environment: NWP post-silicon, FV.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

**This is a NWP-native new ITD domain.** VCCFCFCAB is the FIVR for the CAB (Customer Accelerator Block), a new digital domain specific to NWP. Per the ITD KB (NWP MAS §3): *"ITD on new digital domain [VCCFCFCAB]. No change to ITD support on existing DMR rails."* This TC was created as a placeholder specifically for NWP bring-up. The test steps reference Simics as the initial verification strategy. The VCCFCFCAB is controlled by iMH PrimeCode, consistent with other iMH-managed fabric FIVRs (CFCIO, CFCMEM). This TC is inherently NWP-focused and should be prioritized for NWP silicon bring-up.

**Key Justification:**
- VCCFCFCAB is a NWP-native new domain — this test has no DMR equivalent
- `DMR_PO` sub_feature likely indicates priority carry-over from DMR framework; NWP team should own
- `PMSS_NWP_READINESS_CHECK` tag: explicitly NWP-targeted
- Simics verification first, then silicon
- Test steps describe placeholder with Acode/PCode dependency (Patch23)

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP Simics model with VCCFCFCAB modeled (or NWP silicon with CAB active)
- Acode, PCode, and Patch23 available in NWP firmware
- PythonSv access to `sv.socket0.imh0.punit.*` for ITD compensation registers

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Verify VCCFCFCAB ITD is enabled in NWP PCode | Check NWP PCode MAS for VCCFCFCAB ITD domain configuration |
| 2 | Run ITD thermal test | `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3` |
| 3 | Verify ITD compensation is congruent with expected: `itd.print_itd_info(0, 0)` shows VCCFCFCAB domain | New domain — verify it appears in `print_itd_info` output |
| 4 | Calculate expected ITD compensation per ITD HAS formula | Use `pcode_cfc_itd_slope/slope_2/cutoff_v` (or CAB-specific fuses if dedicated) |
| 5 | Compare calculated vs. actual VCCFCFCAB RC voltage offset | `sv.socket0.imh0.punit.resctrl_cr_vccfcfcab_v_offset.read()` |
| 6 | Verify on Simics first, then silicon validation | Simics validation is primary strategy per TC |

### Key Difference from Other iMH ITD Domains

VCCFCFCAB is a GV-supported FIVR (per KB: "GV | TBD" dual-slope). Unlike VCCFIXDIG/VCCUCIEA which are fused at Vhot with zero slope, VCCFCFCAB is expected to have **active ITD compensation** tracking temperature variation.

### NWP Pass Criteria
- VCCFCFCAB RC voltage offset is non-zero and tracks temperature
- Calculated ITD compensation matches `itd.print_itd_info` output
- Acode (CAB) and PCode collaborate correctly on VCCFCFCAB voltage management

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| VCCFCFCAB | Does not exist on DMR | NWP-native new domain | TC is NWP-only — no DMR baseline to compare |
| GV support | N/A | Yes (GV-supported FIVR) | Active ITD compensation expected |
| ITD fuses | N/A | CAB-specific or shared CFC fuses (TBD per NWP HAS) | Verify with NWP PM team |
| Controller | N/A | iMH PrimeCode (consistent with other fabric rails) | Follow CFCIO/CFCMEM pattern |
| Simics | Primary verification | Simics first, then silicon | Coordinate with simulation team |

---

## Section D: Key Registers & Validation Points

```python
from pm.focus import itd

SockNum = 0

# Print ITD info — VCCFCFCAB should appear as a new domain
print("=== VCCFCFCAB ITD Validation (NWP-native) ===")
itd.print_itd_info(SockNum, 0)

# VCCFCFCAB RC voltage offset
try:
    cab_offset = sv.socket0.imh0.punit.getbypath("resctrl_cr_vccfcfcab_v_offset").read()
    print(f"VCCFCFCAB V_OFFSET: {cab_offset}")
except Exception as e:
    # Try alternate naming convention
    try:
        cab_offset = sv.socket0.imh0.punit.getbypath("resctrl_cr_fcfcab_v_offset").read()
        print(f"VCCFCFCAB V_OFFSET: {cab_offset}")
    except Exception as e2:
        print(f"VCCFCFCAB: {e2} (register path TBD for NWP)")

# VCCFCFCAB ITD fuses (may be CAB-specific or shared with CFC)
try:
    # Try CAB-specific fuse first
    cab_slope = sv.socket0.imh0.fuses.punit.pcode_cab_itd_slope.read()
    print(f"CAB ITD Slope: {cab_slope}")
except Exception:
    # Fall back to CFC shared fuses
    try:
        cfc_slope = sv.socket0.imh0.fuses.punit.pcode_cfc_itd_slope.read()
        print(f"CFC ITD Slope (shared?): {cfc_slope}")
    except Exception as e:
        print(f"ITD fuses: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP-native domain — no DMR baseline** — this TC has no DMR implementation to reference; NWP team must develop test methodology from scratch | High | TC is WIP placeholder; coordinate with NWP iMH team |
| 2 | **VCCFCFCAB ITD fuse set** — unknown if CAB has dedicated ITD fuses or shares CFC fuses; check NWP PCode MAS | High | Critical for test calculation validation |
| 3 | **Simics model maturity** — TC specifies Simics as primary verification; confirm NWP CAB is modeled with FIVR/ITD | Medium | Coordinate with simulation team |
| 4 | **Patch23 dependency** — test steps mention "Acode, PCode, Patch23"; confirm Patch23 support in NWP firmware | Medium | Verify with NWP firmware team |

---

## Section F: Recommendation

**Recommendation: NWP-NATIVE — develop test from scratch; Simics first**

This is the only ITD TC that is NWP-specific. No DMR baseline. Use CFCIO/CFCMEM pattern as template.

Required adaptations:
1. Develop VCCFCFCAB ITD test methodology (use CFCIO pattern as reference)
2. Confirm VCCFCFCAB ITD fuse set from NWP PCode MAS
3. Simics validation first; silicon validation after NWP bring-up
4. `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3` (adapt plugin if needed)

**Priority**: High — NWP-native new domain; must be developed fresh for NWP validation
