# HSD 14027346271: [X4][SIMPL] PFM IMH TPMI registers and their implementation on Primecode are missing

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027346271](https://hsdes.intel.com/appstore/article-one/#/14027346271) |
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
| **Feature** | Power/RAPL | 52% |
| **Sub-Feature** | SIMPL | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

According to SIMPL 
DMR HAS
, SIMPL (also known as PFM) there should be 2 TPMI registers: 

SIMPL_DFC_CONTROL

SIMPL_DFC_STATUS

PythonSV TPMI registers for IMH are missing
 (unlike CBB that does have these TPM registers), also in 
Primecode repository I'm not able to locate the implementation.

BIOS: OKSDCRB1.IPC.0032.D91.2603050313

CBB PCODE: 0x46661925dc70d7a5 

IMH PRIMECODE: 0x30320267110113

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

TPMI Register Implementation: Alex confirmed that two TPMI registers for SIMPL are not implemented in prime code, and Alex noted that programming these registers should be straightforward as per the documentation, with Nilanjan assigned to verify and implement.

﻿[26ww11.3]

Feature Absence Confirmation: SIMPL features are not implemented in Primecode, despite being specified in the HAS documentation.

Vidar emphasized the urgency of implementing these features, especially since they are required for both IMH1 and IMH2, and assigned Suchismita and Nilanjan to review and coordinate updates from the architecture team.

### Description
According to SIMPL 
DMR HAS
, SIMPL (also known as PFM) there should be 2 TPMI registers: 

SIMPL_DFC_CONTROL

SIMPL_DFC_STATUS

PythonSV TPMI registers for IMH are missing
 (unlike CBB that does have these TPM registers), also in 
Primecode repository I'm not able to locate the implementation.

BIOS: OKSDCRB1.IPC.0032.D91.2603050313

CBB PCODE: 0x46661925dc70d7a5 

IMH PRIMECODE: 0x30320267110113

### Comments (latest)
++++14615187272 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14027345042.
++++22611808855 agraback
Same comment as from the SIMPL pmt telemetry one: 14027346203: [X4][SIMPL] iMH PrimeCode telemetry implementation is missing would like to revisit the ROI of this given that SIMPL effectively ZBB'd on DMR IMH with only single supported policy in the fusing.
++++14615224413 vwang
Alex confirmed Primecode didn't implement these control and header stuff for SIMPL and not using those TPMI registers at all.
++++22611816998 mbfausto
Team - I have asked in various forums.  Does the current POR/spec say that we are to implement the TPMI registers, and Primecode hasn't implemented them? Whether we change POR in the future or not is not the issue, the open/question is if Primecode implemented the spec as its currently written and POR.

++++22611817045 mbfausto
[CloneScript] Sighting [sighting_central.sighting.id=14027346271] of [component=fw.primecode] in [release=pkg.dmr-a0] has been cloned to a [feature] to [server.bugeco.id=22022229569] of [component=soc.PrimeCode 2.0#] in [release=dmrhub-a0]
++++14615269012 pcanetel
- 'Does the current POR/spec say that we are to implement the TPMI registers, and Primecode hasn't implemented them?' Yes https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html#configuration-and-status-registers-in-tpmi There have been some changes to the HAS and probably the communication hasn't been so efficient, we need clarification on this so Primecode implementation and the HAS match between them. 

++++14615415119 pcanetel
Do we have any update?

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

- **Primary Feature**: Power/RAPL
- **Sub-Feature**: SIMPL
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI registers`
- `TPMI and`
- `TPMI Register`

## Timeline

- **Submitted**: 2026-03-11 05:25:49
- **Root Caused**: 2026-03-24 23:45:06
- **Days Open**: 71

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
