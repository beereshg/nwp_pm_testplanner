# HSD 14025874051: [DMR][X1 A0 PO][PKGC] Enabling PKGC6 results in Watchdog Timeout and Fabric Disablement in Single DIMM

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025874051](https://hsdes.intel.com/appstore/article-one/#/14025874051) |
| **Status** | complete.broken |
| **Priority** | 2-high |
| **Owner** | shijup1 |
| **Component** | hw.power |
| **Defect Die** | ioe |
| **Conclusion** | hw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 85% |
| **Feature** | Core C-States | 75% |
| **Sub-Feature** | C6 | — |

**Reasoning**: conclusion='hw.bug' → HW

## Root Cause Summary

Summary:

========

Enabling PKGC6 results in MCA 1026 (

Waiting for qch_accept or qch_deny to move the noise Q-channel state from Q_REQUEST to Q_STOPPED or Q_DENIED|{'error_code': 'WATCHDOG', 'error_domain': 'Q-channel', 'source_port_id': 263, 'source_ip': 263, 'ip_type': 'RC', 'instance': 'socket0.imh0.resctrl.rc_cfcio'}

  ) on fused part. At the time of hang only PC2 residency observed.

status scope report : 
https://axonsv.app.intel.com/apps/record-viewer/0198fef1-1601-77e2-8516-00316d223

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww41.1]

The team has identified an issue with the IOCACHE DVP and is working with the arch team to understand the problem, having reproduced it in emulation. 

They are also investigating why similar issues are not observed with UBR DVP, suggesting more nuanced failure modes.

DCCB may need this analysis as well.

[25ww40.4]

Enabling PKGC6 results in Watchdog Timeout and Fabric Disablement in Single DIMM

This wdog timeout has been reproduced on the emulation by George, Abhinav.  Basically, by running single-dimm configuration with the SCA IP_DISABLES added by 

14025751110

. Note: it would occur any time the SCAs are disabled without their associated IOCACHE disable set.

William described several workarounds for the unresponsive DVPs, including setting IP disables on associated IO caches, using ISA spare config bits to ignore the Q channel, fuse disables for IO cache, and watchdog timer disables, all of which can help bypass the issue.

Next step: Vidar will rootcause this to a SoC HW bugeco, DCCB will decide the further steps including PrimeCode WA and/or RTL fix for IMH2.

[25WW39.3]

William is trying the experiments on the system, will add comment with his findings later.

[25WW39.1]

The issue is related to disabling memory controllers and fabric components, confirming that MC disables appear to work but fabric disables are problematic. The issue persists with fabric disables, specifically with DVPs, and further system testing is planned.

[25WW38.3]

The original problem is a watchdog timeout occurring when running PC6 with only one DIMM installed.
The root cause appears to be that PrimeCode disables  half of the fabric IPs under CFCIO, resulting in all DVPs under that half not reporting their status to the package controller (PC), and not responding to Q channel requests. This incomplete status reporting prevents successful entry into PC6.
This is likely a HW bug where SCA/IOCACHE DVP QChs are not handled properly when those IP are disabled.  
WA is a

### Description
Summary:

========

Enabling PKGC6 results in MCA 1026 (

Waiting for qch_accept or qch_deny to move the noise Q-channel state from Q_REQUEST to Q_STOPPED or Q_DENIED|{'error_code': 'WATCHDOG', 'error_domain': 'Q-channel', 'source_port_id': 263, 'source_ip': 263, 'ip_type': 'RC', 'instance': 'socket0.imh0.resctrl.rc_cfcio'}

  ) on fused part. At the time of hang only PC2 residency observed.

status scope report : 
https://axonsv.app.intel.com/apps/record-viewer/0198fef1-1601-77e2-8516-00316d223da5/intel-svtools-report-v1?tab=report

Impact:

========

Silicon hang while enabling PKGC6

Details:

========

REPLACE  with failure and triage details.

==> System configuration ...

X1 fused silicon , 32 Cores

==> BIOS/Patch/IFWI/BKC/CI Versions ...

OKSDCRB1.86B.2025.35.3.01_2688.D02_6020095E_1P0_NonIPClean_Trace_DebugSigned_update_primecode_pcode

==> Reproducibility ...

Always

==> Lightswitch discoveries ...

 None

==> Experiment results ...

### Comments (latest)
++++14614596048 shijup1
<p>Attached status scope captured during PC2 residency hit and SVOS hang happened:&nbsp;<a href="https://axonsv.app.intel.com/apps/record-viewer/0198fef1-1601-77e2-8516-00316d223da5?tab=summary" target="_blank">https://axonsv.app.intel.com/apps/record-viewer/0198fef1-1601-77e2-8516-00316d223da5?tab=summary</a></p><p><br /></p><p>Below are the other debug registers captured</p><p><br /></p><p>===================================================================================================================================================================================================================================================================================================================================================================</p><p>|skt|die_id|inst|inst_name&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;|mscod|mcacod|error type|overflow|error_source|description&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;|error_specific_info&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;|next_steps|</p><p>-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------</p><p>|0&nbsp; |0&nbsp; &nbsp; &nbsp;|0&nbsp; &nbsp;|socket0.imh0.punit|AGG&nbsp; |1026&nbsp; |Fatal&nbsp; &nbsp; &nbsp;|&nbsp; &nbsp; &nbsp; &nbsp; |RC&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; |Waiting for qch_accept or qch_deny to move the noise Q-channel state from Q_REQUEST to Q_STOPPED or Q_DENIED|{'error_code': 'WATCHDOG', 'error_domain': 'Q-channel', 'source_port_id': 263, 'source_ip': 263, 'ip_type': 'RC', 'instance': 'socket0.imh0.resctrl.rc_cfcio'}|&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; |</p><p>-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------</p><p>|0

### Tags
SysDebugCloned,FV_PM,FWTF_PRIORITY_X1,SysDebugDccbDone,FIX_PATCH_DMR_AP1_A0_60000982,FIX_IFWI_DMR_AP1_2025.49.3.02,BKC#OKS_DMR_AP_X1_2025WW50,FIX_BKC_OKS_DMR_AP1_2025WW50,cov.pm.pkgc, PSF=Y

### Conclusion
hw.bug

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

- `sv.socket0.imh0.dfd_dvp.search`
- `sv.socket0.imh0.dfd_dvp.get_by_path`
- `sv.socket0.imh1.dfd_dvp.search`
- `sv.socket0.imh1.dfd_dvp.get_by_path`
- `sv.socket0.imhs.spk.spk0.spk_main_crnode.spk_clock_control.drain_timeout_value.write`

## Timeline

- **Submitted**: 2025-09-06 10:02:27
- **Root Caused**: 2025-10-03 04:38:29
- **Closed**: 2025-12-16 20:42:54
- **Days Open**: 101

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
