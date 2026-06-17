# HSD 22022067937: [DMR][X4][RAPL] Significant Core frequency throttling when running heavy cdyn workloads on high core counts

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22022067937](https://hsdes.intel.com/appstore/article-one/#/22022067937) |
| **Status** | root_caused.validating |
| **Priority** | 3-medium |
| **Owner** | chinnai |
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

Observing significant frequency throttling when running heavy cdyne workloads, such as povray_r, on 192-core/224-core X4 units with higher TDPs of 500W/650W. This throttling reduces frequencies all the way down to 400MHz, which significantly impacts overall performance scores.

The issue seems to be related to FAST RAPL, as disabling the CBB Fast RAPL feature results in stable frequencies but reports power numbers as high as 900W. Thus, disabling RAPL does not appear to be a viable workaround...

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww09.3]

Erick clarified the difference between the 'Stop_Learning' and 'stop_learning_in_margins_flag' flags, recommending that the latter be set to zero to keep learning active within margins, as the feature is not working as expected for DMR.

Nilanjan confirmed understanding of the recommended settings and requested to be included in related discussions, with Erick agreeing to forward meeting series and documentation.

﻿[26ww09.1]

Nilanjan recalled a previous issue with a similar power discrepancy, which Steven Y attributed to a VR firmware update that resolved the error, though the current issue appears to be related to telemetry and PID tuning rather than sensor inaccuracies.

Timothy recommended checking the inputs to the PID and comparing the set power limits with monitored values to determine if the discrepancy is due to sensor issues or PID configuration, while Rajendrakumar confirmed that the latest VR firmware is installed.

The team agreed to share VR script outputs and consult with David Lwu for confirmation, continuing the discussion in an existing chat thread to resolve the discrepancy.

﻿[26ww08.4]

Timothy explained that Srihari planned to file an HSD regarding the PLL mailbox functionality, and no further feedback had been received yet, so the team decided to wait for updates.

﻿[26ww08.3]

Timothy described observed oscillations in power regulation leading to core throttling, emphasizing the need for improved debug tools (PLR, PEM, RAPL_PERF_LIMIT HPM Msg) to identify which limiter is active and to facilitate manual PID tuning.

PID vs. NNPID: The team discussed the effectiveness of the NNPID, which appears to resolve both toggling and locked throttling cases, but agreed to continue collecting data and consider both manual and automatic tuning approaches.

Manual Tuning and Data Collection Plan: Timothy proposed collecting detailed plots of PID inputs and outputs over time, using debug patches to capture internal variables, and incrementally

### Description
Observing significant frequency throttling when running heavy cdyne workloads, such as povray_r, on 192-core/224-core X4 units with higher TDPs of 500W/650W. This throttling reduces frequencies all the way down to 400MHz, which significantly impacts overall performance scores.

The issue seems to be related to FAST RAPL, as disabling the CBB Fast RAPL feature results in stable frequencies but reports power numbers as high as 900W. Thus, disabling RAPL does not appear to be a viable workaround....

Another workaround to achieve stable frequencies involves fixing the frequency to 2.4GHz or lower. This approach results in stable operation with frequencies running at 2.1GHz for povray but it has other side effect like CBB ring running at higher than required frequencies..

Also note in some cases, when running tests with idle states, the system may get stuck at 400MHz until a reboot or disabling/enabling the CBB FAST RAPL feature.

 

This is avg score through the POVRAY run with PCP recipe.. Given the EMON averages the score we are seeing frequency like 1.6 GHz through the run but the power numbers being lower than 650w clearly tells the story that RAPL throttling causing the lower freq.

### Comments (latest)
++++22611750709 chinnai
As discussed in the PM Sync on Wednesday, there are no known issues around this and filing it as sighting to fast track the RAPL throttling as this impacts PCP runs significantly.

++++22611751150 mbfausto
Which frequencies are throttling?  (can we update the title to say core / scf / ccf / etc.) if there is 1 specifically?

++++22611753402 chinnai
@Parekh, Sagar1 Attached IMH/CBB PCUDATA while povray running on the system.  .. Note this was collected while the workload running.. If it has to be collected with different BKM like halting let me know .. 
++++14615072217 parekhsa
Debug in progress.  Current findings from the attached imh logs: Observed heavy CDyne workloads throttling to ~400 MHz. Fast RAPL is active and saturated (fast_rapl_freq_limit=0x4, PID saturated/limited), while reverse‑RAPL line values remain 0 (integral_bound=0x0). This forces the PID integral to clip to zero and collapses output to the min limit. PBM disable is sourced from PCODE_SYSTEM_MODES_CONTROL[15], but current snapshot shows firmware CPL state is not progressing: cpl_flow.patch_persistent.cpl_phases_complete=0x0 cpl_flow.patch_persistent.cpl_done=0x0 cpl_flow.patch_persistent.cpl_finalized=0x0 So CPL3 has not completed; PBM CPL3 flows (including reverse‑line computation) are not running. This explains why reverse‑RAPL values remain zero even though TPMI ADV_CONTROL fields are non‑zero. Next steps:  @Chinnaiyan, Rajendrakumar can you confirm if cpl has completed ? If not, why ? 
++++22611753972 chinnai
The PCODE symbols seems to be not loaded from old patch we used for D2D fix, seems that results in weird PCUDATA.  I am moving to latest patch from Alex for D2D perf workaround, will recollect the logs and attach on new patch. 

++++22611754206 chinnai
Attached newer dump with new patch that confirmed to have PCU data loaded properly. 
++++14615075233 parekhsa
I pulled the new log slice and re‑ran the same checks as before. This one does not show the Fast RAPL failure mode (no zero integral bound / no PBM disable / CPL is complete). Instead, the perf‑limit mask flags a PKG PL2 out‑of‑band limiter. Log snippets (key fields) :  Fast RAPL looks idle / not limiting fast_rapl_inst.fast_rapl_freq_limit=0xff fast_rapl_inst.fast_rapl_limiting=0x0 fast_rapl_inst.pid_controller.is_integral_saturated=0x0 fast_rapl_inst.pid_controller.is_output_limited=0x0 PBM enabled + reverse‑RAPL line valid pwrBdgtMngr.pbm_disabled=0x0 raplVars.patch_persistent_reverse_rapl_line.integral_bound=0x42040000 CPL complete cpl_flow.patch_persistent.cpl_phases_complete=0x4 cpl_flow.patch_persistent.cpl_done=0x1 cpl_flow.patch_persistent.cpl_finalized=0x1 Perf‑limit reason mask raplVars.limiting_reason_mask=0x20 limiting_reason_mask=0x20 maps to bit 5 in the RAPL perf‑limit mask, which corresponds to PKG_PL2_OOB (Package PL2 set via TPMI out‑of‑band). That means the limiter is not Fast RAPL here, it’s a PL2 power limit coming from the OOB path. Summary - This new log does not r

### Tags
BASE PNP,C2M,PAIV_PLAT_PNP,SysDebugDccbBypass,SysDebugCloned,FIX_PATCH_DMR_AP1_A0_60000994,FIX_IFWI_DMR_AP1_2026.10.4.01,FIX_BKC_OKS_DMR_AP1_2026WW12

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

- `TPMI ADV_CONTROL`
- `TPMI out`

## Timeline

- **Submitted**: 2026-02-08 10:07:14
- **Root Caused**: 2026-03-04 21:12:44
- **Days Open**: 102

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
