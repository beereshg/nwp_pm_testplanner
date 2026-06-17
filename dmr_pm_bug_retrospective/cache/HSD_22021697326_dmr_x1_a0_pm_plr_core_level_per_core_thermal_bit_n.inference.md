# HSD 22021697326: [DMR] [X1 A0] [PM]  PLR core level, PER_CORE_THERMAL bit not set after injection of temp above TJ

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22021697326](https://hsdes.intel.com/appstore/article-one/#/22021697326) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | jamesrow |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Platform PM Interface | 80% |
| **Sub-Feature** | TPMI | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

- Platform 

JF53NOR09BN0304

- Fused Part 

-IFWI: 

OKSDCRB1_86B_2025.37.3.01_2733.D06_60000964_0.599.0_1P0_NonIPClean_Trace_DebugSigned.bin

-pcode collats:

expectation:

after we set and observe thermal throttling on a core we expect core and die level to report out thermal limiting, bit 3 for die level and bit 55 for core level

observation:

no thermal throttle indicators from plr die or core level 

0. confirm module9 mades to pma 9:

In [80]: sv.socket0.cbb0.compute1.module9.core0.virtu

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww45.1]

Anatoli explained that pCode and aCode are referencing different bits for thermal reporting in IO_ACP_PERF_LIMIT_CORE, and provided links to the relevant documentation for review.

Anatoli pointed to the documentation and previous comments, confirming that pCcode is aligned with the current spec, but aCode may be using a different one.

Ido confirmed that bit #3 of IO_ACP_PERF_LIMIT_CORE is reporting thermal in aCode per the Spec, but noted the need to discuss with the sighting owner to clarify the perceived issue, and committed to adding detailed comments for further tracking.

[25ww44.3]

Anatoli, Igal, James, and Oma discussed the process for collecting Ptracker, James will take on the action item and consult with Jason, Oma, and others as needed to set up the correct triggers and collect the necessary data.

[25ww44.1]

Jason explained that aCode reports thermal throttling in a different PLR bit than expected, and that pCode may not be incorporating aCode's feedback into the correct bit.

Anatoli decided to assign the ticket to an IDC owner for further investigation, with Jason confirming the absence of a Ptracker log that needs IDC involvement.

[25ww43.3]

When cores self-throttle due to thermal reasons, the expected per-core thermal bit in the PLR is not set, whereas it is set during cross-throttling events, indicating a communication or ownership issue between aCode and pCode.

Cross-throttling is managed by pCode, while self-throttling is managed by aCode, and the issue likely lies in how aCcode communicates self-throttling events to the PLR.

pCode & aCode team should be involved to help clarify the mechanism and resolve the discrepancy, with the issue being tracked for follow-up.

### Description
- Platform 

JF53NOR09BN0304

- Fused Part 

-IFWI: 

OKSDCRB1_86B_2025.37.3.01_2733.D06_60000964_0.599.0_1P0_NonIPClean_Trace_DebugSigned.bin

-pcode collats:

expectation:

after we set and observe thermal throttling on a core we expect core and die level to report out thermal limiting, bit 3 for die level and bit 55 for core level

observation:

no thermal throttle indicators from plr die or core level 

0. confirm module9 mades to pma 9:

In [80]: sv.socket0.cbb0.compute1.module9.core0.virtual_msr_cr_pm_logical_id

Out[80]: 0x48

In [81]: 0x48 >> 3

Out[81]: 
0x9

1. set pma9/module9 to 106C:

In [57]: sv.socket0.cbb0.compute1.pma9.pmsb.dfvfcr_dts_fuse_0.cr_reg36_inst.digthermovrden

Out[57]: 0x1

In [58]: sv.socket0.cbb0.compute1.pma9.pmsb.dfvfcr_dts_fuse_0.cr_reg36_inst.digthermovrdval

Out[58]: 0x156  ## 0x156/2-64=106C

2
. confirm module now sees thermal throttling after crossing TJ through core level therm-status, others cores see nothing as expected

In [67]: sv.socket0.cbb0.compute1.modules.core0.ucode_cr_therm_status

Out[67]:

socket0.cbb0.compute1.module8.core0.ucode_cr_therm_status - 0x88410000

socket0.cbb0.compute1.module9.core0.ucode_cr_therm_status - 0x880003c
1 # 
d therm monitor flipped after crossing TJ

socket0.cbb0.compute1.module10.core0.ucode_cr_therm_status - 0x88410000

socket0.cbb0.compute1.module11.core0.ucode_cr_therm_status - 0x883f0000

socket0.cbb0.compute1.module12.core0.ucode_cr_therm_status - 0x88440000

socket0.cbb0.compute1.module13.core0.ucode_cr_therm_status - 0x88420000

socket0.cbb0.compute1.module14.core0.ucode_cr_therm_status - 0x88410000

socket0.cbb0.compute1.module15.core0.ucode_cr_therm_status - 0x883c0000

3. nothing from PLR core and die level:

In [68]: sv.socket0.cbb0.base.tpmi.plr_die_level.data

Out[68]: 
0x0

#settign up plr mailbox for module 9

In [70]: sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.id

Out[70]: 0x15

In [71]: sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.id=9

In [72]: sv.socket0.cbb0.ba

### Comments (latest)
++++1363439450 mmasri
is it same as the one already opened: https://hsdes.intel.com/appstore/article_legacy/#/16028722592 - [X1 A0 PO] Thermal Monitor Log bit inconsistency observed with MSR 0x19c Can we plz merge this one ?
++++14614744445 jasoncwa
Being from the acode side, I was curious about how pcode was consuming the acode status. Pcode is reading ACP_PERF_LIMIT.thermal and loading it into detailed_ccp_plr. https://github.com/intel-restricted/firmware.power.soc.pcode-cbb-a0/blob/926b1f28761490411fa227f7452e1e384bf15845/source/pcode/flows/slow_limits/plr/plr.cpp#L308 Then it uses the value from ACP_PERF_LIMIT.thermal and ORing it with the pcode EMTT slow limit clipping reason for the coarse grain reason. firmware.power.soc.pcode-cbb-a0/source/pcode/flows/slow_limits/plr/plr.cpp at 926b1f28761490411fa227f7452e1e384bf15845 · intel-restricted/firmware.power.soc.pcode-cbb-a0 Read the detailed_ccp_plr from pcode to check if what acode is sending in the acp_perf_limit.thermal value is received.     // Detailed list of limiters for CCP     enum CcpDetailedPlrId {         // Fast limit reasons         PLR_PROCHOT_CCP_ID,         PLR_PMAX_SOFT_CCP_ID,         PLR_PMAX_HARD_CCP_ID,         PLR_SIMPL_CCP_ID,         // TRL         PLR_TRL_ID,         // Slow limit reasons         PLR_FAST_RAPL_CCP_ID,         PLR_PKG_PL1_INBAND_CCP_ID,         PLR_PKG_PL1_CSR_CCP_ID,         PLR_PKG_PL1_OOB_CCP_ID,         PLR_PKG_PL2_INBAND_CCP_ID,         PLR_PKG_PL2_CSR_CCP_ID,         PLR_PKG_PL2_OOB_CCP_ID,         PLR_PLATFORM_PL1_INBAND_CCP_ID,         PLR_PLATFORM_PL1_CSR_CCP_ID,         PLR_PLATFORM_PL1_OOB_CCP_ID,         PLR_PLATFORM_PL2_INBAND_CCP_ID,         PLR_PLATFORM_PL2_CSR_CCP_ID,         PLR_PLATFORM_PL2_OOB_CCP_ID,         PLR_VR_THERMAL_ALERT_CCP_ID,         PLR_EMTTM_CCP_ID, // jasoncwa: this is the source for PEM_STATUS_PEM_PER_CORE_THERMAL         PLR_PCS_LIMIT_ID,         PLR_SST_PP_DEMOTED_CORES_ID,         PLR_RACL_ID,         // Legacy TRL limit reason         PLR_LEGACY_TRL_ID,         // Acode limit reasons         PLR_ACODE_FREQ_ID,         PLR_ACODE_CURRENT_ID,         PLR_ACODE_THERMAL_ID, //jasoncwa: this is the data from acode self throttling         PLR_ACODE_RAS_ID,         // TRL CDYN limit reasons         PLR_TRL_CDYN0_ID,         PLR_TRL_CDYN1_ID,         PLR_TRL_CDYN2_ID,         PLR_TRL_CDYN3_ID,         PLR_TRL_CDYN4_ID,         PLR_TRL_CDYN5_ID,         // Num elements         NUM_CCP_DETAILED_PLR_ID     }; # This is the PLR variable that should contain the acode thermal report. The index is the CCP ID. # Bit 26 should be PLR_ACODE_THERMAL_ID sv.socket0.cbb0.pcode.vars.plr.detailed_ccp_plr.show() # This is the register acode should be writing to inform pcode of the thermal throttling: sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit.thermal If PER_CORE_THERMAL should be set on acode self throttling, seems like pcode should be ORing detailed_ccp_plr[PLR_EMTTM_CCP_ID] and detailed_ccp_plr[PLR_ACODE_THERMAL_ID

### Tags
FV_PM,cdgmdt.pm,SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_6000097E,FIX_IFWI_DMR_AP1_2025.47.4.01,BKC#OKS_DMR_AP_X1_2025WW48,FIX_BKC_OKS_DMR_AP1_2025WW48, PSF=Y,dmr_neg

### Conclusion
fw.bug

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

- **Primary Feature**: Platform PM Interface
- **Sub-Feature**: TPMI
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x19c`
- `sv.socket0.cbb0.compute1.module9.core0.virtual_msr_cr_pm_logical_id`
- `sv.socket0.cbb0.compute1.pma9.pmsb.dfvfcr_dts_fuse_0.cr_reg36_inst.digthermovrden`
- `sv.socket0.cbb0.compute1.pma9.pmsb.dfvfcr_dts_fuse_0.cr_reg36_inst.digthermovrdval`
- `sv.socket0.cbb0.compute1.modules.core0.ucode_cr_therm_status`
- `sv.socket0.cbb0.base.tpmi.plr_die_level.data`

## Timeline

- **Submitted**: 2025-10-22 05:26:46
- **Root Caused**: 2025-11-07 03:28:09
- **Closed**: 2025-12-29 05:37:29
- **Days Open**: 68

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
