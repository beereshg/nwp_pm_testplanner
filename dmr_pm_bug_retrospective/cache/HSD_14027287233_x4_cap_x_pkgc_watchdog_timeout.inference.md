# HSD 14027287233: [X4] CAP x Pkgc Watchdog timeout

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027287233](https://hsdes.intel.com/appstore/article-one/#/14027287233) |
| **Status** | rejected.filed_by_mistake |
| **Priority** | 2-high |
| **Owner** | spullell |
| **Component** | hw.memory |
| **Defect Die** | ioe |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Core C-States | 52% |
| **Sub-Feature** | C1 | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

System hung before memicals_pause and memic traffic were started.
No alerts seen by show log so CA harasser probably hasn't started injection yet.

02-19 02:00:RESULT   :  socket0.imh0.punit.ras.gpsb.mc_status=0xfa00000000200402
02-19 02:00:RESULT   :    valid=0x1
02-19 02:00:RESULT   :    ovr=0x1
02-19 02:00:RESULT   :    uc=0x1 - UNCORR
02-19 02:00:RESULT   :    en=0x1
02-19 02:00:RESULT   :    miscv=0x1
02-19 02:00:RESULT   :    addrv=0x0
02-19 02:00:RESULT   :    pcc=0x1
02-19 02:00:RESULT  

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww11.3]

Memory team Siva summarized the types of failures observed, including Punit errors and timeouts, and described the process of collecting logs and reproducing failures manually for further analysis.

Joseph and Siva discussed the status of SSR enablement and related workarounds, clarifying that recent tests have SSR disabled and that manual workarounds have been applied during failure reproduction.

Joseph determined that the memory controller, not the Punit, is responsible for the observed failures, and recommended further offline analysis to confirm the root cause and identify the appropriate team for follow-up.

Siva agreed to attempt further manual reproductions and provide systems in the failed state for Joseph to collect additional data, focusing on matching the fail state to previous SSR cap error root causes.

ww10.5

Moving to PM sysdebug for further debug after Joe Brooks reviewed the sighting and agreed with mem sysdebug recommendation.

Memicals only
 : too many denies in a row. And getting RC saying timeout waiting on voltage adapters.

Next Steps:

1) Max) Move to PM sysdebug.

### Description
System hung before memicals_pause and memic traffic were started.
No alerts seen by show log so CA harasser probably hasn't started injection yet.

02-19 02:00:RESULT   :  socket0.imh0.punit.ras.gpsb.mc_status=0xfa00000000200402
02-19 02:00:RESULT   :    valid=0x1
02-19 02:00:RESULT   :    ovr=0x1
02-19 02:00:RESULT   :    uc=0x1 - UNCORR
02-19 02:00:RESULT   :    en=0x1
02-19 02:00:RESULT   :    miscv=0x1
02-19 02:00:RESULT   :    addrv=0x0
02-19 02:00:RESULT   :    pcc=0x1
02-19 02:00:RESULT   :    s=0x0
02-19 02:00:RESULT   :    ar=0x0
02-19 02:00:RESULT   :    thrs_err_st=0x0
02-19 02:00:RESULT   :    corr_err_count=0x0
02-19 02:00:RESULT   :    fw_upd=0x0
02-19 02:00:RESULT   :    other_info=0x0
02-19 02:00:RESULT   :    msec_fw=0x0
02-19 02:00:RESULT   :    msec_hw=0x2
02-19 02:00:RESULT   :    msec_uc=0x0
02-19 02:00:RESULT   :    mccod=0x402
02-19 02:00:RESULT   :  socket0.imh0.punit.ras.gpsb.mc_misc=0x3002010d8200
02-19 02:00:RESULT   :    model_specific_information=0x18010086c1
02-19 02:00:RESULT   :    address_mode=0x0
02-19 02:00:RESULT   :    recoverable_address_lsb=0x0
02-19 02:00:RESULT   :
02-19 02:00:RESULT   :  socket0.imh1.punit.ras.gpsb.mc_status=0xfa00000000200402
02-19 02:00:RESULT   :    valid=0x1
02-19 02:00:RESULT   :    ovr=0x1
02-19 02:00:RESULT   :    uc=0x1 - UNCORR
02-19 02:00:RESULT   :    en=0x1
02-19 02:00:RESULT   :    miscv=0x1
02-19 02:00:RESULT   :    addrv=0x0
02-19 02:00:RESULT   :    pcc=0x1
02-19 02:00:RESULT   :    s=0x0
02-19 02:00:RESULT   :    ar=0x0
02-19 02:00:RESULT   :    thrs_err_st=0x0
02-19 02:00:RESULT   :    corr_err_count=0x0
02-19 02:00:RESULT   :    fw_upd=0x0
02-19 02:00:RESULT   :    other_info=0x0
02-19 02:00:RESULT   :    msec_fw=0x0
02-19 02:00:RESULT   :    msec_hw=0x2
02-19 02:00:RESULT   :    msec_uc=0x0
02-19 02:00:RESULT   :    mccod=0x402
02-19 02:00:RESULT   :  socket0.imh1.punit.ras.gpsb.mc_misc=0x3002010d8200
02-19 02:00:RESULT   :    model_specific_information=0x18010086c1
02-19 02:00:RESULT   :

### Comments (latest)
++++14615159903 spullell
<p>issued trage re-runs and sent axon logs to Hector</p><p><br /></p><p>Nothing else in MC shows up.&nbsp;<br /><br />It reproduced over triage re-runs.&nbsp;<br /><br /><img src="https://hsdes.intel.com/rest/binary/14027128252" style="width: 1783px;" tabindex="-1" /><br /></p>

++++14615159902 spullell
<p>Hector confirmed that the similar issue seen.&nbsp;<br /><br /><br />they have been applying the D2D L1 workaroun and not noticing after that.&nbsp;</p><p><br /></p><p><span style="font-size: inherit;"><strong>##### D2D L1 disable #####</strong></span></p><p><span style="font-size: inherit;">sv.socket0.cbbs.base.d2d_stacks.ulas.ula.ula_link_ctrl.l1_enable=0;</span></p><p><span data-teams="true"></span></p><p><span style="font-size: inherit;">sv.socket0.imhs.d2d_stack.d2d_stacks.uxis.ula_link_ctrl.l1_enable=0;</span></p><p><span style="font-size: inherit;"><br /></span></p><p><span style="font-size: inherit;"><br /></span></p>

++++14615159904 spullell
This workaround is already part of automation&nbsp;<br /><p style="color: rgba(0, 0, 0, 0.87); font-family: Roboto, &quot;Helvetica Neue&quot;, sans-serif; font-size: 12.18px; background-color: rgb(245, 246, 255);"><span style="font-size: inherit;"><strong>##### D2D L1 disable #####</strong></span></p><p style="color: rgba(0, 0, 0, 0.87); font-family: Roboto, &quot;Helvetica Neue&quot;, sans-serif; font-size: 12.18px; background-color: rgb(245, 246, 255);"><span style="font-size: inherit;">sv.socket0.cbbs.base.d2d_stacks.ulas.ula.ula_link_ctrl.l1_enable=0;</span></p><p style="color: rgba(0, 0, 0, 0.87); font-family: Roboto, &quot;Helvetica Neue&quot;, sans-serif; font-size: 12.18px; background-color: rgb(245, 246, 255);"><span data-teams="true"></span></p><p style="color: rgba(0, 0, 0, 0.87); font-family: Roboto, &quot;Helvetica Neue&quot;, sans-serif; font-size: 12.18px; background-color: rgb(245, 246, 255);"><span style="font-size: inherit;">sv.socket0.imhs.d2d_stack.d2d_stacks.uxis.ula_link_ctrl.l1_enable=0;<br /><br /><br />step is automation is:&nbsp;</span></p><p style="color: rgba(0, 0, 0, 0.87); font-family: Roboto, &quot;Helvetica Neue&quot;, sans-serif; font-size: 12.18px; background-color: rgb(245, 246, 255);"><span style="font-size: inherit;">PreTest:&nbsp; &nbsp;&nbsp;</span><span style="font-size: 12.18px;">&quot;PM_Core_C6_WA&quot;</span></p>

++++14615159905 ivangele
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: center;">
      <th></th>
      <th>Test line</th>
      <th>Goal name</th>
      <th>Failed Test Step</th>
      <th>Config</th>
      <th>DDR_Freq</th>
      <th>BIOS_Version</th>
      <th>SVOS_Version</th>
      <th>CustomBiosOverrides</th>
      <th>SUT</th>
      <th>Vendors</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>dmr-ap_vv_a0_x4_mem_fdu3a_0035_3</th>
      <td><a href="https://nga.laas.intel.com/#/dmr_fv/planning/testlines/6198afb9-d8b8-46f7-996e-37f00661ba91"> NGA Test Line </a></td>
      <td>MEM C

### Conclusion
no_root_cause.rejected

### Component
hw.memory

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
- **Sub-Feature**: C1
- **Component Path**: hw.memory

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbbs.base.d2d_stacks.ulas.ula.ula_link_ctrl.l1_enable`
- `sv.socket0.imhs.d2d_stack.d2d_stacks.uxis.ula_link_ctrl.l1_enable`

## Timeline

- **Submitted**: 2026-03-06 23:06:56
- **Closed**: 2026-03-17 05:26:10
- **Days Open**: 10

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
