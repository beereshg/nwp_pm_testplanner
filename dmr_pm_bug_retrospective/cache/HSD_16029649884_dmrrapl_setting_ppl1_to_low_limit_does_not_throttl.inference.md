# HSD 16029649884: [DMR][RAPL]: Setting PPL1 to low limit does not throttle the iMH1 IO Uncore freq

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029649884](https://hsdes.intel.com/appstore/article-one/#/16029649884) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | sagrawa3 |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | PState Stack | 80% |
| **Sub-Feature** | TRL | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Issue: Setting PPL1 to low limit (like 0, 100, 200) doesn't reduce the iMH1 IO freq and the IMH1 toggles between 800 and 1800.

To reproduce -

Run stress-ng iomix workload (stress-ng --cpu 0 --iomix 0 --iomix-bytes 100% -t 30m) and mlc (./mlc --peak_injection_bandwidth)

Check Core, CBB Uncore, IMH  IO/Memory freq using turbostat, all freq scales up properly.

Now, reduce PPL1=low limits (0, 100) and check all freq again, there are two observation -

All freq including iMH0 IO freq throttles to

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
root cause..

﻿[26ww09.3]

Shubham and Sagar1 reported that despite setting the wrapper limit, the frequency is not being clipped as expected. They are working together to provide additional debug variables and logs, with the issue still unresolved and under investigation.

[26ww09.1]

Debug patch 7 & 6 are ready to be tested. pending on the test result.

[26ww07.3]

Sagar provided a new patch to address all possible fixes. 

[26ww07.3]

Abhinad working with Sagar to extract more information and running pre-silicon experiments looking forward for PCUDATA variables. 

﻿[26ww07.1]

Abhinand described that, unlike previous platforms, the IMH1 IO uncore frequency remains high (1800 MHz) for several seconds even when PPL1 is set to a low limit, while other dies throttle as expected. This discrepancy was confirmed by tool outputs and further discussed with Sagar and Timothy.

Timothy explained that differences in frequency between IO dies are expected due to propagation time and slow loop intervals, which can cause temporary mismatches in throttling response between IMH0 and IMH1.

The team analyzed how the nature of the workload affects whether IO frequency is throttled, noting that if the workload is not IO-intensive, the IO frequency may remain high even under PPL1 limits, as the platform may only throttle frequencies where traffic is present.

Timothy emphasized that verification should be based on HAS, not on assumptions or common sense, and suggested that Abhinand review the relevant documentation to determine if the observed behavior constitutes a bug.

Abhinand and Sagar discussed a possible solution involving synchronization of both dies to ensure consistent throttling, but Sagar noted that perfect synchronization would negatively impact response time on the primary die, and the current issue may not be due to synchronization but something else requiring further investigation.

﻿[26ww06.3]

Sagar described how the regular UFS resolution algorithm and IO demand al

### Description
Issue: Setting PPL1 to low limit (like 0, 100, 200) doesn't reduce the iMH1 IO freq and the IMH1 toggles between 800 and 1800.

To reproduce -

Run stress-ng iomix workload (stress-ng --cpu 0 --iomix 0 --iomix-bytes 100% -t 30m) and mlc (./mlc --peak_injection_bandwidth)

Check Core, CBB Uncore, IMH  IO/Memory freq using turbostat, all freq scales up properly.

Now, reduce PPL1=low limits (0, 100) and check all freq again, there are two observation -

All freq including iMH0 IO freq throttles to min as platform power limit is reduced to very low limit but iMH1 IO still toggling between 400/800 & 1800

All freq throttles to min but both IOs keep toggling between 400/800 & 1800

In [32]: sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.ufs_control.show()

0x00000000 : rsvd4 (63:47) (rw) -- Reserved

0x00000078 : efficiency_latency_ctrl_high_threshold (46:40) (rw) -- Utilization point above which freq will be optimized to optimize latency.

0x00000001 : efficiency_latency_ctrl_high_threshold_enable (39:39) (rw) -- If set (1), EFFICIENCY_LATENCY_CTRL_HIGH_THRESHOLD is valid

0x0000000d : efficiency_latency_ctrl_low_threshold (38:32) (rw) -- This field provides the flexibility to alter the region of low power activity. It determines the region of utilization points to which the...

0x00000000 : rsvd2 (31:30) (rw) -- Reserved

0x00000000 : idle_power_ctrl_disable (29:29) (rw) -- When set this bit disables efficient power saving modes during idle scenario for the fabric.  Note that by default the mode is enabled which does impact...

0x00000008 : efficiency_latency_ctrl_ratio (28:22) (rw) -- Fabric domain frequency ratio floor while in the low power activity region determined by Efficiency_Latency_Ctrl.

0x00000004 : min_ratio (21:15) (rw) -- Min fabric domain frequency ratio

0x00000015 : max_ratio (14:08) (rw) -- Max fabric domain frequency ratio

0x00000000 : rsvd1 (07:02) (rw) -- Reserved

0x00000001 : ufs_throttle_mode (01:00) (rw) -- Select one of the UFS throttle modes

0x00

### Comments (latest)
++++1667230158 kumara7
<p><span style="font-size: 18px;">Core and uncore freq while running stress-ng iomix and mlc workload (reduced ppl1 limit in between) -</span></p><p><br /></p><p style="margin-left: 25px;"><span style="font-size: 14px; font-family: &quot;Courier New&quot;;">Core&nbsp; &nbsp; CPU&nbsp; &nbsp; &nbsp;Bzy_MHz IPC&nbsp; &nbsp; &nbsp;IRQ&nbsp; &nbsp; &nbsp;CoreTmp PkgTmp&nbsp; PkgWatt RAMWatt UMHz0.0 UMHz2.0 UMHz2.1 UMHz4.0 UMHz4.1&nbsp; &nbsp; <span style="background-color: rgb(255, 255, 0);">---&gt; IO freq before reducing PPL1 limit is 1800</span></span></p><p style="margin-left: 25px;"><span style="font-size: 14px; font-family: &quot;Courier New&quot;;">-&nbsp; &nbsp; &nbsp; &nbsp;-&nbsp; &nbsp; &nbsp; &nbsp;2683&nbsp; &nbsp; 1.60&nbsp; &nbsp; 121369&nbsp; 78&nbsp; &nbsp; &nbsp; 75&nbsp; &nbsp; &nbsp; 262.38&nbsp; 87.97&nbsp; &nbsp;2700&nbsp; &nbsp; <span style="background-color: rgb(255, 255, 0);">1800</span>&nbsp; &nbsp; 2100&nbsp; &nbsp; <span style="background-color: rgb(255, 255, 0);">1800</span>&nbsp; &nbsp; 2100</span></p><p style="margin-left: 25px;"><span style="font-size: 14px; font-family: &quot;Courier New&quot;;">0&nbsp; &nbsp; &nbsp; &nbsp;0&nbsp; &nbsp; &nbsp; &nbsp;2682&nbsp; &nbsp; 1.95&nbsp; &nbsp; 2451&nbsp; &nbsp; 62&nbsp; &nbsp; &nbsp; 75&nbsp; &nbsp; &nbsp; 262.40&nbsp; 87.98&nbsp; &nbsp;2700&nbsp; &nbsp; 1800&nbsp; &nbsp; 2100&nbsp; &nbsp; 1800&nbsp; &nbsp; 2100</span></p><p style="margin-left: 25px;"><span style="font-size: 14px; font-family: &quot;Courier New&quot;;">1&nbsp; &nbsp; &nbsp; &nbsp;1&nbsp; &nbsp; &nbsp; &nbsp;2682&nbsp; &nbsp; 1.60&nbsp; &nbsp; 2973&nbsp; &nbsp; 58</span></p><p style="margin-left: 25px;"><span style="font-size: 14px; font-family: &quot;Courier New&quot;;">4&nbsp; &nbsp; &nbsp; &nbsp;2&nbsp; &nbsp; &nbsp; &nbsp;2682&nbsp; &nbsp; 2.14&nbsp; &nbsp; 1094&nbsp; &nbsp; 61</span></p><p style="margin-left: 25px;"><span style="font-size: 14px; font-family: &quot;Courier New&quot;;">5&nbsp; &nbsp; &nbsp; &nbsp;3&nbsp; &nbsp; &nbsp; &nbsp;2682&nbsp; &nbsp; 2.17&nbsp; &nbsp; 1101&nbsp; &nbsp; 62</span></p><p style="margin-left: 25px;"><span style="font-size: 14px; font-family: &quot;Courier New&quot;;">8&nbsp; &nbsp; &nbsp; &nbsp;4&nbsp; &nbsp; &nbsp; &nbsp;2681&nbsp; &nbsp; 1.70&nbsp; &nbsp; 2573&nbsp; &nbsp; 72</span></p><p style="margin-left: 25px;"><span style="font-size: 14px; font-family: &quot;Courier New&quot;;">9&nbsp; &nbsp; &nbsp; &nbsp;5&nbsp; &nbsp; &nbsp; &nbsp;2681&nbsp; &nbsp; 1.71&nbsp; &nbsp; 2675&nbsp; &nbsp; 69</span></p><p style="margin-left: 25px;"><span style="font-size: 14px; font-family: &quot;Courier New&quot;;">12&nbsp; &nbsp; &nbsp; 6&nbsp; &nbsp; &nbsp; &nbsp;2681&nbsp; &nbsp; 1.56&nbsp; &nbsp; 2317&nbsp; &nbsp; 69</span></p><p style="margin-left: 25px;"><span style="font-size: 14px; font-family: &quot;Courier New&quot;;">13&nbsp; &nbsp; &nbsp; 7&nbsp; &nbsp; &nbsp; &nbsp;2681&nbsp; &nbsp; 2.07&nbsp; &nbsp; 1456&nbsp; &nbsp; 68</span></p><p style="margin-

### Tags
SysDebugDccbBypass,SysDebugCloned,FIX_PATCH_DMR_AP1_A0_60000999,FIX_IFWI_DMR_AP1_2026.12.5.01,FIX_BKC_OKS_DMR_AP1_2026WW14

### Conclusion
fw.bug

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: TRL
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.ufs_control.show`
- `sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.ufs_control_fabric_1.show`
- `sv.socket0.cbbs.base.tpmi.ufs_control.show`

## Timeline

- **Submitted**: 2026-01-21 11:22:43
- **Root Caused**: 2026-03-03 04:32:48
- **Closed**: 2026-04-01 19:16:12
- **Days Open**: 70

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
