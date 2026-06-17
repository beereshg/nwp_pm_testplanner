# HSD 16028690477: [DMR][X1 A0 PO] [RAPL] Platform RAPL Consumed Power reported Lower than Socket RAPL Consumed Power

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16028690477](https://hsdes.intel.com/appstore/article-one/#/16028690477) |
| **Status** | rejected.merged |
| **Priority** | 3-medium |
| **Owner** | kumara5 |
| **Component** | board.bmc |
| **Defect Die** | ioe |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Power/RAPL | 52% |
| **Sub-Feature** | Socket RAPL | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

﻿
IFWI - OKSDCRB1_86B_2025.38.2.03_2754.D06_60000967_0.606.0_1P0_NonIPClean_Trace_DebugSigned.bin

Socket vs plt power consumption:- Expectation is that socket power(
domain_power_0
) should be lesser then the platform power (
domain_power_1) 
which is not being followed in this case

#Idle 

In [283]: sv.socket0.imh0.pcudata.pwrBdgtMngr.
domain_power_0
.consumed_power,sv.socket0.imh0.pcudata.pwrBdgtMngr.
domain_power_1
.co

nsumed_power,sv.socket0.imh0.pcudata.pwrBdgtMngr.
domain_power_2
.consu

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww42.3]

Manojj will try the same VR release from

 

14025928757
, 
if the result works fine, 

we should merge them together.

[25ww41.1]

Manojj confirmed that platform power readings from registers matched telemetry, and indicated that further help from the platform VR team for the latest VR CFH programming. 

Shreyas will check if the primecode calculated power matches with the raw telemetry data that Manojj collected.

[25ww39.3]

Problem Statement: platform power is consistently measured lower than socket power across multiple platforms.

Harsh provided a previous sighting from GNR where sensor issues on the board caused similar discrepancies, and the team agreed to link the current and historical findings for reference.

Harsh was assigned as co-owner to further investigate and coordinate debug efforts

### Description
﻿
IFWI - OKSDCRB1_86B_2025.38.2.03_2754.D06_60000967_0.606.0_1P0_NonIPClean_Trace_DebugSigned.bin

Socket vs plt power consumption:- Expectation is that socket power(
domain_power_0
) should be lesser then the platform power (
domain_power_1) 
which is not being followed in this case

#Idle 

In [283]: sv.socket0.imh0.pcudata.pwrBdgtMngr.
domain_power_0
.consumed_power,sv.socket0.imh0.pcudata.pwrBdgtMngr.
domain_power_1
.co

nsumed_power,sv.socket0.imh0.pcudata.pwrBdgtMngr.
domain_power_2
.consumed_power,sv.socket0.imh0.pcudata.pkgRAPLDomain.
pkg_power_consumed

Out[283]: (0x42fc3c4b(

126.11776 W

), 0x42ae924a(

87.28572 W

)

, 0x40fafafb(

7.8431373 W

), 0x42fca048(

126.31305 W

))

#Core Stress

sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_0.consumed_power,sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_1.co

nsumed_power,sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_2.consumed_power,sv.socket0.imh0.pcudata.pkgRAPLDomain.pkg_power_consumed

Out[285]: (0x431fb44c(

159.70428 W

), 0x42bcbcbd(

94.36863 W

)

, 0x40fafafb(

7.8431373 W)

, 0x431e8b59(

158.54433 W)

)

#test

##Idle condition

In :  sv.socket0.cbb0.compute0.pmas.pmsb.io_core_operating_point.core_ratio_16p67

socket0.cbb0.compute0.pma0.pmsb.io_core_operating_point.core_ratio_16p67 - 0x00000000

socket0.cbb0.compute0.pma1.pmsb.io_core_operating_point.core_ratio_16p67 - 0x00000000

socket0.cbb0.compute0.pma2.pmsb.io_core_operating_point.core_ratio_16p67 - 0x00000000

socket0.cbb0.compute0.pma3.pmsb.io_core_operating_point.core_ratio_16p67 - 0x00000018

socket0.cbb0.compute0.pma4.pmsb.io_core_operating_point.core_ratio_16p67 - 0x00000000

socket0.cbb0.compute0.pma5.pmsb.io_core_operating_point.core_ratio_16p67 - 0x00000018

socket0.cbb0.compute0.pma6.pmsb.io_core_operating_point.core_ratio_16p67 - 0x00000000

socket0.cbb0.compute0.pma7.pmsb.io_core_operating_point.core_ratio_16p67 - 0x00000018

In :  sv.socket0.cbb0.compute0.pma3.pmsb.io_core_operating_point.core_ratio_16p67/6

4.0

pr.read

### Comments (latest)
++++1667008902 kumara5
<p>Not much difference observed in socket power as well when lowering the PL1 limit of socket RAPL while the core freq get throttled significantly.</p><p>Socket Power is also not showing the expected value.</p><p><span style="font-family: &quot;Courier New&quot;;">In [34]: sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_rapl_limit_cfg.pkg_pwr_lim_1=0</span></p><p><br /></p><p><span style="font-family: &quot;Courier New&quot;;">In [35]: sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_0.consumed_power,sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_p</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; &nbsp; &nbsp;⋮ ower_1.consumed_power,sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_2.consumed_power,sv.socket0.imh0.pcudat</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; &nbsp; &nbsp;⋮ a.pkgRAPLDomain.pkg_power_consumed</span></p><p><span style="font-family: &quot;Courier New&quot;;">Out[35]: (<b>0x42ef2546 (</b></span><font face="Courier New"><b>119.5728 W</b>)</font><span style="font-family: &quot;Courier New&quot;; font-size: 0.87em;">, 0x42bcbcbd (</span><font face="Courier New"><span style="font-size: 10.5966px;">94.36863 W)</span></font><span style="font-family: &quot;Courier New&quot;; font-size: 0.87em;">, 0x40fafafb (</span><font face="Courier New"><span style="font-size: 10.5966px;">7.8431373 W</span></font><span style="font-family: &quot;Courier New&quot;; font-size: 0.87em;">), 0x42f3895c (</span><font face="Courier New"><span style="font-size: 10.5966px;">121.76828 W)</span></font><span style="font-family: &quot;Courier New&quot;; font-size: 0.87em;">)</span></p><p><br /></p><p><span style="font-family: &quot;Courier New&quot;;">In [36]: sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_0.consumed_power,sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_p</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; &nbsp; &nbsp;⋮ ower_1.consumed_power,sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_2.consumed_power,sv.socket0.imh0.pcudat</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; &nbsp; &nbsp;⋮ a.pkgRAPLDomain.pkg_power_consumed</span></p><p><span style="font-family: &quot;Courier New&quot;;">Out[36]: (0x42eacdbb, 0x42bcbcbd, 0x40fafafb, 0x42e3ce84)</span></p><p><br /></p><p><span style="font-family: &quot;Courier New&quot;;">In [37]: sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_rapl_limit_cfg.pkg_pwr_lim_1=0xa28</span></p><p><br /></p><p><span style="font-family: &quot;Courier New&quot;;">In [38]: sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_0.consumed_power,sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_p</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; &nbsp; &nbsp;⋮ ower_1.consumed_power,sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_2.consumed_power,sv.socket0.imh0.pcudat</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; &nbsp; &nbsp;⋮ a.

### Tags
FV_PM_BDC,DMR_A0_PO,FW_Trend

### Conclusion
no_root_cause.rejected

### Component
board.bmc

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
- **Sub-Feature**: Socket RAPL
- **Component Path**: board.bmc

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.pcudata.pwrBdgtMngr`
- `sv.socket0.imh0.pcudata.pkgRAPLDomain`
- `sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_0.consumed_power`

## Timeline

- **Submitted**: 2025-09-24 11:04:41
- **Closed**: 2025-10-16 22:10:59
- **Days Open**: 22

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
