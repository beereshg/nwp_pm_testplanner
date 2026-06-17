# HSD 16029781449: [DMR][RACL] [xPEGA] Uncore frequencies are not throttling when TDC limit is set to minimum value = 1

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029781449](https://hsdes.intel.com/appstore/article-one/#/16029781449) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | salmanha |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 80% |
| **Sub-Feature** | Turbo | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Collaterals
:

X1:

AN004022BMH2013.amr.corp.intel.com

IFWI: OKSDREL1_86B_2026.02.3.01_0031.D19_80000987_0.704.0_1P0_NonIPClean_NoTrace_DebugSigned_VIS.bin

Workload: PTAT-> ./ptat -ct 5 -id

Summary

: 
The Issue is seen only With PEGA Method to request for Core  P1-P0

With Turbo enabled and high ratios requested using Pega.

When TDC=1, core ratios are coming down to minimum value of 400MHz but Uncore frequency(Both CBB and IMH) are not changing from its maximum value.

In [102]: sv.socket0.

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww08.4]

Salman described the observed behavior where uncore throttles with RAPL but not with RACL when TDC is set to one, and Alex explained that this is expected for RACL, while RAPL should be addressed separately.

The team agreed to close the current issue as expected behavior and to file a new HSD specifically for the RAPL scenario, with Erick and Alex providing technical insights into the override mechanisms.

﻿[26ww08.3]

Erick and Alex explained that PEGA overrides the frequency limits set by RACKLE and RAPL at the final calculation stage, which can prevent intended throttling in debug scenarios where TDC is set to minimum.

Timothy and Nilanjan reviewed the logic for resolving core and ring frequency limits, confirming that the CBB should apply the minimum of RAPL and RACL limits, and that the ring should follow a known slope and base relative to the core.

The team decided to invite Salman to the next meeting to clarify the intended test scenario and ensure all parties understand the override flow and debug hooks involved.

### Description
Collaterals
:

X1:

AN004022BMH2013.amr.corp.intel.com

IFWI: OKSDREL1_86B_2026.02.3.01_0031.D19_80000987_0.704.0_1P0_NonIPClean_NoTrace_DebugSigned_VIS.bin

Workload: PTAT-> ./ptat -ct 5 -id

Summary

: 
The Issue is seen only With PEGA Method to request for Core  P1-P0

With Turbo enabled and high ratios requested using Pega.

When TDC=1, core ratios are coming down to minimum value of 400MHz but Uncore frequency(Both CBB and IMH) are not changing from its maximum value.

In [102]: sv.socket0.imh0.pcudata.tdc_limit

Out[102]: 0x73

In [103]: 
sv.socket0.imh0.pcudata.tdc_limit=1

Time = 0.0, Instantaneous current =37.7,
 avg_core_ratio = 400.0, max_core_ratio = 400.0, min_core_ratio = 400.0,

cbb_uncore_ratio=2700,io_mesh_ratio=2100,mem_mesh_ratio=2100

Time = 0.16, Instantaneous current =37.56, avg_core_ratio = 400.0, max_core_ratio = 400.0, min_core_ratio = 400.0,cbb_uncore_ratio=2700,io_mesh_ratio=2100,mem_mesh_ratio=2100

Time = 0.3, Instantaneous current =37.73, avg_core_ratio = 400.0, max_core_ratio = 400.0, min_core_ratio = 400.0,cbb_uncore_ratio=2700,io_mesh_ratio=2100,mem_mesh_ratio=2100

Time = 0.45, Instantaneous current =37.87, avg_core_ratio = 400.0, max_core_ratio = 400.0, min_core_ratio = 400.0,cbb_uncore_ratio=2700,io_mesh_ratio=2100,mem_mesh_ratio=2100

Time = 0.59, Instantaneous current =37.55, avg_core_ratio = 400.0, max_core_ratio = 400.0, min_core_ratio = 400.0,cbb_uncore_ratio=2700,io_mesh_ratio=2100,mem_mesh_ratio=2100

Time = 0.73, Instantaneous current =37.9, avg_core_ratio = 400.0, max_core_ratio = 400.0, min_core_ratio = 400.0,cbb_uncore_ratio=2700,io_mesh_ratio=2100,mem_mesh_ratio=2100

Time = 0.87, Instantaneous current =37.73, avg_core_ratio = 400.0, max_core_ratio = 400.0, min_core_ratio = 400.0,cbb_uncore_ratio=2700,io_mesh_ratio=2100,mem_mesh_ratio=2100

Time = 1.02, Instantaneous current =37.55, avg_core_ratio = 400.0, max_core_ratio = 400.0, min_core_ratio = 400.0,cbb_uncore_ratio=2700,io_mesh_ratio=2100,mem_mesh_ratio=2100

Time 

### Comments (latest)
++++1667261418 salmanha
<ul type="disc" style="direction:ltr;unicode-bidi:embed;margin-top:0in;
 margin-bottom:0in">
 <li style="margin-top:0;margin-bottom:0;vertical-align:middle"><span style="font-family:Calibri;font-size:11.0pt">When pega is released CBB
     Uncore frequency is throttling to minimum value(800MHz), IO mesh throttles
     to 400MHz(minimum) when TDC=1.</span></li>
 <li style="margin-top:0;margin-bottom:0;vertical-align:middle"><span style="font-family:Calibri;font-size:11.0pt">MEM Mesh stays at
     800MHz(P1=Pm=800MHz) when TDC=1 or TDC=0x73(default)</span></li>
</ul><p><br /></p><p><span style="font-size: 11px;"><b>PEGA Released:</b></span></p><p><span style="font-size: 11px;">pega.release()</span></p><p><span style="font-size: 11px;"><b>TDC=0x73(Default)</b></span></p><p><img src="https://hsdes.intel.com/rest/binary/16029744759" style="width: 1307px;" tabindex="-1" /><span style="font-size: 11px;"><br /></span></p><p><span style="font-size: 11px;"><br /></span></p><p><span style="font-size: 11px;"><br /></span></p><p><span style="font-size: 11px;">TDC=1</span></p><p><img src="https://hsdes.intel.com/rest/binary/16029744760" style="width: 1270px;" tabindex="-1" /><span style="font-size: 11px;"><br /></span></p>

++++1667261419 sumanku2
&nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Ramirez Moreno, Carlos O</span>&nbsp;: Can you help with the debug for this issue. With PEGA method the Mesh Frequencies are not scaling up or down. However, with just Workload being in play, this issue is not seen and silicon/FW flow is as expected.<div><br /></div><div>&nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Kumar,Amit6</span>&nbsp;: We shall also add the data for RAPL testing for similar scenaraio, also do we have the observations similar to :&nbsp;<a href="https://hsdes.intel.com/appstore/article-one/#/article/16029649884" target="_blank" style="font-family: Roboto, Arial, sans-serif; background-color: rgb(255, 255, 255); font-size: 0.87em; font-weight: 400;" tabindex="-1">16029649884 - [DMR][RAPL][X1][X4]: Setting PPL1 to low limit doesn't throttle the iMH1 IO Uncore freq</a></div><!--StartFragment--><!--EndFragment-->

++++1667261420 salmanha
<p style="margin: 0in; font-family: Calibri; font-size: 11pt;">AN004022BMH2013.amr.corp.intel.com</p><p style="margin: 0in; font-family: Calibri; font-size: 11pt;">IFWI: OKSDREL1_86B_2026.02.3.01_0031.D19_80000987_0.704.0_1P0_NonIPClean_NoTrace_DebugSigned_VIS.bin</p><ul><li style="margin: 0in; font-family: Calibri; font-size: 11pt;">With various traffics we are still seeing that when pega is requesting max freq on CBB uncore , IMH IO mesh and IMH MEM mesh is getting stucked at P0, while cores are throttled to Pm when TDC=1 (minimum)</li><li style="margin: 0in; font-family: Calibri; font-size: 11pt;">With pega released all core and uncore freq on CBB and IMH throttles to Pm with all the workloads.</li></ul><p><br /></p><p style="margin:0in;fo

### Tags
FV_PM

### Conclusion
not_a_bug

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: Turbo
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.pcudata.tdc_limit`
- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.sst_pp_info_11.show`
- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.sst_pp_info_12.show`
- `sv.socket0.cbb0.base.tpmi.sst_pp_info_11.show`

## Timeline

- **Submitted**: 2026-02-04 20:52:18
- **Closed**: 2026-02-19 21:54:02
- **Days Open**: 15

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
