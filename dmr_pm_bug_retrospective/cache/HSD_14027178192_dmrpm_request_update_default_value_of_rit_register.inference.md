# HSD 14027178192: [DMR][PM] Request update default value of RIT registers tpmi.fit_config_0/1

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027178192](https://hsdes.intel.com/appstore/article-one/#/14027178192) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | dlwu |
| **Component** | hw.power |
| **Defect Die** | ioe |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | PState Stack | 52% |
| **Sub-Feature** | TRL | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

1) We are requesting update of the default value of these two RIT-related registers.

sv.sockets.cbbs.base.tpmi.fit_config_0

sv.sockets.cbbs.base.tpmi.fit_config_1

2) These two registers are currently set to 0x0, which causes RIT to throttle all workloads to TRL0 levels, causing significant performance degradation.

3) We are requesting they be updated to the RIT legacy value of all F's (16 F's total):

sv.sockets.cbbs.base.tpmi.fit_config_0 = 0xFFFFFFFFFFFFFFFF

sv.sockets.cbbs.base.tpmi.fit_

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
1) We are requesting update of the default value of these two RIT-related registers.

sv.sockets.cbbs.base.tpmi.fit_config_0

sv.sockets.cbbs.base.tpmi.fit_config_1

2) These two registers are currently set to 0x0, which causes RIT to throttle all workloads to TRL0 levels, causing significant performance degradation.

3) We are requesting they be updated to the RIT legacy value of all F's (16 F's total):

sv.sockets.cbbs.base.tpmi.fit_config_0 = 0xFFFFFFFFFFFFFFFF

sv.sockets.cbbs.base.tpmi.fit_config_1 = 0xFFFFFFFFFFFFFFFF

### Comments (latest)
++++14615122237 vwang
[CloneScript] PreSighting 14027177997 cloned to Sighting 14027178192
++++22611783926 imelamed
I want to clarify that this issue stems from an incorrect default value selected by the previous architect (who has since left Intel). I am requesting BIOS support to override these values appropriately until the feature can be updated or redefined, as there are several other related issues.
++++1566857761 lzeng14
BIOS has been following https://docs.intel.com/documents/pm_doc/src/server/DMR/DCM%20PNC%20PM%20HAS/RIT.html#bios-interface to provide BIOS knobs "RIT Opt-In" and "FVT (Frequency Variability Tolerance)" with default No and 0. The request is to make the knobs default to Yes and 15 ?  @Melamed, Ido  @Chen, Stanley  Shouldn't the best way of updating the internal default be done by primecode/pcode ? BTW: Why "2) These two registers are currently set to 0x0, which causes RIT to throttle all workloads to TRL0 levels, causing significant performance degradation." ? And which scenario will the value 0 need to be configured for ?
++++14615129711 vwang
Escalated to HIGH We need this change included in ES1, and we should also validate that the workaround functions as expected.

++++14615129744 dlwu
The request is to make the knobs default to No and 15.
++++22611788249 mbfausto
Have we used PythonSV to override the value and checkout perf/functionality/etc. to make sure no fallout?  Have we asked for a Test BIOS? Also I see this line  "until the feature can be updated or redefined, as there are several other related issues" ... so do we expect these values to change soon or we should go ahead and mitigate NOW as those will take long?  Since HIGH (and ES1 impacting), are we sayign that the current values are detrimental, and future tuning will be "better" but we need to do something now as the current values are quite poor and far away from expectations?

++++22611789354 imelamed
Let me clarify the request: We are observing a 5–15% performance loss for SIR/SFR workloads when using FVT=0x0. When FVT is overridden to 0xF for all cores, the performance loss is recovered. Below are the results collected by post-silicon (Raj), and I’ve also attached the Excel file. The request to BIOS is not to change the default values in the BIOS menu, but instead to patch the TPMI registers as if the user had opted in and set FVT=0xF. Specifically, for each CBB, BIOS should write: FIT_CONFIG_0 = 0xFFFFFFFF FIT_CONFIG_1 = 0xFFFFFFFF This is a short-term solution for ES1 until the PM Architecture team implements all necessary changes to fully resolve the issue. A long-term solution may require an updated TPMI release, which could take significantly longer. Additionally, the long-term fix depends on several ongoing changes to this feature. Component Avg Score Avg Score Avg Score Avg Score Avg Score Avg Score Avg Score Avg Score Avg Score New Thresholds + Short PVP Disabled New Thresholds + Short PVP Dis + RIT DIS (FVT=15) New Thresold + Long PVP Enabled + 

### Tags
BIOS_MS_PRE_ALPHA,SysDebugCloned,SysDebugCloned,SysDebugDccbDone,SysDebugDccbDriver,FIX_PATCH_DMR_AP1_A0_60000997,FIX_IFWI_DMR_AP1_2026.11.3.03,BKC#OKS_DMR_AP_X1_2026WW12_INT,FIX_BKC_OKS_DMR_AP1_2026WW14

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: TRL
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI registers`
- `TPMI release`

## Timeline

- **Submitted**: 2026-02-26 03:31:25
- **Root Caused**: 2026-03-04 00:30:01
- **Closed**: 2026-04-29 20:29:11
- **Days Open**: 62

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
