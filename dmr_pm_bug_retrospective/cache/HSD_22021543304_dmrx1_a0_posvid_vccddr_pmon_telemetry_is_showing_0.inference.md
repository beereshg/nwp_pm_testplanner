# HSD 22021543304: [DMR][X1 A0 PO][SVID] VCCDDR Pmon telemetry is showing 0 values

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22021543304](https://hsdes.intel.com/appstore/article-one/#/22021543304) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | pcanetel |
| **Component** | hw.svid |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Power/RAPL | 80% |
| **Sub-Feature** | SVID | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Summary:

========

DDR Pmon readings are showing 0 values.

Impact:

========

Power readings exposed in TPMI registers are 0.

Also impacting DRAM RAPL.

Details:

========

==> System configuration: 

Platform sc00901159h0006  (PO Platform / Unfused part)

==> BIOS/Patch/IFWI/BKC/CI Versions ...

OKSDCRB1.86B.2688.D02.2508272005 - 08/27/2025

bs.go(fused_unit=False, fuse_str={&quot;cbb_base0&quot;:['punit_fuses.fw_fuses_sst_pp_0_module_disable_mask=0xFFFFE8FF','punit_fuses.fw_fuses_llc_slice_

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
Failing Signature: 
 
DDR Pmon readings are showing 0 values.

 

WW37.2

 

What is the issue here ? 
Not able to read SVID values from Pmon issues , 
WIth 16 DIMMS we are able to read values 

Next) David )t
o close this as expected behavior

### Description
Summary:

========

DDR Pmon readings are showing 0 values.

Impact:

========

Power readings exposed in TPMI registers are 0.

Also impacting DRAM RAPL.

Details:

========

==> System configuration: 

Platform sc00901159h0006  (PO Platform / Unfused part)

==> BIOS/Patch/IFWI/BKC/CI Versions ...

OKSDCRB1.86B.2688.D02.2508272005 - 08/27/2025

bs.go(fused_unit=False, fuse_str={&quot;cbb_base0&quot;:['punit_fuses.fw_fuses_sst_pp_0_module_disable_mask=0xFFFFE8FF','punit_fuses.fw_fuses_llc_slice_ia_ccp_dis=0xffff00ff']})

==> Reproducibility

Always

==> Lightswitch discoveries ...

N/A

==> Experiment results ...

------------------------------------------PCODE IO MAP-------------------------------------------------------------------

In [722]:
sv.socket0.imh0.pcodeio_map.showsearch('io_telemetry_vccddr')

io_telemetry_vccddrhv_
i_out_accumulator = 0x59940a0

io_telemetry_vccddrhv_i_out_num_samples_snapshot
= 0xf282f20

io_telemetry_vccddrhv_
p_in_energy_accumulator = 0x0

io_telemetry_vccddrhv_p_in_energy_num_samples_snapshot
= 0xf2f8240

 

In [723]:
sv.socket0.imh0.pcodeio_map.showsearch('io_telemetry_vccddr')

io_telemetry_vccddrhv_
i_out_accumulator = 0x1252a30

io_telemetry_vccddrhv_i_out_num_samples_snapshot
= 0xf7f5120

io_telemetry_vccddrhv_
p_in_energy_accumulator = 0x0

io_telemetry_vccddrhv_p_in_energy_num_samples_snapshot
= 0xf86a440

 

In [724]:
sv.socket0.imh0.pcodeio_map.showsearch('io_telemetry_vccddr')

io_telemetry_vccddrhv_i_out_accumulator
= 0x9bf10a0

io_telemetry_vccddrhv_i_out_num_samples_snapshot
= 0xf9a6720

io_telemetry_vccddrhv_
p_in_energy_accumulator = 0x0

io_telemetry_vccddrhv_p_in_energy_num_samples_snapshot
= 0xfa1ba40

---------------------------------------PCUDATA----------------------------------------------------------------

In [748]:
sv.socket0.imh0.pcudata.pwrBdgtMngr.pmeterData.powerTrackerPMON_0.show()

0x000000000000
0000 : last_accum_snapshot

0x0000000009d0cb40 :
last_num_samples_snapshot

 

In [749]:
sv.socket0.imh0.p

### Comments (latest)
++++22611451384 coramire
<p>After Enabling Pmon on all Vrs&nbsp;</p><p><br /></p><p><span style="white-space: pre">	</span>In [1458]: sv.socket0.imh0.punit.pmusvid.punit_svid_cr_regs.svid_pwrin_mask=-1</p><p><br /></p><p>During boot I can see that SVID starts polling data but after some time Dram Vr stops sending Power data</p><p><br /></p><p>In [1459]: sv.socket0.imh0.punit.pmusvid.punit_svid_vrci_regs.svid_p_in_accumulator</p><p>Out[1459]:</p><p><span style="background-color: rgb(255, 255, 0);">svid_p_in_accumulator[0]=0x0</span></p><p>svid_p_in_accumulator[1]=0xf40a790</p><p>svid_p_in_accumulator[2]=0x19000</p><p>svid_p_in_accumulator[3]=0x63c95a0</p><p>svid_p_in_accumulator[4]=0x4ff76d0</p><p>svid_p_in_accumulator[5]=0x0</p><p>svid_p_in_accumulator[6]=0x0</p><p>svid_p_in_accumulator[7]=0x0</p><p>svid_p_in_accumulator[8]=0x0</p><p><br /></p><p>this problem is reproduced also accessing the vr using the svid mailbox, all other VRS we can enable pmon telemetry and get power readings</p><p><br /></p><p>In [1452]: svid.svid_reg_decode(0,0,0x18,0)</p><p>Out[1452]: <span style="background-color: rgb(255, 255, 0);">(0x0, '0.000 Watts')</span></p><p><br /></p><p>In [1453]: svid.svid_reg_decode(0,0,0x18,0)</p><p>Out[1453]: (0x0, '0.000 Watts')</p><p><br /></p><p>In [1454]: svid.svid_reg_decode(0,0,0x18,0)</p><p>Out[1454]: (0x0, '0.000 Watts')</p><p><br /></p><p>In [1455]: svid.svid_reg_decode(0,0,0x18,0)</p><p>Out[1455]: (0x0, '0.000 Watts')</p><p><br /></p><p>In [1456]: svid.svid_reg_decode(0,0,0x18,0)</p><p>Out[1456]: (0x0, '0.000 Watts')</p><div><br /></div>

++++22611451387 shizhong
<p>Could check register&nbsp;SVID_P_IN_ACCUMULATOR in SVID IP to confirm whether MBVR's data could be polled.</p><p>This register is PMSB bank offset&nbsp;0x4088.</p>

++++22611451385 pcanetel
<p style="margin:0in;font-family:Calibri;font-size:11.0pt">DDR pmon
telemetry is observed on IMH1 which is not expected, as the DDR pmon telemetry should be
only on IMH0.</p>

<p style="margin:0in;font-family:Calibri;font-size:11.0pt">&nbsp;<span style="font-size: 11pt;">&nbsp;</span></p>

<p style="margin:0in"><img src="https://hsdes.intel.com/rest/binary/14025850723" data-processed="true" style="width: 483px; height: 386.681px;" /></p>

<p style="margin:0in;font-family:Calibri;font-size:11.0pt">&nbsp;</p><p style="margin:0in;font-family:Calibri;font-size:11.0pt"><br /></p>

<p style="margin:0in;font-family:Calibri;font-size:11.0pt">According to DRAM
RAPL HAS, IMH0 should poll the PWR_IN telemetry fed into VccDDRHV0 VR.</p>

<p style="margin:0in;font-family:Calibri;font-size:11.0pt">&nbsp;</p>

<p style="margin:0in"><img src="https://hsdes.intel.com/rest/binary/14025850725" data-processed="true" style="width: 820.566px; height: 117.766px;" /></p>

<p style="margin:0in;font-family:Calibri;font-size:11.0pt">&nbsp;</p>

<p style="margin:0in;font-family:Calibri;font-size:11.0pt">From &lt;<a href="https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html#d

### Conclusion
not_a_bug

### Component
hw.svid

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
- **Sub-Feature**: SVID
- **Component Path**: hw.svid

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI registers`
- `sv.socket0.imh0.pcodeio_map.showsearch`
- `sv.socket0.imh0.pcudata.pwrBdgtMngr.pmeterData.powerTrackerPMON_0.show`

## Timeline

- **Submitted**: 2025-09-04 10:15:28
- **Closed**: 2025-09-10 03:10:45
- **Days Open**: 5

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
