# HSD 14025959387: [DMR][X1 A0 PO] CBB Pcode solution for D2D and CBB QCH aggregation on IMH1 is not implemented

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025959387](https://hsdes.intel.com/appstore/article-one/#/14025959387) |
| **Status** | complete.wont_validate |
| **Priority** | 3-medium |
| **Owner** | shijup1 |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.patch.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Sideband/D2D | 80% |
| **Sub-Feature** | UCIe | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

Summary:

========

We found the CBB Pcode solution for D2D and CBB QCH aggregation on IMH1 is not implemented during PKGC6 enabling.

There is a proposed solution on IMH1 for PkgC residency issue due to aggregated D2D Q and P channels according to HAS:

https://docs.intel.com/documents/PM_DOc/src/server/dmr/pm%20features/dmr_idle_flow/dmr_pkgc.html#d2d-and-cbb-qch-aggregation

We are expecting that L1_ENTRY timer is set to 2us on DMR-B0 and 15us on DMR-A0, but we found it was 2us during A0 PO.


## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww43.1]

The HW bug of D2D PkgC6 entry (13012657577) needs a HW fix on IMH2.  But on IMH1, we have a WA that increasing the L1 entry timer from 2us to 15us. PrimeCode has done that, but not CBB pCode yet.

Based on tunning efforts we have done, with this 2us on pCode, the system can achieve maximum residency as for now.  So no need to change pCode although it is pCode bug right now.

[25ww42.1]

The team analyzed data including packet residency, B channel residency, and deny counts, determining that the combination of 15us in IMH and 2us in CBB yields the best results for the X1 part. The current default timer values provide optimal residency, and no immediate Pcode changes are requested.

Ido and Jaivardhan agreed to continue tuning other timers, will provide guidance on further adjustments, with the understanding that residency targets may change as more data is collected and as more CBBs are introduced from X4.

[25ww41.3]

Hector M and Shiju are collecting data on L1 delay for both CBB and IMH as requested by Jaivardhan, with the goal of analyzing the impact of different delay values and sharing the results for further review.

[25ww41.1]

Hector reported a 10% residency penalty when increasing L1 delay from 2us to 15us.

Hector is seeking guidance on which variables and value ranges to tune, with plans to reach out to Jaivardhan for direction, as Ido is unavailable.

Alex confirmed that the pCode implementation only included one of the necessary changes, and Vidar requested clarification and documentation of what is present and missing.

[25ww40.4]

The team discussed the need to increase the L1 entry timer value from 2us to 50us as a workaround for an IMH D2D bug, with the primeCode component updated but the pCode missing the change; Ido clarified it was an IMH D2D bug and requested confirmation from pCode team.

Hector reported a 10% reduction in packet C6 residency after the timer change, documented in the HSD, and Ido noted that packet C6 residency can b

### Description
Summary:

========

We found the CBB Pcode solution for D2D and CBB QCH aggregation on IMH1 is not implemented during PKGC6 enabling.

There is a proposed solution on IMH1 for PkgC residency issue due to aggregated D2D Q and P channels according to HAS:

https://docs.intel.com/documents/PM_DOc/src/server/dmr/pm%20features/dmr_idle_flow/dmr_pkgc.html#d2d-and-cbb-qch-aggregation

We are expecting that L1_ENTRY timer is set to 2us on DMR-B0 and 15us on DMR-A0, but we found it was 2us during A0 PO.

Impact:

========

This could result in very low residency on DMR (miss idle power targets).

Details:

========

REPLACE  with failure and triage details.

==> System configuration ...

X1 fused silicon , 32 Cores

==> BIOS/Patch/IFWI/BKC/CI Versions ...

OKSDCRB1.86B.2025.35.3.01_2688.D02_6020095E_1P0_NonIPClean_Trace_DebugSigned_update_primecode_pcode

==> Reproducibility ...

Always

==> Lightswitch discoveries ...

 None

==> Experiment results ...

In [503]: sv.sockets.cbbs.base.d2d_stacks.ucieddas.uciedda.i_dda_fdi_tmr_config_reg

Out[503]:

socket0.cbb0.base.d2d_stack_0.uciedda_0.uciedda.i_dda_fdi_tmr_config_reg - 0x00000014

socket0.cbb0.base.d2d_stack_0.uciedda_1.uciedda.i_dda_fdi_tmr_config_reg - 0x00000014

socket0.cbb0.base.d2d_stack_1.uciedda_0.uciedda.i_dda_fdi_tmr_config_reg - 0x00000014

socket0.cbb0.base.d2d_stack_1.uciedda_1.uciedda.i_dda_fdi_tmr_config_reg - 0x00000014

### Comments (latest)
++++14614648802 hmpicosm
<p class="MsoNormal"><span style="font-size:11.0pt;mso-ascii-font-family:Aptos;
mso-ascii-theme-font:minor-latin;mso-hansi-font-family:Aptos;mso-hansi-theme-font:
minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-bidi-theme-font:minor-bidi">&nbsp;</span></p>

<p class="MsoNormal"><a name="_MailEndCompose"><span style="font-size:11.0pt;
mso-ascii-font-family:Aptos;mso-ascii-theme-font:minor-latin;mso-hansi-font-family:
Aptos;mso-hansi-theme-font:minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;
mso-bidi-theme-font:minor-bidi">&nbsp;</span></a></p>



<p class="MsoNormal"><a name="_MailOriginal"><b><span style="font-size:11.0pt;
font-family:&quot;Calibri&quot;,sans-serif;mso-fareast-font-family:&quot;Times New Roman&quot;;
mso-ligatures:none">From:</span></b></a><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif;mso-fareast-font-family:
&quot;Times New Roman&quot;;mso-ligatures:none"> Mattapalli, Jaivardhan
&lt;jaivardhan.mattapalli@intel.com&gt; <br />
<b>Sent:</b> Tuesday, September 23, 2025 11:17 AM<br />
<b>To:</b> Gong, Jinwen &lt;jinwen.gong@intel.com&gt;; Picos Morgan, Hector M
&lt;hector.m.picos.morgan@intel.com&gt;; Salman, Nawaf
&lt;nawaf.salman@intel.com&gt;; Ziv, Tomer &lt;tomer.ziv@intel.com&gt;; Zvik,
Dor &lt;dor.zvik@intel.com&gt;; Odler, Anatoli &lt;anatoli.odler@intel.com&gt;;
Aizik, Yoni &lt;yoni.aizik@intel.com&gt;<br />
<b>Cc:</b> Mattapalli, Jaivardhan &lt;jaivardhan.mattapalli@intel.com&gt;<br />
<b>Subject:</b> RE: L1_ENTRY timer was set to 2us for DMR A0<o:p></o:p></span></p>

<p class="MsoNormal"><o:p>&nbsp;</o:p></p>

<p class="MsoNormal"><span style="font-size:11.0pt">L1 entry timer needs to be increased from 2us to 15us
to account for the misalignment of L1 entry attempts between IMH and CBBs.
Although we called out that the optimal value is determined post-si, the
request was to set it as 15us by default.<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">&nbsp;</span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">Thanks,<br />
Jai<o:p></o:p></span></p>

<p class="MsoNormal"><span style="font-size:11.0pt">&nbsp;</span></p>

<p class="MsoNormal"><b><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif;mso-ligatures:none">From:</span></b><span style="font-size:11.0pt;font-family:
&quot;Calibri&quot;,sans-serif;mso-ligatures:none"> Gong, Jinwen &lt;</span><a href="mailto:jinwen.gong@intel.com"><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif;mso-ligatures:none">jinwen.gong@intel.com</span></a><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif;mso-ligatures:none">&gt;
<br />
<b>Sent:</b> Saturday, September 13, 2025 11:05 AM<br />
<b>To:</b> Picos Morgan, Hector M &lt;</span><a href="mailto:hector.m.picos.morgan@intel.com"><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif;mso-ligatures:none">hector.m.picos.morgan@intel.com</span><

### Tags
FV_PM,SysDebugCloned,SysDebugDccbBypass,cov.pm.pkgc6, PSF=Y

### Conclusion
fw.patch.bug

### Component
fw.pcode

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
- **Sub-Feature**: UCIe
- **Component Path**: fw.pcode

## Firmware Touchpoints

### PCODE
- `Pcode change`

## Key Registers

- `sv.socket0.cbb0.base.d2d_stack_0.uciedda_0.uciedda.i_dda_fdi_tmr_config_reg`
- `sv.socket0.imh0.resctrl.rc_cfcmem_ew.resctrl_pblc_perfdbg_regs.perfdbg_cntr_ctrl`
- `sv.socket0.imh0.resctrl.rc_cfcmem_ew.resctrl_pblc_perfdbg_regs.perfdbg_data`

## Timeline

- **Submitted**: 2025-09-24 00:32:04
- **Root Caused**: 2025-10-22 07:24:43
- **Closed**: 2025-12-13 02:44:51
- **Days Open**: 80

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
