# HSD 14026555051: [DMR][X1 A0][PM][PMAX]  mt0_offset is not increasing or decreasing the Pmax detection threshold

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026555051](https://hsdes.intel.com/appstore/article-one/#/14026555051) |
| **Status** | rejected.cannot_reproduce |
| **Priority** | 2-high |
| **Owner** | pcanetel |
| **Component** | hw.pmax |
| **Defect Die** | ioe |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Power/RAPL | 80% |
| **Sub-Feature** | PMAX | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

BIOS: OKSDCRB1.86B.0029.D60.2511200302

System: SC00901159H0001

QDF: Q9LX (VIS-1) - 32 cores

When trying to modify PMAX trip point using 
pmax_config1.mt0_offset 
directly
 
or through 
PL4 interface
, there is none effect on PMAX IP event detection.

# PL4 fuses

sv.socket0.imhs.fuses.showsearch('pl4')

punit.pcode_socket_pl4_power_default = 0x40e

punit.pcode_pl4_scale_factor = 0x5d

punit.pcode_non_vccin_pl4_power = 0x21

punit.pcode_socket_pl4_power_default = 0x40e

punit.pcode_pl4_scale_f

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
BIOS: OKSDCRB1.86B.0029.D60.2511200302

System: SC00901159H0001

QDF: Q9LX (VIS-1) - 32 cores

When trying to modify PMAX trip point using 
pmax_config1.mt0_offset 
directly
 
or through 
PL4 interface
, there is none effect on PMAX IP event detection.

# PL4 fuses

sv.socket0.imhs.fuses.showsearch('pl4')

punit.pcode_socket_pl4_power_default = 0x40e

punit.pcode_pl4_scale_factor = 0x5d

punit.pcode_non_vccin_pl4_power = 0x21

punit.pcode_socket_pl4_power_default = 0x40e

punit.pcode_pl4_scale_factor = 0x22

punit.pcode_non_vccin_pl4_power = 0x21

#PMAX fuses

sv.socket0.imhs.fuses.showsearch('pmax_en')

pmax_top.pmax_control_pmax_en = 0x1

pmax_top.virtual.pmax_control_pmax_en_df = 0x0

pmax_top.pmax_control_pmax_en = 0x1

pmax_top.virtual.pmax_control_pmax_en_df = 0x0

#PL4 and mt_0_offset default values

sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control.show()

0x00000000000 : lock (63:63) (rw/l) -- When set, all settings in this register are locked and are treated as Read Only until next reset.

0x00000000000 : pwr_lim_en (62:62) (rw/l) -- Enable(1) or Disable(0)

0x00000000000 : rsvd (61:18) (rw/l) -- Reserved

0x00000002070 : pwr_lim (17:00) (rw/l) -- This field indicates the PL4 power limitation. The unit of measurement is defined in POWER_UNIT[PWR_UNIT].  #1038 W

sv.socket0.imh0.pmax.pmax0.pmax_config1.show()

0x00000000 : fdd_offset (30:24) (rw) -- Offset value used to change the trip point of the PMax Fast Droop Detector. This will increase or decrease the FDD thresho...

0x00000000 : mt2_offset (22:16) (rw) -- Offset value used to change the trip point of the PMax detector level 2. This will increase or decrease the Pmax detection...

0x00000000 : mt1_offset (14:08) (rw) -- Offset value used to change the trip point of the PMax detector level 1. This will increase or decrease the Pmax detection...

0x00000000 : mt0_offset (06:00) (rw) -- Offset value used to change the trip point of the PMax detector level 0. This will increase or decrease 

### Comments (latest)
++++14614873832 pcanetel
Not able to reproduce the issue anymore. BIOS: OKSDCRB1.86B.0029.D60.2511200302 System: SC00901159H0001 QDF: Q9LX (VIS-1) - 32 cores #original DAC code sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_dac0_hvm_codes 0x86 #trying to see pmax events by modifying the DAC code sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_dac0_hvm_codes = 0x86 + 5 #PMAX counter not increasing  sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x1  sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x1  sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_dac0_hvm_codes = 0x86 + 8 sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x1 #notice that pmax counter starts counting with much bigger DAC code sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_dac0_hvm_codes = 0xc5  sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x5bbd  sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x5bbf   #modifying the vtrip by using DAC code = 0xc4 + mt_offset = 2 to see pmax events sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_dac0_hvm_codes = 0xc4  sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x5bd6  sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x5bd6 sv.socket0.imh0.pmax.pmax0.pmax_config1.mt0_offset= 2  sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x7581  sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x7e80  sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x8b3 #modifying the vtrip by using DAC code = 0xc4 + mt_offset = 0 to stop seeing pmax events sv.socket0.imh0.pmax.pmax0.pmax_config1.mt0_offset= 0  sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x12e3  sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x12e3  sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.read() 0x12e3

### Tags
FV_PM

### Conclusion
no_root_cause.rejected

### Component
hw.pmax

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
- **Component Path**: hw.pmax

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imhs.fuses.showsearch`
- `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control.show`
- `sv.socket0.imh0.pmax.pmax0.pmax_config1.show`
- `sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_dac0_hvm_codes`

## Timeline

- **Submitted**: 2025-12-04 10:29:51
- **Closed**: 2025-12-08 13:08:02
- **Days Open**: 4

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
