# HSD 16029895595: [DMR A0 VV][X4][RAPL] The mitigation algo is not triggered by primecode when power is limited

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029895595](https://hsdes.intel.com/appstore/article-one/#/16029895595) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | kumara5 |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Power/RAPL | 80% |
| **Sub-Feature** | Socket RAPL | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

The mitigation algorithm is not triggered by prime code when power budget is limited.

Expectation:-

After setting Power Limit to 0, the rapl pid should lower down to 1 and core should throttle down to Pm

Observation:-

After setting TPMI PL1 socket rapl limit to 0

ptpcfsms.ptpcfsms.socket_rapl_pl1_control=0x4000000000280000

    ptpcfsms.ptpcfsms.socket_rapl_pl1_control.lock=0x0

    ptpcfsms.ptpcfsms.socket_rapl_pl1_control.pwr_lim_en=0x1

    ptpcfsms.ptpcfsms.socket_rapl_pl1_control.rsvd=

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww10.3]

primecode team fixed the division by 0 issue on latest debug patch. Confirmation of 1w is all that needed to be confirmed. Erick has already merged the change. This sighting can be root-caused or merged with 22022067937 which is root caused to the same JIRA
, any other symptom can be tracked on a separate sighting. JIRA that fixes the issue 

SERVERPMFW-25508

﻿[26ww09.3]

Power Limit Not Affecting Core Ratios: Carlos reported that setting the TPMI power limit to zero does not lower the core ratios as expected, a behavior that previously worked with earlier prime code patches. The team reviewed logs showing the PID output remaining at 15 instead of dropping to 1.

Erick and Alex discussed the internal handling of PID output variables, noting that the TPMI input is being read correctly but the PID output is not being updated as anticipated. Erick committed to reviewing the code to identify the root cause.

Nilanjan questioned whether baseline test cases, such as setting PL1 to zero, had been validated in the current codebase. Erick was unsure and agreed to investigate further, while Carlos offered to provide additional debug data if needed.

[26ww08.4]

Amit6 reported that when the power limit is set to zero, neither core throttling nor PID value reduction occurs, and noted that this behavior was not present in an earlier version of the prime code.

Alex requested that the affected component be specified as firmware prime code to ensure proper tracking.

Amit6 provided additional details, showing that the power consumed remains the same regardless of the power limit setting

### Description
The mitigation algorithm is not triggered by prime code when power budget is limited.

Expectation:-

After setting Power Limit to 0, the rapl pid should lower down to 1 and core should throttle down to Pm

Observation:-

After setting TPMI PL1 socket rapl limit to 0

ptpcfsms.ptpcfsms.socket_rapl_pl1_control=0x4000000000280000

    ptpcfsms.ptpcfsms.socket_rapl_pl1_control.lock=0x0

    ptpcfsms.ptpcfsms.socket_rapl_pl1_control.pwr_lim_en=0x1

    ptpcfsms.ptpcfsms.socket_rapl_pl1_control.rsvd=0x0

    ptpcfsms.ptpcfsms.socket_rapl_pl1_control.time_window=0xa

    ptpcfsms.ptpcfsms.socket_rapl_pl1_control.pwr_lim=0x0

Primecode is reading correctly the limit and updating the  internal pcudata variable to 0

pkg_pl1_rapl_limit_cfgs_1.power_limit=0x0

But PID is still not lowered, we expect a 1 value for a 0 PL limit

raplVars.socket_rapl_pid_output=0x15

raplVars.platform_rapl_pid_output=0xff

So cores ratios are not lowered

raplVars.clos_rapl_freq_0=0x15

raplVars.clos_rapl_freq_1=0x15

raplVars.clos_rapl_freq_2=0x15

raplVars.clos_rapl_freq_3=0x15

More Details:-

BIOS Version: OKSDCRB1.86B.0032.D44.2602111815

IMH PRIMECODE | 0x21020265244437 -- 

FAIL

BIOS Version: OKSDCRB1.86B.0032.D14.2602052017

IMH PRIMECODE | 0x1272026134525fb
 -->
Pass

### Comments (latest)
++++1667299802 kumara5
<p>At the time of failure when PL1 limit is 0, the core is running at 2100MHz which is unexpected, no activity in core 0. This seems to be unexpected</p><p>The socket RAPL PID when PL1 = 0&nbsp;</p><div style="font-family: Consolas, &quot;Courier New&quot;, monospace; line-height: 19px; white-space: pre;"><span style="background-color: rgb(255, 255, 0);">raplVars.socket_rapl_pid_output=0x15</span></div><p><br /></p><p><br /></p><p><br /></p><p><span style="font-family: &quot;Courier New&quot;;">+---------------------------------+---------------+--------------+--------------+------------------------------+-------+-------+-------------+-------------+</span></p><p><span style="font-family: &quot;Courier New&quot;;">| Module&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; | Pstate Mode&nbsp; &nbsp;|&nbsp; &nbsp;PEGA ratio |&nbsp; &nbsp;Pcode GPSS | PLR Die&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; |&nbsp; &nbsp;WP1 |&nbsp; &nbsp;WP4 | IPC C0/C1&nbsp; &nbsp;|&nbsp; &nbsp;MSR 0x198 |</span></p><p><span style="font-family: &quot;Courier New&quot;;">+=================================+===============+==============+==============+==============================+=======+=======+=============+=============+</span></p><p><span style="font-family: &quot;Courier New&quot;;">| socket0.cbb0.compute1.module8&nbsp; &nbsp;| PEGA&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; |&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;32 |&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;21 | (['POWER'], ['PKG PL1_CSR']) |&nbsp; &nbsp; 21 |&nbsp; &nbsp; 27 | <span style="background-color: rgb(255, 255, 0);">5.22/5.22&nbsp;</span> &nbsp;|&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 21 |</span></p><p><span style="font-family: &quot;Courier New&quot;;">+---------------------------------+---------------+--------------+--------------+------------------------------+-------+-------+-------------+-------------+</span></p><p><span style="font-family: &quot;Courier New&quot;;">| socket0.cbb0.compute1.module9&nbsp; &nbsp;| PEGA&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; |&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;32 |&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;21 | (['POWER'], ['PKG PL1_CSR']) |&nbsp; &nbsp; 21 |&nbsp; &nbsp; 27 | 5.22/5.22&nbsp; &nbsp;|&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 21 |</span></p><p><span style="font-family: &quot;Courier New&quot;;">+---------------------------------+---------------+--------------+--------------+------------------------------+-------+-------+-------------+-------------+</span></p><p><span style="font-family: &quot;Courier New&quot;;">| socket0.cbb0.compute1.module10&nbsp; | PEGA&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; |&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;32 |&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;21 | (['POWER'], ['PKG PL1_CSR']) |&nbsp; &nbsp; 21 |&nbsp; &nbsp; 27 | 5.22/5.22&nbsp; &nbsp;|&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 21 |</span></p><p><span style="font-family: &quot;Courier New&quot;;">+--------

### Tags
FV_PM,SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_60000994,FIX_IFWI_DMR_AP1_2026.10.4.01,FIX_BKC_OKS_DMR_AP1_2026WW12

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
- **Sub-Feature**: Socket RAPL
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x198`
- `TPMI PL1`
- `TPMI power`
- `TPMI input`
- `sv.socket0.imh0.pcudata.fast_rapl_inst.patch_persistent.dfx_pwr_target_override_enable`
- `sv.socket0.imh0.pcudata.fast_rapl_inst.patch_persistent.dfx_pwr_target_override_value`

## Timeline

- **Submitted**: 2026-02-19 21:33:06
- **Root Caused**: 2026-03-04 22:17:38
- **Closed**: 2026-04-27 18:47:29
- **Days Open**: 66

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
