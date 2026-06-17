# SoC Thermal > TCC (Thermal Control Circuit)

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: TCC (Thermal Control Circuit) defines the temperature setpoint (`eff_tj_max`) at which EMTTM throttling engages across all dies. It is a configuration mechanism — not a standalone throttle — that establishes the common temperature target for all three EMTTM PID loops.

**Topology**:
```
Fuse TjMax ─┬─ SST-PP level T_THROTTLE ─┬─> eff_tj_max ─> Acode PID (Core EMTTM)
             ├─ C1E offset (if disabled)  │               ─> PCode PID (CBB EMTTM)
             └─ TCC offset (MSR 0x1A2)    │               ─> PrimeCode PID (IMH EMTTM)
                                          │
BIOS programs TCC offset at boot ─────────┘
PrimeCode samples at PH2.52 + each reset → distributes to CBBs
```

**Key operational principle**: `eff_tj_max = SST-PP_T_THROTTLE − (C1E_offset + TCC_offset)`. PrimeCode computes at init and on SST-PP level changes via `ThermalVars::updateEffectiveTripPoint()`. `IA32_MISC_ENABLE[3]` is the master enable — when 0, EMTTM does not engage even above eff_tj_max. RATL (`TCC_OFFSET_CLAMPING_BIT`) allows time-averaged throttling below P1 for sustained workloads.

**Boot activation**: TCC offset sampled by PrimeCode at PH2.52 (PCode kernel init) and after each warm/cold reset. Fused TjMax is read at PH1.x during fuse download.

The Thermal Control Circuit (TCC) defines the **temperature threshold** at which the processor begins active thermal throttling (EMTTM). TCC Activation is not a standalone mechanism — it is the **trigger condition** that activates the EMTTM thermal management stack.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| DTS (Core, SOC, CCF, IMH) | CBB Top/Base + IMH | Temperature sensors providing readings against eff_tj_max setpoint for all EMTTM PIDs | SHORT_TELEM push, PMSB IOs | [CBB Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) |
| Fuse array (per die) | All dies | Stores TjMax base (`TJ_MAX_OFFSET`, `TJ_MAX_GUARD_BAND`) and per-SST-PP `T_THROTTLE` temperatures | `SST_PP_x_T_THROTTLE` (x=0..4) | HAS |
| Punit / IO regs (CBB) | CBB Base Die | Reads TCC offset via `IO_TEMPERATURE_TARGET`; computes eff_tj_max for EMTTM PID; reports via `CBB_TEMP_TARGET` PMT | `IO_TEMPERATURE_TARGET.TJ_MAX_TCC_OFFSET` | [CBB Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) |
| PrimeCode (IMH Punit) | IMH die | Samples TCC offset from MSR 0x1A2; computes eff_tj_max via `updateEffectiveTripPoint()`; updates `REF_TEMP` in MSR | `thermal_vars.cpp`; `sampleTempTargetTccOfs()` | PrimeCode src |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PrimeCode (IMH) | IMH die | Samples TCC offset at PH2.52 and each warm/cold reset; computes eff_tj_max; updates `IA32_TEMPERATURE_TARGET[REF_TEMP]`; distributes to CBBs | `ThermalVars::sampleTempTargetTccOfs()`, `updateEffectiveTripPoint()` in `thermal_vars.cpp` | PrimeCode src |
| PCode (CBB) | CBB Base Die | Reads `IO_TEMPERATURE_TARGET.TJ_MAX_TCC_OFFSET`; uses for EMTTM PID temperature target; reports `EFF_TCC_OFFSET` in `CBB_TEMP_TARGET` PMT | PMT 0x2E880 `[31:24] EFF_TCC_OFFSET` | Legacy Key Registers |
| Acode (Core) | Core PMA | Uses eff_tj_max from SHORT_TELEM path as Core EMTTM temperature target; DTD threshold derived from same base | Core EMTTM PID setpoint | Legacy Architecture Summary |
| BIOS / UEFI | Platform | Programs `IA32_TEMPERATURE_TARGET[TJ_MAX_TCC_OFFSET]` at boot; sets `IA32_MISC_ENABLE[3]`; optionally enables RATL via TCC_OFFSET_CLAMPING_BIT | Boot-time MSR programming; TCC offset = 0 by default unless platform-specific | HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_TEMPERATURE_TARGET` | 0x1A2 | RW | [29:24] TJ_MAX_TCC_OFFSET (0–63°C); [23:16] REF_TEMP (≈ eff_tj_max, written by PrimeCode); [15:8] FAN_TEMP_TARGET_OFST; [7] TCC_OFFSET_CLAMPING_BIT (RATL); [6:0] TCC_OFFSET_TIME_WINDOW; [31] LOCKED | Intel SDM |
| MSR `IA32_MISC_ENABLE` | 0x1A0 | RW (vMSR) | [3] AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE — master TCC enable; 0 = EMTTM does not engage even above eff_tj_max | Intel SDM |
| MSR `IA32_THERM_STATUS` | 0x19C (per-core) | RO/RWC | [0/1] THERMAL_MONITOR_STATUS/LOG — core at/above TCC activation point | Intel SDM |
| MSR `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | RO/RWC | [0/1] THERMAL_MONITOR_STATUS/LOG — package at/above TCC activation | Intel SDM |
| TPMI PMT | `CBB_TEMP_TARGET` (0x2E880) | RO | [23:16] EFF_TJ_MAX, [31:24] EFF_TCC_OFFSET — EMTTM telemetry observability | [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/TPMI/DMR_TPMI.html) |
| Fuse | `SST_PP_x_T_THROTTLE` (x=0..4) | — | Per-SST-PP level TCC activation temperature; fused at HVM | HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| TCC offset range | 0–63 | °C | `IA32_TEMPERATURE_TARGET[29:24]`; lowers TCC activation point below fused TjMax | Intel SDM |
| eff_tj_max formula | TjMax − SST-PP_offset − C1E_offset − TCC_offset | °C | Computed by PrimeCode at PH2.52 and after each reset | Legacy Architecture Summary |
| TjMax base (fused) | 125 | °C | Product-specific; TJ_MAX_OFFSET subtracted; TJ_MAX_GUARD_BAND added | Legacy Architecture Summary |
| Guard band (GNR+) | 0 | °C | DTS_CAL_GUARDBAND=0 for GNR and later; REF_TEMP = eff_tj_max exactly | Legacy Key Registers |
| TCC offset sampling cadence | PH2.52 + each reset | — | `sampleTempTargetTccOfs()` in PrimeCode init path | Legacy Source Paths |
| RATL time window | 0–127 | encoded | `IA32_TEMPERATURE_TARGET[6:0]` TCC_OFFSET_TIME_WINDOW; enables below-P1 EMTTM | Intel SDM |
| EMTTM engage latency after TCC threshold crossed | ~300 | μS | Core EMTTM PID period (fastest response); CBB/IMH ~1 mS | EMTTM KB article |
| C1E-disabled TjMax offset (fused) | product-specific | °C | `TJ_MAX_C1E_DISABLED_OFFSET` — extra offset applied when C1E is BIOS-disabled | Legacy Architecture Summary |

## NWP Delta

**TCC (Thermal Control Circuit) is fully supported on NWP** — no changes from DMR.

- TCC activation temperature is factory-fused (REF_TEMP)
- TCC offset via `IA32_TEMPERATURE_TARGET` MSR (0x1A2) `TJ_MAX_TCC_OFFSET` unchanged
- Effective TjMax = TjMax fuse - Eff_TJ_MAX_TCC_Offset
- SST-BF TCC interaction: no SST-PP/BF on NWP → simplified TCC target calculation

### Validation Impact
- Same TCC test cases apply
- No SST-BF cross-product needed (SST-PP/BF/CP removed on NWP)

## Legacy (Human-Curated Reference)

### Architecture Summary

The Thermal Control Circuit (TCC) defines the **temperature threshold** at which the processor begins active thermal throttling (EMTTM). TCC Activation is not a standalone mechanism — it is the **trigger condition** that activates the EMTTM thermal management stack.

#### Key Concepts

- **TCC Activation Temperature** (`eff_tj_max`): The temperature at which EMTTM thermal throttling begins. Derived from fused TjMax minus configurable offsets.
- **TCC Offset** (`TJ_MAX_TCC_OFFSET`): A BIOS-programmable offset (0–63°C) that **lowers** the TCC activation point, causing throttling to engage earlier. Stored in `IA32_TEMPERATURE_TARGET[29:24]`.
- **RATL (Running Average Thermal Limit)**: When `TCC_OFFSET_CLAMPING_BIT[7]` is set in `IA32_TEMPERATURE_TARGET`, EMTTM throttling below P1 is enabled via a time-averaged (EWMA) thermal window.

#### eff_tj_max Derivation

The effective TCC activation temperature is computed by PrimeCode/PCode at boot and on SST-PP level changes:

```
// Fused TjMax base
Tj_max = 125°C - FUSE_TJ_MAX_OFFSET + FUSE_TJ_MAX_GUARD_BAND

// SST-PP resolution (if SST-PP active)
eff_tj_max_sst = SST-BF enabled ?
    SST_BF_CONFIG_[level]_T_THROTTLE :
    SST_PP_[level]_T_THROTTLE

// C1E offset (when C1E disabled by BIOS)
eff_tj_max_c1e_offset = C1E_disabled ?
    fuse.TJ_MAX_C1E_DISABLED_OFFSET : 0

// TCC offset (BIOS-programmed)
eff_tj_max_msr_offset = IA32_TEMPERATURE_TARGET[TJ_MAX_TCC_OFFSET]

// Final calculation
eff_tj_max = eff_tj_max_sst - (eff_tj_max_c1e_offset + eff_tj_max_msr_offset)
```

#### PrimeCode TCC Offset Sampling

PrimeCode (iMH) samples the TCC offset at init and on warm/cold reset via `ThermalVars::sampleTempTargetTccOfs()`:

```cpp
// From src/flow/thermals/thermals_common/v2_0/thermal_vars.cpp
void ThermalVars::sampleTempTargetTccOfs() {
    IOREG_TIE temperature_target(RegOffset::TEMPERATURE_TARGET);
    uint32_t tcc_ofst = 0U;
    BitOps::extract(tcc_ofst, temperature_target.regRead(),
        val(temperature_target::tj_max_tcc_offset_lsb),
        val(temperature_target::tj_max_tcc_offset_num_bits));
    patch_persistent.temperature_target_tcc_ofs = tcc_ofst;
}
```

This feeds `updateEffectiveTripPoint()`:
```cpp
void ThermalVars::updateEffectiveTripPoint() {
    eff_therm_trip = std::fmax(0, (thermal_tj_max - patch_persistent.temperature_target_tcc_ofs));
}
```

#### PCode TCC Usage

CBB PCode reads `IO_TEMPERATURE_TARGET.TJ_MAX_TCC_OFFSET` and uses it for:
- Computing `eff_tj_max` for the EMTTM PID temperature target
- Reporting via `CBB_TEMP_TARGET.EFF_TCC_OFFSET` telemetry register (PMT)
- Computing margins in `MARGIN_TO_THROTTLE` and `MARGIN_TO_TCONTROL`

#### TCC Activation vs BIOS Knob "Auto Thermal Control Circuit Enable"

- `IA32_MISC_ENABLE[3]` (`AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE`) is the **master enable** for per-core TCC/EMTTM
- When bit 3 = 0: Thermal throttling does NOT engage even when temperature exceeds eff_tj_max
- When bit 3 = 1: Normal EMTTM operation — throttling begins at eff_tj_max
- BIOS programs this during boot; must be set for thermal protection

#### RATL (Running Average Thermal Limit)

When `IA32_TEMPERATURE_TARGET[TCC_OFFSET_CLAMPING_BIT]` (bit 7) = 1:
- EMTTM throttling below P1 is allowed
- Thermal averaging uses the time window from `TCC_OFFSET_TIME_WINDOW[6:0]` (bits 6:0)
- Enables sustained workloads to briefly exceed eff_tj_max as long as the running average stays within budget
- Without RATL, EMTTM can only reduce frequency down to P1 (guaranteed ratio)

### Key Registers & Interfaces

#### MSRs

| MSR | Address | Scope | Key Fields | Description |
|-----|---------|-------|------------|-------------|
| `IA32_TEMPERATURE_TARGET` | 0x1A2 | Pkg-MC | `TCC_OFFSET_TIME_WINDOW[6:0]` | RATL averaging window |
| | | | `TCC_OFFSET_CLAMPING_BIT[7]` | Enable RATL throttling below P1 |
| | | | `FAN_TEMP_TARGET_OFST[15:8]` | T-Control offset for fan management |
| | | | `REF_TEMP[23:16]` | Reference temperature (≈ eff_tj_max) |
| | | | `TJ_MAX_TCC_OFFSET[29:24]` | TCC offset (0–63°C) — lowers TCC activation point |
| | | | `LOCKED[31]` | Lock until reset |
| `IA32_MISC_ENABLE` | 0x1A0 | Thread (vMSR) | `AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE[3]` | Master enable for TCC/EMTTM |
| `IA32_THERM_STATUS` | 0x19C | Core | `THERMAL_MONITOR_STATUS[0]` | Core at/above TCC activation point |
| `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | Package | `THERMAL_MONITOR_STATUS[0]` | Package at/above TCC activation point |

#### PCode Internal

| Register | Description |
|----------|-------------|
| `IO_TEMPERATURE_TARGET` | PCode IO backing for MSR 0x1A2 |
| `CBB_TEMP_TARGET` (PMT 0x2E880) | `EFF_TJ_MAX[23:16]`, `EFF_TCC_OFFSET[31:24]` — telemetry observability |

#### Fuses

| Fuse | Description |
|------|-------------|
| `TJ_MAX_OFFSET` | Offset from base 125°C (product-specific SKU binning) |
| `TJ_MAX_GUARD_BAND` | Guard band adder (post-Si margin) |
| `DTS_CAL_GUARDBAND` | DTS calibration guard band (GNR+: 0) |
| `TJ_MAX_C1E_DISABLED_OFFSET` | Additional offset when C1E is disabled by BIOS |
| `SST_PP_x_T_THROTTLE` (x=0..4) | Per SST-PP level TCC activation temperature |
| `SST_BF_CONFIG_x_T_CONTROL_OFFSET` (x=0..4) | Per SST-PP level T-Control offset |
| `THERMAL_THROTTLE_UNLOCK` | Must be set to allow SW disable of EMTTM |

#### Source Paths

| Repo | Path | Key Content |
|------|------|-------------|
| PrimeCode | `src/flow/thermals/thermals_common/v2_0/thermal_vars.cpp` | `sampleTempTargetTccOfs()`, `updateEffectiveTripPoint()` |
| PrimeCode | `src/flow/thermals/thermals_common/v2_0/thermal_vars.hpp` | `ThermalVars` class — `eff_therm_trip`, `temperature_target_tcc_ofs` |
| PrimeCode | `src/flow/thermals/thermals_common/v1_0/thermal_event_handler.cpp` | Reset-time TCC offset sampling |
| PrimeCode | `src/flow/thermals/management/Core/v1_0/core_thermal_management.cpp` | Core EMTTM using `eff_therm_trip` trip points |
| PCode (CBB) | `source/pcode/flows/thermals/thermal_report.cpp` | `IO_TEMPERATURE_TARGET().read().get_TJ_MAX_TCC_OFFSET()` for telemetry |
| PCode (CBB) | `source/pcode/flows/thermals/thermal_report.h` | `EMTTM` class, `get_fused_tj_max()` |

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS (DMR Thermal) | [DMR SoC Thermal HAS — TCC](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | TCC offset, eff_tj_max calculation, RATL |
| HAS (CBB Thermal Mgmt) | [CBB Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) | CBB EMTTM PID using eff_tj_max |
| Related KB | [EMTTM](emttm.md) | Throttling algorithm activated by TCC |
| Related KB | [CBB Thermal Management](cbb_thermal_management.md) | eff_tj_max derivation, PID controller |
| Related KB | [Thermal Reporting](thermal_reporting.md) | How TCC status is reported in MSRs |

#### Test Case Details

**22022421642 — IA32_MISC_ENABLES TCC Enable/Disable**
- Set `AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE` = 0 → heat above eff_tj_max → verify NO throttling
- Set = 1 → verify EMTTM engages normally
- Verify CPUID.06h discovery bits match expected capabilities

**22022421646 — IA32_TEMPERATURE_TARGET Validation**
- Verify `REF_TEMP` = eff_tj_max (with GNR+ guardband = 0)
- Program `TJ_MAX_TCC_OFFSET` = various values (0, 10, 30, 63) → verify eff_tj_max adjusts
- Verify `LOCKED` bit prevents further writes
- Verify SST-PP level changes update REF_TEMP correctly
- Verify `TCC_OFFSET_CLAMPING_BIT` enables RATL below-P1 throttling

**22022421647 — IA32_THERM_STATUS with TCC**
- Heat CCP above eff_tj_max → verify `THERMAL_MONITOR_STATUS[0]` = 1
- Vary `TJ_MAX_TCC_OFFSET` → verify throttling threshold shifts accordingly
- Verify EWMA filter (α=0.7) prevents transient false positives

### NWP Delta

> **Items to verify for NWP** (not yet confirmed — check NWP HAS when available):

| Area | Question | DMR Baseline |
|------|----------|--------------|
| Base TjMax | Same 125°C base? | DMR: 125°C - FUSE_TJ_MAX_OFFSET + guardband |
| TCC Offset range | Same 0–63°C? | DMR: 6-bit field [29:24] in MSR 0x1A2 |
| RATL support | Same clamping bit + time window? | DMR: bit 7 enables below-P1, bits 6:0 = window |
| SST-PP T_THROTTLE | Same per-level fuses? | DMR: 5 SST-PP levels |
| C1E offset | Same `TJ_MAX_C1E_DISABLED_OFFSET` fuse? | DMR: Applied when C1E disabled |
| eff_tj_max formula | Any changes? | DMR: eff_tj_max_sst - (c1e_offset + tcc_offset) |
| DTS_CAL_GUARDBAND | Still 0 (as GNR+)? | GNR+: 0, so REF_TEMP ≈ eff_tj_max |
