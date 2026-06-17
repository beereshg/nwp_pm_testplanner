# PM Cross Products > PMX Cross Products

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [PM Cross Products](pm_cross_products_main.md)

## Baseline (DMR)

### What is PMX?
**PMX (PM eXerciser)** is a PythonSV-based test framework that runs multiple PM workloads concurrently
to validate cross-product interactions between C-states, P-states, RAPL, thermal, SVID, and PECI.
PMX drives hardware via PythonSV `namednodes` (direct register injection), running concurrent apps
with self-checking invariant validators.

### Topology
- Runs on the PythonSV host connecting to the SUT via `namednodes` interface
- Concurrent apps target: CBB Punit (PCode), IMH Punit (Primecode), Cores (Acode/µcode)
- Profile definitions in `pm/pmx/xml/dmr.xml`; NWP will need `nwp.xml`

### Operating Principle
`runPmx.py` loads a profile from `dmr.xml`, instantiates app/checker classes, and runs them in parallel
via `pmx_process.py`. Each app has `setup()`, `run()`, `check()` methods. Duration controlled by `-tM`
(minutes) or `-M` (iterations). `pmx_triage.py` collects failures with context.

### Boot-Time Init
No firmware init required — PMX is a test-time tool. Platform must be booted to SVOS with PythonSV
accessible. Profile selected at invocation.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| CBB Punit | CBB | Target for RAPL, C-state coordination, SVID, thermal injection via namednodes | `PKG_POWER_LIMIT`, `PACKAGE_C6_RESIDENCY`, SVID mailbox regs | DMR CBB PM HAS |
| IMH Punit | IMH | Target for memory RAPL, HPM message injection, OS mailbox | `DRAM_POWER_LIMIT`, `DRAM_ENERGY_STATUS` | HPM Message Spec |
| Core / Acode | CBB Compute | Target for C-state residency injection; MWAIT state machine | `CORE_FUSE_C6_ENABLE`, `MODULE_C6_LATENCY` | DMR CBB PM HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PCode | CBB Punit | C-state coordination, RAPL PID loop, SVID voltage sequencing, thermal response — all exercised concurrently by PMX apps | `PKG_POWER_LIMIT`, VR mailbox, PROCHOT | PCode CBB flows |
| Primecode | IMH Punit | RAPL domain management, HPM routing, OS mailbox — exercised by PMX DRAM/HPM apps | `DRAM_POWER_LIMIT`, HPM messages | Primecode flows |
| Acode | Core | MWAIT execution, core C-state entry/exit, VF curve application — exercised by PMX C-state apps | C-state entry/exit | Acode microcode |
| BIOS | Platform init | Feature enable/disable, power limit init, SST config before PMX runs | Feature enable knobs | NWP BIOS HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| PythonSV `namednodes` | `pm/pmx/runPmx.py` | RW | Register-level concurrent PM injection; PMX primary interface | PythonSV framework |
| PMX profile XML | `pm/pmx/xml/dmr.xml` | Config | Platform profile definitions (apps, checkers, parameters) | PMX source |
| `PKG_POWER_LIMIT` | MSR 0x610 | RW | RAPL power limit injection | IA32 Arch SDM / RAPL HAS |
| `IA_TEMPERATURE_TARGET` | MSR 0x1A2 | RO | Thermal target for checker apps | DMR SoC PM HAS |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| Profile count (DMR) | 8+ profiles: pmax, cstates, cpu_rapl, svid, epb_cross, peci_*, fit_cross, arden | pmx/xml/dmr.xml |
| NWP profile XML | Needs `nwp.xml` (not yet created) | NWP PM MAS |
| D2D apps on NWP | Must be removed/skipped (NIO has no D2D) | NWP PM MAS |
| PkgC6 profiles on NWP | Must limit to PkgC2 (PkgC6 ZBB’d) | NWP PM MAS |
| Invocation | `python3 runPmx.py -x dmr.xml -p <profile> -tM <min> -M <iter>` | PMX source |

## NWP Delta

| Area | DMR (N-1) | NWP | Notes |
|------|----------|-----|-------|
| Platform XML | `dmr.xml` | **Needs `nwp.xml`** | New profile definitions required for NWP |
| D2D cross-product apps | D2D PM apps active | **Remove/skip** | NIO has no D2D |
| MeshGV profiles | Supported | **Skip** | MeshGV not applicable on NWP |
| PkgC6 profiles | `pkgc` profile works | **Limit to PkgC2** | PkgC6 ZBB’d on NWP |
| PEGA C-state injection | Supported | TBD confirm | Verify PEGA availability on NWP |
| Covered TC | HSD 14023548389 | Runnable_On_N-1 | PMX cross products |

## Legacy (Human-Curated Reference)

*All original content preserved below for reference.*

### Architecture Summary

**PMX (PM eXerciser)** is a PythonSV-based test orchestration framework that runs **multiple PM workloads and checkers concurrently** to validate cross-product interactions between PM features. PMX drives the hardware through the PythonSV `namednodes` interface, injecting concurrent stimuli (C-state transitions, RAPL updates, SVID voltage changes, PECI polling) while self-checking invariants.

#### PMX Orchestration Architecture

```
   runPmx.py                                    SUT Hardware
  ┌─────────────────┐                            ┌───────────────┐
  │ Profile loader   │                            │ CBB Punit     │
  │ (dmr.xml /       │                            │ (PCode)       │
  │  nwp.xml)        │                            ├───────────────┤
  ├─────────────────┤    namednodes / SVOS     │ IMH Punit     │
  │ App 1: RAPL      ├────────────────────────►│ (Primecode)   │
  │ App 2: C-states  ├────────────────────────►├───────────────┤
  │ App 3: SVID      ├────────────────────────►│ Cores         │
  │ App 4: PECI      │                            │ (Acode/µcode) │
  │ Chk: residency   │                            └───────────────┘
  └─────────────────┘
```

#### Profile Categories (from `dmr.xml`)

| Profile | Concurrent Apps | What it tests |
|---------|----------------|---------------|
| `pmax` | RAPL max + turbo + thermal | Maximum power envelope stability |
| `cstates` | C-state + ccx_residency | C-state coordination, module/package resolution |
| `cpu_rapl` | RAPL + core_power + fit | RAPL throttling × P-state × FIT |
| `svid` | SVID + VR + core_power | Voltage regulator cross-product |
| `epb_cross` | EPB + HWP + C-state | Energy Performance Bias interactions |
| `peci_*` | PECI polling + thermal + power | Platform interface cross-product |
| `fit_cross` | FIT + RAPL + turbo | Frequency-integration cross-product |
| `arden` | Arden + mem_traffic | Memory power management |

#### Invocation

```bash
python3 runPmx.py -x dmr.xml -p <profile> -tM <minutes> -M <iterations>
# Example: PMX C-state cross-product for 5 iterations
python3 runPmx.py -x dmr.xml -p cstates -H 1 -M 5
```

### Execution Flow

1. **Load profile**: Parse `dmr.xml` (or future `nwp.xml`) for selected profile
2. **Instantiate apps**: Each concurrent app is a Python class with `setup()`, `run()`, `check()` methods
3. **Parallel execution**: All apps run concurrently via `pmx_process.py` process manager
4. **Duration/iteration control**: Run for `-tM` minutes or `-M` iterations
5. **Self-check**: Each checker app validates invariants (residency counters, power limits, voltage states)
6. **Triage**: `pmx_triage.py` collects results, flags failures with context

### Key Registers & Interfaces

PMX accesses registers via PythonSV `namednodes`:
- C-state: `CORE_FUSE_C6_ENABLE`, `MODULE_C6_LATENCY`, `PACKAGE_C6_RESIDENCY`
- RAPL: `PKG_POWER_LIMIT`, `PKG_ENERGY_STATUS`, `PLATFORM_POWER_LIMIT`
- SVID: SVID mailbox registers (VR address/command/data)
- Thermal: `IA_TEMPERATURE_TARGET`, `PACKAGE_THERM_STATUS`
- PECI: RdPkgConfig/WrPkgConfig opcodes

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) | SoC PM architecture |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | CBB PM cross-product |
| PythonSV src | `pm/pmx/runPmx.py` | PMX entry point |
| PythonSV src | `pm/pmx/xml/dmr.xml` | Platform profile definitions |
| PythonSV src | `pm/pmx/pmx_lib2.py` | PMX core library |
| PythonSV src | `pm/pmx/pmx_triage.py` | Failure triage module |

| HSD ID | Title | Segment | NWP Scope |
|--------|-------|---------|-----------|  
| 14023548389 | pmx cross products | FV | Runnable_On_N-1 |

### Related Sightings

| HSD | Title | Relevance |
|-----|-------|----------|
| 14020000571 | System hung when solar cstate test is run | C-state cross-product hang (GNR) |

