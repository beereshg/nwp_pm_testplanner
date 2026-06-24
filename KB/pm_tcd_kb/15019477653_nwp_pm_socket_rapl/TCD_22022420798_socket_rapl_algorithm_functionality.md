# TCD: Socket RAPL Algorithm & Functionality Verification
<!-- sibling: TCD_22022420806_socket_rapl_cross_products.md -->

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420798](https://hsdes.intel.com/appstore/article-one/#/22022420798) |
| **Title** | Socket RAPL Algorithm & Functionality Verification |
| **Status** | open |
| **Owner** | mps |
| **Parent TP** | [15019477653 — NWP PM Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477653) |
| **KB last updated** | 2026-06-24 |
| **Feature** | Power / RAPL — Socket RAPL |

## Section 1: Architecture / Micro-architecture and Functionality

**Socket RAPL (Running Average Power Limit)** enforces socket-level and platform-level power limits using closed-loop **NN-PID (Neural Network PID)** control implemented in PrimeCode on the **NIO / IMH-P root die**. At runtime, PrimeCode samples power telemetry, computes the required performance ceiling, resolves the minimum limit across active controllers, and distributes the result to all compute dies via **HPM 0x14** as **RAPL_PERF_LIMIT**. Each CBB PCode enforces the received limit locally and reports status through **HPM 0x16**.**NN-PID (Neural Network PID)** control implemented in PrimeCode on the **NIO / IMH-P root die**. At runtime, PrimeCode samples power telemetry, computes the required performance ceiling, resolves the minimum limit across active controllers, and distributes the result to all compute dies via **HPM 0x14** as **RAPL_PERF_LIMIT**. Each CBB PCode enforces the received limit locally and reports status through **HPM 0x16**.

**Active controllers**: Socket PL1 ×2 | Socket PL2 ×2 | Platform PL1 ×2 | Platform PL2 ×2 | FastRAPL ×1 (500 µs loop)

### Runtime Control Flow

1. BIOS programs boot-time RAPL configuration through CSR / TPMI
2. PrimeCode initializes RAPL controllers during platform initialization (PH6)
3. PrimeCode periodically reads IMON power telemetry (1 ms loop)
4. Each active controller computes an updated frequency ceiling
5. PrimeCode resolves effective ceiling = min(all active controller outputs)
6. PrimeCode distributes ceiling to all active CBBs via HPM 0x14
7. If resolved ceiling < **Pm** → PrimeCode asserts **fast_throttle** (clock div + arch throttle)

### Block Decomposition

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Boot Time (BIOS CPL3)                                                    │
│  ┌──────────┐ programs   ┌────────────────────────────────────────────┐  │
│  │   BIOS   ├───────────►│ TPMI SRAM (NIO / IMH-P die)               │  │
│  │ CSR +    │            │ PL1_CONTROL: PWR_LIM, TIME_WINDOW, LOCK   │  │
│  │ TPMI     │            │ PL2_CONTROL: PWR_LIM, TIME_WINDOW, LOCK   │  │
│  └──────────┘            └────────────┬──────────────────────────────┘  │
│                                       │ PrimeCode reads at runtime       │
└───────────────────────────────────────┼──────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼──────────────────────────────────┐
│ Runtime: PrimeCode NN-PID (NIO / IMH-P root, 1 ms loop)                 │
│                                                                          │
│ Flow:                                                                    │
│   1. Read IMON telemetry → actual power                                  │
│   2. Compute error = PL_target − actual_power                            │
│   3. Generate RAPL_PID_FREQ_OUTPUT per controller                        │
│   4. RAPL_PERF_LIMIT = min(all active controller outputs)                │
│   5. Send HPM 0x14 → NIO Leaf → CBB0, CBB1                              │
│   6. Assert fast_throttle if output < Pm                                 │
└───────────────────────┬──────────────────────────────────────────────────┘
                        │ HPM 0x14: RAPL_PERF_LIMIT (freq ceiling)
┌───────────────────────▼──────────────────────────────────────────────────┐
│ CBB PCode (×2 on NWP)                                                    │
│ Enforces received ceiling, updates throttle accounting (PERF_STATUS),    │
│ reports LEAF_PERF_STATUS through HPM 0x16                                │
└──────────────────────────────────────────────────────────────────────────┘
```

### Socket RAPL Properties

| Property | PL1 | PL2 |
|----------|-----|-----|
| Default value | TDP (fused) | 1.2 × TDP |
| PID target | 100% of PL1 | 90% of programmed PL2 |
| Time window (τ) | 1–5 s (clipped) | 11.7–39 ms (clipped) |
| Loop rate | 1 ms | 1 ms |
| Response time | 3–5 × τ | ~8 ms |
| Settling time | 3–5 × τ | ~25 ms |
| Steady-state error | < 1% | < 1% |
| FastRAPL response | — | < 4 ms |

### NWP-Specific Deltas

- NWP implements **2 CBBs** only (cbb0 + cbb1) — loop `range(2)` not `range(4)`
- NWP uses **NIO** as the root PM path: `sv.socket0.nio.punit.*`
- Legacy RAPL MSRs **0x610 / 0x611 / 0x606** are **deprecated** — reads return 0, writes silently dropped
- Runtime programming and validation shall use **TPMI** only
- FastRAPL is supported on NWP
- Default limits: **PL1 = fused TDP**, **PL2 = 1.2 × fused TDP**

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022421962 — RAPL Cold TDP checkout](https://hsdes.intel.com/appstore/article-one/#/22022421962) | Cold boot defaults | PL_INFO / default fuse initialization |
| [22022421965 — RAPL Response time and quality](https://hsdes.intel.com/appstore/article-one/#/22022421965) | Response time / quality | NN-PID convergence; freq oscillation ≤ ±1 bin |
| [22022421976 — Sweep CPU RAPL limits](https://hsdes.intel.com/appstore/article-one/#/22022421976) | Sweep limits | Runtime TPMI PL1 writes; ENERGY_STATUS validation |
| [22022421978 — Throttling below Pm](https://hsdes.intel.com/appstore/article-one/#/22022421978) | Below-Pm throttle | fast_throttle assertion; clock div + arch throttle |
| [22022421989 — Verify capability to change limits](https://hsdes.intel.com/appstore/article-one/#/22022421989) | Runtime changes | Re-convergence after TPMI update |
| [22022421931 — Validate RAPL=0 during OS Boot](https://hsdes.intel.com/appstore/article-one/#/22022421931) | Counter initialization | ENERGY_STATUS / PERF_STATUS reset at boot |
| [[PSS] PEM — Socket RAPL PL1](https://hsdes.intel.com/appstore/article-one/#/16030715720) | Socket RAPL PL1 | PL1 enforcement via NN-PID |
| [[PSS] PEM — Socket RAPL PL2](https://hsdes.intel.com/appstore/article-one/#/16030715722) | Socket RAPL PL2 | PL2 enforcement via NN-PID |
| [[PSS] Perf Status — Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/16030715724) | PERF_STATUS | Throttle accounting accuracy |
| [[PSS] PLR — Socket RAPL PL2](https://hsdes.intel.com/appstore/article-one/#/16030715726) | PL2 response | PL2 step response; settling time |
| [[PSS] PLR — Socket RAPL PL1](https://hsdes.intel.com/appstore/article-one/#/16030715728) | PL1 response | PL1 step response; settling time |
| [[PSS] Verify Mistletoe PRT](https://hsdes.intel.com/appstore/article-one/#/16030715734) | PRT validation | OOB / platform runtime path |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| TPMI | `PL1_CONTROL` | Runtime programming of PL1 — PWR_LIM, TIME_WINDOW, LOCK |
| TPMI | `PL2_CONTROL` | Runtime programming of PL2 — same format |
| TPMI | `ENERGY_STATUS` | Energy accumulation — ENERGY [31:0] (0.0625 J/LSB), TIME [63:32] (10 ns) |
| TPMI | `PERF_STATUS` | Throttle accounting — PWR_LIMIT_THROTTLE_CTR [31:0] |
| TPMI | `PL_INFO` | Capability discovery — MAX_PL1, MIN_PL, MAX_PL2 (RO) |
| CSR | `PKG_RAPL_LIMIT` | BIOS boot-time programming; locked before OS handoff |
| MSR 0xBC | `IA32_MISC_PACKAGE_CTLS` | Energy filtering control [0] — not deprecated on NWP |
| MSR 0x610 / 0x611 / 0x606 | Deprecated | Not supported on NWP; reads = 0; writes silently dropped |
| OOB | PECI-over-MCTP / IPMI | BMC / NM access path to TPMI via OOBMSM |

---

## Section 3: Reset, Power, and Clocking

- RAPL PID state is not retained across reset; PrimeCode reinitializes during **PH6**
- BIOS programs boot-time defaults before OS handoff; CSR locked at boot
- `fast_throttle` wire is reset on warm reset and re-armed during PH6 initialization
- Socket and platform RAPL controllers initialize independently at PH6
- `ENERGY_STATUS` resets to 0 on cold reset; **not reset on warm reset** — software must handle rollover
- `PERF_STATUS` throttle counter: reset on cold reset; retention behavior on warm reset must be validated

---

## Section 4: Programming Model

**Power unit**: U11.3 format — 1 LSB = 0.125 W

**Time window encoding**: `T[19:17] × 2^T[22:20]` (exponential format)

Programming rules:
- Out-of-range `TIME_WINDOW` values shall be clipped to supported range (PL1: 1–5 s; PL2: 11.7–39 ms)
- `PWR_LIM` values above maximum shall be clipped by PrimeCode
- Runtime software shall use **TPMI** — deprecated MSR programming shall not be used on NWP
- Setting PL2 < PL1 shall be rejected or clipped per platform policy

---

## Section 5: Operational Behavior

Socket RAPL shall:
- Monitor runtime power via IMON telemetry (1 ms nominal)
- Enforce programmed power limits through PrimeCode NN-PID control loops
- Distribute the effective performance ceiling to all active compute dies
- Assert fast_throttle when the resolved ceiling is below Pm
- Expose control, status, and accounting through TPMI

This TCD covers: default initialization, runtime programming, convergence quality, throttle accounting, below-Pm behavior, and interface correctness.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|------------------|
| PL1 = 0 W | Clamped to minimum; RAPL_PERF_LIMIT = Pm; fast_throttle asserted |
| PL1 > TDP | Accepted; enforcement depends on measured power |
| TIME_WINDOW out of range | Clipped to valid range by PrimeCode |
| LOCK bit asserted | Writes rejected; reads unaffected |
| Deprecated MSR write | Silent drop; TPMI not updated |
| ENERGY_STATUS overflow | Counter wraps (32-bit monotonic); software must handle rollover |
| OOB and OS both program limits | Last write wins; PCode resolves min(OOB, OS) when both active |
| PL2 < PL1 | Rejected or clipped per implementation policy |

---

## Section 7: Security / Safety / Policy

- BIOS may lock runtime limit registers via TPMI LOCK bit
- CSR `PKG_RAPL_LIMIT` is boot-time only; locked before OS handoff
- TPMI is the sole supported runtime interface on NWP
- OOB access (PECI-over-MCTP) is subject to platform authentication and policy
- Validation shall use supported interfaces only (TPMI, not deprecated MSRs)

---

## Section 8: References

- [Socket RAPL KB — socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md) — NN-PID architecture, HPM topology, KPI table
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — RAPL PH6 init, fast_throttle, TPMI mapping
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html) — Socket RAPL feature applicability
- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) — TPMI register definitions, PL1/PL2 algorithm
- [DMR IMH PM HAS §7.3](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) — NN-PID controller, HPM 0x14/0x16
