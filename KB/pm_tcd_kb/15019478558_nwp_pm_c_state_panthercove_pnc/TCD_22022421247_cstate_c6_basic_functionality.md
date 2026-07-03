## Section 1: Architecture / Micro-architecture and Functionality

**C6** is a deep core sleep state on NWP (PantherCove PNC) that minimizes power by flushing core caches, draining internal buffers, and gating power to the core logic. NWP supports three C6 variants: **C6A** (Autonomous — OS-requested via MWAIT), **C6S** (Supervised — PCode-managed), and **C6S-P** (Supervised with Power-Gate). PkgC6 is **Zero Bit Budget (ZBB)** on NWP and must not be entered; `IA32_PKG_C6_RESIDENCY` (MSR 0x3F9) must remain 0 throughout testing.

### C6 Variant Summary

| Variant | Trigger | LLC Flush | Power Gate | NWP Notes |
|---------|---------|-----------|------------|-----------|
| C6A | MWAIT 0x60 | Yes | No | Autonomous, OS-driven |
| C6S | PCode policy | Yes | No | Supervised low-power |
| C6S-P | PCode policy | Yes | Yes | Maximum save state |
| PkgC6 | — | — | — | **ZBB on NWP — must not enter** |

### BIOS Knob to Register Propagation

Key BIOS knobs controlling C6 behavior:

| BIOS Knob | Register | MSR / Path | NWP Default |
|-----------|----------|------------|-------------|
| `C6Enable` | CST_CONFIG_CONTROL | MSR 0xE2, bits[25:24] | Enabled |
| `PackageCStateLimit` | PKG_CST_CONFIG_CTL | MSR 0xE2, bits[2:0] | C6 allowed |
| `PEGA C-State` | PMG_CST_CONFIG_CONTROL | MSR 0xE2 | Enabled |
| `dfx_ctrl_unprotected.core_cstate_limit` | DFX register | PythonSV path | Per test |

### Residency Counter MSRs

| Counter | MSR Address | Notes |
|---------|-------------|-------|
| Core C6 residency | 0x3FC (IA32_C6_RESIDENCY) | Per-core, resets on RESET |
| Core C3 residency | 0x3FD | Maps to C6S on NWP |
| Package C6 residency | 0x3F9 | Must stay **0** (ZBB) |
| Core C1 residency | 0x660–0x669 | Per-core C1 dwell time |


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

**OS → PCode C-State Request Flow:**

The ACPI Cx state is requested by OS via the `MWAIT` instruction with a sub-state hint:

```
MWAIT hint 0x60 → C6A request → Core autonomously flushes LLC → C6A entry
MWAIT hint 0x20 → C1E request → C1E autopromotion path
```

The OS reads ACPI `_CST` objects to discover supported C-states. On NWP, the BIOS exposes C1, C6A/C6S/C6SP based on `C6Enable` knob state. PCode intercepts the C6 grant through the **PCM (Power Control Messaging)** interface.

| Interface | Direction | Description |
|-----------|-----------|-------------|
| ACPI MWAIT | OS → Core | Cx state request |
| PCM Cx message | Core → PCode | C6 entry/exit notification |
| PECI/TPMI | BMC → PCode | Power limit override |
| PythonSV `cbb0/cbb1` | Debug | Register inspection |

## Section 3: Reset, Power, and Clocking

- C6 entry is **blocked during reset sequences** — PCode guards the reset exclusion window
- Core clock is gated during C6; uncore (UPI, LLC tags) remains active
- FIVR (Fully Integrated Voltage Regulator) transitions to retention voltage during C6A; power-gated during C6S-P
- On C6 exit, PLR (Platform Latency Requirement) must be satisfied before OS resumes

**C6 Entry Power Sequence:**
1. Core flushes L1/L2 to LLC (for C6A) or all to DRAM (for C6S)
2. Core signals PCode via PCM with Cx entry notification
3. PCode adjusts FIVR to retention/off voltage
4. Core clock is gated
5. Snoop filter entry invalidated (C6S only)

## Section 4: Programming Model

### Key MSR Configuration (IA32_CST_CONFIG_CONTROL, MSR 0xE2)

| Bit(s) | Field | Description |
|--------|-------|-------------|
| [2:0] | `pkg_c_state_limit` | Max allowed package C-state (6=C6, 7=C7) |
| [6] | `io_mwait_redirect` | Enable/disable IO-based Cx entry |
| [10] | `unlock` | Allow OS to change CST limit |
| [25:24] | `c6_enable` | Core C6 enable (01=C6, 10=C6S, 11=C6S-P) |

### PythonSV Validation Paths

```python
# Read C6 residency counter for all cores
for c in range(2):   # CBB 0,1
    for core in range(48):
        r = sv.socket0.getbypath(f"cbb{c}.compute0.module0.core{core}.msr.ia32_c6_residency").read()
        print(f"CBB{c} core{core} C6 residency: {r:#x}")

# Verify PkgC6 stays 0 (ZBB)
pkgc6 = sv.socket0.uncore.msr.ia32_pkg_c6_residency.read()
assert pkgc6 == 0, f"PkgC6 must be ZBB but got {pkgc6:#x}"

# Check MSR 0xE2 C6 enable bits
cst_cfg = sv.socket0.cbb0.compute0.module0.core0.msr.ia32_cst_config_ctrl.read()
print(f"C6 enable bits[25:24]: {(cst_cfg >> 24) & 0x3:#x}")
```

## Section 5: Operational Behavior

### TC Coverage Map

| TC HSD | Title | Scope |
|--------|-------|-------|
| [22022423030](https://hsdes.intel.com/appstore/article-one/#/22022423030) | CState Bios_knobs checkout | — |
| [22022423031](https://hsdes.intel.com/appstore/article-one/#/22022423031) | CState Bios_knobs checkout PIV | — |
| [22022423032](https://hsdes.intel.com/appstore/article-one/#/22022423032) | CState C6 residency check | — |
| [22022423036](https://hsdes.intel.com/appstore/article-one/#/22022423036) | CState C6 residency counters and CStates residency KPI | — |
| [22022423038](https://hsdes.intel.com/appstore/article-one/#/22022423038) | CState MSR Control | — |
| [22022423039](https://hsdes.intel.com/appstore/article-one/#/22022423039) | CState dfx_ctrl_unprotected.core_cstate_limit checkout_silicon | — |
| [22022423042](https://hsdes.intel.com/appstore/article-one/#/22022423042) | Enable PEGA C-States | — |
| [22022423044](https://hsdes.intel.com/appstore/article-one/#/22022423044) | Multiple B2B cstates on same core | — |
| [22022423047](https://hsdes.intel.com/appstore/article-one/#/22022423047) | [Solar] CStates - CStates_unsupported -- Exercise | — |
| [22022423050](https://hsdes.intel.com/appstore/article-one/#/22022423050) | [Solar] CStates - CStates_unsupported_Random -- Exercise | — |
| [22022423053](https://hsdes.intel.com/appstore/article-one/#/22022423053) | [Solar] CStates - CStates_unsupported_Random -- Verify | — |
| [22022423057](https://hsdes.intel.com/appstore/article-one/#/22022423057) | [Solar]_CStates-CStates_unsupported--Verify | — |
| [16030768408](https://hsdes.intel.com/appstore/article-one/#/16030768408) | CState C6 residency counters | — |
| [16030768409](https://hsdes.intel.com/appstore/article-one/#/16030768409) | CState Fuse dfx_ctrl_unprotected.core_cstate_limit checkout_silicon | — |


| Scenario | Covered By |
|----------|-----------|
| BIOS knobs propagate to MSR 0xE2 | CState Bios_knobs checkout TCs |
| C6 residency counters increment | CState C6 residency check TCs |
| KPI — C6 dwell time meets spec | CState C6 residency counters and KPI |
| MSR 0xE2 control field checkout | CState MSR Control TC |
| dfx_ctrl cstate_limit | CState dfx_ctrl_unprotected TC |
| PEGA C-state enable | Enable PEGA C-States TC |
| B2B C-state on same core | Multiple B2B cstates TC |
| MWAIT encodings | CState MWAIT Encodings TC |

## Section 6: Corner Cases and Error Handling

- **PkgC6 ZBB violation**: If `IA32_PKG_C6_RESIDENCY` (0x3F9) > 0, it indicates an architectural deviation — raise a pre-sighting
- **C6 residency not incrementing**: Check `C6Enable` knob, verify no SW/HW demotion to C1 is active, verify OS is not using `HALT` (C1) instead of MWAIT
- **Fuse dfx_ctrl override**: `dfx_ctrl_unprotected.core_cstate_limit` fuse can lock the core to C1 regardless of BIOS — must verify fuse state before C6 tests
- **B2B stress**: Multiple back-to-back C6 entries on the same core should not cause hang or MCA

## Section 7: Security / Safety / Policy

- Core caches are flushed on C6 entry — no security-sensitive data retained in core during C6
- FIVR voltage retention state during C6A ensures secure micro-architecture state
- `dfx_ctrl_unprotected` registers require DFX unlocking (pre-production only)

## Section 8: References

- [Core C-States HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_C_States/Core_C_States_HAS.html)
- [ACP PM HAS — Autonomous Core Perimeter](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html)
- Intel SDM — MSR 0xE2 (IA32_CST_CONFIG_CONTROL), MSR 0x3F9 (PKG_C6_RESIDENCY), MSR 0x3FC (C6_RESIDENCY)
- [NWP PM TP: C-State (PantherCove PNC)](https://hsdes.intel.com/appstore/article-one/#/15019478558)
- [TCD HSD 22022421247](https://hsdes.intel.com/appstore/article-one/#/22022421247)
