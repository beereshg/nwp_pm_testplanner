# Pstate Stack > Pstate-Turbo Mode

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: Turbo mode allows cores to boost above P1 when thermal and power headroom is available. Turbo Ratio Limits (TRL) define the maximum turbo per active core count — fused at manufacturing, optionally overridden by BIOS/OOB. Sub-features: Module Turbo (1CPM, allows one core per module to boost higher), PCT (Priority Core Turbo, preferred cores get higher TRL). NWP: SST-PP/BF removed (single TRL profile); monolithic (no MasterMax multi-die coordination).

**Topology**:
```
Fuse TRL (per active core count: 1..N) ─┐
BIOS/OOB TRL override (downward only) ──┤─> effective_TRL = min(fused, override)
                                         │
PCode turbo manager (each PEGA cycle):
  power_headroom  = PL1/PL2_budget - current_package_power
  thermal_headroom = Tjmax - current_Tj
  ICCP_license_cap = current ICCP license ratio ceiling
  EET_attenuation  = EET-reduced max turbo
  resolved_turbo = min(effective_TRL[active_cores], power_hdroom, thermal_hdroom, ICCP, EET)
Core FIVR + PLL ──> operating at resolved_turbo
  PLR (MSR 0x64F): reports which constraint(s) limited turbo
```

**Key operational principle**: Turbo is fully automatic — OS enables turbo (via `IA32_MISC_ENABLE[38]`=0 means turbo allowed) and sets HWP_REQUEST/PERF_CTL; PCode handles the rest. 1CPM allows modules with only one active core to exceed the multi-core TRL. PCT designates preferred cores that receive priority allocation of higher TRL slots.

**Boot activation**: BIOS enables turbo mode. PCode reads TRL fuses at boot. Turbo active from CPL3 handoff whenever headroom exists.

Turbo mode allows CPU cores to operate above the guaranteed P1 frequency when thermal and power headroom exists. The turbo frequency range extends from P1 up to the maximum single-core turbo (P01), with the achievable turbo ratio decreasing as more cores become active. Turbo Ratio Limits (TRL) define the maximum turbo ratio for each active core count, fused at manufacturing and optionally overridden by BIOS or OOB.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core FIVR + PLL | CBB Top Die | Execute GV transition to turbo ratio when PCode grants boost above P1; hold at turbo while headroom exists | GV control; ratio register | CBB PM HAS |
| TRL fuse register | IMH die | Stores manufacturing-characterized max turbo ratio per active core count (1..N cores); basis for turbo headroom | Fuse read at boot | CBB PM HAS |
| Package thermal sensor + power sensor | CBB / IMH | Measure Tj and package power for continuous turbo headroom evaluation | Thermal diode; power measurement | CBB PM HAS |
| PLR interface (MSR 0x64F) | Per-core | Reports which constraint (thermal, power, ICCP, EET) is actively limiting turbo | MSR 0x64F | PLR HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | Provides thermal telemetry (SHORT_TELEM) to PCode; no direct turbo management role | SHORT_TELEM | ACP PM HAS |
| PCode / PEGA (CBB) | CBB Base Die | Reads TRL fuses + overrides at boot; evaluates power/thermal/ICCP/EET headroom each PEGA cycle; resolves turbo ratio per active core count; manages 1CPM + PCT priority scheduling; sets PLR on turbo limit | Turbo flow; `source/pcode/flows/autonomous_pstate/` | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) |
| PrimeCode (IMH) | IMH die | Propagates package-level power limits to CBB PCode as turbo headroom constraint; no direct per-core turbo role | HPM power limits | DMR SoC PM HAS |
| BIOS / UEFI | Platform | Enables turbo mode; programs TRL overrides (BIOS knobs); configures 1CPM, PCT; sets PL1/PL2 (power budget for turbo headroom) | BIOS knobs; MSR 0x1A0[38]=0 enables turbo | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `TURBO_RATIO_LIMIT` | 0x1AD [63:0] | RO | Max turbo ratio for active core counts 1–8 (1 ratio per byte); fused TRL | Intel SDM |
| MSR `IA32_MISC_ENABLE` | 0x1A0 [38] | RW | Turbo disable bit: 1 = turbo disabled; 0 = turbo allowed (default) | Intel SDM |
| MSR `IA32_PERF_STATUS` | 0x198 | RO | Current operating ratio (reflects turbo boost or PLR-limited value) | Intel SDM |
| TPMI TRL | TPMI MMIO | RW (OOB) | OOB read/override of TRL values; BMC can lower max turbo OOB | TPMI HAS |
| MSR `PACKAGE_POWER_LIMIT` | 0x610 | RW | PL1/PL2 power budget that constrains turbo headroom | Intel SDM |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Turbo activation condition | power_headroom > 0 AND thermal_headroom > 0 | — | Both power budget and thermal margin required for turbo boost | Legacy Execution Flow |
| TRL variation by core count | P0n (1 core) → P1 (all cores) | — | TRL decreases as active core count increases; fuse-dependent per NWP SKU | Legacy Architecture Summary |
| Module Turbo (1CPM) | Higher than multi-core TRL | ratio | When only 1 core active per module, 1CPM grants higher boost than standard multi-core TRL | Legacy Architecture Summary |
| MasterMax | N/A (NWP monolithic) | — | MasterMax multi-die turbo coordination removed; not applicable on single-die NWP | Legacy NWP Delta |
| PLR turbo reason | MSR 0x64F bits | — | Thermal/Power/ICCP/EET PLR bits report active turbo limiting reason | Legacy Execution Flow |

## NWP Delta

**Turbo mode and TRL (Turbo Ratio Limits) are fully supported on NWP server** — reused from DMR.

- Turbo mode activation, ratio selection, and TRL flows unchanged
- Same MSR_TURBO_RATIO_LIMIT interfaces
- Same fuse-based TRL definitions
- PantherCove BigCore turbo algorithm reused

### Topology Impact
- 2 CBBs × 48 cores = 96 cores max → different active-core TRL profile (fuse-dependent)
- SST-PP removed → no per-SST-level TRL variation
- SST-BF removed → no SST-BF high-frequency core boost at guaranteed ratio

### Validation Impact
- Same turbo mode test cases apply
- TRL values will differ from DMR (different core count, different fuse profile)
- Skip SST-PP/BF TRL cross-product tests

## Legacy (Human-Curated Reference)

### Architecture Summary

Turbo mode allows CPU cores to operate above the guaranteed P1 frequency when thermal and power headroom exists. The turbo frequency range extends from P1 up to the maximum single-core turbo (P01), with the achievable turbo ratio decreasing as more cores become active. Turbo Ratio Limits (TRL) define the maximum turbo ratio for each active core count, fused at manufacturing and optionally overridden by BIOS or OOB.

PCode manages turbo by continuously evaluating available headroom: package power budget (PL1/PL2 minus current power), thermal margin (Tjmax minus current temperature), electrical limits (ICCP license, VR current), and per-core turbo ratio limits. When headroom is available, PCode allows cores to boost above P1. When headroom is exhausted, PCode clips frequency back to P1 or below.

Key turbo sub-features include: **Module Turbo (1CPM)** — allows one core per module to boost higher than the multi-core TRL; **Priority Core Turbo (PCT)** — designates preferred cores that receive higher turbo ratios; **MasterMax Turbo** — coordinates turbo across dies in multi-die packages; **Turbo Bypass** — allows OS to disable turbo selectively. Turbo functionality is validated across BIOS configurations, OOB TPMI control, scaling governors, harasser stress tests, warm resets, and Resource Isolation Technology (RIT) scenarios.

### Execution Flow

1. **BIOS Configuration** — BIOS enables turbo mode and programs TRL overrides (if any). Module Turbo, PCT, and other turbo sub-features are configured via BIOS knobs.
2. **Fuse Read** — PCode reads fused TRL values for 1-core through N-core active counts. These define the maximum turbo ratio per active core count.
3. **TRL Override** — BIOS or OOB (via TPMI TURBO_RATIO_LIMIT_WRITE) can override fused TRL values downward. PCode uses min(fused_TRL, override_TRL) as the effective limit.
4. **Turbo Headroom Evaluation** — PCode evaluates power headroom (PL1/PL2 budget), thermal headroom (Tjmax margin), electrical limits (ICCP, VR), and active core count to determine the achievable turbo ratio.
5. **Turbo Boost** — If headroom exists, PCode boosts core frequency above P1 up to the TRL for the current active core count. Module Turbo may allow higher ratio for single-core-per-module configurations.
6. **Dynamic Adjustment** — As workload, temperature, and power change, PCode continuously adjusts turbo ratio. PLR bits report any turbo limiting reasons.
7. **Validation** — Tests verify TRL accuracy, turbo enable/disable, PCT core preference, Module Turbo boost, turbo persistence across warm resets, and turbo behavior under OOB TPMI control.

### Key Registers & Interfaces

| Register / MSR | Address | Description |
|----------------|---------|-------------|
| TURBO_RATIO_LIMIT | MSR 0x1AD–0x1AE | Fused TRL per active core count |
| TURBO_RATIO_LIMIT_CORES | MSR 0x1AE | Extended TRL for high core counts |
| IA32_MISC_ENABLE | MSR 0x1A0 bit 38 | Turbo disable bit |
| IA32_PERF_STATUS | MSR 0x198 | Current turbo ratio |
| TPMI TRL | TPMI MMIO | OOB turbo ratio limit read/write |
| PACKAGE_POWER_LIMIT | MSR 0x610 | PL1/PL2 power budget for turbo |
| IA32_THERM_STATUS | MSR 0x19C | Thermal margin for turbo |
| PLR | MSR 0x64F | Turbo limit reasons |
| MODULE_TURBO_CONFIG | PCode internal | 1CPM configuration |
| PCT_CONFIG | PCode internal | Priority Core Turbo designation |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) | Full turbo specification |
| HAS | [DMR Turbo — PCT](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html#priority-core-turbo-pct) | Priority Core Turbo |
| HAS | [DMR Turbo — Module Turbo (1CPM)](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html#module-turbo-1-core-per-module) | Module Turbo 1CPM |
| HAS | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) | Turbo in P-state context |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | CBB PM turbo management |
| MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP turbo specification |
| Primecode src | `src/flow/turbo/` | Turbo ratio limit enforcement |
| PCode src | `source/pcode/flows/autonomous_pstate/` | Turbo boost flow |

### Related Sightings

Turbo ratio not reaching fused TRL, PCT core ranking inconsistency, and 1CPM boost not activating are common DMR sighting patterns. Monitor on NWP.

### NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| Turbo mode | Supported | Supported | Same turbo framework |
| TRL fuses | DMR SKU-specific | NWP SKU-specific | Different fused ratio values |
| Module Turbo (1CPM) | Supported | Supported | Same 1CPM mechanism |
| PCT | Supported | Supported | Same priority core logic |
| MasterMax | Multi-die coordination | N/A (monolithic) | No cross-die turbo on NWP |
| OOB TRL via TPMI | Supported | Supported | Same TPMI interface |
| RIT | Supported | Supported | Resource Isolation Technology preserved |
