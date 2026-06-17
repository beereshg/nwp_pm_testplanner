# HSD 14027043232: [DMR][PM][TPMI] Bad mapping for TPMI registers OPC_DIMM_TEMPS_*

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027043232](https://hsdes.intel.com/appstore/article-one/#/14027043232) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | hmpicosm |
| **Component** | hw.power |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Platform PM Interface | 80% |
| **Sub-Feature** | PECI | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

According to 
TPMI HAS
 this should be the mapping for OPC_DIMM_TEMPS_* to access DIMM temperatures when CLTT with PECI is enabled.

Using TPMI framework provided by OOBMSM team we expect to have the following behavior when access to memory channel temperature registers.

Looks that the mapping is not correct configured since trying to write to a memory channel results on writing to another one even another portid that it is not valid, see the following example for more reference.

In : 

 #read

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
According to 
TPMI HAS
 this should be the mapping for OPC_DIMM_TEMPS_* to access DIMM temperatures when CLTT with PECI is enabled.

Using TPMI framework provided by OOBMSM team we expect to have the following behavior when access to memory channel temperature registers.

Looks that the mapping is not correct configured since trying to write to a memory channel results on writing to another one even another portid that it is not valid, see the following example for more reference.

In : 

 #reading temps before write

In :  

sv.socket0.imhs.memss.mcs.mcscheds_common.dimm_temp_snapshot

[

0

]

socket0.imh0.memss.mc0.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh0.memss.mc1.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh0.memss.mc2.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh0.memss.mc3.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh0.memss.mc4.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh0.memss.mc5.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh0.memss.mc6.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh0.memss.mc7.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh1.memss.mc0.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh1.memss.mc1.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh1.memss.mc2.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh1.memss.mc3.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh1.memss.mc4.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh1.memss.mc5.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh1.memss.mc6.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

socket0.imh1.memss.mc7.mcscheds_common.dimm_temp_snapshot

[

0

] - 

0x00181919

In :  

#setting WAs from OOBMSM

In :  

sv.socket0.imhs.oobmsm.oobm

### Comments (latest)
++++22611757794 agraback
Pasting my comment from the presighting: When the TPMI spec is saying this field is Package mapped, this is the MC to Pkg Mapping it's referring to: So if i look at this memory map from a previous comment ( 14615068671) That translates to this Dimm Channel # which is what the OPC_DIMM_TEMP is indexed by -- it is not by MC x IMH. This should clean up your results but recommend to check with unique values in each Dimm Channel to make sure it is proper Skt Imh Mc Dimm Dimm Channel on Package 0 0 2 0 CH2 0 0 3 0 CH0 0 0 6 0 CH10 0 0 7 0 CH8 0 1 1 0 CH13 0 1 2 0 CH11 0 1 5 0 CH5 0 1 6 0 CH3
++++14615092376 lmalagon
Not a bug, we can close this. Clarification provided by  @Grabacki, Alex on how primecode is mapping each MC temperature, TPMI Arch (Stan) made a modification to the spec after clarify that these registers are not linked to the MC number  After this clarification validated the values populated in opc_dimm_temps_* with successful result:

### Conclusion
not_a_bug

### Component
hw.power

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

- **Primary Feature**: Platform PM Interface
- **Sub-Feature**: PECI
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI registers`
- `TPMI HAS`
- `TPMI framework`
- `TPMI OSX`
- `TPMI STRUCTURE`
- `TPMI Watcher`
- `TPMI WA`
- `TPMI data`
- `TPMI spec`
- `TPMI Arch`

## Timeline

- **Submitted**: 2026-02-11 23:06:27
- **Closed**: 2026-02-18 13:05:33
- **Days Open**: 6

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
