# Thermal > Thermal Reporting

> **Status**: Enriched from PCode `thermal_report.cpp` + `thermal_sampling.cpp` + Primecode `src/flow/thermals/reporting/` (May 2026)
> **Parent**: [Thermal](thermal_main.md)
> **Source Confidence**: High — PCode thermal source + Primecode reporting flow verified.

## Architecture Summary

**Thermal Reporting** aggregates temperature data from DTS (Digital Thermal Sensors) across the package and reports it via architectural MSRs and telemetry interfaces. The CBB PCode samples DTS sensors, computes per-CCP and package-wide thermal status, applies EWMA filtering, and sends `SOCKET_THERMAL` HPM messages to Primecode for package-level aggregation.

### Thermal Reporting Pipeline

```
  DTS Sensors              PCode (CBB)                  Primecode (IMH)
  ┌───────────┐       ┌────────────────────┐       ┌────────────────┐
  │ Core DTS  │       │ thermal_sampling   │       │ reporting_pkg  │
  │ SOC DTS   ├──ADC►│ .cpp               │       │ reporting_core │
  │ IO DTS    │       │ min/max aggregate  ├─HPM►│                │
  └───────────┘       ├────────────────────┤       │ Package status │
                       │ thermal_report.cpp │       │ MSR update     │
                       │ EWMA filter        │       │                │
                       │ per-CCP status     │       │ IA32_PKG_      │
                       └────────────────────┘       │ THERM_STATUS   │
                                                    └────────────────┘
```

### EWMA Thermal Filter ("Therm-Monitor-Status-Filter")

The `THERMAL_MONITOR_STATUS` EWMA filter suppresses transient thermal throttle events using an exponential moving average (α=0.7, configurable decay/TAU). Without the filter, short TDP spikes appear as sustained thermal issues. Configured via `SOCKET_THERMAL` HPM `DECAY` field or `PM_MISC_CONTROL` mailbox sub-command `THERM_MONITOR_STATUS` (opcode 0xd0, sub 0x20).

## Execution Flow

1. **DTS sampling**: PCode `thermal_sampling.cpp` periodically reads DTS ADC values from cores, SOC, IO domains
2. **Aggregation**: Min/max across all CCPs computed
3. **Per-CCP status**: `update_ccp_therm_status_tx()` updates `IA32_THERM_STATUS` for each core
4. **EWMA filter**: Applies exponential moving average to suppress transient events
5. **HPM report**: `send_updated_report_to_imh()` sends `SOCKET_THERMAL` HPM with aggregated thermal data
6. **Package status**: Primecode `reporting_pkg` updates `IA32_PACKAGE_THERM_STATUS`, `MCP_THERMAL_REPORT_1/2`
7. **OS reads MSRs**: Thermal management software reads status MSRs for fan control and throttle decisions

## Key Registers & Interfaces

| MSR / Register | Address | Description |
|----------------|---------|-------------|
| `IA32_THERM_STATUS` | 0x19C | Per-core temp, PROCHOT/OOS/threshold status+log |
| `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | Package-aggregated max temp + status bits |
| `IA32_PACKAGE_THERM_MARGIN` | 0x1A1 | Margin to T-Control (S8.8) for fan regulation |
| `IA32_TEMPERATURE_TARGET` | 0x1A2 | REF_TEMP, TCC offset, T-Control offset |
| `MCP_THERMAL_REPORT_1` | 0x1A3 | MARGIN_TO_THROTTLE + MARGIN_TO_TCONTROL (S10.6) |
| `MCP_THERMAL_REPORT_2` | 0x1A5 | Absolute max temp in package (S10.6) |

## Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | Thermal reporting architecture |
| HAS | [Socket Thermal Management](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Socket thermal overview |
| HAS | [ITD HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/ITD/ITD_HAS.html) | Internal Temperature Distribution |
| PCode src | `source/pcode/flows/thermals/thermal_report.cpp` | Per-CCP status + EWMA |
| PCode src | `source/pcode/flows/thermals/thermal_sampling.cpp` | DTS readout + aggregation |
| Primecode src | `src/flow/thermals/reporting/reporting_pkg/` | Package thermal status |
| Primecode src | `src/flow/thermals/reporting/reporting_core/` | Core thermal status |

| HSD ID | Title | Segment | NWP Scope |
|--------|-------|---------|-----------|  
| 22022452948 | PM_THERM - CBB Thermal Management | PV | Runnable_On_N-1 |
| 22022452950 | PMSS_THERMAL - Thermal BIOS Knob "Therm-Monitor-Status-Filter" Validation | PV | Runnable_On_N-1 |
| 22022462213 | PM_THERM-Platform_Thermal_Solution_Validation-L | PV | Runnable_On_N-1 |

## Related Sightings

No DMR thermal reporting-specific sightings identified in retrospective.

## NWP Delta

| Area | DMR (N-1) | NWP | Notes |
|------|----------|-----|-------|
| DTS sensor count | Multi-die (CBB + leaf dies) | Single die (NIO) | Simpler aggregation |
| EWMA filter | Supported | Same expected | Verify NIO PCode EWMA path |
| SOCKET_THERMAL HPM | Cross-die HPM | **Local only** | NIO — no inter-die HPM for thermal |
| Thermal report MSRs | Same | Same expected | |
