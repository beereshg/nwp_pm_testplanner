# HSD 16030620540: MC6 Residency for Module0 is going 0% when running WL on other Modules

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16030620540](https://hsdes.intel.com/appstore/article-one/#/16030620540) |
| **Status** | open.clone |
| **Priority** | 3-medium |
| **Owner** | hkharya |
| **Component** | fw.acode |
| **Defect Die** | compute |
| **Conclusion** |  |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | MC6 | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Issue:

MC6 Residency for Module0 is going 0% when running WL on other Modules.

Below had 3 Modules. When running WL on Module1, Module0 MC6 residency also going down.

Tried 3 different WL {AIB, Stress-ng, Instlat}, seeing same behavior.

System Details
:

Bios: OKSDCRB1.86B.0030.D43.2512102234

Patch: 0x8000098300000000

BMC: oks-2025.50.0

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿

﻿[26ww21.3]

  -    Email discussion indicates that 

interrupt activity

 and 

untuned L2 flush values

 may be contributing to reduced 

MC6/PKG-C6 residency

.

  -    

Testing by 

Harsh Kharya

 across multiple 

l2_flush_demotion_policy

 and 

l2_flush_policy_minimal_hold_time

 settings showed the best MC6 residency with:

            L2_FLUSH_DEMOTION_POLICY = 0x2

            

l2_flush_policy_minimal_hold_time = 0.0 ms

 or 

0.1 ms

            

Peak MC6 residency of 

up to 71.2%

  -    

Based on current data, 

Ido Melamed

 recommended retuning the aCode defaults:

            

aggressive_hold_time

: 

5 ms -> 2 ms

            

gentle_hold_time

: 

2 ms -> 1 ms

            

minimal_hold_time

: 

0.5 ms -> 0 ms

  -    

Current assumption is that these knobs should 

not affect C1 demotion

, since: 

C1 demotion

 is controlled at the 

core level 
and 

L2 flush policy

 is controlled at the 

module level

  -    

Next steps:

            

Complete sweep/testing across all core modules

            

Evaluate impact on 

PKG-C6 residency

            

Select the default policy based on measured 

PKG-C6 results

### Description
Issue:

MC6 Residency for Module0 is going 0% when running WL on other Modules.

Below had 3 Modules. When running WL on Module1, Module0 MC6 residency also going down.

Tried 3 different WL {AIB, Stress-ng, Instlat}, seeing same behavior.

System Details
:

Bios: OKSDCRB1.86B.0030.D43.2512102234

Patch: 0x8000098300000000

BMC: oks-2025.50.0

### Comments (latest)
++++1667515758 hkharya
<span data-teams="true"><p>Checked the behavior on CWF.</p><p>When Running WL on 2 Modules, Mod0 MC6 has dropped slightly but not to 0.</p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/16029475246" style="width: 1489.6px;" tabindex="-1" /><br /></p><p>&nbsp;</p><p><span class="___164yu9v ftuwxu6 f1qdqbpl fua484e f1o6l1dn fac4klo frp1kbq f3wazqe f19l72ij fcsrh55 frnyhdv fyo61pj f1spqul0 f7dkd9s fkq5uzf f1x4fozf fwl63ro f1npyoe5 f10yrmu1 f1w45tcp f1rhua56 f18c6rdl f1e7lo8u f1dpi1ry f1vs2jsm f1o6uux1 f1nu0r7q fg0t3io f1x8dyll f2yyzyc f1sjbqdg fyzb71r fh1aahx f1oktu5 f1d3652t fed2bxt fpeluho f1e76dpb f1lwmlrd f1nri12l f1d705n1 f1jrvuk2 f11h0gum f1tandro fxjdbx7 f1hva1tl fsaoqmu f1w7c29l f1uakdsb f7jsfu7 f1hz9qas f1vmprsu fbmzazh f1oojlmx fpbf6y8 fy6vjqu fuo4419 fbzygsp fnuenae fw75flx f12oply1 fvyt4us f4ki1i fyy2ueq f1w3oopj fum67ou f1j64hbx f1a9cdrb f1q6iyvy f1s5r85c f920ium fhj6euq f30elfj f1kcike0 f1byno2r f5wk2nc fo3pyhm f1m95b1n fob93lq f9myhws fwkcdud f1a3p1vp" itemtype="http://schema.skype.com/AMSImage"></span></p></span>

++++1667515759 hkharya
<p>Even when running WL on one module of CBB3, still <b><u>MC6 residency of Module0</u></b>{CBB0} becoming 0%.</p><p><br /></p><p>&nbsp;<img src="https://hsdes.intel.com/rest/binary/16029580598" style="width: 1186.08px;" tabindex="-1" /></p>

++++1667515760 hkharya
<p><b><u>Email Thread Update:</u></b></p><p><br /></p><p class="MsoNormal"><a name="_MailOriginal" target="_blank" tabindex="-1"><span lang="EN-US" style="font-size:
11.0pt;font-family:&quot;Calibri&quot;,sans-serif;mso-font-kerning:0pt;mso-ansi-language:
EN-US;mso-fareast-language:EN-IN">_____________________________________________<br />
<b>From:</b> Kharya, Harsh &lt;harsh.kharya@intel.com&gt; <br />
<b>Sent:</b> 20 January 2026 08:48 AM<br />
<b>To:</b> Melamed, Ido &lt;ido.melamed@intel.com&gt;<br />
<b>Cc:</b> Amarnath, Abhinand &lt;abhinand.amarnath@intel.com&gt;; Shashi,
Anjana &lt;anjana.shashi@intel.com&gt;; P S, Manojj
&lt;manojj.p.s@intel.com&gt;; Kumar, Abhishek7
&lt;abhishek7.kumar@intel.com&gt;; Deuskar, Devyani
&lt;devyani.deuskar@intel.com&gt;<br />
<b>Subject:</b> RE: DMR Module0 MC6 Residency<o:p></o:p></span></a></p><p class="MsoNormal"><o:p>&nbsp;</o:p></p><p class="MsoNormal"><o:p>&nbsp;</o:p></p><p class="MsoNormal">Hi Ido,<o:p></o:p></p><p class="MsoNormal"><o:p>&nbsp;</o:p></p><p class="MsoNormal"><span lang="EN-US" style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif;color:#7030A0;
mso-ansi-language:EN-US">“Do you use any module disable in your system?” – No<o:p></o:p></span></p><p class="MsoNormal"><o:p>&nbsp;</o:p></p><p class="MsoNormal">Below is the o/p: <o:p></o:p></p><p class="MsoNormal"><o:p>&nbsp;</o:p></p><p class="MsoNormal"><span style="font-family:&quot;Courier New&quot;">In [304]: sv.socket0.cbbs.computes.modules<o:p></o:p></span></p><p class="MsoNormal"><span style="font-family:&quot;Courier New&quot;">Out[304]:<o:p></o:p></span></p><p class="MsoNorm

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

- **Primary Feature**: Core C-States
- **Sub-Feature**: MC6
- **Component Path**: fw.acode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbbs.computes.modules`
- `sv.socket0.cbb0.compute0.pma0.pmsb.io_core_operating_point.core_ratio_16p67`

## Timeline

- **Submitted**: 2026-05-20 13:23:01
- **Days Open**: 1

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
