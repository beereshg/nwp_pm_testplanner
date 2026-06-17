# HSD 16029272544: [DMR_PMSS][Pre-VV][X1][RAPL_PMAX]: MT0 threshold read via CR register is not set to 63

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029272544](https://hsdes.intel.com/appstore/article-one/#/16029272544) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | mps |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Power/RAPL | 75% |
| **Sub-Feature** | PMAX | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

Expected Behavior:

MT0 threshold read via CR register should set to 63

Actual Behavior:

MT0 threshold read via CR register is not set to 63

logs:

https://axonsv.app.intel.com/apps/record-viewer?id=86ee9308-f67e-44af-8ee0-0f78b48997cd

 

 

  
\\amr.corp.intel.com\ec\proj\peg\daiv\diamondrapids\ExecutionLogs\dmr_pv\Oak_Stream81c278f0\jf53nor09bn0401\1602880432c811c5bc_1

 

[INFO]

 2025-10-22 10:17:51,019 

[kayak.domains.pmss.internals.dmr: display_pysv_values: 283]

: +------------------

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww02.3]

Suchi will follow up with Manojj for latest findings.

[26ww02.1]

Alex reported that the current fuse values on available parts do not allow prime code to reach the expected MT0 threshold value of 63, as specified in the HAS, prompting a review of the logic and expectations.

Nilanjan and Suchismita acknowledged the need to consult with Nazar's team to confirm if the correct fusing and tuning have been performed for the MP Max circuit, as neither had immediate answers.

Timothy clarified that the trip point value is a tunable constant determined by fusing, not strictly specified in the HAS, and suggested that any discrepancy is likely a fusing issue rather than an architectural problem.

AR: Suchismita agreed to follow up with Nazar's team, and lead the discussion with the relevant group to resolve the issue.

[25ww51.3]

Meghana debugging why the primecode issue has problems, a fuse dump was required, Meghana will check the fuses to see if there is something wrong in the code related to such fuses. 

[25ww51.1]

Manojj collecting and posting data for Meghana to analyze calculation discrepancies.

[25ww50.4]

Meghana is looking into pre-si regressions and value is correct to be 63 but post-si is showing 62, Meghana will follow up on debugging. Getting primecode trace is the next step

[25ww49.1]

Manojj reported that after enabling the RAPL PL4 control DPM register and setting the PL to zero, the threshold should cap at 63 but is observed as 62, similar to a previous issue in GNR, and questioned whether this is a primeCode or HAS update issue.

Shreyas and Meghana confirmed that the issue was already addressed in GNR and the same logic applies to DMR, with the Jira ticket closed as a duplicate since the calculations are consistent and only the fuse name changed.

Shreyas and Alex will double-check the changes and confirm if any further action is needed, agreeing to keep the issue open for a few days for additional review before closing.

### Description
Expected Behavior:

MT0 threshold read via CR register should set to 63

Actual Behavior:

MT0 threshold read via CR register is not set to 63

logs:

https://axonsv.app.intel.com/apps/record-viewer?id=86ee9308-f67e-44af-8ee0-0f78b48997cd

 

 

  
\\amr.corp.intel.com\ec\proj\peg\daiv\diamondrapids\ExecutionLogs\dmr_pv\Oak_Stream81c278f0\jf53nor09bn0401\1602880432c811c5bc_1

 

[INFO]

 2025-10-22 10:17:51,019 

[kayak.domains.pmss.internals.dmr: display_pysv_values: 283]

: +-----------------------------------------------------+-------------+

[INFO]

 2025-10-22 10:17:51,019 

[kayak.domains.pmss.internals.dmr: display_pysv_values: 284]

: | Pysv Register                                       | Value       |

[INFO]

 2025-10-22 10:17:51,019 

[kayak.domains.pmss.internals.dmr: display_pysv_values: 285]

: +-----------------------------------------------------+-------------+

[INFO]

 2025-10-22 10:17:51,019 

[kayak.domains.pmss.internals.dmr: display_pysv_values: 289]

: | sv.socket0.imh0.pmax.pmax0.pmax_config1.mt0_offset  |  0x0000003b |

[INFO]

 2025-10-22 10:17:51,019 

[kayak.domains.pmss.internals.dmr: display_pysv_values: 289]

: | sv.socket0.imh1.pmax.pmax0.pmax_config1.mt0_offset  |  0x0000003b |

[INFO]

 2025-10-22 10:17:51,019 

[kayak.domains.pmss.internals.dmr: display_pysv_values: 291]

: +-----------------------------------------------------+-------------+

[INFO]

 2025-10-22 10:17:51,019 

[tests.contents.powermanagement.rapl.icc_max_harasser_test: validate_via_pysv: 165]

: pre mt0_offset: 

[' 0x0000003b', ' 0x0000003b']

[ERROR]

 2025-10-22 10:17:51,019 

[tests.contents.powermanagement.rapl.icc_max_harasser_test: validate_via_pysv: 171]

: MT0 threshold read via CR register is not set to 63

test:

Name| POWER_ICC_MAX_HARASSER

### Comments (latest)
++++1667137126 hkharya
<p>As per HAS, Primecode to clip the threshould to max <u>0x3F{63}</u>.</p><p><a href="https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PMax.html#pmax-register" target="_blank">https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PMax.html#pmax-register</a>&nbsp;</p><p><img src="https://hsdes.intel.com/rest/binary/16029009452" style="width: 784.986px;" /></p><p><br /></p><p><u>NextStep</u> - Try reproducing this issue manually. Try putting high PL4 Lim &amp; check if MT0_Offset is clipped to 0x3f or not</p>

++++1667137127 mps
******************************* After booting to OS ***************************************************************<br /><br /><div><div><span style="font-size: 14px;">In [127]: sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control.show()</span></div><div><span style="font-size: 14px;">0x00000000000 : lock (63:63) (rw/l) -- When set, all settings in this register are locked and are treated as Read Only until next reset.</span></div><div><span style="font-size: 14px;">0x00000000000 : pwr_lim_en (62:62) (rw/l) -- Enable(1) or Disable(0)</span></div><div><span style="font-size: 14px;">0x00000000000 : rsvd (61:18) (rw/l) -- Reserved</span></div><div><span style="font-size: 14px;">0x000000021e8 : pwr_lim (17:00) (rw/l) -- This field indicates the PL4 power limitation. The unit of measurement is defined in POWER_UNIT[PWR_UNIT].</span></div><div><span style="font-size: 14px;"><br /></span></div><div><span style="font-size: 14px;">0x00000000000 : lock (63:63) (rw/l) -- When set, all settings in this register are locked and are treated as Read Only until next reset.</span></div><div><span style="font-size: 14px;">0x00000000000 : pwr_lim_en (62:62) (rw/l) -- Enable(1) or Disable(0)</span></div><div><span style="font-size: 14px;">0x00000000000 : rsvd (61:18) (rw/l) -- Reserved</span></div><div><span style="font-size: 14px;">0x00000000000 : pwr_lim (17:00) (rw/l) -- This field indicates the PL4 power limitation. The unit of measurement is defined in POWER_UNIT[PWR_UNIT].</span></div></div><div><br /></div><div><br /></div><div>In [109]: sv.sockets.imhs.pmax.pmax0.pmax_config1.mt0_offset</div><div>Out[109]:</div><div>socket0.imh0.pmax.pmax0.pmax_config1.mt0_offset - 0x00000000</div><div>socket0.imh1.pmax.pmax0.pmax_config1.mt0_offset - 0x0000001d</div><br /><!--StartFragment-->*******************************&nbsp;

<!--StartFragment-->pwr_lim_en&nbsp;<!--EndFragment-->&nbsp;= 0x1 and&nbsp;

<!--StartFragment-->pwr_lim&nbsp;<!--EndFragment-->&nbsp; = 0x0&nbsp; (for 2 imh)&nbsp; ***************************************************************<br /><br /><!--EndFragment--><span style="font-size: 14px;">sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control.pwr_lim_en = 0x1<br />sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control.pwr_lim = 0x0<br /></span><br /><div><div><span style="font-size: 14px;">In [115]: sv.socket0.imhs.punit.ptpcfsms.ptp

### Conclusion
not_a_bug

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

- **Primary Feature**: Power/RAPL
- **Sub-Feature**: PMAX
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI PMAX`
- `TPMI  https`
- `TPMI is`
- `sv.socket0.imh0.pmax.pmax0.pmax_config1.mt0_offset`
- `sv.socket0.imh1.pmax.pmax0.pmax_config1.mt0_offset`
- `sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control.show`
- `sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control.pwr_lim_en`
- `sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control.pwr_lim`

## Timeline

- **Submitted**: 2025-11-25 16:15:46
- **Closed**: 2026-01-14 00:34:17
- **Days Open**: 49

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
