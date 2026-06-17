# HSD 22022016949: [DMR] [X1] [PM][ThermTrip]  Cattrip observed on DTS with CattripDisable fuse set after setting DTS to above 135C(cattrip threshold)

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22022016949](https://hsdes.intel.com/appstore/article-one/#/22022016949) |
| **Status** | rejected.cannot_reproduce |
| **Priority** | 3-medium |
| **Owner** | jamesrow |
| **Component** | hw.power |
| **Defect Die** | base |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | SoC Thermal | 52% |
| **Sub-Feature** | DTS | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

- Platform: an004022bmh2291

- Fused Part 

-IFWI: 

OKSDCRB1_86B_2025.37.3.01_2733.D06_60000964_0.599.0_1P0_NonIPClean_Trace_DebugSigned.bin

-pcode collats:

expectation: 

After overriding dts_center's cattripDisable fuse we expect a cattrip and system shutdown to not occur after we inject that DTS with a temp higher then 135C

observation:

Cattrip mca logged after dts is set to 145C even though cattrip was fuse disabled.

steps to reproduce:

override dts centers cattrip disable fuse:

b.go

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww08.4]

Testing Methodology and Challenges: James described the current approach to testing the DTS Cattrip disable fuse, which involves manipulating catch-up codes to force a Cattrip event, but noted that this method does not accurately test the fuse's intended behavior due to the signal being overridden downstream.

James emphasized that the main blocker is determining the correct values for the catch-up codes to trigger the desired behavior, and that the DTS team is needed to provide guidance on the voltage-to-temperature conversion algorithm.

James will update the HSD with the current status and side discussions to maintain visibility, and James agreed to do so while awaiting further input from the DTS team.
 

﻿[26ww06.3]

James explained that the current method of overriding the cattrip signal does not effectively test the fuse's intended behavior, as it simply disables the signal that would otherwise be blocked by the fuse.

﻿[26ww06.1]

James described the current methodology for disabling CatTrip via the DTS and the fuse, noting that overriding the signal downstream from the DTS may not work as intended, and outlined ongoing experiments to confirm the architecture and behavior.

Joseph S clarified that Elena is the current owner for this issue, and suggested involving the DTS IP owner or Nazar's team if further architectural support is needed.

James is collecting additional data and will continue to coordinate with the aCode owners and Chen to determine the correct next steps, with plans to provide an update at the next meeting.

[26ww05.4]

Need James to provide the answers to the questions Elena is asking. AR James

### Description
- Platform: an004022bmh2291

- Fused Part 

-IFWI: 

OKSDCRB1_86B_2025.37.3.01_2733.D06_60000964_0.599.0_1P0_NonIPClean_Trace_DebugSigned.bin

-pcode collats:

expectation: 

After overriding dts_center's cattripDisable fuse we expect a cattrip and system shutdown to not occur after we inject that DTS with a temp higher then 135C

observation:

Cattrip mca logged after dts is set to 145C even though cattrip was fuse disabled.

steps to reproduce:

override dts centers cattrip disable fuse:

b.go(fused_unit=True, fuse_str={&quot;imh&quot;:['dts_center.cattripdisable=0x1']})

confirm fuse overridden:

sv.socket0.imh0.fuses.showsearch(&quot;cattripdisable&quot;,&quot;p&quot;)

dts_center.cattripdisable = 0x1

inject temp in the center dts above 135C:

sv.socket0.imh0.taps.dts_center0.tapconfig.digthermovrdval=(145+64)*2

sv.socket0.imh0.taps.dts_center0.tapconfig.digthermovrden=1

Cattrip MCA logged:

server_ip_debug.punit.errors.show_mca_status(source=&quot;reg&quot;)

### Comments (latest)
++++22611713068 jamesrow
<p>same steps reproduced on FDU7:</p><p><br /></p><p>log:&nbsp;<a href="https://hsdes.intel.com/resource/22022010238" target="_blank" tabindex="-1">log</a></p><p><br /></p><p>snippet of MCA:&nbsp;</p><p><img src="https://hsdes.intel.com/rest/binary/22022010250" style="width: 1335px;" tabindex="-1" /><br /></p>
++++14614990240 elenamur
 @Rowe, James I have a couple of clarifying/baseline questions: Have you been able to reproduce this on multiple systems? Have you tried reproducing this issue with the latest IFWI? Is there a particular reason that you have been using this IFWI: OKSDCRB1_86B_2025.37.3.01_2733.D06_60000964_0.599.0_1P0_NonIPClean_Trace_DebugSigned.bin  Is this IFWI an orange, purple, or blue release?

++++14614990303 jsbrooks
The MCA listed is a Primecode MCA.  That MCA is logged purely based on the temperature telemetry data that Primecode receives.  It is not affected by modifying dts_center's cattripDisable. Fuses could be modified, but should clarify test objectives first.
++++22611729886 mbfausto
 @Rowe, James  / Team - no updates in a week here.  Please support your open sighting promptly.  Thanks!
++++14615012607 jsbrooks
The MCA_RECOVERABLE_DIE_THERMAL_TOO_HOT is categorized as UCNA, not UC.  So, no IERR should be logged.  Status_scope with error should capture that info:  status_scope.run(collectors=["namednodes"], analyzers=["error"]) Alternately, these can be run:      from pysvtools import server_ip_debug      server_ip_debug.rasip.errors.show_mca_status()      server_ip_debug.rasip.watch_windows.show(source='reg')      from pysvtools.fv_ras_tools.mca_tools.dmr_mca_tools_po import mca_tools as _mca      _mca.dump_machine_check_architecture()     import  diamondrapids.users.rbai.ras_debug  as sd    sd.show_err If want to avoid the Primecode MCA, telemetry either needs to be disabled or overridden for that DTS.  But, let's first determine if that's necessary.      sv.socket0.imh0.pcudata.thermaltopo_instance.sensor_instances_2.raw_valid      sv.socket0.imh0.pcudata.thermaltopo_instance.sensor_instances_2.raw_temperature      Instance map to DTS (IMH1): primecode/src/pcode/src/cfgdata/dmr_imh1_a0/v1_0/thermal_topology.hpp
++++22611730493 jamesrow 
Prioritizing ARs, eta WW5.5, having hard time using bootscript for fuse overrides with DfxS3mSoftrap enabled, got a WA now. reproduce with latest ifwi and confirm power shutdown, not just that mca is logged run status scope to confirm no IERR logged reproduced on x4 and x1 and multiple DTSs


++++22611732862 jamesrow
on non-VIS debug system Gmzp301002h0038 observed MCA but no power shutdown as expected:  IFWI DCRB1_86B_2026.05.1.01_0031.D94_6000098C_0.735 system doesn't shutdown as expected on DTS with cattrip disabled by fuses and temp at 145C and mca logged as expected but system also doesn't shutdown when dts with cattrip enabled and temp at 145C that also loggs a mca system finally shutdowns when the cattrip dfx hooks likely due to overriding the temp i

### Tags
FV_PM

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

- **Primary Feature**: SoC Thermal
- **Sub-Feature**: DTS
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.fuses.showsearch`
- `sv.socket0.imh0.taps.dts_center0.tapconfig.digthermovrdval`
- `sv.socket0.imh0.taps.dts_center0.tapconfig.digthermovrden`
- `sv.socket0.imh0.pcudata.thermaltopo_instance.sensor_instances_2.raw_valid`
- `sv.socket0.imh0.pcudata.thermaltopo_instance.sensor_instances_2.raw_temperature`

## Timeline

- **Submitted**: 2026-01-22 07:28:24
- **Closed**: 2026-03-02 23:22:27
- **Days Open**: 39

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
