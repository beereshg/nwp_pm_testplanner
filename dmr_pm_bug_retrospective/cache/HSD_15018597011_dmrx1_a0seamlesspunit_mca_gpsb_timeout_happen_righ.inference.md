# HSD 15018597011: [DMR][X1 A0][Seamless]Punit MCA_GPSB_TIMEOUT happen right after OSPL patch update - missing OSPL handling for IO Skip Disables WA

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [15018597011](https://hsdes.intel.com/appstore/article-one/#/15018597011) |
| **Status** | rejected.merged |
| **Priority** | 2-high |
| **Owner** | nbharati |
| **Component** | fw.primecode |
| **Defect Die** | soc |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Reset/Boot | 75% |
| **Sub-Feature** | Boot | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Seamless patch activation is failing with MLC UC error. All the logs are attached.

System: AN004022BMH2405.amr.corp.intel.com
IFWI: OKSDCRB1_86B_2025.39.2.01_2787.D03_ACTMwa2sFix_MMCfix_UP_600AA968_BIOSKnobs_TdxS3M_Dfxes_ACTM_bypass_RFMDfx

IFWI located at \\amr.corp.intel.com\ec\proj\debug\DMR\User\mseeniv\IFWI\for_ucodeUpdate_testing

Run below commands from pythonsv before kernel boot starts -

>> itp.unlock()

>> unlock(); sv.socket0.imhs.hiop.hiops.hiop_reg.poison_control.en_poison_on_ca =

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww46.3]

Nikita reported that a BIOS fix was tested but results were inconsistent, with the issue sometimes passing and sometimes failing, and noted a dependent issue blocking OSPL.

Alex recommended splitting the GPSB timeout issue from the IO skip disable workaround, treating them as separate sightings for more effective tracking and resolution.

Nikita will file a new sighting specifically for the GPSB timeout.

### Description
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

          0x00000000 : cec (52:38) (rw_v) --  Correctable Error Count

          0x00000000 : bitfix_allocated (53:53) (rw_v) -- Status tracking is Green if this bit is set when a logged error is allocated into bi...

          0x00000000 : bitfix_overcapacity (54:54) (rw_v) -

### Comments (latest)
++++1566618059 nbharati
We observed side band access corruption as well during seamless patch activation

++++1566618058 nbharati
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
FV_CONCURRENCY,Cloned_ToSiliconSighting,Cloned_ToSiliconSighting,FV_SEAMLESS

### Conclusion
no_root_cause.rejected

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

- **Primary Feature**: Reset/Boot
- **Sub-Feature**: Boot
- **Component Path**: fw.primecode

## Firmware Touchpoints

### BIOS
- `BIOS fix`

## Key Registers

- `TPMI fast`
- `TPMI OSXML`
- `sv.socket0.imhs.hiop.hiops.hiop_reg.poison_control.en_poison_on_ca`
- `sv.socket0.cbbs.computes.modules.cores.scp_cr_patchload_post_cnt.read`
- `sv.socket0.cbbs.computes.modules.cores.scp_cr_patchload_flags.read`

## Timeline

- **Submitted**: 2025-11-04 06:39:21
- **Closed**: 2025-11-12 22:28:53
- **Days Open**: 8

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
