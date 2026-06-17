# HSD 14026820727: [DMR][CBB]PNC Pcode routine for HVM is treating DCM31 differently than other DCMs

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026820727](https://hsdes.intel.com/appstore/article-one/#/14026820727) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | mmejiass |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 45% |
| **Sub-Feature** | general | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

In debugging the DMR SBFT DCM31 issue (https://hsdes.intel.com/appstore/article-one/#/article/14025989892), we saw that there were some RING configurations
that were written in DCM31 but not the other 30 DCMs (who got reset default
values) as part of the reset/pcode flow in HVM. All other DCMs (0-30) retained their reset defaults. It looks like there might be a bug in the pcode routines (SEND_LUT_CONFIG and COMPARE_CORE_PMA_BEFORE_RING) that is doing the extraneous writes. We need to understand 

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
SBFT  HPM  Mickey to confirm

[26ww18.1]

pending ptracker and analysis by pCode
.
[26ww17.1]

Pending on test data by 

Mejias Segura, Marisol

﻿[26ww15.1]

Issue: A side effect observed in SBFT mode related to LUT programming, concluding that the issue is a non-functional side effect specific to SBFT mode

SBFT Mode and LUT Programming: Anatoli explained that the observed side effect in SBFT single logical ID mode is due to the interaction between LUT programming and SBFT mode, which is not a supported configuration. The team previously instructed users to skip the LUT programming step to avoid the side effect, and confirmed that this does not impact functional testing of SBFT mode. 
This behavior is an unintended side effect, not a functional defect, and recommended rejecting the issue unless a functional impact is demonstrated.

Mickey described a workaround for DCM 31 in DMR, which involves skipping certain routines to avoid the issue, and confirmed that the workaround has no impact. The team agreed that if the issue is SBFT-specific and HVM can handle it, no firmware fix is needed.

Mickey and others emphasized the need for airtight evidence that the issue is strictly SBFT-specific, as some experiments did not yield expected results when disabling DCM 31. The team agreed to revisit the issue in the following week’s meeting after further investigation.

[26ww12.3]

Vidar will contact owner and pCoder.

[26ww10.3]

Waiting on pCode input

﻿[26ww09.3]

Anatoli said that Shareef and Zeev: If skip a specific reset stage, pCode have no problem, but they are they trying to basically try to understand what the DCM has different value than others.

[26ww08.4]

AR Marisol to start a conversation about this HSD for faster update

[26ww08.3]

Anatoli suspect there might be some steps that manufacture test should skip. Will talk with Shareef offline
.

[26ww07.3]

Zeev and Shareef determined that a specific function could be skipped via register configuration to avoid issu

### Description
In debugging the DMR SBFT DCM31 issue (https://hsdes.intel.com/appstore/article-one/#/article/14025989892), we saw that there were some RING configurations
that were written in DCM31 but not the other 30 DCMs (who got reset default
values) as part of the reset/pcode flow in HVM. All other DCMs (0-30) retained their reset defaults. It looks like there might be a bug in the pcode routines (SEND_LUT_CONFIG and COMPARE_CORE_PMA_BEFORE_RING) that is doing the extraneous writes. We need to understand the root-cause why DCM31 is being treated differently than other DCMs. 

 

 

Current Pcode model used in HVM: /nfs/site/disks/mfg_dmr_021/work_area/dhleivaa/buildModel/fc_emu_full_hvm-cbb-a0-main-25ww24a_v2/target/fw_emu/PCODE_ROOT/

Programming mismatch between 31 and other DCMs

### Comments (latest)
++++22611736532 mbfausto
Team - there are 0 comments since submitting 3 weeks ago.  Please provide an immediate status and summary of your sighting please  @Tadesse, Mickey  and  @Mejias Segura, Marisol .  What's the current experiments and debug in progress?
++++14615033085 mmejiass
As requested by Anatoli: - Checked RESET_MISC_VALIDATION_HOOKS[SB_CCP_POSTED_AT_RESET], it returns 0x0 in Si - Checked CCF_PMA_CFG register, here's the read from Si: No more experiments have been defined by pcode owner. I also checked the pcode version currently used in HVM (/nfs/site/disks/mfg_dmr_021/work_area/dhleivaa/buildModel/fc_emu_full_hvm-cbb-a0-main-25ww24a_v2/target/fw_emu/PCODE_ROOT/), found that inside ring_domain.ccp file, the SBO_SLICE_ID is set to a value of decimal 31 (line 452: /nfs/site/disks/mfg_dmr_021/work_area/dhleivaa/buildModel/fc_emu_full_hvm-cbb-a0-main-25ww24a_v2/target/fw_emu/PCODE_ROOT/source/pcode/drivers/ring/ring_domain.cpp): Also confirmed  from pcode.asm file (lines 15348 and 15349 from /nfs/site/disks/mfg_dmr_021/work_area/dhleivaa/buildModel/fc_emu_full_hvm-cbb-a0-main-25ww24a_v2/target/fw_emu/PCODE_ROOT/output/pcode/sim/bin/pcode.asm) that when send_ring_lut is done, SBO_SLICE_ID is used: Waiting for confirmation from Anatoli to see if setting of SBO_SLICE_ID to decimal 31 inside ring_domain.cpp can cause pcode to treat DCM31 differently to the other DCMs or if there are other experiments pcode team wants to do in Silicon.    

++++14615057348 dtadesse
With the help of the reset module team and Dmitry, this issue was reproduced in emulation that includes DCM31 (4 DCM module). We can see that DCM31 gets a non-zero value uniquely from the other DCMs.  Dmitry and I traced through the code and essentially the writes seem to be coming from Pcode during LUT programming. Somehow the programming around DCM31 is unique - we need pcode team  @Odler, Anatoli to investigate why Pcode is doing this incorrect programming to a unique DCM. We do not know if this is something that is SBFT/Tester specific due to core ID configuration or a more comprehensive issue that may affect system, so would like to get input on this ASAP.  Here is the ring_ctl4 difference between DCM0 and DCM31 This write was traced back IDIU2C register write  The register write above is coming from the programming of the ring_ctl4 in the core PMA which happens before phase2 completes.  Tracing this to the pcode lst file, it seems the writes could be part of the Pcode LUT programming. In addition, there seem to be unique references to DCM31 and 30 around that programming. 
++++1363573856 sheno
I think i have a direction for the issue: check what is the value of the fuse punit_fuses/fw_fuses_SST_PP_0_MODULE_DISABLE_MASK in the simulation is: 0x7ffffffe à DCM31 enabled. but we have a configuration in MLC: sbft_single_logical_id = 1 i remember that there was an issue with this configuration with pcode !!! there was an assumption on this fuse once the config sbft_single_logical_i

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

## Timeline

- **Submitted**: 2026-01-14 01:45:24
- **Closed**: 2026-05-14 17:24:31
- **Days Open**: 120

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
