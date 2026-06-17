# HSD 14026554742: [DMR] Issue with reading on-die temperature by reading PMA_UC_reg_130

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026554742](https://hsdes.intel.com/appstore/article-one/#/14026554742) |
| **Status** | rejected.merged |
| **Priority** | 2-high |
| **Owner** | jamesrow |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | SoC Thermal | 75% |
| **Sub-Feature** | DTS | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

C
ollected on-die temperature from DTS by reading PMA

_UC_reg_130 after
varying temperature on an MDV platform. 

According to the 18A DTS data sheet, to obtain degrees in Celsius, we
must divide the register value by two and then subtract 64 ((Tdec/2)-64). 

Observed mostly linear trend as expected when temperature was increased. However, sometimes unexpected readings are observed, which especially occur at hot temperatures, as you can see in the pythonSV snippet below. 
 
As you can see below

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww05.1]

With primecode w8000098B (patch) and min_accurate_temp fuse), we no longer see the issue at hot or cold. James will consult with Arch to confirm the expected behavior regarding fuse changes and to ensure that providing a fuse override for testing does not risk unsupported operation. James clarified that the fuse issue were being mixed with those about PMA_UC__Reg_130, which appears resolved, and committed to separating these into distinct sightings to avoid confusion.

[26ww03.3]

Next step is to create a primecode debug patch to see how many times the update function is run, currently looks like beeing stalled. James will check with Ryan to see if the new patch did or not resolve the issue. 

[26ww03.1]

Shravani Narella drives a daily task force on this.

[26ww02.3]

Waiting of thermal head results to define next steps. Currently DFX injection works fine but need actual thermal head results to verify real world functionality

[26ww02.1]

We discussed methods for thermal injection, with Ryan confirming plans to use the thermal head for real temperature injection and the need to validate telemetry data paths, while planning further synchronization with James.

Alex explained that James used pysv-based injection with pcudata DFX overrides, which bypasses certain DTS sensor paths, while Ryan is tasked with performing real temperature injection using the thermal head to ensure all telemetry paths are validated.

Alex requested that Ryan, when using the thermal head, also plot IO telemetry DTS values to ensure that primecode receives accurate DTS data forwarded from the sensors, aiming to detect any mismatches in the data path.

Ryan and Alex agreed to sync with James to clarify recent observations, as there were discrepancies in James' comments regarding issue reproduction. Ryan also mentioned plans to update the image on the host and coordinate with Prakash, with further actions scheduled for the week.

### Description
C
ollected on-die temperature from DTS by reading PMA

_UC_reg_130 after
varying temperature on an MDV platform. 

According to the 18A DTS data sheet, to obtain degrees in Celsius, we
must divide the register value by two and then subtract 64 ((Tdec/2)-64). 

Observed mostly linear trend as expected when temperature was increased. However, sometimes unexpected readings are observed, which especially occur at hot temperatures, as you can see in the pythonSV snippet below. 
 
As you can see below, we are reading the correct temperature (~80C) using
the DTS function, but occasionally PMA_UC_reg_130 provides zero or
unexpected readings.

The plot below illustrates how the reg_130 code became stuck at 0x14a (330 dec) when booted at a high temperature and later decreased. It doesn't appear to make sense.
. I

f it is booted at a low temperature and later
      increased, reading shows anticipated trend.

### Comments (latest)
++++14614872677 snerella
Additional Details After Data Review with Prakash Multiple Boot  and Temperature Ramp Scenarios Tested: Booting at each temperature from -10°C to 90°C and from 90°C to -10°C, then reading the PMA UC register at each step. Booting at high temperature, then lowering the temperature without rebooting, and reading the PMA UC register at each interval. Booting at low temperature, then increasing the temperature, and reading the PMA UC register at each interval. Linear Trend at Normal Temperatures: From 0°C to 90°C, PMA_UC_reg_130 readings generally follow a linear trend as expected. However, unexpected readings are observed below 0°C and above 90°C. Anomalous Readings at Extreme Temperatures (Four Behaviors Observed): At -10°C, the   PMA UC register consistently reads zero and does not track the actual temperature. When booted at high temperatures (e.g., 90°C), lowering the temperature causes the register to become stuck or not refresh, remaining at a value such as 0x14a (330 decimal). At 90°C, the register occasionally reads zero instead of the expected value. The register sometimes reads zero at both hot and cold extremes.
++++22611627664 jamesrow
I do wonder if another env issue with GPSB like https://hsdes.intel.com/appstore/article-one/#/14026054882, similarly I need to presight how DFX hooks for temp injection don't work on SUT, if running experiments on host then this can be ignored. pattern we can all see right is that temp crosses TJ then the register fails to read immediately or sometime later, question is why after crossing TJ why does it fail to read? does reading zero temp only happen when at TJ? the reason it stays at 101C(TJ) is because system throttling every GV domain. at a certain level the soft throttling won't be able keep temp down from the rising temp of the thermal head, but temp doesn't go above TJ+3 or +10 for thermtrip that would shut the system down. so its not that Wonder what the poll rate is for this experiment, maybe we miss temp rising TJ+3 or +10? also, wonder if that reg caps its reading at TJ, similar to package_therm_margin or pkg_therm_status where it reads zero if no delta from TJ. would be nice to read those regs and see if they read TJ(temp is zero) to match with pma_UC_reg_30 since this only happens at thermal soft throttling, to rule out EMTTM can try to disable it if thermal_throttle unlock is set "imhInst.fuses.punit.pcode_thermal_throttle_unlock" and set zero to "imhInst.punit.ptpcfsms.ptpcfsms.firm_config.emttm_enable"
++++14614878528 snerella
WW50.1: Ryan to look into below : pattern we can all see right is that temp crosses TJ then the register fails to read immediately or sometime later, question is why after crossing TJ why does it fail to read? does reading zero temp only happen when at TJ? the reason it stays at 101C(TJ) is because system throttling every GV domain. at a certain level the soft throttling won't be able keep temp down from the rising temp of the thermal head, b

### Tags
avephy,io ev impact

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

- **Primary Feature**: SoC Thermal
- **Sub-Feature**: DTS
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imhs.pi6.pcieg6.pxps.avephys.uc.pma_uc_reg_130`
- `sv.socket0.imhs.pi6.pcieg6.pxps.avephys.uc.pma_uc_reg_9`
- `sv.socket0.imh0.fuses.punit.pcode_thermal_throttle_unlock`
- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.firm_config.emttm_enable`

## Timeline

- **Submitted**: 2025-12-04 08:27:38
- **Closed**: 2026-01-29 06:00:30
- **Days Open**: 55

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
