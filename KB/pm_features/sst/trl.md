# SST > TRL (Turbo Ratio Limits)

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SST](sst_main.md)

## Baseline (DMR)

**TRL (Turbo Ratio Limit)** is the frequency ceiling mechanism that SST-PP, SST-TF, and legacy turbo build on. PCode `TrlManager` maintains four TRL tables: `legacy_trl` (8 buckets, single-freq), `sst_pp_cdyn_trl` (8 buckets × 6 CDYN), `hi_prio_clos_cdyn_trl` (3 buckets × 6 CDYN for HP cores), and `low_prio_clos_cdyn_trl` (1 bucket × 6 CDYN for LP cores). A hash-based O(1) bucket lookup resolves the active ratio from active core count. ODC TRL = min(SST_PP_INFO_4, MSR 0x1AD, ODC_TURBO_MAX_RATIO).

**Topology**: Fuses define TRL arrays per PP level → PrimeCode populates SST_PP_INFO_4..10 and SST_TF_INFO_1..8 TPMI registers at reset Phase 5 → PCode `TrlManager` loads tables from TPMI IO space at runtime → workpoint calc consumes TRL ratios per CDYN index.

```
TRL table load (on SST event or reset)
├── TrlManager::load_sst_pp_trl(): reads IO_SST_PP_INFO_4..9 (ratios) + IO_SST_PP_INFO_10 (buckets)
├── TrlManager::load_hp_clos_trl(): reads IO_SST_TF_INFO_2..7 (ratios) + IO_SST_TF_INFO_8 (buckets)
├── TrlManager::load_lp_clos_trl(): reads IO_SST_TF_INFO_0 (LP_CLIP ratios per CDYN)
└── ODC resolution: IO_ODC_TRL_RATIOS = min(SST_PP_INFO_4, MSR_0x1AD, ODC_TURBO_MAX_RATIO)

Workpoint consumption (WP4 — CDYN-aware path)
├── get_sst_pp_cdyn_ratio_limits(active_cores) → base SST-PP TRL from bucket hash
├── If SST-TF enabled:
│   ├── HP cores: get_hp_clos_cdyn_ratio_limits() → max(SST_PP, HP_CLOS)
│   └── LP cores: get_lp_clos_cdyn_ratio_limits() → clip(SST_PP, LP_CLOS)
└── If SST-TF disabled: SST_PP_TRL used directly for all cores
```

**Boot activation**: TRL tables loaded at reset Phase 5 (from TPMI) and reloaded on each SST event (PP change, TF enable/disable, MSR 0x1AD write). ODC TRL resolved whenever ODC_TURBO_MAX or MSR 0x1AD changes.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| TPMI SRAM (SST-PP TRL) | IMH-P die | SST_PP_INFO_4..10: SST-PP TRL ratios per CDYN × 8 buckets + bucket core-counts | SST_PP_INFO_4..9 (ratios), SST_PP_INFO_10 (buckets) | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SRAM (SST-TF TRL) | IMH-P die | SST_TF_INFO_1..8: HP TRL per CDYN × 3 buckets + LP clip ratios | SST_TF_INFO_0 (LP clip), SST_TF_INFO_2..7 (HP TRL), SST_TF_INFO_8 (buckets) | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| MSR interface | CBB compute | MSR 0x1AD (PRIMARY_TURBO_RATIO_LIMIT): 3-way ODC TRL min with SST_PP and ODC_TURBO_MAX | IO_ODC_TRL_RATIOS = min(SST_PP, 0x1AD, ODC_MAX) | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PCode TrlManager | CBB (Root/Leaf) | Maintains all 4 TRL tables; loads/reloads on SST events; O(1) bucket hash lookup; FWU_VAR safety: skips reload during FWU | `trl_manager.cpp::load_sst_pp_trl()`, `load_hp_clos_trl()`, `load_lp_clos_trl()`, `get_sst_pp_cdyn_ratio_limits()` | PCode source |
| PCode SstManager | CBB Root | Triggers TRL reload on: PP level change, TF enable/disable, MSR 0x1AD write, CCP mask change, ODC_TURBO_MAX change | `sst_manager.cpp` slow-loop event detection | PCode source |
| PrimeCode (IMH-P) | IMH-P | Reads SST_PP and SST_TF fuse arrays at reset Phase 5; writes SST_PP_INFO_4..10 and SST_TF_INFO_1..8 TPMI registers | `sst_tpmi_general.cpp::tpmiInit()`, `sst_tpmi_compute.cpp::getTrlRatioForSstPpInit/TfInit()` | Primecode source |
| BIOS | Pre-OS | May write MSR 0x1AD to override TRL; sets OC lock (FLEX_RATIO_L.oc_lock) to gate further 0x1AD writes | BIOS TRL override knob | PCode source |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR | 0x1AD (PRIMARY_TURBO_RATIO_LIMIT) | RW | 8 × 8-bit TRL ratios per bucket (CDYN 0/SSE); writeable by BIOS/OS; gated by OC lock | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| MSR | 0x1AE (PRIMARY_TURBO_RATIO_LIMIT_CORES) | RO | 8 × 8-bit core-count per bucket; written by PCode from SST-PP | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_PP_INFO_4..9 (per PP level) | RO | SST-PP TRL ratios: 8 buckets × 6 CDYN levels | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| IO register | IO_ODC_TRL_RATIOS | RO | Resolved TRL = min(SST_PP, MSR 0x1AD, ODC_TURBO_MAX_RATIO) per bucket | PCode IO register map |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| SST-PP TRL buckets | 8 (core-count indexed); 6 CDYN levels per bucket | PCode `trl_manager.h` |
| HP CLOS TRL buckets | 3; 6 CDYN levels per bucket | PCode `trl_manager.h` |
| LP CLOS TRL | 1 bucket; 6 CDYN levels (LP_CLIP_RATIO_0..5) | PCode `trl_manager.h` |
| Bucket lookup | O(1) hash using 64-bit index_to_bucket_hash; linear fallback if core count > 64 | PCode `turbo_ratio_limits.h` |
| CDYN levels | 6: SSE, AVX2, AVX3, TMUL, AMX, reserved | Primecode Config::CCP::max_num_ccp_cdyn_levels |
| ODC TRL resolution | min(SST_PP_INFO_4, MSR 0x1AD, IO_ODC_TURBO_MAX_RATIO); 0 = unlimited (NO_LIMIT_RATIO) | PCode `trl_manager.cpp` |
| FWU_VAR TRL safety | TRL reload skipped during FWU to prevent half-updated state | PCode `trl_manager.cpp` |

## NWP Delta

### Delta 1: Max Core Count and Bucket Hash Width
TRL bucket resolution uses a 64-bit `index_to_bucket_hash`. DMR has up to 128 cores (across modules), exceeding 64 bits, which triggers `get_bucket_data_linear_search()` fallback for HP CLOS TRL. NWP core counts determine whether the hash path or linear path is used; verify `Config::GlobalTopology::max_num_cores` against the 64-bit hash limit. The `static_assert(Config::GlobalTopology::max_num_ccps <= sizeof(uint32_t)*8)` in `SstManager` constrains CCP count to 32 — confirm NWP matches.

### Delta 2: CDYN Level Count
TRL tables assume `Config::CCP::max_num_ccp_cdyn_levels = 6`. NWP should inherit this from DMR. If NWP introduces new instruction classes (beyond AMX), the CDYN level count and all TRL table dimensions would need updating.

### Delta 3: ODC_TURBO_MAX_RATIO Behavior
The `IO_ODC_TURBO_MAX_RATIO` register's reset value of 0 means "unlimited" (mapped to `NO_LIMIT_RATIO` internally). If NWP SKU fusing sets a non-zero ODC cap, verify the 3-way min resolution (`min(SST_PP, MSR_0x1AD, ODC_MAX)`) produces correct effective TRL for each bucket.

### Delta 4: Legacy TRL dfx Disable
`TrlManager` has a `dfx_disable_legacy_trl` flag. When set, `get_single_freq_ratio_limit()` returns `NO_LIMIT_RATIO` (effectively disabling legacy TRL). This is a DFx control — verify NWP DFx knob wiring matches DMR.

## Legacy (Human-Curated Reference)

### Architecture Summary

**TRL (Turbo Ratio Limits)** defines the maximum turbo frequency (ratio) a core may achieve as a function of the number of simultaneously active cores and the current CDYN workload level. TRL is the foundational frequency-ceiling mechanism that SST-PP, SST-TF, and legacy turbo all build upon.

#### How It Works
PCode's `TrlManager` maintains **four** independent TRL tables that are loaded from TPMI registers and MSRs at init and reloaded whenever the SST-PP level or SST-TF enable state changes:

| TRL Table | Dimensions | Source Registers | Consumer |
|-----------|-----------|-----------------|----------|
| **Legacy TRL** | 8 buckets, single-freq (SSE only) | MSR 0x1AD ratios, SST_PP_INFO_10 buckets | WP1 (single-frequency path) |
| **SST-PP TRL** | 8 buckets x 6 CDYN levels | SST_PP_INFO_4..9 (ratios), SST_PP_INFO_10 (buckets) | WP4 base ratio for all cores |
| **HP CLOS TRL** | 3 buckets x 6 CDYN levels | SST_TF_INFO_2..7 (ratios), SST_TF_INFO_8 (buckets) | WP4 elevated ratio for HP cores (when SST-TF enabled) |
| **LP CLOS TRL** | 1 bucket (flat) x 6 CDYN levels | SST_TF_INFO_0 (LP_CLIP_RATIO_0..5) | WP4 clipped ratio for LP cores (when SST-TF enabled) |

#### Bucket Resolution
Each TRL table maps core-count to a bucket using a **hash-based O(1) lookup** (for tables with <= 64 cores) or **linear search** (for HP CLOS with smaller bucket counts):
- Bucket boundaries are stored as core-count thresholds (e.g., {1, 4, 6, 8, 10, 16, 20, 28})
- A 64-bit `index_to_bucket_hash` is built from the bucket table during `update_bucket_hash()`, with each bit position representing a core-count boundary
- For a given active-core count N, the bucket index = popcount of bits set below position N in the hash

#### ODC TRL Resolution
The **ODC (On-Die Compute) TRL** is a resolved register that represents the effective turbo ceiling visible to the core:
```
ODC_TRL_RATIOS[bucket] = min(SST_PP_INFO_4[pp_level], MSR_0x1AD, ODC_TURBO_MAX_RATIO)
```
This 3-way min ensures the core sees the most restrictive of: fused SST-PP ratios, BIOS/OS-programmed MSR limits, and the ODC turbo cap.

#### Key Design Points
- **CDYN awareness**: All TRL tables except Legacy are indexed by CDYN level (SSE, AVX2, AVX3, TMUL, AMX, +1). This allows lower turbo ratios for heavy workloads (AVX3/TMUL) vs lighter ones (SSE).
- **SST-PP level coupling**: When the PP level changes (runtime or boot), all four TRL tables are reloaded because each PP level has independently fused ratio/bucket values.
- **MSR 0x1AD writability**: BIOS or OS can write MSR 0x1AD to override TRL ratios. PCode detects changes in its slow-loop and updates Legacy TRL + ODC TRL accordingly.
- **FIT_INFO_0 update**: After loading SST-PP TRL, PCode writes `IO_FIT_INFO_0` with the P0n bucket ratios per CDYN level, which provides the all-core turbo ratios to downstream consumers.
- **FW Update safety**: All internal state (`sst_pp_level`, `hp_ccps_mask`, `primary_turbo_ratio_limit_msr_data`, `sst_tf_enabled`) is preserved across PCode FW updates via `FWU_VAR` and `post_fw_update_init()`.


### Execution Flow

```
1. PCode Init — TrlManager::init()
   |-- Ensure SstManager init ran first (static_assert on FlowID ordering)
   |-- state.sst_pp_level = sst_manager.get_sst_pp_level()
   |-- state.hp_ccps_mask = clos.get_hp_ccps_mask()
   |-- state.odc_turbo_max_ratio = read_odc_turbo_max_ratio()
   +-- load_trl_tables():
       |-- load_lp_clos_trl():
       |   |-- Read IO_SST_TF_INFO_0 indexed by current PP level
       |   |-- Extract LP_CLIP_RATIO_0..5 (6 CDYN levels)
       |   +-- Replace zero ratios with NO_LIMIT_RATIO
       |-- load_hp_clos_trl():
       |   |-- Read IO_SST_TF_INFO_8 (bucket core-counts) indexed by PP level
       |   |-- Populate hi_prio_clos_cdyn_trl bucket table
       |   +-- For each CDYN level 0..5:
       |       +-- Read IO_SST_TF_INFO_2..7, load ratios into hi_prio_clos_cdyn_trl
       |-- load_sst_pp_trl():
       |   |-- Read IO_SST_PP_INFO_10 (bucket core-counts) indexed by PP level
       |   |-- Write IO_ODC_TRL_NUMCORES (copy of SST-PP buckets)
       |   |-- Write MSR 0x1AE (PRIMARY_TURBO_RATIO_LIMIT_CORES)
       |   |-- Populate sst_pp_cdyn_trl bucket table
       |   |-- For each CDYN level 0..5:
       |   |   +-- Read IO_SST_PP_INFO_4..9, load ratios
       |   |-- Write MSR 0x1AD from SST_PP ratios (CDYN 0)
       |   |-- Write IO_FIT_INFO_0 with P0n bucket ratios per CDYN
       |   |-- Compute ODC_TRL_RATIOS and write
       |   +-- Update bucket hash for SST-PP TRL
       +-- load_legacy_trl():
           |-- Copy bucket table from SST-PP TRL
           |-- Write MSR 0x1AE
           |-- Load ratios from MSR 0x1AD (state.primary_turbo_ratio_limit_msr_data)
           +-- Update bucket hash

2. PCode Post-Reset Init — TrlManager::post_reset_init()
   +-- Sample sst_resolved_ccps_mask from SstManager

3. PCode Slow Loop — TrlManager::periodic_update_tx() -> update_state()
   |-- If HP CCP mask changed -> signal WP calc
   |-- If SST PP level changed -> reload ALL TRL tables, signal WP calc
   |-- If SST-TF enable changed -> signal WP calc
   |-- If MSR 0x1AD changed (BIOS/OS write) -> reload legacy TRL ratios + resolve ODC TRL
   |-- If SST resolved CCP mask changed -> signal WP calc
   +-- If ODC_TURBO_MAX_RATIO changed -> resolve ODC TRL (no WP signal)

4. Workpoint Consumption (WP1 / WP4)
   |-- WP1 (single-freq): get_single_freq_ratio_limit(active_cores) -> legacy_trl bucket lookup
   +-- WP4 (CDYN-aware):
       |-- get_sst_pp_cdyn_ratio_limits(active_cores) -> base SST-PP TRL
       |-- If SST-TF enabled:
       |   |-- get_hp_clos_cdyn_ratio_limits(active_cores) -> max(SST_PP, HP_CLOS)
       |   +-- get_lp_clos_cdyn_ratio_limits(active_cores) -> clip(SST_PP, LP_CLOS)
       +-- If SST-TF disabled: SST_PP_TRL used directly for all cores
```


### Key Registers & Interfaces

#### TPMI SST Registers (per dielet, per PP level)

| Register | Description |
|----------|-------------|
| `SST_PP_INFO_4..9` | SST-PP TRL ratios: 8 buckets x 6 CDYN levels |
| `SST_PP_INFO_10` | SST-PP TRL bucket core-count boundaries (8 buckets) |
| `SST_TF_INFO_0` | LP CLOS clip ratios (LP_CLIP_RATIO_0..5) |
| `SST_TF_INFO_2..7` | HP CLOS TRL ratios per CDYN level (3 buckets each) |
| `SST_TF_INFO_8` | HP CLOS bucket core-counts (3 buckets) |

#### MSRs

| MSR | Address | Description |
|-----|---------|-------------|
| `PRIMARY_TURBO_RATIO_LIMIT` | 0x1AD | 8 x 8-bit turbo ratios per bucket (CDYN 0 / SSE). Written by PCode from SST-PP; readable/writable by BIOS/OS |
| `PRIMARY_TURBO_RATIO_LIMIT_CORES` | 0x1AE | 8 x 8-bit core-count per bucket. Written by PCode from SST-PP |

#### PCode IO Registers

| Register | Description |
|----------|-------------|
| `IO_ODC_TRL_RATIOS` | Resolved = min(SST_PP_INFO_4, MSR 0x1AD, ODC_TURBO_MAX_RATIO) |
| `IO_ODC_TRL_NUMCORES` | Copy of SST-PP bucket core-counts |
| `IO_ODC_TURBO_MAX_RATIO` | Turbo cap ratio (0 = unlimited) |
| `IO_FIT_INFO_0` | P0n (all-core) ratios per CDYN level |
| `IO_PRIMARY_TURBO_RATIO_LIMIT` | PCode IO mirror of MSR 0x1AD |
| `IO_PRIMARY_TURBO_RATIO_LIMIT_CORES` | PCode IO mirror of MSR 0x1AE |

#### Internal Data Structures (PCode)

| Structure | Type | Description |
|-----------|------|-------------|
| `legacy_trl` | `trl_sfl_buckets_t` | 8 buckets, single-freq ratios (WP1 path) |
| `sst_pp_cdyn_trl` | `trl_cdyn_buckets_t` | 8 buckets x 6 CDYN ratios (WP4 base) |
| `hi_prio_clos_cdyn_trl` | `trl_hi_prio_clos_cdyn_buckets_t` | 3 buckets x 6 CDYN ratios (HP cores) |
| `low_prio_clos_cdyn_trl` | `trl_low_prio_clos_cdyn_buckets_t` | 1 bucket x 6 CDYN ratios (LP cores) |
| `bucket_data_t<T, N>` | template | Bucket container with hash-based O(1) lookup and linear fallback |

#### HPM Messages

| Message | Description |
|---------|-------------|
| `HPM_MSG_COMPUTE_CLOS_CONFIG` | Updates `num_hp_modules` in TrlManager for HP CLOS bucket resolution |


### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | Intel SST HAS (docs.intel.com/documents/pm_doc -> SST) | TRL register definitions within SST-PP and SST-TF sections |
| PCode src | `source/pcode/flows/trls/trl_manager.h` | TrlManager class — API surface, state struct, TRL table members |
| PCode src | `source/pcode/flows/trls/trl_manager.cpp` | Full implementation — init, load tables, slow-loop update, ODC resolution |
| PCode src | `source/pcode/flows/trls/turbo_ratio_limits.h` | `bucket_data_t`, `ratios_array_t`, hash-based bucket lookup, TRL config constants |
| PCode src | `source/pcode/flows/sst/sst_manager.h` | SST state provider consumed by TrlManager (`get_sst_pp_level`, `get_sst_tf_enabled`, `get_sst_resolved_module_mask`) |
| Primecode src | `src/flow/sst/sst_tpmi_general/v2_0/sst_tpmi_general.cpp` | TPMI register init that populates SST_PP_INFO and SST_TF_INFO registers |
| Primecode src | `src/flow/sst/sst_tpmi_compute/v1_0/sst_tpmi_compute.cpp` | TRL fuse accessors (`getTrlRatioForSstPpInit`, `getTrlNumCoresForSstPpInit`) |
| Test scripts | `intel_speed_select perf-profile info` | SW readout of TRL buckets per PP level |


### Related Sightings
<!-- No TRL-specific NWP sightings identified yet -->
