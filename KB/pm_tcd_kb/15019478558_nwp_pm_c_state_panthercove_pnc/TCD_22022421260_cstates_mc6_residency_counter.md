## Section 1: Architecture / Micro-architecture and Functionality

**Module C6 (MC6)** is a module-level sleep state on NWP (PantherCove PNC) where all cores in a DCM (Dual Core Module or similar compute tile unit) have entered C6, allowing the shared module resources (module clock, module FIVR) to be further power-gated. MC6 is coordinated by PCode and enabled when **all cores in a module** reach C6.

NWP has **12 DCMs per socket** organized across 2 CBBs × 6 compute units (modules). Each module contains **8 cores** (48 cores / 6 modules per CBB = 8 cores/module).

### MC6 Residency Counter MSRs

| MSR | Name | Scope | Reset |
|-----|------|-------|-------|
| 0x664 | MODULE_C6_RESIDENCY | Per-module | Platform reset |
| — | MC6 dwell counter | PythonSV PMSB | Per-query |

### MC6 Entry Conditions

| Condition | Requirement |
|-----------|------------|
| All cores in module | Must be in C6 (C6A or C6S) |
| PCode grant | MC6 grant signal issued by PCode |
| Module idle counter | Module idle for > MC6 threshold cycles |

> **NWP Note:** 12 DCMs per socket (6 per CBB × 2 CBBs). All 8 cores per module must be in C6 before MC6 is granted.


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

```
All 8 cores in module enter C6
    → PCode detects all-core-idle in module
    → MC6 grant issued via PCM
    → Module clock gate + module FIVR power-down
    → MC6 residency counter begins incrementing
    → First interrupt to any core → MC6 exit (all cores wake)
```

## Section 3: Reset, Power, and Clocking

- MC6 entry requires coordinated clock gating across all 8 cores in the module
- MC6 exit wakes all cores simultaneously — the interrupting core gets the interrupt, others return to C6 individually if no pending interrupts
- Module FIVR power-down reduces leakage significantly compared to core C6 alone

## Section 4: Programming Model

```python
# Verify MC6 residency across all 12 modules
import time
s = sv.socket0

# Pre-idle snapshot
pre_mc6 = []
for c in range(2):     # 2 CBBs
    for m in range(6): # 6 modules per CBB
        try:
            res = s.getbypath(f"cbb{c}.compute{m}.module_c6_residency").read()
            pre_mc6.append((c, m, res))
        except: pre_mc6.append((c, m, 0))

time.sleep(3)  # allow MC6 to be entered

post_mc6 = []
for c in range(2):
    for m in range(6):
        try:
            res = s.getbypath(f"cbb{c}.compute{m}.module_c6_residency").read()
            post_mc6.append((c, m, res))
        except: post_mc6.append((c, m, 0))

for i, (c, m, pre_r) in enumerate(pre_mc6):
    post_r = post_mc6[i][2]
    delta = post_r - pre_r
    status = "OK" if delta > 0 else "STUCK"
    print(f"CBB{c} Module{m} MC6 residency delta: {delta:#x} [{status}]")
```

## Section 5: Operational Behavior

### TC Coverage Map

| TC HSD | Title | Scope |
|--------|-------|-------|
| [22022423069](https://hsdes.intel.com/appstore/article-one/#/22022423069) | CState Entry Actions: Verify flow MC6 | — |
| [22022423081](https://hsdes.intel.com/appstore/article-one/#/22022423081) | CStates MC6 residency counter  and flow check | — |
| [16030715590](https://hsdes.intel.com/appstore/article-one/#/16030715590) | [PSS]MC6 Residency Counter | — |
| [16030768415](https://hsdes.intel.com/appstore/article-one/#/16030768415) | CStates MC6 residency counter | — |


## Section 6: Corner Cases and Error Handling

- **MC6 not entered despite all cores in C6**: Check if module idle counter threshold is too high, or if one core has pending interrupt preventing C6
- **MC6 residency stuck at 0**: Verify PSS test leaves system fully idle for > MC6 threshold duration (typically 1–2 ms)
- **MC6 exit wakes wrong core**: On interrupt, the correct core (interrupt target) must wake first — verify with ITH/VISA capture

## Section 7: Security / Safety / Policy

- MC6 power-gate must restore all module-shared resources correctly on exit — validated by residency counter + register-check TCs

## Section 8: References

- [Core C-States HAS — Module C-States](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_C_States/Core_C_States_HAS.html)
- [TCD HSD 22022421260](https://hsdes.intel.com/appstore/article-one/#/22022421260)
