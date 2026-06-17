# HSD 18044248015: Refresh, CA, ECC harassers fail hit IMH Punit MCA_RECOVERABLE_DIE_THERMAL_TOO_HOT - IMH DTS

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [18044248015](https://hsdes.intel.com/appstore/article-one/#/18044248015) |
| **Status** | open.clone |
| **Priority** | 2-high |
| **Owner** | jamesrow |
| **Component** | hw.dts |
| **Defect Die** | ioe |
| **Conclusion** |  |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | SoC Thermal | 75% |
| **Sub-Feature** | DTS | — |

**Reasoning**: keyword 'eco' in title/desc → HW

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
﻿[26ww21.3]

James reported that plugins were deployed across the entire testing suite, resulting in over 3000 test runs on 106 systems, with no IMH failures detected. The team plans to expand testing to several hundred systems by the end of the week.

Still the lack of viewpins access for certain thermal sensors (DDRA and DDRB), which necessitates acquiring additional systems to confirm the scope of affected hardware.

James mentioned ongoing debugging efforts in pre-Si environments and the goal of identifying affected systems through comprehensive plugin checks for IMH and CBB failures.

﻿[26ww21.1]

James described ongoing experiments and plugin deployments aimed at reproducing issues across more systems, with the goal of distinguishing between manufacturing defects and other causes.

James noted that root cause analysis is hampered by the lack of necessary tools, such as viewpins, and that the team is relying on system reproduction and additional debug data to make progress.

﻿[26ww20.1]

Alex reported that James indicated no firmware workaround is possible for the DTS issue, though a patch may still be tested.

﻿[26ww19.3]

TF group decided to treat the CBB and IMH DTS IP bugs separately because, despite similar symptoms, the underlying causes are suspected to be different, with the CBB issue likely tied to a NovaLake DTS bug and the IMH issue potentially being a different bug.

DTS IP Version Differences: 

different versions of the DTS IP are present in CBB and IMH, with only CBB A0 base and compute having the problematic version, while other variants have a fixed version, necessitating different debug and mitigation approaches.

Anatoli and Matthew discussed the lack of clear documentation for the pCode workaround in NovaLake, noting that the workaround details are not specified in the tickets, and that further investigation is needed to determine the correct mitigation steps.

Next: the ongoing daily debug 

thread focused on confirming the root cause of th

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
++++1862549268 wrjones
<p>Copy/pasting punit mca decode info here:</p><p><br /></p><p>from pysvtools import server_ip_debug</p><p>server_ip_debug.punit.errors.show_mca_status(source=&quot;reg&quot;)</p><p><br /></p><p>server_ip_debug.resctrl.errors.show_mca_status(source=&quot;reg&quot;)</p><p><br /></p><p>server_ip_debug.rsrc_adapt.errors.show_mca_status(source=&quot;reg&quot;)</p>

++++1862549271 wrjones
14026946466 (related-link) - link(s) are added via link tab.

++++1862549270 wrjones
Linking HSD:&nbsp;https://hsdes.intel.com/appstore/article-one/#/14026946466

++++1862549269 ivangele
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: center;">
      <th></th>
      <th>BIOS_Version</th>
      <th>Config</th>
      <th>CustomBiosOverrides</th>
      <th>DDR_Freq</th>
      <th>Failed Test Step</th>
      <th>Goal name</th>
      <th>SUT</th>
      <th>SVOS_Version</th>
      <th>Test line</th>
      <th>Vendors</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>dmr-ap_vv_a0_x4_mem_fdu1c_0006_0</th>
      <td>0032.D44</td>
      <td>FDU1A</td>
      <td>PeriodicRcomp=Disabled, ShallowSelfRefreshEnable=Disabled</td>
      <td>8000MHz</td>
      <td>DMR_MEM_Maint_Harasser_norcomp</td>
      <td>MEM MAINTENANCE | Maintenance Harasser | Mainteance_Harasser</td>
      <td>gmzp301002h0020</td>
      <td>2603, 019.10</td>
      <td><a href="https://nga.laas.intel.com/#/dmr_fv/planning/testlines/4c554340-fcd4-4342-95d6-48773e130fe5"> NGA Test Line </a></td>
      <td>H</td>
    </tr>
  </tbody>
</table>

++++1862549272 ivangele
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: center;">
      <th></th>
      <th>BIOS_Version</th>
      <th>Config</th>
      <th>CustomBiosOverrides</th>
      <th>DDR_Freq</th>
      <th>Failed Test Step</th>
      <th>Goal name</th>
      <th>SUT</th>
      <th>SVOS_Version</th>
      <th>Test line</th>
      <th>Vendors</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>dmr-ap_vv_a0_x4_mem_mdu24a_0009_0</th>
      <td>0032.D44</td>
      <td>MDU24A</td>
      <td>thermalthrottlingsupport=CLTT, PeriodicRcomp=Disabled, ShallowSelfRefreshEnable=Disabled</td>
      <td>8000MHz</td>
      <td>DMR_MEM_Maint_Harasser_norcomp</td>
      <td>MEM CROSS PRODUCTS | Maintenance x PM | Maint x CLTT MR4</td>
      <td>an004022bmh1781</td>
      <td>2603, 019.10</td>
      <td><a href="https://nga.laas.intel.com/#/dmr_fv/planning/testlines/9b1094fc-fbb1-4add-9b3d-c5c74fab7218"> NGA Test Line </a></td>
      <td>H, M, S</td>
    </tr>
  </tbody>
</table>

++++1862549275 ivangele
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: center;">
      <th></th>
      <th>BIOS_Version</th>
      <th>Config</th>
      <th>CustomBiosOverrides</th>
      <th>DDR_Freq</th>
      <th>Failed Test Step</th>
      <th>Goal name</th>
      <th>SUT</th>
      <th>SVOS_Version</th>
      <th>Test line</th>
      <th>Vendors</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <

### Tags
ps2strend,FV_PM,concern,va.ti_risk

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

### PRIMECODE
- `Primecode change`

## Key Registers

- `sv.socket0.imh0.hwrs.gpsb.hwrs_cmd_current_index`
- `sv.socket0.imh1.hwrs.gpsb.hwrs_cmd_current_index`
- `sv.socket0.cbb0.taps.punit0.pcubclkctrl_wake.pcu_bclk_wake_green_boot_fsm_state`
- `sv.socket0.cbb1.taps.punit0.pcubclkctrl_wake.pcu_bclk_wake_green_boot_fsm_state`
- `sv.socket0.cbb2.taps.punit0.pcubclkctrl_wake.pcu_bclk_wake_green_boot_fsm_state`

## Timeline

- **Submitted**: 2026-02-25 06:03:36
- **Days Open**: 85

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
