# HSD 14026570380: [DMR][X1 A0] TXT is enabled in BIOS but it is disabled in B2P MBX read_pcu_misc_config

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026570380](https://hsdes.intel.com/appstore/article-one/#/14026570380) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | egomezgo |
| **Component** | bios |
| **Defect Die** | soc |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **BIOS** | 65% |
| **Feature** | PState Stack | 45% |
| **Sub-Feature** | general | — |

**Reasoning**: component='bios' → BIOS

## Root Cause Summary

Summary:

========

BIOS knob has 

ProcessorLtsxEnable = 0x1

 but B2P MBX 

READ_PCU_MISC_CONFIG.TXT_ENABLE = 0x0

Details:

========

==> System configuration: FDU3A/FDU3C

==> QDF: 

==> BIOS/Patch/IFWI/BKC/CI Versions: 

==> Reproducibility: Always

==> Lightswitch discoveries ...

==> Experiment results ...

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww10.1]

Synced offline with Carlos and Emiliano, agreed to reject this as not a defect, any follow up of this issue can be opened in another ticket

[26ww09.3]

Joe S mentioned it is expected behavior, will add comment. trending to be rejected 

[26ww08.4]

Emiliano is on vacations till next week, he touched based with security team and they do not have a concern, they see TXT working as expected. Trend is to reject this sighitng as not a defect. 

﻿[26ww07.1]

Emiliano reported difficulties in collecting the required log to debug TXT enablement, and sought feedback from the security team, with Vidar emphasizing the importance of documenting all actions and findings.

[26ww04.3]

Emiliano is trying to collect Primecode trace with a right trigger. will ping Alex for help. 

[26ww04.3]

Hector synced with Emiliano, plan is to take the trace today. 

[26ww03.3]

It looks suspicious as other fields on that same register are working fine, reproducibility is 100%, next step is for Emiliano to contact Edgar Chung's team to get support for primecode trace. Root primecode will get the command and forward for all leaves. 

[26ww03.1]

Joseph S noted that the issue is intermittent and may be related to sequence or firmware timing, suggesting additional system time or rerunning the configuration on Cemex to reproduce the problem.

It was confirmed that BIOS does write the relevant bit, but the full sequence was not vetted, and further investigation is needed to determine the root cause.

[25ww51.3]

Stanley and Suchi agreed to follow up with the conversation

[25ww51.1]

AR: Suchismita will discuss with Nilanjan and Stanley to clarify the remaining inquiry.

[25ww50.3]

Nilanjan and Stanley agreed to take an action item to clarify the intersection of BIOS, TPMI, and B2P mailbox usage for TXT, and to determine if the register is still in use or should be removed.

The group discussed how TXT enablement interacts with near TDP features, with Alex explaining that the PCU misco

### Description
Summary:

========

BIOS knob has 

ProcessorLtsxEnable = 0x1

 but B2P MBX 

READ_PCU_MISC_CONFIG.TXT_ENABLE = 0x0

Details:

========

==> System configuration: FDU3A/FDU3C

==> QDF: 

==> BIOS/Patch/IFWI/BKC/CI Versions: 

==> Reproducibility: Always

==> Lightswitch discoveries ...

==> Experiment results ...

### Comments (latest)
++++14614873893 hmpicosm
Hi Emiliano, since TXT is a Security feature, could you please sync with Security team on this issue?

++++14614873894 egomezgo
<p>BIOS:&nbsp;&nbsp;OKSDCRB1.86B.0029.D60.2511200302&nbsp;<br />Attaching log:&nbsp;<a href="https://hsdes.intel.com/resource/14026570257" target="_blank">https://hsdes.intel.com/resource/14026570257</a>&nbsp;<br /><br />Before and after and I dont see the MBX change:<br /><img src="https://hsdes.intel.com/rest/binary/14026570254" style="width: 800px;" /><br /><br /><img src="https://hsdes.intel.com/rest/binary/14026570255" style="width: 800px;" /><br /><br /><br /></p>

++++14614873895 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14026211672.

++++14614877725 jsbrooks
Debug Status summary: Star (BIOS) confirmed that changing the BIOS knob ProcessorLtsxEnable=0x1 should result in B2P WRITE_PCU_MISC_CONFIG to set PCU_MISC_CONFIG.TXT_ENABLE bit. There was some data in debug thread that Emiliano didn't see this failure at some point; so, we should monitor for intermittency.   Simics run w/ same BIOS knob settings may shed some light, in case this is a RMW issue, etc.  
++++22611670144 mbfausto
No comments for ~3 weeks, what's the current status of the debug?  we should have the simics run results and the pcode trace/debug_patch (if needed) results to see how primecode is responding, right?  What are the results of that?
++++14614959013 egomezgo
Still seeing issue:  BIOS: OKSDCRB1.86B.0030.D63.2512181804
++++22611729996 mbfausto
Team - no comments or updates in over 2 weeks.  Need to get traction on your issue, what is your latest status and progress of experiments in flight?
++++14615017655 egomezgo
Manual process is slow in order to get the desired signals. Need some more guidance regarding the the trigger trace, not sure if someone from PrimeCode could support me.

++++14615069949 egomezgo 
From  @Peterson, Val feedback from Security team, seems that they wouldn't be able to run their TXT tests if the command is not sent.


++++14615072078 abaskara
Hi, I have checked the attachment 2025_12_06_BIOSLog_Pmax_TXT.log from this hsd. Seems BTG is failing, S00,invalid signature S00,BTG Key Manifest Failed S00,Error Logged: Class Code = 0011, Error Code = 0004, Minor Code = 000A ERROR: LT_SPAD_DONE_LOW register. LT_ERROR_CODE_LOW[0xFED30328] = 0xC00A9110 BIOS ACM error present. Aborting lock config. Failed to run LockConfig Status = Device Error This might be the reason for your issue? Please try with latest orange IFWI in VIS part. TXT  is successfully validated already. Thanks, Arun

++++14615076610 egomezgo
Today  @Perez Carrillo, Adriana help me to enable TXT but seems we are still missing something to enable it. Also seems that some more configuration as well is needed in order to enable this feature, like TPM and some other BIOS knobs like ProcessorSmxEnable = 1 and ProcessorVmxEnable = 1. Will continue working with her just to

### Tags
FV_PM

### Conclusion
not_a_bug

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: general
- **Component Path**: bios

## Firmware Touchpoints

### BIOS
- `BIOS knob`

## Timeline

- **Submitted**: 2025-12-06 07:04:51
- **Closed**: 2026-03-02 21:34:48
- **Days Open**: 86

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
