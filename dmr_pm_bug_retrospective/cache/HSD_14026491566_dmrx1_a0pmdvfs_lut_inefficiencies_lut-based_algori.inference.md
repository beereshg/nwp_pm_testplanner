# HSD 14026491566: [DMR]X1 A0][PM][DVFS] LUT Inefficiencies & LUT-based algorithms updates for IMH memory fabric DVFS

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026491566](https://hsdes.intel.com/appstore/article-one/#/14026491566) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | attran2 |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Telemetry | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Bug uncovered in LUT programming:  With mem_fabric_freq_lut[0] := 8 originally, no memory ratio change can be observed when max CAS/ms count crosses mem_fabric_memory_bw_threshold[0] because its MIN_RATIO is also 8. 
Furthermore DMR architects understand mem (and io) frequencies won't be higher than 2GHz, so LUT indices 0,4,5 for ratio 8,22,25 will be unused thus 1/2 of existing LUT entries are wasted. 

AR Primecode:

 provide a patch to fix/reconfig the LUT-based algorithms:

If max telemetry 

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww48.1]

Based on two experiments were run on the X1 platform with 16 DIMMs, focusing on memory traffic thresholds and frequency transitions, A discrepancy was observed where the measured memory frequency was consistently lower than predicted by the maximum CAS count algorithm, with DVFS selecting a lower frequency bin than expected. Arch described the need to revise the frequency selection lookup table, removing unused or redundant entries and aligning thresholds to cover only the necessary frequency bins. The team discussed making the minimum and maximum frequency indices explicit in the architecture documentation, and agreed to update the spec and code accordingly, with Primecode team reviewing the implementation before changes are finalized.

### Description
Bug uncovered in LUT programming:  With mem_fabric_freq_lut[0] := 8 originally, no memory ratio change can be observed when max CAS/ms count crosses mem_fabric_memory_bw_threshold[0] because its MIN_RATIO is also 8. 
Furthermore DMR architects understand mem (and io) frequencies won't be higher than 2GHz, so LUT indices 0,4,5 for ratio 8,22,25 will be unused thus 1/2 of existing LUT entries are wasted. 

AR Primecode:

 provide a patch to fix/reconfig the LUT-based algorithms:

If max telemetry is below the lowest threshold, a DVFS rule should default to UFS_CONTROL.min_ratio:

IF maxΔcount < mem_fabric_*_bw_threshold[0], THEN mem_fabric_mem_freq_ratio := UFS_CONTROL.min_ratio

For more effective use of the LUTs: mem_fabric_freq_lut[] = ubr_d2d_freq_lut[] = {10, 12, 14, 16, 18, 20}

All LUTs' *threshold[] should be reprogrammed, aligning to the revised freq_lut from (ii).

For MCR vs. DDR5 DIMMs populated, the MC BW and the required mem fabric frequencies are quite different.  Primecode should detect the memory type, and then use one of the 2 sets of mem_fabric_*_memory_bw_threshold[] below.
In summary, the revised LUTs should have the following contents:

### Comments (latest)
++++14614841366 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14026485276.

++++14614850993 vwang
Based on the data collection of the mother sighting(14025923151), we found few issues from the HAS and Primcecode. We use this one to address the modification of the LUT. 

++++14614863104 shreyasu
Timothy and I met to discuss all the changes. The following are notes from the meeting: We want to do 3 changes: 1.UBR_D2D, MEM BW CHECK, RING BW CHECK = min freq as default values before the LUT search begins 2. Update all the tables values based on experimentation 3. Add the mcr vs ddr5 check changes based on AMAP Register Next steps: 1. AR Timothy: Do we expect the DIMM types to be uniform across all MCs? Double check with Vijay  2. AR Timothy: When is the information available? End of Ph5 and End of BIOS? 3. AR Shreyas: Make sure AMAP register is accessible in DMR. Alex mentioned that we use a new register Mc::DfiCommonCtrl in DMR to determine DIMM type.  4. AR Shreyas to confirm with Vidar that we use this current HSD (14026491566) for the spec change. We could use the earlier HSD (14025923151) for the other arch/post-si debug work that is still open and on-going. Once Timothy makes the HAS updates, this one can be cloned to a primecode spec change.  Parent HSD that has history: https://hsdes.intel.com/appstore/article-one/#/14025923151

++++14614863987 vwang 
Discussed with Timonthy, we use this one to address the HAS updates and Primecode changes of LUT accordingly.


++++14614864064 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14026491566] of [component=fw.primecode] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [feature] to [server.bugeco.id=14026545317] of [component=soc.PrimeCode 2.0#] in [release=dmrhub-a0]
++++22611621129 tkam 
With regards to my comment 1.c, I have updated the DMR Fabrics DVFS HAS at https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html#memory-fabric-gv-flow-chart This primecode bugeco 14026491566 should fix LUT Inefficiencies & LUT-based algorithms updates for IMH memory and IO fabric DVFS. Specifically, I propose primecode include similar LUT fixes related to IO fabric DVFS as appended below.


++++22611726858 mbfausto
[SysDebug] The FW ticket (id=14026545317) cloned from this sighting has been fixed and released in ingredient version "DMR_A0_6000098C" on [SysDebug] Sighting tag appended with "FIX_PATCH_DMR_A0_6000098C" [SysDebug] [SysDebug] The Sighting owner (attran2) may be enabled to validate the fix is working in the released collateral.

++++22611727032 mbfausto
[SysDebug Tag Script] IFWI version "DMR_AP_2026.05.1.02" has been released that contains the component release "FIX_PATCH_DMR_A0_6000098C" [SysDebug Tag Script] Sighting tag appended with "FIX_IFWI_DMR_AP_2026.05.1.02"

++++22611731497 mbfausto
[SysDebug Tag Script] BKC version "OKS_DMR_AP_2026WW06" has been released that contai

### Tags
SysDebugCloned,SysDebugDccbBypass,FV_PM,FIX_PATCH_DMR_AP1_A0_6000098C,FIX_IFWI_DMR_AP1_2026.05.1.02,FIX_BKC_OKS_DMR_AP1_2026WW06, PSF=N

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

- **Primary Feature**: Telemetry
- **Sub-Feature**: general
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2025-11-22 02:14:29
- **Root Caused**: 2025-12-03 06:14:53
- **Closed**: 2026-02-13 17:22:31
- **Days Open**: 83

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
