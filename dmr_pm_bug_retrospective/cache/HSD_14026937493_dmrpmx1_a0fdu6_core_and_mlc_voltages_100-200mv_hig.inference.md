# HSD 14026937493: [DMR][PM][X1 A0][FDU6] Core and MLC voltages 100-200mV high then expected, only FDU6

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026937493](https://hsdes.intel.com/appstore/article-one/#/14026937493) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | jamesrow |
| **Component** | val.env.test |
| **Defect Die** | compute |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Telemetry | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

PLATFORM: 
an004022bms1815

pcode collats:

nga test result: 

https://nga-prod.laas.intel.com/#/dmr_fv/planning/testResult/55eb54ca-e8c6-4538-96de-6a0ff7ad415e

 

expectation:

based on the ratio of the core and vf curve expect voltage to be with 26mV(10 units)  from the actual when including itd offset.

the expectation is upheld in multiple volume runs where core ratio is as expected with 2mV of error.

example of core ITD pass, mlc fail though: 
22022017784 - [DMR][PM][X1 A0][FDU1] MLC ITD 

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
PLATFORM: 
an004022bms1815

pcode collats:

nga test result: 

https://nga-prod.laas.intel.com/#/dmr_fv/planning/testResult/55eb54ca-e8c6-4538-96de-6a0ff7ad415e

 

expectation:

based on the ratio of the core and vf curve expect voltage to be with 26mV(10 units)  from the actual when including itd offset.

the expectation is upheld in multiple volume runs where core ratio is as expected with 2mV of error.

example of core ITD pass, mlc fail though: 
22022017784 - [DMR][PM][X1 A0][FDU1] MLC ITD offset not included in workpoint target, only config with this failure. base voltage expectation matches actual voltage

observation: 

ccf, ucie are all core in their voltage expectations, core and mlc off by 100-200mV

different from  
22021924882 - [DMR][PM][X1 A0] All MLC voltages higher than expected by ~80mV due to single core requesting max voltage

since error is larger and cor is also effected.

different from 
22022017784 - [DMR][PM][X1 A0][FDU1] MLC ITD offset not included in workpoint target, only config with this failure. base voltage expectation matches actual voltage

since voltage is higher not lower then expected

Initial debug:

need reruns that will include telemetry on the current ratio of the cores during the test

table:

### Comments (latest)
++++14615011367 jamesrow
<p>next steps:</p><ul><li>request reruns from nga to collect telemetry on core ratios and workpoints</li></ul>

++++14615011368 jamesrow
<p>reproduced high core and mlc voltages on another fdu6 system:&nbsp;<a href="https://nga.laas.intel.com/#/dmr_fv/planning/testResult/1b7a8f81-0b4f-4fe9-ab6c-2948069152e6" target="_blank" tabindex="-1">https://nga.laas.intel.com/#/dmr_fv/planning/testResult/1b7a8f81-0b4f-4fe9-ab6c-2948069152e6</a><a href="https://nga.laas.intel.com/#/dmr_fv/planning/testResult/1b7a8f81-0b4f-4fe9-ab6c-2948069152e6" target="_blank" tabindex="-1"></a></p><p>also rerun including additional debug info on MCLK operating points and hints to pcode.</p><p><br /></p><p>cannot be reproduced on any other config, other configs only observed mlc smaller voltage delta's as seen in:&nbsp;<a href="https://hsdes.intel.com/appstore/article-one/#/article/22021924882" target="_blank" tabindex="-1">https://hsdes.intel.com/appstore/article-one/#/article/22021924882</a>&nbsp;</p><p><br /></p><p><br /></p><p>next step request debug time on system 1841 or 1815 to collect acode.vars for acode debug.&nbsp;</p>

++++14615011369 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 22022017876.
++++22611743697 jamesrow
with an update to content with MLC not using separate itd and vf fusing until zero we see good results. need to rerun on FDU6. table from system that orginally had mlc fails:

### Tags
FV_PM

### Conclusion
not_a_bug

### Component
val.env.test

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
- **Component Path**: val.env.test

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-01-30 00:30:46
- **Root Caused**: 2026-02-06 00:14:29
- **Closed**: 2026-02-06 01:57:10
- **Days Open**: 7

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
