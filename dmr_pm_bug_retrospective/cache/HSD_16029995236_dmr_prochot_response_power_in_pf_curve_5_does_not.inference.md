# HSD 16029995236: [DMR] Prochot Response Power in PF Curve 5 does not work as expected when Prochot is injected (with P0 > 3200)

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029995236](https://hsdes.intel.com/appstore/article-one/#/16029995236) |
| **Status** | rejected.cannot_reproduce |
| **Priority** | 3-medium |
| **Owner** | kumara7 |
| **Component** | fw.acode |
| **Defect Die** | ioe |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | PState Stack | 75% |
| **Sub-Feature** | Turbo | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

When Prochot is injected, cores are throttling to their respective prochot freq when prochot_response_power is set to &quot;pcode_socket_virus_power_frequency_curve_power_point_0/1/2/3/4&quot;

But in case of &quot;pcode_socket_virus_power_frequency_curve_power_point_5&quot;, cores throttles to Pm (400) instead of respective prochot freq (3300). 

This table highlights the 
working
 and not-working case. 

	

System Info - 
 cs16ca101gn0303

Sockets : 2

Cores : 96

CPU's : 96

P0 frequency : 34

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww13.3]

When stepping through the PF curve, the core frequency limit drops from 2200 to 400 at the top of the curve, which is not expected. The team confirmed that IMH and pCode are issuing the correct limits, but the core is still limited to 400, suggesting a possible issue with Punits communication to A code or A code's consumption of those limits.

Next: James will collect and analyzing all WP data, including reading PMSB CR and taking IRA traces to observe actual WPs set by aCode. The team agreed to collect all WP data, not just WP4, and to coordinate with the platform team for further analysis.

﻿[26ww13.1]

James doesn't think Chen got the point of the issue, Tsur is help from aCode side from now.

[26ww12.4]
Data collection WIP and under debug and moving along

﻿[26ww12.3]

James, Jason, and Chen discussed the mechanism for communicating WP4 limits between pCode and aCode, with James explaining that aCode determines its own limits and does not require explicit grants from pCode, and agreed to collect and log relevant data for Chen's review

James explained that aCode determines its own WP4 limits and does not require permission or grants from pCode, as all necessary information is sent and aCode makes decisions independently.

James and Jason agreed to log all relevant data in aCode variables to address Chen's request and to provide a comprehensive explanation of the observed behavior.

﻿[26ww12.1]

Abhishek7 collected pCode tracker dumps, and the team analyzed logs to confirm that pCode receives and sets correct limits, shifting focus to aCode's handling of these limits and planning to snoop HBM messages for further insight.

Tsur was assigned to check with aCode experts regarding adherence to limits communicated by pCode, and the team discussed the need for aCode insight to resolve ceiling mismatches, with Anatoli and others reviewing logs for confirmation.

﻿[26ww11.3]

James reported that Abhishek verified the seeding limits sent by IMH matched those

### Description
When Prochot is injected, cores are throttling to their respective prochot freq when prochot_response_power is set to &quot;pcode_socket_virus_power_frequency_curve_power_point_0/1/2/3/4&quot;

But in case of &quot;pcode_socket_virus_power_frequency_curve_power_point_5&quot;, cores throttles to Pm (400) instead of respective prochot freq (3300). 

This table highlights the 
working
 and not-working case. 

	

System Info - 
 cs16ca101gn0303

Sockets : 2

Cores : 96

CPU's : 96

P0 frequency : 3400MHz

P1 frequency : 2100MHz

Pn frequency : 600MHz

Pm frequency : 400MHz

Turbo is enabled on system

[root@cs16ca101gs0303 turbostat]# dmidecode -s bios-version

OKSDCRB1.IPC.0031.D94.2601260626

[root@cs16ca101gs0303 turbostat]# rdmsr 0x8b

8000098c00000000

[root@cs16ca101gs0303 turbostat]#

Socket CBB IMH Cores CPU's  PKG_TDP PKG_MAX_PWR PKG_MIN_PWR RAPL_PL1 RAPL_PL2 DR

    0   1   2    48   48      350W     420W         0W        350W     420W

    1   1   2    48   48      350W     420W         0W        350W     420W

### Comments (latest)
++++1667327334 kumara7
<div><p>When Prochot is injected, cores are throttling to their respective prochot freq&nbsp;when prochot_response_power is set to &quot;pcode_socket_virus_power_frequency_curve_power_point_0/1/2/3/4&quot;</p><p>But in case of &quot;pcode_socket_virus_power_frequency_curve_power_point_5&quot;, cores throttles to Pm (400) instead of respective prochot freq (3300).&nbsp;</p><p><br /></p><p>This table highlights the<span style="background-color: rgb(255, 255, 255);">&nbsp;working</span>&nbsp;and not-working case.&nbsp;</p><p><br /></p><p><span style="white-space: pre;">	</span><img src="https://hsdes.intel.com/rest/binary/16029794849" tabindex="-1" data-processed="true" style="width: 710.156px; height: 465.013px;" /></p></div><div><span style="background-color: rgb(255, 255, 0);"><br /></span></div><div><span style="background-color: rgb(255, 255, 0);"><br /></span></div><div><span style="background-color: rgb(255, 255, 0);">Logs attached - </span></div><div><span style="background-color: rgb(255, 255, 255);">1. pcudata_dump_cs16ca101gn0303.zip</span></div><div>2.&nbsp;cs16ca101gn0303_experiment_data.txt</div><div><br /></div><div><br /></div><div><span style="background-color: rgb(255, 255, 0);">System Info - </span></div><div style="margin-left: 25px;">Sockets : 2</div><div style="margin-left: 25px;">Cores : 96</div><div style="margin-left: 25px;">CPU's : 96</div><div style="margin-left: 25px;">P0 frequency : 3400MHz</div><div style="margin-left: 25px;">P1 frequency : 2100MHz</div><div style="margin-left: 25px;">Pn frequency : 600MHz</div><div style="margin-left: 25px;">Pm frequency : 400MHz</div><div style="margin-left: 25px;">Turbo is enabled on system</div><div style="margin-left: 25px;"><br /></div><div style=""><div style=""><span style="font-family: &quot;Courier New&quot;;">Socket CBB IMH Cores CPU's&nbsp; PKG_TDP PKG_MAX_PWR PKG_MIN_PWR RAPL_PL1 RAPL_PL2 DR</span></div><div style=""><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; 0&nbsp; &nbsp;1&nbsp; &nbsp;2&nbsp; &nbsp; 48&nbsp; &nbsp;48&nbsp; &nbsp; &nbsp; 350W&nbsp; &nbsp; &nbsp;420W&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;0W&nbsp; &nbsp; &nbsp; &nbsp; 350W&nbsp; &nbsp; &nbsp;420W</span></div><div style=""><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; 1&nbsp; &nbsp;1&nbsp; &nbsp;2&nbsp; &nbsp; 48&nbsp; &nbsp;48&nbsp; &nbsp; &nbsp; 350W&nbsp; &nbsp; &nbsp;420W&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;0W&nbsp; &nbsp; &nbsp; &nbsp; 350W&nbsp; &nbsp; &nbsp;420W</span></div></div><div><br /></div><div><br /></div><div><span style="background-color: rgb(255, 255, 0);"><br /></span></div><div><span style="background-color: rgb(255, 255, 0);">Setting prochot response power = pcode_socket_virus_power_frequency_curve_power_point_5</span></div><div><br /></div><div style="margin-left: 25px;">In [74]: sv.sockets.imhs.fuses.punit.pcode_socket_virus_power_frequency_curve_power_point_5</div><div style="margin-left: 25px;">Out[74]:</div><div style="margin-

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: Turbo
- **Component Path**: fw.acode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbb0.compute0.showsearch`

## Timeline

- **Submitted**: 2026-03-03 18:12:27
- **Closed**: 2026-03-27 07:07:30
- **Days Open**: 23

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
