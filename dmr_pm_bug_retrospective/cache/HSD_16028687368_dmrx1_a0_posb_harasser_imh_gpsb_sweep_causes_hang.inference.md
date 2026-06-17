# HSD 16028687368: [DMR][X1 A0 PO][SB Harasser] IMH GPSB Sweep causes Hang with MCA_GPSB_Timeout Reported for *D2D* EP

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16028687368](https://hsdes.intel.com/appstore/article-one/#/16028687368) |
| **Status** | rejected.not_a_defect |
| **Priority** | 2-high |
| **Owner** | salmanha |
| **Component** | hw.uncore |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Sideband/D2D | 80% |
| **Sub-Feature** | GPSB | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Collaterals
:

Platform: SC00901159H0033.amr.corp.intel.com

IFWI: OKSDCRB1_86B_2025.37.2.01_2733.D04_60000965_0.598.0_1P0_NonIPClean_Trace_DebugSigned_MonitorMwaitEnable.bin

Summary
:

Observing 
FATAL
 error with 
GPSB_TIMEOUT
 while sweeping all pcode EP_PORTS on IMH.

Hitting issue at EP- 
gpio_d2d_iosf_gpsb
, Port-
399

Tried reproducing it with  

DfxRstCplBitsEn=0x3
 (without PM Flows) and still seeing FATAL error at same port.

after bypassing 
 (gpio_d2d_iosf_gpsb, Port-399) and runnin

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww47.1]

This is a timeout issue on a D2D endpoint when using a tool to generate PMSB and GPSB traffic, with Joseph's comment indicating that non-posted transactions to a tunneling endpoint returned invalid SAI, causing a fatal error.

Daniel clarified that the tunneling endpoint was not mapped in the virtual port ID table, resulting in a dummy completion with invalid SAI, which the Punit hardware dropped, leading to a timeout reported by Primecode.

Nilanjan and Suman questioned why the completion was dropped and discussed the implications for real-world scenarios, with consensus that while the current implementation matches the specification, there may be a gap if Primecode cannot observe the response, warranting further offline discussion.

[25ww46.3]

Issue Summary and Root Cause: Daniel summarized that the GPSB timeout occurs due to sending to a tunneling endpoint without using a virtual port ID, resulting in a remapping table miss and a dummy completion without SAI, which Punit then drops.

Vijeta confirmed Daniel's diagnosis, explaining that only specific sideband flows are enabled for D2D crossing, and the observed behavior aligns with the design.

Daniel proposed disabling SAI checking in the Punit to confirm that the issue does not occur, planning to coordinate with Salman for test.

[25ww44.3]

Ido requested a full trace of CR accesses on silicon, specifically comparing accesses on different D2D instances to determine if the same payload is used and to rule out tool or SoC issues. 
Suman acknowledged the request and agreed to collect apples-to-apples traces for both failing and non-failing endpoints. 
Suman explained the challenges in collecting traces due to iOSF bus contention but committed to working with the debug tool team to obtain the necessary data. 
Suman will set up a focused follow-up meeting to discuss findings and create a BKM for similar issues.

[25ww44.1]

Salman provided detailed steps to the pre-silicon team for reproducing the issue 

### Description
Collaterals
:

Platform: SC00901159H0033.amr.corp.intel.com

IFWI: OKSDCRB1_86B_2025.37.2.01_2733.D04_60000965_0.598.0_1P0_NonIPClean_Trace_DebugSigned_MonitorMwaitEnable.bin

Summary
:

Observing 
FATAL
 error with 
GPSB_TIMEOUT
 while sweeping all pcode EP_PORTS on IMH.

Hitting issue at EP- 
gpio_d2d_iosf_gpsb
, Port-
399

Tried reproducing it with  

DfxRstCplBitsEn=0x3
 (without PM Flows) and still seeing FATAL error at same port.

after bypassing 
 (gpio_d2d_iosf_gpsb, Port-399) and running test again we are observing hang at following Eps:

EP-
gpio_s5_iosf_gpsb
,Port-
398
.

EP-
hamvf_iosfsbep
,       Port-
350

Steps to Reproduce:

import diamondrapids.pm.SB_Harasser.sb_harasser_DMR as hr

hr.run_harasser_loop(interval = 10, t_time = 900, die_id=[8], pcode=1, ocode=0)

(Additional details for SB Harasser execution: https://wiki.ith.intel.com/spaces/fvcommon/pages/4296573600/SideBand+Harassers)

EP- 
gpio_d2d_iosf_gpsb
, Port-
399

EP-
gpio_s5_iosf_gpsb
,Port-
398
.

EP-
hamvf_iosfsbep
, Port-
350

### Comments (latest)
++++1667007085 jzlevule
When the failure is completely unknown, the submitter's domain must be used when filing sub_forum as a starting point.&nbsp; Please start doing this automatically when filing a Pre-Sighting.

++++1667007086 salmanha
<p class="MsoNormal">Platform - JF53NOR09BN0304.amr.corp.intel.com<o:p></o:p></p>

<p class="MsoNormal"><o:p>&nbsp;</o:p></p>

<p class="MsoNormal"><b><u><span style="font-size:14.0pt">SB-Harasser</span></u></b><span style="font-size:11.0pt">:<o:p></o:p></span></p>

<p class="MsoNormal" style="margin-left:.25in"><span style="font-size:11.0pt">Collaterals:<o:p></o:p></span></p>

<p class="MsoNormal" style="margin-left:.75in;text-indent:-.25in;mso-list:l2 level1 lfo1;
tab-stops:list .5in"><!--[if !supportLists]--><span style="font-size:10.0pt;
mso-bidi-font-size:11.0pt;font-family:Symbol;mso-fareast-font-family:Symbol;
mso-bidi-font-family:Symbol">&middot;<span style="font-variant-numeric: normal; font-variant-east-asian: normal; font-variant-alternates: normal; font-size-adjust: none; font-kerning: auto; font-optical-sizing: auto; font-feature-settings: normal; font-variation-settings: normal; font-variant-position: normal; font-variant-emoji: normal; font-stretch: normal; font-size: 7pt; line-height: normal; font-family: &quot;Times New Roman&quot;;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
</span></span><!--[endif]--><span style="font-size:11.0pt">IFWI:&nbsp;&nbsp;OKSDCRB1_86B_2025.38.2.01_2754.D05_60000967_0.606.0_1P0_NonIPClean_Trace_DebugSigned_MonitorMwaitEnable.bin<o:p></o:p></span></p>

<p class="MsoNormal" style="margin-left:.25in"><span style="font-size:11.0pt">&nbsp;</span></p>

<p class="MsoNormal" style="margin-left:.25in"><span style="font-size:11.0pt">Summary:<o:p></o:p></span></p>

<ul style="margin-top:0in" type="disc">
 <li class="MsoListParagraph" style="margin-left:.25in;mso-list:l1 level1 lfo3"><span style="font-size:11.0pt;mso-fareast-font-family:&quot;Times New Roman&quot;">Tried
     to run SB-Harasser with latest portid collateral file(</span><span style="font-size:11.0pt"><a href="https://intel.sharepoint.com/:x:/r/sites/DiamondRapids/IMH_SOC_Spec/Shared%20Documents/SoC%20Spec%20Latest%20Version/soc_spec/topology/die/global_ids/SbPortIdProvider.csv"><!--[if gte vml 1]><v:shapetype
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
      <v:path o:extrusionok="f" gradientshap

### Tags
DMR_A0_PO,FV_PM_BDC,FV_PM,FV_SB_HARASSER,dmr_neg

### Conclusion
not_a_bug

### Component
hw.uncore

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

- **Primary Feature**: Sideband/D2D
- **Sub-Feature**: GPSB
- **Component Path**: hw.uncore

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.pcudata.timeoutsEnabled`

## Timeline

- **Submitted**: 2025-09-23 22:58:09
- **Closed**: 2025-11-17 21:37:13
- **Days Open**: 54

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
