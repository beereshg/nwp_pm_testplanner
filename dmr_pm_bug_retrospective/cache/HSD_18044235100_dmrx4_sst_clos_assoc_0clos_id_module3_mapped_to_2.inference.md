# HSD 18044235100: [DMR][X4] SST_CLOS_ASSOC_0.CLOS_ID_MODULE3 mapped to 2 modules

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [18044235100](https://hsdes.intel.com/appstore/article-one/#/18044235100) |
| **Status** | root_caused.awaiting_fix |
| **Priority** | 2-high |
| **Owner** | lmalagon |
| **Component** | hw.big_core |
| **Defect Die** | compute |
| **Conclusion** | hw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 85% |
| **Feature** | PState Stack | 45% |
| **Sub-Feature** | general | — |

**Reasoning**: conclusion='hw.bug' → HW

## Root Cause Summary

When SST TF is enabled, assigning SST_CLOS_ASSOC_0.CLOS_ID_MODULE3 to CLOS ID 3 we realized that it is mapped to 2 modules

Assigned to CLOS ID 3 resolving respective ratios.

Assigning only sst_clos_assoc_0.clos_id_module3 to HP (0) modules

Assigned to CLOS ID 0 is module 11 mapped to sst_clos_assoc_0.clos_id_module3 is resolving correctly the ratios but also 
module 27 is affected even when it is subscribed to CLOS ID 3
:

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww15.4]

Ido, 

Anatoli

 and Sagar discussed that there are multiple sightings(18044235100/22022111812) , possibly related to the same root cause, and emphasized the need to track each separately while sharing relevant information and patches.

Next: Ido will review the latest updates from Carlos and coordinate with Anatoli to determine if the issues are related and what further steps are needed. Vidar will provide links and facilitate communication among the teams.

[26ww10.3]

Jason will send out the debug data required on aCode for the CCP_WP4

﻿[26ww10.1]

CCP Allocation Anomaly: Orna described a scenario where CCP3 is correctly allocated to the high-priority mask, but CCP19, despite being allocated to the low-priority mask, receives high-priority ratio values. This behavior appears when only CCP3's allocation is changed, suggesting a logical ID interpretation issue in the aCode.

Orna and Leonardo observed that the allocation issue consistently occurs when there is a logical ID difference of 16 between CCPs, indicating a possible glitch in how the aCode interprets logical IDs, with similar patterns found in other HSDs.

Vidar confirmed that Jason is assigned to investigate the issue, with Jason acknowledging the need to review the HSD data and debug further. The team agreed to reference the PMCS debug channel for updated lists and assignments.

﻿[26ww09.3]

Orna is working on this

﻿[26ww09.1]

Leonardo described that module 27 is being mapped to both high and low priority CLOS IDs, resulting in unexpected ratio assignments, which is not aligned with the intended configuration.

The team noted the absence of a clear programming guide for CBB, with Sagar and Carlos confirming that only HAS and HSDS documents are available, making it challenging to verify correct mapping procedures.

We may need to ask arch and pCode teams to define and correct the programming guide, ensuring that future mappings adhere to architectural requirements.

### Description
When SST TF is enabled, assigning SST_CLOS_ASSOC_0.CLOS_ID_MODULE3 to CLOS ID 3 we realized that it is mapped to 2 modules

Assigned to CLOS ID 3 resolving respective ratios.

Assigning only sst_clos_assoc_0.clos_id_module3 to HP (0) modules

Assigned to CLOS ID 0 is module 11 mapped to sst_clos_assoc_0.clos_id_module3 is resolving correctly the ratios but also 
module 27 is affected even when it is subscribed to CLOS ID 3
:

### Comments (latest)
++++1862546812 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14027115992.
++++14615106856 lmalagon
Attached pcode dumps before and after changing CLOS ID for module.
++++1363590973 osumszyk
Hi, From the logs, I can see that the current PP level is 0, and the enabled CCP mask at this PP level is 0x88f7fe. That is, CCPs 11 and 27 are not enabled. This is due to fuse SST_PP_0_MODULE_DISABLE_MASK. See in logs: sstmanager.sst_pp_level=0x0  ccp_cfg.pp_info2.at0 = 0x88f7fe
++++14615118671 lmalagon
@Sumszyk, Orna  PythonSV uses the physical enumeration and physically that modules are enabled in the corresponding pp level (0) the fuse that you mention is the correct one and decoded to binary it shows that both modules are enabled. Note: Module column is reflecting the path in pythonSV pp_info_2.resolved_module_mask contains the logical. As compute0 die (cbb top die) does not have any module active the logical shift right the complete byte corresponding to that compute die. As shown in the image in the description there is a column to map which instance from pcode resolved module mask is used for each physical module. For these particular 2 modules physical module 11 correspond to the 3rd resolved module (pCode) and physical module 27 correspond to 19th resolved module (pCode). According to the value that pp_info2 contains both are enabled in the respective pp level
++++1363593584 osumszyk
Hi, Thanks Leonardo. Indeed, now I see in the logs that CCP physical ID 11 is mapped to logical ID 3 CCP physical ID 27 is mapped to logical ID 19 And they are both enabled. From here I am writing with logical IDs. I can also see that CCP 3 is mapped to CLOS 0 (HP) and CCP 19 is mapped to CLOS 3 (LP). All CCPs have the same set of limits in WP4: Limits for HP CCPs:  workpoint_calc.soc_workpoints_final.ia.ring_pd.trls.hp_cdyn_trls_resolved.data.at0.value_=0x1d workpoint_calc.soc_workpoints_final.ia.ring_pd.trls.hp_cdyn_trls_resolved.data.at1.value_=0x1d workpoint_calc.soc_workpoints_final.ia.ring_pd.trls.hp_cdyn_trls_resolved.data.at2.value_=0x1d workpoint_calc.soc_workpoints_final.ia.ring_pd.trls.hp_cdyn_trls_resolved.data.at3.value_=0x1d workpoint_calc.soc_workpoints_final.ia.ring_pd.trls.hp_cdyn_trls_resolved.data.at4.value_=0x1d workpoint_calc.soc_workpoints_final.ia.ring_pd.trls.hp_cdyn_trls_resolved.data.at5.value_=0x1d Limits for LP CCPs: workpoint_calc.soc_workpoints_final.ia.ring_pd.trls.lp_cdyn_trls_resolved.data.at0.value_=0xe workpoint_calc.soc_workpoints_final.ia.ring_pd.trls.lp_cdyn_trls_resolved.data.at1.value_=0xe workpoint_calc.soc_workpoints_final.ia.ring_pd.trls.lp_cdyn_trls_resolved.data.at2.value_=0x9 workpoint_calc.soc_workpoints_final.ia.ring_pd.trls.lp_cdyn_trls_resolved.data.at3.value_=0x6 workpoint_calc.soc_workpoints_final.ia.ring_pd.trls.lp_cdyn_trls_resolved.data.at4.value_=0xf workpoint_calc.soc_workpoints_final.ia.ring_pd.trls.lp_cdyn_trls_resolved.data.at5.value_=0x0 Li

### Tags
FV_PM,SysDebugCloned,SysDebugDccbDone

### Conclusion
hw.bug

### Component
hw.big_core

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
- **Sub-Feature**: general
- **Component Path**: hw.big_core

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x08B`
- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_io_regs.wp_cv_ia_ccp_wp4_0`
- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_io_regs.wp_cv_ia_ccp_wp4_1`
- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_io_regs.wp_cv_ia_ccp_wp4_mask_0.show`
- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_io_regs.wp_cv_ia_ccp_wp4_mask_1.show`
- `sv.socket0.cbb0.compute1.pma11.showsearch`

## Timeline

- **Submitted**: 2026-02-20 07:57:28
- **Root Caused**: 2026-03-13 04:50:49
- **Days Open**: 90

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
