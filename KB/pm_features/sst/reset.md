# SST > Reset

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SST](sst_main.md)
> **Source Confidence**: High — Reset flow from PCode `sst_manager.cpp` (`init`, `post_reset_init`), `reset.cpp`, `ccp_config.cpp`, Primecode `sst_tpmi_general.cpp` (`tpmiInit`, `repopulateSstVarsFromTpmiReg`). NWP scope inferred from [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) SST scope.

## Baseline (DMR)

**SST Reset** defines SST configuration behavior across cold boot, warm boot, and firmware update boundaries. On **cold boot**, all SST state is re-initialized from fuses and VDM straps. On **warm boot**, SST configuration persists via `FWU_VAR` — PP level, CP/TF/BF enable, lock state, and priority type survive across warm resets. `SST_PP_LOCK`, once set, persists until the next cold reset.

**Topology**: Fuses + VDM strap → PCode `SstManager::init()` (cold: full re-init; warm: FWU_VAR restore) → `SstManager::post_reset_init()` (resolves module mask) → `update_cfgs()` at BIOS CPL3.

```
Cold boot
├── SstManager::init(): reads VDM strap for initial PP level
├── PrimeCode SstTpmiGeneral::tpmiInit(): populates all SST TPMI banks from fuses
├── SstManager::post_reset_init(): resolves RESOLVED_MODULE_MASK
└── update_cfgs() at BIOS CPL3: computes ALLOWED_LEVEL_MASK, runs configs_done

Warm boot (FWU boundary)
├── SstManager::init(): detects fw_update_flow.in_progress() → skips full re-init
├── PrimeCode repopulateSstVarsFromTpmiReg(): reloads internal state from surviving TPMI regs
├── FWU_VAR persists: sst_pp_level, sst_tf_enabled, sst_cp_enabled, sst_pp_locked, etc.
└── update_cfgs() runs again at BIOS CPL3 with configs_done = false (re-runs configs)
```

**Boot activation**: SST TPMI registers populated at reset Phase 5. Cold boot: from fuses. Warm boot: from FWU_VAR. SST_PP_LOCK bit persists until power cycle (cold reset).

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| VDM strap | IMH-P | Provides initial PP level at cold reset (SST_PP_CONTROL.SST_PP_LEVEL strap field) | VDMdw1 SST_PP_LEVEL field | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SRAM + NVM | IMH-P die | SST register banks; NVM-backed fields survive warm reset; FWU_VAR in PCode SRAM | SST_PP_CONTROL, SST_PP_STATUS, SST_HEADER | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Fuse controller | IMH die | Source of truth for all SST configuration on cold boot (SST_PP_LEVEL_EN_MASK, per-level arrays) | SST fuse arrays (fuses_sst.xml) | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PrimeCode (IMH-P) | IMH-P | Cold boot: `tpmiInit()` populates all SST TPMI banks from fuses. Warm boot: `repopulateSstVarsFromTpmiReg()` reloads internal state | `sst_tpmi_general.cpp::tpmiInit()`, `repopulateSstVarsFromTpmiReg()` | Primecode source |
| PCode (CBB Root) | Root CBB | Cold: `SstManager::init()` reads VDM strap + full init. Warm: detects FWU in progress, restores from FWU_VAR. Both: `post_reset_init()` resolves module masks | `sst_manager.cpp::init()`, `post_reset_init()` | PCode source |
| PCode (CBB Leaf) | Leaf CBB | CCP manager re-resolves core masks after reset: sst_pp_lvl_changed or reset_resolve triggers recompute | `ccp_manager.cpp`, `ccp_config.cpp` | PCode source |
| BIOS | Pre-OS | Triggers `update_cfgs()` at CPL3; sets `configs_done` flag (false at init, ensuring configs re-run post-FWU) | BIOS CPL3 SST config flow | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| TPMI SST | SST_PP_CONTROL.SST_PP_LEVEL | RW | Active PP level; cold: VDM strap; warm: FWU_VAR preserved | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_PP_CONTROL.SST_PP_LOCK | RW | Lock bit: persists until cold reset once set; cold: from SST_PP_DYNAMIC_DISABLE fuse | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_PP_STATUS | RO/V | Mirrors CONTROL after update; survives warm via FWU_VAR | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| FWU_VAR variables that persist | sst_pp_level, sst_tf_enabled, sst_bf_enabled, sst_cp_enabled, sst_pp_locked, sst_cp_priority_type, sst_pp_level_last_request | PCode `sst_manager.cpp` |
| Cold vs warm re-init | Cold: full tpmiInit() from fuses. Warm: repopulateSstVarsFromTpmiReg() from surviving TPMI | Primecode source |
| SST_PP_LOCK cold reset | Cleared on cold reset only; survives warm reset and FWU | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| NWP applicable scope | SST-TF/PCT reset persistence only; SST-PP/CP/BF warm boot is out of scope (ZBB’d) | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |

## NWP Delta

### NWP Status: ⚠ Partial

Reset events × SST. Warm/cold boot persistence testing is applicable for **SST-TF/PCT configuration only** — verifying PCT CLOS assignments, TRL overrides, and feature_state survive resets.

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| SST-TF/PCT reset persistence | ✅ Applicable | Inferred from NWP PM MAS SST scope |
| SST-PP/CP/BF reset persistence | ❌ Out of scope (ZBB'd) | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |

## Legacy (Human-Curated Reference)

### Architecture Summary

**SST Reset** covers the behavior of SST configuration across warm boot, cold boot, and firmware update (FWU) boundaries. On **cold boot**, all SST state is re-initialized from fuses and VDM straps — PP level reverts to the strap-programmed initial value, CP/BF/TF are reset to fuse defaults, and all TPMI registers are repopulated. On **warm boot**, SST configuration **persists** through the `FWU_VAR` mechanism — the PP level, CP enable, lock state, and last-request parameters survive across warm resets. The SST `SST_PP_CONTROL.SST_PP_LOCK` bit, once set, persists until the next cold reset, preventing further PP level changes.

#### Reset Sequence

1. **Cold boot path** — `SstManager::init()` reads fuses and VDM strap for initial PP level, programs all TPMI registers (HEADER, PP_CONTROL, PP_STATUS, CP). Primecode `SstTpmiGeneral::tpmiInit()` populates all SST TPMI register banks from fuses
2. **Warm boot path** — `FWU_VAR`-tagged variables (`sst_pp_level`, `sst_tf_enabled`, `sst_bf_enabled`, `sst_cp_enabled`, `sst_pp_locked`, `sst_cp_priority_type`) are preserved. `SstManager::init()` checks `fw_update_flow.in_progress()` and skips re-initialization if FWU. Primecode calls `repopulateSstVarsFromTpmiReg()` to reload internal state from surviving TPMI registers
3. **Post-reset** — `SstManager::post_reset_init()` updates `RESOLVED_MODULE_MASK` (requires reset-computed topology data). PCode CCP manager re-resolves core masks: `sst_pp_lvl_changed || reset_resolve` triggers re-computation
4. **Configs gate** — `update_cfgs()` runs only after BIOS CPL3. `configs_done` flag is `false` on init, ensuring configs re-run after FWU

#### FWU_VAR Persistence (PCode SST Manager)
| Variable | Default | Survives Warm Boot |
|----------|---------|-------------------|
| `sst_pp_level` | from strap | Yes |
| `sst_tf_enabled` | false | Yes |
| `sst_bf_enabled` | false | Yes |
| `sst_cp_enabled` | false | Yes |
| `sst_pp_locked` | false | Yes |
| `sst_cp_priority_type` | 0 | Yes |
| `sst_pp_level_last_request` | MAX+1 (sentinel) | Yes |
| `sst_pp_control_changed` | false | Yes |
| `sst_pp_status_update_counter` | 0 | Yes |
| `sst_pp_level_error` | false | Yes |


### Key Registers & Interfaces

| Register | Reset Behavior |
|----------|---------------|
| `SST_PP_CONTROL.SST_PP_LEVEL` | Cold: set from VDM strap. Warm: preserved |
| `SST_PP_CONTROL.SST_PP_LOCK` | Cold: set from `SST_PP_DYNAMIC_DISABLE` fuse. Warm: preserved |
| `SST_PP_STATUS` | Cold: mirrors control. Warm: preserved via FWU_VAR |
| `SST_HEADER.CAPABILITY_MASK` | Cold: from fuses. Warm: preserved |
| `SST_CP_STATUS.EXCURSION_TO_MIN` | Clearable via `SST_CP_CONTROL.RESET_EXCURSION_TO_MIN` |
| All `SST_PP_INFO_*` | Repopulated from fuses during reset (both warm and cold) |


### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST_PP_LOCK, reset behavior |
| PCode SST mgr | `source/pcode/flows/sst/sst_manager.cpp` | `init()`, `post_reset_init()` |
| PCode reset | `source/pcode/reset/reset.cpp` | SST_PP_INFO calculation during reset |
| PCode CCP config | `source/pcode/drivers/ccp_config.cpp` | SST_PP strap select at reset |
| PCode CCP manager | `source/pcode/drivers/ccp_manager.cpp` | Reset-resolve mask recomputation |
| Primecode TPMI general | `src/flow/sst/sst_tpmi_general/v2_0/sst_tpmi_general.cpp` | `repopulateSstVarsFromTpmiReg()` |
| Primecode SST flow | `src/flow/sst/sst_common/v2_0/sst.cpp` | `getSstPpLevel()` from VDM strap |


### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->
