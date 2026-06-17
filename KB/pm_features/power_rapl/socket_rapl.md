# Power/RAPL > Socket RAPL

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing + topology (WW22.3 2026)
> **Parent**: [Power / RAPL](power_rapl_main.md)

## Baseline (DMR)

**What it does**: Socket RAPL (Running Average Power Limit) enforces package-level power limits (PL1/PL2) across all components within the socket — all CBB and IMH dies — using closed-loop NN-PID controllers.

**Topology**:
```
                 ┌─────────────────────────────────────────────────────────────┐
                 │                        Socket                               │
   BIOS ──CSR───►│  ┌──────────┐  HPM 0x14   ┌──────────┐  HPM 0x14  ┌───────┐│
   OS ──IN_TPMI─►│  │ IMH-P    │────────────►│ IMH-S    │───────────►│ CBB×4 ││
   BMC ──OOB────►│  │(Primecode│◄────────────│(Primecode│◄───────────│(PCode)││
                 │  │ Root)    │ SUB_SOCKET  │ Leaf)    │ HPM 0x16   │       ││
                 │  │ PID×9    │   ENERGY    │ RACL PID │ LEAF_PERF  │freq   ││
                 │  └─────┬────┘             └──────────┘ STATUS     │ceiling││
                 │        │ WP1/WP3                                  └───┬───┘│
   VR ──SVID────►│        ▼                                              │    │
                 │   ┌─────────┐                                  fast_throttle
                 │   │  Cores  │◄────────────────────────────────────────┘    │
                 └───┴─────────┴──────────────────────────────────────────────┘
```
- **IMH-P (Root)**: Runs 9 NN-PID controllers (Socket PL1×2, PL2×2, Platform PL1×2, PL2×2, FastRAPL×1), resolves min frequency
- **IMH-S (Leaf)**: Runs local RACL PID, forwards RAPL_PERF_LIMIT to CBBs
- **CBB**: PCode enforces frequency ceiling, reports LEAF_PERF_STATUS back to IMH

**Key operational principle**: PrimeCode implements NN-PID (Neural Network PID) controllers that adapt Kp/Ki/Kd weights online via backpropagation. Power telemetry (IMON via SVID) feeds the PIDs; the min-resolved output (RAPL_PID_FREQ_OUTPUT) is distributed via HPM to all CBBs, which enforce frequency ceilings on cores. If output < Pm, PCode asserts `fast_throttle` wire for clock division + arch throttle.

**Boot activation**: PH6 (Runtime) — BIOS programs CSR limits and locks; PrimeCode initializes NN-PID defaults (PL1=TDP, PL2=1.2×TDP); runtime control via TPMI.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| **PrimeCode / PMA** | IMH (Primary) | Runs NN-PID controllers for Socket/Platform/Fast RAPL; resolves min frequency; distributes limits | HPM RAPL_PERF_LIMIT (0x14), SUB_SOCKET_ENERGY, WP1/WP3 to Acode | DMR IMH PM HAS §7.3 |
| **PrimeCode / PMA** | IMH (Secondary) | Runs local RACL PID; forwards RAPL_PERF_LIMIT to CBBs; aggregates LEAF_PERF_STATUS | HPM 0x14→CBB, HPM 0x16←CBB | DMR IMH PM HAS §7.3 |
| **PCode / PUNIT** | CBB (×4) | Enforces frequency ceiling from RAPL_PID_FREQ_OUTPUT; increments PERF_STATUS counters; applies CLOS mapping | HPM 0x14 (recv), HPM 0x16 (send), fast_throttle wire | DMR CBB PM HAS §6.4 |
| **OOBMSM** | IMH | TPMI endpoint for BMC/NM OOB access; Primary→Sideband translation via LTM | OOB_TPMI, PECI-over-MCTP | DMR IMH PM HAS §8.2 |
| **MBVR / VR** | Platform | Voltage regulator provides IMON telemetry and FIVR_INPUT_VOLTAGE for energy measurement | SVID telemetry | DMR PM HAS §9 |
| **D2D / UCIe** | Inter-die | Carries HPM messages between IMH↔IMH, IMH↔CBB | HPM over D2D FDI | DMR D2D HAS |
| **Core Perimeter (ACP)** | CBB | Receives WP1/WP3 workpoints from PCode; applies frequency/Cdyn limits via Acode | WP1, WP3, GO_INC_GB_ELEC | PNC PM HAS §7 |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| **PrimeCode** | IMH-P (Root) | Runs all Socket/Platform/Fast RAPL NN-PID loops; computes min(PID outputs); distributes RAPL_PERF_LIMIT | `sendRaplPerfLimit`, `distributeRaplPerfLimitHpm`, `raplHpmSocketRaplRcvPerfStatusHandler` | Primecode RAPL flow |
| **PrimeCode** | IMH-S (Leaf) | Runs local RACL PID; combines with root limits; forwards to CBBs | `distributeRaplPerfLimitHpm`, RACL PID loop | Primecode RAPL flow |
| **PCode** | CBB | Receives RAPL_PERF_LIMIT; enforces freq ceiling on cores; reports LEAF_PERF_STATUS; increments throttle counters | HPM handlers 0x14/0x16, PERF_STATUS incrementer | DMR CBB PM HAS §6.4 |
| **Acode** | Core | Samples WP1/WP3; applies PVP threshold; responds to fast_throttle | `GO_INC_GB_ELEC` handler, fast_throttle response | PNC PM HAS §7 |
| **BIOS/UEFI** | Platform | Programs CSR PACKAGE_RAPL_LIMIT at boot; locks registers; sets B2P config | B2P WRITE_PCU_MISC_CONFIG, CSR programming | DMR BIOS Spec |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| **TPMI PL1_CONTROL** | TPMI_ID=0x00, idx=2 | RW_L | PWR_LIM [17:0], TIME_WINDOW [24:18], LOCK [63]. Primary OS interface for Socket RAPL PL1 | DMR TPMI HAS §4.2 |
| **TPMI PL2_CONTROL** | TPMI_ID=0x00, idx=3 | RW_L | PWR_LIM [17:0], TIME_WINDOW [24:18], LOCK [63]. Primary OS interface for Socket RAPL PL2 | DMR TPMI HAS §4.2 |
| **TPMI ENERGY_STATUS** | TPMI_ID=0x00, idx=7 | RO_V | ENERGY [31:0] (monotonic), TIME [63:32] (10ns units). Fuzzed if MSR 0xBC.bit0=1 | DMR TPMI HAS §4.2 |
| **TPMI PERF_STATUS** | TPMI_ID=0x00, idx=8 | RO_V | PWR_LIMIT_THROTTLE_CTR [31:0] — time spent throttled by RAPL | DMR TPMI HAS §4.2 |
| **TPMI PL_INFO** | TPMI_ID=0x00, idx=9 | RO | MAX_PL1 [17:0]=TDP, MIN_PL [35:18], MAX_PL2 [53:36]=1.2×TDP | DMR TPMI HAS §4.2 |
| **CSR PKG_RAPL_LIMIT** | BIOS-only | RW_L | PKG_PWR_LIM_1/2, TIME, LOCK. BIOS programs once at boot | DMR CBB PM HAS |
| **CSR PKG_ENERGY_STATUS** | BIOS-only | RO | ENERGY [31:0] — mirrors TPMI | DMR CBB PM HAS |
| **MSR 0x610** | IA32_PKG_RAPL_LIMIT | **Deprecated** | Write=silent drop, Read=0 on DMR | DMR PM HAS §5.2 |
| **MSR 0x611** | IA32_PKG_ENERGY_STATUS | **Deprecated** | Read=0 on DMR | DMR PM HAS §5.2 |
| **MSR 0x606** | IA32_PKG_POWER_SKU_UNIT | **Deprecated** | Read=0 on DMR | DMR PM HAS §5.2 |
| **MSR 0xBC** | IA32_MISC_PACKAGE_CTLS | RW | ENERGY_FILTERING_ENABLE [0] — controls energy fuzzing (not deprecated) | DMR PM HAS §5.2 |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| **PID Loop Rate (Slow)** | 1 | ms | Socket RAPL PL1/PL2, Platform RAPL | DMR NNPID HAS |
| **PID Loop Rate (Fast)** | 500 | µs | Fast RAPL IO | DMR NNPID HAS |
| **PL1 Tau Range** | 1–5 | s | Clipped by PrimeCode if out-of-range; default=1s | DMR IMH PM HAS |
| **PL2 Tau Range** | 11.71875–39.0625 | ms | Clipped by PrimeCode if out-of-range | DMR IMH PM HAS |
| **PL1 Response Time** | 3–5× | τ | Time to converge to target power | NNPID Tuning BKM |
| **PL1 Settling Time** | 3–5× | τ | Time for power oscillation < 1% | NNPID Tuning BKM |
| **PL2 Response Time** | ~8 | ms | Platform RAPL PL2 | NNPID Tuning BKM |
| **PL2 Settling Time** | ~25 | ms | Platform RAPL PL2 | NNPID Tuning BKM |
| **Fast RAPL Response** | <4 | ms | Fast RAPL loop response | NNPID Tuning BKM |
| **Freq Oscillation Limit** | ±1 | bin (100 MHz) | Core frequency ripple at steady state | NNPID Tuning BKM |
| **Steady-State Error** | <1% | % target | Power error at convergence | NNPID Tuning BKM |
| **PL1 Default** | TDP | W | = Fused TDP of SKU | DMR PM HAS |
| **PL2 Default** | 1.2×TDP | W | = 120% of fused TDP | DMR PM HAS |
| **PL2 PID Target** | 0.9×PL2 | W | PID uses 90% of PL2 field as target | DMR PM HAS |
| **Energy Status TIME granularity** | 10 | ns | TPMI ENERGY_STATUS TIME field | DMR TPMI HAS |
| **EWMA α (PL1, τ=1s)** | ~0.999 | — | $α = e^{-t_{period}/τ}$, t=1ms, τ=1s | NNPID HAS |
| **HPM RAPL_PERF_LIMIT period** | 1 | ms | IMH→CBB messaging rate | DMR PM HAS |

## NWP Delta

**Socket RAPL (PL1/PL2/PL_tau) is supported on NWP** — reused from DMR.

- Socket RAPL PID algorithm, TPMI interface, and register programming are reused
- FastRAPL is supported for fast power limiting feedback
- HPM messaging between NIO and CBB for RAPL_PID_FREQ_OUTPUT is maintained
- Single NIO die manages all RAPL domains (vs dual IMH on DMR)

### Validation Impact
- Same Socket RAPL test cases apply
- Verify NIO single-die RAPL coordination (vs DMR dual-IMH HPM messaging)

## Legacy (Human-Curated Reference)

### Architecture Summary

Socket RAPL controls power balancing across all components physically located within the socket (all CBB + IMH dies). DMR consolidates the interface from 4 controllers (MSR, PECI, CSR, TPMI) down to **2 controllers** (CSR + TPMI). MSR and PECI PCS are **deprecated** — writes silently dropped, reads return 0.

**FW Agents**: Primecode (IMH-P: runs all *RAPL PIDs), PCode (CBB: perf status counters, fast_throttle, arch throttle)
**Interfaces**: TPMI (in-band + OOB), CSR (BIOS one-time), HPM (RAPL_PERF_LIMIT 0x14-0x15, LEAF_PERF_STATUS 0x16)
**PID Topology**: 9 *RAPL PIDs on IMH-P: Socket PL1 (×2: TPMI + CSR), Socket PL2 (×2), Platform PL1 (×2), Platform PL2 (×2), Fast RAPL (×1). Min-resolved output → RAPL_PID_FREQ_OUTPUT.
**PID Algorithm**: **NN-PID** (Neural Network PID) replaces classic PID on DMR — adaptive online training, no manual tuning. See [NN-PID Section](#nn-pid-neural-network-pid-controller) below.

### Execution Flow

1. **BIOS config** → programs CSR `PACKAGE_RAPL_LIMIT` (PL1, PL2, TW1, TW2) + locks. Programs TPMI OSXML defaults.
2. **Primecode init** → resolves PL1 (default = TDP), PL2 (default = 1.2×TDP). Clips PL1 Tau to [1s, 5s], PL2 Tau to [11.71875ms, 39.0625ms].
3. **Runtime** → IMH-S sends SUB_SOCKET_ENERGY to IMH-P. IMH-P runs PL1/PL2 PIDs (PL1 target = PL1 field, PL2 target = 0.9×PL2 field).
4. **HPM distribution** → IMH-P sends RAPL_PERF_LIMIT to IMH-S (with RACL_PID_FREQ_OUTPUT=0xFF). Each IMH sends RAPL_PERF_LIMIT to its CBBs.
5. **CBB enforcement** → PCode applies frequency ceiling. Increments SOCKET_RAPL_PERF_STATUS if DCM_freq == RAPL_PID_FREQ_OUTPUT and Socket/Fast RAPL flags set.
6. **CBB reporting** → CBB sends LEAF_PERF_STATUS to IMH. IMH-S aggregates and sends to IMH-P. IMH-P updates TPMI PERF_STATUS registers.
7. **PLR reporting** → 1-hot priority: Platform PL2 > Platform PL1 > Fast RAPL > Socket PL2 > Socket PL1. CSR flag has priority over TPMI if both limit.

### NN-PID (Neural Network PID Controller)

> **HAS**: [DMR IMH NNPID HAS v0.5](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/NNPID%20HAS/NNPID%20HAS.html) (Anna Querbach, Oct 2025)
> **FAS**: [Primecode mathutils — NN-PID](https://docs.primecode.intel.com/master/mathutils.html#mathutils_overview_nnpid)

#### Why NN-PID Replaces Classic PID on DMR

Classic PID has two limitations on DMR: (1) 15-20 PID controllers require 2-3 quarters of manual post-si tuning, and (2) static Kp/Ki/Kd cannot adapt to unknown customer workloads → sub-optimal performance and customer recalls. NN-PID reduces tuning from quarters to minutes via adaptive online training and adapts in real-time to workload changes.

**Backwards compatible**: setting learning rate=0 and manually setting weights/Kp/Ki/Kd produces classic PID behavior.

#### Scope — PID Instances Replaced by NN-PID

| Flow | PID Count | Loop Rate | Notes |
|------|-----------|-----------|-------|
| **RAPL PKG (Socket)** | **2** | **1ms (slow loop)** | **PL1 + PL2 — this feature** |
| RAPL PSYS (Platform) | 2 | 1ms | PL1 + PL2 |
| RAPL DRAM | 1 | 1ms | ZBB on NWP |
| Fast RAPL IO | 1 | 500µs (fast loop) | ZBB on NWP |
| RACL | 1 | 1ms | Per-IMH VR TDC |
| Uncore Thermal (EMTTM) | 1 | 1ms | — |
| Memclos DRC | N (per compute die) | 1ms | — |

#### Architecture — 3-Layer Neural Network

```
Input Layer              PID Layer                Output Layer
┌──────────┐        ┌──────────────────┐        ┌──────────┐
│ Normalize │──Ws1──►│ P(n) = A(NT·Ws1  │        │          │
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

- **Input layer**: normalizes setpoint (NT = input/setpoint) and feedback signals. Applies per-weight to each PID node
- **PID layer**: P/I/D activation functions with 6 adaptive weights (Ws1-3, Wf1-3). Trained via backpropagation to minimize derivative of error
- **Output layer**: sums weighted PID outputs, applies EWMA smoothing, controls learning state

#### Input Signal Filtering (EWMA)

Power input from PMON is smoothed before entering NN-PID:

$f_{smooth}(x_i) = \alpha \cdot x_{i-1} + (1-\alpha) \cdot x_i$

$\alpha = \exp\left(-\frac{t_{period}}{\tau_{input}}\right)$

For Socket RAPL: $\tau_{input}$ = OEM-programmed tau (1-5s for PL1), $t_{period}$ = 1ms (slow loop). Example: τ=1s, t=1ms → α ≈ 0.999.

#### NN-PID Operational Modes

| Mode | Condition | Behavior |
|------|-----------|----------|
| Learning | Normal operation | Backpropagation updates weights each iteration — adapts Kp/Ki/Kd |
| Inference Only | Output saturation detected | No learning — prevents weight scaling too large (anti-windup equivalent) |
| Classic PID | learning_rate=0, manual weights | Backwards compatible — identical to static PID |

#### Variable Delta-Time (DT) Support

Corrects for scheduling jitter — designed March 2026:

| Term | Formula | Classic PID (before) |
|------|---------|----------------------|
| time_factor | `delta_time / expected_delta_time` | 1.0 (implicit) |
| **P[t]** | Error[t] | same |
| **I[t]** | I[t-1] + integral_factor × **time_factor** × Error[t] | I[t-1] + integral_factor × Error[t] |
| **D[t]** | (Error[t] - Error[t-1]) / **time_factor** | Error[t] - Error[t-1] |

- Expected dt: 1000µs (slow loop PL1/PL2) or 500µs (Fast RAPL)
- Safety: if delta_time == 0 → skip PID update, return previous output
- Ship flag: `use_variable_dt = false` for safe rollout, flip `true` per-platform once validated

#### Socket RAPL NN-PID Configuration

- **Output range**: P0max to Pm (read from fused values of each part), or 1 (100MHz) to max via UFS reverse lookup
- **Interpolation range**: min(5) to max(42) [fused]
- Configured per-instance — Socket RAPL config differs from Thermal (temperature range) and DRAM RAPL (MC BW range)

#### Tuning / Passing Criteria

| Metric | Requirement |
|--------|-------------|
| Core frequency oscillation | ±1 bin (100MHz) |
| Socket RAPL response time | 3-5× tau |
| Socket RAPL settling time | 3-5× tau |
| Platform RAPL response time | 8ms |
| Platform RAPL settling time | 25ms |
| Steady-state power error | < 1% of target power limit |
| Fast RAPL response time | < 4ms |

#### RACL Init Note (HSD 22022367941)

During early boot (CPL3), RACL NN-PID history/init = all zeros → output smoothing limits ramp rate while TDC current is large → `power_limitation_log` shows false RACL trigger. Fix: set Kp = maxNodeWeight at init.

#### FastRAPL Init Note (HSD 22022442799)

Extra sampling of all VRCI telemetry items before first readings — initializes `prev_` values for accurate delta values on first calculations.

#### Debug

NN-PID debug via **Intel Trace Hub (ITH)** or **Primecode local buffer** (faster, uses remaining SRAM). Buffer requirements: all internal NN-PID variables capturable, PythonSV mask interface, programmable triggers (min/max level, average over N samples, AND/OR, nth event).

#### NN-PID Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [NNPID HAS v0.5](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/NNPID%20HAS/NNPID%20HAS.html) | Architecture, formulas, modes, DT, tuning |
| FAS | [Primecode mathutils — NN-PID](https://docs.primecode.intel.com/master/mathutils.html#mathutils_overview_nnpid) | Implementation reference |
| PR | [PR #7610 — Initial NN-PID](https://github.com/intel-restricted/firmware.management.primecode.firmware/pull/7610/) | Original NN-PID implementation |
| PR | [PR #9551 — Unified NN-PID](https://github.com/intel-restricted/firmware.management.primecode.firmware/pull/9551) | Unified PR across all PID instances |
| BKM | [NN-PID Tuning & Validation — RAPL Server](https://intel-my.sharepoint.com/:w:/r/personal/ofri_seroussi_intel_com/_layouts/15/doc2.aspx?sourcedoc=%7BCFB64C3F-F951-4491-BE97-1E76224FB2EC%7D) | Tuning BKM doc |
| HSD | [22022367941](https://hsdes.intel.com/appstore/article-one/#/article/22022367941) | RACL init false trigger |
| HSD | [22022442799](https://hsdes.intel.com/appstore/article/#/22022442799) | FastRAPL init fix |

### Key Registers & Interfaces

#### TPMI Registers (Socket RAPL domain)
| Register | Index | Key Fields |
|----------|-------|------------|
| Domain Header | 0 | — |
| Power Unit | 1 | PWR_UNIT, ENERGY_UNIT, TIME_UNIT |
| Power Limit (PL1/PL2) | 2-5 | PWR_LIM (18-bit), TIME_WINDOW (8-bit), PWR_LIM_EN, LOCK |
| Energy Status | 7 | ENERGY (32-bit RO), TIME (32-bit, 10ns) |
| Perf Status | 8 | PWR_LIMIT_THROTTLE_CTR (32-bit RO) |
| Power Limit Info | 9 | MAX_PL1 (=TDP), MIN_PL, MAX_PL2 (=1.2×TDP), MAX_TW |

#### CSR Registers
| Register | Key Fields |
|----------|------------|
| PACKAGE_POWER_SKU_CFG | PKG_TDP, PKG_MIN_PWR, PKG_MAX_PWR, PKG_MAX_WIN (RO) |
| PACKAGE_POWER_SKU_UNIT_CFG | PWR_UNIT, ENERGY_UNIT, TIME_UNIT (RO) |
| PACKAGE_RAPL_LIMIT | PKG_PWR_LIM_1/2 (15-bit), PKG_PWR_LIM_EN, CLMP (ignored), TIME, LOCK |
| PACKAGE_ENERGY_STATUS | ENERGY (32-bit RO) |
| PACKAGE_RAPL_PERF_STATUS | PWR_LIMIT_THROTTLE_CTR (32-bit RO) |

#### Deprecated MSRs (reads=0, writes=silent drop)
`0x606` PACKAGE_POWER_SKU_UNIT, `0x610` PACKAGE_RAPL_LIMIT, `0x611` PACKAGE_ENERGY_STATUS, `0x613` PACKAGE_RAPL_PERF_STATUS, `0x614` PACKAGE_POWER_SKU

#### HPM Messages
| Opcode | Message | Key Fields |
|--------|---------|------------|
| 0x14-0x15 | RAPL_PERF_LIMIT | RAPL_PID_FREQ_OUTPUT [63:56], RACL_PID_FREQ_OUTPUT [55:48], CLOS_0-3_LIMIT, PLR flags [44:32], FIVR_INPUT_VOLTAGE [31:16] |
| 0x16 | LEAF_PERF_STATUS | SOCKET_RAPL_PERF_STATUS [47:32], PLATFORM_RAPL_PERF_STATUS [63:48], RACL_PERF_STATUS [31:16] |

#### Interface Selection Truth Table
| IB_READ_BLOCK | IB_WRITE_BLOCK | PCS_SELECT | RAPL Access |
|---------------|----------------|------------|-------------|
| 0 | 0 | 0 | Inband: TPMI R/W + CSR. OOB: TPMI |
| 0 | 1 | 0 | Inband: CSR + TPMI RO. OOB: TPMI |
| 1 | 1 | 0 | Inband: CSR only. OOB: TPMI |
| 1 | 0 | 0 | **Invalid** — Ocode rejects |

> PCS_SELECT is always 0 on DMR (PCS deprecated). Ocode rejects TPMI_SET_STATE if PCS_SELECT=1.

---

### Interface Touch Points

All agents and interfaces that read/write/consume Socket RAPL data, organized by interface type.

#### Interface Matrix (DMR / NWP)

| Register / Parameter | MSR | IN_TPMI | OOB_TPMI | CSR | Fuses | MB (B2P/U2P) |
|----------------------|-----|---------|----------|-----|-------|--------------|
| POWER_UNIT | Read=0 (0x606) | RO (idx 1) | RO | RO (PKG_PWR_SKU_UNIT_CFG) | — | — |
| PL1_CONTROL | Drop/0 (0x610) | RW_L (idx 2) | RW | RW_L (PKG_RAPL_LIMIT) | TDP default | B2P (SST-PP) |
| PL2_CONTROL | Drop/0 (0x610) | RW_L (idx 3) | RW | RW_L (PKG_RAPL_LIMIT) | 1.2×TDP default | B2P (SST-PP) |
| PL4_CONTROL | — | RW_L (idx 5) | RW | — | Fuse-init | — |
| ENERGY_STATUS | Read=0 (0x611) | RO_V (idx 7) | RO | RO (PKG_ENERGY_STATUS) | — | — |
| PERF_STATUS | Read=0 (0x613) | RO_V (idx 8) | RO | RO (PKG_RAPL_PERF_STATUS) | — | — |
| PL_INFO | Read=0 (0x614) | RWL (idx 9) | RW | RO (PKG_PWR_SKU_CFG) | TDP, MIN_PWR | B2P (SST-PP) |
| DOMAIN_INFO | — | RWL (idx 10) | RW | — | — | — |
| INTERRUPT | — | RW (idx 11) | RW | — | — | — |
| DOMAIN_HEADER | — | RO (idx 0) | RO | — | — | — |
| ENERGY_FILTERING (0xBC) | RW | — | — | — | — | — |
| RAPL_PERF_LIMIT | — | — | — | — | — | HPM 0x14-0x15 |
| LEAF_PERF_STATUS | — | — | — | — | — | HPM 0x16 |
| fast_throttle wire | — | — | — | — | — | A2P (WP1/WP3) |
| TDP / MIN_POWER fuses | — | — | — | — | Init | — |
| Cold TDP fuses | — | — | — | — | TEMP + DELTA | — |

> **Key**: RW = read-write, RO = read-only, RW_L = read-write lockable, RO_V = read-only volatile, Drop/0 = write silently dropped / read returns 0 (deprecated), — = not supported
>
> - **MSR**: All RAPL MSRs except 0xBC deprecated on DMR — writes silently dropped, reads return 0
> - **IN_TPMI**: Primary OS/driver interface. TPMI_ID=0x00, package-scoped. Access controlled by IB_WRITE_BLOCK/IB_READ_BLOCK
> - **OOB_TPMI**: BMC/NM access via RdEndpointCfg/WrEndpointCfg. PCS_SELECT=0 (mandatory). PCS deprecated on DMR
> - **CSR**: BIOS one-time programming at boot, then locked. Shadows TPMI values at init
> - **Fuses**: TDP, MIN_POWER, Cold TDP thresholds, SST-PP per-level TDP
> - **MB**: B2P (BIOS→Pcode config), HPM (inter-die RAPL messaging), A2P/Acode (core freq/Cdyn control), SVID (VR telemetry)

#### MSR Interface (Deprecated on DMR)
| MSR Address | Name | R/W | DMR Behavior | GNR Behavior |
|-------------|------|-----|-------------|--------------|
| 0x606 | PACKAGE_POWER_SKU_UNIT | RO | **Read=0** | Returns PWR/ENERGY/TIME units |
| 0x610 | PACKAGE_RAPL_LIMIT | RW | **Write=silent drop, Read=0** | PL1/PL2 power limit + TW + enable + lock |
| 0x611 | PACKAGE_ENERGY_STATUS | RO | **Read=0** | Accumulated energy counter |
| 0x613 | PACKAGE_RAPL_PERF_STATUS | RO | **Read=0** | Throttle time counter |
| 0x614 | PACKAGE_POWER_SKU | RO | **Read=0** | TDP, min power, max power, max TW |
| 0xBC | IA32_MISC_PACKAGE_CTLS | RW | Active | ENERGY_FILTERING_ENABLE bit[0] — controls energy fuzzing |

> **DMR/NWP**: All RAPL MSRs except 0xBC are fully deprecated. No error response — writes silently dropped, reads return 0.

#### Inband TPMI (IN_TPMI) — OS/Driver Access
> See [TPMI Infrastructure Reference](../tpmi_infrastructure.md) for VSEC/PFS/LUT discovery flow, access protection, and TPMI control interface.
> RAPL = **TPMI_ID 0x00**, package-scoped, NumEntries=1, EntrySize=96 DW, CapOffset=8K. opt-out (enabled by default).
> SRAM backed: `PCU_CR_TPMI_MAILBOX1[0]` → `SOCKET_RAPL_DOMAIN_HEADER`.

| TPMI Index | Register | Access | Init Source | Notes |
|------------|----------|--------|-------------|-------|
| 0 | DOMAIN_HEADER | RO | Pcode | TYPE=2 (package), FLAGS bitmask of valid registers, SIZE=1 (128B) |
| 1 | POWER_UNIT | RO | OSXML | PWR_UNIT [3:0], ENERGY_UNIT [10:6], TIME_UNIT [15:12] |
| 2 | PL1_CONTROL | RW_L | Pcode (TDP fuse + OSXML) | PWR_LIM [17:0], TIME_WINDOW [24:18], PWR_LIM_EN [62] (ignored, always on), LOCK [63] |
| 3 | PL2_CONTROL | RW_L | Pcode (1.2×TDP + OSXML) | PWR_LIM [17:0], TIME_WINDOW [24:18], PWR_LIM_EN [62], LOCK [63] |
| 4 | PL3 (Reserved) | RO | — | Reserved (0x0) on DMR |
| 5 | PL4_CONTROL | RW_L | Fuse | PWR_LIM [17:0], PWR_LIM_EN [62], LOCK [63] |
| 6 | PL_OFFSETS | RO | — | Reserved on DMR |
| 7 | ENERGY_STATUS | RO_V | HW counter | ENERGY [31:0] (monotonic, auto-wrap), TIME [63:32] (10ns units). Fuzzed if 0xBC.bit0=1 |
| 8 | PERF_STATUS | RO_V | Pcode | PWR_LIMIT_THROTTLE_CTR [31:0] |
| 9 | PL_INFO | RWL (Pcode locks) | Pcode | MAX_PL1 [17:0]=TDP, MIN_PL [35:18], MAX_PL2 [53:36]=1.2×TDP, MAX_TW [60:54], LOCK [63] |
| 10 | DOMAIN_INFO | RWL | Pcode | ROOT [0], DOMAIN_ID [3:1]. Not enabled for Socket RAPL (Psys only) |
| 11 | INTERRUPT | RW | SW | Mask [0], Status [1] (W1C) |

> **Access control**: IB_READ_BLOCK / IB_WRITE_BLOCK bits in TPMI control determine R/W/RO/NoAccess for inband. See Interface Selection Truth Table above.

#### OOB TPMI (OOB_TPMI) — BMC/NM Access
| Register | OOB Access | Notes |
|----------|-----------|-------|
| PL1_CONTROL | RW | BMC can set power limits below platform maximums |
| PL2_CONTROL | RW | BMC can set PL2 |
| PL_INFO | RW (Platform RAPL) | BMC initializes Platform RAPL PL_INFO; can override BIOS settings |
| ENERGY_STATUS | RO | Same fuzzed value as inband |
| PERF_STATUS | RO | Same counter as inband |

> **OOB selection**: PCS_SELECT=0 (mandatory on DMR). OOB always uses TPMI, never PCS. OOBMSM provides Primary→Sideband translation via LTM for RAPL registers.
> **DMR OOB access**: Uses Rd/WrEndpointCfg with BDF_BAR64 (addressType=0x6), segment=0 + system-assigned BDF. PECI-to-HostDD loopback allows access during PkgC (unlike GNR). BMC must add `BMC_TPMI_FEATURES_FIXED_OFFSET` (from PMT TPMI watcher bit[63:32]) to register offset.
> **All-Fs check**: If SOCKET_RAPL_DOMAIN_HEADER returns all-1s → instance invalid + all registers in that instance are invalid (even if completion=0x40).

#### CSR Interface — BIOS One-Time Programming
| CSR Register | Access | Init | Pcode Bounds | Notes |
|-------------|--------|------|--------------|-------|
| PACKAGE_POWER_SKU_CFG | RO | Pcode (=TPMI) | — | PKG_TDP [14:0], PKG_MIN_PWR, PKG_MAX_PWR, PKG_MAX_WIN |
| PACKAGE_POWER_SKU_UNIT_CFG | RO | Pcode (=TPMI) | — | PWR_UNIT, ENERGY_UNIT, TIME_UNIT |
| PACKAGE_RAPL_LIMIT | RW | BIOS | PL1 ≤ TDP, PL2 ≤ 1.2×TDP, TW1∈[1s,5s], TW2∈[11.7ms,39ms] | PKG_PWR_LIM_1/2, CLMP (ignored), TIME, LOCK |
| PACKAGE_ENERGY_STATUS | RO | HW | — | ENERGY [31:0] |
| PACKAGE_RAPL_PERF_STATUS | RO | Pcode | — | PWR_LIMIT_THROTTLE_CTR [31:0] |

> **Usage model**: BIOS programs CSR once at boot → sets LOCK. CSR values shadow TPMI at init. Runtime SW uses TPMI exclusively.

#### Fuses
| Fuse | Width | Format | Purpose |
|------|-------|--------|---------|
| TDP | — | — | Base thermal design power for SKU |
| MIN_POWER_OF_SKU | — | — | Minimum power limit allowed → PL_INFO.MIN_PL |
| COLD_LONG_POWER_LIMIT_TEMP | 8 | S8.7.0 | Temperature threshold for Cold TDP |
| COLD_LONG_POWER_LIMIT_DELTA | 8 | U8.8.0 | PL1 offset at cold temperatures |
| SST-PP fuses | — | — | TDP per perf profile level |
| **Removed on DMR** | | | MAX_LONG_POWER_LIMIT, MAX_SHORT_POWER_LIMIT, PKG_PWR_LIM_1_MAX, PKG_PWR_LIM_2_MAX, PKG_PWR_LIM_2_MAX_TIME_WINDOW |

#### HPM Messages (PMSB Sideband)
| Opcode | Direction | Message | Key Fields |
|--------|-----------|---------|------------|
| 0x14-0x15 | IMH-P→IMH-S, IMH→CBBs | RAPL_PERF_LIMIT | RAPL_PID_FREQ_OUTPUT [63:56], RACL_PID_FREQ_OUTPUT [55:48], CLOS_0-3_LIMIT [95:64], PLR flags [44:32] (1-hot), FIVR_INPUT_VOLTAGE [31:16] (U3.13) |
| 0x16 | CBBs→IMH | LEAF_PERF_STATUS | SOCKET_RAPL_PERF_STATUS [47:32], PLATFORM_RAPL_PERF_STATUS [63:48], RACL_PERF_STATUS [31:16] |
| SUB_SOCKET_ENERGY | IMH-S→IMH-P | SUB_SOCKET_ENERGY | Energy telemetry from leaf IMH to root for PID calibration |
| ~~0x1b-0x1c~~ | ~~deprecated~~ | ~~PL2_FAST_THROTTLE_LIMIT~~ | ~~Removed on DMR (was N-strike FastRAPL)~~ |
| ~~0x1d-0x1e~~ | ~~deprecated~~ | ~~FAST_RAPL_INST_PWR_FREQ_LIMIT~~ | ~~Removed on DMR (was N-strike FastRAPL)~~ |

#### B2P Mailbox (BIOS-to-Punit)
| Command | Direction | Purpose | RAPL Relevance |
|---------|-----------|---------|---------------|
| WRITE_PCU_MISC_CONFIG | BIOS→Pcode | Miscellaneous Pcode config | bit[1:1]=1 required for PL2_SAFETY_NET_ENABLE (FastRAPL prerequisite) |
| SST-PP level change | BIOS→Pcode | Change SST perf profile | Triggers Pcode to update TDP, PL1, PL2 defaults, PL_INFO.MAX_PL1/MAX_PL2 |
| RAPL config commands | BIOS→Pcode | RAPL parameter programming | Initial RAPL configuration at boot |

#### U2P Mailbox (Uncore-to-Punit)
| Agent | Direction | Purpose | RAPL Relevance |
|-------|-----------|---------|---------------|
| OOBMSM | OOB→Pcode | Platform management commands | PECI thermal/power commands routed through U2P to Pcode. On DMR PECI PCS for RAPL is deprecated — BMC uses OOB TPMI instead |
#### TPMI Control Interface (RAPL-specific)
| Operation | Command | RAPL Behavior |
|-----------|---------|---------------|
| TPMI_GET_STATE (0x10) | TPMI_ID=0x00 | Returns STATE, IB_WRITE_BLOCK, IB_READ_BLOCK, PCS_SELECT(=0), LOCK |
| TPMI_SET_STATE (0x11) | TPMI_ID=0x00 | BIOS locks RAPL before OS boot. IB_WRITE_BLOCK=1 if BMC owns writes |
| Opt-out | IB sets IB_WRITE_BLOCK=1 | Inband TPMI becomes RO; OOB retains R/W |
| Fastpath | TPMI_REQ | Pcode wakes on any RAPL SRAM line write, resolves line index, processes new PL/TW |
#### A2P / Acode Interface (Core Perimeter)
| Interface | Direction | Purpose | RAPL Relevance |
|-----------|-----------|---------|---------------|
| PMSB WP1 | Pcode→Acode | Workpoint 1: target frequency | Pcode sets WP1.Frequency=Pm when throttling below Pm |
| PMSB WP3 | Pcode→Acode | Workpoint 3: ICC limits | Pcode forces ICC_LIMIT0=ICC_LIMIT1=1 for lowest Cdyn level during below-Pm throttle |
| GO_INC_GB_ELEC | Pcode→Acode | Trigger Acode GV command | Acode samples WP and applies PVP threshold |
| ACK_INC_GB_ELEC | Acode→Pcode | Acode acknowledgment | Confirms Cdyn level change |
| fast_throttle wire | Pcode/HW→Core | Clock division trigger | Asserted when RAPL_PID_FREQ_OUTPUT < Pm or PMAX/PROCHOT events |
| IO_THERM_INDICATIONS.FAST_RAPL_THROTTLE[22] | Pcode→Core | Slow-limit fast_throttle | Pcode asserts for RAPL/RACL/Thermal; deasserts when all sources clear |

#### SVID Interface (Voltage Regulator)
| Agent | Direction | Purpose | RAPL Relevance |
|-------|-----------|---------|---------------|
| Primecode→VR | IMH→MBVR | MBVR voltage read | FIVR_INPUT_VOLTAGE in RAPL_PERF_LIMIT = MBVR set voltage - DC loadline drop |
| VR→Primecode | MBVR→IMH | Telemetry (IMON) | Energy measurement input for RAPL PID |

#### Interface Flow Summary
```
                    ┌─────────────┐
    BIOS ──CSR────►│             │
    BIOS ──B2P────►│   Pcode     │──HPM 0x14──►CBB Pcode──fast_throttle──►Core
    OS/SW──IN_TPMI─►│   (IMH-P)   │──HPM 0x14──►IMH-S Primecode
    BMC ──OOB_TPMI─►│             │◄──HPM 0x16──CBBs (LEAF_PERF_STATUS)
                    │  Primecode  │◄──SUB_SOCKET_ENERGY──IMH-S
    Fuses─────────►│             │
    MBVR/VR──SVID──►│             │──WP1/WP3──►Acode (Core Perimeter)
                    └──TPMI regs──┘
                      ▲  ▲  ▲
                     MSR=0  │  │
                    (deprecated) │
                         IN_TPMI OOB_TPMI
```

---

### Cover Points / Subflows

#### CP1: PL1 Power Limiting
| Aspect | Cover Point | HAS Reference |
|--------|-------------|---------------|
| CP1.1 | PL1 default = TDP; verify power converges to TDP under sustained load | Power targets section |
| CP1.2 | PL1 Tau range [1s, 5s]; values outside this range clipped by Primecode | PL1 Tau reduction |
| CP1.3 | PL1 Tau default = 1s in reference platforms | PL1 Tau Implementation |
| CP1.4 | PL1_EN ignored by Pcode (always enabled) — verify PL1 enforced even if PL1_EN=0 | Register Programming |
| CP1.5 | CLMP_LIM_1 ignored by Pcode (assumed 1) | Register Programming |
| CP1.6 | PL1 bounds check: non-OC ≤ 1.0×TDP of current PP level; OC unlimited | Register Programming |
| CP1.7 | Sweep PL1 values: verify throttle response at each power target | TC: Sweep CPU RAPL limits |
| CP1.8 | PL1 settling time (time to converge to target power) | TC: PL1 settling time |
| CP1.9 | Cold TDP: if SW PL1 ≥ fused TDP AND SOC_MIN_TEMP < COLD_LONG_POWER_LIMIT_TEMP → Effective PL1 += COLD_TDP_OFFSET | TDP @ Cold |
| CP1.10 | Cold TDP applies only to PL1, not PL2 | TDP @ Cold |

#### CP2: PL2 Power Limiting
| Aspect | Cover Point | HAS Reference |
|--------|-------------|---------------|
| CP2.1 | PL2 default = 1.2×TDP; PID target = 0.9×PL2 register field | Power targets |
| CP2.2 | PL2 Tau range [11.71875ms, 39.0625ms]; out-of-range clipped | PL2 Tau Implementation |
| CP2.3 | PL2 short-burst power excursion and recovery within Tau window | PL2 Interface |
| CP2.4 | PL2 bounds check: non-OC ≤ 1.2×TDP; OC unlimited | Register Programming |
| CP2.5 | Verify PL2 is effective with higher workload transients | TC: Fast RAPL - PEM Verification |

#### CP3: Interface Consolidation (MSR/PECI Deprecation)
| Aspect | Cover Point | HAS Reference |
|--------|-------------|---------------|
| CP3.1 | MSR writes to 0x610/611/613/614 silently dropped | MSR and TPMI Registers |
| CP3.2 | MSR reads from 0x606/610/611/613/614 return 0 | MSR and TPMI Registers |
| CP3.3 | Negative test: Write MSR → verify no power limit change | TC: RAPL MSR checks - Negative |
| CP3.4 | TPMI R/W verified for in-band software | Interface Selection |
| CP3.5 | TPMI R/W verified for OOB (BMC) software | TC: Socket Rapl verification - OOB |
| CP3.6 | CSR one-time BIOS programming + lock verified | Register Programming |
| CP3.7 | IB_READ/WRITE_BLOCK truth table: all 4 combinations verified | Interface Selection |
| CP3.8 | PCS_SELECT=1 rejected by Ocode | Interface Selection |

#### CP4: HPM Messaging & Multi-Die Coordination
| Aspect | Cover Point | HAS Reference |
|--------|-------------|---------------|
| CP4.1 | IMH-P→IMH-S RAPL_PERF_LIMIT: RACL_PID_FREQ_OUTPUT=0xFF (RACL is local) | Communications between IMH & CBB |
| CP4.2 | IMH→CBB RAPL_PERF_LIMIT: min-resolved RAPL_PID_FREQ_OUTPUT, CLOS_0-3_LIMIT | HPM RAPL_PERF_LIMIT |
| CP4.3 | CBB→IMH LEAF_PERF_STATUS: SOCKET_RAPL_PERF_STATUS incremented correctly | LEAF_PERF_STATUS |
| CP4.4 | PLR 1-hot flag priority: Plat PL2 > Plat PL1 > Fast > Sock PL2 > Sock PL1 | RAPL_PERF_LIMIT |
| CP4.5 | If both CSR and TPMI limit, CSR flag set (not TPMI) | RAPL_PERF_LIMIT |
| CP4.6 | If no RAPL PID limiting → RAPL_PID_FREQ_OUTPUT=0xFF, no flags set | RAPL_PERF_LIMIT |
| CP4.7 | HPM verification: validate HPM messages match HAS field definitions | TC: RAPL HPM verification |
| CP4.8 | FIVR_INPUT_VOLTAGE field (U3.13) in RAPL_PERF_LIMIT | HPM RAPL_PERF_LIMIT |

#### CP5: Perf Status & Energy Reporting
| Aspect | Cover Point | HAS Reference |
|--------|-------------|---------------|
| CP5.1 | SOCKET_RAPL_PERF_STATUS increments when DCM_freq == RAPL_PID_FREQ_OUTPUT AND Socket/Fast RAPL flags set | CBB increment *RAPL_PERF_STATUS |
| CP5.2 | ENERGY_STATUS counter monotonically increasing under load | Register Programming |
| CP5.3 | ENERGY_STATUS TIME field uses 10ns units | Register Programming |
| CP5.4 | Perf status reported correctly via TPMI | TC: RAPL Perf status |
| CP5.5 | Energy status and IMON telemetry correlation | TC: RAPL IMON Addressing and Telemetry |
| CP5.6 | Energy status reporting accuracy | TC: RAPL Energy status reporting |

#### CP6: PEM (PnP Excursion Monitor)
| Aspect | Cover Point | HAS Reference |
|--------|-------------|---------------|
| CP6.1 | PEM PL1 CFG counter updates based on Socket RAPL PL1 limiting | PrimeCode Flow |
| CP6.2 | PEM PL2 CFG counter updates based on Socket RAPL PL2 limiting | PrimeCode Flow |
| CP6.3 | PEM verified for Socket RAPL PL1 | TC: [PSS] PEM - Socket RAPL PL1 |
| CP6.4 | PEM verified for Socket RAPL PL2 | TC: [PSS] PEM - Socket RAPL PL2 |

#### CP7: PLR (Perf Limit Reasons)
| Aspect | Cover Point | HAS Reference |
|--------|-------------|---------------|
| CP7.1 | PLR Socket RAPL PL1 — fine-grained (inband/CSR/OOB) | CBB evaluate PLR bits |
| CP7.2 | PLR Socket RAPL PL2 — fine-grained (inband/CSR/OOB) | CBB evaluate PLR bits |
| CP7.3 | PLR Fast RAPL flag set when FastRAPL is sole limiter | CBB evaluate PLR bits |
| CP7.4 | PLR condition: asserted only if RAPL_PID_FREQ_OUTPUT < Max_of_Reverse_Lines | RAPL_PERF_LIMIT (HSD 16029367861) |
| CP7.5 | PLR Socket RAPL PL1 verified | TC: [PSS] PLR - Socket RAPL PL1 |
| CP7.6 | PLR Socket RAPL PL2 verified | TC: [PSS] PLR - Socket RAPL PL2 |
| CP7.7 | PLR fine + coarse reporting | TC: RAPL Perf limit reasons - Fine & Coarse |

#### CP8: Integral Windup Mechanism
| Aspect | Cover Point | HAS Reference |
|--------|-------------|---------------|
| CP8.1 | Actuator feedback u_k = min of all *RAPL PID outputs | Integral Windup Mechanism |
| CP8.2 | Integral clipped by Max_of_Reverse_Lines = max(IA_P0, Reverse_CCF_Line_1, ...) | Integral Windup Mechanism |
| CP8.3 | Kt=Ki (default) — saturation tracking enabled | Integral Windup Mechanism |
| CP8.4 | PKG_ACTUATOR_FEEDBACK_INCLUDES_MESH default=0 (mesh excluded from feedback) | Integral Windup Mechanism |
| CP8.5 | Frequency recovery after RAPL constraint removed (no persistent windup) | Integral Windup Mechanism |

#### CP9: Throttling Below Pm
| Aspect | Cover Point | HAS Reference |
|--------|-------------|---------------|
| CP9.1 | If RAPL_PID_FREQ_OUTPUT < Pm → Pcode asserts fast_throttle wire → clock division + arch throttle (1:8) | Throttling Cores below Pm |
| CP9.2 | If RAPL_PID_FREQ_OUTPUT < Pm → Pcode forces lowest Cdyn via WP3 (ICC_LIMIT0=ICC_LIMIT1=1) | Forcing Lowest Cdyn via WP3 |
| CP9.3 | Exit: all cores ≥ Pm → deassert fast_throttle, restore WP3 with EDP ICC limits | Forcing Lowest Cdyn exit |
| CP9.4 | Verify throttling below Pm actually reduces power below TDP | TC: Throttling below Pm |

#### CP10: BIOS / Fuse Configuration
| Aspect | Cover Point | HAS Reference |
|--------|-------------|---------------|
| CP10.1 | BIOS knobs correctly program CSR RAPL limits | TC: RAPL BIOS Knobs Verification |
| CP10.2 | RAPL-related fuse values verified | TC: RAPL - Checkout fuses |
| CP10.3 | LOCK bit prevents further modification of CSR registers | TC: RAPL limit lock |
| CP10.4 | PL2_SAFETY_NET_ENABLE=1 default (required for FastRAPL) | BIOS Changes |
| CP10.5 | B2P WRITE_PCU_MISC_CONFIG bit[1:1]=1 if BIOS issues this command | BIOS Changes |

#### CP11: Cross Products
| Aspect | Cover Point | HAS Reference |
|--------|-------------|---------------|
| CP11.1 | Socket RAPL × RACL: min freq ceiling applied | Cross Products table |
| CP11.2 | Socket RAPL × Platform RAPL: min freq ceiling applied | Cross Products table |
| CP11.3 | Socket RAPL × PMAX: simultaneous, no interference | Cross Products table |
| CP11.4 | Socket RAPL × PROCHOT: simultaneous operation | Cross Products table |
| CP11.5 | Socket RAPL × UFS: independent for IMH fabric, RAPL line for CBB | Cross Products table |
| CP11.6 | Socket RAPL × PkgC: RAPL flows continue during PkgC | Cross Products table |
| CP11.7 | Socket RAPL × OSPL: limits + counters retained | Cross Products table |
| CP11.8 | Socket RAPL × Reset (cold/warm): limits + counters reset to defaults | Cross Products table |
| CP11.9 | Socket RAPL × SST: interaction with SST-PP level TDP | TC: Socket rapl x SST |
| CP11.10 | Socket RAPL × core/IO traffic: throttling under mixed workload | TC: Socket Rapl x Core x IO Traffic |
| CP11.11 | Socket RAPL × Security (Mistletoe PRT): energy fuzzing | TC: RAPL X Security |

#### CP12: NWP-Specific Deltas
| Aspect | Cover Point | HAS Reference |
|--------|-------------|---------------|
| CP12.1 | NWP Socket RAPL functional at 450W TDP | NWP PM MAS |
| CP12.2 | NWP: DRAM RAPL ZBB'd → negative check (no effect) | TC: [PSS] DRAM RAPL ZBB Negative |
| CP12.3 | NWP: Platform RAPL/Psys ZBB'd → negative check | NWP PM MAS |
| CP12.4 | NWP: SIMPL ZBB'd → negative check | NWP PM MAS |
| CP12.5 | NWP: Fast RAPL ZBB'd → negative check | NWP PM MAS |
| CP12.6 | NWP: Fine Grained Energy ZBB'd → negative check | NWP PM MAS |
| CP12.7 | NWP: Dual DDR SVID rails (VCCDDR_HV + VCCDDR_HV1) both contribute to socket_power_vrs_imon — verify 6-VR energy sum | svid.xml: socket_power_vrs_imon |
| CP12.8 | NWP: VCCDDR_HV1 elective discovery — verify graceful fallback to VCCD1_HV_CPU0_POWER fuse when rail absent | svid.xml: elective_discretionary_vr_array |
| CP12.9 | NWP: Non-mandatory VR fuse fallback accuracy — compare fuse-based vs IMON-based socket power for VCCDDR_HV, VCCDDR_HV1, VCCFA_EHV, VCCANA | svid.xml: non_mandatory_vr_fuse_array |
| CP12.10 | NWP: UFS disabled (fuse UFS_DISABLE=1) — verify mesh freq fixed at 2 GHz, RAPL PID cannot throttle mesh | dut/nwp_imh_cfg.xml |
| CP12.11 | NWP: NN-PID convergence with core-freq-only actuator (no mesh DVFS) — verify settling time ≤ 5× tau at 450W | NN-PID tuning |
| CP12.12 | NWP: VCCFA_EHV removal — if removed from SVID, verify fallback to VCCFA_EHV_CPU0_POWER fuse and no MCA | svid.xml: non_mandatory_vr_array |
| CP12.13 | NWP: rapl_reporting disabled — verify TPMI PERF_STATUS/ENERGY_STATUS still update via alternate paths | dut/nwp_imh_cfg.xml |
| CP12.14 | NWP: Single SVID bus (Bus 1 absent) — all 6 socket VRs polled on Bus 0, verify telemetry freshness | svid.xml: poll_priority_bus1 = INVALID |
| CP12.15 | NWP: VCCC2CSIP FIVR domain present in fivr_energy_mapping — verify `FIVR_DOMAINS_NUM ≥ 13` and IIN_ACCUMULATOR telemetry for C2C SIP is summed into socket power | HSD 22021977883 / fivr_energy_mapping.hpp |
| CP12.16 | NWP: ENERGY_STATUS accuracy with D2D-heavy workload — verify RAPL energy accounts for ~25W C2C SIP power (compare RAPL vs external power meter, delta < 10%) | TC: RAPL Energy status reporting |
| CP12.17 | NWP: VCCFA_EHV IMON reflects increased FIVR load from VCCC2CSIP domain — expected higher baseline vs DMR (13 FIVRs vs 12) | TC: RAPL IMON Addressing and Telemetry |
| CP12.18 | NWP: RACL TDC thresholds accommodate VCCFA_EHV current increase from 13th FIVR domain — verify no false RACL limiting under D2D traffic | TC: Socket Rapl x RACL x Psys |
| CP12.19 | NWP: Socket RAPL × D2D traffic cross-product — run 800GB/s D2D bandwidth workload, verify PL1/PL2 response settles without oscillation at +25W C2C power | TC: Socket Rapl x Core Traffic x IO Traffic |
| CP12.20 | NWP: PkgC entry/exit with VCCC2CSIP domain split — verify D2D link quiescing at different voltage (0.94V C2C vs 0.66V CAB) doesn't stall PkgC transition | TC: RAPL X Pkgc |
| CP12.21 | NWP: VCCC2CDIG ITD fuses present and applied — verify `VCCC2CDIG_ITD_CUTOFF_V`, `VCCC2CDIG_ITD_SLOPE`, `VCCC2CDIG_ITD_TEMP_OFFSET`, `VCCC2CDIG_ACTIVE_VOLTAGE` are read from fuse and used in voltage computation | HSD 22022032536 |
| CP12.22 | NWP: ITD voltage correction on VCCC2CDIG tracks DTS temperature — sweep temperature from cold to hot, verify voltage decreases with increasing temperature per ITD algorithm | ITD HAS |
| CP12.23 | NWP: VCCFIXDIG_E/W ITD fuse values appropriate for MC + HSF combined power scope — verify ITD-corrected voltage is within safe range for both MC and HSF logic | HSD 14026585116 |
| CP12.24 | NWP: No-ITD fallback (slopes zeroed) — verify Socket RAPL converges at +4-7W higher power when VCCC2CDIG and VCCFIXDIG ITD is disabled | Negative test |
| CP12.25 | NWP: Binning × RAPL — verify NN-PID convergence across different QDFs with different per-part VF binning fuses (no manual re-tuning needed) | ITD HAS + NN-PID HAS |

---

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR RAPL Simplification HAS v1.05](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html) | Primary HAS — Socket/Platform/Fast RAPL |
| HAS | [DMR NNPID HAS v0.5](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/NNPID%20HAS/NNPID%20HAS.html) | NN-PID algorithm replacing classic PID on DMR |
| HAS | [Socket RAPL HAS (Wave3/GNR)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) | Legacy reference (PID details, throttle below Pm) |
| HAS | [GNR Socket RAPL HAS (HPM system)](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/socketRAPL/socket_rapl.html#in-a-hpm-system) | GNR PID implementation reference |
| HAS | [HPM Message Specification](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html#RAPL_PERF_LIMIT) | RAPL_PERF_LIMIT, LEAF_PERF_STATUS fields |
| HAS | [DMR Fabric DVFS — RACL/RAPL connectivity](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html#connecting-racl-rapl-to-fabric-dvfs) | RAPL → fabric freq limit path |
| HAS | [PEM HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/PEM_HAS.html) | PnP Excursion Monitor spec |
| HAS | [DMR PLR HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PLR.html) | Perf Limit Reasons spec |
| HAS | [RACL / VR TDC HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Dual_VCCIN_RACL_VRTDC/RACL_VR_TDC.html) | RACL PID (per-IMH) |
| HAS | [DRAM RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html#dram-running-average-power-limit-rapl) | DRAM RAPL (ZBB on NWP) |
| HAS | [GNR RAPL Tuning Guide](https://docs.intel.com/documents/pm_doc/src/server/GNR/post_si/RAPL_Tuning/RAPL_Tuning_Guide.html) | Post-si tuning reference |
| HAS | [TPMI HAS — LTM FW](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html#ltm-fw) | Interface selection truth table |
| HAS | [Arch RAPL TPMI Interface](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/RAPL_DVSEC/RAPL_DVSEC.html#pl1-pl2-idx-23) | TPMI register layout (PL1/PL2/Energy/Perf/PLInfo domain registers) |
| HAS | [RAPL VSEC Sheets (xlsx)](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/RAPL_DVSEC/assets/RAPL_VSEC_sheets.xlsx) | Register bitfield source spreadsheet |
| HAS | [TPMI/DVSEC MMIO HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/DVSEC%20MMIO/dvsec_mmio.html) | TPMI address mapping, PFS, VSEC capability structure |
| HAS | [TPMI Roles & Responsibilities](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/DVSEC%20MMIO/dvsec_mmio.html#roles-and-responsibilities) | PCS_SELECT, IB/OOB access control |
| HAS | [HPM FastRAPL HAS (GNR)](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/hpm_fast_rapl/hpm_fast_rapl.html) | FastRAPL PID specification |
| HAS | [Pcode FAS — DCF Throttling](https://docs.primecode.intel.com/master/dcf_throttling.html) | Throttle below Pm implementation |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP deltas — Socket RAPL only |
| Spreadsheet | [DMR_RAPL.xlsx](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/assets/DMR_RAPL.xlsx) | Register tables, interface selection, cross products |
| HSD | [22021977883](https://hsdes.intel.com/appstore/article-one/#/article/22021977883) | VCCCAB → VCCCAB + VCCC2CSIP FIVR domain split proposal |
| HSD | [22022032536](https://hsdes.intel.com/appstore/article-one/#/article/22022032536) | ITD/Binning on FIVR VCCC2CDIG and VCCFIXDIG_E/W |
| HSD | [14026585116](https://hsdes.intel.com/appstore/article-one/#/article/14026585116) | [NWP] VCCFIXDIG tracking — VCCFIXDIG_E/W powers MC + HSF |

---

### Primecode Source Files (IMH-P / IMH-S)

> Repo: `firmware.management.primecode.firmware`

#### RAPL Domain Flows — `src/flow/rapl/`
| File | Version | Purpose |
|------|---------|---------|
| `rapl_common/v2_0/rapl_vars.hpp` | v2_0 | Global RAPL state — enums (`rapl_all_inputs`, `rapl_all_limits`, `rapl_comm_type`), PBM structures, PID output tracking, energy/time status, CLOS freq arrays |
| `rapl_common/v2_0/rapl_vars.cpp` | v2_0 | RAPL variable initialization |
| `rapl_package/v2_0/rapl_pkg_domain.hpp` | v2_0 | **Socket (PKG) RAPL domain** — PID constants (Kp=0x9, Ki=0x39, Kd=0, Kt calibrated), max PL2 TW=0x21. Inherits `RAPLDomain` |
| `rapl_package/v2_0/rapl_pkg_domain.cpp` | v2_0 | Socket RAPL PID loop implementation |
| `rapl_psys/v2_0/rapl_psys_domain.hpp` | v2_0 | Platform RAPL (PSYS) domain — same PID constants as PKG |
| `rapl_psys/v2_0/rapl_psys_domain.cpp` | v2_0 | Platform RAPL PID loop |
| `rapl_pbm/v2_0/rapl_pbm.hpp` | v2_0 | Power Budget Manager (PBM) — PL resolution, TDP guard band |
| `rapl_pbm/v2_0/rapl_pbm.cpp` | v2_0 | PBM implementation |
| `rapl_pbm/v2_1/rapl_pbm.cpp` | v2_1 | PBM v2.1 (DMR/NWP) |
| `rapl_bridge/v2_0/rapl_bridge_common.hpp` | v2_0 | Bridge RAPL domain output → core CLOS frequency limits |
| `rapl_bridge/v2_0/rapl_bridge_common.cpp` | v2_0 | Bridge implementation |
| `rapl_sst/v2_0/rapl_sst.hpp` | v2_0 | SST-PP integration with RAPL TDP |
| `rapl_sst/v2_0/rapl_sst.cpp` | v2_0 | SST RAPL implementation |
| `rapl_algo/` | — | RAPL algorithm core (PID engine) |
| `rapl_dram/` | — | DRAM RAPL domain (ZBB on NWP) |

#### RAPL HPM Messaging — `src/flow/rapl/rapl_messaging/`
| File | Purpose |
|------|---------|
| `rapl_hpm_root/v2_0/rapl_hpm_root.cpp` | **Root IMH (IMH-P)**: sends `RAPL_PERF_LIMIT` to leaf IMH + CBBs. Min-resolves fast RAPL freq with regular RAPL output. Distributes CLOS limits |
| `rapl_hpm_leaf_io/v2_0/rapl_hpm_leaf_io.cpp` | **Leaf IMH (IMH-S)**: receives `RAPL_PERF_LIMIT`, applies freq limits via core driver |

#### Fast RAPL — `src/flow/fast_rapl/`
| File | Version | Purpose |
|------|---------|---------|
| `fast_rapl_io/v2_0/fast_rapl_io.hpp` | v2_0 | Root die Fast RAPL — 500µs power excursion response. Tracks `bios_fast_rapl_enabled`, freq limit, limiting flag |
| `fast_rapl_io/v2_0/fast_rapl_io.cpp` | v2_0 | Fast RAPL IO implementation |
| `fast_rapl_common/v2_0/fast_rapl_common.hpp` | v2_0 | Shared fast RAPL logic |
| `fast_rapl_common/v2_0/fast_rapl_common.cpp` | v2_0 | Common implementation |
| `fast_rapl_compute/v1_1/fast_rapl_compute.hpp` | v1_1 | CBB-side fast RAPL compute |

#### TPMI Mailbox — `src/flow/mailbox/tpmi/`
| File | Purpose |
|------|---------|
| `v1_0/tpmi_mailbox_commands.cpp` | Handles SOCKET_RAPL_PERF_STATUS / ENERGY_STATUS SRAM line updates on TPMI write |
| `tpmi_range/v2_0/tpmi_mailbox_range.hpp` | SOCKET_RAPL_DOMAIN_HEADER start address, range definitions for TPMI access filtering |

#### HPM Message Definitions — `src/flow/hpm/`
| File | Key Content |
|------|-------------|
| `hpm_common/v2_0/hpm_mailbox.xml` | `RAPL_PERF_LIMIT` (0x14-0x15): RAPL_PID_FREQ_OUTPUT, CLOS_0-3_LIMIT, PKG_PL1/PL2 inband/OOB reason bits. `LEAF_PERF_STATUS` (0x16): SOCKET_RAPL_PERF_STATUS[47:32] |
| `hpm_common/v1_0/hpm_mailbox.xml` | Legacy: SOCKET_RAPL_F0-F3, SOCKET_RAPL_LEAF_PERF_STATUS |

#### UFS × RAPL — `src/flow/ufs/`
| File | Purpose |
|------|---------|
| `ufs_algos/v2_0/ufs_rapl.hpp` | UFS RAPL algorithm integration — freq output min'd with UFS PID |
| `ufs_algos/v2_0/ufs_rapl.cpp` | UFS RAPL implementation |

#### PMax (PL4) — `src/flow/pmax/`
| File | Purpose |
|------|---------|
| `pmax_common/v1_0/pmax_common_tpmi.cpp` | Socket RAPL PL4 control via TPMI |

#### BIOS Mailbox — `src/flow/mailbox/bios/`
| File | Purpose |
|------|---------|
| `v1_0/bios_mailbox.xml` | THRESHOLD_TO_OVERRIDE_IGNORE_PLATFORM_RAPL_PID_OUTPUT field |

#### IP Drivers — `src/ip/`
| File | Purpose |
|------|---------|
| `svid/v2_0/svid_pmeter.hpp` | Power meter — energy calculation per RAPL domain (PKG, PSYS) |
| `svid/v2_0/svid_pmeter.cpp` | Power meter implementation (SVID telemetry → RAPL energy input) |
| `fuse/v2_0/fuses.xml` | RAPL fuse feature flags: DRAM_RAPL, TDP, PL1 cold limit, extra MCP/CPU die power |
| `fuse/v2_0/fuses_sst.xml` | SST_PP_UFS_RAPL_SLOPE/BASE arrays (per PP level) |
| `core/corecommon/v1_0/base_ia_main.hpp` | `setCoreClosRaplLimits()`, `socket_rapl_freq[]` — applies RAPL freq ceiling to cores |
| `core/corecommon/v1_0/base_ia_main.cpp` | Core frequency limiting from RAPL PID output |
| `core/corecommon/v1_0/base_ia_actions.cpp` | Core action handler: applies RAPL limits |

#### Config Data — `src/cfgdata/`
| File | Purpose |
|------|---------|
| `tpmi_osxml/v1_0/AddressMap_TPMI.os.xml` | TPMI Socket RAPL register map: DOMAIN_HEADER (0xC800), POWER_UNIT (0xC808), PL1_CONTROL (0xC810), PL2_CONTROL (0xC818), PL4_CONTROL (0xC828), ENERGY_STATUS (0xC838), PERF_STATUS (0xC840), PL_INFO (0xC848) |
| `trace/primeCodeTrace.xml` | RAPL trace IDs: FAST_RAPL_POWER, RAPL_SUBFLOWS_TRACE, RAPL_PKG_INSTANCE_TRACE, PSYS_PLATFORM_RAPL_PID_OUTPUT |

#### Primecode Documentation — `src/doc/`
| File | Content |
|------|---------|
| `socket_rapl.dox` | Primary Socket RAPL architecture doc (517KB+) |
| `rapl.dox` | RAPL overview — all domains (PKG, PSYS, DRAM, PLATFORM) |
| `rapl_dmr.dox` | DMR-specific: TPMI opcodes, dual hierarchy, FastRAPL extensions |
| `rapl_debug.dox` | RAPL debugging guide |
| `platform_rapl.dox` | Platform RAPL domain |
| `fast_rapl.dox` | Fast RAPL feature details |
| `dram_rapl.dox` | DRAM RAPL with PID_MAX_LIMIT tuning |
| `dmr/dmr_ufs_rapl.dox` | UFS + RAPL interaction on DMR |
| `dmr/dmr_tpmi_rapl_counters.dox` | TPMI counter update mechanism |

---

### Pcode Source Files (CBB)

> Repo: `firmware.power.soc.pcode-cbb-a0`

#### RAPL Core Logic — `source/pcode/flows/slow_limits/rapl/`
| File | Purpose |
|------|---------|
| `rapl.h` | RAPL flow class — receives `RAPL_PERF_LIMIT` HPM msg, computes per-CLOS freq ceilings from power limit + CCF BW utilization. Loads SST_PP slope/base fuse arrays |
| `rapl.cpp` | Implementation: `REGISTER_FLOW(Rapl, rapl, FlowID::rapl)`, runs every 1ms (slow loop). Loads `SST_PP_x_UFS_RAPL_SLOPE_y` / `SST_PP_x_UFS_RAPL_BASE_y` fuses |

#### PLR (Performance Limit Reasons) — `source/pcode/flows/slow_limits/plr/`
| File | Purpose |
|------|---------|
| `plr.h` | Tracks `num_ccps_limited_by_socket_rapl`. PLR bitmask: PKG_PL1_INBAND/CSR/OOB, PKG_PL2_INBAND/CSR/OOB, FAST_RAPL, PLATFORM_PL1/PL2 |
| `plr.cpp` | Counts CCPs limited by Socket/Fast RAPL → increments `SOCKET_RAPL_PERF_STATUS` counter → reported in `LEAF_PERF_STATUS[47:32]` HPM msg to IMH-P |

#### HPM Message Spec — `source/hpm/`
| File | Key Content |
|------|-------------|
| `hpm_msgs.xml` | `RAPL_PERF_LIMIT` (0x14): bits[0:12] PLR flags, bits[24:31] RAPL_PID_FREQ_OUTPUT, bits[32:63] CLOS_0-3_LIMIT. `LEAF_PERF_STATUS` (0x16): SOCKET_RAPL_PERF_STATUS[47:32] |

#### TPMI Register Definitions — `source/tpmi/`
| File | Key Content |
|------|-------------|
| `Struct_all.os.xml` | RAPL_DOMAIN_HEADER, RAPL_POWER_UNIT, RAPL_POWER_LIMIT, RAPL_PERF_STATUS (PWR_LIMIT_THROTTLE_CTR[31:0]), RAPL_ENERGY_STATUS, RAPL_POWER_INFO |
| `AddressMap_TPMI.os.xml` | Socket RAPL TPMI addresses: DOMAIN_HEADER (0xCC00), POWER_UNIT (0xCC08), PL1_CONTROL (0xCC10), PL2_CONTROL (0xCC18), PL4_CONTROL (0xCC28), ENERGY_STATUS (0xCC38), PERF_STATUS (0xCC40), PL_INFO (0xCC48) |

#### FW Update Variable DB
| File | Key Content |
|------|-------------|
| `source/pcode/flows/fw_update/fwu_var_frz_db.json` | `Plr::num_ccps_limited_by_socket_rapl` — debug/telemetry snapshot variable |

#### Pcode Simulation Tests — `verif/`
| Path | Tests |
|------|-------|
| `foxcode/fox2/tests/cbb_rapl.cfg` | Socket RAPL config + PERF_STATUS HPM checks |
| `foxcode/fox2/tests/cbb_plr.cfg` | PLR with SOCKET_RAPL_PERF_STATUS (900+ lines) |
| `foxcode/fox2/tests/cbb_ring_plr.cfg` | Ring PLR with FAST_RAPL flag |
| `foxcode/lib/rapl_*.rb` | Ruby RAPL libs: `rapl_interface.rb`, `rapl_domain.rb`, `rapl_checker.rb`, `rapl_time.rb` |
| `tests/peci/peci_pcs_read_rapl_performance_status.rb` | PECI PCS read RAPL_PERF_STATUS |

---

### Source Code Flow Summary

```
┌──────────────────────────────────────────────────────────────────────┐
│                    PRIMECODE (IMH-P / Root Die)                      │
│                                                                      │
│  TPMI write ──► tpmi_mailbox_commands.cpp                           │
│       │              ↓                                               │
│       │     rapl_vars.hpp (global state)                             │
│       │              ↓                                               │
│       ├──► rapl_pkg_domain.cpp  ──► PID loop (Kp=0x9, Ki=0x39)     │
│       ├──► rapl_psys_domain.cpp ──► Platform PID loop               │
│       ├──► fast_rapl_io.cpp     ──► 500µs excursion handler         │
│       │              ↓                                               │
│       │     rapl_pbm.cpp (PL resolution, min across domains)        │
│       │              ↓                                               │
│       │     rapl_bridge_common.cpp (PID output → CLOS freq limits)  │
│       │              ↓                                               │
│       └──► rapl_hpm_root.cpp ──► HPM RAPL_PERF_LIMIT (0x14)        │
│                     │                  ↓ to IMH-S + CBBs            │
│                     │                                                │
│  ◄── rapl_hpm_leaf_io.cpp (IMH-S receives, applies to its cores)   │
│                                                                      │
│  svid_pmeter.cpp ──► energy telemetry ──► RAPL energy input         │
│  base_ia_main.cpp ──► setCoreClosRaplLimits() on IMH cores          │
└──────────────────────────────────────────────────────────────────────┘
                            │ HPM 0x14
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      PCODE (CBB Die)                                 │
│                                                                      │
│  HPM RAPL_PERF_LIMIT (0x14) ──► rapl.h/cpp                         │
│       ↓                                                              │
│  Compute per-CLOS freq ceiling (fuse slope/base × utilization)      │
│       ↓                                                              │
│  SlowLimits ──► apply ceiling to each CCP                           │
│       ↓                                                              │
│  plr.cpp ──► detect SOCKET_RAPL-limited CCPs                       │
│       ↓     count num_ccps_limited_by_socket_rapl                   │
│       ↓                                                              │
│  HPM LEAF_PERF_STATUS (0x16) ──► SOCKET_RAPL_PERF_STATUS[47:32]   │
│       │                         back to IMH-P                        │
│       └──► IMH-P updates TPMI 0xC840 (SOCKET_RAPL_PERF_STATUS)     │
└──────────────────────────────────────────────────────────────────────┘
```

### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->

### NWP Delta

> **Source**: Primecode `dut/nwp_imh_cfg.xml`, `src/cfgdata/nwp_imh/v1_0/svid.xml`, `src/cfgdata/nwp_imh/v1_0/fivr_energy_mapping.hpp`
> **MAS**: [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)

#### NWP Scope Summary

NWP supports **Socket RAPL only**. The following are ZBB (Zero-Based Budget):
- DRAM RAPL
- Platform RAPL / Psys
- SIMPL (Proactive IccMax)
- Fast RAPL
- Fine-Grained Energy Reporting

#### Delta 1: Dual DDR Memory SVID Rails + LPDDR6 Power Delivery

NWP uses LPDDR6 instead of DDR5. LPDDR6 memory power is split across **both MBVR and FIVR**:

**LPDDR6 Power Delivery Map**:

| Component | Power Rail | VR Type | Measurement | Socket RAPL Path |
|---|---|---|---|---|
| LPDDR6 DRAM chips (VDD IO rail 0) | `VCCDDR_HV` (addr 0) | **MBVR** | SVID IMON | `socket_power_vrs_imon` sum |
| LPDDR6 DRAM chips (VDD IO rail 1) | `VCCDDR_HV1` (addr 5) | **MBVR** | SVID IMON | `socket_power_vrs_imon` sum |
| Memory Controller East (on-die logic) | `RA_FIVR_MC_E` | **FIVR** | IIN_ACCUMULATOR telemetry | Primecode `energy_report` FIVR sum |
| Memory Controller West (on-die logic) | `RA_FIVR_MC_W` | **FIVR** | IIN_ACCUMULATOR telemetry | Primecode `energy_report` FIVR sum |
| MC IO (PHY/DFI interface) | `RA_FIVR_FIXDIG_MIO_1/3/4` | **FIVR** | IIN_ACCUMULATOR telemetry | Primecode `energy_report` FIVR sum |

DRAM chips are powered externally (MBVR), while the on-die MC logic + MC IO are powered by on-die FIVRs. Both contribute to Socket RAPL through separate paths.

**DMR → NWP SVID rail change**: DMR has a **single** `VCCDDR_HV` rail spanning both IMH dies. NWP splits this into **two independent rails**:

| SVID Rail | DMR (addr) | NWP (addr) | Classification | Notes |
|-----------|:---:|:---:|---|---|
| `VCCDDR_HV` | 0 | 0 | Non-mandatory | Memory VDD IO rail 0 |
| `VCCDDR_HV1` | — (slot 5 unused) | **5** | Non-mandatory, elective | Memory VDD IO rail 1 (**NWP-only**) |

**Socket RAPL impact**:
- NWP `socket_power_vrs_imon` sums current from **6 VRs** (VCCIN, VCCINF, VCCANA, VCCFA_EHV, VCCDDR_HV, VCCDDR_HV1) vs DMR's 5
- The NN-PID controller receives a higher composite current input from the additional rail
- `VCCDDR_HV1` is listed as **elective/discretionary** — probed via `NoMcaOnError` path, so Socket RAPL must gracefully handle configs where only one DDR rail is populated
- When `VCCDDR_HV1` is absent (discovery failure), Socket RAPL falls back to fuse-based static power (`VCCD1_HV_CPU0_POWER`) — reduces energy measurement accuracy
- Both `VCCDDR_HV` VRs are in `non_mandatory_vr_list` — when absent, DRAM power is invisible to Socket RAPL (only fuse fallback)

#### Delta 2: Non-Mandatory VR Expansion

NWP classifies **4 VRs as non-mandatory** (vs DMR's effectively 0 non-mandatory). When a non-mandatory VR is absent (SVID discovery fails), Socket RAPL uses the **fuse-backed static power estimate** instead of live SVID telemetry:

| Non-Mandatory VR | Fuse Backing | Socket Power Impact |
|---|---|---|
| `VCCDDR_HV` | `VCCD0_HV_CPU0_POWER` | Memory rail 0 — static estimate if VR absent |
| `VCCDDR_HV1` | `VCCD1_HV_CPU0_POWER` | Memory rail 1 — static estimate if VR absent |
| `VCCFA_EHV` | `VCCFA_EHV_CPU0_POWER` | FIVR supply rail — static estimate if VR absent |
| `VCCANA` | `VCCANA0_CPU0_POWER` | Analog rail — static estimate if VR absent |

**Accuracy tradeoff**: Fuse values are static worst-case estimates, not real-time measurements. With up to 4 VRs falling back to fuse values, NWP Socket RAPL PID operates with more measurement uncertainty than DMR.

#### Delta 3: VCCFA_EHV (Analog/Support MBVR) — Removal Pending

`VCCFA_EHV` (SVID addr 4) is a **1.8V MBVR rail** supplying **analog and support functions**: DTS, PLL, BGR, PMAX, DDR-related circuitry, and GPIO (described as "EHV supply for 1276 AIPs" in CBB PD HAS). It is **not** a FIVR output domain — it is architecturally distinct from the internal FIVR domains.

**Spec-confirmed** (DMR SoC PM HAS, CBB PD HAS 0.8, DMR Overview HAS, OKS PAS):
- VCCFA_EHV is an **MBVR** on **SVID address 04h**
- It supplies **special IPs / analog reference** functions, not FIVR regulators directly
- It is separate from internal FIVR output domains (VCCFIXDIG, VCCCFC, VCCUCIeA, etc.)

**Code-confirmed** (`svid.xml`, `fivr_energy_mapping.hpp`):
- Currently in NWP's `socket_power_vrs_imon` array, classified as **non-mandatory** (`non_mandatory_vr_list` index 2)
- Removal from SVID is pending (platform space constraints, <5A draw)
- **If removed**: Socket RAPL loses live current monitoring for this rail → falls back to `VCCFA_EHV_CPU0_POWER` fuse value (static)
- **FIVR-internal telemetry unaffected**: The 12 FIVR domains (via `fivr_energy_mapping.hpp`) continue reporting energy via internal `IIN_ACCUMULATOR` telemetry — this is independent of the SVID VCCFA_EHV rail
- **Net effect**: Socket PL1/PL2 NN-PID accuracy degrades slightly for the analog/support power component, but FIVR domain-level energy reporting is unaffected
- ITD UCIE Reset flow uses **v1_2 (no-op stub)** because "NWP has different FIVR/DTS UCIE rail names" — the FIVR naming divergence is already acknowledged

> **Sources**: [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html), [CBB PD HAS 0.8](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Power%20Delivery/DMR_CBB%20PD%20HAS.0.8.html), [DMR Overview HAS](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/DMR_Overview_HAS.html), [OKS PAS](https://docs.intel.com/documents/server-platform-arch/Oakstream/pas/OksPAS.html)

#### Delta 4: UFS Disabled on IMH — Fixed Mesh Frequency

NWP defaults `UFS_DISABLE=1` (fuse-controlled). The `ufs_perf_p_limit` module is also **commented out** in the DUT config:

| Mesh Domain | DMR (UFS enabled) | NWP (UFS disabled) |
|---|---|---|
| CFCMEM (Memory Mesh) | Dynamic DVFS | **Fixed 2 GHz** |
| CFCIO (IO Mesh) | Dynamic DVFS | **Fixed 2 GHz** |

**Socket RAPL implications**:

1. **Energy reporting still works** — The 12 FIVR domains (including `RA_FIVR_CFCMEM_E/W` and `RA_FIVR_CFCCIO`) continue accumulating `IIN_ACCUMULATOR` telemetry. UFS disabling does not turn off FIVR telemetry.

2. **PID control knob eliminated** — With UFS disabled, Socket RAPL's NN-PID **cannot throttle mesh frequency** to reduce power. On DMR, RAPL can lower CFCMEM/CFCIO frequency as a power reduction lever. On NWP, mesh runs at fixed 2 GHz regardless of power limit pressure.

3. **Power profile is less dynamic** — Mesh power becomes a fixed baseline rather than a variable. The NN-PID must rely entirely on:
   - **Core frequency throttling** (primary actuator)
   - **RACL current limiting** (per-IMH VR TDC)
   - This reduces the response envelope vs DMR

4. **TPMI advertises UFS disabled** — `autonomous_ufs_disabled=1` in TPMI header, so OS/VMM software won't attempt mesh frequency control

5. **CP11.5 (Socket RAPL × UFS)** cross-product still relevant but simplified — RAPL line for CBB fabric freq still applies, but IMH fabric freq is fixed. The `ufs_rapl.hpp` integration point exists but with no dynamic mesh lever.

#### Delta 5: Disabled/ZBB FW Modules Affecting Socket RAPL

| Module | NWP Status | Impact on Socket RAPL |
|---|---|---|
| `rapl_reporting` (v1_0) | **Commented out** | No RAPL telemetry reporting to TPMI consumers — NN-PID runs but status exposure is limited |
| `mem_bw_report` (v2_0) | **Commented out** | Hardcoded `NUM_MEM_CHANNELS=8` (DMR IO); NWP has 32 MCs. No memory bandwidth feedback to RAPL |
| `ufs_perf_p_limit` (v1_0) | **Commented out** | No UFS-based performance P-state limiting |
| DRAM RAPL | **ZBB** | `dram_power_vrs_imon = INVALID` — no live DRAM current monitoring. DRAM power in socket total is via DDR SVID rails only |
| Platform RAPL / Psys | **ZBB** | `platform_power_vrs_imon = INVALID` — no platform-level power coordination |
| Fast RAPL | **Compiled but ZBB** | `fast_rapl_common` + `fast_rapl_io` modules present in DUT config but feature scope says ZBB — negative check only |
| SIMPL | **Compiled** | All 4 state machines present (`simpl_algo`, `simpl_hpm`, `simpl_leaf_state`, `simpl_root_state`, `simpl_tpmi`) — may be active for IccMax proactive control even though ZBB'd at feature level |
| Fine-Grained Energy | **ZBB** | Two separate FIVR energy systems: (1) **PCode CBB** — `FivrEnergyTelemetry` reads CBB FIVRs (CCP/Ring/UCIe/MLC), gated by `DOMAIN_ENERGY_REPORTING_ENABLE` fuse. When ZBB/disabled, PCode stops all CBB per-domain FIVR energy reads. (2) **Primecode IMH** — `energy_report` flow reads IMH FIVRs (MC/VCCI2CA/FIXDIG/CFC) via telemetry push buffer, feeds Socket RAPL energy sum. This path is **independent** of PCode's fuse gate. Net effect: Socket RAPL still gets IMH FIVR power via Primecode, but CBB FIVR per-domain energy is truly lost (not just hidden) |

#### Delta 6: Single SVID Bus (No Bus 1)

NWP has `ALL_CALL_1 = -1` ("cannot be used since local die's Bus1 is not present") and `poll_priority_bus1_vr_array = INVALID`. All VRs are on Bus 0. This simplifies SVID polling but means all 6 socket power VRs share a single bus — potential polling latency impact on SVID telemetry freshness feeding the NN-PID.

#### Delta 7: NWP Socket Power VR Topology Summary

```
                ┌─────────────────────────────────────────────────┐
                │       NWP Socket RAPL Power Input               │
                │                                                 │
                │  Mandatory:                                     │
                │    VCCIN (addr 1) ──────────────┐               │
                │    VCCINF (addr 3) ─────────────┤               │
                │                                 │               │
                │  Non-Mandatory (fuse fallback):  │               │
                │    VCCANA (addr 2) ─────────────┤               │
                │    VCCFA_EHV (addr 4) ──────────┤  socket_      │
                │    VCCDDR_HV (addr 0) ──────────┤  power_       │
                │    VCCDDR_HV1 (addr 5) ─────────┤  vrs_imon     │
                │         [NWP-only, elective]    │               │
                │                                 ▼               │
                │                          ┌──────────┐           │
                │  FIVR Telemetry ────────►│  NN-PID  │           │
                │  (12 domains, all        │  Socket  │           │
                │   enabled, CFCMEM/       │  PL1/PL2 │           │
                │   CFCIO fixed @2GHz)     └────┬─────┘           │
                │                               │                 │
                │                     ┌─────────┼──────────┐      │
                │                     ▼         ▼          ▼      │
                │               Core Freq    RACL     Mesh Freq   │
                │               Throttle    Current    (UFS) ❌    │
                │               (active)    Limit     DISABLED    │
                │                          (active)               │
                └─────────────────────────────────────────────────┘
```

#### Delta 8: Validation Implications

| Area | NWP-Specific Concern | Test Impact |
|---|---|---|
| **SVID discovery** | VCCDDR_HV1 elective — test with 1 DDR rail populated and both | Add config variant to IMON/energy tests |
| **Non-mandatory VR fallback** | 4 VRs may use fuse values — verify fuse→socket power accuracy | New TC: compare IMON vs fuse-based power under load |
| **UFS × RAPL** | Mesh freq fixed — RAPL can only throttle cores | UFS×RAPL test (22021970114) is simplified; verify no false PLR from mesh |
| **PID tuning** | Fewer actuators — NN-PID must converge with core freq only | May need different Kp/Ki weights vs DMR; verify settling time at 450W TDP |
| **Energy accuracy** | Static fuse fallback for up to 4 rails | Verify ENERGY_STATUS accuracy with mixed mandatory/non-mandatory VR presence |
| **VCCFA_EHV removal** | If removed, FIVR supply power is static estimate only | Negative test: remove VCCFA_EHV, verify graceful fallback + energy accuracy |
| **450W TDP** | Higher absolute power → larger PID excursions | Verify PL1/PL2 settling time and oscillation at 450W (vs DMR ~350W) |
| **rapl_reporting disabled** | TPMI consumers may not see full RAPL status | Verify TPMI PERF_STATUS still updates via other paths |
| **VCCC2CSIP domain split** | New FIVR domain adds ~25W; if not in energy mapping, Socket RAPL underreports | Verify FIVR energy mapping includes VCCC2CSIP once implemented (see Delta 9) |

#### Delta 9: VCCCAB → VCCCAB + VCCC2CSIP FIVR Domain Split (Proposed)

> **HSD**: [22021977883](https://hsdes.intel.com/appstore/article-one/#/article/22021977883) — Proposal to add FIVR domain for C2C SIP
> **Status**: Proposed (under review) — not yet implemented in Primecode
> **Contacts**: PwrDel: Bryan Strnad, Package: Jayashree Kar / Sandhya Arikatla, SD: Kevin Kerr / Andy Rehm, Clock: Binta Patel, PNP: Anand Vetcha / Vivek Garg

##### Background

The C2C SIP logic (Nimbus nvhub — die-to-die interconnect) on NWP requires significantly higher voltage than the rest of the CAB (Coherent Agent Bus) domain to meet 2GHz D2D timing targets. This forces a FIVR domain split:

| Parameter | Original Assumption | Revised Estimate | Delta |
|---|---|---|---|
| C2C SIP power (SOCVDD) | ~5W | **~25W** (14 links, 0.94V, 105C, 2GHz) | **+20W** |
| VCCCAB voltage for nvhub timing | 0.66V (default) | **0.86V** (+200mV) | — |
| VCCCAB power at raised voltage | 23.4W | **~40W** | **+16W** |
| **Combined domain power increase** | — | — | **~40W** |

The combined +40W exceeds FIVR sizing limitations → **domain must split**. FIVR ganging is not an option.

##### Proposal

Split `VCCCAB` into two separate FIVR domains:
- **VCCCAB** — stays at low voltage (~0.66V), saves 15-20W by not raising voltage for nvhub
- **VCCC2CSIP** — new 48-bump FIVR domain, runs at ~0.94V to hit 2GHz D2D timing
- Voltage domain crossing at existing ASF boundary (with clock crossing) — no added latency

> **Note**: The domain split also creates a companion digital domain **VCCC2CDIG** that will require ITD/Binning fuse support. See [Delta 10](#delta-10-itdbinning-on-vccc2cdig-and-vccfixdig_ew-fivr-domains) for details.

##### Primecode Implementation Scope (Base FIVR — No ITD)

The base Primecode work for the new HWRS-controlled FIVR domain covers standard FIVR bring-up only. **No voltage programming / ITD is included in this feature** — ITD is tracked separately under [22022032536](https://hsdes.intel.com/appstore/article-one/#/article/22022032536) (Delta 10).

| Work Item | Description |
|---|---|
| **Disable handling** | FIVR disable logic via HWRS (Hardware Reset Sequence) |
| **Error monitoring and reporting** | MCA/error path for new FIVR domain |
| **Topology awareness** | New FIVR domain added to topology data structures |
| **Fuses (presence)** | Presence fuse for new FIVR domain |
| **HWRS** | HWRS integration for disable logic |
| **Topology (shared FIVR logic)** | Shared FIVR infrastructure integration |
| **Presence detection** | New mask/field for FIVR presence detection |

> **Effort estimate**: ~2 weeks
> **Scope**: Standard changes for any new HWRS-controlled FIVR. Voltage programming (ITD) is explicitly **out of scope** for this feature.

##### NWP Physical Topology — Current State

The NWP codebase already has topology awareness of CAB/C2C/UCIe entities but **no VCCC2CSIP FIVR domain** in the energy mapping:

| Entity | Instance | Status |
|---|---|---|
| `ra_fivr_vcccfccab` | 18 | Present in `physical_topology.hpp` — CAB FIVR exists |
| `ra_fivr_vccfixdig_ucie_nw` | 21 | UCIe FIVR NW quadrant |
| `ra_fivr_vccfixdig_ucie_ne` | 22 | UCIe FIVR NE quadrant |
| `ra_ljpll_c2c` | 33 | C2C-specific PLL |
| `isa_cabw0`, `isa_cabe0` | 51, 52 | CAB ISA endpoints (west/east) |
| `UCIEDDA_D2D_0`, `UCIEDDA_D2D_1` | 74, 75 | UCIe DDA D2D instances |
| **VCCC2CSIP FIVR** | — | **Not present** — proposed new domain |
| **VCCC2CDIG FIVR** | — | **Not present** — proposed new digital domain (ITD/Binning target) |

##### Socket RAPL Impact

**Severity: HIGH** — directly affects energy measurement accuracy and TDP headroom.

1. **FIVR Energy Mapping Gap**: NWP's `fivr_energy_mapping.hpp` currently maps **12 FIVR domains** (identical to DMR). The proposed VCCC2CSIP domain would be a **13th domain** (or replace one). Until this domain is added to the mapping:
   - Socket RAPL's FIVR telemetry path (`IIN_ACCUMULATOR` sum) **underreports** socket energy by ~25W
   - NN-PID receives incorrect (low) power input → **under-throttles** relative to actual power
   - ENERGY_STATUS register reads lower than actual socket power consumption

2. **TDP Impact**: The +20-40W delta directly reduces Socket RAPL headroom:
   - Current NWP TDP target: ~450W
   - If VCCC2CSIP adds 25W visible power, effective headroom drops to ~425W for other domains
   - PL1/PL2 limits may need adjustment to account for higher baseline power

3. **No New MBVR/SVID Rail**: VCCC2CSIP is an **on-die FIVR domain** powered from the VCCFA_EHV MBVR supply. It does **not** add a new SVID VR address. Socket RAPL measures this domain's power via FIVR internal telemetry (`IIN_ACCUMULATOR`), not SVID IMON.

4. **VCCFA_EHV Current Draw Increase**: The new FIVR domain draws from VCCFA_EHV, increasing total FIVR supply current. If VCCFA_EHV is already classified as non-mandatory (Delta 3), the fuse fallback accuracy gets **worse** because the static fuse estimate was sized for 12 FIVR domains, not 13.

5. **RACL Interaction**: RACL monitors per-IMH VR TDC current. Higher VCCFA_EHV draw from the new FIVR may push RACL thresholds closer to trip → potential false RACL limiting under heavy D2D traffic.

6. **D2D Link Activity × RAPL Cross-Product**: With C2C SIP running at 0.94V and consuming ~25W, D2D-heavy workloads (multi-socket coherency, 800GB/s total BW) create a new power profile that Socket RAPL's NN-PID hasn't seen. This is a new cross-product: **Socket RAPL × D2D traffic intensity**.

##### SVID Test Content Impact

| Impact Area | Change Required | Severity |
|---|---|---|
| **New SVID VR discovery** | **None** — VCCC2CSIP is on-die FIVR, not an MBVR | None |
| **SVID IMON tests** | VCCFA_EHV IMON readings will be higher (more FIVR current draw) — update expected ranges | Low |
| **socket_power_vrs_imon array** | **No change** — still 6 MBVRs; FIVR power is via IIN_ACCUMULATOR, not SVID | None |
| **FIVR energy mapping** | Must add VCCC2CSIP domain to `fivr_energy_mapping.hpp` (FIVR_DOMAINS_NUM → 13) with correct `IIN_ACCUMULATOR` + `IIN_NUM_SAMPLES` telemetry IDs | **HIGH** |
| **Telemetry XML** | Must add `RA_FIVR_VCCC2CSIP_FIVR_IIN_ACCUMULATOR` and `RA_FIVR_VCCC2CSIP_FIVR_IIN_NUM_SAMPLES` items | **HIGH** |
| **Energy accuracy tests** | RAPL IMON/energy tests (22022422042, 22022422023) must account for 13th FIVR domain power | Medium |
| **RACL threshold tests** | Verify RACL TDC thresholds accommodate increased VCCFA_EHV current from 13th FIVR | Medium |
| **PnP power budget** | TDP fuse value must account for +25W C2C SIP power; existing fuse checkout test (22022422017) must validate | Medium |

##### Power Estimate Summary (from HSD)

**VCCCAB voltage sensitivity (Pdyn only, no leakage):**

| Voltage Raise | VCCCAB Voltage | Power | Delta |
|:---:|:---:|:---:|:---:|
| +0mV | 0.66V | 23.4W | baseline |
| +100mV | 0.76V | 31W | +7.6W |
| +150mV | 0.81V | 35W | +12W |
| +200mV | 0.86V | 40W | +16W |
| +250mV | 0.91V | 44.5W | +21W |

**C2C SIP power (on SOCVDD):**
- 14 links, Nimbus nvhub at 0.94V, 105C, 2GHz: **~20W** (nvhub only)
- Total with other C2C logic: **~25W** (working assumption)
- Current PnP assumption: ~5W → **4-5× underestimated**

> **Note**: All power numbers are very low confidence with high error bars (based on Nimbus N3→N5 scaling, no I3 data yet)

##### Open Questions for Validation

1. When will VCCC2CSIP telemetry items be added to NWP telemetry XML?
2. What `I_OUT_EXP` and `MAX_I_OUT` scaling factors will be used for the new FIVR domain?
3. Will the VCCFA_EHV non-mandatory fuse (`VCCFA_EHV_CPU0_POWER`) be updated to account for 13 FIVR domains?
4. Is there a cross-product test case for **Socket RAPL × D2D traffic** at 800GB/s BW?
5. Will the domain split affect PkgC entry/exit (D2D link quiescing at different voltage than CAB)?
6. What is the ITD ROI for VCCC2CDIG — confirmed 4-7W savings vs implementation cost? (See Delta 10)

#### Delta 10: ITD/Binning on VCCC2CDIG and VCCFIXDIG_E/W FIVR Domains

> **HSD**: [22022032536](https://hsdes.intel.com/appstore/article-one/#/article/22022032536) — [NWP] ITD/Binning on FIVR VCCC2CDIG and VCCFIXDIG_E, and VCCFIXDIG_W
> **Parent HSD**: [22021977883](https://hsdes.intel.com/appstore/article-one/#/article/22021977883) — VCCCAB → VCCCAB + VCCC2CSIP FIVR domain split
> **VCCFIXDIG tracking**: [14026585116](https://hsdes.intel.com/appstore/article-one/#/article/14026585116) — [NWP] VCCFIXDIG tracking
> **Status**: por-1 (release: nwp_imh-a0) — tagged `FW_IMPACT`, `PRIMECODE_COMMIT`
> **Owner**: sschang3 | **Arch**: Bryan Strnad (bstrnad) | **Design**: twmellin

##### Background — What is ITD?

ITD (Intelligent Thermal Design) adjusts FIVR output voltage based on real-time die temperature readings from DTS (Digital Thermal Sensor). At cold temperatures, silicon requires higher voltage to meet timing; at hot temperatures, leakage increases but voltage can be reduced. Without ITD, voltage must be set for worst-case cold corner → wastes **4-7W** of power that could be reclaimed.

**Binning** is the companion feature: per-part VF (voltage-frequency) curve optimization based on manufacturing process variation. Together, ITD + Binning allow each individual part to run at its optimal voltage for the current temperature, saving power.

> **Relationship to Delta 9**: The base VCCC2CSIP/VCCC2CDIG FIVR domain support (Delta 9) explicitly excludes voltage programming/ITD. ITD/Binning is an **additive feature** on top of the base FIVR support, requiring separate Primecode fuse definitions, DTS temp integration, and post-si tuning effort. The base FIVR runs at a **fixed voltage** without ITD — meaning 4-7W more power consumed at hot temperatures.

##### ITD Algorithm (from PCode)

ITD correction is a piecewise-linear function of voltage and temperature:

```
correction = slope × (cutoff_V - V_input) × (cutoff_Tj - T_current)
```

- **Two-slope model**: slope1 below V_x crossover, slope2 above — allows non-linear V/T correction
- **Floor voltage**: ITD correction not applied below floor_v
- **Temperature clamp**: correction bounded by [MIN_TEMPERATURE, ITD_CUTOFF_TJ]
- **Above-Tj slope**: separate correction for temperatures exceeding cutoff_Tj
- **Negative ITD disable**: can be fused off if negative corrections (voltage reduction at high temp) cause instability

##### Required Fuses for VCCC2CDIG

| Fuse Name | Width | Encoding | Purpose |
|---|---|---|---|
| `VCCC2CDIG_ITD_CUTOFF_V` | 9b | U1.8 V | Voltage below which ITD correction applies |
| `VCCC2CDIG_ITD_SLOPE` | 5b | U-8.13 1/C | Temperature-voltage correction slope |
| `VCCC2CDIG_ITD_TEMP_OFFSET` | 6b | U6.0 C | DTS placement compensation offset |
| `VCCC2CDIG_ACTIVE_VOLTAGE` | 9b | U1.8 V | Uncompensated Vhot baseline voltage |

These follow the established Primecode ITD fuse pattern used by existing domains (VCCUCIEA, VCCFIXDIG, CFC, TA, etc.).

##### VCCFIXDIG_E/W — ITD/Binning for MC + HSF

Per [14026585116](https://hsdes.intel.com/appstore/article-one/#/article/14026585116), on NWP the **VCCFIXDIG_E/W** rails power the **Memory Controller (MC) + HSF** (High Speed Fabric). These domains already have ITD fuse definitions in Primecode:

| Fuse (existing pattern) | XML Source | Array Name |
|---|---|---|
| `VCCFIXDIG_%I_ITD_SLOPE` | `fuses_mc_common.xml` | `MC_ITD_SLOPE_ARRAY` |
| `VCCFIXDIG_%I_ITD_CUTOFF_V` | `fuses_mc_common.xml` | `MC_ITD_CUTOFF_V_ARRAY` |
| `VCCFIXDIG_%I_ITD_TEMP_OFFSET` | `fuses_mc_common.xml` | `MC_ITD_TEMP_OFFSET_ARRAY` |
| `VCCFIXDIG_%I_ACTIVE_VOLTAGE` | `fuses_mc_common.xml` | `MC_ACTIVE_VOLTAGE_ARRAY` |

The `%I` instances are defined by `FUSES_MC_VOLTAGE_RAILS`, which maps to the E/W split. The ITD infrastructure for VCCFIXDIG is **already implemented** in Primecode — the NWP delta is that these rails now power MC + HSF (broader scope than DMR), so ITD fuse values may need re-tuning.

##### Socket RAPL Impact

1. **ITD reduces FIVR power by 4-7W**: ITD allows voltage reduction at hot temperatures → directly reduces FIVR current draw → Socket RAPL sees lower energy via IIN_ACCUMULATOR. Without ITD, Socket RAPL measures the worst-case voltage power at all temperatures.

2. **Binning shifts TDP headroom**: Per-part VF curve optimization means each part has different power characteristics. Socket RAPL's NN-PID must handle this variability without re-tuning.

3. **VCCC2CDIG adds another FIVR domain to energy mapping**: Combined with VCCC2CSIP (Delta 9), the domain split creates **two** new domains that must be added to `fivr_energy_mapping.hpp`. FIVR_DOMAINS_NUM may grow from 12 → 14.

4. **ITD voltage adjustment creates dynamic FIVR power profile**: FIVR voltage changes with temperature → power draw is not constant even at fixed frequency. Socket RAPL's 1ms PID loop must track these voltage-driven power changes in addition to workload changes.

5. **VCCFIXDIG_E/W ITD scope broadens on NWP**: Since VCCFIXDIG_E/W now powers MC + HSF (not just MC), ITD corrections on this rail affect a larger power footprint. Incorrect ITD fuse values would cause larger power measurement errors in Socket RAPL.

##### Key Stakeholder Comments (from HSD 22022032536)

- **sschang3**: "As a team, we know how to support ITD on any rail. We need the ROI statement. For 'I', this comes with some effort in Pre-Si (most Primecode support of this new rail from DTS temp readings), along with Post-Si debug/tuning, and Manufacturing. For 'R', we need feedback from PnP on the return."
- **slerner**: "The ROI document for removing ITD is uploaded as an attachment. **Power increases by 4-7W**. Note that **binning is still recommended** for those domains."
- **jgarciab**: Moving to strawman based on review in PM WG, PD WG, and one-off review with relevant stakeholders.

##### Validation Implications

| Area | Concern | Test Impact |
|---|---|---|
| **FIVR energy mapping** | VCCC2CDIG must be added alongside VCCC2CSIP — potentially 14 FIVR domains total | Verify `fivr_energy_mapping.hpp` includes both C2C domains |
| **ITD fuse checkout** | New VCCC2CDIG fuses need validation against DTS readings | Add ITD fuse checkout to RAPL fuse test (22022422017) |
| **Energy accuracy vs temperature** | ITD-corrected voltage creates temperature-dependent power profile | Sweep DTS temperatures, verify ENERGY_STATUS tracks ITD-driven power changes |
| **VCCFIXDIG_E/W scope** | MC + HSF powered from same rail — ITD tuning affects broader power envelope | Verify ITD fuse values are appropriate for combined MC+HSF power scope |
| **Binning × RAPL** | Per-part VF curves mean power at same freq varies across parts | Test RAPL convergence across multiple QDFs with different binning fuses |
| **No-ITD fallback (4-7W penalty)** | If ITD is disabled/zeroed, Socket RAPL sees 4-7W more power at hot | Negative test: zero ITD slopes, verify RAPL still converges (at higher power) |
