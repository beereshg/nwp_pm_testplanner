## Section 1: Architecture / Micro-architecture and Functionality

**AshTree PRT (Power Reference Test)** is a cross-product system-level test that exercises C-state behavior under realistic OS workloads, combining OS-Idle sequences, P-state transitions, and C-state stress into a single reference test suite. On NWP (PantherCove PNC), AshTree PRT validates that C-states interact correctly with P-state scaling, DVFS, and PMX (Power Management Extensions).

### Block Decomposition

```
┌─────────────────────────────────────────────────────────────────────────┐
│                AshTree PRT Test Execution Flow (NWP)                     │
└─────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────┐
  │  NWP SUT: SVOS booted, C-states + P-states enabled               │
  └───────────────────────────────┬───────────────────────────────┘
                                  │
                 ┌──────────────┴────────────────┐
                 │                              │
          PRT variant?                    PRT variant?
                 │                              │
    ┌────────────┴───────┐        ┌─────────┬─────────────┐
    ▼                  ▼              ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Long OS Idle│ │ PEGA        │ │ Solar C+P+D│ │ Silicon    │
│             │ │ CStates +   │ │            │ │ (full)     │
│ System idle │ │ PStates     │ │ Solar +    │ │            │
│ 30+ seconds │ │             │ │ DVFS +     │ │ All above  │
│ Deep C-state│ │ PEGA enable │ │ C-states   │ │ combined   │
│ entry check │ │ + P-state   │ │ concurrent │ │            │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │             │             │             │
       └────────────┴────────────┴────────────┘
                           │
                           ▼
           ┌─────────────────────────┐
           │  PythonSV post-run checks   │
           │  · C6 residency advanced    │
           │  · PkgC6 = 0 (ZBB) ✓       │ ← NWP invariant
           │  · No MCA / IERR            │
           │  · P-state achieved target  │
           └─────────────────────────┘
```

### AshTree PRT Test Modes

| Test | Scope | Key Validation |
|------|-------|----------------|
| `PRT_Long OS Idle` | System-level C-state | Deep C-state entry under OS idle workload |
| `PRT_PEGA CStates/PStates` | PEGA + P-state + C-state | Cross-product: PEGA enable + DVFS interaction |
| `PRT_Solar CStates/PStates/DVFS` | Solar + C-state + DVFS | Solar stress with DVFS transitions |
| `PRT_silicon` | Silicon-level regression | Full suite on NWP silicon |

### Cross-Product Scenarios

| Interaction | Description | Risk |
|-------------|-------------|------|
| P-state change during C6 exit | Frequency change request while core exiting C6 | Race condition |
| DVFS during MC6 | P-state transition while module in MC6 | Clock change during power gate |
| PEGA + C6 | PEGA power gate + core C6 simultaneously | Over-aggressive power gating |
| PMX + C-state | PMX telemetry collection during C-state transitions | Counter corruption |


### NWP-Specific Deltas

| Aspect | DMR (Reference) | NWP (PantherCove PNC) | Impact on Test |
|--------|----------------|----------------------|----------------|
| CBB count | Up to 4 | **2** | All-core loops: `range(4)` -> `range(2)` |
| Cores per CBB | 64 | **48** | Per-CBB loops: `range(64)` -> `range(48)` |
| Total cores | 256 | **96** | Scale workload and verification accordingly |
| PkgC6 | Supported | **ZBB (Zero Bit Budget)** | `IA32_PKG_C6_RESIDENCY` (0x3F9) must stay 0 |
| Register prefix | `cbb{0..3}` | **`cbb{0,1}`** | Adjust all PythonSV paths |
| DCM count | 32 per socket | **12 per socket** | MC6 module loops: `range(32)` -> `range(12)` |
| HW Thread count | 2 per core | **2 per core** | No change |


## Section 2: Interfaces and Protocols

AshTree PRT uses **OS-level scheduling** to drive idle periods and DVFS changes:

```
Test harness: AshTree OS-level runner
  → Drives CPU utilization patterns via linux scheduler
  → Exercises DVFS via /sys/devices/system/cpu/cpufreq/ 
  → Captures C-state residency via /sys/devices/system/cpu/cpu*/cpuidle/
  → Cross-validates with PythonSV register inspection
```

## Section 3: Reset, Power, and Clocking

- PRT_Long OS Idle requires system fully idle for extended period (30+ seconds) to capture deep C-state entry
- Solar component uses solar.sh with NWP-specific config (2 CBBs, 48 cores)

## Section 4: Programming Model

```python
# AshTree PRT example: verify C-state + P-state interaction
# Run from SVOS with PythonSV loaded
s = sv.socket0

# Snapshot pre-test state
pre_c6 = [s.getbypath(f"cbb{c}.compute0.module0.core{k}.msr.ia32_c6_residency").read()
           for c in range(2) for k in range(48)]

# System runs AshTree PRT_Long_OS_Idle (external command)
# Then verify C-state counters advanced and PkgC6 stays 0
post_c6 = [s.getbypath(f"cbb{c}.compute0.module0.core{k}.msr.ia32_c6_residency").read()
           for c in range(2) for k in range(48)]

# Critical: PkgC6 must stay ZBB
assert s.uncore.msr.ia32_pkg_c6_residency.read() == 0, "PkgC6 ZBB violated!"
print(f"C6 residency advanced on {sum(p>r for p,r in zip(post_c6,pre_c6))}/96 cores")
```

## Section 5: Operational Behavior

### TC Coverage Map

| TC HSD | Title | Scope |
|--------|-------|-------|
| [22022423101](https://hsdes.intel.com/appstore/article-one/#/22022423101) | AshTree PRT_Long OS Idle | — |
| [22022423102](https://hsdes.intel.com/appstore/article-one/#/22022423102) | AshTree PRT_PEGA CStates / PStates | — |
| [22022423104](https://hsdes.intel.com/appstore/article-one/#/22022423104) | AshTree PRT_Solar CStates/PStates/DVFS | — |
| [22022423105](https://hsdes.intel.com/appstore/article-one/#/22022423105) | AshTree PRT_silicon | — |


## Section 6: Corner Cases and Error Handling

- **PRT_silicon TC**: Runs full suite — any individual failure breaks the TC. Triage by checking which sub-test failed
- **DVFS during MC6 hang**: If P-state transition is requested while module is in MC6, PCode must sequence correctly — this is a known risk scenario
- **PEGA interaction**: PEGA autonomous power gating must be compatible with C-state entry — verify no double power-gate

## Section 7: Security / Safety / Policy

- AshTree PRT exercises real OS scheduling — may expose timing-dependent security vulnerabilities in C-state transitions

## Section 8: References

- [Core C-States HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_C_States/Core_C_States_HAS.html)
- [AshTree Test Framework Documentation](https://goto.intel.com/ashtree)
- [TCD HSD 22022421289](https://hsdes.intel.com/appstore/article-one/#/22022421289)
