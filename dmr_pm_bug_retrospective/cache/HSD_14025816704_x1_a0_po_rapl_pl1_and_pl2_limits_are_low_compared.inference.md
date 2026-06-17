# HSD 14025816704: [X1 A0 PO] [RAPL] PL1 and PL2 limits are low compared to the TDP

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025816704](https://hsdes.intel.com/appstore/article-one/#/14025816704) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | kumara5 |
| **Component** | bios |
| **Defect Die** | base |
| **Conclusion** | bios.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **BIOS** | 70% |
| **Feature** | Power/RAPL | 80% |
| **Sub-Feature** | Socket RAPL | — |

**Reasoning**: tag contains FIX_IFWI/FIX_BIOS → BIOS

## Root Cause Summary

This is verified on multiple platforms
Summary:

Platform- jf53nor09bn0302.amr.corp.intel.com (PO Platform (Unfused))

IFWI - 
01_OKSDCRB1.86B.2025.34.1.02_2654.D06_70000940._1P0_NonIPClean_Trace_DebugSigned_PE8_Resetcpl1234Enable.bin

Normally, PL1 is set close to the TDP, and PL2 is set higher than TDP to allow for short bursts of higher performance. For a 350W TDP, we would expect PL1 to be around 350W and PL2 to be higher (e.g., 400–450W, depending on platform and cooling). 

Having PL1 at 3

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
Failing signature: RAPL PL1, and PL2 are not being set correctly by BIOS , due to BIOS unable to red data from Memory ( basic itp access)

 

 

 

 

WW36.2

 

From Suman
  
&quot;Based on inputs from Tamir (CBB PCODE), Seems like there is expected delta for TPMI space to be 64 bit alligned v/s 34b aligned as the specification : DMR CBB Punit GNR Legacy Review. This looks like some arch spec mismatch in GNR to DMR and IMO shall be taken care by BIOS as Feature Req. 

This is a HW limitation (due to timing restrictions) that can’t be patched. 
This is deviation in specs v/s GNR to CBB as defined in 
https://docs.intel.com/documents/pm_doc/src/DMR_CBB/MAS/GNR_Legacy/punit_gnr_legacy_review.html#two-misalignments-between-gnr-legacy-to-cbb

Next)David)
 Clone this to BIOS feature ( Vidar did it already) 

 

 

WW35.5

 

No major update, Joe will run few more experiments to double check the behavior

 

 

 

 

WW35.4

 

From Hector “Normally, PL1 is set close to the TDP, and PL2 is set higher than TDP to allow for short bursts of higher performance. For a 350W TDP, we would expect PL1 to be around 350W and PL2 to be higher (e.g., 400–450W, depending on platform and cooling). Having PL1 at 32W and PL2 at 36W would severely throttle the processor, preventing it from reaching anywhere near its designed performance.”

 

From Amit “The PL1 and PL2 limits are correctly copied by the primecode, but are getting overwritten by the BIOS at CPL3/4 to a lower value.”

 

Bios response to Amit Findings “When “PL1 Power Limit”/”PL2 Power Limit” knobs are 0 (default), bios program these register with value from the Fused TPD coming from TPMI’s SST_PP_INFO-1.TDP times the power unit.

 

Assuming knobs are default, let’s review TPMI’s SST_PP_INFO-1.TDP”

 

Seems like BIOS is not getting the expected data -> Probably an acces method problem

 

Is concerning why we cannot acces this data ->

 

 

 

 

Next) Joe Brooks) Please chase the access issue ( check if we have runs in M

### Description
This is verified on multiple platforms
Summary:

Platform- jf53nor09bn0302.amr.corp.intel.com (PO Platform (Unfused))

IFWI - 
01_OKSDCRB1.86B.2025.34.1.02_2654.D06_70000940._1P0_NonIPClean_Trace_DebugSigned_PE8_Resetcpl1234Enable.bin

Normally, PL1 is set close to the TDP, and PL2 is set higher than TDP to allow for short bursts of higher performance. For a 350W TDP, we would expect PL1 to be around 350W and PL2 to be higher (e.g., 400–450W, depending on platform and cooling). 

Having PL1 at 32W and PL2 at 36W would severely throttle the processor, preventing it from reaching anywhere near its designed performance.

#TPMI

In [135]: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control.show()

0x000000000 : lock (63:63) (rw/l) -- When set, all settings in this register are locked and are treated as Read Only until next reset.

0x000000001 : pwr_lim_en (62:62) (rw/l) -- Enable(1) or Disable(0)

0x000000000 : rsvd (61:25) (rw/l) -- Reserved

0x00000000a : time_window (24:18) (rw/l) -- Indicates the length of time window over which the power limit will be used by the processor.  The time w...

0x000000100 : pwr_lim (17:00) (rw/l) -- This field indicates the power limitation for the socket RAPL domain.  The unit of measurement is defined in ...

In [136]: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl2_control.show()

0x000000000 : lock (63:63) (rw/l) -- When set, all settings in this register are locked and are treated as Read Only until next reset.

0x000000001 : pwr_lim_en (62:62) (rw/l) -- Enable(1) or Disable(0)

0x000000000 : rsvd (61:25) (rw/l) -- Reserved

0x000000043 : time_window (24:18) (rw/l) -- Indicates the length of time window over which the power limit will be used by the processor.  The time w...

0x000000133 : pwr_lim (17:00) (rw/l) -- This field indicates the power limitation for the socket RAPL domain.  The unit of measurement is defined in ...

In [145]: sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_power_sku.pkg_tdp.getsp

### Comments (latest)
++++14614561315 kumara5
<div><span style="font-size: 14px;">The PL1 and PL2 limits are correctly copied by the primecode, but are</span>&nbsp;getting overwritten by the BIOS at CPL3/4 to a lower value.</div><!--StartFragment--><!--EndFragment--><div><span style="font-size: 14px;"><u><b><br /></b></u></span></div><div><span style="font-size: 14px;"><u><b><br /></b></u></span></div><div><span style="font-size: 14px;"><u><b>After CPL2 completion</b></u></span></div><div><span style="font-size: 14px;">In [12]: while(1):</span></div><div><span style="font-size: 14px;">&nbsp; &nbsp; ...:&nbsp; &nbsp; &nbsp;if(<span style="background-color: rgb(255, 255, 0);">sv.socket0.imh0.pcodeio_map.io_bios_reset_cpl.rst_cpl2==1</span>):</span></div><div><span style="font-size: 14px;">&nbsp; &nbsp; ...:&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;itp.halt()</span></div><div><span style="font-size: 14px;">&nbsp; &nbsp; ...:&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;break</span></div><div><span style="font-size: 14px;">&nbsp; &nbsp; [GPC core group] Halt on 2 devices -- 11:53:35.797573 2025-08-26</span></div><div><br /></div><div>#TPMI</div><div><span style="font-size: 14px;"><br /></span></div><div><span style="font-size: 14px;">In [18]: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control.show()</span></div><div><span style="font-size: 14px;">0x000000000 : lock (63:63) (rw/l) -- When set, all settings in this register are locked and are treated as...</span></div><div><span style="font-size: 14px;">0x000000001 : pwr_lim_en (62:62) (rw/l) -- Enable(1) or Disable(0)</span></div><div><span style="font-size: 14px;">0x000000000 : rsvd (61:25) (rw/l) -- Reserved</span></div><div><span style="font-size: 14px;">0x00000000a : time_window (24:18) (rw/l) -- Indicates the length of time window over which the power limit...</span></div><div><span style="font-size: 14px;"><b><span style="background-color: rgb(0, 255, 0);">0x000000af0</span> : </b>pwr_lim (17:00) (rw/l) -- This field indicates the power limitation for the socket RAPL doma...</span></div><div><span style="font-size: 14px;"><br /></span></div><div><span style="font-size: 14px;"><br /></span></div><div><span style="font-size: 14px;">In [19]: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl2_control.show()</span></div><div><span style="font-size: 14px;">0x000000000 : lock (63:63) (rw/l) -- When set, all settings in this register are locked and are treated as...</span></div><div><span style="font-size: 14px;">0x000000001 : pwr_lim_en (62:62) (rw/l) -- Enable(1) or Disable(0)</span></div><div><span style="font-size: 14px;">0x000000000 : rsvd (61:25) (rw/l) -- Reserved</span></div><div><span style="font-size: 14px;">0x000000004 : time_window (24:18) (rw/l) -- Indicates the length of time window over which the power limit...</span></div><div><span style="font-size: 14px;"><b><span style="background-color: rgb(0, 255, 0);">0x000000d20</span> : </b>pwr_lim (17:00) (rw/l) -- This field indicates the power limitation for the sock

### Tags
FV_PM_BDC,BIOS_FEATURE,BIOS_MS_POWER_ON,SysDebugCloned,SysDebugDccbBypass,BIOS_RCR,TEMP_WA_BIOS_OAKSTRM.0.RPB.2733.D.04_POWERON,FWTF_PO_UNBLOCKED,FV_PM,FIX_BIOS_OAKSTRM.0.RPB.0029.D.15,FIX_IFWI_DMR_AP1_2025.45.4.02,FIX_BKC_OKS_DMR_AP1_2025WW46

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

- **Primary Feature**: Power/RAPL
- **Sub-Feature**: Socket RAPL
- **Component Path**: bios

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI

In`
- `TPMI space`
- `TPMI Arch`
- `TPMI register`
- `TPMI SRAM`
- `TPMI CAP`
- `TPMI package`
- `TPMI missing`
- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control.show`
- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl2_control.show`

## Timeline

- **Submitted**: 2025-08-27 03:04:59
- **Root Caused**: 2025-09-02 22:47:56
- **Closed**: 2026-03-11 19:01:18
- **Days Open**: 196

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
