# HSD 14026152660: [X1 A0] MIO Trunk Clock gating - QActive is not deasserting for MIOs with unpopulated ports

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026152660](https://hsdes.intel.com/appstore/article-one/#/14026152660) |
| **Status** | root_caused.awaiting_fix |
| **Priority** | 2-high |
| **Owner** | elenamur |
| **Component** | fw.primecode.wa |
| **Defect Die** | ioe |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 75% |
| **Sub-Feature** | TRL | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Configuration
 

- PCIe testcard supporting L0

.

Responder QActive signals are not being deasserted for 3 instances for iMH0 & IMH1

sv.sockets.imhs.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regss.r_qch_status.qactive_status

Out[91]:

socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs0.r_qch_status.qactive_status
- 
0x00000001

socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs1.r_qch_status.qactive_status
- 
0x00000001

socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_reg

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww03.3]

New recipe is defined and in progress, Mythili working on the patch, debug PR is up doing local CD validation on primecode side. Probably getting the patch today if everything is good. Elena, Tensea or Hector to test the patch.

[26ww03.1]

Elena and Joe are rerunning the original task and updating the test script to match the bit settings used in the ULA workaround, aiming to determine if these changes affect the outcome and to clarify why certain settings were chosen.

Mythili raised questions regarding the necessity of setting bit #17 and whether the value should be cumulative or overridden, with Elena tasked to evaluate these aspects and confirm the correct approach.

Mythili is waiting for Elena and Joe to finalize the workaround details before proceeding to provide a debug patch, ensuring all configuration and register settings are properly addressed.

[26ww02.3]

Mythili from primecode team is currently working on the design of the test patch with JoeB/Alex for testing, one it is ready team will post the patch. There is already a sighting for the ULA sideband hang, JoeB can provide the ticket number, so this HW WA will be only applied to A0. There is also a Primecode ticket which can be used to expand this ticket instead of creating a new one. Sysdebug to syncup with primecode to agree on the paperwork to move this sighting to root cause

[26ww02.1]

Elena reported implementing a workaround in pysv to achieve MIO trunk location, with plans to push the solution as a primecode patch after syncing with Joe, Tensae, and Hector. Hector outlined that the next step, led by Tensae, is to cross-check the workaround with PkgC to ensure that the new recipe does not break PkgC functionality, as delegating can occur both during and outside of PkgC.

Vidar instructed Hector and Elena to synchronize with Tensae and participate in the group chat to review results and determine if the workaround can be productized without impacting other features.

[25ww51.3]

Ele

### Description
Configuration
 

- PCIe testcard supporting L0

.

Responder QActive signals are not being deasserted for 3 instances for iMH0 & IMH1

sv.sockets.imhs.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regss.r_qch_status.qactive_status

Out[91]:

socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs0.r_qch_status.qactive_status
- 
0x00000001

socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs1.r_qch_status.qactive_status
- 
0x00000001

socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs2.r_qch_status.qactive_status
- 
0x00000001

socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs3.r_qch_status.qactive_status
- 0x00000000

socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs4.r_qch_status.qactive_status
- 0x00000000

socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs5.r_qch_status.qactive_status
- 0x00000000

socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs6.r_qch_status.qactive_status
- 0x00000000

socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs7.r_qch_status.qactive_status
- 0x00000000

socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs8.r_qch_status.qactive_status
- 0x00000000

socket0.imh1.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs0.r_qch_status.qactive_status
-
 0x00000001

socket0.imh1.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs1.r_qch_status.qactive_status
- 
0x00000001

socket0.imh1.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs2.r_qch_status.qactive_status
- 
0x00000001

socket0.imh1.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs3.r_qch_status.qactive_status
- 0x00000000

socket0.imh1.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs4.r_qch_status.qactive_status
- 0x00000000

socket0.imh1.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs5.r_qch_status.qactive_status
- 0x00000000

socket0.imh1.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs6.r_qch_status.qactive_status
- 0x00000000

socket0.imh1.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regs7.r_qch_status.qactive_status
- 0x00000000

socket0.imh1.resctrl.rc

### Comments (latest)
++++14614760349 hmpicosm
<p>Logs captured during debug.</p><p><br /></p><p>We are seeing Noise QCh deassertion as seen by RC (i_qch_status). Late QCh is never deasserted.</p><p><br /></p><p>Some questions?</p><ol><li>Is it correct that noise QCh QActive is deasserting when card is on L0 state?</li></ol><p>Port pxp3.port0 (PCIE-FM) is x16 (ilw=x16) (GEN6/dP0x6/uP0x6). LTSSM = UP_L0,&nbsp;

<span style="background-color: rgb(0, 255, 0);">resctrl_prvt_idle_noise_regs1.i_qch_status.qactive_status = 0x0</span></p><ol><li>Should we expect late QCh QActive also deasserting?&nbsp;</li><li>How unpopulated ports and L1 are supposed to behave?<!--EndFragment--><!--EndFragment--></li></ol><p><br /></p><p>In [60]: ltssm.sls()</p><p>=============================================</p><p>SOCKET0</p><p>=============================================</p><p>&nbsp; &nbsp; &nbsp; &nbsp; P0 P1 P2 P3 P4 P5 P6 P7</p><p>PXP0 is x1 x1 x1 x1</p><p>PXP1 is x16 -- -- -- -- -- -- --</p><p>PXP3 is x16 -- -- -- -- -- -- --</p><p>PXP4 is x16 -- -- -- -- -- -- --</p><p>PXP8 is x4 -- -- --</p><p>PXP9 is x16 -- -- -- -- -- -- --</p><p>PXP11 is x16 -- -- -- -- -- -- --</p><p>PXP12 is x16 -- -- -- -- -- -- --</p><p>Port pxp0.port0 (PCIE-NFM) is x1 (ilw=x1) (GEN2/-6.0dB). LTSSM = UP_L0</p><p>Port pxp0.port1 (PCIE-NFM) is x1 (ilw=x1) (GEN2/-6.0dB). LTSSM = UP_L0</p><p>Port pxp0.port2 (PCIE-NFM) is x1 (ilw=x1) (GEN1/-3.5dB). LTSSM = UP_L0</p><p>Port pxp0.port3 (PCIE-NFM) is x1 (ilw=x1) (GEN4/dP0x7/uP0x6). LTSSM = UP_L0</p><p>Port pxp1.port0 (PCIE-NFM) is x-- (ilw=x--) (GEN1/-3.5dB). LTSSM = POL_ACTIVE</p><p>Port pxp3.port0 (PCIE-FM) is x16 (ilw=x16) (GEN6/dP0x6/uP0x6). LTSSM = UP_L0</p><p>Port pxp4.port0 (PCIE-NFM) is x-- (ilw=x--) (GEN1/-3.5dB). LTSSM = POL_ACTIVE</p><p>Port pxp8.port0 (PCIE-NFM) is x-- (ilw=x--) (GEN1/-3.5dB). LTSSM = DET_QUIET</p><p>Port pxp9.port0 (PCIE-NFM) is x-- (ilw=x--) (GEN1/-3.5dB). LTSSM = POL_ACTIVE</p><p>Port pxp11.port0 (PCIE-NFM) is x-- (ilw=x--) (GEN1/-3.5dB). LTSSM = DET_QUIET</p><p>Port pxp12.port0 (PCIE-NFM) is x-- (ilw=x--) (GEN1/-3.5dB). LTSSM = POL_ACTIVE</p><div><br /></div><div><br /></div><div><div>In [63]: sv.socket0.imhs.resctrl.rc_mio_ew.showsearch('qactive_status','f')</div><div><span style="background-color: rgb(255, 255, 0);">resctrl_prvt_idle_late_regs0.i_qch_status.qactive_status = 0x1</span></div><div><span style="background-color: rgb(255, 255, 0);">resctrl_prvt_idle_late_regs0.r_qch_status.qactive_status = 0x1</span></div><div><span style="background-color: rgb(255, 255, 0);">resctrl_prvt_idle_late_regs1.i_qch_status.qactive_status = 0x1</span></div><div><span style="background-color: rgb(255, 255, 0);">resctrl_prvt_idle_late_regs1.r_qch_status.qactive_status = 0x1</span></div><div><span style="background-color: rgb(255, 255, 0);">resctrl_prvt_idle_late_regs2.i_qch_status.qactive_status = 0x1</span></div><div><span style="background-color: rgb(255, 255, 0);">resctrl_prvt_idle_late_regs2.r_qch_status.qactive_status = 0x1</span></div><div>

### Tags
FV_PM,SysDebugCloned,SysDebugCloned,SysDebugDccbDone, PSF=Y,SysDebugDccbDriver

### Conclusion
hw.arch

### Component
fw.primecode.wa

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
- **Sub-Feature**: TRL
- **Component Path**: fw.primecode.wa

## Firmware Touchpoints

### BIOS
- `Bios knob`

## Key Registers

- `sv.socket0.imhs.resctrl.rc_mio_ew.showsearch`
- `sv.socket0.imh0.pi6.pcieg6.pxp3.cxp.port0.linkcap.aspmsup`
- `sv.socket0.imh0.pi6.pcieg6.pxp3.cxp.port0.linkctl.aspmctl`
- `sv.socket0.imhs.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regss.qch_fsm_policy.enable_auto_idle`
- `sv.socket0.imhs.resctrl.rc_mio_ew.resctrl_prvt_idle_noise_regss.qch_fsm_policy.enable_auto_idle`

## Timeline

- **Submitted**: 2025-10-30 01:52:48
- **Root Caused**: 2026-01-28 05:21:41
- **Days Open**: 203

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
