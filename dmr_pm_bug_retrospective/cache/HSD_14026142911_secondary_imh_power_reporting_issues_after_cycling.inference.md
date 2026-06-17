# HSD 14026142911: Secondary IMH power reporting issues after cycling through workload

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026142911](https://hsdes.intel.com/appstore/article-one/#/14026142911) |
| **Status** | complete.broken |
| **Priority** | 3-medium |
| **Owner** | dlwu |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Power/RAPL | 80% |
| **Sub-Feature** | VR | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

After updating the MBVR config files dated 10/09/2025 provided by VR team, VR read back via prime code now match NIDAQ/Pacpro well. As we continue our testing. We are seeing another anomaly with the VR readback. The pkg_power readback via power_top is matching well against Pacpro during the initial idle state after reboot. It is also matching well when we measure it running BGEMM. As we continue the cycle of idling, run BGEMM, idling, run BGEMM, we see the secondary IMH power reporting to start 

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww45.1]

Upadhyay, Shreyas found potential math rollover while calculating delta and generated a patch for the test.

Vidar will contact David Lwu to test it.

[25ww44.3]

The issue is IMH1 power readings become zero after 20-30 minutes, causing incorrect total power reporting(after updating the motherboard VRs). The problem was replicated using both manual and scripted readbacks, and was observed across different power management systems.

Shreyas and David discussed ongoing experiments to isolate whether the issue lies within primeCode or the telemetry data it receives. Shreyas will try to reproduce the issue on CTE, which would allow for deeper inspection of primeCode internals, while also continuing platform-level debugging.

David indicated no further experiments are planned on his side for now, while Shreyas are continuing the investigation.

### Description
After updating the MBVR config files dated 10/09/2025 provided by VR team, VR read back via prime code now match NIDAQ/Pacpro well. As we continue our testing. We are seeing another anomaly with the VR readback. The pkg_power readback via power_top is matching well against Pacpro during the initial idle state after reboot. It is also matching well when we measure it running BGEMM. As we continue the cycle of idling, run BGEMM, idling, run BGEMM, we see the secondary IMH power reporting to start falling, to point where it is reporting 0. While secondary IMH power reporting is 0, power readback from Pacpro remains fine, and power reporting via primcode svid readback for each domain remains fine and match Pacpro.

First BGEMM run:

primecode readback using Canete Leyva, Patricia's script compared against Pacpro. Note the last table read back using command sp.get_energy_status_calc(). Notice 2nd column &quot;imh1 VR pwr&quot; more or less matches against the 6th column &quot;imh0 subsktpwr&quot;:

Second BGEMM run:

Note the last table read back using command sp.get_energy_status_calc(). Notice 2nd column &quot;imh1 VR pwr&quot; is now different vs. &quot;imh0 subsktpwr&quot;. imh0 subsktpwr has now dropped, and is causing total pkg_power reported to be ~10W lower than expected. Pacpro readback and SVID power readback per MBVR domain remains the same between runs.

Third BGEMM run:

Note the last table read back using command sp.get_energy_status_calc(). Notice 2nd column &quot;imh1 VR pwr&quot; is now VERY different vs. &quot;imh0 subsktpwr&quot;. imh0 subsktpwr has now dropped to zero, and is causing total pkg_power reported to completely not include power from imh1. Pacpro readback and SVID power readback per MBVR domain remains the same between runs (~140W or so, comparable to the last two runs).

Please refer to Patricia's comments in the referenced ticket below, where she also observed that imh1 power was not being included in the total power reporting; however, s

### Comments (latest)
++++14614755088 vwang
[CloneScript] PreSighting 14026142667 cloned to Sighting 14026142911

++++14614757428 pcanetel
Could you repeat the same experiment but now only reading directly the pcudata variable? Just want to discard that the continued use of the script is generating this behavior.  import diamondrapids.pm.pmutils.convert as c subsocketpower = c.convert.bin2float(socket.imh0.pcudata.raplVars.sub_socket_power.get_value(), 'float')

++++14614758181 dlwu
Based on Patricia's request, experiment was repeated but with only imh0_subsktpwr being logged and nothing else. Failure still occurs. Also note that all IO/PCIe cards have been removed from system so system is more inline with rest of power on systems. Raw data has also been attached to ticket.

++++14614758575 dlwu
We are seeing the same failure on another PM system sc00901168h8008 after extended period of time. Note imh0 subsktpwr is reading 0, while imh1 power summed from MBVR svid power readback via primecode is reading at 31.81W.

++++14614771679 shreyasu
Okay I have a test patch try something. Could you try to load this IFWI and retry reproducing the issue? \\amr\ec\proj\debug\DMR\User\shreyasu\subsocket_energy_test_patch\OKSDCRB1_86B_2025.43.0.01_2834.D10_60000975_0.637.0_1P0_NonIPClean_Trace_DebugSigned_socbkc_40580378_202511021509.bin PatchID: 0x40580378 Note: Please make sure to load the pcudata variables in pythonSV before running any experiments. The pcudata xml can be found in \\amr\ec\proj\debug\DMR\User\shreyasu\subsocket_energy_test_patch\rapl_subsocket_energy_rollover. Please capture the same information as below.

++++14614778373 shreyasu
David/Simeon tried the below IFWI and it was showing some inconsistencies. I've added additional changes to the following IFWI: \\amr.corp.intel.com\ec\proj\debug\DMR\User\shreyasu\rapl_subsocket_energy_rollover_v2\OKSDCRB1_86B_2025.43.0.01_2834.D10_60000975_0.637.0_1P0_NonIPClean_Trace_DebugSigned_socbkc_40580385_202511041613.bin PatchID: 40580385 Please make sure to load the Pcudata XML. It can be found here: \\amr.corp.intel.com\ec\proj\debug\DMR\User\shreyasu\rapl_subsocket_energy_rollover_v2

++++14614792528 srotich
Tested primecode patch from Shreyas : \\amr.corp.intel.com\ec\proj\debug\DMR\User\shreyasu\rapl_subsocket_energy_rollover_v2\OKSDCRB1_86B_2025.43.0.01_2834.D10_60000975_0.637.0_1P0_NonIPClean_Trace_DebugSigned_socbkc_40580385_202511041613.bin PatchID: 40580385 The run different stress levels of workloads for 4 hours and so far power look accurate and IMH1 power is still included in calculation of socket power

++++14614792607 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14026142911] of [component=fw.primecode] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [bug] to [server.bugeco.id=14026232225] of [component=soc.PrimeCode 2.0#] in [release=dmrhub-a0]
++++22611575206 mbfausto 
.

++++22611575252 mbfausto 
.
++++14614836614 dlwu
Matthew Fausto, you originally updated with new IFWI versions, which

### Tags
PTP_SoC,SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_6000097E,FIX_IFWI_DMR_AP1_2025.47.4.01,FIX_BKC_OKS_DMR_AP1_2025WW48, PSF=Y

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
- **Sub-Feature**: VR
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.pcudata.showsearch`
- `sv.socket0.imh1.pcudata.svid_inst.deltaSnapshotArrayImon_0.accumSample`

## Timeline

- **Submitted**: 2025-10-28 22:12:55
- **Root Caused**: 2025-11-07 03:08:58
- **Closed**: 2025-12-04 03:15:35
- **Days Open**: 36

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
