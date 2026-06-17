# HSD 14026719389: [DMR][X1 A0] RIT - Lower-cdyn frequency is being throttled down to heavier workload frequency

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026719389](https://hsdes.intel.com/appstore/article-one/#/14026719389) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | dlwu |
| **Component** | hw.power |
| **Defect Die** | base |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 75% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | C6 | — |

**Reasoning**: errata_status='transferred' → HW

## Root Cause Summary

- When testing RIT (noisy neighbor) feature, we are seeing that when running two different workloads on two cores within the same module, the core running the lower cdyn frequency is being throttled down to the heavier workload frequency.

- In our testing, we run the lighter workload bwaves on core0. htop reports core0 frequency while running bwaves alone is 3.1GHz.

- We then run the heavier workload BGEMM on core1. htop reports core1 frequency while running BGEMM alone is 2.5GHz.

- When we r

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww05.1]

Chen confirmed 
the frequency limit comes from fuses that limit the max-frequency for high cdyn licenses (AVX512).

David is 
experimenting modulating it with ido to see how it affects the frequency.

 

[26ww04.3]

David working with Ido to see what is the correct fuse value. Having bootscript issues with latest IFWI. After the experiments will review to file the CBB. 

[26ww03.3]

aCode team involved recently, next step is for aCode to review values and determine next steps. 

[26ww03.1]

David conducted the same experiment as before, this time logging additional registers as requested, and attached the results in an Excel file for review.

[26ww02.3]

David has provided latest results requested by Ido, next step will depend on Ido analysis. AR sysdebug to find the ticket that tracks the new feature submitted by Ido for tracking purposes

[26ww02.1]

David described that when running workloads on two cores of the same Module, the expected frequency adjustment behavior based on the RIT noisy neighbor feature was not observed, regardless of the FVT setting.

The team noted previous struggles with enabling RIT TPMI registers and TRL tables, which are now resolved, but the core feature remains non-functional. David emphasized the need for a debug session with Ido to align validation and architecture perspectives.

Ido and Timothy identified that in DMR, primecode can lower the frequency below the minimum ratio, but unlike GNR, there is no extra step to prevent throttling below 400 MHz, which is required for certain SKUs.

The team is working to gather data on which SKUs require this support, aiming to determine the necessary level of extra throttling to meet TDP or mitigate thermal issues.

An HSD has been filed to track the missing feature, and the team plans to bring the requirement to the CBB team and possibly escalate to a global bug board or CCB for approval once the data review is complete.

### Description
- When testing RIT (noisy neighbor) feature, we are seeing that when running two different workloads on two cores within the same module, the core running the lower cdyn frequency is being throttled down to the heavier workload frequency.

- In our testing, we run the lighter workload bwaves on core0. htop reports core0 frequency while running bwaves alone is 3.1GHz.

- We then run the heavier workload BGEMM on core1. htop reports core1 frequency while running BGEMM alone is 2.5GHz.

- When we run the two workloads together, with bwaves and BGEMM running on core0 and core1, respectively, we see the frequency on core0 is being throttled down to the heavier workload (BGEMM) frequency of 2.5GHz.

- Our expectation is that core1 frequency should rise to match the frequency of core0 running the lighter workload.

Steps to reproduce
:

Boot system to OS idle.

Enable C6 via:

import
pysvtools.xmlcli.nvram as nvram

ram =
nvram.getNVRAM()

ram.pull()

ram.MonitorMWait =
&quot;Enabled&quot;

ram.TurboMode=1

ram.push()

Reboot system to OS idle.

Apply PM recipe:

##Apply PM recipe (details on link):

#https://wiki.ith.intel.com/spaces/fvcommon/pages/4331187759/DMR+PM+Power+On+Recipe

#Below commands as same as in wiki link above (sept5)

#Disable CBB RAPL/RACL due to thresholds setting issue

sv.sockets.cbbs.pcode.vars.rapl.dfx_ring_rapl_disabled=1

sv.sockets.cbbs.pcode.vars.rapl.dfx_ccp_rapl_disabled=1

sv.sockets.cbbs.pcode.vars.rapl.dfx_racl_disabled=1

#sv.sockets.imhs.pcudata.tdc_limit=0

#CC6 IPC issue WA for halting without losing CC6 residency

ipc.config.debugport0.PlatformControl.PreqNotWired = &quot;True&quot;

ipc.config.debugport0.PlatformControl.PrdyNotWired = &quot;True&quot;

ipc.forcereconfig()

ipc.unlock()

#PC2 WA

sv.sockets.imhs.resctrl.rc_cfcio.resctrl_pblc_idle_noise_regss.qch_error_cfg.watchdog_q_enter_disable=1

#PC6 WA

sv.sockets.imhs.isa.isa_mio_1.spare_cfg0=0x18000

#RAPL Settings on IMH to WA BIOS issue with settings:

sv.sockets.imhs.pcudat

### Comments (latest)
++++14614935637 srotich
<p>We set TRL License mapping&nbsp; min and max threshold such that they match ICCP licenses and we see noisy neighbor impacting frequencies</p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">&nbsp;</p><p style="margin:0in;font-family:-apple-system;font-size:10.5pt">sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.min_threshold_idx._0
= 0</p><p style="margin:0in;font-family:-apple-system;font-size:10.5pt">sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.min_threshold_idx._1
= 0 #SSE</p><p style="margin:0in;font-family:-apple-system;font-size:10.5pt">sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.min_threshold_idx._2
= 1 #AVX2</p><p style="margin:0in;font-family:-apple-system;font-size:10.5pt">sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.min_threshold_idx._3
= 2 #AVX512</p><p style="margin:0in;font-family:-apple-system;font-size:10.5pt">sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.min_threshold_idx._4
= 3 #TMUL</p><p style="margin:0in;font-family:-apple-system;font-size:10.5pt">&nbsp;</p><p style="margin:0in;font-family:-apple-system;font-size:10.5pt">sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.max_threshold_idx._0
= 2</p><p style="margin:0in;font-family:-apple-system;font-size:10.5pt">sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.max_threshold_idx._1
= 2</p><p style="margin:0in;font-family:-apple-system;font-size:10.5pt">sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.max_threshold_idx._2
= 4</p><p style="margin:0in;font-family:-apple-system;font-size:10.5pt">sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.max_threshold_idx._3
= 4</p><p>





















</p><p style="margin:0in;font-family:-apple-system;font-size:10.5pt">sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.max_threshold_idx._4
= 4</p><p style="margin:0in;font-family:-apple-system;font-size:10.5pt"><br /></p><p style="margin:0in;font-family:-apple-system;font-size:10.5pt">Frequency response:</p><p style="margin:0in;font-family:-apple-system;font-size:10.5pt"><span style="font-family: Calibri; font-size: 11pt;">&nbsp;</span></p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">a). Povray alone:</p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">&nbsp;<img src="https://hsdes.intel.com/rest/binary/14026162496" width="892" height="134" style="font-family: Roboto, Arial, sans-serif; font-size: 14px;" /></p><p style="margin:0in;font-family:Calibri;font-size:11.0pt"><br /></p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">b). BGEMM alone</p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">&nbsp;</p><p style="margin:0in"><img src="https://hsdes.intel.com/rest/binary/14026162497" width="850" height="150" /></p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">&nbsp;</p><p><span style="font-family: Calibri; font-size: 11pt;">&nbsp;</span></p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">c). Povray + BGEM

### Tags
PTP_SoC,SysDebugCloned,SysDebugCloned,SysDebugDccbDone,SysDebugDccbDriver,FIX_FUSE_UCC_AP1_A0_Y26W16P0

### Conclusion
hw.arch

### Component
hw.power

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
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI registers`
- `sv.socket0.cbb0.base.tpmi.rit_header.show`
- `sv.socket0.cbb0.base.tpmi.fit_config_0.show`
- `sv.socket0.cbb0.base.tpmi.fit_config_1.show`
- `sv.socket0.cbb0.base.tpmi.fit_info_0.show`
- `sv.socket0.cbb0.compute0.pma4.pmsb.resolution_control_2.show`

## Timeline

- **Submitted**: 2026-01-01 02:37:23
- **Root Caused**: 2026-01-29 02:26:36
- **Closed**: 2026-05-06 03:13:59
- **Days Open**: 125

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
