# Deep Analysis: [ITD] Verify VCCUCIEA ITD

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421546 |
| **Title** | [ITD] Verify VCCUCIEA ITD |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | VCCUCIEA (UCIe PHY Analog FIVR) — iMH PrimeCode |
| **NWP Disposition** | **Runnable_On_N-1** |

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

### NWP Pass Criteria
- All 4 VCCUCIEA sub-domains: actual voltage matches expected (base + ITD offset) within 26 mV
- Per-domain ITD fuses are non-zero (slope, cutoff_v) — if zero, flag as fuse programming issue
- Temperature telemetry from dedicated UCIe DTS reflects realistic thermal conditions

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| VCCUCIEA domains | NW, SW, SE (3 domains) | NWP UCIe PHY placement (verify) | Confirm domain count from NWP CFC HAS |
| ITD slope | 0 (fused at Vhot) | Same expectation | No change |
| DTS source | `dts_ucie_b` at RC_CFCMEM | Same DTS family (verify NWP) | Confirm NWP UCIe DTS mapping |
| XML config | `dmr.xml` | `nwp.xml` | **Must update** |

---

## Section D: Key Registers & Validation Points

```python
from pm.focus import itd

# Print ITD info — all VCCUCIEA domains should show 0
itd.print_itd_info(0, 0)

# VCCUCIEA RC offsets (expect 0 for fixed-freq domain)
for domain in ["vccuciea_nw", "vccuciea_sw", "vccuciea_se"]:
    try:
        offset = sv.socket0.imh0.punit.getbypath(f"resctrl_cr_{domain}_v_offset").read()
        status = "PASS (zero)" if offset == 0 else f"UNEXPECTED ({offset})"
        print(f"VCCUCIEA {domain.upper()} V_OFFSET: {offset} [{status}]")
    except Exception as e:
        print(f"VCCUCIEA {domain}: {e}")

# UCIe DTS read
try:
    dts_ucie = sv.socket0.imh0.punit.getbypath("rsrc_adapt_dtsucie_b").read()
    print(f"DTS UCIe_B: 0x{dts_ucie:08X}")
except Exception as e:
    print(f"DTS UCIe_B: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP VCCUCIEA domain count** — NW/SW/SE on DMR; NWP UCIe PHY placement may differ | Low | Verify from NWP CFC/UCIe HAS |
| 2 | **Non-zero slope corner case** — pre-production parts may have non-zero slope; expected failure that validates ITD framework | Low | Flag to NWP PM team |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify UCIe PHY domain count**

VCCUCIEA ITD is "fused at Vhot" architecture identical on NWP. Zero slope/offset verification is straightforward.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`
2. Confirm NWP VCCUCIEA domain names (NW/SW/SE or different layout)
3. Verify NWP UCIe DTS (`dts_ucie_b`) sensor placement

**Priority**: Medium — `logs,cmdline` bring-up verification; fixed-frequency rail fuse check
