# HSD 16028722660: [X1 A0 PO] PEM Status Does Not Assert PROCHOT Bit During C-State Transitions and External Injection

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16028722660](https://hsdes.intel.com/appstore/article-one/#/16028722660) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | mps |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | C6 | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Expectation:

PEM status should correctly report events for both fast and slow limit reasons in all power states (C0, C1 and C6). PLR fine-level bits should also be populated accurately in both states.

Observation: (Due to issue with C6 enabled stability experiment limited to C0 and C1)

In C0 state, PEM status behaves as expected, correctly reporting both fast and slow limit events.

In C1 state, PEM status reports zero for fast limit events (unexpected), but continues to report slow limit eve

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww47.3]

Discussed how platform excursion events, such as frequency clipping, are reported by PEM when the core is in C1A and when the platform is profile assisted. Stanley pointed out that in principle, SOC platform events should be reported by Pcode and not routed through Acode, as using Acode reduces the usability of PAM. Manojj shared that creating realistic external excursion events for testing is currently not possible, unlike in SPR, and noted that the current method uses ITP PythonSV for injection. Stanley suggests verifying how these externally injected events propagate inside the SOC and which controller actually reports them. AR Manojj to follow up on tracing the event propagation and how the reporting works and confirm the flow for ITP-triggered events and their reporting path.

[25ww46.4]

Manojj raised concerns about differences in system behavior due to varying core counts between DMR and GNR, questioning whether this affects the data path and reporting.

Stanley and Nilanjan suggested that debugging should start from the pCode perspective to identify issues.

Orna agreed that the PEM feature is incorrectly implemented in pCode, with counters incrementing when status bits are zero and the logic for excursions not following the specification; the team initiated plans to coordinate a reimplementation with the pCode team.

[25ww46.3]

Manojj reported that the PEM status does not assert as expected, with counter data showing increments but PEM status remaining zero, as confirmed by Stan.

Tamir assigned the issue to Chen from the aCode team for further debugging, as the problem appears to originate from aCode not providing correct data.

[25ww45.1]

Manoj has setup a meeting with Tamir today, will have some progress.

[25ww44.3]

Tamir and Nawaf will try to capture some pCode trace for this one with some trigger points.

[25ww44.1]

Wait for Nawaf's return, with Igal and Anatoli syncing with Tamir to prepare for continued debug.

[25ww43.3]

While slow

### Description
Expectation:

PEM status should correctly report events for both fast and slow limit reasons in all power states (C0, C1 and C6). PLR fine-level bits should also be populated accurately in both states.

Observation: (Due to issue with C6 enabled stability experiment limited to C0 and C1)

In C0 state, PEM status behaves as expected, correctly reporting both fast and slow limit events.

In C1 state, PEM status reports zero for fast limit events (unexpected), but continues to report slow limit events correctly. PLR fine-level bits are populated correctly in C1.

Experiments:

Various limit triggers (PROCHOT, PMAX, RAPL, RACL) were applied with PEM enabled and configured.

For fast limit triggers (PROCHOT, PMAX), PEM status was zero in C1 but correct in C0.

For slow limit triggers (RAPL, RACL), PEM status was correct in both C0 and C1.

PLR fine-level bits were consistently populated in C1 for all cases.

PEM HAS: 
https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/PEM_HAS.html

### Comments (latest)
++++1667025200 hkharya
PFB the table with both cases when Cores at C0 & C1. Captured the Freq before & after injecting the event. Along with PLR bits. When Cores at C1, PEM not showing any clipping reason for Fast Limits events {PROCHOT, Pmax} but it tell correctly for Slow limit event {RAPL, RACL}.   Recipe: Turbo-> Enabled, PEM FET -> 0x16, PEM TW -> 0x6. Note: Issue is observed with Turbo Disabled also.   Case1: Kept all the Cores at C1 State. Events Event Type Freq Before the event Freq After the event PEM PLR_DIE_LEVEL PLR_MB_DATA Expecting below bits to be set: Actual Bits which are set Prochot Injected Fast Limit 2200Mhz 500Mhz 0x0 0x11 0x200000000000011 PEM : Bit25 PLR_DIE : Bit4 PLR_MB: Bit57, Bit4 PEM : None PLR_DIE : Bit4 PLR_MB: Bit57, Bit4 PMAX Fast Limit 2200Mhz 500Mhz 0x0 0x3 0x10000000003 PEM : Bit8 PLR_DIE : Bit1 PLR_MB: Bit40, Bit1 PEM : None PLR_DIE : Bit1 PLR_MB: Bit40, Bit1 PL1=0 Slow Limit 2200Mhz 400Mhz 0x401 0x4 0x40000000004 PEM : Bit10 PLR_DIE : Bit2 PLR_MB: Bit42,Bit2 PEM : Bit10 PLR_DIE : Bit2 PLR_MB: Bit42,Bit2   Case2: Kept all the Cores at C0 State. Events Event Type Freq Before the event Freq After the event PEM PLR_DIE_LEVEL PLR_MB_DATA Expecting below bits to be set: Actual Bits which are set Prochot Injected Fast Limit 2200Mhz 500Mhz 0x2000001 0x11 0x200000000000011 PEM : Bit25 PLR_DIE : Bit4 PLR_MB: Bit57, Bit4 PEM : Bit25 PLR_DIE : Bit4 PLR_MB: Bit57, Bit4 Pmax Fast Limit 2200Mhz 500Mhz 0x101 0x3 0x10000000003 PEM : Bit8 PLR_DIE : Bit1 PLR_MB: Bit40, Bit1 PEM : Bit8 PLR_DIE : Bit1 PLR_MB: Bit40, Bit1 PL1=0 Slow Limit 2200Mhz 400Mhz 0x401 0x4 0x40000000004 PEM : Bit10 PLR_DIE : Bit2 PLR_MB: Bit42,Bit2 PEM : Bit10 PLR_DIE : Bit2 PLR_MB: Bit42,Bit2   Cmds: PROCHOT Cmd -> sv.socket0.imh0.pcodeio_map.io_throttle_signals_override.global_prochot_hw_inject = 0x1. PMAX -> sv.socket0.imh0.pcodeio_map.io_throttle_signals_override.throttle_1_hw_disable=0x1 & sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject=0x1.   System Details: Cores : 32 P0 : 3100Mhz P1 : 1300Mhz Pn : 800Mhz PM : 400Mhz
++++14614687083 wstathis
Received a emu run dir from  @Lampe, Yossef with prochot and pcode trackers where we may be able to find some info on what is going on with PEM: /nfs/site/proj/cbb/cbb.emulation.models.1/fc_emu/fc_emu-cbb-b0-main-25ww38b/regression/soc/level0_c4m2_ave_reduced_model_zse5.list/cbb_pm_mc6_pstate_selfcheck_prochot/ptracker.beta.log.gz

++++14614692823 jjhingra
Thanks for the ptracker!  Looks like pem_status_average is always 0 in the run so we'll never set anything in pem_status -  9368:[1949487]     ,MEM_W ,[0x6000cc48],      32b,  pem_telemetry.pem_status_average[0]                                             ,                 0x0,   <-- 0.0f,   9369:[1949497]     ,MEM_W ,[0x6000cc4c],      32b,  pem_telemetry.pem_status_average[1]                                             ,                 0x0,   <-- 0.0f,   9370:[1949517]     ,MEM_W ,[0x6000cc50],      32b,  pem_telemetry.pem_status_average[2]     

### Tags
SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_6000098D,FIX_IFWI_DMR_AP1_2026.05.4.01,BKC#OKS_DMR_AP_X1_2026WW08,FIX_BKC_OKS_DMR_AP1_2026WW07, PSF=Y

### Conclusion
fw.bug

### Component
fw.pcode

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
- **Component Path**: fw.pcode

## Firmware Touchpoints

### PCODE
- `pCode patch`

## Key Registers

- `sv.socket0.imh0.pcodeio_map.io_throttle_signals_override.global_prochot_hw_inject`
- `sv.socket0.imh0.pcodeio_map.io_throttle_signals_override.throttle_1_hw_disable`
- `sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject`
- `sv.socket0.cbb0.pcode.vars.plr.showsearch`

## Timeline

- **Submitted**: 2025-09-26 18:48:46
- **Root Caused**: 2025-12-04 23:56:57
- **Closed**: 2026-02-06 23:37:22
- **Days Open**: 133

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
