# HSD 16029401177: [DMR][X1 A0][RACL] CBB Mesh Ratio is scaling down to minimum value before cores ratio with RACL TDC limits sweep.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029401177](https://hsdes.intel.com/appstore/article-one/#/16029401177) |
| **Status** | complete.wont_validate |
| **Priority** | 3-medium |
| **Owner** | salmanha |
| **Component** | hw.power |
| **Defect Die** | base |
| **Conclusion** | doc |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Collaterals
:

Platform
: AN004022BMH2291.amr.corp.intel.com.

IFWI
: 
 
OKSDCRB1.86B.0029.D15.2511052036

HAS: 

https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Dual_VCCIN_RACL_VRTDC/RACL_VR_TDC.html#racl-implementation

Summary:

When we are sweeping TDC limits from upper values to lower values then we are observing that CBB mesh freq is going down to its minimum value even before core reaches to Pn.

Expectation is that first cores will scale down to Pn and then mesh freq

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww50.4]

Issue looks like an implementation misalignment between the CBB mesh frequency expectation due to a 
potentially architectural requirement needing clarification

, Nilanjan/Timothy/Suchi will follow up with pCode/primeCode implementation, from spec the following sentence needs to be defined:

Mesh Frequency reduction (as part of RACL): Mesh frequency limiter comes in if there is still an excursion after core frrequecy is limited to minimal. After core reaches Pn, if we still have excursion, Pcode should reduce mesh frequency one bin at a time until there is no RACL violation.

### Description
Collaterals
:

Platform
: AN004022BMH2291.amr.corp.intel.com.

IFWI
: 
 
OKSDCRB1.86B.0029.D15.2511052036

HAS: 

https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Dual_VCCIN_RACL_VRTDC/RACL_VR_TDC.html#racl-implementation

Summary:

When we are sweeping TDC limits from upper values to lower values then we are observing that CBB mesh freq is going down to its minimum value even before core reaches to Pn.

Expectation is that first cores will scale down to Pn and then mesh freq will start reducing one bin at a time.

In [24]: sv.socket0.cbb0.base.tpmi.sst_pp_info_11.show()

0x00000000 : rsvd (63:56) (ro/v) -- Reserved

0x00000008 : pm_fabric_ratio (55:48) (ro/v) -- Fabric (Uncore) minimum freq...

0x00000008 : p1_fabric_ratio (47:40) (ro/v) -- Fabric (Uncore) TDP frequenc...

0x0000001b : p0_fabric_ratio (39:32) (ro/v) -- Fabric (Uncore) maximum freq...

0x00000004 : pm_core_ratio (31:24) (ro/v) -- Core minimum frequency ratio.

0x00000006 : pn_core_ratio (23:16) (ro/v) -- Core maximum efficiency freque...

0x00000015 : p1_core_ratio (15:08) (ro/v) -- Core TDP frequency ratio.

0x00000022 : p0_core_ratio (07:00) (ro/v) -- Core maximum frequency ratio l...

### Comments (latest)
++++1667168498 sumanku2
[CloneScript] Sighting 16029401177 cloned from PreSighting 16029362346
++++22611636774 mbfausto 
re-openeing, this sighting isn't root-caused, nothing in the comments indicating the issue, and no clones by sysdebug (or links/adoption to the doc ticket with the issue). Also if there is an implementation change needed ... this is NOT just a doc update.  If this is a "spec update with a FW change in response" that is not the same thing as a 'doc update'.  @Wang, Vidar  - Please help make sure the sighting is root-caused properly and identify what tickets we have or need and lets get those cloned.  Thanks! My Speculation:  hw.power / hw.arch root-cause with a server.bugeco doc.arch SPEC ticket for SOC PM Spec updates.  Arch/SLD should then file the appropriate FW mitigation tickets once the spec is updated/defined.  This appears so far to now be *not* a doc bug.
++++14614897256 vwang
Discussed with Arch team and confirmed the current throttling behavior is as expected, with all domains reducing frequency together, and that the confusion arose from a misstatement in the HAS.

++++14614897274 vwang 
.

++++14614899585 vwang 
SOC PM HAS update only  – no implementation changes Updated HAS is: https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Dual_VCCIN_RACL_VRTDC/RACL_VR_TDC.html#racl-implementation


++++14614899632 vwang
[CloneScript] Sighting [sighting_central.sighting.id=16029401177] of [component=hw.power] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [bug] to [server.bugeco.id=14026616676] of [component=soc.top] in [release=dmrhub-a0]
++++22611645540 sghosh7 
HAS updated: https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Dual_VCCIN_RACL_VRTDC/RACL_VR_TDC.html There is no bug from throttling perspective, Mesh freq reduction for RACL is already following the mechanism defined in DMR Fabric DVFS HAS: https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html#raplracl-limits-for-imh-memory-io-fabric-frequencies

### Tags
FV_PM,FV_PM_BDC,SysDebugCloned,SysDebugCloned,SysDebugDccbBypass

### Conclusion
doc

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

- `sv.socket0.cbb0.base.tpmi.sst_pp_info_11.show`

## Timeline

- **Submitted**: 2025-12-09 21:47:45
- **Root Caused**: 2025-12-16 13:01:12
- **Closed**: 2025-12-18 03:38:20
- **Days Open**: 8

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
