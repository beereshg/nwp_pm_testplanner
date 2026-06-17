# HSD 16028722646: [DMR][X1 A0 PO] MC6 residency counters inaccurate despite high core C6 residency

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16028722646](https://hsdes.intel.com/appstore/article-one/#/16028722646) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | hkharya |
| **Component** | fw.ucode.big_core |
| **Defect Die** | compute |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | MC6 | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Issue:

Getting MC6 Residency ~1% whereas C6S Residency is 99%.

Checked with the Turbostat tool as well as with a script that polls counters from MSR_0x664. Both were showing the same data.

System Collaterals:

BMC: oks-2025.25.4

PatchID: 6022095e00000000

Bios-version : OKSDCRB1.E9I.2688.D02.2509040000

Dimm_Config : 16+0

 Hynix RE32 2Rx8 8000

 

QDF: Q7YL/32Cores

Knobs

: ACPIC2Enum-'

C6S-P as ACPI C2'. MonitorMwait='0x1'

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww44.3]

Ido confirmed that Justin and the core team are handling MC6 counter debug, with plans to involve Justin directly in future meetings for more efficient troubleshooting.

[25ww44.1]

The team is discussing this offline and will update soon.

[25ww43.3]

Justin is now involved in debugging this MC6 counter issue, with clarification from the core team pending and an update to the sighting expected soon.

[25ww43.1]

Ido is following up with the core team offline.

Zobel, Shmulik is taking AR for the efforts of the pre-si side.
Harsh is collecting more data.

[25ww42.3]

Harsh, Ido, and Vidar discussed the C6 residency counter issue, its possible relation to a known hardware bug in Nova Lake, and the need for further validation with an A code patch.

Ido pointed out a known HW bug in NVL where the TSC is not been read atomically, potentially causing corruption. This issue may be related to that  HW bug patched in NVL, but need to test with the aCode patch to confirm if the same root cause applies.

AR: Ido will follow up with the core team for more information and to answer Harsh's question about why the issue does not appear in C6 residency

[25ww42.1]

Harsh described observing low MC6 residency (around 1%) while core C6 residency was high (99%), suggesting a possible issue with the MC6 counter rather than actual module wake events.

the both cores enter C6 with high residency and the counter is not counting properly or still the model is still stuck in MC0.

This is a case where MC6 residency counters appeared to be inaccurate despite high core C6 residency, discussed possible causes, and outlined next steps for further triage and involvement of core PM owners

We need to distinguish between a true module wake-up and a counter malfunction by cross-verifying with other counters and system states, and suggested involving the core team for expert analysis.

[25ww41.3]

Anjana confirmed that the signature observed in their system differs from the NovaLake iss

### Description
Issue:

Getting MC6 Residency ~1% whereas C6S Residency is 99%.

Checked with the Turbostat tool as well as with a script that polls counters from MSR_0x664. Both were showing the same data.

System Collaterals:

BMC: oks-2025.25.4

PatchID: 6022095e00000000

Bios-version : OKSDCRB1.E9I.2688.D02.2509040000

Dimm_Config : 16+0

 Hynix RE32 2Rx8 8000

 

QDF: Q7YL/32Cores

Knobs

: ACPIC2Enum-'

C6S-P as ACPI C2'. MonitorMwait='0x1'

### Comments (latest)
++++14614672331 vwang
From TB: to my opinion this is not even a sighting level, they still need to collect more data, they are not even sure they read it correctly, moreover MC6 is acode/ucode and not pcode

++++14614672522 jtgilmer
How do you know this isn't a stimulus problem? What was your baseline?
++++1667023221 hkharya
From  @Gopal, Beeresh  We conducted experiment to ensure MC6 flow kicks consistently. Both the prerequisite of core entering C6 and MLC SSA requestion hint = 0  are observed but still very low MC6 residency.     CBB HAS Reference: https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCP%20HAS/cbb_cpp_has.html#mlc-fivr-control “In case of module MC6 entry, in which MLC is flushed and there is no requirement for MLC SSA voltage, Acode might request CCP_ELECTRICAL_REQUEST.VCCMLCSSA_TARGET_HINT = 0V, but might also keep its electrical budget.”     Step Action VCCMLCSSA_TARGET_HINT MC6 Residency Observation 1 Run workload on all modules 0x128 to 0x168 0% All cores active, hint values elevated, MC6 not triggered 2 Kill the workload 0 1.8% Workload stopped, hint dropped, MC6 begins to kick in 3 Run workload on only one module ~0x128 0% Single module active, hint elevated again, MC6 suppressed 4 Pause workload using kill -STOP <pid> 0 1.8% Workload paused, hint dropped, MC6 expected to increase     In [584]: sv.socket0.cbb0.pcode.vars.workpoint_calc.soc_workpoints_wish.ia.ring_pd.ccps.ats.logical.electrical_req.vccmlcssa_target_hint Out[584]: socket0.cbb0.pcode.vars.workpoint_calc.soc_workpoints_wish.ia.ring_pd.ccps.at0.logical.electrical_req.vccmlcssa_target_hint - 0x00000112 socket0.cbb0.pcode.vars.workpoint_calc.soc_workpoints_wish.ia.ring_pd.ccps.at1.logical.electrical_req.vccmlcssa_target_hint - 0x00000000 socket0.cbb0.pcode.vars.workpoint_calc.soc_workpoints_wish.ia.ring_pd.ccps.at2.logical.electrical_req.vccmlcssa_target_hint - 0x00000000 socket0.cbb0.pcode.vars.workpoint_calc.soc_workpoints_wish.ia.ring_pd.ccps.at3.logical.electrical_req.vccmlcssa_target_hint - 0x00000000 socket0.cbb0.pcode.vars.workpoint_calc.soc_workpoints_wish.ia.ring_pd.ccps.at4.logical.electrical_req.vccmlcssa_target_hint - 0x00000000 socket0.cbb0.pcode.vars.workpoint_calc.soc_workpoints_wish.ia.ring_pd.ccps.at5.logical.electrical_req.vccmlcssa_target_hint - 0x00000000 socket0.cbb0.pcode.vars.workpoint_calc.soc_workpoints_wish.ia.ring_pd.ccps.at6.logical.electrical_req.vccmlcssa_target_hint - 0x00000000 socket0.cbb0.pcode.vars.workpoint_calc.soc_workpoints_wish.ia.ring_pd.ccps.at7.logical.electrical_req.vccmlcssa_target_hint - 0x00000000 socket0.cbb0.pcode.vars.workpoint_calc.soc_workpoints_wish.ia.ring_pd.ccps.at8.logical.electrical_req.vccmlcssa_target_hint - 0x00000000 socket0.cbb0.pcode.vars.workpoint_calc.soc_workpoints_wish.ia.ring_pd.ccps.at9.logical.electrical_req.vccmlcssa_target_hint - 0x00000000 socket0.cbb0.pcode.vars.workpoint_calc.soc_workpoints_wish.ia.ring_pd.ccps.at10.logical.electrical_req.vccmlcssa_target_hint - 0x00000

### Tags
SysDebugDccbBypass,SysDebugCloned,FIX_PATCH_DMR_AP1_A0_60000983,FIX_IFWI_DMR_AP1_2025.50.5.01,BKC#OKS_DMR_AP_X1_2025WW51,FIX_BKC_OKS_DMR_AP1_2025WW51, PSF=Y,dmr_neg

### Conclusion
fw.bug

### Component
fw.ucode.big_core

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
- **Sub-Feature**: MC6
- **Component Path**: fw.ucode.big_core

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x10`
- `MSR 0x664`
- `sv.socket0.cbb0.pcode.vars.workpoint_calc.soc_workpoints_wish.ia.ring_pd.ccps.ats.logical.electrical_req.vccmlcssa_target_hint`
- `sv.socket0.cbb0.computes.pmas.pmsb.target_wp5.vcc_mlc_sram_grant.show`
- `sv.socket0.cbb0.computes.pmas.acode.vars.acode_vars.g_s_acode_cfg_raw_db.vf_curve.CFG_SSA_MIN_VOLTAGE`
- `sv.socket0.cbb0.computes.pmas.pmsb.target_wp5.show`
- `sv.socket0.cbb0.computes.pmas.gpsb.telem_mc6_res_count`

## Timeline

- **Submitted**: 2025-09-26 18:41:27
- **Root Caused**: 2025-11-06 03:17:41
- **Closed**: 2026-02-23 21:10:03
- **Days Open**: 150

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
