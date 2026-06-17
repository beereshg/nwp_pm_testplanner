# HSD 21044390244: [Bytedance][DMR AP][Beidou V5] BMC PLDM DIMM TEMP sensor data is 0 during host DC on

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [21044390244](https://hsdes.intel.com/appstore/article-one/#/21044390244) |
| **Status** | root_caused.awaiting_fix |
| **Priority** | 3-medium |
| **Owner** | yongli3 |
| **Component** | fw.ocode |
| **Defect Die** | ioe |
| **Conclusion** | fw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | SoC Thermal | 52% |
| **Sub-Feature** | DTS | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

This issue is cloned from 
https://hsdes.intel.com/appstore/article-one/#/14027556552.
 The customer reported that: 

PLDM is available after CPU boot. But only CPU DTS Temp has a reading, CPU Power, DIMM Temp, DIMM Power has a reading of 0. After waiting for a long time, there is a probability that the sensor readings are normal.

The customer would like to know whether the CPU can give a clear signal that MCTP/PLDM is available.

I also can reproduce this issue on JNC RP with:

 BMC FW: oks-20

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww20.3]

Ocode may be able to use IO_BIOS_RESET_CPL[4] (RST_CPL4) as a readiness check before returning PLDM sensor data. This bit is set by BIOS only after DRAM calibration is complete, and DRAM PBM / power meter are not expected to work before that. If Ocode can read this register over sideband, it could return the proper completion when RST_CPL4=0 instead of reporting enabled sensors with 0 readings.

[26ww20.1]

Vidar will sync with Kami offline. He is OoO today

[26ww18.3]

Email discussion is on going, Primecode team is track this one.

### Description
This issue is cloned from 
https://hsdes.intel.com/appstore/article-one/#/14027556552.
 The customer reported that: 

PLDM is available after CPU boot. But only CPU DTS Temp has a reading, CPU Power, DIMM Temp, DIMM Power has a reading of 0. After waiting for a long time, there is a probability that the sensor readings are normal.

The customer would like to know whether the CPU can give a clear signal that MCTP/PLDM is available.

I also can reproduce this issue on JNC RP with:

 BMC FW: oks-2026.15.0

BIOS: OKSDCRB1.86B.0033.D87.2603311943

Reproduce steps:

AC on or power cycle the host, during BIOS booting, check the pkg_temp_dts and dimm_temp_ch0_0 sensor values in PLDM service.

The dimm_temp_ch0_0 is 0 for a long time until almost BIOS boot completed.

The pkg_temp_dts sensor is available much faster.

On BMC, using the below command to query the two sensors during host CPU booting:

# pkg_temp_dts

while [ true ]; do date;  pldmtool platform GetSensorReading --mctp_network 2 --mctp_eid 9 --sensor_id 5 -r 0; sleep 1; done

# dimm_temp_ch0_0

while [ true ]; do date;  pldmtool platform GetSensorReading --mctp_network 2 --mctp_eid 9 --sensor_id 7 -r 0; sleep 1; done

For the DIMM temp, the sensor operation State is &quot;enabled&quot;, but the value is 0

{

    &quot;sensorDataSize&quot;: &quot;uint8&quot;,

    &quot;sensorOperationalState&quot;: &quot;Sensor Enabled&quot;,

    &quot;sensorEventMessageEnable&quot;: &quot;Sensor No Event Generation&quot;,

    &quot;presentState&quot;: &quot;Sensor Normal&quot;,

    &quot;previousState&quot;: &quot;Sensor Unknown&quot;,

    &quot;eventState&quot;: &quot;Sensor Unknown&quot;,

    &quot;presentReading&quot;: 0

}

Based on the PLDM spec, the enabled state should return a valid date

### Comments (latest)
++++22611867397 agraback
Primecode does not start populating OPC_DIMM_TEMPS until after CPL3 to avoid any conflicts with BIOS MRC

++++22611868825 daalonso 
Guys,  This is David DMR Sysdebug lead, can you please put a good summary on why this is pointing to OOBMSM , a comment below refers to an email, for the velocity of the debug better to put a summary rather than just attach emails , we receive several new sightings per day so we appreciates summaries that helps us to analyze the failure quick 


++++22611876895 vwang 
DIMM temperature reads as 0 during early boot because Primecode intentionally delays populating OPC_DIMM_TEMPS until after CPL3 to avoid interfering with BIOS MRC. Since PLDM only forwards data from OOBMSM, this behavior appears to be an expected initialization/timing limitation rather than a PLDM bug. likely due to sensor availability timing:  -  Early boot: DIMM temp data is not yet populated  -  After CPL3: Primecode begins populating DIMM temps  -  PLDM then reflects the now-valid readings
++++2162579796 kblamows
Ocode can check the IO_BIOS_RESET_CPL register and return the proper completion base on it. (in the same way we check "valid" bit) Let me check if Ocode can read it over sideband.
++++14615422003 vwang
Ocode can potentially use IO_BIOS_RESET_CPL[4] (RST_CPL4) as an additional readiness qualifier before returning PLDM sensor data. This bit is intended as a BIOS ↔ Ocode handshake and is set by BIOS only after DRAM parameter calibration is completed and the processor is ready to start the DRAM power meter with valid coefficients. Per the register definition, DRAM PBM / DRAM power meter functionality is not expected to work until this bit is set. Based on that, Ocode could check this bit in the same way it currently checks the sensor/data valid indication and return the appropriate completion when RST_CPL4=0 instead of exposing a sensor as enabled with a 0 reading. This would better align the PLDM response with actual platform readiness and avoid misleading early boot values.  @Blamowski, Kamil will update whether Ocode can read IO_BIOS_RESET_CPL over sideband.  If yes, this looks like a reasonable mechanism to gate DIMM/power-related PLDM responses until BIOS memory initialization is complete.

++++14615422158 kblamows
We will implement it as an enhancement. Here is Ocode HSD to track: https://hsdes.intel.com/appstore/article-one/#/21044421669 
++++2162585101 mspica
Updating owner to original submitter from server_platf.  @Li, Yong B please follow up with verification after the change will be ready
++++14615423193 vwang 
oCode did not have a readiness check for dimm_temp sensor reporting. It serviced the request by reading the corresponding register and, if the returned value was 0, treated it as a valid reading with present state = normal. Unlike other temperature sensors (for example dimm_temp_ts0/ts1), dimm_temp handling did not use a hardware valid bit, and oCode also did not verify whether memory calibration was c

### Tags
SysDebugDccbBypass

### Conclusion
fw.arch

### Component
fw.ocode

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
- **Component Path**: fw.ocode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-04-29 13:59:20
- **Root Caused**: 2026-05-14 20:55:08
- **Days Open**: 22

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
