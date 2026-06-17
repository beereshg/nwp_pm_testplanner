# HSD 16028992828: [DMR][X1 A0] [RAPL] PLATFORM_RAPL_PERF_STATUS is not Changing (Core Throttling is not Happening) for platform_consumed_power > PPL1/2 limit

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16028992828](https://hsdes.intel.com/appstore/article-one/#/16028992828) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | kumara5 |
| **Component** | fw.ifwi |
| **Defect Die** | ioe |
| **Conclusion** | fw.patch.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **BIOS** | 70% |
| **Feature** | Power/RAPL | 80% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_IFWI/FIX_BIOS → BIOS

## Root Cause Summary

Observed behavior:

Platform perf status does not update even when the platform consumed power is more than the Platform power limits set by 
BIOS knobs or CSR Write. 

Expected: 
As per HAS snippet Below, We expect Platform Perf Status to change for above test intent. Its not chnaging for the programmed PPL1/2 Limits with 

exiting CSR definition with resolution of 0.125 (0x3). We see if we program the Values with Resolution of 1W in the same Registers

, Test is OK. 

System - SC00901159H0033/

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww44.3]

Vidar will promote this to BIOS feature to push forward.

[25ww44.1]

Suman raised a new issue regarding PLATFORM_RAPL_PERF_STATUS not updating as expected, possibly due to a resolution mismatch in the CSR field (default .125W vs. expected 1W). The team discussed the impact on throttling and the need for BIOS, OSXML, and primeCode to align on the correct unit. Shreyas and Timothy clarified that prime code assumes 1W units, and any deviation is a separate bug. The group agreed to verify BIOS programming and ensure OSXML updates are in flight.

Vidar will contact the BIOS team to clarify the handshake regarding the spec change. Shreyas will locate and share the OSXML update ticket.

### Description
Observed behavior:

Platform perf status does not update even when the platform consumed power is more than the Platform power limits set by 
BIOS knobs or CSR Write. 

Expected: 
As per HAS snippet Below, We expect Platform Perf Status to change for above test intent. Its not chnaging for the programmed PPL1/2 Limits with 

exiting CSR definition with resolution of 0.125 (0x3). We see if we program the Values with Resolution of 1W in the same Registers

, Test is OK. 

System - SC00901159H0033/
SC00901159H0008

IFWI - 

OKSDCRB1.86B.2834.D10.2510170119

Confirmed on another system as well with same latest ifwi

The Perf status is not hitting even if the consumed power is far greater than the Power limit

def rapl_energy_check():

    ...:     skt_power = sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_0.consumed_power

    ...:     plt_power = sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_1.consumed_power

    ...:     drm_power = sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_2.consumed_power

    ...:     pkg_power = sv.socket0.imh0.pcudata.pkgRAPLDomain.pkg_power_consumed

    ...:     # Pack as unsigned int (4 bytes) and unpack as float

    ...:     socket_power = struct.unpack('!f', struct.pack('!I', skt_power))[0]

    ...:     platform_power = struct.unpack('!f', struct.pack('!I', plt_power))[0]

    ...:     dram_power = struct.unpack('!f', struct.pack('!I', drm_power))[0]

    ...:     package_power = struct.unpack('!f', struct.pack('!I', pkg_power))[0]

    ...:     print(&quot;socket_power =&quot;,socket_power)

    ...:     print(&quot;platform_power =&quot;,platform_power)

    ...:     print(&quot;dram_power =&quot;,dram_power)

    ...:     print(&quot;package_power =&quot;,package_power)

    ...:

In [127]: rapl_energy_check

--------> rapl_energy_check()

socket_power = 91.4091796875

platform_power = 94.3686294555664

dram_power = 0.0

package_power = 93.04032897949219

In [128]: rapl_energy_check

--------> rapl_energy_check()

socket_pow

### Comments (latest)
++++1667072704 kumara5
<p>Observation:-</p><p>Issue can be reproduced with CSR or TPMI method.</p><p>Changing the limit from BIOS knob also reproduces the issue.</p><p><br /></p><p><img src="https://hsdes.intel.com/rest/binary/16028992570" style="width: 560.594px; height: 354.968px;" data-processed="true" /><!--StartFragment--><!--EndFragment--></p><p><br /></p><p>According to the results observed till now, it is more of pointing to the resolution issue:-&nbsp;</p><ul><li>Although the power limit register is defined with a resolution of 0.125W, the actual enforcement of the power limit seems to be of 1W granularity.</li><li> As a result, the core begins to throttle and the performance status is triggered when the consumed power exceeds the power limit rounded to the nearest PPL1*(1)W instead of PPl1*(1/8) W. </li><li>Therefore, the observed throttling behavior is consistent and correct if we consider the effective power limit resolution to be 1W instead of the nominal 0.125W specified in the register.</li></ul><p><br /><!--EndFragment--></p>

++++1667072705 sumanku2
<p><!--StartFragment-->Promoting this to Sighting: Based on the Experiments and Data analyzed: The Issue is seen with BIOS, CSR and TPMI for PLATFROM RAPL PERF STATUS not changing as expected. Also we see that there seems to be change in resolution (0.125 to 1) for the Reg Definition and may need update into OSXML + BIOS Handshake as well.</p><p><br /></p><p>More information is in previous Comments from &nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Kumar,Amit6</span>&nbsp;.&nbsp;</p>

++++1667072706 sumanku2
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 16028980986.

++++1667072709 sumanku2
[CloneScript] Sighting 16028992828 cloned from PreSighting 16028980986
++++14614758620 vwang 
The approved feature "Change Psys PWR_UNIT to 1W (from 1/8W)"  needs both Primecode and BIOS changes, PRIMECODE team for 1W PWR_UNIT has been made in ww41 release, but BIOS side has not done yet. the mismatch between Primecode and BIOS causes this issue.


++++14614759490 vwang
[CloneScript] Sighting [sighting_central.sighting.id=16028992828] of [component=bios] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [feature] to [central_firmware.feature.id=14026151644] of [component=bios.uncore] in [release=bios.oakstream_diamondrapids]
++++22611554250 mbfausto
Team - what is the Feature CCB that was missing the BIOS Feature?  (Based on the 1 sentence, this shouldn't be a sighting this should be going to the CCB owner and getting the CCB-->BIOS Feature clone) unless there's more to this story ...
++++14614764265 vwang
BIOS CCB Paula has cloned below bios feature from soc feature.  BIOS team will implement the code change based on that. 14026150683 - [DMR-CCB] Change Psys PWR_UNIT to 1W (from 1/8W)

++++14614766992 srotich
we tested psys using  IFWI: IFWI:  OKSDCRB1.86B.2834.D10.2510221943 The power resolution is

### Tags
presighting_bdc,FV_PM,BIOS_MS_POWER_ON,SysDebugCloned,SysDebugDccbBypass,FIX_BIOS_OAKSTRM.0.RPB.0029.D.91,FIX_IFWI_DMR_AP1_2025.49.3.02,FIX_BKC_OKS_DMR_AP1_2025WW50, PSF=Y

### Conclusion
fw.patch.bug

### Component
fw.ifwi

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
- **Component Path**: fw.ifwi

## Firmware Touchpoints

### BIOS
- `BIOS knob`

## Key Registers

- `MSR 0x199`
- `MSR 0x198`
- `TPMI method`
- `TPMI for`
- `sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_0.consumed_power`
- `sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_1.consumed_power`
- `sv.socket0.imh0.pcudata.pwrBdgtMngr.domain_power_2.consumed_power`
- `sv.socket0.imh0.pcudata.pkgRAPLDomain.pkg_power_consumed`
- `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.platform_rapl_limit_cfg.ppl1`

## Timeline

- **Submitted**: 2025-10-27 15:13:48
- **Root Caused**: 2025-10-29 22:59:47
- **Closed**: 2026-03-11 19:01:10
- **Days Open**: 135

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
