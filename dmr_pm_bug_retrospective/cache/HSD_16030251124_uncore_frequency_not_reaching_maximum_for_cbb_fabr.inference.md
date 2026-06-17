# HSD 16030251124: Uncore frequency not reaching maximum for CBB fabric when LoM is enabled

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16030251124](https://hsdes.intel.com/appstore/article-one/#/16030251124) |
| **Status** | root_caused.validating |
| **Priority** | 2-high |
| **Owner** | sagrawa3 |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | PState Stack | 80% |
| **Sub-Feature** | TRL | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Expectation:

As per HAS 
https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html#lom-and-opm
,When ELC is disabled aka LOM enabled, the High thresholds and the low thresholds should be 0 and hence the Uncore frequency for all CBB fabric should be at max.

Problem Statement:

When we enabled LOM via BIOS knob, the ELC thresholds(both low and high) are 0 but still the frequency is not reaching to max(In this case 0x1b - 2700).

This scenario is only seen for PCOD

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
Pending on test of the patch from pCode

﻿[26ww16.1]

In order to prove the theory, Tamir is working pCode test patch

﻿[26ww15.4]

The team analyzed a potential issue with the ELC algorithm in LOM mode, discussed the expected behavior, identified a possible bug in the pCode implementation or BIOS settings, and agreed to collect further data using a pTracker for root cause analysis.

ELC Algorithm Behavior: Anatoli raised concerns that the ELC algorithm may incorrectly enter the ELC low region in LOM mode, despite both thresholds being set to zero. Timothy explained that, by design, this should not occur, and if it does, it indicates a bug.

Spec and Implementation Review: Timothy and Anatoli reviewed the pseudo code and spec, noting a minor critique of the logic of &quot;ELC Mode Selection&quot;(an 'else if' should be 'less than' rather than 'less than or equal'), but concluded this should not affect the observed behavior. The group agreed the issue is likely in the pCode implementation or BIOS configuration.

Next: Anatoli will coordinate with Yevgeni and Timothy, and Shubham will provide pTracker. The team will review the collected data to determine if the issue is with pCode or BIOS implementation, or the spec itself.

### Description
Expectation:

As per HAS 
https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html#lom-and-opm
,When ELC is disabled aka LOM enabled, the High thresholds and the low thresholds should be 0 and hence the Uncore frequency for all CBB fabric should be at max.

Problem Statement:

When we enabled LOM via BIOS knob, the ELC thresholds(both low and high) are 0 but still the frequency is not reaching to max(In this case 0x1b - 2700).

This scenario is only seen for PCODE(CBB fabric) and not for IMH.

UFS control TPMI register:

In [19]: sv.sockets.cbbs.base.tpmi.ufs_control.show()

0x00000008 : efficiency_latency_ctrl_mid_ratio (63:57) (rw) -- Fabric Ratio when utilization is higher than ELC_LOW_...

0x00000000 : rsvd4 (56:47) (rw) -- Reserved

0x00000000 
: efficiency_latency_ctrl_high_threshold (46:40) (rw) -- Utilization point above which freq will be optim...

0x00000001 
: efficiency_latency_ctrl_high_threshold_enable (39:39) (rw) -- If set (1), EFFICIENCY_LATENCY_CTRL_HIGH_...

0x00000000 
: efficiency_latency_ctrl_low_threshold (38:32) (rw) -- This field provides the flexibility to alter the ...

0x00000000 : rsvd2 (31:31) (rw) -- Reserved

0x00000000 : uniform_cbb_fabric_freq_mode (30:30) (rw) -- If enabled (set to 1), the compute fabric frequencies will...

0x00000000 : idle_power_ctrl_disable (29:29) (rw) -- When set this bit disables efficient power saving modes during ...

0x00000000 : efficiency_latency_ctrl_low_ratio (28:22) (rw) -- Fabric domain frequency ratio floor while in the low ...

0x00000008 : min_ratio (21:15) (rw) -- Min fabric domain frequency ratio

0x0000001b : max_ratio (14:08) (rw) -- Max fabric domain frequency ratio

0x00000000 : rsvd1 (07:02) (rw) -- Reserved

0x00000001 : ufs_throttle_mode (01:00) (rw) -- Select one of the UFS throttle modes

In [20]:  sv.sockets.imhs.punit.ptpcfsms.ptpcfsms.ufs_control.show()

0x00000004 : efficiency_latency_ctrl_mid_ratio (63:57) (rw) -- Fabric Ratio when utilization is h

### Comments (latest)
++++1667413799 sagrawa3
<p>Summary:</p><p style="box-sizing: border-box; margin: 0px; padding: 0px; color: rgb(0, 0, 0); font-family: Roboto, Arial, sans-serif; font-size: 14px; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; background-color: rgb(255, 255, 255); text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: initial;">As per HAS&nbsp;<a href="https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html#lom-and-opm" target="_blank" tabindex="-1" style="box-sizing: border-box; cursor: pointer; background-color: inherit; color: rgb(51, 122, 183); font-family: inherit; font-weight: inherit; text-decoration: inherit;">https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html#lom-and-opm</a>,When ELC is disabled aka LOM enabled, the ELC High thresholds and the ELC low thresholds should be 0 for both and hence the Uncore frequency for all CBB fabric should be at max.</p><p style="box-sizing: border-box; margin: 0px; padding: 0px; color: rgb(0, 0, 0); font-family: Roboto, Arial, sans-serif; font-size: 14px; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; background-color: rgb(255, 255, 255); text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: initial;"><br /></p><p style="box-sizing: border-box; margin: 0px; padding: 0px; color: rgb(0, 0, 0); font-family: Roboto, Arial, sans-serif; font-size: 14px; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; background-color: rgb(255, 255, 255); text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: initial;">When we enabled LOM via BIOS knob, the ELC thresholds(both low and high) are 0 but still the frequency is not reaching to max(In this case 0x1b - 2700).</p><p><!--StartFragment--><!--EndFragment--></p><p style="box-sizing: border-box; margin: 0px; padding: 0px; color: rgb(0, 0, 0); font-family: Roboto, Arial, sans-serif; font-size: 14px; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; background-color: rgb(255, 255, 255); text-decoration-thickn

### Tags
SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_600009A2,FIX_IFWI_DMR_AP1_2026.20.3.04

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
- **Sub-Feature**: TRL
- **Component Path**: fw.pcode

## Firmware Touchpoints

### BIOS
- `BIOS knob`

## Key Registers

- `TPMI register`
- `TPMI Register`

## Timeline

- **Submitted**: 2026-04-07 08:10:14
- **Root Caused**: 2026-04-17 20:42:05
- **Days Open**: 44

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
