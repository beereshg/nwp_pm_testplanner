# HSD 18044365227: [DMR X1][PMT][BMC][OOBMSM] Inconsistent Memory Channels in PMT metrics

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [18044365227](https://hsdes.intel.com/appstore/article-one/#/18044365227) |
| **Status** | root_caused.awaiting_fix |
| **Priority** | 3-medium |
| **Owner** | bjanicki |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Telemetry | 75% |
| **Sub-Feature** | Punit Telemetry | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

PAE

 submitted question from Dell about issue in CUPS service related to PMT metrics - after analysis it seems like there is so additional mapping or it is a bug.

﻿

Issue

:

Inconsistent Memory Channels order in metrics 

MEMORY_READ_BW_COUNTER_CHx / 

MEMORY_WRITE_BW_COUNTER_CHx

 from

 

iMH PUNIT Telemetry Aggregator. Observed valid counters reading on disabled/empty MC while on active/populated zero is reported.    

Description:

System contain single DIMM populated - MC3.

Counters bo

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww18.3]

Burrel is working a test patch

﻿[26ww17.3]

The discussion is still on going with more people involved. 

﻿[26ww17.1]

Suchismita is driving the discussion with Vijay on the mapping spreadsheet 

between telemetry items and local IMH MC#

﻿[26ww16.4]

Alex suggested updating PrimeCode PMT entries to use local memory controller numbers instead of DIMM channel numbers, pending confirmation of the mapping for both root and secondary IMH from Suchismita.

Burrell questioned whether the BIOS setting for DIMM population was correct, noting that the dimm_pop bit should reflect actual hardware population, and requested additional data dumps for verification.

Next: continue coordinating with Suchismita and the BIOS team, with Alex planning to formalize the request via email for official attention and further investigation.

### Description
PAE

 submitted question from Dell about issue in CUPS service related to PMT metrics - after analysis it seems like there is so additional mapping or it is a bug.

﻿

Issue

:

Inconsistent Memory Channels order in metrics 

MEMORY_READ_BW_COUNTER_CHx / 

MEMORY_WRITE_BW_COUNTER_CHx

 from

 

iMH PUNIT Telemetry Aggregator. Observed valid counters reading on disabled/empty MC while on active/populated zero is reported.    

Description:

System contain single DIMM populated - MC3.

Counters both READ and WRITE are consistent:

BMC based on DIMMMTR register is reporting MC3 as active and populated as well.

However, reading from the BMC registers: 
MEMORY_READ_BW_COUNTER_CHx / 

MEMORY_WRITE_BW_COUNTER_CHx

Based on spec: 

https://docs.intel.com/documents/primecode/has/PMT_Definitions/dmr_imh/pmt_telemetry.html#about-this-document

and xml: 
https://github.com/intel-innersource/applications.manageability.intel-pmt.tools.python.support.intel-pmt/blob/6f38144a6ac2223d3c1dd8b4d0115eb4cf41f1c7/xml/DMR/IMH/dmr_aggregator.xml#L285

with the result mapping as is in the table below 

Indicate some discrepancies 

Situation observed:

MC

BMC - PMT OOB API

PYSV 

(
  free_run_cntr_read.countervalue )

0

pmt_cmds
  command --opCode GetTelemetrySample --id 9 --index 0 --sampleId 15

Value:
  0x0000000000000000

 

NaN

1

pmt_cmds
  command --opCode GetTelemetrySample --id 9 --index 0 --sampleId 16

Value:
  0x0000000000000000

 

NaN

2

pmt_cmds
  command --opCode GetTelemetrySample --id 9 --index 0 --sampleId 17

Value:
  0x0000000000000000

 

subch0 Value:
  0x0000000000000000

subch1 Value:
  0x0000000000000000

3

pmt_cmds
  command --opCode GetTelemetrySample --id 9 --index 0 --sampleId 18

Value:
  0x0000000000000000

 

subch0 Value: 0x0000000026f4666f

subch1 Value: 0x00000000282be9ad

Total: 0x4F20 501C

4

pmt_cmds
  command --opCode GetTelemetrySample --id 9 --index 0 --sampleId 19

Value:
  0x0000000000000000

 

subch0 Value:
  0x0000000000000000

subch1 Va

### Comments (latest)
++++1862573838 bjanicki
<p>Hi &nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Palanisamy, Saravanan</span>&nbsp;/ &nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Spica, Michal</span>&nbsp;</p><p>Could help with assignment of this sighting.&nbsp;<br />Since it is related to iMH Aggregator I believe the PUINT team might be able to help</p><p><br /></p><p>Regards,</p><p>Bartosz</p>
++++14615310774 daalonso
 @Dominguez, Caesar   @Fausto, Matthew B  Can you guys please have a look?
++++22611837705 mbfausto
Pinged offline and assigning to vt.pm as it right now is IMH P-Unit HW functionality under investigation for Telemetry.
++++14615316039 vwang
 @Pal, Poulomi Could you check?
++++22611837855 agraback
Looks like all three of these areas are potentially out of sync with each other: [Primecode] PMT Telemetry items only listed as CH0-7 on both IMHs [Punit<->MC Telemetry] Tele Items listed as MC East and West 0-3 [SoC Pkg Mapping] CH0-16 spread across both IMHs and Secondary IMH rotated 180 deg (possibly affecting MC East vs West alignment) 15 0x0078 MEMORY_READ_BW_COUNTER_CH[0] 16 0x0080 MEMORY_READ_BW_COUNTER_CH[1] 17 0x0088 MEMORY_READ_BW_COUNTER_CH[2] 18 0x0090 MEMORY_READ_BW_COUNTER_CH[3] 19 0x0098 MEMORY_READ_BW_COUNTER_CH[4] 20 0x00a0 MEMORY_READ_BW_COUNTER_CH[5] 21 0x00a8 MEMORY_READ_BW_COUNTER_CH[6] 22 0x00b0 MEMORY_READ_BW_COUNTER_CH[7]     static constexpr uint32_t mem_ch_bw_read_telemetry_items[NUM_MEM_CHANNELS] = {         val(Primecode::uncore_tele_item::MC_E_TELE_RD_COUNT0),         val(Primecode::uncore_tele_item::MC_E_TELE_RD_COUNT1),         val(Primecode::uncore_tele_item::MC_E_TELE_RD_COUNT2),         val(Primecode::uncore_tele_item::MC_E_TELE_RD_COUNT3),         val(Primecode::uncore_tele_item::MC_W_TELE_RD_COUNT0),         val(Primecode::uncore_tele_item::MC_W_TELE_RD_COUNT1),         val(Primecode::uncore_tele_item::MC_W_TELE_RD_COUNT2),         val(Primecode::uncore_tele_item::MC_W_TELE_RD_COUNT3),     };
++++14615318452 vwang
It seems Primecode owns all PMT reporting.

++++14615325811 bgbest 
IGNORE PREVIOUS COMMENT  Correction - used the wrong value 0xf00c as reference should be 0xf000c.

++++22611844867 agraback
This is what i found as the mapping the DMR telemetry spreadsheet HAS: https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Telemetry.html Spreadsheet: https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/assets/DMR_IMH_Telemetry.xlsx MC_E_TELE_RD_COUNT0 memtopright//mc_0 MC_E_TELE_RD_COUNT1 memtopright//mc_1 MC_E_TELE_RD_COUNT2 mc_6 MC_E_TELE_RD_COUNT3 mc_7 MC_W_TELE_RD_COUNT0 memtopleft//mc_0// MC_W_TELE_RD_COUNT1 memtopleft//mc_1 MC_W_TELE_RD_COUNT2 mc_2 MC_W_TELE_RD_COUNT3 mc_3 So it seems like in Primecode we could just update the PMT entries to local MC# instead of Dimm Ch# but need to confirm the mapping with Suchi for both root and secondary imh. Sent her a direct message on IM as well

++++22611856195 agraback
Had a call wi

### Tags
SysDebugCloned

### Conclusion
hw.arch

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
- **Sub-Feature**: Punit Telemetry
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.pcodeio_map.logregister`
- `sv.socket0.imh0.punit.pmuarray.pmuarray.logregister`
- `sv.socket0.imh0.memss.mcs.subchs.mctrk.dimmmtr_0`
- `sv.socket0.imh0.memss.mcs.subchs.mctrk.dimmmtr_1`
- `sv.socket0.imh0.memss.mcs.subchs.mcscheds.free_run_cntr_read.countervalue`

## Timeline

- **Submitted**: 2026-04-08 18:52:40
- **Root Caused**: 2026-05-12 03:48:03
- **Days Open**: 43

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
