# HSD 14026538676: [DMR][X1 A0][CCF PM] Observed CCF scaling SBO/CBO PMONs not as expected compared to spec

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026538676](https://hsdes.intel.com/appstore/article-one/#/14026538676) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | shijup1 |
| **Component** | hw.ccf |
| **Defect Die** | base |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Reset/Boot | 45% |
| **Sub-Feature** | general | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

When programming CBO/SBO PMON events, we see inconsistency in which pmoncounter registers show values.

For each PMON we checked using index 0 in the arrays, we consistently see some of the sv.socket0.cbb0.base.i_ccf_envX.egress_

YY
.pmoncounter registers incrementing (need to confirm if always the same i_ccf_envX and egress_YY) but not always values in sv.socket0.cbb0.base.i_ccf_envs.egress_sbo.pmoncounter

For indexes 1 through 3, we don't always see values.

In table below:  

&quot;egress_X

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww50.3]

Anh-thu described that programming both CBO and SBO together caused PMON counters to increase in both, while programming them separately resulted in expected behavior, leading to confusion about the underlying cause.

Shiju Philip explained that the new recipe involves programming the unmask register by setting the bit field rather than writing the value directly, which resolved the issue, though the team remains uncertain why the previous method failed.

The group agreed to continue working with Yuval to determine if the new recipe reflects expected behavior or if further documentation updates are needed, and to keep the severity at medium while awaiting confirmation.

[25ww50.1]

PMONs are not counting as expected, not clear if it is PMON defect or HAS defect, for which need CBB team to clarify. 
AR sysdebug to escalate, Hector/Anh to add sysdebug to mail

### Description
When programming CBO/SBO PMON events, we see inconsistency in which pmoncounter registers show values.

For each PMON we checked using index 0 in the arrays, we consistently see some of the sv.socket0.cbb0.base.i_ccf_envX.egress_

YY
.pmoncounter registers incrementing (need to confirm if always the same i_ccf_envX and egress_YY) but not always values in sv.socket0.cbb0.base.i_ccf_envs.egress_sbo.pmoncounter

For indexes 1 through 3, we don't always see values.

In table below:  

&quot;egress_XX&quot; or &quot;XX&quot; is same as CBO from excel sheet

green -> ok.  Blue/Pink -> not meeting expectation but Niv thinks possibly less worrisome.  White -> not meeting expectation and more worrisome

Last experiment Anh ran today - she programmed each index with the same event and got the following results (egress_XX[Index] is yes if any of them show values as we haven't yet confirmed the mapping on the ports):

DMR System observations:

Results were consistent between two systems with DMR AP A0 X1 fused parts.

Expectations from excel sheet (
https://docs.intel.com/documents/ClientSilicon/DMR_CBB/global/CCF/DMR_CBB_CCF.1.0.html#useful-links

   
-> Link to CBB_CCF_PMON_1.2.xlsx Excel sheet I am comparing against what we
observed)

 

 

  

  

  

  

  

  

  

  

  

  

  

  

 

 

 

 

Programming like the following but in each index:

#Frz and reset counters

sv.socket0.cbb0.base.sncu_top.sncevents.ncupmonglobalcontrol.frz = 0x1
sv.socket0.cbb0.base.i_ccf_envs.egresss.pmoncountercontrol.rst=1
sv.socket0.cbb0.base.i_ccf_envs.egress_sbo.pmoncountercontrol.rst=1
sv.socket0.cbb0.base.i_ccf_envs.egresss.pmoncountercontrol.ev_sel=0
sv.socket0.cbb0.base.i_ccf_envs.egresss.pmoncountercontrol.umask=0

#Set ID and mask

sv.socket0.cbb0.base.i_ccf_envs.egresss.pmoncountercontrol[0].ev_sel=0x24
sv.socket0.cbb0.base.i_ccf_envs.egress_sbo.pmoncountercontrol[0].ev_sel=0x24
sv.socket0.cbb0.base.i_ccf_envs.egresss.pmoncountercontrol[0].umask=1
sv.socket0.cbb0.base.i_ccf_envs.e

### Comments (latest)
++++14614859918 sasmith2
<p>Adding some of the email thread content and contacts:</p><p><br /></p><p><br /></p><p><b>Revised summary of issue by Niv:<br /></b></p><p class="MsoNormal"><b><span style="font-size:11.0pt;
mso-ligatures:none">From:</span></b><span style="font-size:11.0pt;mso-ligatures:
none"> Aharonovich, Niv &lt;<a href="mailto:niv.aharonovich@intel.com">niv.aharonovich@intel.com</a>&gt;
<br />
<b>Sent:</b> Tuesday, September 30, 2025 14:29<br />
<b>To:</b> Smith, Stephen A &lt;<a href="mailto:stephen.a.smith@intel.com">stephen.a.smith@intel.com</a>&gt;;
Stern, Chaimy &lt;<a href="mailto:chaimy.stern@intel.com">chaimy.stern@intel.com</a>&gt;;
Polishuk, Leon &lt;<a href="mailto:leon.polishuk@intel.com">leon.polishuk@intel.com</a>&gt;;
Aronov, Boris &lt;<a href="mailto:boris.aronov@intel.com">boris.aronov@intel.com</a>&gt;;
Grotas, Yossi &lt;<a href="mailto:yossi.grotas@intel.com">yossi.grotas@intel.com</a>&gt;<br />
<b>Cc:</b> Tran, Anh-thu &lt;<a href="mailto:anh-thu.tran@intel.com">anh-thu.tran@intel.com</a>&gt;;
Picos Morgan, Hector M &lt;<a href="mailto:hector.m.picos.morgan@intel.com">hector.m.picos.morgan@intel.com</a>&gt;<br />
<b>Subject:</b> RE: DMR AP A0 CCF PMON Observations<o:p></o:p></span></p><p class="MsoNormal"><o:p>&nbsp;</o:p></p><p class="MsoNormal"><span style="font-family:&quot;Aptos&quot;,sans-serif">Ok, I think I
understand.<o:p></o:p></span></p><p class="MsoNormal"><span style="font-family:&quot;Aptos&quot;,sans-serif">I can answer
some of the questions and ping Boris on the rest:<o:p></o:p></span></p><p class="MsoNormal"><span style="font-family:&quot;Aptos&quot;,sans-serif">&nbsp;</span></p><p class="MsoNormal"><span style="font-family:&quot;Aptos&quot;,sans-serif">In general, you
could compress the columns to 4 options:<o:p></o:p></span></p><ul style="margin-top:0in" type="disc">
 <li class="MsoListParagraph" style="margin-left:0in;mso-list:l0 level1 lfo2"><span style="font-family:&quot;Aptos&quot;,sans-serif;mso-fareast-font-family:&quot;Times New Roman&quot;">CBO
     Counter 0<o:p></o:p></span></li>
 <li class="MsoListParagraph" style="margin-left:0in;mso-list:l0 level1 lfo2"><span style="font-family:&quot;Aptos&quot;,sans-serif;mso-fareast-font-family:&quot;Times New Roman&quot;">CBO
     Counters 1,2,3<o:p></o:p></span></li>
 <li class="MsoListParagraph" style="margin-left:0in;mso-list:l0 level1 lfo2"><span style="font-family:&quot;Aptos&quot;,sans-serif;mso-fareast-font-family:&quot;Times New Roman&quot;">SBO
     Counter 0<o:p></o:p></span></li>
 <li class="MsoListParagraph" style="margin-left:0in;mso-list:l0 level1 lfo2"><span style="font-family:&quot;Aptos&quot;,sans-serif;mso-fareast-font-family:&quot;Times New Roman&quot;">SBO
     Counters 1,2,3<o:p></o:p></span></li>
</ul><p class="MsoNormal"><span style="font-family:&quot;Aptos&quot;,sans-serif">From what I
see, you don’t see a difference between what you call XX (which is CBOs)
counters 1,2,3 or SBO counters 1,2,3, right?<o:p></o:p></span></p>

### Tags
FV_PM

### Conclusion
not_a_bug

### Component
hw.ccf

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
- **Sub-Feature**: general
- **Component Path**: hw.ccf

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbb0.base.i_ccf_envX.egress_`
- `sv.socket0.cbb0.base.i_ccf_envs.egress_sbo.pmoncounter`
- `sv.socket0.cbb0.base.sncu_top.sncevents.ncupmonglobalcontrol.frz`
- `sv.socket0.cbb0.base.i_ccf_envs.egresss.pmoncountercontrol.rst`
- `sv.socket0.cbb0.base.i_ccf_envs.egress_sbo.pmoncountercontrol.rst`

## Timeline

- **Submitted**: 2025-12-02 09:29:41
- **Closed**: 2025-12-15 22:28:14
- **Days Open**: 13

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
