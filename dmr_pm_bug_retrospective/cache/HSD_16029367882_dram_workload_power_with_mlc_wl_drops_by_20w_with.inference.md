# HSD 16029367882: DRAM Workload Power with MLC WL drops by ~20W with PrimeCode "6000097b00000000" compared to the previous one "6000097900000000"

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029367882](https://hsdes.intel.com/appstore/article-one/#/16029367882) |
| **Status** | rejected.merged |
| **Priority** | 3-medium |
| **Owner** | kumara7 |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Power/RAPL | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

Test :

16028804459-22021669501-PMSS-DRAM_RAPL-_Different_DRAM_throttling_time_window_Oak_Stream_Platform_1_DMR-PD013-611_CentOS

Logs : 
More info

System: 
fl31ca102nn0305

BKC :WW47 

========================= Step-7 Started =========================

Step-7 Name: Measured power should be equal to DRAM PL limit for socket

==================================================================

[INFO]
 2025-11-27 20:46:06,441 
[tests.contents.powermanagement.rapl.dram_rapl.dram_throttling_time_win

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww50.3]

Alex clarified that the big hammer, medium, and small hammer VN credit workarounds are now disabled by default, stabilizing DRAM power, and suggested closing or merging the sighting for tracking purposes.

### Description
Test :

16028804459-22021669501-PMSS-DRAM_RAPL-_Different_DRAM_throttling_time_window_Oak_Stream_Platform_1_DMR-PD013-611_CentOS

Logs : 
More info

System: 
fl31ca102nn0305

BKC :WW47 

========================= Step-7 Started =========================

Step-7 Name: Measured power should be equal to DRAM PL limit for socket

==================================================================

[INFO]
 2025-11-27 20:46:06,441 
[tests.contents.powermanagement.rapl.dram_rapl.dram_throttling_time_window: test_dram_throttling_time_window: 213]
: Measured power should be equal to DRAM PL limit for socket 0

[ERROR]
 2025-11-27 20:46:06,458 
[kayak.core.case_template.kayak_pre_post_action_plugin: log_test_outcome: 72]
: Test FAILED: tests/contents/powermanagement/rapl/dram_rapl/dram_throttling_time_window.py::TestDRAMThrottlingTimeWindow::test_dram_throttling_time_window

[INFO]
 2025-11-27 20:46:06,458 
[kayak.core.case_template.kayak_pre_post_action_plugin: log_test_outcome: 73]
: Test Failed in 4455.625886999973s

[ERROR]
 2025-11-27 20:46:06,458 
[kayak.core.case_template.kayak_pre_post_action_plugin: pytest_exception_interact: 301]
: self = 
<tests
.
contents
.
powermanagement
.
rapl
.
dram_rapl
.
dram_throttling_time_window
.
TestDRAMThrottlingTimeWindow
 
object
 
at
 
0x0000012B69FB8B90

>

pmss_power = 
<kayak
.
domains
.
pmss
.
power
.
programs
.
dmr
.
DMRPowerLib
 
object
 
at
 
0x0000012B0F4BBFD0

>

    @pytest.mark.prepare_sut_state(action=Boot2OS())

    @pytest.mark.testcase(id=name)

    def test_dram_throttling_time_window(self, pmss_power: PowerCommonlib):

        &quot;&quot;&quot;Test method for verifying DRAM throttling time window functionality.

    

        This method sets various BIOS knobs, reads and writes DRAM power limits,

        launches workloads, and verifies the power limits.

    

        Args:

            pmss_power (PowerCommonlib): The power management library instance.

    

        &quot;&quot;&quot;

        online_cores = pm

### Comments (latest)
++++1667159317 aamarna1
 @Grabacki, Alex  - We have narrowed down this behaviour to a primecode patch difference being between PO branch v/s IMH1 VV branch.  Below table highlights the regression results for same test.  Summary :  On primecode 97b onwards the same MLC workload on same system for some reason has lower bandwidth on memory controller PCM output shows very less bandwidth it seems like reads / writes into the memory are slow. IMH Mem frequency doesn't matter as passing or failing case uncore freq is 800MHz , due to less reads and writes power on DRAM is lower 
++++22611620504 agraback
I suspect this could be due to the VN Credit "Big Hammer" WA being enabled by default starting with UP 97B primecode. Could you try with UP 97F that has it disabled by default to see if the behavior improves?
++++1667161455 kumara7
 @Grabacki, Alex Issue is not observed with UP 97F, DRAM Power with MLC WL is back to the level where it used to be before.  DRAM Power is 54W when PL1=TDP Core    CPU     Bzy_MHz IPC     IRQ     CoreTmp PkgTmp  PkgWatt RAMWatt UMHz0.0 UMHz2.0 UMHz2.1 UMHz4.0 UMHz4.1 -       -       2200    0.55    6127    40      44      98.29   54.90   2200    800     800     800     800 4       0       2200    0.01    1006    40      44      98.29   54.90   2200    800     800     800     800 5       1       2200    0.78    1054    39 16      2       2200    0.66    1004    38 17      3       2200    0.65    1004    36 28      4       2200    0.45    1052    22 29      5       2200    0.72    1007    26 DRAM Power is 39W when PL1=0 Core    CPU     Bzy_MHz IPC     IRQ     CoreTmp PkgTmp  PkgWatt RAMWatt UMHz0.0 UMHz2.0 UMHz2.1 UMHz4.0 UMHz4.1 -       -       2200    0.27    6127    38      41      96.92   39.21   2200    800     1800    800     1800 4       0       2200    0.03    1006    38      41      96.92   39.21   2200    800     1800    800     1800 5       1       2200    0.33    1053    37 16      2       2200    0.32    1004    37 17      3       2200    0.32    1005    35 28      4       2200    0.29    1053    21 29      5       2200    0.33    1006    25 System - jf53nor09bn0306.amr.corp.intel.com IFWI - OKSDCRB1.86B.0029.D50.2511162333 UP - 6000097f00000000
++++22611623654 agraback
Ok that's good. The Big Hammer WA is not expected to come back or be enabled by default any more. If you want to get an idea on the future w/a impact, you can enable the "small hammer w/a aka recipe 3d".  Path to that variable in pythonsv should be something like: sv.socket0.imhs.pcudata.reset_persistent.enable_specific_ubr_vn_credit_wa = 0x2 then run the workload. The final official w/a is trending to be recipe 5 which is just a tweaking of the settings from 3d.
++++14614877518 jesussal
14025848487 (related-link) - link(s) are added via link tab.
++++1667167725 kumara7
@Grabacki, Alex I have tested the impact of small hammer w/a. I used 29.D89 IFWI which had UP 8000097f00000000. Power and frequency are scaling properly and they stay stable without s

### Conclusion
no_root_cause.rejected

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

### BIOS
- `BIOS knob`

## Key Registers

- `TPMI interface`
- `sv.socket0.imhs.pcudata.reset_persistent.enable_specific_ubr_vn_credit_wa`

## Timeline

- **Submitted**: 2025-12-04 20:51:55
- **Closed**: 2025-12-11 07:30:36
- **Days Open**: 6

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
