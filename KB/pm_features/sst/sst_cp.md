# SST > SST-CP

## Baseline (DMR)

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SST](sst_main.md)
> **Source Confidence**: High — Architecture from PCode `sst_manager.cpp` (`update_sst_cp_config`), Primecode `sst_tpmi_general.cpp` (`sstCpInit`), TPMI OSXML CP register definitions, fuse `SST_CP_ENABLE`.

### What is SST-CP?
**SST-CP (Core Power)** provides CLOS-based core frequency partitioning, allowing the OS or VMM to assign cores to different **CLOS (Class of Service)** groups with distinct frequency min/max limits and priority levels. When power-constrained, PCode allocates frequency budget preferentially to higher-priority CLOS groups, enabling workload-aware core prioritization.

### Topology
- TPMI SST-CP register space lives on each CBB instance (same as other SST sub-features).
- CLOS configuration registers (`SST_CLOS_CONFIG_0..N`, `SST_CLOS_ASSOC_0..N`) are in TPMI SRAM, initialized by Primecode.
- PCode HPM message `COMPUTE_CLOS_CONFIG` propagates CLOS config Root → Leaf.
- SST-CP is **ZBB’d on NWP** as a standalone user feature; CLOS ordered throttling remains active via PCT.

### Operating Principle
SW enables CP by writing `SST_CP_CONTROL.SST_CP_ENABLE = 1`. PCode `update_sst_cp_config()` validates fuse and HWP state. CLOS group frequency bands are programmed by SW; PCode enforces per-CLOS min/max during RAPL arbitration. Priority mode selects Ordered (strict) or Proportional (weighted) scheduling.

### Boot-Time Init
Primecode `sstCpInit()` initializes `SST_CP_HEADER`, `SST_CP_CONTROL` (disabled), `SST_CP_STATUS` (clear), `SST_CLOS_CONFIG_*` (unconstrained defaults), `SST_CLOS_ASSOC_*` (all cores in CLOS 0).

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| TPMI SRAM (SST-CP) | CBB | CLOS config register storage: HEADER, CONTROL, STATUS, CLOS_CONFIG, CLOS_ASSOC | Primecode init writes; PCode reads CLOS enforcement config | Intel SST HAS §SST-CP Registers |
| Fuse controller | CBB | `SST_CP_ENABLE` gates CP capability bit in `SST_HEADER.CAPABILITY_MASK[0]` | CP enabled only when fuse set + HWP enabled | fuses_sst.xml |
| Core FIVR + P-state arbiter | Compute | Enforces per-CLOS min/max frequency limits under power constraint | PCode drives CLOS-aware budget allocation | Intel SST HAS §SST-CP |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PCode | `source/pcode/flows/sst/sst_manager.cpp` | Validates CP enable request against fuse+HWP; applies CLOS config; handles excursion tracking | `update_sst_cp_config()`, `CLOS_*_LIMIT` from RAPL_PERF_LIMIT HPM | PCode sst_manager.cpp |
| PCode HPM | `source/hpm/hpm_msgs.xml` | Propagates CLOS config Root→Leaf via `COMPUTE_CLOS_CONFIG`; receives `RAPL_PERF_LIMIT` with CLOS fields | `COMPUTE_CLOS_CONFIG`, `RAPL_PERF_LIMIT` | hpm_msgs.xml |
| PrimeCode | `src/flow/sst/sst_tpmi_general/v2_0/sst_tpmi_general.cpp` | Initializes all CP TPMI registers at reset | `sstCpInit()`: HEADER, CONTROL, STATUS, CLOS_CONFIG, CLOS_ASSOC | sst_tpmi_general.cpp |
| BIOS | Platform init | Configures initial CLOS assignments for SMM/BIOS workloads if needed | Writes `SST_CLOS_ASSOC_*` before OS handoff | N/A |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| TPMI `SST_CP_CONTROL` | TPMI SST-CP offset | RW | Runtime CP enable + priority type select + excursion reset | Intel SST HAS §SST-CP Registers |
| TPMI `SST_CP_STATUS` | TPMI SST-CP offset | RO/V | Resolved CP enable + priority type + error type + excursion-to-min per CLOS | Intel SST HAS §CLOS Status |
| TPMI `SST_CLOS_CONFIG_0..N` | TPMI SST-CP offset | RW | Per-CLOS: MIN ratio, MAX ratio, proportional priority weight | Intel SST HAS §SST-CP Registers |
| TPMI `SST_CLOS_ASSOC_0..N` | TPMI SST-CP offset | RW | Core-to-CLOS assignment (2 bits per core, 4 CLOS groups) | Intel SST HAS §SST-CP Registers |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| CLOS count | 4 (typical NWP) | Primecode `CLOS_COUNTS` enum, sst_tpmi_general.hpp |
| Priority modes | 2: Ordered (0), Proportional (1) | Intel SST HAS §SST-CP, PCode sst_manager.cpp |
| CP fuse gate | `SST_CP_ENABLE` must = 1 + HWP must be enabled | fuses_sst.xml, update_sst_cp_config() |
| NWP standalone status | ❌ ZBB’d (standalone); ✅ Active as PCT mechanism (ordered throttling) | NWP PM MAS, HSD 22021155414 |
| ZBB negative test | TC 22022060653 validates CP/BF correctly disabled on NWP | NWP PM test plan |

## NWP Delta

### NWP Status: ❌ ZBB’d (standalone) / ✅ Active as PCT mechanism

SST-CP as a **standalone user-configurable feature** is ZBB’d on NWP. However, SST-CP **ordered throttling** (`SST_CP_PRIORITY_TYPE = 0`) remains active as the underlying mechanism for PCT’s CLOS-based HP/LP core partitioning.

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| SST-CP standalone | ❌ ZBB’d | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html), [HSD 22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) |
| SST-CP ordered throttling (via PCT) | ✅ Active | PCT sets CLOS groups; `SST_CP_PRIORITY_TYPE = Ordered` |\  
| CLOS_ASSOC / CLOS_CONFIG init | ✅ Required | Primecode `sstCpInit()` still runs for PCT support |\  
| ZBB negative validation | TC 22022060653 | Confirms CP/BF standalone are correctly disabled |

## Legacy (Human-Curated Reference)

*All original content preserved below for reference.*

### Architecture Summary

**SST-CP (Core Power)** provides CLOS-based core frequency partitioning, allowing the OS or VMM to assign cores to different **CLOS (Class of Service)** groups with distinct frequency min/max limits and priority levels. When power-constrained, PCode allocates frequency budget preferentially to higher-priority CLOS groups, enabling workload-aware core prioritization. SST-CP is **ZBB'd as a standalone feature on NWP** but remains **active as the underlying mechanism for PCT** (which uses CLOS groups to implement HP/LP core partitioning).

#### How It Works

1. **Fuse gate** — `SST_CP_ENABLE` fuse must be set. Also requires HWP enabled (`MISC_PWR_MGMT2.ENABLE_HWP`)
2. **Reset init** — Primecode `sstCpInit()` initializes:
   - `SST_CP_HEADER` (RO) — feature ID, revision, ratio unit
   - `SST_CP_CONTROL` (RW) — initialized to 0 (CP disabled)
   - `SST_CP_STATUS` (RO/V) — initialized to 0
   - `SST_CLOS_CONFIG_0` through `SST_CLOS_CONFIG_N` — default max=0xFF (unconstrained), min=0
   - `SST_CLOS_ASSOC_0` through `SST_CLOS_ASSOC_N` — default all-zeros (all cores in CLOS 0)
3. **Runtime enable** — SW writes `SST_CP_CONTROL.SST_CP_ENABLE = 1`. PCode `update_sst_cp_config()` validates against fuse and HWP state. If illegal, sets `SST_CP_STATUS.ERROR_TYPE = NOT_SUPPORTED_BY_HW` (0x1)
4. **CLOS configuration** — SW programs per-CLOS min/max ratios via `SST_CLOS_CONFIG_*` registers and assigns cores to CLOS groups via `SST_CLOS_ASSOC_*` registers
5. **Priority type** — `SST_CP_CONTROL.SST_CP_PRIORITY_TYPE` selects between Ordered (0) and Proportional (1) priority. Ordered: strict priority ordering. Proportional: frequency weight based on `CLOS_PROPORTIONAL_PRIORITY` field
6. **Excursion tracking** — `SST_CP_STATUS.EXCURSION_TO_MIN` tracks per-CLOS whether frequency dropped to minimum. SW clears via `SST_CP_CONTROL.RESET_EXCURSION_TO_MIN` (write-0-to-clear semantics)

#### CLOS Structure
- **CLOS count** = `SST_NUM_CLOS_LEVELS` (typically 4)
- Each CLOS group has: `MIN` (floor ratio), `MAX` (ceiling ratio), `CLOS_PROPORTIONAL_PRIORITY` (weight 0x0=max perf, 0xF=min perf)
- Cores are assigned to CLOS via `SST_CLOS_ASSOC_*` registers (2-bit CLOS ID per core)

### Key Registers & Interfaces

| Register | Access | Description |
|----------|--------|-------------|
| `SST_HEADER.CAPABILITY_MASK[0]` | RO | SST-CP capability — from `SST_CP_ENABLE` fuse |
| `SST_CP_HEADER` | RO | Feature ID, revision, ratio unit |
| `SST_CP_CONTROL.SST_CP_ENABLE` | RW | Runtime CP enable request |
| `SST_CP_CONTROL.SST_CP_PRIORITY_TYPE` | RW | 0=Ordered, 1=Proportional |
| `SST_CP_CONTROL.RESET_EXCURSION_TO_MIN` | RW | Write-0-to-clear excursion bits |
| `SST_CP_STATUS.SST_CP_ENABLE` | RO/V | Resolved CP enabled state |
| `SST_CP_STATUS.SST_CP_PRIORITY_TYPE` | RO/V | Reflected priority type |
| `SST_CP_STATUS.ERROR_TYPE` | RO/V | 0=no error, 1=not supported by HW |
| `SST_CP_STATUS.EXCURSION_TO_MIN` | RO/V | Per-CLOS excursion-to-min tracking |
| `SST_CLOS_CONFIG_0..N` | RW | Per-CLOS: MIN, MAX, PROPORTIONAL_PRIORITY |
| `SST_CLOS_ASSOC_0..N` | RW | Core-to-CLOS assignment (2 bits per core) |
| HPM `COMPUTE_CLOS_CONFIG` | HPM | Root→Leaf CLOS configuration; response provides package-scope counts for SST-TF |
| HPM `RAPL_PERF_LIMIT` | HPM | Contains `CLOS_*_LIMIT` fields driven by RAPL source |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Intel SST HAS — SST-CP Registers](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html#sst-cp-registers) | Full CP register definitions |
| HAS | [CLOS Status](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html#clos_status) | Excursion tracking semantics |
| PCode SST mgr | `source/pcode/flows/sst/sst_manager.cpp` | `update_sst_cp_config()` — CP enable/priority/excursion logic |
| PCode HPM msgs | `source/hpm/hpm_msgs.xml` | `COMPUTE_CLOS_CONFIG`, `RAPL_PERF_LIMIT` with CLOS fields |
| Primecode TPMI CP init | `src/flow/sst/sst_tpmi_general/v2_0/sst_tpmi_general.cpp` | `sstCpInit()` — HEADER/CONTROL/STATUS/CLOS_CONFIG/CLOS_ASSOC |
| Primecode TPMI header | `src/flow/sst/sst_tpmi_general/v2_0/sst_tpmi_general.hpp` | `CLOS_COUNTS`, capability mask enums |
| TPMI OSXML | `src/cfgdata/tpmi_osxml/v1_0/Struct_all.os.xml` | SST_CP_CONTROL/STATUS/CLOS_CONFIG bitfield definitions |
| Primecode fuse | `src/ip/fuse/v2_0/fuses_sst.xml` | `SST_CP_ENABLE` fuse definition |

### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->

