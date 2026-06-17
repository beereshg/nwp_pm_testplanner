# PM Cross Products — Main Flow

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing; AIPM sub-feature added (2026-05-31)
> **Parent**: [KB Index](../INDEX.md)

## Baseline (DMR)

### What is PM Cross Products?
PM Cross Products validates that multiple PM features work correctly **simultaneously**. Individual PM
features (C-states, P-states, RAPL, thermal, SVID, PECI) are validated in isolation by dedicated suites;
cross-product tests catch regressions in feature interactions.

Two complementary tools: **PMX** (PythonSV register-level concurrent injection) and **Solar** (OS-level
MWAIT/WRMSR instruction injection exercising the real OS PM path).

### Topology
```
  PMX (PythonSV)            Solar (SVOS user-space)
  namednodes reg injection   MWAIT / WRMSR instructions
        |                          |
        +----------+---------------+
                   |
          HW PM State Machines
          CBB Punit / IMH Punit / Cores
```

### Operating Principle
PMX: concurrent Python apps drive C-state + RAPL + SVID + PECI simultaneously; self-checking invariant
validators detect regressions. Solar: exercise phase injects PM patterns; verify phase validates residency
counters and checks for MCAs / hangs.

### Boot-Time Init
No firmware init required — both tools are test-time. Platform must be booted to SVOS with PythonSV
accessible. BIOS must have all tested features enabled.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| CBB Punit (PCode) | CBB | Primary target: C-state coordination, RAPL, P-state arbitration, SVID, thermal — all concurrent | All PM state machine regs | DMR CBB PM HAS |
| IMH Punit (Primecode) | IMH | DRAM RAPL, HPM routing, OS mailbox — concurrent with CBB PM | `DRAM_POWER_LIMIT`, HPM msgs | HPM Message Spec |
| Core / Acode | CBB Compute | MWAIT-driven C-state entry/exit; P-state requests; PICLET budget negotiation | C-state SM, MWAIT, WRMSR | DMR CBB PM HAS |
| SAGV mailbox | CBB Punit | Debug-unlocked for Solar; SA frequency injection during cross-product stress | `SAGV_CONFIG_HANDLER` | PCode mboxgen_bios.xml |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PCode | CBB PUnit | C-state coordination, P-state arbitration, RAPL PID, thermal response, SVID — all concurrent during cross-product | All CBB PM flows | PCode CBB flows |
| Primecode | IMH PUnit | DRAM RAPL, HPM message routing, OS mailbox — concurrent with CBB PM stress | DRAM RAPL, HPM msgs | Primecode flows |
| Acode | Core | MWAIT execution, CC1/CC6 entry/exit, PICLET, VF curve during Solar/PMX stress | Core C-state SM | Acode microcode |
| BIOS | Platform init | Feature enable/disable (PkgC, SST, RAPL), power limit init before cross-product runs | All feature enable knobs | NWP BIOS HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| PythonSV `namednodes` | `pm/pmx/runPmx.py` | RW | PMX: register-level concurrent PM injection | PythonSV framework |
| `MWAIT` instruction | x86 | WO (Solar) | Solar: C-state entry hint per core | IA32 Arch SDM |
| `IA32_PERF_CTL` | MSR 0x199 | RW (Solar) | Solar: P-state request | IA32 Arch SDM |
| `MSR_PKG_C6_RESIDENCY` | MSR 0x3FA | RO (Solar verify) | Solar: package C6 counter validation | DMR CBB PM HAS |
| `SAGV_CONFIG_HANDLER` | PCode mailbox | RW (Solar only) | SA frequency injection during stress | PCode mboxgen_bios.xml |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| Subflows | 2: PMX Cross Products, Solar Cross Products | pm_cross_products_main.md |
| NWP platform XMLs required | `nwp.xml` (PMX) + `SOLAR_NWP_XMLS/` (Solar) — neither exists yet | NWP PM MAS |
| PkgC6 removal on NWP | Must limit to PkgC2 across both tools | NWP PM MAS |
| D2D cross-product removal | Remove D2D apps from PMX; D2D C-state interaction N/A on NWP | NWP PM MAS |
| Known sightings | HSD 14020000571 (Solar C-state hang, GNR); HSD 14023081070 (Solar reset × SNC) | HSD |

## NWP Delta

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| Feature supported | ✅ Carried from DMR | NWP PM MAS |
| PMX platform XML | Needs `nwp.xml` profile definitions | NWP PM MAS |
| Solar platform XMLs | Needs `SOLAR_NWP_XMLS/` exercise + verify profiles | NWP PM MAS |
| D2D cross-product | ❌ N/A — NIO monolithic, no D2D link PM | NWP PM MAS |
| MeshGV profiles | ❌ Skip — MeshGV not applicable on NWP | NWP PM MAS |
| PkgC6 scenarios | ❌ ZBB’d — limit to PkgC2 across both tools | NWP PM MAS |
| NWP simplified topology | NIO monolithic — fewer cross-product interaction surfaces than DMR | NWP PM MAS |
| AIPM (Autonomous Idle PM) | ✅ Partial — active-link TCG ZBB'd; no-device + IP-disable sub-scenarios kept; see [aipm.md](aipm.md) | NWP AIPM scoping |  

## Sub-Feature Articles

| Article | Feature | NWP Status |
|---------|---------|------------|
| [PMX Cross Products](pmx_cross_products.md) | PythonSV concurrent PM injection | ✅ |
| [Solar Cross Products](solar_cross_products.md) | OS-level concurrent PM injection | ✅ |
| [PM Sideband Harasser](pm_sideband_harasser.md) | Sideband harass during PM transitions | ✅ |
| [AIPM — Autonomous Idle PM](aipm.md) | HW-autonomous MIO trunk clock gating | ✅ Partial (no-device + IP-disable; active-link ZBB) |

## Legacy (Human-Curated Reference)

*All original content preserved below for reference.*

### Architecture Summary

**PM Cross Products** validates that multiple PM features work correctly when exercised **simultaneously**. Individual PM features (C-states, P-states, RAPL, thermal, SVID, PECI) are validated in isolation by dedicated test suites; cross-product tests verify no regressions when they interact concurrently.

Two complementary tools drive cross-product validation:

| Tool | Level | Approach |
|------|-------|----------|
| **PMX** (PM eXerciser) | PythonSV / register-level | Concurrent apps via `namednodes` — direct HW register injection |
| **Solar** | OS / SVOS user-space | MWAIT/WRMSR instruction injection — exercises real OS PM path |

```
  ┌──────────────────┐     ┌──────────────────┐
  │ PMX             │     │ Solar            │
  │ (PythonSV)      │     │ (OS-level)       │
  │                  │     │                  │
  │ Register-level   │     │ MWAIT / WRMSR    │
  │ concurrent apps  │     │ instruction      │
  │                  │     │ injection        │
  └────────┬─────────┘     └────────┬─────────┘
           │                         │
           └─────────┬─────────────┘
                     │
           ┌────────┴─────────┐
           │  HW PM State         │
           │  Machines            │
           │  (Punit/Core/Mem)    │
           └───────────────────┘
```

#### Cross-Product Interaction Matrix

| Feature A | Feature B | Key Interaction |
|-----------|-----------|------------------|
| C-state | P-state | Frequency restoration on C-state exit |
| C-state | RAPL | Power budget during deep C-state transitions |
| RAPL | Thermal | PROCHOT override vs. power limit clipping |
| SVID | P-state | Voltage sequencer timing during freq changes |
| PECI | C-state | Temperature sampling during idle |
| D2D PM | PkgC | D2D link state vs. package C-state (DMR only) |

### FW Agents

- **PCode (CBB Punit)**: C-state coordination, P-state arbitration, RAPL PID loop, thermal response
- **Primecode (IMH Punit)**: RAPL domain management, OS mailbox, HPM message routing
- **Acode (Core)**: MWAIT execution, core C-state entry/exit, VF curve application
- **BIOS**: Feature enable/disable, power limit initialization, SST configuration

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) | Master SoC PM — cross-feature interactions |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | CBB PM cross-product (C-state × P-state × thermal) |
| HAS | [HPM Message Specification](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html) | Cross-die HPM interactions |
| HAS | [DMR D2D PM Perimeter HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/D2D/DMR_D2D_Perimeter.html) | D2D perimeter: cross-die PROCHOT, THERMTRIP |
| HAS | [DMR D2D Power Management HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/D2D_PM/D2D_PM.html) | D2D PM resources |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS |
| HAS | [DMR Firmware Architecture](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/FirmwareArch.html) | FW architecture context |
| PythonSV src | `pm/pmx/runPmx.py` | PMX entry point |
| PythonSV src | `pm/pmx/xml/dmr.xml` | PMX platform profile definitions |
| Tool | `SOLAR_DMR_XMLS/` | Solar exercise/verify configs |

### Related Sightings

| HSD | Title | Relevance |
|-----|-------|----------|
| 14020000571 | System hung when solar cstate test is run | C-state cross-product hang (GNR) |
| 14023081070 | Fail to boot in SNC mode during solar test | Reset × solar cross-product |

### Subflows (2)

| # | Subflow | Status | TCs | Segment | Notes |
|---|---------|--------|-----|---------|-------|
| 1 | [PMX Cross Products](pmx_cross_products.md) | Enriched | 1 | FV | PythonSV concurrent PM app orchestration |
| 2 | [Solar Cross Products](solar_cross_products.md) | Enriched | 1 | FV | OS-level MWAIT/WRMSR cross-product stress |
| | **Total** | 2/2 enriched | **2** | | |

