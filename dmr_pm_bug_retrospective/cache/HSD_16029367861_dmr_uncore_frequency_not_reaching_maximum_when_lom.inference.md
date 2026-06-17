# HSD 16029367861: [DMR] Uncore frequency not reaching maximum when LoM is enabled

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029367861](https://hsdes.intel.com/appstore/article-one/#/16029367861) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | sagrawa3 |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Power/RAPL | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Problem Statement:

Uncore Frequency is not reaching to maximum when LoM is enabled.

Expectation:

1. LOM is designed for maximum performance. It operates core and fabric frequencies at their peak within the Running Average Power Limit(RAPL) budget.

2. BIOS controls and locks EPB to Perf (0) and sets ELC Low & High & Thresholds := 0%.

Actual Behaviour:

- The fabric frequencies are 

not 

operating at peak.

- The resolved EPB is 

not 

locked at performance.

- ELC High and low thresholds 

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww3.3]

Next step is to wait for architectural/implementation pcode commit, email thread in place, waiting on pcode side, AR sysdebug to poke pcode team for commitement 

[26ww03.1]

Timothy highlighted the need for confirmation from pCode regarding their ability to implement changes differently, noting that if the HPM message is not fixed, pCode would need to adjust their coding for the ELC high feature.

[26ww02.3]

Primecode and Architecture teams updated ELC implementation to be more precise and primecode team delivered this new implementation patch to platform team to do the appropriate testing. Let's wait the test result. There is also a recommendation to test this patch for the following sighting 14026508259 as both fall into the ELC feature there could be positive impact. 

[26ww02.1]

Detection Logic Revision: The team has identified that the current method for detecting RAPL limited conditions could yield false positives or negatives. Shreyas recommended altering the pseudo code in the HAS to use a more accurate method, specifically checking if the HPM message bit frequency exceeds the maximum of the reverse line, to avoid misdetection. Timothy confirmed that the necessary command in the fourth paragraph of the HAS is correct and committed to double-checking and updating the HAS once back in the office. Shreyas and Brian are informed of the required changes, and the implementation will proceed once the HAS is updated. Vidar suggested creating a test patch for the new logic, and Alex agreed to coordinate with Shreyas the coming test patch.

[25ww51.3]

Need to know why IMH1 (second IMH) is still being set, issue is not with LOM or ELC, something on primecode is still setting up IMH1 limit. Timothy suggests to cross check with Shrihari, as they already saw a similar issue, following up, Abhinad already sync'd, Shrihari opened a new sighting as the original issue is not solved. Next step, Shreyas and Abhinad will continue with live debug trying to find why

### Description
Problem Statement:

Uncore Frequency is not reaching to maximum when LoM is enabled.

Expectation:

1. LOM is designed for maximum performance. It operates core and fabric frequencies at their peak within the Running Average Power Limit(RAPL) budget.

2. BIOS controls and locks EPB to Perf (0) and sets ELC Low & High & Thresholds := 0%.

Actual Behaviour:

- The fabric frequencies are 

not 

operating at peak.

- The resolved EPB is 

not 

locked at performance.

- ELC High and low thresholds are

 

0%.

Below is the screenshot which tells the uncore frequency when the Latency Optimized Mode is enabled, resolved EPB(which is not 0) and UFS control register details.

### Comments (latest)
++++1667159282 sagrawa3
<p>Checked on CWF and GNR systems:<br /><br />When Latency optimized mode is enabled in CWF, the uncore frequency was at its peak.</p><p><br />Screenshot from CWF:</p><p><br /></p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/16029221050" style="width: 1221px; height: 282.135px;" data-processed="true" /></p><p><br /></p><p><br /></p><p>Data from GNR:</p><p><img src="https://hsdes.intel.com/rest/binary/16029221051" style="width: 501px;" /><br /></p>

++++1667159283 ankitrat
Shubham to update - <br />When Lom Disabled : Is ufs control register changing?&nbsp;<br />Change EPB to perf with Lom enabled and update the uncore freq. results.<br /><br />

++++1667159284 sagrawa3
<p>Changing the EPB to 0(Perf), Even then the uncore frequency doesnot peak.</p><p><br /></p><p><br /></p><p><br /></p><p><br /></p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/16029269679" style="width: 1805px;" />&nbsp;</p><p><img src="https://hsdes.intel.com/rest/binary/16029269698" style="width: 882px;" /><br /></p>

++++1667159285 sagrawa3
<p class="MsoNormal"><span style="font-size:10.0pt;line-height:115%">When LOM is
enabled:<o:p></o:p></span></p><p class="MsoNormal"><span style="font-size:10.0pt;line-height:115%">&nbsp;</span></p><p class="MsoNormal"><span style="font-size:10.0pt;line-height:115%">-&nbsp;<b>In
Idle scenario:</b><o:p></o:p></span></p><p class="MsoNormal"><span style="font-size:10.0pt;line-height:115%">CBB Uncore
is at 2700(max) but IMH Uncore(IO and Mem) is operating at min(400)<o:p></o:p></span></p><p class="MsoNormal"><span style="font-size:10.0pt;line-height:115%"><br /></span></p><p class="MsoNormal"><span style="font-size:10.0pt;line-height:115%">-&nbsp;<b>Running
Workload:</b>&nbsp;stress-ng --cpu 2 --iomix 8 -vm 4 --vm-bytes 128M --fork 4<o:p></o:p></span></p><p class="MsoNormal"><span style="font-size:10.0pt;line-height:115%">CBB
uncore&nbsp; operates at 2700(max) and IMH Uncore(IO and Mem) operating varies from 400-1800, with heavy IPC workload.<o:p></o:p></span></p><p class="MsoNormal"><span style="font-size:10.0pt;line-height:115%">No change in
IMH Uncore when LOM is enabled and disabled.&nbsp;<o:p></o:p></span></p><p class="MsoNormal"><span style="font-size:10.0pt;line-height:115%"><br /></span></p><p class="MsoNormal"><span style="font-size:10.0pt;line-height:115%">-
Checked&nbsp;<b>resolved EPB</b>&nbsp;: -&nbsp;0x1<o:p></o:p></span></p><p class="MsoNormal"><span style="font-size:10.0pt;line-height:115%">Checked the
resolved EPB via (socket0.imh0.pcudata.resolved_socket_epb - 0x1), It was 0x1, </span></p><p class="MsoNormal"><span style="font-size:10.0pt;line-height:115%">Changed
the<b> EPB to Performance(from both BIOS and OS)</b>, but no change</span></p><p class="MsoNormal"><span style="font-size:10.0pt;line-height:115%"><br /></span></p><p class="MsoNormal"><span style="font-size:10.0pt;line-height:115%"><br /></span></p><p class="MsoNormal"><span style="font-size:10.0pt;line-height:

### Tags
SysDebugCloned,SysDebugCloned_RCBypass,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_60000994,FIX_PATCH_DMR_AP1_A0_60000994,FIX_IFWI_DMR_AP1_2026.10.4.01,BKC#OKS_DMR_AP_X1_2026WW12,FIX_BKC_OKS_DMR_AP1_2026WW12

### Conclusion
fw.arch

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

- `TPMI but`
- `TPMI interface`

## Timeline

- **Submitted**: 2025-12-04 20:42:51
- **Root Caused**: 2026-02-02 12:26:24
- **Closed**: 2026-04-01 06:33:11
- **Days Open**: 117

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
