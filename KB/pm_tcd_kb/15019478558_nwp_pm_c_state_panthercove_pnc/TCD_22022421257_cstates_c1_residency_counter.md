## Section 1: Architecture / Micro-architecture and Functionality

**C1** is the lightest core sleep state on NWP (PantherCove PNC), entered via the `HALT` instruction or via MWAIT with hint 0x00/0x10. C1 keeps the core powered and clock-gated, allowing the fastest exit latency (<1 μs). The **C1 residency counter** MSRs track the cumulative time a core has spent in C1, providing power management visibility to PCode and OS.

### Block Decomposition

```
┌───────────────────────────────────────────────────────────────────────────┐
│            C1 / C1E State Machine and Residency Counting (NWP)           │
└───────────────────────────────────────────────────────────────────────────┘

                 ┌─────────────────────────────┐
                 │         C0 (Active)         │
                 │  CPU executing instructions │
                 └───────────────┬─────────────┘
                                 │
              ┌──────────────────┴──────────────────┐
              │ HALT / MWAIT 0x00      MWAIT 0x10   │
              ▼                                      ▼
    ┌─────────────────────┐             ┌─────────────────────┐
    │   C1 (Halt State)   │             │  C1E (Enhanced C1)  │
    │                     │             │                     │
    │ Clock gated only    │             │ Clock gated         │
    │ FIVR unchanged      │  ◄──────── │ FIVR reduced        │
    │ < 1 μs exit         │ autopromo  │ ~10 μs exit         │
    │                     │  if knob=0 │                     │
    └──────────┬──────────┘             └──────────┬──────────┘
               │                                   │
               │  MSR 0x660 (C1 residency)         │
               │  per-thread counter               │
               │  increments each cycle in C1/C1E  │
               └──────────────┬────────────────────┘
                               │
                               │ Interrupt arrives
                               ▼
                 ┌─────────────────────────────┐
                 │      C0 Resume              │
                 │  Counter snapshot frozen    │
                 │  Delta = time spent in C1   │
                 └─────────────────────────────┘

  NWP scope: 96 cores × 2 threads = 192 C1 residency counter instances
  MSR range: 0x660–0x669 (per-thread C1 dwell, per-core physical)
  PkgC6 residency (0x3F9) stays 0 throughout — ZBB invariant
```

### C1 vs C1E on NWP

| Feature | C1 | C1E (Fast C1E) |
|---------|----|----|
| Entry | HALT / MWAIT 0x00 | MWAIT 0x20 or C1E autopromotion |
| Core clock | Gated | Gated |
| Voltage | Unchanged | Reduced via FIVR |
| Exit latency | < 1 μs | ~10 μs (FIVR ramp) |
| MSR | 0x660–0x669 (C1 dwell) | 0x660–0x669 (C1E dwell) |

### C1 Residency Counter MSRs

| MSR Address | Name | Description |
|-------------|------|-------------|
| 0x660 | IA32_THREAD_C1_RESIDENCY | C1 dwell time, thread 0 |
| 0x661 | IA32_THREAD_C1_RESIDENCY | C1 dwell time, thread 1 |
| 0x3FC | IA32_C3_RESIDENCY | Maps to C6 on NWP |
| 0x3FD | — | Unused on NWP |

> **NWP Note:** C1 residency is tracked per-thread via MSR range 0x660–0x669. Each of the 96 cores (2 CBBs × 48) has its own per-thread residency counter.


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

C1 entry:
```
OS executes HALT or MWAIT 0x00/0x10 → Core enters C1 → Clock gated
  → Interrupt arrives → Core exits C1 → Resumes from next instruction
```

The OS reads `mperf` / `aperf` ratio to estimate effective CPU utilization; C1 time is reflected in `mperf` dropping below `tsc` rate.

## Section 3: Reset, Power, and Clocking

- C1 residency counters are **not reset** on wakeup — they accumulate monotonically since last platform reset
- Counters are reset on `CPUID` after `RESET#` assertion
- 64-bit counter — wraps approximately every 584 years at 3 GHz

## Section 4: Programming Model

```python
# Read C1 residency for all cores, verify they increment during idle
import time
s = sv.socket0
pre = []
for c in range(2):
    for k in range(48):
        val = s.getbypath(f"cbb{c}.compute0.module0.core{k}.msr.ia32_thread_c1_residency_t0").read()
        pre.append((c, k, val))

time.sleep(1)   # let system idle

for i, (c, k, pre_val) in enumerate(pre):
    post_val = s.getbypath(f"cbb{c}.compute0.module0.core{k}.msr.ia32_thread_c1_residency_t0").read()
    delta = post_val - pre_val
    if delta == 0:
        print(f"WARNING: CBB{c} core{k} C1 residency did not increment")
```

## Section 5: Operational Behavior

### TC Coverage Map

| TC HSD | Title | Scope |
|--------|-------|-------|
| [22022423079](https://hsdes.intel.com/appstore/article-one/#/22022423079) | CStates C1 residency counter | — |
| [16030715581](https://hsdes.intel.com/appstore/article-one/#/16030715581) | [PSS]C1 Residency Counter | — |


## Section 6: Corner Cases and Error Handling

- **Counter stuck at zero**: Indicates core never entered C1 (may be running workload) — verify system is idle before checking
- **Counter overflow**: 64-bit counter should never overflow in practice but verify counter width
- **C1 vs C1E residency**: If C1E autopromotion is enabled, OS-requested C1 entries may automatically promote to C1E — verify by checking voltage change on FIVR

## Section 7: Security / Safety / Policy

- C1 residency counters are readable from user-mode with appropriate MSR access — consider filtering in hypervisor for side-channel mitigation

## Section 8: References

- [Core C-States HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_C_States/Core_C_States_HAS.html)
- Intel SDM Vol.3 — IA32_C3_RESIDENCY (0x3FC), Thread C1 Residency MSRs (0x660–0x669)
- [TCD HSD 22022421257](https://hsdes.intel.com/appstore/article-one/#/22022421257)
