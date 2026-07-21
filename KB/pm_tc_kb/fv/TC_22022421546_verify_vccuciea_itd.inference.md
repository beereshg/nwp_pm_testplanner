# Deep Analysis: [ITD] Verify VCCUCIEA ITD

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421546 |
| **Title** | [ITD] Verify VCCUCIEA ITD |
| **Date** | 2025-07-21 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | VCCUCIEA (UCIe PHY Analog FIVR) — iMH PrimeCode |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Version** | 2.0 |
| **Last Updated** | 2025-07-21 |

---


## Test Case Intent

Validates that VCCUCIEA (UCIe PHY Analog) ITD compensation is correctly applied across all 4 directional sub-domains (NW, NE, SW, SE). For each sub-domain: reads the current DTS temperature from the dedicated UCIe thermal topology sensor, reads the actual FIVR voltage from the resource controller workpoint, independently calculates the expected ITD offset using the dual-slope algorithm with per-domain fuse coefficients, and verifies that actual voltage matches expected (base + offset) within the 26 mV guardband.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

VCCUCIEA is a **fixed-frequency FIVR** for the UCIe PHY Analog. Like VCCFIXDIG, VCCUCIEA is **fused at Vhot — no ITD compensation is expected in production**. The test verifies that fuse checkout confirms zero slope and no compensation is applied at runtime. There are multiple VCCUCIEA domains: NW, SW, SE (directional placement of UCIe PHY blocks). The DTS source is `dts_ucie_b` (`rsrc_adapt_dtsucie_b`, RC_CFCMEM). On NWP, UCIe PHY Analog is present (UCIe D2D links between CBBs and CBB-to-IMH). The domain count and DTS placement may differ based on NWP die geometry. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- VCCUCIEA ITD via iMH PrimeCode present on NWP (UCIe PHY Analog rail)
- Fixed-frequency: fused at Vhot → ITD_SLOPE = 0 expected in production
- `logs,cmdline` tag: log capture + command-line output verification
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon with UCIe PHY links trained (D2D connectivity active)
- ITD fuses non-zero for VCCUCIEA domains (verified by TC 22022421521)
- PythonSv access to `sv.socket0.imh0.*`
- Test command: `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`

### Adapted Test Steps (from itd_pmx.py mainTest — RC class, rc_cfcmem_ew)

| Step | Action | Expected Result (PASS) | Failure Indication |
|------|--------|----------------------|-------------------|
| 1 | Load IMH fuse RAM and read shared ITD fuses: `itd_cutoff_tj`, `itd_min_override_temp`, `min_accurate_temp` | All three shared fuses readable and non-zero | Access fault or zero value in any shared fuse |
| 2 | For each VCCUCIEA sub-domain (NW, NE, SW, SE): read per-domain ITD fuses — slope, slope_2, cutoff_v, cutoff_v_2, cutoff_v_x | Per-domain slope and cutoff_v are non-zero; dual-slope fuses present if domain supports it | Zero slope or cutoff_v indicates unprogrammed fuse |
| 3 | Read each sub-domain's temperature from its thermal topology register (simple_domain_instances 8/9/10/11) | Temperature within valid operating range (−10°C to +110°C) | Temperature out of range or read failure |
| 4 | Read each sub-domain's actual voltage from the resource controller workpoint register (× 0.0025 V) | Voltage > 0 and within expected FIVR operating range (0.4–1.2 V) | Zero voltage or out-of-range value |
| 5 | Read fused base voltage for each sub-domain (non-GV fixed-frequency — no ratio lookup needed) | Base voltage matches fused `active_voltage` value | Mismatch or zero base voltage |
| 6 | Apply MIN_ACCURATE_TEMP guard: if temperature < min_accurate_temp, substitute min_override_temp | Guard correctly applied — effective temp used in calculation is ≥ min_accurate_temp | Guard not applied when temperature is below threshold |
| 7 | Calculate expected ITD offset using dual-slope algorithm: select slope based on voltage vs cutoff_v_x crossover; compute offset = slope × (cutoff_v − base_voltage) × (cutoff_tj − temperature) | Offset is non-negative when in ITD zone (temp < cutoff_tj and voltage < cutoff_v) | Negative offset in ITD zone or non-zero offset outside ITD zone |
| 8 | Compute expected voltage = base voltage + ITD offset | Expected voltage is within valid FIVR range | Expected voltage outside operating bounds |
| 9 | Compare expected vs actual voltage per sub-domain | Delta ≤ 26 mV for all 4 sub-domains (NW, NE, SW, SE) | Delta > 26 mV on any sub-domain — ITD compensation mismatch |
| 10 | Log per-sub-domain results table with columns: domain, IMH path, DTS, temperature, base volt, slope, offset, guardband, delta, expected, actual, PASS/FAIL | All rows show PASS | Any row shows FAIL |

### VCCUCIEA Domain Mapping (from itd_pmx.py)

| Sub-Domain | RC Name | Thermal Register | DTS Index |
|---|---|---|---|
| VCCUCIEA_NW | `vccuciea_nw` | `simple_domain_instances_9.min_temperature` | 59 |
| VCCUCIEA_NE | `vccuciea_ne` | `simple_domain_instances_8.min_temperature` | 58 |
| VCCUCIEA_SW | `vccuciea_sw` | `simple_domain_instances_11.min_temperature` | 61 |
| VCCUCIEA_SE | `vccuciea_se` | `simple_domain_instances_10.min_temperature` | 60 |

### Pass / Fail Criteria
- **PASS**: All 4 VCCUCIEA sub-domains (NW, NE, SW, SE) have actual voltage matching expected (base + ITD offset) within 26 mV guardband; per-domain ITD fuses are non-zero (slope, cutoff_v); temperature telemetry from dedicated UCIe DTS reflects valid operating range (−10°C to +110°C)
- **FAIL**: Any sub-domain voltage delta exceeds 26 mV, OR any per-domain ITD fuse is zero when non-zero expected, OR temperature reading out of valid range

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| VCCUCIEA domains | NW, NE, SW, SE (4 domains) | **NW, NE, SW, SE (4 domains) — CONFIRMED** | No change; identical domain count confirmed from NWP baby-steps FIVR modules and itd_pmx.py |
| ITD slope | 0 (fused at Vhot, production) | Same expectation — fixed-freq rail fused at Vhot | No change |
| DTS source | `dts_ucie_b` at RC_CFCMEM_EW | Same DTS family — `simple_domain_instances_8/9/10/11` | Confirmed identical mapping |
| XML config | `dmr.xml` | `nwp.xml` | **Must update** |
| FIVR controller path | `sv.socket0.imh0.fivrhip.fivr_vccuciea_{nw,ne,sw,se}` | Same path — **CONFIRMED** on NWP (both die0/die1) | No change |
| RC path | `imh.resctrl.rc_cfcmem_ew.resctrl_prvt_wp_regs.vr_wp_cv[N].voltage` | Same RC — **CONFIRMED** in NWP pkgc.py and itd_pmx.py | No change |
| FIVR type | DCFCI (ViNF-gated analog FIVR) | Same type — fivrhip_dcfci_vinfgated hierarchy confirmed | No change |
| Dual-slope fuses | `cutoff_v_2`, `cutoff_v_x`, `slope_2` set to 0 for VCCUCIEA (single slope only) | Same — code skips dual-slope for cfcmem_ew domains | No change |
| Idle workpoint | `rc_cfcmem_ew.resctrl_prvt_wp_regs.vr_wp_idle[1..4]` | Confirmed in NWP pkgc.py `check_VCCUCIEA()` | No change |

### NWP Evidence Sources
- **NWP itd_pmx.py** (line 740): `rc_names= ["vccuciea_nw", "vccuciea_ne", "vccuciea_sw", "vccuciea_se"]`
- **NWP baby-steps modules**: `fivr_vccuciea_{nw,ne,sw,se}_skt0_die{0,1}.py` all present in `pdi_dev_tools/applications/fuse_tools/apps/fuse_based_baby_steps/babysteps_modules/`
- **NWP pkgc.py** (line 711-735): `check_VCCUCIEA()` reads all 4 domains via `rc_cfcmem_ew.resctrl_prvt_wp_regs.vr_wp_idle[1..4]`
- **NWP pkgc_pmx.py** (line 1123): `test_check_VCCUCIEA()` test method present
- **Co-Design Spec**: Confirmed 4 domains (NW, NE, SW, SE), each mapped to local UCIe DTS sensor

---

## Section D: Key Registers & Validation Points

### Register Paths (NWP Confirmed)

| Register | Path | Purpose |
|----------|------|---------|
| FIVR Controller (NW) | `sv.socket0.imh0.fivrhip.fivr_vccuciea_nw` | Physical FIVR controller for NW UCIe PHY analog |
| FIVR Controller (NE) | `sv.socket0.imh0.fivrhip.fivr_vccuciea_ne` | Physical FIVR controller for NE UCIe PHY analog |
| FIVR Controller (SW) | `sv.socket0.imh0.fivrhip.fivr_vccuciea_sw` | Physical FIVR controller for SW UCIe PHY analog |
| FIVR Controller (SE) | `sv.socket0.imh0.fivrhip.fivr_vccuciea_se` | Physical FIVR controller for SE UCIe PHY analog |
| Active Voltage WP (NW) | `imh.resctrl.rc_cfcmem_ew.resctrl_prvt_wp_regs.vr_wp_cv[1].voltage` | NW voltage × 0.0025V |
| Active Voltage WP (NE) | `imh.resctrl.rc_cfcmem_ew.resctrl_prvt_wp_regs.vr_wp_cv[2].voltage` | NE voltage × 0.0025V |
| Active Voltage WP (SW) | `imh.resctrl.rc_cfcmem_ew.resctrl_prvt_wp_regs.vr_wp_cv[3].voltage` | SW voltage × 0.0025V |
| Active Voltage WP (SE) | `imh.resctrl.rc_cfcmem_ew.resctrl_prvt_wp_regs.vr_wp_cv[4].voltage` | SE voltage × 0.0025V |
| Idle Voltage WP (NW) | `imh.resctrl.rc_cfcmem_ew.resctrl_prvt_wp_regs.vr_wp_idle[1].voltage` | NW idle voltage × 2.5mV |
| Idle Voltage WP (NE) | `imh.resctrl.rc_cfcmem_ew.resctrl_prvt_wp_regs.vr_wp_idle[2].voltage` | NE idle voltage × 2.5mV |
| Idle Voltage WP (SW) | `imh.resctrl.rc_cfcmem_ew.resctrl_prvt_wp_regs.vr_wp_idle[3].voltage` | SW idle voltage × 2.5mV |
| Idle Voltage WP (SE) | `imh.resctrl.rc_cfcmem_ew.resctrl_prvt_wp_regs.vr_wp_idle[4].voltage` | SE idle voltage × 2.5mV |
| DTS Temp (NW) | `imh.pcudata.thermaltopo_instance.simple_domain_instances_9.min_temperature` | NW UCIe DTS sensor |
| DTS Temp (NE) | `imh.pcudata.thermaltopo_instance.simple_domain_instances_8.min_temperature` | NE UCIe DTS sensor |
| DTS Temp (SW) | `imh.pcudata.thermaltopo_instance.simple_domain_instances_11.min_temperature` | SW UCIe DTS sensor |
| DTS Temp (SE) | `imh.pcudata.thermaltopo_instance.simple_domain_instances_10.min_temperature` | SE UCIe DTS sensor |
| ITD Cutoff TJ | `imh.fuses.punit.pcode_itd_cutoff_tj` | Shared temperature threshold (U7.0 format) |
| ITD Min Override | `imh.fuses.punit.pcode_itd_min_override_temp` | Override temp when below min_accurate (S6.0) |
| Min Accurate Temp | `imh.fuses.punit.pcode_min_accurate_temp` | DTS reliability threshold (S6.0) |
| Active Voltage Fuse (NW) | `imh.fuses.punit.pcode_vccuciea_nw_active_voltage` | Fused base voltage (U1.8 format) |
| Active Voltage Fuse (NE) | `imh.fuses.punit.pcode_vccuciea_ne_active_voltage` | Fused base voltage (U1.8 format) |
| Active Voltage Fuse (SW) | `imh.fuses.punit.pcode_vccuciea_sw_active_voltage` | Fused base voltage (U1.8 format) |
| Active Voltage Fuse (SE) | `imh.fuses.punit.pcode_vccuciea_se_active_voltage` | Fused base voltage (U1.8 format) |
| ITD Slope Fuse (NW) | `imh.fuses.punit.pcode_vccuciea_nw_itd_slope` | Per-domain ITD slope (U8.13 format) |
| ITD Cutoff_V Fuse (NW) | `imh.fuses.punit.pcode_vccuciea_nw_itd_cutoff_v` | Per-domain voltage cutoff (U1.8 format) |

### ITD Algorithm (Spec-Confirmed Pseudo-code)

```plaintext
if (TEMP < FUSED_MIN_ACCURATE_TEMP)
    TEMP = FUSED_ITD_MIN_OVERRIDE_TEMP
DELTA_TEMP = FUSE.ITD_CUTOFF_TJ - TEMP
CUTOFF_V = (VOLTAGE < FUSE.ITD_CUTOFF_V_X) ? FUSE.ITD_CUTOFF_V : FUSE.ITD_CUTOFF_V_2
DELTA_VOLT = CUTOFF_V - VOLTAGE
ITD_SLOPE = (VOLTAGE < FUSE.ITD_CUTOFF_V_X) ? FUSE.ITD_SLOPE_1 : FUSE.ITD_SLOPE_2
if (DELTA_VOLT > 0 && DELTA_TEMP > 0)
    VOLT_COMP_VALUE = ITD_SLOPE * DELTA_VOLT * DELTA_TEMP
else
    VOLT_COMP_VALUE = 0
```

### Fuse Format Summary

| Fuse | Format | Unit | Notes |
|------|--------|------|-------|
| `active_voltage` | U1.8 | V | Fixed base voltage for VCCUCIEA |
| `itd_slope` | U8.13 | V/(V·°C) | Single slope (slope_2 = 0 for VCCUCIEA) |
| `itd_cutoff_v` | U1.8 | V | Voltage threshold |
| `itd_cutoff_tj` | U7.0 | °C | Temperature threshold (shared across IMH) |
| `min_accurate_temp` | S6.0 | °C | DTS reliability floor |
| `min_override_temp` | S6.0 | °C | Substitute when DTS unreliable |

### Quick Validation Script (PythonSV)

```python
from pm.focus import itd

# Print ITD info — all VCCUCIEA domains should show slope=0 (fused at Vhot)
itd.print_itd_info(0, 0)

# Read VCCUCIEA workpoints directly
for i, domain in enumerate(["vccuciea_nw", "vccuciea_ne", "vccuciea_sw", "vccuciea_se"]):
    # Active voltage
    v_active = sv.socket0.imh0.resctrl.rc_cfcmem_ew.resctrl_prvt_wp_regs.vr_wp_cv[i+1].voltage * 0.0025
    # Idle voltage
    v_idle = sv.socket0.imh0.resctrl.rc_cfcmem_ew.resctrl_prvt_wp_regs.vr_wp_idle[i+1].voltage * 0.0025
    # Fused active voltage
    v_fuse = sv.socket0.imh0.fuses.punit.getbypath(f"pcode_{domain}_active_voltage")
    # ITD slope (expect 0 for production)
    slope = sv.socket0.imh0.fuses.punit.getbypath(f"pcode_{domain}_itd_slope")
    print(f"{domain.upper():15s} | Active: {v_active:.4f}V | Idle: {v_idle:.4f}V | Fuse: 0x{v_fuse:04X} | Slope: {slope}")

# DTS temperatures for UCIe domains
for idx, name in [(9, "NW"), (8, "NE"), (11, "SW"), (10, "SE")]:
    temp = sv.socket0.imh0.pcudata.thermaltopo_instance.getbypath(f"simple_domain_instances_{idx}.min_temperature")
    print(f"DTS UCIe {name}: {temp}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Status | Notes |
|---|----------------|----------|--------|-------|
| 1 | ~~NWP VCCUCIEA domain count~~ | ~~Low~~ | **RESOLVED** | Confirmed 4 domains (NW, NE, SW, SE) from NWP code and spec — identical to DMR |
| 2 | **Non-zero slope corner case** — pre-production parts may have non-zero slope | Low | Open | Expected behavior that validates ITD framework is functional; production parts fused at Vhot with slope=0 |
| 3 | **DTS index mapping stability** — DTS indices (58-61) confirmed in itd_pmx.py but not yet validated on NWP silicon | Low | Open | Verify on first NWP silicon bring-up |
| 4 | **Dual-slope disabled for VCCUCIEA** — code explicitly sets `cutoff_v_2 = 0, cutoff_v_x = 0, slope_2 = 0` | Info | Confirmed | By design: fixed-freq domains use single-slope only |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; CONFIRMED 4 UCIe PHY domains identical to DMR**

VCCUCIEA ITD is "fused at Vhot" architecture identical on NWP. Zero slope/offset verification is straightforward. All register paths, RC mappings, DTS indices, and FIVR controllers have been confirmed present and identical on NWP.

### Required Adaptations:
1. `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`
2. ✅ NWP VCCUCIEA domain names confirmed: NW, NE, SW, SE (4 domains)
3. ✅ NWP UCIe DTS (`dts_ucie_b`) sensor placement confirmed: indices 58-61
4. ✅ FIVR controller path confirmed: `sv.socket0.imh{0,1}.fivrhip.fivr_vccuciea_{nw,ne,sw,se}`

### Related TCs in NWP:
- **TC 22022421521**: ITD fuse checkout (prerequisite — verifies fuses are programmed)
- **pkgc_pmx.py `test_check_VCCUCIEA()`**: Idle state VCCUCIEA verification (HSD 14019738574)
- **pkgc.py `check_VCCUCIEA()`**: Standalone VCCUCIEA voltage check utility

### Interaction with Other Features:
- **PkgC**: During package C-state entry, VCCUCIEA idle voltage must match active WP (no voltage reduction for UCIe PHY analog)
- **D2D Link Training**: UCIe PHY links must be trained before ITD verification (VCCUCIEA powers the analog PHY)
- **FIVR Health Indicators**: Each VCCUCIEA FIVR has full HI (Health Indicator) monitoring via `fivrhip_dcfci_vinfgated.hi_config1/hi_config2`

**Priority**: Medium — `logs,cmdline` bring-up verification; fixed-frequency rail fuse check
**Confidence**: HIGH — all technical details verified from NWP codebase and spec

---

### Post-Process

N/A

## References
- [ITD HAS — DMR IMH Thermal](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html)
- [NWP CFC HAS — UCIe PHY Domains](https://docs.intel.com/documents/pm_doc/src/NWP_IMH/HAS/Thermal/)
- [TC 22022421521 — ITD Fuse Checkout (Prerequisite)](https://hsdes.intel.com/appstore/article-one/#/22022421521)
- [HSD 14019738574 — check_VCCUCIEA PkgC Verification](https://hsdes.intel.com/appstore/article-one/#/14019738574)
