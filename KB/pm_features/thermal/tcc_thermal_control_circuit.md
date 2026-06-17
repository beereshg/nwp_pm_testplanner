# Thermal > TCC (Thermal Control Circuit)

> **Status**: Enriched from Primecode `thermal_vars.cpp` + PCode `thermal_report.cpp` + MSR architecture (May 2026)
> **Parent**: [Thermal](thermal_main.md)
> **Source Confidence**: High — Primecode TCC offset handling + PCode thermal_report TCC readout verified.

## Architecture Summary

**TCC (Thermal Control Circuit)** implements frequency throttling when junction temperature reaches the TCC activation point. The activation temperature is computed as:

$$T_{TCC} = T_{j,max,SST} - (C1E_{offset} + TCC_{offset})$$

where `T_j,max,SST` is the fused base TjMax (~105°C typical for server), `C1E_offset` is the C1E energy-optimization offset, and `TCC_offset` is the BIOS-configurable offset (0–63°C).

### TCC Activation/Deactivation Flow

```
  Temperature rises                        Temperature falls
  ┌────────────────┐                    ┌────────────────┐
  │ Tj >= Tcc     │                    │ Tj < Tcc      │
  │ EMTTM throttle│                    │ Throttle      │
  │ begins        │                    │ released      │
  │               │                    │               │
  │ P-state →     │                    │ P-state →     │
  │ reduced ratio │                    │ normal ratio  │
  └────────────────┘                    └────────────────┘
```

### Key Controls

| Control | Location | Description |
|---------|----------|-------------|
| **TCC master enable** | `IA32_MISC_ENABLE[3]` | `AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE` — when 0, NO throttling even above TCC |
| **TCC offset** | `IA32_TEMPERATURE_TARGET[29:24]` | 0–63°C offset lowering TCC activation point |
| **RATL enable** | `IA32_TEMPERATURE_TARGET[7]` | `TCC_OFFSET_CLAMPING_BIT` — enables throttling below P1 |
| **RATL window** | `IA32_TEMPERATURE_TARGET[6:0]` | `TCC_OFFSET_TIME_WINDOW` — time-averaged throttle window |

### Test Scenarios

- **TCC Activation and Deactivation** (22022462216): Apply thermal stress to exceed TCC activation, verify EMTTM throttling engages, remove stress, verify throttle releases
- **TCC Offset Validation** (22022462218): Program various TCC offset values via BIOS knob, verify effective TCC activation point shifts accordingly

## Execution Flow

1. **BIOS configures**: TCC offset via `IA32_TEMPERATURE_TARGET[29:24]`, TCC enable via `IA32_MISC_ENABLE[3]`
2. **Runtime**: PCode `thermal_report.cpp` reads `IO_TEMPERATURE_TARGET().get_TJ_MAX_TCC_OFFSET()` for effective offset
3. **Primecode**: `sampleTempTargetTccOfs()` reads offset, `updateEffectiveTripPoint()` computes effective TCC
4. **Temperature check**: DTS temp compared to effective TCC point
5. **Activation**: If Tj >= TCC → EMTTM thermal throttling engages (core ratio reduced)
6. **Deactivation**: If Tj < TCC → throttle released, normal P-state resumes
7. **Telemetry**: `EFF_TCC_OFFSET` reported in PCode telemetry

## Key Registers & Interfaces

| MSR / Register | Address | Field | Description |
|----------------|---------|-------|-------------|
| `IA32_MISC_ENABLE` | 0x1A0 | [3] | TCC master enable/disable |
| `IA32_TEMPERATURE_TARGET` | 0x1A2 | [29:24] | TCC offset (0–63°C) |
| `IA32_TEMPERATURE_TARGET` | 0x1A2 | [7] | RATL clamping enable |
| `IA32_TEMPERATURE_TARGET` | 0x1A2 | [6:0] | RATL time window |
| `IA32_THERM_STATUS` | 0x19C | [0] | Thermal monitor status |

## Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR SoC Thermal Management](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | TCC/EMTTM architecture |
| HAS | [ACP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html) | ACP thermal controls (Acode) |
| Primecode src | `src/flow/thermals/thermals_common/v2_0/thermal_vars.cpp` | `sampleTempTargetTccOfs()`, `updateEffectiveTripPoint()` |
| PCode src | `source/pcode/flows/thermals/thermal_report.cpp` | TCC offset readout for telemetry |

| HSD ID | Title | Segment | NWP Scope |
|--------|-------|---------|-----------|  
| 22022462216 | PM_THERM-TCC_Activation_and_Deactivation-L | PV | Runnable_On_N-1 |
| 22022462218 | PM_THERM-TCC_Offset_Validation-L | PV | Runnable_On_N-1 |

## Related Sightings

No DMR TCC-specific sightings identified in retrospective.

## NWP Delta

| Area | DMR (N-1) | NWP | Notes |
|------|----------|-----|-------|
| TCC activation temp | ~105°C (fused) | NIO TBD | Different TjMax fusing expected |
| TCC offset range | 0–63°C | Same expected | |
| RATL support | Supported | Same expected | |
| EMTTM throttle mechanism | Same | Same expected | |
