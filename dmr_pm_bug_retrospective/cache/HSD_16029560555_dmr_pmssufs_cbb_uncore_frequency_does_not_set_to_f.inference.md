# HSD 16029560555: [DMR_PMSS][UFS] CBB uncore frequency does not set to floor value and operates at 2200 most of the times due to ELC thresholds being 0

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029560555](https://hsdes.intel.com/appstore/article-one/#/16029560555) |
| **Status** | complete.broken |
| **Priority** | 3-medium |
| **Owner** | sagrawa3 |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Fabric DVFS | 52% |
| **Sub-Feature** | Uncore Freq | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Expectation:

CBB uncore frequency does not set to floor value(0x8) and operates at 2200 most of the times when in IDLE.

The default value of Thresholds(Low and High) as per HAS is as follows:

Observation:

Ring(CBB) Pcode uncore frequency thresholds are always 0x0 even when the LOM is disabled, But the IMH primecode sets the correct thresholds.

CBB:

IMHs:(Memory and IO Fabric)

UFS tpmi register:

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww08.3]

Timothy advocated for BIOS to handle all initialization of ELC-related fields to avoid non-uniform behavior, with the BIOS team confirming their ability to implement the requested changes.

[26ww3.3]

Latest results shows that primecode is initializing the values but pcode is not. Thresholds are not BIOS responsibility, it needs to come from pcode. Next step is to get pcode/Timothy input. Shubham/Abhinad will start Timothy conversation and follow up with pcode if needed. 

[26ww3.1]

Shubham described that CBB ELC thresholds are zero even when latency optimized mode is disabled, while IMH thresholds are correctly set, prompting a review of register values and BIOS behavior.

Timothy and Ido clarified that the default value is zero and BIOS is responsible for programming the correct thresholds based on the latency optimized mode setting.

Abhinand and others agreed to check the register values before and after BIOS execution to confirm if BIOS is missing the programming step for CBB, and Timothy will consult the specification and coordinate with the BIOS team.

### Description
Expectation:

CBB uncore frequency does not set to floor value(0x8) and operates at 2200 most of the times when in IDLE.

The default value of Thresholds(Low and High) as per HAS is as follows:

Observation:

Ring(CBB) Pcode uncore frequency thresholds are always 0x0 even when the LOM is disabled, But the IMH primecode sets the correct thresholds.

CBB:

IMHs:(Memory and IO Fabric)

UFS tpmi register:

### Comments (latest)
++++1667203694 aamarna1 
Register and issue details are present in the description of the HSD , we spoke to Tamir and Sagar and we are unclear as to who has to program the CBB UFS ELC threshold registers. We checked the register at CPL1 and at UEFI IMH side ELC thresholds are programmed while CBB side it is 0 ; due to which CBB uncore ring frequency is always running at 2200 MHz even at idle.  Further checked pcode , tamir too did check what we see is that pcode is just reading the UFS Control register there is no mention of initialization in pcode. So need to know if its primecode which has to program CBB fabric register too so that pcode can use the values.  Functionally when we program the ELC thresholds manually via TPMI CBB ring frequency comes down and works as expected. This HSD to understand what should be the default value coming out of reset because HAS mentions it should be 10% and 95% for all 3 uncore fabrics. If this is intentional or not and is pcode responsible to program these registers is a question to be answered.  In [3]:  sv.socket0.cbb0.base.tpmi.ufs_control.show() 0x00000000 : rsvd4 (63:47) (rw) -- Reserved 0x00000000 : efficiency_latency_ctrl_high_threshold (46:40) (rw) -- Utilization point above which freq will be optim...</span> 0x00000000 : efficiency_latency_ctrl_high_threshold_enable (39:39) (rw) -- If set (1), EFFICIENCY_LATENCY_CTRL_HIGH_...</span> 0x00000000 : efficiency_latency_ctrl_low_threshold (38:32) (rw) -- This field provides the flexibility to alter the ... 0x00000000 : rsvd2 (31:30) (rw) -- Reserved 0x00000000 : idle_power_ctrl_disable (29:29) (rw) -- When set this bit disables efficient power saving modes during ... 0x00000008 : efficiency_latency_ctrl_ratio (28:22) (rw) -- Fabric domain frequency ratio floor while in the low powe... 0x00000008 : min_ratio (21:15) (rw) -- Min fabric domain frequency ratio 0x0000001b : max_ratio (14:08) (rw) -- Max fabric domain frequency ratio 0x00000000 : rsvd1 (07:02) (rw) -- Reserved 0x00000001 : ufs_throttle_mode (01:00) (rw) -- Select one of the UFS throttle modes In [4]:  sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_control.show() 0x00000000 : rsvd4 (63:47) (rw) -- Reserved 0x00000078 : efficiency_latency_ctrl_high_threshold (46:40) (rw) -- Utilization point above which freq will be optim...</span> 0x00000001 : efficiency_</span>latency_ctrl_high_threshold_enable (39:39) (rw) -- If set (1), EFFICIENCY_LATENCY_CTRL_HIGH_... 0x0000000d : efficiency_latency_ctrl_low_threshold (38:32) (rw) -- This field provides the flexibility to alter the ... 0x00000000 : rsvd2 (31:30) (rw) -- Reserved 0x00000000 : idle_power_ctrl_disable (29:29) (rw) -- When set this bit disables efficient power saving modes during ... 0x00000008 : efficiency_latency_ctrl_ratio (28:22) (rw) -- Fabric domain frequency ratio floor while in the low powe... 0x00000004 : min_ratio (21:15) (rw) -- Min fabric domain frequency ratio 0x00000015 : max_ratio (14:08) (rw) -- Max fabric domain frequency ratio 0x000

### Tags
SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_6000098D,FIX_IFWI_DMR_AP1_2026.05.4.01,BKC#OKS_DMR_AP_X1_2026WW08,FIX_BKC_OKS_DMR_AP1_2026WW07

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

- **Primary Feature**: Fabric DVFS
- **Sub-Feature**: Uncore Freq
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI CBB`
- `TPMI Register`
- `TPMI UFS`
- `TPMI registers`
- `TPMI register`
- `sv.socket0.cbb0.base.tpmi.ufs_control.show`
- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_control.show`
- `sv.socket0.imh0.pcodeio_map.io_bios_reset_cpl.show`
- `sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.ufs_control.efficiency_latency_ctrl_low_threshold`
- `sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.ufs_control.efficiency_latency_ctrl_high_threshold`

## Timeline

- **Submitted**: 2026-01-07 21:43:19
- **Root Caused**: 2026-02-23 22:56:12
- **Closed**: 2026-02-24 02:40:09
- **Days Open**: 47

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
