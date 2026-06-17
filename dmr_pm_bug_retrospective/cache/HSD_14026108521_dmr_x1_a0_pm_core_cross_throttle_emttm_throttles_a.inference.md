# HSD 14026108521: [DMR] [X1 A0] [PM]  core CROSS throttle EMTTM throttles at 109C rather then 104C due to pcode variable ref_temp

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026108521](https://hsdes.intel.com/appstore/article-one/#/14026108521) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | jamesrow |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | SoC Thermal | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

expectation:

core throttling occurs at t_throttle(100C) and core cross throttle occurs at t_throttle+4C.

observation:

core does throttle at t_throttle fuse, but core cross throttling occurs still at tj_max+4C(109C) not at ideally 104C. 

this is due to core cross throttling being governed by pcodes ref_temp/temperature_target, that is still at 105C(Highest tj max).

core cross throttle still occurs at 108C, expected would be tj+3C(103). should we open a separate hsd for this issue?

cross thr

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww47.3]

No representatives attended to updated on this sighting. Sysdebug to follow up offline.

[25ww46.4]

Yuval explained that cross-tile throttling is triggered only when the system fails to cool down after reaching a 'do not exceed' temperature threshold, which is typically higher than TJ Max, and is not directly related to TJ Max itself.

James and Yuval discussed the event flow, confirming that self-throttling occurs at TJ Max, but cross-throttling is only asserted after the system remains above the 'do not exceed' threshold for a set period, and is deasserted only after cooling below TJ Max plus an offset.

[25ww45.1]

Adi suspected a fix was delivered in release 22.8. James confirmed the fix for the base frequency throttling at 100&deg;C works as expected.

Remaining Issue: Cross-throttling still uses 105&deg;C instead of the corrected 100&deg;C control temperature.

This suggests the algorithm is referencing a different temperature variable (ref_temp) rather than the corrected EMTTM control temp.

PP level in use is PP0; TjMax fuses and SST-BF conditions may affect behavior.

Need to verify EMTTM transactions and pCode indications.

Next Steps:

James will collect detailed pTracker with proper triggers to capture POWER_CTL register readings.

James to coordinate with Igor (and possibly Tamir) offline to set up CBB trace triggers for accurate data collection.

[25ww44.3]

James explained the resolution of a previous issue where the core self-throttle mechanism was using the wrong temperature threshold, and highlighted a remaining issue where the cross-throttle mechanism still uses an outdated variable (ref_temp at 105 instead of 100), requiring further investigation and possible pCode updates.
AR: James will collect pTracker with the new pCode patch.

[25ww43.3]

Cross-throttling is managed by pCode (using ref_temp), while self-throttling is managed by aCode. Previous from the self throttle sighting that fixes the aCode EMTTM issue, now we may need the 

### Description
expectation:

core throttling occurs at t_throttle(100C) and core cross throttle occurs at t_throttle+4C.

observation:

core does throttle at t_throttle fuse, but core cross throttling occurs still at tj_max+4C(109C) not at ideally 104C. 

this is due to core cross throttling being governed by pcodes ref_temp/temperature_target, that is still at 105C(Highest tj max).

core cross throttle still occurs at 108C, expected would be tj+3C(103). should we open a separate hsd for this issue?

cross throttle is govered by temp_target(ref temp) so likly a different issue, why is ref_temp 0x69? 

cross throttle occurs at temp_target+3: 
https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html#cross-throttle
 

ref temp should be 0x64: sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.temperature_target.ref_temp =
 

0x69

t_throttle is 0x64: sv.socket0.cbb0.base.fuses.punit_fuses.fw_fuses_sst_pp_0_t_throttle =
 

0x64

might be the fan_temp_offset, not sure where this value is used, not in ref_temp/temp_target/eff_tj_max: sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.temperature_target.fan_temp_target_ofst =
 

0x8

nothing else in eff_tj_calc would cause ref_temp to hit worst case tj:
 

https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html#temperature-target-handling

### Comments (latest)
++++14614732689 jamesrow
<p>next step:</p><p>reproduce on another system and log pcode collats and bios and steps followed</p>

++++14614732690 jamesrow
<p>I see during reset, set to highest tj(105) but don't see &quot;ref_temp&quot; referenced anywhere else in cbb pcode:</p><p><a href="https://github.com/intel-restricted/firmware.power.soc.pcode-cbb-a0/blob/534aa1814691b45bb8e62763b36e0a227ab15eb0/source/pcode/reset/reset.cpp#L1422" target="_blank">https://github.com/intel-restricted/firmware.power.soc.pcode-cbb-a0/blob/534aa1814691b45bb8e62763b36e0a227ab15eb0/source/pcode/reset/reset.cpp#L1422</a>&nbsp;</p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/22021690555" style="width: 629px;" /><br /></p>

++++14614732691 jamesrow
<p>reproduced on&nbsp;JF53NOR09BN0304</p><p>bios: OKSDCRB1.86B.2817.D06.2510082049</p><p>pcode collats:</p><p><img src="https://hsdes.intel.com/rest/binary/22021690612" style="width: 25%;" data-processed="true" /></p><p><br /></p><p>summary of steps followed in log:&nbsp;<a href="https://hsdes.intel.com/resource/22021690608" target="_blank">emttm_crosss_Core_throttle_at_105</a></p><ul><li>ref temp at 0x69, even though tcc_offset, cie_disable equal zero and t_throttle is 0x64</li><li>injected 106 and observed self throttling</li><li>injected 109C and oberved cross throtlting</li></ul>
++++22611535816 jamesrow
reproduced on VIS-1 parts, system Sc00901159h0006: bios:  OKSDCRB1.E9I.2798.D02.2509291324 pcode collats:  summary of steps followed in log: log ref temp at 0x69, even though tcc_offset, cie_disable equal zero and t_throttle is 0x64 injected 106 and observed self throttling injected 109C and observed cross throttling including core_cross_throttle set for core under test and freq clipping  related sighting: https://hsdes.intel.com/appstore/article-one/#/22021600619, core_per_thermal bit in plr fine grained only set when core cross throttling
++++1363446616 ayonish
Hi, This seems to be related to a different bug:  https://hsdes.intel.com/appstore/article-one/#/14026030624  https://hsdes.intel.com/appstore/article-one/#/article/14025976766 The cross throttle flow is: 1. Pcode updates CCPs with eff tj max in PMA_CR_EMTTM_ALGO_MISC[CONTROL_TEMP]( this is where the prev bug is) 2. CCPs run their PID. CCP gets heated over the tj limit provided by pcode. 3. CCP sends cross throttle request to pcode. 4. pcode activates cross throttle. since there was a bug in step 1 where pcode reported the wrong limit to CCPs the cross throttle request was sent at a wrong limit. To validate please check this with the version containing the fix of the bug

++++1363446816 aodler
 @Rowe, James  the PCode version you are using 0x7862e2a09f09ba92 is 22.1.22.6, it doesn't yet contain the fix for https://hsdes.intel.com/appstore/article-one/#/14026030624 You need to take PCode 22.1.22.8, UP 60000978
++++22611556723 jamesrow
reproduced and ran pcode tracker in //. log: emttm cross throt ptracker original comment noticing cross throttle s

### Tags
FV_PM

### Conclusion
not_a_bug

### Component
fw.pcode

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

- **Primary Feature**: SoC Thermal
- **Sub-Feature**: general
- **Component Path**: fw.pcode

## Firmware Touchpoints

### PCODE
- `pCode update`
- `pCode patch`

## Key Registers

- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.temperature_target.ref_temp`
- `sv.socket0.cbb0.base.fuses.punit_fuses.fw_fuses_sst_pp_0_t_throttle`
- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.temperature_target.fan_temp_target_ofst`
- `sv.socket0.cbb0.compute0.pma0.pmsb.dfvfcr_dts_fuse_0.cr_reg36_inst.digthermovrdval`
- `sv.socket0.cbb0.compute0.pma0.pmsb.dfvfcr_dts_fuse_0.cr_reg36_inst.digthermovrden`

## Timeline

- **Submitted**: 2025-10-22 01:52:04
- **Closed**: 2025-11-21 02:05:24
- **Days Open**: 30

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
