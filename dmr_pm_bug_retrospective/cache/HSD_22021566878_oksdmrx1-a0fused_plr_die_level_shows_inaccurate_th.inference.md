# HSD 22021566878: [OKS][DMR][x1-a0][fused] : PLR_DIE_LEVEL shows inaccurate Thermal Clipping reason

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22021566878](https://hsdes.intel.com/appstore/article-one/#/22021566878) |
| **Status** | rejected.merged |
| **Priority** | 3-medium |
| **Owner** | ashashi |
| **Component** | fw.acode |
| **Defect Die** | compute |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Power/RAPL | 75% |
| **Sub-Feature** | general | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Observing PLR_DIE_LEVEL showing inaccurate clipping reason as Thermal when frequency is actually not clipped.

Steps to Reproduce:

1. Boot system to OS

2. Change PL1, PL2 levels using below commands (This is due to HSD: https://hsdes.intel.com/appstore/article-one/#/article/14025816704)

./pmutil_bin -mmiow 0xF6803000 0x178 0x80878D2000158AF0

./pmutil_bin -tW SOCKET_RAPL_PL1_CONTROL -d 0x4000000000280af0

./pmutil_bin -tW SOCKET_RAPL_PL2_CONTROL -d 0x40000000010c0d20

3. Disable RACL using th

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww51.3]

Issues with booting the IFWI with this aCode, once Anjana and team get it working will provide an update

[25ww50.4]

New aCode release is getting out tentatively this week, which fixes several PLR issues, need submitter to retry with this new aCode version to see if problem is fixes. aCode fix details are provided by Vidar on comments. 

[25ww47.3]

Anjana to follow up with DTS team as feedback has not been received yet and involve Sysdebug in the conversation

[25ww47.1]

Jason explained that the NNTM model, which predicts future throttling based on DTS readings, is not tuned for low temperatures on power-on parts, leading to the thermal throttle bit being set; Steven Y and Suman identified the relevant DTS and manufacturing contacts for further investigation.

Coordination with DTS and Manufacturing Teams: Steven Y provided names of DTS and validation contacts, clarified recent manufacturing fixes for DTS calibration, and agreed to share further information, while Jason and Suman planned to follow up with these teams to obtain accurate temperature data and resolve the issue.

[25ww46.3]

Jason reported disabling turbo at runtime made the thermal event issue disappear, but re-enabling turbo did not cause the issue to return, prompting further investigation. Jason emphasized the need for a long alog trace to observe periodic thermal throttling events and work point calculations, which are infrequent and require extended trace duration. 

Anjana described difficulties in collecting trace logs due to ITH issues and ongoing collaboration with ITH support to obtain the necessary parameters for successful trace collection.

[25ww45.1]

Igal and Tamir has discussed this one and concluded this is an aCode issues.  pCode just uses use indication from aCode and aCode is not sending the correct information.

Alex raised concerns about issues being passed between firmware teams without clear ownership, suggesting that someone from the SLD team should help triage c

### Description
Observing PLR_DIE_LEVEL showing inaccurate clipping reason as Thermal when frequency is actually not clipped.

Steps to Reproduce:

1. Boot system to OS

2. Change PL1, PL2 levels using below commands (This is due to HSD: https://hsdes.intel.com/appstore/article-one/#/article/14025816704)

./pmutil_bin -mmiow 0xF6803000 0x178 0x80878D2000158AF0

./pmutil_bin -tW SOCKET_RAPL_PL1_CONTROL -d 0x4000000000280af0

./pmutil_bin -tW SOCKET_RAPL_PL2_CONTROL -d 0x40000000010c0d20

3. Disable RACL using the below command (This is due to HSD: 
https://hsdes.intel.com/appstore/article-one/#/article/22021531862)

sv.socket0.cbb0.pcode.vars.rapl.dfx_racl_disabled=1

4. Now clear the PLR DIE LEVEL using &quot;./pmutil_bin -tW PLR_DIE_LEVEL -d 0x0&quot;

5. Read back the PLR DIE LEVEL uisng &quot;./pmutil_bin -tR PLR_DIE_LEVEL&quot;

Frequency is seen clipped due to Thermal

6. Package /Core thermal MSRs 0x1b1/0x19c do not report any thermal logging

7. PEM Status do not show any thermal events

System Configuration - 32 core

BIOS: OKSDCRB1.E9I.2704.D05.2509042049

In [19]: sv.sockets.cbbs.pcode.hash_id.show()

0x34a10b73130a9ea1 : hash_id

In [20]: sv.sockets.imhs.pcudata.fwVersion.fwBuildStamp.show()

0x0000000008282025 : hi

0x0000000012032292 : lo

0x0000000008282025 : hi

0x0000000012032292 : lo

BMC: oks-2025.25.4-0-g737a7a3c6

### Comments (latest)
++++22611462529 hkharya
<p><span style="font-family: &quot;Courier New&quot;;"><b><u>High Level Summary</u></b>:</span></p><p><span style="font-family: &quot;Courier New&quot;;">-&gt; At System Idle - Seeing thermal bit set on PLR_DIE_LEVEL.</span></p><p><span style="font-family: &quot;Courier New&quot;;">-&gt; On 0x1b1{PKGC_THERM_STATUS} - We don't any thermal clipping.</span></p><p><span style="font-family: &quot;Courier New&quot;;">-&gt; On ACP_PERF_LIMIT reg don't see any bits sets.</span><span style="font-family: &quot;Courier New&quot;;"></span></p><p><br /></p><p><span style="font-family: &quot;Courier New&quot;;">acp_perf_limit=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.frequency=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.current=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.power=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.thermal=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.platform=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.pdp=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.ras=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.misc=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.qos=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.valid=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.rsvd0=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.freq_iccp0=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.freq_iccp1=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.freq_iccp2=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.freq_iccp3=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.freq_iccp4=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.freq_iccp5=0x0</span></p><p><span style="font-family: &quot;Courier New&quot;;">&nbsp; &nbsp; acp_perf_limit.rsvd1=0x0</span></p><p><br /></p><p><span style="font-family: &quot;Courier New&quot;;"><u>Scenario-1:</u></span></p><p><span style="font-family: &quot;Courier New&quot;;">At Idle, with Core C0 state only enabled- No thermal clip seen.</span></p><p><span style="font-family: &quot;Courier New&quot;;">At Idle, with Core C1&nbsp;</span><span style="font-family: &quot;Courier New&quot;;">state</span><span style="font-family: &quot;Courier New&quot;;">&nbsp

### Conclusion
no_root_cause.rejected

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

- **Primary Feature**: Power/RAPL
- **Sub-Feature**: general
- **Component Path**: fw.acode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbb0.pcode.vars.rapl.dfx_racl_disabled`
- `sv.socket0.cbb0.pcode.vars.plr.break_is_enabled`
- `sv.socket0.cbbs.base.tpmi.plr_die_level`
- `sv.socket0.cbb0.pcode.vars.plr.ring_plr.show`
- `sv.socket0.cbb0.pcode.vars.plr.ccp_plr.ats.coarse_grain_status`

## Timeline

- **Submitted**: 2025-09-12 03:35:57
- **Closed**: 2026-01-12 23:28:32
- **Days Open**: 122

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
