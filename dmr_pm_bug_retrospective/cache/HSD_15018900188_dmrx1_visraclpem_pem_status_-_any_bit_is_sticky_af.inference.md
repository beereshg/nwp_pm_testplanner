# HSD 15018900188: [DMR][X1 VIS][RACL/PEM] PEM_STATUS - ANY bit is sticky after software is clearing PEM_STATUS register.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [15018900188](https://hsdes.intel.com/appstore/article-one/#/15018900188) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | salmanha |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Platform PM Interface | 52% |
| **Sub-Feature** | TPMI | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Collaterals
:

X1:

Platform: AN004022BMH2291.amr.corp.intel.com

IFWI: OKSDCRB1_86B_2025.51.5.01_0030.D63_80000985_0.697.0_1P0_NonIPClean_Trace_DebugSigned_VIS_PM_PLR_FIX.bin

Summary

:

If SW clears all bits except the ANY bit, it is Pcode’s responsibility to clear the ANY bit. 

We have observed that PEM_STATUS - ANY bit is sticky and not getting cleared until platform reset.

From HAS: 
https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/PEM_HAS.html#pem_status-gen3---dmr

I

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
Collaterals
:

X1:

Platform: AN004022BMH2291.amr.corp.intel.com

IFWI: OKSDCRB1_86B_2025.51.5.01_0030.D63_80000985_0.697.0_1P0_NonIPClean_Trace_DebugSigned_VIS_PM_PLR_FIX.bin

Summary

:

If SW clears all bits except the ANY bit, it is Pcode’s responsibility to clear the ANY bit. 

We have observed that PEM_STATUS - ANY bit is sticky and not getting cleared until platform reset.

From HAS: 
https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/PEM_HAS.html#pem_status-gen3---dmr

In [53]: sv.socket0.cbbs.base.tpmi.pem_status

Out[53]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000400001

In [54]: sv.socket0.cbbs.base.tpmi.pem_status=0

In [55]: sv.socket0.cbbs.base.tpmi.pem_status

Out[55]: socket0.cbb0.base.tpmi.pem_status - 
0x0000000000000001

In [56]: sv.socket0.cbbs.base.tpmi.pem_status

Out[56]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000000001

In [57]: sv.socket0.cbbs.base.tpmi.pem_status

Out[57]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000000001

In [58]: sv.socket0.cbbs.base.tpmi.pem_status

Out[58]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000000001

In [59]: sv.socket0.cbbs.base.tpmi.pem_status

Out[59]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000000001

In [60]: sv.socket0.cbbs.base.tpmi.pem_status

Out[60]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000000001

In [61]: sv.socket0.cbbs.base.tpmi.pem_status

Out[61]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000000001

In [62]: sv.socket0.cbbs.base.tpmi.pem_status

Out[62]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000000001

In [63]: sv.socket0.cbbs.base.tpmi.pem_status

Out[63]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000000001

In [64]: sv.socket0.cbbs.base.tpmi.pem_status

Out[64]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000000001

In [65]: sv.socket0.cbbs.base.tpmi.pem_status=0

In [66]: sv.socket0.cbbs.base.tpmi.pem_status

Out[66]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000000001

For Reference:

### Comments (latest)
++++1566781007 sumanku2
[CloneScript] Sighting 15018900188 cloned from PreSighting 16029571149

++++1566781010 sumanku2
 @Wang, Vidar : We need this to be debugged and reviewed by PCODE/Primecode team. With the latest collaterals, We are observing PEM_STATUS - ANY bit is sticky and not getting cleared until platform reset. As per the HAS this shall be SW cleared. Also, we are observing that the Any Counter is not changing so there is no specific excursion events that shall be flagged. 
++++1363552939 aodler
 @Kumar, Suman1 ,  @Wang, Vidar please look at ticket https://hsdes.intel.com/appstore/article-one/#/13014207623 We just found it by pcode validation couple of weeks ago - can you link the ticket to the sighting?
++++14614962962 vwang 
.
++++22611716427 mbfausto
[SysDebug] The FW ticket (id=13014207623) cloned from this sighting has been fixed and released in ingredient version "DMR_A0_6000098B" on [SysDebug] Sighting tag appended with "FIX_PATCH_DMR_A0_6000098B" [SysDebug] [SysDebug] The Sighting owner (salmanha) may be enabled to validate the fix is working in the released collateral.

++++22611716430 mbfausto
[SysDebug Tag Script] IFWI version "DMR_AP_2026.04.3.02" has been released that contains the component release "FIX_PATCH_DMR_A0_6000098B" [SysDebug Tag Script] Sighting tag appended with "FIX_IFWI_DMR_AP_2026.04.3.02"
++++1667243659 salmanha
Issue is Fixed with Patch:  "FIX_PATCH_DMR_A0_6000098B" Platform: AN004022BMH2291.amr.corp.intel.com IFWI: OKSDCRB1_86B_2026.04.3.02_0031.D76_8000098B_0.727.0_1P0_NonIPClean_Trace_DebugSigned_VIS Patch:  "FIX_PATCH_DMR_A0_6000098B" In [194]: sv.socket0.cbbs.base.tpmi.pem_status Out[194]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000000000 In [195]: sv.socket0.cbbs.base.tpmi.pem_status Out[195]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000000000 In [196]: sv.socket0.cbbs.base.tpmi.pem_status Out[196]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000000000 In [197]: sv.socket0.imh0.pcudata.tdc_limit=0x1 In [198]: sv.socket0.cbbs.base.tpmi.pem_status Out[198]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000400001 In [199]: sv.socket0.imh0.pcudata.tdc_limit=0x73 In [200]: sv.socket0.cbbs.base.tpmi.pem_status Out[200]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000400001 In [201]: sv.socket0.cbbs.base.tpmi.pem_status=0 In [202]: sv.socket0.cbbs.base.tpmi.pem_status Out[202]: socket0.cbb0.base.tpmi.pem_status - 0x0000000000000000
++++22611739500 mbfausto
[SysDebug Tag Script] BKC version "OKS_DMR_AP_2026WW06" has been released that contains the component release "FIX_IFWI_DMR_AP_2026.04.3.02" [SysDebug Tag Script] Sighting tag appended with "FIX_BKC_OKS_DMR_AP_2026WW06"

### Tags
FV_PM_BDC,SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_6000098B,FIX_IFWI_DMR_AP1_2026.04.3.02,BKC#OKS_DMR_AP_X1_2026WW06,FIX_BKC_OKS_DMR_AP1_2026WW06

### Conclusion
fw.bug

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

- **Primary Feature**: Platform PM Interface
- **Sub-Feature**: TPMI
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbbs.base.tpmi.pem_status`

## Timeline

- **Submitted**: 2026-01-12 19:48:57
- **Root Caused**: 2026-01-14 00:15:37
- **Closed**: 2026-01-27 22:25:04
- **Days Open**: 15

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
