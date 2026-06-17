# SoC Thermal > EMTTM

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: EMTTM (Enhanced Multi-Threaded Thermal Management) is the umbrella thermal throttling algorithm spanning all DMR dies via three nested PID feedback loops, each targeting the same `eff_tj_max` setpoint at different response rates.

**Topology**:
```
Core DTS ──SHORT_TELEM ~102.4 μS──> Acode PID (Core EMTTM ~300 μS/DCM)
                                      ├── self-throttle: IA freq ceiling
                                      └── cross-core-throttle REQ ─> PCode
CBB SOC/CCF DTS ──SA Thermal Puller──> PCode PID (CBB EMTTM ~1 mS)
                                        ├── CCF/Ring freq ceiling
                                        └── HPM SOCKET_THERMAL ──────> PrimeCode
IMH DTS ──────────────────────────────> PrimeCode PID (IMH EMTTM ~1 mS)
                                         └── Mem Fabric + IO Fabric freq ceilings
```

**Key operational principle**: Three independent PID loops at decreasing response speed. Each uses `eff_tj_max` (fused TjMax minus SST-PP + C1E + TCC offsets) as the temperature setpoint. Squared-error acceleration in CBB PCode when error ≤ −1°C. Cross-throttle cascades upward when a non-throttlable domain is still hot after a throttlable domain is saturated at min ratio.

**Boot activation**: THA/DTD (Do-Not-Exceed) active at PH1.2. Core EMTTM from PH3+ (CCP telemetry active). CBB and IMH EMTTM from PH2.52 (PCode kernel enabled).

EMTTM (Enhanced Multi-Threaded Thermal Management) is the umbrella term for the PID-based thermal throttling algorithm across all dies. On DMR, there are **three EMTTM layers**:

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core DTS Gen2.6 / PMA | CBB Top Die (per core) | Temperature sensor input to Acode EMTTM PID; drives DTD sticky/non-sticky interrupts | SHORT_TELEM ~102.4 μS push; DTD sticky → Hammer to LFM; DTD non-sticky (±3°C) → ITD recalc | [ACP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html) |
| SOC / CCF DTS | CBB Base Die | SA Thermal Puller inputs for CBB PCode CCF/Ring PID | PMSB IOs → `PCU_CR_DTS_TEMP_CCF[N:0]`, `PCU_CR_DTS_TEMP_SOC` | [CBB Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) |
| GPSS | CBB / IMH | Global P-State Switch — applies PID frequency ceiling to domain clock | Ratio ceiling register | — |
| FIVR (VccR / VccCore) | CBB | Voltage rails for CCF/Ring and cores; bounds achievable frequency | Voltage supply | — |
| IMH DTS | IMH die | Temperature inputs to PrimeCode Mem/IO Fabric PID loops | PMSB-style DTS reads | [Socket Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core PMA, CBB Top Die | Runs Core EMTTM PID ~300 μS/DCM; handles DTD sticky (→ Hammer to LFM) and non-sticky (→ ITD recalc); requests cross-throttle via PMSB when at LFM and still hot | `CROSS_CORE_THROTTLE_REQ` PMSB_PCU_CR_VIRTUAL_SIG[13]; `IO_ACODE_ALGO_VALUES1[MAX_ALLOWED_RATIO]` | [ACP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html) |
| PCode (CBB) | CBB Base Die | Runs CBB EMTTM PID ~1 mS; self-throttle (CCF/Ring) + cross-throttle (Core→Ring, Core→Core); sends HPM SOCKET_THERMAL to Root; updates per-core THERM_STATUS | `eff_tj_max` calc; squared error accel when error ≤ −1°C; `THERM_STATUS_UPDATE` PMA_CR | [CBB Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) |
| PrimeCode (IMH) | IMH die | Runs IMH EMTTM PID ~1 mS for Mem Fabric + IO Fabric (independent loops, Kp=0.17 Ki=0.06); receives HPM SOCKET_THERMAL; updates `IA32_PACKAGE_THERM_STATUS` and TPMI | HPM `SOCKET_THERMAL` receive; updates `MCP_THERMAL_REPORT_1/2`; `DNS_EVENT_DELIVERY[THERMAL_INTERRUPT]` | [Socket Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) |
| BIOS / UEFI | Platform | Programs TCC offset (`IA32_TEMPERATURE_TARGET`); sets EMTTM master enable (`IA32_MISC_ENABLE[3]`); optionally disables EMTTM (DMR Edge only) | Boot-time MSR programming | HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | RO/RWC | [0/1] THERMAL_MONITOR_STATUS/LOG; [23:16] TEMPERATURE (relative to pkg TjMax) | Intel SDM |
| MSR `IA32_MISC_ENABLE` | 0x1A0 | RW (vMSR) | [3] AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE — master TCC/EMTTM enable; 0 = disable throttling | Intel SDM |
| MSR `IA32_TEMPERATURE_TARGET` | 0x1A2 | RW | [29:24] TJ_MAX_TCC_OFFSET (0–63°C); [23:16] REF_TEMP (≈ eff_tj_max); [7] TCC_OFFSET_CLAMPING_BIT (RATL) | Intel SDM |
| PLR | Bit 3 (`THERMAL`) | Mailbox | In-die thermal throttle active | CBB PM HAS |
| TPMI PMT | `CBB_TEMP_TARGET` (0x2E880) | RO | [23:16] EFF_TJ_MAX, [31:24] EFF_TCC_OFFSET | [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/TPMI/DMR_TPMI.html) |
| PECI | `READ_MODULE_TEMP` (cmd 9) | RO | Package thermal margin from PrimeCode | Intel PECI spec |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Core EMTTM PID period | ~300 | μS | Per-DCM; Acode runs independently on each CCP | Legacy Architecture Summary |
| CBB EMTTM PID period | ~1 | mS | PCode slow loop; CCF/Ring domain | Legacy Architecture Summary |
| IMH EMTTM PID period | ~1 | mS | PrimeCode slow loop; Mem Fabric + IO Fabric independent PIDs | Legacy Architecture Summary |
| THA/DTD fast-path (Hammer to LFM) | ~nS | — | DTS sticky DTD threshold → Acode drops to LFM; no PID loop involved | Legacy Architecture Summary |
| RATL / EWMA averaging window | ~seconds | — | Package-level time-averaged thermal window for sustained limits | Legacy Architecture Summary |
| Squared-error acceleration threshold | −1 | °C | CBB PCode: when error ≤ −1°C, error ← −error² (faster response) | Legacy Execution Flow |
| Temperature decay rate — Core (PkgC) | 40 | °C/mS | Core telemetry frozen in PkgC; PCode decays toward ambient | Legacy Execution Flow |
| Temperature decay rate — non-Core (PkgC) | 5 | °C/mS | SOC/CCF/IMH DTS decay rate during PkgC sleep | Legacy Execution Flow |
| PID vs N-Strike performance advantage | ~0.5 | bin | Pre-Si modeling; N-Strike dithering caused ~5% perf loss vs PID stable point | Legacy Architecture Summary |
| SHORT_TELEM push rate | ~102.4 | μS | Per-DCM; Domain0 (Core) + Domain1 (MLCSSA) min/max temps | Legacy Execution Flow |

## NWP Delta

**EMTTM PID algorithm is fully supported on NWP** — reused from DMR.

- All three EMTTM layers supported: Core EMTTM (ACP), CBB EMTTM (PCode), IMH EMTTM (PrimeCode on NIO)
- PID controller logic unchanged across all layers
- NIO runs IMH EMTTM (single die vs dual IMH) — only one NIO EMTTM instance
- Memory stack is LPDDR6 (vs DDR5) — may affect IMH thermal fabric limits
- PID replaced N-Strike on IMH — same rationale applies to NIO

### Validation Impact
- Core + CBB EMTTM: identical tests, fewer CBBs
- IMH/NIO EMTTM: single instance, but LPDDR6 thermal behavior may differ

## Legacy (Human-Curated Reference)

### Architecture Summary

EMTTM (Enhanced Multi-Threaded Thermal Management) is the umbrella term for the PID-based thermal throttling algorithm across all dies. On DMR, there are **three EMTTM layers**:

| Layer | FW Agent | Die | Algorithm | Domains | Response Rate |
|-------|----------|-----|-----------|---------|---------------|
| Core EMTTM | Acode (ACP) | CBB | PID + THA/DTD | Per-DCM core | ~300µS (fast path ~nS) |
| CBB EMTTM | PCode | CBB | PID | CCF/Ring, cross-throttle | ~1mS slow loop |
| IMH EMTTM | PrimeCode | IMH | PID | Memory Fabric, IO Fabric | ~1mS slow loop |

See [CBB Thermal Management](cbb_thermal_management.md) for CBB/Core EMTTM details and [IMH Thermal Management](imh_thermal_management.md) for IMH EMTTM details.

#### Why PID Replaced N-Strike on IMH
- DMR sustained workloads on memory/IO fabric run closer to TjMax than prior generations
- N-Strike algorithm throttles to Pn and holds for 16 slow-loop cycles → **dithering** on sustained workloads → up to **5% perf impact**
- PID controller provides **stable frequency at the thermal limit** → ~0.5 bin better than N-Strike
- Pre-Si modeling confirmed PID (green) vs N-Strike (blue) stability advantage

#### Thermal Response Hierarchy (All Dies)
```
Temp 0°C ──────────────────────────────────────────────── 130°C
         │                                                 │
         │  ITD (slow loop)  ──────────────────────────    │
         │                                                 │
         │  Core EMTTM (ACP, ~300µS)  ────────────────    │
         │                                                 │
         │  CBB EMTTM (PCode PID, ~1mS)  ─────────────   │
         │                                                 │
         │  IMH Fabric EMTTM (Primecode PID, ~1mS)  ──   │
         │                                                 │
         │  VR Hot (~97% TEMP_MAX)  → P1 all ─────────    │
         │  Prochot (platform GPIO) → response power ─    │
         │  OOS (TjMax+10 or sustained max throttle) ─    │
         │  Thermtrip (catastrophic shutdown)  ────────    │
```

### Execution Flow

#### PSS Test Focus: IMH Thermal Throttling

The PSS test cases focus on the **IMH die EMTTM behavior** visible through OS-accessible registers:

1. **Trigger thermal excursion**: Run sustained high-bandwidth memory/IO workload → push IMH temps toward TjMax
2. **Verify throttling**: IMH PrimeCode PID reduces fabric frequency → `IA32_PACKAGE_THERM_STATUS.THERMAL_MONITOR_STATUS` = 1
3. **Verify PLR**: PLR mailbox `THERMAL` bit (bit 3) set during throttle
4. **Verify recovery**: Reduce workload → PID releases ceiling → PLR clears

#### EMTTM Disable Path
- Fuse `THERMAL_THROTTLE_UNLOCK` must be set to allow SW disable
- `PCODE_SYSTEM_MODES_CONTROL[6]` = 1 → disables EMTTM (package DFX hook)
- `FIRM_CONFIG[4]` = 0 → disables EMTTM (BIOS-controlled)
- SW disable only allowed for DMR Edge (Carmel Beach), not SP/AP
- ⚠️ Disabling EMTTM may result in overheat critical condition

### Key Registers & Interfaces

| Register / Interface | Scope | Key Fields | Purpose |
|---|---|---|---|
| `IA32_PACKAGE_THERM_STATUS` (MSR 0x1B1) | Package | `THERMAL_MONITOR_STATUS[0]`, `THERMAL_MONITOR_LOG[1]`, `TEMPERATURE[23:16]` | Thermal throttle status |
| `IA32_MISC_ENABLE` (Thread MSR 0x1A0) | Thread | `THERMAL_MONITOR_ENABLE` | Enable/disable TCC |
| `PCODE_SYSTEM_MODES_CONTROL[6]` | Package | `EMTTM_DISABLE` | DFX disable hook |
| `FIRM_CONFIG[4]` | Package | `EMTTM_ENABLE` | BIOS enable/disable |
| PLR bit 3 (`THERMAL`) | Core | — | In-die thermal throttle active |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR SoC Thermal HAS — Thermal Management](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#thermal-management) | All EMTTM layers |
| HAS | [CBB Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) | CBB PCode EMTTM |
| HAS | [ACP PM HAS — Autonomous Thermal Management](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html#acp-2.0-autonomous-thermal-management) | Core EMTTM (Acode) |
| Primecode src | TODO | |
| Test scripts | TODO | |

#### Test Case Details

**22022015520 — [PSS] IMH Thermal Throttling**
- Drive sustained high-bandwidth workload on memory/IO fabric → push IMH die temp toward TjMax
- Verify PID throttle engages: fabric frequency ceiling reduces gradually (not abrupt N-Strike)
- Verify `IA32_PACKAGE_THERM_STATUS.THERMAL_MONITOR_STATUS` = 1 during throttle
- Verify PID recovery when workload reduces
- Check EWMA filtering behavior if enabled

**22022023843 — [PSS] PLR Status Registers Check for Thermal Events**
- During thermal throttle, read PLR mailbox (`PLR_MAILBOX_INTERFACE` + `PLR_MAILBOX_DATA`)
- Verify `THERMAL` bit (bit 3) is set — in-die thermal throttle active
- Verify `PLATFORM` bit (bit 4) is NOT set (that's for PROCHOT/VR Hot, not EMTTM)
- De-assert thermal condition → verify `THERMAL` bit clears
- Cross-reference with `IA32_PACKAGE_THERM_STATUS` for consistency

### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->

### NWP Delta
- NWP keeps all three EMTTM layers (Core Acode, CBB PCode, IMH PrimeCode PID)
- NWP keeps PID-based algorithm for IMH (replaces N-Strike)
- Verify NWP PID tuning parameters if changed from DMR defaults (Kp=0.17, Ki=0.06)
- Thermal HW Assist never enabled on DMR CBB — same for NWP
