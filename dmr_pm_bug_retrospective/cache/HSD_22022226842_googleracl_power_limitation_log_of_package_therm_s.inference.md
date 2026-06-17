# HSD 22022226842: [Google][RACL] power_limitation_log of package_therm_status (MSR 0x1B1_bit11) is always 1 after RST_CPL4

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22022226842](https://hsdes.intel.com/appstore/article-one/#/22022226842) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | vikramma |
| **Component** | hw.power |
| **Defect Die** | ioe |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Power/RAPL | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

We will see power limit event occur under OVSS w/o any action.

And we check the MSR 0x1b1 bit 10, 11 to confirm the event occur or not.

Google need us to clarify if the behavior can align CRB or not.

So, please help to check below list test result:

1. Use Intel internal os which have been confirmed trigger power limit event or not by MSR register checking on CRB and verify on ichiban system again.

2. Use the OVSS on Intel ichiban 1S which have been confirmed power limit event occur by MSR r

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww17.1]

Alex provided a debug patch to collect additional logs, confirming that the telemetry numbers from PrimeCode matched hand calculations for current values sent to the RACL PID.

Anna reviewed data from Narahari and found RACL PID regulation to be working as expected in their tests, while Alex continued to observe excursions in other environments, prompting further comparison.

Anna and Timothy emphasized the need to capture detailed input and output data from the RACL PID controller during boot, including current values, TDC targets, and PID outputs, to identify the root cause of observed excursions.

The team agreed to coordinate with Erik and Sahil to set up comprehensive data capture, aiming to collect long traces from the onset of oscillation or excursion through to reporting, to facilitate deeper analysis.

﻿[26ww16.1]

Arch discussion is on-going

﻿[26ww15.4]

Anna reported that initial RACL validation showed correct regulation to set current limits, but further validation under stress and corner cases is pending. Timothy and Nilanjan raised concerns about why the RACL limit would be tripped during reset and emphasized the need to identify the root cause.

Matthew and Joseph identified relevant power delivery and validation team members to engage in the investigation, and Anna agreed to connect with them for further debugging.

Joseph inquired about when RACL logging is enabled during boot. Vikram confirmed that the issue can be reproduced in both Google and Intel labs, and Vikram will assist with logging and data collection.

﻿[26ww15.1]

NPID/FastRAPL Power Spike Debug and Response Analysis: the team analyzed power spikes during boot related to NNPID and FastRAPL, discussing detection, response mechanisms, and plans for further debugging in a dedicated follow-up meeting.

Power Spike Detection and Response: Anna and Timothy explained that NNPID is designed to self-tune and regulate power spikes, with FastRAPL being more sensitive due to its lack 

### Description
We will see power limit event occur under OVSS w/o any action.

And we check the MSR 0x1b1 bit 10, 11 to confirm the event occur or not.

Google need us to clarify if the behavior can align CRB or not.

So, please help to check below list test result:

1. Use Intel internal os which have been confirmed trigger power limit event or not by MSR register checking on CRB and verify on ichiban system again.

2. Use the OVSS on Intel ichiban 1S which have been confirmed power limit event occur by MSR register checking and verify on CRB again.

### Comments (latest)
++++22611815305 ips_hsdes_brdg
<p style="margin-top: 0px; color: #0070C0;" class="no-indent"><span lang="EN" style="font-size:10.0pt;font-family:&quot;IntelOne Text&quot;,sans-serif">Routing rule <b>customer_project_name</b> matched:</span></p>
    <table role="presentation" width="1050" border="0" cellspacing="0" cellpadding="0" style="width:1050px;max-width:1050px;table-layout:fixed;border-collapse:collapse;border-spacing:0;mso-table-lspace:0pt;mso-table-rspace:0pt;word-wrap:break-word;overflow-wrap:break-word;">
<colgroup>
  <col style="width:100px;max-width:100px;" />
  <col style="width:128px;max-width:128px;" />
  <col style="width:60px;max-width:60px;" />
  <col style="width:134px;max-width:134px;" />
  <col style="width:60px;max-width:60px;" />
  <col style="width:84px;max-width:84px;" />
  <col style="width:61px;max-width:61px;" />
  <col style="width:123px;max-width:123px;" />
  <col style="width:60px;max-width:60px;" />
  <col style="width:240px;max-width:240px;" />
</colgroup>
  <tbody><tr>
    <th style="padding:5px;white-space:nowrap;text-align:left;border:1px solid #4a4a4a;box-sizing:border-box;background-color:#0095FF;color:#FFF;">customer_company</th>
    <th style="padding:5px;white-space:nowrap;text-align:left;border:1px solid #4a4a4a;box-sizing:border-box;background-color:#0095FF;color:#FFF;">customer_project_name</th>
    <th style="padding:5px;white-space:nowrap;text-align:left;border:1px solid #4a4a4a;box-sizing:border-box;background-color:#0095FF;color:#FFF;">family</th>
    <th style="padding:5px;white-space:nowrap;text-align:left;border:1px solid #4a4a4a;box-sizing:border-box;background-color:#0095FF;color:#FFF;">suspected_problem_area</th>
    <th style="padding:5px;white-space:nowrap;text-align:left;border:1px solid #4a4a4a;box-sizing:border-box;background-color:#0095FF;color:#FFF;">cpu</th>
    <th style="padding:5px;white-space:nowrap;text-align:left;border:1px solid #4a4a4a;box-sizing:border-box;background-color:#0095FF;color:#FFF;">in_slot_model</th>
    <th style="padding:5px;white-space:nowrap;text-align:left;border:1px solid #4a4a4a;box-sizing:border-box;background-color:#0095FF;color:#FFF;">new owner</th>
    <th style="padding:5px;white-space:nowrap;text-align:left;border:1px solid #4a4a4a;box-sizing:border-box;background-color:#0095FF;color:#FFF;">new customer_company</th>
    <th style="padding:5px;white-space:nowrap;text-align:left;border:1px solid #4a4a4a;box-sizing:border-box;background-color:#0095FF;color:#FFF;">new odm</th>
    <th style="padding:5px;white-space:nowrap;text-align:left;border:1px solid #4a4a4a;box-sizing:border-box;background-color:#0095FF;color:#FFF;">new notify</th>
  </tr>
  <tr>
    <td style="padding:5px;white-space:normal;word-wrap:break-word;overflow-wrap:break-word;word-break:break-word;-ms-word-break:break-all;border:1px solid #4a4a4a;box-sizing:border-box;background-clip:padding-box;max-width:100%;vertical-align:top;line-height:1.2; mso-line-height-rule:exactly;mso-table-lspace

### Tags
ADTM_Review,SysDebugCloned,SysDebugCloned_RCBypass,SysDebugDccbDone,SysDebugDccbDriver,FIX_PATCH_DMR_AP1_A0_600009A2,FIX_IFWI_DMR_AP1_2026.20.3.04

### Conclusion
hw.arch

### Component
hw.power

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
- **Sub-Feature**: general
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x1B1`
- `MSR 0x1b1`
- `MSR 0x19c`
- `MSR
     0x1B1`
- `MSR
0x19c`
- `MSR
0x1b1`
- `MSR 0x8b`
- `MSR 0x19C`
- `TPMI PLR`
- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.opc_pkg_therm_status.show`

## Timeline

- **Submitted**: 2026-03-24 01:57:12
- **Root Caused**: 2026-04-23 04:21:18
- **Closed**: 2026-05-19 20:14:50
- **Days Open**: 56

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
