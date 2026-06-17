# SoC Thermal > Thermal Reporting

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: Thermal reporting is the observability layer — CBB PCode updates per-core `IA32_THERM_STATUS` each slow-loop; IMH PrimeCode aggregates all-die telemetry via `SOCKET_THERMAL` HPM into package MSRs, D-line registers, and TPMI/PMT entries.

**Topology**:
```
DTS (per-CCP, per-IP) ──> CBB PCode slow-loop (~1mS):
  IA32_THERM_STATUS (0x19C) ──────────────────────────> OS thermal driver
  CORE_PERF_LIMIT_REASONS ────────────────────────────> OS power driver

CBB PCode ──SOCKET_THERMAL HPM──> Root IMH PrimeCode:
  IA32_PACKAGE_THERM_STATUS (0x1B1) ──────────────────> OS + BMC/PECI
  IA32_PACKAGE_THERM_MARGIN (0x1A1) ──────────────────> Fan control
  MCP_THERMAL_REPORT_1 (0x1A3) ───────────────────────> D-line / BMC
  MCP_THERMAL_REPORT_2 (0x1A5) ───────────────────────> D-line / BMC
  PACKAGE_TEMPERATURE (CR 0xFB980) ───────────────────> TPMI PMT
  IA32_TEMPERATURE_TARGET (0x1A2) ────────────────────> BIOS / OS init
```

**Key operational principle**: Per-core TEMPERATURE field is `eff_tj_max − local_temp` (relative, higher = cooler). Package TEMPERATURE is `PKG_MAX_TEMP − eff_tj_max` (margin to throttle). EWMA filter (α=0.7) applied to per-CCP temp before `THERMAL_MONITOR_STATUS` bit is set. OOS detection: temp ≥ eff_tj_max+10°C OR sustained max-throttle for OOS_CNTR_THRESHOLD=20 loops.

**Boot activation**: `IA32_TEMPERATURE_TARGET` programmed by PrimeCode at PH2.52 (eff_tj_max computed). `IA32_MISC_ENABLE[3]` set by BIOS. Steady-state reporting active from PH2.52.

Thermal reporting exposes temperature status, margins, and throttling reasons to OS/SW through a set of MSRs, TPMI registers, and PMT counters. It is the **observability layer** of the thermal management stack — consuming DTS telemetry processed by PCode/PrimeCode and presenting it in architecturally-defined register formats.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| DTS (Core Gen2.6 + IMH Gen1) | All dies | Raw temperature source for all reporting registers | SHORT_TELEM (core, ~102.4μS), SA Thermal Puller (SOC/CCF/IMH, ~1mS) | CBB Thermal HAS; DMR SoC Thermal HAS |
| HPM `SOCKET_THERMAL` bus | CBB→IMH | Carries per-CBB min/max temps, margins, OOS status to Root IMH each slow-loop | HPM message; `OUT_OF_SPEC_STATUS`, `MAX_TEMP`, `MARGIN_TO_THROTTLE` | Socket Thermal HAS |
| CCP PMA CRs | CBB Top Die | `THERM_STATUS_UPDATE` CR (PCode writes) → CCP merges into `IA32_THERM_STATUS` and sets LOG bits | GPSB portid override write | CBB Thermal Mgmt HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core PMA | Provides Core DTS SHORT_TELEM to PCode; no direct OS register writes | SHORT_TELEM push ~102.4μS | ACP PM HAS |
| PCode (CBB) | CBB Base Die | Reads per-CCP max temp; applies EWMA (α=0.7); computes status bits; writes `THERM_STATUS_UPDATE` PMA CR (only on change); updates `CORE_PERF_LIMIT_REASONS`; sets `PP0_TEMPERATURE` | `ThermalReport::update_ccp_therm_status_tx()`; `IO_INTERDIE_THROTTLE_SIGNALS_STATUS` | CBB Thermal Mgmt HAS |
| PrimeCode (IMH) | IMH die | Aggregates `SOCKET_THERMAL` HPM from all leaves; computes `PKG_MAX_TEMPERATURE`; writes all package MSRs; applies optional pkg-level EWMA filter; detects OOS (2 paths); programs `IA32_TEMPERATURE_TARGET` at PH2.52 | `IA32_PACKAGE_THERM_STATUS`; `MCP_THERMAL_REPORT_1/2`; `PACKAGE_TEMPERATURE` CR | DMR Thermal HAS |
| BIOS / UEFI | Platform | Programs `IA32_MISC_ENABLE[3]` (TCC enable); `POWER_CTL`; reads `IA32_TEMPERATURE_TARGET` for fan engagement; configures TPMI thermal registers | Boot-time MSR programming | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_THERM_STATUS` | 0x19C (per-core) | RO/RWC | [0/1] THERMAL_MONITOR_STATUS/LOG; [23:16] TEMPERATURE (relative, higher = cooler); [31] VALID | Intel SDM |
| MSR `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | RO/RWC | [0/1] THERMAL_MONITOR_STATUS/LOG; [4/5] OOS_STATUS/LOG; [23:16] TEMPERATURE (margin to throttle) | Intel SDM |
| MSR `IA32_TEMPERATURE_TARGET` | 0x1A2 | RW | [23:16] REF_TEMP (eff_tj_max − DTS_CAL_GUARDBAND); [15:8] FAN_TEMP_TARGET_OFST (T_CONTROL_OFFSET); [29:24] TCC_OFFSET | Intel SDM |
| MSR `IA32_PACKAGE_THERM_MARGIN` | 0x1A1 | RO | Margin to Tcontrol (S8.8, fan speed control) | Intel SDM |
| MSR `MCP_THERMAL_REPORT_1` | 0x1A3 | RO | [15:0] MARGIN_TO_THROTTLE (S10.6); [31:16] MARGIN_TO_TCONTROL (S10.6) — D-line | Intel SDM |
| MSR `MCP_THERMAL_REPORT_2` | 0x1A5 | RO | Absolute max temperature (S10.6) — D-line | Intel SDM |
| `PACKAGE_TEMPERATURE` CR | 0xFB980 | RO | Absolute pkg max temp + 64°C offset (prevents underflow) | DMR Thermal HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| CBB slow-loop reporting period | ~1 | mS | PCode updates `IA32_THERM_STATUS` and SOCKET_THERMAL HPM per iteration | Legacy Architecture Summary |
| EWMA filter coefficient (α) | 0.7 | — | Applied to per-CCP temperature before THERMAL_MONITOR_STATUS; suppresses single-loop transient spikes | Legacy Execution Flow |
| OOS temperature path threshold | +10 | °C | PKG_MAX_TEMP ≥ eff_tj_max + 10°C → OOS immediately | Legacy Execution Flow |
| OOS timer path (sustained max throttle) | 20 | slow loops | `OOS_CNTR_THRESHOLD` — decremented each loop with max throttle active | Legacy Execution Flow |
| `THERM_STATUS_UPDATE` write guard | On change only | — | PCode skips GPSB write if status unchanged from previous; reduces PMSB traffic | Legacy Execution Flow |
| TEMPERATURE field format (per-core) | eff_tj_max − local_temp | °C | Higher = cooler; 0 = at TCC activation; relative to eff_tj_max | Intel SDM |
| TEMPERATURE field format (package) | PKG_MAX_TEMP − eff_tj_max | °C | Negative = above TCC point (throttling active) | Intel SDM |
| Special DTS codes | 0x8000 / 0x8001 / 0x8002 | — | Not ready / calc error / sensor non-valid; handled in PCode DTS pipeline | Legacy Key Registers |

## NWP Delta

**Thermal reporting (MSRs and TPMI) is fully supported on NWP** — no changes from DMR.

- `IA32_THERM_STATUS` (0x19C), `IA32_TEMPERATURE_TARGET` (0x1A2), `IA32_PACKAGE_THERM_STATUS` (0x1B1) unchanged
- TPMI/PMT thermal reporting flows reused from DMR
- Package temperature = max of all core and uncore DTS readings (single NIO + 2 CBBs)
- Digital Thermometer relative temperature (REF_TEMP based) unchanged
- PECI temperature reporting unchanged

### Validation Impact
- Same thermal reporting test cases apply
- Package temperature aggregation simpler (3 dice vs 6 dice in DMR)

## Legacy (Human-Curated Reference)

### Architecture Summary

Thermal reporting exposes temperature status, margins, and throttling reasons to OS/SW through a set of MSRs, TPMI registers, and PMT counters. It is the **observability layer** of the thermal management stack — consuming DTS telemetry processed by PCode/PrimeCode and presenting it in architecturally-defined register formats.

#### Reporting Hierarchy

```
DTS Sensors (per-CCP, per-IP)
        │
        ▼
CBB PCode: update_ccp_therm_status_tx()          IMH PrimeCode: thermal aggregation
  ├─ IA32_THERM_STATUS (0x19C) — per-core         ├─ IA32_PACKAGE_THERM_STATUS (0x1B1)
  ├─ THERM_STATUS_UPDATE PMA CR → CCP             ├─ IA32_PACKAGE_THERM_MARGIN (0x1A1)
  └─ CORE_PERF_LIMIT_REASONS                      ├─ MCP_THERMAL_REPORT_1 (0x1A3)
                                                   ├─ MCP_THERMAL_REPORT_2 (0x1A5)
    SOCKET_THERMAL HPM ──→                         ├─ PACKAGE_TEMPERATURE
    (leaf → root telemetry)                        ├─ IA32_TEMPERATURE_TARGET (0x1A2)
                                                   └─ POWER_CTL (0x1FC)
```

#### Reporting Scopes

| Scope | Owner | Key Registers | Consumers |
|-------|-------|---------------|-----------|
| **Core** | CBB PCode | `IA32_THERM_STATUS` (0x19C), `CORE_PERF_LIMIT_REASONS` | OS thermal driver, BIOS, telemetry |
| **Package** | Root iMH PrimeCode | `IA32_PACKAGE_THERM_STATUS` (0x1B1), `IA32_PACKAGE_THERM_MARGIN` (0x1A1), `PACKAGE_TEMPERATURE` | OS, BMC/PECI, fan control |
| **D-line** | Root iMH PrimeCode | `MCP_THERMAL_REPORT_1` (0x1A3), `MCP_THERMAL_REPORT_2` (0x1A5) | BMC, out-of-band monitoring |
| **Config/Discovery** | PrimeCode (boot) | `IA32_TEMPERATURE_TARGET` (0x1A2), `IA32_MISC_ENABLE` (0x1A0), `POWER_CTL` (0x1FC) | BIOS, OS init |

#### Multi-Die Reporting Flow

Each leaf CBB/IMH die computes its local thermal metrics and sends them to the Root IMH via `SOCKET_THERMAL` HPM:

```
CBB0/1 ──SOCKET_THERMAL──→ Root IMH (Primary)
CBB2/3 ──SOCKET_THERMAL──→       │
IMH_S  ──SOCKET_THERMAL──→       │
                                  ▼
                          Aggregate: PKG_MAX_TEMP = max(all dies)
                          Compute: margins, OOS, thresholds, PROCHOT
                          Write: IA32_PACKAGE_THERM_STATUS, margins, MCP reports
```

---

### Execution Flow

#### Boot-Time Configuration

1. **PrimeCode reads fuses**: `FUSE_TJ_MAX_OFFSET`, `FUSE_TJ_MAX_GUARD_BAND`, `DTS_CAL_GUARDBAND`, `T_CONTROL_OFFSET`, `SST_PP_T_THROTTLE[]`
2. **PrimeCode computes** `eff_tj_max`:
   ```
   Tj_max = 125°C - FUSE_TJ_MAX_OFFSET + FUSE_TJ_MAX_GUARD_BAND
   eff_tj_max = Tj_max - TJ_MAX_TCC_OFFSET
   ```
   With SST-PP: `eff_tj_max = SST_PP_T_THROTTLE[level]` (or `SST_BF_CONFIG_T_THROTTLE[level]` if SST-BF enabled)
3. **PrimeCode programs** `IA32_TEMPERATURE_TARGET`:
   - `REF_TEMP[23:16]` = eff_tj_max - `FUSE_DTS_CAL_GUARDBAND` (GNR+: GB=0, so REF_TEMP ≈ eff_tj_max)
   - `FAN_TEMP_TARGET_OFST[15:8]` = resolved `FUSED_T_CONTROL_OFFSET`
   - `TCC_OFFSET_TIME_WINDOW[6:0]` = RATL averaging window
4. **BIOS programs** `IA32_MISC_ENABLE[3]` = `AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE` (enables core TCC)
5. **BIOS programs** `POWER_CTL` = VR_THERM_ALERT_DISABLE, PROCHOT config, C1E_ENABLE

#### Steady-State Reporting Loop (CBB PCode)

Each CBB PCode slow loop (~1mS):

1. **Read** per-CCP max temperature from DTS telemetry (`thermals.get_CCP_minmax_temp(ccp_id).maxT()`)
2. **Compute** `temp_delta = eff_tj_max - per_ccp_max_temperature`
3. **Apply EWMA filter**: `filtered_temp = (1-α)×current + α×prev` (α = 0.7, used for `THERMAL_MONITOR_STATUS` only)
4. **Set status bits** in `THERM_STATUS_UPDATE` PMA CR:
   - `THERMAL_MONITOR_STATUS` = 1 if filtered_temp ≥ eff_tj_max (trip_temp - temperature ≤ 0)
   - `THRESHOLD1/2_STATUS` = 1 if temp_delta ≤ `THRESHOLD_REL_TEMP` from `IO_THERM_INTERRUPT`
   - `PROCHOT_STATUS` = live prochot wire from `IO_INTERDIE_THROTTLE_SIGNALS_STATUS`
   - `POWER_LIMITATION_STATUS` = PLR indicates CCP is power limited
   - `CURRENT_LIMIT_STATUS` = same source
5. **Write** `THERM_STATUS_UPDATE` via portid override to CCP PMA (only if changed from previous)
6. **CCP HW** merges status into `IA32_THERM_STATUS` (0x19C), computes LOG bits (sticky until SW clears)
7. **Update** `PP0_TEMPERATURE` (MCHBAR 0x597C) = EWMA max across all CCPs
8. **Set** `CORE_PERF_LIMIT_REASONS` bits: `THERMAL`, `PROCHOT`, `VR_THERMALERT`, `POWER_LIMIT` (status + log)

#### Steady-State Reporting Loop (IMH PrimeCode)

Root IMH PrimeCode aggregates all leaves each slow loop:

1. **Receive** `SOCKET_THERMAL` HPM from each leaf: `OOS_STATUS`, `MIN_TEMP`, `MAX_TEMP`, `MARGIN_TO_THROTTLE`, `MARGIN_TO_TCONTROL`
2. **Compute** `PKG_MAX_TEMPERATURE` = max(all die max temps)
3. **Update** `IA32_PACKAGE_THERM_STATUS` (0x1B1):
   - `TEMPERATURE[23:16]` = `PKG_MAX_TEMPERATURE - eff_tj_max` (relative, °C)
   - `THERMAL_MONITOR_STATUS[0]` = 1 if PKG_MAX_TEMP ≥ eff_tj_max (with optional EWMA filtering)
   - `OOS_STATUS[4]` = 1 if any die reports OOS (temp ≥ eff_tj_max + 10°C for ≥ 3mS, OR throttle timer expired)
   - `PROCHOT_STATUS[2]` = xxPROCHOT_N assertion state
   - `THRESHOLD1/2_STATUS[6/8]` = 1 if (eff_tj_max - PKG_MAX_TEMP) ≤ threshold rel temp
   - `POWER_LIMITATION_STATUS[10]` = aggregated PLR
   - `PMAX_STATUS[12]` = PMAX detector assertion
   - `HW_FEEDBACK_NOTIFICATION_LOG[26]` = HFI table update
   - `VALID[31]` = DTS in valid range
   - All LOG bits: set on 0→1 transition of corresponding STATUS, sticky until SW RW/0C
4. **Update** `IA32_PACKAGE_THERM_MARGIN` (0x1A1):
   - `THERM_MARGIN[15:0]` = `(eff_tj_max - T_CONTROL_OFFSET + DTS_CONFIG3.TCONTROL_OFFSET) - PKG_MAX_TEMP` (S8.8 format)
5. **Update** `MCP_THERMAL_REPORT_1` (0x1A3):
   - `MARGIN_TO_THROTTLE[15:0]` = eff_tj_max - PKG_MAX_TEMP (S10.6)
   - `MARGIN_TO_TCONTROL[31:16]` = margin to T-Control (S10.6)
6. **Update** `MCP_THERMAL_REPORT_2` (0x1A5):
   - `PACKAGE_ABSOLUTE_MAX_TEMPERATURE[15:0]` = absolute max temp in package (S10.6)
7. **Update** `PACKAGE_TEMPERATURE` CR:
   - `DATA[7:0]` = PKG_MAX_TEMP + 64°C (offset to prevent underflow)

#### DTS Reporting During Reset

- During reset phases, DTS sensors may report stale/invalid temperatures
- PCode must handle the transition from invalid → valid DTS data
- `VALID` bit in THERM_STATUS reflects whether DTS is within valid thermal sensor range
- Special codes: `0x8000` = DTS not ready, `0x8001` = temp calculation error, `0x8002` = thermal sensor non-valid

#### Thermal Monitor Filtering (Package)

Optional EWMA filter on `THERMAL_MONITOR_STATUS` to suppress transient thermal throttling events:

```
ALPHA = exp(-1 × DELTA_TIME / TAU)
EWMA_STATUS = ((1 - ALPHA) × PREV_STATUS) + (ALPHA × CURRENT_STATUS)

if (THERMAL_MONITOR_FILTER_ENABLE == 1)
    THERMAL_MONITOR_STATUS = EWMA_FILTERED_STATUS
else
    THERMAL_MONITOR_STATUS = RAW_STATUS

Where:
  DELTA_TIME = elapsed time from previous sample
  TAU = time window programmable via BIOS (SOCKET_THERMAL HPM)
```

This prevents short-duration throttling events (when CPU exceeds TDP transiently per PL1 time window) from appearing as sustained thermal issues.

#### OOS Detection (Package)

DMR has **two OOS trigger paths**:

```
Path 1 (Temperature): PKG_MAX_TEMP ≥ eff_tj_max + 10°C
Path 2 (Timer):        Max throttling engaged for OOS_CNTR_THRESHOLD (20) slow loops

OOS_TIMER decremented while ANY_DIE_MAX_THROTTLED
OOS_TIMER reset to OOS_CNTR_THRESHOLD when not throttled
GLOBAL_THERMAL_OUTSPEC_TIMER_EXPIRED when OOS_TIMER == 0

OUT_OF_SPEC = 1 if:
  (PKG_MAX_TEMP ≥ eff_tj_max + 10°C) OR
  (GLOBAL_THERMAL_OUTSPEC_TIMER_EXPIRED)
OUT_OF_SPEC = 0 if:
  (PKG_MAX_TEMP < eff_tj_max) AND timer not expired
```

Individual dies compute their OOS status and send it via `SOCKET_THERMAL` HPM to Root. Only package status (`IA32_PACKAGE_THERM_STATUS`) is updated — core-scoped OOS is not reported.

---

### Key Registers & Interfaces

#### Core-Scope Reporting MSRs

| MSR | Address | Scope | Key Fields |
|-----|---------|-------|------------|
| `IA32_THERM_STATUS` | 0x19C | Core | `THERMAL_MONITOR_STATUS[0]`, `LOG[1]`, `PROCHOT_STATUS[2]`, `LOG[3]`, `OOS_STATUS[4]`, `LOG[5]`, `THRESHOLD1_STATUS[6]`, `LOG[7]`, `THRESHOLD2_STATUS[8]`, `LOG[9]`, `POWER_LIMIT_STATUS[10]`, `LOG[11]`, `CURRENT_LIMIT[12]`, `LOG[13]`, `CROSS_DOMAIN[14]`, `LOG[15]`, `TEMPERATURE[23:16]` (relative to TjMax), `RESOLUTION[30:27]` (hardcoded 1°C), `VALID[31]` |
| `CORE_PERF_LIMIT_REASONS` | Pkg | Per-CBB | `THERMAL` (status+log), `PROCHOT` (status+log), `VR_THERMALERT` (status+log), `POWER_LIMIT` (status+log) — resolved from CBB PLR |

#### Package-Scope Reporting MSRs

| MSR | Address | Scope | Key Fields |
|-----|---------|-------|------------|
| `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | Package | `THERMAL_MONITOR_STATUS[0]`, `LOG[1]`, `PROCHOT_STATUS[2]`, `LOG[3]`, `OOS_STATUS[4]`, `LOG[5]`, `THRESHOLD1_STATUS[6]`, `LOG[7]`, `THRESHOLD2_STATUS[8]`, `LOG[9]`, `POWER_LIMITATION_STATUS[10]`, `LOG[11]`, `PMAX_STATUS[12]`, `LOG[13]`, `TEMPERATURE[23:16]`, `HW_FEEDBACK_NOTIFICATION_LOG[26]`, `RESOLUTION[30:27]`, `VALID[31]` |
| `IA32_PACKAGE_THERM_MARGIN` | 0x1A1 | Package | `THERM_MARGIN[15:0]` (S8.8 format — margin to T-Control for fan speed regulation) |
| `MCP_THERMAL_REPORT_1` | 0x1A3 | Package | `MARGIN_TO_THROTTLE[15:0]` (S10.6), `MARGIN_TO_TCONTROL[31:16]` (S10.6) — D-line/BMC support |
| `MCP_THERMAL_REPORT_2` | 0x1A5 | Package | `PACKAGE_ABSOLUTE_MAX_TEMPERATURE[15:0]` (S10.6) — D-line/BMC support |
| `PACKAGE_TEMPERATURE` | CR 0xFB980 | Package | `DATA[7:0]` = pkg temp in °C + 64 (offset to prevent underflow) |

#### Configuration/Discovery MSRs

| MSR | Address | Scope | Key Fields |
|-----|---------|-------|------------|
| `IA32_TEMPERATURE_TARGET` | 0x1A2 | Pkg-MC | `TCC_OFFSET_TIME_WINDOW[6:0]`, `TCC_OFFSET_CLAMPING_BIT[7]`, `FAN_TEMP_TARGET_OFST[15:8]` (T-Control offset), `REF_TEMP[23:16]` (throttle temp), `TJ_MAX_TCC_OFFSET[29:24]`, `LOCKED[31]` |
| `IA32_MISC_ENABLE` | 0x1A0 | Thread (vMSR) | `AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE[3]` — enables core TCC/EMTTM |
| `POWER_CTL` | 0x1FC | Package | `ENABLE_BIDIR_PROCHOT[0]`, `C1E_ENABLE[1]`, `DIS_PROCHOT_OUT[21]`, `PROCHOT_RESPONSE[22]`, `PROCHOT_LOCK[23]`, `VR_THERM_ALERT_DISABLE[24]` |

#### DTS_CONFIG3 (T-Control Customer Override)

| Register | Scope | Access | Key Fields |
|----------|-------|--------|------------|
| `DTS_CONFIG3` | Package | MEM (moved from CFG on DMR) | `TCONTROL_OFFSET[7:0]` (S7.0 — bit 7 sign), `OFFSET_PROGRAMMED[8]` |

- Only consumed by PrimeCode if `ENABLE_TCONTROL_PROGRAMMING` fuse = 1
- Locked by default; PrimeCode unlocks via patch for specific customers
- Not documented in customer-facing docs
- DMR: moved from CFG space to MEM space ([HSD 14011447956](https://hsdes.intel.com/appstore/article-one/article/14011447956))

#### PCode Internal Registers

| Register | Description |
|----------|-------------|
| `THERM_STATUS_UPDATE` (PMA CR) | PCode → CCP status update, module-scoped, PMSB |
| `PP0_TEMPERATURE` (MCHBAR 0x597C) | EWMA max CCP temperature in °C |
| `IO_PACKAGE_THERM_STATUS` | PUnit IO backing for `IA32_PACKAGE_THERM_STATUS` |

#### HPM Messages

| Message | Direction | Fields |
|---------|-----------|--------|
| `SOCKET_THERMAL` | Leaf → Root | `OOS_STATUS`, `MIN_TEMP`, `MAX_TEMP`, `MARGIN_TO_THROTTLE`, `MARGIN_TO_TCONTROL`, `THERMAL_MONITOR_ENABLE`, `DECAY`/`TIME_WINDOW` |
| `SOCKET_THERMAL` | Root → Leaf | `THERMAL_MONITOR_ENABLE`, `DECAY` config |

#### DMR Register Migration

PECI-PCS registers migrated to PMT/TPMI on DMR:

| Category | PCS Index | Description | DMR Access |
|----------|-----------|-------------|------------|
| Package Thermal | 20 | Package Thermal Status | TPMI |
| Package Thermal | 20 | Thermal Monitor Filtering Control | TPMI |
| Package Thermal | 2 | Package Temperature | PMT |
| Package Thermal | 10 | Aggregate Margin to Tcontrol | PMT |
| Package Thermal | 16 | Temperature Target | PMT |
| Package Thermal | 32 | Thermal Constrained Time | PMT |

#### Special Margin Codes

| Code | Meaning |
|------|---------|
| `0x8000` (-128 in S8.8) | DTS not ready / thermal system not initialized |
| `0x8001` | Temperature calculation error |
| `0x8002` | Thermal sensor non-valid error |

#### CPUID Discovery (CPUID.06h)

| Leaf | Bit | Description |
|------|-----|-------------|
| `CPUID.06:EDX[29]` | Thermal Monitor supported |
| `CPUID.06:EAX[0]` | Digital Thermal Sensor supported |
| `CPUID.06:EAX[5]` | Enhanced Clock Modulation Duty Cycle supported |
| `CPUID.06:EAX[6]` | Package Thermal Management supported (MSR 0x19A, 0x19B, 0x19C valid) |
| `CPUID.06:EBX[3:0]` | Number of temperature thresholds supported |

---

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS (DMR Thermal) | [DMR SoC Thermal HAS — Thermal Reporting](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | Primary spec — all reporting registers, pseudocode, OOS/THERMAL_MONITOR algorithms |
| HAS (Socket Thermal) | [Socket Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Cross-gen reference for disabled DTS, thermal monitor filter |
| HAS (CBB Thermal) | [CBB Thermal Management](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) | Per-CCP THERM_STATUS_UPDATE, VR_THERM_ALERT PLR |
| HAS (PM Interrupt) | [PM Interrupt Arch HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/pm_interrupt_arch/pm_interrupt_arch.html) | Interrupt generation from status bit transitions |
| HAS (HPM) | [HPM Message Spec](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html#PROCHOT_FREQ_LIMIT) | SOCKET_THERMAL message format |
| PCode src | `source/pcode/flows/thermals/thermal_report.cpp` | `update_ccp_therm_status_tx()`, `send_updated_report_to_imh()`, `update_pp_and_package_therm_report_regs()` |
| PCode src | `source/pcode/flows/thermals/thermal_report.h` | `set_threshold_bits()`, `set_therm_monitor_bits()`, EWMA alpha |
| Related KB | [Thermal Interrupts](thermal_interrupts.md) | How status bit transitions trigger interrupts |
| Related KB | [CBB DTS Telemetry](cbb_dts_telemetry.md) | DTS sensor pipeline feeding reporting |
| Related KB | [Prochot](prochot.md) | PROCHOT_STATUS bit sourcing |
| Related KB | [MCAs](mcas.md) | OOS detection algorithm |
| HSD | 22012487746 | DTS_CONFIG3 locked by ENABLE_TCONTROL_PROGRAMMING fuse |
| HSD | 14011447956 | DMR: DTS_CONFIG3 moved from CFG to MEM space |

#### Validation Approach

- **CORE_PERF_LIMIT_REASONS** (22022421640): Apply thermal load → verify `THERMAL` status+log bits set in `CORE_PERF_LIMIT_REASONS`. Assert PROCHOT → verify `PROCHOT` bits. Trigger VR hot → verify `VR_THERMALERT` bits. Verify log bits are sticky until SW clears. Verify bits are resolved from CBB PLR aggregation (`LEAF_PERF_STATUS` HPM → Root).

- **DTS temperature reporting during reset** (22022421641): Monitor `IA32_THERM_STATUS[VALID]` bit across reset phases. Verify DTS reports special code `0x8000` (not ready) before thermal system initialization. Verify transition to valid temperature post-init. Verify no false THERMAL_MONITOR_STATUS/OOS assertions during reset when DTS is not yet valid. Check `PACKAGE_TEMPERATURE` CR shows correct value after reset completes.

- **IA32_MISC_ENABLES** (22022421642): Verify `AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE` (bit 3) controls core TCC enablement. When bit 3 = 0, verify thermal throttling does not engage even when temperature exceeds eff_tj_max. When bit 3 = 1, verify EMTTM/thermal throttling engages normally. Verify CPUID.06h discovery bits match expected capabilities (DTS, PKG Thermal Mgmt, threshold count).

- **IA32_PACKAGE_THERM_MARGIN** (22022421643): Read `THERM_MARGIN[15:0]` (S8.8) and verify it equals `(eff_tj_max - T_CONTROL_OFFSET + DTS_CONFIG3.TCONTROL_OFFSET) - PKG_MAX_TEMP`. Vary temperature → verify margin tracks linearly. Verify margin goes negative when temp exceeds T-Control point. Verify special code `0x8000` when DTS not ready. Verify each leaf die's margin is sent via `SOCKET_THERMAL` HPM and Root aggregates correctly.

- **IA32_PACKAGE_THERM_STATUS** (22022421644): Comprehensive register validation — verify all 13 status/log bit pairs:
  - `THERMAL_MONITOR_STATUS[0]` / `LOG[1]`: trigger by heating above eff_tj_max. With EWMA filter enabled, verify short transients are suppressed. Verify LOG sticky until RW/0C.
  - `PROCHOT_STATUS[2]` / `LOG[3]`: assert xxPROCHOT_N → verify status tracks live wire.
  - `OOS_STATUS[4]` / `LOG[5]`: verify both trigger paths (temp ≥ eff_tj_max + 10°C AND timer-based).
  - `THRESHOLD1/2_STATUS[6,8]` / `LOG[7,9]`: program thresholds in `IA32_PACKAGE_THERM_INTERRUPT`, verify crossing.
  - `POWER_LIMITATION_STATUS[10]` / `LOG[11]`: apply power limit → verify.
  - `PMAX_STATUS[12]` / `LOG[13]`: trigger PMAX detector assertion.
  - `HW_FEEDBACK_NOTIFICATION_LOG[26]`: trigger HFI update → verify set on 0→1.
  - `TEMPERATURE[23:16]`: verify = PKG_MAX_TEMP - eff_tj_max. Vary temp, check tracking.
  - `VALID[31]`: verify set only when DTS is in valid range.
  - Verify multi-die aggregation (Root takes max across all dies).

- **IA32_TEMPERATURE_TARGET** (22022421646): Verify `REF_TEMP[23:16]` = eff_tj_max - DTS_CAL_GUARDBAND (GNR+: GB=0). Verify `FAN_TEMP_TARGET_OFST[15:8]` = resolved fused T_CONTROL_OFFSET. Verify `TJ_MAX_TCC_OFFSET[29:24]` reflects BIOS-programmed offset. Verify `LOCKED[31]` bit prevents further writes. Verify SST-PP level changes update REF_TEMP correctly. Verify `TCC_OFFSET_CLAMPING_BIT[7]` enables RATL throttling below P1.

- **IA32_THERM_STATUS (Core MSR 0x19c)** (22022421647): Per-core validation — heat individual CCPs and verify:
  - `TEMPERATURE[23:16]` = per-CCP temp relative to TjMax, tracks DTS readings
  - Each status/log bit pair independently: THERMAL_MONITOR, PROCHOT, OOS, THRESHOLD1/2, POWER_LIMIT, CURRENT_LIMIT, CROSS_DOMAIN
  - EWMA filtering: verify α=0.7 filter on THERMAL_MONITOR_STATUS (not raw)
  - CCP-scoped: verify each core reports independently (not cross-contaminated)
  - Verify PCode writes `THERM_STATUS_UPDATE` PMA CR only when values change (efficiency)
  - Verify LOG bits computed by CCP HW, sticky until SW RW/0C

- **MCP_THERMAL_REPORT_1 (MSR 0x1A3)** (22022421649): Verify `MARGIN_TO_THROTTLE[15:0]` = eff_tj_max - PKG_MAX_TEMP (S10.6 format). Verify `MARGIN_TO_TCONTROL[31:16]` = (eff_tj_max - T_CONTROL_OFFSET) - PKG_MAX_TEMP (S10.6). Vary temperature → verify both margins track. Verify D-line/BMC can read via PECI. Cross-check against `IA32_PACKAGE_THERM_MARGIN` (same source, different format).

- **MCP_THERMAL_REPORT_2 (MSR 0x1A5)** (22022421650): Verify `PACKAGE_ABSOLUTE_MAX_TEMPERATURE[15:0]` (S10.6) = absolute max temp across all dies. Verify updates each slow loop. Verify D-line/BMC readability. Cross-check against `PACKAGE_TEMPERATURE` CR (same source, different format/offset).

- **POWER_CTL** (22022421660): Verify all thermal-relevant fields:
  - `ENABLE_BIDIR_PROCHOT[0]`: not used on DMR (input-only prochot)
  - `C1E_ENABLE[1]`: verify interaction with thermal reporting (C1E offset to eff_tj_max)
  - `DIS_PROCHOT_OUT[21]`: verify prochot output disable
  - `PROCHOT_RESPONSE[22]`: verify prochot response control
  - `PROCHOT_LOCK[23]`: verify lock prevents changes to prochot and VR_THERM_ALERT_DISABLE
  - `VR_THERM_ALERT_DISABLE[24]`: verify disables VR hot reporting/action
  - Verify register is programmed during boot and values persist

- **Extended C6 validation for Thermal Die Level PLR** (22022421665): BEAT test — verify `CORE_PERF_LIMIT_REASONS` thermal/power limit bits behave correctly when cores enter/exit C6. Verify PLR bits are updated even when core is in C6 (status registers updated unconditionally per HAS). Verify per-die PLR aggregation via `LEAF_PERF_STATUS` HPM maintains correctness across C6 transitions. Verify no false PLR assertions after C6 exit due to stale thermal data.

---

### Related Sightings
<!-- No NWP thermal reporting sightings identified yet — populate as they arise -->

---

### NWP Delta

> **Items to verify for NWP** (not yet confirmed — check NWP HAS when available):

| Area | Question | DMR Baseline |
|------|----------|--------------|
| PID thermal control (IMH) | Same dual-domain PID (Memory Fabric + IO Fabric)? Kp=0.17, Ki=0.06? | DMR: PID replaces N-Strike for IMH fabric throttling |
| Thermal monitor EWMA filter | Same TAU / time-window config via BIOS? | DMR: programmable via SOCKET_THERMAL HPM DECAY field |
| OOS timer-based path | Same OOS_CNTR_THRESHOLD=20? | DMR: 20 slow loops of max throttling triggers OOS |
| OOS temperature offset | Same eff_tj_max + 10°C? | DMR: `THERM_OUTOFSPEC_TEMP` = 10°C |
| eff_tj_max formula | Same base 125°C - offset + guardband? | DMR: Tj_max = 125°C - FUSE_TJ_MAX_OFFSET + FUSE_TJ_MAX_GUARD_BAND |
| DTS_CONFIG3 access | Still MEM space? Or further migrated? | DMR: moved from CFG → MEM space |
| PECI-PCS → PMT/TPMI | Same migration for PCS indices 2, 10, 16, 20, 32? | DMR: TPMI for status/filtering, PMT for temp/margin/target |
| CORE_PERF_LIMIT_REASONS | NWP PLR bit assignments match DMR? | DMR: THERMAL, PROCHOT, VR_THERMALERT, POWER_LIMIT |
| Cross-die thermal reporting | NWP die topology for SOCKET_THERMAL HPM aggregation? | DMR: 4 CBB + 2 IMH leaves → Root |
| THERM_STATUS_UPDATE PMA CR | CCP-scoped for BigCore — NWP core type impact? | DMR: module-scoped PMA CR, PMSB delivery |
| Special margin codes | Same 0x8000/0x8001/0x8002? | DMR: documented in HAS |
| MCP_THERMAL_REPORT registers | Same D-line format? Or deprecated/changed? | DMR: 0x1A3 and 0x1A5 for BMC/PECI |
| Squared error acceleration | Same `THERMAL_SQUARED_ERROR_ENABLE` / threshold = -1 for PID? | DMR: accelerates frequency response above TjMax |

#### Confirmed from SERVERPMFW-24119 (NWP MC & CLTT PFHAS)

| Area | NWP Status | Detail |
|------|-----------|--------|
| DIMM temperature source | ✅ **MR4-only** | LPDDR6 does not support TSOD. DIMM temps sourced exclusively from MR4 registers via `IO_TELEMETRY` in PUnit. Same bit encoding/conversion as DMR. |
| DIMM temp aggregation | ✅ Same HPM path | PrimeCode aggregates MR4 DIMM temps on root IO die via HPM — same as DMR. Thermal reporting chain unchanged. |
| DIMM temp conversion | ⚠️ Temporary DMR ranges | Using DMR Gen4 DDR MC HAS MR4/MR109 conversion ranges until NWP LPDDR6-specific ranges provided by architecture. |
| TSOD temperature path | ❌ **Removed** | No TSOD on LPDDR6. No I3C TSOD configuration. `SB_I3C_PUNIT_DEST_ID` not programmed. PECI-based CLTT (`CLTT_PECI_ENABLE` bit 6) still available as override. |

**Source**: [SERVERPMFW-24119 NWP MC & CLTT PFHAS](https://docs.intel.com/documents/primecode/fhas/NWP/SERVERPMFW-24119_NWP_Memory_Controller_Changes.html)
