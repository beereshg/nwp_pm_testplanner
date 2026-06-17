# HSD 14025976766: [DMR] [X1 A0 PO] [PM]  core EMTTM threshold set to 105C rather then 100C from acode fuses

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025976766](https://hsdes.intel.com/appstore/article-one/#/14025976766) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | jamesrow |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | SoC Thermal | 52% |
| **Sub-Feature** | TCC | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

- Platform 

JF53NOR09BN0304

- Fused Part 

-IFWI: 

OKSDCRB1_86B_2025.37.3.01_2733.D06_60000964_0.599.0_1P0_NonIPClean_Trace_DebugSigned.bin

-pcode collats:

expectation:

emttm throttling at eff_tj determined by acode fuses and offsets from tcc

observation:

1 module at expected TJ max with no offsets of 100C and all other at 105C

snippet showing first module at 100C and other at 105C, and confimed throttling occurs at these thresholds

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww41.1]

Alex stated that Lukasz is making a pCode patch. If it works fine, Vidar will root cause it and IDC team members will submit the change.

[25ww40.4]

James described that the periodic update of control temperature in pCode leads to mismatches, and while a fix has been proposed, it does not address why the code chooses the worst-case TJMax at this control temp, prompting further review.

[25ww40.3]

James reported that injecting temperatures above the highest TJmax causes throttling on all modules except the first, which uses a different threshold, and confirmed this issue across multiple systems.

The team discussed that the EMTTM algorithm appears to use the worst-case TJmax for most modules, despite all relevant fuses and MSR offsets being zero, and confirmed that overriding fuse values changes module behavior as expected.

Ido and Jaivardhan noted the need to review design documentation and pCode

### Description
- Platform 

JF53NOR09BN0304

- Fused Part 

-IFWI: 

OKSDCRB1_86B_2025.37.3.01_2733.D06_60000964_0.599.0_1P0_NonIPClean_Trace_DebugSigned.bin

-pcode collats:

expectation:

emttm throttling at eff_tj determined by acode fuses and offsets from tcc

observation:

1 module at expected TJ max with no offsets of 100C and all other at 105C

snippet showing first module at 100C and other at 105C, and confimed throttling occurs at these thresholds

### Comments (latest)
++++14614660158 jamesrow
<p>S2P seeming same behavior, S2P refers to EMTTM when referencing prochot:&nbsp;<a href="https://hsdes.intel.com/appstore/article-one/#/22020871191" target="_blank">https://hsdes.intel.com/appstore/article-one/#/22020871191</a>&nbsp;</p><p><br /></p><p>PM working with S2P and <u>acode possibly inconstantly setting thresholds for emttm algo causing some modules to throttle at 100C and some others at 105C</u></p><p><u><br /></u></p><p>currently determining, if tj fuses are as expect, acode and cbb base tj fuses.</p>

++++14614660159 jamesrow
<p>fuses and offsets don't look to be the issue and control temps incorrectly reported:</p><ul><li>fuses for tj max are to spec for tj_max in acode and highest_tj_max</li><li>TJ_max offsets that go into calulating eff_tj_max all zero, they are not what is causing acode to use 105C</li><li>with the first module control temp at 100C unlike others at 105C, module still only throttles at 106C</li></ul><p><br /></p><p><br /></p><p>assumption is that fuses are correct, tj set to 100C and worst case TJ set 105C, question is&nbsp; why is acode sometimes using TJ as the emttm threshold and sometimes worst case temp?</p><p><!--StartFragment-->also, need to check if msr core scoped tcc_offsets are the cause to why some cores using 105C rather then 100C.</p><p><br /></p><p><br /></p><p><u>worst case TJ should be 105C(0x69) and TJ_max acode fuse 100C(0x64):</u></p><p><a href="https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html#fuses" target="_blank">https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html#fuses</a>&nbsp;</p><p>sv.socket0.cbb0.base.fuses.punit_fuses.fw_fuses_highest_tj_max = 0x69</p><p><img src="https://hsdes.intel.com/rest/binary/22021613211" style="width: 1147px;" /><br /></p><p><br /></p><p><a href="https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_PM_Fuses/DMR_Fuse_Specification.html#acode-pm-fuses" target="_blank">https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_PM_Fuses/DMR_Fuse_Specification.html#acode-pm-fuses</a>&nbsp;</p><p>sv.socket0.cbb0.computes.fuses.core0_fuse.core_fuse_core_fuse_acode_tj_max = 0x64</p><p><img src="https://hsdes.intel.com/rest/binary/22021613212" style="width: 2066px;" data-processed="true" />&nbsp;</p><p><br /></p><p><br /></p><p><br /></p><p><u>Offsets both zero, c1e and tcc_offset:</u></p><p>sv.socket0.cbb0.compute0.punit_fuses.fw_fuses_tj_max_c1e_disabled_offset = 0x0</p><p>sv.socket0.cbb0.computes.modules.core0.pcu_cr_temperature_target.tj_max_tcc_offset = 0x0</p><p><br /></p><p><br /></p><p><u>No throttling observed on core with emttm control temp of 100C when injected into with 102C, but does at 106C:</u></p><p><br /></p><p>pma/module cntrol temp at 100C:</p><p>sv.socket0.cbb0.compute0.pma0.pmsb.emttm_algo_misc = 0x64 #100C</p><div><span style="font-size: 0.87em;"><br /></span></div><p>core no

### Tags
SysDebugCloned,SysDebugDccbBypass,FV_PM,TEMP_WA_PATCH_DMR_AP1_A0_60000976_POWERON,PTP_SoC,FIX_PATCH_DMR_AP1_A0_6000097D,FIX_IFWI_DMR_AP1_2025.47.1.01,FIX_BKC_OKS_DMR_AP1_2025WW47, PSF=Y

### Conclusion
fw.bug

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

- **Primary Feature**: SoC Thermal
- **Sub-Feature**: TCC
- **Component Path**: fw.pcode

## Firmware Touchpoints

### PCODE
- `pCode patch`

## Key Registers

- `sv.socket0.cbb0.base.fuses.punit_fuses.fw_fuses_highest_tj_max`
- `sv.socket0.cbb0.computes.fuses.core0_fuse.core_fuse_core_fuse_acode_tj_max`
- `sv.socket0.cbb0.compute0.punit_fuses.fw_fuses_tj_max_c1e_disabled_offset`
- `sv.socket0.cbb0.computes.modules.core0.pcu_cr_temperature_target.tj_max_tcc_offset`
- `sv.socket0.cbb0.compute0.pma0.pmsb.emttm_algo_misc`

## Timeline

- **Submitted**: 2025-09-26 09:03:14
- **Root Caused**: 2025-10-08 03:34:47
- **Closed**: 2025-12-29 05:53:58
- **Days Open**: 93

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
