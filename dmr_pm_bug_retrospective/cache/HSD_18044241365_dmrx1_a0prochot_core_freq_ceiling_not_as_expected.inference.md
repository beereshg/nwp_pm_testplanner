# HSD 18044241365: [DMR][X1 A0][prochot]  Core freq ceiling not as expected based on pf lookup of the response power value

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [18044241365](https://hsdes.intel.com/appstore/article-one/#/18044241365) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | jamesrow |
| **Component** | fw.acode |
| **Defect Die** | base |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 75% |
| **Sub-Feature** | TRL | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

expectation:

by looking up the pf fuses, the iccp license level, index of license level and response power we determine what ceiling will be set and confirm Ips operating below that ceiling

observation:

Core not throttling below the expected ceiling while all other IPs throttle to their expected ceilings

initial triage, confirm data used in script is correct:

response power used to pf curve lookup

 

In [95]: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.prochot_response_power

Out[95]: 0x2050 #

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww20.1]

James raised questions about why aCode selects index 0 instead of index 3 when ICCP grant is 3, and whether this behavior violates any specification, with Matthew clarifying that WP4 is a limit and not a one-to-one mapping.

James detailed experiments showing unexpected index selections and ratio limits, with manual confirmation of fuse values and response power, and discussed the need to understand the linkage between ICCP levels and WP4 index selection.

Alex suggested testing the patch related to WP4 index selection, and James agreed to provide data and discuss findings with Chen, with ongoing efforts to manually reproduce the issue and collect relevant debug data.

Next: Vidar organize a meeting with aCode, Jim, and architects to address the issue

﻿[26ww18.1]

Work Point Limit Generation: James described that pCode generates WP4 limits for each index, which aCode selects from, but there is an issue where aCode may choose the wrong index, leading to unexpected frequency limits.

The team discussed using a Primecode debug patch to help isolate the issue, prioritizing the showstopper issue but planning to follow up on this as well.

Vidar and James agreed to separate the Punit and aCode issues into distinct settings for clarity, and Alex suggested testing the patch related to WP4 to see if it resolves the observed behavior.

﻿[26ww17.3]

James will provide teh data and discuss with Chen.

﻿[26ww14.3]

Another run last night and pending on collecting data. -- James

﻿[26ww14.1]

James reported the VV results this weekend are also not helpful,  will manually reproduce this week.

﻿[26ww13.3]

James reported difficulties in reproducing the issue on available systems, with failed attempts due to PLR check failures and the need for fuse overrides to simplify debug. The team agreed to consult with the tools team and to attempt further data collection with reduced core counts.

﻿[26ww13.1]

VV reproduced this issue on multiple systems, James will collect the

### Description
expectation:

by looking up the pf fuses, the iccp license level, index of license level and response power we determine what ceiling will be set and confirm Ips operating below that ceiling

observation:

Core not throttling below the expected ceiling while all other IPs throttle to their expected ceilings

initial triage, confirm data used in script is correct:

response power used to pf curve lookup

 

In [95]: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.prochot_response_power

Out[95]: 0x2050 #1034W

#####################################################################################################################################################################################################

# FIELD: prochot_response_power

# Attribute: rw/l

# UpperBit: 14

# LowerBit: 0

# CurrentValue: 8272

# Description:

# Indicates the power limit that pCode has to maintain while xxPROCHOT is asserted. Unit = 0.125 W.

iccp of pma8 during the test:

pmsb.gvctrl_status4.iccp_grant_level = 
0x1

license index to use based on iccp level:

core0_fuse.virtual.core_fuse_core_fuse_acode_vf_index_for_license_0_df = 0x0

core0_fuse.virtual.core_fuse_core_fuse_acode_vf_index_for_license_1_df = 0x1

core0_fuse.virtual.core_fuse_core_fuse_acode_vf_index_for_license_2_df = 0x2

core0_fuse.virtual.core_fuse_core_fuse_acode_vf_index_for_license_3_df = 0x2

core0_fuse.virtual.core_fuse_core_fuse_acode_vf_index_for_license_4_df = 0x3

core0_fuse.virtual.core_fuse_core_fuse_acode_vf_index_for_license_5_df = 0x3

core0_fuse.virtual.core_fuse_core_fuse_acode_vf_index_for_license_6_df = 0x4

core0_fuse.virtual.core_fuse_core_fuse_acode_vf_index_for_license_7_df = 0x4

power points for the curve, formatted in U12.0:

pcode_socket_virus_power_frequency_curve_power_point_0 = 0x145

pcode_socket_virus_power_frequency_curve_power_point_1 = 0x186

pcode_socket_virus_power_frequency_curve_power_point_2 = 0x1c6  #454W

pcode_socket_virus_power_frequency_curve_power_point_3 = 0x2ea   #796W

pcode_soc

### Comments (latest)
++++1862548419 jamesrow
<p>next steps:</p><p>reproduce and determine why what actual ceiling is set for core, possibly try to snoop the hpm message&nbsp;<a href="https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html#PROCHOT_FREQ_LIMIT" target="_blank" tabindex="-1">https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html#PROCHOT_FREQ_LIMIT</a>&nbsp;</p>

++++1862548420 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 22022086660.
++++22611785528 mbfausto
Team - no updates since 2/12 ... what's the current status, experiments in flight, etc.?

++++22611787901 jamesrow
reproducible only at iccp 5: prochot ceiling checks only pass when at lower iccp level 0-2 all cores go to the same ceiling, index 3 pf curve other IPs correct as not using iccp level log next steps: confirm if other iccp levels other than 5 have this issue and  confirm always index lower than expected reproduce multiple times at index 5 passing with iccp index 1: looks like ceiling that is chosen is for iccp index 2 not 3 with prochot response power of 479: snippet of the cores with iccp 5 and ceiling at 900Mhz: all cores map iccp level to same index:
++++1363597964 chenr
please add the information for the core: what are the core's P0 fuse values? what are WP1, WP3 and WP4 registers data?
++++22611794876 jamesrow
thank you, Chen, will reproduce on same system and collect those data points.
++++1363602092 mmasri
do we have the needed reproduction with desired data asked by Chen?
++++14615217366 vwang
 @Rowe, James is working on reproducing the issue across different systems and collect data.
++++22611809584 jamesrow
able to reproduce in volume, added logging of wps as requested and rerunning as WW12.2
++++1363610086 mmasri
@Rowe, James where is this file attached?
++++22611814714 jamesrow
need to pull the logs and volume and analyze

++++22611822084 mbfausto
Team - we have volume reproduction last week but no comment updates/status/experiments/results here this week.  What is the status, current actions in progres, and next steps?

++++22611823459 mbfausto
Any updates here?  What's the current status/open experiments/next steps?  Thanks!

++++22611823493 jamesrow
hitting other issues in volume, plr value unexplected and missing data on CBBs, will try to reproduce manually on debug.

++++22611834008 jamesrow
reproduced with latest runs, is only one lower then expected like the original failure: WP data I dont see much use on why 19 was chosen, could potentially be a round up on the curve? use 1225W point not 1178W point? dump of acode and pmsb WP data:acode dump raw log: prochot log WARN: core_ratio_socket0_cbb0 - Current value 0x13 is not less than previous/pf value 18. Data used to determine 0x9 as ratio limit: pf curve core cdyns: {0: {325.0: 5, 390.0: 5, 454.0: 6, 512.4: 7, 570.8: 8, 629.2: 9, 687.6: 10, 746.0: 11, 794.666666

### Tags
FV_PM

### Conclusion
not_a_bug

### Component
fw.acode

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
- **Component Path**: fw.acode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.prochot_response_power`

## Timeline

- **Submitted**: 2026-02-24 07:10:35
- **Closed**: 2026-05-13 00:50:52
- **Days Open**: 77

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
