# HSD 16029184324: [RAPL][Reset] CBB PLR Die Level logging non-zero value post G3 power cycle

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029184324](https://hsdes.intel.com/appstore/article-one/#/16029184324) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | kumara5 |
| **Component** | val.env.test |
| **Defect Die** | compute |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Reset/Boot | 75% |
| **Sub-Feature** | Warm Reset | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Observed behavior

After G3(Power cycle), PLR die level logs unexpectedly showing the non-zero value; the observed die level status is 0xF/0xB post power cycle (G3)

Expected behavior

The plr die level bit should be 0 post G3. 

PLR 

bits are persistent across warm resets and firmware updates, but 

not

 across a full power cycle. [
DOC Referred - 
https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PLR.html#plr_die_level

]

Collateral/IFWI:

 
OKSDCRB1.86B.2817.D06.2510

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww12.4]
* Boot Ratio is greater than TRL Limit --> This is a no no (otherwise we clip to TRL).
* CBB team said this was fine, legal, not illegal or broken.
* FW Clipping is expected based on this fusing.
* This sighting is to be rejected.not_a_defect (expected behavior) as long as the boot_ratio and TRL fuses for this SKU are correct/expected and not a mistake.
    ==> SKU:  
'Q7YL'

* Steven adding Matthew and Vidar to a existing conversation with Dor to get confirmation here.
==> Need to change priority to MEDIUM - either not a defect or 'single sku defined wrong' or 'DQ rule fix for future silicon created'.

﻿[26ww12.3]

Jason reported that the PLR is being set due to the turbo ratio limit being lower than the boot ratio after reset, which is considered expected behavior based on the current fuse values, as confirmed by Orana.

Steven clarified that the issue is not with the TRL itself but with the boot ratio being set above a valid TRL for the SKU, and suggested checking the boot ratio fuses for both bootstrap and non-bootstrap cores.

Steven will forward relevant threads and fuse information to Jason, and recommended consulting with Dor, who has been involved in similar investigations, to further clarify the expected behavior.

NON_BSP_BOOT_RATIO, BSP_BOOT_RATIO

 

﻿[26ww11.3]

Jason explained that the observed performance limit is expected per specification because the TRL value is lower than 4.1, which sets frequency and ICCP0 limits. He noted that the perf limit value persists through BIOS states until CPL3, after which pCode reads and clears it.

Vidar and Jason discussed the possibility of a fuse being set incorrectly, specifically the TRL fuse being lower than the required value. Jason agreed to check the fuse values on the system and provide the necessary data for further investigation.

Vidar requested Jason to rewrite the system and add a command to capture the fuse value, so the information can be shared with the fuse team for further analysis and

### Description
Observed behavior

After G3(Power cycle), PLR die level logs unexpectedly showing the non-zero value; the observed die level status is 0xF/0xB post power cycle (G3)

Expected behavior

The plr die level bit should be 0 post G3. 

PLR 

bits are persistent across warm resets and firmware updates, but 

not

 across a full power cycle. [
DOC Referred - 
https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PLR.html#plr_die_level

]

Collateral/IFWI:

 
OKSDCRB1.86B.2817.D06.2510082049

Steps to Reproduce

Power cycle (G3) the platform and read the below value

In [59]: sv.socket0.cbb0.base.tpmi.plr_die_level

Out[59]: 

0xf

### Comments (latest)
++++1667119012 kumara5
<div>After the system is fresh booted, we can see the pkg per status counters</div><div><br /></div><div>In [333]: sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.showsearch(&quot;perf_status&quot;)</div><div>package_rapl_perf_status = 0x18174</div><div>dram_rapl_perf_status_cfg = 0x0</div><div>platform_rapl_perf_status = 0x0</div>

++++1667119008 kumara5
<div><span style="font-size: 14px;">System - SC00901159H0006</span></div><div><span style="font-size: 14px;">IFWI - OKSDCRB1_86B_2025.40.0.02_2798.D02</span></div><div><span style="font-size: 14px;"><br /></span></div><div><span style="font-size: 14px;">###Experiment to figure out at what stage the plr die level is getting set and perf status hitting</span></div><div><span style="font-size: 14px;">In [39]: while(1):</span></div><div><span style="font-size: 14px;">&nbsp; &nbsp; ...:&nbsp; &nbsp; &nbsp;if(sv.socket0.imh0.pcodeio_map.io_bios_reset_cpl.rst_cpl2==1):</span></div><div><span style="font-size: 14px;">&nbsp; &nbsp; ...:&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;itp.halt()</span></div><div><span style="font-size: 14px;">&nbsp; &nbsp; ...:&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;break</span></div><div><span style="font-size: 14px;">&nbsp; &nbsp; ...:</span></div><div><span style="font-size: 14px;"><br /></span></div><div><span style="font-size: 14px; background-color: rgb(255, 255, 0);">AT CPL2&nbsp;</span></div><div><span style="font-size: 14px;">In [40]:</span></div><div><span style="font-size: 14px;">&nbsp; &nbsp; [GPC core group] Halt on 6 devices -- 05:42:41.671771 2025-10-23</span></div><div><span style="font-size: 14px;">In [40]:</span></div><div><span style="font-size: 14px;"><br /></span></div><div><span style="font-size: 14px;">In [40]: sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.showsearch(&quot;perf_status&quot;)</span></div><div><span style="font-size: 14px; background-color: rgb(0, 255, 0);">package_rapl_perf_status = 0x0</span></div><div><span style="font-size: 14px;">dram_rapl_perf_status_cfg = 0x0</span></div><div><span style="font-size: 14px;">platform_rapl_perf_status = 0x0</span></div><div><span style="font-size: 14px;"><br /></span></div><div><span style="font-size: 14px;">In [41]: sv.socket0.cbb0.base.tpmi.plr_die_level</span></div><div><span style="font-size: 14px;">Out[41]: <span style="background-color: rgb(0, 255, 0);">0x0</span></span></div><div><br /></div><div><div><span style="font-size: 14px;">socket0.cbb0.compute1.pma8.pmsb.dfvfcr_dts_fuse_0.dfvfreg3_inst.fasttmode_dtstemperature_max - 0x000000be</span></div><div><span style="font-size: 14px;">socket0.cbb0.compute1.pma9.pmsb.dfvfcr_dts_fuse_0.dfvfreg3_inst.fasttmode_dtstemperature_max - 0x000000bf</span></div><div><span style="font-size: 14px;">socket0.cbb0.compute1.pma10.pmsb.dfvfcr_dts_fuse_0.dfvfreg3_inst.fasttmode_dtstemperature_max - 0x000000c8</span></div><div><span style="font-size: 14px;">socket0.cbb0.compute1.pma11.pmsb.dfvfcr_dts_fuse_0.dfvfreg3_inst.fasttmode_dtstemperature_max - 0x000000c2</sp

### Tags
presighting_bdc,FV_PM

### Conclusion
not_a_bug

### Component
val.env.test

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
- **Sub-Feature**: Warm Reset
- **Component Path**: val.env.test

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x199`
- `MSR 0x198`
- `TPMI register`
- `TPMI PLR_DIE_LEVEL`
- `TPMI SST`
- `sv.socket0.cbb0.base.tpmi.plr_die_level`
- `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.showsearch`
- `sv.socket0.imh0.pcodeio_map.io_bios_reset_cpl.rst_cpl2`

## Timeline

- **Submitted**: 2025-11-17 20:17:39
- **Closed**: 2026-03-25 19:08:07
- **Days Open**: 127

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
