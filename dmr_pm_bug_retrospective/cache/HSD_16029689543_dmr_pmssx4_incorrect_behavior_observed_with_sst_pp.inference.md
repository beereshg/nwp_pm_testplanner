# HSD 16029689543: [DMR_PMSS][X4] Incorrect behavior observed with SST_PP_LOCK bit

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029689543](https://hsdes.intel.com/appstore/article-one/#/16029689543) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | ashashi |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Platform PM Interface | 52% |
| **Sub-Feature** | TPMI | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

On a 88c, X4 SKU (QDF: Q9LV) config supporting 2 SST PP Levels (PP0, PP1), observing below incorrect SST_PP_LOCK behavior 

Steps:

1. Boot system to OS with DynamicISS bios knob enabled and in SST PP level 0

2. Verify SST_PP_CONTROL & SST_PP_STATUS TPMI registers are 0 for both IMHs & CBBs

3. Try changing the PP level to unsupported PP level along with setting the lock bit

sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.sst_pp_control=0xf

sv.socket0.cbbs.base.tpmi.sst_pp_control=0xf

4. As per HAS,

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww06.1]

The team discussed the issue where the Pcode incorrectly sets the lock bit when an invalid SST-PP level change is requested, with ongoing coordination via email and involvement from Stan for further clarification

Abhinand and Alex discussed the technical details, noting that the Pcode is reentrant and sets the lock bit in a slow loop, which differs from the event-driven behavior of the prime code; the function update SST-PP level was identified as needing a broader review and potential changes.

Alex suggested that if the issue is urgent, a debug patch could be created by the US team, but otherwise, the team should continue the email discussion to allow the pCode team to decide on the next steps; Abhinand agreed that a debug patch would help, but emphasized the need for a more comprehensive code review.

Adi Yonishi is the owner of the SST code, and that Stan could also make decisions regarding the issue if needed.

### Description
On a 88c, X4 SKU (QDF: Q9LV) config supporting 2 SST PP Levels (PP0, PP1), observing below incorrect SST_PP_LOCK behavior 

Steps:

1. Boot system to OS with DynamicISS bios knob enabled and in SST PP level 0

2. Verify SST_PP_CONTROL & SST_PP_STATUS TPMI registers are 0 for both IMHs & CBBs

3. Try changing the PP level to unsupported PP level along with setting the lock bit

sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.sst_pp_control=0xf

sv.socket0.cbbs.base.tpmi.sst_pp_control=0xf

4. As per HAS, SST_PP_LOCK bit should not be set while trying to change PP level to unsupported PP level

Observing, PP_LOCK bit to be set on all CBB dies while reading SST_PP_STATUS TPMI register

HAS - https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html#gnr-1

System Information:

### Comments (latest)
++++22611729582 ashashi
Initiated email conversation with Pcode team on the issue (Anatoli).
++++1566823958 aamarna1 
 @Wang, Vidar - Please promote this to pcode database.    We had a discussion with Yonish, Adi and confirmed that its a pcode bug.  Scenario :  System boots with default SST PP Status  - SST lock = 0 ; SST PP level = 0 ; SST Error = 0  PP Level change is requested - Invalid level - 0xf with lock bit = 0x1 in SST_PP_Control register.  On this request Pcode enters a transactor update_sst_pp_config and rejects the PP level change with error bit set to 1 and returns from the transactor  Since this transactor runs in a slow loop it gets called again in next slow loop where the sst_pp_error flag is disabled which makes it go further in code to go set the lock bit. Eventually making the status register set ; sst_pp_lock = 1 ; sst_pp_error = 1 ;  Adi proposed a fix to remove the flag from being set every slow loop to avoid this lock bit from getting set when an invalid config is requested ; it further also resolves another issue which we had seen https://hsdes.intel.com/appstore/article-one/#/22022048393 Attached email conversation and logs. 
++++14615057926 vwang
[CloneScript] Sighting [sighting_central.sighting.id=16029689543] of [component=fw.pcode] in [release=pkg.dmr-a0] has been cloned to a [bug] to [heia_soc.bugeco.id=14026985262] of [component=dmrcbbbase.soc.pm.pcode] in [release=dmrcbbbase-a0]
++++22611744521 ashashi
Validated the fix with Pcode patch provided by  @Yonish, Adi -  https://af01p-igk.devtools.intel.com/artifactory/pcode_lnl-igk-local/Debug_packages/CBB/production_encrypted_private/PCODE_CBB_A0_k6133a0791c6fb2f5_sa782143_Private_sst_manager_bug_fix.zip  The issue mentioned in the HSD could not be reproduced: Logs attached Invalid PP Level with PP LOCK Bit - Lock bit is not getting set               In [36]: sv.socket0.cbbs.base.tpmi.sst_pp_control=0xf               In [38]: sv.socket0.cbbs.base.tpmi.sst_pp_status.show()                           0x00000000 : rsvd1 (63:56) (ro/v) -- Reserved                           0x0000003f : feature_error_type (55:32) (ro/v) -- Returns last error of the specific feature.  Three error_type bits per fea...                           0x00000000 : rsvd0 (31:16) (ro/v) -- Reserved                           0x00000000 : feature_state (15:08) (ro/v) -- Bit mask to indicate the enable(1)/disable(0) state of each feature of the curr...                           0x00000001 : sst_pp_error_type (07:04) (ro/v) -- Returns last error of SST-PP control. 0x0: no error 0x1: dynamic PP switch ...                           0x00000000 : sst_pp_lock (03:03) (ro/v) -- Returns the lock bit setting in SST_CONTROL.SST_PP_LOCK                           0x00000000 : sst_pp_level (02:00) (ro/v) -- Returns the current SST-PP level.           2. Invalid PP Level with Feature State - Feature State not getting set but FEATURE ERROR TYPE getting set as expected               In [49]: sv.socket0.cbbs.base.tpmi.sst_

### Tags
SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_60000993,FIX_IFWI_DMR_AP1_2026.09.3.04,FIX_BKC_OKS_DMR_AP1_2026WW12

### Conclusion
fw.bug

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

- **Primary Feature**: Platform PM Interface
- **Sub-Feature**: TPMI
- **Component Path**: fw.pcode

## Firmware Touchpoints

### BIOS
- `bios knob`

## Key Registers

- `TPMI registers`
- `TPMI register`
- `sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.sst_pp_control`
- `sv.socket0.cbbs.base.tpmi.sst_pp_control`
- `sv.socket0.cbbs.base.tpmi.sst_pp_status.show`

## Timeline

- **Submitted**: 2026-01-28 18:17:19
- **Root Caused**: 2026-02-04 23:51:05
- **Closed**: 2026-03-03 20:37:11
- **Days Open**: 34

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
