# SST > Fuse

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SST](sst_main.md)
> **Source Confidence**: High — Fuse definitions from Primecode `fuses_sst.xml`, frozen fuse XML, TPMI OSXML. PCode fuse references from `pcode_fuse.xml` / `pcode_frozen_fuses.rdl`. NWP scope from [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html).

## Baseline (DMR)

**SST Fuse** verification validates correct propagation of SST configuration fuses into TPMI registers during reset. During reset Phase 5 (TPMI_INIT), PrimeCode reads SST fuses and populates `SST_HEADER.CAPABILITY_MASK`, `SST_PP_HEADER`, `SST_PP_INFO_0..11`, and `SST_TF_INFO_0..8`. A mismatch between fuse values and TPMI register content constitutes a validation escape.

**Topology**: Fuse controller (IMH die) → PrimeCode reads via `fuses_sst.xml` → writes SST TPMI SRAM (per-dielet). PCode reads capability from TPMI IO space at runtime to resolve TRL tables and validate feature support.

```
Reset Phase 5 — SST TPMI Init
├── PrimeCode SstTpmiGeneral::tpmiInit()
│   ├── Read fuses: SST_PP_LEVEL_EN_MASK, SST_CP_ENABLE, SST_TF_ENABLE, SST_BF_ENABLE
│   ├── Read per-level arrays: SST_PP_P1_RATIO, SST_PP_TRL, SST_TF_LP_CLIP, SST_TF_HP_TRL
│   ├── Compute SST_HEADER.CAPABILITY_MASK from fuse set
│   └── Write SST_PP_HEADER, SST_PP_INFO_0..11, SST_TF_INFO_0..8, SST_CP_HEADER
└── PCode SstManager::init()
    ├── Read SST_CP_ENABLE + SST_PP_DYNAMIC_DISABLE fuses
    ├── Check HWP state (ENABLE_HWP) — if HWP disabled, clears CP/TF/BF capability
    └── update_cfgs() runs post-BIOS CPL3 with validated capability
```

**Boot activation**: SST fuses blown at manufacturing. TPMI registers populated at each reset Phase 5. OS reads `SST_HEADER.CAPABILITY_MASK` to discover available features.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Fuse controller | IMH die | Stores SST feature-enable bits and per-level TRL/P1/clip fuse arrays | SST_PP_LEVEL_EN_MASK, SST_CP_ENABLE, SST_TF_ENABLE, SST_TF_CONFIG arrays | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SRAM | IMH-P die | Per-dielet SST register banks; NVM-backed, survives PkgC | SST_HEADER, SST_PP_HEADER, SST_PP_INFO_0..11, SST_TF_INFO_0..8 | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| MSR / IO register interface | CBB compute | PCode reads SST TPMI IO mirror registers to resolve TRL tables | IO_SST_PP_INFO_*, IO_SST_TF_INFO_* | Primecode TPMI source |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PrimeCode (IMH-P) | IMH-P | Reads SST fuses via fuses_sst.xml; writes all SST TPMI register banks at reset Phase 5 | `SstTpmiGeneral::tpmiInit()` in `sst_tpmi_general.cpp` | Primecode source |
| PCode (CBB Root) | Root CBB | Reads SST_CP_ENABLE + SST_PP_DYNAMIC_DISABLE fuses; validates capability against HWP state; clears bits if HWP off | `SstManager::init()`, `update_cfgs()` in `sst_manager.cpp` | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| PCode (CBB Leaf) | Leaf CBB | Reads IO_SST_PP_INFO/IO_SST_TF_INFO from TPMI IO space to load TRL tables | `TrlManager::load_sst_pp_trl()`, `load_hp_clos_trl()` | Primecode source |
| BIOS | Pre-OS | Enables HWP (mandatory gate for CP capability); locks features post-init | CPL3 BIOS SST enable flow | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| TPMI SST | SST_HEADER.CAPABILITY_MASK bits[0..4] | RO | Feature capability bitmap: [0]=CP, [1]=PP, [2]=BF, [3]=TF, [4]=HGS | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_PP_HEADER.SST_PP_LEVEL_EN_MASK | RO | Bitmask of enabled PP levels derived from fuses | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_PP_HEADER.ALLOWED_LEVEL_MASK | RO | Locked to boot level when HWP disabled | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_PP_INFO_0..11 (per PP level) | RO | Per-level TDP, P1, TRL arrays, T_THROTTLE, core mask — derived from fuses | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| TPMI init phase | Reset Phase 5 (cold and warm boot) | Primecode reset sequence |
| SST_TF_ENABLE fuse → SST_TF_INFO_0.FEATURE_SUPPORTED | 1:1 fuse-to-TPMI propagation per PP level | Primecode `sst_tpmi_general.cpp` |
| SST_CP_ENABLE fuse → CAPABILITY_MASK[0] | HWP must also be enabled for CP capability bit to be set | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| SST TPMI register count | SST_PP_INFO_0..11 (12 per PP level) + SST_TF_INFO_0..8 (9 registers) | Primecode TPMI map |
| NWP active fuses | SST_TF_ENABLE, PCT_ENABLE, PCT_Module_Mask; SST_PP/CP/BF fuses out of scope | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |

## NWP Delta

### NWP Status: ⚠ Partial scope

SST fuse verification is applicable for **SST-TF/PCT fuses only** (TRL ratios, LP clip ratios, PCT_ENABLE, PCT_Module_Mask). Fuses for ZBB'd features (SST-PP/CP/BF) are out of scope for functional validation but may still need sanity checks.

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| SST-TF/PCT fuses | ✅ Applicable | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| SST-PP/CP/BF fuses | ❌ Out of scope (ZBB'd) | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |

## Legacy (Human-Curated Reference)

### Architecture Summary

SST Fuse verification validates that SST configuration fuses are correctly programmed in silicon and that PCode/Primecode correctly propagates them to TPMI registers visible to OS/VMM. Fuses control which SST sub-features are enabled (PP, TF, BF, CP, FCT), how many PP levels exist, per-level TDP/P1/TRL arrays, core disable masks, and whether dynamic PP switching is allowed. During reset, firmware reads these fuses and populates the `SST_HEADER.CAPABILITY_MASK`, per-level `SST_PP_INFO`, and `SST_CP_HEADER` TPMI registers — a mismatch between fuse intent and register content is a validation escape.

#### Key SST Fuses

| Fuse Name | Width | Feature | Description |
|-----------|-------|---------|-------------|
| `SST_PP_LEVEL_EN_MASK` | 5b | SST_PP | Bitmask of enabled PP levels (0–4). SoftSKU-able |
| `SST_PP_DYNAMIC_DISABLE` | 1b | SST_PP | When set, locks PP level at boot (sets `SST_PP_CONTROL.sst_pp_lock`) |
| `SST_CP_ENABLE` | 1b | SST_CP | Enables CLOS-based core power prioritization |
| `SST_PP_%I_P1_RATIO` (×5 levels × 4 ISAs) | 7b | SST_PP | Guaranteed P1 ratio per PP level per AVX level (SSE/AVX2/AVX512/AMX) |
| `SST_PP_%I_POWER` (×5 levels) | 15b | SST_PP | TDP power per PP level (U12.3 watts) |
| `SST_PP_%I_TURBO_RATIO_LIMIT_RATIOS` | 7b | SST_PP | Max turbo ratio per core-count bucket per CDYN index per PP level |
| `SST_PP_%I_TURBO_RATIO_LIMIT_CORES` | variable | SST_PP | Core-count thresholds per TRL bucket per PP level |
| `SST_PP_%I_T_THROTTLE` | 8b | SST_PP | Thermal throttle temperature per PP level |
| `SST_PP_%I_COOLING_TYPE` | 3b | SST_PP | Cooling type encoding per PP level |
| `SST_PP_CORE_DISABLE_MASK` | per-level | SST_PP | Module disable mask per PP level (MCA if all modules disabled) |
| `TURBO_DISABLE` | 1b | SST_PP | Global turbo disable by fuse |
| `FCT_ENABLE` | 1b | FCT | Favored Core Turbo enable |
| `SST_TF_ENABLE` | (in marketing features) | SST_TF | Turbo Frequency enable |
| `SST_BF_ENABLE` | (in marketing features) | SST_BF | Base Frequency enable |


### Execution Flow

1. **Silicon fuse blow** — Manufacturing programs fuses per LIRA/QDF definition
2. **Reset** — Primecode `SstTpmiGeneral::tpmiInit()` reads fuses via `sst_obj.getFuse()` and populates:
   - `SST_HEADER.CAPABILITY_MASK` bit[0]=SST_CP_ENABLE, bit[1]=(SST_PP_LEVEL_EN_MASK > 0)
   - `SST_PP_HEADER.SST_PP_LEVEL_EN_MASK`, `ALLOWED_LEVEL_MASK`, `DYNAMIC_SWITCHING`
   - Per-level `SST_PP_INFO` registers with P1 ratios, TDP, TRL arrays
3. **PCode** `SstManager::init()` reads `SST_PP_DYNAMIC_DISABLE`, `SST_CP_ENABLE` fuses and programs TPMI control/status registers
4. **BIOS CPL3** — `SstManager::update_cfgs()` checks `MISC_PWR_MGMT2.ENABLE_HWP`; if HWP disabled, clears SST_CP capability and BF/TF support
5. **OS/VMM** reads TPMI `SST_HEADER`, `SST_PP_HEADER` to discover capabilities


### Key Registers & Interfaces

| Register | Access | Description |
|----------|--------|-------------|
| `SST_HEADER.CAPABILITY_MASK` | RO | Bit[0]=CP capable, Bit[1]=PP capable — populated from fuses at reset |
| `SST_PP_HEADER.SST_PP_LEVEL_EN_MASK` | RO | Fused PP level enable mask |
| `SST_PP_HEADER.ALLOWED_LEVEL_MASK` | RO | Runtime-resolved allowed levels (fuse + core-count + lock constraints) |
| `SST_PP_HEADER.DYNAMIC_SWITCHING` | RO | 1 if dynamic PP switch allowed (inverse of `SST_PP_DYNAMIC_DISABLE` fuse) |


### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST_HEADER, SST_PP registers |
| Primecode fuse defs | `src/ip/fuse/v2_0/fuses_sst.xml` | All SST fuse definitions |
| Primecode fuse features | `src/ip/fuse/v2_0/fuses.xml` | Marketing feature flags (SST_PP, SST_TF, SST_BF, SST_CP, FCT) |
| Primecode TPMI init | `src/flow/sst/sst_tpmi_general/v2_0/sst_tpmi_general.cpp` | `tpmiInit()` — fuse→register propagation |
| PCode SST manager | `source/pcode/flows/sst/sst_manager.cpp` | `init()`, `update_cfgs()` |
| Frozen fuses (DMR) | `src/cfgdata/dmr_imh1_a0/v1_0/fuses_zfrozen_soc.xml` | `FUSES_SST_PP_NUM_LEVELS` instances |
| PCode frozen fuses | `source/fuses/pcode_frozen_fuses.rdl` | `FCT_ENABLE`, etc. |


### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->
