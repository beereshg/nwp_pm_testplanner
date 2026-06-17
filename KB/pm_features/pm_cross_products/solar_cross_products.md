# PM Cross Products > Solar Cross Products

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [PM Cross Products](pm_cross_products_main.md)

## Baseline (DMR)

### What is Solar?
**Solar** is an OS-level (SVOS user-space) workload injection tool for PM cross-product validation.
It generates controlled PM stimuli (C-state entry via MWAIT, P-state changes via WRMSR, DVFS transitions)
across cores with configurable patterns. Uses a **two-phase exercise/verify approach**: exercise phase
applies PM patterns; verify phase validates residency counters, state machine consistency, no MCAs/hangs.

### Topology
- Solar runs as a user-space process on SVOS; spawns per-core threads
- Threads issue `MWAIT` (C-state entry) and `WRMSR` (P-state / IA32_PERF_CTL) instructions
- Platform XML profiles: `SOLAR_DMR_XMLS/Exercise/` and `SOLAR_DMR_XMLS/Verify/`
- Special SAGV access via `SAGV_CONFIG_HANDLER` PCode mailbox (debug-unlocked for Solar)

### Operating Principle
Exercise: Solar spawns per-core threads issuing MWAIT/WRMSR per XML profile, exercising multiple PM
domains simultaneously. Verify: reads residency counters (MSR 0x3FD C6, 0x10 TSC) and validates
invariants. Pass = no hang, no MCA, residency within expected range.

### Boot-Time Init
No firmware init required — Solar is a test-time tool. Platform must be booted to SVOS.
NWP requires new Solar XML profiles (`SOLAR_NWP_XMLS/`).

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core + MWAIT SM | CBB Compute | Receives MWAIT hints from Solar threads; drives core C-state entry; C-state resolution per module/package | MWAIT instruction, C-state residency counters | DMR CBB PM HAS |
| CBB Punit (PCode) | CBB | C-state coordination, P-state arbitration, DVFS during Solar stress | `PKG_C6_RESIDENCY`, SVID, turbo arbitration | DMR CBB PM HAS |
| SAGV mailbox | CBB Punit | Debug-accessible `SAGV_CONFIG_HANDLER` for SA frequency injection during cross-product stress | PCode mailbox | PCode mboxgen_bios.xml |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (core µcode) | Core | Executes MWAIT; drives core C-state SM; PICLET budget negotiation; cross-core C-state resolution | MWAIT handling, CC1/CC6 entry/exit | Acode microcode |
| PCode | CBB Punit | Package C-state coordination; P-state arbitration; RAPL PID during concurrent Solar stress | Module/package C-state resolution, RAPL | PCode flows |
| Primecode | IMH Punit | HPM message routing during C-state × P-state stress; DRAM RAPL during Solar memory exercises | HPM C-state messages | Primecode flows |
| BIOS | Platform init | PkgC enable/disable, SAGV_CONFIG_HANDLER access unlock, power limit init | Feature enable knobs | NWP BIOS HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| `MWAIT` instruction | x86 instruction | WO (user-space) | C-state entry hint per core; Solar exercise phase | IA32 Arch SDM |
| `IA32_PERF_CTL` | MSR 0x199 | RW | Legacy P-state request; Solar P-state exercise | IA32 Arch SDM |
| `MSR_CORE_C6_RESIDENCY` | MSR 0x3FD | RO | Core C6 counter; Solar verify phase | DMR CBB PM HAS |
| `MSR_PKG_C6_RESIDENCY` | MSR 0x3FA | RO | Package C6 counter; Solar verify phase | DMR CBB PM HAS |
| `SAGV_CONFIG_HANDLER` | PCode mailbox | RW (Solar only) | SA frequency injection; debug-unlocked for Solar | PCode mboxgen_bios.xml |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| Solar invocation | `solar.sh /cstate -scope 0:0:100 -states C1,C6 -mode e|v` | Solar source |
| Phases | 2: Exercise (`-mode e`) → Verify (`-mode v`) | Solar source |
| NWP platform XMLs | Needs `SOLAR_NWP_XMLS/` (not yet created) | NWP PM MAS |
| PkgC6 scenarios on NWP | Must limit to PkgC2 (PkgC6 ZBB’d) | NWP PM MAS |
| D2D C-state interaction | Remove — NIO monolithic, no D2D | NWP PM MAS |
| Covered TC | HSD 14019764517 | Runnable_On_N-1 | Solar cross products |

## NWP Delta

| Area | DMR (N-1) | NWP | Notes |
|------|----------|-----|-------|
| Solar platform XMLs | `SOLAR_DMR_XMLS/` | **Needs NWP XMLs** | New exercise/verify profiles required |
| MeshGV DVFS | Supported | **Skip** | MeshGV not applicable on NWP |
| PkgC6 scenarios | C6 exercise/verify | **Limit to PkgC2** | PkgC6 ZBB’d on NWP |
| SAGV access | PCode mailbox | Same expected | Verify SAGV_CONFIG_HANDLER on NIO |
| D2D C-state interaction | D2D link PM active | **N/A** | NIO monolithic — simpler cross-product |
| Core count | DMR ~288 cores | NWP TBD | Solar `-scope` parameter needs update |
| Covered TC | HSD 14019764517 | Runnable_On_N-1 | Solar cross products |

## Legacy (Human-Curated Reference)

*All original content preserved below for reference.*

### Architecture Summary

**Solar** is an OS-level workload injection tool for PM validation. It generates controlled PM stimuli (C-state entry via MWAIT, P-state changes, DVFS transitions) across cores with configurable patterns. Solar uses a **two-phase exercise/verify approach**:

1. **Exercise phase** (`-mode e`): Apply random or targeted PM patterns across cores simultaneously
2. **Verify phase** (`-mode v`): Validate residency counters, state machine consistency, no MCAs/hangs

#### Solar Architecture

```
  SVOS User Space                              HW PM State Machines
  ┌─────────────────┐                            ┌───────────────┐
  │ solar.sh         │                            │ Core threads  │
  │                  │                            │  MWAIT(Cx)    │
  │ XML profiles     │    MWAIT / WRMSR           │  P-state MSR  │
  │ (Exercise/       ├────────────────────────►├───────────────┤
  │  Verify)         │                            │ Module/PkgC   │
  │                  │    Residency counters       │ resolution    │
  │ Residency check  │◄────────────────────────┤               │
  └─────────────────┘                            └───────────────┘
```

#### Solar Test Scenarios

| Scenario | Phase | Command Pattern | What it validates |
|----------|-------|-----------------|-------------------|
| C1+C6 mixed | Exercise | `solar.sh /cstate -scope 0:0:100 -states C1,C6 -mode e` | Different cores at different C-state depths |
| C1+C6 mixed | Verify | `solar.sh /cstate -scope 0:0:100 -states C1,C6 -mode v` | Module C-state resolution (MC = min of core states) |
| Random | Exercise | `solar.sh /cstate -scope 0:0:100 -random -mode e` | Random MWAIT hints across cores |
| Random | Verify | `solar.sh /cstate -scope 0:0:100 -random -mode v` | C-state coordination, PICLET, budget negotiation |
| Unsupported MWAIT | Exercise | `solar.sh /cstate -unsupported -mode e` | Invalid MWAIT hint handling (no crash) |
| Legacy P-state + DVFS | Exercise | `solar.sh /cstate_legacy_pstate_dvfs` | Cross-domain: C-state × P-state × DVFS |

#### SAGV Debug Access

Solar has special access to the `SAGV_CONFIG_HANDLER` PCode mailbox even on production-locked parts (marked `<lock type="NONE">Used for debug tools (Solar)</lock>` in PCode `mboxgen_bios.xml`), enabling System Agent frequency changes during cross-product stress.

### Execution Flow

1. **Select platform XML**: `SOLAR_DMR_XMLS/Exercise/` or `SOLAR_DMR_XMLS/Verify/`
2. **Exercise phase**: Solar spawns per-core threads issuing MWAIT/WRMSR instructions per XML profile
3. **Concurrent stress**: Multiple PM domains exercised simultaneously (C-state + P-state + thermal)
4. **Hold duration**: Exercise runs for configured time to allow PM state machines to cycle
5. **Verify phase**: Solar reads residency counters (MSR `0x3FD` C6, `0x10` TSC, etc.) and validates invariants
6. **Result**: Pass if no hang, no MCA, residency counters within expected range

### Key Registers & Interfaces

| Register / MSR | Description | Solar Usage |
|----------------|-------------|-------------|
| `MWAIT` instruction | Core C-state entry | Exercise: issue with various Cx hints |
| `IA32_PERF_CTL` (MSR 0x199) | P-state request | Legacy P-state changes |
| `MSR_CORE_C6_RESIDENCY` (0x3FD) | Core C6 counter | Verify: residency validation |
| `MSR_PKG_C6_RESIDENCY` (0x3FA) | Package C6 counter | Verify: package-level residency |
| `IA32_TSC` (0x10) | Timestamp counter | TSC monotonicity check |
| `SAGV_CONFIG_HANDLER` | PCode mailbox | SA frequency injection |

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) | C-state × P-state interactions |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | Core/module/package C-state resolution |
| Tool | `SOLAR_DMR_XMLS/Exercise/` | DMR Solar exercise profiles |
| Tool | `SOLAR_DMR_XMLS/Verify/` | DMR Solar verify profiles |
| PCode src | `source/mailbox/mboxgen_bios.xml` | SAGV_CONFIG_HANDLER Solar access |

| HSD ID | Title | Segment | NWP Scope |
|--------|-------|---------|-----------|  
| 14019764517 | Solar Cross Products | FV | Runnable_On_N-1 |

### Related Sightings

| HSD | Title | Relevance |
|-----|-------|----------|
| 14020000571 | System hung when solar cstate test is run | GNR C-state cross-product hang |
| 14023081070 | Fail to boot in SNC mode during solar test | Reset × solar cross-product |

