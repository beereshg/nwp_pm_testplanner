# HSD 16030332752: [DMR][AP][BKC][X4][ALPHA][CENTOS] : All core are not operating at ACT Frequency with SSE workload

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16030332752](https://hsdes.intel.com/appstore/article-one/#/16030332752) |
| **Status** | rejected.not_a_defect |
| **Priority** | 2-high |
| **Owner** | sagrawa3 |
| **Component** | fw.pcode |
| **Defect Die** | compute |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 45% |
| **Sub-Feature** | general | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Issue : All available cores are not operating at ACT with Stress

Failing Snippet:

Passing Snippet :

Expected Behaviour:

All Core should operate at ACT Frequency when stress is run

Actual Behaviour:

Couple of Cores fails to Operate at ACT Frequency

Isolation:

1) Issue is observed in Multiple platforms

2) Issue is not Observed with N-1 BKC IFWI with Full Mitigation(OKSDCRB1_86B_2026.10.4.01_0032.D91_80000994_0.770.0_IPCleanDFXEnable_Trace_DebugSigned_VIS_bkcwa_bighammer_enabled)

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww17.1]

Shubham reported ongoing work with Dinesh on the performance recipe for PTP, noting that issues are still being investigated and no external input is required at this time.

﻿[26ww16.4]

Beeresh explained that after a recent BKC release, many cores operated at a lower frequency (1800 MHz) instead of the expected 2300 MHz, resulting in significant performance loss, with the affected cores varying across runs and sockets.

The team determined that a change in the FIT_CONFIG TPMI reset value from 0x0 to 0xF removed the CDYN ceiling guard, allowing inter-core electrical noise to inflate CDYN classification and misclassify modules, leading to lower turbo ratios.

The testing confirmed the bimodal frequency split, and discussions with David (PTP) clarified that the issue was not directly caused by RIT changes but by the FIT_CONFIG default value change, which BIOS did not override.

Next: The team agreed to try standard performance recipes and consult with architecture experts (Ido) if further questions arise, while Stanley requested additional debug links for offline analysis.

### Description
Issue : All available cores are not operating at ACT with Stress

Failing Snippet:

Passing Snippet :

Expected Behaviour:

All Core should operate at ACT Frequency when stress is run

Actual Behaviour:

Couple of Cores fails to Operate at ACT Frequency

Isolation:

1) Issue is observed in Multiple platforms

2) Issue is not Observed with N-1 BKC IFWI with Full Mitigation(OKSDCRB1_86B_2026.10.4.01_0032.D91_80000994_0.770.0_IPCleanDFXEnable_Trace_DebugSigned_VIS_bkcwa_bighammer_enabled)

### Comments (latest)
++++1667434709 bg3
**Root Cause: FIT_CONFIG TPMI reset value change exposing CDYN estimation issue** Discussed with David (PTP). RIT itself is not the root cause — the FIT_CONFIG default value change exposed an underlying CDYN estimator sensitivity in the noisy neighbors flow. **What changed:** Commit `da50db21a` (drop 26ww11a) updated the TPMI XML to change `FIT_CONFIG_0`/`FIT_CONFIG_1` reset values from `0x0` to `0xF` for all module fields. - `FIT_CONFIG = 0x0` → "Frequency fixed to SSE P0n" → MAX_CDYN_CEILING is capped per TRL vector → all cores hold 2300 MHz under SSE load ✅ - `FIT_CONFIG = 0xF` → "Legacy Mode" → MAX_CDYN_CEILING uncapped (`get_cdyn_max_level()`) → PVP CDYN estimator misclassifies ~42% of modules as AMX-class → those modules drop to 1800 MHz ❌ **Key detail:** BIOS has `RITOptIn = No` (default), so BIOS never writes FIT_CONFIG — the registers retain their hardware reset values. The reset value change therefore directly controls pcode behavior without any BIOS opt-in. **Evidence (224-core SSE load, A/B):** - pCode 22.1.30.1 (FIT_CONFIG reset = 0x0) → **Pass** — all 224 cores at 2300 MHz - pCode 22.1.30.2 (FIT_CONFIG reset = 0xF, commit `da50db21a`) → **Fail** — 96 cores at 2300 MHz, 128 cores at 1800 MHz Promoting to central sighting for further debug on the underlying CDYN estimation sensitivity under shared VCC_MLC_SSA PDN noise (suspected).
++++1363633477 aodler
Default value of FIT_CONFIG was changed from 0x0 to 0xF, request change ticket 13014845328 - DMR - RIT registers tpmi.fit_config_0/1 have incorrect default values In case of FIT_CONFIG = 0xFF, Pcode will setup value to CDYN_MAX_LEVEL to RESOLUTION_CONTROL_2[MAX_CDYN_CEILING] Please refer to the HAS: https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCP%20HAS/cbb_cpp_has.html#:~:text=configuration%20is%20updated.-,Pcode%20Min/Max%20Cdyn%20Fuses,-New%20Pcode%20fuses
++++1667445759 sagrawa3 
With the performance recipe shared by  @Rotich, Simeon K, we are not observing this issue. All cores are operating at 2300, when running the SSE workload. Attached the logs.
++++14615357824 vwang
Tests indicate the issue was likely due to incorrect FIT default handling. FIT_CONFIG default was updated from 0x0 to 0xF per HSD 13014845328.    Per HAS, when FIT_CONFIG=0xF,  Pcode programs RESOLUTION_CONTROL_2[MAX_CDYN_CEILING] to CDYN_MAX_LEVEL. With the recommended performance recipe, the issue is no longer reproducible; all cores sustain 2300 MHz during SSE workload.
++++1667461403 bg3 
The tuning steps in the wiki helped to resolve the problem:  DMR PnP AP A0 - FVCommon - Intel Enterprise Wiki.  With BKC release 99D included majority of tuning steps baked-in, verification with this release issue not observed.  14026892221 - [DMR][Tune]:PVP Weights and Thresholds to be added to added to acode (Primecode)

### Conclusion
not_a_bug

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

- `TPMI reset`
- `TPMI XML`

## Timeline

- **Submitted**: 2026-04-16 11:38:19
- **Closed**: 2026-04-22 07:18:49
- **Days Open**: 5

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
