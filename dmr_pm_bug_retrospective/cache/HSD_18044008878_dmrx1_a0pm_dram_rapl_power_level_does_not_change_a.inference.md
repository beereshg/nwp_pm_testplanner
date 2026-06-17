# HSD 18044008878: [DMR][X1 A0][PM] DRAM RAPL Power level does not change after lowering the PL1 control TPMI Power Limit

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [18044008878](https://hsdes.intel.com/appstore/article-one/#/18044008878) |
| **Status** | rejected.filed_by_mistake |
| **Priority** | 3-medium |
| **Owner** | psiebies |
| **Component** | hw.power |
| **Defect Die** | ioe |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Power/RAPL | 80% |
| **Sub-Feature** | general | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

1

Environment details

Platform

        AN004022BMH2511 : Micron128GB (2Rx4) 8Dimms : Fused Q9CZ                                       

IFWI Version

OKSDCRB1_86B_2025.39.2.01_2787.D03_60000968_0.613.0_1P0_NonIPClean_Trace_DebugSigned.bin

Previous working UP version

Unknown

OS version

SVOS

2

Test case details

Test Case Definition 

https://hsdes.intel.com/appstore/article-one/#/article/22021117987

 Steps for reproducing issue:

 1.) Boot to BIOS Menu
2.) Set DRAM RAPL Power Limit Lock

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
1

Environment details

Platform

        AN004022BMH2511 : Micron128GB (2Rx4) 8Dimms : Fused Q9CZ                                       

IFWI Version

OKSDCRB1_86B_2025.39.2.01_2787.D03_60000968_0.613.0_1P0_NonIPClean_Trace_DebugSigned.bin

Previous working UP version

Unknown

OS version

SVOS

2

Test case details

Test Case Definition 

https://hsdes.intel.com/appstore/article-one/#/article/22021117987

 Steps for reproducing issue:

 1.) Boot to BIOS Menu
2.) Set DRAM RAPL Power Limit Lock CSR to Disabled (EDKII Menu/Socket Configuration/Advanced Power Management/Memory & Thermal Configuration/DRAM RAPL Configuration/
DRAM RAPL Power Limit Lock CSR = Disabled

3.) Save BIOS knob changes

	

 and Boot to SVOS

4.)In PythonSV import the following

	
import socket

	
import time

5.) In PythonSV run the following to verify the DRAM RAPL Energy is incrementing as the system runs. The second value read should be different from and greater than the first value.

	

sv.sockets.imh0.punit.ptpcfsms.ptpcfsms.dram_rapl_energy_status.energy.read()

	
time.sleep(1)

	
sv.sockets.imh0.punit.ptpcfsms.ptpcfsms.dram_rapl_energy_status.energy.read()

6.)In PythonSV run the following to get the average pwr of the system while idle

	

seconds = 3

	

energy_unit = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.dram_rapl_power_unit.energy_unit.read()

	

energy_status_first = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.dram_rapl_energy_status.read()

	

time.sleep(seconds)

	

energy_status_second = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.dram_rapl_energy_status.read()

	

energy_first = energy_status_first & 0xffffffff

	

energy_second = energy_status_second & 0xffffffff

	

time_first = (energy_status_first >> 32) & 0xffffffff

	

time_second = (energy_status_second >> 32) & 0xffffffff

	

avg_power = ((1 / (2**energy_unit)) * (energy_second - energy_first)) / ((time_second - time_first) / 100000000)

	

print(f&quot;S0 Avg Input Power: {avg_power:3.5f} over {seconds:2.1f} seconds&quot;)

### Comments (latest)
++++1862504849 psiebies
Hi,&nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Jain, Sangeeta</span>&nbsp;please check and confirm the issue as the TCD owner.

++++1862504851 amundacx
<p>Tried and reproduced the behavior in platform 2511. Observed that the DRAM RAPL throttling is happening and Power or Energy is not getting limited by DRAM RAPL with set limits.</p><p>After analysis, concluded that there is already a bug on RACL&nbsp;<a href="https://hsdes.intel.com/appstore/article-one/#/article/16028418243" target="_blank" style="background-color: rgb(255, 255, 255); font-family: Roboto, Arial, sans-serif; font-weight: 400;">16028418243 - [X1 A0 PO] [RACL]: IMH Primecode Issue for incorrectly calculating the current spikes and causing unexpected RACL Limit to be hit (was: [X1 A0 PO] [RACL]: Primecode RACL Tuning/Enablement on Silicon)</a>&nbsp;which in turn causing this behavior in DRAM RAPL as the RACL becomes the limiter when both RACL and DRAM RAPL cross domain in action.</p><p><br /><!--EndFragment--></p>

++++1862504852 psiebies
Retest once the fix for the RACL issue is available.

++++1862504850 psiebies
<p>Please provide an update with test results from the orange candidate UP with WA from -&nbsp;<a href="https://hsdes.intel.com/appstore/article-one/#/article/14025919950" target="_blank">https://hsdes.intel.com/appstore/article-one/#/article/14025919950</a>.<br />Sync from RACL issue:<br /><!--StartFragment--></p><div _ngcontent-fqp-c383="" class="details" style="display: flex; flex-direction: row; color: rgba(0, 0, 0, 0.87); font-family: Roboto, &quot;Helvetica Neue&quot;, sans-serif; font-size: 12.18px;"><div _ngcontent-fqp-c383="" class="idsid" style="color: rgb(33, 33, 64);"><span _ngcontent-fqp-c383="" class="ng-star-inserted">Fausto, Matthew B</span></div><div _ngcontent-fqp-c383="" class="time-stamp ng-star-inserted" style="padding-left: 10px;"><span _ngcontent-fqp-c383="" class="label" style="color: rgb(170, 170, 170); font-size: 12.18px; padding: 0px; display: inline-block; flex: 0 0 auto; align-self: center;">Last updated on:&nbsp;</span><span _ngcontent-fqp-c383="" class="date-string" style="color: rgb(77, 90, 124);">Thursday, October 2, 2025</span><span _ngcontent-fqp-c383="" class="time-string" style="color: rgb(77, 90, 124); padding: 0px 5px; background: rgba(0, 0, 0, 0.03);">1:35:58 AM</span><span _ngcontent-fqp-c383="" class="ago-string" style="margin-left: 2px; color: rgb(206, 173, 156); display: inline-block;">(28 days ago)</span></div><div _ngcontent-fqp-c383="" class="id" style="padding-left: 15px;"><span _ngcontent-fqp-c383="" class="label" style="color: rgb(170, 170, 170); font-size: 12.18px; padding: 0px; display: inline-block; flex: 0 0 auto; align-self: center;">id:</span>&nbsp;&nbsp;<span _ngcontent-fqp-c383="" class="id-url-string" style="margin-right: 10px;"><a _ngcontent-fqp-c383="" target="_blank" tabindex="-1" href="https://hsdes.intel.com/appstore/article-one/#/article/22611491064">22

### Conclusion
no_root_cause.rejected

### Component
hw.power

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
- **Sub-Feature**: general
- **Component Path**: hw.power

## Firmware Touchpoints

### BIOS
- `BIOS knob`

## Key Registers

- `TPMI Power`
- `TPMI limit`
- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.dram_rapl_power_unit.energy_unit.read`
- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.dram_rapl_energy_status.read`
- `sv.socket0.imh0.memss.mcs.mcscheds_common.chnl_rapl_thrt.throttle_rapl_level`

## Timeline

- **Submitted**: 2025-12-03 13:18:37
- **Closed**: 2025-12-04 06:27:06

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
