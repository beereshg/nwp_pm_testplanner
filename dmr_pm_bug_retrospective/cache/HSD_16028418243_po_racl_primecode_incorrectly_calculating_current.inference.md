# HSD 16028418243: [PO] [RACL]: Primecode incorrectly calculating current spikes causing unexpected RACL Limit to be hit

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16028418243](https://hsdes.intel.com/appstore/article-one/#/16028418243) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | salmanha |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Platform PM Interface | 52% |
| **Sub-Feature** | PECI | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

The HSD is filed to work on the Recipe and Tune the IMH PRIMECODE RACL PID on DMR silicon. The Current Default Tuning with Fused TDC Set ~115A is showing RACL Limit to be hit and Core Frequency is at Min.

WA recommended for Team while RACL tuning is not completed and waiting for Official PCODE:

sv.socket0.imh0.pcudata.io_racl_enabled=0
 

(Recommended) /OR/

Override the RACL_TDC with pcudata to as high as 14000-20000 (Part/Platfrom specific variation is observed)

Observations similar to HSD:

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
Failing Signature: 
 
The HSD is filed to work on the Recipe and Tune the IMH primecode RACL PID on DMR silicon

[WW37.2]

Title looks strange 

Do we expect this to be fined tuned? 

Is this a power blocker, seems like no, please confirm 
Shreayas provide a debug patch 
New feature for DMR 
WHat is the impact for this? <We have a recipe to disable this in case someone hits the problem >

Next)Shreyas/PM team )
 Start the iteration process

### Description
The HSD is filed to work on the Recipe and Tune the IMH PRIMECODE RACL PID on DMR silicon. The Current Default Tuning with Fused TDC Set ~115A is showing RACL Limit to be hit and Core Frequency is at Min.

WA recommended for Team while RACL tuning is not completed and waiting for Official PCODE:

sv.socket0.imh0.pcudata.io_racl_enabled=0
 

(Recommended) /OR/

Override the RACL_TDC with pcudata to as high as 14000-20000 (Part/Platfrom specific variation is observed)

Observations similar to HSD: https://hsdes.intel.com/appstore/article-one/#/article/22021531862

Collaterals
:

Platform: SC00901159H0006.amr.corp.intel.com

IFWI:
 

\\amr.corp.intel.com\ec\proj\debug\DMR\User\agraback\primecode_patch_ww35p2_UlaPoisonDis_UlaSkipEn_NewRev_pr10238_v3\OKSDCRB1.86B.2025.34.4.04_2654.D12_7000094D._1P0_NonIPClean_Trace_DebugSigned_405800F1_202508270750.bin

Summary
:

Seeing large variations in current consumption at both IMH level, causing RACL_PERF_STATUS counter to run freely without any WL. 

TDC fuse values are set to 115A

In :  sv.socket0.imhs.fuses.punit.pcode_tdc_current_limit
 

socket0.imh0.fuses.punit.pcode_tdc_current_limit - 0x00000073

socket0.imh1.fuses.punit.pcode_tdc_current_limit - 0x00000073

### Comments (latest)
++++1666963054 salmanha
<p>Platform:&nbsp;SC00901159H0006.amr.corp.intel.com</p><p>IFWI:\\amr.corp.intel.com\ec\proj\debug\DMR\User\agraback\primecode_patch_ww35p2_UlaPoisonDis_UlaSkipEn_NewRev_pr10238_v3\OKSDCRB1.86B.2025.34.4.04_2654.D12_7000094D._1P0_NonIPClean_Trace_DebugSigned_405800F1_202508270750.bin</p><p><br /></p><p>Observing that RACL_PERF_STATUS is stopping when RACL_TDC limit is increased to a very high value</p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/16028327878" style="width: 1046px;" /><br /></p><!--StartFragment--><!--EndFragment-->

++++1666963055 salmanha
<p>Issue is reproduced on FUSED silicon.</p><p>Platform:&nbsp;SC00901159H0032.amr.corp.intel.com</p><p>IFWI:&nbsp;<a href="file://amr/ec/proj/debug/DMR/Tools/IFWI/Approved/UCC_A0/OKSDCRB1.86B.2025.35.3.01_2688.D02_6020095E_1P0_NonIPClean_Trace_DebugSigned_update_primecode_pcode.bin" style="font-family: Roboto, Arial, sans-serif; background-color: rgb(255, 255, 255); font-weight: 400;">\\amr\ec\proj\debug\DMR\Tools\IFWI\Approved\UCC_A0\OKSDCRB1.86B.2025.35.3.01_2688.D02_6020095E_1P0_NonIPClean_Trace_DebugSigned_update_primecode_pcode.bin</a></p><p><br /></p><p><b>With Default TDC values: PERF_STATUS is incrementing continuously.</b></p><p style="margin:0in;font-family:Calibri;font-size:11.0pt"><img src="https://hsdes.intel.com/rest/binary/16028340807" style="width: 873px;" /></p><p style="margin:0in;font-family:Calibri;font-size:11.0pt"><img src="https://hsdes.intel.com/rest/binary/16028340808" style="width: 50%;" data-processed="true" /></p><p style="margin:0in;font-family:Calibri;font-size:11.0pt"><br /></p><p style="margin:0in;font-family:Calibri;font-size:11.0pt"><br /></p><p style="margin:0in;font-family:Calibri;font-size:11.0pt"><b>Changing limit: PERF_STATUS becomes constant</b></p><p style="margin:0in;font-family:Calibri;font-size:11.0pt"><img src="https://hsdes.intel.com/rest/binary/16028340809" style="width: 50%;" data-processed="true" /><br /></p>

++++1666963056 salmanha
<p>Observing core Pm freq reaching 1.3GHz when TDC is increased to a very high value.</p><p><!--StartFragment--><img src="https://hsdes.intel.com/rest/binary/16028380753" style="width: 50%;" data-processed="true" /><!--EndFragment--></p>

++++1666963057 shreyasu
<p>I've created a debug patch that has increased visibility into RACL. You can find the files here:<br /></p><p><br /></p><p>Debug Unified Patch:&nbsp;\\SCCV69A-CIFS.sc.intel.com\dcsg_0729\users\vdc\DMR\prod\4058013E</p><p>IFWI and Pcudata Collateral: \\amr.corp.intel.com\ec\proj\debug\DMR\User\shreyasu\racl_pid_tuning\OKSDCRB1_86B_2025.36.6.01_2704.D08_60000964_0.595.0_1P0_NonIPClean_Trace_DebugSigned_MonitorMwaitEnable_4058013E_202509090603.bin</p><p><br /></p><p>The following are the new pcudata variables that have been added to the debug patch:</p><p><br /></p><p>racl_instantaneous_current&nbsp;</p><p>racl_current_budget</p><p>racl_prev_budget</p><p>racl_tele_accum_current</p><p>racl_tele_num_samples&nbsp;</p><p><!-

### Tags
FV_PM_BDC,FW_BUG,DMR_A0_PO,IMH_FW,SysDebugCloned,SysDebugDccbBypass,TEMP_WA_PATCH_DMR_AP1_A0_6000096F_POWERON,FWTF_PO_UNBLOCKED,FV_PM,FIX_PATCH_DMR_AP1_A0_6000097B,FIX_IFWI_DMR_AP1_2025.45.4.02,FIX_BKC_OKS_DMR_AP1_2025WW46,PSF=N

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

- **Primary Feature**: Platform PM Interface
- **Sub-Feature**: PECI
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.pcudata.io_racl_enabled`
- `sv.socket0.imhs.fuses.punit.pcode_tdc_current_limit`
- `sv.socket0.imh0.pcudata.racl_instantaneous_current`

## Timeline

- **Submitted**: 2025-09-09 10:25:50
- **Root Caused**: 2025-09-16 22:07:46
- **Closed**: 2025-11-18 03:51:49
- **Days Open**: 69

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
