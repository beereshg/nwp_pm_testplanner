# Core C-States — Main Flow

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing added (2026-05-28)
> **Parent**: [Core C-States](core_c_states_main.md)

## Baseline (DMR)

Core C-states are a **four-level idle state hierarchy** (Thread→Core→Module→Package) managed by a multi-agent firmware stack. The key PNC/LNC architectural shift (used in DMR/NWP) is that **C-state management moved inside the Core Perimeter** — the PMA/Acode now owns entry/exit/demotion instead of the SoC-level PUnit.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| ACP / PMA | CBB | Core-local C-state FSM for all levels: clock-gate (C1), power-gate sequencing (C6), module coordination (MC6) | core_active, cfcclk_qactive, cfcpwr_qactive, inf_qactive, powergood | PNC PM HAS §8 |
| PICLET / FIL | CBB | Interrupt filtering in CC6; queues break events; replays to APIC on exit; SRL snoop default in MC6 | piclet_enable, piclet_replay_ack, gfifo_empty, stop_interface | PNC PM HAS §8.12 |
| C6SRAM | CBB | Stores per-thread and per-core architectural state during C6 power-gate; DCM semaphore for first/last core | save/restore triggers; ML3_CR_PIC_BOOT_MESSAGE base addr; HW semaphore | PNC PM HAS §8.12 |
| SRL (Snoop Response Logic) | CBB | Default snoop responses for sleeping module in MC6 (MLC flushed) | snoopq_empty; FIL stop_interface ack | PNC PM HAS §8.14 |
| Q-channels (CFC_CLK / CFC_PWR / INF) | CBB | Three-resource negotiation; deasserted progressively C1→MC3→MC6→PkgC | Q_CFC_CLK.qactive, Q_CFC_PWR.qactive, INF.qactive (all 3 off → MC6 / PkgC) | PNC PM HAS §8.1, §8.14 |
| FIVR | CBB | Per-core VR: holds voltage in C1; drops to LFM in C1E; powers down in C6; vinf_aon retains C6SRAM | vinf_aon always-on; VCCcore/module gated by PMA | DMR CBB PM HAS |
| PkgC Aggregator (PUnit) | CBB | Package C-state resolution: min(all modules); asserts PkgC idle via HPM to IMH | HPM PkgC_idle; D2D virtual wires | DMR CBB PM HAS |
| SCF / Fabric | CBB + IMH | Fabric clock/power gated at module (MC6) and full package (PkgC6) levels | CFC_CLK/PWR Q-channel aggregation | DMR SoC PM HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| uCode (PantherCove) | CBB core | Thread C-state sequencer: MWAIT/HLT dispatch, C6SRAM save/restore, PICLET setup, ARAT-TTT write, CC6 multi-thread coordination | TC6 entry 10-step flow; CC6 coordinator (ROB nukeaction); PICLET enable/replay; C6 exit reset handler | PNC PM HAS §8.9, §8.12 |
| Acode (Tensilica ACP) | CBB core perimeter | Core-level PM FW: budget negotiation, C6 demotion, Fast C1E WP calc, C6 enter/exit interrupt handling | core_c6_enter() L15323; core_c6_exit() L15423; initiate_core_electric_budget_release_flow(); C6_DEMOTION bit | PNC PM HAS §8; Acode_PNC_SERVER.lst |
| PCode (CBB) | CBB | Package-level aggregator: RESOLUTION_CONTROL.WISH_ALLOW, L2_DEMOTION_POLICY, ICCP budget for C6 exit | Budget negotiation (INC_GB / DEC_GB); WP1/WP3/WP4 update; demotion policy; CRWr ARAT-TTT | DMR CBB PM HAS |
| PrimeCode (IMH) | IMH | Package C-state coordination across CBBs; D2D fabric gating for PkgC; receives HPM C-state messages | HPM C-state messages; D2D power-gating sequence | PrimeCode firmware |
| BIOS / UEFI | Platform | Programs C-state configuration knobs at boot; populates ACPI C-state objects | C6Enable; C1AutoDemotion; MonitorMWait; MSR 0xE2 population | BIOS PM HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MWAIT / HLT | CPU instruction | W | Requests target C-state; EAX[7:4]=state, EAX[3:0]=sub-state (P/A/S/T/E bits) | IA-32 SDM; PNC PM HAS §8.1 |
| MSR CLOCK_CST_CONFIG_CONTROL | 0xE2 | RW | C6/C1 enable/disable; bit[26] C1_DEM_EN, [25] C3_DEM_EN, [28/27] undemotion enables | PNC PM HAS §8.6.5 |
| MSR POWER_CTL | 0x1FC | RW | bit[0] C1E_ENABLE — enables OS C1→C1E promotion via MWAIT sub-state 1 | PNC PM HAS §8.10 |
| MSR CC1 Residency | 0x778 | RO | Crystal cycles in CC1 (C1 and C1E combined) | PNC PM HAS §8.3 |
| MSR CC1 Residency (alt) | 0x660 | RO | CC1 residency in x1 clocks (alternate counter) | PNC PM HAS §8.3.5 |
| MSR CC6 Residency | 0x3FD | RO | Crystal cycles in CC6 power-gated state | PNC PM HAS §8.3 |
| MSR MC6 Residency | 0x664 | RO | Crystal cycles in Module C6 (MLC flushed, module power-gated) | PNC PM HAS §8.3.12 |
| MSR PkgC6 Residency | 0x3F9 | RO | Crystal cycles in Package C6 (reads 0 on NWP — PkgC6 ZBB) | PNC PM HAS §8.1 |
| CPUID.05H | Leaf 5 | RO | Enumerates supported C-states and valid MWAIT hint sub-state encodings | IA-32 SDM |
| ACPI _CST / _CSD | ACPI namespace | RO | OS C-state descriptor; enumerates C1/C6 per logical processor | ACPI Spec 6.x |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| C6 exit latency (DMR) | ~30 | µs | CC6 → CC0 via full PUnit budget negotiation | DMR PSS KPI target |
| C6A (Autonomous) exit latency | < 30 | µs | No PUnit budget negotiation; PMA retains electrical budget | PNC PM HAS §8.5 |
| CC1 / TC1 exit latency | < 1 | µs | Clock-gate only; break event → immediate thread wake | PNC PM HAS §8.9 |
| Slow C1E entry delay | 64–250 | µs | PUnit detects C1E → waits before reducing fmax | PNC PM HAS §8.10.3 |
| Fast C1E exit to first instruction (server) | ~2 | µs | High-voltage LFM WP; no VR ramp-up needed | PNC PM HAS §8.10.2 |
| HW C1E promotion window | 8 entries | — | Sliding buffer; sum ≥ 8 triggers C1→C1E statistical promotion | PNC PM HAS §8.10.5 |
| PkgC6 residency on NWP | 0 | crystal cycles | PkgC6 fused off; FUSE_PKG_C_STATE=0 | NWP PM MAS §6.2 |
| TSC monotonicity | Guaranteed | — | TSC must not go backward across any C-state or P-state transition | IA-32 SDM |

## NWP Delta

**Core C-states subsystem is supported on NWP** — same PantherCove (PNC) core as DMR; key delta is PkgC6 removal.

### Summary Table

| Feature | NWP Status | Key Delta |
|---------|-----------|-----------|
| C1 | Supported | No change (same PNC core, same Acode/PCode flow) |
| C6 (CC6) | Supported | No change (same PNC core, same FW agents) |
| MC6 | Supported | Now deepest idle (no PkgC6 beyond it) |
| PkgC6 | **REMOVED** | Fused off: FUSE_PKG_C_STATE=0 |
| Entry/Exit | Supported | No change (same PNC core, same FW agents) |
| Demotion | Supported | No change (Acode still implements C6 demotion) |
| Fast C1E | Supported | TBD — confirm module-level scope on NWP |
| Cross-products | Reduced | No PkgC6 cross-products |
| PLR | Supported | TBD — confirm PLR implementation on NWP |
| Ashtree PRT | Supported | No change (same PNC core, same Acode/PCode flow) |

### Architecture-Level Deltas
- **Same PantherCove (PNC) P-core** as DMR — ACP/Acode, uCode, PCode FW agents unchanged
- **PkgC6 removed** — fused off; FUSE_PKG_C_STATE=0; Pchannel PUNIT↔RC removed; MC6 is deepest idle
- **No autonomous E-core C6** — core C6 managed same as DMR (PNC core requires Acode involvement)
- Pchannel/Qchannel RCs↔IPs retained for future NWP product lines that may re-enable PkgC6

## Co-Design T2 Ingest (2026-07-19)

Source: Co-Design T2 WHAT-boundary response for TP `15019478558` (Core C-States).

### Structural Decisions

| Decision | Result |
|----------|--------|
| `22022421247` scope | Split recommended into separate C6A vs C6S vs C6S-P WHATs because bars diverge |
| `22022421250` scope | Split recommended: core logical entry sequencing vs module MC6 electrical entry sequencing |
| `22022421253` scope | Split recommended: wake sequencing correctness vs exit-latency envelope validation |
| `22022421260` scope | Keep MC6 residency as primary WHAT; split wake-target behavior into separate WHAT |
| `22022421293` scope | Keep telemetry ownership bounded to PMT/PMX mapping consistency (avoid re-owning functional WHATs) |
| `22022421289` / `22022421307` | Keep as framework/stress TCDs; do not merge into functional WHAT ownership |
| PkgC6 / C6S-P on NWP | Keep parked as out-of-scope for current Newport plan unless scope changes |

### Updated TODO List (from T2 ingest)

| Priority | Item | Owner TCD | Action |
|----------|------|-----------|--------|
| P0 | Split C6 functional ownership by bar boundary | `22022421247` | Done — `22022421247` keeps C6A; created [16031170164](https://hsdes.intel.com/appstore/article-one/#/16031170164) (C6S) and [16031170168](https://hsdes.intel.com/appstore/article-one/#/16031170168) (C6S-P parked) |
| P0 | Split entry sequencing from MC6 electrical sequence | `22022421250` | Done — `22022421250` keeps core entry; created [16031170165](https://hsdes.intel.com/appstore/article-one/#/16031170165) (MC6 entry sequence) |
| P0 | Split wake correctness from latency KPI | `22022421253` | Done — `22022421253` keeps wake ordering; created [16031170166](https://hsdes.intel.com/appstore/article-one/#/16031170166) (exit latency class) |
| P1 | Isolate MC6 wake-target behavior | `22022421260` | Done — `22022421260` keeps residency; created [16031170167](https://hsdes.intel.com/appstore/article-one/#/16031170167) (MC6 wake target) |
| P1 | Bound telemetry scope and remove overlap language | `22022421293` | Edit Section 1/5 text to only own PMX/PMT-to-architectural counter consistency bars |
| P1 | Keep stress TCDs non-owning for functional bars | `22022421289`, `22022421307` | Add explicit note: these are regression frameworks, not primary functional WHAT owners |
| P2 | Add overlap cross-links to reduce future drift | all listed above | Add "Related TCD" links for entry/exit/MC6/telemetry handoff boundaries |
| P2 | Re-run T1 after split draft | TP `15019478558` | Run Co-Design T1 using post-split hierarchy snapshot to validate no residual overlap |

### HSD Creation Order (recommended)

| Order | HSD ID | Title | Source split | Parent TPF |
|------:|--------|-------|--------------|------------|
| 1 | [16031170164](https://hsdes.intel.com/appstore/article-one/#/16031170164) | C6S Behavior and MC6 Qualification | `22022421247` | 15019478559 |
| 2 | [16031170165](https://hsdes.intel.com/appstore/article-one/#/16031170165) | MC6 Electrical Entry Sequence | `22022421250` | 15019478562 |
| 3 | [16031170166](https://hsdes.intel.com/appstore/article-one/#/16031170166) | C-State Exit Latency Class Validation | `22022421253` | 15019478559 |
| 4 | [16031170167](https://hsdes.intel.com/appstore/article-one/#/16031170167) | MC6 Wake Target Behavior | `22022421260` | 15019478562 |
| 5 | [16031170168](https://hsdes.intel.com/appstore/article-one/#/16031170168) | C6S-P and PKGC Behavior (Parked) | `22022421247` | 15019478559 |

Execution notes:
- Create rows 1-4 as active TCDs after preview review.
- Keep row 5 parked unless NWP scope changes to include PKGC targeting.

### Execution Gate

- Do not push any split/new TCD to HSD until preview content is generated and reviewed.
- Any NEW row without a measurable spec-cited bar stays as a parked proposal.
