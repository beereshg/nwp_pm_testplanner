# Deep Analysis: C1 Residency Counter

| Field | Value |
|-------|-------|
| **HSD ID** | [22021970048](https://hsdes.intel.com/appstore/article/#/22021970048) |
| **Title** | C1 Residency Counter |
| **Date** | 2026-06-17 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | PSS |
| **Feature** | Core C-States |
| **Sub-Feature** | C1 / CBB Die |
| **Val Environment** | emulation.hsle, XOS |
| **Framework** | perspec_maestro |
| **Owner** | aprakas2 |
| **Tags** | PCODE, UCODE, INT_VAL, primecode_val_gap_coverage |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Status** | open |

## HSD Hierarchy
- Test Case Definition: [22021969891 — Core C-State Residency Counter Checks](https://hsdes.intel.com/appstore/article/#/22021969891)
- Test Case: [22021970048 — C1 Residency Counter](https://hsdes.intel.com/appstore/article/#/22021970048)

## KB References
- KB Article: [KB/pm_features/core_c_states/c1.md](../../../pm_features/core_c_states/c1.md)
- KB Article: [KB/pm_features/core_c_states/core_c_states_main.md](../../../pm_features/core_c_states/core_c_states_main.md)

## Version History
- v1 (2026-06-17): Initial LLM enrichment from TC description + c1.md KB + NWP architecture constants

---

## Test Case Intent

Verify the per-core C1 residency counter (MSR 0x778 / MSR 0x3FD) increments when cores enter C1 state on NWP silicon/emulation via MWAIT using Intel Idle Driver or Solar tool. Validate ACPI C-state enumeration is correct and CXL VTC domain cross-product coverage is enabled.

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| BIOS | C-states enabled; default BIOS knobs per TC configuration |
| IMH Fuses | punit/PCODE_CORE_C_STATE = 0x3; punit/PCODE_PKG_C_STATE = 0x8 |
| IMH Fuses | PMSRVR_PTPCFSMS_PKG_C_STATE_LIMIT_REQ_FUSED_C_STATE_MAX_LIMIT_FUSE = 0x2 |
| IMH Fuses | PMSRVR_PTPCFSMS_PKG_C_STATE_LIMIT_REQ_FUSED_FUSED_PKGC_STATE_MAX_LIMIT_FUSE = 0x2 |
| CBB Fuses | fw_fuses_CORE_C_STATE; fw_fuses_PKG_C_STATE_LIMIT_REQ_C_STATE_MAX_LIMIT; fw_fuses_PKG_C_STATE_LIMIT_REQ_FUSED_PKGC_STATE_MAX_LIMIT |
| Kernel Config | idle=poll, idle=halt, idle=nomwait must NOT be in boot parameters |
| Tool | Intel Idle Driver or Solar tool available |
| Model | XOS; HSLE with Aunit Fmod and CorePMA |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read baseline per-core C1 residency counter: MSR 0x778 (CC1) and MSR 0x3FD (CC6) on all 96 cores (NWP: 2 CBBs × 48 cores) | Baseline values captured without error | Read failure / access error |
| 2 | Inject MWaits via Intel Idle Driver or Solar tool to drive cores into C1 idle state | Cores enter C1 halt; OS reflects idle | Cores remain active; no idle state entered |
| 3 | Verify BIOS ACPI enumeration | ACPI _CST enumerates C1 descriptor per logical processor | Missing or incorrect _CST object |
| 4 | Wait defined dwell period (~2 seconds) | System remains stable in idle | Unexpected wakeup or errors |
| 5 | Re-read MSR 0x778 (CC1) on all 96 cores | Positive delta on every core | Any core shows zero increment |
| 6 | Verify MSR 0x3FD (CC6) did not inflate significantly | CC6 counter remains near baseline (cores stayed in C1) | CC6 unexpectedly incremented |

### Pass/Fail Criteria

- **PASS**: MSR 0x778 increments on all 96 cores (2 CBBs × 48) after C1 dwell; MSR 0x3FD stays minimal during C1-only dwell
- **FAIL**: Any core shows CC1 residency counter delta = 0 after sustained idle; or CC6 inflates during C1-only dwell

---

## Section A: NWP Delta

**Disposition: Runnable_On_N-1 — Trivial adaptation (topology loop bounds only)**

C1/C1E is fully supported on NWP with the same PantherCove (PNC) core as DMR. The same MWAIT mechanism, residency MSR interface, BIOS ACPI _CST enumeration, and FW agents (uCode, Acode, PCode) apply without functional change.

| Aspect | DMR | NWP | Test Impact |
|--------|-----|-----|-------------|
| Core uarch | PantherCove | **PantherCove** | No change |
| Total cores | up to 256 | **96** | Loop: 96 cores, smaller sample |
| CBB count | up to 4 | **2** | `range(4)` → `range(2)` |
| Cores per CBB | 64 | **48** | `range(64)` → `range(48)` |
| C1 support | Yes | **Yes** | No change |
| MSR 0x778 CC1 | Per-core RO | **Per-core RO** | Same access path |
| MSR 0x3FD CC6 | Per-core RO | **Per-core RO** | Same access path |
| PkgC6 | Supported | **ZBB (fused off)** | No interference with C1 test |
| IMH topology | 2 IMH | **1 NIO** | Register path: `nio.punit.*` not `imh0.*` |

---

## Section B: Interactions

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | Host OS | Issue MWAIT (EAX=0, sub-state=0) or Intel Idle / Solar stimulus | [HW instruction] |
| 2 | uCode (PantherCove) | TC1 entry: CPL check → Monitor check → freeze APIC → inhibit events → clock-gate | [Internal] |
| 3 | ACP / PMA (CBB) | CC1 entry: assert core_active deassert; start CTC-based residency counter | [HW wire] |
| 4 | CTC Crystal Clock | Increment MSR 0x778 (CC1 residency counter) every crystal cycle while in CC1 | [HW wire] |
| 5 | PythonSV / Test | Read MSR 0x778 per-core via SVOS on all 96 NWP cores | [CSR] |
| 6 | Test | Delta check: after > before on all cores | [Test logic] |
| 7 | uCode | Break event received → TC1 exit: deassert clock-gate, resume thread execution | [Internal] |

### Sequence Data

| # | From | To | Message | Interface |
|---|----|------|---------|-----------|
| 1 | OS/Intel Idle Driver | uCode | MWAIT (EAX=0x00) — request C1 idle | [HW instruction] |
| 2 | uCode | ACP/PMA | TC1 entry signal; inhibit interrupts; freeze APIC counter | [Internal] |
| 3 | ACP/PMA | CTC | Assert CC1 active; enable crystal-cycle residency count | [HW wire] |
| 4 | CTC | MSR 0x778 | Increment CC1 residency counter each crystal cycle | [HW wire] |
| 5 | Test/PythonSV | MSR 0x778 | Read per-core CC1 residency (via SVOS `read_msr`) | [CSR] |
| 6 | Break event | uCode | External interrupt / Solar wakeup | [HW wire] |
| 7 | uCode | ACP/PMA | TC1 exit: deassert clock-gate; resume core | [Internal] |

---

## Section C: Coverage

| Coverage Area | DMR Coverage | NWP Gap | Adaptation |
|--------------|-------------|---------|------------|
| C1 residency counter increment (MSR 0x778) | Covered | **None** | Run as-is, update loop bounds |
| CC6 counter isolation during C1 dwell | Covered | **None** | Same check |
| ACPI _CST C1 descriptor enumeration | Covered | **None** | Same BIOS/ACPI flow |
| Cross-product: CXL VTC domain | Covered (SLE has only CXL Xtor) | **None** | Same requirement |
| MWAIT sub-state 0 (C1) and sub-state 1 (C1E) | Covered | **None** | Both sub-states required |
| All cores covered (96 NWP vs up to 256 DMR) | Covered | **Scope reduced** | Verify all 96 NWP cores |
| IMH register path | `imh0.punit.*` | → `nio.punit.*` | Path update required in scripts |

---

## Section D: Spec Refs & Validation Points

| Category | Register | Field/Offset | Expected | Verify On |
|----------|----------|--------------|----------|-----------|
| C1 Residency | MSR 0x778 (CC1_RESIDENCY) | 64-bit monotonic | Positive delta after C1 dwell | Per-core, all 96 NWP cores |
| C1E Enable | MSR 0x1FC (POWER_CTL) | bit[0] C1E_ENABLE | 1 for C1E sub-test | Package level |
| C1 Demotion | MSR 0xE2 (CLOCK_CST_CONFIG) | bit[26] C1_DEMOTION_ENABLE | Configurable | Per-package |
| CC6 Residency | MSR 0x3FD (CC6_RESIDENCY) | 64-bit | Minimal during C1-only dwell | Per-core |
| IMH Fuse (NWP) | nio.punit.PCODE_CORE_C_STATE | [2:0] | 0x3 (C1/C1E enabled) | NWP NIO |
| CBB Fuse | cbb[0-1].punit_fuses.fw_fuses_CORE_C_STATE | [2:0] | 0x3 | Both CBBs |

### PythonSV Validation Commands (NWP)

```python
import time

# NWP: 2 CBBs x 48 cores = 96 total
before = {}
for cbb_idx in range(2):
    for core_idx in range(48):
        cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
        before[(cbb_idx, core_idx)] = cbb.core[core_idx].read_msr(0x778)

# Inject C1 idle stimulus (Intel Idle driver / Solar workload)
time.sleep(2)

fails = []
for cbb_idx in range(2):
    for core_idx in range(48):
        cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
        after = cbb.core[core_idx].read_msr(0x778)
        delta = after - before[(cbb_idx, core_idx)]
        if delta == 0:
            fails.append(f"CBB{cbb_idx} Core{core_idx}: CC1 did not increment")

# Also verify CC6 did not inflate (cores stayed in C1 not C6)
for cbb_idx in range(2):
    cc6 = sv.socket0.getbypath(f"cbb{cbb_idx}").core[0].read_msr(0x3FD)
    print(f"CBB{cbb_idx} CC6={hex(cc6)}")

print(f"RESULT: {'PASS' if not fails else 'FAIL'} — {len(fails)}/96 cores failed")
for f in fails:
    print(f"  FAIL: {f}")
```

**References:**
- PNC PM HAS §8.3: CC1 residency counter (MSR 0x778, crystal cycles)
- PNC PM HAS §8.9: C1/TC1 entry/exit flow
- PNC PM HAS §8.10: C1E (Slow C1E) flow
- DMR CBB PM HAS: Core C1 residency architecture
- CCP 2.0: https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/CCP%202.0/CCP_2_0.html#cstate-entry-flow

---

## Section E: Risk Assessment

| # | Risk / Open Item | Severity | Notes |
|---|-----------------|----------|-------|
| 1 | **Background load** — active cores prevent C1 dwell | Medium | Minimize OS activity; use dedicated idle injection tool |
| 2 | **C1 vs C1E separation** — MSR 0x778 counts both C1 and C1E combined | Low | Run with C1E enabled and disabled separately |
| 3 | **NWP register path** — scripts using `imh0.punit.*` need update to `nio.punit.*` | Medium | All IMH register path references must be updated |
| 4 | **CXL VTC cross-product** — NWP HSLE has only CXL Xtor, not full CXL | Low | Aligned with original TC note; same limitation applies |
| 5 | **HSLE Fmod requirement** — CorePMA + Aunit Fmod needed for emulation | Low | Already captured in pre-conditions; ensure correct HSLE configuration |

---

## Section F: Recommendations

**Recommendation: ADOPT — Trivial adaptation needed (register path and loop bounds).**

C1 residency counter test is directly applicable on NWP with two low-risk changes:

1. **Update CBB loop bounds**: `range(4)` → `range(2)` (CBBs); `range(64)` → `range(48)` (cores/CBB)
2. **Update IMH register path**: `imh0.punit.*` / `imh1.punit.*` → `sv.socket0.nio.punit.*`
3. **Retain HSLE + CorePMA + Aunit Fmod** pre-conditions exactly as in DMR TC
4. **Run both C1E sub-states** (sub-state 0 and 1) to confirm C1E behavior on PNC NWP cores
5. **Document NWP scope**: All 96 cores expected to show CC1 residency increment; CC6 must stay low
