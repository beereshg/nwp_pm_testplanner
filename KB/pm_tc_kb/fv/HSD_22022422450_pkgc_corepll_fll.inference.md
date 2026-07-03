# HSD 22022422450: COREPLL (FLL)

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422450](https://hsdes.intel.com/appstore/article/#/22022422450) |
| **Segment** | FV |
| **Feature** | Package C-States |
| **Sub-Feature** | Clock Actions |
| **Environment** | virtual_platform |
| **Status** | open |
| **Owner** | bg3 |
| **TPF Parent** | [2202242049](https://hsdes.intel.com/appstore/article/#/2202242049) |
| **KB Article** | [KB/pm_features/core_c_states/pkgc.md](KB/pm_features/core_c_states/pkgc.md) |
| **Script** | pkgc.py |

### Version History

| Version | Date | Changes | Trigger |
|---------|------|---------|---------|
| v1 | 2026-05-29 | Initial LLM-driven enrichment with negative test derivation | `enrich batch TPF 2202242049` |

---

## Test Case

### Intent

Verify Core PLL (FLL - Frequency Locked Loop) is properly disabled during Package C6 entry.
When system enters PC6, the COREPLL should be gated (disabled) to save power.
The PLL lock status can be checked via `sv.sockets.cbbs.computes.core_pmas.core_pmsb_top.core_pma_pmsb.pma_debug.pll_lock`.

**DMR Behavior**: During PC6 entry, PUnit coordinates module idle → all cores C6 → fabric idle → PLL gating.
PLL re-locks on PC6 exit before cores can resume.

### Pre-Conditions

1. Boot SVOS with PkgC enabled via BIOS (DMR configuration)
2. System/model booted to OS
3. PkgC entry possible (all break events disabled)
4. PythonSV environment available
5. Only check enabled cores

### Test Steps

| Step | Action | Interface | Expected |
|------|--------|-----------|----------|
| 1 | Boot system with PkgC enabled | BIOS | System boots |
| 2 | Disable all break events to force PC6 | PythonSV | Break events disabled |
| 3 | Wait for system to enter PC6 | Idle | PC6 entry |
| 4 | Read `core_pma_pmsb.pma_debug.pll_lock` | CSR | PLL unlocked (gated) |
| 5 | Generate wake event | Traffic | PC6 exit |
| 6 | Re-read `pll_lock` | CSR | PLL locked (active) |

### Pass/Fail Criteria

**PASS (DMR):**
- During PC6: `pll_lock = 0` for all enabled cores (PLL gated)
- After PC6 exit: `pll_lock = 1` (PLL re-locked)

**FAIL:**
- PLL remains locked during PC6 (power waste)
- PLL fails to re-lock on exit (hang)

---

## Section A: NWP Architecture Delta

**Disposition: Skip (derive negative test)**

PkgC6 is **fused off** on NWP (FUSE_PKG_C_STATE=0). The system will never enter PC6,
so Core PLL will never be gated at package level. This test cannot execute as designed.

**However**, this test is valuable for deriving **negative test content**:
- Verify COREPLL remains LOCKED even when OS requests deepest idle (MC6)
- Verify no unexpected PLL gating occurs during Module C6

### DMR to NWP Delta Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| PkgC6 entry | Supported | **Blocked** (fuse=0) | Test N/A |
| COREPLL gating trigger | PC6 entry | **Never** (no PC6) | PLL stays locked |
| Module C6 PLL behavior | Gated per-module | Same (per-module) | Module-level gating still works |
| Deepest idle state | PC6 | MC6 | Test scope changes |
| pll_lock during idle | 0 (gated) | **1 (locked)** | Negative assertion |

### Negative Test Derivation

**NWP Negative Test: COREPLL_remains_locked_during_MC6**

| Step | Action | Expected (NWP) |
|------|--------|----------------|
| 1 | Boot with PkgC disabled (fuse) | System boots |
| 2 | Force all cores to MC6 | All cores in Module C6 |
| 3 | Read `pll_lock` | **pll_lock = 1** (locked, not gated) |
| 4 | Verify no package-level gating | PKGC_CURRENT_STATE != PC6 |

**Rationale**: Confirms PkgC6 path is disabled; PLL gating only occurs at module level, not package.

---

## Section B: Interactions

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | OS | Request deepest idle (MWAIT C6S-P) | MWAIT |
| 2 | uCode | Propagate to PCode | Q-channel |
| 3 | PCode | Check FUSE_PKG_C_STATE | Fuse |
| 4 | PCode | **Block PC6 (fuse=0)** | Internal |
| 5 | Module | Enter MC6 (module-level) | Q-channel |
| 6 | PLL | **Remain locked** (no package gating) | Hardware |
| 7 | Test | Read pll_lock = 1 | CSR |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|-----|---------|-----------|
| 1 | OS | uCode | MWAIT C6S-P (EAX=0x25) | CPU |
| 2 | uCode | PCode | PkgC request | Q-channel |
| 3 | PCode | Fuse | Read FUSE_PKG_C_STATE | Fuse |
| 4 | Fuse | PCode | **Return 0 (disabled)** | Fuse |
| 5 | PCode | Module | Allow MC6 only | Q-channel |
| 6 | Test | PLL | Read pll_lock | CSR |
| 7 | PLL | Test | **Return 1 (locked)** | CSR |

---

## Section C: Interface Coverage Assessment

| Interface | DMR Coverage | NWP Coverage | Notes |
|-----------|--------------|--------------|-------|
| pma_debug.pll_lock | Yes | **Negative** | Verify locked during MC6 |
| MWAIT C6S-P | Yes | Yes | OS still requests |
| Q-channel | Yes | Yes | Module-level still works |
| FUSE_PKG_C_STATE | N/A | **Negative** | Verify = 0 |
| PKGC_CURRENT_STATE | Yes | **Negative** | Verify never PC6 |

---

## Section D: NWP Specification References

- **NWP PM MAS S6.2**: FUSE_PKG_C_STATE=0 (PkgC6 disabled)
- **PNC PM HAS S8.14**: Package C-state PLL gating architecture
- **KB Article**: [pkgc.md](KB/pm_features/core_c_states/pkgc.md)
- **Register**: sv.sockets.cbbs.computes.core_pmas.core_pmsb_top.core_pma_pmsb.pma_debug.pll_lock

---

## Section E: NWP Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Test executed expecting PC6 | Medium | Low | Skip with documented rationale |
| PLL unexpectedly gated | Low | High | Add negative assertion |
| Module C6 PLL behavior regressed | Low | Medium | Separate MC6 test coverage |

---

## Section F: Recommendations

1. **Skip original test** - PC6 entry not possible on NWP
2. **Derive negative test**: Verify COREPLL remains locked (pll_lock=1) during MC6
3. **Add fuse verification**: Confirm FUSE_PKG_C_STATE=0 as pre-condition
4. **Verify PKGC_CURRENT_STATE**: Never reaches PC6 encoding
5. **Separate MC6 coverage**: Ensure module-level PLL gating tested in MC6 TCs

---

## User Notes

> Instructions for LLM: Read all notes chronologically. Apply corrections/clarifications
> to relevant sections. Do not modify notes - append new entries only.

*(No user notes yet - add feedback to refine this analysis)*
