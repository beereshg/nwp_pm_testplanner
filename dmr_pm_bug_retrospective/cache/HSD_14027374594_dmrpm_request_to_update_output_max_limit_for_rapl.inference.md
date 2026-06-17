# HSD 14027374594: [DMR][PM] Request to update output_max_limit for RAPL NNPIDs for DMR

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027374594](https://hsdes.intel.com/appstore/article-one/#/14027374594) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | sdeshpan |
| **Component** | hw.power |
| **Defect Die** | ioe |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Power/RAPL | 80% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

The configured output range for the output frequency for the PID controllers (NNPID) is 0-255. As values above 35 (corresponding to 3.5GHz) have no control impact, the control response is slower than expected. 

PL2 response while running ssmd virus workload on DMR shows no convergence to the power limit (540W) [Power averaged over PL2 time window of 11ms, sampling interval for the plot is 1ms]

Tested a patch on the same DMR system by configuring the min and max limits as following:

sv.sockets

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww13.3]

Timothy expressed concern that adding an output max limit block to NNPID could slow response and introduce side effects, preferring to tune internal parameters rather than add external limiters. Anna clarified that the intent is to ensure the NN controller operates within the actual hardware range and offered to review data offline.

Anna agreed to update the HSD and HAS with the latest data and recommendations, and to coordinate with Timothy to ensure alignment on the solution before finalizing changes.

[26ww13.1]

Alex and David discussed the status of related bugs, noting ongoing discussions in the NMPID work group and the involvement of multiple team members in data collection and analysis.

Vidar will follow up with the owner directly.

[26ww12.4]

* ARCH conversation in progress - is the NNPID efficient enough to need to care about?

    ==> There may be an NNPID Working Group discussing this.

* Debug patch provided with a change to see if that improves  the performance

Next Steps:

* Val test our debug patch and provide results back to Primecode

* PM arch/Primecode driving/discussing the need for this change (debug patch data probable dependency)

﻿[26ww12.1]

This is fairly new HSD. The owner didn't specify what values they want us to update to. Will sync with them once they come back.

### Description
The configured output range for the output frequency for the PID controllers (NNPID) is 0-255. As values above 35 (corresponding to 3.5GHz) have no control impact, the control response is slower than expected. 

PL2 response while running ssmd virus workload on DMR shows no convergence to the power limit (540W) [Power averaged over PL2 time window of 11ms, sampling interval for the plot is 1ms]

Tested a patch on the same DMR system by configuring the min and max limits as following:

sv.sockets.imhs.pcudata.psys_pl2_pid_controllers_0.output_max_limit
= 0x420C0000

sv.sockets.imhs.pcudata.psys_pl2_pid_controllers_1.output_max_limit
= 0x420C0000

sv.sockets.imhs.pcudata.pkg_pl2_pid_controllers_0.output_max_limit
= 0x420C0000

sv.sockets.imhs.pcudata.pkg_pl2_pid_controllers_1.output_max_limit
= 0x420C0000

sv.sockets.imhs.pcudata.psys_pl1_pid_controllers_0.output_max_limit
= 0x420C0000

sv.sockets.imhs.pcudata.psys_pl1_pid_controllers_1.output_max_limit
= 0x420C0000

sv.sockets.imhs.pcudata.pkg_pl1_pid_controllers_0.output_max_limit
= 0x420C0000

sv.sockets.imhs.pcudata.pkg_pl1_pid_controllers_1.output_max_limit
= 0x420C0000

sv.sockets.imhs.pcudata.fast_rapl_inst.pid_controller.output_max_limit
= 0x420C0000

 

 

sv.sockets.imhs.pcudata.psys_pl2_pid_controllers_0.output_min_limit
= 0x3F800000

sv.sockets.imhs.pcudata.psys_pl2_pid_controllers_1.output_min_limit
= 0x3F800000

sv.sockets.imhs.pcudata.pkg_pl2_pid_controllers_0.output_min_limit
= 0x3F800000

sv.sockets.imhs.pcudata.pkg_pl2_pid_controllers_1.output_min_limit
= 0x3F800000

sv.sockets.imhs.pcudata.psys_pl1_pid_controllers_0.output_min_limit
= 0x3F800000

sv.sockets.imhs.pcudata.psys_pl1_pid_controllers_1.output_min_limit
= 0x3F800000

sv.sockets.imhs.pcudata.pkg_pl1_pid_controllers_0.output_min_limit
= 0x3F800000

sv.sockets.imhs.pcudata.pkg_pl1_pid_controllers_1.output_min_limit
= 0x3F800000

sv.sockets.imhs.pcudata.fast_rapl_inst.pid_controller.output_min_limit
= 0x3F800000

This shows improved PL2 respon

### Comments (latest)
++++14615209273 parekhsa
Hi &nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Deshpande, Sahil</span>&nbsp;,<br />What are the values you need the min and max limited to be updated to ? Do you want them to be set as min -&nbsp;<span style="font-family: Calibri; font-size: 14.6667px;">0x3F800000 and max -&nbsp;</span><span style="font-family: Calibri; font-size: 14.6667px;">0x420C0000 as per your tests ?&nbsp;</span>

++++14615209275 vwang
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 22022185804.

++++14615209285 vwang
[CloneScript] PreSighting 22022185804 cloned to Sighting 14027374594

++++14615215187 sdeshpan
The configured output range is 0-255 for all of the above listed PID controllers. The proposal is for these values to be reset to 1 and 35 for min and max respectively for now.  This shows clear improvement in PL2 response as documented above. This change should also be applied to other pid controllers where output is core frequency, as conceptually, the potential output values need to match realistic core frequency values. Otherwise, these values will be ignored, slowing the control response.  Thanks. 

++++14615218554 parekhsa
Debug Ifwi can be found - \\amr.corp.intel.com\ec\proj\debug\DMR\User\parekhsa\ww11_3_nnpid_trace_on_994\OKSDCRB1_86B_2026.10.4.01_0032.D91_80000994_0.770.0_1P0_NonIPClean_Trace_DebugSigned_VIS_C0581A0B_202603140026.bin Baseline - 994 pcudata xmls can be found in the same location
++++22611817106 mbfausto
 @Wang, Vidar  - what was the result of the follo-wup?  @Lwu, David  - What are the results of the Debug patch Sagar provided last week?

++++22611817424 sdeshpan
Hi  @Fausto, Matthew B,  I have tested the debug patch and it helps improve the behavior similar to as seen in the graphs above. We are still finalizing the actual limits, but it is evident that reducing them from the current 0-255 limits is helping improve PL2 response.  Thanks.
++++14615257535 vwang 
David is not the correct owner of this sighting. I have already talked with  @Deshpande, Sahil this morning and was told the test patch works good with the values.  but they are waiting Arch to finalize the the max and min limit values and update HAS.
++++22611818274 bquerbac 
To be clear, this 0-255 is an pid range configuration input parameter to nnpid. It is a static configuration parameter. We have reviewed test results for both 0-255 and recommended more realistic value of 4-42 in the NNPID weekly sync meetings, which resulted in faster nnpid response. The architecture recommendation is to only configure the nnpid with realistic range that the pid can actually drive the system under control to (eg core_ratio specific DMR sku, from 400Mhz to 3.5 Ghz or 4 to 35). This realistic range can be read from FUSE values for the individual sku (eg: P0max to Pm).   HAS will be updated this week to reflect the realistic range needed for nnpid configuration.
++++14615267208 bqu

### Tags
val_agent,SysDebugCloned,SysDebugCloned_RCBypass,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_6000099D,FIX_IFWI_DMR_AP1_2026.16.3.01,BKC#OKS_DMR_AP_X1_2026WW18,FIX_BKC_OKS_DMR_AP1_2026WW18

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

## Timeline

- **Submitted**: 2026-03-13 00:49:32
- **Root Caused**: 2026-03-27 23:10:50
- **Closed**: 2026-05-14 23:46:10
- **Days Open**: 62

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
