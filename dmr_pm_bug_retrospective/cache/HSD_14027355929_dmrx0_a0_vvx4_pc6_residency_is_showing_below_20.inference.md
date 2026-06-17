# HSD 14027355929: [DMR][X0 A0 VV][X4] PC6 residency is showing below 20%

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027355929](https://hsdes.intel.com/appstore/article-one/#/14027355929) |
| **Status** | root_caused.awaiting_fix |
| **Priority** | 3-medium |
| **Owner** | hmpicosm |
| **Component** | hw.power |
| **Defect Die** | ioe |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | C6 | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

IFWI:  OKSDCRB1.86B.0030.D63.2512181804

SVOS: dmr2544-bookworm-update036.3

configuration:
AcpiC2Enumeration =3,  PackageCState = 2,
MonitorMWait =1

system: SC00901159H0001

PC6 residency is showing below 20% , I have manually tested this on our debug system on latest IFWI and SVOS releases.

Failing testline:    
https://nga.laas.intel.com/#/dmr_fv/planning/testlines/d5e21d3d-1cb2-4033-9c2b-cf569a38c299

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww12.3]

Residency Decline and Experiments: Hector reported that PC6 residency has declined from 40-50% to around 20%, and that applying the L1 bypass patch increases residency to about 60%, though this is still below the 90% KPI target.

### Description
IFWI:  OKSDCRB1.86B.0030.D63.2512181804

SVOS: dmr2544-bookworm-update036.3

configuration:
AcpiC2Enumeration =3,  PackageCState = 2,
MonitorMWait =1

system: SC00901159H0001

PC6 residency is showing below 20% , I have manually tested this on our debug system on latest IFWI and SVOS releases.

Failing testline:    
https://nga.laas.intel.com/#/dmr_fv/planning/testlines/d5e21d3d-1cb2-4033-9c2b-cf569a38c299

### Comments (latest)
++++14615194583 shijup1
<p class="MsoNormal"><span style="font-size:11.0pt;mso-ascii-font-family:Aptos;
mso-ascii-theme-font:minor-latin;mso-hansi-font-family:Aptos;mso-hansi-theme-font:
minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-bidi-theme-font:minor-bidi">Below
is the output of idle script&nbsp;<o:p></o:p></span><span style="font-family: Aptos, sans-serif; font-size: 11pt;">that tracks all the PCH and QCH idle residencies</span></p>

<p class="MsoNormal"><br /></p>

<p class="MsoNormal"><span style="font-size:11.0pt;mso-ascii-font-family:Aptos;
mso-ascii-theme-font:minor-latin;mso-hansi-font-family:Aptos;mso-hansi-theme-font:
minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-bidi-theme-font:minor-bidi">In
[224]: id.measure_ch_pc6_residency()<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt;mso-ascii-font-family:Aptos;
mso-ascii-theme-font:minor-latin;mso-hansi-font-family:Aptos;mso-hansi-theme-font:
minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-bidi-theme-font:minor-bidi">PC6
residency socket0 imh0 0.3298458307785102<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt;mso-ascii-font-family:Aptos;
mso-ascii-theme-font:minor-latin;mso-hansi-font-family:Aptos;mso-hansi-theme-font:
minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-bidi-theme-font:minor-bidi">PC6
residency socket0 imh1 0.4916880369773024<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt;mso-ascii-font-family:Aptos;
mso-ascii-theme-font:minor-latin;mso-hansi-font-family:Aptos;mso-hansi-theme-font:
minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-bidi-theme-font:minor-bidi">************************************************<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt;mso-ascii-font-family:Aptos;
mso-ascii-theme-font:minor-latin;mso-hansi-font-family:Aptos;mso-hansi-theme-font:
minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-bidi-theme-font:minor-bidi">Printing
PCH pc6 residencies<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt;mso-ascii-font-family:Aptos;
mso-ascii-theme-font:minor-latin;mso-hansi-font-family:Aptos;mso-hansi-theme-font:
minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-bidi-theme-font:minor-bidi">************************************************<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt;mso-ascii-font-family:Aptos;
mso-ascii-theme-font:minor-latin;mso-hansi-font-family:Aptos;mso-hansi-theme-font:
minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-bidi-theme-font:minor-bidi">&nbsp;</span></p>

<p class="MsoNormal"><span style="font-size:11.0pt;mso-ascii-font-family:Aptos;
mso-ascii-theme-font:minor-latin;mso-hansi-font-family:Aptos;mso-hansi-theme-font:
minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-bidi-theme-font:minor-bidi">('socket0',
'imh0', 'rc_mio_ew') PCH 0 pc

### Tags
FV_PM,SysDebugDccbDone,SysDebugDccbDriver

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

- **Primary Feature**: Core C-States
- **Sub-Feature**: C6
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imhs.d2d_stack.d2d_stacks.uxis.ula_link_ctrl.l1_enable`

## Timeline

- **Submitted**: 2026-03-11 22:25:26
- **Root Caused**: 2026-03-28 02:46:03
- **Days Open**: 71

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
