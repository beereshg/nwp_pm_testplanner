# HSD 22022439190: [DMR][PkgC6][D2D L1] D2D MCA ULA Run_Entry_Timeout hit during OS idle with PC6 enabled

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22022439190](https://hsdes.intel.com/appstore/article-one/#/22022439190) |
| **Status** | open.clone |
| **Priority** | 2-high |
| **Owner** | hmpicosm |
| **Component** | hw.d2d |
| **Defect Die** | ioe |
| **Conclusion** |  |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Core C-States | 75% |
| **Sub-Feature** | C6 | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

Summary:

========

Hitting iMH Punit MCA when letting system in OS idle with PC6 enabled. 

Reproduced in 1S X4 system. Issue happens after some hours.

In [16]: server_ip_debug.punit.errors.show_mca_status(source=&quot;reg&quot;)

|skt|die_id|inst|inst_name         |mscod               |mcacod|error type|overflow|error_source|description                                                                   |error_specific_info                                                                        

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww21.3]

Elena reported reaching out to the ULA team for assistance in understanding training times and default values, as the team is hitting timeouts and needs guidance on tuning or identifying underlying causes.

Hector explained that applying a debug patch to disable ITD from CFC mem during pkgC flow prevented both the FIVR timeout and another related issue(14027538694) from occurring, suggesting a correlation between the two.

﻿[26ww21.1]

WA is working in 2 stations. Elena analyzed scan dumps and is following
up with UCIe design on findings and next steps.

﻿[26ww20.3]

Hector explained that while traces can be started with IMH target, using SOC target (IMH + CBB) results in PkgC blockage after trace initiation, with ULAs, GPSB timeouts, and non-failed ULAs reported by Primecode, preventing PkgC entry.

The issue was reproduced by Jim in multiple systems; Joe had a meeting to analyze the trace, Hector was unable to attend, and Sarah was mentioned as checking the issue.

Robert suggested increasing the run entry timeout to FFFF, which prevented the issue in one system, but this is only a WA and the root cause remains unknown; further testing and discussion with Robert are planned.

﻿[26ww20.1]

Elena and Hector discussed increasing the run entry timeout value as recommended by Robert, with Hector confirming that maxing out the timeout prevented the issue from occurring during debugging, and Elena explaining the calculation based on clock ticks.

Hector integrated the timeout adjustment into the testing recipe, noting that the issue was previously easy to reproduce but now is avoided, and observed that the problem can now be reproduced in VIS as well as power-on systems.

Hector confirmed that status scope and scan dumps have been collected for the issue, and Elena indicated the need to review these dumps for further insights before drawing conclusions.

﻿[26ww19.3]

Issue: During long OS idle with PC6 enabled and D2D L1 enabled, the system eventually hits a

### Description
Summary:

========

Hitting iMH Punit MCA when letting system in OS idle with PC6 enabled. 

Reproduced in 1S X4 system. Issue happens after some hours.

In [16]: server_ip_debug.punit.errors.show_mca_status(source=&quot;reg&quot;)

|skt|die_id|inst|inst_name         |mscod               |mcacod|error type|overflow|error_source|description                                                                   |error_specific_info                                                                                                                                               |next_steps                                                                      |

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

|0  |0     |0   |socket0.imh0.punit|Shutdown suppression|1036  |          |        |Ucode       |                                                                              |{'error_code': 'MCE when MCIP bit is set'}                                                                                                                        |Error signaled by the core and logged in Punit. Check the core for more details.|

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

|0  |1     |0   |socket0.imh1.punit|AGG                 |1026  |Fatal     |    

### Comments (latest)
++++22611882661 hmpicosm
<p>Captured VISA trace and scandata:</p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/22022411005" style="width: 1658px;" tabindex="-1" /><br /></p>

++++22611882662 jsbrooks
<p>Punit/RC MCA are secondary.&nbsp; This is the failure. D2D must not respond to the PCh request when link gets into this state.</p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/22022414923" style="width: 50%;" tabindex="-1" data-processed="true" /><br /></p>

++++22611882663 hmpicosm
<p>Same issue reproduced in another system&nbsp;<span style="background-color: rgb(20, 20, 20); color: rgba(255, 255, 255, 0.85); font-family: Consolas, monospace;">jf53nor09bn0303&nbsp;</span>running CentOS idle after ~3hrs.</p><p><br /></p><p>Status scope shows the same issue Joe mentioned before:</p><p><img src="https://hsdes.intel.com/rest/binary/22022439178" style="width: 1454.4px;" tabindex="-1" /><br /></p><p><br /></p><table><tbody><tr><td>In [7]: from pysvtools import server_ip_debug</td></tr><tr><td>...: server_ip_debug.punit.errors.show_mca_status(source=&quot;reg&quot;)</td></tr><tr><td>====================================================================================================================================================================================================================================================================================================================================================================================================================================</td></tr><tr><td>|skt|die_id|inst|inst_name&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;|mscod&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;|mcacod|error type|overflow|error_source|description&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; |error_specific_info&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;
 &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; |next_steps&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;|</td></tr><tr><td>----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### Tags
FV_PM

### Component
hw.d2d

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
- **Component Path**: hw.d2d

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-05-04 09:10:42
- **Days Open**: 17

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
