# Deep Analysis: CState C6 residency counters and CStates residency KPI

| Field | Value |
|-------|-------|
| **HSD ID** | 14020416752 |
| **Title** | CState C6 residency counters and CStates residency KPI |
| **Date** | 2026-05-29 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Core C-States |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Test Case

### Test Intent

Verify that per-core and package C-state residency counters increment correctly when the system dwells in each C-state. The test imports `pm.focused.cstate_focus` and calls `cst_residency_focus()` to exercise C0/C1/C3/C6 dwell sequences, then reads back the residency counters to confirm monotonic increase: CC6 per-core (MSR 0x3FD), MC6 per-module (MSR 0x664), CC1 per-core (MSR 0x778), PC2 package (MSR 0x60D), PC3 package (MSR 0x3F8). On NWP, PC6 (MSR 0x3F9) must remain 0 — PkgC6 is ZBB and the package may not enter PC6. The test also validates KPI thresholds (minimum expected residency percentages) per the feature validation plan.

### Pre-Conditions

- NWP silicon or VP at boot-complete; OS idle (minimal background load)
- PythonSv + namednodes loaded
- `pm.focused.cstate_focus` module available in pythonsv environment
- BIOS knob `C6Enable = Enabled`, `MonitorMWait = Enabled`

### Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Import and invoke `cst_residency_focus()` | Use `nwp.xml` instead of `dmr.xml` for platform configuration |
| 2 | Record baseline residency counters for all cores | 2 CBBs x 48 cores = 96 cores; MSR 0x3FD, 0x778, 0x664 per-core |
| 3 | Force system to idle (C6 dwell) for defined period | Same stimulus; NWP enters C6A/C6S; PC6 must NOT be entered |
| 4 | Read residency counters again; verify monotonic increase | CC6 (0x3FD) and MC6 (0x664) must increase; PC6 (0x3F9) must stay 0 |
| 5 | Force C1 dwell; verify CC1 counter (0x778) increases | Same; per all 96 cores |
| 6 | Force PC2/PC3 package idle; verify PC2 (0x60D) and PC3 (0x3F8) increase | Same; package-level counters via `nio.punit.*` |
| 7 | Assert PC6 counter (0x3F9) = 0 throughout | **NWP-specific assertion**: PC6 ZBB — this is a NEGATIVE check |

### Pass/Fail Criteria

**PASS:**
- CC6 residency counter (MSR 0x3FD) increases on all 96 cores after C6 dwell
- MC6 residency counter (MSR 0x664) increases after module-level C6
- CC1 residency counter (MSR 0x778) increases after C1 dwell
- PC2 (0x60D) and PC3 (0x3F8) package counters increase
- **PC6 counter (0x3F9) = 0 at all times** (ZBB negative check)
- Residency percentages meet KPI thresholds from FV plan

**FAIL:**
- Any residency counter (except PC6) does not increase after dwell period
- PC6 counter > 0 (indicates PkgC6 entry, which is ZBB violation)
- Residency percentages below minimum KPI thresholds

---

## Section A: NWP Architecture Delta

**Disposition: Runnable_On_N-1**

Core C-state residency counters (C1, C3, C6 per-core; MC6 per-module; PC2/PC3 package) are supported on NWP. The key adaptation is that the package C6 counter (PC6, MSR 0x3F9) must be verified as ZERO throughout — PkgC6 is ZBB on NWP and must never be entered.

### DMR to NWP Delta Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| PC6 support | Supported | **ZBB** | PC6 counter must be a negative assertion (always 0) |
| Ring C6 | Supported | **ZBB (Ring C3 only)** | MC6 residency accumulates; no deeper Ring C6 |
| CBBs | Up to 4 | **2** | 96 total cores instead of 256 |
| Modules | 8 per CBB (32 total) | **8 per CBB (16 total)** | 16 modules x 6 cores = 96 cores |
| Package residency access | `sv.socket0.imh0/imh1...` | **Single NIO** | Use `sv.socket0.nio.punit.*` for package counters |
| Test command | `runPmx.py -x dmr.xml` | `runPmx.py -x nwp.xml` | Platform config file change |

### NWP Residency Counter Architecture

| Counter | MSR | Scope | NWP Expected |
|---------|-----|-------|--------------|
| CC6 (Core C6) | 0x3FD | Per-core | Increments during C6A/C6S dwell |
| MC6 (Module C6) | 0x664 | Per-module (6 cores) | Increments during C6S |
| CC1 (Core C1) | 0x778 | Per-core | Increments during C1/C1E dwell |
| PC2 | 0x60D | Package | Increments during package idle |
| PC3 | 0x3F8 | Package | Increments during ring C3 |
| **PC6** | **0x3F9** | **Package** | **MUST BE 0 (ZBB)** |

### NWP C-State Hierarchy (Architecture Reference)

```
Thread C-states:    TC0 -> TC1 -> TC6
Core C-states:      CC0 -> CC1 -> CC6 (same PantherCove core as DMR)
Module C-states:    MC0 -> MC3 -> MC6 (deepest on NWP; 6 cores per module)
Package C-states:   PC0 -> PC2 -> PC3 (PC6 is ZBB — fused off)
```

### Key ZBB Features Affecting This Test

- **PkgC6**: Fused off (`FUSE_PKG_C_STATE=0`) — test must assert PC6 counter = 0
- **Ring C6**: ZBB (Ring C3 only) — no additional Ring C6 residency expected

---

## Section B: Interactions

> This section shows firmware/hardware execution flow as swimlane + sequence diagram.

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | Test | Import `cstate_focus` and invoke `cst_residency_focus()` | Test logic |
| 2 | Test | Read baseline CC6 counters (MSR 0x3FD) for 96 cores (2 CBB x 48) | MSR |
| 3 | Test | Read baseline MC6 counters (MSR 0x664) for 16 modules | MSR |
| 4 | Test | Read baseline CC1 counters (MSR 0x778) for 96 cores | MSR |
| 5 | Test | Read baseline PC2/PC3/PC6 counters (MSR 0x60D/0x3F8/0x3F9) | MSR |
| 6 | OS/Test | Force system idle via MWAIT (C6 dwell stimulus) | CPU instruction |
| 7 | uCode | Thread C6 entry: MWAIT dispatch, C6SRAM save, PICLET setup | Internal |
| 8 | Acode | `core_c6_enter()`: budget negotiation, Q-channel deassert | HPM |
| 9 | PCode | Budget grant (INC_GB/DEC_GB); WP update for C6 | HPM |
| 10 | HW | Core PowerGood deasserts; FIVR powers down VCCcore | HW wire |
| 11 | HW | C6 dwell period (5 seconds) | HW wire |
| 12 | Acode | Break event -> `core_c6_exit()`: budget request | HPM |
| 13 | uCode | CC6 exit reset handler: C6SRAM restore, PICLET replay | Internal |
| 14 | Test | Read final CC6 counters; verify monotonic increase | MSR |
| 15 | Test | Read final MC6 counters; verify monotonic increase | MSR |
| 16 | Test | **Assert PC6 counter = 0** (ZBB negative check) | MSR |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|-----|---------|-----------|
| 1 | Test | Core (all 96) | Read MSR 0x3FD (CC6 baseline) | MSR |
| 2 | Test | Core (all 96) | Read MSR 0x778 (CC1 baseline) | MSR |
| 3 | Test | Core (module) | Read MSR 0x664 (MC6 baseline) | MSR |
| 4 | Test | NIO | Read MSR 0x60D/0x3F8/0x3F9 (package counters) | MSR |
| 5 | Test | uCode | MWAIT instruction (EAX=0x20, C6 dwell) | CPU instruction |
| 6 | uCode | Acode | C6 entry request (TC6 coordinator) | Internal |
| 7 | Acode | PCode | INC_GB budget request | HPM |
| 8 | PCode | Acode | Budget grant (WP1/WP3/WP4 update) | HPM |
| 9 | Acode | HW | Q-channel deassert (CFC_CLK -> CFC_PWR) | Q-channel |
| 10 | HW | Core | PowerGood deassert; VCCcore off | HW wire |
| 11 | Break event | Acode | Wake request | HW wire |
| 12 | Acode | PCode | DEC_GB budget release | HPM |
| 13 | uCode | Core | C6SRAM restore -> CC0 | Internal |
| 14 | Test | Core (all 96) | Read MSR 0x3FD (CC6 final, must increase) | MSR |
| 15 | Test | Core (all 96) | Read MSR 0x664 (MC6 final, must increase) | MSR |
| 16 | Test | NIO | Read MSR 0x3F9 (PC6, **must be 0**) | MSR |

---

## Section C: Interface Coverage Assessment

| Interface | Register/Address | Covered | Notes |
|-----------|------------------|---------|-------|
| MSR | 0x3FD (CC6 Residency) | Yes | Per-core, 96 cores |
| MSR | 0x664 (MC6 Residency) | Yes | Per-module, 16 modules |
| MSR | 0x778 (CC1 Residency) | Yes | Per-core, 96 cores |
| MSR | 0x60D (PC2 Residency) | Yes | Package-level |
| MSR | 0x3F8 (PC3 Residency) | Yes | Package-level |
| MSR | 0x3F9 (PC6 Residency) | Yes | **Negative assertion (must be 0)** |
| MSR | 0xE2 (CST_CONFIG_CONTROL) | Partial | C6Enable config — not explicitly read in test |
| MWAIT | C6 dwell instruction | Yes | EAX[7:4]=0x2, sub-states tested |
| CPUID | 0x05 (C-state enumeration) | Partial | Not explicitly validated in test |
| TPMI | — | No | Core C-states use MSR, not TPMI |
| HPM | Budget negotiation | No | Firmware-internal; not directly observable |
| namednodes | `sv.socket0.nio.punit.*` | Yes | Package counter access for NWP |

### Coverage Gaps

1. **CST_CONFIG_CONTROL (0xE2)**: Test assumes BIOS knobs pre-configured; should add explicit read/verify of C6Enable
2. **CPUID.05H**: Should enumerate and verify C6 sub-state availability matches test targets
3. **Residency KPI thresholds**: Pass criteria mention "KPI thresholds from FV plan" but values not specified

---

## Section D: NWP Specification References

- **NWP PM HAS**: [NWP HAS - PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features)
- **NWP PM MAS**: [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- **DMR PM HAS**: [DMR CBB PM HAS](https://docs.intel.com/documents/custom-xeon/dmr-docs/has/PM/DMR_CBB_PM_HAS.html)
- **PNC PM HAS Section 8 (Core C-States)**: PantherCove Core C-State architecture, residency counters (Section 8.3), C6 entry/exit (Section 8.12)
- **PNC PM HAS Section 8.3**: CC6/MC6/CC1 residency counter definitions
- **PNC PM HAS Section 8.12**: C6 power-gate sequence, C6SRAM, PICLET
- **KB Reference**: [Core C-States > c6](../../../KB/pm_features/core_c_states/c6.md) — HW/FW touchpoints, KPI and Timing

---

## Section E: NWP Risk Assessment

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| 1 | Topology mismatch (96 vs 256 cores) | Low | Medium | Update loop bounds to 96 cores; verify per-CBB indexing |
| 2 | PC6 ZBB not enforced | Low | High | Add explicit PC6=0 assertion at every checkpoint |
| 3 | Module count mismatch | Low | Low | 16 modules on NWP vs 32 on DMR; verify MC6 counter scope |
| 4 | NIO vs dual-IMH path for package counters | Medium | Medium | Use `sv.socket0.nio.punit.*` instead of imh0/imh1 |
| 5 | C6 dwell time insufficient for KPI | Medium | Low | Increase dwell period if needed; verify residency meets threshold |

---

## Section F: Recommendations

1. **Add PC6=0 assertion at every checkpoint** — not just at end; catch any unexpected entry immediately
2. **Update topology constants** — hard-code or detect 96-core / 2-CBB / 16-module NWP topology
3. **Use NIO namespace** — replace `sv.socket0.imh0/imh1...` with `sv.socket0.nio.punit.*` for package counters
4. **Document KPI thresholds** — specify minimum residency percentages in pass criteria
5. **Add CPUID.05H validation** — enumerate C6 sub-states and confirm support before test
6. **Add CST_CONFIG_CONTROL read** — verify C6Enable=1 before testing C6 entry
