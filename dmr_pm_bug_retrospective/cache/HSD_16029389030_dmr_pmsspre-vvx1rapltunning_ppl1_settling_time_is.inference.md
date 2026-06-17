# HSD 16029389030: [DMR_PMSS][Pre-VV][X1][RAPL][tunning]: PPL1 settling time is high (~15 sec) irrespective of the TW

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029389030](https://hsdes.intel.com/appstore/article-one/#/16029389030) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | kumara7 |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Power/RAPL | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Issue :  PPL1 settling time is high (~15 sec) irrespective of the TW.

Expectation is that the RAPL limit should be honored within ~5 times x TW hence if TW=1 then it should settle within ~5S and if TW=5 then it should settle within ~25S but in both the cases it takes ~15S to settle.

System - jf53nor09bn0306.amr.corp.intel.com

IFWI - OKSDCRB1.86B.0029.D50.2511162333

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww50.3]

Abhinand and Suman reported that setting platform PL1 to low values resulted in convergence times up to 17 seconds, while other PIDs converged much faster, and shared measurement data for comparison.

Timothy and Stanley emphasized that the issue is likely due to PID tuning, which should be addressed by the Primecode and debug teams, and that functional validation should include response time requirements.

### Description
Issue :  PPL1 settling time is high (~15 sec) irrespective of the TW.

Expectation is that the RAPL limit should be honored within ~5 times x TW hence if TW=1 then it should settle within ~5S and if TW=5 then it should settle within ~25S but in both the cases it takes ~15S to settle.

System - jf53nor09bn0306.amr.corp.intel.com

IFWI - OKSDCRB1.86B.0029.D50.2511162333

### Comments (latest)
++++22611630297 agraback
All PIDS (incl. RAPL) have not been tuned on DMR yet and are still using the values from GNR. PID tuning should be completed first to see if it resolves this issue
++++14614887236 vwang
[CloneScript] Sighting [sighting_central.sighting.id=16029389030] of [component=fw.primecode] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [feature] to [server.bugeco.id=14026593309] of [component=soc.PrimeCode 2.0#] in [release=dmrhub-a0]

++++14614889267 smakine1
PM PTP team will tune all PIDs and this work hasn't started yet.
++++22611775918 agraback
Can this be re-tested with UP 990 that has the NN PID change? Would be good to see how that changes this behavior to better scope future tuning excercises
++++1566848137 kumara7
I have tried the test patch in two systems and below are the settling time with default Time Window - [root@sr20dml004s0203 pmutil]# dmidecode -s bios-version OKSDCRB1.IPC.0031.D94.2601260626 [root@sr20dml004s0203 pmutil]# rdmsr 0x8b 8003099000000000 [root@sr20dml004s0203 pmutil]#
++++22611802621 agraback
Need confirmation from PTP team and/or PM Arch if these time windows are sufficient or more tuning needs to be done at this time.
++++1667352786 kumara7 
 @Grabacki, Alex I am observing new problem with latest patches - After applying newer patches (UP 991 & 993), the RAPL power limits (PL1/PL2/PPL1/PPL2) are not being fully honored. For example, setting PL1=380W does not result in the package power settling at 380W, even after waiting 2-3 minutes. Instead, the package power fluctuates by 5-15W above or below the set limit. Experiment data - [root@dmr-bkc pmutil]# ./pmutil_bin -set_pl1_tpmi 380                                           -------> Set PL1 = 380W [root@dmr-bkc pmutil]# ./pmutil_bin -get_pl1_tpmi For Partition0 Socket0 PL1: 380W For Partition1 Socket0 PL1: 0W Pkg0 power: 392.62,DRAM0 power: 21.76,Platform0 power: 775.91,                     -------> Package power is fluctuating in the range of ~385-400W Pkg0 power: 393.81,DRAM0 power: 22.03,Platform0 power: 777.90, Pkg0 power: 392.64,DRAM0 power: 22.41,Platform0 power: 777.03, Pkg0 power: 392.30,DRAM0 power: 21.83,Platform0 power: 775.91, Pkg0 power: 401.08,DRAM0 power: 23.05,Platform0 power: 786.89, Pkg0 power: 385.85,DRAM0 power: 22.65,Platform0 power: 769.90, Pkg0 power: 400.76,DRAM0 power: 23.09,Platform0 power: 785.91, Pkg0 power: 386.02,DRAM0 power: 21.81,Platform0 power: 768.91, Pkg0 power: 400.46,DRAM0 power: 22.25,Platform0 power: 785.90, [root@dmr-bkc pmutil]# ./pmutil_bin -set_pl1_tpmi 350                                           -------> Set PL1 = 350W [root@dmr-bkc pmutil]# ./pmutil_bin -get_pl1_tpmi For Partition0 Socket0 PL1: 350W For Partition1 Socket0 PL1: 0W Pkg0 power: 357.84,DRAM0 power: 21.35,Platform0 power: 738.89,                    -------> Package power is fluctuating around ~358W Pkg0 power: 358.76,DRAM0 power: 21.73,Platform0 power: 740.90, Pkg0 power: 358.01,DRAM0 power: 21.44,Platform0 power: 738.91, Pkg0 powe

### Tags
SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_60000994,FIX_IFWI_DMR_AP1_2026.10.4.01,FIX_BKC_OKS_DMR_AP1_2026WW12

### Conclusion
fw.arch

### Component
fw.primecode

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
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2025-12-08 18:26:36
- **Root Caused**: 2025-12-11 07:51:19
- **Closed**: 2026-03-23 20:28:12
- **Days Open**: 105

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
