# Thermal > THERMTRIP/CATTRIP

> **Status**: Enriched from Primecode `thermal_vars.hpp` + PCode thermals source + soc_thermal sibling (May 2026)
> **Parent**: [Thermal](thermal_main.md)
> **Source Confidence**: High — Primecode thermal_vars + PCode thermal shutdown path verified.

## Architecture Summary

**THERMTRIP** is an asynchronous HW-driven emergency shutdown triggered when junction temperature exceeds the absolute maximum (~125°C ±10°C, per BJT calibration). There is **no configurable offset** — the threshold is fused per-diode at manufacturing. THERMTRIP operates at the transistor level (no flops), with ~30-100 ns latency.

**CATTRIP** (Catastrophic Trip) is functionally the same mechanism applied to the DRAM/memory domain. SOC DTS daisy chains cover memory, D2D, MIO, accelerator, fabric, and CGU domains.

### THERMTRIP Shutdown Sequence

```
  DTS > Threshold       CBB HW (async, no flops)
  ┌───────────┐     ┌─────────────────────────────────┐
  │ Tj > Tjmax ├─►│ PLL gate → PLL shutdown →        │
  │ (fused)   │     │ FIVR disable (all 42) →       │
  └───────────┘     │ BGR disable → inter-die D2D →  │
                    │ xxTHERMTRIP_N GPIO assertion  │
                    └──────────────────────┬──────────┘
                                           │
                    ┌──────────────────────┴──────────┘
                    │ Platform must shut down other  │
                    │ sockets within 500ms (OKS PDG) │
                    └─────────────────────────────────┘
```

### DMR Key Detail

`xxTHERMTRIP_N` is **output only** at package level (`rxen_b=1`) — sighting HSD 22021682591. Inter-die `yy_thermtrip_n` remains bidirectional for die-to-die propagation.

### Early Throttle Before Trip

Primecode provides firmware-level early throttle before the HW trip point. `getEffThermTripWithEarlyThrottle()` adds a margin and forces emergency frequency reduction when `die_max_temp >= eff_therm_trip_w_early_throttle`.

## Execution Flow

1. **DTS measures temperature**: Continuous analog comparison against fused threshold
2. **Threshold exceeded**: Asynchronous HW comparator triggers (no clock dependency)
3. **PLL gated**: Clock distribution stopped (~30 ns)
4. **PLL shutdown**: PLLs powered down
5. **FIVR disable**: All 42 FIVR rails disabled (DMR CBB)
6. **BGR disable**: Bandgap reference shut down
7. **Inter-die propagation**: D2D `yy_thermtrip_n` asserted to other dies
8. **Package GPIO**: `xxTHERMTRIP_N` asserted to platform
9. **Platform response**: BMC/platform controller shuts down other sockets within 500 ms

## Key Registers & Interfaces

| Register / Signal | Description |
|-------------------|-------------|
| `xxTHERMTRIP_N` GPIO | Package-level thermtrip output (output only on DMR) |
| `yy_thermtrip_n` | Inter-die thermtrip (bidirectional) |
| Primecode `eff_therm_trip` | Effective thermtrip point from thermal_vars |
| Primecode trip points | TP0-TP3 (4 configurable trip points) |

## Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR SoC Thermal Management](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | THERMTRIP architecture |
| HAS | [Socket Thermal Management](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Socket-level thermtrip |
| Primecode src | `src/flow/thermals/thermals_common/v2_0/thermal_vars.hpp` | Trip point definitions |
| Primecode src | `src/flow/thermals/management/Core/v1_0/core_thermal_management.cpp` | Early throttle logic |

| HSD ID | Title | Segment | NWP Scope |
|--------|-------|---------|-----------|  
| 22022462300 | PM_THERM-THERMTRIP_Event-L | PV | Runnable_On_N-1 |

## Related Sightings

| HSD | Title | Relevance |
|-----|-------|----------|
| 22021682591 | xxTHERMTRIP_N rx disabled | DMR package GPIO output-only |

## NWP Delta

| Area | DMR (N-1) | NWP | Notes |
|------|----------|-----|-------|
| FIVR count | 42 FIVRs per CBB | NIO TBD | Different FIVR topology |
| Inter-die propagation | D2D `yy_thermtrip_n` | **N/A** | NIO monolithic — no inter-die |
| xxTHERMTRIP_N direction | Output only | Same expected | |
| Early throttle firmware | Primecode thermal_vars | Same expected | |
