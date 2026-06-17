# HSD 14027689587: [DMR][A0] [X4] [PnP] 3uS C1E Latency KPI being violated by several uS

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027689587](https://hsdes.intel.com/appstore/article-one/#/14027689587) |
| **Status** | open.clone |
| **Priority** | 3-medium |
| **Owner** | nyellise |
| **Component** | fw.acode |
| **Defect Die** | compute |
| **Conclusion** |  |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | C1E | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Observing higher exit latency for 99 and 99.9 percentile on X4 compared to X1.

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww17.1]

Jason described the challenge of aligning VISA and A-Log traces, as their timestamps do not match, making it difficult to determine the entry and exit points for C1E state transitions. We need to identify which VISA signals indicate C1E entry and exit, as the current hardware programming continuously selects work points based on core status.

ITH Team Involvement: Jason planned to reach out to the ITH team for assistance in resolving the timestamp issue and to clarify which signals should be monitored.

A meeting was being organized by Vlad to bring together Jason, James, and other stakeholders to discuss and resolve the trace correlation issue.

### Description
Observing higher exit latency for 99 and 99.9 percentile on X4 compared to X1.

### Comments (latest)
++++14615342176 vwang
[CloneScript] PreSighting 14027592595 cloned to Sighting 14027689587

++++14615343509 jtgilmer
Seems related to this?  14027583557 - [UBR w/a Impact] C-states Exit latency increases to 20mS from 115uS using 32D77 IFWI vs 31D76

++++14615343551 vwang 
 @Rotich, Simeon K  please check if this is similar with your sighting below https://hsdes.intel.com/appstore/article-one/#/article/14027583557


++++14615344315 nyellise 
UBR Credit WA is disabled in these latency measurements. So, not the same issue as the HSD mentioned below..


++++14615354649 jtgilmer
Please sync with Simeon then, as he says its fine on latest IFWI (regardless of the 'hammer'?). What are the differences? Rotich, Simeon K Last updated on: Monday, April 20, 202612:29:23 PM(a day ago) id:  14615347503 Using latest IFWI 32.D25 with small hammer(auto) or big hammer, we cannot re-create the high (20mS) exit latency issue.
++++22611856044 nyellise
HI Justin, I had already talked to Simeon. On the latest IFWI’s we are not seeing the 20ms latency impact that was related to the “hammer”. This HSD is addressing a different latency issue. We are violating a 3us Latency KPI for C1E. We are ~2.5us over the target. DMR latency is also higher compared to GNR. This is not related to “hammer”   I have the VISA traces ready for debug, waiting for IDC team’s feedback.   I am also running into an ITH issue where ACODE and VISA trace are using a different timescale. Making it impossible to correlate the events. ITH Showstopper HSD: https://hsdes.intel.com/resource/14027677155 (Acode and VISA trace results are using different timescales) ITH Bug fix being tracked as T2 improvement: https://hsdes.intel.com/resource/22022338936 (Timestamp Misalignment Issue - Traces not synchronized on Unified Timeline) Related PMA DFD RTL bug: https://hsdes.intel.com/resource/14027715602 ([X1 A0] All of the PMA instantiated DVPs Use 6-bit LTA)   Hope this clarifies the confusion.      

++++22611865228 mbfausto
Who specifically from IDC are we waiting for feedback from?  There aren't any updates in a week and need a follow-up promptly please.
++++1363641027 eladva1 
Suggesting the following:  1. Check if Slow C1e / pkg level C1e is happening. I came to understand that all cores are set to C1e at the same time. Can try and check again with all cores but 1 set to C1/C6 instead.  2. From the core side, check the following signals:  These should provide the time from the moment Core is active again and C1e exit began (not directly the wake, but also not too far off it) to when the ratio is back to what you expect it to be.  I also assume that you are doing explicit C1e - meaning requesting EAX=0x1 and not relying on promotions of any kind.  If the issue is seen at any point during this stage, we can explore what part is taking the longest. If not, we can try and see if there is anything weird with the timing between the wake event and the actual wake. 
++++14615388353 nyellise 
Confirmed Slow C1E is n

### Component
fw.acode

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
- **Sub-Feature**: C1E
- **Component Path**: fw.acode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-04-17 10:45:00
- **Days Open**: 34

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
