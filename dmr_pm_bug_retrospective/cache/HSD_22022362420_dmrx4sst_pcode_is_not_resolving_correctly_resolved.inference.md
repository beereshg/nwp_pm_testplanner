# HSD 22022362420: [DMR][X4][SST] pCode is not resolving correctly resolved_module_mask TPMI register

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22022362420](https://hsdes.intel.com/appstore/article-one/#/22022362420) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | lmalagon |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Platform PM Interface | 52% |
| **Sub-Feature** | TPMI | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

pCode is not resolving correctly sst_pp_info_2.resolved_module_mask TPMI register

Issue in 2 socket system with X4
. 

pCode should be shifting disabled computes an left the remaining ones. In this particular scenario, pCode is not shifting disabled computes and it is handling weird &quot;half disabled compute (nibble)&quot;, making a shift in these nibbles that does not have enabled modules. ptracker and pcode.vars dumps attached.

Issue on 1S X4 system, 

it is only working for CBB 0, remaini

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
doc.arch  SoC Pm :  Nati / 

Sagi Weis to filll the gap of spec.

﻿[26ww18.3]

SST_PP_INFO_2.RESOLVED_MODULE_MASK is architecturally defined as a logical resolved module mask. Current pCode behavior on non-CBB0 X4 configurations returns physical-style masks and/or applies LLC/nibble-based shifting, which is inconsistent with the register definition and reset flow. Resolution should be based on FW_FUSES_SST_PP_*_MODULE_DISABLE_MASK plus logical module enable/disable inputs, with the final TPMI value published as a logical packed mask.

Stan (Arch) and pCode(Anatoli) has already start to investigate this HSD. Anatoli will setup a TF to discuss this gap(spec gap?) and find the potential solution for both DMR and COR.

﻿[26ww17.3]

Leonardo explained that Pcode is not correctly shifting disabled computes in module mask resolution for TPMI registers, resulting in incorrect logical values being exposed, especially for CBB1, CBB2, and CBB3, regardless of PP level. The issue was observed in both one-socket and two-socket systems with X4, but not with X1, and Leonardo provided examples and tables to illustrate the incorrect mask handling. 

Leonardo attached additional dumps for TPMI registers and Ptracker

Next:  pending on pCode to investigate

### Description
pCode is not resolving correctly sst_pp_info_2.resolved_module_mask TPMI register

Issue in 2 socket system with X4
. 

pCode should be shifting disabled computes an left the remaining ones. In this particular scenario, pCode is not shifting disabled computes and it is handling weird &quot;half disabled compute (nibble)&quot;, making a shift in these nibbles that does not have enabled modules. ptracker and pcode.vars dumps attached.

Issue on 1S X4 system, 

it is only working for CBB 0, remaining CBBs are not shifting disabled computes but they are not removing/shifting nibbles.

NOTE - These are not the same QDFs, masks are not equal.

### Comments (latest)
++++22611856571 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14027708349.
++++14615359718 lmalagon
2S system TPMI dumps for each CBB attached. 
++++1363639292 aodler
 @Offen, Zeev  can you please review the ptracker?
++++2162576729 zoffen
pcode is only shifting bit positions in the masks on in the for LLC_SLICE_IA_CCP_DIS (fuse) where slices are off and the same shist applied to all masks i could not find the value of this fuse in the attached files i could not download the pcode vars files (it erros on some file is not available) the mask construction is based on : https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCP%20HAS/cbb_cpp_has.html#topology-control
++++1363639980 aodler 
Folks please review the CCP HAS spec, SST_PP_INFO_2[RESOLVED_MODULE_MASK]: https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCP%20HAS/cbb_cpp_has.html#sst_pp_info_2:~:text=This%20is%20the%20logical%20module%20ID%20mask%20containing%20the%20functional
++++22611865505 mbfausto
 @Malagon Mandujano, Leonardo  - what is the value of your LLC_SLICE_IA_CCP_DIS fuse?  Can we compare FUSE/MASKS cleanly (not screen shots of text please, cannot copy/paste/etc.) and point out what mask you EXPECT versus SEE with the FUSE so that pCode can directly answer/provide specifics?  @Odler, Anatoli  /  @Offen, Zeev - the masks as presented in the description seem expected to you to the customer/user?
++++14615385407 lmalagon
According to the spec  you are providing SST_PP_INFO_2 should be logical value and this is only comes true in CBB0 (only in 1 socket system with X4) 1 Socket system with X4: Lets take the example of the second table in the description... Fused Value column comes from cbb fuse: punit_fuses.fw_fuses_sst_pp_*_module_disable_mask Resolved Fuse Value column comes from the following formula to have the enabled modules: ~punit_fuses.fw_fuses_sst_pp_*_module_disable_mask & 0xFFFFFFFF, and then remove/shift computes (complete) disabled TPMI Resolved Value column comes from TPMI register: sst_pp_info_2.resolved_module_mask Taking PP level 3 values as an example: CBB0: Fuse value = 0xFF1F01FF Resolved fuse value = ~0xFF1F01FF & 0xFFFFFFFF = 0x00E0FE00, then remove the computes disabled -> 0xE0FE TPMI value = 0xE0FE In this CBB TPMI value is correctly handled. CBB1: Fuse value = 0xFF20FF9B Resolved fuse value = ~0xFF20FF9B & 0xFFFFFFFF = 0x00DF0064, then remove the computes disabled -> 0xDF64 TPMI value = 0xDF0064 -- This is a physical IDs for enabled modules and we do not want to expose physical IDs to customers In this CBB, same as CBB2 and CBB3 regardless of the PP level, TPMI register value is not treated same as CBB0. Fuse values: SOCKET0 CBB0 fw_fuses_sst_pp_0_module_disable_mask -> 0x770801ff fw_fuses_sst_pp_1_module_disable_mask -> 0x771901ff fw_fuses_sst_pp_2_module_disable_mask -> 0xff1901ff fw_fuses_sst_pp_3_module_disable_mask -> 0xff1f01ff fw_fuses_llc_slice_

### Tags
FV_PM,SysDebugCloned

### Conclusion
not_a_bug

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

- **Primary Feature**: Platform PM Interface
- **Sub-Feature**: TPMI
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI register`
- `TPMI value`
- `TPMI registers`
- `TPMI dumps`
- `TPMI Resolved`
- `TPMI result`

## Timeline

- **Submitted**: 2026-04-22 05:21:01
- **Root Caused**: 2026-05-06 22:09:55
- **Closed**: 2026-05-08 02:19:42
- **Days Open**: 15

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
