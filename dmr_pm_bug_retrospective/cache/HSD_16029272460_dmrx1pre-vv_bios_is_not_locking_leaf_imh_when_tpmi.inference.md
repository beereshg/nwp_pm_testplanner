# HSD 16029272460: [DMR][X1][Pre-VV]: BIOS is not locking leaf iMH when TPMI lock bit is set from BIOS [TurboPowerLimitLock(Package RAPL Limit Lock)=0x1]

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029272460](https://hsdes.intel.com/appstore/article-one/#/16029272460) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | kumara7 |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Power/RAPL | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

In DMR, when TPMI lock bit is set from BIOS [TurboPowerLimitLock(Package RAPL Limit Lock)=0x0] --> root iMH0 is locked for TPMI RAPL registers, leaf is still unlocked (e.g SOCKET_RAPL_PL1_CONTROL - check 63rd bit)

Side effect -

Architecturally this is fine but any TPMI write to leaf iMH will trigger unecessary fast path which can also lead to fast path storm hence the purpose of locking TPMI register is defeated here (to avoid fast path storm).

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww49.1]

Abhishek described that writes to the leaf IMH partition of TPMI registers are not used by the RAPL algorithm but still go through the fast path, potentially creating unnecessary load on P

rimecode

, and asked if these writes could be blocked.

Stanley noted that there is no current requirement to lock the leaf IMH partition, referencing similar behavior in GNR where unused registers were left unlocked without reported issues, and clarified that locking should be handled by 
P
rimecode

, not BIOS.

Manojj clarified that users can write to the leaf IMH partition via Linux, prompting Stanley to acknowledge the exposure and reconsider the risk, agreeing to review the situation further.

AR: Stanley will consult with PM Arch and 
P
rimecode

 teams, with the possibility of updating the HAS and implementing register locking as a future enhancement if needed.

### Description
In DMR, when TPMI lock bit is set from BIOS [TurboPowerLimitLock(Package RAPL Limit Lock)=0x0] --> root iMH0 is locked for TPMI RAPL registers, leaf is still unlocked (e.g SOCKET_RAPL_PL1_CONTROL - check 63rd bit)

Side effect -

Architecturally this is fine but any TPMI write to leaf iMH will trigger unecessary fast path which can also lead to fast path storm hence the purpose of locking TPMI register is defeated here (to avoid fast path storm).

### Comments (latest)
++++1667137124 aamarna1
This sighting is about right implementation in primecode , Lock bits should be set on both dies of IMH ideally, There is no functional impact as only root die takes action on the PL1 limits and root die does not accept any writes to PL limits when lock bit is set. Need to take a call in sysdebug if this has to be implemented based on ROI. 

++++1667151405 kumara7
Had offline discussion with Stan and he said that "he will check with Primecode team to see if they can "Update IMH primecode to set TPMI_WRITE_DISABLE=1 on all leaf instance RAPL registers, making them read-only." as an enhancement request ".
++++22611616160 schen6
Summary: Update IMH primecode to set TPMI_WRITE_DISABLE=1 on all leaf instance RAPL registers, making them read-only.  Primecode team has agreed support this as an enhancement request.   Context: In our DMR implementation, we have multiple TPMI instances for package-scope RAPL features (Socket, DRAM, Platform). Currently, only the root IMH instance is active while the leaf instance sits unused. IMH primecode ignores software writes to PL/Tau registers on the leaf, and the RAPL_DOMAIN_HEADER register is set to all FFs to signal compliant software to skip it. Affected registers include: • Socket RAPL: PL1, PL2, PL4 • DRAM RAPL: PL1 • Platform RAPL: PL1, PL2   The Issue: Malicious code could spam writes to the leaf instance RAPL registers, generating excessive fastpath events. This won't cause DOS/PDOS, but could impact primecode handler performance for legitimate high-priority events.   Analysis: This isn't a leaf-specific problem, the same attack vector exists for root RAPL registers and any writable TPMI registers across IMHs/CBBs. SAFE has reviewed and considers this type of spam write risk acceptable. This falls under standard defensive coding practices. If we have cycles available, the fix should be straightforward and aligns with robustness best practices.     
++++14614864604 vwang
[CloneScript] Sighting [sighting_central.sighting.id=16029272460] of [component=fw.primecode] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [feature] to [server.bugeco.id=14026547471] of [component=soc.PrimeCode 2.0#] in [release=dmrhub-a0]
++++22611686983 mbfausto
[SysDebug] The FW ticket (id=14026547471) cloned from this sighting has been fixed and released in ingredient version "DMR_A0_60000987" on [SysDebug] Sighting tag appended with "FIX_PATCH_DMR_A0_60000987" [SysDebug] [SysDebug] The Sighting owner (kumara7) may be enabled to validate the fix is working in the released collateral.

++++22611687105 mbfausto
[SysDebug Tag Script] IFWI version "DMR_AP_2026.02.3.01" has been released that contains the component release "FIX_PATCH_DMR_A0_60000987" [SysDebug Tag Script] Sighting tag appended with "FIX_IFWI_DMR_AP_2026.02.3.01"

++++22611695086 mbfausto
[SysDebug Tag Script] BKC version 'OKS_DMR_AP_2026WW04' has been released that contains the component release 'FIX_IFWI_DMR_AP_2026.02.3.01' [SysDebug Tag S

### Tags
SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_60000987,BKC#OKS_DMR_AP_X1_2026WW04,FIX_IFWI_DMR_AP1_2026.02.3.01,FIX_BKC_OKS_DMR_AP1_2026WW04

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
- **Sub-Feature**: general
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI lock`
- `TPMI RAPL`
- `TPMI write`
- `TPMI register`
- `TPMI registers`
- `TPMI instances`
- `TPMI pfs_dump`

## Timeline

- **Submitted**: 2025-11-25 16:10:18
- **Root Caused**: 2025-12-03 13:43:23
- **Closed**: 2026-01-14 20:02:33
- **Days Open**: 50

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
