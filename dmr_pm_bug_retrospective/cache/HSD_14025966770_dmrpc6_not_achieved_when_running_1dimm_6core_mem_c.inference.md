# HSD 14025966770: [DMR]PC6 not achieved when running 1DIMM 6core mem configuration, stuck in PC2.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025966770](https://hsdes.intel.com/appstore/article-one/#/14025966770) |
| **Status** | rejected.cannot_reproduce |
| **Priority** | 2-high |
| **Owner** | hmpicosm |
| **Component** | bios |
| **Defect Die** | ioe |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 75% |
| **Feature** | Core C-States | 75% |
| **Sub-Feature** | C6 | — |

**Reasoning**: errata_status='review_waived' → HW

## Root Cause Summary

Summary:

========

When applying WA for existing sighting 
https://hsdes.intel.com/appstore/article-one/#/article/14025874051
 on a 1DIMM 6 core system, PC6 is not achieved and systems remains at ~50% PC2 residency. Saw inconsistent behavior, with when it was tried on a 32 core machine, hence we have presighting for each (32 core presighting 
https://hsdes.intel.com/appstore/article-one/#/article/14025931167
).

New WA used: 

sv.socket0.imh0.isa.isa_scf_center2top.spare_cfg0=0xffffffff

sv.soc

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww19.3]

Hector will try the latest IFWI and the last 2 IFWIs and see if the issue is still there

﻿[26ww18.3]

No update. Will try new EB BIOS. Systems busy on the FIVR TO issue 

﻿[26ww18.1]

Hector plans to test the new BIOS build on multiple systems with varying memory configurations, focusing on unpopulated channels, and will update the HSD with the results.

﻿[26ww17.3]

BIOS Programming and MSC Idle Bits: The team discussed confusion over BIOS programming of MSC idle bits, with Hector noting that engineering builds set these bits to one, enabling PkgC6, while release BIOS sets them to zero, which does not work; Joe clarified that the spec requires zeros, and the group agreed to consult BIOS and architecture teams for further guidance.

Matthew pointed the need to investigate both BIOS programming and memory controller behavior, suggesting that waiting solely for BIOS responses could delay progress, and recommended engaging with memory controller designers to understand idle signaling.

Hector will plan to set up meetings with Marius and BIOS teams, collect additional debug logs, and continue experiments across multiple systems to validate workarounds and clarify the programming logic for PC6 residency.

﻿[26ww17.1]

BIOS log provided, will flash it to check for correct behavior and to provide BIOS logs

﻿[26ww16.4]

Hector noted that while the BIOS team reported correct programming, logs indicated otherwise, and it was unclear whether A0 or A1 was being programmed. The team observed persistent issues since power-on, suggesting the problem has always existed.

The team decided to continue working with the BIOS team to clarify the programming logic and gather more detailed logs for analysis, with Hector leading the effort.

﻿[26ww14.1]

Hector reported that the team is running experiments on several systems to define and validate a workaround for enabling PkgC6, but frequent FIVR MCA issues are blocking progress, and a debug patch from Alex only allows reac

### Description
Summary:

========

When applying WA for existing sighting 
https://hsdes.intel.com/appstore/article-one/#/article/14025874051
 on a 1DIMM 6 core system, PC6 is not achieved and systems remains at ~50% PC2 residency. Saw inconsistent behavior, with when it was tried on a 32 core machine, hence we have presighting for each (32 core presighting 
https://hsdes.intel.com/appstore/article-one/#/article/14025931167
).

New WA used: 

sv.socket0.imh0.isa.isa_scf_center2top.spare_cfg0=0xffffffff

sv.socket0.imh0.isa.isa_scf_center2top.spare_cfg1=0x3FF

sv.socket0.imh0.isa.isa_scf_center2bot.spare_cfg0=0xffffffff

sv.socket0.imh0.isa.isa_scf_center2bot.spare_cfg1=0x3FF

sv.socket0.imh1.isa.isa_scf_center0bot.spare_cfg0=0xffffffff

sv.socket0.imh1.isa.isa_scf_center0bot.spare_cfg1=0x3ff

sv.socket0.imh1.isa.isa_scf_center0top.spare_cfg0=0xffffffff

sv.socket0.imh1.isa.isa_scf_center0top.spare_cfg1=0x3ff

Impact:

========

PC6 not achieved on 1DIMM mem configuration.

Details:

========

==> System configuration ...

X1 fused silicon , 32 Cores

==> BIOS/Patch/IFWI/BKC/CI Versions ...

OKSDCRB1.86B.2025.35.3.01_2688.D02_6020095E_1P0_NonIPClean_Trace_DebugSigned_update_primecode_pcode

### Comments (latest)
++++14614654440 wstathis
<p>Was able to reproduce this issue on an 8-DIMM system. Saw the same signature of being stuck in PC2, and cfc_idle not asserted with dev_l_qactive0 from imh0/1 RC_CFCMEM_EW.&nbsp;</p><p><br /></p><p>Narrowed down the downstream qactive to MSE from MC stack by applying various overrides until PC6 was achieved. It was found that the following recipe allowed us to achieve 50%-60% PC6 residency.</p><p><br /></p><p>For each non-disabled MC do the following:</p><p class="MsoNormal"><b>sv.socket0.imh[0/1].isa.isa_mc_[0-7].spare_cfg0=0xc0<o:p></o:p></b></p><p class="MsoNormal"><b><br /></b></p><p class="MsoNormal"><img src="https://hsdes.intel.com/rest/binary/18043455506" style="width: 506px;" /><b><br /></b></p><p class="MsoNormal"><a href="https://intel.sharepoint.com/:u:/r/sites/DiamondRapids/IMH_FE/_layouts/15/Doc.aspx?sourcedoc=%7BC22E510E-743F-4D05-831F-4C9153B1E886%7D&amp;file=IMH%20PM%20Construction.vsdx&amp;action=default&amp;mobileredirect=true&amp;clickparams=eyJBcHBOYW1lIjoiVGVhbXMtRGVza3RvcCIsIkFwcFZlcnNpb24iOiIyNy8yMzA5MDExMjI3OCIsIkhhc0ZlZGVyYXRlZFVzZXIiOmZhbHNlfQ%3D%3D&amp;cid=8adc8d9e-03fe-4177-b796-0655a8fc4ae0" target="_blank">https://intel.sharepoint.com/:u:/r/sites/DiamondRapids/IMH_FE/_layouts/15/Doc.aspx?sourcedoc=%7BC22E510E-743F-4D05-831F-4C9153B1E886%7D&amp;file=IMH%20PM%20Construction.vsdx&amp;action=default&amp;mobileredirect=true&amp;clickparams=eyJBcHBOYW1lIjoiVGVhbXMtRGVza3RvcCIsIkFwcFZlcnNpb24iOiIyNy8yMzA5MDExMjI3OCIsIkhhc0ZlZGVyYXRlZFVzZXIiOmZhbHNlfQ%3D%3D&amp;cid=8adc8d9e-03fe-4177-b796-0655a8fc4ae0</a>&nbsp;</p><p class="MsoNormal"><br /></p><p class="MsoNormal"><img src="https://hsdes.intel.com/rest/binary/18043455507" style="width: 1490px;" data-processed="true" /><b><br /></b></p><p class="MsoNormal"><a href="https://intel.sharepoint.com/:x:/r/sites/DiamondRapids/IMH_FE/_layouts/15/Doc.aspx?sourcedoc=%7B5FA0F1C2-1860-4BB8-8C42-3D61B0EFC0E2%7D&amp;file=Pch_Qch_Survivability.xlsx&amp;action=default&amp;mobileredirect=true" target="_blank">https://intel.sharepoint.com/:x:/r/sites/DiamondRapids/IMH_FE/_layouts/15/Doc.aspx?sourcedoc=%7B5FA0F1C2-1860-4BB8-8C42-3D61B0EFC0E2%7D&amp;file=Pch_Qch_Survivability.xlsx&amp;action=default&amp;mobileredirect=true</a>&nbsp;</p><p class="MsoNormal"><br /></p><p class="MsoNormal">Further experiments and research into possible cause of MSE qactive being stuck at 1 are pending.</p>

++++14614654441 shijup1
<p class="MsoNormal"><span style="font-size:11.0pt;mso-ascii-font-family:Aptos;
mso-ascii-theme-font:minor-latin;mso-hansi-font-family:Aptos;mso-hansi-theme-font:
minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-bidi-theme-font:minor-bidi">As
per suggestion by </span><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-ligatures:none">Brooks, Joseph S&nbsp; dumped register values mentioned in feature request HSD</span><span style="font-size:11.0pt;mso-ascii-font-family

### Tags
BIOS_MS_POWER_ON,SysDebugCloned,BIOS_RCR.14026047057,SysDebugDccbBypass,FV_PM

### Conclusion
no_root_cause.rejected

### Component
bios

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

- **Primary Feature**: Core C-States
- **Sub-Feature**: C6
- **Component Path**: bios

## Firmware Touchpoints

### BIOS
- `BIOS fix`
- `BIOS change`

## Key Registers

- `MSR 0x08B`
- `sv.socket0.imh0.isa.isa_scf_center2top.spare_cfg0`
- `sv.socket0.imh0.isa.isa_scf_center2top.spare_cfg1`
- `sv.socket0.imh0.isa.isa_scf_center2bot.spare_cfg0`
- `sv.socket0.imh0.isa.isa_scf_center2bot.spare_cfg1`
- `sv.socket0.imh1.isa.isa_scf_center0bot.spare_cfg0`

## Timeline

- **Submitted**: 2025-09-25 00:12:42
- **Closed**: 2026-05-11 21:00:32
- **Days Open**: 228

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
