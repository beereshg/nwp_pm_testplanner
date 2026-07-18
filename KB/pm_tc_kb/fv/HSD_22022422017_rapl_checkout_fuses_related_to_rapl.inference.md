# TC Description: RAPL - Checkout Fuses Related to RAPL

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422017](https://hsdes.intel.com/appstore/article-one/#/22022422017) |
| **Title** | RAPL - Checkout fuses related to RAPL |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL fuse checkout — verify fuse-driven capability values in PL_INFO |
| **Parent TCD** | [22022420813 -- Socket RAPL Fuse and BIOS Knobs](https://hsdes.intel.com/appstore/article-one/#/22022420813) |
| **Owner** | mps |
| **Status** | open / ready_for_content_review |
| **Priority** | 2-high |
| **Tags** | `DMR_PO`, `PMSS_NWP_READINESS_CHECK` |
| **Val Environment** | silicon, virtual_platform |
| **Val Framework** | os-svos, python-sv |
| **Automation** | `flexconPM.py -c NWPSV.ini` |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Cache version** | 3 |

---

## Test Case Intent

Validates the **fuse checkout** scenario defined in [TCD 22022420813 -- Socket RAPL Fuse and BIOS Knobs](https://hsdes.intel.com/appstore/article-one/#/22022420813) §5, row "Fuse checkout": "PL_INFO.MAX_PL1 = fused TDP; MAX_PL2 = 1.2 x TDP; MIN_PL non-zero; values match silicon fuse programming." PrimeCode reads RAPL capability fuses at PH6 and populates TPMI PL_INFO. This TC reads the raw fuse values and compares them to the TPMI PL_INFO register fields to verify correct fuse-to-register propagation. Legacy MSR 0x606 is deprecated on NWP — reads return 0 and must not be used for power unit discovery.

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon system or VP (Simics) |
| OS / Driver | SVOS with PythonSV environment |
| BIOS | Default BIOS settings; no custom PL overrides |
| Tool | flexconPM.py accessible with NWPSV.ini config |
| Starting state | System booted; PrimeCode has completed PH6 initialization |
| TPMI PL_INFO path | sv.socket0.nio.punit.tpmi.socket_rapl.pl_info |
| Power encoding | U11.3 format: 1 LSB = 0.125 W |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Run flexconPM fuse checkout: flexconPM.py -c NWPSV.ini. This reads all RAPL-related fuses and compares them to the corresponding register values. | flexconPM reports all RAPL fuse-to-register checks PASS. | Any fuse-to-register mismatch flagged by flexconPM. |
| 2 | Read TPMI PL_INFO.MAX_PL1 [17:0] via sv.socket0.nio.punit.tpmi.socket_rapl.pl_info. Compare to expected fused TDP for this NWP SKU. | MAX_PL1 = fused Socket TDP value (U11.3 encoding, e.g., 350W = 0xAF0). | MAX_PL1 does not match expected fused TDP. |
| 3 | Read TPMI PL_INFO.MAX_PL2 [53:36]. Verify = 1.2 x MAX_PL1. | MAX_PL2 = 1.2 x fused TDP (within 1 LSB rounding tolerance). | MAX_PL2 deviates from 1.2x TDP by more than 1 LSB. |
| 4 | Read TPMI PL_INFO.MIN_PL [35:18]. Verify non-zero and less than MAX_PL1. | MIN_PL > 0 and MIN_PL < MAX_PL1. Represents minimum supported power limit for this SKU. | MIN_PL = 0 (uninitialized) or MIN_PL >= MAX_PL1. |
| 5 | Read TPMI POWER_UNIT register. Verify power unit encoding matches expected (U11.3 = 3 fractional bits = power unit = 8). | POWER_UNIT reflects correct fractional bit count for U11.3 encoding. | Power unit mismatch — calculations would produce wrong wattage. |
| 6 | Read CSR package_power_sku (sv.socket0.nio.punit.ptpcioregs.ptpcioregs.package_power_sku). Verify pkg_tdp, pkg_min_pwr, pkg_max_pwr fields match TPMI PL_INFO values. | CSR fields match TPMI PL_INFO: pkg_tdp = MAX_PL1, pkg_min_pwr = MIN_PL, pkg_max_pwr = MAX_PL2. | CSR/TPMI mismatch on any capability field. |
| 7 | Read deprecated MSR 0x606 (IA32_PKG_POWER_SKU_UNIT). Verify returns 0. | MSR 0x606 reads 0. Deprecated on NWP — must not be used for power unit discovery. | MSR 0x606 returns non-zero value (not properly deprecated). |
| 8 | Write to deprecated MSR 0x610 (IA32_PKG_RAPL_LIMIT). Read back TPMI PL1_CONTROL. Verify TPMI value unchanged. | MSR write silently dropped; TPMI PL1_CONTROL unchanged from pre-write value. | TPMI value changed after deprecated MSR write. |

### Pass / Fail Criteria

- **PASS**: Per TCD 22022420813 §5 — PL_INFO.MAX_PL1 = fused TDP for SKU. PL_INFO.MAX_PL2 = 1.2 x TDP (within 1 LSB). PL_INFO.MIN_PL non-zero and < MAX_PL1. CSR package_power_sku matches TPMI PL_INFO. POWER_UNIT encoding correct. Deprecated MSR 0x606 reads 0. Deprecated MSR 0x610 write has no effect on TPMI. flexconPM reports all checks PASS.
- **FAIL**: Any PL_INFO field does not match expected fuse value. CSR/TPMI capability mismatch. Deprecated MSR not properly deprecated. flexconPM reports any failure.

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| TPMI PL_INFO | sv.socket0.nio.punit.tpmi.socket_rapl.pl_info | MAX_PL1 = fused TDP; MAX_PL2 = 1.2x TDP; MIN_PL > 0 |
| TPMI POWER_UNIT | sv.socket0.nio.punit.tpmi.socket_rapl.power_unit | Correct U11.3 encoding |
| CSR package_power_sku | sv.socket0.nio.punit.ptpcioregs.ptpcioregs.package_power_sku | Matches TPMI PL_INFO fields |
| MSR 0x606 | rdmsr 0x606 | Returns 0 (deprecated) |
| MSR 0x610 | wrmsr 0x610 then read TPMI | TPMI unchanged (write silently dropped) |

### Post-Process

N/A

### References

- [TCD 22022420813 -- Socket RAPL Fuse and BIOS Knobs](https://hsdes.intel.com/appstore/article-one/#/22022420813)
- [Wave 3 Common HAS -- Socket RAPL](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html)
- [DMR RAPL Simplification](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_rapl_simplification.html)
- [PrimeCode RAPL DMR](https://docs.intel.com/documents/primecode/primecode_one/firmware%20architecture/ip%20drivers%20and%20libraries/rapl_dmr.html)

---

## Section A: NWP Delta

NWP carries forward DMR fuse structure and TPMI PL_INFO register layout. NIO replaces IMH as root die.

| Aspect | DMR | NWP |
|--------|-----|-----|
| TPMI PL_INFO | sv.socket0.imh0.punit.tpmi.socket_rapl.pl_info | sv.socket0.nio.punit.tpmi.socket_rapl.pl_info |
| flexconPM config | DMRSV.ini | NWPSV.ini |
| MSR 0x606 | Deprecated (reads 0) | Deprecated (reads 0) |

## Section F: Recommendations

Recommendation: ADOPT — DMRSV.ini -> NWPSV.ini; NIO replaces IMH paths. Priority: High — fuse checkout is fundamental bring-up validation confirming PrimeCode correctly consumed all RAPL capability fuses.
