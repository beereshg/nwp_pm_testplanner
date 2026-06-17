# HSD 18044008885: [DMR AP][A0] Package C residency counters for PC2, PC3, PC6, PC7, PC8, PC9, PC10 remains at 0x0

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [18044008885](https://hsdes.intel.com/appstore/article-one/#/18044008885) |
| **Status** | rejected.filed_by_mistake |
| **Priority** | 3-medium |
| **Owner** | psiebies |
| **Component** | val.env.content |
| **Defect Die** | ioe |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | C6 | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Description: 
 the pkgC residency counter (and counters for PC2, PC3, PC6, PC7, PC8) remains at 0x0. The pkgC residency counter reads 0x0, and the counters for its sub-states remain unchanged.

TCID: 
16028383437 - [Post-Si][DMR][SCIV][Power Management][PKGC] Validate PKGC6 entry on CentOS

Test environment :

IFWI
 : https://ubit-artifactory-sc.intel.com/artifactory/DEG-IFWI-LOCAL/SiEn-OakStream-DiamondRapids-AP/IFWI/Purple//2025.41.2.01/OakStreamRp_DMR_1P0_FSP_Glue_Debug/OKSDCRB1_1P0_NonIPClea

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
Description: 
 the pkgC residency counter (and counters for PC2, PC3, PC6, PC7, PC8) remains at 0x0. The pkgC residency counter reads 0x0, and the counters for its sub-states remain unchanged.

TCID: 
16028383437 - [Post-Si][DMR][SCIV][Power Management][PKGC] Validate PKGC6 entry on CentOS

Test environment :

IFWI
 : https://ubit-artifactory-sc.intel.com/artifactory/DEG-IFWI-LOCAL/SiEn-OakStream-DiamondRapids-AP/IFWI/Purple//2025.41.2.01/OakStreamRp_DMR_1P0_FSP_Glue_Debug/OKSDCRB1_1P0_NonIPClean_Trace_DebugSigned/OKSDCRB1_86B_2025.41.2.01_2817.D05_60000970_0.627.0_1P0_NonIPClean_Trace_DebugSigned.bin

Platforms :

AN004022BMH2265, AN004022BMH2511, AN004022BMH2261

Steps to Reproduce issue:

1.
     

Boot to CentOS

2.
     

Check the MSR 0xE2 value

&middot;
        

	

deafult_value_e2= itp.msr(0xE2)

3.
     

Write in the MSR 0xE2 with the value 0x403

&middot;
       

	

 

itp.halt()

&middot;
        

	

itp.msr(0xE2, 0x403)

4.
     

Verify Package C states are enabled:

&middot;
        

	

itp.msr(0xE2)

5.
     

Check PC6 residency through multiple reads (~20
times) of MSR counter:

&middot;
        

	

itp.msr(0x3F9)

 

6.
     

The same observed for

&middot;
        

PC2: MSR 0x60d

&middot;
        

PC3: MSR 0x3f8

&middot;
        

PC6: MSR 0x3f9

&middot;
        

PC7: MSR 0x3fa

&middot;
        

PC8: MSR 0x630

&middot;
        

PC9: MSR 0x631

&middot;
        

PC10: MSR 0x632

 

	

Expected behavior
: 

If the system is idle, multiple reads should display different values-> as residency counter increments while in Pkg C6 state

Actual behavior 
:

### Comments (latest)
++++1862504858 huylex
<p>Impacted test cases:</p><p><!--StartFragment--><a href="https://hsdes.intel.com/appstore/article-one/#/article/16028383437" target="_blank">16028383437 - [Post-Si][DMR][SCIV][Power Management][PKGC] Validate PKGC6 entry on CentOS</a></p><p><!--StartFragment--><a href="https://hsdes.intel.com/appstore/article-one/#/article/16028176323" target="_blank">16028176323 - [Post-Si][DMR][SCIV][Power Management][Misc] Run workload on some cores others keep idle and verify PkgC residency reflects system state</a></p><p><!--StartFragment--><a href="https://hsdes.intel.com/appstore/article-one/#/article/16028646608" target="_blank">16028646608 - [Post-Si][DMR][SCIV][Power Management][PKGC] Validate PKGC entry on CentOS (PC0/C1)</a><!--EndFragment--><!--EndFragment--><!--EndFragment--></p>

++++1862504859 psiebies
Hi, <span style="font-weight: bold; color: #007BFF;" class="intel-user">@M, Srinivasa Rao,</span>&nbsp;please confirm the issue before I push it to the PO WG.

++++1862504860 sm2
<p>Hi <span><span style="font-weight: bold; color: #007BFF;">@Siebieszuk, Pawel</span><span style="color: #000000;">&nbsp;, yes we have seen this issue in Post-SI setups only.&nbsp; On Pre-Si these Test cases were passing. please proceed with&nbsp;</span></span><span style="color: rgb(33, 37, 41); font-size: 1em;">PO WG</span></p>

++++1862504861 psiebies
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 22021653439.

++++1862504862 psiebies
Hi, &nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Ramirez Moreno, Carlos O</span>&nbsp;&nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Picos Morgan, Hector M</span>, could you help with further debugging of this issue? It's also present on the 2S system.

++++1862504863 psiebies
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 18043649980.
++++22611619123 vwang
According to the standard process, please start with pre-sighting with reasonable debugging triage first.

### Conclusion
no_root_cause.rejected

### Component
val.env.content

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
- **Component Path**: val.env.content

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0xE2`
- `MSR 0x60d`
- `MSR 0x3f8`
- `MSR 0x3f9`
- `MSR 0x3fa`
- `MSR 0x630`
- `MSR 0x631`
- `MSR 0x632`

## Timeline

- **Submitted**: 2025-12-03 13:22:07
- **Closed**: 2025-12-04 06:27:49

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
