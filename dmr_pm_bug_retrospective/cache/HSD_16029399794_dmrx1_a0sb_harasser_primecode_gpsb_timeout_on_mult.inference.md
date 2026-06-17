# HSD 16029399794: [DMR][X1 A0][SB Harasser] Primecode GPSB Timeout on Multiple Endpoints with PKGC enabled with pcode read/write.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029399794](https://hsdes.intel.com/appstore/article-one/#/16029399794) |
| **Status** | complete.wont_validate |
| **Priority** | 3-medium |
| **Owner** | salmanha |
| **Component** | val.env.content |
| **Defect Die** | ioe |
| **Conclusion** | env.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **TOOL** | 85% |
| **Feature** | Sideband/D2D | 80% |
| **Sub-Feature** | GPSB | — |

**Reasoning**: conclusion='env.bug' → TOOL

## Root Cause Summary

Collaterals
:

Platform: SC00901159H0033.amr.corp.intel.com

IFWI: 

OKSDCRB1_86B_2025.45.4.02_0029.D15_6000097B_0.650.0_IPCleanDFXEnable_Trace_DebugSigned.bin

Summary
:

Observing GPSB Timeout when running SB harasser through pcode read/write on IMH endpoints with PKGC enabled

MCCMI_DNSTRM_x_MC_x

MSE_x_MC_x

SCA_x

CMS_x

UBR_x

IOLLC_x

mse_multicast_group_for_ncracu_ubox

Steps to Reproduce:

SUT:

biosknob read EETurbo TurboMode MonitorMWait

EETurbo = 0x1 <Enabled>

TurboMode = 0x1 <Enab

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
S
  
97 94 -> GPSB Timeout when running SB harasser through pcode read/write on IMH endpoints with PKGC enabled

 

Salman/Joe Brooks

Failing signature: 

Theory: 

Light switches: 

WA:

 

WW4.3

Anything else pending , seems we are all good -> All was about content fine tuning 
After removing the EP we need to verify that PC6 residency still happens 

Next)Salman)Make sure we still see PC6 residency happening 

WW3.2

Are we done here? No presence from SLD or the owner 

WW2.1

Were we left this was-> haraser may not be aware of Package C (There are no checks done by the SB Harasser itself regarding PkgC)
Do we have a path to make this work ? 
1) We have some SB points that does not play well with Package C ( they are removed from the test)
2) In the other case we are hitting like worst case timing for some SB tnx

Plan is to extend the timeout , and see if this works 

This is not real case , Prime code wont initiate a SB tnx 

Next)Joe)
 Please document what changes we are putting in B step that may help here 

WW51.2

 

 

The SB Harasser is only to enable internal testing to harass the sideband in any way the user desires.

 

There are no checks done by the SB Harasser itself regarding PkgC. If the user wants to cross SB harassing with PkgC that is up to them (and could be a valid use case).

 

For the issue at hand, the IO mesh drops to 800 MHz in PkgC6 so could definitely be the cause of the sideband slowness

 

Issue disappears by disabling the IOSF GPSB timeout.

Accorind to Joe , running the harraser combined with Package C maybe is not a good idea
Joe mentioned there's another bug they recently found  on Pakcage C x D2D ,
In short the harraser may not be aware of Package C 

Next)Joe) Please provide the list of things we can probably remove and see if that helps 

Next)Salman) Can we swithc to regular pythonsv access insteand of the harraser to see if we run into the same issues /
Next)Robert/Salman) Let's find probably another ends poitns that can

### Description
Collaterals
:

Platform: SC00901159H0033.amr.corp.intel.com

IFWI: 

OKSDCRB1_86B_2025.45.4.02_0029.D15_6000097B_0.650.0_IPCleanDFXEnable_Trace_DebugSigned.bin

Summary
:

Observing GPSB Timeout when running SB harasser through pcode read/write on IMH endpoints with PKGC enabled

MCCMI_DNSTRM_x_MC_x

MSE_x_MC_x

SCA_x

CMS_x

UBR_x

IOLLC_x

mse_multicast_group_for_ncracu_ubox

Steps to Reproduce:

SUT:

biosknob read EETurbo TurboMode MonitorMWait

EETurbo = 0x1 <Enabled>

TurboMode = 0x1 <Enabled>

MonitorMWait = 0x1 <Enabled>

msr -w 0x22 -o e2 -a

HOST:

sv.socket0.imh0.isa.isa_scf_center2top.spare_cfg0=0xffffffff

sv.socket0.imh0.isa.isa_scf_center2top.spare_cfg1=0x3FF

sv.socket0.imh0.isa.isa_scf_center2bot.spare_cfg0=0xffffffff

sv.socket0.imh0.isa.isa_scf_center2bot.spare_cfg1=0x3FF

sv.socket0.imh1.isa.isa_scf_center0bot.spare_cfg0=0xffffffff

sv.socket0.imh1.isa.isa_scf_center0bot.spare_cfg1=0x3ff

sv.socket0.imh1.isa.isa_scf_center0top.spare_cfg0=0xffffffff

sv.socket0.imh1.isa.isa_scf_center0top.spare_cfg1=0x3ff

sv.sockets.imhs.isa.isa_mio_1.spare_cfg0=0x18000

sv.sockets.imhs.scf.hamvf.has.cmimiscconfig.chnl1_idle_req_enable=1

sv.sockets.imhs.scf.hamvf.has.cmimiscconfig.chnl0_idle_req_enable=1

import
diamondrapids.pm.SB_Harasser.sb_harasser_DMR as hr

hr.run_harasser_loop(interval
= 10, t_time = 3600, die_id=[8],pmsb=1,gpsb=1,
pcode=1,ocode=0,pcode_operation=1,ocode_operation=0)

Reproduced the issue by manually running the traffic only on portid=0x1f9

sv.socket0.imh0.pcodeio_map.io_sa_bulk_cr_data[3]
= 0

sv.socket0.imh0.pcodeio_map.io_sa_bulk_cr_data[2]
= 0x1f403e8

sv.socket0.imh0.pcodeio_map.io_sa_bulk_cr_data[1]
= 0xffff01f9

sv.socket0.imh0.pcodeio_map.io_sa_bulk_cr_data[0]
= 0xa0000000

### Comments (latest)
++++1667167918 sumanku2
[CloneScript] Sighting 16029399794 cloned from PreSighting 16029183795
++++22611631710 agraback
The SB Harasser is only to enable internal testing to harass the sideband in any way the user desires. There are no checks done by the SB Harasser itself regarding PkgC. If the user wants to cross SB harassing with PkgC that is up to them (and could be a valid use case). For the issue at hand, the IO mesh drops to 800 MHz in PkgC6 so could definitely be the cause of the sideband slowness
++++14614888635 jesussal
Issue disappears by disabling the IOSF GPSB timeout. Harasser sending 500 transactions per second which appears to be within the spec ranges. Evaluating if this needs to go to full chip forum for debug. 

++++14614902190 jsbrooks
Next set of experiments: 1) Disable PkgC. Set IMH MEM and IO frequencies to 800MHz.  Run Primecode harasser.           sv.sockets.imhs.punit.ptpcfsms.ptpcfsms.ufs_control.min_ratio = 8           sv.sockets.imhs.punit.ptpcfsms.ptpcfsms.ufs_control.max_ratio = 8           sv.sockets.imhs.punit.ptpcfsms.ptpcfsms.ufs_control_1.min_ratio = 8           sv.sockets.imhs.punit.ptpcfsms.ptpcfsms.ufs_control_1.max_ratio  = 8 2) Run PkgC w/ Primecode harasser  (Exclude MSE*, RAT*, MCCMI_*, npk, UCIE Phy.) 3) Run PkgC w/ Ocode harasser  (Exclude MSE*, RAT*, MCCMI_*, npk, UCIE Phy.)
++++1566719462 salmanha
Here are results from experiment: OKSDCRB1.86B.0030.D43.2512102234   PC6 disabled PC6 Enabled ( Exclude MSE*, RAT*, MCCMI_*, npk, UCIE Phy.) Primecode(Rd) Pass AN004022BMH2291 Fail https://axonsv.app.intel.com/apps/record-viewer?id=019b2beb-19d5-76b3-9469-1580ca5bfa25 BA00302ECOH0003 Fail https://axonsv.app.intel.com/apps/record-viewer?id=019b2bda-f2b5-7e72-9673-09a1ad9f29dc Ocode(Rd) Pass Pass Primecode(Wr) Pass Pass Ocode(Wr) Pass Pass
++++14614939835 jsbrooks
Thanks for running those experiments.  Given this + the TO disable runs, this does not look to be exposing a HW issue.  Rather, the TO looks to be occurring due to PkgC exit latency.  This is exacerbated by Primecode starting the GPSB timer and then issuing the transaction which will cause PkgC exit.  We'd need mesh WP actions to complete before the sideband transaction could complete. I think next step is going to be a Primecode debug patch that increases the GPSB TO value.  I believe it's a hardcoded constant; so, we could start w/ trippling the value.  I will also take a look at some PreSI logs to see about measuring completion time for such a wake condition.
++++22611677029 agraback
Primecode's GPSB Timeout value can be adjusted with pcudata: sv.socket0.imhs.pcudata.state_instance.gpsb_timeout_in_us
++++1667218734 salmanha
after boot i am seeing this register default value is 0 In [343]: sv.socket0.imhs.pcudata.state_instance.gpsb_timeout_in_us Out[343]: socket0.imh0.pcudata.state_instance.gpsb_timeout_in_us - [32b] 0x00000000 socket0.imh1.pcudata.state_instance.gpsb_timeout_in_us - [32b] 0x00000000
++++22611697284 salmanha 
With latest IMH EP l

### Tags
FV_PM_BDC,FV_SB_HARASSER

### Conclusion
env.bug

### Component
val.env.content

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

- **Primary Feature**: Sideband/D2D
- **Sub-Feature**: GPSB
- **Component Path**: val.env.content

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.isa.isa_scf_center2top.spare_cfg0`
- `sv.socket0.imh0.isa.isa_scf_center2top.spare_cfg1`
- `sv.socket0.imh0.isa.isa_scf_center2bot.spare_cfg0`
- `sv.socket0.imh0.isa.isa_scf_center2bot.spare_cfg1`
- `sv.socket0.imh1.isa.isa_scf_center0bot.spare_cfg0`

## Timeline

- **Submitted**: 2025-12-09 20:34:20
- **Root Caused**: 2026-01-27 09:48:37
- **Closed**: 2026-01-27 09:48:37
- **Days Open**: 48

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
