# HSD 22022023676: [DMR][PM][X1 A0][FDU1]  MLC voltages 30-80mV higher than expected, due to single core hinting higher voltage

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22022023676](https://hsdes.intel.com/appstore/article-one/#/22022023676) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | jamesrow |
| **Component** | val.env.test |
| **Defect Die** | compute |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Tools | 90% |
| **Sub-Feature** | debug_tools | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

PLATFORM: 
SC00901159H0008(

Fused

)

IFWI:  

 

expectation:

Acode includes ITD in its hints to Pcode, where then pcode sets workprint for entire cbb on the max hint as only one fivr for entire base die.

observation: 

All mlcs in the cbb do not include itd offset in their hints

intial debug:

mlc's voltage higher than expected, most cores have voltage as expected:

base voltage used is the max of all the vf curve look ups of all the mlcs in the cbb:

core 0 requesting the high voltage, al

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww06.1]

James reported that the voltage issue is reproducible on FDU6 systems but not on others, and is collecting aCode variable data for further analysis, with the expectation that the data will be used to debug both FDU1 and FDU6 issues.

[26ww05.4]

Single core asking for higher voltage impacts MLC voltages. Timothy recommends to involve Ido Yuval to start debugging that. AR James to start conversation with Ido/
Okunev, Yulia 
if not started already.

### Description
PLATFORM: 
SC00901159H0008(

Fused

)

IFWI:  

 

expectation:

Acode includes ITD in its hints to Pcode, where then pcode sets workprint for entire cbb on the max hint as only one fivr for entire base die.

observation: 

All mlcs in the cbb do not include itd offset in their hints

intial debug:

mlc's voltage higher than expected, most cores have voltage as expected:

base voltage used is the max of all the vf curve look ups of all the mlcs in the cbb:

core 0 requesting the high voltage, all others requesting expecte ~.74V:

ratio's and temp where the same: 

base ratio fuses same between all cores: 

mlc voltage fuses the same as well:

### Comments (latest)
++++22611729978 mbfausto
No comments or updates here since submission (almost a week).  Please make sure to update your sighting with current status, experiments, and results!

++++22611730576 jamesrow
reproduced on Sc00901159h0001 with acode vars telemetry requested from acode owners, several modules requesting higher voltage then expected: log of acode.vars grants and operating points with no content or script running matches what we collected inside the script that performs the itd calculations: log need help processing acode.vars into why mlc hints are higher than expected also have similar log as above for ever mlc check performed while checking mlc itd calcs inside our FV script: itd script runs with acode var logging each mlc in the table below has a log, for instance log "mlc_base_volt_debug_module_8_check" is as telemetry for the first module in the table below also ran mlc checks with temperature data collection to confirm no temperature swings during testing: itd_run_addedThermData_noAcodeVars table of same failures, we see multiple mlc hints higher then the rest that cause mlc voltage to be higher then expected for all mlcs

++++22611737507 jamesrow 
Chen noticed that MC6 was active and that causes cores and mlc to pick largest freq before being quiesced. reran with wkld and checks confirming MC6 counter not incrementing also, reran with itd disabled for the mlc to remove itd from potential cause, fuse setting acode_spare_word_7 to zero for all modules, we see hints 100mV outside its max voltage unexpected that actual voltage did not change between itd being enabled vs. disabled both with MC6 not active and with itd disabled showed no change in data and outlier active mlc voltage is from the same module (module 24) and same voltage(0x15a-0x15b) also, histo'ed module 24s MLCK and 10000 samples never deviated from 2.2Ghz reason why some pma's have 0 for "num_domains_active_allowed' is because their module is not enabled conclusion, MC6 not the cause, unknown why turning off itd for mlc causes no change in WP enabled modules for Sc00901159h0001: spare words 0-5 are the voltages for mlc vf curve, max out at 0xc3(.761V) as seen in spare word 5: core0_fuse.core_fuse_core_fuse_acode_acode_spare_word_0 = 0xaf00af core0_fuse.core_fuse_core_fuse_acode_acode_spare_word_1 = 0xaf00af core0_fuse.core_fuse_core_fuse_acode_acode_spare_word_2 = 0xc000bb core0_fuse.core_fuse_core_fuse_acode_acode_spare_word_3 = 0xc300c3 core0_fuse.core_fuse_core_fuse_acode_acode_spare_word_4 = 0xc300c3 core0_fuse.core_fuse_core_fuse_acode_acode_spare_word_5 = 0xc300c3 #formatted in "U1.8" similar to core's voltage fuse values so .761V core0_fuse.core_fuse_core_fuse_acode_acode_spare_word_6 = 0x20d51f12 core0_fuse.core_fuse_core_fuse_acode_acode_spare_word_7 = 0x0 zipped logs, each contain a log of data without script (noScript) as seen in steps below and similar data from script running along with logs of acode var dump before each module's mlc check: itdMLc_noMC6_debu

### Tags
FV_PM

### Conclusion
not_a_bug

### Component
val.env.test

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

- **Primary Feature**: Tools
- **Sub-Feature**: debug_tools
- **Component Path**: val.env.test

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbb0.computes.modules.showsearch`
- `sv.socket0.cbb0.compute3.pma24.pmsb.target_wp1.core_frequence`

## Timeline

- **Submitted**: 2026-01-24 01:47:47
- **Root Caused**: 2026-02-06 00:13:56
- **Closed**: 2026-02-06 01:56:40
- **Days Open**: 13

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
