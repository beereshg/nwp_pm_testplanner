# TCD: PCT - Enabling & Discovery

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855) |
| **Title** | PCT - Enabling & Discovery |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TP** | [16030762939](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **KB last updated** | 2026-06-22 |

## Feature Overview

See HSD description (updated 2026-06-22 with HAS/MAS-backed content).

## What is PCT (Priority Core Turbo)

PCT is a distinct Intel PM feature that uses SST-TF CLOS-based frequency partitioning to elevate
a small subset of HP cores to P0max (~4.4 GHz on NWP) while clipping LP cores to ~P1.

- **HP core count (NWP)**: 8 (2 per partition x 4 partitions; 2 CBBs x 48 cores = 96 total)
- **PCT gate**: PCT Partition Count BIOS knob > 0 (default = 4); CAPID4.bit29 is GNR-only
- **PrimeCode**: Reset Phase 5 populates SST_TF_INFO_0/2/10 from fuses
- **BIOS**: Programs SST_CLOS_CONFIG, SST_CLOS_ASSOC, SST_CP_CONTROL, MSR 0x1AD per CBB
- **NWP scope**: Only SST-TF + PCT active; SST-PP/CP/BF/HGS are ZBB (HSD 22021155414)

## Enabling Path (key registers)

| Step | Actor | Register | Value |
|------|-------|----------|-------|
| 1 | PrimeCode Phase 5 | SST_TF_INFO_0.LP_CLIP_RATIO_0 | LP frequency ceiling (>=P1) |
| 2 | PrimeCode Phase 5 | SST_TF_INFO_2.RATIO_0 | HP TRL ratio (~4.4 GHz) |
| 3 | PrimeCode Phase 5 | SST_TF_INFO_10 | DLCP PCT_Module_Mask |
| 4 | BIOS CPL3 | SST_CLOS_CONFIG[0].max | HP ceiling from INFO_2.RATIO_0 |
| 5 | BIOS CPL3 | SST_CLOS_CONFIG[3].max | LP ceiling from INFO_0.LP_CLIP_RATIO_0 |
| 6 | BIOS CPL3 | SST_CP_CONTROL.SST_CP_PRIORITY_TYPE | 1 (Ordered Throttling) |
| 7 | BIOS CPL3 | SST_CLOS_ASSOC[core] | HP->CLOS[0], LP->CLOS[3] |
| 8 | BIOS CPL3 | SST_PP_CONTROL.feature_state[1] | 1 (SST-TF active) |
| 9 | BIOS CPL3 | MSR 0x1AD | HP TRL broadcast |

## Discovery Registers

| Interface | Register | Purpose |
|-----------|----------|---------|
| TPMI | SST_HEADER.CAPABILITY_MASK | PCT active bit |
| TPMI | SST_TF_INFO_0.LP_CLIP_RATIO_0 | LP ceiling |
| TPMI | SST_TF_INFO_2.RATIO_0 | HP TRL |
| TPMI | SST_TF_INFO_10 | DLCP HP module mask |
| TPMI | SST_CLOS_ASSOC_* | Per-core CLOS (HP=0/1, LP=2/3) |
| TPMI | SST_CP_CONTROL.sst_cp_enable | PCT globally enabled |
| MSR | IA32_HWP_CAPABILITIES (0x771) | HP=P0max, LP=LP clip |
| MSR | 0x1AD PRIMARY_TURBO_RATIO_LIMIT | HP TRL |
| NVRAM | PctHpModuleCount | HP modules configured |

## Test Cases Under This TCD

| HSD ID | Title | Status | Val Environment |
|--------|-------|--------|-----------------|
| [22022422100](https://hsdes.intel.com/appstore/article-one/#/22022422100) | PCT - BIOS Menu | rejected | virtual_platform |
| [22022422103](https://hsdes.intel.com/appstore/article-one/#/22022422103) | PCT - TPMI register check | open | virtual_platform |


## References

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [IC PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/IC_PCT.html)
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [CCB HSD 14026595435](https://hsdes.intel.com/appstore/article-one/#/14026595435) - NWP 8 HP cores, 4.4 GHz target
- KB: KB/pm_features/sst/pct.md
