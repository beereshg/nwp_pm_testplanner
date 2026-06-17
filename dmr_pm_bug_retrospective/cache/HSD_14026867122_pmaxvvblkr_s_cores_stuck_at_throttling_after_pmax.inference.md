# HSD 14026867122: [PMAX][VVblkr_S] Cores stuck at throttling after PMAX injection harassing

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026867122](https://hsdes.intel.com/appstore/article-one/#/14026867122) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | pcanetel |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | PState Stack | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

After 15 minutes of PMAX events injection cores and CFC ratios are not able to recover from frequency throttling.

Steps to reproduce: 

-Read core frequency

       sv.socket0.cbb0.compute3.module29.core0.ucode_cr_perf_status.core_ratio_100mhz.read()

       13

       

-Set MT0 DAC to the value where PMAX events are generated several times (between 0x0 - 0xff)

       sv.socket0.imh0.pmax.pmax0.
pmax_control.pmax_dac0_hvm_codes.write(0x98)

-Verify PMAX counter is increasing

      sv.socket0

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww14.1]

the new patch removes the IO throttle indication update in the DCF flow to reduce conflicts and unnecessary register accesses, aiming to maintain the PMX IP in the correct state and avoid extra assertions.

Patricia confirmed that data for the harasser patch was already shared with Jayati, but noted that the HC was not updated and results were only shared via chat.

﻿[26ww13.3]

The team continues to investigate the core stuck issue, with Patricia collecting new data and Jayati providing test patches. The group discussed the need for closer synchronization and possibly daily calls to accelerate progress.

﻿[26ww13.1]

Jayati provided another test patch for this core stuck issue; 

Patricia committed to working on this today.

﻿[26ww12.4]

* Traces ready, need review by Primecode/PUnit

* Trace review should tell us if the signal is level coming into PUnit/Primecode, or if there is a different order of events from PMAX IP.

[26ww12.3]

Alex explained that Primecode firmware expectations for PMX IP assertion and semaphore clearing do not match observed Punit hardware behavior, prompting a need for detailed IO register trace collection.

﻿[26ww11.
3]

Patricia clarified that to restore core frequency, both the PMax reset and semaphore bits must be set, as simply setting the reset bit is insufficient.

Patricia committed to collecting and sending IO register trace data to assist with further debugging of the core stuck issue.

﻿[26ww11.1]

Patricia and Kirk coordinated the sharing of experimental results and logs, with Kirk planning to follow up with Meghana for additional insights.

[26ww10.3]

Patch received yday, patch testing will be done today.

﻿[26ww09.3]

Patricia collected data showing unexpected PMAX event assertions and worked with Primecode team, the PMAX & PUNIT teams to verify if the fast path assertion is expected when the semaphore is set. The team is awaiting further analysis and will update sightings as new information becomes available.
N

### Description
After 15 minutes of PMAX events injection cores and CFC ratios are not able to recover from frequency throttling.

Steps to reproduce: 

-Read core frequency

       sv.socket0.cbb0.compute3.module29.core0.ucode_cr_perf_status.core_ratio_100mhz.read()

       13

       

-Set MT0 DAC to the value where PMAX events are generated several times (between 0x0 - 0xff)

       sv.socket0.imh0.pmax.pmax0.
pmax_control.pmax_dac0_hvm_codes.write(0x98)

-Verify PMAX counter is increasing

      sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read()

      Pmax counter sample 1: 0x459

      Pmax counter sample 2: 0x935

      Pmax counter sample 3: 0xb76

      Pmax counter sample 4: 0x1018

-After 15 minutes stop the pmax events injection

      
sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_dac0_hvm_codes.write(0xff)

-Verify PMAX counter is not increasing by reading the counter several times

      sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read()

-We expect the core ratio to be recovered when no more pmax events are happening but we can see that the cores are stuck at pm ratio

      sv.socket0.cbb0.compute3.module29.core0.ucode_cr_perf_status.core_ratio_100mhz.read()

      0x5

We can see that IMH fabric ratios are recovered to their initial values

### Comments (latest)
++++22611708444 jsbrooks
 @Canete Leyva, Patricia - Paty, can you confirm that the pmax injections were only on imh0? Let's also dump these registers for throttle wires.  (We'll need to add them in future status_scope update.) sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_io_regs.interdie_throttle_signals_status sv.socket0.imhs.pcodeio_map.io_throttle_indications

++++22611708981 pcanetel
#Generating several PMAX events in IMH0 sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_dac0_hvm_codes = 0x98 sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x301e sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x5262 sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x7e88 #Restoring DAC value to its original value sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_dac0_hvm_codes=0x2d #Reading core frequency sv.socket0.cbb0.compute3.module29.core0.ucode_cr_perf_status.core_ratio_100mhz 0x5 # Verifying no more pmax events are happening  sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x4963 sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x4963 #Registers for throttle wires In [69]: sv.socket0.imhs.pcodeio_map.io_throttle_indications.show() 0x00000000 : throttle_pwm (16:16) (ro/v) -- Local Pmax PWM soft throttle in... 0x00000000 : throttle_3_reset (14:14) (rw/1s/v) -- Nominally reserved FastR... 0x00000000 : throttle_3_semaphore (13:13) (rw/0c/v) -- Nominally reserved F... 0x00000000 : throttle_3 (12:12) (ro/v) -- Local throttle 3 (Nominally reser... 0x00000000 : throttle_2_reset (10:10) (rw/1s/v) -- Set by pcode, cleared by... 0x00000000 : throttle_2_semaphore (09:09) (rw/0c/v) -- Set by HW on rising ... 0x00000000 : throttle_2 (08:08) (ro/v) -- Local throttle 2 (FastRapl) indic... 0x00000000 : throttle_1_reset (06:06) (rw/1s/v) -- Set by pcode, cleared by... 0x00000000 : throttle_1_semaphore (05:05) (rw/0c/v) -- Set by HW on rising ... 0x00000001 : throttle_1 (04:04) (ro/v) -- Local throttle 1 (Pmax) indicatio... 0x00000000 : throttle_0_reset (02:02) (rw/1s/v) -- Set by pcode, cleared by... 0x00000000 : throttle_0_semaphore (01:01) (rw/0c/v) -- Set by HW on rising ... 0x00000000 : throttle_0 (00:00) (ro/v) -- Local throttle 0 (ProcHot) indica... 0x00000000 : throttle_pwm (16:16) (ro/v) -- Local Pmax PWM soft throttle in... 0x00000000 : throttle_3_reset (14:14) (rw/1s/v) -- Nominally reserved FastR... 0x00000000 : throttle_3_semaphore (13:13) (rw/0c/v) -- Nominally reserved F... 0x00000000 : throttle_3 (12:12) (ro/v) -- Local throttle 3 (Nominally reser... 0x00000000 : throttle_2_reset (10:10) (rw/1s/v) -- Set by pcode, cleared by... 0x00000000 : throttle_2_semaphore (09:09) (rw/0c/v) -- Set by HW on rising ... 0x00000000 : throttle_2 (08:08) (ro/v) -- Local throttle 2 (FastRapl) indic... 0x00000000 : throttle_1_reset (06:06) (rw/1s/v) -- Set by pcode, cleared by... 0x00000000 : throttle_1_semaphore (05:05) (rw/0c/v) -- Set by HW on rising ... 0x00000000 : throttle_1 (04:0

### Tags
FV_PM,SysDebugDccbBypass,SysDebugCloned,dmr_neg,FIX_PATCH_DMR_AP1_A0_600009A2,FIX_IFWI_DMR_AP1_2026.20.3.04

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: general
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbb0.compute3.module29.core0.ucode_cr_perf_status.core_ratio_100mhz.read`
- `sv.socket0.imh0.pmax.pmax0`
- `sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read`
- `sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_dac0_hvm_codes.write`

## Timeline

- **Submitted**: 2026-01-20 00:20:04
- **Root Caused**: 2026-04-01 20:45:16
- **Closed**: 2026-05-19 20:16:48
- **Days Open**: 119

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
