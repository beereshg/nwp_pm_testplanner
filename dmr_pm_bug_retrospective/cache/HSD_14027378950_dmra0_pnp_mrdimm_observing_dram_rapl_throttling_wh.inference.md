# HSD 14027378950: [DMR][A0] [PnP] MRDIMM observing DRAM RAPL throttling when running core2mem max BW traffic, resulting in 30% BW drop

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027378950](https://hsdes.intel.com/appstore/article-one/#/14027378950) |
| **Status** | rejected.merged |
| **Priority** | 3-medium |
| **Owner** | dlwu |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Sideband/D2D | 52% |
| **Sub-Feature** | D2D | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

This is a discovery from the MRDIMM performance issue HSD [
22021918296 - [DMR][X1 A0] [PnP] MRDIMM Memory 100Read BW below Target on 48c 32cbo with only 4ch enabled.
] 
on DMR X1. 

In configurations of DMR X1 and X4 with MRDIM, we have noted an increased number of DRAM RAPL throttling cycles when running traffic with a limited number of DIMMs populated.

[Update 2/12/26: since filing this issue, we found we can reproduce it on 192C and 224C DMR with 16 channels populated with MRDIMM 1DPC]

To 

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
Need to sync with David ...

### Description
This is a discovery from the MRDIMM performance issue HSD [
22021918296 - [DMR][X1 A0] [PnP] MRDIMM Memory 100Read BW below Target on 48c 32cbo with only 4ch enabled.
] 
on DMR X1. 

In configurations of DMR X1 and X4 with MRDIM, we have noted an increased number of DRAM RAPL throttling cycles when running traffic with a limited number of DIMMs populated.

[Update 2/12/26: since filing this issue, we found we can reproduce it on 192C and 224C DMR with 16 channels populated with MRDIMM 1DPC]

To illustrate, in a scenario where only 4 channels were enabled on the DRM X1 with 48c MRDIMMS out of the box, we observed a bandwidth of merely 261 GB/s, which equates to approximately 33 GB/s per sub-channel. This figure falls significantly short of our expectations for MRDIMM, where each sub-channel should ideally achieve around 46-47 GB/s with 90% efficiency. Further EMON profiling revealed that substantial RAPL throttling occurs for approximately 20-25% of cycles on each channel, leading to the observed performance degradation.

A critical observation is that when all 16 channels are in operation, we encounter D2D limitations, and each sub-channel barely reaches around 12 GB/s. While this bandwidth is low, it does not seem to trigger any DRAM RAPL throttling. Conversely, enabling a limited number of channels, as in the aforementioned example with only 4 channels, induces significant stress, resulting in DRAM RAPL throttling.

With DRAM RAPL disabled, we noticed an improvement in bandwidth for 100R, increasing from 261 GB/s to 297 GB/s. 

root@fl31ca106fs0308:/home/pnpwls/mlc# ./mlc_internal --loaded_latency -d0 -b2g

Intel(R) Memory Latency Checker (for Internal Use Only) - v3.12-rc01-private-internal

Command line parameters: --loaded_latency -d0 -b2g

Using buffer size of 2048.000MiB/thread for reads and an additional 2048.000MiB/thread for writes

Measuring Loaded Latencies for the system

Using all the threads from each core if Hyper-threading is enabled

Using Read-onl

### Comments (latest)
++++14615211587 vwang
[CloneScript] PreSighting 22021937101 cloned to Sighting 14027378950
++++22611805767 mbfausto
Team, why was it decided that the theory of "dram_rapl_throttling is due to pid_max limit value set too low" ?  That was identified on 2/18 but the ticket doesn't say why that was dropped and what other avenues have been under debug/exploration? What is the current leading data/theory then?

++++22611805771 mbfausto
WAit, there is a 2nd sighting 14027378956 that discusses the limit value. The title just mentions a BW drop, that's a symptom ... what is this sighting pointing at and debugging?  What is unique about this sighting versus 14027378956?

### Tags
PLATPNP,PNP BASE,BASE PNP,Perf_C2M,PTP_SoC

### Conclusion
no_root_cause.rejected

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

- **Primary Feature**: Sideband/D2D
- **Sub-Feature**: D2D
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-03-13 07:33:17
- **Closed**: 2026-03-16 21:36:39
- **Days Open**: 3

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
