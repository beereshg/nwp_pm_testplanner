## Section 1: Architecture / Micro-architecture and Functionality

**Fast C1E basic functionality** validates end-to-end C1E idle behavior on NWP (PantherCove PNC) — entry, dwell, exit, and residency accumulation. C1E is an enhanced halt state that combines clock gating with FIVR voltage reduction, offering deeper power savings than C1 at the cost of slightly higher exit latency (~10 us vs <1 us).

> **Architecture overview:** See [TPF 15019478560 — Fast C1E](https://hsdes.intel.com/appstore/article-one/#/15019478560) Section 2 Design Details for full-stack cross-layer diagram, start/end flow, and voltage ramp sequence.

### NWP-Specific Deltas

| Aspect | DMR (Reference) | NWP (PantherCove PNC) | Impact on Test |
|--------|----------------|----------------------|----------------|
| CBB count | Up to 4 | **2** | All-core loops: `range(4)` -> `range(2)` |
| Cores per CBB | 64 | **48** | Per-CBB loops: `range(64)` -> `range(48)` |
| Total cores | 256 | **96** | Scale workload and verification accordingly |
| PkgC6 | Supported | **ZBB** | `IA32_PKG_C6_RESIDENCY` (0x3F9) must stay 0 |

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| *(no TCs yet)* | — | — |

## Section 2: Interfaces and Protocols

- `MSR_POWER_CTL` (MSR 0x1FC) bit[1] controls C1E enable
- `IA32_MPERF` / `IA32_APERF` counters freeze during C1E dwell
- C1 residency counters (`IA32_CORE_C1_RESIDENCY`) accumulate during both C1 and C1E

## Section 3: Reset, Power, and Clocking

- C1E entry triggers FIVR voltage ramp-down to C1E target voltage
- C1E exit triggers FIVR voltage ramp-up; clock ungate occurs after voltage settles
- MSR state is preserved across C1E entry/exit (no context save/restore)

## Section 4: Programming Model

C1E is enabled via `MSR_POWER_CTL.c1e_enable` (bit[1]). When enabled, any OS `HALT` instruction causes the core to enter C1E rather than C1. The voltage reduction is handled by FIVR hardware; PCode coordinates the ramp timing.

Key invariants:
- C1E residency is counted in the C1 residency counter (no separate C1E counter)
- `MSR_POWER_CTL` must be consistent across all 96 cores after BIOS init
- C1E dwell must show measurable C1 residency counter progression

## Section 5: Pass/Fail Bar

- With C1E enabled: `IA32_CORE_C1_RESIDENCY` must increment during idle windows (delta > 0 after controlled idle dwell of >= 100 ms)
- C1E entry and exit must complete without hang, MCA, or NLOG error across all 96 cores
- Per-core C1 residency spread (max - min across cores under identical stimulus) must be < 50% of mean residency
- `IA32_PKG_C6_RESIDENCY` (MSR 0x3F9) must remain 0 throughout test

FAIL if any:
- Any core shows zero C1 residency after controlled idle window
- Hang, timeout, or MCA during C1E cycling
- Residency spread exceeds 50% threshold
- Package C6 residency counter increments

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| Rapid C1E entry/exit | Short idle bursts (<1 ms) may not accumulate measurable residency | Not covered | New TC needed for rapid-cycle stress |
| Asymmetric core behavior | One core stuck in C0 while others idle in C1E | Not covered | Add per-core residency check to basic functionality TC |
| C1E under interrupt load | Heavy interrupt rate prevents sustained C1E dwell | Not covered | Verify C1E still enters despite periodic timer interrupts |

## Section 7: Security / Safety / Policy

No security-specific scenarios. C1E does not affect ring/domain isolation.

## Section 8: References

- [Core C-States HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_core_state.html)
- [TPF 15019478560 — Fast C1E](https://hsdes.intel.com/appstore/article-one/#/15019478560)
- Sibling TCDs: [22022421276 — C1E autopromotion](https://hsdes.intel.com/appstore/article-one/#/22022421276), [22022421287 — C1E start/end flow](https://hsdes.intel.com/appstore/article-one/#/22022421287)
