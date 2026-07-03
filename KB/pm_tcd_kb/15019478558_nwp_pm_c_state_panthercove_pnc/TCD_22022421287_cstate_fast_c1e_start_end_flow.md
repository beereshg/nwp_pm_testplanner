## Section 1: Architecture / Micro-architecture and Functionality

**Fast C1E** (Enhanced Halt State) is a power optimization state on NWP (PantherCove PNC) that combines clock gating (like C1) with a FIVR voltage reduction. The **start/end flow** TCD validates that C1E entry and exit sequences complete correctly — voltage transitions, clock gating behavior, and residency counter tracking.

### Fast C1E Start Flow

```
OS: MWAIT 0x20 (or HALT with autopromotion)
    → Core enters C1 → Hardware checks c1e_enable bit
    → c1e_enable=1: FIVR ramp-down to C1E voltage target
    → Clock gate (same as C1)
    → C1E active (core powered but clock+voltage reduced)
```

### Fast C1E End Flow

```
Interrupt arrives → APIC wakes core
    → FIVR ramp-up to C0 nominal voltage
    → Clock ungate
    → Resume instruction fetch
    → C1E exit latency ≈ FIVR ramp time (target: < 10 μs)
```

### Fast C1E Register Checkpoints

| Register | MSR | Expected During C1E | Expected After Exit |
|----------|-----|---------------------|---------------------|
| `msr_power_ctl.c1e_enable` | 0x1FC[1] | 1 | 1 |
| C1 residency counter | 0x660–0x669 | Incrementing | Snapshot frozen |
| FIVR voltage | PythonSV FIVR path | Reduced | Nominal |
| Core state | PM state register | C1E | C0 |


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

Fast C1E does not require additional OS configuration beyond `HALT`/MWAIT. The BIOS-to-OS interface is via ACPI C-state objects:

| ACPI Cx | Maps to | Entry |
|---------|---------|-------|
| C1 | HW C1 | HALT |
| C1E | Fast C1E | HALT + autopromotion |
| C2 | Not supported on NWP | — |
| C6 | HW C6A/C6S | MWAIT 0x60 |

## Section 3: Reset, Power, and Clocking

- FIVR must complete voltage ramp before core clock is ungated on exit
- PLR (Platform Latency Requirement) is not as critical for C1E (< 10 μs) as for C6 (> 100 μs)
- C1E entry and exit must be glitch-free — verify with FIVR telemetry

## Section 4: Programming Model

```python
# Verify C1E start/end flow via FIVR telemetry and residency
s = sv.socket0

# Check C1E is enabled
pwr_ctl = s.cbb0.compute0.module0.core0.msr.msr_power_ctl.read()
assert (pwr_ctl >> 1) & 1 == 1, "C1E must be enabled for this test"

# Measure FIVR voltage during idle (system idle → C1E active)
import time
time.sleep(0.5)  # let cores enter C1E
fivr_v = s.cbb0.compute0.module0.fivr_telemetry.read()
print(f"FIVR voltage during C1E: {fivr_v:#x}")

# Check residency incremented
c1_res = s.cbb0.compute0.module0.core0.msr.ia32_thread_c1_residency_t0.read()
print(f"C1 residency: {c1_res:#x}")
```

## Section 5: Operational Behavior

### TC Coverage Map

| TC HSD | Title | Scope |
|--------|-------|-------|
| [22022423088](https://hsdes.intel.com/appstore/article-one/#/22022423088) | [BEAT] [FV PM/UBOX]GNR: Add a PEGA C1e cross-product test case which u | — |
| [22022423093](https://hsdes.intel.com/appstore/article-one/#/22022423093) | CState Fast C1E: Entry flow_silicon | — |
| [22022423096](https://hsdes.intel.com/appstore/article-one/#/22022423096) | CState Fast C1E: Exit flow_silicon | — |
| [22022423099](https://hsdes.intel.com/appstore/article-one/#/22022423099) | CState Fast C1E: registers_checks_silicon | — |


## Section 6: Corner Cases and Error Handling

- **FIVR ramp incomplete on exit**: If interrupt arrives before FIVR reaches nominal voltage, core may operate at reduced voltage → potential frequency/stability issue
- **C1E not entered despite c1e_enable=1**: Check OS power scheme — some schemes use `HALT` only for C1 and MWAIT for C6 directly
- **Residency counter not incrementing**: Verify core is truly idle (no kernel threads, no IRQs)

## Section 7: Security / Safety / Policy

- Voltage reduction during C1E should not affect secure execution in SMM — verify SMM latency

## Section 8: References

- [Core C-States HAS — Fast C1E Section](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_C_States/Core_C_States_HAS.html)
- [TCD HSD 22022421287](https://hsdes.intel.com/appstore/article-one/#/22022421287)
