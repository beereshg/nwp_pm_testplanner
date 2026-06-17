# HSD 22021541919: [DMR][X1 A0 PO] PkgC flow staying at PC2 Noise Quiesce, reason=Idle not yet achieved on fused parts

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22021541919](https://hsdes.intel.com/appstore/article-one/#/22021541919) |
| **Status** | rejected.merged |
| **Priority** | 2-high |
| **Owner** | hmpicosm |
| **Component** | hw.uncore |
| **Defect Die** | soc |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | C6 | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

Summary:

========

We are seeing PC6 residency of 0%. PC2 residency is ~50% stable.   

Impact:

========

Low Power KPIs cannot be achieved without PC6 enabled

Details:

========

REPLACE  with failure and triage details.

==> System configuration ...

Fused part, 4 cores, single DIMM

==> BIOS/Patch/IFWI/BKC/CI Versions ...

\\amr\ec\proj\debug\DMR\Tools\IFWI\Approved\UCC_A0\OKSDCRB1.86B.2025.35.3.01_2688.D02_6020095E_1P0_NonIPClean_Trace_DebugSigned_update_primecode_pcode.bin

==> Reproduci

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
Failing Signature: 
 
We are seeing PC6 residency of 0%. PC2 residency is ~50% stable

 

Nothing else to chase here merge with known ULA bug 

WW36.4

 

We took a Primecode FW debug trace showing that we are not progressing further PC2 Noise Quiesce, due to Idle not yet achieved.-> Both IMH getting to the same state

 

From Joe Brooks “To clarify the need for this:  sv.sockets.imhs.isa.isa_mio_1.spare_cfg0=0x18000

When MIO-A is configured as PCIE/CXL, the ULA IP is to be disabled.  However, the current workaround for the ULA IP disable sideband bug is to keep ULA IP enabled.  This ISA injection masks the ULA PCh input in this scenario”

Can we get ULA out of PC6 flow? The current recipe works for 1 socket , for 2 socket we still need to discuss this

Next)
Joe) Please define the recipe we need for 1 socket for Prime Code ( Maybe merge this in the same bug as part of the same WA)

### Description
Summary:

========

We are seeing PC6 residency of 0%. PC2 residency is ~50% stable.   

Impact:

========

Low Power KPIs cannot be achieved without PC6 enabled

Details:

========

REPLACE  with failure and triage details.

==> System configuration ...

Fused part, 4 cores, single DIMM

==> BIOS/Patch/IFWI/BKC/CI Versions ...

\\amr\ec\proj\debug\DMR\Tools\IFWI\Approved\UCC_A0\OKSDCRB1.86B.2025.35.3.01_2688.D02_6020095E_1P0_NonIPClean_Trace_DebugSigned_update_primecode_pcode.bin

==> Reproducibility ...

Always

==> Lightswitch discoveries ...

==> Experiment results ...

Please review 
http://goto/dmrtriage

   for Debug Triage suggestions and Guidance

Please review 
http://goto/dmrsubmit
 for Sighting submission guidelines and expectations.

### Comments (latest)
++++22611450496 hmpicosm
<p>We took a Primecode FW debug trace showing that we are not progressing further PC2 Noise Quiesce, due to Idle not yet achieved.</p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/14025849662" style="width: 1532px;" /><br /></p>

++++22611450497 hmpicosm
Attaching Primecode FW trace.

++++22611450498 hmpicosm
<p>We polled ISA clkreq and QChannel QActive status and noticed the following:</p><ul><li>From ISA, d2d stacks and PCIeGen4 are not deasserting clk_req.</li><li><span style="white-space: pre">	</span>D2D stacks are deasserting QActive though:</li></ul><p>---------------------------------------------------------------------------------------------------</p><p>&nbsp; &nbsp; &nbsp; imh0.resctrl.rc_cfcmem_ew.resctrl_prvt_idle_late_regs0.i_qch_status.qactive_status (3:3)</p><p>---------------------------------------------------------------------------------------------------</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;Bin |&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; Dec |&nbsp; &nbsp; &nbsp; &nbsp; Hex |&nbsp; &nbsp;socket0&nbsp; |</p><p>---------------------------------------------------------------------------------------------------</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;0b0 |&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 0 |&nbsp; &nbsp; &nbsp; &nbsp; 0x0 |&nbsp; &nbsp; 98.2%&nbsp; &nbsp;|</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;0b1 |&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 1 |&nbsp; &nbsp; &nbsp; &nbsp; 0x1 |&nbsp; &nbsp; &nbsp;1.8%&nbsp; &nbsp;|</p><p>---------------------------------------------------------------------------------------------------</p><p><br /></p><p><br /></p><p>---------------------------------------------------------------------------------------------------</p><p>&nbsp; &nbsp; &nbsp; imh0.resctrl.rc_cfcmem_ew.resctrl_prvt_idle_late_regs1.i_qch_status.qactive_status (3:3)</p><p>---------------------------------------------------------------------------------------------------</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;Bin |&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; Dec |&nbsp; &nbsp; &nbsp; &nbsp; Hex |&nbsp; &nbsp;socket0&nbsp; |</p><p>---------------------------------------------------------------------------------------------------</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;0b0 |&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 0 |&nbsp; &nbsp; &nbsp; &nbsp; 0x0 |&nbsp; &nbsp;100.0%&nbsp; &nbsp;|</p><p>---------------------------------------------------------------------------------------------------</p><p><br /></p><p>-------------------------------------------------

### Conclusion
no_root_cause.rejected

### Component
hw.uncore

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

- **Primary Feature**: Core C-States
- **Sub-Feature**: C6
- **Component Path**: hw.uncore

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_pch_regs0.dev_pactive_status`
- `sv.socket0.imh1.resctrl.rc_mio_ew.resctrl_prvt_pch_regs0.dev_pactive_status`
- `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_pch_regs0.ctrl_pactive_status`
- `sv.socket0.imh1.resctrl.rc_mio_ew.resctrl_prvt_pch_regs0.ctrl_pactive_status`
- `sv.socket0.cbb0.base.sncu_top.sncevents.ncupmonglobalcontrol.frz`

## Timeline

- **Submitted**: 2025-09-04 00:49:51
- **Closed**: 2025-09-10 09:21:13
- **Days Open**: 6

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
