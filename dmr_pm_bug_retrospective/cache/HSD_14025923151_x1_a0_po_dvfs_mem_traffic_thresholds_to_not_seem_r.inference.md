# HSD 14025923151: [X1 A0 PO] DVFS Mem Traffic Thresholds to not seem realistic

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025923151](https://hsdes.intel.com/appstore/article-one/#/14025923151) |
| **Status** | rejected.merged |
| **Priority** | 3-medium |
| **Owner** | attran2 |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Telemetry | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

0x00000000000f4240 :
mem_fabric_memory_bw_threshold_0

0x0000000000155cc0 :
mem_fabric_memory_bw_threshold_1

0x00000000001b7740 :
mem_fabric_memory_bw_threshold_2

0x00000000001e8480 :
mem_fabric_memory_bw_threshold_3

0x0000000000249f00 :
mem_fabric_memory_bw_threshold_4

0x000000000027ac40 :
mem_fabric_memory_bw_threshold_5

Assuming a 1ms interval between checks with a 64B transaction size with the MC E/W telemetry read & write counters being compared against them.

Threshold Name

Hex Value

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww03.3]

Timothy met with Shrihari suggesting that all tunning should do by PTP team, Adolfo Valdez Bahena will take the next steps for extracting the information that Timothy requires. AR sysdebug to define direction on this sighting, as title says that &quot;threshold is not realistic&quot; but this is for functional correctness, Timothy mentions we probably need a new sighting for the tunning issue and close this sighting as pertinent.

[26ww02.3]

Hector will sync up with Anh for X4 system availability and update Timothy, based on results will define next steps. Based on Matthew comments, will talk to Vidar to see if this is downgraded to pre-sighting as the LUT fix is being tracked on another sighting 
14026491566.

[25ww51.3]

Anh just got an X4 system with 32 cores (1CBBx8cores), that is the best silicon available so far, waiting for results on experiments, 32 cores will probably not be sufficient for final tuning but it is a good start point. 

[25ww51.1]

Timothy clarified the need for systems with as many cores and channels as possible for experiments, but Hector M noted that while 16-channel systems were available, the number of cores remained a constraint, with X1 systems having up to 48 cores and X4 systems up to 32 cores.

Timothy and Hector M agreed that Ann would be provided with an X1 system with 32 cores for debugging, and Hector M confirmed that this allocation would be made within the week.

[25ww50.1]

The progress on task 1.a(16 DIMMs) is blocked due to the lack of suitable hardware with more than 48 cores, and Hector M clarified that only X1 48-core parts are available, not X4.

Timothy outlined the need to rerun MLC components at higher sampling rates to investigate discrepancies between expected and measured memory DVFS algorithm frequency requests, with Anh-thu agreeing to focus on specific test cases and coordinate with Shreyas for validation.

Timothy described observed correlation problems between telemetry counters and MLC bandwidth,

### Description
0x00000000000f4240 :
mem_fabric_memory_bw_threshold_0

0x0000000000155cc0 :
mem_fabric_memory_bw_threshold_1

0x00000000001b7740 :
mem_fabric_memory_bw_threshold_2

0x00000000001e8480 :
mem_fabric_memory_bw_threshold_3

0x0000000000249f00 :
mem_fabric_memory_bw_threshold_4

0x000000000027ac40 :
mem_fabric_memory_bw_threshold_5

Assuming a 1ms interval between checks with a 64B transaction size with the MC E/W telemetry read & write counters being compared against them.

Threshold Name

Hex Value

Decimal Value

GB/s Calculation

GB/s

mem_fabric_memory_bw_threshold_0

0x000f4240

1,000,000

(1,000,000 &times; 64 &times; 1000) / 1,073,741,824

59.60

mem_fabric_memory_bw_threshold_1

0x00155cc0

1,400,000

(1,400,000 &times; 64 &times; 1000) / 1,073,741,824

83.44

mem_fabric_memory_bw_threshold_2

0x001b7740

1,800,000

(1,800,000 &times; 64 &times; 1000) / 1,073,741,824

107.29

mem_fabric_memory_bw_threshold_3

0x001e8480

2,000,000

(2,000,000 &times; 64 &times; 1000) / 1,073,741,824

119.21

mem_fabric_memory_bw_threshold_4

0x00249f00

2,400,000

(2,400,000 &times; 64 &times; 1000) / 1,073,741,824

143.05

mem_fabric_memory_bw_threshold_5

0x0027ac40

2,600,000

(2,600,000 &times; 64 &times; 1000) / 1,073,741,824

154.99

Associated ratios to above thresholds:

0x0000000000000008 :
mem_fabric_freq_lut_0

0x000000000000000e :
mem_fabric_freq_lut_1

0x0000000000000012 :
mem_fabric_freq_lut_2

0x0000000000000014 :
mem_fabric_freq_lut_3

0x0000000000000016 :
mem_fabric_freq_lut_4

0x0000000000000019 :
mem_fabric_freq_lut_5

As I understand, max BW for 1 channel of DDR5 RDIMM would be 64 GB/s and MRDIMM at 102.4 GB/s.  

Thresholds in primecode:

Projected thresholds from DVFS HAS:

DVFS HAS Expectation for 1.8 Ghz - Ratio 0x12

Flow is checking MC read and write channel telemetries before comparing the max delta against the thresholds:

The thresholds therefore don't seem appropriate for one channel's potential read or write BW.

### Comments (latest)
++++14614628944 sasmith2
<p>Some data from system using mem config in description.&nbsp; Telemetries polled every 10s and then delta divided by 10000 to get delta/ms:</p><p><br /></p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/14025913110" style="width: 1538px;" /></p><p><br /></p><p><br /></p><p><br /></p><p><b>MLC output from SVOS:</b></p><p>/usr/local/mlc&gt;./mlc_internal
--peak_injection_bandwidth&nbsp; -b240000
-k0-31 -l64 -t60</p><p><b></b></p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">...</p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">Using traffic with
the following read-write ratios</p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">ALL Reads&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; :&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
65526.0</p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">3:1 Reads-Writes
:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 91470.2</p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">2:1 Reads-Writes
:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 105532.2</p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">1:1 Reads-Writes
:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 117502.2</p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">Stream-triad
like:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 77610.6</p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">All NT writes&nbsp;&nbsp;&nbsp; :&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
87459.9</p><p>













</p><p style="margin:0in;font-family:Calibri;font-size:11.0pt">1:1 Read-NT
write:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 90394.9</p>

++++14614628945 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14025913092.

++++14614629104 sasmith2
It is not completely clear from DVFS HAS whether the thresholds being used by primecode are meant to be per MC channel or not.  Indication from table talking about a counter size, might imply in the columns are based on a single counter (read or write in case of MC BW).    As well, pseudo code does state that the check for the memory telemetry check should be per MC channel read OR write counts: Based on that and MC Client HAS and DMR Memory HAS, these thresholds are not realistic: https://docs.intel.com/documents/arch_datacenter/DMR/Overview/Memory.html https://docs.intel.com/documents/ClientSilicon/mtl/ip/memory/MC/MTL_MC/MC.html I have not heard back from @Kam, Timothy in my Teams message asking about the thresholds mentioned in DVFS HAS and how they were calculated.  Input is appreciated.
++++22611474704 tkam
One can reason this through (a) X1 Si experiments or (b) derivations:-   (A) On Stephen's X1 experiments:   The MLC BWs Stephen reported at the bottom (e.g. 65.526GB/s for 100R) is very low relative to the peak core2mem BW (1024GB/s for 100R DDR5 8000MT/s).  So I assume the lowest memory fabric frequency (800MHz) was selected and should be sufficient to support the reported MLC BW.  In other words, the existing X1 experiments may not be a

### Tags
FV_PM

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

- **Primary Feature**: Telemetry
- **Sub-Feature**: general
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI register`
- `TPMI to`
- `TPMI UFS_CONTROL`
- `sv.socket0.cbbs.base.i_ccf_envs.sbo_misc_regs.arac_ctl.monitor_counter_decrement_value`
- `sv.socket0.cbbs.base.i_ccf_envs.sbo_misc_regs.arac_ctl.monitor_block_ia_counter_saturation`
- `sv.socket0.cbbs.base.i_ccf_envs.sbo_misc_regs.arac_ctl.monitor_block_gt_counter_saturation`
- `sv.socket0.cbbs.base.i_ccf_envs.sbo_misc_regs.arac_ctl.long_ring_countdown`
- `sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.ufs_adv_control_1`

## Timeline

- **Submitted**: 2025-09-17 07:43:56
- **Closed**: 2026-01-15 22:16:39
- **Days Open**: 120

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
