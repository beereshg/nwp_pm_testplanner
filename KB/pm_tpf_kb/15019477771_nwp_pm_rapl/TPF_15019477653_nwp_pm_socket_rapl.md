# TPF 15019477653 — [NWP PM] Socket RAPL

| Field | Value |
|-------|-------|
| **TPF ID** | [15019477653](https://hsdes.intel.com/appstore/article-one/#/15019477653) |
| **Title** | [NWP PM] Socket RAPL |
| **Parent TP** | [15019477771 — [NWP PM] RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477771) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Feature Classification & Introduction

**Socket RAPL (Running Average Power Limit)** is the primary power-limiting feature on NWP. It enforces package-level power limits (PL1 / PL2) across all socket components — both CBB compute dies and the NIO root die — using closed-loop **NN-PID (Neural Network PID)** control implemented in PrimeCode firmware.

**Classification**: Firmware-heavy feature with silicon enforcement. The NN-PID algorithm runs entirely in PrimeCode on the NIO root die; hardware enforcement is delegated to CBB PCode via HPM messaging; silicon provides power telemetry (SVID IMON) and frequency ceiling enforcement.

**Gating mechanism**: Socket RAPL is **always active** on NWP — no fuse or BIOS knob gates the feature. Power limits are initialized from fused TDP values (PL1 = TDP, PL2 = 1.2×TDP) and can be adjusted at runtime via TPMI.

**NWP scope**: Socket RAPL (PL1/PL2) is the **only active RAPL domain** on NWP. DRAM RAPL is fused off ([14025012732](https://hsdes.intel.com/appstore/article-one/#/14025012732)), Platform RAPL/Psys is ZBB ([22021155415](https://hsdes.intel.com/appstore/article-one/#/22021155415)), SIMPL is ZBB, and RACL is ZBB (single VCCIN — no per-VR current limiting needed). FastRAPL (500 µs loop) is supported as part of the Socket RAPL pipeline.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| Active RAPL PIDs | 9 (Socket PL1×2, PL2×2, Platform PL1×2, PL2×2, FastRAPL×1) | DMR IMH PM HAS §7.3 |
| CBB count | 2 (cbb0, cbb1) | NWP topology |
| Root die | NIO (`sv.socket0.nio.punit.*`) | NWP PM MAS |
| PL1 default | Fused TDP | DMR PM HAS |
| PL2 default | 1.2 × Fused TDP | DMR PM HAS |
| PL2 PID target | 0.9 × PL2 field | DMR PM HAS |
| PID slow loop rate | 1 ms | DMR NNPID HAS |
| FastRAPL loop rate | 500 µs | DMR NNPID HAS |
| PL1 τ range | 1–5 s (clipped) | DMR IMH PM HAS |
| PL2 τ range | 11.7–39 ms (clipped) | DMR IMH PM HAS |
| Max TDP | 450 W | NWP PM MAS §3 |
| Nominal TDP | 350 W | NWP PM MAS §3 |
| Legacy MSRs | 0x610/0x611/0x606 — deprecated (reads=0, writes=no-op) | DMR PM HAS §5.2 |
| Energy unit | U11.3 format (1 LSB = 0.125 W) | DMR TPMI HAS |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:12px;font-family:Arial,sans-serif;max-width:700px">
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 5: OS / Tool / BMC</strong><br/>
    <small>intel_rapl driver · turbostat · BMC/NM via PECI-over-MCTP · TPMI sysfs</small>
  </div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 4: BIOS / UEFI Configuration</strong><br/>
    <small>CSR PKG_RAPL_LIMIT programming · TPMI OSXML defaults · LOCK policy</small>
  </div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 3: PrimeCode NN-PID Control (NIO Root)</strong><br/>
    <small>9 NN-PID controllers · EWMA smoothing · min-resolution · HPM 0x14 distribution</small>
  </div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 2: CBB PCode Enforcement</strong><br/>
    <small>Frequency ceiling enforcement · PERF_STATUS accounting · fast_throttle assertion · HPM 0x16 feedback</small>
  </div>
  <div style="background:#FF0000;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 1: Silicon / HW Telemetry</strong><br/>
    <small>SVID IMON current measurement · VR telemetry · D2D/UCIe HPM transport · TPMI SRAM</small>
  </div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| L5: OS / Tool / BMC | ❌ | ❌ | ❌ | ❌ | ✅ | Requires booted OS + intel_rapl driver / turbostat |
| L4: BIOS / UEFI Configuration | ✅ safe | ❌ | ❌ | ✅ | ✅ | VP is the only safe environment for BIOS negative tests |
| L3: PrimeCode NN-PID Control | ✅ | ✅ | ✅ | ✅ | indirect | All tiers validate firmware logic |
| L2: CBB PCode Enforcement | ✅ | ✅ | ✅ | ✅ | indirect | Within-die PCode logic + cross-die HPM protocol |
| L1: Silicon / HW Telemetry | ❌ | ⚠️ | ⚠️ | ✅ | indirect | Real SVID telemetry only on silicon; HSLE/XOS model approximation |

### Socket RAPL Boot / Reset Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Cold Boot                                                                   │
│                                                                             │
│  PH1-PH5: Silicon init, fuse reads                                         │
│    └─ PrimeCode reads RAPL capability fuses (TDP, MIN_PWR, MAX_PWR)        │
│    └─ PrimeCode populates TPMI PL_INFO (MAX_PL1=TDP, MAX_PL2=1.2×TDP)     │
│                                                                             │
│  PH6: Runtime initialization                                               │
│    └─ PrimeCode initializes NN-PID controllers (9 instances)               │
│    └─ Default: PL1=TDP, PL2=1.2×TDP, PL1_τ=1s, PL2_τ=12ms               │
│    └─ NN-PID weights initialized (Kp=maxNodeWeight for RACL)              │
│    └─ FastRAPL: extra VRCI telemetry sampling for prev_ init              │
│                                                                             │
│  BIOS CPL3:                                                                │
│    └─ BIOS reads PL_INFO to discover valid PL range                       │
│    └─ BIOS programs CSR PKG_RAPL_LIMIT (PL1, PL2, τ, LOCK)              │
│    └─ BIOS programs TPMI OSXML defaults                                   │
│    └─ BIOS may assert LOCK bit before OS handoff                          │
│                                                                             │
│  Runtime (1 ms loop):                                                      │
│    └─ NIO PrimeCode reads SVID IMON telemetry → actual power              │
│    └─ NN-PID computes error = PL_target − actual_power                    │
│    └─ Generates RAPL_PID_FREQ_OUTPUT per controller                       │
│    └─ RAPL_PERF_LIMIT = min(all active controller outputs)                │
│    └─ Sends HPM 0x14 → CBB0, CBB1                                        │
│    └─ If output < Pm → asserts fast_throttle (clock div + arch throttle)  │
│    └─ CBBs enforce freq ceiling, report LEAF_PERF_STATUS via HPM 0x16     │
│    └─ NIO aggregates status → updates TPMI PERF_STATUS                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ Warm Reset                                                                  │
│    └─ NN-PID state re-initialized at PH6                                   │
│    └─ ENERGY_STATUS NOT reset (monotonic across warm reset)                │
│    └─ BIOS re-programs PL1/PL2 at CPL3                                    │
│    └─ HPM messaging resumes with fresh RAPL_PERF_LIMIT at PH6 exit       │
│    └─ No stale limit persists after reset                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Socket RAPL Architecture Block (NN-PID Control Loop)

```
                 ┌─────────────────────────────────────────────────────────────┐
                 │                        Socket                               │
   BIOS ──CSR───►│  ┌──────────┐  HPM 0x14   ┌──────────┐                    │
   OS ──IN_TPMI─►│  │ NIO      │────────────►│ CBB0     │                    │
   BMC ──OOB────►│  │(Primecode│             │(PCode)   │                    │
                 │  │ Root)    │  HPM 0x14   │freq ceil  │                    │
                 │  │ PID×9    │────────────►│fast_throttle                   │
                 │  │ NN-PID   │             ├──────────┐                    │
                 │  │          │◄────────────│ CBB1     │                    │
                 │  │ min()    │ HPM 0x16    │(PCode)   │                    │
                 │  │ resolve  │◄────────────│freq ceil  │                    │
                 │  └─────┬────┘ LEAF_PERF   │fast_throttle                   │
                 │        │ IMON             └──────────┘                    │
   VR ──SVID────►│        ▼                                                  │
                 │   ┌─────────┐                                              │
                 │   │  Power  │ actual_power → NN-PID error computation      │
                 │   │ Telemetry│                                              │
                 │   └─────────┘                                              │
                 └────────────────────────────────────────────────────────────┘
```

### NN-PID Neural Network Architecture

```
Input Layer              PID Layer                Output Layer
┌──────────┐        ┌──────────────────┐        ┌──────────┐
│ Normalize │──Ws1──►│ P(n) = f(NT·Ws1  │        │          │
│  (NT)     │──Ws2──►│       + FB·Wf1)  │──Kp───►│  Sum +   │
│           │──Ws3──►│                  │        │  Smooth  │──► Output
│ Feedback  │──Wf1──►│ I(n) = ∫(NT·Ws2  │──Ki───►│  (EWMA)  │   (freq
│  (FB)     │──Wf2──►│       + FB·Wf2)  │        │          │    ratio)
│           │──Wf3──►│ D(n) = Δ(NT·Ws3  │──Kd───►│ Learning │
│           │        │       + FB·Wf3)  │        │  State   │
└──────────┘        └──────────────────┘        └──────────┘
     ▲                                                │
     └──── Backpropagation (weight update) ◄──────────┘
```

**EWMA Input Smoothing**: $f_{smooth}(x_i) = \alpha \cdot x_{i-1} + (1-\alpha) \cdot x_i$ where $\alpha = e^{-t_{period}/\tau}$

### Frequency Hierarchy

| Level | Value | Notes |
|---|---|---|
| P0max | Max turbo frequency | SKU-dependent; highest achievable |
| P01 | 1-core turbo | SST-TF / PCT profile dependent |
| P0n | N-core turbo | Scales with active core count |
| P1 | Guaranteed (base) frequency | All-core sustainable |
| Pn | Minimum operating frequency | Lowest non-zero frequency |
| Pm | Minimum power frequency | Below Pm → fast_throttle (clock div + arch throttle) |
| RAPL_PID_FREQ_OUTPUT | NN-PID resolved ceiling | min(all 9 active controller outputs); distributed via HPM 0x14 |

### Interface & Register Matrix

| Register / MSR | Interface | Access | Key Fields | Feature Effect | Tier Validated |
|---|---|---|---|---|---|
| PL1_CONTROL (TPMI idx=2) | IN_TPMI | RW_L | PWR_LIM [17:0], TIME_WINDOW [24:18], LOCK [63] | Sets Socket RAPL PL1 target | PSS, FV, PV |
| PL2_CONTROL (TPMI idx=3) | IN_TPMI | RW_L | PWR_LIM [17:0], TIME_WINDOW [24:18], LOCK [63] | Sets Socket RAPL PL2 target | PSS, FV, PV |
| PL_INFO (TPMI idx=9) | IN_TPMI | RO | MAX_PL1 [17:0]=TDP, MIN_PL [35:18], MAX_PL2 [53:36] | Capability discovery — fuse-sourced | PSS, FV |
| ENERGY_STATUS (TPMI idx=7) | IN_TPMI | RO_V | ENERGY [31:0] (U11.3, monotonic), TIME [63:32] (10ns) | Power measurement — fuzzed if MSR 0xBC.bit0=1 | FV, PV |
| PERF_STATUS (TPMI idx=8) | IN_TPMI | RO_V | PWR_LIMIT_THROTTLE_CTR [31:0] | Throttle accounting | FV, PV |
| POWER_UNIT (TPMI idx=1) | IN_TPMI | RO | PWR_UNIT [3:0], ENERGY_UNIT [10:6], TIME_UNIT [15:12] | Unit encoding discovery | FV |
| PKG_RAPL_LIMIT | CSR | RW_L | PKG_PWR_LIM_1/2, TIME, LOCK | BIOS boot-time programming; locked before OS handoff | FV |
| MSR 0x610 (deprecated) | MSR | Drop/0 | — | Writes=no-op, Reads=0 on NWP | FV (negative) |
| MSR 0x611 (deprecated) | MSR | Drop/0 | — | Reads=0 on NWP | FV (negative) |
| MSR 0x606 (deprecated) | MSR | Drop/0 | — | Reads=0 on NWP | FV (negative) |
| MSR 0xBC | MSR | RW | ENERGY_FILTERING_ENABLE [0] | Controls energy fuzzing — NOT deprecated | FV |
| HPM 0x14 | HPM | FW | RAPL_PID_FREQ_OUTPUT [63:56], PLR flags [44:32], FIVR_INPUT_VOLTAGE [31:16] | NIO→CBB performance ceiling distribution | PSS (XOS), FV |
| HPM 0x16 | HPM | FW | SOCKET_RAPL_PERF_STATUS [47:32], PLATFORM_RAPL_PERF_STATUS [63:48] | CBB→NIO throttle status feedback | PSS (XOS), FV |
| OOB TPMI | PECI-over-MCTP | RW | Same as IN_TPMI registers | BMC/NM access to Socket RAPL | FV |

### Observability

| Observable | Type | Tool / Command | What It Shows |
|---|---|---|---|
| TPMI ENERGY_STATUS | Register (RO_V) | `sv.socket0.nio.punit.tpmi.socket_rapl.energy_status.read()` | Accumulated energy (J) and timestamp |
| TPMI PERF_STATUS | Register (RO_V) | `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status.read()` | Throttle time counter; fine/coarse reason bits |
| TPMI PL_INFO | Register (RO) | `sv.socket0.nio.punit.tpmi.socket_rapl.pl_info.read()` | Fused capability: MAX_PL1, MIN_PL, MAX_PL2 |
| TPMI PL1/PL2_CONTROL | Register (RW_L) | `sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control.show()` | Current power limit, time window, lock status |
| NN-PID Internal State | FW debug buffer | PrimeCode SRAM debug buffer via PythonSV | PID weights, error, output per iteration |
| ITH Trace (NPK) | Trace | TraceCLI / NPK capture | RAPL limit changes, throttling events, power telemetry |
| PLR (Perf Limit Reasons) | Register | TPMI PERF_STATUS reason fields | 1-hot priority: PlatPL2 > PlatPL1 > FastRAPL > SktPL2 > SktPL1 |
| turbostat | OS tool | `turbostat --show PkgWatt,PkgTmp,Busy%,Bzy_MHz` | Package power, effective frequency under RAPL |
| SVID IMON | VR telemetry | SVID polling by PrimeCode | Real-time current measurement — PID input signal |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs Affected |
|---|---|---|
| TDP fuse value | Determines PL1 default and PL2 = 1.2×TDP; different per SKU | All (especially Fuse/BIOS TCD) |
| LOCK bit policy | BIOS may or may not lock PL1/PL2 before OS handoff; affects runtime modifiability | Registers TCD, Algorithm TCD |
| IB_WRITE_BLOCK / IB_READ_BLOCK | TPMI access control bits — can restrict inband TPMI to RO or CSR-only | Registers TCD, OOB TCD |
| Energy fuzzing (MSR 0xBC.bit0) | When set, ENERGY_STATUS values are fuzzed; affects validation comparison accuracy | Registers TCD, Cross-products (Security) |
| NWP 2-CBB topology | Only 2 CBBs vs DMR 4 — HPM distribution scope reduced | HPM TCD, Algorithm TCD |
| FastRAPL enable | 500 µs fast loop for IO power limiting — may or may not be active depending on platform config | Algorithm TCD, Cross-products TCD |

### Agent Source Ownership

| Layer / Agent | Key Artifact (source file / FAS) |
|---|---|
| PrimeCode (NIO Root) — NN-PID | `src/flow/rapl/` — `sendRaplPerfLimit`, `distributeRaplPerfLimitHpm`, `raplHpmSocketRaplRcvPerfStatusHandler` |
| PrimeCode — NN-PID mathutils | `src/shared/mathutils/` — NN-PID controller, EWMA, backpropagation |
| PCode (CBB) — enforcement | CBB PM HAS §6.4 — HPM handlers 0x14/0x16, PERF_STATUS incrementer, fast_throttle |
| Acode (Core) — WP response | PNC PM HAS §7 — `GO_INC_GB_ELEC` handler, fast_throttle response |
| BIOS/UEFI — boot config | DMR BIOS Spec — B2P WRITE_PCU_MISC_CONFIG, CSR programming |
| OOBMSM — OOB path | DMR IMH PM HAS §8.2 — TPMI endpoint, Primary→Sideband LTM translation |

---

## Section 3: Validation Strategy

Socket RAPL validation requires a **three-tier strategy** (PSS / FV / PV) because the feature spans firmware (NN-PID algorithm), hardware (SVID telemetry, frequency enforcement), cross-die communication (HPM), and OS/tool interfaces (TPMI, intel_rapl driver).

Layer coverage is mapped in §2 — the Validation-Tier Layer Claim table identifies which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

### Tier Definitions

| Tier | Environment | Interface | What It Validates |
|---|---|---|---|
| PSS — VP (Simics) | Virtual platform | PythonSV → TPMI model | Firmware logic paths, BIOS flows, NN-PID algorithm, safe negative testing (invalid PL values, lock violations) |
| PSS — HSLE | Single-die RTL | PythonSV → TPMI RTL | Within-die PCode enforcement logic, PERF_STATUS accounting, fast_throttle assertion |
| PSS — XOS | Both-die RTL (NIO+CBB) | PythonSV → full RTL | Cross-die HPM protocol (0x14/0x16), end-to-end RAPL_PERF_LIMIT delivery and feedback |
| FV | Post-silicon NWP | PythonSV → namednodes | Real SVID telemetry, real frequency enforcement, NN-PID convergence with real power, register interface verification |
| PV | Post-silicon NWP + Ubuntu | intel_rapl / turbostat / sysfs | OS/driver layer validation, E2E user-visible power limiting capability, turbostat correlation |

### Why All Tiers Are Needed

- **PSS** validates firmware correctness (NN-PID algorithm, HPM messaging, edge cases) without risking silicon — VP is the only safe environment for BIOS negative testing
- **FV** validates real silicon behavior: actual SVID telemetry accuracy, real frequency enforcement, NN-PID convergence quality with real power curves, and register interface correctness
- **PV** validates the OS-visible experience: intel_rapl driver integration, turbostat power reporting accuracy, and BMC/NM OOB access paths

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|---|---|---|---|---|---|
| NN-PID algorithm bug (wrong Kp/Ki/Kd, convergence failure) | ✅ | ❌ | ✅ | ✅ | indirect |
| NN-PID weight initialization bug (RACL false trigger pattern) | ✅ | ❌ | ✅ | ✅ | indirect |
| HPM 0x14 delivery failure (RAPL_PERF_LIMIT not reaching CBB) | ❌ | ❌ | ✅ | ✅ | indirect |
| HPM 0x16 feedback failure (LEAF_PERF_STATUS not returned) | ❌ | ❌ | ✅ | ✅ | indirect |
| CBB PCode enforcement bug (freq ceiling not applied) | ❌ | ✅ | ✅ | ✅ | indirect |
| fast_throttle assertion bug (below-Pm behavior) | ❌ | ✅ | ✅ | ✅ | indirect |
| TPMI register access bug (wrong field encoding, lock violation) | ✅ | ❌ | ❌ | ✅ | ✅ |
| Deprecated MSR behavior bug (reads≠0 or writes not dropped) | ✅ | ❌ | ❌ | ✅ | ❌ |
| SVID IMON telemetry error (wrong address, stale data) | ❌ | ❌ | ❌ | ✅ | indirect |
| ENERGY_STATUS counter bug (non-monotonic, wrong unit) | ❌ | ⚠️ | ⚠️ | ✅ | ✅ |
| BIOS negative validation (invalid PL, out-of-range τ) | ✅ safe | ❌ | ❌ | ❌ risky | ❌ |
| OS driver bug (intel_rapl / turbostat misreporting) | ❌ | ❌ | ❌ | ❌ | ✅ |
| OOB/BMC access path bug (PECI-over-MCTP inconsistency) | ❌ | ❌ | ❌ | ✅ | ✅ |
| Cross-product interaction bug (RAPL×Prochot, RAPL×Pmax) | ✅ | ❌ | ✅ | ✅ | ❌ |
| Real-power convergence / TDP tracking accuracy | ❌ | ❌ | ❌ | ✅ | ✅ |
| D2D/UCIe link integrity affecting HPM transport | ❌ | ❌ | ✅ | ✅ | indirect |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique Value |
|---|---|---|---|---|
| Cold boot TDP defaults (PL_INFO validation) | ✅ | ✅ | ✅ | FV: real fuse values; PV: OS-visible discovery |
| PL1 step response and settling time | ✅ | ✅ | ✅ | FV: real NN-PID convergence; PV: turbostat validation |
| PL2 burst and settling | ✅ | ✅ | ✅ | FV: real power transients |
| Below-Pm throttling (fast_throttle) | ✅ | ✅ | ❌ | FV: real clock division + arch throttle |
| Runtime PL change and re-convergence | ✅ | ✅ | ✅ | PV: intel_rapl sysfs write → turbostat effect |
| ENERGY_STATUS monotonicity and accuracy | ⚠️ | ✅ | ✅ | FV: real energy accumulation |
| Deprecated MSR negative testing | ✅ | ✅ | ❌ | PSS: safe negative test env |
| HPM RAPL_PERF_LIMIT distribution to both CBBs | ❌ | ❌ | ❌ | FV: real cross-die messaging (XOS for pre-Si) |
| SVID IMON telemetry accuracy | ❌ | ❌ | ❌ | FV only: real VR telemetry |
| Cross-product: RAPL × Prochot / Pmax / Reset / SST | ✅ | ❌ | ❌ | FV: real multi-limiter coexistence |
| OOB PECI-over-MCTP access consistency | ❌ | ✅ | ✅ | FV: register consistency in-band vs OOB |
| BIOS knob negative testing (PL > MAX, out-of-range τ) | ✅ safe | ❌ | ❌ | VP only: safe for invalid programming |
| Energy fuzzing (MSR 0xBC.bit0) | ✅ | ✅ | ❌ | FV: real energy counter fuzzing |
| Warm reset RAPL recovery | ✅ | ✅ | ❌ | FV: real PID re-initialization + stale limit check |
| Frequency oscillation ≤ ±1 bin at steady state | ❌ | ❌ | ❌ | FV only: real frequency measurement |

---

## Section 5: Risks & Dependencies

### Active Risks

- **R-1: NN-PID tuning quality on NWP silicon** — NN-PID replaces classic PID; adaptive weights mean convergence behavior may differ from DMR. FV must validate PL1/PL2 response time and settling time meet spec (3–5×τ, <1% error).
- **R-2: NIO single-die RAPL coordination** — NWP uses a single NIO root (vs DMR dual-IMH). Any NIO-specific HPM routing or power aggregation difference could affect RAPL accuracy.
- **R-3: FastRAPL initialization** — FastRAPL VRCI telemetry needs extra sampling before first reading (HSD [22022442799](https://hsdes.intel.com/appstore/article-one/#/22022442799)). Incorrect init → stale prev_ values → inaccurate first PID cycle.
- **R-4: RACL init false trigger** — NN-PID Kp initialization must be set to maxNodeWeight at init to prevent false RACL trigger during CPL3 (HSD [22022367941](https://hsdes.intel.com/appstore/article-one/#/22022367941)).
- **R-5: D2D/UCIe link integrity** — HPM messages between NIO and CBBs traverse D2D links. Link instability could cause stale or dropped RAPL_PERF_LIMIT messages.

### Accepted Coverage Limitations (by design — no new TCs required)

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | Real SVID IMON telemetry accuracy | FV only | Silicon-level HW measurement; no pre-Si model can replicate real VR current sensing |
| **G-2** | Real-power NN-PID convergence quality | FV only | NN-PID adaptive weights depend on real workload + real power curves; model-based PID behaves differently |
| **G-3** | OS/driver layer (intel_rapl, turbostat) | PV only | Requires booted OS with full kernel driver stack |
| **G-4** | Frequency oscillation measurement (±1 bin) | FV only | Requires real frequency measurement hardware |
| **G-5** | Cross-die HPM transport over real D2D | FV only (XOS for pre-Si) | HSLE single-die cannot model cross-die HPM; VP model is simplified |
| **G-6** | Multi-socket Socket RAPL coordination | none | No bounded NWP multi-socket Socket RAPL requirement evidenced in HAS/MAS; NWP architecture is 2 CBBs under one NIO hierarchy [spec ref: dmr_rapl_simplification.html] |
| **G-7** | NWP CBB delta HAS for Socket RAPL | none (spec audit) | No NWP CBB delta excerpt retrieved for Socket RAPL; DMR RAPL HAS/CBB collateral path confirmed applicable [spec ref: Co-Design audit 2026-07-18] |

---

## Section 6: DFX Considerations

- **NN-PID Debug Buffer**: PrimeCode maintains a local SRAM debug buffer for all internal NN-PID variables (weights, error, output per iteration). Accessible via PythonSV mask interface with programmable triggers (min/max level, average over N samples, AND/OR, nth event).
- **ITH Trace Hub (NPK)**: RAPL limit changes, throttling events, and power telemetry can be instrumented to emit trace events to ITH. Per-socket channels allow isolated RAPL event analysis.
- **DFX Scratchpad Registers**: Used by firmware and validation teams to record RAPL-related debug state; accessible via U2P or OS mailbox.
- **Crashlog / ACD**: PrimeCode debug buffers can be extracted via crashlog or ACD flows for post-mortem RAPL analysis.
- **PMON Counters**: Socket RAPL exposes PMON counters for power, energy, and throttling events; can be routed to Trace Hub for high-resolution observability.
- **PMT (Platform Monitoring Technology)**: RAPL telemetry is standardized and available via PMT for polling or logged analysis.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| PL1 programmed > MAX_PL1 (fused TDP) | Fuse/BIOS (22022420813), Algorithm (22022420798) | PrimeCode clips to MAX_PL1; TPMI reflects clipped value |
| PL2 programmed < PL1 | Fuse/BIOS (22022420813), Algorithm (22022420798) | PrimeCode resolves conflict — PL2 should not be lower than PL1 |
| Time window outside valid range | Fuse/BIOS (22022420813), Algorithm (22022420798) | PrimeCode clips PL1 τ to [1s, 5s], PL2 τ to [11.7ms, 39ms] |
| LOCK bit set — runtime write attempt | Registers (22022420821) | Write rejected; TPMI value unchanged |
| Deprecated MSR write to 0x610 | Registers (22022420821) | Write silently dropped; no error, no effect |
| Deprecated MSR read from 0x611 | Registers (22022420821) | Returns 0 |
| ENERGY_STATUS rollover (32-bit wrap) | Registers (22022420821), Algorithm (22022420798) | Monotonic wrap; software must handle delta calculation |
| ENERGY_STATUS across warm reset | Registers (22022420821), Cross-products (22022420806) | NOT reset on warm reset — counter persists |
| fast_throttle below Pm | Algorithm (22022420798), HPM (22022420817) | Clock division + arch throttle asserted; both CBBs affected |
| HPM 0x14 not delivered (D2D link issue) | HPM (22022420817) | CBB holds last received limit; stale limit → incorrect enforcement |
| Simultaneous RAPL + Prochot throttle | Cross-products (22022420806) | Effective throttle = max restriction of both limiters |
| RAPL × Pmax coexistence | Cross-products (22022420806) | More restrictive limiter dominates |
| NN-PID output saturation | Algorithm (22022420798) | Learning disabled (inference only); anti-windup equivalent |
| IB_WRITE_BLOCK=1 (TPMI restricted to RO) | Registers (22022420821) | Inband writes rejected; CSR and OOB access only |
| SVID IMON address aliased to wrong domain | SVID (22022420826) | RAPL PID receives incorrect power signal; may over/under-throttle |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Segment | Key Scope |
|---|---|---|---|
| [22022420798](https://hsdes.intel.com/appstore/article-one/#/22022420798) | Socket RAPL Algorithm & Functionality Verification | FV/PSS | NN-PID control loop, PL1/PL2 enforcement, response time, fast_throttle |
| [22022420806](https://hsdes.intel.com/appstore/article-one/#/22022420806) | Socket RAPL Cross-products | FV | RAPL × Security/Core+IO/Reset/Pmax/Prochot/SST interactions |
| [22022420813](https://hsdes.intel.com/appstore/article-one/#/22022420813) | Socket RAPL Fuse and BIOS Knobs | FV | Fuse checkout (TDP, MAX_PL2, MIN_PL), BIOS knob programming, LOCK |
| [22022420817](https://hsdes.intel.com/appstore/article-one/#/22022420817) | Socket RAPL HPM Verification | FV | HPM 0x14/0x16 messaging, NIO→CBB distribution, LEAF_PERF_STATUS feedback |
| [22022420821](https://hsdes.intel.com/appstore/article-one/#/22022420821) | Socket RAPL Registers Verification — CSR and TPMI | FV | TPMI register interface, deprecated MSR negative testing, OOB access |
| [22022420826](https://hsdes.intel.com/appstore/article-one/#/22022420826) | Socket RAPL SVID Reporting Verification | FV | SVID IMON telemetry addressing, accuracy, ENERGY_STATUS correlation |

### Proposed New TCDs (Co-Design Gap Audit 2026-07-18)

| Proposed Title | Risk | Spec Ref | Scope |
|---|---|---|---|
| Socket RAPL - Negative / Boundary Validation | H | RAPL HAS — register programming, extended power-limit fields | Invalid PL1 > MAX_PL1, PL2 < PL1, out-of-range tau, LOCK violation attempt + recovery |
| Socket RAPL - State Transition / Recovery | H | RAPL HAS — register programming, HPM flows | PL change → reset → recovery, lock → unlock via reset, HPM re-sync sequence |
| Socket RAPL - NN-PID Tuning / Modes | H | RAPL HAS — PID clarifications, anti-windup, integral max-clipping | Learning vs inference-only, variable DT, saturation/anti-windup, weight initialization |
| Socket RAPL - FastRAPL Dedicated FV | H | RAPL HAS — FastRAPL anti-windup, common MRF flow, max-clipped integral | 500 µs IO power limiting, dedicated FV coverage beyond PSS TC 15734 |
| Socket RAPL - HPM Error Injection / Timing | H | RAPL HAS — HPM messaging for RAPL/RACL (IMH↔CBB) | HPM timing, delay, dropped message, degraded D2D link (HSLE XOS-specific) |
| Socket RAPL - Error Injection / Recovery | M | RAPL HAS — PM error-handling, programming/interface recovery | Invalid interface recovery, error injection paths |
| Socket RAPL - Below-Pm / Fast Throttle | H | RAPL HAS — FastRAPL/anti-windup/max-clipped-integral, below-min handling | **Created: [TCD 16031169418](https://hsdes.intel.com/appstore/article-one/#/16031169418)** — fast_throttle assertion when output < Pm, clock div + arch throttle, FastRAPL 500 µs loop (TC 22022421978 moved here) |

### References

- [NWP PM MAS — Major Changes from DMR](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#major-changes-from-dmr-product)
- [DMR IMH NNPID HAS v0.5](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/NNPID%20HAS/NNPID%20HAS.html) — NN-PID architecture, formulas, modes
- [Primecode mathutils — NN-PID FAS](https://docs.primecode.intel.com/master/mathutils.html#mathutils_overview_nnpid)
- [NN-PID Tuning & Validation BKM](https://intel-my.sharepoint.com/:w:/r/personal/ofri_seroussi_intel_com/_layouts/15/doc2.aspx?sourcedoc=%7BCFB64C3F-F951-4491-BE97-1E76224FB2EC%7D)
- DMR IMH PM HAS §7.3 — Socket RAPL architecture
- DMR CBB PM HAS §6.4 — PCode enforcement
- DMR TPMI HAS §4.2 — TPMI register definitions
- HSD [22022367941](https://hsdes.intel.com/appstore/article-one/#/22022367941) — RACL init false trigger
- HSD [22022442799](https://hsdes.intel.com/appstore/article-one/#/22022442799) — FastRAPL init fix
- HSD [14025012732](https://hsdes.intel.com/appstore/article-one/#/14025012732) — DRAM RAPL fused off on NWP
- HSD [22021155415](https://hsdes.intel.com/appstore/article-one/#/22021155415) — Platform RAPL ZBB on NWP
- [DMR RAPL Simplification HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_rapl_simplification.html) — Co-Design spec source
- [PM Features Index](https://docs.intel.com/documents/pm_doc/src/server/index.html) — Co-Design spec source
- Co-Design Gap Audit — 2026-07-18 (T1 coverage gap analysis, 14 findings)
