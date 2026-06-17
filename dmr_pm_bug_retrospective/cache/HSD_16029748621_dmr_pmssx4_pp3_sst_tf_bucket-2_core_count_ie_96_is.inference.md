# HSD 16029748621: [DMR_PMSS][X4] : PP3_SST_TF bucket-2 core count (i.e. 96) is greater than PP3 online core count (i.e. 80)

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16029748621](https://hsdes.intel.com/appstore/article-one/#/16029748621) |
| **Status** | complete.wont_validate |
| **Priority** | 2-high |
| **Owner** | ashashi |
| **Component** | hw.fuse.xml |
| **Defect Die** | ioe |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 80% |
| **Sub-Feature** | TRL | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Expected Behavior:

For a PP level, SST-TF bucket core-count shouldn't exceed the online core-count for that PP level. 

Actual Behavior:

In PP3, SST_TF bucket-2 core-count (i.e. 96) is greater than PP3 online core-count (i.e. 80 (20 cores * 4 CBBs))

perf-profile-level-3_enable_cpu_list {'package-0:die-0:powerdomain-0:cpu-0': [0, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 24, 25, 26, 27, 28, 29], 'package-0:die-1:powerdomain-1:cpu-32': [38, 39, 42, 43, 44, 45, 48, 49, 52, 53, 54, 55, 56,

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww07.3]

Forum exploring if we can do some fuse value testing before hand. Anaja will get in touch with Alex for the new fuse value, this seems to be root caused to fuse. 

﻿[26ww07.1]

Anjana will reach out to Toh, alex seang kheng  for the fuse value

﻿[26ww06.3]

SST_TF core-count is greater than online core-count, expectation is that SST bucket2 should never exceed online core counts

Potential incorrect behaviors for algorithms that rely on the SST_TF bucket 2 core count as well as incorrect reporting for monitoring tools.

This could be rooted caused to a fuse definition issue, Leonardo from FV following with Archana from fuse team for resolution, as Archana suggest the fix should come already on new VIS parts but data shows this is indeed a new fuse change to be requested. Next step to be defined after that.

[26ww06.1]

Stan has confirmed this is a fuse issue. will follow up with Fuse team

### Description
Expected Behavior:

For a PP level, SST-TF bucket core-count shouldn't exceed the online core-count for that PP level. 

Actual Behavior:

In PP3, SST_TF bucket-2 core-count (i.e. 96) is greater than PP3 online core-count (i.e. 80 (20 cores * 4 CBBs))

perf-profile-level-3_enable_cpu_list {'package-0:die-0:powerdomain-0:cpu-0': [0, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 24, 25, 26, 27, 28, 29], 'package-0:die-1:powerdomain-1:cpu-32': [38, 39, 42, 43, 44, 45, 48, 49, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63], 'package-0:die-2:powerdomain-2:cpu-64': [64, 65, 66, 67, 72, 73, 74, 75, 78, 79, 80, 81, 82, 83, 86, 87, 92, 93, 94, 95], 'package-0:die-3:powerdomain-3:cpu-96': [102, 103, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 122, 123, 124, 125, 126, 127]}

X4 - 128 core system

[root@dmr-bkc pmutil]# ./pmutil_bin -i

PMUtil Version : 3.13

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

Core MSR_IA32_HWP_CAPABILITIES : 0x1060e1d

Socket SSE TRL : 0x1c

BIOS Version : OKSDCRB1.E9I.0031.D19.2601151412

Scaling Governor : performance

Current Driver : acpi_idle

Scaling Driver : intel_pstate

Kernel Version : 6.14.0-dmr.bkc.6.14.7.4.PO13.16.x86_64

IA32_BIOS_SIGN_ID (Pcode Patch ID) : 0xc058161a00000000

IA32_ENERGY_PERF_BIAS : 0x6

MSR_POWER_CTL : 0xa0084005e

MSR_PKG_CST_CONFIG_CONTROL : 0x22

Turbo is enabled on system (OS)

Socket CBB IMH Cores CPU's  PKG_TDP PKG_MAX_PWR PKG_MIN_PWR RAPL_PL1 RAPL_PL2 DRAM_TDP DRAM_MAX_PWR DRAM_PWR_LIMIT

    0   4   2   128  128      450W     540W         0W        450W     540W     356W     404W          0W

Node 0: CPUs [0-127]

Socket 0: Online CPUs: 128

MSR 0x1AD (TURBO_RATIO_LIMIT):        0x1c1c1c1c1c1c1c1d

MSR 0x1AE (TURBO_RATIO_LIMIT_CORES):  0x4040404038302820

Bucket 0: up to 32 active cores => max turbo ratio 29

### Comments (latest)
++++14615055285 amunshi
Q9X2: looks like SKU definition issue +  @Toh, alex seang kheng /  @Marin Cartin, Erick  - can you pls. look into this issue? 

++++14615055288 amunshi
Actually - this is a PO SKU.   @Marin Cartin, Erick  - if this is the known issue which was promised to be fixed on some VIS SKUs, pls. comment accordingly.

++++14615057473 lmalagon 
 @Munshi, Archana I do not think this is a known issue, this check was missed in FV, and PV team (Anjana/Pragya) catch this issue. This issue is present also in VIS SKUs like QA2A: SST TF bucket 2 is the same value for all CBB base dies punit_fuses.fw_fuses_sst_tf_config_3_turbo_ratio_limit_cores_numcore2=0x60 each CBB only have 10 modules enabled in SST PP level 3 CBB 0: punit_fuses.fw_fuses_sst_pp_3_module_disable_mask=0xff20ff9b [stub] In [8]: bin((~0xff1f01ff) & 0xffffffff).count('1') Out[8]: 0xA CBB 1: punit_fuses.fw_fuses_sst_pp_3_module_disable_mask=0xff20ff9b CBB 2:  punit_fuses.fw_fuses_sst_pp_3_module_disable_mask=0x9e02ffff CBB 3: punit_fuses.fw_fuses_sst_pp_3_module_disable_mask=0x9ff93ff


++++14615064882 vwang
 @Toh, alex seang kheng  will provide the attribute value

++++14615076832 emarinca
Hi  @Munshi, Archana and  @Toh, alex seang kheng , I checked Q9X2 and it is correct that SSTTF CFG3 core count higher value is 96 , versus 80 in the PP level, however this is a value input by Marketing and it is not generated by binsplit calculator, which only takes MKT inputs and calculates the respective frequencies.  A DQ rule must be implemented in OCPLM to catch this discrepancies. We need  @Prado Villeda, Guido R or  @Marupaka, Swapna to provide root cause and help on fixes.  We could create an extra check in BS rules, to prevent building if this if found, but OCPLM happens first and should be the first container.

++++14615077460 stoh4
Thanks Erick. This was old QDF, we did not provide SSTTF freq response back then. Like what Erick mentioned, we did not control the SSTTF core count attributes, but we use them as input to calculate SSTTF frequencies. So I agreed with Erick's proposal, DQ rules needed

++++14615080194 vwang 
[CloneScript] Sighting [sighting_central.sighting.id=16029748621] of [component=hw.fuse.xml] in [release=pkg.dmr-a0] has been cloned to a [bug] to [soc_config.bugeco.id=14027046821] 
++++22611771958 ashashi
Updating email conversation: ----------------------------------------------------------------------------- From: Toh, alex seang kheng <alex.seang.kheng.toh@intel.com> Sent: Wednesday, February 11, 2026 1:03 PM To: Shashi, Anjana <anjana.shashi@intel.com> Cc: Wang, Vidar <vidar.wang@intel.com>; Amarnath, Abhinand <abhinand.amarnath@intel.com>; Salazar, Jesus <jesus.salazar@intel.com>; Marin Cartin, Erick <erick.marin.cartin@intel.com>; Munshi, Archana <archana.munshi@intel.com> Subject: RE: Regarding HSD: 16029748621   I think nothing else can be validated here. Erick is working with marketing team to apply a rule checker (DQ Rule) to ensure future quality     Fr

### Tags
SysDebugCloned,SysDebugDccbBypass

### Conclusion
hw.arch

### Component
hw.fuse.xml

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
- **Component Path**: hw.fuse.xml

## Firmware Touchpoints

### PCODE
- `Pcode Patch`

## Key Registers

- `MSR 0x1AD`
- `MSR 0x1AE`

## Timeline

- **Submitted**: 2026-01-30 23:17:02
- **Root Caused**: 2026-02-12 03:45:08
- **Closed**: 2026-03-17 22:07:10
- **Days Open**: 45

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
