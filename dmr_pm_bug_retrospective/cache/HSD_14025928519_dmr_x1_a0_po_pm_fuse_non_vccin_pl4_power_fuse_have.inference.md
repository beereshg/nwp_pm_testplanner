# HSD 14025928519: [DMR] [X1 A0 PO] [PM] [Fuse] Non_vccin_pl4_power fuse have 0 value

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025928519](https://hsdes.intel.com/appstore/article-one/#/14025928519) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | pcanetel |
| **Component** | hw.fuse.xml |
| **Defect Die** | ioe |
| **Conclusion** | hw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 85% |
| **Feature** | Power/RAPL | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: conclusion='hw.bug' → HW

## Root Cause Summary

- Platform SC00901159H0032

- Fused Part =Q7YL + IFWI=OKSDCRB1.86B.2025.35.3.01_2688.D02_6020095E_1P0_NonIPClean_Trace_DebugSigned_update_primecode_pcode.bin

punit.pcode_non_vccin_pl4_power=
0x0

Expected non zero value to compute a right value of Power Limit 4.

Critical for X4 parts.

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
- Platform SC00901159H0032

- Fused Part =Q7YL + IFWI=OKSDCRB1.86B.2025.35.3.01_2688.D02_6020095E_1P0_NonIPClean_Trace_DebugSigned_update_primecode_pcode.bin

punit.pcode_non_vccin_pl4_power=
0x0

Expected non zero value to compute a right value of Power Limit 4.

Critical for X4 parts.

### Comments (latest)
++++14614633315 vwang
Updating the change after getting the alignment on a Teams chat (Shumin, Archana, Steven Chen, Juan) 1. NON_VCCIN_PL4_POWER fuse must be tied to NON_VCCIN_POWER_PmaxApp attribute. NON_VCCIN_PL4_POWER = dec2hex(NON_VCCIN_POWER_PmaxApp.Value * 8) 2. Shumin will be populating the attribute with worst case total power (hot and cold) for the Iccmax.app scenario of the following rails: VCCINF, VCCANA (dual), VCCFA_EHV, VCCDDR_HV (dual). 3. This attribute will get a value based on per-SKU calculation 4. Independent of this fuse, Shumin will also populate IMH_P_PL4_SCALE_FACTOR and IMH_S_PL4_SCALE_FACTOR for PrimeCode to determine the primary and secondary non-vccin power. These attributes also get per-SKU values.

++++14614633333 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14025928519] of [component=hw.fuse.xml] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [bug] to [server.bugeco.id=14025930786] of [component=soc.top] in [release=dmrhub-a0]
++++22611470898 mbfausto
Fix released for IMH1: >>> hsdt.pt(id_l=['14025928519']) Records Found:  1 ===========|=====================|==============================|======================|=========================|================|==============================================================================================================   HSD ID   |     TICKET TYPE     |           RELEASE            |      COMPONENT       |      STATUS.REASON      |     STATE      |                                                 TICKET NOTES ===========|=====================|==============================|======================|=========================|================|============================================================================================================== 14025855689|   Si Pre-Sighting   |   package.dmrap-ucc-x1-a0    |     hw.fuse.xml      |root_caused.pursuing_fix |  WAIT_FIX_DEF  |[Conclusion]=hw.bug  [BugID]=14025930786  [Die]=ioe  [Fix]=fuse/permanent/A0/ 14025928519|     Si Sighting     |   package.dmrap-ucc-x1-a0    |     hw.fuse.xml      |root_caused.pursuing_fix |  WAIT_FIX_DEF  |[Conclusion]=hw.bug  [BugID]=14025930786  [Die]=ioe  [Fix]=fuse/permanent/A0/ 14025930786|     SOC Bugeco      |          dmrhub-a0           |       soc.top        |       open.clone        | [!] WAIT_SCOPE |[Class]=documentation  [CTS]=fuse.recipe  [CCB]=review_waived,  [WA]=/pending 14025875779|      Fuse CCB       |          dmrhub-a0           |   soc.fuse_config    |        complete         |      POR       |[BugClass]=fuse_prog  [Type]=enhancement  [CCB]=review_needed  [Releases]=dmrhub-a0  [FctRev]=0x1a0040a0  [FfrRev]=UCC_A0_Y25W37P0 14025895193|      Fuse CCB       |         dmrhubmax-a0         |   soc.fuse_config    |       open.clone        |   WAIT_FCCB    |[BugClass]=  [Type]=enhancement  [CCB]=review_needed  [Releases]=dmrhubmax-a0 ===========|=====================|==============================|======================|=========================|=============

### Tags
SysDebugCloned,SysDebugDccbDone,FV_PM,FIX_FUSE_UCC_A0_Y25W37P0,cov.pm.pmax, PSF=Y

### Conclusion
hw.bug

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

- **Primary Feature**: Power/RAPL
- **Sub-Feature**: general
- **Component Path**: hw.fuse.xml

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2025-09-18 03:19:39
- **Root Caused**: 2025-09-18 08:46:30
- **Closed**: 2025-09-24 22:08:27
- **Days Open**: 6

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
