# HSD 16029019452: [DMR][X1 A0][RACL] PEM not reporting correct causes for some TDC limits when RACL Sweep is executed.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029019452](https://hsdes.intel.com/appstore/article-one/#/16029019452) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | salmanha |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.arch |

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

PEM Status register is sometimes not capturing RACL as cause of throttling.

PEM RACL counters and PEM ANY Counter is incrementing but PEM_STATUS is not showing cause for ANY and RACL.

2025-10-17 07:17:40,258:INFO
	
:##################

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww45.1]

Context: Debugging issues related to PLR and PEM reporting inconsistencies, possibly linked to thermal bits and TDC limits.

Alex and Jayati observed anomalies in reporting when sweeping through different RACL limits.

PLR and PEM status reporting may involve aCode and pCode interactions; limits seem to be sent correctly from Primecode to pCode.

Extra anomalies could be tied to other open issues (thermal bits, PLR).

Salman provided PCU data and pTracker; same logs attached to both sightings since issues occurred simultaneously.

pTracker data exists but may need decoding for clarity.

Anatoli will ask Orna (feature owner) to review pTracker format and validate data.

Joe Brooks (SLD) remains listed as owner; Vidar to follow up offline.

Investigation should include cross-product debug and firmware review.

Anjana noted thermal reporting at PLR die level similar to other issues.

James confirmed fine-grain thermal bits flipping during tests, adding complexity.

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

PEM Status register is sometimes not capturing RACL as cause of throttling.

PEM RACL counters and PEM ANY Counter is incrementing but PEM_STATUS is not showing cause for ANY and RACL.

2025-10-17 07:17:40,258:INFO
	
:########################Setting TDC limit to 34 A#################################

2025-10-17 07:17:40,265:CRITICAL
	
:svos

2025-10-17 07:17:40,266:INFO
	
:Sleeping for 5.000000000 seconds

2025-10-17 07:17:45,267:INFO
	
:TDC changed to 0x22 A

2025-10-17 07:17:45,271:INFO
	
:Core Frequency = 1100.0 Ghz and PID =6

2025-10-17 07:17:45,272:INFO
	
:Testing HPM communication 

2025-10-17 07:17:45,272:INFO
	
:RACL HPM (imh0) value: 5

2025-10-17 07:17:45,273:INFO
	
:RACL HPM values match for CBB 0x5 : expected 5, got 0x5

2025-10-17 07:17:45,279:CRITICAL
	
:svos

2025-10-17 07:17:45,279:INFO
	
:Sleeping for 5.000000000 seconds

2025-10-17 07:17:50,284:INFO
	
:RACL LIMIT is Throttled

2025-10-17 07:17:50,284:INFO
	
:RACL perf_status is increasing, delta = -39425

2025-10-17 07:17:50,284:INFO
	
:PEM any counter & PEM RACL counter is increasing, 
any_delta = 7198
, 
racl_delta = 7198

2025-10-17 07:17:50,284:ERROR
	
:
PEM status test is failing: 0x0

2025-10-17 07:17:50,284:INFO
	
:PLR Coarse Level: ['FREQUENCY', 'CURRENT', 'THERMAL'],  PLR Fine Level:['RACL', 'CDYN2']

2025-10-17 07:17:50,284:INFO
	
:CURRENT coarse PLR bit set

2025-10-17 07:17:50,285:INFO
	
:RACL FINE PLR bit set

2025-10-17 07:17:56,699:INFO
	
:########################Setting TDC limit to 37 A#################################

2025-10-17 07:17:56,702:CRITICAL
	
:svos

2025-10-17 07:17:56,702:INFO
	
:Sleeping for 5.000000000 seconds

2025-10-17 07:18:01,703:INFO
	
:TDC changed to 0x25 A

2025-10-17 07:18:01,706:INFO
	
:Core Frequ

### Comments (latest)
++++1667082275 sumanku2
[CloneScript] Sighting 16029019452 cloned from PreSighting 16028942239
++++14614765643 jjhingra
Can you please share the pcudata dump on IMH and CBB and if possible a CBB ptracker around the RACL event where PEM/ PLR are not reporting expected values.
++++22611557685 salmanha
Hi  @Jhingran, Jayati  Please find logs in attachments: 1) IMH PCUDATA dump when RACL TDC limit=42, PEM RACL Counters are incrementing, PEM STATUS = 0 --> pem_imh0_tdc_43.log 2) CBB PCUDATA dump when RACL TDC limit=42, PEM RACL Counters are incrementing, PEM STATUS = 0  --> pem_cbb_tdc_43.log 3) CBB Punit Traces dump when RACL TDC limit=42, PEM RACL Counters are incrementing, PEM STATUS = 0 --> dmr_cbb_pem_triggered.csv
++++1363449982 osumszyk
As we know we have a problem with the CDYN bits because Acode implemented per ICCP license instead of per CDYN level. They need to correct, see 13013704192 - PUSH from CLIENT: [PLR] DMR PLR bug - FREQ_ICCPx / FREQ_CDYNx. About FREQUENCY it comes probably from Acode. THERMAL comes from Acode or EMTTM. Please print also the content of ACP_PERF_LIMIT register which is the Acode report read by PCode. There is one such register per CCP.

++++1363449988 osumszyk
By the way, you should be aware that PEM STATUS is writable and all bits can be cleared in it. Maybe you have SW writing to it during your experiment? From DMR CBB TPMI support Name PEM_STATUS Offset 0xCD90 Size 64-bit Description PEM Status Register Bits Access Default Description 31:0 RW 0 PEM_STATUSWhen read, return the current PEM Status register. When write, Software provides value to override PEM Status register. The reserved bits in PEM_STATUS are ignored by pcode. 63:32 RW 0 RSVDReserved

++++1363452227 osumszyk
Please try to print pcode variable pem_telemetry.pem_status_average[22] during your experiment. This is the EWMA (exponential weighted moving average) for the RACL report in PLR fine grain status. Only when it exceeds the threshold 0.9. the bit for RACL is reported in PEM status.
++++1667094752 salmanha
Platform: SC00901159H0033.amr.corp.intel.com IFWI: \\amr.corp.intel.com\ec\proj\debug\DMR\User\coramire\BIOS\OKSDCRB1_86B_2025.44.2.02_0028.D87_60000978_MMC0.643.0_1P0_NonIPClean_Trace_DebugSigned.bin Full logs in attachments: pem_plr_test.txt TDC_LIMIT PEM_ANY_COUNTER PEM_RACL_COUNTER PEM_STATUS_AVERAGE PEM_STATUS PLR_STATUS ACP_PERF_LIMIT 27A 210244 -->  212264 210252 -->  212273 1.000000 : at22 0x400001 0x40000000000002 acp_perf_limit["fid_232"]=0x200 acp_perf_limit["fid_216"]=0x200 acp_perf_limit["fid_192"]=0x200 acp_perf_limit["fid_136"]=0x200 acp_perf_limit["fid_96"]=0x200 acp_perf_limit["fid_72"]=0x200 acp_perf_limit["fid_56"]=0x200 acp_perf_limit["fid_48"]=0x200 28A 212399 -->  214419 212407 -->  214428 1.000000 : at22 0x400001 0x40000000000002 acp_perf_limit["fid_8"]=0x200 acp_perf_limit["fid_24"]=0x200 acp_perf_limit["fid_56"]=0x200 acp_perf_limit["fid_96"]=0x200 acp_perf_limit["fid_120"]=0x200 acp_perf_limit["fid_160"]=0x200 acp_perf_

### Tags
FV_PM,SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_6000098D,FIX_IFWI_DMR_AP1_2026.05.4.01,BKC#OKS_DMR_AP_X1_2026WW08,FIX_BKC_OKS_DMR_AP1_2026WW07, PSF=Y

### Conclusion
fw.arch

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

- **Primary Feature**: Tools
- **Sub-Feature**: collateral
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI support`
- `sv.socket0.cbb0.base.tpmi.pem_control.show`

## Timeline

- **Submitted**: 2025-10-30 17:11:38
- **Root Caused**: 2025-11-17 22:44:23
- **Closed**: 2026-02-04 19:32:19
- **Days Open**: 97

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
