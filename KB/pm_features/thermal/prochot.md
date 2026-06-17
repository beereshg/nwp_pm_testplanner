# Thermal > PROCHOT

> **Status**: Enriched from Primecode `src/flow/prochot/` + PCode `thermal_report.cpp` + soc_thermal sibling (May 2026)
> **Parent**: [Thermal](thermal_main.md)
> **Source Confidence**: High — Primecode prochot flow + PCode thermal_report verified.

## Architecture Summary

**PROCHOT** (Processor Hot) is a **platform-asserted** thermal throttling signal. Since SPR, PROCHOT is **input-only** — the CPU cannot assert it outbound. The platform (VR, PSU, board logic) asserts the `XX_PROCHOT_N` GPIO pin to signal a thermal emergency (e.g., VR over-temperature, PSU redundancy loss, peak power reduction).

### PROCHOT Response Architecture

```
  Platform                CBB HW              PCode (CBB)         Primecode (IMH)
  ┌──────────┐         ┌─────────┐       ┌─────────┐       ┌───────────┐
  │ VR / PSU  │         │ fast_   │       │ Fastpath│       │ HPM msg   │
  │ asserts   │         │ throttle│       │ handler │       │ to leaves │
  │ PROCHOT_N ├──~250ns►│ to cores├──IRQ►│ freq    ├─HPM►│ per-Cdyn  │
  │           │         │ (HW)    │       │ ceiling │       │ ceiling   │
  └──────────┘         └─────────┘       └─────────┘       └───────────┘
```

### Two-Phase Response

1. **Immediate HW response** (~250 ns): CBB HW asserts `fast_throttle` to all cores — no firmware involvement
2. **PCode firmware response**: Fastpath interrupt → apply `PROCHOT_RESPONSE_POWER` frequency ceiling → de-assert `fast_throttle`. Sends HPM `PROCHOT_POWER_LIMITED_FREQ_LIMIT` with per-Cdyn-level ceiling to all leaf dies

### BIOS Knobs

| Knob | TPMI Register | Description |
|------|--------------|-------------|
| **Prochot Response Power** | `MISC_CTRL_BLOCK` Feature 0x1, Reg 0x06, bits [14:0] | Power limit in 0.125W units (clipped to [PKG_MIN_POWER, TDP]) |
| **Prochot Response Lock** | Same register, bit [63] | Lock until next reset |

## Execution Flow

1. **Platform asserts** `XX_PROCHOT_N` GPIO (active low)
2. **CBB HW fast_throttle** (~250 ns): All cores throttled to minimum ratio immediately
3. **PCode fastpath IRQ**: Reads `IO_INTERDIE_THROTTLE_SIGNALS_STATUS.PROCHOT`
4. **Power-to-frequency conversion**: Uses fused 6-point P-F profile to compute frequency ceiling from `PROCHOT_RESPONSE_POWER`
5. **Primecode `handleAssertion()`**: Receives HPM, applies `setLimits()` per IP
6. **Sustained throttling**: Frequency clamped until platform de-asserts PROCHOT_N
7. **De-assertion**: `handleDeassertion()` → `clearLimits()`, normal P-state resumes

## Key Registers & Interfaces

| Register / MSR | Description |
|----------------|-------------|
| `XX_PROCHOT_N` GPIO | Platform PROCHOT assertion pin (input only) |
| `IO_INTERDIE_THROTTLE_SIGNALS_STATUS.PROCHOT` | PCode status bit |
| `PROCHOT_RESPONSE_POWER` (TPMI MISC_CTRL) | Power limit response value |
| `IA32_THERM_STATUS[0]` (MSR 0x19C) | PROCHOT status/log bits |
| `IA32_PACKAGE_THERM_STATUS[0]` (MSR 0x1B1) | Package-level PROCHOT status |

## Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR SoC Thermal Management](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | PROCHOT architecture |
| HAS | [Socket Thermal Management](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Socket thermal overview |
| Primecode src | `src/flow/prochot/prochot_common/v1_0/prochot.cpp` | `handleAssertion()`, `handleDeassertion()` |
| Primecode src | `src/flow/prochot/prochot_message/v1_0/prochot_message.cpp` | HPM message to leaf dies |
| PCode src | `source/pcode/flows/thermals/thermal_report.cpp` | `set_prochot_bit()` |

| HSD ID | Title | Segment | NWP Scope |
|--------|-------|---------|-----------|  
| 22022452945 | PM_THERM - IMH Thermal Management | PV | Runnable_On_N-1 |
| 22022452951 | PMSS_THERMAL - Thermal BIOS Knob "Prochot Response Lock" Validation | PV | Runnable_On_N-1 |
| 22022452952 | PMSS_THERMAL - Thermal BIOS Knob "Prochot Response Power" Validation | PV | Runnable_On_N-1 |
| 22022462115 | PM_THERM-PROCHOT_Event-L | PV | Runnable_On_N-1 |

## Related Sightings

No DMR PROCHOT-specific sightings identified in retrospective.

## NWP Delta

| Area | DMR (N-1) | NWP | Notes |
|------|----------|-----|-------|
| PROCHOT direction | Input-only (since SPR) | Same | |
| Fast throttle HW path | CBB asserts to all cores | Same expected | NIO single-die |
| D2D PROCHOT propagation | Via D2D perimeter signals | **N/A** | NIO monolithic — no inter-die propagation |
| PROCHOT_RESPONSE_POWER | TPMI MISC_CTRL | Same expected | Verify NIO TPMI opcode |
| Response lock | TPMI lock bit [63] | Same expected | |
