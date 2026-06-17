# HSD 14026892232: [DMR][X1][Tune]:LPM tuned Parameters to be added  to BIOS

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026892232](https://hsdes.intel.com/appstore/article-one/#/14026892232) |
| **Status** | complete.broken |
| **Priority** | 3-medium |
| **Owner** | srotich |
| **Component** | bios |
| **Defect Die** | ioe |
| **Conclusion** | hw.tuning |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **BIOS** | 70% |
| **Feature** | Core C-States | 45% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_IFWI/FIX_BIOS → BIOS

## Root Cause Summary

Memory Low Power mode  (LPM1/LPM3) parameters that needs to be included in IFWI for PCP performance validation:

 

LPM 1 Enabled/Disabled settings

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[0].lpm1_en = 0x1

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[1].lpm1_en = 0x1

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[2].lpm1_en = 0x1

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[3].lpm1_en = 0x1

 

LPM1 Idle timer settings

sv.sockets.imh

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
WW08.3
 
No pm folks moving to perf sysdebug WW08.5

Primecode = Alex Grabacki (may point to Sagar)

### Description
Memory Low Power mode  (LPM1/LPM3) parameters that needs to be included in IFWI for PCP performance validation:

 

LPM 1 Enabled/Disabled settings

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[0].lpm1_en = 0x1

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[1].lpm1_en = 0x1

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[2].lpm1_en = 0x1

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[3].lpm1_en = 0x1

 

LPM1 Idle timer settings

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[0].lpm1_idletime = 0x8

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[1].lpm1_idletime = 0x8

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[2].lpm1_idletime = 0x8

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[3].lpm1_idletime = 0x8

 

 

LPM 3 Enable/Disable settings

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[0].apd_en = 0x0, ppd_en = 0x0

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[1].apd_en = 0x0, ppd_en = 0x1

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[2].apd_en = 0x0, ppd_en = 0x1

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[3].apd_en = 0x0, ppd_en = 0x1

LPM3 Idle timer settings

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[0].lpm3_idletime = 0x1FFF    (8191 in dec)

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[1].lpm3_idletime = 0x1FFF

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[2].lpm3_idletime = 0x1F4  (500 in dec)

sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[3].lpm3_idletime = 0x1F4

### Comments (latest)
++++14614992769 josecarl
[CloneScript] PreSighting 14026878522 cloned to Sighting 14026892232

++++14614999701 srotich
Updated LPM3 from 250 to 8191 for minimum latency loss on 1S and 2S systems:#LPM 3 (no extensive validation yet and not sign off by architect yet, only testing and more data, initial propose by architect is 200) sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[0].lpm3_idletime =8191 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[1].lpm3_idletime =8191 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[2].lpm3_idletime =8191 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[3].lpm3_idletime =8191

++++14615004279 josecarl
Reoved SSR part as it was in https://hsdes.intel.com/appstore/article-one/#/article/14026227844

++++14615066392 josecarl
Ticket was meant to push tunning changes but they were not ready, closing the HSD

++++14615085188 smakine1
USE THESE LATEST TUNED SETTINGS LPM 1: Enabled: sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[0].lpm1_en = 0x1 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[1].lpm1_en = 0x1 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[2].lpm1_en = 0x1 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[3].lpm1_en = 0x1   Idle timer sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[0].lpm1_idletime = 0x8 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[1].lpm1_idletime = 0x8 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[2].lpm1_idletime = 0x8 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[3].lpm1_idletime = 0x8     LPM 3: Enabled: sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[0].apd_en = 0x0 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[1].apd_en = 0x1 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[2].apd_en = 0x1 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[3].apd_en = 0x1   Idle timer sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[0].lpm3_idletime = 0x1FFF    (8191 in dec) sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[1].lpm3_idletime = 0x1FFF sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[2].lpm3_idletime = 0x1F4  (500 in dec) sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[3].lpm3_idletime = 0x1F4

++++14615086768 josecarl
Re opening HSD , values are finally ready will proceed to implementation

++++14615087206 smakine1
Updated settings...Use these. LPM 1 Enabled/Disabled settings sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[0].lpm1_en = 0x1 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[1].lpm1_en = 0x1 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[2].lpm1_en = 0x1 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[3].lpm1_en = 0x1   LPM1 Idle timer settings sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[0].lpm1_idletime = 0x8 sv.sockets.imhs.memss.mcs.mcscheds_common.epb_settings_lvl[1].lpm1_idletime = 0x8 sv.socke

### Tags
PM,PnP,tune,SysDebugCloned,SysDebugDccbBypass,BIOS_MS_PRE_ALPHA,SysDebugCloned_RCBypass,FIX_BIOS_OAKSTRM.0.RPB.0034.D.17,FIX_IFWI_DMR_AP1_2026.16.3.01,FIX_BKC_OKS_DMR_AP1_2026WW18

### Conclusion
hw.tuning

### Component
bios

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
- **Sub-Feature**: general
- **Component Path**: bios

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.memss.mc0.mcscheds_common.epb_settings_lvl`

## Timeline

- **Submitted**: 2026-01-23 22:00:42
- **Root Caused**: 2026-02-20 01:46:20
- **Closed**: 2026-05-04 19:13:50
- **Days Open**: 100

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
