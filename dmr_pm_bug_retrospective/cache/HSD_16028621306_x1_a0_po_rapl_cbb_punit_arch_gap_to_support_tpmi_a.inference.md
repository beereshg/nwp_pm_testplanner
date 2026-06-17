# HSD 16028621306: [X1 A0 PO] [RAPL] CBB Punit ARCH GAP to Support TPMI access for 8/32bit

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16028621306](https://hsdes.intel.com/appstore/article-one/#/16028621306) |
| **Status** | root_caused.awaiting_fix |
| **Priority** | 2-high |
| **Owner** | kumara5 |
| **Component** | hw.punit |
| **Defect Die** | base |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 75% |
| **Feature** | Power/RAPL | 75% |
| **Sub-Feature** | general | — |

**Reasoning**: errata_status='transferred' → HW

## Root Cause Summary

The HSD is forked from 

14025816704 - [X1 A0 PO] [RAPL] PL1 and PL2 limits are low compared to the TDP

 to follow on the HW Feature/Arch Gap for CBB found on DMR A0 PO regarding Missing support for TPMI 8b/32b access. Currently CBB Punit only supports

 64b register access, however the SW TPMI access supports 64b/32b/8b.

The Current implementation with only 64bit access may cause critical data corruption issue in TPMI register access, where partial writes != 64b can inadvertently overwrite ad

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
Issue: 
[25WW38.3] 
The issue is confirmed to be an RTL bug in the CBB Punit and will require an RTL fix(B-step?).
The fix is not optional due to dependencies from customer software; it is considered fundamental for correct operation.
There was a discussion about updating the specification (HAS) to reflect the limitation, especially if the fix only supports 64/32-bit accesses (and not 8- or 16-bit). This is to ensure consistency and avoid confusion for customers and internal teams.
The team agreed that if the limitation is set (only 32- and 64-bit accesses supported), it should be documented and maintained to avoid flip-flopping between generations or steppings.
Validation and documentation will be updated accordingly.
Coordination with the CBB Punit team and further offline discussions are planned to finalize details and downstream impacts.

### Description
The HSD is forked from 

14025816704 - [X1 A0 PO] [RAPL] PL1 and PL2 limits are low compared to the TDP

 to follow on the HW Feature/Arch Gap for CBB found on DMR A0 PO regarding Missing support for TPMI 8b/32b access. Currently CBB Punit only supports

 64b register access, however the SW TPMI access supports 64b/32b/8b.

The Current implementation with only 64bit access may cause critical data corruption issue in TPMI register access, where partial writes != 64b can inadvertently overwrite adjacent data in 64-bit registers and may be fatal.

 

Do Note: for DMR A0 We have got BIOS 

enhancement done to add support for 64bit data access as DMR CBB TPMI space SB access only possible for full 64b CR Rd/Wr and this will be needed for B0 As well for Internal SB access. For the External SW access to TPMI we expect the RTL fix to be done for DMR B0, as part of this HSD.

### Comments (latest)
++++1666992048 sumanku2
13013697015 (related-link) - link(s) are added via link tab.
++++22611467343 mbfausto
Removing fix_* fields, the SOC Bugeco is still awaiting a DCCB Fix decision for A0/B0.
++++1363410750 mtoledan
DMRCBB BB decision:  Bug Title:  CBB: TPMI missing ByteEnable access control, and 32b address alignment BB Decision: DMRCBB A0 – Errata. DMRCBB B0, PMR, DMRHD – HW fix Approved (Conformal option, see below). Bug impact: Fatal, SW interface violation. Arch interface definition bug, miscommunication. Hence CBB-A0 punit HSD rejected: https://hsdes.intel.com/appstore/article-one/#/article/13013697015 and we need BIOS WA fix as at: https://hsdes.intel.com/appstore/article-one/#/14025816704 and CBB-B0 punit HSD approved HW fix: https://hsdes.intel.com/appstore/article-one/#/article/13013724014 (no need for BIOS WA)
++++14614633582 vwang
Maytal and I discussed this issue, and confirmed to replace the incorrect bug_id with the correct B-stepping bug_id.

++++14614633584 vwang
13013724014 (related-link) - link(s) are added via link tab.
++++22611561411 mbfausto 
[SysDebug] The TEMPORARY WORKAROUND BIOS ticket (id=14025847258) linked to this sighting has been fixed and released in ingredient version "OAKSTRM.0.RPB.0029.D.15" on 2025-11-03 [SysDebug] Sighting tag appended with "TEMP_WA_BIOS_OAKSTRM.0.RPB.0029.D.15" [SysDebug]

### Tags
DMR_A0_PO,FV_PM_BDC,CBB_ARCH_GAP,B0_FIX,SysDebugDccbDone,FV_PM,TEMP_WA_BIOS_OAKSTRM.0.RPB.0029.D.15,IMH1_B0_FIX, PSF=Y

### Conclusion
hw.arch

### Component
hw.punit

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
- **Component Path**: hw.punit

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI access`
- `TPMI 8b`
- `TPMI register`
- `TPMI space`
- `TPMI we`
- `TPMI missing`

## Timeline

- **Submitted**: 2025-09-16 18:12:28
- **Root Caused**: 2025-09-16 18:15:18
- **Closed**: 2025-09-16 18:15:18
- **Days Open**: 247

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
