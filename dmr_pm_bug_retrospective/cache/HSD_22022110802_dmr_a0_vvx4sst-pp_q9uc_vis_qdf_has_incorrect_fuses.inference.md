# HSD 22022110802: [DMR A0 VV][X4][SST-PP] Q9UC VIS QDF has incorrect fuses on PP level 4 CDYN index 1

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22022110802](https://hsdes.intel.com/appstore/article-one/#/22022110802) |
| **Status** | complete.wont_validate |
| **Priority** | 2-high |
| **Owner** | lmalagon |
| **Component** | hw.fuse.xml |
| **Defect Die** | base |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 80% |
| **Sub-Feature** | TRL | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

QDF X4 Q9UC has wrong values on fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index1_ratio[0:4]

This is violating fuse rule #52 from 
PM Fuse Specification

All dies are impacted (iMHs and CBBs), 
each fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index1_ratio[0:4] should be >= fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index2_ratio[0:4]

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index1_ratio0=
0x1c

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index1_r

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww10.3]

Need input from the bin split team, Erick is the person we are waiting on. Alex Toh usually is the spokesperson on the fuse CBB. Matthew/Vidar already on mail chain. Next: Matthew will revive the thread. 

﻿[26ww09.1]

Leonardo found that in the QDF X4 Q9UC, the fuse values for SST PP level 4 do not satisfy the requirement that each Cdyn index ratio must be greater than or equal to the next, which was not observed in other QDFs.

Leonardo has escalated the issue to Archana and the fuse CCB team, copying relevant stakeholders, and is waiting for confirmation and guidance on the necessary fuse value corrections.

### Description
QDF X4 Q9UC has wrong values on fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index1_ratio[0:4]

This is violating fuse rule #52 from 
PM Fuse Specification

All dies are impacted (iMHs and CBBs), 
each fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index1_ratio[0:4] should be >= fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index2_ratio[0:4]

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index1_ratio0=
0x1c

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index1_ratio1=
0x1b

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index1_ratio2=
0x1b

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index1_ratio3=
0x1b

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index1_ratio4=
0x1b

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index1_ratio5=0x1b

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index1_ratio6=0x1b

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index1_ratio7=0x1b

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index2_ratio0=
0x20

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index2_ratio1=
0x1f

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index2_ratio2=
0x1f

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index2_ratio3=
0x1d

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index2_ratio4=
0x1c

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index2_ratio5=0x1b

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index2_ratio6=0x1b

punit_fuses.fw_fuses_sst_pp_4_turbo_ratio_limit_ratios_cdyn_index2_ratio7=0x1b

+------------------------------------------------------------------------------------------------+

|                          TRL cdyn check for socket0.imh0 - PP Level 4                          |

+--------+-------------+------------+-------------+------------+------------+-------------+------------+------------+

|   --       | Bucket 0 | Bucket 1 | Buc

### Comments (latest)
++++22611785507 mbfausto
Raising to high if a possible fuse value issue. No updated in a week since filing - shoudln't we know if the fuse value is not matching the SKU?  Or is the fuse value matching expectation and there is a concern we need to update that value?
++++14615127593 vwang 
@Marin Cartin, Erick    @Munshi, Archana  Friendly reminder. We need feedback on this ASAP, please let me know if you need additional information. From Stan: The intention of fuse rule #52 is to ensure that the turbo frequency of Lower Cdyn level is higher. This is critical for optimal functionality.   I believe binsplit team should take a closer look into why this is not the case in this instance.  


++++14615131083 emarinca
I checked the QDF Q9UC in LAVA and the Values for SSTPP4 and also the rest of frequencies are meeting the fuse rule.  Please provide more details on which values you think the rule is broken Q9UC  SSTTF_CFGi_CDYNx_1 >= SSTTF_CFGi_CDYNx_2

++++14615134049 vwang 
This sighting found an fuse issue on SST-PP,  not SST-TF From  @Wilhelmi, Danny J  Erick, I think we have a problem (in orange).  As Leo says you looked at TF instead.    
++++22611792210 mbfausto
Root-caused, but not cloned anywhere.  There is no HSD ticket tracking a SKU definition problem / DQ Rule update. Validation - if you can please use another QDF that is not affected for required validation as there is no more A0 material being built. If there is justification for a Fuse FW override mitigation for this QDF, please contact Fuse CCB.

### Tags
FV_PM,SysDebugDccbBypass,SysDebug_BugId_Ignore,SysDebug_FixId_Ignore

### Conclusion
hw.arch

### Component
hw.fuse.xml

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: TRL
- **Component Path**: hw.fuse.xml

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-02-21 02:18:59
- **Root Caused**: 2026-03-04 22:10:43
- **Closed**: 2026-03-04 22:10:43
- **Days Open**: 11

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
