# HSD 16028613872: [DMR][x1-a0][fused]{RAPL} : platform_rapl_power_unit.energy_unit read as 0xe

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16028613872](https://hsdes.intel.com/appstore/article-one/#/16028613872) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | hkharya |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Power/RAPL | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Actual Behavior

 : 
 

platform_rapl_power_unit.energy_unit read as 0xe.

Expected Behavior

 : 

 
platform_rapl_power_unit.energy_unit should be read as 0x0. 

Because the resolution for platform rapl energy status is 1j which is documented here 

https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Psys/10nm%20wave%203%20Psys_platform%20turbo%20HAS%20rev0.99.html#platform_energy_status

[root@dmr-bkc pmutil]# ./pmutil_bin -tR PLATFORM_RAPL_POWER_UNIT

For Partition0 SOCKET0 TPMI_I

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
Issue: platform_rapl_power_unit.energy_unit Value Discrepancy: 0xE vs. 0x0 from the updated HAS

[25WW40.1]

Timothy explained that Prime Code incorrectly hardcoded the energy unit to one Joule, while the expectation is to reference the energy unit as specified in OSXML. Shreyas and Timothy reviewed multiple documents, including OSXML, GNR and DMR, confirming that the correct value is present in OSXML and that Prime Code should not override it. They agreed that any supplementary documents should be updated if discrepancies are found, but OSXML remains the primary source. Vinila requested that Timothy remove any conflicting references in TPMI HAS and ensure that only the correct value from OSXML is used, to avoid future confusion. Timothy agreed to clean up the documentation and remove the hardcoded value from TPMI HAS. 

PrimeCode team is working on a patch in parallel to TPMI documentation clean up

[25WW39.3]

The ambiguity around the correct energy unit specification. Arch folks need to determine whether the issue is a real bug or a documentation misunderstanding, and the team agreed to await the PM Rock team's findings before taking further action. Suchismita and the PM Arch team will take an action to consult stakeholders and return with a definitive answer, while the team agreed to hold off on further changes until clarification is received. [25WW39.1]
a previously hardcoded value for the energy unit (hex E) was propagated to both internal and external validation teams due to outdated or changed specifications, leading to inconsistencies in validation.  Arch folks raised concerns about the lack of a formal process for freezing or versioning specifications at the start of validation, which contributed to confusion when spec values changed without notification. 
Current State and Next Steps: The group determined that the current documentation appears correct, but prime code still uses an outdated value; action items include identifying the authoritative spec and

### Description
Actual Behavior

 : 
 

platform_rapl_power_unit.energy_unit read as 0xe.

Expected Behavior

 : 

 
platform_rapl_power_unit.energy_unit should be read as 0x0. 

Because the resolution for platform rapl energy status is 1j which is documented here 

https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Psys/10nm%20wave%203%20Psys_platform%20turbo%20HAS%20rev0.99.html#platform_energy_status

[root@dmr-bkc pmutil]# ./pmutil_bin -tR PLATFORM_RAPL_POWER_UNIT

For Partition0 SOCKET0 TPMI_INSTANCE0: 0xa383

For Partition1 SOCKET0 TPMI_INSTANCE0: 00

[root@dmr-bkc pmutil]#

In [6]:
 

sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.platform_rapl_power_unit.show()

0x000000000000 : rsvd3 (63:16) (ro/v) -- RESERVED

0x00000000000a : time_unit (15:12) (ro/v) -- Time Units used for power control registers. The actual unit value is c...

0x000000000000 : rsvd2 (11:11) (ro/v) -- RESERVED

0x00000000000e : energy_unit (10:06) (ro/v) -- Energy Units used for power control registers. The actual unit value ...

0x000000000000 : rsvd1 (05:04) (ro/v) -- RESERVED

0x000000000003 : pwr_unit (03:00) (ro/v) -- Power Units used for power control registers. The actual unit value is c...

### Comments (latest)
++++1666989838 mps
<p>Attaching the email conversation from stan</p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/16028524203" style="width: 1458px; height: 492.104px;" data-processed="true" /><br /></p>

++++1666989839 hkharya
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 16028524193.
++++22611467391 agraback
I looked through the primecode and I don’t see any write to that platform_rapl_power_unit TPMI line.   Do you still see 0xE in that field at CPU reset break?   Which Unified Patch version are you using?

++++22611468030 agraback
Shreyas pointed me to a section of code where primecode loops through the *_rapl_power_unit registers for each RAPL domain and initializes the energy_unit to the same value for all three. So Primecode is indeed the one writing 0xE. Still investigating our side to see if this was a miss (bug) or we never got the hsd request to update the behavior for DMR (enhancement)
++++14614631939 vwang
[CloneScript] Sighting [sighting_central.sighting.id=16028613872] of [component=fw.primecode] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [feature] to [server.bugeco.id=14025927896] of [component=soc.PrimeCode 2.0#] in [release=dmrhub-a0]

++++14614631990 vwang
We will need a patch to confirm teh correct value of platform_rapl_power_unit.energy_unit .

++++14614640702 tdarrow 
Primecode is likely following the wave3 common HAS https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html  Which shows: According to the DMR RAPL HAS it should initialized from TPMI OSXML. https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#register-programming-1  It looks like primecode hardcodes the energy_unit to 0xe and doesn't initialize it to anything else.  Additionally, primecode does not look like it is considering the the energy units at all.  The DMR RAPL HAS states that it's energy units are defined in the PLATFORM_RAPL_POWER_UNIT. This is the section in the code I am talking about:


++++14614643874 vwang
From Stan: If we are reading  platform_rapl_power_unit.energy_unit  from IMH0, it should be 0x0, otherwise it is a bug. The value in CBBs doesn’t care.  @Chen, Stanley  checked OSXML has correct value of 0x0, so Primecode should determine why it is not 0x0.  Arch team please confirm if the recommendation to use the osxml default for Psys Energy Unit made as part of this update to the HAS? Was there a primecode HSD request filed to capture it? Stan Chen 0.90 Updated Socket and Platform RAPL ‘Register Programming’ chapters. 6/1/2025 https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html

++++14614644086 vwang 
We do have the feature request to Change Psys PWR_UNIT to 1W (from 1/8W) SOC CCB 22021507562 - [DMR-CCB] Change Psys PWR_UNIT to 1W (from 1/8W Platform CCB:  15018078904 - [CCB] Change Psys PWR_UNIT to 1W (from 1/8W) The reas

### Tags
SysDebugCloned,SysDebugDccbBypass,TEMP_WA_PATCH_DMR_AP1_A0_60000974_POWERON,FWTF_PO_UNBLOCKED,DMR_Manageability_BEAT,FIX_PATCH_DMR_AP1_A0_6000097B,FIX_IFWI_DMR_AP1_2025.45.4.02,BKC#OKS_DMR_AP_X1_2025WW46,FIX_BKC_OKS_DMR_AP1_2025WW46, PSF=Y

### Conclusion
fw.arch

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
- **Sub-Feature**: general
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI HAS`
- `TPMI documentation`
- `TPMI line`
- `TPMI OSXML`
- `TPMI register`
- `TPMI PLATFORM_RAPL_POWER_UNIT`
- `TPMI space`
- `TPMI PWR_UNIT`
- `TPMI and`
- `TPMI Socket_RAPL_POWER_UNIT`

## Timeline

- **Submitted**: 2025-09-16 09:40:47
- **Root Caused**: 2025-09-18 02:02:09
- **Closed**: 2026-03-03 20:36:56
- **Days Open**: 168

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
