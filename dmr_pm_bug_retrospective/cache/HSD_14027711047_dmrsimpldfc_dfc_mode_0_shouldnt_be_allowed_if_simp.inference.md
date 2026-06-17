# HSD 14027711047: [DMR][SIMPL/DFC] DFC mode 0 shouldn't be allowed if SIMPL_CBB_DFC_EN fuse is set to 1

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027711047](https://hsdes.intel.com/appstore/article-one/#/14027711047) |
| **Status** | open.clone |
| **Priority** | 3-medium |
| **Owner** | pcanetel |
| **Component** | hw.power |
| **Defect Die** | base |
| **Conclusion** |  |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Core C-States | 52% |
| **Sub-Feature** | C1 | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

According to 
SIMPL HAS
, DFC mode 0 (DFC disabled) should be possible only when fuse SIMPL_
CBB_
DFC_
EN is set to 0, but I am able to set that mode even when DFC is enabled by fuse (SIMPL_
CBB_
DFC_
EN = 1).

Fuses present in my system:

punit_fuses.fw_fuses_num_simpl_policies = 0x1

punit_fuses.fw_fuses_simpl_cbb_dfc_en =0x1

punit_fuses.fw_fuses_simpl_policy_0_cbb_cfc_max_freq = 0x1b

punit_fuses.fw_fuses_simpl_policy_0_cbb_ccp_max_freq_cdyn_0 = 0x1d

punit_fuses.fw_fuses_simpl_policy_0_cbb_

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿

﻿[26ww18.3]

Waiting 

a clear statement from Nilanjan

﻿[26ww18.1]

Patricia and Hector explained that during paranoia checks, they discovered that DFC could be disabled by setting mode 0 in the TPMI register, even when the DFC-enable fuse is set, which contradicts expected behavior and was confirmed as an issue during reviews with Nilanjan.

pCode Orna needs a clear statement from Nilanjan or the architecture team is required to determine whether this is a bug or an architectural limitation, and for now, the team will treat it as a non-bug pending further clarification.

Orna clarified that pCode only applies logic based on the fuse and register values, and that the ability to disable DFC via the register when the fuse is enabled is not under pCode control, but rather a result of how the interface is defined and used by OS or out-of-band software.

﻿[26ww17.3]

Patricia described the system still allows a mode that disables DFC behavior even with the DFC-enable fuse set, which was confirmed as unexpected behavior by architect Nilanjan.

Vidar requested Ptracker logs to expedite debugging, and Patricia agreed to collect them, noting clear evidence of simultaneous high frequency in core and ring domains when DFC is disabled.

Next: pCode team need to debug further.

### Description
According to 
SIMPL HAS
, DFC mode 0 (DFC disabled) should be possible only when fuse SIMPL_
CBB_
DFC_
EN is set to 0, but I am able to set that mode even when DFC is enabled by fuse (SIMPL_
CBB_
DFC_
EN = 1).

Fuses present in my system:

punit_fuses.fw_fuses_num_simpl_policies = 0x1

punit_fuses.fw_fuses_simpl_cbb_dfc_en =0x1

punit_fuses.fw_fuses_simpl_policy_0_cbb_cfc_max_freq = 0x1b

punit_fuses.fw_fuses_simpl_policy_0_cbb_ccp_max_freq_cdyn_0 = 0x1d

punit_fuses.fw_fuses_simpl_policy_0_cbb_ccp_max_freq_cdyn_1 = 0x1d

punit_fuses.fw_fuses_simpl_policy_0_cbb_ccp_max_freq_cdyn_2 = 0x1d

punit_fuses.fw_fuses_simpl_policy_0_cbb_ccp_max_freq_cdyn_3 = 0x1d

punit_fuses.fw_fuses_simpl_policy_0_cbb_ccp_max_freq_cdyn_4 = 0x1d

punit_fuses.fw_fuses_simpl_policy_0_cbb_ccp_max_freq_cdyn_5 = 0x1d

 

Fuse values used to enable DFC

punit_fuses.fw_fuses_simpl_policy_0_cbb_dfc_en_min_cores_active=0x1e

punit_fuses.fw_fuses_simpl_policy_0_cbb_dfc_offset_bins_cfc=0x4

punit_fuses.fw_fuses_simpl_policy_0_cbb_dfc_offset_bins_ccp_cdyn_0=0x3

punit_fuses.fw_fuses_simpl_policy_0_cbb_dfc_offset_bins_ccp_cdyn_1=0x4

punit_fuses.fw_fuses_simpl_policy_0_cbb_dfc_offset_bins_ccp_cdyn_2=0x5

punit_fuses.fw_fuses_simpl_policy_0_cbb_dfc_offset_bins_ccp_cdyn_3
=0x6

punit_fuses.fw_fuses_simpl_policy_0_cbb_dfc_offset_bins_ccp_cdyn_4=0x6

punit_fuses.fw_fuses_simpl_policy_0_cbb_dfc_offset_bins_ccp_cdyn_5=0x6

Requesting P0 ratios for cores and
ring:

p0_fabric_ratio = sv.socket0.cbbs[0].base.tpmi.sst_pp_info_11.p0_fabric_ratio.read()       (0x1b)

sv.sockets.cbbs.base.tpmi.ufs_control.max_ratio = p0_fabric_ratio

sv.sockets.cbbs.base.tpmi.ufs_control.min_ratio = p0_fabric_ratio

 

p0_ratio = sv.socket0.cbbs[0].base.tpmi.sst_pp_info_4.ratio_7.read()                                (0x1c)

psdbg.debug.access_to_msr(offset=0x770, data=1, core=&quot;ALL&quot;)

psdbg.debug.access_to_msr(offset=0x774, data=0x1c1c1c, core=&quot;ALL&quot;) 

Setting DFC (PFM) in mode 0 

# PFM_CONTROL[PFM_CBB_MODE] == 

### Comments (latest)
++++14615351392 pcanetel
During a meeting with DCF architect, he confirmed this as a Pcode bug. Allowing P0 frequencies in cores and ring at the same time in parts with frequencies that should be managed by DFC, could represent a risk.

++++14615351393 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14027710892.
++++1363639061 osumszyk
About the statement  "2’b00: DFC is disabled (default). Only encoding supported if fuse SIMPL_CBB_DFC_EN is set to 1’b0" from DMR SoC IccMax Proactive Limits (SIMPL) Control I understand that when DFC is disabled by fuse, then only value 0 is supported in PFM_CONTROL[PFM_CBB_MODE]. That is, if OS/OOB-SW writes 1, 2 or 3 in PFM_CONTROL[PFM_CBB_MODE] while DFC is disabled by fuse, Pcode behaves as if PFM_CONTROL[PFM_CBB_MODE] is 0. However, when DFC is enabled by fuse, any value in PFM_CONTROL[PFM_CBB_MODE] (0, 1, 2 or 3) can be set and Pcode behaves accordingly. PFM_CONTROL[PFM_CBB_MODE]=0 is a valid value and it means that "although DFC is enabled by fuse, it is disabled by OS/OOB-SW". Anyway, it cannot be a Pcode bug since the value set in DFC enable fuse and the value set in PFM_CONTROL[PFM_CBB_MODE] are not controlled by Pcode. Pcode only reads these values and behaves accordingly. If you want to change Pcode behavior, then it is a change in the requirements, an enhancement, not a bug.
++++22611863074 pcanetel
Adding @Palit, Nilanjan 
++++1363639288 aodler
 @Sumszyk, Orna thanks for the detailed clarification. We need confirmation from the arch folks.
++++22611865457 mbfausto
Hector, team, what's the answer here?  Does the PM HAS indicate that this is a LEGAL setting and therefore possible behavior?  Or should FW protect this and clip from 0 to another value?     However, when DFC is enabled by fuse, any value in PFM_CONTROL[PFM_CBB_MODE] (0, 1, 2 or 3) can be set and Pcode behaves accordingly.     PFM_CONTROL[PFM_CBB_MODE]=0 is a valid value and it means that "although DFC is enabled by fuse, it is disabled by OS/OOB-SW".
++++14615384422 vwang
Yesterday, the discussion chat has already been setup with Arch  @Palit, Nilanjan waiting his response.
++++22611883354 mbfausto
Please pull out key data, summaries from all external sources and provide it in the ticket.  GREAT there's a teams chat, but this sighting hasn't been updated in over a week please.  What's the current status?

++++22611883379 pcanetel
Still waiting for architect input.
++++14615411900 jsbrooks
This sighting stemmed from DFC review we had with Nilanjan. The outcome of that review was to file a sighting to drive the spec update regarding case where DFC fuse enable is set to one and TPMI mode 00 is not supported. To rootcause to doc.arch, we just need confirmation on this direction, right?  That would later lead to the enhancement mentioned below by Anatoli and Orna.
++++1363657888 osumszyk
Hi, About the spec change, I would suggest declaring as illegal the value 0 in PFM_CONTRO

### Tags
FV_PM

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

- **Primary Feature**: Core C-States
- **Sub-Feature**: C1
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI register`
- `TPMI mode`
- `sv.socket0.cbbs.base.tpmi.pfm_control`
- `sv.socket0.cbbs.computes.pmas.pmsb.io_core_operating_point.core_ratio_16p67`

## Timeline

- **Submitted**: 2026-04-21 07:50:17
- **Days Open**: 30

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
