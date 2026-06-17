# HSD 14027378956: [DMR][PM] Request to update dram_rapl pid_max_limit value for DMR

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027378956](https://hsdes.intel.com/appstore/article-one/#/14027378956) |
| **Status** | root_caused.validating |
| **Priority** | 3-medium |
| **Owner** | dlwu |
| **Component** | hw.power |
| **Defect Die** | ioe |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | PState Stack | 45% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

1) The current dram_rapl pid_max_limit value is set to 2050 for both RDIMM and MRDIMM.

2) We are requesting that this value be updated so a different value is used for each DIMM type:

RDIMM = 2050. From below graph for RDIMM, we are seeing BW saturation running MLC around pid value of 1700. 2050 will be a good value to give some margin and apply throttling when beyond this limit.

MRDIMM = 3500. From below graph for MRDIMM, we are seeing BW saturation running MLC around pid value of 3200. 3500

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww14.1]

A meeting is planned to obtain information from the MRC team on which register values are used for NNPID configuration, as this detail is missing from the latest HAS update and is blocking progress.

﻿[26ww12.1]

The team reviewed EMON profiling and debug data showing significant DRAM RAPL throttling when limited channels are enabled, and identified that the PID max limit is set too low for MRDIMM, causing bandwidth shortfalls. the main issue is the PID max limit not being set correctly for different memory types, and assigned Vijay as the architecture owner to define the matrix and coordinate updates.

Alex emphasized the need for a spec update to define distinct PID max limits for RDIMM, MRDIMM, and 2DPC configurations

### Description
1) The current dram_rapl pid_max_limit value is set to 2050 for both RDIMM and MRDIMM.

2) We are requesting that this value be updated so a different value is used for each DIMM type:

RDIMM = 2050. From below graph for RDIMM, we are seeing BW saturation running MLC around pid value of 1700. 2050 will be a good value to give some margin and apply throttling when beyond this limit.

MRDIMM = 3500. From below graph for MRDIMM, we are seeing BW saturation running MLC around pid value of 3200. 3500 will be a good value to give some margin and apply throttling when beyond this limit.

### Comments (latest)
++++14615211596 vwang
[CloneScript] PreSighting 14027269356 cloned to Sighting 14027378956

++++14615218197 parekhsa
We were advised to hold off on updating RDIMM/MRDIMM pid_max values until 2‑DPC data is available. While 2‑DPC is expected to require a higher pid_max, the magnitude is currently unclear.

++++14615225020 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14027378956] of [component=hw.power] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [spec] to [server.bugeco.id=14027428014] of [component=soc.top] in [release=dmrhub-a0]

++++14615228522 vwang
There is an email discussion on going,  Vijay is working on the details.  Currently pending below 2 inquires: 1) post-si data to show what is the pid_max needed for each on these configs   -->  David Lwu/Srihari 2) Asked whether the NN-PID can handle wide dynamic range and hence we don't have to do these config based PID limits   --> Anna

++++14615242104 dlwu
1) We note that on a 2DPC system, the speed of the memory is reduced from 8000MT/s to 6000MT/s. This is as expected. 2) We note that the tdp power limit for 2DPC system using this memory configuration is 392W. 3) On 2DPC system, we are seeing a lot of system insability due to UBR VN0 Bug: https://wiki.ith.intel.com/spaces/SIPGSLD/pages/4616304388/UBR+VN0+Bug. Using the workarounds suggested by the HSD i.e. small hammer workaround, large hammer workaround, or C2M's method of running with reduced fixed frequency either corrupted the gathered data, or was not effective on the 2DPC system. 4) We were able to run read-only mlc workload on 2DPC system with 32X RDIMM DDR5-8000 with constant reboot after hanging. 5) Based on data shown below, we recommend to use the same pid_max_limit of 2050 for RDIMM 1DPC as well as 2DPC.
++++22611818283 bquerbac
The architecture recommendation is to only configure the nnpid with realistic range that the pid can actually drive the system under control to (eg: for GNR, I recommended the 2050 limit to keep the system linear. On DMR, for 2 different DIMM types, RDIMM vs MRDIMM, two different max bandwidth are measured to be 3000 and  2050. 1DPC vs. 2DPC did not impact this measurement.)  This realistic range can be read from MRC/BIOS based on actual DIMM trained/initialized on the system. (This is similar to the socket RAPL issue of 0-255, which is unrealistically to large of range.) See below:   HAS will be updated this week to reflect the realistic range needed for nnpid configuration.
++++14615267231 bquerbac
HAS updated: https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/NNPID%20HAS/NNPID%20HAS.html#nnpid-configuration

++++14615270775 parekhsa
Primecode requires details on which registers to read in order to determine the PID max limit based on DRAM type. This information is not included in the latest HAS update. Progress is currently blocked until this information is provided.

++++14615279085 parekhsa
Direction from arch team is to figure out the dimm type and then s

### Tags
val_agent,SysDebugCloned,SysDebugDccbDone,SysDebugDccbDriver,FIX_PATCH_DMR_AP1_A0_600009A2,FIX_IFWI_DMR_AP1_2026.20.3.04

### Conclusion
hw.arch

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: general
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-03-13 07:40:49
- **Root Caused**: 2026-03-18 12:54:10
- **Days Open**: 69

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
