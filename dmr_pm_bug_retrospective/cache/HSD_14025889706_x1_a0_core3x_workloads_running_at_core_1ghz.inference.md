# HSD 14025889706: [X1 A0] Core3X workloads running at Core >= 1GHZ

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025889706](https://hsdes.intel.com/appstore/article-one/#/14025889706) |
| **Status** | rejected.merged |
| **Priority** | 2-high |
| **Owner** | srotich |
| **Component** | hw.d2d |
| **Defect Die** | compute |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 75% |
| **Feature** | PState Stack | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: errata_status='review_waived' → HW

## Root Cause Summary

This is verified on 2 different platforms

Steps to reproduce
:

Reboot the system and apply PM Magic recipe.

Run povray on all 32 cores

Using Pega tool, increase core frequency from 800MHZ and you  will see system crash at about 1GHZ:

import pm.pmutils.pega as pega 

pega.pegaPstate(sktNum='all', dieName='all', iagv=8)

Config

Platform- AN004011BMH1283.amr.corp.intel.com (PO Platform (Fused))

IFWI - 

OKSDCRB1.86B.2025.35.3.01_2688.D02_6020095E_1P0_NonIPClean_Trace_DebugSigned_update_prime

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25WW40.1]

With WA of D2D credit overflow issue, Simeon is able to run workloads successfully. 

Vidar will merge this sighting to 14025858868

[25WW39.3]

Simeon confirmed the issue was observed on multiple systems and parts and collected status scope and Axon with 3- strike disabled. The team discussed the need to identify the IP module responsible for the last step before the crash. We discussed the use of various analyzers (Auto, ERR, etc.) to interpret machine check errors, highlighting the importance of determining which module first reported the error and whether the issue was related to die-to-die training or link problems. Joseph S agreed to provide a recommended list and update the debug handbook.

Next Steps and Ownership: the team agreed to further investigate the root cause offline, with Joseph S and Danny assigned to review sideband status scope and protocol errors, and to document findings and system reproduction counts in the ticket comments.

[25WW39.1]

Systems hang at or above 1 GHz core frequency during certain workloads, with the issue reproducible across multiple systems and independent of fabric or memory frequency.  Disabling the three-strike timeout allowed the hang to be reproduced, but also introduced a separate issue where the system could not return to one-core turbo mode, remaining stuck at all-core turbo.
Simeon will collect status scope, core debug dumps and Axon, especially with 3- strike disabled.

[25ww37.5] 

* Same WL at Max Turbo is working on another unit, this failure so far is failing only on 1 part (1GHz symptom)

* Issue appears to follow the silicon (supporting 1 part issue, or intermittent/something).

* In at least 1 Axon, every core has 3-strike and a CBO MCA ... so maybe IFU MCA may not be the point failure.

* May be another part/failure with a ~2GHz wall.

* Captures on this system all have sideband hangs leading to debug difficulty if sideband WAs are not employed.

* IFU MCAs in the Status Scope, nothing in the Un

### Description
This is verified on 2 different platforms

Steps to reproduce
:

Reboot the system and apply PM Magic recipe.

Run povray on all 32 cores

Using Pega tool, increase core frequency from 800MHZ and you  will see system crash at about 1GHZ:

import pm.pmutils.pega as pega 

pega.pegaPstate(sktNum='all', dieName='all', iagv=8)

Config

Platform- AN004011BMH1283.amr.corp.intel.com (PO Platform (Fused))

IFWI - 

OKSDCRB1.86B.2025.35.3.01_2688.D02_6020095E_1P0_NonIPClean_Trace_DebugSigned_update_primecode_pcode

Measured sv.socket0.imh0.fuses.punit.pcode_tdc_current_limit =0x73 (115A)

Applied PM recipe to disable 

RACL (with RACL Enabled, core frequencies are throttled to 400MHZ)

 &quot;sv.sockets.cbbs.pcode.vars.rapl.dfx_racl_disabled=1

&quot;

and system hang.

Attaching status_scope

from diamondrapids.toolext import status_scope

status_scope.run(collectors=[&quot;namednodes&quot;], analyzers=[&quot;ccfpma&quot;, &quot;pm&quot;, &quot;pm_imh&quot;])

#1283 system 

'c:\\temp\\status_scope\\status_scope_20250905_102152.zip'

### Comments (latest)
++++14614607463 senthil1
Setting sub_forum=vt.ptp (sourcing team) until an owner is assigned&nbsp;

++++14614607464 srotich
<p>Further debug shows:</p><p>1). Frequencies are throttled due to high currents especially on high core count parts (&gt;32 core) -at idle and gets worse with workloads:</p><p><img src="https://hsdes.intel.com/rest/binary/14025880826" style="width: 666px;" /><br /></p><p>2).&nbsp; Disabling RACL (sv.sockets.cbbs.pcode.vars.rapl.dfx_racl_disabled=1) with 32C system (using thermal head); even at idle (EPB=performance) will cause frequencies to rise toP1=1.3GHZ when turbo is disabled and&nbsp; to P0n=2.2GHZ when turbo is enabled&nbsp; .</p><p>&nbsp;With turbo disabled or enabled,&nbsp; the frequency increase due to disabling RAPL limit will cause systems to hang even at idle.</p><p>The Enabled PLR (sv.socket0.cbb0.base.tpmi.plr_die_level) reads 0x9; which indicates thermal and power throttling (bit0 &amp;3).</p><p>&nbsp;</p><p><img src="https://hsdes.intel.com/rest/binary/14025880827" style="width: 50%;" data-processed="true" /><br /></p><p><!--StartFragment-->This was also confirmed by msr 0x19C (T<span style="font-style: italic; font-family: Calibri; font-size: 11pt;">HERM_STATUS&nbsp;</span><span style="font-style: italic; font-family: Calibri; font-size: 11pt;">Thermal Monitor Status)&nbsp;&nbsp;</span><span style="font-family: Calibri; font-size: 11pt;">and msr0x1b&nbsp;</span><span style="font-style: italic; font-family: Calibri; font-size: 11pt;">(</span><span style="font-style: italic; font-family: Calibri; font-size: 11pt;">A32_PACKAGE_THERM_STATUS&nbsp;</span><span style="font-style: italic; font-family: Calibri; font-size: 11pt;">Package Thermal Status Information</span><span style="font-style: italic; font-family: Calibri; font-size: 11pt;">) bits&nbsp;</span><!--EndFragment--></p><p><br /></p><p>i). when thermal head is used; the controlled cooling helps prevent hang; and core frequencies of 1.6GHZ can be sustained with povray (SPEC2017_icc18) runs.</p><p><br /></p><p>ii).&nbsp; With heat-sink, maximum core frequency sustained varies by system. Some max at 800MHZ, and others go run at 1.3GHZ for some workloads but not all.</p><p>This might violate the guaranteed P1 frequencies at right conditions (like license levels).&nbsp;</p><p><br /></p><p>3). The BIOS knob shows DMR has much lower DTS_max or 48C and 16C for 16Core parts)</p><p>Compared to GNR that has 105C for SST-PP Level0 (default)</p><p><img src="https://hsdes.intel.com/rest/binary/14025880828" width="641" height="414" /><img src="https://hsdes.intel.com/rest/binary/14025880829" width="605" height="426" /></p><p><br /></p><p><br /></p><p></p><p><br /></p><p>&nbsp;</p>

++++14614607467 ansvuser
[CloneScript] PreSighting 14025872134 cloned to Sighting 14025889706

++++14614607624 vwang 
Cleaned the component field that had wrong information. The debugging has no direction yet.
++++22611459737 cplacek
To clarify, this sighting is focused on the system (1283) 

### Tags
PTP_SoC

### Conclusion
no_root_cause.rejected

### Component
hw.d2d

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
- **Component Path**: hw.d2d

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.fuses.punit.pcode_tdc_current_limit`
- `sv.socket0.cbbs.computes.modules.cores.rat_cr_defeature2.vecfl_512bitmode`
- `sv.socket0.cbb0.base.tpmi.plr_die_level`

## Timeline

- **Submitted**: 2025-09-10 09:39:11
- **Closed**: 2025-10-01 05:05:51
- **Days Open**: 20

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
