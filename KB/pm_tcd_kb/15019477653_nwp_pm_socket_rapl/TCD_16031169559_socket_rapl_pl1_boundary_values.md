# TCD: Socket RAPL - PL1 Boundary Value Conditions

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169559](https://hsdes.intel.com/appstore/article-one/#/16031169559) |
| **Title** | Socket RAPL - PL1 Boundary Value Conditions |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [15019477653 -- NWP PM Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477653) |
| **KB last updated** | 2026-07-18 |
| **KB revision** | 1 |
| **Feature** | Power / RAPL -- Socket RAPL PL1 boundary values (0W, MIN_PL, TDP) |
| **Created from** | Split from TCD 16031169466 -- PL1 boundary scenarios are distinct from reset register state invariants |

## Section 1: Architecture / Micro-architecture and Functionality

This TCD verifies **Socket RAPL PL1 boundary value behavior** on NWP — what happens when PL1 is set to extreme values (0W, MIN_PL) or toggled between boundary values and TDP at runtime under load. It validates clipping, enforcement, and stability at the edges of the PL1 operating range.

> **Architecture overview:** See [TPF 15019477653](https://hsdes.intel.com/appstore/article-one/#/15019477653) Section 2 Design Details for RAPL PID architecture and PL1 enforcement path.

### Functional Scope

- **PL1 = 0W at boot**: OS reads PL1=0W; PrimeCode clips to MIN_PL from PL_INFO; ENERGY_STATUS = 0 at OS handoff
- **PL1 toggle 0W ↔ TDP under load**: runtime PL1 boundary switching; PrimeCode clips 0W → MIN_PL; restores TDP cleanly; multi-cycle stability

### NWP-Specific Deltas
- PL1 MIN_PL value derived from `PL_INFO.MIN_PL` on NWP NIO die
- Single NIO die runs RAPL PID — no dual-IMH coordination

### TC Coverage Map

| TC | Scope | Key Validation |
|----|-------|----------------|
| [22022421931 -- [BEAT][FV PM][AR] Validate RAPL PL1=0 during OS Boot](https://hsdes.intel.com/appstore/article-one/#/22022421931) | PL1=0 at cold boot | ENERGY_STATUS = 0 at OS boot; PL1 clipped to MIN_PL |
| [16031169546 -- [FV PM] Socket RAPL PL1 Toggle 0W to TDP Under Load](https://hsdes.intel.com/appstore/article-one/#/16031169546) | PL1 runtime toggle | PL1=0W clips to MIN_PL; PL1=TDP restores; multi-cycle stability |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Description |
|-----------|----------------|-------------|
| TPMI PL1_CONTROL | `sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control` | PWR_LIM [17:0] — write 0 to test MIN_PL clipping |
| TPMI PL_INFO | `sv.socket0.nio.punit.tpmi.socket_rapl.pl_info` | MIN_PL [35:18] — minimum power limit; MAX_PL1 [17:0] = TDP |
| TPMI ENERGY_STATUS | `sv.socket0.nio.punit.tpmi.socket_rapl.energy_status` | Verify counter = 0 at boot after PL1=0 |
| TPMI PERF_STATUS | `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status` | Verify throttle counter behavior under PL1=MIN_PL |
| sysfs PL1 | `/sys/class/powercap/intel-rapl:0/constraint_0_power_limit_uw` | OS-visible PL1 interface |

---

## Section 3: Reset, Power, and Clocking

- PL1=0 at boot: BIOS programs PL1=0; PrimeCode clips to MIN_PL during PH6 RAPL init
- Reset behavior of PL1 boundary values is covered by sibling [TCD 16031169466 — Reset Register State Invariants](https://hsdes.intel.com/appstore/article-one/#/16031169466)

---

## Section 4: Programming Model

### PL1 = 0W Clipping

When PL1_CONTROL.PWR_LIM is written to 0, PrimeCode clips the effective PL1 to `PL_INFO.MIN_PL`. The RAPL PID controller uses MIN_PL as the target power, not 0W. The register still reads back 0 (the programmed value), but the PID operates at MIN_PL. This is a firmware clip, not a hardware clip — the register accepts any value but the PID enforces MIN_PL as the floor.

### PL1 Toggle Under Load

When PL1 is toggled between 0W (→MIN_PL) and TDP at runtime:
- **0W → TDP**: PrimeCode PID target changes from MIN_PL to TDP; frequency ceiling rises; cores ramp up. NN-PID adapts weights within 3-5× tau.
- **TDP → 0W**: PrimeCode clips to MIN_PL; PID target drops; frequency ceiling decreases; PERF_STATUS increments while throttling.
- Multi-cycle stability: repeated toggles should not cause PID weight divergence or stale state accumulation.

---

## Section 5: Operational Behavior

> **WHAT:** PL1 boundary values are handled correctly — 0W is clipped to MIN_PL, TDP is enforced at rated power, and transitions between boundary values are clean.

### Scenario x Expected Outcome

| # | Scenario | Expected Outcome | Measurable Bar | TC Link |
|---|----------|-----------------|----------------|---------|
| 1 | PL1=0 at cold boot | PrimeCode clips PL1=0 to MIN_PL; ENERGY_STATUS = 0 at OS handoff | `ENERGY_STATUS.ENERGY[31:0] == 0` at OS boot; effective PL1 = `PL_INFO.MIN_PL` | [22022421931](https://hsdes.intel.com/appstore/article-one/#/22022421931) |
| 2 | PL1 toggle 0W→TDP under load | PL1=0 clips to MIN_PL; PL1=TDP restores rated power; no stale throttle state | Each toggle cycle: PL1=0 → power drops to ~MIN_PL ±10%; PL1=TDP → power rises to ~TDP ±10% within 5×tau | [16031169546](https://hsdes.intel.com/appstore/article-one/#/16031169546) |
| 3 | Multi-cycle stability | 10+ PL1 toggle cycles produce repeatable power behavior | Max-min power variance across cycles < 15% of target | [16031169546](https://hsdes.intel.com/appstore/article-one/#/16031169546) |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **PL1 = 0 with LOCK = 1** | BIOS locks PL1=0; OS cannot override — PrimeCode must still clip to MIN_PL | ⚠️ Verification criterion — add LOCK=1 precondition variant to TC 22022421931 | Add locked PL1=0 step |
| **PL1 toggle during PL2 excursion** | PL2 is actively limiting when PL1 toggled — PID must handle both controllers | ❌ Not covered — no TC tests PL1 toggle during PL2 active | Consider adding as variant of TC 16031169546 |
| **PL1 = MIN_PL exactly** | PL1 written to MIN_PL directly (not 0) — should behave same as clipped 0 | ⚠️ Verification criterion — add MIN_PL direct write step | Add as step in TC 22022421931 |

---

## Section 7: Security / Safety / Policy

- PL1=0 is a valid BIOS configuration; PrimeCode MIN_PL clipping ensures cores do not run at 0W (impossible state)
- LOCK ensures OS cannot override BIOS-configured boundary values

---

## Section 8: References

- [Socket RAPL KB](../../pm_features/power_rapl/socket_rapl.md) -- PL1 enforcement, MIN_PL clipping
- [Wave3 Socket RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) -- PL1/PL2 register definitions
- [TCD 16031169466 -- Reset Register State Invariants](https://hsdes.intel.com/appstore/article-one/#/16031169466) -- sibling: reset behavior of these same registers
- [TCD 22022420798 -- Socket RAPL Algorithm Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) -- sibling: runtime PID behavior
