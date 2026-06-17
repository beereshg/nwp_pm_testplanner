# HSD 22022119354: [DMR-UCC][PMAX] MTPMAX and FDD power protectors not triggering POR throttling action

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22022119354](https://hsdes.intel.com/appstore/article-one/#/22022119354) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | sesparza |
| **Component** | hw.power |
| **Defect Die** | base |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Power/RAPL | 52% |
| **Sub-Feature** | PMAX | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Summary:

========

Throttle_IP selector registers default to 0, causing not POR Throtling actions in MTPMAX and FDD power protectors.

throttle_agg_pick_droop_throttle_output=0x0 

throttle_agg_pick_fast_throttle_output=0x0

For MTPMAX the throttling must be a clock divider type and for FDD the throttling must be an architectural type. To achive this the next Throttle_IP selector register must be 1:

throttle_agg_pick_droop_throttle_output=0x1 

throttle_agg_pick_fast_throttle_output=0x1

HAS i

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww10.1]

Suchismita clarified that their role is to update the HAS documentation to reflect the required throttling mechanisms, while Ido and Nazar are responsible for driving the implementation and coordination with the CBB team.

Timothy and Matthew discussed whether the issue is a hardware, implementation, or specification gap, concluding that it is a configurable muxing issue that can be addressed via firmware or configuration changes rather than hardware modifications.

Matthew emphasized that the architecture team, led by Ido, should drive the bugeco to closure, ensuring all mitigation steps are documented and implemented, and that the HAS update is only one part of the overall solution.

### Description
Summary:

========

Throttle_IP selector registers default to 0, causing not POR Throtling actions in MTPMAX and FDD power protectors.

throttle_agg_pick_droop_throttle_output=0x0 

throttle_agg_pick_fast_throttle_output=0x0

For MTPMAX the throttling must be a clock divider type and for FDD the throttling must be an architectural type. To achive this the next Throttle_IP selector register must be 1:

throttle_agg_pick_droop_throttle_output=0x1 

throttle_agg_pick_fast_throttle_output=0x1

HAS info 
Throttle Aggregator MAS.mmd

### Comments (latest)
++++22611781027 vwang
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14027135957.

++++22611781028 vwang
[CloneScript] PreSighting 14027135957 cloned to Sighting 22022119354

++++22611781075 imelamed
Based on our debug efforts and Carlo’s experiments, we have identified that some of the Muxes in the throttle aggregator were not correctly programmed to provide the required throttling across different power delivery scenarios. It appears that the legacy requirements from GNR were not adequately documented in the DMR HAS area and were not communicated to the CBB team. Fortunately, the throttle aggregator allows for patching or fuse changes to update the Mux settings and meet DMR’s needs. Our immediate next step is to document the following in the DMR Power Delivery / SOC PM HAS: The required throttling actions in the Core when PMAX/PMAX-MT are triggered The required throttling actions in the Core when FDD is triggered I recommend filing a PM Architecture bug with this description and assigning it to Suchi, who has agreed to capture these requirements. The CBB team can then clone this PM Arch bug HSD to implement the necessary Mux overrides. Finally, I suggest keeping the sighting open and not marking it as root caused until all experiments are completed and validated. Ido. 

++++22611784951 mbfausto
Any updates on the experiment results?

++++22611784957 mbfausto
 @Wang, Vidar  - I have updated various fields - given its an SOC PM HAS definition, we should clone to ioe / IMH server.bugeco of cloneType='spec' for a doc.arch ticket.  Once defined and documented, CBB mitigation tickets (as Ido mentions below) to pCode and/or soc_config Fuse CCB tickets as applicable.

++++22611784960 mbfausto
Raising to HIGH as potential fuse changes based on mitigation approach.
++++14615128771 sesparza
According to @Brown, Yuval these are the fuses to modify the aggregator registers: #The fuses for the throttle aggregator which are connected to the COREs: bgr_infra_2_fuse.bgr_infra_2_fuse_throttle_agg_pick_fast_throttle_output = 0x1 bgr_infra_2_fuse.bgr_infra_2_fuse_throttle_agg_pick_droop_throttle_output = 0x1 bgr_infra_1_fuse.bgr_infra_1_fuse_throttle_agg_pick_fast_throttle_output = 0x1 bgr_infra_1_fuse.bgr_infra_1_fuse_throttle_agg_pick_droop_throttle_output = 0x1 bgr_infra_0_fuse.bgr_infra_0_fuse_throttle_agg_pick_fast_throttle_output = 0x1 bgr_infra_0_fuse.bgr_infra_0_fuse_throttle_agg_pick_droop_throttle_output = 0x1 bgr_infra_3_fuse.bgr_infra_3_fuse_throttle_agg_pick_fast_throttle_output = 0x1 bgr_infra_3_fuse.bgr_infra_3_fuse_throttle_agg_pick_droop_throttle_output = 0x1 Note, default value is 0, the request is to change them to 1.

++++14615148298 vwang
[CloneScript] Sighting [sighting_central.sighting.id=22022119354] of [component=hw.power] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [spec] to [server.bugeco.id=14027248580] of [component=soc.top] in [release=dmrhub-a0]

++++14615318

### Tags
Power_PRS,PTP_SoC,SysDebugCloned,FIX_FUSE_UCC_AP1_A0_Y26W16P0,SysDebugDccbDone,SysDebugDccbDriver

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

- **Primary Feature**: Power/RAPL
- **Sub-Feature**: PMAX
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbbs.base.fuses.bgr_infra_2_fuse.bgr_infra_2_fuse_throttle_agg_pick_fast_throttle_output`
- `sv.socket0.cbbs.base.fuses.bgr_infra_2_fuse.bgr_infra_2_fuse_throttle_agg_pick_droop_throttle_output`
- `sv.socket0.cbbs.base.fuses.bgr_infra_1_fuse.bgr_infra_1_fuse_throttle_agg_pick_fast_throttle_output`
- `sv.socket0.cbbs.base.fuses.bgr_infra_1_fuse.bgr_infra_1_fuse_throttle_agg_pick_droop_throttle_output`
- `sv.socket0.cbbs.base.fuses.bgr_infra_0_fuse.bgr_infra_0_fuse_throttle_agg_pick_fast_throttle_output`

## Timeline

- **Submitted**: 2026-02-24 05:46:53
- **Root Caused**: 2026-03-04 11:06:54
- **Closed**: 2026-05-08 00:54:40
- **Days Open**: 72

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
