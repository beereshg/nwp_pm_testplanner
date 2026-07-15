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

PCT (Priority Core Turbo) is a distinct Intel PM feature that uses SST-TF CLOS-based frequency
partitioning to designate a small subset of HP cores to operate at an elevated turbo frequency
(up to P0max, ~4.4 GHz on NWP) while clipping LP cores to approximately P1.

### Block Diagram

```
+---------------------------------------------+   +------------------------------------------+
| Silicon Fuses (read-only, set at mfg)       |   | DLCP Fuse (SKU-specific)                 |
|                                             |   |                                          |
|  GNR: CAPID4.bit29 = 1  <- PCT enable fuse |   |  PCT_Module_Mask fuse                    |
|  DMR/NWP: NOT USED -- all SKUs can opt-in  |   |  Encodes fixed HP core/module positions  |
|                                             |   |  per CBB die per PP level                |
|  SST_TF_INFO_0.LP_CLIP_RATIO_0 (fuse-set)  |   |  Non-zero = DLCP mode active             |
|    LP frequency ceiling (>= P1)            |   |  CLOS_ASSOC[] overridden by fuse mask    |
|  SST_TF_INFO_2.RATIO_0     (fuse-set)      |   |  Exposed to SW via SST_TF_INFO_10        |
|    HP TRL ratio (~4.4 GHz on NWP)          |   |  HWP_CAPABILITY per-core:                |
|  SST_TF_INFO_8.NUM_CORE_0  (fuse-set)      |   |    HP cores: highest_perf = P0max        |
|    Max HP cores supported                  |   |    LP cores: highest_perf = LP clip      |
+--------------------+------------------------+   +------------------+-----------------------+
                     |                                               |
                     | PCode Phase 5 reads fuses, populates TPMI    |
                     |   (at boot, before BIOS CPL3 handoff)        |
                     v                                               v
+-------------------------------------------------------------------------+
| PCode Phase 5 Init (per CBB Root Punit)                                 |
|                                                                         |
|  Writes TPMI from fuse data:                                            |
|    SST_TF_INFO_0.LP_CLIP_RATIO_0  <- LP ceiling (from fuse)            |
|    SST_TF_INFO_2.RATIO_0          <- HP TRL ratio (from fuse)          |
|    SST_TF_INFO_10                 <- DLCP PCT_Module_Mask (0 if std)   |
|    SST_TF_INFO_8.NUM_CORE_0       <- max HP core count (from fuse)     |
+-----------------------------+-------------------------------------------+
                              |
                              | BIOS CPL3 reads TPMI, programs CLOS
                              v
+-------------------------------------------------------------------------+
| Boot Time (BIOS CPL3) -- per CBB dielet (cbb0, cbb1 on NWP)            |
|                                                                         |
|  Standard SKU (CLOS-based assignment):                                  |
|    SST_CLOS_CONFIG[0].max = HP TRL (~4.4 GHz)  <- HP ceiling           |
|    SST_CLOS_CONFIG[3].max = LP clip (~P1)       <- LP ceiling           |
|    SST_CLOS_ASSOC[core]: HP -> CLOS[0], LP -> CLOS[3]                  |
|                                                                         |
|  DLCP SKU (fuse-fixed assignment):                                      |
|    SST_CLOS_ASSOC[] IGNORED by PCode                                    |
|    HP cores determined solely by PCT_Module_Mask fuse                   |
|                                                                         |
|  Both SKUs:                                                             |
|    SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1     <- Ordered throttle     |
|    SST_PP_CONTROL.feature_state[1] = 1         <- SST-TF active        |
|    MSR 0x1AD = SST_TF_INFO_2.RATIO_0           <- HP TRL (not 0xFF)   |
|    PCT Partition Count (BIOS knob) -> NVRAM PctHpModuleCount            |
+-----------------------------+-------------------------------------------+
                              |
                              | PCode reads CLOS config at runtime
                              v
+-------------------------------------------------------------------------+
| Runtime: PCode SST-TF FSM (per CBB Root Punit)                         |
|                                                                         |
|  Standard SKU: uses CLOS[0/3] assignments from BIOS                    |
|  DLCP SKU:     uses PCT_Module_Mask fuse (ignores CLOS_ASSOC)          |
|                                                                         |
|  HP cores: WP4 = SST_TF_INFO_2.RATIO_0  (~4.4 GHz ceiling)            |
|  LP cores: WP4 = SST_TF_INFO_0.LP_CLIP_RATIO_0  (~P1 ceiling)         |
|                                                                         |
|  RAPL Ordered throttle (SST_CP_PRIORITY_TYPE=1):                        |
|    Phase A: reduce LP first                                             |
|    Phase B: maintain HP while LP still above min                        |
|    Phase C: only then reduce HP                                         |
+-----------------------------+-------------------------------------------+
                              |
                              | WP4 per CLOS group broadcast to cores
                              v
+-------------------------------------------------------------------------+
| Core Perimeter (ACP / Acode) -- NWP: 2 CBBs x 48 cores = 96 total     |
|                                                                         |
|  Standard SKU:  HP cores (~8): P0max turbo  |  LP cores (~88): ~P1     |
|  DLCP SKU:      HP positions fuse-fixed     |  LP = all remaining      |
|                                                                         |
|  HWP_CAPABILITY.highest_perf:                                           |
|    Standard: HP=highest_perf (all same), LP=same                        |
|    DLCP:     HP=P0max (per-core reported), LP=LP_clip (per-core)        |
+-------------------------------------------------------------------------+
```

### Primary Use Case (from PCT HAS)
PCT targets Intel Xeon CPU+GPU/accelerator systems where a few CPUs in each partition are
dedicated to servicing one GPU. These GPU-serving cores need maximum frequency while remaining
cores run at a lower frequency. PCT achieves this **without requiring other cores to sleep in C6**
— LP cores remain active at ~P1, unlike P0half which requires half the cores to be in C6.

### Frequency Hierarchy
| Name | Description | Example |
|------|-------------|---------|
| P0max | Maximum turbo frequency | 4.6 GHz (GNR) / ~4.4 GHz (NWP) |
| F3 | PCT HP core frequency (≤ P0max) | 4.4–4.6 GHz |
| P0half | Half-core turbo (requires C6 on half cores) | 3.9 GHz |
| P0n | All-core turbo | 3.6 GHz |
| F2 / LP clip | LP core clip frequency | ~P1 ≈ 2.3 GHz |
| P1 | All-core guaranteed frequency | — |
| Pn | Minimum core frequency | — |

### Key Design Points (from PCT HAS §Solution)
- **No C6 requirement**: HP cores achieve P0max with LP cores fully active at ~P1
- **Default activation**: System boots with PCT enabled if supported; BIOS sets up CLOS before OS handoff
- **HP selection algorithm**: Divide all available processors (in MADT order) into N partitions (default N=4); first consecutive cores in each partition = HP
- **MADT ordering**: BIOS ensures cores in the same module are adjacent in MADT for natural module-scoped HP selection
- **Runtime reconfiguration**: Users can use the Intel SST tool to enable/disable PCT or reassign HP/LP cores at OS runtime
- **Virtualization**: VMM can assign HP logical host cores to specific VMs; all non-HP cores are limited to LP clip frequency

### DMR vs GNR Implementation Differences (from DMR Turbo HAS §PCT)
| Aspect | GNR | DMR / NWP |
|--------|-----|-----------|
| PCT enable fuse | CAPID4.bit29 = 1 | **Not used** — all parts can run PCT or non-PCT |
| PCT default at boot | Enabled if fused | **Disabled by default** (PCT Partition Count = 0) |
| PCT Enable BIOS knob | Standalone "PCT Enable" | **Eliminated** — integrated into PCT Partition Count |
| HP core selection | CAPID4-gated | Available for **all SKUs** via Partition Count opt-in |

### DLCP (Die Level Cherry Picking) (from PCT HAS §Implementation Evolution)
DLCP is a PCT evolution where HP core positions are **fixed at specific physical die locations** via fuse:
- `PCT_Module_Mask` fuse encodes HP core/module assignment per CBB die per PP level
- `SST_TF_INFO_10` TPMI register exposes the mask for SW discovery
- On DLCP SKUs: `CLOS_ASSOC[]` assignments are ignored — Pcode relies exclusively on the fuse mask
- `HWP_CAPABILITY.highest_perf` reported per-core: HP cores = max turbo, LP cores = LP clip frequency
- SW discovery: use `SST_TF_INFO_10` (non-zero = DLCP active), HWP MSR, or Linux SST tool

### Cross-Product Rules (DQ Rules from PCT HAS)
- PCT and SST-BF are **mutually exclusive** (enforced by DQ rule)
- PCT and FCT (Favored Core Turbo) are **mutually exclusive** (enforced by DQ rule)
- If PCT_ENABLE: SST-TF must also be enabled

## Interfaces and Protocols — Discovery Registers

> Placed under **Section 2: Interfaces and Protocols** — TPMI/MSR/NVRAM interfaces
> through which SW observes and interacts with the PCT feature, plus BIOS knobs.

### BIOS Knobs (from CPUPM BIOS Knobs Reference Gen 3)

| BIOS Knob | Options | Default | Notes |
|-----------|---------|---------|-------|
| PCT Enable | Enable / Disable | **Disable (DMR/NWP)** | Hidden if not PCT capable. On GNR: default Enable |
| PCT HP Partition Count | 1–16 HP partitions | **4** | Max = SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS |
| PCT Core Selection | 0–255 | **0** | Starting core position within partition for HP selection. 0 = first core |

> Note: On DMR/NWP the PCT Partition Count knob defaults to 0 (disabled), customers must opt-in.

### TPMI / MSR / NVRAM Registers

| Interface | Register | Purpose |
|-----------|----------|---------| 
| TPMI | SST_HEADER.CAPABILITY_MASK | PCT active bit |
| TPMI | SST_TF_INFO_0.LP_CLIP_RATIO_0 | LP ceiling (≥P1, SKU-fused) |
| TPMI | SST_TF_INFO_2.RATIO_0 | HP TRL ratio (~4.4 GHz on NWP) |
| TPMI | SST_TF_INFO_10 | DLCP: PCT_Module_Mask — fused HP core positions per die (non-zero = DLCP active) |
| TPMI | SST_CLOS_ASSOC_* | Per-core CLOS assignment: HP=CLOS[0/1], LP=CLOS[2/3] |
| TPMI | SST_CP_CONTROL.sst_cp_enable | PCT globally enabled |
| TPMI | SST_CP_CONTROL.SST_CP_PRIORITY_TYPE | Throttling mode: 1 = Ordered (LP throttled first) |
| TPMI | SST_TF_INFO_8.NUM_CORE_0 | Max HP cores supported (used to bound PCT Partition Count knob) |
| MSR | IA32_HWP_CAPABILITIES (0x771) | HP cores report P0max; LP cores report LP clip (DLCP mode) |
| MSR | 0x1AD PRIMARY_TURBO_RATIO_LIMIT | HP TRL broadcast by BIOS at boot |
| NVRAM | PctHpModuleCount | Number of HP modules configured |

## Programming Model — Enabling Path

> Placed under **Section 4: Programming Model** — this is the boot-time register programming
> sequence executed by PrimeCode Phase 5 and BIOS CPL3 to activate PCT.

| Step | Actor | Register | Value |
|------|-------|----------|-------|
| 1 | PrimeCode Phase 5 | SST_TF_INFO_0.LP_CLIP_RATIO_0 | LP frequency ceiling (≥P1) |
| 2 | PrimeCode Phase 5 | SST_TF_INFO_2.RATIO_0 | HP TRL ratio (~4.4 GHz on NWP) |
| 3 | PrimeCode Phase 5 | SST_TF_INFO_10 | DLCP PCT_Module_Mask (non-zero if DLCP SKU) |
| 4 | BIOS CPL3 | SST_CLOS_CONFIG[0].min = P1, .max = SST_TF_INFO_2.RATIO_0 | HP CLOS ceiling |
| 5 | BIOS CPL3 | SST_CLOS_CONFIG[3].min = Pn, .max = SST_TF_INFO_0.LP_CLIP_RATIO_0 | LP CLOS ceiling |
| 6 | BIOS CPL3 | SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1 | Ordered Throttling enabled |
| 7 | BIOS CPL3 | SST_CLOS_ASSOC[core] | HP → CLOS[0]; LP → CLOS[3] |
| 8 | BIOS CPL3 | SST_PP_CONTROL.feature_state[1] = 1 | SST-TF active |
| 9 | BIOS CPL3 | MSR 0x1AD = SST_TF_INFO_2.RATIO_0 | HP TRL broadcast (0xFF no longer valid per HSD 14025997048) |

## TC Coverage

| TC ID | Title | Status | Environment |
|-------|-------|--------|-------------|
| [22022422100](https://hsdes.intel.com/appstore/article-one/#/22022422100) | PCT - BIOS Menu | open | silicon, virtual_platform |
| [22022422103](https://hsdes.intel.com/appstore/article-one/#/22022422103) | PCT - TPMI register check | open | virtual_platform |
| [22022422118](https://hsdes.intel.com/appstore/article-one/#/22022422118) | PCT - DQ Rules (FlexconPM) | open | silicon, virtual_platform |
| [16030715678](https://hsdes.intel.com/appstore/article-one/#/16030715678) | [PSS] PCT - BIOS Menu | open | silicon, virtual_platform |
| [16030715682](https://hsdes.intel.com/appstore/article-one/#/16030715682) | [PSS] PCT - DQ Rules (FlexconPM) | open | silicon, virtual_platform |
| [16030715690](https://hsdes.intel.com/appstore/article-one/#/16030715690) | [PSS] PCT - TPMI register check (FlexconPM) | open | silicon, virtual_platform |
| [16030717720](https://hsdes.intel.com/appstore/article-one/#/16030717720) | [PV]PMSS - SST PCT Discovery | open | — |

## References

- [PCT (Priority Core Turbo) HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — Primary: BIOS flow, CLOS registers, DLCP, fuses, DQ rules, MADT ordering
- [Priority Core Turbo Technology White Paper](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/IC_PCT.html) — Customer-facing overview, GPU use case, virtualization
- [PRIMECODE-9334 Priority Core Turbo (PCT) WIP](https://docs.intel.com/documents/primecode/fhas/GNR/PCT/PRIMECODEF-9334-PCT.html) — PrimeCode FHAS for PCT Phase 5 init
- [Diamond Rapids Server (DMR) Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) — DMR changes: CAPID4.bit29 not used, default disabled, PCT Partition Count knob
- [CPUPM BIOS Knobs Reference (Gen 3)](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Index/CPUPM%20BIOS%20Knobs/BiosKnobs.html) — Exact BIOS knob names, options, defaults (PCT Enable, PCT HP Partition Count, PCT Core Selection)
- [OKS Product Architecture HAS](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/OKS-Product-Architecture-Spec/OKS-Product-Architecture-Spec.html) — OKS platform context
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST-TF CLOS infrastructure underlying PCT
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP scope: SST-TF + PCT only
- [CCB HSD 14026595435](https://hsdes.intel.com/appstore/article-one/#/14026595435) — NWP: 8 HP cores, ~4.4 GHz PCT target (POR-1)
- [HSD 14025997048](https://hsdes.intel.com/appstore/article-one/#/14025997048) — MSR 0x1AD: 0xFF no longer valid; must use SST_TF_INFO_2.RATIO_0
- KB: KB/pm_features/sst/pct.md
