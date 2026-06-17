# HSD 14025998896: [X1 A0 PO] [CBB Pcode] Pcode is not implementing WRITE_DATA_WORD on ucode to pcode mailbox

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025998896](https://hsdes.intel.com/appstore/article-one/#/14025998896) |
| **Status** | rejected.merged |
| **Priority** | 2-high |
| **Owner** | coramire |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 75% |
| **Feature** | Platform PM Interface | 52% |
| **Sub-Feature** | Mailbox | — |

**Reasoning**: errata_status='review_waived' → HW

## Root Cause Summary

Summary:

========

Pcode is mising to implement WRITE_DATA_WORD on ucode to pcode mailbox

In [247]: sv.sockets.cbb0.pcode.vars.rapl.pp_level

Out[247]: socket0.cbb0.pcode.vars.rapl.pp_level - 0x00000005 # I am able to write into this address using tap access

In [259]: sv.socket0.cbb0.pcode.vars.rapl.pp_level.getaddress()['pcu_offset']

Out[259]: 0x6000CD4C

In [248]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_data=0x6000CD4C  #setting RW Pointer

In [249]: sv.socket0.cbb0.pcudata.ucode_pcode

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww40.3]

This is the sighting forked from 

14025967723

### Description
Summary:

========

Pcode is mising to implement WRITE_DATA_WORD on ucode to pcode mailbox

In [247]: sv.sockets.cbb0.pcode.vars.rapl.pp_level

Out[247]: socket0.cbb0.pcode.vars.rapl.pp_level - 0x00000005 # I am able to write into this address using tap access

In [259]: sv.socket0.cbb0.pcode.vars.rapl.pp_level.getaddress()['pcu_offset']

Out[259]: 0x6000CD4C

In [248]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_data=0x6000CD4C  #setting RW Pointer

In [249]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.command=5 

In [250]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy=1

In [251]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface #pcode loaded the pointer

Out[251]: 0x0

In [252]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_data=3 # trying to write 3 into address given before

In [253]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.command=7 # Setting WRITE_DATA_WORD opcode

In [254]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy=1 

In [255]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface 
#Write is failing with INVALID_COMMAND completion code

Out[255]: 0x1

from Source code 
https://github.com/intel-restricted/firmware.power.soc.pcode-cbb-a0/blob/master/source/pcode/mailbox/ucode_mbx.cpp
 seems that WRITE_DATA_WORD 

 command is not implemented

Impact:

========

VV gating

### Comments (latest)
++++14614672810 kwadams
<p>It seems this mailbox command was deprecated from client PTL SoC and CBB inherited:</p><p><a href="https://hsdes.intel.com/appstore/article-one/#/article/13012502502" target="_blank">https://hsdes.intel.com/appstore/article-one/#/article/13012502502</a></p><p><br /></p>

++++14614672811 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14025998852.
++++22611489379 coramire
Stonecypher, David Last updated on: Wednesday, October 1, 20258:06:56 AM(13 minutes ago) id:  14614673490 IIRC I and Josh Pfrimmer explictly asked to not remove this and other funnyio from NVL and DMR
++++14614676913 vwang
This is the sighting forked from 14025967723

++++14614683184 vwang
From Grabacki, Alex : Last updated on: Wednesday, October 1, 20254:00:25 PM(a day ago) id:  22611490697 Stitched IFWI with pcode patch available here: \\amr.corp.intel.com\ec\proj\debug\DMR\User\agraback\ww40p3_u2p_cmd_updates_PCODE_patch With changes: Patch needs to truncate the data for 32 correctly on reads / pointer set operations Patch will need to support 32bit aligned reads for addresses Patch also needs to restore the write opcode: For pcode team reference patch zip:  https://af01p-igk.devtools.intel.com/artifactory/pcode_lnl-igk-local/Debug_packages/CBB/private/PCODE_CBB_A0_ke5eb1fe91a0cb3b5_s822bba1_Private_agraback_ww40p3_u2p_cmd_updates.zip model path: /nfs/site/disks/agraback_wa01/pcode/po_branch_ww40p3_ucode_mbox_changes
++++22611495284 coramire
I am able to verify the restore write opcode on the debug patch,\\amr.corp.intel.com\ec\proj\debug\DMR\User\agraback\ww40p3_u2p_cmd_updates_PCODE_patch I was able to write into pcudata using the MB and read back again using the MB, the patch is working as expected In [310]: sv.socket0.imh0.s3m.ibl_treg.soccm_revids.soccm_current_revid Out[310]: 0x40580207 In [315]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_data=0x6000CD4C  #setting RW Pointer In [316]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.command=5 In [317]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy=1 In [318]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_data=3 # trying to write 3 into address given before In [319]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.command=7 # Setting WRITE_DATA_WORD opcode In [320]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy=1 In [321]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface #Write is SUCCESFUL completion code Out[321]: 0x0                                                                                                                               #trying to readback previous writer using the MB In [322]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_data=0x6000CD4C  #setting RW Pointer In [323]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.command=5 In [324]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy=1 In [328]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbo

### Tags
A0_VV_Gate

### Conclusion
no_root_cause.rejected

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
- **Sub-Feature**: Mailbox
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbb0.pcode.vars.rapl.pp_level.getaddress`
- `sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_data`
- `sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.command`
- `sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy`
- `sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface`

## Timeline

- **Submitted**: 2025-10-01 07:28:19
- **Closed**: 2025-10-03 23:32:35
- **Days Open**: 2

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
