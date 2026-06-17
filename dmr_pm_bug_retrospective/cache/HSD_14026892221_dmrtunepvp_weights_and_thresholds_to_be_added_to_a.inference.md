# HSD 14026892221: [DMR][Tune]:PVP Weights and Thresholds to be added to added to acode (Primecode)

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026892221](https://hsdes.intel.com/appstore/article-one/#/14026892221) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | srotich |
| **Component** | hw.power |
| **Defect Die** | ioe |
| **Conclusion** | hw.tuning |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Unknown | 20% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

USE THESE UPDATED VALUES.....

USE THESE UPDATED VALUES.....

##Long window 1024 cycle:

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._0=0x22

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._1=0x30

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._2=0x35

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._3=0x58

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._4=0x

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
WW09.5
Will root cause with 2 implementation

Next) Simeon)
 add 2 comments 1 for A code and prime code.
Add comment to ensure both changes go together.

Weights to A code
Thresholds to Primecode

WW08.3
  

No pm folks moving to perf sysdebug WW08.5

Primecode = Alex Grabacki (may point to Sagar)
aCode ==> Justin Gilmer (Core MDT)

### Description
USE THESE UPDATED VALUES.....

USE THESE UPDATED VALUES.....

##Long window 1024 cycle:

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._0=0x22

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._1=0x30

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._2=0x35

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._3=0x58

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._4=0x70

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._5=0x70

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._6=0x70

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._7=0x70

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._8=0x70

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._9=0x70

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._10=0x70

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._11=0x70

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._12=0x70

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._13=0x70

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._14=0x70

 

##short window(16 cycle):

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._0=0x3f

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._1=0x3f

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._2=0x3f

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._3=0x80

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._4=0x80

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._5=0x80

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._6=0x80

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pv

### Comments (latest)
++++14614992718 josecarl
[CloneScript] PreSighting 14026878123 cloned to Sighting 14026892221
++++22611729967 mbfausto
Team, this ticket hasn't been touched since cloning.  What's the status? Have you verified with either a debug patch (if needed) or with PythonSV overrides that these values are work as expected?   What other validation/checkout (if any) is needed to verify no harm or nothing is broken?  Any PM flows? What spec are these values defined, is there a PM SOC spec or other thermal/PTP spec documenting these values that need updating prior to implementation? Are these weights going to change in the future or is this tuning final?  (are we tuning 'good enough' or 'imh1 A0 values' and will need to come back) ? You title mentions acode and primecode, yet the register list above seems to be entirely in the CBB so something doesn't seem right?
++++14615066379 josecarl
Ticket was meant to push tunning changes but they were not ready, closing the HSD

++++14615072362 srotich
The values ready to be pushed are:  ##PVP: ##Long window 1024 cycle: sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._0=0x25 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._1=0x2c sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._2=0x32 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._3=0x52 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._4=0x55 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._5=0x55 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._6=0x55 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._7=0x55 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._8=0x55 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._9=0x55 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._10=0x55 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._11=0x55 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._12=0x55 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._13=0x55 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._14=0x55 ##short window(16 cycle): sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._0=0x2e sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._1=0x2e sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._2=0x39 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._3=0x55 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._4=0x58 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._5=0x58 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._6=0x58 sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._0._7=0x58 sv.socket0.cpu.pmas.

### Tags
PNP
PM,SysDebugDccbBypass,SysDebugCloned,SysDebugCloned_RCBypass,FIX_PATCH_DMR_AP1_A0_60000994,FIX_IFWI_DMR_AP1_2026.10.4.01,FIX_BKC_OKS_DMR_AP1_2026WW12

### Conclusion
hw.tuning

### Component
hw.power

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
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._0`
- `sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._1`
- `sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._2`
- `sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._3`
- `sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.pvc_thresholds._1._4`

## Timeline

- **Submitted**: 2026-01-23 21:57:58
- **Root Caused**: 2026-03-04 21:03:30
- **Closed**: 2026-04-18 21:08:12
- **Days Open**: 84

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
