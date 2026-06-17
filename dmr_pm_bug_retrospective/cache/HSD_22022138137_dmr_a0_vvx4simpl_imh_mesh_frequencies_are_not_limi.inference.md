# HSD 22022138137: [DMR A0 VV][X4][SIMPL] IMH mesh frequencies are not limited by SIMPL

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22022138137](https://hsdes.intel.com/appstore/article-one/#/22022138137) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | pcanetel |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

In an idle scenario (no WL) frequency request higher than simpl_max_freq_0 limit is resolved, even when the current policy always is the 0 one.

Setting max frequencies values for 4 policies in IMH

       IO mesh

       sv.socket0.imhs.pcudata.simpl_max_freq_0_
0=10

       sv.socket0.imhs.pcudata.simpl_max_freq_0_1=12

       sv.socket0.imhs.pcudata.simpl_max_freq_0_2=14

       sv.socket0.imhs.pcudata.simpl_max_freq_0_3=18

       Mem mesh

       sv.socket0.imhs.pcudata.simpl_max_freq_1_
0=

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww14.1]

Patricia stated that manual testing with fee overrides is now required for SIMPL, and that this is the correct approach for current validation.

POR and Spec Implementation: Matthew and Alex clarified that either Prime Code needs to implement the existing specifications for TPMI and SIMPL, or a change in the POR must be driven by architecture, with Nilanjan identified as the decision-maker.

﻿[26ww13.3]

Patricia described her process of using fuse overrides to test frequency limits for policy 0, noting that after changing the limit, the frequency did not update as expected. Alex and Nilanjan explained that the floor gets locked by the fuses when IMH code pulls the fuses into SRAM, and that the only reliable way to test is with a properly fused part with multiple policies enabled.

﻿[26ww13.1]

Patricia can do test with fuse override. on-going.

[26ww12.4]

* Seeing value locked in for the max frequency
* Recommend usage update (using the bootscript) and re-test to see if this is a user/test/process issue versus a real FW issue.
﻿[26ww12.1]

Alex needs to work with Patricia to override fuses with boot script and retest.

﻿[26ww11.1]

Carlos confirmed that Nilanjan is the architect owner for SIMPL, and Alex is responsible for meeting with Nilanjan to implement the correct algorithm.

Suchismita offered to check Nilanjan's availability and escalate if urgent, while Alex and Trevor are reviewing the code to identify the cause of the current behavior.

[26ww10.3]

From Nilanjan, DMR only supports 1 policy. Testing is overriding fuse values to use lower values for policy. SIMPL should be able to limit no matter how high the min/max value for the policy is (arch statement). Next step is for arch/primecode to sync up about the implementation, testing condition is perfectly fine under architecture statements.

### Description
In an idle scenario (no WL) frequency request higher than simpl_max_freq_0 limit is resolved, even when the current policy always is the 0 one.

Setting max frequencies values for 4 policies in IMH

       IO mesh

       sv.socket0.imhs.pcudata.simpl_max_freq_0_
0=10

       sv.socket0.imhs.pcudata.simpl_max_freq_0_1=12

       sv.socket0.imhs.pcudata.simpl_max_freq_0_2=14

       sv.socket0.imhs.pcudata.simpl_max_freq_0_3=18

       Mem mesh

       sv.socket0.imhs.pcudata.simpl_max_freq_1_
0=10

       sv.socket0.imhs.pcudata.simpl_max_freq_1_1=12

       sv.socket0.imhs.pcudata.simpl_max_freq_1_2=14

       sv.socket0.imhs.pcudata.simpl_max_freq_1_3=18

       
sv.socket0.imhs.pcudata.showsearch('simpl_max_freq')

       simpl_max_freq_0_0 = 0xa

       simpl_max_freq_0_1 = 0xc

       simpl_max_freq_0_2 = 0xe

       simpl_max_freq_0_3 = 0x12

       simpl_max_freq_1_0 = 0xa

       simpl_max_freq_1_1 = 0xc

       simpl_max_freq_1_2 = 0xe

       simpl_max_freq_1_3 = 0x12

       simpl_max_freq_0_0 = 0xa

       simpl_max_freq_0_1 = 0xc

       simpl_max_freq_0_2 = 0xe

       simpl_max_freq_0_3 = 0x12

       simpl_max_freq_1_0 = 0xa

       simpl_max_freq_1_1 = 0xc

       simpl_max_freq_1_2 = 0xe

       simpl_max_freq_1_3 = 0x12

Requesting IO and MEM frequency higher than policy_2 limits

      IO mesh

     
 sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_control.max_ratio = 
15

      sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_control.min_ratio = 
15

      Mem mesh

 

   
   sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_control_fabric_1.max_ratio = 
15

      sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_control_fabric_1.min_ratio = 
15

Verifying current policy

      
sv.socket0.imh0.pcudata.patch_persistent.current_policy

      
0x0

      sv.socket0.imh1.pcudata.patch_persistent.current_policy

      
0x0

Frequency request resolved, expected to be limited at max freq = 10 as we are in policy 0

     sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status.c

### Comments (latest)
++++22611785990 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14027089381.
++++14615147780 kshtijma 
Hi Hector, To trigger simpl we need to inject IO/MEM traffic into the system by writing to the ufs bandwidth counters. writing to the ufs_control min and max_ratio is not the right way to do it. Simpl flow is triggered just before the workpoint write in the workpoint flow, where it reads the request_pstate which is actually coming from the IO/MEM traffic. Another way to trigger is using pega mailbox which should be a bit easier. The HAS clearly mentions that the SIMPL flow is triggers when it sees some IO/MEM traffic (DMR SoC IccMax Proactive Limits (SIMPL) Control) )


++++14615187125 pcanetel
Pcudata dumps attached here and shared and with Trevor Key as requested.
++++22611804479 agraback
In the pcudata dump, we see sv.socket0.imh0.pcudata.dietopo_instance.CFC_0.feature_die_limits_7_0 = 0x15 which is un-expectedly high. Recommend to remove all overrides and do a fresh boot On our DMR X1 Primecode system we see the SIMPL die limit set to 0xe which matches the lowest simpl_max_freq. I also ran the steps from the description at OS boot and idle and see the ratio remain below the simpl limit despite request a higher one with UFS control -------------------- In [12]: sv.socket0.imh0.pcudata.dietopo_instance.CFC_0.feature_die_limits_7_0 Out[12]: 0xe   In [14]: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status.current_ratio Out[14]: 0x4   In [15]: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status_fabric_1.current_ratio Out[15]: 0x8   In [16]: sv.socket0.imhs.pcudata.showsearch('simpl_max_freq') simpl_max_freq_0_0 = 0xe simpl_max_freq_0_1 = 0x14 simpl_max_freq_0_2 = 0x14 simpl_max_freq_0_3 = 0x17 simpl_max_freq_1_0 = 0x12 simpl_max_freq_1_1 = 0x12 simpl_max_freq_1_2 = 0x17 simpl_max_freq_1_3 = 0x17 simpl_max_freq_0_0 = 0xe simpl_max_freq_0_1 = 0x14 simpl_max_freq_0_2 = 0x14 simpl_max_freq_0_3 = 0x17 simpl_max_freq_1_0 = 0x12 simpl_max_freq_1_1 = 0x12 simpl_max_freq_1_2 = 0x17 simpl_max_freq_1_3 = 0x17     In [18]: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_control.max_ratio = 15     ...: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_control.min_ratio = 15     In [20]: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_control_fabric_1.max_ratio = 15     ...: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_control_fabric_1.min_ratio = 15   In [21]: sv.socket0.imh1.pcudata.dietopo_instance.CFC_0.feature_die_limits_7_0 Out[21]: 0xe   In [22]: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status.current_ratio Out[22]: 0x4   In [23]: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status_fabric_1.current_ratio Out[23]: 0x8   In [24]: sv.socket0.imh0.pcudata.patch_persistent.current_policy Out[24]: 0x0
++++14615210955 pcanetel 
In my X4 system I have to do the pcudata variables override as the fuses are set to an single value: 0x15 due to the decision of only have only 1 policy enabled for DMR. Primecode

### Tags
FV_PM

### Conclusion
not_a_bug

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

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI and`
- `TPMI ones`
- `TPMI registers`
- `sv.socket0.imhs.pcudata.simpl_max_freq_0_`
- `sv.socket0.imhs.pcudata.simpl_max_freq_0_1`
- `sv.socket0.imhs.pcudata.simpl_max_freq_0_2`
- `sv.socket0.imhs.pcudata.simpl_max_freq_0_3`
- `sv.socket0.imhs.pcudata.simpl_max_freq_1_`

## Timeline

- **Submitted**: 2026-02-27 07:42:58
- **Closed**: 2026-04-01 20:37:19
- **Days Open**: 33

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
