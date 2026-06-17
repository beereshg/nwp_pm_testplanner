# HSD 14025976840: [DMR][PM] LAVA attribute SSTTF_CFG0_CDYN4_LP_CLIP_FREQ is wrong for Q9CY and Q9LX SKUs

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025976840](https://hsdes.intel.com/appstore/article-one/#/14025976840) |
| **Status** | complete.wont_validate |
| **Priority** | 3-medium |
| **Owner** | lmalagon |
| **Component** | hw.fuse.xml |
| **Defect Die** | base |
| **Conclusion** | hw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 85% |
| **Feature** | Platform PM Interface | 52% |
| **Sub-Feature** | PECI | — |

**Reasoning**: conclusion='hw.bug' → HW

## Root Cause Summary

After reviewing the latest QDFs LAVA attributes for SST Features, we realized that SSTTF_
CFG0_
CDYN4_
LP_
CLIP_
FREQ is breaking the following rule from 
PM Fuse Specification HAS
:

These are the current values:

QDF

Q9CY

Q9LX

SSTTF_CFG0_CDYN0_LP_CLIP_FREQ

1.3

1.3

SSTTF_CFG0_CDYN1_LP_CLIP_FREQ

1.3

1.3

SSTTF_CFG0_CDYN2_LP_CLIP_FREQ

0.9

0.9

SSTTF_CFG0_CDYN3_LP_CLIP_FREQ

0.6

0.6

SSTTF_CFG0_CDYN4_LP_CLIP_FREQ

1.2

1.2 

This value should be lower than CDYN3 = 0.6

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
After reviewing the latest QDFs LAVA attributes for SST Features, we realized that SSTTF_
CFG0_
CDYN4_
LP_
CLIP_
FREQ is breaking the following rule from 
PM Fuse Specification HAS
:

These are the current values:

QDF

Q9CY

Q9LX

SSTTF_CFG0_CDYN0_LP_CLIP_FREQ

1.3

1.3

SSTTF_CFG0_CDYN1_LP_CLIP_FREQ

1.3

1.3

SSTTF_CFG0_CDYN2_LP_CLIP_FREQ

0.9

0.9

SSTTF_CFG0_CDYN3_LP_CLIP_FREQ

0.6

0.6

SSTTF_CFG0_CDYN4_LP_CLIP_FREQ

1.2

1.2 

This value should be lower than CDYN3 = 0.6

### Comments (latest)
++++14614660245 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14025945356.
++++22611487060 mbfausto
After reviewing the latest QDFs LAVA attributes for SST Features, we realized that SSTTF_CFG0_CDYN4_LP_CLIP_FREQ is breaking the following rule from PM Fuse Specification HAS: These are the current values: QDF Q9CY Q9LX SSTTF_CFG0_CDYN0_LP_CLIP_FREQ 1.3 1.3 SSTTF_CFG0_CDYN1_LP_CLIP_FREQ 1.3 1.3 SSTTF_CFG0_CDYN2_LP_CLIP_FREQ 0.9 0.9 SSTTF_CFG0_CDYN3_LP_CLIP_FREQ 0.6 0.6 SSTTF_CFG0_CDYN4_LP_CLIP_FREQ 1.2 1.2  This value should be lower than CDYN3 = 0.6
++++14614688527 stoh4
answered in https://hsdes.intel.com/appstore/article-one/#/14025945356 Punit.PCODE_SST_TF_CONFIG_0_LP_CLIP_RATIO_CDYN_INDEX0, Dec2Hex(double.Parse(lineItem.SSTTF_CFG0_SSE_LP_CLIP_FREQ.Value) * 10))); Punit.PCODE_SST_TF_CONFIG_0_LP_CLIP_RATIO_CDYN_INDEX1, Dec2Hex(double.Parse(lineItem.SSTTF_CFG0_AVX2_LP_CLIP_FREQ.Value) * 10))); Punit.PCODE_SST_TF_CONFIG_0_LP_CLIP_RATIO_CDYN_INDEX2, Dec2Hex(double.Parse(lineItem.SSTTF_CFG0_AVX512_LP_CLIP_FREQ.Value) * 10))); Punit.PCODE_SST_TF_CONFIG_0_LP_CLIP_RATIO_CDYN_INDEX3, Dec2Hex(double.Parse(lineItem.SSTTF_CFG0_AVX512H_LP_CLIP_FRE.Value) * 10))); Punit.PCODE_SST_TF_CONFIG_0_LP_CLIP_RATIO_CDYN_INDEX4, Dec2Hex(double.Parse(lineItem.SSTTF_CFG0_AMX_LP_CLIP_FREQ.Value) * 10))); LP_CLIP frequency guidelines: • SSTTF Cfg[0..4] SSE LP Clip = Speed, SSTPP[1..4] SSE P1 • SSTTF Cfg[0..4] AVX2 LP Clip = Speed, SSTPP[1..4] SSE P1 • SSTTF Cfg[0..4] AVX512 LP Clip = SSTPP[0..4] AVX2 P1 • SSTTF Cfg[0..4] AVX512H LP Clip = SSTPP[0..4] AVX512 P1 • SSTTF Cfg[0..4] AMX LP Clip = SSTPP[0..4] AMX P1 In DMR, (unlike GNR) AMX P1 specifically can be higher freq than AVX2 P1 and AVX512 P1 Hence the rule of CDYN4 freq to be < CDYN3 is not valid, as CDYN4 is equal to AMX P1

++++14614700085 stoh4
Answered as below: In DMR, (unlike GNR) AMX P1 specifically can be higher freq than AVX2 P1 and AVX512 P1 Hence the rule of CDYN4 freq to be < CDYN3 is not valid, as CDYN4 is equal to AMX P1 HAS maybe outdated for DMR https://docs.intel.com/documents/pm_doc/src/server/GNR/Globals/fuses/PM_fuses.html
++++22611548746 schen6 
This requires a DQ rule change because TMUL runs at half the core frequency (half-cycle) on PNC/DMR. As a result, its Cdyn is expected to be lower than AVX512 and may be either lower or higher than AVX2. The P1 frequency relationship (and LP_CLIP_FREQ) is still under review, as post-silicon measurements are not yet stable or confirmed.


++++22611556833 mbfausto
Since there is no HSD for  Lava Attribute issues (leading to an incorrect fusing), assuming "released" and moving to .validating.  I'm sorry for anyone who is getting ping emails because it may not be "released/available" but that's the cost of no ticket tracking ;(  Good luck!

++++22611563285 lmalagon
According to last comment from Stan (PM SST arch) and Alex, there is no issue on this since in DMR AMX can be a lower value tha

### Tags
FV_PM,FIX_FUSE_LAVA,SysDebugDccbBypass, PSF=Y

### Conclusion
hw.bug

### Component
hw.fuse.xml

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
- **Component Path**: hw.fuse.xml

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2025-09-26 09:38:14
- **Root Caused**: 2025-11-07 02:33:37
- **Closed**: 2025-11-07 02:33:37
- **Days Open**: 41

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
