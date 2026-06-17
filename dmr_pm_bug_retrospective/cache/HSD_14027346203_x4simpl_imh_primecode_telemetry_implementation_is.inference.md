# HSD 14027346203: [X4][SIMPL] iMH PrimeCode telemetry implementation is missing

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027346203](https://hsdes.intel.com/appstore/article-one/#/14027346203) |
| **Status** | root_caused.awaiting_fix |
| **Priority** | 2-high |
| **Owner** | pcanetel |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Telemetry | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

According to the 
SIMPL HAS
, IMH should have residency counters but this doesn't exist on Primecode.

Also SIMPL is not mentioned on 
IMH Telemetry HAS 
neither on pmt_telemetry.json (Primecode)

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww14.1]

POR and Spec Implementation: Matthew and Alex clarified that either Prime Code needs to implement the existing specifications for TPMI and SIMPL, or a change in the POR must be driven by architecture, with Nilanjan identified as the decision-maker.

[26ww12.4]
* Nilanjan confirmed offline he is going to be reviewing and working on this SIMPLE issue this week.

﻿[26ww12.3]

Hector explained that although the current system supports only a single simple policy, Nilanjan requested validation for multiple simple policies, as future scenarios may require this capability after post-PRQ when have more than one policy enabled.

Nilanjan is the final authority on decisions regarding the validation of multiple simple policies, and no changes to this process are expected unless directed by Nilanjan.
﻿[26ww12.1]

Missing SIMPL Telemetry: The team identified that SIMPL telemetry definitions are not present in the code and discussed the need for PM telemetry updates. Alex explained that residency counters and telemetry SRAM space are required, and Suchismita clarified the distinction between PM telemetry and Primecode pushes, planning to sync with Eric Diemer for further clarification.

Suchismita raised questions about the ownership and scope of the telemetry, distinguishing between PM telemetry and prime code telemetry, and Alex clarified that the SIMPL policy is firmware-defined and not tied to a specific RC, with counters tracked and pushed to telemetry SRAM.

﻿[26ww11.3]

Feature Absence Confirmation: Carlos and Alex confirmed that PMT telemetry and SIMPL features are not implemented in Primecode, despite being specified in the HAS documentation.

Vidar emphasized the urgency of implementing these features, especially since they are required for both IMH1 and IMH2, and assigned Suchismita and Nilanjan to review and coordinate updates from the architecture team.

### Description
According to the 
SIMPL HAS
, IMH should have residency counters but this doesn't exist on Primecode.

Also SIMPL is not mentioned on 
IMH Telemetry HAS 
neither on pmt_telemetry.json (Primecode)

### Comments (latest)
++++14615187217 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14027327143.

++++14615218272 ejdehaem
SIMPL in the IMH was reduced to a single Policy.  There is no dynamic change in SIMPL policy and such the Residency is 100% I see no value in implementing this functionality in DMR.
++++22611809577 mbfausto
1) Do we need a SPEC update (CCB or just doc.arch and update) if we are updated this way? 2) With a 'single policy', do we still have any opens/issues? If we just need to change the spec, and no CCB is needed, lets file the server.bugeco to update the SPEC and root-cause this as a 'doc' bug.
++++14615224008 coramire
 @Fausto, Matthew B We need Architecture feedback to ZBB this implementation, SIMPL is fuse limited to 1 policy on DMR AP, but we expect this feature to be available and fully functional even with 1 policy, if later on the program more policies are fuse enabled given manufacturing(future skus) or validation(mitigation for power delivery issues) feedback we expect to support it.

++++14615227437 vwang
Hector explained that although the current system supports only a single simple policy, @Palit, Nilanjan  requested validation for multiple simple policies, as future scenarios may require this capability after post-PRQ when have more than one policy enabled. @Palit, Nilanjan  is the final authority on decisions regarding the validation of multiple simple policies
++++22611815155 mbfausto 
If the current POR is 1 policy, and ARch wants more.  Please REJECT this sighting and file a Feature CCB.  Sightings are not used for new feature requests. Or are we saying the POR of the feature supports multiple, it was just not IMPLEMENTED as such?
++++14615249282 coramire
 @Fausto, Matthew B This telemetry is not related with number of supported policy's as it can be implemented with single policy, from my viewpoint is a good way to discover that there is only one supported policy. it is up to Architecture to zbb the implementation if there is no value. From validation side if it is in the HAS it is required to be implemented. If primecode viewpoint is that there is no value they need to follow up with architecture and request to change the HAS.
++++22611817010 mbfausto
I completely agree, Carlos.  And I'm not sure why the pings about this are going unanswered.  I mistakingly thought the telemetry was tied to the single policy. In this case I'm root-causing this as the forum_notes and previous conversations make it ... mostly clear ... this is a feature in the HAS that has not been implemented.   If we chose NOT to implement it, that's a CBB and POR change that PM/Primecode can drive through as a mitigation for this ticket,

++++22611817022 mbfausto
[CloneScript] Sighting [sighting_central.sighting.id=14027346203] of [component=fw.primecode] in [release=pkg.dmr-a0] has been cloned to a [feature] to [server.bugeco.id=22022229540] of [component=soc.PrimeCode 2.0#] in [release=dm

### Tags
FV_PM,SysDebugCloned,SysDebugDccbBypass

### Conclusion
fw.arch

### Component
fw.primecode

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

- **Primary Feature**: Telemetry
- **Sub-Feature**: general
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI and`

## Timeline

- **Submitted**: 2026-03-11 05:15:07
- **Root Caused**: 2026-03-24 23:42:56
- **Days Open**: 71

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
