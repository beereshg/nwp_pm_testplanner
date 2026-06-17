# HSD 14025889998: [DMR][X1 A0 PO][PEGA] PrimeCode not clearing PEGA Pstate override in DVFS ratios.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025889998](https://hsdes.intel.com/appstore/article-one/#/14025889998) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | egomezgo |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | PState Stack | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Sending PEGA Pstate to IO Mesh:

Command 1 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_data = 0x1

Command 1 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_interface = 0x8000000000000024

Command 2 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_data = 0xa

Command 2 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_interface = 0x8000000000000026

Command 0 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_data = 0xa0000000

Command 0 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_interf

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25WW38.3]
Issue: Pega Command Release Issue in PST Control DBFS
Hector explained that the spec states sending a Pega command with no bits set should release the previous command, but this is not happening unless the module master bit is set.  Vidar will root cause to PrimeCode.

### Description
Sending PEGA Pstate to IO Mesh:

Command 1 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_data = 0x1

Command 1 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_interface = 0x8000000000000024

Command 2 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_data = 0xa

Command 2 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_interface = 0x8000000000000026

Command 0 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_data = 0xa0000000

Command 0 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_interface = 0x8000000000000022

Command 1 socket0.imh1.punit.ptpcfsms.ptpcfsms.aux_mailbox_data = 0x1

Command 1 socket0.imh1.punit.ptpcfsms.ptpcfsms.aux_mailbox_interface = 0x8000000000000024

Command 2 socket0.imh1.punit.ptpcfsms.ptpcfsms.aux_mailbox_data = 0xa

Command 2 socket0.imh1.punit.ptpcfsms.ptpcfsms.aux_mailbox_interface = 0x8000000000000026

Command 0 socket0.imh1.punit.ptpcfsms.ptpcfsms.aux_mailbox_data = 0xa0000000

Command 0 socket0.imh1.punit.ptpcfsms.ptpcfsms.aux_mailbox_interface = 0x8000000000000022

UFS_STATUS.CURRENT_RATIO

sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status.current_ratio

0xa 

PCUDATA

sv.socket0.imhs.pcudata.dietopo_instance.CFC_0.pega_pstate_override

socket0.imh0.pcudata.dietopo_instance.CFC_0.pega_pstate_override - 
0x0000000a

socket0.imh1.pcudata.dietopo_instance.CFC_0.pega_pstate_override - 
0x0000000a

Sending command to clear PEGA Pstate Override:

Command 1 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_data = 0x0

Command 1 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_interface = 0x8000000000000024

Command 2 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_data = 0x0

Command 2 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_interface = 0x8000000000000026

Command 0 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_data = 0xa0000000

Command 0 socket0.imh0.punit.ptpcfsms.ptpcfsms.aux_mailbox_interface 0x8000000000000022

Command 1 socket0.imh1.punit.ptpcfsms.ptpcfsms.aux_mailbox_data = 0x0

Command 1 socket0.imh1.punit.ptpcfs

### Comments (latest)
++++14614607622 egomezgo
<div class="BIZfh" style="border: 0px; font: inherit; margin: 0px; padding: 0px; vertical-align: baseline; color: inherit; opacity: 1; transition: opacity 0.3s; visibility: visible;"><div visibility="hidden" style="border: 0px; font: inherit; margin: 0px; padding: 0px; vertical-align: baseline; color: inherit;"><div class="rps_a763" style="border: 0px; font: inherit; margin: 0px; padding: 0px; vertical-align: baseline; color: inherit;"><div dir="ltr" style="border: 0px; font: inherit; margin: 0px; padding: 0px; vertical-align: baseline; color: inherit;"><div class="x_elementToProof" style="border: 0px; font-style: inherit; font-variant: inherit; font-weight: inherit; font-stretch: inherit; font-size: 11pt; line-height: inherit; font-family: Aptos, Aptos_EmbeddedFont, Aptos_MSFontService, Calibri, Helvetica, sans-serif; font-optical-sizing: inherit; font-size-adjust: inherit; font-kerning: inherit; font-feature-settings: inherit; font-variation-settings: inherit; margin: 0px; padding: 0px; vertical-align: baseline; color: rgb(0, 0, 0);"><!--StartFragment--><div style="font-family: Calibri, Arial, Helvetica, sans-serif; font-size: 12pt;"><b>From:</b>&nbsp;DeHaemer, Eric J &lt;eric.j.dehaemer@intel.com&gt;<br /><b>Sent:</b>&nbsp;Thursday, September 4, 2025 2:19 PM<br /><b>To:</b>&nbsp;Upadhyay, Shreyas &lt;shreyas.upadhyay@intel.com&gt;<br /><b>Cc:</b>&nbsp;Grabacki, Alex &lt;alex.grabacki@intel.com&gt;; Gomez Guerrero, Emiliano &lt;emiliano.gomez.guerrero@intel.com&gt;<br /><b>Subject:</b>&nbsp;Re: Power On Pega Command Behavior Clarification
</div><div style="font-family: Calibri, Arial, Helvetica, sans-serif; font-size: 12pt;"><br /></div><div style="direction: ltr; font-size: 11pt;">Each PEGA command is independent. If you exclude a module from the mask, then it should remove its PEGA override. Otherwise there is no way to remove a override for a module.</div><div style="direction: ltr; font-size: 11pt;">So by setting module_mask = 0, you remove the override from all modules.</div><div style="direction: ltr; font-size: 11pt;"><br /></div><div style="direction: ltr; font-size: 11pt;">--Eric</div><div style="direction: ltr; font-size: 11pt;"><br /></div><div style="direction: ltr;"><br /></div><div style="direction: ltr; font-family: Calibri, Arial, Helvetica, sans-serif; font-size: 12pt;"><br /></div><hr style="direction: ltr; display: inline-block; width: 98%;" /><div style="direction: ltr; font-family: Calibri, Arial, Helvetica, sans-serif; font-size: 12pt;"><b>From:</b>&nbsp;Upadhyay, Shreyas &lt;shreyas.upadhyay@intel.com&gt;<br /><b>Sent:</b>&nbsp;Thursday, September 4, 2025 2:52 PM<br /><b>To:</b>&nbsp;DeHaemer, Eric J &lt;eric.j.dehaemer@intel.com&gt;<br /><b>Cc:</b>&nbsp;Grabacki, Alex &lt;alex.grabacki@intel.com&gt;; Gomez Guerrero, Emiliano &lt;emiliano.gomez.guerrero@intel.com&gt;<br /><b>Subject:</b>&nbsp;Power On Pega Command Behavior Clarification</div><div style="direction: ltr; font-family: Calibri, Arial,

### Tags
SysDebugCloned,SysDebugDccbBypass,TEMP_WA_PATCH_DMR_AP1_A0_60000974_POWERON,FWTF_PO_UNBLOCKED,FV_PM,FIX_PATCH_DMR_AP1_A0_6000097B,FIX_IFWI_DMR_AP1_2025.45.4.02,FIX_BKC_OKS_DMR_AP1_2025WW46,cov.pm.pega, PSF=Y

### Conclusion
fw.bug

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
- **Sub-Feature**: general
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status.current_ratio`
- `sv.socket0.imhs.pcudata.dietopo_instance.CFC_0.pega_pstate_override`

## Timeline

- **Submitted**: 2025-09-10 11:24:22
- **Root Caused**: 2025-09-18 22:07:32
- **Closed**: 2025-11-26 01:49:21
- **Days Open**: 76

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
