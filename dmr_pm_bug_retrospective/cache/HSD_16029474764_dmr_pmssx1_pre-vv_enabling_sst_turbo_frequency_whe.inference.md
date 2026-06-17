# HSD 16029474764: [DMR_PMSS][X1] [Pre-VV] Enabling SST Turbo Frequency when modules in CLOS3/CLOS2 groups results in system hang

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029474764](https://hsdes.intel.com/appstore/article-one/#/16029474764) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | ashashi |
| **Component** | fw.acode |
| **Defect Die** | compute |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | PState Stack | 75% |
| **Sub-Feature** | Turbo | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Enabling SST-TF when all or few modules are in CLOS 3 / CLOS 2 groups results in system hang.

Below combinations are tried using ISS tool from CentOS.

SST CP Enable -> Subscribe modules to CLOS 0 -> SST TF enable -> System Stable

SST CP Enable -> Subscribe modules to CLOS 1 -> SST TF enable -> System Stable

SST CP Enable -> 

Subscribe modules to 

CLOS 2 -> SST TF enable -> System Crash

SST CP Enable -> 

Subscribe modules to
 
CLOS 3 -> SST TF enable -> System Crash

SST CP Enable using &

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww06.1]

Chen has suggestiona changes from aCode side. We may need aCode patch to verify. Also Fuse change is also needed.

[26ww05.3]

Stan recommended implementing a fix in either aCode or pCode to handle zero values gracefully and differentiate them from regular non-zero settings.

[26ww04.3]

Anjana will contact Tamir to start aCode debug about the MCA. 

﻿

[26ww3.3]

Mail already in place waiting for the answer to 

cdyn_index5 value. Next step is for sysdebug to grab attention from pcode team to get the expected data. Wait has been already couple of weeks. 

[26ww03.1]

Anjana explained that the system experiences a hard hang when turbo frequency is enabled with modules set to lower priority CLOS levels, and is awaiting input from Nathi and the pCode team regarding the validity of limit 5 for cores.

Further responses from Nathi, and Anatoli are needed to determine the correct course of action, with ongoing communication maintained via email.

### Description
Enabling SST-TF when all or few modules are in CLOS 3 / CLOS 2 groups results in system hang.

Below combinations are tried using ISS tool from CentOS.

SST CP Enable -> Subscribe modules to CLOS 0 -> SST TF enable -> System Stable

SST CP Enable -> Subscribe modules to CLOS 1 -> SST TF enable -> System Stable

SST CP Enable -> 

Subscribe modules to 

CLOS 2 -> SST TF enable -> System Crash

SST CP Enable -> 

Subscribe modules to
 
CLOS 3 -> SST TF enable -> System Crash

SST CP Enable using &quot;
intel-speed-select core-power enable
&quot;

Subscribing Modules to CLOS groups using &quot;
intel-speed-select -c 0-47 core-power assoc -c
 
X
&quot;, 
X -> 0,1,2,3 CLOS groups

SST TF Enable using &quot;
intel-speed-select turbo-freq enable
&quot;

Able to observe similar hang when above commands are tried using SST TPMI registers.

System Details

48C X1 Part , QDF: 
Q9UL

BIOS Version : OKSDCRB1.IPC.0029.D15.2511052036

Kernel Version : 6.14.0-dmr.bkc.6.14.9.1.20.x86_64

IA32_BIOS_SIGN_ID (Pcode Patch ID) : 0x8000097b00000000

### Comments (latest)
++++1667185420 ashashi 
Note: The same issue occurs when using "intel-speed-select turbo-freq enable -a" directly instead of above steps mentioned in description for failure reproduction. The issue occurs if any of the modules are in CLOS3/CLOS2.  If all modules in CLOS0/CLOS1, we do not see this issue From AXON, not able to decode CBB Pcode hang: https://axonsv.app.intel.com/apps/record-viewer?id=019afed9-2356-7971-95b6-b1a66f1b2641 

++++1667185421 ashashi
<p>Attaching the Pcode tracker log</p><p><br /></p><p>From the pcudata dump:</p><p><br /></p><p>The resolved TRL via wp4 mapping when modules are in CLOS3 and when SST TF is enabled looks proper and&nbsp; mapped to TF LP Clip frequency as per fuses</p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/22021896605" style="width: 503.688px; height: 182.183px;" data-processed="true" /><br /></p><p></p><p><br /></p><p><b>SST TF LP Clip Frequency&nbsp;</b></p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/22021891464" style="width: 50%;" data-processed="true" /></p><p><br /></p><p><b>Fuse values</b></p><p><img src="https://hsdes.intel.com/rest/binary/22021897550" style="width: 1441.03px;" /><br /></p>

++++1667185436 aamarna1
Updates from Email :  Re: Query on CBB MCA Error Code  Amarnath, Abhinand ​Markovitch, Yuval;​Eiger, Yonatan;​Abitan, Nati;​Gilmer, Justin T​ ​Kharya, Harsh;​Janakiraman, Anand;​Brooks, Joseph S;​Shashi, Anjana;​Chen, Stanley​ +Stan,  Some more data pointers :  We have 48C SKU which supports SST TF, so we are basically enabling SST TF and by default all cores are subscribed to CLOS0 (High Priority Cores) ; then we subscribe 2 cores Core 0 , 1 (any core used fails) , to Clos3 (Low Priority Cores) system hangs with a CBB error which Yuval has pointed out.  Gathered some more data points from WP4 perspective : Core 0 is apparently stuck for GVFSM but core_live_status didn't show any stuck ; TRL MASK for LP Cores mask is correctly aligned WP4_0 is for LP core and WP4_1 is for HP cores :  In [49]: sv.socket0.cbbs.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ia_dvfs_fsm_debug.show() 0x00000000 : mlc (03:03) (ro/v) -- If this bit is set, related DVFS FSM will control the DVFS adapter. 0x00000000 : d2d_ucie (02:02) (ro/v) -- If this bit is set, related DVFS FSM will control the DVFS adapter. 0x00000000 : ccf (01:01) (ro/v) -- If this bit is set, related DVFS FSM will control the DVFS adapter. 0x00000001 : ia (00:00) (ro/v) -- If this bit is set, related DVFS FSM will control the DVFS adapter. In [51]: sv.socket0.cbbs.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ia_core_dvfs_adapter_debug.show() 0x00000001 : ccp_wait_mask (31:00) (ro/v) -- CCP wait mask. In [61]: sv.socket0.cbbs.pcudata.wp_rv_ia_ccp_wp4_0.show() 0x00000000 : reserved1 (63:62) (rw) -- Reserved field 0x00000000 : limit5 (61:52) (rw) -- Resolved TRL frequency for License Bucket 5. 0x0000007e : limit4 (51:42) (rw) -- Resolved TRL frequency for License Bucket 4. 0x00000036 : limit3 (41:32) (rw) -- Re

### Tags
SysDebugDccbBypass,SysDebugCloned,FIX_PATCH_DMR_AP1_A0_60000990,FIX_IFWI_DMR_AP1_2026.07.4.01,BKC#OKS_DMR_AP_X1_2026WW08,FIX_BKC_OKS_DMR_AP1_2026WW08

### Conclusion
fw.bug

### Component
fw.acode

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: Turbo
- **Component Path**: fw.acode

## Firmware Touchpoints

### PCODE
- `Pcode Patch`

## Key Registers

- `TPMI registers`
- `sv.socket0.cbbs.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ia_dvfs_fsm_debug.show`
- `sv.socket0.cbbs.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ia_core_dvfs_adapter_debug.show`
- `sv.socket0.cbbs.pcudata.wp_rv_ia_ccp_wp4_0.show`
- `sv.socket0.cbbs.pcudata.wp_rv_ia_ccp_wp4_1.show`
- `sv.socket0.cbbs.pcudata.wp_rv_ia_ccp_wp4_mask_0.show`

## Timeline

- **Submitted**: 2025-12-18 23:16:53
- **Root Caused**: 2026-02-06 02:11:58
- **Closed**: 2026-02-19 00:39:20
- **Days Open**: 62

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
