# Memory Thermal — Main Flow

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [KB Index](../INDEX.md)

## Baseline (DMR)

### What is Memory Thermal?
Memory Thermal encompasses all DRAM thermal protection and reporting on the IMH (Integrated Memory Hub).
Uses **Closed Loop Thermal Throttling (CLTT)** with two temperature sources: MR4 register reads (JEDEC DDR5)
and PECI/TSOD external temperature injection. Protection escalates: CLTT throttle → DDRIO throttle →
MEMHOT → MEMTRIP → platform CATTRIP (full power-off).

### Topology
```
  DRAM (DDR5/MCR)       MC Hardware (IMH)          Primecode (IMH)
  MR4 temp register --MRR--> CLTT engine         CLTT flow: config/init
  TSOD (ext)               threshold compare    HPM routing (multi-die)
                           throttle actions     MEMHOT I/O control
  Platform                 MEMHOT assert        MEMTRIP -> CATTRIP
  MEMHOT_IN --GPIO-->      MEMTRIP assert       PECI temp inject
  MEMHOT_OUT <--GPIO--
```

### Operating Principle
Temperature escalation: BW throttle (CLTT) → MEMHOT_OUT (platform alert) → MEMTRIP → THERMTRIP (PSU off).
DDRIO compensation (RCOMP ~127 ms) runs independently for PHY signal integrity.

### Boot-Time Init
BIOS programs all CLTT thresholds, throttle levels, MEMHOT/MEMTRIP routing, and CLTT mode selection
(MR4 / TSOD / PECI) via B2P mailbox. Primecode arms trip propagation at reset step 61.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| MC CLTT engine | IMH | Hardware thermal comparator for all thresholds (Lo/Mid/Hi/MemHot/MemTrip); drives BW throttle, 2× refresh, MEMHOT_OUT, MEMTRIP signals | `dimm_temp_snapshot` vs threshold regs | DMR DDR5/MCR HAS |
| DDRIO PHY | IMH | 3 remote DTS diodes per MC; RCOMP FSM (~127 ms); DTS temp distribution to analog consumers | RCOMP completion to MC; DTS codes to COMP FSM | DMR DDR5/MCR HAS |
| Punit OR-tree | CBB PUnit | `THERMTRIP_CONFIG_CFG` routes memtrip/thermtrip signals; arms via `scu_trip_enable` at reset step 61 | THERMTRIP# / MEMTRIP# platform pins | SoC PM HAS |
| TPMI OPC block | IMH | Exposes `OPC_DIMM_TEMPS` for OOB/BMC access; bridges BMC→Primecode temp injection | TPMI write/read; `OPC_HEADER.MEMORY_CHANNELS` | DMR DDR5/MCR HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Primecode CLTT | `src/flow/cltt/` | 1 ms periodic: reads MC MR4/TSOD telemetry, converts to °C, writes MC registers, publishes TPMI, sends HPM | `collectTempPeriodicallyMr4Mode()`, `writeMcTemperatureRegisters()`, `sendDimmTempOnHpm()` | Primecode CLTT flow |
| Primecode TPMI | `src/flow/tpmi/` | Receives BMC PECI CLTT temps; routes to CLTT::storeTpmiClttTemps(); SECURITY GATE: rejects if CLTT_PECI_ENABLE=0 | `OpcTpmi::handleDimmTemps()` | Primecode TPMI handler |
| Primecode reset | `src/flow/reset/` | Arms trip propagation at reset step 61 (`HWRS_RESET_COMPLETE`) via `scu_trip_enable` | Reset step 61 | Primecode reset sequence |
| PCode | CBB PUnit | DDRIO PM messages (RCOMP/DVFS/SAGV), MEMHOT→PROCHOT routing, RAPL integration, THERMTRIP OR-tree routing | `MemorySubSystem`, `IO_FIRM_CONFIG`, `THERMTRIP_CONFIG_CFG` | PCode thermal flows |
| BIOS | Platform init | CLTT mode selection, all threshold programming, MEMHOT/MEMTRIP routing, TSOD disable for PECI mode | `B2P WRITE_PCU_MISC_CONFIG`, all MC threshold regs | NWP BIOS HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| B2P mailbox `PCU_MISC_CONFIG` | `MR4_CLTT_ENABLE`, `CLTT_PECI_ENABLE` bits | RW (BIOS) | CLTT mode selection | DMR DDR5/MCR HAS |
| TPMI `OPC_DIMM_TEMPS_[0..3]` | TPMI OPC offset | RW (BMC) / RO (readback) | Per-DIMM temperatures for PECI CLTT mode | DMR DDR5/MCR HAS |
| MC `dimm_temp_thresh` | MCHBAR GPSB | RW (BIOS) | Low/mid/high/memtrip thresholds per DIMM | DMR DDR5/MCR HAS |
| `THERMTRIP_CONFIG_CFG` | Punit GPSB offset 0x4E0 | RW (BIOS) | memtrip→thermtrip routing enables (default all=1) | SoC PM HAS |
| `IA_PERF_LIMIT_REASONS` MSR | 0x1B1 | RO (OS) | Reflects MEMHOT→PROCHOT throttle | IA32 Arch SDM |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| MR4 polling period | ~128 ms (MC HW) | DMR DDR5/MCR HAS |
| Primecode CLTT timer | 1 ms | Primecode CLTT flow |
| RCOMP period | ~127 ms / 40–45 µs max duration | DMR DDR5/MCR HAS |
| Memtrip→Thermtrip default | Enabled (must be explicitly disabled by BIOS) | THERMTRIP_CONFIG_CFG |
| Trip propagation arm | Reset step 61 (`HWRS_RESET_COMPLETE`) | Primecode reset |
| Subflows | 5: DDRIO, MR4, Memhot, Memtrip, PECI | memory_thermal_main.md |

## NWP Delta

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| Feature supported | ✅ Carried from DMR; NIO as sole IMH host | NWP PM MAS |
| IMH topology | Single NIO (NWP IMH) replaces DMR dual-die IMH | NWP PM MAS |
| HPM multi-die distribution | Not applicable (single-die NWP) | NWP PM MAS |
| CLTT modes (MR4/TSOD/PECI) | All three modes carried | NWP PM MAS |
| MEMHOT / MEMTRIP / THERMTRIP | Same OR-tree; THERMTRIP_CONFIG_CFG bits identical | SoC PM HAS |
| Memory channels | NWP SP: 8; NWP AP: up to 16 (`OPC_HEADER.MEMORY_CHANNELS`) | OPC_HEADER |

## Legacy (Human-Curated Reference)

*All original content preserved below for reference.*

### NWP Spec Context
| Field | Value |
|-------|-------|
| HAS ref | NWP HAS: MR4-based CLTT, Memhot, Memtrip |
| MAS ref | NWP PM MAS: Memory thermal supported |
| NWP delta | Memory thermal carried from DMR — NIO as sole IMH host |
| NWP supported | True |

### Architecture Summary

**Memory Thermal** encompasses all DRAM thermal protection and reporting mechanisms on the IMH (Integrated Memory Hub). The system uses **Closed Loop Thermal Throttling (CLTT)** with two temperature sources: MR4 register reads from DRAM devices and PECI/TSOD external temperature injection. Protection escalates through three severity levels: throttling, MEMHOT, and MEMTRIP.

```
  DRAM (DDR5/MCR)          MC Hardware (IMH)         Primecode (IMH)
  ┌─────────────┐         ┌──────────────────┐       ┌──────────────────┐
  │ MR4 temp    │         │ CLTT engine      │       │ CLTT flow        │
  │ register    ├──MRR──►│ threshold compare │       │ config/init      │
  │             │         │                  │       │                  │
  │ TSOD (ext)  │         │ Throttle action  │       │ HPM routing      │
  └─────────────┘         │ ├─ BW throttle   │       │                  │
                          │ ├─ Refresh rate ↑│       │ Memhot I/O       │
  Platform                │ ├─ MEMHOT assert │       │ Memtrip → CATTRIP│
  ┌─────────────┐         │ └─ MEMTRIP assert│       │                  │
  │ MEMHOT_IN   ├───GPIO─►│                  │       │ PECI temp inject │
  │ MEMHOT_OUT  │◄──GPIO──┤                  │       │                  │
  └─────────────┘         └──────────────────┘       └──────────────────┘
```

#### Thermal Protection Hierarchy (Memory)

| Level | Mechanism | Trigger | Response |
|-------|-----------|---------|----------|
| 1 | **CLTT throttle** | MR4 temp > warm threshold | Memory bandwidth throttle |
| 2 | **DDRIO throttle** | DDRIO DTS > threshold | DDRIO frequency/timing adjustment |
| 3 | **MEMHOT** | MR4 temp > hot threshold | Assert MEMHOT_OUT GPIO + optional PROCHOT routing |
| 4 | **MEMTRIP** | MR4 temp > critical threshold | Assert MEMTRIP → CATTRIP → platform shutdown |
| 5 | **PECI override** | BMC injects temp via PECI | Same throttle/memhot/memtrip actions |

### FW Agents

- **Primecode (IMH Punit)**: CLTT configuration, MR4 polling, MEMHOT I/O control, MEMTRIP → CATTRIP routing, PECI temperature injection
- **MC Hardware**: CLTT engine with hardware comparators for throttle/memhot/memtrip thresholds
- **BIOS**: Memory thermal knobs (CLTT enable, threshold configuration, MEMHOT mode, MEMTRIP enable)
- **BMC (via PECI)**: External temperature injection for closed-loop thermal management

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR DDR5/MCR - MR4 CLTT](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html#mr4-based-cltt) | MR4-based CLTT architecture |
| HAS | [DMR SoC Thermal Management](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | Thermal overview including memory |
| HAS | [Socket Thermal Management](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Socket-level thermal |
| HAS | [ITD HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/ITD/ITD_HAS.html) | Internal Temperature Distribution |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS |
| HAS | [NWP BIOS HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/BIOS/NWP.html) | Memory thermal BIOS knobs |
| Primecode src | `src/flow/cltt/` | CLTT main flow |
| Primecode src | `src/flow/thermals/` | Thermal management |

### Related Sightings

No DMR memory thermal-specific sightings identified in retrospective.

### Subflows (5)

| # | Subflow | Status | TCs | Segment | Notes |
|---|---------|--------|-----|---------|-------|
| 1 | [DDRIO](ddrio.md) | Enriched | 1 | FV | DDRIO DTS thermal throttle |
| 2 | [MR4](mr4.md) | Enriched | 4 | FV | MR4 register-based CLTT |
| 3 | [Memhot](memhot.md) | Enriched | 5 | FV | MEMHOT_IN/OUT GPIO interface |
| 4 | [Memtrip](memtrip.md) | Enriched | 4 | FV | Emergency MEMTRIP → CATTRIP |
| 5 | [PECI](peci.md) | Enriched | 4 | FV | PECI temperature injection |
| | **Total** | 5/5 enriched | **18** | | |

