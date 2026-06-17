# HSD 22022354136: [DMR][ES2][Tune]:CDYN_RATIO scalars to be updated to pcode for ES2

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22022354136](https://hsdes.intel.com/appstore/article-one/#/22022354136) |
| **Status** | root_caused.awaiting_fix |
| **Priority** | 3-medium |
| **Owner** | srotich |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Reset/Boot | 52% |
| **Sub-Feature** | Boot | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

These are updated pcode values that need to be updated to go with acode changes in  
https://hsdes.intel.com/appstore/article-one/#/article/14027577904

  )

here are the corresponding short window (pvp16) CDYN_RATIO scalars associated with the new pvp16 thresholds below.

These will need to be updated along with the PVP threshold changes:

 

PVC Cdyn Class

0

1

2

3

4

PVP16 thresholds

63 (0x3f)

63 (0x3f)

63 (0x3f)

101 (0x65)

101 (0x65)

Acode/Pcode PVP16 CDYN_RATIO scalars

1.000

1.0

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww18.3]

ES2 introduces updated PVP (short window / PVP16) thresholds, and new scalars are required to match those thresholds. 

The PVP16 CDYN_RATIO scalars corresponding to the new thresholds. 
These scalars are programmed in CORE_PMA_CR_CONFIG_25 through CONFIG_32, which contain an array of 16 values.

The HSD table currently lists only 5 values, raising the question of whether to update just the first five entries.

Although aCode tuning drives the need for changes, pCode programs CONFIG_25–32, not aCode.

Pending:
Should only the first five entries of the 16-entry CONFIG_25–32 array be updated to match the HSD table, or should the full array be handled?

Where exactly the tuning values should be documented (clarification requested, CCP HAS suggested)

### Description
These are updated pcode values that need to be updated to go with acode changes in  
https://hsdes.intel.com/appstore/article-one/#/article/14027577904

  )

here are the corresponding short window (pvp16) CDYN_RATIO scalars associated with the new pvp16 thresholds below.

These will need to be updated along with the PVP threshold changes:

 

PVC Cdyn Class

0

1

2

3

4

PVP16 thresholds

63 (0x3f)

63 (0x3f)

63 (0x3f)

101 (0x65)

101 (0x65)

Acode/Pcode PVP16 CDYN_RATIO scalars

1.000

1.000

1.000

1.457

1.457

 

MFG is fusing the PVP16 cdyn from CDYN0 level (the anchor), so these CDYN_RATIO scalars are relative to that.

 

These are the CDYN_RATIO CRs that need to be programmed/updated:

CORE_PMA_CR_CONFIG_25-32

CORE_PMA_CR_CDYN_RATIO_0_1

Address: 0x3068

[15:0]

CDYN_RATIO_0

Cdyn ratio for Cdyn mapping table. Used for communicating required current Cdyn from Acode to Dcode and vice versa. Those are boot time configuration and acode copy it to its DRAM as prt of its wakeup sequence

[31:16]

CDYN_RATIO_1

### Comments (latest)
++++22611852978 vwang
[CloneScript] PreSighting 14027702064 cloned to Sighting 22022354136

++++22611853015 vwang
This one pairs with aCode changes from 14027577904

++++22611863108 aodler
Hi This HSD is missing information and context. What is the spec? Is this spec change request? What is the source for CDYN_RATIO? Are these fuses? @Abitan, Nati are you familiar with this request?   Thanks, Anatoli.  

++++22611865473 mbfausto
Team, this should never have been filed as a sighting.  if this change was "needed with the acode chagnes" ... then this is all being handled incorrectly please. 1) There should have been 1 sighting pointing to the specific tunign activity, identifying the ingredients (aCode, pCode), and teh root-cause is to update the performance SPEC that documents these values. 2) THEN we would clone that spec bugeco, to be updated, and following a primecode and aCode mitigation tickets would be filed to implement the spec change. Do not just use a sighting ticket for each ingredient change without context, coordination, and link to the DEFECT (performance tuning) that should happen. Now, I'm suspecting aCode variables/values do not have a source spec. In THIS case, for the CDYN_RATIO, where is that documented and decided on in the DMR programming?  When post-silicon tunes or MFG determines a new value, where is the value documented as the POR for the program (for each program/stepping/etc. ... whatever granularity) ?

++++22611865483 mbfausto
 @Odler, Anatoli  - While we're following up with PTP ... if this register is programmed by pCode currently, what spec are you obtaining this value from?  Wouldn't we use the same spec?  (I'm assuming it is currently pCode and taking that at face value). So pCode should know what spec they take this value from, and that would help answer the question too.
++++14615384466 vwang
The discussion group has been setup to coordinate with Arch, pCode and aCode teams.

++++14615389103 vwang 
The PVP16 CDYN_RATIO scalars corresponding to the new thresholds. These scalars are programmed in CORE_PMA_CR_CONFIG_25 through CONFIG_32, which contain an array of 16 values. The HSD table currently lists only 5 values, raising the question of whether to update just the first five entries. Although aCode tuning drives the need for changes, pCode programs CONFIG_25–32, not aCode. PVP16 thresholds by CDYN class 0..4: 63, 63, 63, 101, 101 Hex: 0x3f, 0x3f, 0x3f, 0x65, 0x65 CDYN_RATIO scalars by class 0..4:  1.000, 1.000, 1.000, 1.457, 1.457


++++14615389193 vwang
[CloneScript] Sighting [sighting_central.sighting.id=22022354136] of [component=fw.pcode] in [release=pkg.dmr-a0] has been cloned to a [feature] to [heia_soc.bugeco.id=14027782627] of [component=dmrcbbbase.soc.pm.pcode] in [release=dmrcbbbase-a0]

++++14615404225 srotich
From: Chen, Steven Y Sent: Wednesday, April 29, 2026 9:12 AM To: Odler, Anatoli <anatoli.odler@intel.com>; Bustan, Yuval <yuval.bustan@intel.com>; Rotich, Simeon K <simeon.k.rotich@intel.com>; 

### Tags
pnp pm,PM,SysDebugCloned,SysDebugDccbBypass

### Conclusion
fw.arch

### Component
fw.pcode

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

- **Primary Feature**: Reset/Boot
- **Sub-Feature**: Boot
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-04-21 00:03:08
- **Root Caused**: 2026-04-30 05:54:48
- **Days Open**: 30

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
