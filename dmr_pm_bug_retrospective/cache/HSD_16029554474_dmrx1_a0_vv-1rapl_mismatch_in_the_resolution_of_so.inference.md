# HSD 16029554474: [DMR][X1 A0 VV-1][RAPL] Mismatch in the resolution of socket and platform rapl power limits

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029554474](https://hsdes.intel.com/appstore/article-one/#/16029554474) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | kumara5 |
| **Component** | val.env.content |
| **Defect Die** | base |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Power/RAPL | 75% |
| **Sub-Feature** | Socket RAPL | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

HSD is to get Design/Arch input for Power Limit Resolution to be used for Socket RAPL (1/8 W) v/s Platform RAPL (1W)

IFWI - OKSDCRB1.E9I.0030.D43.2512191249

System - SC00901159H0001

Expectation -

The RAPL power limits are expected to be configured to the 1W resolution as discussed in 
https://hsdes.intel.com/appstore/article-one/#/16028992828
 

Observation

The socket rapl resolution is 0.125W and the platform rapl power limit resolution is 1W. Is this expected?

Also, need a clarity on the

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww03.1]

Timothy explained that the socket RAPL uses a resolution of 1/8 Watt while the platform RAPL uses 1 Watt, due to the higher dynamic range required for platform-level power consumption. 
Timothy emphasized that the specification clearly defines the resolution, and validation should verify the correct parameter is used, with no ambiguity expected.

Hector M agreed to follow up with Amit and Suman to determine if their concern is solely about the differing resolutions or if another issue exists, and to clarify the HSD title if necessary.

### Description
HSD is to get Design/Arch input for Power Limit Resolution to be used for Socket RAPL (1/8 W) v/s Platform RAPL (1W)

IFWI - OKSDCRB1.E9I.0030.D43.2512191249

System - SC00901159H0001

Expectation -

The RAPL power limits are expected to be configured to the 1W resolution as discussed in 
https://hsdes.intel.com/appstore/article-one/#/16028992828
 

Observation

The socket rapl resolution is 0.125W and the platform rapl power limit resolution is 1W. Is this expected?

Also, need a clarity on the description --> 
The actual unit value is calculated by 1 W / Power(2,PWR_UNIT). The default value of 0011b corresponds to 1/8 W.

0.125W resolution

In [93]: sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_rapl_limit_cfg.show

-------> sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_rapl_limit_cfg.show()

0x00000000 : pkg_pwr_lim_lock (63:63) (rw/l) -- When set, all settings in this register are locked and are treated as Read Only. This bit will typically set by BIOS during boot time or resume from Sx.

0x00000043 : pkg_pwr_lim_2_time (55:49) (rw/l) -- x = PKG_PWR_LIM_2_TIME[55:54] y = PKG_PWR_LIM_2_TIME[53:49] The timing interval window is Floating Point number given by 1.x * power(2,y). The unit of measurement is defined in PACKAG...

0x00000001 : pkg_clmp_lim_2 (48:48) (rw/l) -- Package Clamping limitation #2 - Allow going below P1. 0b     PBM is limited between P1 and P0. 1b     PBM can go below P1.

0x00000001 : pkg_pwr_lim_2_en (47:47) (rw/l) -- This bit enables/disables PKG_PWR_LIM_2. 0b  Package Power Limit 2 is Disabled 1b  Package Power Limit 2 is Enabled

0x00000c30 : pkg_pwr_lim_2 (46:32) (rw/l) -- This field indicates the power limitation #2. The unit of measurement is defined in PACKAGE_POWER_SKU_UNIT_MSR[PWR_UNIT].

0x0000000a : pkg_pwr_lim_1_time (23:17) (rw/l) -- x = PKG_PWR_LIM_1_TIME[23:22] y = PKG_PWR_LIM_1_TIME[21:17] The timing interval window is Floating Point number given by 1.x * power(2,y). The unit of measurement is defined in PACKAG...

0

### Comments (latest)
++++1667202104 sumanku2
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 16029538780.

++++1667202105 sumanku2
[CloneScript] Sighting 16029554474 cloned from PreSighting 16029538780
++++22611693963 tkam 
> Expectation - > The RAPL power limits are expected to be configured to the 1W resolution as discussed in https://hsdes.intel.com/appstore/article-one/#/16028992828  First, please refer to a HAS (see HAS sections below) not an HSD (16028992828) for any expected behavior, against which you would sight and file a bug: With reference to the table under https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#socket-rapl, the power unit for socket RAPL is specified by the SOCKET_RAPL_POWER_UNIT.PWR_UNIT TPMI register field.  Please read it's actual TPMI value, report it here and check if what you observed in Socket RAPL PL1/PL2 conform to this power unit. With reference to the other table under https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#platform-rapl, the power unit for platform RAPL is specified by the PLATFORM_RAPL_POWER_UNIT.PWR_UNIT TPMI register field.  Please read it's actual TPMI value, report it here and check if what you observed in Platform RAPL PPL1/PL2 conform to that other power unit. Second, the sighting HSD 16028992828 is exclusively about the power unit used for Platform RAPL, and not Socket RAPL.  (In any case, I couldn't find Socket RAPL power unit stated in 16028992828, thought this is beside my points.) > Observation > The socket rapl resolution is 0.125W and the platform rapl power limit resolution is 1W. Is this expected? > Also, need a clarity on the description --> The actual unit value is calculated by 1 W / Power(2,PWR_UNIT). The default value of 0011b corresponds to 1/8 W. The answer to first question must come definitively from reading Socket RAPL and Platform RAPL power unit registers.  Yes, the architect intentions are indeed "the socket rapl resolution is 0.125W and the platform rapl power limit resolution is 1W".

### Tags
FV_PM

### Conclusion
not_a_bug

### Component
val.env.content

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
- **Sub-Feature**: Socket RAPL
- **Component Path**: val.env.content

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI register`
- `TPMI value`
- `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_rapl_limit_cfg.show`
- `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_power_sku_unit_cfg.pwr_unit.show`
- `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.platform_rapl_limit_cfg.show`

## Timeline

- **Submitted**: 2026-01-07 11:50:43
- **Closed**: 2026-01-13 14:41:49
- **Days Open**: 6

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
