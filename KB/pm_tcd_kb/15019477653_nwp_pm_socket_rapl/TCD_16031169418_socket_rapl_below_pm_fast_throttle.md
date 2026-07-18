# TCD: Socket RAPL - Below-Pm / Fast Throttle

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169418](https://hsdes.intel.com/appstore/article-one/#/16031169418) |
| **Title** | Socket RAPL - Below-Pm / Fast Throttle |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [15019477653 -- NWP PM Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477653) |
| **Siblings** | [22022420798 -- Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) . [22022420806 -- Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) . [22022420813 -- Fuse and BIOS Knobs](https://hsdes.intel.com/appstore/article-one/#/22022420813) . [22022420817 -- HPM Verification](https://hsdes.intel.com/appstore/article-one/#/22022420817) . [22022420821 -- Registers Verification](https://hsdes.intel.com/appstore/article-one/#/22022420821) . [22022420826 -- SVID Reporting](https://hsdes.intel.com/appstore/article-one/#/22022420826) |
| **KB last updated** | 2026-07-18 |
| **Feature** | Power / RAPL -- Socket RAPL below-Pm throttle and FastRAPL |
| **Created from** | Co-Design T2 WHAT-boundary audit 2026-07-18 -- split from TCD 22022420798 |

## Section 1: Architecture / Micro-architecture and Functionality

This TCD verifies the **below-Pm fast_throttle mechanism** and **FastRAPL (500 us loop)** behavior on NWP. When the NN-PID resolved frequency ceiling drops below **Pm** (minimum operating frequency), PrimeCode asserts the **fast_throttle** wire, which triggers clock division and architectural throttle on the affected CBBs. This is a binary, assertional mechanism distinct from the continuous PID convergence behavior validated by sibling TCD 22022420798.

**FastRAPL** operates at a 500 us loop rate (vs 1 ms for Socket RAPL PL1/PL2) and provides faster power limiting feedback for IO power events. FastRAPL has distinct anti-windup behavior and integral max-clipping that differs from the Socket RAPL slow-loop controllers.

> **Architecture overview:** See [TPF 15019477653 -- NWP PM Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477653) Section 2 Design Details for boot flow, NN-PID architecture, and frequency hierarchy.

### Functional Scope

- **fast_throttle assertion** when RAPL_PID_FREQ_OUTPUT < Pm
- **Clock division** applied on affected CBBs when fast_throttle is active
- **Architectural throttle** (arch throttle) concurrent with clock division
- **fast_throttle de-assertion** when PID output recovers above Pm
- **FastRAPL** 500 us loop behavior -- IO power limiting via dedicated fast PID
- **FastRAPL anti-windup** -- integral max-clipping when output saturates
- **FastRAPL initialization** -- extra VRCI telemetry sampling before first PID cycle (HSD 22022442799)

### Below-Pm Mechanism

```
+--------------------------------------------------------------------------+
| PrimeCode NN-PID (NIO root, 1 ms / 500 us loop)                         |
|                                                                          |
|  RAPL_PID_FREQ_OUTPUT = min(all active controller outputs)               |
|                                                                          |
|  IF RAPL_PID_FREQ_OUTPUT >= Pm:                                          |
|    Normal operation -- distribute freq ceiling via HPM 0x14              |
|    fast_throttle = DEASSERTED                                            |
|                                                                          |
|  IF RAPL_PID_FREQ_OUTPUT < Pm:                                           |
|    fast_throttle = ASSERTED                                              |
|    Clock division applied on all active CBBs                             |
|    Architectural throttle engaged on affected cores                      |
|    Effective frequency drops below Pm via clock gating                   |
+------------------------+-------------------------------------------------+
                         |
                         | fast_throttle wire + HPM 0x14 (RAPL_PERF_LIMIT)
                         v
+--------------------------------------------------------------------------+
| CBB PCode (x2 on NWP)                                                   |
|                                                                          |
|  IF fast_throttle ASSERTED:                                              |
|    Apply clock division -- effective frequency << Pm                     |
|    Apply arch throttle -- reduce IPC via instruction throttling          |
|    PERF_STATUS increments (Socket RAPL + Fast RAPL flags set)           |
|    Report LEAF_PERF_STATUS via HPM 0x16                                  |
|                                                                          |
|  IF fast_throttle DEASSERTED:                                            |
|    Remove clock division -- frequency recovers                           |
|    Remove arch throttle -- full IPC restored                             |
+--------------------------------------------------------------------------+
```

### FastRAPL vs Socket RAPL Slow Loop

| Property | Socket RAPL (Slow) | FastRAPL |
|----------|-------------------|----------|
| Loop rate | 1 ms | 500 us |
| Controllers | PL1 x2, PL2 x2 | 1 (IO power) |
| Response time | 3-5x tau | < 4 ms |
| Anti-windup | NN-PID inference-only mode | Integral max-clipping (distinct) |
| Init requirement | Standard NN-PID weight init | Extra VRCI telemetry sampling (HSD 22022442799) |
| PERF_STATUS flag | Socket RAPL PL1/PL2 flags | Fast RAPL flag |
| PLR attribution | SktPL1 / SktPL2 | FastRAPL (higher priority than SktPL1) |

### NWP Applicability

- fast_throttle and FastRAPL are **supported on NWP**
- NWP has 2 CBBs -- fast_throttle affects both CBB0 and CBB1
- NIO root die asserts fast_throttle; CBB PCode enforces
- FastRAPL PEM status readable via CBB TPMI pem_status
- Pm value is fused per SKU

### TC Coverage Map

| TC | Scope | Key Validation |
|----|-------|----------------|
| [22022421978 -- Throttling below Pm](https://hsdes.intel.com/appstore/article-one/#/22022421978) | Below-Pm fast_throttle | fast_throttle asserted when output < Pm; clock div + arch throttle applied; freq drops below Pm; both CBBs affected; recovery when output >= Pm |

### Coverage Gaps (from Co-Design T1 audit)

| Gap | Recommended TC | Priority |
|-----|---------------|----------|
| FastRAPL dedicated FV -- 500 us loop, IO power limiting | *(TC TBD)* -- FastRAPL enforcement, response < 4 ms, anti-windup behavior | H |
| FastRAPL initialization -- VRCI telemetry extra sampling | *(TC TBD)* -- verify no stale prev_ values on first PID cycle | M |
| fast_throttle assertion/de-assertion timing | *(TC TBD)* -- measure latency from PID output < Pm to clock div active | M |
| FastRAPL PERF_STATUS flag attribution | *(TC TBD)* -- verify Fast RAPL flag set in PERF_STATUS when FastRAPL limits | M |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Description |
|-----------|----------------|-------------|
| fast_throttle wire | PrimeCode -> CBB PCode (A2P WP1/WP3) | Binary throttle assertion when PID output < Pm |
| HPM 0x14 | RAPL_PERF_LIMIT | Carries resolved frequency ceiling; fast_throttle flag embedded |
| HPM 0x16 | LEAF_PERF_STATUS | CBB feedback including Socket RAPL + Fast RAPL throttle status |
| TPMI PERF_STATUS | sv.socket0.nio.punit.tpmi.socket_rapl.perf_status | Software-visible throttle counter; Fast RAPL flag bit |
| TPMI PEM_STATUS | sv.socket0.cbb{0,1}.base.tpmi.pem_status | FastRAPL PEM status per CBB |
| TPMI ENERGY_STATUS | sv.socket0.nio.punit.tpmi.socket_rapl.energy_status | Energy accumulation during below-Pm throttle |

> Spec ref: RAPL HAS -- FastRAPL anti-windup, common MRF flow, max-clipped integral behavior; dmr_rapl_simplification.html

---

## Section 3: Reset, Power, and Clocking

- fast_throttle is de-asserted during reset; no residual throttle after warm reset
- FastRAPL PID state re-initialized at PH6 after reset
- FastRAPL VRCI telemetry requires extra sampling before first PID cycle post-reset (HSD 22022442799)
- Clock division removed when fast_throttle de-asserts -- frequency recovery is immediate
- Pm value is fuse-defined and does not change across resets

---

## Section 4: Programming Model

### Verifying fast_throttle Behavior

1. Program PL1 to a value that will produce RAPL_PID_FREQ_OUTPUT < Pm under high load
2. Apply sustained high workload (e.g. all-core AVX)
3. Observe: effective frequency drops below Pm; clock division active
4. Read TPMI PERF_STATUS: throttle counter increments; Socket RAPL flags set
5. Relax PL1 to value above current power draw
6. Observe: fast_throttle de-asserts; frequency recovers above Pm; clock div removed

### Verifying FastRAPL

1. Configure FastRAPL with a power target that will trigger under IO load
2. Apply IO-intensive workload
3. Observe: FastRAPL PEM_STATUS shows active limiting within < 4 ms
4. Read TPMI PERF_STATUS: Fast RAPL flag set
5. Verify PLR priority: FastRAPL > SktPL1 when both active

On NWP: validation via sv.socket0.nio.punit.* for NIO PrimeCode state, sv.socket0.cbb{0,1}.* for CBB PCode state.

---

## Section 5: Operational Behavior

> **WHAT:** Below-Pm fast_throttle mechanism correctness and FastRAPL enforcement behavior.

**Pass/fail bar:**
- fast_throttle ASSERTED when RAPL_PID_FREQ_OUTPUT < Pm
- Clock division applied on both CBB0 and CBB1 when fast_throttle active
- Architectural throttle engaged concurrently with clock division
- Effective frequency drops below Pm during fast_throttle
- fast_throttle DE-ASSERTED when PID output recovers >= Pm; frequency recovers
- PERF_STATUS increments during fast_throttle; correct flag bits set
- FastRAPL response time: < 4 ms
- FastRAPL anti-windup: integral max-clipping prevents overshoot after saturation
- No stale fast_throttle after warm reset

**Out of scope:**
- NN-PID convergence quality (response/settling time for PL1/PL2) -> TCD 22022420798
- Register interface correctness -> TCD 22022420821
- HPM messaging path -> TCD 22022420817

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|------------------|
| PL1 = 0 W (extreme low limit) | RAPL_PID_FREQ_OUTPUT < Pm; fast_throttle asserted; max clock division |
| PL1 just above Pm power equivalent | Borderline -- PID output oscillates around Pm; fast_throttle may chatter |
| fast_throttle + Prochot simultaneous | Both throttle mechanisms active; most restrictive dominates |
| FastRAPL output saturates (integral max-clip) | Anti-windup engages; learning disabled (inference-only mode); output held at saturation limit |
| FastRAPL init with stale VRCI telemetry | If extra sampling skipped: first PID cycle uses stale prev_ values; inaccurate delta -> incorrect first output (HSD 22022442799) |
| Warm reset during active fast_throttle | fast_throttle de-asserted; clock div removed; PID re-initialized at PH6; no residual throttle |
| FastRAPL + Socket RAPL PL1 both active | PLR priority: FastRAPL > SktPL1; PERF_STATUS reflects higher-priority reason |
| Only CBB0 under load, CBB1 idle | fast_throttle applies to both CBBs equally; CBB1 may see unnecessary throttle (by design -- socket-level limit) |

---

## Section 7: Security / Safety / Policy

- fast_throttle is a safety mechanism preventing excessive power draw beyond socket capability
- Clock division is a hardware-enforced mechanism -- cannot be overridden by software
- FastRAPL provides faster response than slow-loop PL1/PL2 for IO power events
- No security-sensitive data in fast_throttle or FastRAPL paths

---

## Section 8: References

- [Socket RAPL KB -- socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md) -- NN-PID architecture, fast_throttle, FastRAPL
- [TCD 22022420798 -- Socket RAPL Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) -- NN-PID convergence (sibling TCD)
- [DMR RAPL Simplification HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_rapl_simplification.html) -- FastRAPL anti-windup, max-clipped integral
- [DMR IMH NNPID HAS v0.5](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/NNPID%20HAS/NNPID%20HAS.html) -- NN-PID output range, Pm handling
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html) -- NWP RAPL scope
- HSD [22022442799](https://hsdes.intel.com/appstore/article-one/#/22022442799) -- FastRAPL init fix (extra VRCI sampling)
- Co-Design T2 audit 2026-07-18 -- WHAT-boundary split from TCD 22022420798 [spec ref: RAPL HAS -- FastRAPL/anti-windup/max-clipped-integral]
