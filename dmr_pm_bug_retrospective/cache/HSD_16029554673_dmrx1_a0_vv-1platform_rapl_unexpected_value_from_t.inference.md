# HSD 16029554673: [DMR][X1 A0 VV-1][Platform RAPL] Unexpected value from TPMI platform_rapl_pl1_control

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029554673](https://hsdes.intel.com/appstore/article-one/#/16029554673) |
| **Status** | rejected.cannot_reproduce |
| **Priority** | 3-medium |
| **Owner** | kumara5 |
| **Component** | bios |
| **Defect Die** | soc |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **BIOS** | 65% |
| **Feature** | Power/RAPL | 75% |
| **Sub-Feature** | general | — |

**Reasoning**: component='bios' → BIOS

## Root Cause Summary

-----------------  Platform RAPL TPMI inband and OOB access Check  -----------------

2025-12-22 02:18:12,158:INFO
    
:

+--------------------------------------------------+--------------------+--------------------+--------------------+------------------+

| Register                                                | Punit                                   | TPMI MMIO                      | TPMI OOB                        | Compare Result            |

+=============================+============

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww02.3]

Submitter cannot reproduce the issue after upgrading to latest IFWI. Issue was only using CLI and not through the BIOS menu. Rejecting as cannot reproduce.

### Description
-----------------  Platform RAPL TPMI inband and OOB access Check  -----------------

2025-12-22 02:18:12,158:INFO
    
:

+--------------------------------------------------+--------------------+--------------------+--------------------+------------------+

| Register                                                | Punit                                   | TPMI MMIO                      | TPMI OOB                        | Compare Result            |

+=============================+====================+====================+====================+==================+

| platform_rapl_domain_header              | 0x78f00010101                 | 0x78f00010101                  | 0x78f00010101                 | PASS                            |

+---------------------------------------------------+-----------------------------------+-----------------------------------+------------------------------------+-------------------------------+

| platform_rapl_power_unit                     | 0xa000                              | 0xa000                               | 0xa000                               | PASS                            |

+---------------------------------------------------+-----------------------------------+-----------------------------------+------------------------------------+-------------------------------+

| platform_rapl_pl1_control                     | 0xc000000000001f40        | 0xc000000000001f40       | 0x4000000000001f40         | FAIL                            |

+---------------------------------------------------+-----------------------------------+-----------------------------------+------------------------------------+-------------------------------+

| platform_rapl_pl2_control                     | 0xc000000000003e80       | 0xc000000000003e80      | 0xc000000000003e80        | PASS                            |

+---------------------------------------------------+-----------------------------------+-----------------------------------+---

### Comments (latest)
++++1667202134 kumara5
<p>The value which is a mismatch in the VV system is a lock bit, since there was no bios knob added at the time of run the expected value of 63rd bit should be set(1). tpmi oob is showing this bit as 0 which is a problem.</p><p><br /></p><p>Checked on the debug system(an004022bmh2291.amr.corp.intel.com), still seeing the known tpmi issues.&nbsp;</p><p><br /></p><p>-----------------&nbsp; Platform RAPL TPMI inband and OOB access Check&nbsp; -----------------</p><p><br /></p><p><br /></p><p><span style="font-family: &quot;Courier New&quot;;">+-----------------------------+--------------------+-------------+------------+------------------+</span></p><p><span style="font-family: &quot;Courier New&quot;;">| Register&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; | Punit&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; | TPMI MMIO&nbsp; &nbsp;| TPMI OOB&nbsp; &nbsp;| Compare Result&nbsp; &nbsp;|</span></p><p><span style="font-family: &quot;Courier New&quot;;">+=============================+====================+=============+============+==================+</span></p><p><span style="font-family: &quot;Courier New&quot;;">| platform_rapl_domain_header | 0x78f00010101&nbsp; &nbsp; &nbsp; | 0x0&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;| -0x1&nbsp; &nbsp; &nbsp; &nbsp;| FAIL&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;|</span></p><p><span style="font-family: &quot;Courier New&quot;;">+-----------------------------+--------------------+-------------+------------+------------------+</span></p><p><span style="font-family: &quot;Courier New&quot;;">| platform_rapl_power_unit&nbsp; &nbsp; | 0xa000&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;| 0x0&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;| -0x1&nbsp; &nbsp; &nbsp; &nbsp;| FAIL&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;|</span></p><p><span style="font-family: &quot;Courier New&quot;;">+-----------------------------+--------------------+-------------+------------+------------------+</span></p><p><span style="font-family: &quot;Courier New&quot;;">| platform_rapl_pl1_control&nbsp; &nbsp;| 0x4000000000000fa0 | 0x0&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;| -0x1&nbsp; &nbsp; &nbsp; &nbsp;| FAIL&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;|</span></p><p><span style="font-family: &quot;Courier New&quot;;">+-----------------------------+--------------------+-------------+------------+------------------+</span></p><p><span style="font-family: &quot;Courier New&quot;;">| platform_rapl_pl2_control&nbsp; &nbsp;| 0x4000000000001f40 | 0x0&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;| -0x1&nbsp; &nbsp; &nbsp; &nbsp;| FAIL&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;|</span></p><p><span style="font-family: &quot;Courier New&quot;;">+-----------------------------+--------------------+-------------+------------+------------------+</span></p><p><span style="font-family: &quot;Courier New&quot;;">| platform_rapl_energy_status | 0x9b447f680001721d | 0x0&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;| -0x1&nbsp; &nbsp; &n

### Conclusion
no_root_cause.rejected

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

- **Primary Feature**: Power/RAPL
- **Sub-Feature**: general
- **Component Path**: bios

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI platform_rapl_pl1_control`
- `TPMI inband`
- `TPMI MMIO`
- `TPMI OOB`
- `TPMI method`
- `TPMI OSX`
- `TPMI STRUCTURE`
- `TPMI Watcher`
- `TPMI WA`
- `TPMI FEATURE`

## Timeline

- **Submitted**: 2026-01-07 11:56:17
- **Closed**: 2026-01-08 03:27:46

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
