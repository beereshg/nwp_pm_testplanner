# HSD 14026866307: [DMR][X1 A0 VV][Mem_Thermals] BIOS is not programming correctly the thresholds when 2x refresh is set

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026866307](https://hsdes.intel.com/appstore/article-one/#/14026866307) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | lmalagon |
| **Component** | bios |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **BIOS** | 65% |
| **Feature** | SoC Thermal | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: component='bios' → BIOS

## Root Cause Summary

BIOS is not programming correctly the thresholds when 2x refresh is set according to the specification in 

DMR CLTT Whitepaper

. 

Actual value programmed for all DIMMs: 0x645f5d53

Expected value programmed for all DIMMs: 0x64555352

Thresholds should be calculated as follow:

 

2025-12-30 20:58:41,733:INFO    :*******
***Socket0 Imh0 Mc0 SubCh0 Dimm0**
********

2025-12-30 20:58:41,733:WARNING :Current threshold = 0x645f5d53 | Default threshold = 1683313490

2025-12-30 20:58:41,733:ERROR   

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww05.4]

AR Leo to provide the information, ETA end of day

[26ww04.3]

Leo will start sync up with Aaron as understanding is different and provide status of the sync to determine next steps.

### Description
BIOS is not programming correctly the thresholds when 2x refresh is set according to the specification in 

DMR CLTT Whitepaper

. 

Actual value programmed for all DIMMs: 0x645f5d53

Expected value programmed for all DIMMs: 0x64555352

Thresholds should be calculated as follow:

 

2025-12-30 20:58:41,733:INFO    :*******
***Socket0 Imh0 Mc0 SubCh0 Dimm0**
********

2025-12-30 20:58:41,733:WARNING :Current threshold = 0x645f5d53 | Default threshold = 1683313490

2025-12-30 20:58:41,733:ERROR   :Current threshold temperatures do not matches with default temperatures

2025-12-30 20:58:41,734:INFO    :*******
***Socket0 Imh0 Mc1 SubCh0 Dimm0**
********

2025-12-30 20:58:41,734:WARNING :Current threshold = 0x645f5d53 | Default threshold = 1683313490

2025-12-30 20:58:41,734:ERROR   :Current threshold temperatures do not matches with default temperatures

2025-12-30 20:58:41,735:INFO    :*******
***Socket0 Imh0 Mc2 SubCh0 Dimm0**
********

2025-12-30 20:58:41,735:WARNING :Current threshold = 0x645f5d53 | Default threshold = 1683313490

2025-12-30 20:58:41,735:ERROR   :Current threshold temperatures do not matches with default temperatures

2025-12-30 20:58:41,735:INFO    :*******
***Socket0 Imh0 Mc3 SubCh0 Dimm0**
********

2025-12-30 20:58:41,736:WARNING :Current threshold = 0x645f5d53 | Default threshold = 1683313490

2025-12-30 20:58:41,736:ERROR   :Current threshold temperatures do not matches with default temperatures

2025-12-30 20:58:41,736:INFO    :*******
***Socket0 Imh0 Mc4 SubCh0 Dimm0**
********

2025-12-30 20:58:41,736:WARNING :Current threshold = 0x645f5d53 | Default threshold = 1683313490

2025-12-30 20:58:41,736:ERROR   :Current threshold temperatures do not matches with default temperatures

2025-12-30 20:58:41,737:INFO    :*******
***Socket0 Imh0 Mc5 SubCh0 Dimm0**
********

2025-12-30 20:58:41,737:WARNING :Current threshold = 0x645f5d53 | Default threshold = 1683313490

2025-12-30 20:58:41,737:ERROR   :Current threshold temperatures do not matches wit

### Comments (latest)
++++22611708284 aaronpen
I believe BIOS is doing the correct thing. May need to tweak the white paper to separate threshold and tsod offset programming We are programming the Temp thresholds to DIMM_TEMP_THRESH_0 and DIMM_TEMP_THRESH_1.  We are then programming the tsod offset to DIMM_TEMP_EV_OFST_0 and DIMM_TEMP_EV_OFST_1.
++++14614985251 lmalagon
Thanks  @Peng, Aaron , according with our conversation adding the DIMM_TEMP_EV_OFST to the DIMM_TSOD_TEMP_* or subtracting from DIMM_TEMP_THRESH_* should be the same result in the temp/thresh convergence, we need inputs from PM Arch CLTT White Paper owner to clarify if there is an issue in the calculated value as BIOS is doing it or we can continue with same value when 2xRefresh is not enabled.  @Mathiyalagan, Vijay Anand could you please provide your inputs here? Current value in system: 0x645f5d53 - Same as if 2xRefresh is not enabled. Calculated value accordingly with rules from CLTT white paper: 0x64555352

++++14615000003 mathiyal
Leonardo - Tables that you mentioned in the HSD summary is what i expect to be programmed.  Aaron - The issue Leonardo pointing is that 2x refresh enabled & disabled are having the same values programmed by BIOS, which should not be the case
++++22611722912 aaronpen
I think I misunderstood the offset in the white paper table. This is separate from the tsod offset. The offset based on die dram count is missing in the code. This should be promoted to central_firmware.bug. Thermal thresholds should be different with 1x vs 2x refresh. We can verify it with a test bios with the correct offsets applied. 
++++1862530473 dbassa
Actual registers provided seem to be matching second table from description for non-3ds DIMM for 2x enabled.  Field Name Field Default Actual Expected according to HSD dimm_temp_low_maxthreshold 0x55 0x53=83 0x52=81 dimm_temp_mid_maxthreshold 0x5A 0x5d=93 0x53=83 dimm_temp_high_maxthreshold 0x5F 0x5f=95 0x55=85 dimm_temp_memtrip_threshold 0x0FF 0x64=100 0x64=100 Can you provide more information about expected values? Also could you provide BIOS log from both 2x and non-2x cases? log attached to this HSD doesnt contain any bios traces.
++++14615063069 lmalagon
This is not an issue, we can reject this HSD as not a defect. Based on Damian's comment I had to take a look deeper, there was a confusion/misunderstanding on how is configured depending if the system has MRDIMMs or RDIMMs, as MRDIMMs supports CLTT with TSOD and this is the case we were validating the code was mixing HW/SW configurations, after look in the code and make some proper modifications we are able to see correct values programmed against expected.  +---------------------------------------------------------------------------------+ |                     Threshold Verification Results for TSOD                     | +-------------------------------+-------------------+--------------------+--------+ |              DIMM             | Current Threshold | Expected Threshold | Result | +-----------

### Tags
FV_PM

### Conclusion
not_a_bug

### Component
bios

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
- **Sub-Feature**: general
- **Component Path**: bios

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-01-19 21:56:14
- **Closed**: 2026-02-06 12:33:52
- **Days Open**: 17

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
