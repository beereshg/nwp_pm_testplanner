# HSD 14027577904: [DMR][ES2][Tune]:PVC Thresholds and idx mapping to be added to acode for ES2

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027577904](https://hsdes.intel.com/appstore/article-one/#/14027577904) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | srotich |
| **Component** | fw.acode |
| **Defect Die** | compute |
| **Conclusion** | hw.tuning |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Unknown | 20% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

These are updated acode values with changes from ES1 (14026892221)

##PVP Thresholds:

##Long window 1024 cycle:

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._0=0x26

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._1=0x30 

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._2=0x35

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._3=0x50

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_c

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
pending testing of the patch by Simeon

﻿[26ww15.1]

ES2 Tuning: the team coordinated the implementation and deployment of ES2 tuning values, agreeing on the need for a debug patch, validation, and synchronization with manufacturing to ensure the patch is included before ES2 release

Simeon confirmed that the new tuning values are targeted for ES2, and Jason agreed to create a debug patch for validation. The team discussed the need for a separate branch if required and the process for integrating the patch into the main line.

Steven emphasized the importance of validating the tuning with broader teams and ensuring coordination with manufacturing, as changes are also being made to the ES2 test program. The patch must be included before ES2 silicon is released.

### Description
These are updated acode values with changes from ES1 (14026892221)

##PVP Thresholds:

##Long window 1024 cycle:

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._0=0x26

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._1=0x30 

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._2=0x35

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._3=0x50

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._4=0x60

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._5=0x60

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._6=0x60

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._7=0x60

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._8=0x60

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._9=0x60

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._10=0x60

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._11=0x60

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._12=0x60

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._13=0x60

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._14=0x60

#short window (64/16 cycle)

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._0=0x3f

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._1=0x3f

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._2=0x3f

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._3=0x65

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._4=0x65

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._5=0x65

sv.sockets.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._6=0x65

sv.sockets.cpu.pmas.acode

### Comments (latest)
++++14615290394 vwang
[CloneScript] PreSighting 14027577581 cloned to Sighting 14027577904

++++14615297861 srotich 
Deltas from previous  ES1 changes (22022155764) are highlighted in Red


++++14615298829 jasoncwa
Attached debug patches that include the requested tuning changes: In [131]: sv.sockets.cpu.pma1.acode.vars.acode_cal_vars.g_pvc_cal.showsearch('') max_allowed_throtling_ratio = 0x3ba3d70a target_threshold_divider = 0x3f59999a hysteresis_time = 0x3d090 hw_interrupt_threshold = 0x7 max_threshold_idx._0 = 0x2 max_threshold_idx._1 = 0x2 max_threshold_idx._2 = 0x4 max_threshold_idx._3 = 0x4 max_threshold_idx._4 = 0x4 min_threshold_idx._0 = 0x0 min_threshold_idx._1 = 0x0 min_threshold_idx._2 = 0x2 min_threshold_idx._3 = 0x3 min_threshold_idx._4 = 0x3 pvc_thresholds._0._0 = 0x3f pvc_thresholds._0._1 = 0x3f pvc_thresholds._0._2 = 0x3f pvc_thresholds._0._3 = 0x65 pvc_thresholds._0._4 = 0x65 pvc_thresholds._0._5 = 0x65 pvc_thresholds._0._6 = 0x65 pvc_thresholds._0._7 = 0x65 pvc_thresholds._0._8 = 0x65 pvc_thresholds._0._9 = 0x65 pvc_thresholds._0._10 = 0x65 pvc_thresholds._0._11 = 0x65 pvc_thresholds._0._12 = 0x65 pvc_thresholds._0._13 = 0x65 pvc_thresholds._0._14 = 0x65 pvc_thresholds._0._15 = 0x65 pvc_thresholds._1._0 = 0x26 pvc_thresholds._1._1 = 0x30 pvc_thresholds._1._2 = 0x35 pvc_thresholds._1._3 = 0x50 pvc_thresholds._1._4 = 0x60 pvc_thresholds._1._5 = 0x60 pvc_thresholds._1._6 = 0x60 pvc_thresholds._1._7 = 0x60 pvc_thresholds._1._8 = 0x60 pvc_thresholds._1._9 = 0x60 pvc_thresholds._1._10 = 0x60 pvc_thresholds._1._11 = 0x60 pvc_thresholds._1._12 = 0x60 pvc_thresholds._1._13 = 0x60 pvc_thresholds._1._14 = 0x60 pvc_thresholds._1._15 = 0x60
++++22611832799 mbfausto
Does aCode consume these form a CBB spec or is/will this just be an aCode enhancement request?
++++14615303859 vwang
the importance of validating the tuning with broader teams and ensuring coordination with manufacturing, as changes are also being made to the ES2 test program. The patch must be included before ES2 silicon is released.
++++22611837420 mbfausto
Any update to the status an my questions I posed below? Does aCode consume these form a CBB spec or is/will this just be an aCode enhancement request?
++++14615313582 vwang
The test patch was attached.

++++14615314832 vwang
 @Fausto, Matthew B   I talked with them and was told it is an enhancement request.
++++1363627775 mmasri 
You'll need to clone it over to acode enhancement (in case debug patch is working for u ) 
++++14615328250 srotich
Validated the patch "UP_DMR_A0_8041099A_DBGSIGNED.pdb" . Confirmed PVP long and short window settings look good.
++++22611841240 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14027577904] of [component=fw.acode] in [release=pkg.dmr-a0] has been cloned to a [feature] to [ip_cpu_bigcore.bugeco.id=22022314809] of [component=pnc.ip.acode] in [release=pnc-a0]
++++14615345106 srotich
Checked IFWI 34D25(primecode 99D) and realized this critical register to enable 16cycle short wind

### Tags
pnp pm,SysDebugDccbBypass,SysDebugCloned,SysDebugCloned,FIX_PATCH_DMR_AP1_A0_600009A2,FIX_IFWI_DMR_AP1_2026.20.3.04

### Conclusion
hw.tuning

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

- **Primary Feature**: Unknown
- **Sub-Feature**: general
- **Component Path**: fw.acode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-04-04 04:35:32
- **Root Caused**: 2026-04-14 09:24:34
- **Closed**: 2026-05-21 03:03:07
- **Days Open**: 46

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
