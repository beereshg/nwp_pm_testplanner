# HSD 22021941705: [DMR][X1 A0] Rse_configuration & threshold/ Weights not configured properly impact Ring Scalability AI Model output

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22021941705](https://hsdes.intel.com/appstore/article-one/#/22021941705) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | dlevy1 |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | PState Stack | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

2 findings impact the output of the Ring scalability AI model:

1) Finding #1: The DMR PO Ring scalability model weights & thresholds were set based on some engineering judgment. 

With the DMR PO values, the Ring= Core Freq even when running WL like Leela that is expected to benefit from the Ring freq reduction. 

However, when setting LNL values, the model is shown to be over-reactive.  A 
10 bin Core to Ring freq delta is shown for 

ALL

 WLs (even for WL like omnetpp that requires higher Ri

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww2.1]

The team discussed tuning the ring scalability feature, identified configuration mismatches, outlined steps for model retraining, and emphasized the need for improved validation and documentation for future projects.

David J described that the ring scalability feature exhibited unexpected core-to-ring frequency deltas due to misconfigured weights, thresholds, and LLC configuration parameters, which were corrected by aligning with previous project settings.

Ido and Srihari stressed the importance of understanding how the configuration bug was introduced and how such issues can be detected earlier, advocating for improved pre-silicon validation and proactive reviews.

Ido requested that David J and the team document the tuning process and learnings to facilitate smoother transitions and reduce turnaround time for similar features in future projects.

Model Retraining Process: Srihari outlined a multi-step process: collecting data for the AI team, retraining the model for server workloads and DMR configuration, and iteratively refining the model based on observed behavior, with tracking via HSDs.

### Description
2 findings impact the output of the Ring scalability AI model:

1) Finding #1: The DMR PO Ring scalability model weights & thresholds were set based on some engineering judgment. 

With the DMR PO values, the Ring= Core Freq even when running WL like Leela that is expected to benefit from the Ring freq reduction. 

However, when setting LNL values, the model is shown to be over-reactive.  A 
10 bin Core to Ring freq delta is shown for 

ALL

 WLs (even for WL like omnetpp that requires higher Ring Freq).

2)  PMON were pulled while running leelah &  Omnetto. Analysis done by the AI Team shows that there is no risk of wrong PMON HW behavior apart on TOR occupancy looks to be too high.

This parameter is directly impact by the ring 

3) Finding #2: RSE Configuration

After a discussion with the AI Team & Designer, it was understood that the rse_configuration size 16k as expected but 2k.

When moving from 2k  ring scale cycle (rse_config =0) to 16k  ring scale cycle (rse config =3) 
AND 
running with the LNL Model: 

the behavior is as expected:  

3) Aging_cfg register:  

It 
Indicates how much the previous grade affects the new grade (max is 15 of 16)  (smoothing)

On PTL, it was set as 6, on DMR, it's 4:

While running Omnettp, 

 

The distress_factor is impacted when reducing it to 4 (Bimodal distribution); Still there is no impact on the Core to Ring frequency delta.

While running Leelah, the behavior is more noisy.

 

Need fine tuning of this parameter.

Bottom Line:

1) The Weights & Threshold of the AI model have to be matched to the LNL model . THe following patch was checked: 

https://af01p-igk.devtools.intel.com/artifactory/pcode_lnl-igk-local/Debug_packages/CBB/production_encrypted_private/PCODE_CBB_A0_k53a943dbf89c7b34_s5f53a8b_Private_reing_scal_on_rev22.1.26.0_ver0.zip  

2) The rse_configuration as to be updated to 3:

sv.socket0.cbb0.base.i_ccf_env3.sbo_misc_regs.sbo_ring_scale_weights_misc.rse_configuration = 3

sv.socket0.cbb0.base.i_ccf_env0.sb

### Comments (latest)
++++22611669755 mbfausto
If these are 3? different issues, please file TWO sightings (and not cloning them so they are in the same HSD set).  each issue/defect/mitigation is tracked separately. 1) 1) Finding #1: The DMR PO Ring scalability model weights & thresholds were set based on some engineering judgment. So is this a modelling issue?  These are not tracked/resolved/addressed in Silicon Sightings. 2)  PMON were pulled while running leelah &  Omnetto. Analysis done by the AI Team shows that there is no risk of wrong PMON HW behavior apart on TOR occupancy looks to be too high. This looks again like a modelling/test run issue and not a HW/FW defect.  Correct? 3)  The Rest Are you indicating there are *register programming values that BIOS/FW should default to different values* or just that you needed to set them differently for your Perf KPI testing? Please help us understand, if these 3 issues are all configurations for your testing or models, this sighting is to be rejected.  If you are indicating that there are DMR value programmed that should be changed in BIOS/FW as a result of Tuning or a spec mismatch, please identify whether its an implementation issue (what DMR spec says value A but we are programming/seeing value B) ... or help identify the spec where we want to UPDATE the value for DMR.

++++22611669756 mbfausto
Updating to vt.perf and val.env  ... as at this point this appears to be a PTP tuning issue and model issue and not a PM HW/FW issue or a Perf arch gap.  Awaiting more information before changing again.
++++1363548720 dlevy1
The Pcode patch containing the required changes was provided: Package is ready to be uploaded to the artifactory. Production encrypted, debug signed file uploaded successfully to: https://af01p-igk.devtools.intel.com/artifactory/pcode_lnl-igk-local/Debug_packages/CBB/production_encrypted_private/PCODE_CBB_A0_kda6fa7371337e56b_s5f53a8b_Private_ring_scal_params_on_rev22.1.26.0_ver1.zip All the required parameters were updated, including the rse_configuration: s.  
++++14614964906 vwang
Confirmed with David J, the test was done on a VIS part and works fine now. So we can root cause this to 13014331309

++++14614964919 vwang 
.

++++14614964917 vwang
.

++++14614964916 vwang
.

++++14614964915 vwang
.

++++14614964914 vwang
.

++++14614964912 vwang
.
++++22611786326 mbfausto
[SysDebug] The FW ticket (id=13014331309) cloned from this sighting has been fixed and released in ingredient version "DMR_A0_60000993" on [SysDebug] Sighting tag appended with "FIX_PATCH_DMR_A0_60000993" [SysDebug] [SysDebug] The Sighting owner (dlevy1) may be enabled to validate the fix is working in the released collateral.

++++22611786330 mbfausto
[SysDebug Tag Script] IFWI version "DMR_AP_2026.09.3.04" has been released that contains the component release "FIX_PATCH_DMR_A0_60000993" [SysDebug Tag Script] Sighting tag appended with "FIX_IFWI_DMR_AP_2026.09.3.04"
++++1363599412 dlevy1
(1) I have verified it on a released IFWI/ingredi

### Tags
SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_60000993,FIX_IFWI_DMR_AP1_2026.09.3.04,BKC#OKS_DMR_AP_X1_2026WW10_INT,FIX_BKC_OKS_DMR_AP1_2026WW12

### Conclusion
fw.arch

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: general
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbb0.base.i_ccf_env3.sbo_misc_regs.sbo_ring_scale_weights_misc.rse_configuration`
- `sv.socket0.cbb0.base.i_ccf_env0.sbo_misc_regs.sbo_ring_scale_weights_misc.rse_configuration`
- `sv.socket0.cbb0.base.i_ccf_env1.sbo_misc_regs.sbo_ring_scale_weights_misc.rse_configuration`
- `sv.socket0.cbb0.base.i_ccf_env2.sbo_misc_regs.sbo_ring_scale_weights_misc.rse_configuration`

## Timeline

- **Submitted**: 2025-12-31 01:17:52
- **Root Caused**: 2026-01-14 11:51:44
- **Closed**: 2026-03-09 19:09:15
- **Days Open**: 68

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
