# HSD 14026423291: [DMR_BMC][Pre VV][X1] BMC IPMI sensor list does not show DIMM temperatures due to invalid OPC_HEADER.MEMORY_CHANNELS reporting 0 channels

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026423291](https://hsdes.intel.com/appstore/article-one/#/14026423291) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | lmalagon |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Platform PM Interface | 75% |
| **Sub-Feature** | TPMI | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

IPMI sensor list fails to display DIMM temperature sensors because OPC_HEADER.MEMORY_CHANNELS incorrectly reports 0 channels while actual DIMM temperature data exists.

Root Cause:

OPC_HEADER register reports MEMORY_CHANNELS=0, causing BMC to skip DIMM sensor creation despite valid temperature data being present in OPC_DIMM_TEMPS_3.

root@bmc-mac984fee1ac84c:~# busctl introspect  com.intel.TPMI /com/intel/tpmi/cpu0/domain8/15

NAME                                TYPE      SIGNATURE RESULT/VALUE

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
IPMI sensor list fails to display DIMM temperature sensors because OPC_HEADER.MEMORY_CHANNELS incorrectly reports 0 channels while actual DIMM temperature data exists.

Root Cause:

OPC_HEADER register reports MEMORY_CHANNELS=0, causing BMC to skip DIMM sensor creation despite valid temperature data being present in OPC_DIMM_TEMPS_3.

root@bmc-mac984fee1ac84c:~# busctl introspect  com.intel.TPMI /com/intel/tpmi/cpu0/domain8/15

NAME                                TYPE      SIGNATURE RESULT/VALUE   FLAGS

com.intel.TPMI.Access               interface -         -              -

.Instances                          property  u         1              emits-change

.Offset                             property  u         33640448       emits-change

.Size                               property  u         88             emits-change

.ValidInstanceOffsets               property  a{uu}     1 0 33640448   emits-change

com.intel.TPMI.Control              interface -         -              -

.Enabled                            property  b         true           emits-change writable

.InBandReadAllowed                  property  b         false          emits-change writable

.InBandWriteAllowed                 property  b         false          emits-change writable

.Locked                             property  b         true           emits-change writable

.UsePCS                             property  b         false          emits-change writable

com.intel.TPMI.FeatureName          interface -         -              -

.Name                               property  s         &quot;OOB_PKG_CTLS&quot; emits-change

org.freedesktop.DBus.Introspectable interface -         -              -

.Introspect                         method    -         s              -

org.freedesktop.DBus.Peer           interface -         -              -

.GetMachineId                       method    -         s              -

.Ping                               method    -         -          

### Comments (latest)
++++14614811074 jigonzal
[CloneScript] PreSighting 16029092259 cloned to Sighting 14026423291
++++22611574966 agraback
Synced with the team on this and it looks like this particular note added to DMR TPMI HAS without informing primecode team. This can be promoted as a Feature Request (enhancement) to Primecode so we can implement this change for DMR
++++14614817644 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14026423291] of [component=fw.primecode] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [feature] to [server.bugeco.id=14026445460] of [component=soc.PrimeCode 2.0#] in [release=dmrhub-a0]
++++22611590592 agraback
Email sent to Stanley Chen to get clarity on if this field is for current number of memory channels or max number of memory channels (as AP can support 12 or 8 channels too if disabled by sku or BIOS)

++++22611592811 agraback
Stan confirmed this field is for Max Supported Memory Channels of the system. We'll make the change in primecode to populate this to 16 for DMR AP.

++++22611646005 mbfausto
[SysDebug] The FW ticket (id=14026445460) cloned from this sighting has been fixed and released in ingredient version 'DMR_A0_60000984' on [SysDebug] Sighting tag appended with 'FIX_PATCH_DMR_A0_60000984' [SysDebug] [SysDebug] The Sighting owner (vdongre) may be enabled to validate the fix is working in the released collateral.

++++22611648253 schen6
There is no "TPMI spec update" on DMR w.r.t. OPC_HEADER.memory_channels. There was a clarification question on this topic last month but it didn't result in a spec update.   OPC was added to DMR as part of the PCS transition, and the OPC_xxx register spec was finalized in Nov 2023. There have been no changes since.

++++22611649569 mbfausto
[SysDebug Tag Script] IFWI version 'DMR_AP_2025.51.5.01' has been released that contains the component release 'FIX_PATCH_DMR_A0_60000984' [SysDebug Tag Script] Sighting tag appended with 'FIX_IFWI_DMR_AP_2025.51.5.01'
++++1566730743 vdongre
IFWI Version 2025.51.3.06 BIOS Version 0030.D63 CPU Unified Patch 80000985 With updated IFWI, channel reporting is 0. peci_cmds -a 48 -i 8 RdEndpointConfigMMIO 6 1 0 0 2 1 0x201A000 -s 8    cc:0x40 0x00000000c0010001 peci_cmds -a 48 -i 8 RdEndpointConfigMMIO 6 1 0 0 2 1 0x201A050 -s 8    cc:0x40 0x0000000000000060 However, in python SV, it is showing number of channels = 0x10 (16).
++++22611665118 mbfausto
[SysDebug Tag Script] BKC version 'OKS_DMR_AP_2025WW52' has been released that contains the component release 'FIX_IFWI_DMR_AP_2025.51.5.01' [SysDebug Tag Script] Sighting tag appended with 'FIX_BKC_OKS_DMR_AP_2025WW52'

++++22611665528 mbfausto
 @Dongre, Vishal  - Can you confirm the BDF is correct for this IFWI/LTM?  Let's treat "your BDF access is not returning the register value you expect" ... you may file a NEW PRE-SIGHTING until you triage and verify your BDF access is correct. Can you confirm that with this FW, the register is now 0x10 where before it was 0x0 (so the defect is fixed)

### Tags
Priority_BMC_DMR_A0_PO,Manageability,DMR_Manageability_VV,SysDebugCloned,SysDebugDccbBypass,DMR_Manageability_BEAT,FIX_PATCH_DMR_AP1_A0_60000984,FIX_IFWI_DMR_AP1_2025.51.5.01,BKC#OKS_DMR_AP_X1_2025WW52,FIX_BKC_OKS_DMR_AP1_2025WW52, PSF=Y

### Conclusion
fw.bug

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

- **Primary Feature**: Platform PM Interface
- **Sub-Feature**: TPMI
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI HAS`
- `TPMI spec`
- `TPMI  import`
- `TPMI USING`
- `TPMI iMH`
- `TPMI specification`
- `TPMI addresses`
- `TPMI enumeration`
- `TPMI for`

## Timeline

- **Submitted**: 2025-11-13 09:30:58
- **Root Caused**: 2025-11-14 08:35:31
- **Closed**: 2026-02-10 21:27:19
- **Days Open**: 89

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
