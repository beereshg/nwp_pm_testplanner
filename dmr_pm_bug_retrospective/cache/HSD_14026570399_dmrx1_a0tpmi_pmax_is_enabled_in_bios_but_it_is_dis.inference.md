# HSD 14026570399: [DMR][X1 A0][TPMI] PMAX is enabled in BIOS but it is disabled in read_pcu_misc_config

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026570399](https://hsdes.intel.com/appstore/article-one/#/14026570399) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | egomezgo |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Power/RAPL | 52% |
| **Sub-Feature** | PMAX | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Summary:

========

BIOS knob has 

PmaxDetector= 0x1

 but B2P MBX 

READ_PCU_MISC_CONFIG.PMAX_DISABLE= 0x1

Details:

========

==> System configuration: FDU3A/FDU3B/FDU3C

==> QDF: 

==> BIOS/Patch/IFWI/BKC/CI Versions: 

==> Reproducibility: Always

==> Lightswitch discoveries ...

==> Experiment results ...

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww50.3]

The team noted that the PCU miscellaneous config register's role in disabling PMAX is unclear, with Suchismita confirming that BIOS currently disables PMAX via other means and Stanley stating that legacy mailbox commands should be deprecated in favor of TPMI.

Nilanjan and Stanley agreed to take an action item to clarify the intersection of BIOS, TPMI, and B2P mailbox usage for PMAX and TXT, and to determine if the register is still in use or should be removed.

[25ww50.1]

This is a problem where register values differ from the expected setting in BIOS. Seems like BIOS is not using read_pcu_misc_config as the primary method. Suchi and Timothy working on architecture input to clarify expectations on PCU_MISc_CONFIG as HAS only covers TPMI.

### Description
Summary:

========

BIOS knob has 

PmaxDetector= 0x1

 but B2P MBX 

READ_PCU_MISC_CONFIG.PMAX_DISABLE= 0x1

Details:

========

==> System configuration: FDU3A/FDU3B/FDU3C

==> QDF: 

==> BIOS/Patch/IFWI/BKC/CI Versions: 

==> Reproducibility: Always

==> Lightswitch discoveries ...

==> Experiment results ...

### Comments (latest)
++++14614873903 egomezgo
Wating on Arch feedback to see what's the expected behavior, but we are still able to reproduce on latest IFWI.

++++14614873904 egomezgo
<p><!--StartFragment--><span style="font-size: 12.18px;">BIOS:&nbsp;&nbsp;OKSDCRB1.86B.0029.D60.2511200302&nbsp;</span><br style="font-size: 12.18px;" /><span style="font-size: 12.18px;">Attaching log:&nbsp;</span><a href="https://hsdes.intel.com/resource/14026570259" target="_blank">https://hsdes.intel.com/resource/14026570259</a><span style="font-size: 12.18px;">&nbsp;</span><br style="font-size: 12.18px;" /><br style="font-size: 12.18px;" /><span style="font-size: 12.18px;">Before and after and I dont see the MBX change:</span><br style="font-size: 12.18px;" /><img src="https://hsdes.intel.com/rest/binary/14026570254" style="font-size: 12.18px; width: 800px;" /><br style="font-size: 12.18px;" /><br style="font-size: 12.18px;" /><img src="https://hsdes.intel.com/rest/binary/14026570255" style="font-size: 12.18px; width: 800px;" /><br style="font-size: 12.18px;" /><br style="font-size: 12.18px;" /><!--EndFragment--></p>

++++14614873905 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14026211793.

++++14614877702 jsbrooks
Debug status summary: Feedback from Star (BIOS):   BIOS knob PmaxDetector has been to program TPMI PMAX_CONTROL.pmax_disable_mask since GNR, so no BIOS code is touching PCU_MISC_CONFIG.PMAX_DISABLE. Suchi and Timothy are reviewing Arch expectations of PCU_MISC_CONFIG.PMAX_DISABLE. HAS currently only covers the TPMI bit. Sighting is awaiting Arch clarification before disposition.
++++22611633019 schen6
All PMAX programming interfaces have moved to TPMI since GNR, as shown in this HAS chapter. Primecode should deprecate the PMAX_DISABLE bit in read/write_pcu_misc_config; it's optional but recommended for cleanup.
++++14614886612 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14026570399] of [component=fw.primecode] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [feature] to [server.bugeco.id=14026592034] of [component=soc.PrimeCode 2.0#] in [release=dmrhub-a0]

++++14615087847 mbfausto
[SysDebug] The FW ticket (id=14026592034) cloned from this sighting has been fixed and released in ingredient version "DMR_A0_60000990" on [SysDebug] Sighting tag appended with "FIX_PATCH_DMR_A0_60000990" [SysDebug] [SysDebug] The Sighting owner (egomezgo) may be enabled to validate the fix is working in the released collateral.

++++14615087874 mbfausto
[SysDebug Tag Script] IFWI version "DMR_AP_2026.07.4.01" has been released that contains the component release "FIX_PATCH_DMR_A0_60000990" [SysDebug Tag Script] Sighting tag appended with "FIX_IFWI_DMR_AP_2026.07.4.01"
++++22611772003 mbfausto
[SysDebug Tag Script] BKC version "OKS_DMR_AP_2026WW08" has been released that contains the component release "FIX_IFWI_DMR_AP_2026.07.4.01" [SysDebug Tag Script] Sighting tag appended with "FIX_BKC_OKS_DMR_

### Tags
SysDebugCloned,SysDebugDccbBypass,FV_PM,FIX_PATCH_DMR_AP1_A0_60000990,FIX_IFWI_DMR_AP1_2026.07.4.01,BKC#OKS_DMR_AP_X1_2026WW08,FIX_BKC_OKS_DMR_AP1_2026WW08

### Conclusion
fw.arch

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
- **Sub-Feature**: PMAX
- **Component Path**: fw.primecode

## Firmware Touchpoints

### BIOS
- `BIOS knob`

## Key Registers

- `TPMI PMAX_CONTROL`
- `TPMI bit`
- `TPMI since`

## Timeline

- **Submitted**: 2025-12-06 07:12:08
- **Root Caused**: 2025-12-11 04:40:45
- **Closed**: 2026-03-11 19:03:21
- **Days Open**: 95

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
