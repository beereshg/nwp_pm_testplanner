# HSD 14027859270: Request to update dfault DRAM RAPL tau window value to 1024ms.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027859270](https://hsdes.intel.com/appstore/article-one/#/14027859270) |
| **Status** | root_caused.pursuing_fix |
| **Priority** | 3-medium |
| **Owner** | dlwu |
| **Component** | hw.power |
| **Defect Die** | ioe |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Power/RAPL | 75% |
| **Sub-Feature** | general | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

1) DRAM RAPL loop is active on DMR after reboot.

2) DRAM RAPL tau window value is current set to &quot;0x0&quot; by default, which corresponds to 1ms. This value can be read back from:

              sv.sockets.imhs.punit.ptpcioregs.ptpcioregs.dram_plane_power_limit_cfg.

ctrl_time_win = 0x0

              sv.sockets.imhs.punit.ptpcfsms.ptpcfsms.dram_rapl_pl1_control.

time_window = 0x0

#############################################################################

In [349]:
sv.sockets.imhs.pun

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
1) DRAM RAPL loop is active on DMR after reboot.

2) DRAM RAPL tau window value is current set to &quot;0x0&quot; by default, which corresponds to 1ms. This value can be read back from:

              sv.sockets.imhs.punit.ptpcioregs.ptpcioregs.dram_plane_power_limit_cfg.

ctrl_time_win = 0x0

              sv.sockets.imhs.punit.ptpcfsms.ptpcfsms.dram_rapl_pl1_control.

time_window = 0x0

#############################################################################

In [349]:
sv.sockets.imhs.punit.ptpcioregs.ptpcioregs.dram_plane_power_limit_cfg.show

-------->
sv.sockets.imhs.punit.ptpcioregs.ptpcioregs.dram_plane_power_limit_cfg.show()

0x00000000 :
pp_pwr_lim_lock (63:63) (rw/l) -- When set, all settings in this register are
locked and are treated as Read Only.

0x00000000 :
ctrl_time_win (23:17) (rw/l) -- x = CTRL_TIME_WIN[23:22]   y = CTRL_TIME_WIN[21:17]      The timing interval window is Floating
Point number given by 1.x ...

0x00000000 :
reserved (16:16) (ro) -- Reserved

0x00000000 :
pwr_lim_ctrl_en (15:15) (rw/l) -- This bit must be set in order to limit the
power of the DRAM power plane.     
0b     DRAM power plane power
limitation ...

0x00000000 :
dram_pp_pwr_lim (14:00) (rw/l) -- This is the power limitation on the IA cores
power plane.      The unit of measurement
is defined in DRAM_POWER_INFO_UNI...

 

0x00000000 :
pp_pwr_lim_lock (63:63) (rw/l) -- When set, all settings in this register are
locked and are treated as Read Only.

0x00000000 :
ctrl_time_win (23:17) (rw/l) -- x = CTRL_TIME_WIN[23:22]   y = CTRL_TIME_WIN[21:17]      The timing interval window is Floating
Point number given by 1.x ...

0x00000000 :
reserved (16:16) (ro) -- Reserved

0x00000000 :
pwr_lim_ctrl_en (15:15) (rw/l) -- This bit must be set in order to limit the
power of the DRAM power plane.     
0b     DRAM power plane power
limitation ...

0x00000000 :
dram_pp_pwr_lim (14:00) (rw/l) -- This is the power limitation on the IA cores
power plane.      The unit of measurement
is

### Comments (latest)
++++14615423681 vwang
[CloneScript] PreSighting 14027859063 cloned to Sighting 14027859270

++++14615429686 vwang 
This HSD is to request spec update for the default DRAM RAPL tau/time window setting after reboot. The issue is that the DRAM RAPL control loop comes up with a default value of 0x0 (~1 ms), which is considered too low and inconsistent with HAS guidance. The requested fix is to change the default to 0xA (~1024 ms), identified as the minimum valid setting within the expected operating range of roughly 1 to 5 seconds. In practical terms, this update is intended to align the platform’s default DRAM power-limit behavior with architectural expectations and avoid an invalid or overly aggressive control response at boot. @Mathiyalagan, Vijay Anand will update spec for this, also we will need Primecode changes accordingly.


++++14615429796 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14027859270] of [component=hw.power] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [feature] to [server.bugeco.id=14027868007] of [component=soc.top] in [release=dmrhub-a0]

### Tags
SysDebugCloned

### Conclusion
hw.arch

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

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-05-14 22:21:46
- **Root Caused**: 2026-05-15 23:25:37
- **Days Open**: 7

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
