## Section 1: Architecture / Micro-architecture and Functionality

**C-State Entry Actions** define the micro-architectural sequence executed when a core or module transitions into a sleep state (C6A, C6S, C6S-P, or MC6). On NWP (PantherCove PNC), entry actions include LLC cache flush, PCM messaging to PCode, voltage droop, and clock gating. Each C6 variant has a different depth of entry action.

### T2 Boundary Notes (2026-07-19)

- This TCD keeps core-level logical entry flow ownership.
- Module MC6 electrical entry sequencing is split to `TCD_NEW_mc6_entry_sequence.md`.

### Entry Action Sequence by C-State Variant

| Step | C6A | C6S | C6S-P | MC6 |
|------|-----|-----|-------|-----|
| 1 | L1/L2 flush to LLC | L1/L2 + LLC flush | L1/L2 + LLC flush | All cores flush |
| 2 | PCM Cx-entry notify | PCM Cx-entry notify | PCM Cx-entry notify | PCM MC6 notify |
| 3 | Core clock gate | Core clock gate | Core power gate | Module clock gate |
| 4 | FIVR retention | FIVR retention | FIVR off | Module FIVR off |
| 5 | — | Snoop filter inval | Snoop filter inval | Module snoop inval |

### Block Decomposition

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    C6 Entry Action Sequence (NWP)                          │
└─────────────────────────────────────────────────────────────────────────────┘

  OS path (C6A)                   PCode path (C6S / C6S-P)
  ┌──────────────┐                ┌────────────────────────┐
  │ MWAIT 0x60  │                │ PCode: all-core-idle   │
  │ (C6A hint)  │                │ detected in tile       │
  └──────┬───────┘                └───────────┬────────────┘
         │                                    │
         └──────────────────┬─────────────────┘
                            │
                            ▼
               ┌────────────────────────┐
               │   Entry Guards Check   │
               │  · no pending IRQ      │
               │  · CST limit allows C6 │
               │  · not in reset seq    │
               └────────────┬───────────┘
                            │ all guards pass
                            ▼
               ┌────────────────────────┐
               │    LLC Cache Flush     │
               │  C6A:  L1/L2 → LLC   │
               │  C6S:  L1/L2+LLC→DRAM│
               │  C6S-P: same as C6S  │
               └────────────┬───────────┘
                            │
                            ▼
               ┌────────────────────────┐
               │  PCM Cx-Entry Notify   │
               │  Core ──────► PCode   │
               └────────────┬───────────┘
                            │
              ┌─────────────┴──────────────┐
              │                            │
              ▼                            ▼
     ┌─────────────────┐       ┌──────────────────────┐
     │      C6A        │       │    C6S / C6S-P       │
     │  FIVR retention │       │  FIVR off (C6S-P)    │
     │  Clock gate     │       │  Core power-gate     │
     │  SF unchanged   │       │  Snoop filter inval  │
     └────────┬────────┘       └──────────┬───────────┘
              │                            │
              └─────────────┬──────────────┘
                            │
                            ▼
               ┌────────────────────────┐
               │  C6 Active             │
               │  IA32_C6_RESIDENCY incr│
               │  PkgC6 = 0 (ZBB) ✓    │ ← NWP invariant: 0x3F9 must stay 0
               └────────────────────────┘
```

### NWP C6 Entry Action Register Checkpoints

| Checkpoint | Register | Expected Value on Entry |
|-----------|---------|------------------------|
| Core C6 residency starts | `IA32_C6_RESIDENCY` (0x3FC) | Incrementing |
| PkgC6 stays at 0 | `IA32_PKG_C6_RESIDENCY` (0x3F9) | 0 (ZBB) |
| PCM state | `pcode_pcm_status` | C6 entry state |
| Core power state | `cbb0.compute0.module0.core0.power_state` | C6 |


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

C6 entry is triggered via the **MWAIT** instruction (OS path) or **PCode autonomous policy** (Supervised path):

```
OS Path (C6A):
  CPU executes MWAIT 0x60 → HW evaluates entry conditions → LLC flush → C6A entry

PCode Path (C6S):
  PCode detects all-core-idle → issues PCM C6S command → cores flush → C6S entry

MC6 Path:
  All cores in module idle → PCode issues MC6 command → module clock gate → MC6 entry
```

**PCM (Power Control Messaging)** is the key interface between cores and PCode for C-state coordination on NWP.

## Section 3: Reset, Power, and Clocking

- C6 entry is blocked when `MSR_PKGC_IRTL` interrupt latency threshold prevents entry
- PCode abort entry if a pending interrupt arrives between flush and clock gate
- Entry latency budget includes LLC flush time (proportional to LLC occupancy)

## Section 4: Programming Model

```python
# Verify C6A entry flow — check residency counter before and after idle
import time
s = sv.socket0
tid = 22022421250

# Pre-entry: snapshot residency
pre = [s.getbypath(f"cbb{c}.compute0.module0.core{k}.msr.ia32_c6_residency").read()
       for c in range(2) for k in range(48)]

# Trigger C6A on all cores (workload idle for > threshold)
time.sleep(2)

# Post-entry: verify residency incremented
post = [s.getbypath(f"cbb{c}.compute0.module0.core{k}.msr.ia32_c6_residency").read()
        for c in range(2) for k in range(48)]

assert any(p > r for p,r in zip(post,pre)), "C6 residency not incrementing — entry failed"
assert s.uncore.msr.ia32_pkg_c6_residency.read() == 0, "PkgC6 ZBB violated on NWP"
```

## Section 5: Operational Behavior

### TC Coverage Map

| TC HSD | Title | Scope |
|--------|-------|-------|
| [22022423062](https://hsdes.intel.com/appstore/article-one/#/22022423062) | CState Entry Actions: Verify Flow C6A | — |
| [22022423064](https://hsdes.intel.com/appstore/article-one/#/22022423064) | CState Entry Actions: Verify Flow C6S | — |
| [22022423067](https://hsdes.intel.com/appstore/article-one/#/22022423067) | CState Entry Actions: Verify flow C6S-P | — |
| [16030715579](https://hsdes.intel.com/appstore/article-one/#/16030715579) | [PSS]PEGA/Solar Based C6 injection | — |
| [16030715587](https://hsdes.intel.com/appstore/article-one/#/16030715587) | [PSS]C6 Residency Counter | — |
| [16030715592](https://hsdes.intel.com/appstore/article-one/#/16030715592) | [PSS]PLR Status registers Check during Cstates | — |
| [16030768411](https://hsdes.intel.com/appstore/article-one/#/16030768411) | CState MWAIT Encodings (Place Holder) | — |


## Section 6: Corner Cases and Error Handling

- **Entry abort**: If a pending interrupt arrives between LLC flush start and clock gate, PCode must safely abort entry and restore core to C0. Verify with `CState Entry Actions: Verify flow` TCs.
- **Partial flush**: If LLC flush is incomplete (high occupancy, cache thrash), entry latency increases. Test with pre-loaded LLC workload.
- **MC6 barrier**: All cores in module must reach C6 individually before MC6 is granted. Race conditions between core C6 entry are covered by the MC6 TC.

## Section 7: Security / Safety / Policy

- LLC flush on C6 entry ensures no speculative data remains in core during power gate (Spectre/Meltdown mitigation)
- PCode must serialize C6 entry with ongoing PMI (Performance Monitoring Interrupt) delivery

## Section 8: References

- [Core C-States HAS — Entry Actions Section](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_C_States/Core_C_States_HAS.html)
- Intel SDM Vol.3, Chapter 14 — Power and Thermal Management
- [TCD HSD 22022421250](https://hsdes.intel.com/appstore/article-one/#/22022421250)
