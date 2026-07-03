## Section 1: Architecture / Micro-architecture and Functionality

**C-State Exit Actions** define the micro-architectural wake-up sequence executed when a core or module transitions from C6 back to C0. On NWP (PantherCove PNC), exit is triggered by an interrupt (IPI, APIC timer, external interrupt) and involves power restoration, clock ungating, and PLR (Platform Latency Requirement) compliance.

### Exit Action Sequence by C-State Variant

| Step | C6A Exit | C6S Exit | C6S-P Exit | MC6 Exit |
|------|----------|----------|------------|----------|
| 1 | Interrupt arrives | Interrupt arrives | Interrupt arrives | Interrupt to any core |
| 2 | FIVR ramps to C0 | FIVR ramps to C0 | FIVR power-on + ramp | Module FIVR power-on |
| 3 | Core clock ungate | Core clock ungate | Core reset exit | Module clock ungate |
| 4 | Resume fetch @ RIP | Resume fetch @ RIP | Resume from save state | All module cores exit |
| 5 | — | Snoop filter restore | Snoop filter restore | — |

### Exit Latency KPI (PLR compliance)

| C-State | Target Exit Latency | NWP Budget |
|---------|--------------------|-----------:|
| C6A | ≤ 200 μs | TBD from HAS |
| C6S | ≤ 500 μs | TBD from HAS |
| C6S-P | ≤ 1000 μs | TBD from HAS |
| MC6 | ≤ 1000 μs | TBD from HAS |


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

C6 exit is triggered by hardware interrupt delivery. The OS measures exit latency via ACPI `_CSD` (C-State Dependency) and ACPI `_CST` latency fields. The PLR register constrains minimum latency requirement.

```
Interrupt arrives → APIC delivers to core → Core wakes from C6 
  → FIVR ramp (timed by PLR) → Clock ungate → ISR executes
```

**PLR (Platform Latency Requirement):** MSR `MSR_PKGC_IRTL` (0xA08) sets the interrupt response time limit. If the system cannot exit within PLR, package-level entry is inhibited.

## Section 3: Reset, Power, and Clocking

- FIVR voltage ramp rate limits minimum exit latency
- On MC6 exit, all cores in module must exit together (coordinated by PCode)
- PLR must be programmed to account for worst-case C6S-P exit latency

## Section 4: Programming Model

```python
# Measure C6 exit latency using TSC delta
import ctypes
s = sv.socket0

# Force specific core to C6A, time the exit
# (Use hardware performance counter or OS-level latency measurement)
# Verify PLR register is programmed correctly
plr = s.cbb0.compute0.module0.core0.msr.msr_pkgc_irtl.read()
print(f"PLR: {plr:#x}")
```

## Section 5: Operational Behavior

### TC Coverage Map

| TC HSD | Title | Scope |
|--------|-------|-------|
| [22022423070](https://hsdes.intel.com/appstore/article-one/#/22022423070) | CState Exit Actions: verify flow C6A | — |
| [22022423074](https://hsdes.intel.com/appstore/article-one/#/22022423074) | CState Exit Actions: verify flow C6S | — |
| [22022423076](https://hsdes.intel.com/appstore/article-one/#/22022423076) | CState Exit Actions: verify flow C6S-P | — |
| [22022423078](https://hsdes.intel.com/appstore/article-one/#/22022423078) | CState Exit Actions: verify flow MC6 | — |


## Section 6: Corner Cases and Error Handling

- **Exit from power-gated state (C6S-P)**: Requires full micro-architectural state restore from save area — verify all registers restored correctly
- **Spurious wake**: If interrupt arrives immediately after C6 entry starts, PCode must abort entry cleanly
- **MC6 exit race**: If one core in module receives an interrupt while others are still in MC6, the interrupt must wake the module but hold other cores at C6 until they receive their own interrupt

## Section 7: Security / Safety / Policy

- Save state for C6S-P is stored in secure SRAM — verify no leakage of architectural state between tenants

## Section 8: References

- [Core C-States HAS — Exit Actions](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_C_States/Core_C_States_HAS.html)
- Intel SDM — MWAIT, MONITOR, Interrupt delivery to sleeping cores
- [TCD HSD 22022421253](https://hsdes.intel.com/appstore/article-one/#/22022421253)
