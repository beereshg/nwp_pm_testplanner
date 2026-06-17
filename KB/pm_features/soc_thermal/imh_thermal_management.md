# SoC Thermal > IMH Thermal Management

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: PrimeCode runs two independent PID feedback loops (Memory Fabric and IO Fabric) to keep IMH die temperature below `eff_tj_max`. Also generates package thermal telemetry (OOS detection, EWMA-filtered THERMAL_MONITOR_STATUS) and aggregates all-die thermal status into OS MSRs.

**Topology**:
```
IMH DTS (max per fabric domain) ──> PrimeCode PID loops (Kp=0.17 Ki=0.06)
  Mem Fabric PID ──> Mem Fabric freq ceiling ──> GPSS
  IO  Fabric PID ──> IO  Fabric freq ceiling ──> GPSS
    │
    ├── OOS check (max_temp ≥ eff_tj_max + 10°C + timer) ──> IA32_PACKAGE_THERM_STATUS[OOS]
    ├── EWMA filter ──> THERMAL_MONITOR_STATUS
    └── HPM SOCKET_THERMAL (per CBB) ──> Root aggregate ──> MCP_THERMAL_REPORT_1/2
```

**Key operational principle**: Squared-error acceleration (error ≤ −1°C → error ← −error²) for fast response when near TjMax. Cross-die throttle: CBB→IMH (`UPS_EVENT_DELIVERY`) forces fabric to P1. EMTTM master enable: `FIRM_CONFIG[4]` (BIOS) or `PCODE_SYSTEM_MODES_CONTROL[6]` (DFX). UFS thermal ceiling (`CLM_PERF_LIMIT_REASONS.CLIPPED_EMTTM` MSR 0x6B1 bit 1).

**Boot activation**: BIOS programs `FIRM_CONFIG.EMTTM_ENABLE=1` at PH0. PrimeCode slow loop and EMTTM PID active from PH2.52.

IMH thermal management controls fabric frequencies (Memory Fabric and IO Fabric) to keep die temperature below TJ_MAX. Unlike CBB which uses ACP-based per-core thermal management, IMH relies on a **PID (Proportional-Integral-Derivative) control loop** for sustained thermal throttling.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| IMH DTS (19 per die) | IMH die | Per-domain max temperature as PID input; all IP stacks monitored | RC read 0x7E00/0x7E04; 5 RC channels | [DMR SoC Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) |
| GPSS / Fabric clock gate | IMH die | Applies PrimeCode PID freq ceiling to Memory Fabric and IO Fabric independently | Fabric freq ratio registers (slow-limits check) | [DMR SoC Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) |
| FIVR rails (VCCCFCMEM, VCCCFCIO) | IMH die | Voltage rails for fabric; EMTTM PID freq ceiling constrains operating point | `RESCTRL_CR_VOLTAGE_OFFSET.OFFSET` | RC HAS |
| PMSB / HPM bus | IMH↔CBB | Carries `SOCKET_THERMAL` HPM (OOS, min/max temp, margins); carries `UPS_EVENT_DELIVERY[cross_die_throttle]` | HPM message bus | Socket Thermal HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core PMA | No IMH EMTTM role; Core EMTTM runs at CBB layer | — | — |
| PCode (CBB) | CBB Base Die | Sends `HPM UPS_EVENT_DELIVERY[cross_die_throttle]` to IMH when CBB hot → IMH forces fabric to P1 | `UPS_EVENT_DELIVERY` HPM | CBB PM HAS |
| PrimeCode (IMH) | IMH die | Runs two independent EMTTM PID loops (Mem + IO fabric) each slow loop (~1mS); OOS detection; EWMA filtering of THERMAL_MONITOR_STATUS; populates all package thermal MSRs; sends HPM DNS_EVENT_DELIVERY[cross_die_throttle] | `FIRM_CONFIG[4]`; `MCP_THERMAL_REPORT_1/2`; `IA32_PACKAGE_THERM_STATUS`; `DNS_EVENT_DELIVERY` | [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) |
| BIOS / UEFI | Platform | Programs `FIRM_CONFIG.EMTTM_ENABLE`; sets EWMA TAU; optionally programs `DTS_CONFIG3.TCONTROL_OFFSET` (gated by fuse `ENABLE_TCONTROL_PROGRAMMING`) | Boot-time firmware init | HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | RO/RWC | [0/1] THERMAL_MONITOR_STATUS/LOG; [4/5] OUT_OF_SPEC_STATUS/LOG; [23:16] TEMPERATURE | Intel SDM |
| MSR `MCP_THERMAL_REPORT_1` | 0x1A3 | RO | [15:0] MARGIN_TO_THROTTLE; [31:16] MARGIN_TO_TCONTROL (D-line, from PrimeCode) | Intel SDM |
| MSR `MCP_THERMAL_REPORT_2` | 0x1A5 | RO | Absolute max temperature (D-line) | Intel SDM |
| MSR `IA32_PACKAGE_THERM_MARGIN` | 0x1A1 | RO | Margin to Tcontrol (8.8 fixed-point) for fan speed control | Intel SDM |
| `FIRM_CONFIG[4]` | — | RW (BIOS) | `EMTTM_ENABLE` — master enable for uncore thermal throttling | Legacy Key Registers |
| `CLM_PERF_LIMIT_REASONS` | MSR 0x6B1 | RO | [1] `CLIPPED_EMTTM` — mesh freq thermally limited by IMH PID; [17] sticky log | [UFS HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/UFS/UFS_HAS.html) |
| `DTS_CONFIG3` | MEM space | RW | `TCONTROL_OFFSET[6:0]` — fan engage temp offset; gated by fuse `ENABLE_TCONTROL_PROGRAMMING` | Legacy Key Registers |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| IMH EMTTM PID period | ~1 | mS | PrimeCode slow loop; separate loops for Mem Fabric and IO Fabric | Legacy Architecture Summary |
| PID Kp (proportional gain) | 0.17 | — | Default for both Mem and IO fabric PIDs; client-derived value | Legacy Architecture Summary |
| PID Ki (integral gain) | 0.06 | — | Default for both Mem and IO fabric PIDs | Legacy Architecture Summary |
| Squared-error acceleration threshold | −1 | °C | error ≤ −1°C → error ← −error²; faster freq reduction when near TjMax | Legacy Execution Flow |
| OOS temperature offset | +10 | °C | OOS when max_temp ≥ eff_tj_max + 10°C (`THERM_OUTOFSPEC_TEMP`) | Legacy Execution Flow |
| OOS hold-off counter threshold | 20 | — | `OOS_CNTR_THRESHOLD` — max-throttled iterations before OOS asserted | Legacy Execution Flow |
| EMTTM active from | PH2.52 | — | PCode kernel enabled; BIOS programs `FIRM_CONFIG.EMTTM_ENABLE=1` | Legacy Boot Sequence |
| UFS thermal ceiling (PLR bit) | `CLIPPED_EMTTM` | bit 1 MSR 0x6B1 | Asserts when PID output limits mesh freq; [17] sticky log | Legacy Feature Interactions |
| Cold-action TDP adjustment | Runtime | — | DMR option #2: hot/typical binning + runtime delta at cold temps | Legacy Execution Flow |

## NWP Delta

**IMH thermal management is supported on NWP** via NIO (single die, derivative of IMH2).

### Topology Changes
- Single NIO die — one PrimeCode instance runs IMH EMTTM
- No cross-IMH thermal coordination needed (vs dual IMH in DMR)
- Memory stack is LPDDR6 (vs DDR5) — different thermal characteristics

### Functional Changes
- EMTTM PID algorithm unchanged
- Memory fabric and IO fabric frequency limiting via PrimeCode unchanged
- HPM SOCKET_THERMAL messaging to CBBs unchanged (1 NIO → 2 CBBs)
- N-Strike disabled for NIO (PID only, same as DMR IMH)
- Cross-die throttle: "no plans to add nor deprecate any CBB PM flow" — but cross-die throttle may be simplified since only 1 NIO

### Validation Impact
- Single NIO simplifies thermal management test matrix
- LPDDR6 thermal behavior needs separate characterization
- Verify NIO→CBB HPM thermal messages with 2-CBB topology

## Legacy (Human-Curated Reference)

### Architecture Summary

IMH thermal management controls fabric frequencies (Memory Fabric and IO Fabric) to keep die temperature below TJ_MAX. Unlike CBB which uses ACP-based per-core thermal management, IMH relies on a **PID (Proportional-Integral-Derivative) control loop** for sustained thermal throttling.

**Key DMR deltas from legacy:**
- CBB Pcode handles all CBB die thermal actions + core throttling; IMH Primecode does NOT support the N-Strike core throttling algorithm
- Cross-die throttling is NOT supported by default — each die manages its own thermals independently
- PID-based controller replaces the legacy N-Strike algorithm for IMH die, providing ~0.5 bin better fabric frequency under sustained workloads near TJ_MAX
- Dual fabric support (Memory Fabric + IO Fabric) with independent PID loops per fabric domain

**Two layers of thermal management:**
1. **PID-based EMTTM** at IMH die boundary (controlled by Primecode):
   - Separate PID loops for Memory Fabric and IO Fabric
   - Input: Max temp across each fabric domain + Effective TJ_MAX
   - Output: Fabric frequency ceiling applied in slow-limits check
   - Default PID parameters: Kp = 0.17, Ki = 0.06
   - Squared-error acceleration for temps above TJ_MAX (enabled by default, threshold = -1°C)
2. **Cross-die throttling** (HPM-based, limited support):
   - IMH→CBB: `DNS_EVENT_DELIVERY[cross_die_throttle]` — CBB overrides temp input to TJ_MAX
   - CBB→IMH: `UPS_EVENT_DELIVERY[cross_die_throttle]` — IMH forces fabric freqs to P1

### Execution Flow

#### PID Thermal Control (Slow Loop)
1. **BIOS config**: BIOS programs `FIRM_CONFIG.EMTTM_ENABLE=1` and thermal fuses are loaded
2. **Temperature collection**: Primecode collects DTS telemetry from all IMH IP domains every slow loop
3. **Effective TJ_MAX calculation**:
   ```
   EFFECTIVE_TJ_MAX_SST = IF(SST_PP_CONTROL.FEATURE_STATE) SST_BF_CONFIG_T_THROTTLE ELSE SST_PP_T_THROTTLE
   EFFECTIVE_TJ_MAX = EFFECTIVE_TJ_MAX_SST - EFFECTIVE_TJ_MAX_OFFSET_MSR - EFFECTIVE_TJ_MAX_OFFSET_C1E
   IF(FUSE_OC_ENABLED) EFFECTIVE_TJ_MAX = OC_TJ_MAX_OVERRIDE
   ```
4. **PID computation** (per fabric domain):
   ```
   PID_INPUT_ERROR = EFFECTIVE_TJ_MAX - DTS_MAX_TEMP
   IF(THERMAL_SQUARED_ERROR_ENABLE AND PID_INPUT_ERROR <= -1):
       PID_INPUT_ERROR = (PID_INPUT_ERROR)^2   # acceleration
   ERROR_DELTA = PID_INPUT_ERROR - PID_INPUT_ERROR_PREV
   # Standard PID: Kp * error + Ki * integral + Kd * derivative
   ```
5. **Frequency ceiling**: PID output applied as fabric frequency ceiling in slow-limits check
6. **OS observable**: `IA32_PACKAGE_THERM_STATUS.THERMAL_MONITOR_STATUS` set when any die throttling

#### Disabling Uncore Thermal Throttling
Two mechanisms (debug only — risks overheat):
- `PCODE_SYSTEM_MODES_CONTROL[6]` = 1 → disables EMTTM (package-scoped DFX hook)
- `FIRM_CONFIG[4]` = 0 → disables EMTTM (BIOS-controlled, locks TT2 to fixed P-state/LFM)

#### Cold Action
- Temperature can cause worst-case power at **cold** temps (leakage + ITD voltage offsets)
- DMR assumes hot/typical temperature for binning but adjusts power/frequency limits at cold
- TDP @ Cold: see [DMR Socket RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#tdp-cold)
- PMAX @ Cold: see DMR PMAX HAS

#### Thermal Reporting (IMH → Package MSRs)

IMH PrimeCode aggregates thermal data from all dies via HPM and populates package-scoped registers.

##### THERMAL_MONITOR_STATUS (bit 0 of `IA32_PACKAGE_THERM_STATUS`)
Set when any die in the package is thermally throttling. Supports **EWMA filtering** to suppress transient assertions:
```
if (PKG_MAX_TEMPERATURE >= EFFECTIVE_TJ_MAX)
    RAW_THERMAL_MONITOR_STATUS = 1
else
    RAW_THERMAL_MONITOR_STATUS = 0

ALPHA = exp^(-1 * DELTA_TIME / TAU)
EWMA_FILTERED = ((1-ALPHA) * PREV_STATUS) + (ALPHA * CURRENT_STATUS)

if (THERMAL_MONITOR_FILTER_ENABLE = 1)
    THERMAL_MONITOR_STATUS = EWMA_FILTERED
else
    THERMAL_MONITOR_STATUS = RAW_THERMAL_MONITOR_STATUS
```
- **TAU** is programmable by BIOS — sets the averaging time window
- Even with a proper thermal solution, transient throttling may occur during turbo bursts before fans respond
- Customers can enable filtering to report only **sustained** thermal throttling

##### Out-of-Spec (OOS) Detection
OOS is an interrupt-only event — indicates the system is heading toward thermtrip. Does NOT trigger additional throttling.
```
OOS_CNTR_THRESHOLD = 20

# Timer decrements while any die is max-throttled
IF (ANY_DIE_MAX_THROTTLED)
    OOS_TIMER = OOS_TIMER - 1
ELSE
    OOS_TIMER = OOS_CNTR_THRESHOLD

# OOS assertion logic
IF (PKG_MAX_TEMPERATURE >= EFFECTIVE_TJ_MAX + 10)     # THERM_OUTOFSPEC_TEMP = 10°C
    OUT_OF_SPEC = 1
ELSE IF (OOS_TIMER == 0)                              # sustained max throttle
    OUT_OF_SPEC = 1
ELSE IF (PKG_MAX_TEMPERATURE < EFFECTIVE_TJ_MAX)       # below throttle temp
    OUT_OF_SPEC = 0
```
- Individual dies compute their own OOS status and send to root via HPM `SOCKET_THERMAL`
- Only package-scoped OOS is reported (not per-core)

##### Temperature Reporting
- `IA32_PACKAGE_THERM_STATUS.TEMPERATURE[23:16]` = `PKG_MAX_TEMPERATURE - EFFECTIVE_TJ_MAX` (margin to throttle, relative)
- `PACKAGE_TEMPERATURE` (PCU CR 0xfb980) = absolute temp + 64°C (to prevent underflow)
- `IA32_PACKAGE_THERM_MARGIN.THERM_MARGIN` = `(EFFECTIVE_TJ_MAX - FUSED_T_CONTROL_OFFSET + DTS_CONFIG3.TCONTROL_OFFSET) - MAX_TEMPERATURE` (8.8 format, for fan speed control)

##### MCP Thermal Reporting (D-line support)
- `MCP_THERMAL_REPORT_1` (Pkg MSR 0x1A3): Margin to Throttle, Margin to Tcontrol
- `MCP_THERMAL_REPORT_2` (Pkg MSR 0x1A5): Absolute Max Temperature

##### DTS_CONFIG3 (Tcontrol Offset)
Allows customers to adjust the fan engagement temperature (`Tcontrol`) relative to TjMax:
- `TCONTROL_OFFSET[6:0]` — unsigned integer offset; bit 7 = sign bit
- `OFFSET_PROGRAMMED[8]` — set when SW has programmed the offset
- Gated by fuse `ENABLE_TCONTROL_PROGRAMMING` (must be 1 to take effect)
- Register moved from CFG space to MEM space on DMR ([HSD 14011447956](https://hsdes.intel.com/appstore/article-one/article/14011447956))
- ⚠️ Locked by default — PrimeCode unlocks via patch only for customers who need it

##### Special Thermal Margin Codes
| Code | Meaning |
|------|---------|
| `0x8000` | DTS not ready (also returned if BMC reads before thermal init) |
| `0x8001` | Temp calculation error |
| `0x8002` | Thermal sensor non-valid error |

### Key Registers & Interfaces

| Register / Interface | Scope | Purpose |
|---|---|---|
| `FIRM_CONFIG[4]` (EMTTM_ENABLE) | Package | BIOS enables/disables EMTTM |
| `PCODE_SYSTEM_MODES_CONTROL[6]` | Package | DFX hook to disable EMTTM |
| `IA32_PACKAGE_THERM_STATUS` (MSR 0x1B1) | Package | Thermal monitor status, OOS, prochot, thresholds, temperature |
| `IA32_TEMPERATURE_TARGET` (MSR 0x1A4) | Package | TJ_MAX, TCC_OFFSET, FAN_TEMP_TARGET_OFST |
| `PACKAGE_TEMPERATURE` (PCU CR 0xfb980) | Package | Absolute package temp (+ 64°C offset) |
| `IA32_PACKAGE_THERM_MARGIN` (MSR 0x1A1) | Package | Margin to Tcontrol (8.8 format) for fan control |
| HPM `SOCKET_THERMAL` | Die→Root | Leaf dies report: OOS status, min/max temp, margin to throttle/Tcontrol |
| HPM `DNS_EVENT_DELIVERY[cross_die_throttle]` | Root→Leaf | IMH→CBB cross-die throttle assertion |
| HPM `UPS_EVENT_DELIVERY[cross_die_throttle]` | Leaf→Root | CBB→IMH cross-die throttle assertion |
| `SST_PP_T_THROTTLE[pp_index]` | Die fuse | TJ_MAX per SST-PP level |
| `FUSE_THERMAL_THROTTLE_UNLOCK` | Die fuse | If set, SW can disable EMTTM |
| `MCP_THERMAL_REPORT_1` (MSR 0x1A3) | Package | Margin to Throttle + Margin to Tcontrol (D-line) |
| `MCP_THERMAL_REPORT_2` (MSR 0x1A5) | Package | Absolute Max Temperature (D-line) |
| `DTS_CONFIG3` (MEM space) | Package | `TCONTROL_OFFSET[6:0]` + sign bit + `OFFSET_PROGRAMMED[8]` |

#### Thermal Fuses
| Fuse | Width | Scope | Format | Description |
|------|-------|-------|--------|-------------|
| `SST_PP_[pp]_T_THROTTLE` | 8 | Die (CBB & IMH) | — | TjMax for this SST PP level (initial throttle threshold) |
| `SST_BF_CONFIG_[pp]_T_THROTTLE` | 8 | Die (CBB & IMH) | — | TjMax when SST BF enabled |
| `T_CONTROL_OFFSET` | 5 | Die (CBB & IMH) | U5.0 | Fan engage temp negative offset from TjMax |
| `SST_BF_CONFIG_[pp]_T_CONTROL_OFFSET` | 5 | Die | U5.0 | Tcontrol offset when SST BF enabled |
| `DTS_CAL_GUARDBAND` | 7 | Die | U3.4 | DTS calibration guardband in °C (value is zero on DMR) |
| `TRUE_TD_ENABLE` | 1 | Die | — | Enable True TD for core/mesh voltage rails |
| `ENABLE_TCONTROL_PROGRAMMING` | 1 | Die | — | Allow `DTS_CONFIG3.TCONTROL_OFFSET` to take effect |
| `THERMAL_THROTTLE_UNLOCK` | 1 | Die | — | If set, SW can disable EMTTM |
| `DISABLED_MODULE_DTS_MASK` | 64 | CBB Die | — | Per-module bitmask; 1=ignore that module's DTS |
| `IMH_DOMAIN_ITD_SLOPE` | 5 | Die | U-8.13 | ITD slope per rail (°C/V) |
| `ITD_CUTOFF_TJ` | 7 | Die | U7.0 | Temperature above which ITD not needed |
| `MIN_ACCURATE_TEMP` | 7 | Die | S6.0 | Temp below which DTS readings unreliable |

### Feature Interactions

#### UFS (Uncore Frequency Scaling) × Thermal

IMH EMTTM PID output feeds directly into the UFS frequency resolution as `clm_thermal_limit` — a hard ceiling on mesh/CLM frequency:

```
# UFS Final Consolidation (from UFS HAS)
max_clm_freq = min(MSR_UNCORE_RATIO_LIMIT[MAX_RATIO],
                   clm_rapl_limit,
                   clm_thermal_limit,        # ← IMH EMTTM PID output
                   FUSE_CFC_P0_RATIO)

min_clm_freq = max(MSR_UNCORE_RATIO_LIMIT[MIN_RATIO],
                   perf_p_limit,
                   FUSE_CFC_MIN_RATIO)

clm_freq = clamp(clm_freq_from_ufs, min_clm_freq, max_clm_freq)
```

**Key interactions:**

| Aspect | Detail |
|--------|--------|
| Thermal ceiling | IMH PID reduces fabric freq when die temp approaches TjMax → overrides UFS autonomous decisions |
| PLR reporting | `CLM_PERF_LIMIT_REASONS.CLIPPED_EMTTM` (MSR 0x6B1, bit 1) = 1 when thermal is limiting mesh freq; `CLIPPED_EMTTM_LOG` (bit 17) = sticky |
| Active Idle | UFS Active Idle Efficiency Mode respects thermal limits — resolved freq is "subjected to SLOW_LIMITS like RAPL and thermal flows" |
| UFS-RAPL | When power-constrained, UFS-RAPL reduces mesh freq linearly with core RAPL limit — if both thermal AND RAPL limit, the lower ceiling wins |
| Concurrent IO | In concurrent core+IO scenarios, UFS may bypass RAPL ceiling for IO BW — but thermal ceiling is never bypassed |
| Squared error | When PID squared-error kicks in (temp > TjMax + 1°C), thermal ceiling drops more aggressively, overriding any UFS up-votes |

> **Validation note for test 22022421520 (Verify Uncore Throttling)**: Confirm `CLM_PERF_LIMIT_REASONS.CLIPPED_EMTTM` asserts when PID output limits mesh freq. Verify it clears when PID releases the ceiling.

---

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR SoC Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | Comprehensive DMR thermal management |
| HAS | [CBB Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) | CBB EMTTM/ACP thermal details |
| HAS | [Socket Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Wave3 common thermal framework |
| HAS | [DMR RAPL HAS (TDP Cold)](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#tdp-cold) | Cold temperature power adjustments |
| HAS | [UFS HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/UFS/UFS_HAS.html) | UFS algorithm, UFS-RAPL, thermal ceiling in Final Consolidation |
| Primecode src | TODO | |
| PCode src | TODO | |
| Test scripts | TODO | |

#### Test Case Details

**22022421518 — Verify Cold Action**
- Validates runtime cold-temperature adjustments to power/frequency limits
- Cold temp shifts the power envelope: leakage decreases but ITD voltage compensation increases → net power impact varies by operating point
- Historically the hottest temperature was worst-case for TDP/Pmax, but since SKX/BDX, worst-case power can occur at cold
- DMR uses option #2: assume hot/typical for binning, then apply runtime adjustments at cold
- **Checks**: TDP cold adjustment applied correctly, PMAX cold adjustment applied, frequency limits consistent with cold power model

**22022421519 — Verify Disabling Uncore Thermal Throttling**
- Tests the two DFX disable mechanisms:
  1. `PCODE_SYSTEM_MODES_CONTROL[6]` (EMTTM_DISABLE) = 1 → disables EMTTM
  2. `FIRM_CONFIG[4]` (EMTTM_ENABLE) = 0 → disables EMTTM, locks TT2 to fixed P-state (LFM)
- Verifies `THERMAL_THROTTLE_UNLOCK` fuse gates the SW disable path
- Confirms fabric frequencies are no longer limited by thermal PID when disabled
- ⚠️ Must run with adequate cooling — disabling EMTTM removes thermal protection

**22022421520 — Verify Uncore Throttling (PID)**
- Core test for IMH thermal management — validates PID control loop behavior
- Drive sustained high-bandwidth workload on memory/IO fabric → push temperatures toward TjMax
- **Verify PID behavior**: gradual frequency reduction (not abrupt N-Strike dithering that loses ~0.5 bin)
- **Verify squared error acceleration**: when temp exceeds TjMax by > 1°C, error term is squared for faster response
- **Verify PID recovery**: frequency ceiling gradually released as temperature drops
- **Verify reporting**: `IA32_PACKAGE_THERM_STATUS.THERMAL_MONITOR_STATUS` set during throttling, `TEMPERATURE[23:16]` reflects correct margin
- **Verify EWMA filtering**: if thermal monitor filtering enabled, status bit reflects sustained throttling only
- PID tuning: Kp=0.17, Ki=0.06 (client-derived defaults)

### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->

### NWP Delta
- NWP keeps IMH PID-based thermal throttling (EMTTM) for fabric frequency control
- NWP keeps cold-action adjustments for TDP/PMAX
- Thermal HW Assist was never enabled on DMR CBB — same for NWP
- Cross-die throttling remains not POR (same as DMR)
- Verify NWP-specific PID tuning parameters (Kp, Ki) if changed from DMR defaults
- DTS sensor placement may differ due to NWP die floorplan — verify DTS-to-domain mapping from NWP-specific collateral
- TPMI/PMT register migration for thermal registers applies equally to NWP
