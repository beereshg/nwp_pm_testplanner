# HSD 14027364000: [DMR][X4[PM][PC6] Recoverable - CMCI - RC - Reached PKGC consecutive denied attempts limit P-channel 1

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027364000](https://hsdes.intel.com/appstore/article-one/#/14027364000) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | hmpicosm |
| **Component** | hw.rc |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Core C-States | 75% |
| **Sub-Feature** | C6 | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

Seeing this error in X4 VIS part 224c, during long PC6 testing, in OS idle
 

In [68]: from pysvtools import server_ip_debug

In [69]: server_ip_debug.punit.errors.show_mca_status(source=&quot;reg&quot;)

=======================================================================================================================================================================================================================================================================================================

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
Follow up with Joe for A0 
﻿[26ww12.3]

Joseph provided details on the required patches and confirmed that applying both D2D L1 bypass, pCode patches and disable retry timeout on D2D Q and P channels, should address the observed signature, with Hector planning to test this approach.

Hector and Joseph agreed to coordinate on scheduling long-duration tests on system 2471, as these experiments require 12-24 hours of continuous operation to observe the effects of the patches.

### Description
Seeing this error in X4 VIS part 224c, during long PC6 testing, in OS idle
 

In [68]: from pysvtools import server_ip_debug

In [69]: server_ip_debug.punit.errors.show_mca_status(source=&quot;reg&quot;)

=======================================================================================================================================================================================================================================================================================================================================================================================

|skt|die_id|inst|inst_name         |mscod|mcacod|error type        |overflow|error_source|description                                                                                                  |error_specific_info                                                                                                                                                |next_steps|

---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

|0  |0     |0   |socket0.imh0.punit|AGG  |1026  |
Recoverable - CMCI
|1       |RC          |
Reached the programmed limit of consecutive denied attempts to move to Package-C Idle Pstate for P-channel 1
.|{'error_code': '
PC6_RETRY
', 'error_domain': 'P-channel', 'source_port_id': 265, 'source_ip': 265, 'ip_type': 'RC', 'instance': '
socket0.imh0.resctrl.rc_cfcmem_ew
'}|          |

---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### Comments (latest)
++++14615197431 jsbrooks
<p>Is this with D2D L1 bypassed or enabled?</p><p><br /></p><p><br /></p>

++++14615197432 hmpicosm
This issue is reproduced with D2D L1 bypassed.&nbsp;

++++14615197433 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 22022109716.

++++14615220166 jsbrooks
We are not currently running with the full B0 workaround on IMH for the PkgC D2D/LTR bug.  We manually do step #2, but we are not doing #4.  Step #4 should resolved this sighting.

++++14615220176 jsbrooks
Please rerun with the following: sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_idle_late_regs0.qch_error_cfg.pkgc_retry_threshold_disable = 1 sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_idle_late_regs1.qch_error_cfg.pkgc_retry_threshold_disable = 1 sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_pch_regs0.pch_error_cfg.pkgc_retry_threshold_disable = 1 sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_pch_regs1.pch_error_cfg.pkgc_retry_threshold_disable = 1

++++14615227094 hmpicosm
System ANxx2471 is running with below ingredients: D2D L1 bypass pcode patch: \\amr.corp.intel.com\ec\proj\debug\DMR\User\agraback\ww10p2_rebased_pcode_skip_d2d_l1\OKSDCRB1_86B_2026.09.3.04_0032.D77_80000993_0.758.0_1P0_NonIPClean_Trace_DebugSigned_VIS_C0581957_202603040711.bin IMH D2D L1 disabled: sv.socket0.imhs.d2d_stack.d2d_stacks.uxis.ula_link_ctrl.l1_enable=0; D2D QCh/PCh retry timeout disable: sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_idle_late_regs0.qch_error_cfg.pkgc_retry_threshold_disable = 1 sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_idle_late_regs1.qch_error_cfg.pkgc_retry_threshold_disable = 1 sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_pch_regs0.pch_error_cfg.pkgc_retry_threshold_disable = 1 sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_pch_regs1.pch_error_cfg.pkgc_retry_threshold_disable = 1

++++14615229465 hmpicosm
System ANxx2471 has been running for more than 18 hrs. It has not exhibited the issue: In [225]: sv.sockets.imhs.punit.ras.gpsb.mc_status Out[225]: socket0.imh0.punit.ras.gpsb.mc_status - 0x0000000000000000 socket0.imh1.punit.ras.gpsb.mc_status - 0x0000000000000000 In [226]: server_ip_debug.punit.errors.show_mca_status(source="reg") In [227]:
++++22611811747 mbfausto
 @Brooks, Joseph S  - What is the bug this is a WA for?  Is DMR-AP UCC A0 missing some FW setting we need that didn't get filed?
++++14615232026 hmpicosm
System ANxx2471 has been running for ~30 hrs. It has not exhibited the issue. System will be taken for other validation activities:

++++14615232606 jsbrooks
 @Fausto, Matthew B  This is the original HW bug https://hsdes.intel.com/appstore/article-one/#/14026073009. AP1 A0 patch - Modified PkgC flow to reduce impact of bug, but D2D L1 is enabled. AP1 B0 patch - Bypass D2D L1.  (IMH snapshot pasted earlier) AP2 - HW fix. So, I don't think this was an issue w/ any official patch; I think this was missing step in manually implementing B0 patch.



### Tags
FV_PM

### Conclusion
not_a_bug

### Component
hw.rc

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
- **Component Path**: hw.rc

## Firmware Touchpoints

### PCODE
- `pCode patch`

## Key Registers

- `sv.socket0.imhs.d2d_stack.d2d_stacks.uxis.ula_link_ctrl.l1_enable`
- `sv.socket0.cbbs.base.d2d_stacks.ulas.ula.ula_link_ctrl.l1_enable`

## Timeline

- **Submitted**: 2026-03-12 07:13:15
- **Closed**: 2026-03-23 23:48:07
- **Days Open**: 11

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
