# HSD 14026867149: [DMR][X1 A0 VV][HWP][VVblkr_S] Not possible to updated IA32_HWP_REQUEST.EPP_VALID MSR bits

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026867149](https://hsdes.intel.com/appstore/article-one/#/14026867149) |
| **Status** | rejected.not_a_defect |
| **Priority** | 2-high |
| **Owner** | egomezgo |
| **Component** | hw.fuse.xml |
| **Defect Die** | base |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 52% |
| **Sub-Feature** | HWP | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Valid bits are not able to be written:

Trying to set all 5 valid bits (0xF8)

EPP_VALID bit is not updated

CPUID.06.EAX[17]
	
Thread HWP request valid bits is equal to 0

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww08.4]

Emiliano will be OOO, probably Carlos will be covering for him, need to catch up with him

﻿[26ww07.1]

Fuse Value Analysis: Emiliano and Ido examined the  IA32_HWP_REQUEST.EPP_VALID MSR bits and their relationship to package control, with Emiliano referencing legacy HAS and pseudo code to explain the override mechanism.

Ido requested Emiliano to provide additional background and documentation to clarify how the fuse is related to package control, and to compare default values between DMR and GNR platforms.

Ido asked Emiliano to experimentally change the fuse value and confirm whether the package request is honored, to close the loop on the investigation.

Ido reminded Emiliano to consider other inputs to the core calculation and ensure all relevant conditions are checked when analyzing the override behavior.

[26ww05.4]

AR Emiliano will contact Justin to ask for some debug guidance on this. 

[26ww04.3]

Current theory is that ucode is not allowing this bits to be written. Vidar will add uCode/SLD contacts. This bits were not used in previous platforms, this is the first server generation that uses this valid bits.

### Description
Valid bits are not able to be written:

Trying to set all 5 valid bits (0xF8)

EPP_VALID bit is not updated

CPUID.06.EAX[17]
	
Thread HWP request valid bits is equal to 0

### Comments (latest)
++++14614978696 egomezgo
<p>Seems that neither of the valid bits can be written:</p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/14026810015" style="width: 435px;" tabindex="-1" /><br /><br />Also tried using pythonSV but also didn't worked:<br /></p><p><img src="https://hsdes.intel.com/rest/binary/14026810016" style="width: 593px;" tabindex="-1" /><br /><br /></p>

++++14614978697 egomezgo
<p>In LNL HAS is mentioned:<a href="https://docs.intel.com/documents/pm_doc/src/LNL/HAS/HWP/HWP.html#ia32_hwp_request-0x774" target="_blank" tabindex="-1" style="background-color: rgb(255, 255, 255); font-family: Roboto, Arial, sans-serif; font-weight: 400;"><br class="Apple-interchange-newline" />https://docs.intel.com/documents/pm_doc/src/LNL/HAS/HWP/HWP.html#ia32_hwp_request-0x774</a>&nbsp;</p><p><!--EndFragment--><br /><img src="https://hsdes.intel.com/rest/binary/14026810025" style="width: 1031px;" tabindex="-1" /></p><p><br /></p><p><br />On DMR HAS is mentioned on pseudocode of resolution of each related field:</p><p><a href="https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCP%20HAS/cbb_cpp_has.html#hwp-request-core-pma-resolution---pseudo-code" target="_blank" tabindex="-1">https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCP%20HAS/cbb_cpp_has.html#hwp-request-core-pma-resolution---pseudo-code</a><br /><span style="font-size: 12.18px;">&nbsp;</span><br /><img src="https://hsdes.intel.com/rest/binary/14026810026" style="width: 1683px;" tabindex="-1" /><br /></p>

++++14614978698 egomezgo
<p>From arch feedback valid bits are still in use in DMR:</p><p><br /></p><div style="font-family: Calibri, Arial, Helvetica, sans-serif; font-size: 12pt;"><b>From:</b>&nbsp;Melamed, Ido &lt;ido.melamed@intel.com&gt;<br /><b>Sent:</b>&nbsp;Tuesday, January 13, 2026 5:31 PM<br /><b>To:</b>&nbsp;Gomez Guerrero, Emiliano &lt;emiliano.gomez.guerrero@intel.com&gt;<br /><b>Subject:</b>&nbsp;RE: HWP Request Valid Bits
</div><div style="font-family: Calibri, Arial, Helvetica, sans-serif; font-size: 12pt;"><br /></div><p style="margin: 0in; font-family: Aptos, sans-serif; font-size: 12pt;"><span style="font-family: Calibri, sans-serif; font-size: 11pt; color: rgb(112, 48, 160);">Hi Emiliano,</span></p><p style="margin: 0in; font-family: Aptos, sans-serif; font-size: 12pt;"><span style="font-family: Calibri, sans-serif; font-size: 11pt; color: rgb(112, 48, 160);">Apologies for the delayed response.</span></p><p style="margin: 0in; font-family: Aptos, sans-serif; font-size: 12pt;"><span style="font-family: Calibri, sans-serif; font-size: 11pt; color: rgb(112, 48, 160);">HWP is fully supported in DMR. Could you please check the HWP status on your system by reading CPUID leaf 0x6?</span></p><p style="margin: 0in; font-family: Aptos, sans-serif; font-size: 12pt;"><span style="font-family: Calibri, sans-serif; font-size: 11pt; color: rgb(112, 48, 160);">Thank you,</span></p><p style="margin: 0in; font-family: Aptos, sans-serif;

### Tags
FV_PM

### Conclusion
not_a_bug

### Component
hw.fuse.xml

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
- **Sub-Feature**: HWP
- **Component Path**: hw.fuse.xml

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cpu.module0.core0.fscp_cr_misc_flags_0.ia_32_pm_hwp_enable_sticky`
- `sv.socket0.cpu.module0.core0.fscp_cr_core_config_0.data_0_21`

## Timeline

- **Submitted**: 2026-01-20 00:27:56
- **Closed**: 2026-03-02 23:45:33
- **Days Open**: 41

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
