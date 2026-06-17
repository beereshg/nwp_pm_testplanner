# HSD 14026935410: [DMR][X1 A0 VV][HWP OOB] HWP OOB Request cannot override HWP_REQUEST_PKG

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026935410](https://hsdes.intel.com/appstore/article-one/#/14026935410) |
| **Status** | rejected.not_a_defect |
| **Priority** | 2-high |
| **Owner** | egomezgo |
| **Component** | hw.power |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 80% |
| **Sub-Feature** | HWP | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

In the case where the HWP_REQUEST_PKG request is fixing ratio we cannot restore HWP to choose a ratio using CPU utilization using the OPC_HWP_CONTROLS:

1) Setting IA32_HWP_REQUEST.PACKAGE_CONTROL (MSR 0x774) bit on all cores to be controlled by the HWP_REQUEST_PKG (MSR 0x772) request. 

After write:

2) Fix ratios to 0xA using inband HWP_REQUEST_PKG (MSR 0x772):

After write:

3) Run highly scalable core workload (system was idle before)

WL command line:

4) Trying to reenable HWP Pstates base

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww09.3]

Carlos demonstrated that enabling all HWP overrides does not prevent in-band inputs from clipping ratios, due to the lack of a 'desired' field in the architecture. Nilanjan and Anatoli discussed the implications and agreed that this represents a definition gap.

Nilanjan noted that previous generations managed out-of-band overrides differently, and the team needs to review how pCode and Primecode handle the desired field. The group agreed to follow up with Ido and architecture teams to resolve the gap.

[26ww08.3]

Ido will check this one again and response the HSD.  Anatoli will sync with Vladislav and update the HSD..

[26ww07.3]

Vladislav was assisting with analysis, referencing similar past issues, and Anatoli agreed to send a reminder to Vladislav to expedite feedback.

﻿[26ww07.1]

pCode tracker is available and pending review by pCoder.

﻿[26ww06.3]

HWP ratio cannot be restored when HWP_REQUEST_PKG is used to fix a ratio while OPC_HWP_CONTROLS are active.

May result in improper CPU utilization and suboptimal power management due to incorrect ratio settings by HWP.

Emiliano from FV team engaged with CBB arch and pCode teams for debug. Currently waiting from pCode/arch teams on the requested data to determine next steps.

﻿[26ww06.1]

Emiliano will provide a pCode trace as requested

[26ww05.4]

AR Emiliano to start conversation with Anatoli for next steps. Carlos suggest this probably can be fixed in FW but PMA HW is the one that resolves this, implying there could potentially be an RTL issue but fixed/WA by FW. Bumping to high.

### Description
In the case where the HWP_REQUEST_PKG request is fixing ratio we cannot restore HWP to choose a ratio using CPU utilization using the OPC_HWP_CONTROLS:

1) Setting IA32_HWP_REQUEST.PACKAGE_CONTROL (MSR 0x774) bit on all cores to be controlled by the HWP_REQUEST_PKG (MSR 0x772) request. 

After write:

2) Fix ratios to 0xA using inband HWP_REQUEST_PKG (MSR 0x772):

After write:

3) Run highly scalable core workload (system was idle before)

WL command line:

4) Trying to reenable HWP Pstates based on core utilization using out of band OPC_HWP_CONTROLS:
After write:

5) After out of band request cores are not resolving 

OPC_HWP_CONTROLS.MAXIMUM_PERFORMANCE 

ratio, they are still clipped at inband request:

6) After ending the core workload, and having the cores idle, core ratios are not lowered to OPC_HWP_CONTROLS.MINIMUM_PERFORMANCE ratio:

### Comments (latest)
++++14615010268 egomezgo
Waiting for arch feedback to confirm is an issue.

++++14615010269 imelamed
<span data-teams="true">Can you please add screenshots for steps 1, 2, 3 of the written MSR to see what fields were written?</span>

++++14615010270 egomezgo
Updated description with MSR fields

++++14615010271 imelamed
<p style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;">The configuration appears to be correct.</p><p style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;">A quick review of the latest Pcode did not reveal any references to OPC_HWP_CONTROLS.</p><p style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;">I recommend reaching out to the Pcode owners for further debugging and considering promoting to sighting if necessary.</p>

++++14615010272 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14026913045.

++++14615017651 egomezgo
Having trouble to get a pcode trace in order to engage with pcode team. Need some permissions to update the collateral for the pcode trace tool. Waiting for it.

++++14615055186 egomezgo
I added a Pcode tracker, a Pcode vars dump log and GPSB dump log in the attachments.

++++14615075618 egomezgo
Already working  @Barkanass, Vladislav verifying the wrong behavior. Waiting feedback from him.

++++14615085356 egomezgo
I talked with Vlad and we both agree that a changed is needed to overcome Pcode consuming inband input when out of band override is enabled. We need input from  @Melamed, Ido  When inband desired_performance input starts to be ignored?   OPC_HWP_CONTROLS.MIN OPC_HWP_CONTROLS.MAX INBAND.DESIRED consumed as an input 0 0 Yes 1 0 Yes ? 0 1 Yes ? 1 1 No ?
++++22611774866 imelamed
Hi Emiliano, OOB takes precedence over INBAND whenever both ENABLE_OUT_OF_BAND_AUTONOMOUS and ENABLE_HWP are set to 1 in MISC_PWR_MGMT (MSR 1AAh). Let me know if you have any questions, Ido. 
++++14615110864 mbfausto
Team, no updates since Wednesday.  Sounds like Vlad has agreed there is an issue, so do we have root-cause and what the defect is?  Is this a pCode bug?

++++14615114835 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14026935410] of [component=fw.pcode] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [bug] to [heia_soc.bugeco.id=14027160346] of [component=dmrcbbbase.soc.pm.pcode] in [release=dmrcbbbase-a0]

++++14615120108 coramire
In this scenario we are in HWP Native mode no OOB mode so enable_out_of_band_autonomous bit is not set, but oob override using opc_hwp_controls is available in native Mode In [33]: sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.misc_pwr_mgmt2.enable_out_of_band_autonomous Out[33]: 0x0 After Enabling HWP Override in OPC HWP Controls In [37]: sv.sockets.imh0.punit.ptpcfsms.ptpcfsms.opc_hwp_controls.show() 0x00000000 : rsvd3 (63:44) (rw) -- Reserved. 0x00000000 : alt_epb (43:40) (rw) -- Out-of-b

### Tags
FV_PM

### Conclusion
not_a_bug

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: HWP
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x774`
- `MSR 0x772`
- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.misc_pwr_mgmt2.enable_out_of_band_autonomous`
- `sv.socket0.cbb0.compute1.module8.core0.ucode_cr_perf_status.core_ratio_100mhz`
- `sv.socket0.cbb0.compute1.module8.core0.pcu_cr_ia32_hwp_request_pkg.desired_performance`

## Timeline

- **Submitted**: 2026-01-29 20:38:54
- **Closed**: 2026-03-13 04:53:50
- **Days Open**: 42

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
