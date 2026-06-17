# HSD 16029019388: [DMR][X1 A0][RACL] PLR reporting Thermal(CDYN2) and Frequency as causes along with RACL with some TDC limits when RACL Sweep is executed.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029019388](https://hsdes.intel.com/appstore/article-one/#/16029019388) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | salmanha |
| **Component** | fw.acode |
| **Defect Die** | compute |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Tools | 52% |
| **Sub-Feature** | collateral | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Collaterals
:

Platform
: JF53NOR09BN0304.amr.corp.intel.com

IFWI
: 
 

\\
amr.corp.intel.com
\ec\proj\debug\DMR\User\coramire\BIOS\OKSDCRB1_86B_2025.41.3.01_2817.D06_60000970_0.627.0_1P0_NonIPClean_Trace_DebugSigned.bin

Workload  -->  ./ptat -ct 5 

Summary
:

Observing 
Frequency
 and 
Thermal
 as Coarse Grain Cause with 
CDYN2
 as fine grain cause when RACL is Throttling.

PEM is rot reporting these causes.

2025-10-17 07:19:15,689:INFO
	
:########################Setting TDC limit to 33 A##

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww51.3]

Current IFWI provided in the comments is not booting, JustinG/AnjanaS are helping with creating the IFWI. Next step, once the IFWI is created provided results on the HSD 

[25ww50.4]

Salman will start email conversation with aCode team and copy sysdebug to follow up on the inputs. Need POC for aCode, Vidar will add them to mail start with Roy

[25ww47.3]

No representatives attended to updated on this sighting. Sysdebug to follow up offline.

[25ww47.1]

Salman confirmed, Orna/Anatoli's patch has no impact on our issue.  pCode team needs to debug further.

[25ww46.4]

Orna explained that a bug in pCode caused the thermal bit to be set only in the coarse grain PLR report and not in the fine grain section, which was identified and a correction was provided; however, Orna noted uncertainty about whether other issues exist beyond this bug.

James discussed the observed mismatch between PEM status and PLR status, with James clarifying that PEM bits are only set and never cleared by pCode, and that software or OS may be responsible for clearing the PEM register, leading to discrepancies.

Orna agreed that the PEM feature is incorrectly implemented in pCode, with counters incrementing when status bits are zero and the logic for excursions not following the specification; the team initiated plans to coordinate a reimplementation with the pCode team, identifying .

James and Salman discussed testing patches to address the issues, with Salman attempting to flash a test image and encountering system issues, and James offering to run experiments to confirm if thermal events are being correctly reported and to help debug the root cause.

Hector M suggested to hold off on promoting new presightings related to PLR and PEM until the implementation is corrected, with Vidar planning to start an email thread with the pCode lead to coordinate the fix.

[25ww45.1]

Debugging issues related to PLR and PEM reporting inconsistencies, possibly linked to thermal bits and TDC lim

### Description
Collaterals
:

Platform
: JF53NOR09BN0304.amr.corp.intel.com

IFWI
: 
 

\\
amr.corp.intel.com
\ec\proj\debug\DMR\User\coramire\BIOS\OKSDCRB1_86B_2025.41.3.01_2817.D06_60000970_0.627.0_1P0_NonIPClean_Trace_DebugSigned.bin

Workload  -->  ./ptat -ct 5 

Summary
:

Observing 
Frequency
 and 
Thermal
 as Coarse Grain Cause with 
CDYN2
 as fine grain cause when RACL is Throttling.

PEM is rot reporting these causes.

2025-10-17 07:19:15,689:INFO
	
:########################Setting TDC limit to 33 A#################################

2025-10-17 07:19:15,696:CRITICAL
	
:svos

2025-10-17 07:19:15,697:INFO
	
:Sleeping for 5.000000000 seconds

2025-10-17 07:19:20,698:INFO
	
:TDC changed to 0x21 A

2025-10-17 07:19:20,708:INFO
	
:Core Frequency = 400.0 Ghz and PID =2

2025-10-17 07:19:20,708:INFO
	
:Testing HPM communication 

2025-10-17 07:19:20,709:INFO
	
:RACL HPM (imh0) value: 3

2025-10-17 07:19:20,710:ERROR
	
:Mismatch in RACL HPM values for CBB 0x4 : expected 3, got 0x4

2025-10-17 07:19:20,715:CRITICAL
	
:svos

2025-10-17 07:19:20,715:INFO
	
:Sleeping for 5.000000000 seconds

2025-10-17 07:19:25,718:INFO
	
:RACL LIMIT is Throttled

2025-10-17 07:19:25,719:INFO
	
:RACL perf_status is increasing, delta = 3935

2025-10-17 07:19:25,719:INFO
	
:PEM any counter & PEM RACL counter is increasing, any_delta = 8051, racl_delta = 8052

2025-10-17 07:19:25,720:INFO
	
:PEM status is reporting ANY and RACL: 0x400001

2025-10-17 07:19:25,721:INFO
	
:PLR Coarse Level: ['
FREQUENCY
', 'CURRENT', '
THERMAL
'],  PLR Fine Level:['RACL', '
CDYN2
']

2025-10-17 07:19:25,721:INFO
	
:CURRENT coarse PLR bit set

2025-10-17 07:19:25,721:INFO
	
:RACL FINE PLR bit set

2025-10-17 07:19:25,721:INFO
	
:Core Frequency = 400.0 Ghz and PID =2

2025-10-17 07:19:25,722:INFO
	
:Testing TDC convergence 

2025-10-17 07:19:25,723:INFO
	
:TDC changed to 0x6a A

2025-10-17 07:19:25,723:INFO
	
:Setting TDC time_window = 1564 

2025-10-17 07:19:25,724:CRITICAL
	
:svos

2025-10-17 07:19:25,724:INFO
	
:Sleeping fo

### Comments (latest)
++++1667082261 sumanku2
[CloneScript] Sighting 16029019388 cloned from PreSighting 16028942262
++++14614765606 jjhingra
Can you please share the pcudata dump on IMH and CBB and if possible a CBB ptracker around the RACL event where PEM/ PLR are not reporting expected values.
++++22611557686 salmanha
Hi  @Jhingran, Jayati  Please find logs in attachments: 1) IMH PCUDATA dump when RACL TDC limit=33, PLR is reporting ['FREQUENCY', 'CURRENT', 'THERMAL'] --> plr_imh0_tdc_33.log 2) CBB PCUDATA dump when RACL TDC limit=33, PLR is reporting ['FREQUENCY', 'CURRENT', 'THERMAL']    --> plr_cbb0_tdc_33.log 3) CBB Punit Traces dump when RACL TDC limit=33, PLR is reporting ['FREQUENCY', 'CURRENT', 'THERMAL']   --> dmr_cbb_plr_triggered.csv
++++1363449985 osumszyk
As we know we have a problem with the CDYN bits because Acode implemented per ICCP license instead of per CDYN level. They need to correct, see 13013704192 - PUSH from CLIENT: [PLR] DMR PLR bug - FREQ_ICCPx / FREQ_CDYNx. About FREQUENCY it comes probably from Acode. THERMAL comes from Acode or EMTTM. Please print also the content of ACP_PERF_LIMIT register which is the Acode report read by PCode. There is one such register per CCP.

++++1363449990 osumszyk
By the way, you should be aware that PEM STATUS is writable and all bits can be cleared in it. Maybe you have SW writing to it during your experiment? From DMR CBB TPMI support Name PEM_STATUS Offset 0xCD90 Size 64-bit Description PEM Status Register Bits Access Default Description 31:0 RW 0 PEM_STATUSWhen read, return the current PEM Status register. When write, Software provides value to override PEM Status register. The reserved bits in PEM_STATUS are ignored by pcode. 63:32 RW 0 RSVDReserved
++++1667112334 salmanha
Hi  @Sumszyk, Orna  Please find status for ACP_PERF_LIMIT with different values of TDC. For Reference: sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit     0x00000000 : rsvd1 (31:22) (rw/v) -- RSVD     0x00000000 : freq_iccp5 (21:21) (rw/v) -- Set if WP4[ICCP-5].F less than WP1.F and WP4[ICCP-5] less than ICCP-5 P0. Corresponds to Frequency CG reason.     0x00000000 : freq_iccp4 (20:20) (rw/v) -- Set if WP4[ICCP-4].F less than WP1.F and WP4[ICCP-4] less than ICCP-4 P0. Corresponds to Frequency CG reason.     0x00000000 : freq_iccp3 (19:19) (rw/v) -- Set if WP4[ICCP-3].F less than WP1.F and WP4[ICCP-3] less than ICCP-3 P0. Corresponds to Frequency CG reason.     0x00000000 : freq_iccp2 (18:18) (rw/v) -- Set if WP4[ICCP-2].F less than WP1.F and WP4[ICCP-2] less than ICCP-2 P0. Corresponds to Frequency CG reason.     0x00000000 : freq_iccp1 (17:17) (rw/v) -- Set if WP4[ICCP-1].F less than WP1.F and WP4[ICCP-1] less than ICCP-1 P0. Corresponds to Frequency CG reason.     0x00000000 : freq_iccp0 (16:16) (rw/v) -- Set if WP4[ICCP-0].F less than WP1.F and WP4[ICCP-0] less than ICCP-0 P0. Corresponds to Frequency CG reason.     0x00000000 : rsvd0 (15:10) (rw/v) -- RSVD     0x00000001 : valid (09:09) (rw/v) -- Acode always se

### Tags
FV_PM,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_60000987,FIX_IFWI_DMR_AP1_2026.02.3.01,BKC#OKS_DMR_AP_X1_2026WW04,FIX_BKC_OKS_DMR_AP1_2026WW04

### Conclusion
fw.bug

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

- **Primary Feature**: Tools
- **Sub-Feature**: collateral
- **Component Path**: fw.acode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI support`
- `TPMI register`
- `sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit`
- `sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.command`
- `sv.socket0.cbb0.base.tpmi.plr_mailbox_data`
- `sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.run_busy`
- `sv.socket0.cbb0.base.tpmi.plr_mailbox_data.get_value`

## Timeline

- **Submitted**: 2025-10-30 17:08:30
- **Root Caused**: 2026-01-12 20:23:08
- **Closed**: 2026-01-13 19:45:20
- **Days Open**: 75

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
