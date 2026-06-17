# HSD 14027378730: [DMR][PM] New Solution:  Primecode does Pmax Offset computation

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027378730](https://hsdes.intel.com/appstore/article-one/#/14027378730) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | dlwu |
| **Component** | bios |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **BIOS** | 65% |
| **Feature** | Power/RAPL | 52% |
| **Sub-Feature** | PMAX | — |

**Reasoning**: component='bios' → BIOS

## Root Cause Summary

Requirement(s)
*

 :

CURRENT Solution:

BIOS reads load line value

BIOS reads TDP value

BIOS gets Pmax offset from a table:

The table is static for a given Loan Line value

Uses TDP value to retrieve the offset value.

Bios applies user input adjustment

Bios writes TPMI register with adjusted Pmax value

pCode writes Pmax HW with value provided by BIOS

New Solution:  pCode does Pmax Offset computation 

pCode compute the V_offset_RLL using the formula

Pcode writes V_offset_RLL into TPMI P

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
Requirement(s)
*

 :

CURRENT Solution:

BIOS reads load line value

BIOS reads TDP value

BIOS gets Pmax offset from a table:

The table is static for a given Loan Line value

Uses TDP value to retrieve the offset value.

Bios applies user input adjustment

Bios writes TPMI register with adjusted Pmax value

pCode writes Pmax HW with value provided by BIOS

New Solution:  pCode does Pmax Offset computation 

pCode compute the V_offset_RLL using the formula

Pcode writes V_offset_RLL into TPMI PMAX_CONTROL.PMAX_VTRIP_THRESHOLD_OFFSET

BIOS reads V_offset_RLL from TPMI register (instead of reading Lookup table)

BIOS applies user input adjustment

Bios writes TPMI register with adjusted V_offset_RLL

pCode writes Pmax HW with value provided by BIOS

### Comments (latest)
++++14615211528 vwang
[CloneScript] PreSighting 14027378428 cloned to Sighting 14027378730

++++14615211545 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14027378730] of [component=fw.primecode] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [feature] to [server.bugeco.id=14027378787] of [component=soc.PrimeCode 2.0#] in [release=dmrhub-a0]

++++14615211554 vwang
This HSD is for the feature: https://hsdes.intel.com/appstore/article-one/#/22020012509

++++14615211556 vwang
22020012509 (related-link) - link(s) are added via link tab.
++++22611805722 mbfausto
Team - this HSD was root-caused to Primecode however the root_cause_description was filled with pCode/BIOS steps. pCode compute the V_offset_RLL using the formula Pcode writes V_offset_RLL into TPMI PMAX_CONTROL.PMAX_VTRIP_THRESHOLD_OFFSET BIOS reads V_offset_RLL from TPMI register (instead of reading Lookup table) BIOS applies user input adjustment Bios writes TPMI register with adjusted V_offset_RLL pCode writes Pmax HW with value provided by BIOS 1) Is the pCode/BIOS portion already implemented and this is ONLY an update to the Primecode-specific portion  (so, a fw.arch update in the Primecode-specific algirhtm) ? OR 2) This is a PMAX SOC PM Spec update (hw.power / hw.arch) and we need Primecode, pCode, and BIOS modifications (and we need to update fields/the clone set?)
++++14615214210 agraback
The BIOS feature Vidar links below links back to an old DMR Primecode hsd whic hwas implemented 5 months ago HSD 14021914748 [GNR PUSH][DMR]GNR Pmax BIOS LoadLine Offset - Pcode Implementation Proposal Is there a bug in that implementation?

++++14615214610 vwang
 @Vu, Lan D and Jayati asked a HSD to track below GNR push changes for DMR.  HSD 14021914748 Lan is working on the HAS update for this. 

++++14615215061 vwang
@Cuevas Farfan, Eduardo  confirmed BIOS changes has already been implemented too. Design Document is here: https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/PL4/pl4.html#computation-of-the-offsets
++++22611807770 mbfausto
This sighting was filed asking 'did DMR implement that code 6 months ago' ? and root-caused also ... the answer was "yes, its already all implementeD".  no failure, no debug, no root-cause.

### Tags
val_agent,SysDebugCloned

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

- **Primary Feature**: Power/RAPL
- **Sub-Feature**: PMAX
- **Component Path**: bios

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI register`
- `TPMI PMAX_CONTROL`

## Timeline

- **Submitted**: 2026-03-13 07:03:48
- **Closed**: 2026-03-17 01:44:02
- **Days Open**: 3

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
