# HSD 22021682591: Package THERMTRIP# Bi-Directional Design introduce the external noise to internal, result in False THERMTRIP - THERMTRIP# as Output Only

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22021682591](https://hsdes.intel.com/appstore/article-one/#/22021682591) |
| **Status** | root_caused.awaiting_fix |
| **Priority** | 2-high |
| **Owner** | tiangeng |
| **Component** | hw.gpio |
| **Defect Die** | ioe |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 75% |
| **Feature** | SoC Thermal | 45% |
| **Sub-Feature** | general | — |

**Reasoning**: errata_status='review_waived' → HW

## Root Cause Summary

We need the DMR to modify the package level THERMTRIP# from the current Bi-directional to the OD output only. We have customer False THERMTRIP issue on EGS due to this bi-directional design. Some noise on the platform will let the local socket die think it is the THERMALTRIP from Remote socket dies. Then, it will start to re-drive the local socket THERMTRIP pin to solid LOW. It will let the Platform CPLD think it is real Thermtrip situation and shutdown the system. And it is hard to debug when i

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww43.1]

This is a customer(

xFusion

) issue on SPR/EMR where a bug in the customer board and inject noise in THERMTRIP package pin and caused platform shutdowns.

The team discussed that the bidirectional design of THERMTRIP package pin allows platform noise to trigger CPU shutdowns, and that GNR's output-only design avoids this problem. The recommendation is to make the DMR THERMTRIP signal output-only at the SOC level. the recommendation now is to ground the RX bit to zero.

Jaivardhan and Satish clarified that platform logic is responsible for shutting down other sockets within 500 milliseconds, and that the sockets are isolated by CPLD, making the bidirectional design unnecessary and potentially problematic.

GPIO Configuration and Implementation: The group agreed that the change should be captured as a GPIO definition update, with Linda as the GPIO owner, and discussed whether the change should be implemented at the GPIO or controller level.

ARs: Satish and Jaivardhan agreed to summarize the recommendation and next steps, including which product stepping the change should apply to, and to coordinate with the GPIO team for implementation.

### Description
We need the DMR to modify the package level THERMTRIP# from the current Bi-directional to the OD output only. We have customer False THERMTRIP issue on EGS due to this bi-directional design. Some noise on the platform will let the local socket die think it is the THERMALTRIP from Remote socket dies. Then, it will start to re-drive the local socket THERMTRIP pin to solid LOW. It will let the Platform CPLD think it is real Thermtrip situation and shutdown the system. And it is hard to debug when in EGS. And we can hardly tell if it is external noise or silicon die problem.

 

Since we heard the DMR also did the Bi-directional design, will need to let the DMR design team aware and make the changes (keep the internal dies connection as bi-directional, but change the package level to external as OD output only) ASAP if possible.

1.  why SPR & EMR THERMTRIP# pin behave is different with GNR? EDS define as Open drain output, but SPR & EMR behaves as In/out; GNR behaves as output only

2. how to configure SPR pin as OPEN Drain output only?

 
We can see that THERMTRIP# behavior 
is different between SPR/EMR & GNR
.
 

 

 

SPR & EMR

GNR

EDS package pin definition 

#613206: 
open drain output

#635356: 
open drain output

Pull down CPU0_THERMTRIP_N signal to GND on RP by pulse experiment :
 1) remove CPU0_THERMTRIP_N to CPLD to avoid CPLD turn off power; 
 2) Pull down CPU0_THERMTRIP_N signal to GND on RP by pulse

 

CPU 0 will drive CPU0_THERMTRIP_N signal Low; CPU behaves 'real' THERMTRIP# happened; 

 Blue: CPU0_THERMTRIP_N; 
 Purple: CPU0_THERMTRIP_N pull up power rail
 

 

 

CPU0 internal will not been impacted by the external signal. CPU_THERMTRIP_N will back to high if we release the force to GND;
 System has no any impact.

### Comments (latest)
++++22611522442 sys_voc
Routing rules applied: Company match:<br />
server_platf_ae.bug.customer_company=xfusion<br />
family='Eagle Stream Platforms'<br />
server_platf_ae.bug.suspected_problem_area='*'<br />
server_platf_ae.bug.cpu='*'<br />
server_platf_ae.bug.customer_project_name='*'<br />
<br />To change rules create a new article from https://hsdes.intel.com/appstore/article/#/1407520027<br />Routing rules last modified Tue Sep 10 11:44:32 2024 (PST)<br /><br />PAE issue expectations https://voice.intel.com/static/docs/issues/expectations.html

++++22611522439 wangmin3
<div>0093:&nbsp;</div><div>&nbsp; &nbsp;<img src="https://hsdes.intel.com/rest/binary/15016770352" data-filename="image.png" style="width: 1404px;" /></div><div>0040:</div><div><img src="https://hsdes.intel.com/rest/binary/15016770357" data-filename="image.png" style="width: 1398px;" /></div><div>0051:</div><div><img src="https://hsdes.intel.com/rest/binary/15016770358" data-filename="image.png" style="width: 1405px;" /><br /></div>

++++22611522441 fmtool
<span style="color:blue;font-size:14px;"> CCE Weekly Sysdebug Review ww38: </span> <br /><span> Any question, please contact CCE debug owner: jie.j.yan@intel.com </span> <br /><table border="2" cellpadding="6"><tbody><tr> <td>Review Notes</td> <td>CE Owner</td> <td>Action</td> <td>Due date</td> <td>Tag</td> </tr>  <tr>  <td style="word-break:" break-all;="">ww38: multiple systems from fleet reporting themtrip in BMC SEL; the actual temp was not high according to the customer; it could be either CPU defect or system design problem such as CPLD, etc.   </td>  <td>nan</td><td><p>1. reproduce with the retired CPUs</p> <p>2. Get the themtrip signal routing from xFustion</p> <p>3. if the thermtrip signal is routed through CPLD to BMC, noise might be generated there, xFustion can try to examine their CPLD logic and the circuits, see if there's potential risk there</p></td><td>ww38</td><td>nan</td></tr>  </tbody></table>

++++22611522440 kamanna
<p>Adding details that I sent over email&nbsp;</p><p>I reviewed all the MOW articles and sent them via email to Kevin Zhoung</p><p><br /></p><p><br /></p>

++++22611522447 kamanna
<p>adding <span><span style="font-weight: bold; color: #007BFF;">@Schaefer, Dave</span><span style="color: #000000;">&nbsp;</span></span><span><span style="font-weight: bold; color: #007BFF;"></span></span></p><p><span><span style="color: #000000;"><br /></span></span></p><p><span><span style="color: #000000;">Summary of the issue:</span></span></p><p class="MsoNormal" style="text-indent:9.0pt"><span style="font-size:11.0pt">Customer
design is 2S design.</span></p><p class="MsoNormal" style="margin-left:.5in"><span style="font-size:11.0pt">System
unexpected shutdown due to CPU1 thermal trip asserted, BMC does not record
other failure. CPU: 8468V; Failure rate: 6 of 5000+</span></p><p class="MsoNormal" style="text-indent:9.0pt"><span style="font-size:11.0pt">Issue
Triage:</span></p><p>









</p><ol style="marg

### Tags
SysDebugCloned,SysDebugDccbDone,SysDebugDccbDriver, PSF=Y

### Conclusion
hw.arch

### Component
hw.gpio

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
- **Sub-Feature**: general
- **Component Path**: hw.gpio

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x425`

## Timeline

- **Submitted**: 2025-10-15 22:37:05
- **Root Caused**: 2025-10-23 22:00:33
- **Days Open**: 218

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
