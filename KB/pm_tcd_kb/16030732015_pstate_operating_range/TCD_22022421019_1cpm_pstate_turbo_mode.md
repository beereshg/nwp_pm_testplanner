# TCD 22022421019 -- 1CPM - Pstate Turbo Mode

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421019](https://hsdes.intel.com/appstore/article-one/#/22022421019) |
| **Title** | 1CPM - Pstate Turbo Mode |
| **Status** | open |
| **Owner** | akurathi |
| **Parent TPF** | [16030732015 -- P-State Operating Range & Frequency Configuration](https://hsdes.intel.com/appstore/article-one/#/16030732015) |
| **Child TCs** | [22022422391](https://hsdes.intel.com/appstore/article-one/#/22022422391) -- 1 Core Per Module Check |
| **KB last updated** | 2026-07-17 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**1CPM (1 Core Per Module) Turbo**, also called **Module Turbo**, grants additional turbo frequency headroom when only one core in a DCM (Dual Core Module) is active. Since the remaining core's power/thermal budget is unused, PCode can grant the active core a higher TRL than the standard multi-core TRL would allow.

The feature is gated by fusing (`SST_PP_MISC_STATUS.MODULE_TURBO_CAPABILITY`), enabled by BIOS/OS via `SST_PP_MISC_CONTROL.MODULE_TURBO_CONTROL`, and enforced by PCode through the TRL resolver in the slow loop.

### Key Concepts

| Concept | Description |
|---------|-------------|
| **1CPM / Module Turbo** | When only 1 core per DCM module is active, PCode grants a higher 1CPM TRL ratio vs standard multi-core TRL |
| **MODULE_TURBO_CAPABILITY** | RO fuse bit in `SST_PP_MISC_STATUS` -- 1=supported, 0=not supported on this SKU |
| **MODULE_TURBO_CONTROL** | RW bit in `SST_PP_MISC_CONTROL` -- 1=enable, 0=disable module turbo |
| **MODULE_TURBO_STATUS** | RO status bit in `SST_PP_MISC_STATUS` -- reflects current active state |
| **1CPM TRL** | Special TRL bucket for single-core-per-module scenario; higher than all-core TRL |
| **DCM** | Dual Core Module -- NWP PantherCove (PNC) module contains 2 threads per module |
| **PMA single_cpm_disable** | PCode writes `PMA_CR_CONFIG_10.single_cpm_disable` bit to CCF PMA to enable/disable the 1CPM path |

### NWP-Specific Deltas

- NWP uses **PantherCove (PNC)** core with **2 threads per module** -- 1CPM means 1 active thread in the module.
- **2 CBBs** (cbb0 + cbb1) -- PCode iterates over big-core CCPs only (`ccp_cfg.get_big_ccp_mask()`).
- **Atom dies excluded** -- `reset.get_is_atom_die()` check skips 1CPM on atom/efficiency cores.
- **SST integration** -- 1CPM is part of the SST-PP MISC register set; controlled alongside SST-TF/PCT.

### PCode Implementation Details

- **SstManager** (`flows/sst/sst_manager.cpp`): Monitors `SST_PP_MISC_CONTROL.MODULE_TURBO_CONTROL` in slow loop. When changed, updates `MODULE_TURBO_STATUS` and sets `module_turbo_enabled_changed` flag.
- **PeriodicRegisterUpdate** (`flows/periodic_register_update.cpp`): `module_turbo_ccp_update_tx(ccp_id)` runs per-CCP. Reads `MODULE_TURBO_STATUS`, writes `PMA_CR_CONFIG_10.single_cpm_disable` to each CCF PMA.
- **Fuse gate**: Only enters 1CPM logic if `SST_PP_MISC_STATUS_MODULE_TURBO_CAPABILITY` fuse is set AND not an atom die.

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422391 -- 1 Core Per Module Check](https://hsdes.intel.com/appstore/article-one/#/22022422391) | 1CPM turbo grant | Verify Module Turbo grants higher TRL when 1 core active per module; verify capability/control/status registers; frequency observed via PERF_STATUS |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Direction | Description |
|-----------|----------------|-----------|-------------|
| TPMI SST | SST_PP_MISC_STATUS.MODULE_TURBO_CAPABILITY | RO | Fuse-derived: 1=1CPM supported on this SKU |
| TPMI SST | SST_PP_MISC_CONTROL.MODULE_TURBO_CONTROL | RW | Enable/disable Module Turbo (BIOS/OS) |
| TPMI SST | SST_PP_MISC_STATUS.MODULE_TURBO_STATUS | RO | Current active state (set by PCode) |
| PCode internal | PMA_CR_CONFIG_10.single_cpm_disable | WO | PCode writes to CCF PMA per CCP to control 1CPM path |
| MSR | IA32_PERF_STATUS (0x198) | RO | Observed frequency ratio -- used to verify 1CPM TRL reached |
| MSR | IA32_HWP_CAPABILITIES (0x771) | RO | P0n ratio -- 1CPM TRL may exceed standard P0n |
| Fuse | SST_PP_MISC_STATUS_MODULE_TURBO_CAPABILITY | RO | Source fuse for capability bit |
| PythonSV | sv.socket0.nio0.tpmi.sst_pp_misc_status.module_turbo_capability | RO | Capability readback |
| PythonSV | sv.socket0.nio0.tpmi.sst_pp_misc_control.module_turbo_control | RW | Enable/disable |

---

## Section 3: Reset / Power / Clocking

- **PH5 (PrimeCode)**: `SST_PP_MISC_STATUS.MODULE_TURBO_CAPABILITY` populated from fuse.
- **CPL3 (BIOS)**: BIOS reads capability; if supported, writes `MODULE_TURBO_CONTROL=1` to enable.
- **PCode slow loop**: `SstManager` detects control change, updates status, signals `module_turbo_enabled_changed`.
- **PeriodicRegisterUpdate**: Propagates enable/disable to each CCF PMA via `PMA_CR_CONFIG_10`.
- **Reset**: Module Turbo state lost on cold reset; BIOS must re-enable at CPL3. Warm reset preserves.
- **C-state interaction**: When all cores in a module exit C-state, PCode re-evaluates 1CPM eligibility.

---

## Section 4: Programming Model

### Enable 1CPM (BIOS/OS)

```python
nio = sv.socket0.nio0
# Check capability
cap = nio.tpmi.sst_pp_misc_status.module_turbo_capability
assert cap == 1, "Module Turbo not supported on this SKU"

# Enable Module Turbo
nio.tpmi.sst_pp_misc_control.module_turbo_control.write(1)
import time; time.sleep(0.02)  # Wait for slow loop

# Verify status
status = nio.tpmi.sst_pp_misc_status.module_turbo_status
assert status == 1, "Module Turbo not active after enable"
```

### Validate 1CPM TRL

```python
# Put all cores except 1 in C6 via PEGA
import pm.pmutils.pega as pega
pega.pegaCstate(0, 'cbb0', domainDict={'c6sp': 'all_but_core0'})
time.sleep(0.05)

# Read active frequency on remaining core
perf_status = sv.socket0.cbb0.compute0.module0.core0.thread0.msr(0x198)
current_ratio = (perf_status >> 8) & 0xFF

# Should be at 1CPM TRL (higher than all-core TRL)
p0n = nio.tpmi.sst_pp_info_11.p0_fabric_ratio
print(f"1CPM ratio: {current_ratio}, P0n: {p0n}")
# 1CPM TRL >= P0n expected
```

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior |
|----------|-------------------|
| 1 core active per module, 1CPM enabled | Core runs at 1CPM TRL (higher than multi-core TRL) |
| 2 cores active in module, 1CPM enabled | Standard multi-core TRL applies; no 1CPM boost |
| 1CPM capability=0 (not fused) | MODULE_TURBO_CONTROL writes have no effect; status stays 0 |
| BIOS enables 1CPM at CPL3 | PCode detects, writes PMA_CR_CONFIG_10; active within 1 slow-loop |
| OS disables 1CPM at runtime | PCode reverts PMA_CR_CONFIG_10; 1CPM TRL no longer granted |
| 1CPM + thermal limit | Thermal cap overrides 1CPM TRL if Tj exceeded |
| 1CPM + RAPL PL1 | RAPL constraint overrides 1CPM TRL if power budget exceeded |
| C-state exit (1 core wakes) | PCode re-evaluates 1CPM eligibility; grants 1CPM TRL if only 1 core active |

---

## Section 6: Corner Cases & Error Handling

- **Module boundary**: Verify 1CPM is per-module, not per-CBB. Two modules in a CBB can each have 1CPM independently.
- **Thread vs core**: On PNC with 2 threads/core, verify 1CPM considers core-level activity, not thread-level.
- **1CPM + SST-TF interaction**: Verify 1CPM TRL takes precedence over SST-TF HP TRL when applicable.
- **1CPM + PCT interaction**: Verify PCT HP core + 1CPM grants the maximum available ratio.
- **1CPM disabled mid-workload**: Verify frequency drops from 1CPM TRL to standard TRL within 1 slow-loop.
- **Atom die exclusion**: Verify 1CPM is not applied to atom/efficiency cores (`get_is_atom_die()` check).
- **Capability=0 + Control=1**: Verify PCode ignores enable when capability bit is 0.

---

## Section 7: Security / Safety / Policy

- MODULE_TURBO_CONTROL is in TPMI (OS-accessible at ring-0). No lock bit documented.
- 1CPM does not bypass thermal or RAPL limits -- global constraints always override.
- MODULE_TURBO_CAPABILITY is fuse-derived (RO) -- cannot be SW-enabled on unsupported SKUs.

---

## Section 8: References

- [Core P-State HAS -- TRL & Module Turbo](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html)
- [SST Intel HAS -- SST_PP_MISC registers](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [NWP PM MAS -- Module Turbo](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [Parent TPF HSD 16030732015](https://hsdes.intel.com/appstore/article-one/#/16030732015)