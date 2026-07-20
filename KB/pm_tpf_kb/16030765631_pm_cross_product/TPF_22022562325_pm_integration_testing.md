# TPF 22022562325 — PM Integration Testing

| Field | Value |
|-------|-------|
| **TPF ID** | [22022562325](https://hsdes.intel.com/appstore/article/#/22022562325) |
| **Title** | PM Integration Testing |
| **Parent TP** | [16030765631 — [NWP PM] PM Cross Product](https://hsdes.intel.com/appstore/article/#/16030765631) |
| **Owner** | thangama |
| **Status** | open |
| **KB last updated** | 2026-07-20 |

---

## Section 1: Feature Classification & Introduction

PM Integration Testing validates cross-feature power management interactions and stress scenarios on NWP using multi-domain concurrent workloads. This TPF exercises feature interactions that individual feature TPFs cannot cover in isolation — the system-level emergent behavior when RAPL, RACL, C-states, HWP, DVFS, and legacy P-states operate simultaneously under stress.

**Classification:** Integration / Stress testing — firmware + silicon + platform interaction validation.

**Gating Mechanism:** Feature coverage is gated by NWP fuse configuration:
- Socket RAPL: Supported (required)
- Fast RAPL: Supported (required)
- RACL: Supported (required)
- Platform RAPL (Psys): **Not supported** (fused off on NWP)
- DRAM RAPL: **Not supported** (fused off on NWP)
- PkgC6: **Not supported** (fused off on NWP)

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| Socket RAPL | Supported | NWP PM HAS |
| Fast RAPL | Supported | NWP PM HAS |
| RACL | Supported (partition-level current limiting) | NWP PM HAS |
| Platform RAPL (Psys) | Not supported (fused off) | NWP PM HAS |
| DRAM RAPL | Not supported (fused off) | NWP PM HAS |
| PkgC6 | Not supported (fused off) | NWP PM HAS |
| Core C-states | C0, C1, C1e, C6 | NWP PM HAS |
| Core GV (CBB-side) | Supported — CBB core domain V/F transitions | NWP PM HAS |
| IMH Fabric DVFS | **Not supported on NWP** — no IMH-side uncore DVFS | NWP delta |
| HWP | Supported via TPMI | NWP PM HAS |
| Legacy P-states | Supported via TPMI | NWP PM HAS |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:12px;font-family:Arial,sans-serif;max-width:700px">
  <div style="background:#4472C4;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 5: OS / Tool</strong> — PMX stress tool, Solar PM random generator, intel_pstate driver, HWP / Legacy P-state requests</div>
  <div style="background:#ED7D31;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 4: BIOS / Platform Config</strong> — RAPL limits, RACL config, C-state enable, DVFS knobs, power domain setup</div>
  <div style="background:#A020F0;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 3: PCode / OCode Firmware</strong> — RAPL PID controller, RACL enforcement, frequency arbitration, C-state coordination, DVFS execution</div>
  <div style="background:#70AD47;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 2: Sideband / Platform Agent</strong> — Sideband harasser injection, PEGA interface, CBB↔IMH HPM messages, wake/idle signals</div>
  <div style="background:#FF0000;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 1: Silicon / HW</strong> — FIVR, VR interface, frequency PLLs, power gating, thermal sensors, clock domain crossings</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| Layer 5: OS / Tool | ❌ | ❌ | ❌ | ✅ | ✅ | PMX/Solar tools require booted OS with PythonSV or tool stack |
| Layer 4: BIOS / Platform Config | ✅ | ❌ | ❌ | ✅ | ✅ | Config validation at BIOS + post-Si |
| Layer 3: PCode / OCode Firmware | ✅ | ✅ | ✅ | ✅ | ⚠️ | Full firmware coverage pre-Si; FV primary; PV indirect only |
| Layer 2: Sideband / Platform Agent | ✅ | ⚠️ | ✅ | ✅ | ❌ | Sideband harasser requires XOS or FV; HSLE partial |
| Layer 1: Silicon / HW | ❌ | ✅ | ✅ | ✅ | ⚠️ | Real silicon at FV; RTL at HSLE/XOS; PV observes indirectly |

### PM Cross-Product Interaction Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        OS / Tool Layer                                │
│  ┌─────────┐   ┌───────────┐   ┌──────────────┐   ┌─────────────┐  │
│  │   PMX   │   │   Solar   │   │  SB Harasser │   │ HWP/P-state │  │
│  │  Stress │   │  Random   │   │  Injection   │   │  Requests   │  │
│  └────┬────┘   └─────┬─────┘   └──────┬───────┘   └──────┬──────┘  │
└───────┼───────────────┼────────────────┼───────────────────┼─────────┘
        │               │                │                   │
        ▼               ▼                ▼                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   PCode / OCode Firmware                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────┐  │
│  │  RAPL PID    │  │    RACL      │  │   Frequency Arbitration   │  │
│  │  Controller  │  │  Enforcer    │  │  (min of all limiters)    │  │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬──────────────┘  │
│         │                  │                       │                  │
│         └──────────────────┴───────────────────────┘                  │
│                            │                                          │
│                    ┌───────▼───────┐                                  │
│                    │   DVFS Exec   │                                  │
│                    │  + C-state    │                                  │
│                    │  Coordination │                                  │
│                    └───────┬───────┘                                  │
└────────────────────────────┼─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│               Sideband / Platform Agent Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐        │
│  │  CBB↔IMH HPM │  │  PEGA I/F    │  │  Wake/Idle Signals  │        │
│  │  Messages    │  │              │  │  (Q-ch / P-ch)      │        │
│  └──────────────┘  └──────────────┘  └─────────────────────┘        │
└──────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Silicon / HW Layer                                  │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────────┐  ┌──────────┐  │
│  │  FIVR  │  │  PLLs  │  │  Power │  │  Thermal   │  │  Clock   │  │
│  │        │  │        │  │  Gates │  │  Sensors   │  │  X-ings  │  │
│  └────────┘  └────────┘  └────────┘  └────────────┘  └──────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### Key Cross-Product Interaction Flows

**Flow 1 — RAPL + C-state Exit Storm:**
1. Multiple cores in C6 → power consumption low → RAPL headroom available
2. Simultaneous C6 exit (workload burst) → sudden power spike
3. RAPL PID detects power overshoot → asserts frequency ceiling
4. Arbitration reduces frequency for all active cores
5. **Risk:** Delayed PID response allows transient overcurrent

**Flow 2 — RACL Partition Throttle + HWP:**
1. HWP requests P0 on all cores in partition
2. RACL current limit hit in one partition
3. Frequency ceiling applied per-partition (not socket-wide)
4. Other partition continues at requested frequency
5. **Risk:** Non-uniform performance not reported correctly in telemetry

**Flow 3 — Sideband Harasser + PM Transition:**
1. Core entering C6 → Q-channel handshake in progress
2. Sideband harasser injects spurious wake/idle signal
3. PM state machine must reject spurious wake or handle gracefully
4. **Risk:** Hang if state machine accepts spurious signal during handshake

### Interface & Register Matrix

| Register / MSR | Field | Default | Feature Effect | Tier Validated |
|---|---|---|---|---|
| MSR_RAPL_POWER_UNIT | POWER_UNIT, TIME_UNIT, ENERGY_UNIT | HW default | Defines RAPL measurement units | FV, PSS |
| MSR_PKG_POWER_LIMIT | PL1, PL2, CLAMP, TIME_WINDOW | BIOS config | Socket power limits | FV, PV |
| MSR_PKG_ENERGY_STATUS | ENERGY | 0 | Running energy counter for RAPL | FV, PSS |
| RACL_LIMIT (TPMI) | CURRENT_LIMIT, TIME_WINDOW | BIOS config | Per-partition current limit | FV, PSS |
| MSR_PKG_PERF_STATUS | THROTTLE_LOG | 0 | Throttle active indicator | FV, PV |
| IA32_HWP_REQUEST | MIN_PERF, MAX_PERF, DESIRED | OS request | HWP frequency request | FV, PV |
| IA32_PERF_CTL | TARGET_RATIO | OS request | Legacy P-state ratio | FV, PV |
| LEAF_PERF_STATUS | CURRENT_RATIO | HW | Actual running frequency | FV, PSS, PV |

### Observability

| Observable | Type | Tool / Command | What It Shows |
|---|---|---|---|
| MSR_PKG_PERF_STATUS | MSR | `rdmsr 0x613` / PythonSV | Active throttle reason (RAPL, RACL, thermal) |
| RAPL energy counters | MSR | `turbostat` / PythonSV | Power consumption tracking |
| LEAF_PERF_STATUS | Register | PythonSV namednodes | Current frequency per core |
| PLR (Perf Limit Reasons) | TPMI | PythonSV | Active limiter identification |
| Sideband trace | ITH T2 | TraceCLI VISA capture | Sideband signal injection/response |
| C-state residency | MSR | `turbostat` / PythonSV | Core and package C-state time |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs Affected |
|---|---|---|
| NWP with RACL fused ON | Full RAPL + RACL cross-product | All |
| NWP with RACL fused OFF | RAPL-only cross-product (RACL tests skipped) | 16031172977 (Security x RACL TC) |
| Single-partition config | RACL partition interaction not testable | 16031172977 |
| Multi-partition config | Full cross-partition arbitration testable | All |
| PkgC6 fused OFF (all NWP) | No PkgC6 cross-products | 16031172977 (Security x PC6 TC is ZBB) |
| Platform RAPL fused OFF (all NWP) | No Psys cross-products | 16031172977 (Security x Platform RAPL reduced scope) |
| DRAM RAPL fused OFF (all NWP) | No DRAM RAPL cross-products | 16031172977 (Security x DRAM RAPL TC may be N/A) |
| No IMH-side DVFS on NWP | All DVFS references = CBB Core GV only | 16031172978, 16031172980, 16031172981, 16031172982 |

### Agent Source Ownership

| Layer / Agent | Key Artifact (source file / FAS) |
|---|---|
| PMX Stress Tool | PMX tool binary (validation tool — external to firmware) |
| Solar PM Random | Solar PM generator (validation tool — external) |
| Sideband Harasser | SB Harasser tool (validation infrastructure) |
| PCode RAPL | PrimeCode `src/flow/rapl/` (RAPL PID loop) |
| PCode RACL | PrimeCode `src/ip/racl/` (current limit enforcement) |
| PCode DVFS | PrimeCode `src/flow/dispatcher/` (frequency arbitration) |
| PCode C-state | PrimeCode `src/flow/pkgc/` + `src/ip/cstate/` |
| HPM Messages | PrimeCode `src/ip/hpm/` (CBB↔IMH protocol) |
| BIOS Config | BIOS RAPL/RACL knob programming |

### Microarch→Scenario Coverage Matrix

| # | Element (from §2) | Category | Implied WHAT | Realized as TCD | TC(s) | Tier | Status |
|---|---|---|---|---|---|---|---|
| 1 | C-state × HWP × Core GV random | Cross-feature stress | No hang/MCA; freq converges to HWP_CAP band after stimulus | 16031172978 | 22022421701-06 | FV | ✓ |
| 2 | C-state × legacy P-state × Core GV random | Cross-feature stress | Legacy P-state correctly arbitrated under C-state churn | 16031172980 | 22022421709-14 | FV | ✓ |
| 3 | Isolated C-state × Core GV | Isolated interaction | C-state change has no impact on GV request completion | 16031172981 | 22022421715, 17 | FV | ✓ |
| 4 | Isolated P-state × Core GV | Isolated interaction | Final V/F matches resolved P-state/GV target | 16031172982 | 22022421718, 19 | FV | ✓ |
| 5 | iMH GPSB/PMSB endpoint sweep | Register boundary | All iMH PM endpoints accessible and respond correctly | 22022421311 | 22022423123, 25 | FV | ✓ |
| 6 | CBB GPSB/PMSB endpoint sweep | Register boundary | All CBB PM endpoints accessible and respond correctly | 16031172974 | 22022423121, 22 | FV | ✓ |
| 7 | PMX Security × Socket RAPL | Security cross-product | RAPL enforcement persists with energy fuzzing active | 16031172977 | 22022421700 | FV | ✓ |
| 8 | PMX Security × RACL | Security cross-product | RACL enforcement persists with energy fuzzing active | 16031172977 | 22022421698 | FV | ✓ |
| 9 | PMX Security × PC6 | Security cross-product | **ZBB on NWP** — PkgC6 not supported | 16031172977 | 22022421695 | FV | ❌ ZBB |
| 10 | PMX Security × DRAM RAPL | Security cross-product | **May be fused off on NWP** — verify fuse state | 16031172977 | 22022421691 | FV | ⚠️ PARTIAL |
| 11 | Sideband harasser × CBB DVFS | Layer interface | PM transitions complete under SB congestion | 16031172983 | 22022423114 | FV | ✓ |
| 12 | Sideband harasser × PEGA C-states | Layer interface | C-state Q-ch handshake survives SB stress | 16031172983 | 22022423116 | FV | ✓ |
| 13 | Sideband harasser × Solar C/P-states | Layer interface | Random PM transitions robust under SB congestion | 16031172983 | 22022423117, 19 | FV | ✓ |
| 14 | PSS Memory PM ZBB negative | Negative validation | ZBB features confirmed disabled; no activation on trigger | 16031172984 | 16030715653 | PSS | ✓ |
| 15 | PSS Sideband Harasser | Firmware validation | SB harasser start/stop cycle without hang in simulation | 16031172984 | 16030715718 | PSS | ✓ |
| 16 | HPM message loss under sideband stress | Cross-die interface | CBB desired ratio reaches IMH under bus contention | GAP | — | PSS (XOS), FV | ⚠️ GAP |
| 17 | RAPL limit change during active throttle | FSM state transition | PL1/PL2 change propagates without frequency discontinuity | GAP | — | FV, PSS | ⚠️ GAP |
| 18 | Reset during active cross-product stress | Reset interaction | Warm reset during PMX stress completes cleanly | GAP | — | FV | ⚠️ GAP |

---

## Section 3: Validation Strategy

PM Integration Testing uses a three-tier approach to maximize cross-product interaction coverage:

**PSS (Pre-Silicon Simulation):**
- **VP (Simics):** Validates firmware logic for RAPL/RACL arbitration under simulated multi-core scenarios. Safe for destructive/negative tests (invalid BIOS configs, limit boundary violations).
- **HSLE (single-die RTL):** Validates within-die PCode RAPL/RACL logic, frequency arbitration correctness.
- **XOS (both-die RTL):** **Mandatory** for sideband harasser and HPM message validation — these require full CBB↔IMH interaction.

**FV (Post-Silicon Functional Validation):**
- Primary tier for cross-product stress. PMX and Solar tools run directly on NWP silicon with PythonSV control.
- Real power/frequency measurement validates RAPL PID behavior and RACL enforcement under actual silicon conditions.
- Sideband harasser exercises real platform sideband paths.

**PV (Platform Validation):**
- OS-level validation: `turbostat`, `intel_pstate` driver behavior under cross-product workloads.
- Indirect observation of PM integration health through performance counters and thermal telemetry.

> **Layer coverage:** See §2 — Validation-Tier Layer Claim table for which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|---|---|---|---|---|---|
| RAPL PID arbitration logic bug | ✅ | ✅ | ✅ | ✅ | indirect |
| RACL per-partition enforcement bug | ✅ | ✅ | ✅ | ✅ | indirect |
| Cross-die HPM message ordering bug | ❌ | ❌ | ✅ | ✅ | indirect |
| Sideband signal race condition | ❌ | ⚠️ | ✅ | ✅ | ❌ |
| C-state exit storm power spike | ❌ | ⚠️ | ✅ | ✅ | indirect |
| Frequency arbitration priority inversion | ✅ | ✅ | ✅ | ✅ | indirect |
| Telemetry / PLR reporting mismatch | ✅ | ❌ | ✅ | ✅ | ✅ |
| Reset during stress hang | ❌ | ❌ | ⚠️ | ✅ | ❌ |
| Real power/frequency convergence | ❌ | ❌ | ❌ | ✅ | ✅ |
| OS driver interaction bug (intel_pstate) | ❌ | ❌ | ❌ | ❌ | ✅ |

### Scenario Coverage Across Tiers

| Scenario | PSS (VP) | PSS (XOS) | FV | PV | Unique Value |
|---|---|---|---|---|---|
| PMX directed cross-product stress | ✅ | ✅ | ✅ | ❌ | Deterministic, repeatable stress on known PM flows |
| Solar random PM events | ❌ | ⚠️ | ✅ | ❌ | Uncovers rare corner-case timing bugs |
| Sideband harasser injection | ❌ | ✅ | ✅ | ❌ | Validates robustness against platform noise |
| Multi-domain concurrent RAPL+RACL+HWP | ✅ | ✅ | ✅ | indirect | Arbitration correctness under load |
| Endpoint sweep under stress | ❌ | ❌ | ✅ | ❌ | Real silicon register accessibility |

---

## Section 5: Risks & Dependencies

### Active Risks

- **R-1: Tool maturity on NWP.** PMX and Solar tools may need NWP-specific configuration tuning compared to prior programs. Validation blocked until tool BKC for NWP is available.
- **R-2: Sideband harasser coverage.** SB Harasser tool requires NWP-specific sideband signal definitions — coverage depends on platform team delivering signal maps.
- **R-3: RACL fuse gating.** If early NWP steppings have RACL fused off, RACL cross-products are untestable until RACL-enabled parts arrive.
- **R-4: XOS model availability.** Full cross-die HPM + sideband scenarios require XOS environment — availability may lag behind VP/HSLE.

### Accepted Coverage Limitations (by design — no new TCs required)

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | PkgC6 cross-products | N/A | PkgC6 fused off on all NWP — feature not present |
| **G-2** | Platform RAPL (Psys) cross-products | N/A | Psys fused off on NWP — feature not present |
| **G-3** | DRAM RAPL cross-products | N/A | DRAM RAPL fused off on NWP — feature not present |
| **G-4** | Real power measurement accuracy in PSS | FV only | VP/HSLE cannot model real power delivery — inherent |

---

## Section 6: DFX Considerations

- **ITH T2 / VISA Sideband Trace:** Required for observing sideband harasser signal injection and PM state machine response. Capture domain: OOBMSM/Sideband subsystem.
- **RAPL Debug Counters:** PCode RAPL debug counters must be enabled for post-mortem analysis of throttle events during stress.
- **PLR (Perf Limit Reasons):** TPMI-based PLR registers provide limiter identification — critical for cross-product root cause when multiple limiters are active.
- **C-state Residency Counters:** MSR-based residency counters validate C-state behavior during stress — useful for diagnosing C6 exit storm effects.
- **Firmware Trace (fw_trace):** PrimeCode firmware trace output aids diagnosis of RAPL/RACL/DVFS arbitration sequence under stress.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| Simultaneous C6 exit on all cores (power spike) | 16031172978, 16031172980 | RAPL PID responds within SLA; no overcurrent damage |
| RACL limiter in one partition + RAPL limiter in another | 16031172977 | Each partition throttled by its most restrictive limiter |
| Sideband harasser during C-state entry handshake | 16031172983 | Q-channel handshake completes or cleanly aborts; no hang |
| Rapid PL1/PL2 toggling during active throttle | 16031172977 | RAPL PID adapts without frequency discontinuity or overshoot |
| HWP MIN > RAPL-allowed ceiling | 16031172978 | Actual frequency clamped to RAPL ceiling (HWP MIN not guaranteed) |
| Legacy P-state request during RACL throttle | 16031172980 | P-state request clipped by active RACL limit |
| Endpoint register read during PM transition | 22022421311, 16031172974 | Register access completes without hang or corruption |
| Reset during active cross-product stress | All | Clean reset completion; no residual PM state corruption |
| Energy fuzzing + active RAPL throttle | 16031172977 | RAPL enforcement persists despite fuzzed telemetry |
| PkgC6 security cross-product on NWP | 16031172977 | **ZBB** — TC 22022421695 not applicable |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Segment | Owner | Status |
|---|---|---|---|---|
| [22022421311](https://hsdes.intel.com/appstore/article/#/22022421311) | iMH PM EndPoint Sweep | server | thangama | open |
| [16031172974](https://hsdes.intel.com/appstore/article/#/16031172974) | CBB PM EndPoint Sweep | server | thangama | open |
| [16031172977](https://hsdes.intel.com/appstore/article/#/16031172977) | PMX Security cross product | server | thangama | open |
| [16031172978](https://hsdes.intel.com/appstore/article/#/16031172978) | Solar C-state x HWP x Core GV Random Stress | server | thangama | open |
| [16031172980](https://hsdes.intel.com/appstore/article/#/16031172980) | Solar C-state x Legacy P-state x Core GV Random Stress | server | thangama | open |
| [16031172981](https://hsdes.intel.com/appstore/article/#/16031172981) | Solar Isolated C-state Entry Exit Under Core GV | server | thangama | open |
| [16031172982](https://hsdes.intel.com/appstore/article/#/16031172982) | Solar Isolated P-state HWP Frequency Selection | server | thangama | open |
| [16031172983](https://hsdes.intel.com/appstore/article/#/16031172983) | SB Harasser Robustness During PM Transitions | server | thangama | open |
| [16031172984](https://hsdes.intel.com/appstore/article/#/16031172984) | PSS Negative test content | server | thangama | open |

### Dissolved TCDs (rejected after T2 restructure 2026-07-20)

| TCD ID | Former Title | Reason |
|---|---|---|
| [22022420633](https://hsdes.intel.com/appstore/article/#/22022420633) | Solar Cross Products | Dissolved: violated one-WHAT rule; TCs split to 4 new TCDs |
| [22022421309](https://hsdes.intel.com/appstore/article/#/22022421309) | Cross Products | Dissolved: clubbed SB-harasser + misplaced TCs; active TCs moved to 16031172983 |

### References

- [NWP PM HAS — RAPL / RACL / DVFS sections](https://hsdes.intel.com) (Co-Design project: NWP)
- [TPF 22022562325 — PM Integration Testing](https://hsdes.intel.com/appstore/article/#/22022562325)
- [TP 16030765631 — [NWP PM] PM Cross Product](https://hsdes.intel.com/appstore/article/#/16030765631)
- Co-Design T2 enrichment query: NWP PM cross-product stress testing methodology (2026-07-20)
- Co-Design T2 enrichment query: RAPL/RACL/PC6/HWP interaction bug classes (2026-07-20)
