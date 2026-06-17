# HSD 14027420071: [DMR][PM][DVFS] UNIFORM_CBB_FABRIC_FREQ feature is not working as expected

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027420071](https://hsdes.intel.com/appstore/article-one/#/14027420071) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | attran2 |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | PState Stack | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Experience: #1

1. Enable uniform_cbb_fabric_freq by either setting BIOS knob UniformCbbFabricFrequency to 1 or by writing to bit 30 of CBBs and IMHs UFS_CONTROL register

2. Set min_ratio of CBB0 to 0x10, other 3 CBBs left as min_ratio = 8.  

3. Check UFS_STATUS[current_ratio], expect all CBBs to have ratio 0x10 but instead only saw CBB0.current_ratio  = 0x10, others still had current_ratio =0x8

\

Experience #2:

1. Enable uniform_cbb_fabric_freq by either setting BIOS knob UniformCbbFabricF

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww13.1]

On-going debugging for 

HPM Agent ID 

is in progress with Pre-Si and Primecode teams.

[26ww12.4]

* No Post-Silicon Debug discussion, expecting initial feature checkout is done with IP / pre-silicon / emulation (or directly with post-si validation <--> Firmware coder  to iterate and get POC/proven working for initial checkout).
* NOT rejecting it right now, reproduced by PSS.  If execution makes progress / finds an issue / maintains there are FW issues and not usage/etc we can root-cause this and go.  IF  we find onion peeling or &quot;feature horribly broken&quot; needing initial enabling of the feature back and forth (val <--> IP) then we should do that bulk work as a pre-sighting or in PSS/IP versus post-silicon sighting/bug/rinse/repeat.
* Hector to follow up with Jeff on handling.

﻿[26ww12.3]

UNIFORM_CBB_FABRIC_FREQ: Joseph clarified UNIFORM_CBB_FABRIC_FREQ is a firmware-only feature for TPRQ, not hardware-dependent, and should be treated as medium priority, with validation deferred if pre-silicon validation is scheduled.

Alex confirmed that Kevin implemented the feature and suggested direct coordination with him for further debugging and validation, especially regarding observed issues with downstream ratios.

Hector and Joseph discussed whether validation of this feature would gate tape-in for C0, concluding that if all features are required to be validated, then it should be included in the validation plan.

### Description
Experience: #1

1. Enable uniform_cbb_fabric_freq by either setting BIOS knob UniformCbbFabricFrequency to 1 or by writing to bit 30 of CBBs and IMHs UFS_CONTROL register

2. Set min_ratio of CBB0 to 0x10, other 3 CBBs left as min_ratio = 8.  

3. Check UFS_STATUS[current_ratio], expect all CBBs to have ratio 0x10 but instead only saw CBB0.current_ratio  = 0x10, others still had current_ratio =0x8

\

Experience #2:

1. Enable uniform_cbb_fabric_freq by either setting BIOS knob UniformCbbFabricFrequency to 1 or by writing to bit 30 of CBBs and IMHs UFS_CONTROL register

2. Run high memory traffic workload

3. Check frequencies every few seconds: different frequencies shown across CBBs

### Comments (latest)
++++14615223043 jscanlo1 
Observing the same in PSS In simics RingPStates::hpm_downstream_ccf_resolved_min_ratio.value is always 0   (trace taken on CBB0) , either pcode thinks the feature is disabled, or Primecode is not sending any value? void RingPStates::handle_hpm_cbb_ccf_frequency(const hpm::HPM_MSG_CBB_CCF_FREQUENCY_t &msg) {     if (io::IO_UFS_CONTROL_t().read().get_UNIFORM_CBB_FABRIC_FREQ_MODE()==0) {         hpm_downstream_ccf_resolved_min_ratio = 0 ;     } else if (update_var(hpm_downstream_ccf_resolved_min_ratio , Ratio_t(msg.get_DOWNSTREAM_CCF_RESOLVED_MIN_RATIO()))) {         SIGNAL_EVENT(ring_pstate_run);     } } 
UFS_HEADER interface version is 0x3 across all dies
Bit 30 is set in UFS_CONTROL across all dies  (enabled through BIOS in my run)

++++14615223044 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14027388372.
++++22611809589 mbfausto
So we have the pcode and primecode register dumps, have looked at all the frequencies, confirmed all the enables that the BIOS knob should set, right?  Did you confirm that the feature is in fact enabled from FW's perspective?
++++14615224558 attran2
Few more observation: Scenario #1: biosknob UniformCbbFabricFrequencyMode=1. - Ran memical command that targeted only thread 0 (CBB0) (memicals -bind=0) - Saw CBB0.current_ratio = CCB2.current_ratio= CBB3.current_ratio = 0x11, CBB1.current_ratio = CBB1.min_ratio =0x8 - Disabled feature by clearing the uniform_cbb_farbric_frequency_mode in UFS_control - Saw CBB0.current_ratio=0x11, CCB1.current_ratio = CCB2.current_ratio = CBB3.current_ratio = 0x8   - Reneabled feafure by setting the uniform_cbb_farbric_frequency_mode in UFS_control - Saw CBB0.current_ratio = CCB2.current_ratio= CBB3.current_ratio = 0x11, CBB1.current_ratio = CBB1.min_ratio =0x8 Scenario 2:biosknob UniformCbbFabricFrequencyMode=0 - Enabled feature by setting  uniform_cbb_farbric_frequency_mode in UFS_control - Ran memical command that targeted only thread 0 (CBB0) (memicals -bind=0) - Saw CBB0.current_ratio = 0x11, CCB1.current_ratio= CBB2.current_ratio = CBB3.current_ratio = CBB1.min_ratio =0x8 -  What does BIOS knob setting do besides setting the uniform_cbb_fabric_frequency_mode bits in UFS_CONTROL?

++++14615224677 attran2 
Scenario #4: biosknob UniformCbbFabricFrequencyMode=1. - Ran memical command that targeted only thread 64 (CBB1) (memicals -bind=64) - Saw CBB1.current_ratio = CCB2.current_ratio= CBB3.current_ratio = 0x11, CBB0.current_ratio = CBB0.min_ratio =0x8 Looks like the DOWNSTREAM_CCF_RESOLVED_MIN_RATIO for CBB0 and CBB1 is always 0 Scenario #4: biosknob UniformCbbFabricFrequencyMode=1. - Ran memical command that targeted only thread 128 or thread 192 (CBB2 or CBB3) (memicals -bind=128/192) - Saw CCB2.current_ratio= CBB3.current_ratio = 0x11, CBB0.current_ratio = CBB1.current_ratio =  CBB0.min_ratio =0x8
++++22611812593 jscanlo1 
attached primecode + pcode trackers from simics Debug in progress w

### Tags
FV_PM,SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_6000099D,FIX_IFWI_DMR_AP1_2026.16.3.01,BKC#OKS_DMR_AP_X1_2026WW18,FIX_BKC_OKS_DMR_AP1_2026WW18

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: general
- **Component Path**: fw.primecode

## Firmware Touchpoints

### BIOS
- `BIOS knob`

## Key Registers

- `TPMI min`

## Timeline

- **Submitted**: 2026-03-18 01:21:46
- **Root Caused**: 2026-03-24 23:27:14
- **Closed**: 2026-04-29 21:53:13
- **Days Open**: 42

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
