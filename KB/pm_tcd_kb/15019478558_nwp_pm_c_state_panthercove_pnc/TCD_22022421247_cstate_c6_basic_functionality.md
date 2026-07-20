## Section 1: Architecture / Micro-architecture and Functionality

**C6A (Autonomous C6)** is the OS-requested deep core sleep state on NWP (PantherCove PNC), entered via `MWAIT 0x60`. C6A flushes L1/L2 to LLC (but not to DRAM), drops FIVR to retention voltage, and gates the core clock. C6A does not power-gate the core and does not flush MLC. The core exits autonomously on any wake event (interrupt/IPI/timer).

### T2 Boundary Notes (2026-07-19)

- This TCD owns **C6A behavior and C6A residency observability only**.
- C6S + MC6 qualification: [16031170164](https://hsdes.intel.com/appstore/article-one/#/16031170164).
- C6S-P / PKGC: [16031170168](https://hsdes.intel.com/appstore/article-one/#/16031170168) (parked).
- Entry sequencing (all variants): [22022421250](https://hsdes.intel.com/appstore/article-one/#/22022421250).
- Exit sequencing: [22022421253](https://hsdes.intel.com/appstore/article-one/#/22022421253).
- Exit latency KPI: [16031170166](https://hsdes.intel.com/appstore/article-one/#/16031170166).
- MC6 residency: [22022421260](https://hsdes.intel.com/appstore/article-one/#/22022421260).
- MC6 wake target: [16031170167](https://hsdes.intel.com/appstore/article-one/#/16031170167).
- C1 residency: [22022421257](https://hsdes.intel.com/appstore/article-one/#/22022421257).
- Demotion/undemotion policy: [22022421266](https://hsdes.intel.com/appstore/article-one/#/22022421266).

### C6A Characteristics

| Property | C6A Value |
|----------|-----------|
| Trigger | `MWAIT 0x60` (OS-driven) |
| LLC flush | L1/L2 → LLC only (MLC not flushed to DRAM) |
| Power gate | No |
| FIVR | Retention voltage |
| Exit | Autonomous on wake event |
| Residency MSR | `IA32_C6_RESIDENCY` (MSR 0x3FC) |

### BIOS Knob to C6A Register Propagation

| BIOS Knob | Register | MSR / Path | NWP Default |
|-----------|----------|------------|-------------|
| `C6Enable` | CST_CONFIG_CONTROL | MSR 0xE2, bits[25:24] = 01 | Enabled |
| `PEGA C-State` | PMG_CST_CONFIG_CONTROL | MSR 0xE2 | Enabled |

### NWP-Specific Deltas (C6A scope)

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | Up to 4 | **2** | Loop: `range(4)` → `range(2)` |
| Cores per CBB | 64 | **48** | Loop: `range(64)` → `range(48)` |
| Total cores | 256 | **96** | Scale verification |
| PkgC6 | Supported | **ZBB** | `MSR 0x3F9` must stay 0 |
| Register prefix | `cbb{0..3}` | **`cbb{0,1}`** | 2-CBB namespace |


## Section 2: Interfaces and Protocols

**C6A Request Flow (OS path only — this TCD's scope):**

```
MWAIT hint 0x60 → Core evaluates entry conditions → L1/L2 flush to LLC → C6A entry
```

| Interface | Direction | Description |
|-----------|-----------|-------------|
| ACPI MWAIT 0x60 | OS → Core | C6A state request |
| PCM Cx message | Core → PCode | C6A entry/exit notification |
| PythonSV `cbb{0,1}` | Debug | Register inspection |

> C6S/C6S-P request paths are owned by [16031170164](https://hsdes.intel.com/appstore/article-one/#/16031170164) and [16031170168](https://hsdes.intel.com/appstore/article-one/#/16031170168).

## Section 3: Reset, Power, and Clocking

- C6A entry is blocked during reset sequences (PCode exclusion window).
- Core clock is gated during C6A; uncore (UPI, LLC tags) remains active.
- FIVR transitions to retention voltage during C6A (not power-gated — that is C6S-P scope).
- On C6A exit, PLR must be satisfied before OS resumes.

## Section 4: Programming Model

### Key MSR Configuration (C6A-relevant bits only)

| Bit(s) | Field | Description |
|--------|-------|-------------|
| [25:24] | `c6_enable` | 01 = C6A enabled |

> Full MSR 0xE2 bit map including demotion/undemotion bits is owned by [22022421266](https://hsdes.intel.com/appstore/article-one/#/22022421266).

### PythonSV C6A Validation

```python
# Read C6A residency counter for all cores
for c in range(2):   # CBB 0,1
    for core in range(48):
        r = sv.socket0.getbypath(f"cbb{c}.compute0.module0.core{core}.msr.ia32_c6_residency").read()
        print(f"CBB{c} core{core} C6 residency: {r:#x}")

# Verify PkgC6 stays 0 (ZBB invariant)
pkgc6 = sv.socket0.uncore.msr.ia32_pkg_c6_residency.read()
assert pkgc6 == 0, f"PkgC6 must be ZBB but got {pkgc6:#x}"
```

## Section 5: Operational Behavior

### Pass/Fail Bar (C6A only)

- `IA32_C6_RESIDENCY` (MSR 0x3FC) increments when C6A stimulus is applied via MWAIT 0x60.
- `IA32_PKG_C6_RESIDENCY` (MSR 0x3F9) remains 0 (NWP ZBB invariant).
- BIOS knobs propagate correctly to MSR 0xE2 bits[25:24] = 01 for C6A.
- No hang/MCA across C6A entry-exit cycles.

FAIL if: C6A residency does not increment under valid stimulus; PkgC6 residency > 0; BIOS knob mismatch; hang or MCA.

### TC Coverage Map (C6A-owned TCs only)

| TC HSD | Title | C6A Scope |
|--------|-------|-----------|
| [22022423030](https://hsdes.intel.com/appstore/article-one/#/22022423030) | CState Bios_knobs checkout | BIOS → MSR 0xE2 propagation |
| [22022423031](https://hsdes.intel.com/appstore/article-one/#/22022423031) | CState Bios_knobs checkout PIV | PIV variant |
| [22022423032](https://hsdes.intel.com/appstore/article-one/#/22022423032) | CState C6 residency check | C6A residency increment |
| [22022423036](https://hsdes.intel.com/appstore/article-one/#/22022423036) | CState C6 residency counters and KPI | C6A dwell time KPI |

### TCs needing reparent review

The following TCs were listed here but belong to other split TCDs:

| TC HSD | Title | Recommended owner |
|--------|-------|--------------------|
| [22022423038](https://hsdes.intel.com/appstore/article-one/#/22022423038) | CState MSR Control | [22022421266](https://hsdes.intel.com/appstore/article-one/#/22022421266) (demotion/undemotion) — full MSR 0xE2 ownership |
| [22022423039](https://hsdes.intel.com/appstore/article-one/#/22022423039) | CState dfx_ctrl_unprotected | Shared DFX checkout — keep here or move to a DFX TCD |
| [22022423042](https://hsdes.intel.com/appstore/article-one/#/22022423042) | Enable PEGA C-States | Cross-cutting PEGA enable — keep here (C6A is primary PEGA target) |
| [22022423044](https://hsdes.intel.com/appstore/article-one/#/22022423044) | Multiple B2B cstates on same core | Stress/stability — consider [22022421307](https://hsdes.intel.com/appstore/article-one/#/22022421307) (Solar) |
| [22022423047](https://hsdes.intel.com/appstore/article-one/#/22022423047) | [Solar] CStates_unsupported Exercise | [22022421307](https://hsdes.intel.com/appstore/article-one/#/22022421307) (Solar framework) |
| [22022423050](https://hsdes.intel.com/appstore/article-one/#/22022423050) | [Solar] CStates_unsupported_Random Exercise | [22022421307](https://hsdes.intel.com/appstore/article-one/#/22022421307) (Solar framework) |
| [22022423053](https://hsdes.intel.com/appstore/article-one/#/22022423053) | [Solar] CStates_unsupported_Random Verify | [22022421307](https://hsdes.intel.com/appstore/article-one/#/22022421307) (Solar framework) |
| [22022423057](https://hsdes.intel.com/appstore/article-one/#/22022423057) | [Solar] CStates_unsupported Verify | [22022421307](https://hsdes.intel.com/appstore/article-one/#/22022421307) (Solar framework) |
| [16030768408](https://hsdes.intel.com/appstore/article-one/#/16030768408) | CState C6 residency counters | Duplicate of 22022423032 — verify and deduplicate |
| [16030768409](https://hsdes.intel.com/appstore/article-one/#/16030768409) | CState Fuse dfx_ctrl_unprotected | Same as 22022423039 — verify and deduplicate |

## Section 6: Corner Cases and Error Handling

- **PkgC6 ZBB invariant**: If `MSR 0x3F9` > 0, raise a pre-sighting. (ZBB scope details owned by [16031170168](https://hsdes.intel.com/appstore/article-one/#/16031170168).)
- **C6A residency not incrementing**: Verify `C6Enable` knob and MSR 0xE2 bits[25:24] = 01; check no demotion active (demotion scope: [22022421266](https://hsdes.intel.com/appstore/article-one/#/22022421266)).
- **Fuse dfx_ctrl override**: `dfx_ctrl_unprotected.core_cstate_limit` can lock core to C1 — verify fuse state before C6A tests.

## Section 7: Security / Safety / Policy

- Core L1/L2 caches are flushed to LLC on C6A entry.
- FIVR retention during C6A preserves micro-architectural state securely.
- `dfx_ctrl_unprotected` registers require DFX unlock (pre-production only).

## Section 8: References

- [Core C-States HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_C_States/Core_C_States_HAS.html)
- [ACP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html)
- Intel SDM — MSR 0xE2 (IA32_CST_CONFIG_CONTROL), MSR 0x3F9 (PKG_C6_RESIDENCY), MSR 0x3FC (C6_RESIDENCY)
- [TCD HSD 22022421247](https://hsdes.intel.com/appstore/article-one/#/22022421247)
- Split siblings: [16031170164](https://hsdes.intel.com/appstore/article-one/#/16031170164) (C6S), [16031170168](https://hsdes.intel.com/appstore/article-one/#/16031170168) (C6S-P parked)
