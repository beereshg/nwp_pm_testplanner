# HSD 16029995259: [DMR] Seeing very high value in MC6 Residency.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029995259](https://hsdes.intel.com/appstore/article-one/#/16029995259) |
| **Status** | root_caused.awaiting_fix |
| **Priority** | 3-medium |
| **Owner** | hkharya |
| **Component** | fw.ucode.big_core |
| **Defect Die** | compute |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 50% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | MC6 | — |

**Reasoning**: conclusion=fw.bug, defaulting → FW_PCODE

## Root Cause Summary

Issue:

Seeing very high value in MC6 Residency. >100%

System Details
:

Bios: OKSDCRB1.86B.0030.D43.2512102234

Patch: 0x8000098300000000

BMC: oks-2025.50.0

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww13.1]

Elad explained that a patch introduced a bug by using an incorrect multiplication instruction for C6 residency, leading to erroneous telemetry values.

[26ww12.4]

* Struggling to reproduce in Core FV

* If need station - yell Hector's way to get that allocated and happening.

﻿[26ww12.3]

Harsh described that the residency counter for MC6 unexpectedly resets after about 40 minutes, resulting in large or negative values, while other counters increment correctly; Jason and Harsh confirmed this occurs even when the system is idle.

Jason planned to provide Elad with a DMR station to attempt to reproduce the issue on a client system, and Hector and FV validation were identified as resources to help source additional machines if needed.

The team discussed that the issue appears fundamental, as the MSR should not be cleared in this manner, and agreed to perform further idle read tests and monitor the counter behavior across different platforms.

### Description
Issue:

Seeing very high value in MC6 Residency. >100%

System Details
:

Bios: OKSDCRB1.86B.0030.D43.2512102234

Patch: 0x8000098300000000

BMC: oks-2025.50.0

### Comments (latest)
++++1667327348 hkharya
<p>Issue seen with SSMON also.</p><p>UP - 0x985</p><p>Logs in the attachments.</p><p><br /></p><p><u style="font-weight: bold;">SSMON:</u>&nbsp;<span style="font-family: &quot;Courier New&quot;;"><i>./ssmon -p 1 -d 2 -l 1 -y 2 -x SSMON_MC6_CHECK</i></span></p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/16029581749" style="width: 1528px;" tabindex="-1" /></p><p><br /></p><p><u style="font-weight: bold;">Turbostat:</u>&nbsp;<i><span style="font-family: &quot;Courier New&quot;;">./turbostat
-q -i 1 -s Core,CPU,IPC,IRQ,Bzy_MHz,CPU%c1,CPU%c6,Mod%c6,Pkg%pc2,Pkg%pc6</span></i></p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/16029581750" style="width: 856px;" tabindex="-1" /><br /></p>

++++1667327350 hkharya
<p>Captured the <b><u>MC6 Counter MSR_0x664</u></b> &amp; <b><u>TSC MSR_0x10</u></b> along with <b><u>oobmsm TSC counter</u></b>. <font color="#ff0000"><b>I didn't not see any high/garbage value in any of the msr data.</b></font></p><p><font color="#ff0000"><b><br /></b></font></p><p>Logs -<font color="#ff0000" style="font-weight: bold;">&nbsp;</font><a href="https://hsdes.intel.com/resource/16029639767" target="_blank" tabindex="-1">https://hsdes.intel.com/resource/16029639767</a><font color="#ff0000"><b>&nbsp;</b></font></p><p><img src="https://hsdes.intel.com/rest/binary/16029639777" style="width: 480.98px;" tabindex="-1" /><font color="#ff0000"><b><br /></b></font></p><p><font color="#ff0000"><b><br /></b></font></p><p><img src="https://hsdes.intel.com/rest/binary/16029639778" style="width: 569.986px;" tabindex="-1" /><br /></p>

++++1667327352 hkharya
<p>Checking with &nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Bityutskiy, Artem</span>&nbsp;from Linux Kernel team. He suggested to check again with latest turbostat binary.</p><p><br /></p><p>Now with the latest Turbostat. 2025.12.05, instead of high/large MC6 number, seeing &quot;nan&quot; in some places.</p><p>Log -&nbsp;<a href="https://hsdes.intel.com/resource/15018975770" target="_blank" tabindex="-1">https://hsdes.intel.com/resource/15018975770</a>&nbsp;</p><p><br /></p><p><span data-teams="true"></span></p><p><span class="___164yu9v ftuwxu6 f1qdqbpl fua484e f1o6l1dn fac4klo frp1kbq f3wazqe f19l72ij fcsrh55 frnyhdv fyo61pj f1spqul0 f7dkd9s fkq5uzf f1x4fozf fwl63ro f1npyoe5 f10yrmu1 f1w45tcp f1rhua56 f18c6rdl f1e7lo8u f1dpi1ry f1vs2jsm f1o6uux1 f1nu0r7q fg0t3io f1x8dyll f2yyzyc f1sjbqdg fyzb71r fh1aahx f1oktu5 f1d3652t fed2bxt fpeluho f1e76dpb f1lwmlrd f1nri12l f1d705n1 f1jrvuk2 f11h0gum f1tandro fxjdbx7 f1hva1tl fsaoqmu f1w7c29l f1uakdsb f7jsfu7 f1hz9qas f1vmprsu fbmzazh f1oojlmx fpbf6y8 fy6vjqu fuo4419 fbzygsp fnuenae fw75flx f12oply1 fvyt4us f4ki1i fyy2ueq f1w3oopj fum67ou f1j64hbx f1a9cdrb f1q6iyvy f1s5r85c f920ium fhj6euq f30elfj f1kcike0 f1byno2r f5wk2nc fo3pyhm f1m95b1n fob93lq f9myhws fwkcdud f1a3p1vp" itemtype="http://schema.skype.com/AMSImage"><img alt="image" aria-label="image" class="fui-Image

### Tags
SysDebugCloned,SysDebugDccbBypass

### Conclusion
fw.bug

### Component
fw.ucode.big_core

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
- **Sub-Feature**: MC6
- **Component Path**: fw.ucode.big_core

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x664`

## Timeline

- **Submitted**: 2026-03-03 18:17:34
- **Root Caused**: 2026-03-23 22:24:39
- **Days Open**: 79

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
