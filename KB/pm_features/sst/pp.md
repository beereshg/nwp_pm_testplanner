# SST > PP

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SST](sst_main.md)
> **Source Confidence**: High — Architecture from PCode `sst_manager.cpp`/`.h`, Primecode `sst_tpmi_general.cpp`/`.hpp`, fuse definitions in `fuses_sst.xml`, TPMI OSXML. PP is ZBB'd on NWP per [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html).

## Baseline (DMR)

**SST-PP (Performance Profile)** allows up to 5 TDP/frequency configurations (PP0–PP4) to be defined at manufacturing via fuses and selected at runtime by BIOS or OOB management. Each PP level defines its own TDP, P1 ratios (per ISA: SSE/AVX2/AVX512/AMX), TRL arrays, thermal throttle temperature, cooling type, and module disable mask. **ZBB’d on NWP** — `SstResetInit_next` and `SstTpmiResetInit_next` appear in `ok_going_zero.txt`.

**Topology (DMR reference)**: Fuses define up to 5 PP levels → PrimeCode reads fuses and populates SST_PP_INFO_0..11 per level → PCode resolves allowed levels at boot → BIOS/OS selects active level via SST_PP_CONTROL.

```
Reset-time PP initialization
├── PCode reads VDM strap → initial SST_PP_CONTROL.SST_PP_LEVEL
├── PrimeCode tpmiInit(): reads fuses → writes SST_PP_HEADER + SST_PP_INFO_0..11
├── SstManager::post_reset_init(): resolves module masks + RESOLVED_MODULE_COUNT
└── update_cfgs() at BIOS CPL3: computes ALLOWED_LEVEL_MASK

Runtime PP level change (DMR only — not applicable on NWP)
├── SW writes SST_PP_CONTROL.SST_PP_LEVEL
├── PCode update_sst_pp_config(): validates (lock, allowed mask), waits 2 slow loops
└── SST_PP_STATUS updated with new level and error code
```

**Boot activation**: Fuses blown at manufacturing; TPMI registers populated at reset Phase 5. **N/A on NWP** (ZBB’d). DMR only.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Fuse controller | IMH die | Defines PP levels: SST_PP_LEVEL_EN_MASK, per-level P1/TDP/TRL/T_THROTTLE/module-disable arrays | SST_PP fuse arrays (fuses_sst.xml) | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SRAM | IMH-P die | Stores SST_PP_HEADER + SST_PP_INFO_0..11 per PP level; NVM-backed | SST_PP_CONTROL, SST_PP_STATUS, SST_PP_INFO_0..11 | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| VDM strap | IMH-P | Provides initial PP level at reset (SST_PP_CONTROL.SST_PP_LEVEL) | VDM soft strap: SST_PP_LEVEL field | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PrimeCode (IMH-P) | IMH-P | Reads SST_PP fuses; populates SST_PP_HEADER + SST_PP_INFO_0..11 at reset Phase 5 | `sst_tpmi_general.cpp::tpmiInit()`, `sst_common.cpp`, fuse accessors | Primecode source |
| PCode (CBB Root) | Root CBB | Reads VDM strap for initial PP level; resolves ALLOWED_LEVEL_MASK; manages PP level change: validate → wait 2 slow loops → update STATUS | `sst_manager.cpp::init()`, `update_sst_pp_config()`, `post_reset_init()` | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| PCode (CBB Leaf) | Leaf CBB | Receives PP level change via HPM; updates local core-count masks; signals TRL reload | `ccp_manager.cpp`, `ccp_config.cpp` | PCode source |
| BIOS | Pre-OS | Programs initial PP level if different from strap; enforces DQ rules (mutex with FlexRatio for dynamic PP) | BIOS PP level/lock knobs | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| TPMI SST | SST_PP_CONTROL.SST_PP_LEVEL | RW | Requested active PP level; validated by PCode | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_PP_HEADER.ALLOWED_LEVEL_MASK | RO | Runtime-resolved valid PP levels; locked if HWP disabled | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_PP_STATUS.ERROR_TYPE | RO/V | 0=ok, 1=DYNAMIC_PP_SWITCH_NOT_ALLOWED; read-clear via CONTROL write | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_PP_INFO_0..11 (per PP level) | RO | Per-level TDP, P1 ratios, TRL, T_THROTTLE, module counts | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| Maximum PP levels | 5 (PP0–PP4); PP0 = nominal TDP/frequency | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| PP level change propagation | 2 PCode slow-loop cycles before STATUS acknowledges | PCode `sst_manager.cpp` |
| PP lock persistence | SST_PP_CONTROL.SST_PP_LOCK persists until next cold reset | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| NWP status | ❌ ZBB’d — SstResetInit_next, SstTpmiResetInit_next in ok_going_zero.txt | `nwp_imh/v1_0/ok_going_zero.txt` lines 270, 297–298 |

## NWP Delta

### NWP Status: ❌ ZBB'd

SST-PP (Dynamic and Static) is **ZBB'd** on NWP. Test cases listed as `Runnable_On_N-1` are expected to serve as **negative/sanity validation only** — verifying PP is correctly disabled.

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| SST-PP Dynamic | ❌ ZBB'd | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html), [HSD 22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) |
| SST-PP Static | ❌ ZBB'd | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html), [HSD 22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) |

## Legacy (Human-Curated Reference)

### Architecture Summary

**SST-PP (Performance Profile)** allows multiple TDP/frequency configurations (up to 5 levels: PP0–PP4) to be defined at manufacturing via fuses and selectable at runtime by BIOS or OOB management. Each PP level defines its own TDP power, P1 ratios (per ISA: SSE/AVX2/AVX512/AMX), TRL arrays, thermal throttle temperature, cooling type, and core disable mask. PP0 is the base/nominal level; higher PP levels typically trade core count for higher per-core frequency and/or higher TDP. SST-PP is **ZBB'd on NWP** — both `SstResetInit_next` and `SstTpmiResetInit_next` appear in `ok_going_zero.txt`.

#### How It Works

1. **Fuses** define up to 5 PP levels via `SST_PP_LEVEL_EN_MASK` (which levels exist), per-level P1 ratios, TDP, TRL arrays, T_THROTTLE, and module disable masks
2. **Reset** — PCode reads VDM strap for initial PP level (`SST_PP_CONTROL.SST_PP_LEVEL`), validates against `SST_PP_LEVEL_EN_MASK`. If `SST_PP_DYNAMIC_DISABLE` fuse is set, the level is locked at boot
3. **Post-reset** — `SstManager::post_reset_init()` resolves module masks and populates `SST_PP_INFO_1.RESOLVED_MODULE_COUNT` per level
4. **BIOS CPL3** — `update_cfgs()` computes `ALLOWED_LEVEL_MASK` by intersecting fuse enable mask with core-count constraints (PP levels requiring more modules than the boot level are disallowed)
5. **Runtime** — SW writes new level to `SST_PP_CONTROL.SST_PP_LEVEL`. PCode `update_sst_pp_config()` validates (lock check, allowed mask check), updates internal state, waits 2 slow-loops for propagation, then writes `SST_PP_STATUS` with new level and feature state
6. **Error reporting** — If request is invalid: `SST_PP_STATUS.ERROR_TYPE` = `DYNAMIC_PP_SWITCH_NOT_ALLOWED` (0x1). Feature-level errors: `NOT_HW_SUPPORTED` (0x1), `FEATURE_STATE_CHANGE_NOT_ALLOWED` (0x7)

#### PP Level Contents (per level)
- P1 ratios (4 ISA levels: SSE, AVX2, AVX512, AMX)
- TDP power (U12.3 watts)
- TRL array (turbo ratio limits × core-count buckets × CDYN indices)
- Thermal throttle temperature
- Cooling type
- Module disable mask (resolved at runtime)
- BF/TF feature enable (independently controllable per level via `FEATURE_STATE`)


### Key Registers & Interfaces

| Register | Access | Description |
|----------|--------|-------------|
| `SST_PP_HEADER.SST_PP_LEVEL_EN_MASK` | RO | Fused PP levels available |
| `SST_PP_HEADER.ALLOWED_LEVEL_MASK` | RO | Runtime-resolved allowed levels |
| `SST_PP_HEADER.DYNAMIC_SWITCHING` | RO | Whether runtime PP switching is allowed |
| `SST_PP_CONTROL.SST_PP_LEVEL` | RW | Current/requested PP level |
| `SST_PP_CONTROL.SST_PP_LOCK` | RW | Lock bit — once set, level changes rejected till next reset |
| `SST_PP_CONTROL.FEATURE_STATE` | RW | Bit[0]=BF enable, Bit[1]=TF enable |
| `SST_PP_STATUS.SST_PP_LEVEL` | RO/V | Acknowledged PP level |
| `SST_PP_STATUS.ERROR_TYPE` | RO/V | PP-level error code |
| `SST_PP_STATUS.FEATURE_ERROR_TYPE` | RO/V | BF/TF feature error codes |
| `SST_PP_INFO_0` through `SST_PP_INFO_11` | RO | Per-level config: TDP, P1, TRL, module counts, core masks |


### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Intel SST HAS — SST-PP Registers](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html#sst-pp-registers) | Full register definitions |
| PCode SST mgr | `source/pcode/flows/sst/sst_manager.cpp`, `sst_manager.h` | `init()`, `post_reset_init()`, `update_sst_pp_config()` |
| Primecode TPMI general | `src/flow/sst/sst_tpmi_general/v2_0/sst_tpmi_general.cpp` | `tpmiInit()` — PP header/info register population |
| Primecode SST common | `src/flow/sst/sst_common/v2_0/sst.cpp`, `sst.hpp` | `getSstPpLevel()`, `getPureFuse()`, per-level fuse access |
| Primecode fuse defs | `src/ip/fuse/v2_0/fuses_sst.xml` | PP-level fuse arrays |
| TPMI OSXML | `src/cfgdata/tpmi_osxml/v1_0/Struct_all.os.xml` | SST_PP register bitfield definitions |
| NWP ZBB evidence | `src/cfgdata/nwp_imh/v1_0/ok_going_zero.txt` | Lines 270, 297–298 |


### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->
