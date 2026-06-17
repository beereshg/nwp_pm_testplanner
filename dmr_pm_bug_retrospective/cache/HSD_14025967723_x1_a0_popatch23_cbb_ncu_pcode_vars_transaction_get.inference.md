# HSD 14025967723: [X1 A0 PO][Patch23] CBB NCU Pcode Vars transaction gets stuck and returns Address for most iterative attempts

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025967723](https://hsdes.intel.com/appstore/article-one/#/14025967723) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | dstonecy |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Platform PM Interface | 52% |
| **Sub-Feature** | Mailbox | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Summary:

========

Iterative pcode variable reads are returning the address from the mailbox, rather than the data from the request

see 
https://hsdes.intel.com/appstore/article-one/#/article/15014719950
 for similar behavior in VP fmod modeling from bad run-busy-bit checks

Impact:

========

Randomly wrong data from register reads in live platform (maybe every other read attempt

Details:

========

In [73]: p23.punit_mem_exclusive(0x60000000)

Out[73]: 0x60000000

In [74]: p23.punit_mem_exc

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww40.4]

The same issue was observed in Pre-Si by Tan, Chun Ming.

Carlos O was able to write into pcudata using the mailbox and read back again.

PrimeCode team managed to create the pCode patch, which was verified by Carlos to resolve the issue; the patch involved reverting previously removed pCode code.

David/Carlos will further verify this debug pCode patch and update the sighting.

[25ww40.3]

David reported that the mailbox interface is returning 64-bit data instead of the expected 32-bit, and the write operation was removed from the code base of pCode without review, these affect virtually all VV PM validation activities, including cross-product testing.

The same issue is reproduced by Tan, Chun Ming on his pre-Si platform.

pCode changes that causes these issues are pcode &quot;FEATURE: Deprecate the UCode2PCode MBX WRITE_DATA Services&quot; with Commit dd81697

Those changes were made without proper review or communication with validation teams.

Next Steps: Alex will try to cover pCode team and attempt both reverting those code changes (removal of the write operation and addressing the 32/64-bit issue),  The team agreed to treat the issue as a showstopper and prioritize the fix.

Alex proved the pCode test patche this afternoon.

[25ww40.1]

No pCode attendance.  Vidar communicated with pCoder at night and updated the response.

### Description
Summary:

========

Iterative pcode variable reads are returning the address from the mailbox, rather than the data from the request

see 
https://hsdes.intel.com/appstore/article-one/#/article/15014719950
 for similar behavior in VP fmod modeling from bad run-busy-bit checks

Impact:

========

Randomly wrong data from register reads in live platform (maybe every other read attempt

Details:

========

In [73]: p23.punit_mem_exclusive(0x60000000)

Out[73]: 0x60000000

In [74]: p23.punit_mem_exclusive(0x60000004)

Out[74]: 0x3333333334A10B73

In [75]: p23.punit_mem_exclusive(0x60000000)

Out[75]: 0x60000000

In [76]: p23.punit_mem_exclusive(0x60000000)

Out[76]: 0x34A10B73130A9EA1

In [77]: p23.punit_mem_exclusive(0x60000004)

Out[77]: 0x60000004

In [78]: p23.punit_mem_exclusive(0x60000004)

Out[78]: 0x3333333334A10B73

In [79]: p23.punit_mem_exclusive(0x60000000)

Out[79]: 0x60000000

In [80]: p23.punit_mem_exclusive(0x60000000)

Out[80]: 0x34A10B73130A9EA1

### Comments (latest)
++++14614657957 kwadams 
Ran the patch2 instruction twice and checked the ucode_pcode_mailbox in punit. On every other iteration there is bad return data and the interface command is ReturnCode:  ILLEGAL_DATA=0x4 In [100]: cd.patch2(0x6000_0000, 0xc, 0, 4) -W- verify patch3 is supported. if not, you can try setting socket0.cbb0.compute0.module4.core0.scp_cr_psmi_ctrl.enable_cr_access manually Out[100]: {'DMR0_PNC4_C0_T0': 0xAF2BFF001A156BB4} In [102]: sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode_mailbox_interface["fid_32"].show() 0x00000000 : run_busy (31:31) (rw/1s) -- UCODE may write to the two mailbox registers only when RUN_BUSY is cleared (0b).  Setting RUN_BUSY to 1b will create a Fast Path event.  After setting this bit, UCODE will poll this... 0x00000000 : param2 (29:16) (rw) --  The mailbox param 2, set by Ucode. 0x00000000 : param1 (15:08) (rw) --  The mailbox param 1, set by Ucode. 0x00000000 : command (07:00) (rw) -- This field contains the UCODE request command on asserting RUN_BUSY or the PCODE response code on RUN_BUSY de-assertion. In [101]: sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode_mailbox_data["fid_32"].show() 0xaf2bff001a156bb4 : data (63:00) (rw) -- This field contains the data associated with specific commands. In [103]: cd.patch2(0x6000_0000, 0xc, 0, 4) -W- verify patch3 is supported. if not, you can try setting socket0.cbb0.compute0.module4.core0.scp_cr_psmi_ctrl.enable_cr_access manually Out[103]: {'DMR0_PNC4_C0_T0': 0x0} In [105]: sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode_mailbox_interface["fid_32"].show() 0x00000000 : run_busy (31:31) (rw/1s) -- UCODE may write to the two mailbox registers only when RUN_BUSY is cleared (0b).  Setting RUN_BUSY to 1b will create a Fast Path event.  After setting this bit, UCODE will poll this... 0x00000000 : param2 (29:16) (rw) --  The mailbox param 2, set by Ucode. 0x00000000 : param1 (15:08) (rw) --  The mailbox param 1, set by Ucode. 0x00000004 : command (07:00) (rw) -- This field contains the UCODE request command on asserting RUN_BUSY or the PCODE response code on RUN_BUSY de-assertion. In [104]: sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode_mailbox_data["fid_32"].show() 0x0000000000000000 : data (63:00) (rw) -- This field contains the data associated with specific commands.


++++14614658252 kwadams
Issue the command direct to U2P in Punit is working fine back to back.  Need to check why ucode is creating INVALID_DATA response every other iteration. In [126]: sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode_mailbox_data["fid_32"]=0x6000_0000 In [127]: sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode_mailbox_interface["fid_32"].command=5 In [128]: sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode_mailbox_interface["fid_32"].run_busy=1 In [129]: sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode

### Tags
SysDebugCloned,SysDebugDccbBypass,FWTF_PO_UNBLOCKED,TEMP_WA_PATCH_DMR_AP1_A0_60000970_POWERON,FIX_PATCH_DMR_AP1_A0_6000097D,FIX_IFWI_DMR_AP1_2025.47.1.01,UP_DMR_A0_60000979_TPRODSIGNED,SysDebug_FixId_Ignore,FIX_BKC_OKS_DMR_AP1_2025WW47, PSF=Y

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

- **Primary Feature**: Platform PM Interface
- **Sub-Feature**: Mailbox
- **Component Path**: fw.pcode

## Firmware Touchpoints

### PCODE
- `pCode patch`
- `pCode change`

## Key Registers

- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode_mailbox_interface`
- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode_mailbox_data`

## Timeline

- **Submitted**: 2025-09-25 02:29:30
- **Root Caused**: 2025-10-04 01:14:31
- **Closed**: 2026-01-09 20:46:01
- **Days Open**: 106

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
