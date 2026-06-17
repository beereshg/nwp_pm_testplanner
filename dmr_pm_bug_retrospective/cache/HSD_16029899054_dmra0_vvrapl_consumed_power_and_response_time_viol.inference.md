# HSD 16029899054: [DMR][A0 VV][RAPL] Consumed Power and response time violation in fast rapl power limit

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029899054](https://hsdes.intel.com/appstore/article-one/#/16029899054) |
| **Status** | rejected.merged |
| **Priority** | 2-high |
| **Owner** | kumara5 |
| **Component** | fw.acode |
| **Defect Die** | soc |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Power/RAPL | 75% |
| **Sub-Feature** | Fast RAPL | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Consumed power is exceeding the fast rapl power limit around 110W-130W and also does not converge with 4ms in X1.

At higher power the workload is not enough to force the consumed power to violate the limits so we may be seeing finer data. 

But in the mid range we consistently observe that the power excursions are violating the set design rule.

Expectation - The steady state err is expected to be <1% and should converge within 4ms as per the doc 
https://docs.intel.com/documents/pm_doc/src/ser

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww10.3]

Based on the input on the forum, merging this sighting with 
16029389030 - [DMR_PMSS][Pre-VV][X1][RAPL][tunning]: PPL1 settling time is high (~15 sec) irrespective of the TW

﻿[26ww09.3]

Simeon has a PID receipt that could help on this. AMit will try it out.

﻿[26ww09.1]

Amit will test the latest 

IFWI that has UP 990 or greater

### Description
Consumed power is exceeding the fast rapl power limit around 110W-130W and also does not converge with 4ms in X1.

At higher power the workload is not enough to force the consumed power to violate the limits so we may be seeing finer data. 

But in the mid range we consistently observe that the power excursions are violating the set design rule.

Expectation - The steady state err is expected to be <1% and should converge within 4ms as per the doc 
https://docs.intel.com/documents/pm_doc/src/server/GNR/post_si/RAPL_Tuning/RAPL_Tuning_Guide.html#objectives
 

Observation on X1 system(TDP =325W):-

BIOS- OKSDCRB1.86B.0031.D94.2601260110

System - SC00901159H0001

The red straight lines on the graph shows the response time violation 

Orange line is the fast rapl set power limit 

Blue lines indicate the instantaneous power consumption of package (
imh0.pcudata.pkgRAPLDomain.pkg_power_consumed.read())

Workload running (./ptat -ct 5)

Sweeping FAST limits: [105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 151]

Setting FAST limit to 150 W (more finer)

Setting FAST limit to 110 W (

more high's and low's in consumed power

)

NO Workload 

Sweeping FAST limits: [94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104]

Setting FAST limit to 90 W (finer)

Setting FAST limit to 110 W (more high's and low's in consumed power)

### Comments (latest)
++++1667300845 kumara5
<p>In GNR we had &lt;1% power consumption tolerance as passing criteria&nbsp;<a href="https://docs.intel.com/documents/pm_doc/src/server/GNR/post_si/RAPL_Tuning/RAPL_Tuning_Guide.html#objectives" target="_blank" tabindex="-1">https://docs.intel.com/documents/pm_doc/src/server/GNR/post_si/RAPL_Tuning/RAPL_Tuning_Guide.html#objectives</a>&nbsp;</p><p><img src="https://hsdes.intel.com/rest/binary/16029783838" style="width: 573.965px;" tabindex="-1" /><br /></p>

++++1667300846 kumara5
<p>This issue is seen on X4 on debug system</p><p><br /></p><p><span style="font-family: &quot;Courier New&quot;;">2026-02-13 03:51:38,430:INFO</span><span style="white-space: pre; font-family: &quot;Courier New&quot;;">	</span><span style="font-family: &quot;Courier New&quot;;">:Sampled 188 power values for FAST_RAPL over 0.0025s: [160, 414, 160, 352, 162, 311, 210, 219, 595, 159, 566, 158, 600, 159, 605, 158, 335, 159, 473, 163, 445, 159, 323, 449, 160, 522, 160, 347, 277, 158, 523, 163, 457, 159, 433, 158, 352, 447, 159, 405, 168, 315, 439, 162, 502, 157, 536, 160, 188, 407, 160, 464, 163, 468, 159, 403, 160, 334, 390, 157, 345, 276, 159, 522, 166, 534, 160, 445, 160, 160, 528, 159, 447, 161, 310, 370, 166, 495, 158, 518, 161, 321, 352, 160, 515, 161, 448, 160, 426, 159, 350, 159, 337, 580, 159, 586, 158, 587, 158, 597, 161, 609, 341, 272, 159, 491, 161, 401, 158, 322, 452, 157, 381, 160, 320, 423, 158, 522, 163, 465, 159, 433, 159, 379, 560, 158, 370, 162, 341, 250, 192, 479, 158, 540, 159, 571, 333, 158, 546, 162, 440, 156, 400, 159, 332, 292, 160, 356, 219, 303, 321, 168, 565, 157, 452, 177, 404, 532, 159, 451, 159, 329, 319, 163, 477, 163, 380, 162, 309, 441, 158, 525, 163, 443, 158, 399, 160, 359, 576, 158, 349, 180, 314, 455, 164, 540, 158, 553]</span></p><p><span style="font-family: &quot;Courier New&quot;;">2026-02-13 03:51:38,430:INFO</span><span style="white-space: pre; font-family: &quot;Courier New&quot;;">	</span><span style="font-family: &quot;Courier New&quot;;">:Max Power value for FAST_RAPL over sampled interval: 609 W</span></p><p><span style="font-family: &quot;Courier New&quot;;">2026-02-13 03:51:38,430:INFO</span><span style="white-space: pre; font-family: &quot;Courier New&quot;;">	</span><span style="font-family: &quot;Courier New&quot;;">:Sleeping for 1.000000000 seconds</span></p><p><span style="font-family: &quot;Courier New&quot;;">2026-02-13 03:51:39,452:INFO</span><span style="white-space: pre; font-family: &quot;Courier New&quot;;">	</span><span style="font-family: &quot;Courier New&quot;;">:Core Frequency = 2.8 Ghz</span></p><p><span style="font-family: &quot;Courier New&quot;;">2026-02-13 03:51:39,452:INFO</span><span style="white-space: pre; font-family: &quot;Courier New&quot;;">	</span><span style="font-family: &quot;Courier New&quot;;">:Consumed Power (avg over PL2 window) = 311 W, Max Power reached : 609 W</span></p><p><span style="font-family: &quot;Courier New&quot;;">2026-02-13 03:51:39,465:INFO</span><s

### Tags
FV_PM

### Conclusion
no_root_cause.rejected

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

- **Primary Feature**: Power/RAPL
- **Sub-Feature**: Fast RAPL
- **Component Path**: fw.acode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-02-20 11:49:38
- **Closed**: 2026-03-04 23:26:26
- **Days Open**: 12

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
