# HSD 14027824962: [DMR] [A0][X1][PM][SST] SST-CP proportional throttling drops priority core 0 to 400 MHz under power injection instead of holding max frequency

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027824962](https://hsdes.intel.com/appstore/article-one/#/14027824962) |
| **Status** | open.assigned |
| **Priority** | 3-medium |
| **Owner** | xni6 |
| **Component** | fw.primecode |
| **Defect Die** | base |
| **Conclusion** |  |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | SST | 75% |
| **Sub-Feature** | SST-CP | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

1

Environment details

Platform

 

IFWI Version

 0P8_29.D.85_Pre359

CPU

 

PCH

 

BMC version

 

Memory Configuration

 

BKC Version

 

OS version

 

SPS/CSME FW

 

NVM driver

 

2

Test case details

CTC ID

 

Test ID

 15014966158

Requirement ID

 

Test Design ID

 

3

No. Of test cases Impacted

 

4

Logs & Screenshot attached

Y/N

 

Simics Package details:

simlauncher run dmr-rio-7 
2025ww47.6.00_04

--cores 16 --memory 500 --disk 1000 --path 
pre359
 --mode vnc

IFWI:

 

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww21.1]

SSTCP Enablement and Handler Registration manual enabling does not fully activate the feature due to handler registration gaps, and agreed to continue debugging and consult with architects.

Sagar explained that enabling SSTCP manually in PythonSV does not trigger the handler, resulting in incomplete feature activation and missing steps in the flow.

The team clarified that the TPMI handler registration for SST-CP is handled differently from other flows, and that double registration could cause issues, emphasizing the need for correct handler setup.

Power Injection and Throttling Behavior Analysis: the effects of power injection on core frequency throttling, clarifying test procedures and the expected behavior when power limits are artificially constrained.

Test Setup and Power Injection: The team reviewed the steps for injecting current to simulate high power consumption, using specific commands and telemetry settings to enable throttling and observe frequency changes.

Expected Throttling Behavior: Leonardo explained that when power is limited, both low and high priority cores will eventually be throttled to 400 MHz, and James confirmed that similar experiments are being conducted to validate this behavior.

Next: Sagar will consult with architects to identify any remaining gaps, and Leonardo offered to join the discussion and review the test setup for further insights. Also the meaning of power injection values and ask other team members to ensure accurate test execution and data collection.

﻿[26ww20.3]

This a new issue, Sagar has provided an initial response, requested additional logs, and is awaiting further information; the issue is considered a work in progress with ongoing updates.

### Description
1

Environment details

Platform

 

IFWI Version

 0P8_29.D.85_Pre359

CPU

 

PCH

 

BMC version

 

Memory Configuration

 

BKC Version

 

OS version

 

SPS/CSME FW

 

NVM driver

 

2

Test case details

CTC ID

 

Test ID

 15014966158

Requirement ID

 

Test Design ID

 

3

No. Of test cases Impacted

 

4

Logs & Screenshot attached

Y/N

 

Simics Package details:

simlauncher run dmr-rio-7 
2025ww47.6.00_04

--cores 16 --memory 500 --disk 1000 --path 
pre359
 --mode vnc

IFWI:

 

  
Normal

  
0

  

  

  

  

  
false

  
false

  
false

  

  
EN-US

  
X-NONE

  
X-NONE

  

   

   

   

   

   

   

   

   

   

  

  
MicrosoftInternetExplorer4

  

   

   

   

   

   

   

   

   

   

   

   

  

 

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

 

### Comments (latest)
++++14615406688 sd1x
<p>Hi &nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Andrew, MerinX Anna</span>&nbsp;,</p><p><br /></p><p>Could you please attached the logs &amp; Scripts</p>

++++14615406690 sd1x
<p class="MsoNormal"><b><span style="font-size:11.0pt">Debug Update:<o:p></o:p></span></b></p>

<p class="MsoNormal"><b><span style="font-size:11.0pt">&nbsp;</span></b></p>

<p class="MsoNormal"><span style="font-size:11.0pt">Tried to reproduce the issue
with latest config ( IMH2_Pre425+32D14), <b>Issue is reproducing.<o:p></o:p></b></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">Expected is Core 1 value should
be decreased &amp; actual is Core 0 &amp; Core 1 are same value.<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">Please find below
observations and attached logs.<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">&nbsp;</span></p>

<p class="MsoNormal"><span style="font-size:11.0pt;mso-no-proof:yes"><!--[if gte vml 1]><v:shapetype
 id="_x0000_t75" coordsize="21600,21600" o:spt="75" o:preferrelative="t"
 path="m@4@5l@4@11@9@11@9@5xe" filled="f" stroked="f">
 <v:stroke joinstyle="miter"/>
 <v:formulas>
  <v:f eqn="if lineDrawn pixelLineWidth 0"/>
  <v:f eqn="sum @0 1 0"/>
  <v:f eqn="sum 0 0 @1"/>
  <v:f eqn="prod @2 1 2"/>
  <v:f eqn="prod @3 21600 pixelWidth"/>
  <v:f eqn="prod @3 21600 pixelHeight"/>
  <v:f eqn="sum @0 0 1"/>
  <v:f eqn="prod @6 1 2"/>
  <v:f eqn="prod @7 21600 pixelWidth"/>
  <v:f eqn="sum @8 21600 0"/>
  <v:f eqn="prod @7 21600 pixelHeight"/>
  <v:f eqn="sum @10 21600 0"/>
 </v:formulas>
 <v:path o:extrusionok="f" gradientshapeok="t" o:connecttype="rect"/>
 <o:lock v:ext="edit" aspectratio="t"/>
</v:shapetype><v:shape id="Picture_x0020_1" o:spid="_x0000_i1025" type="#_x0000_t75"
 style='width:100.5pt;height:119pt;visibility:visible;mso-wrap-style:square'>
 <v:imagedata src="file:///C:/Users/sd1x/AppData/Local/Temp/msohtmlclip1/01/clip_image001.png"
  o:title=""/>
</v:shape><![endif]--><!--[if !vml]--><img width="134" height="159" src="https://hsdes.intel.com/rest/binary/16029811322" v:shapes="Picture_x0020_1" tabindex="-1" /><!--[endif]--></span><span style="font-size:11.0pt"><o:p></o:p></span></p>

<p class="MsoNormal"><o:p>&nbsp;</o:p></p>

++++14615406694 xni6
<p id="isPasted" style="margin: 0in 0in 8pt; font-family: Calibri, sans-serif; font-size: 11pt;"><span style="font-weight: bolder;"><span style="font-size: 15px;">@p k, vinithx raj</span></span></p><p id="isPasted" style="margin: 0in 0in 8pt; font-family: Calibri, sans-serif; font-size: 11pt;"><span style="font-weight: bolder;"><span style="font-size: 15px;"><br /></span></span></p><p id="isPasted" style="margin: 0in 0in 8pt; font-family: Calibri, sans-serif; font-size: 11pt;"><span style="font-weight: bolder;"><span style="font-size: 15px;">can you check below steps in current test environment?</span></span></p><p id="isPasted" style="margin: 0in 0in 8pt; font-family

### Tags
val_agent

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

- **Primary Feature**: SST
- **Sub-Feature**: SST-CP
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI handler`
- `TPMI has`
- `TPMI mailbox`
- `TPMI register`
- `TPMI writes`
- `TPMI write`

## Timeline

- **Submitted**: 2026-05-09 07:54:46
- **Days Open**: 12

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
