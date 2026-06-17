# HSD 14026805774: [X1 A0 VV] Not seeing C6 autodemotion to C1

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026805774](https://hsdes.intel.com/appstore/article-one/#/14026805774) |
| **Status** | root_caused.awaiting_fix |
| **Priority** | 2-high |
| **Owner** | tensaeke |
| **Component** | fw.acode |
| **Defect Die** | compute |
| **Conclusion** | hw.tuning |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 75% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | C6 | — |

**Reasoning**: errata_status='review_waived' → HW

## Root Cause Summary

IFWI: OKSDCRB1.86B.0029.D89.2511252052

Configuration: 

         Enable C6SP as AcpiC2Enumeration, while keeping AcpiC3Enumeration as Disabled.

         AcpiC2Enumeration
3

          AcpiC3Enumeration 0

          MonitorMWait 1

          C1AutoDemotion 1

          C1AutoUnDemotion 1

-> with the following steps and configuration on latest IFWI release I am seeing it demotes to C0 instead of C1 

STEPS: 

       HWP enabled, 

       turbo enabled: msr 1a0 = 
0x0000000000851089

       turb

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww11.1]

Vax, Elad is on leave, but expects to have initial tuning values by the end of the week. Hector confirmed that the power and performance team is responsible for providing the final values.

Feature Enablement Strategy: Matthew emphasized the importance of enabling the feature for validation with reasonably tuned values, even if final tuning is not complete, to avoid delays in functional validation and bug discovery.

Simeon and Hector noted that the feature is currently disabled by default and can be enabled via BIOS knobs for validation. They agreed that it is better to keep the feature disabled by default until tuning is complete to avoid performance regressions.

Jaivardhan mistioned the default enablement policy for the feature, agreeing to double-check the default setting for the DMR program and ensure it aligns with customer expectations and past experiences.

[26ww10.3]

Calibration will come on a patch. Person who owned this went or reserve duty, Jason looking forward for a person to implement that. Simeon plans to do some tunning as well. 

﻿[26ww10.1]

Tensae and Jason planned to meet after the main meeting to consolidate calibration experiments and further investigate auto demotion tuning, aiming to clarify conflicting information and update the team accordingly.

Tensae expressed the need to review all calibration experiments and results with Jason to ensure a comprehensive understanding before conducting one more experiment and providing an update.

﻿[26ww09.3]

Simeon and Anatoli reviewed the history of auto demotion implementation, noting that previous aCode-based solutions were replaced by pCode in recent products. Anatoli agreed to review the current status and consult with relevant owners.

Ido suggested Jason send email to aCode owners like Rami, Elad etc. to bring their attention.

﻿[26ww09.1]

Jason and Tense are actively debugging this in the workgroup.

﻿[26ww08.3]

Jason confirmed that the trace file was decoded without illegal p

### Description
IFWI: OKSDCRB1.86B.0029.D89.2511252052

Configuration: 

         Enable C6SP as AcpiC2Enumeration, while keeping AcpiC3Enumeration as Disabled.

         AcpiC2Enumeration
3

          AcpiC3Enumeration 0

          MonitorMWait 1

          C1AutoDemotion 1

          C1AutoUnDemotion 1

-> with the following steps and configuration on latest IFWI release I am seeing it demotes to C0 instead of C1 

STEPS: 

       HWP enabled, 

       turbo enabled: msr 1a0 = 
0x0000000000851089

       turbo request: msr
-w 0x404040 -o 0x774 -a

       adjusted epb to performance mode  msr
-w 0 -o 0x1b0 -a

       applied light wl (stress-ng
--cpu 256 -l 20)

### Comments (latest)
++++14614957103 ssingh2
Since this is blocking blocking a complete flow validation - C6 autodemotion to C1 moving this to showstopper

++++14614957101 tensaeke
<p>I<span style="font-family: Arial;"> have attached the acode trace results:</span></p><p><span style="color: rgb(16, 24, 40); font-family: Arial; font-size: 13px;">I am seeing&nbsp;</span><strong style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;"><span style="font-family: Arial;">c6 demotion final decision 0x0</span></strong><span style="color: rgb(16, 24, 40); font-family: Arial; font-size: 13px;">&nbsp;in the Acode trace, is this an indication of why C6 demotion to C1 is not happening?</span></p>

++++14614957100 tensaeke
<p><br /></p><p><span style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;"><br /></span></p><p><span style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;">Adding additional data collected applying the configuration needed for C1 demotion (configurations in the description)</span><span style="color: rgb(16, 24, 40); font-family: Arial; font-size: 13px;">:&nbsp;</span><span style="color: rgb(16, 24, 40); font-family: Arial; font-size: 13px;">I have verified that configuration settings are correctly applied as described in spec. I checked that&nbsp;</span><code style="white-space-collapse: break-spaces; color: rgb(16, 24, 40); font-size: 13px;"><span style="font-family: Arial;">C1_demotion_policy</span></code><span style="color: rgb(16, 24, 40); font-family: Arial; font-size: 13px;">&nbsp;is set to&nbsp;</span><code style="white-space-collapse: break-spaces; color: rgb(16, 24, 40); font-size: 13px;"><span style="font-family: Arial;">0x0</span></code><span style="color: rgb(16, 24, 40); font-family: Arial; font-size: 13px;">&nbsp;(the most aggressive setting for C6→C1 demotion), and confirmed MSR&nbsp;</span><code style="white-space-collapse: break-spaces; color: rgb(16, 24, 40); font-size: 13px;"><span style="font-family: Arial;">0xE2 </span></code><span style="color: rgb(16, 24, 40); font-family: Arial; font-size: 13px;">that C1 demotion is enabled, which are expected settings for C1 demotion to happen.</span></p><p><br /></p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/14026673149" style="width: 755.537px; height: 114.574px;" tabindex="-1" data-processed="true" /></p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/14026673150" style="width: 749.22px; height: 353.609px;" tabindex="-1" data-processed="true" /><br /></p><p><br /></p><p><br /></p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/14026673151" style="width: 812.537px; height: 95.935px;" tabindex="-1" data-processed="true" /><br /></p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/14026673152" style="width: 773.537px; height: 489.18px;" tabindex="-1" data-processed="true" /></p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/14026673153" st

### Tags
FV_PM,SysDebugCloned,SysDebugDccbBypass

### Conclusion
hw.tuning

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
- **Sub-Feature**: C6
- **Component Path**: fw.acode

## Firmware Touchpoints

### BIOS
- `BIOS knob`

## Key Registers

- `sv.socket0.cbb0.computes.pmas.pmsb.resolution_control`
- `sv.socket0.cbb0.compute1.pma8.pmsb.resolution_control.show`
- `sv.socket0.cbb0.computes.pmas.acode.vars.acode_cal_vars.g_c6_cal_db.num_of_int_thr_for_demotion._0`
- `sv.socket0.cbbs.computes.modules`
- `sv.socket0.cbb0.compute0.modules`

## Timeline

- **Submitted**: 2026-01-12 10:25:09
- **Root Caused**: 2026-03-17 00:43:09
- **Days Open**: 129

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
