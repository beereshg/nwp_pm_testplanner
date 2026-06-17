# HSD 15019113675: [Google] power_limitation_status and power_limitation_log of package_therm_status are always 1 after RST_CPL4

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [15019113675](https://hsdes.intel.com/appstore/article-one/#/15019113675) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | kwu2 |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.bug |

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
[26ww12.4]
* Debug Patch provided that may address/identify 1 case that is at issue.
* After data from the debug patch is provided, may be a 2nd case.
* Seeing fuse combinations in a way (that seems legal/fine) that FW may not be covering and missing some limit checking.
* Hector --> why is VAL not seeing this with the flattened SIMPL programming, will we/do we see this failure on newer parts?  Where in internal validation should we have caught this?

﻿[26ww12.3]

Alex identified that the mesh RAPL is being flagged even when min, max, and request values are equal, and is consulting with the team to determine if additional checks are needed.

Kevin clarified that Ichiban EVT is a Google developer platform used for stress testing after power-on, and that the team is working to ensure the issue is resolved before further testing.

﻿[26ww12.1]

Register Mapping Clarification: Alex explained the distinction between read-only and write-only registers for PACKAGE_THERM_STATUS and PACKAGE_THERM_command, confirming that Primecode sets the command and Punit hardware aggregates status, resolving confusion about register writes.

The team identified a short period after CPL4 where mesh RAPL limits are flagged, suspecting timing issues with initial checks against default values, and noted that no real limits are set during this phase.

Alex and Sagar planned to continue investigating Primecode flows to pinpoint the cause, with Kevin offering to provide additional data if required, and Alex balancing this investigation with other ES1 blockers.

﻿[26ww11.3]

Alex and Jason discussed how the prime code writes to specific registers, with Jason identifying that MSR 1B1 points to CR10D88, and James noting the importance of distinguishing between package and core level thermal status registers.

James and Alex debated whether the observed power limitation is caused by the core or another agent, concluding that further investigation is needed to determine which IP is responsible for set

### Description
We will see power limit event occur under OVSS w/o any action.

And we check the MSR 0x1b1 bit 10, 11 to confirm the event occur or not.

Google need us to clarify if the behavior can align CRB or not.

So, please help to check below list test result:

1. Use Intel internal os which have been confirmed trigger power limit event or not by MSR register checking on CRB and verify on ichiban system again.

2. Use the OVSS on Intel ichiban 1S which have been confirmed power limit event occur by MSR register checking and verify on CRB again.

### Comments (latest)
++++1566863556 ips_hsdes_brdg
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
    <td style="padding:5px;white-space:normal;word-wrap:break-word;overflow-wrap:break-word;word-break:break-word;-ms-word-break:break-all;border:1px solid #4a4a4a;box-sizing:border-box;background-clip:padding-box;max-width:100%;vertical-align:top;line-height:1.2; mso-line-height-rule:exactly;mso-table-lspace:

### Tags
ADTM_Review,SysDebugDccbBypass,SysDebugCloned, PSF=Y,FIX_PATCH_DMR_AP1_A0_6000099A,FIX_IFWI_DMR_AP1_2026.13.3.01,FIX_BKC_OKS_DMR_AP1_2026WW16

### Conclusion
fw.bug

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
- **Sub-Feature**: general
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x1b1`
- `MSR 0x19c`
- `MSR 0x1B1`
- `MSR 0x19C`
- `TPMI opc_pkg_therm_status`
- `sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem`
- `sv.socket0.imh0.ubox.ncdecs.biosnonstickyscratchpad_mem`
- `sv.socket0.imh0.punit.throttle.package_therm_status.show`

## Timeline

- **Submitted**: 2026-03-03 11:48:19
- **Root Caused**: 2026-03-20 04:00:18
- **Closed**: 2026-04-07 20:32:25
- **Days Open**: 35

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
