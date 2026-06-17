# HSD 22022456572: Refresh, CA, ECC harassers fail hit IMH Punit MCA_RECOVERABLE_DIE_THERMAL_TOO_HOT - CBB DTS

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22022456572](https://hsdes.intel.com/appstore/article-one/#/22022456572) |
| **Status** | root_caused.pursuing_fix |
| **Priority** | 2-high |
| **Owner** | jamesrow |
| **Component** | hw.dts |
| **Defect Die** | compute |
| **Conclusion** | hw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 85% |
| **Feature** | SoC Thermal | 75% |
| **Sub-Feature** | DTS | — |

**Reasoning**: conclusion='hw.bug' → HW

## Root Cause Summary

Similar failure on VV: 
https://hsdes.intel.com/appstore/article-one/#/article/14026994273

BMC          version                      = 26.02
BMC          Force Update Mode            = no
BIOS         version per dmidecode        = OKSDCRB1.86B.0032.D14.2602052017 - 02/05/2026
TTF varies, and can take up to 23hr
02-14 13:24:RESULT   :  socket0.imh0.punit.ras.gpsb.mc_status=0xa80000007e000402
02-14 13:24:RESULT   :    valid=0x1
02-14 13:24:RESULT   :    ovr=0x0
02-14 13:24:RESULT   :    uc=0x1 -

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww19.3]

TF group decided to treat the CBB and IMH DTS IP bugs separately because, despite similar symptoms, the underlying causes are suspected to be different, with the CBB issue likely tied to a NovaLake DTS bug and the IMH issue potentially being a different bug.

DTS IP Version Differences: 

different versions of the DTS IP are present in CBB and IMH, with only CBB A0 base and compute having the problematic version, while other variants have a fixed version, necessitating different debug and mitigation approaches.

Anatoli and Matthew discussed the lack of clear documentation for the pCode workaround in NovaLake, noting that the workaround details are not specified in the tickets, and that further investigation is needed to determine the correct mitigation steps.

Next: the ongoing daily debug 

thread focused on confirming the root cause of the CBB symptom, investigating workarounds, and determining if the IMH observation is related or requires a separate solution, with involvement from Primecode and pCode teams as needed.

### Description
Similar failure on VV: 
https://hsdes.intel.com/appstore/article-one/#/article/14026994273

BMC          version                      = 26.02
BMC          Force Update Mode            = no
BIOS         version per dmidecode        = OKSDCRB1.86B.0032.D14.2602052017 - 02/05/2026
TTF varies, and can take up to 23hr
02-14 13:24:RESULT   :  socket0.imh0.punit.ras.gpsb.mc_status=0xa80000007e000402
02-14 13:24:RESULT   :    valid=0x1
02-14 13:24:RESULT   :    ovr=0x0
02-14 13:24:RESULT   :    uc=0x1 - UNCORR
02-14 13:24:RESULT   :    en=0x0
02-14 13:24:RESULT   :    miscv=0x1
02-14 13:24:RESULT   :    addrv=0x0
02-14 13:24:RESULT   :    pcc=0x0
02-14 13:24:RESULT   :    s=0x0
02-14 13:24:RESULT   :    ar=0x0
02-14 13:24:RESULT   :    thrs_err_st=0x0
02-14 13:24:RESULT   :    corr_err_count=0x0
02-14 13:24:RESULT   :    fw_upd=0x0
02-14 13:24:RESULT   :    other_info=0x0
02-14 13:24:RESULT   :    msec_fw=0x7e
02-14 13:24:RESULT   :    msec_hw=0x0
02-14 13:24:RESULT   :    msec_uc=0x0
02-14 13:24:RESULT   :    mccod=0x402
02-14 13:24:RESULT   :  socket0.imh0.punit.ras.gpsb.mc_misc=0x22980000
02-14 13:24:RESULT   :    model_specific_information=0x114c00
02-14 13:24:RESULT   :    address_mode=0x0
02-14 13:24:RESULT   :    recoverable_address_lsb=0x0
02-14 13:24:RESULT   :

*Pre HSD created using EyeGlassBridge for NGA*

  

    

      

      
Test line

      
Goal name

      
Failed Test Step

      
Config

      
DDR_Freq

      
BIOS_Version

      
SVOS_Version

      
SUT

      
Vendors

      
CustomBiosOverrides

    

  

  

    

      
dmr-ap_vv_a0_x4_mmx_mdu24a_0005_0

      

 NGA Test Line 

      
MEM MATRIX | AP Mem Matrix | Host Stress CECC MDU24

      
DMR_MEM_EccHarasser

      
MDU24A

      
8000MHz

      
0032.D14

      
2603, 017.5

      
an004022bmh1781

      
H, M, S

      
NaN

    

    

      
dmr-ap_vv_a0_x4_mmx_mdu12a_0008_0

      

 NGA Test Line 

      
MEM MATRIX | AP Mem Matrix | Host Stress Refresh MDU12

      
DMR_MEM_Refresh

### Comments (latest)
++++22611887248 mbfausto
This sighting is tracking the CBB DTS observation identified will debugging DMR Sighting 18044248015.  At this time it is trending to a known DTS IP Bugeco that impacts CBB A0 die only for the DMR program:     [NVL P0][IVT] Observed system hitting DMU MCA with Thermal too hot (RECOVERABLE_DIE_THERMAL_TOO_HOT)     SOC Bugeco:  https://hsdes.intel.com/appstore/article-one/#/article/14025800886     ccb_por:  25ww36.3: In the post silicon, it is observe that high temperature is always being push to the DMU from the Core DTS. After debug the high temperature from the DTS is actually coming from a CDC bug internal to the DTS IP. The DMU is reading the temperature in the CRI CLK while the internal DTS is running on DTS CLK. Due to the broken CDC handling of DTS CLK to CRI CLK. The wrong high temperature is being push to DMU. The HW fixed will be happen internal to the DTS HW. SOC need to have a validation test to ensure this bug is fully fixes. Dcode,Acode WA is still being evaluated. Current plan is just to clone the FW WA ticket for place holder. The bug will be fix in all 2nd stepping for NVL and all stepping on RZL. Reject NVLC-A0, NVLC-P0, NVLC-T0. Clone NVLC-A0 for dcode WA. Clone approved HW fixes in NVLC-L0, NVLC-R0, NVLC-H0, NVLC-J0,RZLC-P0 and RZLC-A0. 1) We have NOT concluded yet (that I am currently aware of) that the CBB observation is this DTS IP Bug.  WIP. 2) DMR does not have an SOC Bugeco nor the dCode/pCode WA that NVL implemented for this DTS IP Bug. 3) Here is a list of "what DMR Die/Steppings are impacted by this DTS Bug.     CBB A0 (as confirmed by @Burak, Maxim)     gpio_library.DTS_G2_for_Intel_1278p6@8.MAINLINE-> which has the DTS bug.       CBB B0 & C0 (as confirmed by Maxim)     gpio_library.DTS_G2_for_Intel_1278p6@14.MAINLINE -> which doesn’t have the bug. Bug is fixed inside DTS IP.       IMH1 A0     gpio_library.DTS_G1_for_Intel_3@18.MAINLINE -> which doesn’t have the bug to begin with.       IMH2 A0 & IMH1 B0     gpio_library.DTS_G1_for_Intel_3@19.MAINLINE-> which doesn’t have the bug to begin with.  

++++22611891418 mbfausto
[CloneScript] Sighting [sighting_central.sighting.id=22022456572] of [component=hw.big_core] in [release=pkg.dmr-a0] has been cloned to a [bug] to [ip_cpu_bigcore.bugeco.id=22022466650] of [component=pnc.ip.core] in [release=pnc-a0]

++++22611891455 mbfausto
I should have written this here, my apologies. The current DTS Sighting TF members (with DTS IP representation) believe the DTS debug data matches the NVL Core DTS IP bugeco and have decided we are ready to root-cause. 1) It is requested we can get the aCode FW Mitigation as a DEBUG PATCH as soon as possible, to continue seeing if there are more/other issues. 2) If the IMH DTS sighting turns out to impact CBB as well, *that* sighting will continue driving for all instances 3) If another symptom occurs (that is not the under-debug IMH DTS symptom) a new sighting will/should be filed.

++++22611894745 jamesrow
WW19.5 update

### Tags
ps2strend,FV_PM,concern,SysDebugCloned

### Conclusion
hw.bug

### Component
hw.dts

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

- **Primary Feature**: SoC Thermal
- **Sub-Feature**: DTS
- **Component Path**: hw.dts

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-05-06 19:35:48
- **Root Caused**: 2026-05-08 22:02:35
- **Days Open**: 15

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
