# HSD 14025929892: [X1 A0 PO] Primecode Qch config for PkgC is affecting the PCIe UIO DVPs

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025929892](https://hsdes.intel.com/appstore/article-one/#/14025929892) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | rakeshr1 |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Reset/Boot | 52% |
| **Sub-Feature** | Boot | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

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
[25ww39.1]
The Primecode WA definition for the HW bug 14024668474 is not correct. We need to adjust the WA definition and Primecode will implement accordingly.
Vidar will follow up later and promote this to a spec bug.

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
++++14614638654 jsbrooks
Root-cause:  Bug in 14024668474 workaround definition. MIO TCG (Trunk Clock Gating) gates the trunk clock based on RC detecting idleness in MIO stack via QCh.   One of the PkgC HW bug workarounds (14024668474) masks the Qactive from all DVP in IMH.  That workaround affects MIO TCG also, which was missed in the patch definition.  The side effect is that TCG entry will not account for DVP status.  Further, TCG exit will not cause noise QCH (DVP) to exit Q_STOPPED; each QCH is trigged independently. Revised workaround proposal (in alignment w/ Arch):     - For RC_MIO_EW, Primecode to apply the '474 w/a on PkgC entry: RESCTRL_QCH_NOISE_<all>_CR_I_QCH_CTRL.FORCE_QACTIVE_ENABLE = 1 RESCTRL_QCH_NOISE_<all>_CR_I_QCH_CTRL.FORCE_QACTIVE_VALUE = 0   - For RC_MIO_EW, on PkgC exit: RESCTRL_QCH_NOISE_<all>_CR_I_QCH_CTRL.FORCE_QACTIVE_ENABLE = 0 RESCTRL_QCH_NOISE_<all>_CR_I_QCH_CTRL.FORCE_QACTIVE_VALUE = 0

++++14614639018 agraback
To get an updated workaround definition, this sighting should be promoted first to a spec bug so it can be used to update the HW WA recipe from DCCB who will then clone new tickets for primecode. Can follow the cloning example from this unrelated Memory sighting 14025847187 [X1 A0 PO] MC reports DIMM Temp as 25'C when TSOD reports 30'C

++++14614645873 vwang 
Sysdebug is investigating the right cloning for the correct set of the HW WA bug 14024668474.


++++14614649636 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14025929892] of [component=hw.dfd] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [spec] to [server.bugeco.id=14025960856] of [component=soc.top] in [release=dmrhub-a0]

++++14614673807 vwang
Waiting DCCB's direction for the coming PrimCode patch.
++++1667087785 spmukher
AR Patch Board to confirm fix availability in UP/IFWI.  Latest trace status:  ===========|=====================|==============================|======================|=========================|================|==============================================================================================================   HSD ID   |     TICKET TYPE     |           RELEASE            |      COMPONENT       |      STATUS.REASON      |     STATE      |                                                 TICKET NOTES ===========|=====================|==============================|======================|=========================|================|============================================================================================================== 14025874985|   Si Pre-Sighting   |   package.dmrap-ucc-x1-a0    |     fw.primecode     |root_caused.awaiting_fix |  WAIT_FIX_REL  |[P]=SS [Conclusion]=hw.arch  [BugID]=14025960856  [Die]=ioe  [DccbBypass]  [Fix]=fw/permanent/A0/14026072509 14025929892|     Si Sighting     |   package.dmrap-ucc-x1-a0    |     fw.primecode     |root_caused.awaiting_fix |  WAIT_FIX_REL  |[P]=H  [Conclusion]=hw.arch  [BugID]=14025960856  [Die]=ioe  [DccbBypass]  [Fix]=[o]fw/permanent/A0/14

### Tags
SysDebugCloned,SysDebugCloned,SysDebugDccbBypass,FWTF_PO_UNBLOCKED,FIX_PATCH_DMR_AP1_A0_6000097D,FIX_IFWI_DMR_AP1_2025.47.1.01,FIX_BKC_OKS_DMR_AP1_2025WW47,cov.pm.pkgc6, PSF=Y

### Conclusion
hw.arch

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

- **Primary Feature**: Reset/Boot
- **Sub-Feature**: Boot
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.dfd_dvp.dvp_fblp_pclk_7_0_mio_1.dvp_main.dvp_status.show`

## Timeline

- **Submitted**: 2025-09-18 05:25:18
- **Root Caused**: 2025-09-23 04:19:01
- **Closed**: 2026-03-10 18:19:36
- **Days Open**: 173

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
