# HSD 14026619509: [DMR][X4][PM] highest_tj_max fuse is zero on all cbbs

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026619509](https://hsdes.intel.com/appstore/article-one/#/14026619509) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | jamesrow |
| **Component** | hw.fuse.xml |
| **Defect Die** | base |
| **Conclusion** | hw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 85% |
| **Feature** | Reset/Boot | 52% |
| **Sub-Feature** | Boot | — |

**Reasoning**: conclusion='hw.bug' → HW

## Root Cause Summary

QDF: Q99C

expectation: 

Highest_TJ_max is used as default TJ during boot, before pcode calculates actual TJ using sst_t_throttle values.

if zero during boot system will think it is thermal throttling

after boot risk is there is no longer a guard band for how high customers can alter TJ max running the risk of easy thermtrips

observation:

in all cbbs fuse is zero:

punit_fuses.fw_fuses_highest_tj_max=0x0

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww51.3]

Seems like fuse cbb is already in place, sysdebug will follow up with Hector to see if the there is any extra follow up is requried or just tracking

fix_ip=fuse

### Description
QDF: Q99C

expectation: 

Highest_TJ_max is used as default TJ during boot, before pcode calculates actual TJ using sst_t_throttle values.

if zero during boot system will think it is thermal throttling

after boot risk is there is no longer a guard band for how high customers can alter TJ max running the risk of easy thermtrips

observation:

in all cbbs fuse is zero:

punit_fuses.fw_fuses_highest_tj_max=0x0

### Comments (latest)
++++14614900924 dbarnett
<p class="MsoNormal">I did a quick LAVA + FLE string search for the
highest_tj_max.</p><p class="MsoNormal"><br /></p><p class="MsoNormal">In fuse equation, highest_tj_max was controlled by:</p><p class="MsoNormal" style="margin-left:.5in"><span style="font-size:10.0pt;
font-family:&quot;Calibri&quot;,sans-serif;background:yellow;mso-highlight:yellow">Dec2Hex</span><span style="font-size:10.0pt;font-family:&quot;Calibri&quot;,sans-serif">(new[]{ lineItem.<span style="background:yellow;mso-highlight:yellow">_0_T_Throttle_BF_CBB</span>.Value,
lineItem.<span style="background:yellow;mso-highlight:yellow">_1_T_Throttle_BF_CBB</span>.Value,
lineItem.<span style="background:yellow;mso-highlight:yellow">_2_T_Throttle_BF_CBB</span>.Value,
lineItem.<span style="background:yellow;mso-highlight:yellow">_3_T_Throttle_BF_CBB</span>.Value,
lineItem.<span style="background:yellow;mso-highlight:yellow">_4_T_Throttle_BF_CBB</span>.Value,
lineItem.<span style="background:yellow;mso-highlight:yellow">_0_T_Throttle_CBB</span>.Value,
lineItem.<span style="background:yellow;mso-highlight:yellow">_1_T_Throttle_CBB</span>.Value,lineItem.<span style="background:yellow;mso-highlight:yellow">_2_T_Throttle_CBB</span>.Value,
lineItem.<span style="background:yellow;mso-highlight:yellow">_3_T_Throttle_CBB</span>.Value,
lineItem.<span style="background:yellow;mso-highlight:yellow">_4_T_Throttle_CBB</span>.Value}<span style="background:yellow;mso-highlight:yellow">.Min()</span>)));<o:p></o:p></span></p><p class="MsoNormal"> <o:p></o:p></p>

<p class="MsoNormal"><o:p>&nbsp;</o:p></p>

<p class="MsoNormal">Looks like in LAVA that <span style="font-family:&quot;Calibri&quot;,sans-serif;
background:yellow;mso-highlight:yellow">*_T_Throttle_BF_CBB</span><span style="font-family:&quot;Calibri&quot;,sans-serif"> is set to 0 for the majority of QDF’s
(minus a few for X4 VV/ES1, but we haven’t seen those yet so not relevant
here). Additionally, I double checked and am reading 0’s for highest_tj_max in
our FLE files for X1 VIS and ES0.<o:p></o:p></span></p><p class="MsoNormal"><span style="font-family:&quot;Calibri&quot;,sans-serif"><br /></span></p><p class="MsoNormal"><img src="https://hsdes.intel.com/rest/binary/14026602914" style="width: 25%;" tabindex="-1" data-processed="true" /><span style="font-family:&quot;Calibri&quot;,sans-serif"><br /></span></p>

<p class="MsoNormal"><span style="font-family:&quot;Calibri&quot;,sans-serif">&nbsp;</span></p>

<p class="MsoNormal"><span style="font-family:&quot;Calibri&quot;,sans-serif">Snippet from X1 VIS xml that I had:<br />
</span>name=&quot;punit_fuses.fw_fuses_highest_tj_max&quot;
ram_address=&quot;0xb0a&quot; start_bit=&quot;0x7&quot;
shared=&quot;False&quot; write=&quot;True&quot; value=&quot;0x00&quot; /&gt;</p><p class="MsoNormal"><o:p><br /></o:p></p><p class="MsoNormal"><o:p><br /></o:p></p>

++++14614900925 bdbrock
<p>this needs to promote -- we should have a set value (at least the default 105C) for highes

### Tags
FV_PM,SysDebugCloned,SysDebugCloned,SysDebugDccbDone,FIX_FUSE_UCC_A0_Y26W03P0

### Conclusion
hw.bug

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

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2025-12-17 00:16:21
- **Root Caused**: 2025-12-17 22:46:53
- **Closed**: 2026-05-12 23:44:07
- **Days Open**: 146

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
