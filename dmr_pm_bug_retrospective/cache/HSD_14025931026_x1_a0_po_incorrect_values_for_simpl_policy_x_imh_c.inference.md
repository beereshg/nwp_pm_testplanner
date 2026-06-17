# HSD 14025931026: [X1 A0 PO] Incorrect values for SIMPL_POLICY_X_IMH_CFCIO_MAX_FREQ and CFCMEM_MAX_FREQ

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025931026](https://hsdes.intel.com/appstore/article-one/#/14025931026) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | pcanetel |
| **Component** | hw.fuse.xml |
| **Defect Die** | ioe |
| **Conclusion** | hw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 85% |
| **Feature** | Power/RAPL | 52% |
| **Sub-Feature** | SIMPL | — |

**Reasoning**: conclusion='hw.bug' → HW

## Root Cause Summary

Due to a recent update in the SIMPL HAS, now the IMH SIMPL fuses have incorrect values:

https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww42.3]

The fuse CCB items are linked and tracked, with multiple related items documented. 

Hector expressed concern about the lack of defined fuses for upcoming volume validation, noting that delays could impact the VIS fusing schedule. Nilanjan clarified that the relevant fuses are defined but require correct value assignment and release.

Nilanjan committed to working with Archana, Alex, and Keith to separate the required fuses from VFC fuses and ensure their timely release. Anh-thu emphasized the importance of not missing the last opportunity for VIS part inclusion.

Nilanjan agreed to double-check fuse values with Eric and coordinate with Archana to resolve any outstanding issues, aiming to meet the early next week deadline for VIS fusing.

[25ww39.1]

Fuse CCB is scheduled today.
Vidar/Hector will follow up afterwards and move forward .

### Description
Due to a recent update in the SIMPL HAS, now the IMH SIMPL fuses have incorrect values:

https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html

### Comments (latest)
++++14614633468 amunshi
<p>&nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Mattapalli, Jaivardhan</span>&nbsp; - need your help with values for all the SIMPL feature related&nbsp; fuses in IMH as well as BASE DIe ( CBB).</p><p>All fuses are currently at the &quot;default&quot; values.</p><p>









</p>

++++14614633469 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 22021534302.

++++14614633470 hmpicosm
Fuse CCB https://hsdes.intel.com/appstore/article-one/#/14025873957

++++14614633474 hmpicosm
14025873957 (related-link) - link(s) are added via link tab.

++++14614648898 pcanetel
 @Wang, Vidar can we move this to root_caused as we already have a fuse CCB?

++++14614650658 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14025931026] of [component=hw.fuse.xml] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [feature] to [server.bugeco.id=14025962405] of [component=soc.top] in [release=dmrhub-a0]
++++22611568000 pcanetel
Still going on the discussion about SIMPL feature, according to Marupaka, Swapna probably the feature won't be enabled in A0 stepping.
++++14614841853 pcanetel
AN004022BMH2085 (Q9UQ) system Limits frequencies set to 2.1 for all policies. IMH0 pcode_simpl_policy_0_imh_cfcio_max_freq=0x15 pcode_simpl_policy_1_imh_cfcio_max_freq=0x15 pcode_simpl_policy_2_imh_cfcio_max_freq=0x15 pcode_simpl_policy_3_imh_cfcio_max_freq=0x15 pcode_simpl_policy_0_imh_cfcmem_max_freq=0x15 pcode_simpl_policy_1_imh_cfcmem_max_freq=0x15 pcode_simpl_policy_2_imh_cfcmem_max_freq=0x15 pcode_simpl_policy_3_imh_cfcmem_max_freq=0x15 IMH1  pcode_simpl_policy_0_imh_cfcio_max_freq=0x15 pcode_simpl_policy_1_imh_cfcio_max_freq=0x15 pcode_simpl_policy_2_imh_cfcio_max_freq=0x15 pcode_simpl_policy_3_imh_cfcio_max_freq=0x15 pcode_simpl_policy_0_imh_cfcmem_max_freq=0x15 pcode_simpl_policy_1_imh_cfcmem_max_freq=0x15 pcode_simpl_policy_2_imh_cfcmem_max_freq=0x15 pcode_simpl_policy_3_imh_cfcmem_max_freq=0x15
++++22611597115 mbfausto
Is this the correct value?  the fused units are correct?
++++14614845350 pcanetel
VIS parts Q9UN, Q9UQ, Q9UP have the expected value (2.1 for all the policies) in CFCIO_MAX_FREQ and CFCMEM_MAX_FREQ SIMPL fuses.

### Tags
SysDebugCloned,FV_PM,SysDebugDccbBypass,FIX_FUSE_UCC_A0_Y25W45P0,cov.pm.simpl, PSF=Y

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
- **Sub-Feature**: SIMPL
- **Component Path**: hw.fuse.xml

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2025-09-18 09:54:08
- **Root Caused**: 2025-09-24 08:25:20
- **Closed**: 2025-11-26 01:49:33
- **Days Open**: 68

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
