# HSD 22022111812: [DMR][X4] Modules assigned as LP are resolving wrong ratios with SST TF enabled

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22022111812](https://hsdes.intel.com/appstore/article-one/#/22022111812) |
| **Status** | rejected.merged |
| **Priority** | 3-medium |
| **Owner** | lmalagon |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 45% |
| **Sub-Feature** | general | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Modules assigned as LP are resolving wrong ratios with SST TF enabled without WL, they are resolving TF LP CLIP RATIO CDYN3 and we expected to resolve TF LP CLIP RATIO CDYN0.

As we do not have WL grant license level is 1:

but acp_perf_limit is showing clipping by freq_iccp3

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww15.4]

Ido, 

Anatoli

 and Sagar discussed that there are multiple sightings(18044235100/22022111812) , possibly related to the same root cause, and emphasized the need to track each separately while sharing relevant information and patches.

Next: Ido will review the latest updates from Carlos and coordinate with Anatoli to determine if the issues are related and what further steps are needed. Vidar will provide links and facilitate communication among the teams.

﻿[26ww15.1]

Anatoli will discuss with Nati, Stan and Ido offline

﻿[26ww14.1]

Stanley explained that the ceiling type should be set to zero for server use cases, and that the architectural value is provided by aCode, but the actual fix should be implemented in pCode, pending confirmation from Nati.

Nati, as HAS owner, needs to review and confirm whether pCode can implement the required change, and if not, further investigation will be needed before proceeding.

﻿[26ww13.1]

Leonardo described experiments conducted with compute 0 enabled and disabled, noting differences in system behavior, and agreed to update Python SV and provide comparative data for Jason's analysis.

Jason requested that Leonardo perform the experiment with compute 0 enabled and disabled along updated PythonSV and, if the issue reproduces, Jason would conduct live debugging to examine the mapping and further isolate the problem.

[26ww12.4]

* Waiting for experiments - fewer modules and not using Compute 0 to get consistent data to analyze
* New Python SV has an update to see if the issue is resolved (python mapping issue).
Next Steps
* Val to update PythonSV and try to reproduce, and see the results if there is more onion peeling to do.

﻿[26ww12.3]

Python SV Mapping Issue with Compute 0 Disabled: Leonardo and Jason discussed a mapping issue in PythonSV when compute 0 is disabled, with Jason updating PythonSV to remove PMAs for disabled computes and Leonardo planning to test on a system with compute 0 enabled.

Jason update

### Description
Modules assigned as LP are resolving wrong ratios with SST TF enabled without WL, they are resolving TF LP CLIP RATIO CDYN3 and we expected to resolve TF LP CLIP RATIO CDYN0.

As we do not have WL grant license level is 1:

but acp_perf_limit is showing clipping by freq_iccp3

### Comments (latest)
++++22611778855 hmpicosm
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14027138061.
++++1363591001 osumszyk
Hi, From the log: ccp_manager.cdyn_max_level=0x4 That is Acode can choose to work on any Cdyn level between 0 and 4 included. ICCP license is not CDYN level. Please ask Acode or Arch @Abitan, Nati for detail explanation.
++++14615118594 lmalagon
 @Abitan, Nati could you please provide feedback on this? It is not expected to resolve that level when no WL is running.
++++1667315621 pragyata
We're observing the same issue 22022090529, where CLOS3/2 cores are clipped at Cdyn level-3/4 LP-clip frequency instead of Cdyn level-0 LP-clip frequency.    In PP0, All cores are operating at 600 MHz(Cdyn level-3 LP clip freq) except 2-3 modules which are operating at 1400 MHz(Cdyn level-0 LP clip freq) The issue is observed across all PP levels.
++++22611789364 mbfausto
Do we have the logs/registers and/or traces for aCode to consult?  What was aCode's assessment from ~1 week ago when provided with the data?   What are the next steps here?
++++1363597603 chenr
i am not sure i understand what is the issue here. there is no connection between ICCP license and Cdyn. acode can get a limit of the maximal Cdyn from SoC, and he can be at and cdyn level which does not cross it. can you better explain the issue you think that exist? in addition, please supply the core's PMSB resolution_control_2 CR in the "failing" module
++++14615187222 lmalagon
Attached dum for PMA9 assigned as LP and resolving CDYN3 In [55]: sv.socket0.cbb0.compute1.pma9.pmsb.resolution_control_2.show() 0x00000003 : max_cdyn_ceiling (05:02) (rw) -- Max CDYN Pcode is responsible to update sibling cores policy (aka noisy neighbor PVC) for core to apply. Configuration is dynamic and core is expec... 0x00000001 : max_min_cdyn_ceiling_type (01:01) (rw) -- Noisy neighbour: Cores Max or Min CDYN ceiling type 0x00000001 : noisy_neighbor_policy_en (00:00) (rw) -- En means, protection from noisy neighbor is enab

++++14615211172 vwang 
 @Ranel, Chen  could you check if this sighting is similar with below core PMA bug? 18044235100 - [DMR][X4] SST_CLOS_ASSOC_0.CLOS_ID_MODULE3 mapped to 2 modules
++++1363606623 chenr
Hi, in the dump i see that pmsb.slice_cfg.logical_id=0x1 to my understanding, the WP4 bug in the PMA relates only in modules that has logical_id > 15 therefore, i think is a different issue

++++1363606630 chenr
In addition, i do not understand the problem statement. i see in the dump: pmsb.resolution_control_2=0xf     pmsb.resolution_control_2.max_cdyn_ceiling=0x3 this means that core is limited Cdyn limit of 3. can someone explain the problem statement?

++++1363606720 obenor
I do not understand the issue as well. What is the problem statement. Dumps are second level of details.

++++1363608077 mmasri
@Malagon Mandujano, Leonardo @Picos Morgan, Hector M  - can you please advise on PMA/Acode open below?
++++22611810073 lmalagon
@R

### Tags
FV_PM

### Conclusion
no_root_cause.rejected

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: general
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbb0.compute1.pma9.pmsb.resolution_control_2.show`
- `sv.socket0.cbb0.compute1.module9.core0.ctap_cr_iccp_status.show`
- `sv.socket0.cbb0.compute1.pma9.pmsb.io_core_operating_point.core_ratio_16p67`

## Timeline

- **Submitted**: 2026-02-21 06:04:17
- **Closed**: 2026-04-15 05:20:20
- **Days Open**: 52

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
