# HSD 14027324884: MIO DVP inaccessible once MIO TCG has been entered

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027324884](https://hsdes.intel.com/appstore/article-one/#/14027324884) |
| **Status** | complete.wont_validate |
| **Priority** | 2-high |
| **Owner** | rakeshr1 |
| **Component** | hw.power |
| **Defect Die** | ioe |
| **Conclusion** | doc |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Reset/Boot | 52% |
| **Sub-Feature** | Boot | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

Summary:

========

The DVP PCIe Gen6 is prepared to receive data by default but almost to arrive to EDK menu the value of the DVP register is altered and produce an unexpected behavior.

Impact:

========

DVP doesn't work as expected and unable to perform PCIe scenarios.

Details:

========

We booted and we run many halt/go operations in order to check the BIOS affected the DVP register values and we catches before the EDK menu appears. Below you can see the changes before and after the halt 

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww12.4]
* What is the root-cause and lets get this root-caused please

﻿[26ww12.3]

Arc/Microarchitecture Bug: Joseph confirmed the root cause of a feature bug defined at the arc/microarchitecture level, discussed a workaround involving RC register overwrite, and planned to document the solution and update HSD.

Joseph stated that the feature is defined in a way that prevents correct operation, confirming it as an arc/microarchitecture bug rather than a connection issue.

Workaround Proposal: The proposed workaround involves having the ITH tool forcibly send an RC overwrite to activate the queue on the DVP, though the logistics of this approach are still being evaluated.

﻿[26ww12.1]

Joe confirmed this is a HW issue (RTL fix for DVP access), we'll probably make ITH work around it. This is a MIO stack level feature with an IO die.

### Description
Summary:

========

The DVP PCIe Gen6 is prepared to receive data by default but almost to arrive to EDK menu the value of the DVP register is altered and produce an unexpected behavior.

Impact:

========

DVP doesn't work as expected and unable to perform PCIe scenarios.

Details:

========

We booted and we run many halt/go operations in order to check the BIOS affected the DVP register values and we catches before the EDK menu appears. Below you can see the changes before and after the halt operation. 

The bios we used for this experiment is: \\amr.corp.intel.com\ec\proj\debug\DMR\User\_Groups\pcie\ifwi\SPK_test_Gen5PCIE_DMR_PCIe_AVEPHYFlexBus_BIOS_0.005_OKSDCRB1.86B.2025.35.3.01_2688.D02_6020095E_1P0_NonIPClean_Trace_DebugSigned_update_primecode_pcode.bin

Please check the Bios log in the attachment section.

In [134]: sv.socket0.imh0.dfd_dvp.dvp_fblp_pclk_7_0_mio_1.dvp_main.dvp_status.show

--------> sv.socket0.imh0.dfd_dvp.dvp_fblp_pclk_7_0_mio_1.dvp_main.dvp_status.show()

0x00000000 : rsvd_31_31 (31:31) (ro) -- Reserved

0x00000000 : update_lta_fsm_status (30:29) (ro/v) -- Current value of LTA Status state machine:

        00: IDLE                                        0...

0x00000000 : qactivedtfstatus (28:28) (ro/v) -- current value of *dvp_dtf_qactive* signal (if present, otherwise 0).

0x00000000 : qactivestatus (27:27) (ro/v) -- current value of *dvp_qactive* signal.

0x00000001 : qreqstatus (26:26) (ro/v) -- current value of *dvp_qreqn* signal.

0x00000002 : qsmstatus (25:23) (ro/v) -- current Quiescence State Machine Status (000: Q_STOPPED; 001: Q_EXIT; 010: ...

0x00000001 : ltaval (22:22) (ro/v) -- LTA Valid (LTAVal): This bit is set to indicate that the LTA counter is valid

0x00000000 : periodictsstat (21:21) (ro/v) -- Periodic TS Status (PeriodicTSStat): Logical OR of all packetizers nee...

0x00000003 : ucifsmstat (20:19) (ro/v) -- UCI FSM Status (UCIFSMStat): Current state of DVP arbiter's UCI FSM. 00: I...

0x00000000 : dtfactstat (18:18)

### Comments (latest)
++++14615174542 senthil1
Setting sub_forum=vt.dfx

++++14615174543 jiaxinno
<p>&nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Garcia Rodriguez, Federico</span>&nbsp;,</p><p><br /></p><p>Can you check below&nbsp; qsm_status register under SPK? is qsm_status&nbsp; register change to 0？</p><!--StartFragment--><!--EndFragment--><p><br /></p><p>#define SPK_GLOBAL_STS_SB_SPK_REG&nbsp; &nbsp; &nbsp; &nbsp; (0x00000004U)</p><p>#define SPK_GLOBAL_STS_SB_SPK_DEFAULT&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;0x00000000</p><p><br /></p><p>typedef union {</p><p>&nbsp; struct {</p><p>&nbsp; &nbsp; UINT32 idle : 1;</p><p><br /></p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; /* Bits[0:0], Access Type=RO/V, default=0x00000000*/</p><p><br /></p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; /*</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;When set, indicates that all internal buffers</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;inside of Sierra Peak are empty and all credits</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;have been returned to the upstream debug trace</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;fabric arbiter. Note that this does not ensure</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;that there are transactions inflight to the</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;Sierra Peak upstream on the debug trace fabric.</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;Note that this does not ensure that all memory</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;writes from Sierra Peak have completed in</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;memory; rather it means that Sierra Peak has</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;completed sending all memory transactions.</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; */</p><p><br /></p><p>&nbsp; &nbsp; UINT32 wrap_stat : 1; /**&lt; Memory Wrap Status */</p><p><br /></p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; /* Bits[1:1], Access Type=RO/V, default=0x00000000*/</p><p><br /></p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp

### Tags
val_agent,SysDebugCloned, PSF=Y,SysDebugDccbBypass

### Conclusion
doc

### Component
hw.power

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

- **Primary Feature**: Reset/Boot
- **Sub-Feature**: Boot
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.dfd_dvp.dvp_fblp_pclk_7_0_mio_1.dvp_main.dvp_status.show`
- `sv.socket0.imh0.dfd_dvp.dvp_fblp_pclk_7_0_mio_1.dvp_main`

## Timeline

- **Submitted**: 2026-03-10 03:10:17
- **Root Caused**: 2026-03-20 23:11:42
- **Closed**: 2026-05-06 02:46:57
- **Days Open**: 56

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
