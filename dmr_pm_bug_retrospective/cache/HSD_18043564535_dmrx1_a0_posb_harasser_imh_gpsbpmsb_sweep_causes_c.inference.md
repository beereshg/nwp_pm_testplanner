# HSD 18043564535: [DMR][X1 A0 PO][SB Harasser] IMH GPSB/PMSB Sweep causes core MCA Hang with OCODE on APB Endpoints.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [18043564535](https://hsdes.intel.com/appstore/article-one/#/18043564535) |
| **Status** | complete.wont_validate |
| **Priority** | 2-high |
| **Owner** | dlerner |
| **Component** | hw.dfx |
| **Defect Die** | ioe |
| **Conclusion** | doc |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 75% |
| **Feature** | Sideband/D2D | 80% |
| **Sub-Feature** | GPSB | — |

**Reasoning**: errata_status='review_waived' → HW

## Root Cause Summary

Collaterals
:

Platform: 

SC00901159H0033.amr.corp.intel.com

JF53NOR09BN0304.amr.corp.intel.com

IFWI: 

WW39.3 - 
OKSDCRB1_86B_2025.39.1.01_2754.D13_60000968_0.609.0_1P0_NonIPClean_Trace_DebugSigned.bin

WW40.1 -  OKSDCRB1_86B_2025.39.4.01_2787.D05_6000096B_0.614.0_1P0_NonIPClean_Trace_DebugSigned_2S_SSCDis_UXI16_IOMMUDis_UXIL1dis.bin

Summary
:

Able to reproduce this issue on 2 platforms.

While running SB Harasser with Ocode we are hitting core MCA Hang.

Status scope dump - https://axonsv

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww41.1]

While debugging 

an issue in the debug register definition, we found this is a register spec bug in
 

fsa_pardfd1_APB
.  the struct type should be NSIP2APB_FSA_RTDR_STRUCT instead of FSA_RTDR_STRUCT.
Vidar will clone this to a SoC spec bug.

### Description
Collaterals
:

Platform: 

SC00901159H0033.amr.corp.intel.com

JF53NOR09BN0304.amr.corp.intel.com

IFWI: 

WW39.3 - 
OKSDCRB1_86B_2025.39.1.01_2754.D13_60000968_0.609.0_1P0_NonIPClean_Trace_DebugSigned.bin

WW40.1 -  OKSDCRB1_86B_2025.39.4.01_2787.D05_6000096B_0.614.0_1P0_NonIPClean_Trace_DebugSigned_2S_SSCDis_UXI16_IOMMUDis_UXIL1dis.bin

Summary
:

Able to reproduce this issue on 2 platforms.

While running SB Harasser with Ocode we are hitting core MCA Hang.

Status scope dump - https://axonsv.app.intel.com/apps/record-viewer/01997b10-752a-7520-b37e-8487c0ac40de?tab=summary

Steps to Reproduce:

import diamondrapids.pm.SB_Harasser.sb_harasser_DMR as hr

hr.run_harasser_loop(interval = 10, t_time = 900, die_id=[8], pcode=0, ocode=1)

### Comments (latest)
++++1862463968 jzlevule
<div>When the failure is completely unknown, the submitter's domain must be used when filing sub_forum as a starting point.&nbsp; Please start doing this automatically when filing a Pre-Sighting</div><div><br /></div>

++++1862463969 dlerner
<p>This looks like an issue in the debug register definition, not a real hang scenario. The sideband adapters connecting to APB (aka NSIP2APB) have different debug registers compared to the normal IOSF-SB FSAs, but certain instances of NSIP2APB do not reflect that. For example:</p><p><br /></p><div><span style="font-family: &quot;Courier New&quot;;">sv.socket0.imh0.taps.parsochmcbotleft0.fsa_pardfd1_apb.fields</span></div><div><span style="font-family: &quot;Courier New&quot;;">Out[5]:</span></div><div><span style="font-family: &quot;Courier New&quot;;">['dummy_lo',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'pc_tx_pending',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'barrier_pending',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'pcq_trk_full',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'pc_rx_sb_pending',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'pc_rx_nsip_pending',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'np_tx_pending',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'pc_np_lut_error',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'pc_np_mcast_detected',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'mcast_agg_pending',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'pc_np_mcast_error',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'pc_np_8b_16b_error',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'np_rx_sb_pending',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'np_rx_nsip_pending',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'np_or_barrier_ack_pending',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'np_cntr_ovrf_udrf',</span></div><div><span style="font-family: &quot;Courier New&quot;;">&nbsp;'ism_idle']</span></div><div><span style="font-family: &quot;Courier New&quot;;"><br /></span></div><div><span style="font-family: Arial;">The fields should instead look like this:</span></div><div><span style="font-family: Arial;"><br /></span></div><p></p><div><font face="Arial"><span style="font-family: &quot;Courier New&quot;;">sv.socket0.imh0.taps.parsoccenter10.fsa_apb_serializer_center1_vinf_apb.fields</span></font></div><div><div style=""><font face="Arial"><span style="font-family: &quot;Courier New&quot;;">Out[6]:</span></font></div><div style=""><font face="Arial"><span style="font-family: &quot;Courier New&quot;;">['dummy_lo',</spa

### Tags
SysDebugCloned,SysDebugDccbBypass,FV_PM,DMR_Manageability_BEAT,FV_SB_HARASSER

### Conclusion
doc

### Component
hw.dfx

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
- **Component Path**: hw.dfx

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.taps.parsochmcbotleft0.fsa_pardfd1_apb.fields`
- `sv.socket0.imh0.taps.parsoccenter10.fsa_apb_serializer_center1_vinf_apb.fields`

## Timeline

- **Submitted**: 2025-10-04 01:04:51
- **Root Caused**: 2025-10-07 01:22:31
- **Closed**: 2025-10-22 20:47:08
- **Days Open**: 18

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
