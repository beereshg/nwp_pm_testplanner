# HSD 16030141410: [DMR][X4 A0 VV][Fast RAPL] Consumed Power violation in fast rapl/PL2 power limit

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16030141410](https://hsdes.intel.com/appstore/article-one/#/16030141410) |
| **Status** | open.clone |
| **Priority** | 2-high |
| **Owner** | salmanha |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** |  |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Power/RAPL | 80% |
| **Sub-Feature** | Fast RAPL | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

Consumed power is exceeding the fast rapl power limit.

Expectation - The steady state err is expected to be <1% and should converge within 4ms as per the doc 
https://docs.intel.com/documents/pm_doc/src/server/GNR/post_si/RAPL_Tuning/RAPL_Tuning_Guide.html#objectives
 

Observation on A0 X4 system(Fused TDP: 500):-

BIOS Version: OKSDCRB1.86B.0032.D91.2603050314

QDF String: Q9UC

System - 
ba00302ecos0018

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww20.1]

Erick explained that the tuning worker for FastRAPL will revert to the classic PID and conduct manual tuning sweeps, with potential spec changes or HSD updates to reflect the new implementation, and clarified that Srihari's team is responsible for the tuning.

﻿[26ww17.3]

TF work in progress. The NNPID working group is actively debugging and conducting various tuning experiments. We will provide an update here once a potential fix is identified or once next steps have been determined in consultation with the architects.

﻿[26ww17.1]

Sagar confirmed the daily RAPL TF on going.

﻿[26ww16.4]

Sagar reported on experiments and data collection for Fast RAPL issues, with plans to update the ticket once results are available, and Shubham confirmed the sharing of relevant P-code patches.

﻿[26ww15.1]

Amit is on vacation

﻿[26ww14.1]

Timothy and Anna reviewed recent data showing power limit violations, confirmed that NNPID is involved, and described ongoing debug meetings and attempts to tune the fast RAPL instance.

Anna emphasized the need to collect more debug data to understand the root cause, with plans to meet with Sahil and continue active debugging in the weekly sync.

Anna offered to be added to relevant HSDs and debug efforts, and provided updates on other related issues, encouraging the team to include her in future communications for NNPID-related topics.

﻿[26ww13.1]

Observed Power Limit Deviations: Amit6 described that when setting PL2 to 219W, the average measured power was 270W, indicating a significant deviation from the expected value, with even larger discrepancies observed in fast RAPL cases.

Alex suggested checking with the PTP team to see if similar behavior was observed, and Simeon agreed to compare results using other power tracking tools such as turbostat to validate the findings.

Amit6 will attach relevant log and data files, and Alex requested additional data such as histograms and comparisons with other tools to better understa

### Description
Consumed power is exceeding the fast rapl power limit.

Expectation - The steady state err is expected to be <1% and should converge within 4ms as per the doc 
https://docs.intel.com/documents/pm_doc/src/server/GNR/post_si/RAPL_Tuning/RAPL_Tuning_Guide.html#objectives
 

Observation on A0 X4 system(Fused TDP: 500):-

BIOS Version: OKSDCRB1.86B.0032.D91.2603050314

QDF String: Q9UC

System - 
ba00302ecos0018

### Comments (latest)
++++1667381206 kumara5
<p>In GNR we had &lt;1% power consumption tolerance as passing criteria&nbsp;<a href="https://docs.intel.com/documents/pm_doc/src/server/GNR/post_si/RAPL_Tuning/RAPL_Tuning_Guide.html#objectives" target="_blank" tabindex="-1">https://docs.intel.com/documents/pm_doc/src/server/GNR/post_si/RAPL_Tuning/RAPL_Tuning_Guide.html#objectives</a>&nbsp;</p><p><img src="https://hsdes.intel.com/rest/binary/16029783838" style="width: 573.965px;" tabindex="-1" /><br /></p>

++++1667381207 kumara5
<p>This issue is seen on X4 on debug system</p><p><br /></p><p><span style="font-family: &quot;Courier New&quot;;">2026-02-13 03:51:38,430:INFO</span><span style="white-space: pre; font-family: &quot;Courier New&quot;;">	</span><span style="font-family: &quot;Courier New&quot;;">:Sampled 188 power values for FAST_RAPL over 0.0025s: [160, 414, 160, 352, 162, 311, 210, 219, 595, 159, 566, 158, 600, 159, 605, 158, 335, 159, 473, 163, 445, 159, 323, 449, 160, 522, 160, 347, 277, 158, 523, 163, 457, 159, 433, 158, 352, 447, 159, 405, 168, 315, 439, 162, 502, 157, 536, 160, 188, 407, 160, 464, 163, 468, 159, 403, 160, 334, 390, 157, 345, 276, 159, 522, 166, 534, 160, 445, 160, 160, 528, 159, 447, 161, 310, 370, 166, 495, 158, 518, 161, 321, 352, 160, 515, 161, 448, 160, 426, 159, 350, 159, 337, 580, 159, 586, 158, 587, 158, 597, 161, 609, 341, 272, 159, 491, 161, 401, 158, 322, 452, 157, 381, 160, 320, 423, 158, 522, 163, 465, 159, 433, 159, 379, 560, 158, 370, 162, 341, 250, 192, 479, 158, 540, 159, 571, 333, 158, 546, 162, 440, 156, 400, 159, 332, 292, 160, 356, 219, 303, 321, 168, 565, 157, 452, 177, 404, 532, 159, 451, 159, 329, 319, 163, 477, 163, 380, 162, 309, 441, 158, 525, 163, 443, 158, 399, 160, 359, 576, 158, 349, 180, 314, 455, 164, 540, 158, 553]</span></p><p><span style="font-family: &quot;Courier New&quot;;">2026-02-13 03:51:38,430:INFO</span><span style="white-space: pre; font-family: &quot;Courier New&quot;;">	</span><span style="font-family: &quot;Courier New&quot;;">:Max Power value for FAST_RAPL over sampled interval: 609 W</span></p><p><span style="font-family: &quot;Courier New&quot;;">2026-02-13 03:51:38,430:INFO</span><span style="white-space: pre; font-family: &quot;Courier New&quot;;">	</span><span style="font-family: &quot;Courier New&quot;;">:Sleeping for 1.000000000 seconds</span></p><p><span style="font-family: &quot;Courier New&quot;;">2026-02-13 03:51:39,452:INFO</span><span style="white-space: pre; font-family: &quot;Courier New&quot;;">	</span><span style="font-family: &quot;Courier New&quot;;">:Core Frequency = 2.8 Ghz</span></p><p><span style="font-family: &quot;Courier New&quot;;">2026-02-13 03:51:39,452:INFO</span><span style="white-space: pre; font-family: &quot;Courier New&quot;;">	</span><span style="font-family: &quot;Courier New&quot;;">:Consumed Power (avg over PL2 window) = 311 W, Max Power reached : 609 W</span></p><p><span style="font-family: &quot;Courier New&quot;;">2026-02-13 03:51:39,465:INFO</span><s

### Tags
FV_PM

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
- **Sub-Feature**: Fast RAPL
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI mailbox`
- `TPMI sub`
- `sv.socket0.imh0.pcudata.fast_rapl_inst.patch_persistent.dfx_pwr_target_override_enable`
- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status`

## Timeline

- **Submitted**: 2026-03-23 11:46:56
- **Days Open**: 59

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
