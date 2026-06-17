# HSD 14026674467: [DMR][X4] Watchdog timeouts from rc_cfcmem_ew resource controller when enabling PC6

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026674467](https://hsdes.intel.com/appstore/article-one/#/14026674467) |
| **Status** | rejected.merged |
| **Priority** | 2-high |
| **Owner** | shijup1 |
| **Component** | hw.rc |
| **Defect Die** | soc |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 75% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | C6 | — |

**Reasoning**: errata_status='review_needed' → HW

## Root Cause Summary

Summary: 
Hitting IMH PUNIT AGG MCA while enabling PKGC6 in X4 silicon

Recipe Used:
 MonitorMWait=Enable, MSR 0xe2 set to 0x22

Impact:
 System hang due to MCA in IMH

System Configuration:
 DMR XCC X4 fused silicon, 16-ch in 1DPC config

BIOS: 
30_D17

Reproducability:
 Always

Light Switch Recovery:
 Disable PC6

Status Scope at failure:
 
https://axonsv.app.intel.com/apps/record-viewer/019b224c-a98c-77c1-8400-814dc079b9d0?tab=summary

Details:

Error1:

Waiting for device (P-channel 1) to tr

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww07.3]

Jinwen was working with the trace and Visa teams to obtain relevant trace data, and Hector M agreed to coordinate and share any updates with the group.

﻿[26ww07.1]

Hector M explained that a dedicated task force, including Joe and Sarah, is actively debugging die-to-die and watchdog timeout issues, with ongoing discussions and updates primarily occurring in a team chat rather than formal documentation.

The team noted that while there are different error signatures, such as die-to-die timeouts and resource controller watchdog timeouts, it is still unclear if these share a common root cause, and merging investigations is premature.

14026822627  /  14026674467

﻿[26ww05.3]

Shiju Philip reported that the UCIE recipe provided by Robert Southwell was applied to two setups, both of which passed without failures, and additional experiments suggested stability improvements with the ITD fuse override.

The team discussed that the same UCIE recipe and workarounds were being tested for related issues, such as RC watchdog timeouts, and that initial results were promising but more setups needed to be tested to confirm the fix's effectiveness.

Joseph S noted that multiple error signatures were being tracked across several sightings, and planned to clean up the records, file a new pre-sighting for any remaining unique signatures, and eventually merge related sightings for clarity. (14026674467 / 14026822627)

[26ww04.3]

Yesterday Robert Southwell provided a new UCIe recipe, FV is observing some stability but issue still there. Hector sill sync up wit
h Sarah to check if its the same or different recipe and give it a try. AR 

FV will try the experiments as Sarah and Robert recipes are not the same. 

[26ww03.3]

This is unique to X4, PV team is also reproducing this, new task force started yday, is in place for all PC6 run by Joe and Elena. Next step to be defined after analyzing all the different failures related to this HSD.

[26ww03.1]

Shiju is OoO, Elena will

### Description
Summary: 
Hitting IMH PUNIT AGG MCA while enabling PKGC6 in X4 silicon

Recipe Used:
 MonitorMWait=Enable, MSR 0xe2 set to 0x22

Impact:
 System hang due to MCA in IMH

System Configuration:
 DMR XCC X4 fused silicon, 16-ch in 1DPC config

BIOS: 
30_D17

Reproducability:
 Always

Light Switch Recovery:
 Disable PC6

Status Scope at failure:
 
https://axonsv.app.intel.com/apps/record-viewer/019b224c-a98c-77c1-8400-814dc079b9d0?tab=summary

Details:

Error1:

Waiting for device (P-channel 1) to transition
out of P_CONTINUE or P_COMPLETE|{'error_code': 'WATCHDOG', 'error_domain':
'P-channel', 'source_port_id': 265, 'source_ip': 265, 'ip_type': 'RC',
'instance': 'socket0.imh1.resctrl.rc_cfcmem_ew'}|

Error2:

In [65]: server_ip_debug.punit.errors.show_mca_status()

===============================================================================================================================================================================================================================================================================================================================================================================================================================================

|skt|die_id|inst|inst_name         |mscod|mcacod|error type|overflow|error_source|description                                                            |error_specific_info                                                                                                                                                                                                    |next_steps                                                  |

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### Comments (latest)
++++14614921663 shijup1
<b>Status Scope at failure:</b>&nbsp;<a href="https://axonsv.app.intel.com/apps/record-viewer/019b224c-a98c-77c1-8400-814dc079b9d0?tab=summary" target="_blank" tabindex="-1" style="background-color: rgb(255, 255, 255); font-family: Roboto, Arial, sans-serif; font-weight: 400;">https://axonsv.app.intel.com/apps/record-viewer/019b224c-a98c-77c1-8400-814dc079b9d0?tab=summary</a><!--EndFragment-->

++++14614921664 shijup1
<p class="MsoNormal"><span style="font-size:11.0pt">Since all hang are due to
rc_cfcmem_ew watchdog timeout, did an <span style="background-image: initial; background-position: initial; background-size: initial; background-repeat: initial; background-attachment: initial; background-origin: initial; background-clip: initial;">experiment to disable all related watchdog timer checks, with this PKGC
was stable&nbsp; for one hour.</span> This confirms the resource controller
pkgc6 functionality is not broken, but the handshake is taking longer time to
execute. Below is the recipe used to disable watchdog timer.<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">&nbsp;</span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_idle_late_regss.qch_error_cfg.watchdog_q_enter_signal_disable=1<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_idle_late_regss.qch_error_cfg.watchdog_q_exit_signal_disable=1<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_idle_late_regss.qch_error_cfg.watchdog_q_exit_disable=1<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_idle_late_regss.qch_error_cfg.watchdog_q_enter_disable=1<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_idle_late_regss.qch_error_cfg.watchdog_q_exit_disable=1<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_idle_late_regss.qch_error_cfg.watchdog_resource_active_signal_disable=1<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_idle_late_regss.qch_error_cfg.watchdog_resource_idle_signal_disable=1<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_idle_late_regss.qch_error_cfg.watchdog_resource_active_disable=1<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">sv.sockets.imhs.resctrl.rc_cfcmem_ew.resctrl_pblc_idle_late_regss.qch_error_cfg.watchdog_resource_idle_disable=1<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">&nbsp;<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">sv.sockets.imhs.resct

### Tags
FV_PM

### Conclusion
no_root_cause.rejected

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

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0xe2`
- `MSR 0xE2`
- `sv.socket0.cbb0.base.d2d_stacks.ulas.ula.ula_link_ctrl.l1_enable`
- `sv.socket0.imhs.d2d_stack.d2d_stacks.uxis.ula_link_ctrl.l1_enable`
- `sv.socket0.imhs.d2d_stack.d2d_stacks.ucie_phy.ucie_ohsphy_ms.ucie_ohsphy_cr_txfifo_threshold`
- `sv.socket0.cbbs.base.d2d_stacks.ucie_ophy.ucie_ohsphy_ms.ucie_ohsphy_cr_txfifo_threshold`
- `sv.socket0.imhs.d2d_stack.d2d_stacks.ucie_phy.ucie_ohsphy_shareds.ucie_ohsphy_shared_quadgen_ctrl.gv_disable`

## Timeline

- **Submitted**: 2025-12-23 08:03:59
- **Closed**: 2026-02-23 22:24:01
- **Days Open**: 62

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
