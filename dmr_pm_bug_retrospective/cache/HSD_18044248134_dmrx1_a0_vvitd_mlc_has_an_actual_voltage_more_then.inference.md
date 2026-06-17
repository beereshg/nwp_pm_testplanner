# HSD 18044248134: [DMR][X1 A0 VV][ITD] MLC has an actual voltage more then 0.026V delta from expected voltage

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [18044248134](https://hsdes.intel.com/appstore/article-one/#/18044248134) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | jamesrow |
| **Component** | fw.acode |
| **Defect Die** | compute |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | SoC Thermal | 52% |
| **Sub-Feature** | ITD | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

2026-02-14 07:25:22,230:ERROR
    
:IP being tested has a actual voltage more then 0.026V delta from expected voltage

2026-02-14 07:25:22,233:ERROR
    
:No Failure Description

2026-02-14 07:25:22,233:ERROR
    
:
    
Error occurred in log_errorOrExit(). Check traceback.

2026-02-14 07:25:22,235:RESULT
    
:02/14/26 07:25:22 - ran 0:02:39.697635

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww14.1]

James described reproducing the voltage delta issue on a volume X4 system with reduced core count and ITD turned off, adding halts in checks to ensure data freshness and noting that this improved the accuracy of MLC delta measurements.

Curve Calculation and Delta Source: James explained that the expected voltage is calculated using the same VF curve as the core, with the worst-case seed in bucket, and that the delta is the difference between this expectation and the actual measured value, highlighting that the seed in curves can behave unexpectedly and may contribute to the observed deltas.

Jason and James agreed to review the aCode dump and compare ICCP levels, with James noting that all relevant variables are logged for comparison, and that further testing on other systems is planned to determine if the issue is system-specific.

﻿[26ww13.3]

James reported difficulties in reproducing the issue on available systems, with failed attempts due to PLR check failures and the need for fuse overrides to simplify debug. The team agreed to consult with the tools team and to attempt further data collection with reduced core counts.
we will need to collect more data for Jason to debug.

﻿[26ww13.1]

James mentioned the system was booting right now, we should have some results today.

[26ww12.4]

* Feedback from Core PM

* NBL may be a factor here, gave register to check if its involved (disable and see if matching expectations)

    ==> NBL changes FIVR WP based on which row is elected, and may elevate voltage to compensate for 0s

﻿[26ww12.3]

Voltage Delta Analysis and Logging for MLC Issue: James worked on reproducing and logging voltage deltas across modules, reducing core counts to simplify analysis, and planned to rerun tests to capture logs for modules with large errors.

James reduced the core count on the test system to two to simplify voltage delta analysis, collected all relevant data in A code variables, and identified modules with higher-than-expe

### Description
2026-02-14 07:25:22,230:ERROR
    
:IP being tested has a actual voltage more then 0.026V delta from expected voltage

2026-02-14 07:25:22,233:ERROR
    
:No Failure Description

2026-02-14 07:25:22,233:ERROR
    
:
    
Error occurred in log_errorOrExit(). Check traceback.

2026-02-14 07:25:22,235:RESULT
    
:02/14/26 07:25:22 - ran 0:02:39.697635

### Comments (latest)
++++1862549332 jamesrow
<p>MLC checks still failing after acode expectation changes were pushed to scripts.</p><p>some mlc passing with improved delta's but still cannot be ignored.</p><p><br /></p><p>next steps:</p><p>rerun on debug to confirm mlc expecations still working</p><p><br /></p><p><br /></p><p><br /></p><p>MLC values passing wit few mV delta when checking in mlc expectations changes:</p><p><img src="https://hsdes.intel.com/rest/binary/22022107773" style="width: 1435px;" tabindex="-1" /><br /></p><p><br /></p>

++++1862549333 jamesrow
<p>reproduced on debug system&nbsp;Gmzp301002h0038:</p><p><br /></p><p>with fuses enabled several mV of error and fails the lenient pass criteria of 26mV:</p><p><img src="https://hsdes.intel.com/rest/binary/22022108212" style="width: 1833px;" tabindex="-1" />&nbsp;</p><p><br /></p><p><br /></p><p>with itd fuses disabled almost no error:</p><p><img src="https://hsdes.intel.com/rest/binary/22022108213" style="width: 1907px;" tabindex="-1" /></p><p><br /></p><p><br /></p><p>will confirm correct data being used for the calulations, since core is still very correct, nothing wrong with core data that we expect mlc to use as well, such as fuses, temp and ratio&nbsp;</p>

++++1862549334 jamesrow
<p>fuses and temp used for core and mlc check is the same by printing the fuses and temp used for the check:</p><p>#mlc uses core's temp</p><p><br /></p><p>#module 31 fuses and temp</p><p>ip Core id31 fuses:</p><p>{'cutoff_v': 0.970947265625, 'cutoff_v2': 1.0260009765625, 'cutoff_tj': 103.0, 'floor_v': 0.0, 'slope': 0.0025177001953125, 'slope2': 0.5390625, 'min_override_temp': 104.0, 'slope_above_cutoff_tj': 0.0, 'vx': 1.02625931237869, 'min_accurate_temp': 0x0}</p><p>temperature: 3.5</p><p>mlc temperture : 4.0</p><p><br /></p><p>#mlc module 31 fuses and temp</p><p>ip Core id31 fuses:</p><p>{'cutoff_v': 0.970947265625, 'cutoff_v2': 1.0260009765625, 'cutoff_tj': 103.0, 'floor_v': 0.0, 'slope': 0.0025177001953125, 'slope2': 0.5390625, 'min_override_temp': 104.0, 'slope_above_cutoff_tj': 0.0, 'vx': 1.02625931237869, 'min_accurate_temp': 0x0}</p><p>temperature: 3.5</p><p>mlc temperture : 4.0</p><p><br /></p><p><br /></p><p><br /></p><p>Summary, below not the cause:</p><ul><li>fuses, as same used for both core and mlc check</li><li>temperature, as same temp used for both checks</li><li>vf curve and cdyn curves, as no error when itd is disabled</li></ul><p><br /></p>

++++1862549335 jamesrow
<p>X4 also failed:&nbsp;<a href="https://nga-prod.laas.intel.com/#/dmr_fv/failureManagement/failures/602c8e8a-1c22-41c7-a8ca-299602b91ba7" target="_blank" tabindex="-1">https://nga-prod.laas.intel.com/#/dmr_fv/failureManagement/failures/602c8e8a-1c22-41c7-a8ca-299602b91ba7</a><a href="https://nga-prod.laas.intel.com/#/dmr_fv/failureManagement/failures/602c8e8a-1c22-41c7-a8ca-299602b91ba7" target="_blank" tabindex="-1"></a></p><ul><li>one mlc with error greater then 25mV(10 wp units), still several MLCs with close to failing with the lenient

### Tags
FV_PM

### Conclusion
not_a_bug

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

- **Primary Feature**: SoC Thermal
- **Sub-Feature**: ITD
- **Component Path**: fw.acode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-02-25 11:21:54
- **Closed**: 2026-04-01 20:40:17
- **Days Open**: 35

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
