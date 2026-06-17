# HSD 14025976902: [DMR][X1 A0 PO][PMAX] Pmax status reporting not triggered using global_pmax_inject

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025976902](https://hsdes.intel.com/appstore/article-one/#/14025976902) |
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
| **Feature** | Power/RAPL | 52% |
| **Sub-Feature** | PMAX | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

System: SC00901159H0008

BIOS: OKSDCRB1_86B_2025.37.4.02_2733.D07_60000964_0.601.0_1P0_NonIPClean_Trace_DebugSigned.bin

QDF: Q9CZ

Recipe used to inject pmax event:

sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.external_trigger=0x0

sv.socket0.imh0.punit.throttle.pmax_service.punit_supervises_pmax=0x1

sv.socket0.imh0.punit.throttle.pmax_service.punit_root_supervisor=0x0

sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.pmax_disable=0x0

sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pma

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww44.1]

Patricia confirmed that the patch from Jayati resolved the logging issue in the PMax status and PMax log bit, but raised a question about the inability to clear the log bit.

Alex explained that the log bit is latched and typically only cleared by a warm reset, though there may be other methods involving a write-one-to-clear operation in another register, which would not involve primeCode.

Vidar will promote this to primeCode bugeco.

[25ww43.1]

The Primecode debug patch did help us to find this issue is timing-based, a single shot injection that then sends the assert and deassert immediately back-to-back with each other.

Seems like the Pmax deassertion fast path comes in and Primecode deasserts the throttling before the root die is able to run the periodic function to update that OPC package Thermal status. 

Patricia ran 19 times and eventually saw it.

On the root die we could call the package thermal function as part of the flow, but if this was only injected on the secondary IMH then that might still have a timing issue with that.

AR: Alex/Jayati are considering a separate message or path to update the register outside the periodic function if the single shot injection continues to cause missed updates

[25ww42.3]

Alex reported that the Pmax trigger is not consistently reflected in the status register, despite hardware responses indicating proper throttling. Alex is preparing a new debug patch with extensive logging to trace the assertion and deassertion paths.

Timothy and Nilanjan emphasized the need to validate both entry and exit responses for Pmax, noting that hardware may respond correctly while Primecode may not complete the mitigation sequence.

Primecode team is leading the debug effort, and sharing results from the new debug patch.

[25ww42.1]

Pranav has discussed with Arch and was told another way to trigger Pmax by setting global_pmax_latch_bypass=0x0 instead of global_pmax_inject=0x1, Patricia will try it out.

We need to understa

### Description
System: SC00901159H0008

BIOS: OKSDCRB1_86B_2025.37.4.02_2733.D07_60000964_0.601.0_1P0_NonIPClean_Trace_DebugSigned.bin

QDF: Q9CZ

Recipe used to inject pmax event:

sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.external_trigger=0x0

sv.socket0.imh0.punit.throttle.pmax_service.punit_supervises_pmax=0x1

sv.socket0.imh0.punit.throttle.pmax_service.punit_root_supervisor=0x0

sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.pmax_disable=0x0

sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_latch_bypass=0x1

sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject=0x1

Pmax status / event not set

sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.opc_pkg_therm_status.show()

0x000000000000 : rsvd (63:14) (rw) -- Reserved.

0x000000000000
 : pmax_log (13:13) (rw) -- Sticky log bit indicating the PMAX detector has been asserted since the last time this bit was cleared by SW.

0x000000000000
 : pmax_status (12:12) (rw) -- Status bit for the PMAX detector. An assertion means the PMAX detector circuit has asserted (up to a 1ms delay). The status bit...

0x000000000001 : power_limitation_log (11:11) (rw) -- Sticky log bit that asserts when either IA is running at P-state below the (max P-state - offset) or that Graphics is ...

0x000000000001 : power_limitation_status (10:10) (rw) -- Status log bit that notifies that either IA is running at P-state below the (max P-state - offset) or that GT is ru...

0x000000000000 : threshold2_log (09:09) (rw) -- Sticky log bit that asserts on a 0 to 1 or 1 to 0 transition of the Threshold2_Status bit.

0x000000000000 : threshold2_status (08:08) (rw) -- Indicates that the current temperature is higher than or equal to the Threshold2 defined in the IA32_PACKAGE_THERM_INTERR...

0x000000000000 : threshold1_log (07:07) (rw) -- Sticky log bit that asserts on a 0 to 1 or 1 to 0 transition of the Threshold1_Status bit.

0x000000000000 : threshold1_status (06:06) (rw) -- Indicates that the current temperature is higher than or equal to the Th

### Comments (latest)
++++14614666232 pcanetel 
Verify pmax events are reflected in punit registers: opc_pkg_therm_status and Performance Limit Reasons. - Using sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject - fail - Generating a pmax event from PMAX IP modifying DAC codes - fail   Inside PMAX ip the event counters are increasing, also FIVR team is able to see the pmax trigger signal in scope but from punit side we don't have any pmax log bit set. - Using .pcodeio_map.io_throttle_signals_override  - pass   We are able to see pmax log bit in punit.


++++14614667183 pmopkar
If we need global_pmax_inject to cause the PMAX throttling we need  sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.pmax_disable=0x1 I see that sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.pmax_disable=0x0 in the recipe mentioned in the description. This will cause PUnit to use input from PMAX IP for throttling.  I see both PMAX IP generated throttling as well as global_pmax_inject in this sighting. I believe they are mutually exclusive. If PMAX IP triggered throttling is needed then following programming model is to be used(pmax_gpio_trigger.pmax_disable=0x0) https://docs.intel.com/documents/sysip_pm/DROP_gen4/TRM/TRM/TRM.html#to-enable-hard-pmax-throttling If DFX hook based PMAX throttling is needed then following programming model is to be used(pmax_gpio_trigger.pmax_disable=0x1) https://docs.intel.com/documents/sysip_pm/DROP_gen4/TRM/TRM/TRM.html#programming-model---throttling-manual-hooks

++++14614668118 pcanetel
System: JF53NOR09BN0304 BIOS: OKSDCRB1.86B.2754.D08.2509182054  PMax event emulated by using an IO register bit to inject as if a PMax assertion did arrive from the SoC into PUnit. (https://docs.intel.com/documents/sysip_pm/DROP_gen4/TRM/TRM/TRM.html#to-enable-hard-pmax-throttling ) Configuring Punits to ignore external PMax sources:    sv.socket0.imhs.punit.throttle.pmax_gpio_trigger.external_trigger    socket0.imh0.punit.throttle.pmax_gpio_trigger.external_trigger - 0x00000000    socket0.imh1.punit.throttle.pmax_gpio_trigger.external_trigger - 0x00000000    sv.socket0.imhs.punit.throttle.pmax_service.punit_supervises_pmax    socket0.imh0.punit.throttle.pmax_service.punit_supervises_pmax - 0x00000001    socket0.imh1.punit.throttle.pmax_service.punit_supervises_pmax - 0x00000001    sv.socket0.imhs.punit.throttle.pmax_gpio_trigger.pmax_disable    socket0.imh0.punit.throttle.pmax_gpio_trigger.pmax_disable - 0x00000001    socket0.imh1.punit.throttle.pmax_gpio_trigger.pmax_disable - 0x00000001 Pmax injection    sv.socket0.imhs.pcodeio_map.io_pmax_config.global_pmax_inject=0x1 Still not able to get any pmax log    sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.opc_pkg_therm_status.show()    0x000000000000 : rsvd (63:14) (rw) -- Reserved.    0x000000000000 : pmax_log (13:13) (rw) -- Sticky log bit indicating the PMAX detector has been asserted since the la...    0x000000000000 : pmax_status (12:12) (rw) -- Status bit for the PMAX detector. An assertion means the PMAX detector .

### Tags
FV_PM,SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_6000097B,FIX_IFWI_DMR_AP1_2025.45.4.02,FIX_BKC_OKS_DMR_AP1_2025WW46, PSF=Y

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

- **Primary Feature**: Power/RAPL
- **Sub-Feature**: PMAX
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.external_trigger`
- `sv.socket0.imh0.punit.throttle.pmax_service.punit_supervises_pmax`
- `sv.socket0.imh0.punit.throttle.pmax_service.punit_root_supervisor`
- `sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.pmax_disable`
- `sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_latch_bypass`

## Timeline

- **Submitted**: 2025-09-26 10:08:46
- **Root Caused**: 2025-10-28 00:12:17
- **Closed**: 2025-12-02 02:36:58
- **Days Open**: 66

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
