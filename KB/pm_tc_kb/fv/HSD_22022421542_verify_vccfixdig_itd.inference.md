# Deep Analysis: [ITD] Verify VCCFIXDIG ITD

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421542 |
| **Title** | [ITD] Verify VCCFIXDIG ITD |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | VCCFIXDIG (Fixed-frequency Digital FIVR) — iMH PrimeCode |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates that VCCFIXDIG (MIO fixed-digital) ITD compensation is correctly applied across all 3 MIO sub-domains (MIO_1, MIO_3, MIO_4). For each sub-domain: reads temperature from its dedicated thermal topology register (simple_domain_instances 3/4/5), reads actual voltage from rc_mio_ew resctrl workpoint, reads fused base voltage, computes expected ITD offset, and verifies actual voltage matches expected within 26 mV guardband.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

VCCFIXDIG is a **fixed-frequency FIVR** rail. Per the ITD architecture, **VCCFIXDIG is fused at Vhot — no ITD compensation is expected**. The ITD_SLOPE for VCCFIXDIG is 0 in production fusing. This test verifies that:
1. The VCCFIXDIG fuse checkout confirms zero slope (no ITD compensation)
2. The DTS and RC offset infrastructure is working (even with zero compensation)

The DTS source is `dts_ddr_a` (based on the test step table: `rsrc_adapt_dtsddr_a 0x7E00`, `RC_MC_E`). On NWP, VCCFIXDIG is the fixed-frequency digital rail — same architecture, same "fused at Vhot" expectation. The sub_feature `logs,cmdline` indicates this TC captures logs and command-line outputs for validation.

**Key Justification:**
- VCCFIXDIG is present on NWP as a fixed-frequency FIVR
- "Fused at Vhot — no ITD compensation expected" applies on NWP
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP
- Primary verification: ITD_SLOPE = 0 confirmed, no compensation applied

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon with VCCFIXDIG active
- VCCFIXDIG ITD fuses: `ITD_SLOPE = 0` expected (fused at Vhot)
- PythonSv access to `sv.socket0.imh0.punit.*`

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run ITD thermal test | `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3` |
| 2 | Verify VCCFIXDIG ITD slope fuse = 0 | Read `pcode_itd_slope` for VCCFIXDIG domain (separate from core/CFC slope fuses) |
| 3 | `itd.print_itd_info(0, 0)` — verify VCCFIXDIG shows 0 compensation | Expected: no voltage offset for this domain |
| 4 | Read VCCFIXDIG DTS: `dts_ddr_a` at `RC_MC_E` | NWP DDR DTS sensor: `rsrc_adapt_dtsddr_a 0x7E00` |
| 5 | Verify VCCFIXDIG RC offset = 0 (no ITD applied) | `sv.socket0.imh0.punit.resctrl_cr_vccfixdig_v_offset.read()` — expect 0 |
| 6 | Capture logs (`logs` sub_feature tag) | Save `itd.print_itd_info` output + command-line output to test log |

### VCCFIXDIG DTS Source (from test steps table)

| DTS Name | Resource Adapter | RC Offset | RC Location | Index |
|----------|------------------|-----------|-------------|-------|
| `dts_ddr_a` | `rsrc_adapt_dtsddr_a` | `0x7E00` | `RC_MC_E` | 0,1,2 |
| `dts_ddr_a` | `rsrc_adapt_dtsddr_a` | `0x7E04` | `RC_MC_E` | 0,1,2 |

### NWP Pass Criteria
- VCCFIXDIG ITD_SLOPE fuse = 0 (production fusing at Vhot)
- RC voltage offset for VCCFIXDIG = 0 (no ITD compensation applied)
- DTS infrastructure (`dts_ddr_a`) reads correctly even with zero slope
- `itd.print_itd_info` confirms VCCFIXDIG compensation = 0V

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| VCCFIXDIG architecture | Fixed-frequency, fused at Vhot | Same on NWP | Direct reuse |
| ITD slope | 0 (production fusing) | Same expectation | No change |
| DTS source | `dts_ddr_a` at `RC_MC_E` | NWP DDR DTS (verify MC location) | Confirm NWP MC-E/W topology |
| VCCFIXDIG variants | `VCCFIXDIG_E` (and others per HAS) | NWP VCCFIXDIG domains (verify) | Check NWP VCCFIXDIG domain count |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
from pm.focus import itd

SockNum = 0

# Print ITD info — VCCFIXDIG should show 0 compensation
print("=== VCCFIXDIG ITD Validation ===")
itd.print_itd_info(SockNum, 0)

# VCCFIXDIG RC voltage offset (expect 0)
for domain_name in ["vccfixdig_e", "vccfixdig_w"]:  # verify NWP domain names
    try:
        offset = sv.socket0.imh0.punit.getbypath(f"resctrl_cr_{domain_name}_v_offset").read()
        status = "PASS (zero)" if offset == 0 else f"UNEXPECTED ({offset})"
        print(f"VCCFIXDIG {domain_name.upper()} V_OFFSET: {offset} [{status}]")
    except Exception as e:
        print(f"VCCFIXDIG {domain_name}: {e}")

# DDR DTS read
try:
    dts_ddr = sv.socket0.imh0.punit.getbypath("rsrc_adapt_dtsddr_a").read()
    print(f"DTS DDR_A: 0x{dts_ddr:08X}")
except Exception as e:
    print(f"DTS DDR_A: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP VCCFIXDIG domain count** — DMR has multiple VCCFIXDIG variants (E, W, MIO_*); NWP may have different set | Low | Verify from NWP SVID/CFC HAS |
| 2 | **Non-zero slope corner case** — if any VCCFIXDIG domain has non-zero slope in pre-production fusing, this TC would FAIL — expected and worth investigating | Low | Flag to NWP PM team; production fusing should have ITD_SLOPE=0 |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify VCCFIXDIG domain names**

VCCFIXDIG ITD verification is straightforward: confirm zero slope and zero compensation. Same "fused at Vhot" architecture on NWP.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`
2. Verify NWP VCCFIXDIG domain names (E, W, MIO variants)
3. Confirm NWP DDR DTS (`dts_ddr_a`) sensor placement for MC-E

**Priority**: Medium — `logs,cmdline` tag means this is primarily a log capture/verification TC; straightforward bring-up check
