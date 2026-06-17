# HSD 14027024846: [DMR A0][X4] Slowness in SVOS when enabling MonitorMWait

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027024846](https://hsdes.intel.com/appstore/article-one/#/14027024846) |
| **Status** | rejected.not_a_defect |
| **Priority** | 2-high |
| **Owner** | hmpicosm |
| **Component** | fw.acode |
| **Defect Die** | compute |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | C1 | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

Seeing SW hangs and instability in X4 VV when enabling MonitorMWait.

SW hangs occur during or after SVOS boot, usually after a couple of minutes in SVOS idle.

Kernel task scheduler detects and report task hung.

Issue can be recovered (No slowness - Task progressing) after putting cores into ProbeMode: ipc.halt();ipc,go() or by limiting to CC1 using DFX: 
s

v.sockets.cbbs.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.dfx_ctrl_unprotected.core_cstate_limit=1

Issue is reproduced ALWAYS 100%

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww07.3]

Currently suspecting known aCode bug, which was supposed to be fix on latest aCode version but it issue is still observed. UP has not been fully validated which can cause corner cases. This started to pop on X4 VV, causing all testing to run with monitorMwait disabled, this prevents CBB feedback from FV team. Rerun with monitor enabled have been already in placed but all test are failing. Next step is to disable c-states and p-states for debug with aCode team, waiting on Justin and Jason.

### Description
Seeing SW hangs and instability in X4 VV when enabling MonitorMWait.

SW hangs occur during or after SVOS boot, usually after a couple of minutes in SVOS idle.

Kernel task scheduler detects and report task hung.

Issue can be recovered (No slowness - Task progressing) after putting cores into ProbeMode: ipc.halt();ipc,go() or by limiting to CC1 using DFX: 
s

v.sockets.cbbs.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.dfx_ctrl_unprotected.core_cstate_limit=1

Issue is reproduced ALWAYS 100%

### Comments (latest)
++++14615075108 dstonecy
This also has a high recurrence on 2S, or any system that sits relatively idle for long periods of time (10s of minutes) Some processes complete, others (high memory allocation e.g. pythonsv) seem to fail consistently
++++22611756794 hmpicosm
Meeting minutes ww7.2. Attendants: @Warren, Jason  ,  @Brooks, Joseph S , @Wang, Vidar ,  @Picos Morgan, Hector M  Jason thinks this issue could be related to the known acode PStates x CStates issue 13014051741 - [DMR][A0] aCode stuck in WP calc loop when stressing but issue is reproduced with UP 0x98D (acode 179) which is expected to have the acode fix included. Jason looked into the acode traces: "I looked at the acode trace and it looks like the traces are not good. They contain lots of illegal packets. These packets should have been fixed in the latest T1 collateral a couple months ago". Next steps: Update ITH and capture acode traces again Capture state dumps on failure (script seems to be broken). Turn off PStates requests via Kernel and try to reproduce Change the governor from polling every 15us to 150us: echo 150 > /sys/devices/system/cpu/cpufreq/schedutil/rate_limit_us Reproduce issue in another X4 VIS system.

++++22611756797 hmpicosm
Issue is still reproduced after changing polling to 150us: Change the governor from polling every 15us to 150us: echo 150 > /sys/devices/system/cpu/cpufreq/schedutil/rate_limit_us
++++14615077972 hmpicosm
Shiju helped captured a new acode trace after updating ITH T1 to latest (attached). Update ITH and capture acode traces again
++++22611759034 hmpicosm
Experiment: Turn off PStates requests via Kernel and try to reproduce Issue was reproduced after disabling IA core PStates by using the next methods, running at steady freq of 1.4GHz : sv.sockets.cbbs.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.dfx_ctrl_unprotected.freeze_ia_freq=1 Setting BIOS knob ProcessorEistEnable=0

++++22611762364 hmpicosm
Seeing better system stability when enabling MonitorMWait when using the following binary:   ifwi \\DataGroveANUX2.an.intel.com\pse_SV_Exec\diamondrapids\FV\StationUpdates\Firmware\IFWI\OKSDCRB1_86B_2026.06.5.01_0032.D14_8000098E_0.742.0_1P0_NonIPClean_Trace_DebugSigned_VDC.bin The 2 debug systems that reproduce the issue in less than 5 minutes, have been stable for hours in SVOS idle and after applying several resets.  I triggered two reruns in VV X4 suite that also have passed: https://nga.laas.intel.com/#/dmr_fv/planning/testResult/91b95a25-af38-4fbf-abcd-7c947e0d69f3 https://nga.laas.intel.com/#/dmr_fv/planning/testResult/5277b60b-7935-44e1-aebe-8a12a7c95579
++++14615097989 jtgilmer
Seems something in latest UP made issue go away (0x98D vs 0x98E)? Are we good to reject this then?

### Tags
FV_PM

### Conclusion
not_a_bug

### Component
fw.acode

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
- **Sub-Feature**: C1
- **Component Path**: fw.acode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-02-10 21:38:18
- **Closed**: 2026-02-19 13:07:47
- **Days Open**: 8

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
