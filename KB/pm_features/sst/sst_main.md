# SST — Main Flow

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Generated**: 2026-05-23 from nwp_pm_test_cases.json (69 TCs)
> **Source Confidence**: High — all 12 subflows enriched from source analysis.

## Baseline (DMR)

**SST (Speed Select Technology)** is a family of features enabling runtime CPU power/frequency configuration. SST provides TPMI-based interfaces for performance profile selection (SST-PP), CLOS-based core frequency partitioning (SST-TF), core priority throttling (SST-CP), base-frequency boost (SST-BF), and hardware-guided scheduling (HGS). Fuses define all per-level capability; TPMI registers expose them to BIOS and OS.

**Topology (NWP)**: 2 CBBs (48 cores each) + 1 IMH-P. Only SST-TF (via PCT) is active. SST-PP, SST-CP standalone, SST-BF, and HGS are ZBB’d.

```
  BIOS / OS / BMC                SST Feature Stack (NWP)
  ┌────────────────┐     ┌──────────────────────────────┐
  │ SST tool       │     │ SST-TF (Turbo Frequency)  ✅ │
  │ TPMI driver    │     │ SST-PP (Perf Profile)     ❌ │
  │ B2P mailbox    ├────►│ SST-CP (Core Power)       ❌ │
  │ OOB (BMC)      │     │ SST-BF (Base Freq)        ❌ │
  └────────────────┘     │ HGS (HW-Guided Sched)    ❌ │
                         │ PCT (Priority Core Turbo) ✅ │
                         └───────┤──────────────────┘
                               │
                    ┌─────────┴──────────────┐
                    │ Fuse controller → TPMI regs   │
                    │ PrimeCode (src/flow/sst/)    │
                    │ PCode (sst_manager.cpp)       │
                    └────────────────────────────┘
  ✅ = NWP Active    ❌ = NWP ZBB’d
```

**Boot activation**: SST-TF/PCT enabled at BIOS CPL3 via partition count knob. TPMI registers populated at reset Phase 5 from fuses. OS discovers feature set via `SST_HEADER.CAPABILITY_MASK`.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| TPMI SRAM | IMH-P die | Stores all SST register banks (HEADER, PP, TF, CP, CLOS); NVM-backed; survives PkgC | SST_HEADER, SST_PP_*, SST_TF_INFO_*, SST_CP_*, SST_CLOS_* | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Fuse controller | IMH die | All SST feature-enable bits + per-level TRL/P1/clip arrays; read at reset Phase 5 | SST_PP_LEVEL_EN_MASK, SST_TF_ENABLE, PCT_ENABLE, PCT_Module_Mask, TRL arrays | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Core FIVR + PLL | CBB compute | Applies CLOS-based frequency limits (HP: P0max ceiling, LP: ~P1 clip) per workpoint calc | Per-CLOS ratio enforcement | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| P2U Mailbox | CBB compute | PCode→Ucode channel for HGS performance table writes (ZBB’d on NWP) | P2U opcode HGS | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PCode (CBB) | Root + Leaf CBB | SST state machine (sst_manager.cpp): PP changes, CP enable/priority, TF enable/disable, HGS ranking; TRL management (trl_manager.cpp): 4 TRL tables, CDYN-indexed | `sst_manager.cpp`, `trl_manager.cpp`, `ccp_manager.cpp` | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| PrimeCode (IMH-P) | IMH-P | SST TPMI register init at reset Phase 5: reads all SST fuses, writes HEADER/PP_HEADER/PP_INFO/TF_INFO/CP_HEADER; warm boot: repopulateFromTpmiReg | `sst_tpmi_general.cpp::tpmiInit()`, `sst_tpmi_compute.cpp`, `sst_common.cpp` | Primecode source |
| BIOS | Pre-OS | SST knob configuration (PP level, PCT partition count, lock bit); HWP enable; CLOS programming for PCT | BIOS PM knobs; CPUPM FAS | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| Acode | Compute core | Executes at PCode-assigned CLOS ratio; no direct SST flow in Acode | Architecture reference | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| TPMI SST | SST_HEADER.CAPABILITY_MASK | RO | Feature capability bitmap; OS discovers available features at boot | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_PP_CONTROL / SST_PP_STATUS / SST_PP_INFO_0..11 | RW/RO | PP level control, status, and per-level configuration data | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_CP_CONTROL / SST_CLOS_CONFIG_* / SST_CLOS_ASSOC_* | RW | CLOS priority and per-core assignment (active via PCT on NWP) | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| MSR | 0x1AD (PRIMARY_TURBO_RATIO_LIMIT) | RW | HP TRL override; written by BIOS from SST_TF_INFO_2.RATIO_0 when TF active | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| MSR | IA32_HWP_CAPABILITIES (0x771) per core | RO | highest_perf: HP vs LP differentiation under PCT/DLCP | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| NWP active SST features | 2 of 7 (SST-TF + PCT); SST-PP, SST-CP, SST-BF, HGS ZBB’d | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| NWP PCT HP core count | 8 HP cores across 4 partitions (2 per partition; 2 CBBs × 48 cores) | CCB HSD 14026595435 |
| NWP PCT frequency target | 4.4 GHz (POR-1) | CCB HSD 14026595435 |
| Subflow count | 12 subflows, 69 total test cases | NWP test plan |
| TPMI SST register init phase | Reset Phase 5 (cold and warm boot) | Primecode reset sequence |
| SST state across warm reset | FWU_VAR preserves: pp_level, tf_enabled, cp_enabled, pp_locked, cp_priority_type | PCode `sst_manager.cpp` |

## NWP Delta

### NWP SST Scope

NWP supports only the PCT profile for SST-TF. All other SST sub-features are ZBB’d.

| Sub-feature | DMR Status | NWP Status | Notes |
|-------------|-----------|------------|-------|
| SST-TF | ✅ Active | ✅ Active | Underlying mechanism for PCT |
| PCT | ✅ Active | ✅ Active | Primary NWP interface; 8 HP cores, 4 partitions |
| SST-PP dynamic | ✅ Active | ❌ ZBB’d | [HSD 22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) |
| SST-CP standalone | ✅ Active | ❌ ZBB’d | CP ordered throttling active as PCT mechanism |
| SST-BF | ✅ Active | ❌ ZBB’d | [HSD 22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) |
| HGS | ✅ Active | ❌ ZBB’d | `ok_going_zero.txt` lines 195–197 |

### NWP Reference

| Field | Value |
|-------|-------|
| HAS ref | NWP HAS: PCT profile for SST-TF only |
| MAS ref | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html): SST-TF (PCT profile). ZBB: SST-CP, SST-PP, SST-BF, Favored Core w/ DCM |
| CCB | [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) — NWP: Support 8 PCT cores |
| Test cases | 69 total TCs across 12 subflows; NWP-active TCs via PCT subflow (21 TCs) and TF subflow (15 TCs) |

## Legacy (Human-Curated Reference)

### NWP Spec Context
| Field | Value |
|-------|-------|
| HAS ref | NWP HAS: PCT profile for SST-TF only |
| MAS ref | NWP PM MAS: SST-TF (PCT profile). ZBB: SST-CP, SST-PP, SST-BF, Favored Core w/ DCM |
| NWP delta | NWP keeps only PCT profile for SST-TF. SST-CP/PP/BF/HGS all ZBB'd. |
| NWP supported | True (SST-TF via PCT only) |


### Architecture Summary

**SST (Speed Select Technology)** is a family of features that allow runtime tuning of CPU power/frequency characteristics. SST provides multiple sub-features that interact through fuses, TPMI registers, and B2P mailbox commands:

```
  BIOS / OS / BMC                SST Feature Stack
  ┌────────────────┐     ┌──────────────────────────────┐
  │ SST tool       │     │ SST-TF (Turbo Frequency)  ✅ │
  │ TPMI driver    │     │ SST-PP (Perf Profile)     ❌ │
  │ B2P mailbox    ├────►│ SST-CP (Core Power)       ❌ │
  │ OOB (BMC)      │     │ SST-BF (Base Freq)        ❌ │
  └────────────────┘     │ HGS (Hw-Guided Sched)     ❌ │
                         │ PCT (Perf Config Tool)    ✅ │
                         └─────────┬────────────────────┘
                                   │
                         ┌─────────┴────────────────────┐
                         │ PCode (sst_manager.cpp)       │
                         │ Primecode (src/flow/sst/)     │
                         │ Fuse controller → TPMI regs   │
                         └──────────────────────────────┘
  ✅ = NWP Active    ❌ = NWP ZBB'd
```

#### NWP SST Scope Summary

| Sub-feature | DMR | NWP | Notes |
|-------------|-----|-----|-------|
| SST-TF | ✅ Active | ✅ Active | Turbo Ratio Limits via PCT profile |
| PCT | ✅ Active | ✅ Active | Performance Configuration Tool — primary user interface |
| SST-PP | ✅ Active | ❌ ZBB'd | Multi-TDP performance profiles |
| SST-CP | ✅ Active | ❌ ZBB'd (standalone) | CLOS prioritization (active as PCT mechanism) |
| SST-BF | ✅ Active | ❌ ZBB'd | Base Frequency boost for favored cores |
| HGS | ✅ Active | ❌ ZBB'd | Hardware-Guided Scheduling |


### FW Agents

- **PCode (CBB Punit)**: SST state machine (`sst_manager.cpp`), TRL management, PP level changes, CP CLOS enforcement, HGS core ranking
- **Primecode (IMH Punit)**: SST TPMI register initialization, fuse-to-register propagation, PP/CP/BF/TF TPMI headers, B2P mailbox commands
- **BIOS**: SST knob configuration, PP level selection at boot, lock bit control
- **BMC (OOB)**: Runtime PP/CP/TF changes via TPMI OOB path


### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Intel SST HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST master architecture |
| HAS | [SST TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/IC_SST_TPMI.html) | SST TPMI register interface |
| HAS | [PCT HAS (Arch Common)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) | PCT architecture |
| HAS | [IC PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/IC_PCT.html) | IC PCT implementation |
| HAS | [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) | TPMI interface |
| HAS | [NWP BIOS HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/BIOS/NWP.html) | BIOS SST knobs |
| HAS | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) | Turbo/TRL interaction with SST-TF |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS |
| Primecode src | `src/flow/sst/sst_common/` | Core SST class, fuse access |
| Primecode src | `src/flow/sst/sst_tpmi_general/` | TPMI register init |
| PCode src | `source/pcode/flows/sst/sst_manager.cpp` | SST runtime state machine |
| PCode src | `source/pcode/flows/trls/trl_manager.cpp` | TRL management |


### Related Sightings

No DMR SST-specific showstopper sightings identified in retrospective.


### Subflows (12)

| # | Subflow | Status | TCs | Segment | NWP Status |
|---|---------|--------|-----|---------|------------|
| 1 | [Cross-Product](cross_product.md) | Enriched | 2 | Mixed | Active (SST-TF related) |
| 2 | [Flex Ratio](flex_ratio.md) | Enriched | 1 | FV | Active |
| 3 | [Fuse](fuse.md) | Enriched | 4 | PSS/PV | Active (fuse verification) |
| 4 | [HGS](hgs.md) | Enriched | 2 | FV | ❌ ZBB'd |
| 5 | [HWP Cross-Product](hwp_cross_product.md) | Enriched | 3 | PV | ⚠ Partial |
| 6 | [PCT](pct.md) | Enriched | 21 | Mixed | ✅ Active |
| 7 | [PP](pp.md) | Enriched | 12 | FV/PV | ❌ ZBB'd |
| 8 | [RAPL](rapl.md) | Enriched | 1 | PV | Active (RAPL SST interaction) |
| 9 | [Reset](reset.md) | Enriched | 2 | PV | ⚠ Partial |
| 10 | [SST-CP](sst_cp.md) | Enriched | 5 | PSS/PV | ❌ ZBB'd (standalone) |
| 11 | [TF](tf.md) | Enriched | 15 | Mixed | ✅ Active |
| 12 | [TRL](trl.md) | Enriched | 1 | FV | ✅ Active |
| | **Total** | 12/12 enriched | **69** | | |
