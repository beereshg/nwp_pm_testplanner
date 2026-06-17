# SST > PCT (Priority Core Turbo)

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing + HP core selection algorithm + LP clip resolution + RAPL-PCT TDP convergence (2026-05-29)
> **Parent**: [SST](sst_main.md)
> **Source Confidence**: High — Architecture from [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html), [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html). Feature distinction from [DMR Overview HAS CBB Feature List](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/DMR_Overview_HAS.html). NWP scope from [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) + [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435). See [Source Notes](#source-notes).

## Baseline (DMR)

**PCT (Priority Core Turbo)** is a distinct Intel feature that uses SST-TF’s CLOS-based frequency partitioning to elevate a small subset of HP cores to P0max while clipping LP cores to approximately P1. BIOS divides all physical cores into partitions and designates HP core(s) per partition. PCode runs the standard SST-TF flow unchanged. **Active on NWP** with 8 HP cores across 4 partitions (2 CBBs × 48 cores).

**Topology**: BIOS discovers PCT capability (CAPID4.bit29 on GNR; partition count on DMR/NWP) → programs SST-TF TPMI CLOS registers per dielet → PCode enforces CLOS-based frequency limits at runtime. DLCP variant: `PCT_Module_Mask` fuse fixes HP core positions at specific die locations; `SST_TF_INFO_10` exposes the mask.

```
BIOS Boot
├── Read PCT capability (partition count knob, NWP default = 4)
├── Divide 96 cores (2 CBBs × 48) into 4 partitions of 24
├── Select 2 HP cores per partition (8 HP total)
├── Per dielet, program SST-TF TPMI registers:
│   ├── SST_CLOS_CONFIG[0]: min=P1, max=SST_TF_INFO_2.RATIO_0 (HP)
│   ├── SST_CLOS_CONFIG[3]: min=Pn, max=SST_TF_INFO_0.LP_CLIP_RATIO_0 (LP)
│   ├── SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1 (Ordered Throttling)
│   ├── SST_CLOS_ASSOC[]: HP cores → CLOS[0], LP cores → CLOS[3]
│   └── SST_PP_CONTROL.feature_state[1] = 1 (SST-TF active)
└── Override MSR 0x1AD with SST_TF_INFO_2.RATIO_0 (HP TRL)

PCode Runtime (identical to standard SST-TF)
├── Enforces CLOS-based frequency limits per core
├── HP cores → up to PCT TRL ratio (4.4 GHz target on NWP)
└── LP cores → clipped to LP_CLIP ratio (~P1)
```

**Boot activation**: Enabled at BIOS CPL3. `SST_PP_CONTROL.feature_state[1] = 1` activates SST-TF/PCT. PCT Partition Count BIOS knob (default = 4) drives HP core selection.

**HP core selection rule**: BIOS enumerates all enabled physical cores in APIC ID order (MADT order: big P-cores first, then compute die Atoms, then SoC Atoms). Cores are divided evenly into N partitions. The **first processor** in each partition is the core with the lowest APIC ID in that group — offset 0 within the partition. This is the default HP core (CLOS[0]); all other cores in the partition become LP (CLOS[3]). The `PCT Core Select` BIOS knob shifts this offset for manual override.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| TPMI SRAM (SST) | IMH-P die | Stores CLOS config, CLOS assoc, TF info registers per dielet; DLCP: SST_TF_INFO_10 HP mask | SST_CLOS_CONFIG[0/3], SST_CLOS_ASSOC, SST_TF_INFO_0/2/10 | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| Fuse controller | IMH die | PCT_Module_Mask fuse (DLCP); SST_TF_CONFIG LP clip + HP TRL arrays per PP level | PCT_ENABLE, PCT_Module_Mask, SST_TF_CONFIG fuse arrays | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| Core FIVR + PLL | CBB compute | Enforces per-CLOS frequency min/max; HP cores get P0max headroom, LP cores clipped at ~P1 | CLOS ratio enforcement via workpoint calc | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| BIOS | Pre-OS | Discovers PCT capability; divides cores into partitions; programs all SST-TF TPMI registers; overrides MSR 0x1AD with HP TRL | BIOS PCT partition/core-select knobs; CPUPM FAS | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| PCode (CBB) | Root + Leaf CBB | Runs standard SST-TF flow: enforces CLOS-based frequency limits; manages SST-TF feature state; handles CLOS_CONFIG updates | `sst_manager.cpp::update_cfgs()`, `trl_manager.cpp::load_hp_clos_trl()` | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| PrimeCode (IMH-P) | IMH-P | Reads SST_TF fuses + PCT_Module_Mask; populates SST_TF_INFO_0..10 TPMI registers at reset Phase 5 | `sst_tpmi_general.cpp::sstTfInfoInit()`, `sst_tpmi_compute.cpp` | Primecode source |
| PCode RAPL PID (CBB) | Root CBB | Runs RAPL PID controller (1ms loop); under PL1 constraint applies ordered throttling (SST_CP_PRIORITY_TYPE=1): LP cores throttled first, HP cores maintained at PCT frequency until LP at minimum, then HP reduced | RAPL PID + CLOS ordered throttle | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html), MCP query 2026-05-29 |
| Acode | Compute core | Executes at PCode-assigned CLOS ratio (HP = P0max ceiling, LP = LP_CLIP ceiling); no special PCT logic in Acode | Architecture reference | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| TPMI SST | SST_CLOS_CONFIG[0].max, SST_CLOS_CONFIG[3].max | RW (BIOS) | HP and LP core frequency ceilings; set by BIOS from SST_TF_INFO fuses | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_TF_INFO_10 (DLCP) | RO | PCT HP module mask per die; discovered by OS SST tool | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| MSR | 0x1AD (PRIMARY_TURBO_RATIO_LIMIT) | RW | HP TRL ratio overridden by BIOS with SST_TF_INFO_2.RATIO_0 when PCT active | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| MSR | IA32_HWP_CAPABILITIES (0x771) per core | RO | highest_perf: HP cores report P0max, LP cores report LP clip (DLCP mode) | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| TPMI Socket RAPL | SOCKET_RAPL_PL1_CONTROL (.PWR_LIM, .TIME_WINDOW, .PWR_LIM_EN) | RW | Socket RAPL PL1 limit; **NWP: MSR 0x610/0x638 deprecated (BIOS HSD 14018460453)** — use TPMI path instead | MCP query 2026-05-29; [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| NWP HP core count | 8 HP cores (2 per partition × 4 partitions) | CCB [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) |
| NWP PCT frequency target | 4.4 GHz (POR-1; fallback to legacy SST-TF) | CCB [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) |
| NWP CBB topology | 2 CBBs × 48 cores = 96 cores total | NWP architecture |
| HP TRL buckets | 3 (SSE/CDYN-indexed); LP: 1 bucket (LP_CLIP ratio) | Primecode `sst_tpmi_compute.cpp` |
| PCT vs SST-BF | ❌ Mutually exclusive (SST-BF ZBB’d on NWP) | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| DLCP activation | PCT_Module_Mask fuse + SST_TF_INFO_10 register; NWP: DLCP not explicitly referenced — manufacturing fused core masks via CLOS used instead | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| Default HP core | First processor per partition = lowest APIC ID in MADT order (P-cores first) | DMR CBB spec, MCP query 2026-05-29 |
| LP clip ratio | ≥ P1_Lo (fused per SKU via SST_TF_CONFIG); NWP SKU-specific value TBD | NWP MCP query 2026-05-29 |
| RAPL PID period | 1 ms (standard PCode RAPL loop) | [CBB SST Manager FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/SST_manager/cbb_SST_manager_FAS.html) |
| RAPL-PCT throttle order | LP cores drop frequency first; HP maintained at PCT TRL until LP at minimum, then HP reduced | SST HAS §Ordered Throttling; MCP query 2026-05-29 |
| NWP RAPL PL1 interface | TPMI `SOCKET_RAPL_PL1_CONTROL.PWR_LIM`; MSR 0x610/0x638 deprecated (BIOS HSD 14018460453) | MCP query 2026-05-29 |

## NWP Delta

### NWP PCT Status: ✅ Supported

PCT is one of only **2 SST features supported on NWP** (out of 7 on DMR). All other SST features are ZBB'd:

| SST Feature | NWP Status | HSD |
|-------------|-----------|-----|
| SST-PP Dynamic | ZBB'd | [22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) |
| SST-PP Static | ZBB'd | [22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) |
| SST-PP [HGS] | ZBB'd | [22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) |
| SST-CP | ZBB'd | [22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) |
| SST-BF | ZBB'd | [22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) |
| **SST-TF** | **Supported** | PCT profile for SST-TF |
| **PCT** | **Supported** | [14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) |

### NWP PCT Configuration

| Parameter | NWP Value | Source |
|-----------|-----------|--------|
| PCT core count | **8 HP cores** | CCB 14026595435 |
| PCT frequency target | **4.4 GHz** | CCB 14026595435 (POR-1, trending) |
| Status | POR-1 | Fallback to legacy SST-TF flow if Vrel risk materializes |
| CBB topology | 2 CBBs × 48 cores = **96 cores total** | NWP architecture |
| Default partitions | 4 → 24 cores/partition | 96 ÷ 4 = 24 |
| HP cores per partition | 2 (8 total ÷ 4 partitions) | Standard PCT algorithm |

### NWP Topology Impacts on PCT

- **2 CBBs (not 4)**: DMR has 4 CBBs × 32 cores; NWP has 2 CBBs × 48 cores. Partition algorithm divides across fewer, larger dies.
- **CPUID leaf 0x1F**: Cdie ID and Core ID bit positions are discovered via CPUID 0x1F (same as DMR, differs from GNR which used fixed bit[8:7] / bit[6:1]).
- **No SST-PP switching**: Since SST-PP is ZBB'd, cross-product interaction between PCT and dynamic PP switching is eliminated. PCT operates on the single boot PP level only.
- **MADT structure**: NWP die topology (NIO + 2 CBBs) produces a different MADT "Processor Local x2APIC" ordering than DMR (2 IMH + 4 CBBs). Partition → core mapping must be validated.

### DMR Evolution Applied to NWP

- **PCT Enable knob eliminated**: On DMR+, the standalone "PCT Enable" knob is integrated into "PCT Partition Count" (default = 0 = disabled). This DMR change carries to NWP.
- **CAPID4.bit29 not used**: DMR and NWP do not use CAPID4.bit29 for PCT capability (GNR-only). All parts can operate in either PCT or non-PCT mode.
- **DLCP support**: Confirm whether NWP uses DLCP (PCT_Module_Mask fuse + SST_TF_INFO_10) or legacy arbitrary core selection.

### RAPL-PCT Ordered Throttling on NWP

When RAPL PL1 enforces TDP and PCT is active, PCode distributes the frequency reduction in priority order:
1. LP cores are throttled first (frequency drops toward LP_CLIP_RATIO_0 minimum).
2. HP cores maintain PCT TRL frequency while LP cores still have headroom above minimum.
3. Only after LP cores reach minimum frequency are HP cores reduced.
4. `SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1` (Ordered) is the register that enables this behavior.

On NWP, the RAPL PL1 limit is read and enforced via TPMI `SOCKET_RAPL_PL1_CONTROL` (not MSR — MSR 0x610/0x638 are deprecated).

### Open Items

| Area | Status | Notes |
|------|--------|-------|
| DLCP on NWP | ⚠ Partially resolved | DLCP not explicitly referenced in NWP spec; manufacturing fused core masks via CLOS interface used instead. Arbitrary SW selection possible but manufacturing recommends fused mask for thermal/reliability. Confirm via BIOS FAS when available. |
| Vrel risk | ⚠ Open | CCB 14026595435 notes Vrel risk — if it materializes, PCT falls back to legacy SST-TF. Current status: trending POR. |
| BIOS knob exposure | ✅ Confirmed | PCT Partition Count and PCT Core Select BIOS knobs are exposed on NWP (NWP MCP query 2026-05-29). Warm reset required for changes. |
| LP clip frequency | ⚠ Partially resolved | MCP confirms LP clip ≥ P1_Lo, fused per SKU via SST_TF_CONFIG. NWP SKU-specific LP clip ratio value still needs confirmation from BIOS FAS or TPMI dump. |

## Legacy (Human-Curated Reference)

### Architecture Summary

**PCT (Priority Core Turbo)** is a **distinct, separately tracked feature** that leverages Intel SST-TF (Speed Select Technology — Turbo Frequency) as its underlying mechanism. It allows a small number of **High Priority (HP)** cores (typically 4 or 8) to operate at an elevated turbo frequency (up to P0max) while remaining **Low Priority (LP)** cores are clipped to approximately P1, freeing power budget for the HP cores.

#### PCT vs SST-TF — Feature Distinction

PCT is **not** simply another name for SST-TF. Evidence from multiple sources confirms PCT is tracked as its own feature:

| Evidence | Source |
|----------|--------|
| `[DMR-CCB] Support Priority Core Turbo (PCT) for DMR` — separate feature item (HSD 14023051596, priority 2-high, domain power_and_perf) | [DMR Overview HAS — CBB Feature List](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/DMR_Overview_HAS.html) |
| `PCT (Priority Core Turbo) HAS` — standalone architecture specification | [PM Server Index](https://docs.intel.com/documents/pm_doc/src/server/index.html) |
| `PCT (Priority Core Turbo) White Paper` — separate public-facing document | [PM Server Index](https://docs.intel.com/documents/pm_doc/src/server/index.html) |
| DLCP (Die Level Cherry Picking) — PCT-specific implementation evolution with its own fuses (`PCT_Module_Mask`) and registers (`SST_TF_INFO_10`) | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| CAPID4.bit29 — dedicated PCT enable fuse separate from SSTTF_ENABLE | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |

**Summary**: SST-TF is the **mechanism** (CLOS-based frequency partitioning via TPMI). PCT is the **feature** (partitioned core topology with elevated turbo for GPU-bound workloads) that uses SST-TF. PCT adds: BIOS partition/core-select knobs, DLCP die-level cherry picking, DQ rules (mutex with SST-BF/FCT), and its own CAPID/fuse/LIRA enablement.

#### How It Works
1. **BIOS** discovers PCT capability (CAPID4.bit29 on GNR; partition-count based on DMR+) and divides all available physical cores into **N partitions** (default N=4).
2. **BIOS** selects one or more consecutive cores per partition as HP cores (default: first core(s) in each partition).
3. **BIOS** programs SST-TF TPMI CLOS registers — HP cores subscribe to CLOS[0] (max = PCT TRL ratio), LP cores to CLOS[3] (max = LP clip ratio ~P1).
4. **PCode** runs the **legacy SST-TF flow** unchanged — from PCode's perspective, PCT is identical to SST-TF.
5. **OS/SW** schedules high-priority workloads onto HP cores (identified via MADT, HWP MSR, or SST tool).

#### Frequency Hierarchy

| Level | Description | Example |
|-------|-------------|---------|
| P0max | Maximum turbo frequency | 4.6 GHz |
| F3 | PCT HP frequency (≤ P0max) | 4.4–4.6 GHz |
| P0half | Half-core turbo (requires C6 on half cores) | 3.9 GHz |
| P0n | All-core turbo | 3.6 GHz |
| F2 | LP clipped frequency (~P1) | 2.3 GHz |
| P1 | All-core guaranteed frequency | — |
| Pn | Minimum core frequency | — |

#### Key Design Points
- **No C6 requirement**: Unlike P0half, PCT elevates HP core frequency without requiring other cores to sleep in C6 — LP cores stay active at clipped frequency.
- **GPU/Accelerator use case**: Primary target is CPU+GPU systems where a few cores per partition are dedicated to GPU servicing and need maximum frequency.
- **Runtime reconfiguration**: Users can use the Intel SST tool to enable/disable PCT and reassign HP/LP cores at OS runtime.
- **Virtualization**: VMM assigns HP logical cores to specific VMs. PCT is SoC-wide — if SST-TF is active, all LP cores across all VMs are clipped.

#### DLCP (Die Level Cherry Picking) — Implementation Evolution

DLCP extends PCT by fixing HP core positions at specific physical die locations via the `PCT_Module_Mask` fuse, rather than allowing arbitrary SW selection:
- `PCT_Module_Mask` fuse encodes HP core/module assignment (per CBB die, per PP level)
- `SST_TF_INFO_10` TPMI register exposes the mask for SW discovery
- PCode reports different `HWP_CAPABILITY.highest_perf` for HP vs LP cores
- DLCP and legacy TF core selection are mutually exclusive
- SW discovers HP cores via: HWP MSR enumeration, Linux SST tool, or direct TPMI access


### Execution Flow

```
1. BIOS Boot
   ├── Read CAPID4.bit29 (GNR) or PCT Partition Count knob (DMR+)
   ├── If PCT not supported/disabled → skip, conventional turbo
   ├── Discover available cores (exclude BIST-failed / BIOS-disabled)
   ├── Divide cores into N partitions (default 4)
   ├── Select HP cores per partition (default: first core(s))
   └── Program SST-TF TPMI registers on each dielet:
       ├── SST_CLOS_CONFIG[0].min = P1, .max = SST_TF_INFO_2.RATIO_0  (HP)
       ├── SST_CLOS_CONFIG[3].min = Pn, .max = SST_TF_INFO_0.LP_CLIP_RATIO_0  (LP)
       ├── SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1 (Ordered Throttling)
       ├── SST_CLOS_ASSOC[] → HP cores → CLOS[0], LP cores → CLOS[3]
       ├── SST_PP_CONTROL.feature_state[1] = 1
       └── Override MSR 0x1AD (TRL) with SST_TF_INFO_2.RATIO_0

2. PCode Runtime
   └── Runs legacy SST-TF flow (identical to non-PCT SST-TF)
       ├── Enforces CLOS-based frequency limits
       ├── HP cores → up to PCT TRL ratio
       └── LP cores → clipped to LP_CLIP frequency

3. OS Runtime (optional reconfiguration)
   └── Intel SST tool can:
       ├── Enable/disable PCT dynamically
       ├── Reassign HP/LP cores
       └── Query HP core identification
```


### Key Registers & Interfaces

#### TPMI SST Registers (per dielet)

| Register | Description |
|----------|-------------|
| `SST_CLOS_CONFIG[0]` | HP core frequency bounds: min=P1, max=PCT TRL ratio |
| `SST_CLOS_CONFIG[3]` | LP core frequency bounds: min=Pn, max=LP clip ratio |
| `SST_CP_CONTROL` | `.SST_CP_PRIORITY_TYPE = 1` (Ordered Throttling) |
| `SST_CLOS_ASSOC[0..N]` | Per-core CLOS assignment (HP→CLOS[0], LP→CLOS[3]) |
| `SST_PP_CONTROL` | `.feature_state[1] = 1` activates PCT/TF |
| `SST_TF_INFO_0` | LP clip ratio per CDYN index |
| `SST_TF_INFO_2` | HP TRL ratio (bucket 0 = PCT bucket) |
| `SST_TF_INFO_10` | DLCP PCT HP module mask (new, per die per PP) |

#### Fuses

| Fuse | Description |
|------|-------------|
| `CAPID_CAPID4_29_rsvd` | PCT_ENABLE: 1=supported, 0=not (GNR only; DMR/NWP do not use this fuse) |
| `PCT_ENABLE` (LIRA) | Enabled/Disabled — indicates PCT support for SKU |
| `PCT_Module_Mask` | DLCP: per-CBB per-PP HP module assignment mask |
| `SST_TF_CONFIG_[0..4]_LP_CLIP_RATIO_CDYN_INDEX[0..5]` | LP clipping ratio per config/CDYN |
| `SST_TF_CONFIG_[0..4]_TURBO_RATIO_LIMIT_CORES_NUMCORE[0..2]` | HP core count per TRL bucket |
| `SST_TF_CONFIG_[0..4]_TURBO_RATIO_LIMIT_RATIOS_CDYN_INDEX[0..5]_RATIO[0..2]` | HP TRL ratio per bucket |

#### MSRs

| MSR | Description |
|-----|-------------|
| `0x1AD` (Turbo_Ratio_Limit) | BIOS overrides with SST_TF_INFO_2.RATIO_0 when PCT active |
| `IA32_HWP_CAPABILITIES` | `.highest_perf` — DLCP: per-core HP vs LP distinction |

#### BIOS Knobs

| Knob | Options | Default | Notes |
|------|---------|---------|-------|
| PCT Enable | Enable / Disable | Enable | GNR: hidden if CAPID4.bit29=0. DMR+: integrated into Partition Count |
| PCT Partition Count | Auto / Manual | Auto (=4) | Manual: user-specified, min=1, max ≤ SKU PCT core count |
| PCT Core Select | Auto / Manual | Auto (=first core) | Manual: starting core position offset |

#### DQ Rules
- PCT requires `SSTTF_ENABLE = Enabled`
- PCT is **mutually exclusive** with SST-BF
- PCT is **mutually exclusive** with FCT (Favored Core Turbo)


### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [PCT HAS (Arch Common)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) | Authoritative PCT architecture spec (Rev 0.81, Oct 2025) |
| HAS | [IC PCT White Paper (Arch Common)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/IC_PCT.html) | Public-facing PCT Technology white paper |
| HAS | [Intel SST HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST-TF underlying framework |
| HAS | [SST TPMI HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/IC_SST_TPMI.html) | TPMI register definitions for SST |
| HAS | [DMR SST Features](https://docs.intel.com/documents/pm_doc/src/server/DMR-HBM/PM%20Features/DMR_SST_Features.html) | DMR SST-TF/PCT implementation |
| HAS | [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) | DMR PM roadmap (SST-TF confirmed) |
| FAS | [Primecode SST FHAS (DMR)](https://docs.intel.com/documents/primecode/fhas/DMR/SST/SST.html) | Primecode SST-TF firmware flows |
| FAS | [CBB SST Manager FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/SST_manager/cbb_SST_manager_FAS.html) | CBB PCode SST manager (leaf) |
| BIOS FAS | [Oakstream CPUPM FAS](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Dmr/DMR/Oakstream_CPUPM_FAS.html) | BIOS PCT programming flow |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS — SST-TF (PCT profile) confirmed |
| CCB | [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) | NWP: Support 8 PCT cores |
| CCB | [HSD 14026595435 — DLCP](https://hsdes.intel.com/appstore/article/#/14026595435) | DLCP implementation |
| CCB | [HSD 14023051596](https://hsdes.intel.com/appstore/article/#/14023051596) | DMR-CCB: Support Priority Core Turbo (PCT) for DMR (2-high, power_and_perf) |
| CCB | [HSD 14024172012](https://hsdes.intel.com/appstore/article/#/14024172012) | DMR: SST TF INFO reg changes (3-medium, power_management) |
| SoC HAS | [DMR SoC Overview HAS](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/DMR_Overview_HAS.html) | DMR die partitioning, CBB feature list (confirms PCT as distinct feature) |
| Index | [PM Server Spec Index](https://docs.intel.com/documents/pm_doc/src/server/index.html) | Lists PCT HAS and PCT White Paper as standalone documents |
| Comparison | [DMR vs NWP PM Comparison](../../dmr_vs_nwp_pm_comparison.html) | Feature-level support/ZBB matrix |


### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->

### Test Cases

| HSD | Title | Scope | Test Tool |
|-----|-------|-------|-----------|
| [22022422105](https://hsdes.intel.com/appstore/article/#/22022422105) | PCT - Default HP core selection | NWP, Active PM | `runPmx.py -x nwp.xml -p pct -tM 60 -M 10 --retry_count 2` |
| [22022422117](https://hsdes.intel.com/appstore/article/#/22022422117) | PCT - Verify TDP convergence | NWP, Active PM | `runPmx.py -x nwp.xml -p pct -tM 60 -M 10 --retry_count 2` |

**22022422105 — Test Intent**: Verifies the default HP core selection algorithm — SW divides all available processors into N partitions (default N=4) and the first processor in each partition (lowest APIC ID) is configured as the PCT HP core assigned to CLOS[0]. Validates BIOS-programmed SST-TF TPMI registers reflect this assignment correctly.

**22022422117 — Test Intent**: Verifies RAPL TDP convergence behavior under PCT. Enables PCT, runs PTAT workload on all 96 cores, applies RAPL PL1 limit, then verifies: (1) power converges to PL1; (2) LP cores drop frequency first (ordered throttling: SST_CP_PRIORITY_TYPE=1); (3) HP cores maintain PCT frequency while LP cores still have headroom above minimum; (4) HP TRL frequency is preserved until LP cores reach minimum. Uses TPMI `SOCKET_RAPL_PL1_CONTROL` (MSR deprecated on NWP).


### Source Notes

| Claim Category | Confidence | Source |
|---------------|------------|--------|
| PCT as distinct feature (not SST-TF alias) | ✅ Confirmed | [DMR Overview HAS — CBB Feature List](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/DMR_Overview_HAS.html) (row 58: HSD 14023051596), [PM Server Index](https://docs.intel.com/documents/pm_doc/src/server/index.html) |
| CLOS-based frequency partitioning | ✅ Confirmed | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| `SST_CLOS_CONFIG`, `SST_CLOS_ASSOC`, `SST_CP_CONTROL` registers | ✅ Confirmed | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html), [SST TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/IC_SST_TPMI.html) |
| CAPID4.bit29 PCT enable fuse | ✅ Confirmed | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| DLCP (`PCT_Module_Mask`, `SST_TF_INFO_10`) | ✅ Confirmed | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| DQ rules (mutex SST-BF, FCT) | ✅ Confirmed | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| BIOS programming flow (partition, core select, TPMI registers) | ⚠ FAS-derived | [Oakstream CPUPM FAS](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Dmr/DMR/Oakstream_CPUPM_FAS.html) — not directly verified in this pass |
| PCode runs legacy SST-TF flow unchanged | ⚠ FAS-derived | [CBB SST Manager FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/SST_manager/cbb_SST_manager_FAS.html) — not directly verified |
| Frequency hierarchy values (P0max, F3, etc.) | ⚠ Illustrative | Example values from PCT HAS; actual NWP values depend on SKU |
| BIOS knobs (PCT Enable, Partition Count, Core Select) | ⚠ FAS-derived | [Oakstream CPUPM FAS](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Dmr/DMR/Oakstream_CPUPM_FAS.html) |
| NWP 8 HP cores @ 4.4GHz | ⚠ HSD | [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) (POR-1, trending) |
| NWP topology impacts (2 CBBs × 48 cores) | ⚠ Inferred | NWP architecture; not from a single authoritative spec passage |
| NWP PCT Enable knob eliminated (DMR+) | ⚠ Inferred | From DMR PCT HAS pattern; NWP BIOS FAS not directly verified |
| LP clip ratio | ⚠ Partially resolved — MCP confirms LP clip ≥ P1_Lo (fused per SKU via SST_TF_CONFIG); NWP SKU-specific value still needs BIOS FAS or TPMI dump confirmation |
| PCT × C6 interaction | All 5 PV test cases are "Only_On_N" — NWP C6 is supported but PkgC6 is ZBB'd. Verify half-core turbo (P0half) behavior when PCT is also active. |
| BIOS knob exposure | ✅ Confirmed — PCT Partition Count and Core Select knobs are exposed; warm reset required for changes (NWP MCP query 2026-05-29) |

#### Collateral
- [DMR vs NWP PM Comparison](../../dmr_vs_nwp_pm_comparison.html) — SST section confirms PCT supported, 5 other SST features ZBB'd
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — Section 3 ZBB list: SST-TF (PCT profile) supported
