# HSD 14027742612: [DMR][A0][2S] PkgC6 Residency is extremely low at 33% on a 2S system with D2D L1 disabled

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027742612](https://hsdes.intel.com/appstore/article-one/#/14027742612) |
| **Status** | open.clone |
| **Priority** | 3-medium |
| **Owner** | nyellise |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** |  |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Core C-States | 75% |
| **Sub-Feature** | C6 | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

With D2D L1 disabled, 2S Residency on 224 Core systems is extremely Low at 33%. System is spending a lot of time in PC2 Coordination Phase ~25% of time.

D2D L1 was disabled in both IMH RTL through PythonSV injections and through Pcode WA variable m_skip_d2d_l1_entry_hsd_14026480202

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
data collection is ongoing
﻿[26ww21.1]

Nagamani is collecting more data and work with Jai.

﻿[26ww20.1]

Nagamani will update more data to provide updated data for Primecode, Alex confirming Nagamani's ongoing triage.

﻿[26ww18.3]

Primecode team needs more dump and log to debug. Nagamani will sync with them.

﻿[26ww18.1]

Nagamani will collect PC data to help understand why the system is spending excessive time in PC2 coordination, with no immediate changes planned until more data is available.

### Description
With D2D L1 disabled, 2S Residency on 224 Core systems is extremely Low at 33%. System is spending a lot of time in PC2 Coordination Phase ~25% of time.

D2D L1 was disabled in both IMH RTL through PythonSV injections and through Pcode WA variable m_skip_d2d_l1_entry_hsd_14026480202

### Comments (latest)
++++14615372838 vwang
Modified title and description to add<span data-teams="true">&nbsp;&quot;with D2D L1 disabled&quot;</span>

++++14615372840 vwang
[CloneScript] PreSighting 14027742005 cloned to Sighting 14027742612
++++22611865258 mbfausto
If there isn't pcudata and hysteresis data for debug by EOD, please REJECT this back to pre-sighting.  This should not have been promoted without any triage information or debug data.
++++14615383502 jsbrooks
pcudata is insufficient.  We need pm_imh status_scope and/or RC residency readouts from 2+ systems.   And as a reminder to those reading this sighting, 2S PkgC on AP1 A0 is running in a non-POR mode due to no support for UXI L1.  Although we are bypassing that for validation purposes.

++++14615383540 vwang
There are offline discussions with few Arch folks for few months. More triage and data will be added soon.   @Yellisetty, Nagamani 
++++22611865329 mbfausto
Can we confirm HOW we are disabling D2D L1?  BIOS Knob?  We have a HW_WA which alters some of the configuration for D2D L1 and I thought a request for  the IMH1-B0 pCode bypass back-porting into IMH1-A0 to be controlled by a variable ... What do the PKGC Exit/Abort statistics indicate in pCode and/or Primecode?  This sighting has 0 data and as you can see no one is able to do anything in the last 4 days since filing ...
++++14615383907 nyellise
D2D L1 was disabled in both IMH RTL through PythonSV injections and through Pcode WA variable m_skip_d2d_l1_entry_hsd_14026480202 Will add RC Residency data and status scope data soon. Snippet showing Zero D2D L1 residency (Its 0 for all CBB dies, showing only CBB0 here): ---------------------------------------------------------------------------------------------------       cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_io_regs.wp_rv_d2d_p_ch.pstate_dist_stack1 (5:3) ---------------------------------------------------------------------------------------------------                                    Bin |          Dec |        Hex |   socket0  |  socket1  | ---------------------------------------------------------------------------------------------------                                    0b0 |            0 |        0x0 |   100.0%   |  100.0%   | ---------------------------------------------------------------------------------------------------       cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_io_regs.wp_rv_d2d_p_ch.pstate_dist_stack0 (2:0) ---------------------------------------------------------------------------------------------------                                    Bin |          Dec |        Hex |   socket0  |  socket1  | ---------------------------------------------------------------------------------------------------                                    0b0 |            0 |        0x0 |   100.0%   |  100.0%   | ---------------------------------------------------------------------------------------------------

++++14615384504 vwang 
The latest IFWI has integrated pCode changes of Pcode WA vari

### Tags
PTP_SoC

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

- **Primary Feature**: Core C-States
- **Sub-Feature**: C6
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.pcodeio_map.io_c2c3tt_cfg`
- `sv.socket0.imh1.pcodeio_map.io_c2c3tt_cfg`
- `sv.socket1.imh0.pcodeio_map.io_c2c3tt_cfg`
- `sv.socket1.imh1.pcodeio_map.io_c2c3tt_cfg`
- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pm_last_wake_unfiltered`

## Timeline

- **Submitted**: 2026-04-24 22:15:45
- **Days Open**: 27

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
