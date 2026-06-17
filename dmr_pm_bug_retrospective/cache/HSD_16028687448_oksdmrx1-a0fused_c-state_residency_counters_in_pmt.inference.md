# HSD 16028687448: [OKS][DMR][x1-a0][fused] C-State Residency Counters in PMT SRAM not properly incrementing.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16028687448](https://hsdes.intel.com/appstore/article-one/#/16028687448) |
| **Status** | rejected.filed_by_mistake |
| **Priority** | 2-high |
| **Owner** | hkharya |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | MC6 | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

Issue:

C-State Residency Counters stored in CBB Punit PMT SRAM are not properly incrementing.

Below Counter are not incrementing properly. 

1. MC1E: TeleID = 0xd (MC1E_RES_COUNT), DomainID = 0

2. C6A: TeleID = 0xc (AUTOC6_RES_COUNT), DomainID = 1/2 (big core) or 1/2/3/4 (Atom)

3. C6S counter: 

TeleID = 0xb (MC6_RES_COUNT), DomainID = 0

DMR-CBB

 - 

https://hsdes.intel.com/appstore/article-one/#/article/13011397897

 

BIOS Knob set - AcpiC2Enum-'C6A' AcpiC3Enum-'C6SP'.

Platform has - 32

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
Issue:

C-State Residency Counters stored in CBB Punit PMT SRAM are not properly incrementing.

Below Counter are not incrementing properly. 

1. MC1E: TeleID = 0xd (MC1E_RES_COUNT), DomainID = 0

2. C6A: TeleID = 0xc (AUTOC6_RES_COUNT), DomainID = 1/2 (big core) or 1/2/3/4 (Atom)

3. C6S counter: 

TeleID = 0xb (MC6_RES_COUNT), DomainID = 0

DMR-CBB

 - 

https://hsdes.intel.com/appstore/article-one/#/article/13011397897

 

BIOS Knob set - AcpiC2Enum-'C6A' AcpiC3Enum-'C6SP'.

Platform has - 32 Cores/16 Modules.

1. Don't see C6A counter incrementing properly for all the cores.

pmt.dmr-bkc.0.c6a_residency_core0.c6a_residency_core0 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core1.c6a_residency_core1 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core2.c6a_residency_core2 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core3.c6a_residency_core3 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core4.c6a_residency_core4 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core5.c6a_residency_core5 22402.74520432 1755220888

pmt.dmr-bkc.0.c6a_residency_core6.c6a_residency_core6 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core7.c6a_residency_core7 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core8.c6a_residency_core8 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core9.c6a_residency_core9 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core10.c6a_residency_core10 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core11.c6a_residency_core11 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core12.c6a_residency_core12 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core13.c6a_residency_core13 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core14.c6a_residency_core14 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core15.c6a_residency_core15 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core16.c6a_residency_core16 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core17.c6a_residency_core17 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core18.c6a_residency_core18 0.0 1755220888

pmt.dmr-bkc.0.c6a_residency_core19.c6a_residency_core1

### Comments (latest)
++++1667007154 aamarna1
<p>Please re-try with all the Module C States workarounds :&nbsp;</p><p><br /></p><p style="box-sizing: border-box; margin: 0px; padding: 0px; color: rgb(0, 0, 0); font-family: Roboto, Arial, sans-serif; font-size: 14px; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; background-color: rgb(255, 255, 255); text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: initial;">halt()</p><p style="box-sizing: border-box; margin: 0px; padding: 0px; color: rgb(0, 0, 0); font-family: Roboto, Arial, sans-serif; font-size: 14px; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; background-color: rgb(255, 255, 255); text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: initial;">sv.sockets.cbbs.computes.modules.cores.iq_cr_debug2.disable_iqtarget_parity=1</p><p style="box-sizing: border-box; margin: 0px; padding: 0px; color: rgb(0, 0, 0); font-family: Roboto, Arial, sans-serif; font-size: 14px; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; background-color: rgb(255, 255, 255); text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: initial;">sv.sockets.cbbs.computes.modules.cores.rat_cr_defeature2.vecfl_512bitmode=1</p><p style="box-sizing: border-box; margin: 0px; padding: 0px; color: rgb(0, 0, 0); font-family: Roboto, Arial, sans-serif; font-size: 14px; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; background-color: rgb(255, 255, 255); text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: initial;">sv.sockets.cbbs.computes.modules.cores.ml3_cr_pic_debug_modes.disable_async_mcerr=1<br style="box-sizing: border-box;" />sv.sockets.cbbs.computes.modules.cores.ml3_cr_pic_debug_modes.disable_async_mckind=1<br style="box-sizing: border-box;" />sv.sockets.cbbs.computes.modules.cores.ml3_cr_pic_control.suppress_uc_err_on_3_strike=1<br style="box-sizing: border-box;" />sv.sockets.cbbs.computes.modules.cores.ml3_cr_pic_debug_modes.disable_three_strike_cnt=0</p><p style="box-sizing: border-box; margin: 0px; paddi

### Conclusion
no_root_cause.rejected

### Component
fw.pcode

## Root Cause Description

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Fix Description

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Source Code References

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Component Interaction: Root Cause

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Component Interaction: Fix

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Feature Mapping

- **Primary Feature**: Core C-States
- **Sub-Feature**: MC6
- **Component Path**: fw.pcode

## Firmware Touchpoints

### BIOS
- `BIOS Knob`

## Timeline

- **Submitted**: 2025-09-24 00:12:01
- **Closed**: 2025-09-24 04:01:48

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
