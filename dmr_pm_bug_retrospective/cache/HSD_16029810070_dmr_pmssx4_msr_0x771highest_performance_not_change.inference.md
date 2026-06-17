# HSD 16029810070: [DMR_PMSS][X4] : MSR 0x771.HIGHEST_PERFORMANCE not changed to Pm for non enabled cores on SST PP Dynamic switching

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029810070](https://hsdes.intel.com/appstore/article-one/#/16029810070) |
| **Status** | complete.validated |
| **Priority** | 3-medium |
| **Owner** | ashashi |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | PState Stack | 80% |
| **Sub-Feature** | TRL | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

On a 128c, X4 SKU (QDF: Q9X2), observing on SST PP level switch, 

HWP_CAPABILITIES.HIGHEST_PERFORMANCE
 and 
GUARANTEED_PERFORMANCE
 
is not changed to Pm
 for cores which are not enabled in the corresponding PP level.

Steps to Reproduce:

1. Boot to OS in PP level 0

2. Switch to a PP level where few cores are not present using &quot;intel-speed-select perf-profile set-config-level -l X&quot; (X can be 1/2/3)

3. Read MSR 0x771 using &quot;rdmsr -a 0x771&quot;

Expected Behavior:

Not enabled

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
On a 128c, X4 SKU (QDF: Q9X2), observing on SST PP level switch, 

HWP_CAPABILITIES.HIGHEST_PERFORMANCE
 and 
GUARANTEED_PERFORMANCE
 
is not changed to Pm
 for cores which are not enabled in the corresponding PP level.

Steps to Reproduce:

1. Boot to OS in PP level 0

2. Switch to a PP level where few cores are not present using &quot;intel-speed-select perf-profile set-config-level -l X&quot; (X can be 1/2/3)

3. Read MSR 0x771 using &quot;rdmsr -a 0x771&quot;

Expected Behavior:

Not enabled cores for that PP level should show 
HWP_CAPABILITIES.HIGHEST_PERFORMANCE
 & 
GUARANTEED_PERFORMANCE 
values set to Pm.

Observed Behavior:

Not enabled cores show corresponding PP level 
HWP_CAPABILITIES.HIGHEST_PERFORMANCE
 & 
GUARANTEED_PERFORMANCE values and not Pm value of 400(Pm for this QDF)

Log Snippet:

System Information:

[root@dmr-bkc pmutil]# ./pmutil_bin -i

PMUtil Version : 3.12

Platform : DMR Server

Sockets : 1

Cores : 128

CPU's : 128

P0 frequency : 2900MHz

P1 frequency : 1400MHz

Pn frequency : 600MHz

Pm frequency : 400MHz

min core hwp ratio : 0x1d

max core hwp ratio : 0x1d

Core MSR_IA32_HWP_CAPABILITIES : 0x1061c1d

Socket SSE TRL : 0x1d

BIOS Version : OKSDCRB1.E9I.0031.D19.2601151412

Scaling Governor : performance

Current Driver : intel_idle

Scaling Driver : intel_pstate

Kernel Version : 6.14.0-dmr.bkc.6.14.10.5.23.x86_64

IA32_BIOS_SIGN_ID (Pcode Patch ID) : 0xc058161a00000000

IA32_ENERGY_PERF_BIAS : 0x6

MSR_POWER_CTL : 0xa0084005c

MSR_PKG_CST_CONFIG_CONTROL : 0x20

Turbo is enabled on system (OS)

Socket CBB IMH Cores CPU's  PKG_TDP PKG_MAX_PWR PKG_MIN_PWR RAPL_PL1 RAPL_PL2 DRAM_TDP DRAM_MAX_PWR DRAM_PWR_LIMIT

    0   4   2   128  128      450W     540W         0W        450W     540W     356W     404W          0W

Node 0: CPUs [0-127]

Socket 0: Online CPUs: 128

MSR 0x1AD (TURBO_RATIO_LIMIT):        0x1d1d1d1d1d1d1d1d

MSR 0x1AE (TURBO_RATIO_LIMIT_CORES):  0x4040404038302820

Bucket 0: up to 32 active cores => max turbo ratio 29

Bu

### Comments (latest)
++++1667272932 ashashi
<p>Tried changing the PP level via TPMI registers , sst_pp_control and still observed 0x771 not showing Pm for non enabled cores.</p><p><br /></p>
++++22611755101 ashashi
As per HAS: SST-HAS , on Dynamic SST PP level switch, MSR 0x771.HIGHEST_PERFORMANCE & GUARANTEED_PERFORMANCE should be changed to Pm for not enabled cores in the PP level. Currently we are observing , the non enabled cores of a PP level after SST PP Dynamic switching does not show Pm when MSR 0x771.HIGHEST_PERFORMANCE & GUARANTEED_PERFORMANCE is read.
++++14615074389 vwang
[CloneScript] Sighting [sighting_central.sighting.id=16029810070] of [component=fw.pcode] in [release=pkg.dmr-a0] has been cloned to a [bug] to [heia_soc.bugeco.id=14027027077] of [component=dmrcbbbase.soc.pm.pcode] in [release=dmrcbbbase-a0]
++++22611821830 mbfausto
[SysDebug] The FW ticket (id=14027027077) cloned from this sighting has been fixed and released in ingredient version "DMR_A0_6000099A" on [SysDebug] Sighting tag appended with "FIX_PATCH_DMR_A0_6000099A" [SysDebug] [SysDebug] The Sighting owner (ashashi) may be enabled to validate the fix is working in the released collateral.

++++22611822018 mbfausto
[SysDebug Tag Script] IFWI version "DMR_AP_2026.13.3.01" has been released that contains the component release "FIX_PATCH_DMR_A0_6000099A" [SysDebug Tag Script] Sighting tag appended with "FIX_IFWI_DMR_AP_2026.13.3.01"

++++22611823740 ashashi
Validated the below failure with BIOS: OKSDCRB1.IPC.0033.D62.2603242248, UP: 0x8000099a. The failure mentioned in the HSD is no longer observed. The issue is good to close

++++22611833202 mbfausto
[SysDebug Tag Script] BKC version "OKS_DMR_AP_2026WW16" has been released that contains the component release "FIX_IFWI_DMR_AP_2026.13.3.01" [SysDebug Tag Script] Sighting tag appended with "FIX_BKC_OKS_DMR_AP_2026WW16"

### Tags
SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_6000099A,FIX_IFWI_DMR_AP1_2026.13.3.01,FIX_BKC_OKS_DMR_AP1_2026WW16

### Conclusion
fw.bug

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
- **Sub-Feature**: TRL
- **Component Path**: fw.pcode

## Firmware Touchpoints

### PCODE
- `Pcode Patch`

## Key Registers

- `MSR 0x771`
- `MSR 0x1AD`
- `MSR 0x1AE`
- `MSR 0x771`
- `TPMI registers`

## Timeline

- **Submitted**: 2026-02-09 22:02:40
- **Root Caused**: 2026-02-10 23:28:47
- **Closed**: 2026-04-08 00:47:22
- **Days Open**: 57

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
