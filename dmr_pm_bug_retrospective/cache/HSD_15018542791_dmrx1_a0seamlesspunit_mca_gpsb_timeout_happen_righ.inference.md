# HSD 15018542791: [DMR][X1 A0][Seamless]Punit MCA_GPSB_TIMEOUT happen right after OSPL patch update - VF sequencer watchdog timeout

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [15018542791](https://hsdes.intel.com/appstore/article-one/#/15018542791) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | nbharati |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Sideband/D2D | 80% |
| **Sub-Feature** | GPSB | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

This sighting addresses 
VF sequencer watchdog timeout only (Primecode):

- potential cause: Primecode not restoring D2D_Link enable/disables after OSPL

- would be new issue

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Seamless patch activation is failing with MLC UC error. All the logs are attached.

System: AN004022BMH2405.amr.corp.intel.com
IFWI: OKSDCRB1_86B_2025.39.2.01_2787.D03_ACTMwa2sFix_MMCfix_UP_600AA968_BIOSKnobs_TdxS3M_Dfxes_ACTM_bypass_RFMDfx

IFWI loc

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww45.1]

The VF sequencer watchdog timeout is caused by Primecode losing track of which D2D_Link instances are enabled after OSPL, and a patch was created to address this. The team agreed to separate this issue for clarity and promote the fix to PrimeCode.

Primecode handles overall D2D IP instance disabling and persist that but we have a sub IP for D2D link to handle ITD and that sub IP which we properly enabled or disabled during the D2D main band training flow. That training flow gets skipped from a reset, so we didn't do the enabling disabling of that. After OSPL, Primecode needs to run ITD on all links, even though they're not available.

Alex described the MCA GPSB timeout as related to the IO skip disables workaround, which was not persisting across OSPL. The workaround was updated and submitted in mainline, and the team is working with validator submitters to ensure a working combination of debug patches, including proper signing for OSPL images.

Vidar will root cause the issue of the VF sequencer watchdog timeout, a separate sighting will address MCA GPSB timeout.

-------------------------------------------------------------------------------------------------------------

S 

 

27 91 -> Hitting VF sequencer watchdog timeout after OSPL flow

Diego/Visha

Failing signature: VF sequencer watchdog timeout after OSPL flow

 

Theory: 

Light switches: 

WA:

 

WW43.3

 

(MCA) code 0x402The error indicates a timeout while waiting for a response from the voltage resource adapter during a workpoint change. 

What about trying to disable FIVR? Joe is checking this 

According to Craig this happens while we access wrmsr 0x79 

This is happening at least in 2 systems ( BDC and Ricardo)

Next) Joe)

 Please have a look a define next steps for this

### Description
This sighting addresses 
VF sequencer watchdog timeout only (Primecode):

- potential cause: Primecode not restoring D2D_Link enable/disables after OSPL

- would be new issue

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Seamless patch activation is failing with MLC UC error. All the logs are attached.

System: AN004022BMH2405.amr.corp.intel.com
IFWI: OKSDCRB1_86B_2025.39.2.01_2787.D03_ACTMwa2sFix_MMCfix_UP_600AA968_BIOSKnobs_TdxS3M_Dfxes_ACTM_bypass_RFMDfx

IFWI located at \\amr.corp.intel.com\ec\proj\debug\DMR\User\mseeniv\IFWI\for_ucodeUpdate_testing

Run below commands from pythonsv before kernel boot starts -

>> itp.unlock()

>> unlock(); sv.socket0.imhs.hiop.hiops.hiop_reg.poison_control.en_poison_on_ca = 0

Microcode version after OS boot - 

IFWI microcode revisions     = 0x600AA968

Once system is booted to OS, patch load was done using below commands -

$ cp 

UP_DMR_A0_6000096A_TPRODSIGNED.pdb.min_1

 /lib/firmware/intel-ucode/13-01-00

$ echo Y > /sys/kernel/debug/microcode/loading
$ echo Y > /sys/kernel/debug/microcode/staging

$ echo 1 > /sys/kernel/debug/microcode/anyrev
$ echo 1 > /sys/devices/system/cpu/microcode/reload

System gets stuck at this stage, leading to MCA error (hard hang)

dmesg shows staging is successful but during activation, system is getting hard hang

Below is the MCA dump -

 

************* Bank:03 - Name:MLC        - Scope:Module  **************

    -->BANG!! Machine Check Found at Bank:03 Name:MLC        Socket:00 IP:MLC

      MC_STATUS=0xF2000000E1810400, MC_CTL=0x000000000000007F, MC_CTL2=0x0000000040000001 MC_ADDR=0x0000000000000000 MC_MISC=0x0000000000000000

      socket0.cbb0.compute2.module22.ml2_cr_mc3_status

      0x00000400 : mcacod (15:00) (rw_v) --  Machine Check Architecture Error Code

          0x0000e181 : mscod (31:16) (rw_v) --  Model Specific Error Code

          0x00000000 : enh_mca_avail0 (37:32) (rw_v) -- Available when Enhanced MCA is in use

          0x00000000 : cec 

### Comments (latest)
++++1566588598 nbharati
We observed side band access corruption as well during seamless patch activation

++++1566588600 nbharati
<span data-teams="true"><p>We have tested the OSPL flow by excluding icode and ocode in the FW but encountered Punit CATERR by end of the OSPL.</p><p>Sharing the quick reference log for review.</p><p>&nbsp;</p><p>root@AN004022BMS2405:/&gt;[&nbsp; 920.830992] microcode: configs: loading=true, staging=true, anyrev=true<br /><span style="color: rgb(43, 155, 98);"><strong>[&nbsp; 929.144517] microcode: Staging was successful.</strong></span><br /><span style="color: rgb(43, 155, 98);"><strong>[&nbsp; 929.255015] microcode: load: updated on 1 primary CPUs with 5 siblings</strong></span><br /><span style="color: rgb(43, 155, 98);"><strong>[&nbsp; 929.265020] microcode: revision: 0x600aa968 -&gt; 0x405801e5</strong></span><br />
[&nbsp; 929.273695] sgx: EUPDATESVN was successful, but CPUSVN was not updated, because current SVN was not newer than CPUSVN.<br />
WheaElogSwSmiCallback Enter<br /><span style="color: rgb(253, 192, 48);"><strong>PANIC: Fatal machine check on current CPU</strong></span></p><p>&nbsp;</p><p>In :&nbsp; sv.socket0.imh0.s3m.ibl_treg.s3m_s3mfw_revids.show()<br /><span style="background-color: rgb(130, 205, 168);"><strong>0x03022964 : </strong></span>s3m_s3mfw_boot_revid (63:32) (rw/p/l) -- RevID of the S3M FW image loaded at system boot / after cold/global reset<br /><span style="background-color: rgb(130, 205, 168);"><strong>0x03022979 :</strong> </span>s3m_s3mfw_current_revid (31:00) (rw/p/l) -- RevID of the current S3M FW image (boot version or new version after a seamless upda...</p><p>&nbsp;</p><p>MCA signature:</p><p>&nbsp;</p><p><br />
&nbsp; ************* Bank:11 - Name:PUNIT_IMH&nbsp; - Scope:IMH&nbsp;&nbsp;&nbsp;&nbsp; **************<br />
&nbsp;&nbsp;&nbsp; --&gt;BANG!! Machine Check Found at Bank:11 Name:PUNIT_IMH&nbsp; Socket:00 IP:PUNIT_IMH<br /><span style="background-color: rgb(253, 212, 114);"><strong>MC_STATUS=0xBA00000000200402</strong></span>, MC_CTL=0xFFFFFFFFFFFFFFFF, MC_CTL2=0x0000000040000000 MC_ADDR=0x0000000000000000 <span style="color: rgb(253, 192, 48);"><strong>MC_MISC=0x0000000101098200</strong></span><br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; s<span style="color: rgb(253, 192, 48);"><strong>ocket0.imh0.punit.ras.gpsb.mc_status</strong></span><br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 0x00000001 : valid (63:63) (rw/v/p) -- Indicates that this register contains a valid MCA error that was detected.<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 0x00000000 : ovr (62:62) (rw/v/p) -- Another MCA error was detected when VALID was already set to 1b.&nbsp; In other words, a second MCA...<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 0x00000001 : uc (61:61) (rw/v/p) -- UNCORR -- Indicates (when set) that the processor did not correct the error condition. 0b&nbsp;&nbsp;&nbsp;&nbsp; C...<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbs

### Tags
FV_CONCURRENCY,SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_6000097D,FIX_IFWI_DMR_AP1_2025.47.1.01,FV_SEAMLESS,FIX_BKC_OKS_DMR_AP1_2025WW47, PSF=Y

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

- **Primary Feature**: Sideband/D2D
- **Sub-Feature**: GPSB
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imhs.hiop.hiops.hiop_reg.poison_control.en_poison_on_ca`
- `sv.socket0.cbbs.computes.modules.cores.scp_cr_patchload_post_cnt.read`
- `sv.socket0.cbbs.computes.modules.cores.scp_cr_patchload_flags.read`

## Timeline

- **Submitted**: 2025-10-22 06:13:12
- **Root Caused**: 2025-11-04 06:13:02
- **Closed**: 2026-01-29 19:42:35
- **Days Open**: 99

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
