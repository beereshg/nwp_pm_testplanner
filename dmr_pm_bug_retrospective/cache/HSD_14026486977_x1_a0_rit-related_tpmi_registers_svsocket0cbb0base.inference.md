# HSD 14026486977: [X1 A0] RIT-related TPMI registers sv.socket0.cbb0.base.tpmi.fit_config_0/1 cannot be set correctly.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026486977](https://hsdes.intel.com/appstore/article-one/#/14026486977) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | dlwu |
| **Component** | board.platform |
| **Defect Die** | base |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 80% |
| **Sub-Feature** | AVX | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

1) TRL license mapping min/max thresholds were set via the same method as Simeon detailed in a previous comment:

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.min_threshold_idx._0 = 0

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.min_threshold_idx._1 = 0 #SSE

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.min_threshold_idx._2 = 1 #AVX2

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.min_threshold_idx._3 = 2 #AVX512

sv.socket0.cpu.pmas.acode.vars.acode_ca

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww50.1]

This is a pythonsv issue that requires OSXML collateral update. AR sysdebug to escalate to pythonsv team to follow up on a method to update OSXML manually. Related pythonsv ticket 14026154100 as there is a new collateral released on Friday and it will continue to change throughout the program.

[25ww49.1]

AR sysdebug to follow up with pythonsv to find a way to update collaterals as Stan mentions it continues to change during the entire program

[25ww48.1]

David explained that using different OSXML versions (ww7 vs. 26 or 41) across components caused register offset mismatches, resulting in configuration issues.

Stanley and Anatoli clarified that versions 26 and 41 are compatible, but mixing with version 7 is not, and recommended aligning all components to the same version to resolve the issue.

### Description
1) TRL license mapping min/max thresholds were set via the same method as Simeon detailed in a previous comment:

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.min_threshold_idx._0 = 0

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.min_threshold_idx._1 = 0 #SSE

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.min_threshold_idx._2 = 1 #AVX2

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.min_threshold_idx._3 = 2 #AVX512

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.min_threshold_idx._4 = 3 #TMUL

 

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.max_threshold_idx._0 = 2

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.max_threshold_idx._1 = 2

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.max_threshold_idx._2 = 4

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.max_threshold_idx._3 = 4

sv.socket0.cpu.pmas.acode.vars.acode_cal_vars.g_pvc_cal.max_threshold_idx._4 = 4

2) PM recipe was applied.

3) Turbo mode was enabled via BIOS.

4) we checked the FVT value via register readback and find they are all reading 0x0.

In [74]: sv.socket0.cbb0.base.tpmi.fit_config_0.show()

0x00000000 : fit_module15 (63:60) (rw) -- Frequency Variability Tolerance for Module 15

0x00000000 : fit_module14 (59:56) (rw) -- Frequency Variability Tolerance for Module 14

0x00000000 : fit_module13 (55:52) (rw) -- Frequency Variability Tolerance for Module 13

0x00000000 : fit_module12 (51:48) (rw) -- Frequency Variability Tolerance for Module 12

0x00000000 : fit_module11 (47:44) (rw) -- Frequency Variability Tolerance for Module 11

0x00000000 : fit_module10 (43:40) (rw) -- Frequency Variability Tolerance for Module 10

0x00000000 : fit_module9 (39:36) (rw) -- Frequency Variability Tolerance for Module 9

0x00000000 : fit_module8 (35:32) (rw) -- Frequency Variability Tolerance for Module 8

0x00000000 : fit_module7 (31:28) (rw) -- Frequency Variability Tolerance for Module 7

0x00000000 : fit_module6 (27:24) (rw)

### Comments (latest)
++++14614840057 srotich
Issue see in in IFWI:  BIOS OKSDCRB1.E9I.2834.D10.2511131301 11/13/2025 and VIS IFWI:  BIOS OKSDCRB1.86B.0029.D50.2511162333 11/16/2025 

++++14614841584 daalonso
 @Dominguez, Caesar  Can you please chime in ? 

++++14614841878 cadoming 
Pleae verify your OXML version used.I see you are only using pythonsv access method to TPMI register. YOu cna use OOBMSM script. import diamondrapids.pm.OOBMSM.tpmi.tpmi_register as treg import diamondrapids.oobmsm_fv.peci_framework.peciObj as po dfx = po.peciObj(0) treg.access_tpmi_oob(dfx,'RIT', 'fit_config_0','cbb',0) Search for: Yellwo ones shoudl match the below ones INFO:  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^- READ OPERATION  -^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ INFO:  TPMI OSX RELEASE  -->  skt0.cbb0: TPMI_MAILBOX_OSXML_DMR_WW26_2025 INFO:  TPMI STRUCTURE FILES -->  TPMI_Data_Structures_rev2p5_DMR0.xlsx  |  TPMI_Data_Structures_rev2p5_DMR1.xlsx Also if those are not correct can you make an attmpe to updte your Pythonsv conifguration to use hte latest CBB ones, 25ww28b - for CBB one. if still failing have you attmepted to make MMIO(on DMR BIOS is most of the time doing an MMIO TPMI request) access of PECI access? and those are also having issue?


++++14614842266 cadoming
i could get access to FV PM Team (Carlos Ramires/ Emiliano GOmez)THey are using BKMS for TPMI Ensuring using THe correct OXML package i was able to write on them. n [64]: sv.socket0.cbb0.base.tpmi.fit_config_1 Out[64]: 0x0 In [65]: sv.socket0.cbb0.base.tpmi.fit_config_1 = 0xffffffffffffffff In [66]: sv.socket0.cbb0.base.tpmi.fit_config_1 Out[66]: 0xffffffffffffffff In [67]:

++++14614844205 dlwu
Dominguez, Caesar, could you please state what version of the IFWI you performed your test on, and how that version compares to the ones we stated in the comments before, i.e. newer/older. Thank you.

++++14614844231 dlwu 
Ran script on 1502: import diamondrapids.pm.OOBMSM.tpmi.tpmi_register as treg import diamondrapids.oobmsm_fv.peci_framework.peciObj as po dfx = po.peciObj(0) treg.access_tpmi_oob(dfx,'RIT', 'fit_config_0','cbb',0) INFO:  ARGS ENTERED: 5 INFO:  OOB CONNECTION:  INFO:  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^- READ OPERATION  -^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ INFO:  TPMI OSX RELEASE  -->  skt0.cbb0: TPMI_MAILBOX_OSXML_DMR_WW07_2025 INFO:  TPMI STRUCTURE FILES -->  TPMI_Data_Structures_rev2p6_DMR0.xlsx  |  TPMI_Data_Structures_rev2p6_DMR1.xlsx INFO:  ARG:1 - FEATURE   -->  RIT INFO:  ARG:2 - REGISTER  -->  FIT_CONFIG_0 INFO:  ARG:3 - PORTID    -->  CBB0 INFO:  ARG:4 - IMH       -->  0x0 INFO:  ARG:4 - CBB       -->  0x0 INFO:  ARG:5 - SOCKET ID -->  0x0 INFO:  ARG:6 - DATA      -->  -0x1  || IF -1 then is READ operation VSEC values: 1801000B 1010042 2120000 6002 Found BAR address: %X IPC SKIP DEBUG: [SEGMENT, BUS, DEVICE, FUNCTION]   :  [0, 0, 2, 1] INFO: PFS RIT MMIO_ADRESS:  0x1010ffc06000 DEBUG:  ['Feature Name', 'TPMI_ID', 'Num Entries', 'Entry Size (

### Tags
PTP_SoC,DMR_Manageability_VV,TPMI_DMR_A0_TF

### Conclusion
not_a_bug

### Component
board.platform

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
- **Component Path**: board.platform

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x08B`
- `TPMI registers`
- `TPMI OSXML`
- `TPMI register`
- `TPMI OSX`
- `TPMI STRUCTURE`
- `TPMI request`
- `TPMI Ensuring`
- `TPMI Watcher`
- `TPMI WA`

## Timeline

- **Submitted**: 2025-11-21 20:26:38
- **Closed**: 2025-12-17 06:56:46
- **Days Open**: 25

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
