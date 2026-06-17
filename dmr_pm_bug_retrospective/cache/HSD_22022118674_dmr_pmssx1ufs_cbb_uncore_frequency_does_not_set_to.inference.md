# HSD 22022118674: [DMR_PMSS][X1][UFS] CBB uncore frequency does not set to floor value(0x8) - BIOS Enhancement

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22022118674](https://hsdes.intel.com/appstore/article-one/#/22022118674) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | sagrawa3 |
| **Component** | bios |
| **Defect Die** | ioe |
| **Conclusion** | bios.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **BIOS** | 70% |
| **Feature** | Fabric DVFS | 52% |
| **Sub-Feature** | Uncore Freq | — |

**Reasoning**: tag contains FIX_IFWI/FIX_BIOS → BIOS

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
++++22611780717 vwang 
From:  @Kam, Timothy : Thanks for all the input, deliberations and checkings, we have reached the consensus that DMR BIOS should program all ELC-related fields under all possible LOM (Latency Optimized Mode) knob settings, namely Auto, Enable and Disable, as shown in the revised table below.  BIOS needs to separately program the UFS_CONTROL register fields for CCF via CBB cluster ID0, for mem fabric via IMH Cluster ID1 and for IO fabric via IMH Cluster ID0.  With this BIOS patch, primecode and pcode will not need to initialize these UFS_CONTROL register ELC-related fields.   TPMI Register Settings LOM = Auto or Enable LOM = Disable EFFICIENCY_LATENCY_CTRL_RATIO 0 12 (CCF), 12 (Mem), 8 (IO) EFFICIENCY_LATENCY_CTRL_LOW_THRESHOLD 0% 10% EFFICIENCY_LATENCY_CTRL_HIGH_THRESHOLD 0% 95% EFFICIENCY_LATENCY_CTRL_HIGH_THRESHOLD_ENABLE 1 1 EFFICIENCY_LATENCY_CTRL_MID_RATIO UFS_MIN UFS_MIN A related HAS section has been added at : https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html#bios-implementation-of-lom-knob Sagar> Currently, Primecode initializes the EFFICIENCY_LATENCY_CTRL_MID_RATIO to EFFICIENCY_LATENCY_CTRL_LOW_RATIO… I do not expect Primecode initializes as above, especially as we recommend ELC_MID_RATIO < ELC_LOW_RATIO to customers. Instead during runtime, I expect Primecode always resolves fabric frequency at or above UFS_MIN.   Eduardo> Currently the request is to set EFFICIENCY_LATENCY_CTRL_MID_RATIO equal to UFS_MIN Your setting is also fine but not necessary: BIOS can keep doing this as long as BIOS knows that UFS_MIN for IO fabric can be 400MHz if all IO ports are not populated.  For all other cases, UFS_MIN must be 800MHz. As mentioned above, Primecode knows and resolves with the appropriate UFS_MIN, so I thought BIOS can simply initialize EFFICIENCY_LATENCY_CTRL_MID_RATIO to 0. From Sagar: From the Primecode side, I would like to add the following: At runtime, Primecode always resolves the MID ratio directly from the current TPMI register values, ensuring that we operate using whatever BIOS or any other source has most recently programmed. During boot, Primecode initializes EFFICIENCY_LATENCY_CTRL_MID_RATIO to the same value as LOW_RATIO. The underlying assumption has been that the MID ratio should be at least as high as the low ratio since utilization increasing should naturally drive the fabric frequency upward. Regardless of the MID ratio setting, Primecode will always resolve the UFS fabric frequency at or above UFS_MIN, so functional behavior and minimum performance safeguards remain intact. One clarification question from our side: You mentioned that we recommend ELC_MID_RATIO < ELC_LOW_RATIO to customers. Could you help us understand why this is the recommended guidance? From a fabric‑scaling perspective, a ratio increasing with utilization appears intuitive, so we would like to understand the architectural intent behind MID being lower than LOW.


++++22611780737 vwang 
.


### Tags
BIOS_MS_PRE_ALPHA,SysDebugCloned, SysDebugDccbBypass,FIX_BIOS_OAKSTRM.0.RPB.0033.D.54,
OAKSTRM.0.RPB.0033.D.54,FIX_IFWI_DMR_AP1_2026.13.3.01,FIX_BKC_OKS_DMR_AP1_2026WW16

### Conclusion
bios.bug

### Component
bios

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
- **Component Path**: bios

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI Register`
- `TPMI register`

## Timeline

- **Submitted**: 2026-02-24 03:23:37
- **Root Caused**: 2026-02-24 05:14:22
- **Closed**: 2026-04-07 20:33:16
- **Days Open**: 42

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
