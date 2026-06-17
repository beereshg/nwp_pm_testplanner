# HSD 14026063964: [DMR][X1 A0 PO] Turbo Ratio Limit (TRL) Frequencies not followed when different license level workloads are run

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026063964](https://hsdes.intel.com/appstore/article-one/#/14026063964) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | srotich |
| **Component** | fw.acode |
| **Defect Die** | compute |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 80% |
| **Sub-Feature** | AVX | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

This is verified on 3 different platforms (32 core and 6 core)

Steps to reproduce
:

Enable Turbo  in BIOS menu or clear bit38 of msr 0x1a0

Run different license workloads like:

	
XZ-license1(SSE); povray -license 2(AVX2); BGEMM license 3 (AVX512)

sv.socket0.cbb0.compute0.mcast_core.core_pmsb_top.core_pma_pmsb.pma_debug.iccp_granted 

Track granted license and corresponding all core Turbo frequencies

Fused TRL values shows all core turbo frequency limits (P0n) as SSE=2.2GHZ;  AVX2=2.0GHZ; A

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww43.3]

The pvp values need be tuned before PVC can separate workloads according to their cdyn levels. tunning is underway. it first we see that the request for pvc to work on day 1

[25ww43.1]

Issue: the frequencies remain at SSE levels while SSE, AVX2, and AVX512 counters increment correctly
Vidar will pull in CBB core/pcode team into the loop.

[25ww42.3]

Issue: turbo ratio limits are not scaling down as expected when running higher license level workloads, remaining stuck at the SSE frequency even when the license granted increases.

Ido and Steven Y asked which registers are programmed to indicate license level changes and suggested collecting Pmon data for different workloads to determine if the system recognizes and enforces license changes.

Next Steps: Simeon will collect additional Pmon data for BGM workloads, and may nee the core validation team to assist with further debugging.

### Description
This is verified on 3 different platforms (32 core and 6 core)

Steps to reproduce
:

Enable Turbo  in BIOS menu or clear bit38 of msr 0x1a0

Run different license workloads like:

	
XZ-license1(SSE); povray -license 2(AVX2); BGEMM license 3 (AVX512)

sv.socket0.cbb0.compute0.mcast_core.core_pmsb_top.core_pma_pmsb.pma_debug.iccp_granted 

Track granted license and corresponding all core Turbo frequencies

Fused TRL values shows all core turbo frequency limits (P0n) as SSE=2.2GHZ;  AVX2=2.0GHZ; AVX512=1.6GHZ

However, we see frequencies at 2.2GHZ for all license levels.

Config

Platform- AN004011BMH1502.amr.corp.intel.com (PO Platform (32 core Fused))

IFWI -  

OKSDCRB1.86B.2798.D03.2509300401

TRL frequencies table :

In [413]: sv.socket0.cbb0.base.tpmi.sst_pp_info_4.show()

0x000000

16

 : ratio_7 (63:56) (ro/v) -- Turbo ratio limit value for bucket 7 of the specific cdyn level.<<<<<<SSE all core Turbo=2.2GHZ

0x00000016 : ratio_6 (55:48) (ro/v) -- Turbo ratio limit value for bucket 6 of the specific cdyn level.

0x00000017 : ratio_5 (47:40) (ro/v) -- Turbo ratio limit value for bucket 5 of the specific cdyn level.

0x00000017 : ratio_4 (39:32) (ro/v) -- Turbo ratio limit value for bucket 4 of the specific cdyn level.

0x0000001a : ratio_3 (31:24) (ro/v) -- Turbo ratio limit value for bucket 3 of the specific cdyn level.

0x0000001b : ratio_2 (23:16) (ro/v) -- Turbo ratio limit value for bucket 2 of the specific cdyn level.

0x0000001c : ratio_1 (15:08) (ro/v) -- Turbo ratio limit value for bucket 1 of the specific cdyn level.

0x000000

1f

 : ratio_0 (07:00) (ro/v) -- Turbo ratio limit value for bucket 0 of the specific cdyn level. (Note: Ratio of 0x0 in the TRL registers implies that particular turbo limit level is not supported.)

In [414]: sv.socket0.cbb0.base.tpmi.sst_pp_info_5.show()

0x000000

14

 : ratio_7 (63:56) (ro/v) -- Turbo ratio limit value for bucket 7 of the specific cdyn level.<<<< all core turbo for AVX2=2.0GHZ

0x00000014 : ratio_6 (55:48) 

### Comments (latest)
++++14614710881 dlwu
<p>While active workload is running, we can readback the active TRL # core and TRL frequency ratio table that is being observed via:</p><p><!--StartFragment-->sv.socket0.cbb0.base.tpmi.odc_trl_numcores.show<!--EndFragment--></p><p>sv.socket0.cbb0.base.tpmi.odc_trl_ratios.show</p><p><span style="background-image: initial; background-position: initial; background-size: initial; background-repeat: initial; background-attachment: initial; background-origin: initial; background-clip: initial;">sv.socket0.cbb0.compute0.mcast_core.core_pmsb_top.core_pma_pmsb.pma_debug.iccp_granted</span></p><p><span style="background-image: initial; background-position: initial; background-size: initial; background-repeat: initial; background-attachment: initial; background-origin: initial; background-clip: initial;"><br /></span></p><p><span style="background-image: initial; background-position: initial; background-size: initial; background-repeat: initial; background-attachment: initial; background-origin: initial; background-clip: initial;">We ran BGEMM on all 6 cores:</span></p><p><img src="https://hsdes.intel.com/rest/binary/14026052150" style="width: 689px;" /><span style="background-image: initial; background-position: initial; background-size: initial; background-repeat: initial; background-attachment: initial; background-origin: initial; background-clip: initial;"><br /></span></p><p><span style="background-image: initial; background-position: initial; background-size: initial; background-repeat: initial; background-attachment: initial; background-origin: initial; background-clip: initial;"><br /></span></p><p><span style="background-image: initial; background-position: initial; background-size: initial; background-repeat: initial; background-attachment: initial; background-origin: initial; background-clip: initial;">You can see BGEMM is actually license level 3.The table that should be copied over to trl_ratios, which is the active table, should be the one corresponding to license level 3 (info_7 or info_8) but it is copying that for license level 0 (info_4).</span></p><p><img src="https://hsdes.intel.com/rest/binary/14026052151" style="width: 1452px;" /><span style="background-image: initial; background-position: initial; background-size: initial; background-repeat: initial; background-attachment: initial; background-origin: initial; background-clip: initial;"><br /></span></p><p><span style="background-image: initial; background-position: initial; background-size: initial; background-repeat: initial; background-attachment: initial; background-origin: initial; background-clip: initial;"><br /></span></p><p><img src="https://hsdes.intel.com/rest/binary/14026052152" style="width: 1489px;" /><span style="background-image: initial; background-position: initial; background-size: initial; background-repeat: initial; background-attachment: initial; background-origin: initial; background-clip: initial;"><br /></span></p><p><br /></p><p><br /></p>

### Tags
core.pnp,PM,acp,PTP_SoC

### Conclusion
not_a_bug

### Component
fw.acode

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
- **Sub-Feature**: AVX
- **Component Path**: fw.acode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbb0.compute0.mcast_core.core_pmsb_top.core_pma_pmsb.pma_debug.iccp_granted`
- `sv.socket0.cbb0.base.tpmi.sst_pp_info_4.show`
- `sv.socket0.cbb0.base.tpmi.sst_pp_info_5.show`
- `sv.socket0.cbb0.base.tpmi.sst_pp_info_10.show`
- `sv.socket0.cbb0.base.tpmi.odc_trl_numcores.show`

## Timeline

- **Submitted**: 2025-10-15 06:24:59
- **Closed**: 2025-10-30 22:55:53
- **Days Open**: 15

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
