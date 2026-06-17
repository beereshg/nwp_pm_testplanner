# HSD 14026569727: [X1 A0 VV-1] [CBB][VV] valid temperatures reported by punit from disabled modules

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026569727](https://hsdes.intel.com/appstore/article-one/#/14026569727) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | jamesrow |
| **Component** | fw.acode |
| **Defect Die** | compute |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Tools | 90% |
| **Sub-Feature** | debug_tools | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

PLATFORM: 

SC00901159H0033

IFWI:  OKSDCRB1.86B.0029.D50.2511162333

debug log of below snippets: 
debug log

expectation:

https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html#disabled-dts

 

https://hsdes.intel.com/appstore/article-one/#/article/13010612929

 

email chain clarifying dts core disable expectations: 
dts core disable WW25

if a module is disable via lp_enable and module disable mask then expect dtsenable/ovrd to be enab

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww51.3]

New acode change has been released on NVL, Vidar requested to get a DMR patch and he pasted it on the comments, need testing from FV team to verify the patch works or check if it needs changes

[25ww50.1]

HAS specification is correct. When
both cores are disabled, Acode is supposed to close the DTSs as well. 

However, due to hardware bugs,
this disabling did not occur. 

This issue has been identified in NVL and it impacts DMR, this sighting was created with the intention of tracking the implementation from NVL into DMR, Ido has more details on the issue. AR sysdebug to assess priority.

### Description
PLATFORM: 

SC00901159H0033

IFWI:  OKSDCRB1.86B.0029.D50.2511162333

debug log of below snippets: 
debug log

expectation:

https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html#disabled-dts

 

https://hsdes.intel.com/appstore/article-one/#/article/13010612929

 

email chain clarifying dts core disable expectations: 
dts core disable WW25

if a module is disable via lp_enable and module disable mask then expect dtsenable/ovrd to be enabled and set to zero

    and assume then that punit does not show the modules temp telemtry as valid and on pma side mask off all diodes for that module/core that is disabled

observation:

all dtsenables/ovrd are zero for both modules with lp_enable of 0x3 and 0x0

min and max temps reported by punit are valid from disabled modules

first 14 diodes are not valid for each core for both en/disabled cores even though dts mask is 0x7ff, seems to be backwards as well

all dtsenables/ovrd are zero for both modules with lp_enable of 0x3 and 0x0:

pmas lps examples:

In [68]: sv.socket0.cbb0.computes.pmas.pmsb.lp_enable

Out[68]:

socket0.cbb0.compute0.pma0.pmsb.lp_enable - 0x00000003

socket0.cbb0.compute0.pma1.pmsb.lp_enable - 0x00000003

socket0.cbb0.compute0.pma2.pmsb.lp_enable - 0x00000000

socket0.cbb0.compute0.pma3.pmsb.lp_enable - 0x00000003

...

number of populated modules:

len(sv.socket0.cbb0.computes.modules)

0x10

example of ovrds and enables are same for bopth enabled and disbled modules:

In [83]: sv.socket0.cbb0.computes.pmas.pmsb.showsearch(&quot;dtsenable&quot;,&quot;p&quot;)

dfvfcr_dts_fuse_0.dfvfreg5_inst.dtsenableovrd = 0x0

dfvfcr_dts_fuse_0.dfvfreg5_inst.dtsenable = 0x0

dfvfcr_dts_fuse_1.dfvfreg5_inst.dtsenableovrd = 0x0

dfvfcr_dts_fuse_1.dfvfreg5_inst.dtsenable = 0x0

dfvfcr_dts_fuse_0.dfvfreg5_inst.dtsenableovrd = 0x0

dfvfcr_dts_fuse_0.dfvfreg5_inst.dtsenable = 0x0

dfvfcr_dts_fuse_1.dfvfreg5_inst.dtsenableovrd = 0x0

dfvfcr_dts_fuse_1.dfvfreg5_inst.dt

### Comments (latest)
++++14614873398 hmpicosm
<p class="MsoNormal"><span style="font-size:11.0pt;mso-ascii-font-family:Aptos;
mso-ascii-theme-font:minor-latin;mso-hansi-font-family:Aptos;mso-hansi-theme-font:
minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-bidi-theme-font:minor-bidi"><o:p>&nbsp;</o:p></span></p>

<p class="MsoNormal"><a name="_MailEndCompose" target="_blank"><span style="font-size:11.0pt;
mso-ascii-font-family:Aptos;mso-ascii-theme-font:minor-latin;mso-hansi-font-family:
Aptos;mso-hansi-theme-font:minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;
mso-bidi-theme-font:minor-bidi"><o:p>&nbsp;</o:p></span></a></p>



<p class="MsoNormal"><a name="_MailOriginal" target="_blank"><b><span style="font-size:11.0pt;
font-family:&quot;Calibri&quot;,sans-serif;mso-fareast-font-family:&quot;Times New Roman&quot;;
mso-ligatures:none">From:</span></b></a><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif;mso-fareast-font-family:
&quot;Times New Roman&quot;;mso-ligatures:none"> Picos Morgan, Hector M <br />
<b>Sent:</b> Thursday, December 4, 2025 11:43 AM<br />
<b>To:</b> Rowe, James &lt;James.Rowe@intel.com&gt;; Mattapalli, Jaivardhan
&lt;Jaivardhan.Mattapalli@intel.com&gt;; Melamed, Ido
&lt;ido.melamed@intel.com&gt;<br />
<b>Cc:</b> Ramirez Moreno, Carlos O &lt;carlos.o.ramirez.moreno@intel.com&gt;<br />
<b>Subject:</b> RE: Valid Temps from disabled modules<o:p></o:p></span></p>

<p class="MsoNormal"><o:p>&nbsp;</o:p></p>

<p class="MsoNormal"><span style="font-size:11.0pt">Adding </span><a id="OWAAMAD861D7081B940878333D0389663536B" href="mailto:ido.melamed@intel.com" target="_blank"><span style="font-size: 11pt; font-family: Aptos, sans-serif;">@Melamed, Ido</span></a><span style="font-size:11.0pt"><o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt"><o:p>&nbsp;</o:p></span></p>

<p class="MsoNormal"><b><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif;mso-ligatures:none">From:</span></b><span style="font-size:11.0pt;font-family:
&quot;Calibri&quot;,sans-serif;mso-ligatures:none"> Rowe, James &lt;</span><a href="mailto:james.rowe@intel.com" target="_blank"><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif;mso-ligatures:none">james.rowe@intel.com</span></a><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif;mso-ligatures:none">&gt;
<br />
<b>Sent:</b> Thursday, December 4, 2025 11:41 AM<br />
<b>To:</b> Mattapalli, Jaivardhan &lt;</span><a href="mailto:jaivardhan.mattapalli@intel.com" target="_blank"><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif;mso-ligatures:none">jaivardhan.mattapalli@intel.com</span></a><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif;mso-ligatures:none">&gt;<br />
<b>Cc:</b> Ramirez Moreno, Carlos O &lt;</span><a href="mailto:carlos.o.ramirez.moreno@intel.com" target="_blank"><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif;mso-lig

### Tags
FV_PM,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_60000987,FIX_IFWI_DMR_AP1_2026.02.3.01,BKC#OKS_DMR_AP_X1_2026WW04,FIX_BKC_OKS_DMR_AP1_2026WW04

### Conclusion
fw.bug

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

- **Primary Feature**: Tools
- **Sub-Feature**: debug_tools
- **Component Path**: fw.acode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbb0.computes.pmas.pmsb.lp_enable`
- `sv.socket0.cbb0.computes.modules`
- `sv.socket0.cbb0.computes.pmas.pmsb.showsearch`
- `sv.socket0.cbb0.compute3.pma31.pmsb.dfvfcr_dts_fuse_0.dfvfreg72_inst.active_diode_mask_32`

## Timeline

- **Submitted**: 2025-12-06 04:39:36
- **Root Caused**: 2026-01-01 00:04:00
- **Closed**: 2026-01-29 19:42:04
- **Days Open**: 54

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
