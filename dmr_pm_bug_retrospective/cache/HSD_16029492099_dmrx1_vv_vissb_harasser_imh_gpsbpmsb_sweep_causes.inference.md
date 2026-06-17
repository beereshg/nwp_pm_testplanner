# HSD 16029492099: [DMR][X1 VV VIS][SB Harasser] IMH GPSB/PMSB Sweep causes Hang with PRIMECODE posted transactions.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029492099](https://hsdes.intel.com/appstore/article-one/#/16029492099) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | salmanha |
| **Component** | hw.uncore |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Sideband/D2D | 80% |
| **Sub-Feature** | GPSB | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

Collaterals
:

Platform: 

AN004022BMH2291.amr.corp.intel.com

IFWI: 

OKSDCRB1.86B.0030.D43.2512102234

Summary
:

Able to reproduce this issue on 2 platforms.

While running SB Harasser with Primecode on IMH EPs we are seeing Hang.

Status scope dump - 
https://axonsv.app.intel.com/apps/record-viewer/019b2b32-6a33-7102-9a6c-f28ba9a6fca4

Steps to Reproduce:

import diamondrapids.pm.SB_Harasser.sb_harasser_DMR as hr

#Primecode(Read)-Posted

hr.run_harasser_loop(interval
= 10, t_time = 300, die

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww03.3]

SB harasser Testline will be updated to exclude the Aux EP from EP
targetted. AR sysdebug to close this sighting. 

[26ww03.1]

Joseph S clarified that external agents should not access the endpoint register, and is seeking documentation and confirmation from the S3M team to ensure proper handling and avoid future issues.

### Description
Collaterals
:

Platform: 

AN004022BMH2291.amr.corp.intel.com

IFWI: 

OKSDCRB1.86B.0030.D43.2512102234

Summary
:

Able to reproduce this issue on 2 platforms.

While running SB Harasser with Primecode on IMH EPs we are seeing Hang.

Status scope dump - 
https://axonsv.app.intel.com/apps/record-viewer/019b2b32-6a33-7102-9a6c-f28ba9a6fca4

Steps to Reproduce:

import diamondrapids.pm.SB_Harasser.sb_harasser_DMR as hr

#Primecode(Read)-Posted

hr.run_harasser_loop(interval
= 10, t_time = 300, die_id=[8],pmsb=1,gpsb=1,
pcode=1,ocode=0,pcode_operation=0,pcode_operation_type=1)

#Primecode(Write)-Posted

hr.run_harasser_loop(interval = 10, t_time = 300, die_id=[8],pmsb=1,gpsb=1, pcode=1,ocode=0,pcode_operation=1,pcode_operation_type=1)

### Comments (latest)
++++1667189357 salmanha
<p style="margin:0in;font-family:Calibri;font-size:11.0pt">Tried manual Posted transactions on following EP:</p><div style="direction:ltr">

<table border="1" cellpadding="0" cellspacing="0" valign="top" style="direction: ltr; border-style: solid; border-color: rgb(163, 163, 163); border-width: 1pt;" title="" summary="">
 <tbody><tr>
  <td style="border-color: rgb(163, 163, 163); border-width: 1pt; vertical-align: top; width: 0.6673in; padding: 4pt;">
  <p style="margin: 0in; font-family: &quot;Aptos Narrow&quot;; font-size: 11pt;">S3M</p>
  </td>
  <td style="border-color: rgb(163, 163, 163); border-width: 1pt; vertical-align: top; width: 1.0395in; padding: 4pt;">
  <p style="margin: 0in; font-family: &quot;Aptos Narrow&quot;; font-size: 11pt;">iosf_sb_1_ibl</p>
  </td>
  <td style="border-color: rgb(163, 163, 163); border-width: 1pt; vertical-align: top; width: 0.8055in; padding: 4pt;">
  <p style="margin: 0in; font-family: &quot;Aptos Narrow&quot;; font-size: 11pt;">{3:
  None}</p>
  </td>
  <td style="border-color: rgb(163, 163, 163); border-width: 1pt; vertical-align: top; width: 0.6673in; padding: 4pt;">
  <p style="margin: 0in; font-family: &quot;Aptos Narrow&quot;; font-size: 11pt;">GPSB</p>
  </td>
  <td style="border-color: rgb(163, 163, 163); border-width: 1pt; vertical-align: top; width: 0.6673in; padding: 4pt;">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt">&nbsp;</p>
  </td>
  <td style="border-color: rgb(163, 163, 163); border-width: 1pt; vertical-align: top; width: 0.5in; padding: 4pt;">
  <p style="margin: 0in; font-family: &quot;Aptos Narrow&quot;; font-size: 11pt;">All</p>
  </td>
 </tr>
</tbody></table>

</div><p style="margin:0in;font-family:Calibri;font-size:11.0pt"><br /></p><div style="direction:ltr">

<table border="1" cellpadding="0" cellspacing="0" valign="top" style="direction: ltr; border-style: solid; border-color: rgb(163, 163, 163); border-width: 1pt;" title="" summary="">
 <tbody><tr>
  <td style="border-color: rgb(163, 163, 163); border-width: 1pt; vertical-align: top; width: 1.2819in; padding: 4pt;">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt">&nbsp;</p>
  </td>
  <td style="border-color: rgb(163, 163, 163); border-width: 1pt; vertical-align: top; width: 4.3923in; padding: 4pt;">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt">Command line for
  posted/non-posted read on portid=3</p>
  </td>
  <td style="border-color: rgb(163, 163, 163); border-width: 1pt; vertical-align: top; width: 0.5312in; padding: 4pt;">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt">Status</p>
  </td>
 </tr>
 <tr>
  <td style="border-color: rgb(163, 163, 163); border-width: 1pt; vertical-align: top; width: 1.3013in; padding: 4pt;">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt">Non-Posted Read</p>
  </td>
  <td style="border-color: rgb(163, 163, 163); border-width: 1pt; vertical-align: top; width: 4.4111in; padding: 4pt;">
  <p style="margin:0i

### Tags
Sideband,PRIMECODE_SB_HARASSER,FV_PM_BDC,FV_SB_HARASSER

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

- `sv.socket0.imh0.pcodeio_map.io_sa_bulk_cr_data`

## Timeline

- **Submitted**: 2025-12-22 15:32:13
- **Closed**: 2026-01-15 03:46:49
- **Days Open**: 23

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
