# HSD 14026931860: [DMR][IMH][PrimeCode] CFCMEM_CDYN_MAX fuse is set to 0 by UPS causing FIVR to transition to PS1 which is not POR for CFCMEM FIVR.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026931860](https://hsdes.intel.com/appstore/article-one/#/14026931860) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | haaguirr |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Power/RAPL | 60% |
| **Sub-Feature** | VR | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

CFCMEM_W and CFCMEM_E FIVRs are booting at PS1 which is not POR. This is happening due to the following fuse is set to 0x0.

	

punit.pcode_cfcmem_cdyn_max = 0x0

 

From Juan F Chacon Chavarria:

           
So both teams are setting part of the fuses involved with the intention of
forcing CFCMEM FIVR at PS0.

However both strategies are not getting along, as it is seen current
CFCMEM Cdyn combination is forcing CFCMEM FIVR at PS1 always:

 

  

punit.pcode_cfcmem_cdyn_max = 0x0
      (From UP

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
S 18 60 

Hector/Alex 

Summary : CFCMEM_W and CFCMEM_E FIVRs are booting at PS1 which is not POR. This is happening due to the following fuse is set to 0x0.

punit.pcode_cfcmem_cdyn_max = 0x0

 

WW5.4

 

So both teams are setting part of the fuses involved with the intention of forcing CFCMEM FIVR at PS0.

 

However both strategies are not getting along, as it is seen current CFCMEM Cdyn combination is forcing CFCMEM FIVR at PS1 always:

 

punit.pcode_cfcmem_cdyn_max = 0x0 (From UPS/Modeling we agreed on this value 0 because FIVR PS was not POR for CFCMEM FIVR)

punit.pcode_cfcmem_ps0_iccmax = 0xff (Hector’s BKM to force at PS0)

punit.pcode_cfcmem_ps1_iccmax = 0x0 (Hector’s BKM to force at PS0)

 

What this change means?

 

What are the implication of running with different values? 

No major concern, no power implications here 
 

Ready to clone this to bugeco -> This is just an implementation issue 
Not critical for ES1

Next)Alex/Team) Please provide a debug patch 
Next)Matthew) Please promote this as a Prime code bug

### Description
CFCMEM_W and CFCMEM_E FIVRs are booting at PS1 which is not POR. This is happening due to the following fuse is set to 0x0.

	

punit.pcode_cfcmem_cdyn_max = 0x0

 

From Juan F Chacon Chavarria:

           
So both teams are setting part of the fuses involved with the intention of
forcing CFCMEM FIVR at PS0.

However both strategies are not getting along, as it is seen current
CFCMEM Cdyn combination is forcing CFCMEM FIVR at PS1 always:

 

  

punit.pcode_cfcmem_cdyn_max = 0x0
      (From UPS/Modeling we agreed on this value 0 because FIVR PS was not POR
      for CFCMEM FIVR)

  

punit.pcode_cfcmem_ps0_iccmax =
      0xff (Hector’s BKM to force at PS0)

  

punit.pcode_cfcmem_ps1_iccmax = 0x0
      (Hector’s BKM to force at PS0)

 

           

@Toh, alex
seang kheng

 

@Chen,
Steven Y

 would you recommend some viable combination of the fuses
above to achieve forcing CFCMEM FIVR at PS0?

 

  
Normal

  
0

  

  

  

  

  
false

  
false

  
false

  

  
EN-US

  
X-NONE

  
X-NONE

  

   

   

   

   

   

   

   

   

   

  

  
MicrosoftInternetExplorer4

  

   

   

   

   

   

   

   

   

   

   

   

  

 

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

### Comments (latest)
++++14615010388 ejdehaem
If CFCMEM_CDYN_MAX = 0 and CFCMEM_LEAKAGE_REFERENCE_CURRENT = 0, then the resolved ICC calculation = 0. With the current primecode implementation if the ICC calculation resolves to 0 Amps we will wind up in PS1. We should treat this as a Primecode bug and use fuse CDYN_MAX == 0 to disable phase shedding and always stay in PS0.

++++14615010418 ejdehaem 
Here is the analysis and proposed solution Bug Report: Phase Shedding Algorithm Incorrectly Selects PS1 When Current Draw is Zero Problem Description The FIVR Phase Shedding algorithm in DynamicFivrPsCalculator::findPsEncodingForGivenMaxCurrent() incorrectly returns PS1 (lowest performance state) instead of PS0 (highest performance state) when the calculated ICC (max current) equals zero. Root Cause The search algorithm uses strict inequality (<) which fails when both the calculated current and PS level ICCMAX threshold are zero: // Current implementation in fivr_ps_calc.cpp line 106 while ((ps_enc > 0U) && (ps_level_icc_max_array[ps_enc] < max_current)) { ps_enc--; }
 Failure scenario: Fusing: PS0_ICCMAX = 0xFF (255A), PS1_ICCMAX = 0 Calculated current: ICC = 0 (when cdyn_max = 0 and ref_leakage = 0) Algorithm checks: PS1_ICCMAX < ICC → 0 < 0 → FALSE Loop doesn't execute, returns PS1 ❌ Expected behavior: Should return PS0 since PS1 cannot support any current (including 0A) Impact Safe fusing configurations fail: When PS1_ICCMAX = 0 is used to disable PS1, the algorithm incorrectly selects it anyway CFC domain with cdyn_max = 0: Always runs in PS1 instead of intended PS0 Violates HAS requirement: Per DMR HAS, algorithm must find "lowest PSx_CURRENT which is greater than or equal to total_max_current" Affected Code File: src/flow/fivr_ps_calc/v1_0/fivr_ps_calc.cpp Function: DynamicFivrPsCalculator::findPsEncodingForGivenMaxCurrent() Lines: 93-112 Component: CFC Phase Shedding (DMR Gen) Proposed Solution Add phase shedding disable logic in DynamicFivrPsCalculator class: 1. Add member variable in fivr_ps_calc.hpp: bool phase_shedding_enabled;
 2. Update init() method to detect disable condition: void Primecode::DynamicFivrPsCalculator::init(float ref_volt_init, float ref_temp_init, float ref_leakage_init, float cdyn_max_init, float cdyn_v_correction_init, float leak_eq_v_init, float leak_eq_t_init, float leak_eq_vt_init, float* domain_ps_icc_max_array) { reference_voltage = ref_volt_init; reference_temperature = ref_temp_init; reference_leakage_current = ref_leakage_init; cdyn_max = cdyn_max_init; cdyn_v_correction = cdyn_v_correction_init; leak_eq_v = leak_eq_v_init; leak_eq_t = leak_eq_t_init; leak_eq_vt = leak_eq_vt_init; ps_level_icc_max_array = domain_ps_icc_max_array; // Disable phase shedding if cdyn_max is zero phase_shedding_enabled = (cdyn_max_init != 0.0f); }
 3. Update calculatePhaseSheddingVal() method: uint8_t Primecode::DynamicFivrPsCalculator::calculatePhaseSheddingVal(uint32_t frequency_hz, float voltage, float temperature) { // If phase shedding disabled, al

### Tags
FIVR,PrimeCode,SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_60000994,FIX_PATCH_DMR_AP1_A0_60000994,FIX_IFWI_DMR_AP1_2026.10.4.01,BKC#OKS_DMR_AP_X1_2026WW12,FIX_BKC_OKS_DMR_AP1_2026WW12

### Conclusion
fw.bug

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
- **Sub-Feature**: VR
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-01-29 04:18:34
- **Root Caused**: 2026-02-04 22:46:08
- **Closed**: 2026-03-20 18:37:58
- **Days Open**: 50

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
