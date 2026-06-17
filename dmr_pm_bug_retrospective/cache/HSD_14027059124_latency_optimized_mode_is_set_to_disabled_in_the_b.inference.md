# HSD 14027059124: Latency Optimized Mode is set to Disabled in the BIOS and it needs to be set to Enabled by default

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027059124](https://hsdes.intel.com/appstore/article-one/#/14027059124) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | smakine1 |
| **Component** | bios |
| **Defect Die** | compute |
| **Conclusion** | bios.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **BIOS** | 70% |
| **Feature** | Unknown | 20% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_IFWI/FIX_BIOS → BIOS

## Root Cause Summary

POR is LOM Enabled

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
POR is LOM Enabled

### Comments (latest)
++++14615087802 smakine1
LOM and OPM Since SPR, cloud customers strongly request an ‘easy button’ BIOS option for up to 20% power reduction with 5% WL performance impact. This led to introduction of the LOM (Latency Optimized Mode) and OPM (Optimized Power Mode) which BIOS can configured via the ELC policies as specified/implemented above. Following previous Xeon generations, the current DMR post-Si decision is to have LOM as DMR default mode out-of-the-box. But customers do have the opt-in BIOS option to instead select OPM with the ELC Low/Mid/High. Xeon Generation ICX SPR EMR GNR/CWF DMR Default Mode OOB UFS Perf UFS Perf UFS Perf LOM LOM Opt-In BIOS Knob na OPM w/AIM OPM w/AIM++ OPM w/ELC OPM w/ELC https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html#lom-and-opm
++++1566843178 lzeng14
Just FYI:  22021361210 - [BHS GNR-AP/SP] Changing the Out-of-box mode (OPM = Optimized Power Mode or LOM disabled) to LOM (Latency Optimized Mode) enabled as Default was used for driving the default change for GNR.
++++14615095238 vwang
We need to track this BIOS changes from SOC side, not from platform side. 

++++14615095244 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14027059124] of [component=bios] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [feature] to [central_firmware.feature.id=14027096010] of [component=bios.uncore] in [release=bios.oakstream_diamondrapids]

++++14615334432 vwang 
The team discussed changing the out-of-box mode to LOM (Latency Optimized Mode) as default for DMR, PMR, and OKS, with confirmation needed for PMR and COR. COR already has LOM as default and does not require a CCB or new feature; PMR is likely to follow DMR but confirmation from Palit, Nilanjan is pending. DMR BIOS implementation should be done ASAP.


++++14615338587 vwang
BIOS team works on the code changes.
++++22611858823 mbfausto
[SysDebug] The BIOS ticket (id=15019222202) cloned from this sighting has been fixed and released in ingredient version "OAKSTRM.0.RPB.0034.D.53" on 2026-04-21 [SysDebug] Sighting tag appended with "FIX_BIOS_OAKSTRM.0.RPB.0034.D.53" [SysDebug] [SysDebug] The Sighting owner (smakine1) may be enabled to validate the fix is working in the released collateral.

++++22611871187 mbfausto
[SysDebug Tag Script] IFWI version "DMR_AP1_2026.18.3.02" has been released that contains the component release "FIX_BIOS_OAKSTRM.0.RPB.0034.D.5" [SysDebug Tag Script] Sighting tag appended with "FIX_IFWI_DMR_AP1_2026.18.3.02"
++++14615424294 smakine1
Verified that LOM is enabled in the BIOS by default. This was verified in 34.D68 version of theIFWI but this could have been enabled in earlier IFWIs as well. And the IMH frequencies are as expected.
++++22611906095 mbfausto
[SysDebug Tag Script] BKC version "OKS_DMR_AP1_2026WW20" has been released that contains the component release "FIX_IFWI_DMR_AP1_2026.18.3.02" [SysDebug Tag Script] Sighting tag appended with "FIX_BKC_OKS_DMR_AP1_2026WW20"

### Tags
BIOS_MS_PRE_ALPHA,SysDebugCloned,SysDebugDccbBypass,FIX_BIOS_OAKSTRM.0.RPB.0034.D.53,FIX_IFWI_DMR_AP1_2026.18.3.02,BKC#OKS_DMR_AP_X1_2026WW20,FIX_BKC_OKS_DMR_AP1_2026WW20

### Conclusion
bios.bug

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

- **Primary Feature**: Unknown
- **Sub-Feature**: general
- **Component Path**: bios

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-02-13 09:05:58
- **Root Caused**: 2026-02-18 13:17:39
- **Closed**: 2026-05-15 01:09:27
- **Days Open**: 90

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
