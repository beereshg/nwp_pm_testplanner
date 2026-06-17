# HSD 22021559010: [X1 A0 PO][DMR][IMH1][fused] - Observing Incorrect LOWEST_LINEAR_PERFORMANCE value for MSR 0x771

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22021559010](https://hsdes.intel.com/appstore/article-one/#/22021559010) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | aamarna1 |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Reset/Boot | 75% |
| **Sub-Feature** | Boot | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Boot System with CPL_EN. 

Read MSR 0x771. Observing incorrect value for 
Bits 31:24 - 

LOWEST_LINEAR_PERFORMANCE
 for MSR 0x771. The value is seen set to 100.

[root@2025ww28-CentOS pmutil]# rdmsr 0x771

1
080d1f

From platform info msr, 0xCE, minimum frequency ratio is shown as 4

[root@2025ww28-CentOS
~]# rdmsr 0xce

4
080cfd800d00

Fuse info:
 

name=&quot;core0_fuse.core_fuse_core_fuse_acode_ia_min_ratio&quot;  value=&quot;0b0000100&quot;

From sst_pp_info_11, minimum frequency is seen as 

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25WW39.3]

No pCoder attendance

[25WW39.1]

No pCoder attendance

[25WW38.3]
Issue: incorrect value for Bits 31:24 - LOWEST_LINEAR_PERFORMANCE for MSR 0x771
We discussed this Pcode issue where the lowest linear performance value in the MSR 0x771 is hardcoded to 1 instead of reflecting the correct fuse value
Abhinand explained that the whereas all the other values are being picked up from the fuse, but only this lowest linear performance they've hard coded to 1.
Next step: Abhinand investigate whether the value should come from core fuses or Punit fuses and how the value is propagated.

### Description
Boot System with CPL_EN. 

Read MSR 0x771. Observing incorrect value for 
Bits 31:24 - 

LOWEST_LINEAR_PERFORMANCE
 for MSR 0x771. The value is seen set to 100.

[root@2025ww28-CentOS pmutil]# rdmsr 0x771

1
080d1f

From platform info msr, 0xCE, minimum frequency ratio is shown as 4

[root@2025ww28-CentOS
~]# rdmsr 0xce

4
080cfd800d00

Fuse info:
 

name=&quot;core0_fuse.core_fuse_core_fuse_acode_ia_min_ratio&quot;  value=&quot;0b0000100&quot;

From sst_pp_info_11, minimum frequency is seen as 400

Bootscript Recipe - Recipe_23 + ITD Disable Fuse Override for IMH 

Latest Magic Recipe - 
\\
amr.corp.intel.com
\ec\proj\debug\DMR\Tools\IFWI\Approved\UCC_A0\

magic_OKSDCRB1.86B.2025.34.4.03_2654.D10_7020094E_1P0_NonIPClean_Trace_DebugSigned_updated_S3M

System Details

SC00901159H0021

1S

D5J42F1100028

### Comments (latest)
++++22611458984 ctan82
<p>For LOWEST_LINEAR_PERFORMANCE == 1 in MSR 0x771, we had this in pre-silicon and it was mentioned all according to spec and it is not a bug.</p><p><a href="https://hsdes.intel.com/appstore/article-one/#/article/15016504147" target="_blank">https://hsdes.intel.com/appstore/article-one/#/article/15016504147</a></p><p><br /></p>

++++22611458985 aamarna1
<p>&nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Tan, Chun Ming</span>&nbsp;- In that case from our past experience in GNR when DFC kicks in we have seen frequency drop to 400MHZ / 500 MHZ and this value reflects the same in MSR on GNR / CWF / SRF. In this case in DMR from fuse ia_min_ratio is 400 so system will go down to 400MHz but from customer perspective they will be looking at MSR and thinking it should be 100MHz this is a discrepancy.&nbsp;</p><p><br /></p><p>Adding Nati, Abitan and Anatoli to comment further.</p><p><br /></p><p><!--StartFragment--><img src="https://hsdes.intel.com/rest/binary/22021523250" alt="" /><!--EndFragment--></p><p><br /></p><p><br /></p>

++++22611458986 aamarna1
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 22021519534.

++++22611459009 aamarna1
Had a word with Stan, CBB Pcode should honour IA_MIN_RATIO from fuse for Pm frequency and it should not be hardcoded to 0x1. 
++++1566486950 ctan82
15016504147 (related-link) - link(s) are added via link tab.
++++22611459183 schen6
If lowest_perf reports a value lower than the actual hardware supported minimum freq (IA_MIN_RATIO fuse), it can lead to software making invalid requests, inaccurate power/performance modeling, confusion during validation, and misleading user reporting. My recommendation is we should fix this issue. 
++++14614607213 vwang
Adding FW sides into the loop.
++++1363412841 ygorbman
Hi,  @Wang, Vidar  I see this https://hsdes.intel.com/appstore/article-one/#/article/15016504147 HSD is rejected. So, why this issue is opened again? Who from DMR can approve this requirement again?  From HSD: From: Sabin, Yevgeni <yevgeni.sabin@intel.com> Sent: Wednesday, October 30, 2024 12:17 AM To: Miranda Morales, Hiram <hiram.miranda.morales@intel.com>; Scanlon, Jeffrey <jeffrey.scanlon@intel.com>; Ziv, Tomer <tomer.ziv@intel.com> Cc: Seenivasagam, Muthumari <muthumari.seenivasagam@intel.com> Subject: RE: s15016504147 - LOWEST_LINEAR_PERFORMANCE value read from MSR 0x771 is 1   As I already answered in other thread – spec allows both implementations, so this is not a bug. We will stay with current implementation since there is no issue.     Thanks, Yevgeni
++++22611474375 sghosh7
Updates from Anatoli Odler (9/18): "Hi folks, We had a discussion with Nati and other folks. We qualify this issue as a Pcode bug: LOWEST_LINEAR_PERFORMANCE shall be assigned to fuse IA_MIN_RATIO. We will clone it to PCode bugeco ticket.   Thanks, Anatoli" Pcode bugeco 13013733525
++++14614658563 vwang
Abitan, Nati, Odler, Anatol

### Tags
cdgmdt.pm,SysDebugCloned,SysDebugDccbBypass

### Conclusion
not_a_bug

### Component
fw.pcode

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

- **Primary Feature**: Reset/Boot
- **Sub-Feature**: Boot
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x771`

## Timeline

- **Submitted**: 2025-09-10 04:22:12
- **Root Caused**: 2025-09-26 00:32:30
- **Closed**: 2025-11-19 21:44:00
- **Days Open**: 70

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
