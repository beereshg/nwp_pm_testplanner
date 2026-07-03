## Section 1: Architecture / Micro-architecture and Functionality

**C-State Demotion/Undemotion** is a PCode-managed policy mechanism on NWP (PantherCove PNC) that dynamically adjusts the maximum allowed C-state a core can enter. PCode can **demote** a core from C6 to C1 (or C6S to C6A) when system conditions (high-frequency wake-up rate, latency sensitivity) indicate deep C-states would hurt performance. **Undemotion** re-allows deeper C-states when conditions improve.

### Block Decomposition

```
┌────────────────────────────────────────────────────────────────────────┐
│           Demotion / Undemotion Decision Flow (NWP)                    │
└────────────────────────────────────────────────────────────────────────┘

     ┌──────────────────────────────────────────────────┐
     │ OS requests deep C-state (C6A via MWAIT 0x60)              │
     └───────────────────────────┬──────────────────────┘
                              │
                              ▼
     ┌──────────────────────────────────────────────────┐
     │ Acode evaluates wake-rate sample                            │
     │ Compare against MSR_C6_THRESHOLD (0x1A4)                   │
     └───────────────────────────┬──────────────────────┘
                              │
          ┌─────────────────┴────────────────────┐
   Wake-rate         |              Wake-rate
   < threshold       |              >= threshold
   (undemotion)      |              (demotion)
         ▼           |                    ▼
  ┌───────────────┐   |          ┌────────────────────┐
  │  No demotion   │   |          │  Apply demotion:    │
  │  Enter C6A as  │   |          │  C6A→C6S→C1→C0     │
  │  requested     │   |          │  (via MSR 0xE2     │
  │                │   |          │   bits [27:26])     │
  └───────────────┘   |          └─────────┬──────────┘
                         |                    │
                         |                    ▼
                         |     ┌────────────────────┐
                         |     │ Core enters C1   │
                         |     │ (not C6A)        │
                         |     └─────────┬──────────┘
                         |                    │
                         |                    ▼  undemotion timer expires
                         |     ┌────────────────────┐
                         |     │ Undemotion:       │
                         └─────► │ Allow C6A again  │
                               └────────────────────┘

  MSR 0xE2 key bits: [26]=C1_demotion_enable  [27]=C6→C1_demotion_enable
  Acode drives decisions; PCode enforces the resulting C-state limit.
  All 96 cores must have consistent demotion bits (validate all CBBs).
```

### Demotion Policy Hierarchy

```
OS requests C6A → PCode evaluates demotion policy
    ├─► No demotion: Core enters C6A as requested
    ├─► C6A→C6S demotion: Core enters C6S instead
    ├─► C6→C1 demotion: Core enters C1 (shallow save)
    └─► C1→C0 demotion: Core stays in C0 (policy override)
```

### Key MSRs for Demotion Configuration

| MSR | Name | Field | Purpose |
|-----|------|-------|---------|
| 0xE2 | `IA32_CST_CONFIG_CONTROL` | [25:24] | Max C-state allowed (HW enforcement) |
| 0xE2 | `IA32_CST_CONFIG_CONTROL` | [26] | C1 demotion enable |
| 0xE2 | `IA32_CST_CONFIG_CONTROL` | [27] | C6→C1 demotion enable |
| 0x1A4 | `MSR_C6_THRESHOLD` | [7:0] | C6 demotion threshold count |

### Demotion/Undemotion Policy Registers

| Register | Description | NWP Path |
|----------|-------------|---------|
| `CLOCK_CST_CONFIG_CONTROL` (0xE2) | Main C-state config, demotion bits | Per-core MSR |
| `MSR_C1_DEMOTION_ENABLE` | C1 demotion enable | MSR 0xE2[26] |
| `MSR_C6_DEMOTION_ENABLE` | C6 demotion enable | MSR 0xE2[27] |
| `MSR_C_THRESHOLD` | Wake rate threshold for demotion | MSR 0x1A4 |
| Acode interaction | Acode drives demotion decisions | Via Acode registers |


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

Demotion is transparent to the OS — the OS requests C6 but the hardware enters C1. The ACPI C-state latency values in `_CST` remain unchanged; PCode internally enforces the demotion.

**Acode interaction**: NWP uses **Acode** (Autonomous Code running on the cbb compute tile) to evaluate real-time demotion decisions. Acode samples wake-rate (wakeups/second) and compares against programmed thresholds.

## Section 3: Reset, Power, and Clocking

- Demotion state (current demoted C-state limit) is reset on platform warm reset
- Undemotion timer must expire before returning to deep C-states
- Hysteresis is built into undemotion to prevent ping-pong between C1 and C6

## Section 4: Programming Model

```python
# Configure and verify C6->C1 demotion
s = sv.socket0

# Read current demotion configuration from MSR 0xE2 on all cores
for c in range(2):
    for k in range(48):
        cst_cfg = s.getbypath(f"cbb{c}.compute0.module0.core{k}.msr.ia32_cst_config_ctrl").read()
        c1_dem = (cst_cfg >> 26) & 1
        c6_dem = (cst_cfg >> 27) & 1
        print(f"CBB{c} core{k}: c1_demotion={c1_dem} c6_demotion={c6_dem}")

# Verify demotion matches BIOS knob setting
# If BIOS set DemotionPolicy=Enabled, all cores should have demotion bits set
```

## Section 5: Operational Behavior

### TC Coverage Map

| TC HSD | Title | Scope |
|--------|-------|-------|
| [22022423083](https://hsdes.intel.com/appstore/article-one/#/22022423083) | CStates: C6A Demotion policy check | — |
| [22022423084](https://hsdes.intel.com/appstore/article-one/#/22022423084) | CStates: C6S Demotion policy check | — |
| [22022423085](https://hsdes.intel.com/appstore/article-one/#/22022423085) | CStates: C6SP Demotion policy check | — |
| [22022423086](https://hsdes.intel.com/appstore/article-one/#/22022423086) | CStates: Demotion/Undemotion: CLOCK_CST_CONFIG_CONTROL_MSR(0XE2) silic | — |
| [22022423087](https://hsdes.intel.com/appstore/article-one/#/22022423087) | CStates: Demotion: Acode interaction_silicon | — |
| [16030715552](https://hsdes.intel.com/appstore/article-one/#/16030715552) | [PSS]C1/C6 Demotion/Undemotion BIOSKnobs | — |


| Scenario | TC |
|----------|---|
| C6A demotion policy validation | CStates: C6A Demotion policy check |
| C6S demotion policy validation | CStates: C6S Demotion policy check |
| C6SP demotion policy validation | CStates: C6SP Demotion policy check |
| MSR 0xE2 demotion bits checkout | CLOCK_CST_CONFIG_CONTROL_MSR TC |
| Acode interaction with demotion | CStates: Demotion: Acode interaction |
| BIOS knob→register propagation | PSS BIOS Knobs TC |

## Section 6: Corner Cases and Error Handling

- **Stuck in demotion**: If PCode never undemotes (undemotion timer too long), cores stay in C1 → residency counters show no C6 dwell → power regression. Verify undemotion timer is correctly programmed.
- **Acode→PCode handshake failure**: Acode demotion decision must be received by PCode within the decision window. Missed handshake = no demotion applied.
- **MSR inconsistency across CBBs**: If CBB0 and CBB1 have different demotion policy bits, behavior is undefined. Validate all 96 cores have consistent MSR 0xE2.

## Section 7: Security / Safety / Policy

- Demotion must not be applied in real-time critical contexts (e.g., interrupt handlers in OS). Kernel-level latency-sensitive threads should set `pm_qos` to prevent demotion.

## Section 8: References

- [Core C-States HAS — Demotion Section](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_C_States/Core_C_States_HAS.html)
- Intel SDM — MSR 0xE2 (IA32_CST_CONFIG_CONTROL) demotion bits
- [TCD HSD 22022421266](https://hsdes.intel.com/appstore/article-one/#/22022421266)
