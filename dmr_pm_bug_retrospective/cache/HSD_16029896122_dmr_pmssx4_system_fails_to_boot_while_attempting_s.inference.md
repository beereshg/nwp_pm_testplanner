# HSD 16029896122: [DMR_PMSS][X4] : System fails to boot while attempting static SST PP Level set from BIOS

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029896122](https://hsdes.intel.com/appstore/article-one/#/16029896122) |
| **Status** | complete.wont_validate |
| **Priority** | 2-high |
| **Owner** | ashashi |
| **Component** | hw.fuse.xml |
| **Defect Die** | compute |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Reset/Boot | 75% |
| **Sub-Feature** | Boot | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

On a 128c, X4 SKU (QDF: Q9X2), unable to boot the system when attempting to set a static SST PP level from BIOS.

Steps:

1. Set  BIOS Knob
 &quot;
IssTdpLevel
&quot; to any value
. 

2. Set 
&quot;
DfxS3mSoftStrap
&quot; to Enabled

3. On boot, system is getting stuck.

Note: Issue is reproducible irrespective of 
SSC Enabled/Disabled
 & 
DynamicISS Enabled/Disabled

BIOS Boot hang

System Info

BIOS Version : OKSDCRB1.86B.0031.D94.2601290349

IA32_BIOS_SIGN_ID (Pcode Patch ID) : 0x8000098d0000

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww10.1]

Anjana relayed that Ido will outline possible solutions and next steps for the die-to-die training issue, with Amit Kaship leading the die-to-die team and Sarah and Amit involved in the ongoing discussions.

﻿[26ww09.3]

System Hang During Static SSTPP Switching: a hang occurring when enabling static SST-PP via BIOS, specifically during S3M soft provisioning. The system fails to boot, prompting a detailed review of BIOS knob combinations and their effects on system behavior.

Yuping explained that the failure signature points to a FIFO overflow, likely related to LCLK frequency mismatches during training. The team suspects that after a code reset, the required 2 GHz LCLK condition may not be met, leading to the observed error.

Ido and Yuping debated whether training at frequencies other than 2 GHz should cause functional failures. Yuping maintained that the training process itself would fail if the O clock is not at the specified frequency, while Ido argued it should only affect training duration, not success.

Vidar and Yuping agreed to continue the technical discussion offline, involving UCI experts Sarah and Yishan to clarify the training requirements and resolve the disagreement.

﻿[26ww09.1]

Anjana described that switching static SST-PP levels via BIOS triggers a soft provisioning flow, after which the system hangs around phase 5 due to a die-to-die mainband link training failure. The failure is 100% reproducible when switching from the default level to higher levels.

Matthew recommended collecting specific training error status logs and comparing them with known signatures, as well as confirming that the latest firmware and BIOS versions are being used for accurate reproduction and analysis.

Nilanjan stressed the importance of verifying that all configuration changes, especially those related to pCode and BIOS, are correctly propagated during the SST-PP change, as misconfiguration could lead to the observed link training failures.

The team ag

### Description
On a 128c, X4 SKU (QDF: Q9X2), unable to boot the system when attempting to set a static SST PP level from BIOS.

Steps:

1. Set  BIOS Knob
 &quot;
IssTdpLevel
&quot; to any value
. 

2. Set 
&quot;
DfxS3mSoftStrap
&quot; to Enabled

3. On boot, system is getting stuck.

Note: Issue is reproducible irrespective of 
SSC Enabled/Disabled
 & 
DynamicISS Enabled/Disabled

BIOS Boot hang

System Info

BIOS Version : OKSDCRB1.86B.0031.D94.2601290349

IA32_BIOS_SIGN_ID (Pcode Patch ID) : 0x8000098d00000000

Kernel Version : 6.14.0-dmr.bkc.6.14.7.4.PO13.16.x86_64

### Comments (latest)
++++1667300008 ashashi
<p>System hangs with the below D2D failure. Could be related to platform HSD:&nbsp;<a href="https://hsdes.intel.com/appstore/article-one/#/article/16029346204" target="_blank" tabindex="-1">https://hsdes.intel.com/appstore/article-one/#/article/16029346204</a>&nbsp;</p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/22022047911" style="width: 1375px;" tabindex="-1" /></p><p><br /></p><p>Need to collect additional failure logs</p>

++++1667300007 abduljaf
<p>Tried the below experiment,</p><p><br /></p><p>Dfxs3m enabled + IssTDPlevel (Auto), DynamicISS(En) ---&gt; booted to OS</p><p>Dfxs3m enabled &nbsp;+ IssTDPlevel=0 , DynamicISS(En) ---&gt; booted to OS</p><p><span style="background-color: rgb(255, 0, 0);">Dfxs3m enabled + IssTDPlevel=1, DynamicISS(En) --&gt; failed to boot</span></p><p><span data-teams="true"></span></p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/16029765098" style="width: 1440px;" tabindex="-1" /><br /></p>

++++1667300009 abduljaf
<p>SST PP module_disable_mask seems wrong,</p><p><img src="https://hsdes.intel.com/rest/binary/16029768824" style="width: 705px;" tabindex="-1" data-processed="true" /></p><p><br /></p><p>In [5]: sv.socket0.cbbs.base.fuses.punit_fuses.fw_fuses_sst_pp_0_module_disable_mask.show()</p><p>0x5008ecff : fw_fuses_sst_pp_0_module_disable_mask -- Per-module bit mask. A '1' indicates that module is disabled.</p><p>0x48ff0d92 : fw_fuses_sst_pp_0_module_disable_mask -- Per-module bit mask. A '1' indicates that module is disabled.</p><p>0x4e0a09ff : fw_fuses_sst_pp_0_module_disable_mask -- Per-module bit mask. A '1' indicates that module is disabled.</p><p>0x4a005eff : fw_fuses_sst_pp_0_module_disable_mask -- Per-module bit mask. A '1' indicates that module is disabled.</p><p><br /></p><p>In [8]: ~(0x5008ecff) &amp; 0xffffffff</p><p>Out[8]: 0xAFF71300</p><p><br /></p><p>In [6]: sv.socket0.cbbs.base.fuses.punit_fuses.fw_fuses_sst_pp_1_module_disable_mask.show()</p><p>0x5208edff : fw_fuses_sst_pp_1_module_disable_mask -- Per-module bit mask. A '1' indicates that module is disabled.</p><p>0x48ff0d9b : fw_fuses_sst_pp_1_module_disable_mask -- Per-module bit mask. A '1' indicates that module is disabled.</p><p>0x5e0a29ff : fw_fuses_sst_pp_1_module_disable_mask -- Per-module bit mask. A '1' indicates that module is disabled.</p><p>0x4a00dfff : fw_fuses_sst_pp_1_module_disable_mask -- Per-module bit mask. A '1' indicates that module is disabled.</p><p><br /></p><p>In [7]: ~(0x5208edff) &amp; 0xffffffff</p><p>Out[7]: 0xADF71200</p><p><br /></p><p>In [9]: ~(0x48ff0d92) &amp; 0xffffffff</p><p>Out[9]: 0xB700F26D</p>

++++1667300010 abduljaf
<p>I have tried below experiments by disabling modules with&nbsp;<span style="background-color: rgb(245, 246, 255); color: rgba(0, 0, 0, 0.87); font-family: Roboto, &quot;Helvetica Neue&quot;, sans-serif; font-size: 12.18px;">sst_pp_1_module_disable_mask </span>instead of setting IssTDPlevel knob,</p><p><br /></p><p>changed the belo

### Tags
SysDebugCloned,SysDebugDccbBypass

### Conclusion
hw.arch

### Component
hw.fuse.xml

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
- **Component Path**: hw.fuse.xml

## Firmware Touchpoints

### PCODE
- `Pcode Patch`

### BIOS
- `BIOS Knob`
- `BIOS knob`

## Key Registers

- `TPMI dump`
- `sv.socket0.cbbs.base.fuses.punit_fuses.fw_fuses_sst_pp_0_module_disable_mask.show`
- `sv.socket0.cbbs.base.fuses.punit_fuses.fw_fuses_sst_pp_1_module_disable_mask.show`

## Timeline

- **Submitted**: 2026-02-19 23:47:42
- **Root Caused**: 2026-03-04 20:57:02
- **Closed**: 2026-03-17 22:09:35
- **Days Open**: 25

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
