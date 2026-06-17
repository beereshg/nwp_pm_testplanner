# HSD 14025928757: [X1 A0 PO] PKG Power reported by power_top tool is incorrect when compared against NIDAQ measurements

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025928757](https://hsdes.intel.com/appstore/article-one/#/14025928757) |
| **Status** | rejected.cannot_reproduce |
| **Priority** | 2-high |
| **Owner** | dlwu |
| **Component** | board.platform |
| **Defect Die** | base |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Power/RAPL | 52% |
| **Sub-Feature** | VR | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

- First noticed this issue early during power on using host AN004011BMH1273 and 1532, where package power was coming in much lower than expected. We were able to verify this issue on S2T's 1512 system, where there is a NIDAQ (flexlogger) connected. Results are shown in the table below. power_top readback is much lower vs. NIDAQ and PRS MBVR Tool.

Steps to reproduce
:

Boot system to OS idle. Measure idle power using NIDAQ. Verify NIDAQ via flexlogger reading is valid using PRS MBVR tool provide

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww43.1]

Waiting VR team to try the release out on more systems before we close this sighting.

[25ww42.3]

David has tried the new VR release, and the results are good now. T

his update was tested before the official bulletin and that the VR team considered the change incremental, but field validation showed significant improvements. There is a possible gap in the VR validation process.

The team agreed to document the resolution process, run additional cycles on updated systems, and ensure proper engineering judgment before closing the issue.

Vidar and others agreed to leave the issue open until the official VR release is available and more teams can test the update.

Vidar will take responsibility for sending out a broad notification to all teams and clarified that the update should apply to all DMR systems.

[25ww41.3]

David reported that the VR team expects to release the new configuration file by the end of the week, but the exact timing is still to be determined; Vidar offered to initiate an email thread to increase the priority, as multiple issues are blocked by this release.

Steven Y and Nilanjan stressed the importance of confirming with the VR team whether they are observing the same telemetry errors on VCCIN, and suggested that the team should not wait for the update without first verifying if the VR team has already calibrated and seen similar errors.

Shreyas asked if the correct configuration file was used for the platform, and David confirmed that the 500W file was matched appropriately, ruling out file mismatch as a source of error.

[25ww41.1]

David updated on attempts to flash new VR firmware to address telemetry issues, reporting a failed attempt and ongoing coordination with the VR and PRS teams for alternative flashing methods. David described manually flashing the VRs with new files using the MPS dongle, which resulted in a VR error and required reverting to the original settings to avoid system downtime.

David is seeking to retry the

### Description
- First noticed this issue early during power on using host AN004011BMH1273 and 1532, where package power was coming in much lower than expected. We were able to verify this issue on S2T's 1512 system, where there is a NIDAQ (flexlogger) connected. Results are shown in the table below. power_top readback is much lower vs. NIDAQ and PRS MBVR Tool.

Steps to reproduce
:

Boot system to OS idle. Measure idle power using NIDAQ. Verify NIDAQ via flexlogger reading is valid using PRS MBVR tool provided by 
Esparza Godinez, Salvador. Read back package power using power_top tool.

Run povray on system after booting to OS. Measure power using NIDAQ. Verify NIDAQ via flexlogger reading is valid using PRS MBVR tool provided by Esparza Godinez, Salvador. Read back package power using power_top tool.

Config

Platform- AN004011BMH1273.amr.corp.intel.com (PO Platform (Fused)) - IO system

Platform- AN004011BMH1532.amr.corp.intel.com (PO Platform (Fused)) - PM system

Platform- AN004011BMH1512.amr.corp.intel.com (PO Platform (Fused)) - S2T system

- For power_top tool, package power is being read back using register sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_energy_status.read(). The value being read back is much lower vs. NIDAQ read.

- For NIDAQ, we are summing the total power from the 10 accessible MBVR's.

- FOR PRS MBVR tool provided by Esparza Godinez, Salvador, MBVR power is being directly read from  ipc.i2c library. The total power is from the 10 accessible MBVR's are summed together.

- PRS MBVR tool installation for DMR:

pip install pysvtools.maes

- PRS MBVR tool usage for DMR:

import
pysvtools.maes.data_capture.vrscript as measure

m =
measure.VRSCRIPT()

m.Connect(&quot;IPC&quot;)

m.setTestConfig(VRSCRIPTSettings
= {'VRs': ['ALL'], 'kpi': [['Pout']], 'plt_name': 'jnc', 'plot': False, 'dtb':
False, 'dtb_vr': None, 'dtb_config': {}})

m.start()

m.Stop()

m.SaveLogs()

### Comments (latest)
++++14614632438 vwang
[CloneScript] PreSighting 14025919322 cloned to Sighting 14025928757

++++14614638165 agraback
What is the expected value of  fuses.punit.pcode_pkg_power_adder ? Do we need a fuse recipe update? Do we want to try changing that value in the bootscript to see if it aligns the results?

++++14614650573 dlwu
We were able to apply fuse override on pkg_power_adder. We tried both 0x1 and 0xff values. The output results were completely off. Need input as to how to best set pkg_power_adder.   FUSE OVERRIDE METHOD: import toolext.bootscript.boot as b b.go(pwrgoodmethod="manual",fused_unit=True, fuse_str={"imh0":['punit.pcode_pkg_power_adder=0x1'],"imh1":['punit.pcode_pkg_power_adder=0x1']}) RESULTING VALUE VIA POWER_TOP:

++++14614651280 srotich
The HAS specs (https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_PM_Fuses/DMR_Fuse_Specification.html) for default power_adder fuse value is 0x0  Feature Fuse Name IMH Scope CBB Scope Width POR Equation PO SAFE LIRA/LAVA attribute Definition Owner Value Owner Units Format Default Description Encoding class sub_class RAPL PKG_POWER_ADDER Yes No 8 POR: m 8’h0   Timothy Manuel     0 Extra fixed package power for the SoC. This is used to capture power not coverd by VR IMONs. Used in the power meter / RAPL flow; U4.4 Feature PowerManagement

++++14614652082 vwang
From: Palit: For reference: here are rails with SVID: https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html#svid-connecti… And list of all MBVRs: https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html#dmr-imh-cbb-m…

++++14614660778 sychen
Confirmed with MFG/UPS team that the PCODE_PKG_POWER_ADDER fuse is already dynamic (owned by UPS). Once the PTP/S2T team gets more reliable measurement data on the non-SVID rails (ie. VCCVNN, VCC3P3, VCCA_HV), they will update the fused value. The expectation is that the total power on these 3 rails is not that large and will not explain the overall delta being observed between power_top and PI/NIDAQ total pkg power measurements in this sighting. I suggest the team try and breakdown the RAPL/power_top data to per-VR and do per-VR power correlation against the PI/NIDAQ measurements.

++++14614672423 pcanetel
Issue observed in socket_rapl_energy_status.energy:  on some boots it is not adding the power consumed by IMH1, we suspect that HPM (0x1a) SUB_SOCKET_ENERGY is not received by IMH0 as the variable raplVars.sub_socket_power that stores the payload from the message is 0. IMH0 power ~98.37 W IMH1 power ~46.69 W Reported socket power is 95.5 W vs 143 W calculated.  IMH0 (98.37) + IMH1 (46.69) + mcp_fixed_power (0) + pkg_power_adder (0) = 143. Notice that raplVars.sub_socket_power = 0 In [37]: sv.socket0.imh0.pcudata.raplVars.sub_socket_power.show() 0x00000000 : sub_socket_power   On another system we don't see the issue, sub_socket_power has the expected value and socket power is including the IMH1 power consumption

++++14

### Tags
Cloned_ToSiliconSighting,PTP_SoC

### Conclusion
no_root_cause.rejected

### Component
board.platform

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
- **Component Path**: board.platform

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_energy_status.read`
- `sv.socket0.imh0.pcudata.raplVars.sub_socket_power.show`

## Timeline

- **Submitted**: 2025-09-18 03:46:30
- **Closed**: 2025-10-22 08:46:49
- **Days Open**: 34

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
