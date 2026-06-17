# HSD 14026508259: [DMR][X1 A0] LatencyOptimizedMode  (LOM) when Disabled does not show expected ELC and Ring, mem & IO frequencies

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026508259](https://hsdes.intel.com/appstore/article-one/#/14026508259) |
| **Status** | rejected.merged |
| **Priority** | 3-medium |
| **Owner** | srotich |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 80% |
| **Sub-Feature** | Turbo | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Summary:

=========

LatencyOptimizedMode (LOM) when Disabled in BIOS does not increase ring, mem & IO frequencies as expected to P0 frequencies.

LOM feature, when disabled, the ELC will operate ELC-Lo to ELC mid ratio  depending on number of active cores (in C0)

Settings:

LOM Disabled in BIOS

Observation

2 cores in C0;
frequency drops from 1200 to 800MHZ (issue)

root@sut-8000 ~]#
cpc -cs POLL-only -cl 0-1

For cores [0, 1]
setting cstates: ['POLL-only']

[root@sut-8000 ~]#
turbostat -q -S

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww02.3]

primecode team suggest to test the same patch provided in 16029367861 as both sightings fall into the ELC domain, there could be potential positive results that impact this sighting. 

[25ww51.3]

Data has been provided, and Shreyas/Sagar are providing support and waiting on the other LOM sighting. Need to do more research as if the root cause is the same as the other LOM sighting and, if they are the same, merge it. Tomothy suggest to verify the HAS expectation is the same as the sighting submitter/test case. 

[25ww51.1]

Vidar will contact PM team for the test result.

[25ww50.1]

Opposed to 
16029367861
, when LOM is disabled, ELC lo-mid ratio is not the expected one. Stan mentioned there is a new ELC algorithm released on Friday, pCode will work on alignment to the last release. In paralel need Simeon to provide input to Shreyas to continue debug.

### Description
Summary:

=========

LatencyOptimizedMode (LOM) when Disabled in BIOS does not increase ring, mem & IO frequencies as expected to P0 frequencies.

LOM feature, when disabled, the ELC will operate ELC-Lo to ELC mid ratio  depending on number of active cores (in C0)

Settings:

LOM Disabled in BIOS

Observation

2 cores in C0;
frequency drops from 1200 to 800MHZ (issue)

root@sut-8000 ~]#
cpc -cs POLL-only -cl 0-1

For cores [0, 1]
setting cstates: ['POLL-only']

[root@sut-8000 ~]#
turbostat -q -S --hide Avg_MHz,IRQ,NMI,SMI,POLL,POLL+,C1-,C1,PKG_%,RAM_% -c
package

Can not set timer.

Busy%   Bzy_MHz TSC_MHz IPC     POLL   
POLL+   C1-     C1     
POLL%   C1%     CPU%c1 
CPU%c6  CoreTmp CoreThr PkgTmp  Pkg%pc2 Pkg%pc6 PkgWatt RAMWatt UMHz0.0
UMHz2.0 UMHz2.1

6.26    2200   
1300    0.14    155215 
64      0       562    
6.23    93.74   93.74  
0.00    55      0      
54      0.00    0.00   
132.09  7.82    2200   
400     800

6.27    2200   
1300    0.14    155232 
75      0       545    
6.23    93.73   93.73  
0.00    55      0      
54      0.00    0.00   
132.14  7.81    2200   
400     800

6.26    2200   
1300    0.14    155201 
57      0       398    
6.23    93.75   93.74  
0.00    55      0      
54      0.00    0.00   
131.88  7.81    2200   
400     800

6.26    2200   
1300    0.14    155217 
71      0       444    
6.23    93.74   93.74  
0.00    55      0      
54      0.00    0.00   
132.18  7.81    2200   
400     800

^C6.27  2200   
1300    0.15    13260  
6       0       101    
6.22    93.74   93.73  
0.00    54      0      
54      0.00    0.00   
131.64  7.86    2200   
400     800

[root@sut-8000 ~]#

Min ratio=0xd; we
see 1.3GHZ

 

 

 

#Read 1.3GHZ

 

 

 

 

 

##High threshold
=16; low threshold=400

 

 

output freq:

Results:

when all cores set to C1 (no active core), the ELC is not kicking in. We expect 1.2GHZ; seeing 800MHZ

Expect
ELC low =800MHZ up to 4 cores: expecting 1.2GHZ, but we see 800MHZ

##Expected
ELC High: for LOM di

### Comments (latest)
++++14614849086 vwang
[CloneScript] PreSighting 14026130685 cloned to Sighting 14026508259

++++14614862868 shreyasu
Hey Simeon, could you check the following pcudata variables to see the state of the system? Get maybe 100 samples of each when you're seeing the problem behavior. We want to figure out if we're actually seeing the expected telemetry on the system itself. ufs_heuristics.io_fabric_freq_req ufs_heuristics.mem_fabric_freq_req ufs_heuristics.ufs_elc.perf_mode_mem_ratio ufs_heuristics.ufs_elc.perf_mode_io_ratio ufs_heuristics.ufs_elc.elc_low_io_frequency_limit ufs_heuristics.ufs_elc.elc_low_mem_frequency_limit ufs_heuristics.ufs_elc.efficiency_latency_cntrl_mode ufs_heuristics.ufs_elc.perf_mode_enable ufs_heuristics.ufs_elc.active_cbb_c0_util_max ufs_heuristics.ufs_elc.core_c0_time_0.val ufs_heuristics.ufs_elc.core_c0_time_1.val ufs_heuristics.ufs_elc.core_c0_time_prev_0.val ufs_heuristics.ufs_elc.core_c0_time_prev_1.val ufs_heuristics.ufs_elc.total_time_0.val ufs_heuristics.ufs_elc.total_time_1.val ufs_heuristics.ufs_elc.total_time_prev_0.val ufs_heuristics.ufs_elc.total_time_prev_1.val ufs_heuristics.ufs_io_traffic.freq_limit ufs_heuristics.ufs_mem_bound.freq_limit ufs_heuristics.ufs_mem_d2d.freq_limit ufs_heuristics.ufs_mem_mc_traffic.freq_limit ufs_heuristics.ufs_mem_ring.freq_limit

++++14614899618 smakine1
ELC_LOW is enabled by setting threshold to a large value (0x60) and ratio is set to 0xa. ELC_LOW functionality is observed only when all cores are in C1 or C1E. When even a single core in C0, we see frequency going back to min_ratio, which is set to 0x8 or 0x4. This data is from a VIS 48c part with OKSDCRB1.86B.0030.D43.2512112121 12/11/2025 BIOS. [root@SC8013 srihari]# turbostat -S -q -c package --hide=NMI,SMI,IRQ,LLCkRPS,CPU%c1,CPU%c6 Avg_MHz Busy%   Bzy_MHz TSC_MHz IPC     POLL%   C1%     C1E%    C6A%    C6S%    C6SP%   Mod%c6  CoreTmp CoreThr PkgTmp  Pkg%pc2 Pkg%pc6 PkgWatt RAMWatt UMHz0.0 UMHz2.0 UMHz2.1 0       0.00    3000    2100    0.98                         0.00       100.00  0.00    0.00    0.00    0.00    0.00    45      0       45      0.00    0.00    80.12   15.27   2700    1000    1000 0       0.00    3000    2100    0.80                         0.00       100.00  0.00    0.00    0.00    0.00    0.00    45      0       46      0.00    0.00    80.15   15.26   2700    1000    1000 0       0.01    3000    2100    0.89                         0.00         99.99   0.00    0.00    0.00    0.00    0.00    44      0       45      0.00    0.00    80.09   15.28   2700    1000    1000 In [167]: sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.ufs_control_fabric_1.show() 0x00000000 : rsvd4 (63:47) (rw) -- Reserved 0x00000060 : efficiency_latency_ctrl_high_threshold (46:40) (rw) -- Utilization point above which freq will be optimized to optimize latency. 0x00000001 : efficiency_latency_ctrl_high_threshold_enable (39:39) (rw) -- If set (1), EFFICIENCY_LATENCY_CTRL_HIGH_THRESHOLD is valid 0x00000060 : efficiency_latency_ctrl_low_thresho

### Tags
PM

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: Turbo
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.ufs_control_fabric_1.show`
- `sv.socket0.imhs.punit.ptpcfsms.ptpcfsms.ufs_control.show`
- `sv.socket0.imhs.pcudata.ufs_heuristics.io_fabric_freq_req`
- `sv.socket0.imhs.pcudata.ufs_heuristics.mem_fabric_freq_req`
- `sv.socket0.imhs.pcudata.ufs_heuristics.ufs_elc.perf_mode_mem_ratio`

## Timeline

- **Submitted**: 2025-11-26 02:29:55
- **Closed**: 2026-01-08 12:39:44
- **Days Open**: 43

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
