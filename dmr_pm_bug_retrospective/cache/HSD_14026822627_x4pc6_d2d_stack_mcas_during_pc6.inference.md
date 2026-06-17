# HSD 14026822627: [X4][PC6] D2D Stack MCAs during PC6

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026822627](https://hsdes.intel.com/appstore/article-one/#/14026822627) |
| **Status** | root_caused.awaiting_fix |
| **Priority** | 1-showstopper |
| **Owner** | hmpicosm |
| **Component** | hw.d2d |
| **Defect Die** | soc |
| **Conclusion** | hw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 85% |
| **Feature** | Sideband/D2D | 80% |
| **Sub-Feature** | GPSB | — |

**Reasoning**: conclusion='hw.bug' → HW

## Root Cause Summary

During DMR A0 VV, we are seeing hangs when testing PC6. Issue is sporadic and seen only in a few platforms.

CBB Punit MCA along with D2D MCAs are logged. There is also RC timing out on moving QChannels / PChannels into Q_RUN.

D2D are showing training errors.

TOR TOs are also logged in SCAs.

Timeouts also seen in HAMVF.

PUNIT MCA

  socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.mc_status=0xbe00000000030410

    valid=0x1

    ovr=0x0

    uc=0x1

    en=0x1

    miscv=0x1

    addr

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww18.3]

This HSD missed DCCB last week, it is planned to be discussed in DCCB this week.

﻿[26ww16.4]

Hector reported that the batch has been running stably for over 24 to 36 hours across different systems, suggesting it as a candidate for official release. Vidar and Matthew agreed, but clarified that the final decision lies with the DCCB and Joe Brooks.

Matthew emphasized that Joe Brooks owns the approval process and that all relevant information should be communicated to Joe, the SOC workaround team, Joshy, and DCCB, as this forum cannot approve the release.

Matthew explained the need for an SOC workaround ticket, and if one does not exist, design should notify Jagdish, Joshy, and Bob to document the bug ECO and propose a firmware workaround. The bug ECO must be moved to the 'change defined' state to signal readiness for DCCB review.

﻿[26ww14.1]

5 different systems are being used for experiments, with ongoing data collection and attempts to reproduce failures as requested by Joe, and that a pre-sighting is in place for the new FIVR MCA issue.

Despite multiple attempts and system variations, the team has not yet found a reliable workaround for running systems with PkgC6 enabled, as new issues continue to arise during testing.

﻿[26ww13.3]

Hector reported that Jimmy disabled all timeouts except one and observed stable system operation for two days, suggesting the timeouts may be related to the issue. The team planned to further investigate with the TF.

﻿[26ww12.3]

Die-to-Die Timer and Timeout Issues: The team reviewed ongoing experiments to address timer and timeout issues in die-to-die communication, including increasing timeout delays and running emulation tests, with the goal of achieving a working solution before tape-in.

Joseph described running experiments with increased timeout delays and disabled timeouts, as well as encountering a new signature related to CFCMITD during PkgC exit, indicating ongoing investigation.

The team planned to use emu

### Description
During DMR A0 VV, we are seeing hangs when testing PC6. Issue is sporadic and seen only in a few platforms.

CBB Punit MCA along with D2D MCAs are logged. There is also RC timing out on moving QChannels / PChannels into Q_RUN.

D2D are showing training errors.

TOR TOs are also logged in SCAs.

Timeouts also seen in HAMVF.

PUNIT MCA

  socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.mc_status=0xbe00000000030410

    valid=0x1

    ovr=0x0

    uc=0x1

    en=0x1

    miscv=0x1

    addrv=0x1

    pcc=0x1

    s=0x0

    ar=0x0

    correrrorstatusind=0x0

    corr_err_count=0x0

    fw_upd=0x0

    enh_mca_avail0=0x0

    mca_error_type=0x0

    mca_error_code=0x3

    mccod=0x410

  socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.mc_misc=0x941d00b0

    enh_mca_avail=0x9

    corrected_error_count=0x41

    error_address=0xd00b0

  socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.mc_addr=0x600a4520600a30ee

 D2D MCA

  socket0.cbb0.base.d2d_stack_0.ula_0.ula.ula_mc_st=0xba000040002d0e0f

    valid=0x1

    over=0x0

    uc=0x1

    en=0x1

    miscv=0x1

    addrv=0x0

    pcc=0x1

    s=0x0

    ar=0x0

    corr_err_sts_ind=0x0

    cor_err_cnt=0x1

    fw_upd=0x0

    other_info=0x0

    mscod_spare=0x0

    mscod_code=0x2d

    mcacod_rsvd=0x0

    mcacod_int=0x1

    mcacod_pp=0x3

    mcacod_t=0x0

    mcacod_rrrr=0x0

    mcacod_ii=0x3

    mcacod_ll=0x3

  socket0.cbb0.base.d2d_stack_0.ula_0.ula.ula_mc_misc=0x2ad00200

    prot_msg_info=0x0

    pchannel_state=0x0

    rsvd3=0x0

    phy_state0=0xa

    last_unc_err=0x2d

    cor_err=0x1

    rsvd2=0x0

  SCA MCA

  socket0.imh0.scf.sca.sca8.util.mc_status=0xfe00000000120147

    val=0x1

    over=0x1

    uc=0x1 - UNCORR

    en=0x1

    miscv=0x1

    addrv=0x1

    pcc=0x1

    s=0x0

    ar=0x0

    correrrorstatusind=0x0 - No Tracking

    corr_err_count=0x0

    enh_mca_avail0=0x0

    model_specific_error_code=0x12 - TOR_TIMEOUT

    mca_error_code=0x147

  socket0.imh0.scf.sca

### Comments (latest)
++++14614964254 shijup1
<p>The main cause of hang is IO timeout, Need to enable small hammer WA for these configs.</p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/16029598672" style="width: 903px;" tabindex="-1" /><br /></p>

++++14614964255 rsouthwe
<p>Adding UCIe EV team.</p><p><br /></p><p>It looks like the CBB0&lt;-&gt;IMH1 D2D link is going into trainerror after an L1 exit:</p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp;+----------------------------------------------------------------------------+</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp;|&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; Link State (cbb0_p0_imh1_p4)&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; |</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp;+--------+------+------+--------+-----------+-------+-----------+------------+</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp;| Socket | Die&nbsp; | Port | Module | N-3&nbsp; &nbsp; &nbsp; &nbsp;| N-2&nbsp; &nbsp;| N-1&nbsp; &nbsp; &nbsp; &nbsp;| N&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; |</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp;+--------+------+------+--------+-----------+-------+-----------+------------+</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp;| 0&nbsp; &nbsp; &nbsp; | cbb0 | 0&nbsp; &nbsp; | 0&nbsp; &nbsp; &nbsp; | ACTIVE&nbsp; &nbsp; | L1_L2 | TXSELFCAL | TRAINERROR |</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp;| 0&nbsp; &nbsp; &nbsp; | cbb0 | 0&nbsp; &nbsp; | 1&nbsp; &nbsp; &nbsp; | ACTIVE&nbsp; &nbsp; | L1_L2 | TXSELFCAL | TRAINERROR |</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp;| 0&nbsp; &nbsp; &nbsp; | cbb0 | 0&nbsp; &nbsp; | 2&nbsp; &nbsp; &nbsp; | ACTIVE&nbsp; &nbsp; | L1_L2 | TXSELFCAL | TRAINERROR |</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp;| 0&nbsp; &nbsp; &nbsp; | imh1 | 4&nbsp; &nbsp; | 0&nbsp; &nbsp; &nbsp; | TXSELFCAL | L1_L2 | TXSELFCAL | TRAINERROR |</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp;| 0&nbsp; &nbsp; &nbsp; | imh1 | 4&nbsp; &nbsp; | 1&nbsp; &nbsp; &nbsp; | TXSELFCAL | L1_L2 | TXSELFCAL | TRAINERROR |</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp;| 0&nbsp; &nbsp; &nbsp; | imh1 | 4&nbsp; &nbsp; | 2&nbsp; &nbsp; &nbsp; | ACTIVE&nbsp; &nbsp; | L1_L2 | TXSELFCAL | TRAINERROR |</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp;+--------+------+------+--------+-----------+-------+-----------+------------+</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp;+----------------------------------------------------------------------------+</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp;|&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; Link State (cbb0_p1_im

### Tags
FV_PM,VVblkr_M,SysDebugCloned,SysDebugDccbDone,FIX_PATCH_DMR_AP1_A0_600009A2,FIX_IFWI_DMR_AP1_2026.20.3.04,Primecode_WA_Implemented

### Conclusion
hw.bug

### Component
hw.d2d

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

- **Primary Feature**: Sideband/D2D
- **Sub-Feature**: GPSB
- **Component Path**: hw.d2d

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0xE2`
- `MSR 0x08B`
- `sv.socket0.cbb0.base.d2d_stack_0.ula_0.ula.ula_mc_st`
- `sv.socket0.cbb0.base.d2d_stack_0.ula_0.ula.ula_mc_st.show`
- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.mc_status`
- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.mc_status.show`
- `sv.socket0.imhs.d2d_stack.d2d_stacks.ucie_phy.ucie_ohsphy_shareds.ucie_ohsphy_shared_cr_rcomp_glue_misc2.rcomp_mbtrain_cal_en`

## Timeline

- **Submitted**: 2026-01-14 06:06:36
- **Root Caused**: 2026-03-26 18:47:05
- **Days Open**: 127

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
