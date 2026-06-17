# Core C-States > Cross-Product

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing added (2026-05-28)
> **Parent**: [Core C-States](core_c_states_main.md)

## Baseline (DMR)

Cross-product tests validate C-state behavior under concurrent conditions: C-state transitions with active interrupts, mixed C1/C6 on different cores, random C-state patterns, and interaction with other PM features (C1E, PEGA, Solar).

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| ACP / PMA | CBB | All C-state FSMs exercised under cross-product stress: C1E abort under PEGA, mixed CC1/CC6, rapid MC state resolution | C1E FSM abort point; module state resolution (MCx = min of core states) | PNC PM HAS §8.10; §8.14 |
| PEGA (Performance Events Generator Agent) | CBB | Injects synthetic C-state requests and high-rate interrupts (≥38M INTx/sec) to stress C1E FSM and residency counters | pega_cmd1; INTx injection rate control; C-state request injection | DMR PEGA HAS |
| PICLET / FIL | CBB | Must correctly handle burst interrupt delivery without replay ordering errors under high PEGA load | piclet_enable/replay under high interrupt rates | PNC PM HAS §8.12 |
| SCF / Fabric | CBB + IMH | Fabric state consistency validated under rapid C-state cycling across multiple cores simultaneously | fabric_active; snoop traffic during mixed C1+C6 states | DMR SoC PM HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Tensilica ACP) | CBB core perimeter | C1E FSM under PEGA stress: rapid C1E enter/abort/re-enter cycles; module state resolution (MC = min of core states) | C1E FSM abort handler; MC1E entry gate (all cores ≥ C1E); PEGA C-state injection response | PNC PM HAS §8.10.5 |
| uCode (PantherCove) | CBB core | Processes rapid MWAIT/MONITOR cycles under Solar random C-state patterns; handles cross-core CC6 coordination under stress | ROB nukeaction under high interrupt rates; C-state state machine self-check (PMX ccx_test) | PNC PM HAS §8.12 |
| PCode (CBB) | CBB | PEGA configuration; workload characterization under stress affects demotion decisions; WISH_ALLOW updates during cross-product | PEGA cmd programming; RESOLUTION_CONTROL updates under load | DMR CBB PM HAS |
| BIOS / UEFI | Platform | Baseline C-state configuration that determines which cross-products are valid | C6Enable; MonitorMWait; C1AutoDemotion — must be correctly set for cross-product tests | BIOS PM HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR CC1 Residency | 0x778 | RO | Crystal cycles in CC1; validated in cross-product with concurrent PM activity | PNC PM HAS §8.3 |
| MSR CC6 Residency | 0x3FD | RO | Crystal cycles in CC6; validated for consistency under PEGA interrupt injection | PNC PM HAS §8.3 |
| CORE_PMA_CR_CORE_STATUS | CR (uCode-written) | RO to OS | Core C-state (CC0/CC1/CC6); used in self-checking PMX ccx_test verification | PNC PM HAS §8.12 |
| pega_cmd1 | PEGA CR | WO | PEGA C-state injection control; rate and pattern configuration | DMR PEGA HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| PEGA INTx injection rate (stress) | ≥ 38 M | interrupts/s | Applied during C1E + PEGA cross-product test scenario | PSS TC description |
| HW C1E promotion under PEGA | Degraded | — | Rapid entry/exit resets sliding window; statistical promotion may be suppressed | PNC PM HAS §8.10.5 |
| C6 exit latency under PEGA | ~30 | µs | Same DMR KPI target maintained even under high interrupt injection load | DMR PSS KPI target |
| Module C-state resolution | MCx = min(cores) | — | MC state = minimum C-state depth of all enabled cores in module | PNC PM HAS §8.14 |
| Solar exercise+verify pattern | Two-phase | — | Exercise: random C-state patterns; Verify: residency counters, no hangs | PSS TC description |

## NWP Delta

**C-state cross-product interactions are supported on NWP** — same PNC core; reduced matrix due to PkgC6 removal.

### Removed Cross-Products
- **PkgC6 × ***: All PkgC6 cross-products removed (PkgC6 not supported on NWP)
- PkgC6 × PROCHOT, PkgC6 × D2D, PkgC6 × RAPL — all N/A
- PkgC6 × MC6 flush deadlock scenario — N/A (no PkgC6)
- SST-PP × C-states — applicability on NWP: **TBD** (confirm from NWP PM MAS)

### Retained Cross-Products (same PNC core architecture as DMR)
- C1/C6 × PEGA interrupt injection — same test scenarios
- C6 × Turbo (core/module level)
- C6 × RAPL (module level)
- C6 × Thermal (module level)
- MC6 × Memory thermal
- Fast C1E × DVFS — TBD (confirm same module-level scope)
- Solar random C-state exercise — same (same PNC core)

### Validation Impact
- Reduced cross-product matrix (no PkgC6)
- Core/module C-state cross-products: same as DMR (same PNC architecture and FW agents)

## Legacy (Human-Curated Reference)

### Architecture Summary

Cross-product tests validate C-state behavior under concurrent conditions: C-state transitions with active interrupts, mixed C1/C6 on different cores, random C-state patterns, and interaction with other PM features (C1E, PEGA, Solar).

#### Key Cross-Product Scenarios

| Scenario | Interaction | Risk |
|----------|------------|------|
| **C1E + PEGA interrupts** | 38M+ INTx/sec while cores cycle C1E | C1E promotion/demotion algorithm stress; PMA interrupt handling contention |
| **PMX ccx_test** | Self-checking C-state test with concurrent PM activity | Validates C-state state machine integrity |
| **C1+C6 mixed** (Solar) | Different cores at different C-state depths simultaneously | Tests module C-state resolution logic (MC = min of core states) |
| **Random C-state** (Solar) | Random MWAIT hints across cores | Stress test for C-state coordination, PICLET, budget negotiation |

#### PEGA C1E Interaction *(confirmed: [PNC PM HAS §8.10](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

When PEGA injects C1E and high-rate interrupts arrive simultaneously:
- PMA C1E FSM must handle rapid C1E enter → abort → re-enter cycles
- C1E abort point is after fast GV-down but before voltage applied
- The abort handler cannot interrupt the electrical part → some latency absorbed
- HW C1E promotion algorithm (8-entry sliding window) may get confused by rapid short C1 windows

#### Solar C-State Exercise/Verify Pattern

Solar tests use a two-phase approach:
1. **Exercise**: Apply random C-state patterns, inject stimuli, run concurrently
2. **Verify**: Validate residency counters, state machine consistency, no hangs

### Key Registers & Interfaces

| Register | Description | Source |
|----------|-------------|--------|
| `pega_cmd1` | PEGA C-state injection control | ⚠ PEGA HAS |
| MSR `0x3FD` | CC6 residency counter | ✅ PNC PM HAS §8.3 |
| MSR `0x778` | CC1 residency counter | ✅ PNC PM HAS §8.3 |
| `CORE_PMA_CR_CORE_STATUS` | Core C-state (used in self-checking) | ✅ PNC PM HAS §8.12 |

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) | PEGA injection mechanism |
| HAS | [PNC PM HAS 0.5](c:\github\NWP\PNC%20PM%20HAS%200.5.docx) | C1E + C6 interaction |
| PSS | [HSD 22022018466](c:\github\NWP\nwp_pss_deep_analysis_automated\HSD_22022018466_PSS_DeepAnalysis.html) | PEGA/Solar C-state injection deep analysis |

### Related Sightings
| | C1E + high-rate interrupt stress |
| | Solar random C-state transitions — exercise + verify pattern |

### NWP Delta

| Area | DMR (N-1) | NWP | Notes |
|------|----------|-----|-------|
| PEGA C-state injection | Supported | Same expected | ⚠ Confirm NWP PEGA support |
| Solar C-state tests | Supported | Same expected | MeshGV NA for NWP (noted in ashtree_prt) |
| Mixed C1+C6 | Supported | Same | Module resolution logic unchanged |

### Source Notes

| # | Claim | Confidence | Source |
|---|-------|-----------|--------|
| 1 | PEGA C1E + INTx interaction scenario | ⚠ Inferred | TC title + PNC PM HAS §8.10 C1E abort flow |
| 2 | Solar exercise/verify pattern | ⚠ Inferred | TC titles |
| 3 | C1E abort point (after GV-down, before voltage) | ✅ Confirmed | PNC PM HAS §8.10.5 |
