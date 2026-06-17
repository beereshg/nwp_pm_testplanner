# HSD 16029411875: [DMR][X1 A0][RAPL] Core Throttling Issue: No Throttle Below Pm with RAPL PID Out = 1

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029411875](https://hsdes.intel.com/appstore/article-one/#/16029411875) |
| **Status** | complete.broken |
| **Priority** | 2-high |
| **Owner** | kumara5 |
| **Component** | hw.power |
| **Defect Die** | compute |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | PState Stack | 75% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Expected Behavior:-

From
 

RAPL HAS

 

PCode should engage core throttling any time that RAPL PID is below Pm

 

But in current CBB Pcode implementation any time that PID is less than Pm the core does not throttle below Pm.

Observed Behavior:-

sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.sst_pp_info_11.show()

0x00000000 : rsvd (63:56) (ro/v) -- Reserved

0x00000004 : pm_fabric_ratio (55:48) (ro/v) -- Fabric (Uncore) minimum frequency ratio.

0x00000008 : p1_fabric_ratio (47:40) (ro/v) -- Fabri

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww51.3]

Meeting still pending to be in place, will follow up with CBB stakeholders and submitter

[25ww51.1]

A recurring problem related to power throttling and frequency scaling, which has been discussed for a long time but remains unresolved. The concern is that the inability to reduce frequency sufficiently during emergencies impairs power control and mitigation.

Previous generations allowed throttling down to Pm plus DCF for thermal excursions.

Recent changes moved to using PLL clock divide instead of DCF, which limits frequency reduction to the fused Pm level.

This impacts the ability to quickly converge to low power states during debugging (e.g., Sapphire Rapids case).

Vidar will setup group discussion with PM and CBB experts together to debug.

### Description
Expected Behavior:-

From
 

RAPL HAS

 

PCode should engage core throttling any time that RAPL PID is below Pm

 

But in current CBB Pcode implementation any time that PID is less than Pm the core does not throttle below Pm.

Observed Behavior:-

sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.sst_pp_info_11.show()

0x00000000 : rsvd (63:56) (ro/v) -- Reserved

0x00000004 : pm_fabric_ratio (55:48) (ro/v) -- Fabric (Uncore) minimum frequency ratio.

0x00000008 : p1_fabric_ratio (47:40) (ro/v) -- Fabric (Uncore) TDP frequency ratio.

0x00000015 : p0_fabric_ratio (39:32) (ro/v) -- Fabric (Uncore) maximum frequency ratio limit.

0x00000004 : pm_core_ratio (31:24) (ro/v) -- Core minimum frequency ratio.

0x00000008 : pn_core_ratio (23:16) (ro/v) -- Core maximum efficiency frequency ratio.

0x0000000d : p1_core_ratio (15:08) (ro/v) -- Core TDP frequency ratio.

0x0000001f : p0_core_ratio (07:00) (ro/v) -- Core maximum frequency ratio limit.

Platform RAPL

In [34]: sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.platform_rapl_limit_cfg.ppl2

Out[34]: 0x1f40

In [35]: sv.socket0.imh0.pcudata.raplVars.platform_rapl_pid_output.get_value()

Out[35]: [32b] 0x000000FF

In [36]: sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.platform_rapl_limit_cfg.ppl2=0

In [37]: sv.socket0.imh0.pcudata.raplVars.platform_rapl_pid_output.get_value()

Out[37]: [32b] 
0x00000001

+--------------------------------+----------------+-------------+--------------+-----------------+-------+-------+-------------+

| Module                         | Pstate Mode    |   MSR 0x199 |   Pcode GPSS | PLR Die         |   WP1 |   WP4 |   MSR 0x198 |

+================================+================+=============+==============+=================+=======+=======+=============+

| socket0.cbb0.compute1.module8  | Legacy Pstates |          13 |            4 | (['POWER'], []) |     4 |   170 |           4 |

+--------------------------------+----------------+-------------+--------------+-----------------+-------+-------+------

### Comments (latest)
++++1667171918 sumanku2
[CloneScript] Sighting 16029411875 cloned from PreSighting 16029055557
++++22611635460 mbfausto
 @Kumar, Suman1  - you are pointing to a pre-silicon sighting from months ago.  are you saying (1) the HAS was never updated, or (2) it was updated but it required a pCode change?  There is no SPEC ticket filed off of 0471 so let's get clarity on if the HAS is correct as updated, or if this is a new change or discovery or something different?  The component for that ticket is a "documentation only - no implementaiton change" ... and no doc.arch tiket ws filed or FW implementation ticket ... so that ticket you are referencing is not tracking any changes at all.   Starting from what's implemented today and spec'd today, what is wrong or missing or needs to change? 1) Any DMR specs where pCode implementation is missing/incorrect (and what did Anatoli/Tomer/pCode indicate when asked?). 2) Any behavior that is not  documented in DMR RAPL HASes that we need to document properly (and if implementation is necessary).

++++22611657067 imelamed
The legacy server behavior, where Pcode is required to limit cores to a restricted Cdyn, is not supported in DMR. To my knowledge, this requirement was never communicated to the CBB team, even though it is referenced as legacy support in the HAS—which was updated to include DMR. As a result, the CBB team was not made aware that this support was needed. We are currently working with the BinSplit team to provide justification and data on whether this support is essential, and to determine how many SKUs are failing the TDP check. Since this appears to be an architectural issue, I recommend closing this sighting as root-caused and opening an architecture bug. Timothy Kam is the RAPL owner for DMR, so the architecture bug should be filed under his name or me as a contact to help drive resolution for DMR. Ido. 

++++22611668678 mbfausto
Thanks  @Melamed, Ido  - that makes sense and I agree.  I will file a server.feature for Timothy to drive for DMR PM (versus heia_soc.feature) so that the DMR-wide PM HAS and specs are all driven and any SOC impacts.

++++22611668693 mbfausto
[CloneScript] Sighting [sighting_central.sighting.id=16029411875] of [component=hw.power] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [ccb] to [server.feature.id=22021941890] of [component=soc.top] in [release=dmrhub-a0]

++++22611700433 tkam 
As requested, the HAS section related to this CBB/core capability is made available at https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#throttling-cores-below-pm.  SPR/EMR/GNR *code are supporting throttling cores below Pm, as spec'ed first for SPR in https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html#throttling-below-pm-spr-onwards.   Thanks to this sightings, we uncovered that CBB pcode has not implemented this legacy capability, and will meet early next week with the CBB Pcode stakeholds 

### Tags
presighting_bdc,FV_PM,SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_6000099A,FIX_IFWI_DMR_AP1_2026.13.3.01,BKC#OKS_DMR_AP_X1_2026WW14_INT, PSF=Y,FIX_BKC_OKS_DMR_AP1_2026WW16

### Conclusion
hw.arch

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: general
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x199`
- `MSR 0x198`
- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.sst_pp_info_11.show`
- `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.platform_rapl_limit_cfg.ppl2`
- `sv.socket0.imh0.pcudata.raplVars.platform_rapl_pid_output.get_value`

## Timeline

- **Submitted**: 2025-12-10 22:04:35
- **Root Caused**: 2025-12-31 03:08:03
- **Closed**: 2026-04-16 20:10:26
- **Days Open**: 126

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
