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

Validates the VCCUCIEA (UCIe A-side) ITD compensation scenario defined in [TCD 16031170073 — Fabric/IO Rail ITD](https://hsdes.intel.com/appstore/article-one/#/16031170073) §5. Environment: NWP post-silicon, FV.

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
- NWP silicon with UCIe PHY Analog active (D2D links trained)
- VCCUCIEA ITD fuse: `ITD_SLOPE = 0` expected (fused at Vhot)
- PythonSv access to `sv.socket0.imh0.punit.*`

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run ITD thermal test | `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3` |
| 2 | Verify VCCUCIEA ITD slope fuse = 0 for each domain (NW, SW, SE variants) | Read slope fuses; expect 0 for each VCCUCIEA domain |
| 3 | `itd.print_itd_info(0, 0)` shows VCCUCIEA domains with 0 compensation | Verify all VCCUCIEA_* show 0V offset |
| 4 | Read VCCUCIEA DTS: `dts_ucie_b` at RC_CFCMEM | `rsrc_adapt_dtsucie_b 0x7E00` — NWP UCIe DTS placement |
| 5 | Verify RC offset = 0 for all VCCUCIEA domains | `imh0.punit.resctrl_cr_vccuciea_{nw|sw|se}_v_offset` |
| 6 | Capture logs and command-line output | Save to test log |

### VCCUCIEA DTS Source (from test steps)

| DTS Name | Resource Adapter | RC Offset | RC Location | Index |
|----------|------------------|-----------|-------------|-------|
| `dts_ucie_b` | `rsrc_adapt_dtsucie_b` | `0x7E00` | `RC_CFCMEM` | 0,1,2 |

NWP: Confirm VCCUCIEA_NW/SW/SE domain count based on NWP UCIe PHY placement.

### NWP Pass Criteria
- All VCCUCIEA domains: ITD_SLOPE fuse = 0
- RC voltage offset = 0 (no ITD compensation applied)
- `itd.print_itd_info` confirms 0V for all VCCUCIEA domains

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
