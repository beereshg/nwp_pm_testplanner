# HSD 14027804531: [DMR][X4 A0 VV][LOM]{UFS} Memory and IO Frequency throttling while running xz and hitting TDP with LOM Enabled and Disabled

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027804531](https://hsdes.intel.com/appstore/article-one/#/14027804531) |
| **Status** | open.clone |
| **Priority** | 3-medium |
| **Owner** | avaldezb |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** |  |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

When running xz workload, we observe memory and IO frequency throttling upon reaching TDP. This behavior occurs with LOM Enabled and LOM disabled while ELC High is active.

Using histo, we captured the frequency requested by ELC High (per mode ratio) and the limiting reason mask. At the point where we hit TDP, the limiting reasons mask changes from 0x0 to 0x4 (. At the same time, the frequency ratio requested by ELC High changes from 21 to 8.

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww21]

UFS Algorithm Tuning may need few weeks.

﻿[26ww20.3]

UFS Algorithm Tuning

Sagar provided a patch and extensive data collected, with discussions ongoing with architects about next steps

Testing showed that keeping frequency high in Lambo improved performance in memory-intensive workloads but negatively impacted core-bound workloads, prompting further investigation into algorithm adjustments.

Timothy explained that the team is tuning the UFS algorithm, focusing on balancing memory and core-intensive workloads, with XZ workload being neither fully memory nor core intensive, and efforts underway to achieve optimal frequency.

Targeted ES2 for improvements; the problem is considered a high priority but requires time for resolution.

### Description
When running xz workload, we observe memory and IO frequency throttling upon reaching TDP. This behavior occurs with LOM Enabled and LOM disabled while ELC High is active.

Using histo, we captured the frequency requested by ELC High (per mode ratio) and the limiting reason mask. At the point where we hit TDP, the limiting reasons mask changes from 0x0 to 0x4 (. At the same time, the frequency ratio requested by ELC High changes from 21 to 8.

### Comments (latest)
++++14615398209 srotich
<p>We&nbsp; did 557.xZ workload analysis and memory frequency is&nbsp; pushed to 800MHZ at TDP and&nbsp; we are not seeing the expected performance gains when LOM is enabled:<img src="https://hsdes.intel.com/rest/binary/22022428850" style="width: 1721.88px;" tabindex="-1" /></p><p><br /></p><p>Frequency and power response pattern with ELC enabled; and LOM enabled/disabled shows severe memory frequency throttling gradually to 800MHZ (on both IMH0 &amp; IMH1) when running XZ at TDP. This results in performance loss.</p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/22022428851" style="width: 1875.99px;" tabindex="-1" /><br /></p>

++++14615398211 vwang
Please add the discussions with Primecode team and Arch.

++++14615398212 srotich
<p>From DMR post-si meeting discussion with Architects and primecode team on 1 May 2026,</p><p>it was decided to have a test patch that has the option to use/ignore RAPL condition in ELC High/mid ratio in the DVFS flow:</p><p></p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/22022433356" style="width: 645.99px;" tabindex="-1" /><br /></p><p>This will help determine if we can make the also latency-sensitive and this help improve XZ performance.&nbsp;</p><p>The test path will be experimental and after running all regression workloads (plus PNPJET); then it can be made default.</p><p>&nbsp;</p><p><br /></p><p><br /></p><p><br /></p><p>&nbsp;</p>

++++14615398210 vchagan
[AI-GENERATED UPDATE - val_agent / GitHub Copilot]
This ticket was updated automatically by val_agent. Please verify the changes below before acting on this ticket or sharing it upstream. If any field is incorrect, revert it and leave a follow-up comment.

Fields changed: sub_forum=vt.pm, owner=avaldezb (was empty), reason=assigned, tag=val_agent

Evidence basis: Memory/IO freq throttle on TDP hit; ELC High freq 21-&gt;8; fw.primecode set; owner from submitted_by

++++14615398217 vwang
[CloneScript] PreSighting 22022421284 cloned to Sighting 14027804531
++++22611898893 mbfausto
Team - there are no comments or updates since cloning a week ago.  Please provide a current status of what's going on, open experiments, next steps and who owns them please.  THANKS!
++++14615419685 srotich
These are the overall performance impact of test patch.  we see expected benefits with patch for memory intensive workloads kike XZ, but we lose performance in core intensive workloads like povray and exchange.  Overall SIR perf is about same; but we lose 1% in SFR. Exploring other tuning solutions.

++++14615422683 vwang
This is an UFS Algorithm Tuning effort. Sagar provided a patch and extensive data collected, with discussions ongoing with architects about next steps Testing showed that keeping frequency high in Lambo improved performance in memory-intensive workloads but negatively impacted core-bound workloads, prompting further investigation into algorithm adjustments. Timothy explained that the team is tuning the UFS al

### Tags
val_agent

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: general
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-05-07 02:15:53
- **Days Open**: 14

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
