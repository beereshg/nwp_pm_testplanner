# HSD 14026846139: [DMR][A0][X4][SST] SST BF is incorrectly resolving P1 HI Priority cores

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026846139](https://hsdes.intel.com/appstore/article-one/#/14026846139) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | lmalagon |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Platform PM Interface | 52% |
| **Sub-Feature** | TPMI | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

On QDF Q9X2:

In [99]: sv.socket0.cbb0.base.fuses.punit_fuses.fw_fuses_sst_bf_config_0_p1_hi_priority_module_mask

Out[99]: 0x60230000

According to fuse mask it is expected to resolve 5 modules as Hi Pi (physical)

SOCKET0 CBB0 COMPUTE2 MODULE16

SOCKET0 CBB0 COMPUTE2 MODULE17

SOCKET0 CBB0 COMPUTE2 MODULE21

SOCKET0 CBB0 COMPUTE3 MODULE29

SOCKET0 CBB0 COMPUTE3 MODULE30

pCode is resolving Hi P1 ratio to only 2 modules (physical)

SOCKET0 CBB0 COMPUTE3 MODULE24

SOCKET0 CBB0 COMPUTE3 MODULE29


## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww04.3]

Logical mask and pyshical mask is mixing, causing resolved ration for P1 cores is not correct. pCode is the one that resolves this equations, Vidar asked Anatoli to engage in this debug.

### Description
On QDF Q9X2:

In [99]: sv.socket0.cbb0.base.fuses.punit_fuses.fw_fuses_sst_bf_config_0_p1_hi_priority_module_mask

Out[99]: 0x60230000

According to fuse mask it is expected to resolve 5 modules as Hi Pi (physical)

SOCKET0 CBB0 COMPUTE2 MODULE16

SOCKET0 CBB0 COMPUTE2 MODULE17

SOCKET0 CBB0 COMPUTE2 MODULE21

SOCKET0 CBB0 COMPUTE3 MODULE29

SOCKET0 CBB0 COMPUTE3 MODULE30

pCode is resolving Hi P1 ratio to only 2 modules (physical)

SOCKET0 CBB0 COMPUTE3 MODULE24

SOCKET0 CBB0 COMPUTE3 MODULE29

sst_pp_info_2 is resolving the physical mask it is expected to be populated with a logical mask

In [100]: sv.socket0.cbb0.base.fuses.punit_fuses.fw_fuses_sst_pp_0_module_disable_mask (physical)

Out[100]: 0x1a009eff

In [101]: sv.socket0.cbb0.base.tpmi.sst_pp_info_2 #(logical)

Out[101]: 0xe5ff61

In [102]: sv.socket0.cbb0.base.tpmi.sst_bf_info_1 

Out[102]: 0x60230000 #it is expected to be a subset of sst_pp_info_2 logical mask

### Comments (latest)
++++14614972603 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14026846048.

++++14614985181 lmalagon
Waiting for  @Odler, Anatoli to provide feedback about this issue.
++++1363560334 aodler
 @Malagon Mandujano, Leonardo the HAS documentation says that SST_BF_INFO_1[P1_HI_MODULE_MASK] represents logical module mask. Please find  SST_BF_INFO_1 in here  https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html#detailed-registers-definition
++++14614990457 lmalagon
 @Odler, Anatoli yes. as you mention the HAS says that SST_BF_INFO_1.P1_HI_MODULE_MASK represents the logical module mask but reading the register it has the physical value. In [99]: sv.socket0.cbb0.base.fuses.punit_fuses.fw_fuses_sst_bf_config_0_p1_hi_priority_module_mask Out[99]: 0x60230000 #physical In [102]: sv.socket0.cbb0.base.tpmi.sst_bf_info_1  Out[102]: 0x60230000 #physical p1_hi_priority_module_mask is assigning modules that are not logical enabled. 0b1100 0000 0100 0110 0000 0000 0000 0000 #bin(sv.socket0.cbb0.base.tpmi.sst_pp_info_2.resolved_module_mask)
0b0000 0001 1100 1011 1111 1111 0110 0001 #bin(sv.socket0.cbb0.base.tpmi.sst_bf_info_1.p1_hi_module_mask)
++++1363560485 aodler
 @Malagon Mandujano, Leonardo Please adjust the fuses accordingly, to represent logical module mask.
++++14614992705 lmalagon
 @Odler, Anatoli Fuse definition across all SKUs is physical (in this project and historically) see the table below from Intel SST HAS, and this is the link for PM Fuse Specification Please adjust the code accordingly to the requirements from Arch definition @Chen, Stanley . Fuse is physical module ID and register reporting is logical ID.
++++1363560688 aodler
 @Malagon Mandujano, Leonardo let me check that with the arch folks in IDC
++++14614998451 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14026846139] of [component=fw.pcode] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [bug] to [heia_soc.bugeco.id=14026908324] of [component=dmrcbbbase.soc.pm.pcode] in [release=dmrcbbbase-a0]
++++22611786325 mbfausto
[SysDebug] The FW ticket (id=14026908324) cloned from this sighting has been fixed and released in ingredient version "DMR_A0_60000993" on [SysDebug] Sighting tag appended with "FIX_PATCH_DMR_A0_60000993" [SysDebug] [SysDebug] The Sighting owner (lmalagon) may be enabled to validate the fix is working in the released collateral.

++++22611786328 mbfausto
[SysDebug Tag Script] IFWI version "DMR_AP_2026.09.3.04" has been released that contains the component release "FIX_PATCH_DMR_A0_60000993" [SysDebug Tag Script] Sighting tag appended with "FIX_IFWI_DMR_AP_2026.09.3.04"
++++14615135760 lmalagon
﻿FIX_IFWI_DMR_AP_2026.09.3.04 validated. We can close this sighting. It is working as expected, thanks for the tracking.
++++22611820434 mbfausto
[SysDebug Tag Script] BKC version "OKS_DMR_AP_2026WW12" has been released that contains the component release "FIX_IFWI_DMR_AP

### Tags
FV_PM,SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_60000993,FIX_IFWI_DMR_AP1_2026.09.3.04,BKC#OKS_DMR_AP_X1_2026WW10_INT,FIX_BKC_OKS_DMR_AP1_2026WW12

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

- **Primary Feature**: Platform PM Interface
- **Sub-Feature**: TPMI
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbb0.base.fuses.punit_fuses.fw_fuses_sst_bf_config_0_p1_hi_priority_module_mask`
- `sv.socket0.cbb0.base.fuses.punit_fuses.fw_fuses_sst_pp_0_module_disable_mask`
- `sv.socket0.cbb0.base.tpmi.sst_pp_info_2`
- `sv.socket0.cbb0.base.tpmi.sst_bf_info_1`

## Timeline

- **Submitted**: 2026-01-16 06:17:01
- **Root Caused**: 2026-01-26 23:10:15
- **Closed**: 2026-03-03 20:37:49
- **Days Open**: 46

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
