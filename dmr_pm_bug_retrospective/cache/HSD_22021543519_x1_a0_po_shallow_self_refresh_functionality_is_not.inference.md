# HSD 22021543519: [X1 A0 PO] Shallow Self Refresh functionality is not disabled even when BIOS knob is set to Disabled

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22021543519](https://hsdes.intel.com/appstore/article-one/#/22021543519) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | hmpicosm |
| **Component** | bios |
| **Defect Die** | compute |
| **Conclusion** | bios.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **BIOS** | 70% |
| **Feature** | Core C-States | 45% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_IFWI/FIX_BIOS → BIOS

## Root Cause Summary

Summary:

========

In DMR PO, during Shallow
Self Refresh enabling, we noticed that Primecode is setting enable_auto_idle
bits to enabled MC PChannels even when Shallow Self Refresh = Disabled in BIOS
knob.

Impact:

========

Shallow Self Refresh feature cannot be disabled by customers

Details:

========

REPLACE  with failure and triage details.

==> System configuration ...

12-ch and 16-ch SKUs X1 DMR AP, both unfused and fused parts

==> BIOS/Patch/IFWI/BKC/CI Versions ...

==> Reproducib

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25WW38.3]
Issue: BIOS Shallow Self Refresh Disablement Not Working
We discussed an issue where disabling Shallow Self Refresh via a BIOS knob does not work due to a missing B2P implementation, agreed to confirm the BIOS ticket and coordinate with the BIOS team for resolution.

### Description
Summary:

========

In DMR PO, during Shallow
Self Refresh enabling, we noticed that Primecode is setting enable_auto_idle
bits to enabled MC PChannels even when Shallow Self Refresh = Disabled in BIOS
knob.

Impact:

========

Shallow Self Refresh feature cannot be disabled by customers

Details:

========

REPLACE  with failure and triage details.

==> System configuration ...

12-ch and 16-ch SKUs X1 DMR AP, both unfused and fused parts

==> BIOS/Patch/IFWI/BKC/CI Versions ...

==> Reproducibility ...

==> Lightswitch discoveries ...

==> Experiment results ...

Please review 
http://goto/dmrtriage

   for Debug Triage suggestions and Guidance

Please review 
http://goto/dmrsubmit
 for Sighting submission guidelines and expectations.

### Comments (latest)
++++22611451426 hmpicosm
<p class="MsoNormal"><span style="font-size:11.0pt">&nbsp;</span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">In DMR PO, during Shallow
Self Refresh enabling, we noticed that Primecode is setting enable_auto_idle
bits to enabled MC PChannels even when Shallow Self Refresh = Disabled in BIOS
knob.<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">&nbsp;</span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">There is a server.bugco for
adding B2P functionality for controlling this, however I don’t see any BIOS
tickets attached to it or find the BIOS version where this is implemented. One
note, we had tried before Simics version from ww28 (2025ww28.1.00_46) and
confirmed SSR BIOS knob enable/disable was working back then, so this seems to
be a regression?? &nbsp;<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt"><a href="https://hsdes.intel.com/appstore/article-one/#/14024721750">https://hsdes.intel.com/appstore/article-one/#/14024721750</a><o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt"><a href="https://hsdes.intel.com/appstore/article-one/#/14024884946">https://hsdes.intel.com/appstore/article-one/#/14024884946</a><o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">&nbsp;</span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">We are going to capture BIOS
logs (system was taken from us for other urgent tasks), but could you please
help us check the BIOS version where this B2P server.bugeco was implemented?<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">&nbsp;</span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">/Hector<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">&nbsp;</span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">&nbsp;</span></p>

<p class="MsoNormal"><span style="font-size:11.0pt"><!--[if gte vml 1]><v:shapetype
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
 alt="" style='width:442.5pt;height:540.75pt'>
 <v:imagedata src="file:///C:/Users/hmpicosm/AppData/Local/Temp/msohtmlclip1/01/clip_image001.png"
  o:href="cid:image001.png@01DC19DB.46B56EE0"/>
</v:shape><![endif]--><!--[if !vml

### Tags
BIOS_MS_POWER_ON,SysDebugCloned,SysDebugDccbBypass,BIOS_RCR.14025870967,FIX_BIOS_OAKSTRM.0.RPB.0027.D.88,FV_PM,FIX_IFWI_DMR_AP1_2025.43.5.01,FIX_BKC_OKS_DMR_AP1_2025WW44

### Conclusion
bios.bug

### Component
bios

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
- **Sub-Feature**: general
- **Component Path**: bios

## Firmware Touchpoints

### BIOS
- `BIOS knob`
- `BIOS
knob`

## Timeline

- **Submitted**: 2025-09-04 11:23:03
- **Root Caused**: 2025-09-19 21:08:22
- **Closed**: 2025-10-02 01:33:25
- **Days Open**: 27

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
