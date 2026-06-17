# SST > TF (Turbo Frequency)

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SST](sst_main.md)

## Baseline (DMR)

**SST-TF (Turbo Frequency)** partitions cores into HP (high priority, CLOS[0]) and LP (low priority, CLOS[3]) groups with distinct frequency ceilings. Four TRL tables are maintained by PCode `TrlManager`: Legacy, SST-PP, HP CLOS, and LP CLOS. TRL ratios are CDYN-indexed (6 levels: SSE/AVX2/AVX3/TMUL/AMX/+1) with O(1) bucket hash lookup. SST-TF is the underlying mechanism for PCT on NWP.

**Topology**: Fuses define LP clip ratios + HP TRL arrays per PP level → PrimeCode populates SST_TF_INFO_0..8 TPMI registers at reset Phase 5 → PCode `TrlManager` loads tables from TPMI IO space → workpoint calc applies per-CLOS ratio limits at runtime.

```
Reset Phase 5 — TF TPMI Init
├── PrimeCode sstTfInfoInit(): reads SST_TF fuse arrays
├── Writes SST_TF_INFO_0 (LP clip ratios per CDYN)
└── Writes SST_TF_INFO_1..8 (HP TRL ratios per CDYN × 3 buckets)

PCode slow-loop — SST-TF feature detection
├── SstManager detects feature_state[1] change (enable/disable)
├── Sends HPM COMPUTE_CLOS_CONFIG with HP module counts
├── TrlManager::load_hp_clos_trl(): reads IO_SST_TF_INFO_1..8 → fills hi_prio_clos_cdyn_trl
├── TrlManager::load_lp_clos_trl(): reads IO_SST_TF_INFO_0 → fills low_prio_clos_cdyn_trl
└── Workpoint calc: HP cores → max(SST_PP, HP_CLOS); LP cores → clip(SST_PP, LP_CLOS)
```

**Boot activation**: Enabled by BIOS at CPL3 via `SST_PP_CONTROL.feature_state[1] = 1`. HP/LP CLOS assignments programmed by BIOS in `SST_CLOS_ASSOC` registers.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| TPMI SRAM (SST-TF) | IMH-P die | Stores SST_TF_INFO_0..8 per PP level: LP clip ratios and HP TRL arrays per CDYN × bucket | SST_TF_INFO_0..8 | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Fuse controller | IMH die | SST_TF fuse arrays: LP_CLIP_RATIO per CDYN, HP TRL ratios per bucket × CDYN × PP level | SST_TF_CONFIG_[0..4] fuse arrays | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Core FIVR + PLL | CBB compute | Enforces HP (elevated TRL) and LP (clipped) frequency per CLOS group; CDYN-aware ratio selection | CLOS frequency via workpoint calc | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PrimeCode (IMH-P) | IMH-P | Reads SST_TF fuse arrays at reset Phase 5; writes SST_TF_INFO_0..8 TPMI registers; handles SST_TF_INFO_8 for feature_revision >= 2 | `sst_tpmi_general.cpp::sstTfInfoInit()`, `sst_tpmi_compute.cpp::getTrlRatioForSstTfInit()` | Primecode source |
| PCode TrlManager | CBB (Root/Leaf) | Maintains 4 TRL tables; loads HP CLOS (3 buckets × 6 CDYN) and LP CLOS (1 bucket × 6 CDYN) from TPMI IO; updates on SST-TF enable/disable | `trl_manager.cpp::load_hp_clos_trl()`, `load_lp_clos_trl()` | PCode source |
| PCode SstManager | CBB Root | Detects SST-TF feature_state change in slow loop; sends HPM COMPUTE_CLOS_CONFIG with HP module counts to TrlManager | `sst_manager.cpp`, `hpm_msgs.xml::HPM_MSG_COMPUTE_CLOS_CONFIG` | PCode source |
| BIOS | Pre-OS | Enables SST-TF via SST_PP_CONTROL.feature_state[1]; programs CLOS assignments (HP→CLOS[0], LP→CLOS[3]); overrides MSR 0x1AD | BIOS TF/PCT knobs | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| TPMI SST | SST_PP_CONTROL.feature_state[1] | RW | SST-TF enable/disable; monitored by PCode slow loop | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_TF_INFO_0 (LP clip ratios) | RO | LP_CLIP_RATIO_0..5 per CDYN level; FEATURE_SUPPORTED bit | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_TF_INFO_2..7 (HP TRL per CDYN) | RO | HP TRL ratios: 3 buckets × 6 CDYN levels | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_CLOS_ASSOC_0..N | RW | Per-core CLOS assignment; HP→CLOS[0], LP→CLOS[3] (set by BIOS) | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| MSR | 0x1AD (PRIMARY_TURBO_RATIO_LIMIT) | RW | HP TRL ratios (CDYN 0/SSE); updated from SST_TF_INFO_2 when TF active | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| HP TRL buckets | 3 (per CDYN level); LP: 1 bucket (LP_CLIP ratio) | Primecode `sst_tpmi_compute.cpp` |
| CDYN levels | 6: SSE, AVX2, AVX3, TMUL, AMX, reserved | Primecode Config::CCP::max_num_ccp_cdyn_levels |
| TRL table count in PCode | 4: legacy_trl, sst_pp_cdyn_trl, hi_prio_clos_cdyn_trl, low_prio_clos_cdyn_trl | PCode `trl_manager.h` |
| SST-TF enable detection | PCode slow loop (not interrupt-driven); 1+ slow-loop latency before TRL tables reload | PCode source |
| SST_TF_INFO_8 | New register for feature_revision >= 2: additional HP bucket core-counts | PCode/Primecode source |
| NWP status | ✅ Active via PCT — SST-TF is the underlying mechanism for NWP PCT | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |

## NWP Delta

### Delta 1: CDYN Levels and Bucket Counts
NWP inherits DMR's 6-level CDYN indexing (SSE, AVX2, AVX3, TMUL, AMX, +1 reserved) and 3-bucket HP CLOS TRL model. Config constants `Config::CCP::max_num_ccp_cdyn_levels` and `TRL_Config::max_num_buckets_sst_tf_hp = 3` apply unchanged. Verify NWP fuse definitions match these dimensions.

### Delta 2: SST_TF_INFO_8 (Feature Revision >= 2)
DMR introduced `SST_TF_INFO_8` for additional HP bucket core-counts when `feature_revision >= 2`. NWP inherits the same `feature_revision_default_value` in Primecode TPMI mailbox RDL. Confirm NWP OSXML provides the `SST_TF_INFO_8` register offset.

### Delta 3: Module Turbo Integration
`SstManager` tracks a `module_turbo_enabled` state (via `FWU_VAR`) which interacts with SST-TF CLOS resolution. The CLOS update flow sends `HPM_MSG_COMPUTE_CLOS_CONFIG` with HP module counts to `TrlManager`. Verify NWP HPM message routing matches DMR topology (different die counts/CBB layout may affect module counts).

### Delta 4: ODC TRL Resolution
The resolved ODC TRL = min(SST_PP_INFO_4, MSR 0x1AD, ODC_TURBO_MAX_RATIO). NWP should verify `IO_ODC_TURBO_MAX_RATIO` reset value and that the 3-way min resolution produces correct capped ratios for NWP-specific SKU fusing.

## Legacy (Human-Curated Reference)

### Architecture Summary

**SST-TF (Speed Select Technology — Turbo Frequency)** divides cores into **High Priority (HP)** and **Low Priority (LP)** groups with different turbo frequency ceilings. HP cores receive elevated TRL ratios (up to the SST-TF TRL bucket values), while LP cores are clipped to a lower frequency ceiling (the LP_CLIP ratio), freeing power budget for the HP group.

#### How It Works
1. **Fuse-based capability**: SST-TF support per PP level is determined by the `SST_TF_ENABLE` fuse. The feature is disabled if either `SST_TF_ENABLE=0` or `TURBO_DISABLE=1` for the current PP level.
2. **BIOS / Primecode init** programs the SST TPMI register space during reset Phase 5 (`TPMI_INIT`):
   - `SST_TF_INFO_0`: LP clip ratios per CDYN level and `feature_supported` bit
   - `SST_TF_INFO_1`: HP core-count-per-bucket (TRL bucket boundaries)
   - `SST_TF_INFO_2..7`: HP TRL ratios per bucket per CDYN level (6 CDYN levels x up to 3 buckets)
   - `SST_TF_INFO_8`: HP core-count buckets for CLOS resolution (feature_revision >= 2)
3. **PCode SST Manager** (`SstManager`) runs a slow-loop transaction (`update_sst_config_tx`) that reads `SST_PP_CONTROL.feature_state` bit 1 to determine if SST-TF is enabled at runtime.
4. **PCode TRL Manager** (`TrlManager`) maintains four independent TRL tables: **Legacy** (single-freq, WP1), **SST-PP** (per-CDYN, 8 buckets), **HP CLOS** (per-CDYN, 3 buckets), and **LP CLOS** (per-CDYN, 1 bucket = flat clip). On each slow loop it checks for SST-TF enable/disable state changes from `SstManager` and reloads TRL tables when the PP level changes.
5. **Workpoint Calc** consumes HP/LP ratio limits from `TrlManager` to produce per-core frequency workpoints. When SST-TF is enabled:
   - HP cores: `WP4 = max(SST_PP_TRL[bucket], HP_CLOS_TRL[hp_core_count])` — elevated ratio
   - LP cores: `WP4 = clip(SST_PP_TRL[bucket], LP_CLOS_TRL)` — clipped ratio

#### Key Design Points
- **HP core identification**: HP cores are identified by CLOS assignment — CLOS[0] = HP, CLOS[3] = LP. The HP CCP mask is tracked by the CLOS update flow and consumed by `TrlManager::get_hp_ccps_mask()`.
- **CDYN-indexed ratios**: Both HP and LP TRL tables are indexed by CDYN level (SSE, AVX2, AVX3, TMUL, AMX, ...), providing workload-aware frequency differentiation.
- **Bucket model**: HP CLOS TRL uses up to 3 core-count buckets (vs 8 for SST-PP). A linear search resolves the applicable bucket from the number of active HP cores.
- **Dynamic enable/disable**: OS can toggle SST-TF at runtime via `SST_PP_CONTROL.feature_state[1]`. PCode detects the change in its slow-loop and propagates to `TrlManager`, which signals Workpoint Calc to recompute.
- **SST-PP level interaction**: When SST-PP level changes, all four TRL tables are reloaded from TPMI registers (different PP levels have different fused TRL/LP-clip values). The MSR 0x1AD (PRIMARY_TURBO_RATIO_LIMIT) is also updated.
- **PCT / DLCP relationship**: PCT (Priority Core Turbo) and DLCP (Die Level Cherry Picking) are consumer features built on top of SST-TF. PCT partitions cores and assigns HP/LP via CLOS; DLCP fixes HP core positions via fuse. From PCode's perspective, all three use the same SST-TF flow — the difference is how HP cores are selected (SW vs fuse).


### Execution Flow

```
1. Primecode Reset Phase 5 — TPMI_INIT (sst_tpmi_general.cpp -> sstTfInfoInit)
   |-- Read SST_TF_ENABLE fuse per PP level
   |-- Read TURBO_DISABLE fuse
   |-- tf_supported = SST_TF_ENABLE && !TURBO_DISABLE
   |-- Program SST_TF_INFO_0 per PP level:
   |   |-- feature_supported = tf_supported
   |   +-- LP_CLIP_RATIO_0..5 (per CDYN level) from SST_TF_CONFIG_LP_CLIP_RATIO fuses
   |-- Program SST_TF_INFO_1: HP core-count-per-bucket from SST_TF_CONFIG_TRL_CORES fuses
   |-- Program SST_TF_INFO_2..7: HP TRL ratios per bucket/CDYN from SST_TF_CONFIG_TRL_RATIOS fuses
   |-- Program SST_TF_INFO_8: additional HP bucket info (feature_revision >= 2)
   +-- Lock read-only TPMI registers

2. PCode Init — TrlManager::init()
   |-- Sample SST PP level from SstManager
   |-- Read HP CCP mask from CLOS update flow
   |-- Read ODC_TURBO_MAX_RATIO
   |-- Load all four TRL tables:
   |   |-- load_lp_clos_trl() -> reads SST_TF_INFO_0 LP_CLIP_RATIO_0..5
   |   |-- load_hp_clos_trl() -> reads SST_TF_INFO_8 (buckets), SST_TF_INFO_2..7 (ratios)
   |   |-- load_sst_pp_trl() -> reads SST_PP_INFO_10 (buckets), SST_PP_INFO_4..9 (ratios)
   |   |   |-- Updates MSR 0x1AD (PRIMARY_TURBO_RATIO_LIMIT)
   |   |   |-- Updates MSR 0x1AE (PRIMARY_TURBO_RATIO_LIMIT_CORES)
   |   |   |-- Updates ODC_TRL_RATIOS
   |   |   +-- Updates FIT_INFO_0 (P0n ratios per CDYN)
   |   +-- load_legacy_trl() -> copies SST-PP buckets, reads MSR 0x1AD ratios

3. PCode Slow Loop — TrlManager::periodic_update_tx() -> update_state()
   |-- Check HP CCP mask change -> signal WP calc if changed
   |-- Check SST PP level change -> reload all TRL tables if changed
   |-- Check SST-TF enable change -> signal WP calc if changed
   |-- Check MSR 0x1AD (BIOS/OS override) -> reload legacy TRL ratios, resolve ODC TRL
   |-- Check SST resolved CCP mask change
   +-- Check ODC_TURBO_MAX_RATIO change -> resolve ODC TRL

4. Workpoint Calc (per core, fast path)
   |-- If SST-TF enabled:
   |   |-- HP core (CLOS[0]): ratio = max(SST_PP_TRL[active_cores], HP_CLOS_TRL[hp_cores])
   |   +-- LP core (CLOS[3]): ratio = clip(SST_PP_TRL[active_cores], LP_CLOS_TRL)
   +-- If SST-TF disabled:
       +-- All cores: ratio = SST_PP_TRL[active_cores] (no HP/LP differentiation)

5. OS Runtime (optional)
   |-- Toggle SST-TF via SST_PP_CONTROL.feature_state[1]
   |-- Reassign HP/LP cores via SST_CLOS_ASSOC TPMI registers
   +-- Query HP identification via HWP MSR or Intel SST tool
```


### Key Registers & Interfaces

#### TPMI SST Registers (per dielet, per PP level)

| Register | Description |
|----------|-------------|
| `SST_TF_INFO_0` | LP clip ratios per CDYN (LP_CLIP_RATIO_0..5), `feature_supported` bit |
| `SST_TF_INFO_1` | HP core-count-per-bucket (TRL bucket boundaries, up to 3 buckets) |
| `SST_TF_INFO_2` | HP TRL ratios for CDYN level 0 (SSE), buckets 0..2 |
| `SST_TF_INFO_3` | HP TRL ratios for CDYN level 1 (AVX2) |
| `SST_TF_INFO_4` | HP TRL ratios for CDYN level 2 (AVX3) |
| `SST_TF_INFO_5` | HP TRL ratios for CDYN level 3 (TMUL) |
| `SST_TF_INFO_6` | HP TRL ratios for CDYN level 4 (AMX) |
| `SST_TF_INFO_7` | HP TRL ratios for CDYN level 5 |
| `SST_TF_INFO_8` | HP bucket core-counts for CLOS resolution (feature_revision >= 2) |
| `SST_PP_CONTROL` | `.feature_state[1]` = SST-TF enable/disable (RW by OS) |
| `SST_CLOS_ASSOC` | Per-core CLOS assignment (HP->CLOS[0], LP->CLOS[3]) |

#### MSRs

| MSR | Address | Description |
|-----|---------|-------------|
| `PRIMARY_TURBO_RATIO_LIMIT` | 0x1AD | 8 x 8-bit ratios per bucket (CDYN 0 / SSE). Updated from SST_PP_INFO_4 |
| `PRIMARY_TURBO_RATIO_LIMIT_CORES` | 0x1AE | 8 x 8-bit core-count-per-bucket. Updated from SST_PP_INFO_10 |

#### PCode TPMI IO Registers

| Register | Description |
|----------|-------------|
| `IO_SST_TF_INFO_0` | LP clip ratios (read by `TrlManager::load_lp_clos_trl`) |
| `IO_SST_TF_INFO_2..7` | HP TRL ratios per CDYN (read by `TrlManager::load_hp_clos_trl`) |
| `IO_SST_TF_INFO_8` | HP bucket core-counts (read by `TrlManager::load_hp_clos_trl`) |
| `IO_SST_PP_INFO_4..9` | SST-PP TRL ratios per CDYN (read by `TrlManager::load_sst_pp_trl`) |
| `IO_SST_PP_INFO_10` | SST-PP TRL buckets (read by `TrlManager::load_sst_pp_trl`) |
| `IO_ODC_TRL_RATIOS` | Resolved TRL ratios = min(SST_PP, MSR 0x1AD, ODC_TURBO_MAX_RATIO) |
| `IO_FIT_INFO_0` | P0n ratios per CDYN level (updated from SST-PP TRL) |

#### Fuses

| Fuse | Description |
|------|-------------|
| `SST_TF_ENABLE` | Per-PP-level: 1=TF supported for this PP level |
| `TURBO_DISABLE` | Global: if 1, all turbo (including TF) is disabled |
| `SST_TF_CONFIG_LP_CLIP_RATIO_ARRAY` | LP clip ratio per CDYN index per PP level |
| `SST_TF_CONFIG_TURBO_RATIO_LIMIT_RATIOS_ARRAY` | HP TRL ratios per bucket x CDYN x PP level |
| `SST_TF_CONFIG_TURBO_RATIO_LIMIT_CORES_ARRAY` | HP core-count per TRL bucket per PP level |
| `SST_PP_TURBO_RATIO_LIMIT_RATIOS_ARRAY` | SST-PP TRL ratios (base, before HP/LP split) |
| `SST_PP_TURBO_RATIO_LIMIT_CORES_ARRAY` | SST-PP TRL bucket boundaries |
| `SST_PP_LEVEL_EN_MASK` | Enabled PP levels bitmask |

#### HPM Messages

| Message | Description |
|---------|-------------|
| `HPM_MSG_COMPUTE_CLOS_CONFIG` | Carries `PKG_MODULE_COUNT_CLOS_0` + `PKG_MODULE_COUNT_CLOS_1` -> updates `num_hp_modules` in TrlManager |


### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | Intel SST HAS (docs.intel.com/documents/pm_doc -> SST) | SST-PP / SST-TF / SST-CP register definitions |
| Primecode src | `src/flow/sst/sst_common/v2_0/sst.cpp` | SST boot PP level init |
| Primecode src | `src/flow/sst/sst_tpmi_general/v2_0/sst_tpmi_general.cpp` | SST TPMI register programming incl. `sstTfInfoInit()` |
| Primecode src | `src/flow/sst/sst_tpmi_compute/v1_0/sst_tpmi_compute.cpp` | Compute-die TRL fuse accessors (`getTrlRatioForSstTfInit`, `getTrlNumCoresForSstTfInit`) |
| PCode src | `source/pcode/flows/sst/sst_manager.h` | SST runtime manager — `get_sst_tf_enabled()`, feature state tracking |
| PCode src | `source/pcode/flows/trls/trl_manager.cpp` | TRL table loading & slow-loop update |
| PCode src | `source/pcode/flows/trls/turbo_ratio_limits.h` | TRL bucket data structures, CDYN-indexed ratio containers |
| Test scripts | Intel SST tool (Linux `intel_speed_select`) | SW discovery/toggle of SST-TF |


### Related Sightings
<!-- No SST-TF-specific NWP sightings identified yet -->
