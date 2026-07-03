# HSD 22022422596: PkgC x SPD I3C_silicon

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422596](https://hsdes.intel.com/appstore/article/#/22022422596) |
| **Segment** | FV |
| **Feature** | Package C-States |
| **Sub-Feature** | PkgC x SPD I3C |
| **Environment** | virtual_platform |
| **Status** | open |
| **Owner** | mmaltese |
| **TPF Parent** | [2202242049](https://hsdes.intel.com/appstore/article/#/2202242049) |
| **KB Article** | [KB/pm_features/core_c_states/pkgc.md](KB/pm_features/core_c_states/pkgc.md) |

### Version History

| Version | Date | Changes | Trigger |
|---------|------|---------|---------|
| v1 | 2026-05-29 | LLM-driven enrichment with negative test derivation | `enrich batch TPF 2202242049` |

---

## Test Case

### Intent

Verify SPD I3C error injection handling during PC6apply.

### Pre-Conditions

1. Boot SVOS with PkgC enabled via BIOS (DMR configuration)
2. PythonSV environment available
3. System at idle or controlled traffic state

### Pass/Fail Criteria (DMR)

**PASS:** PC6 entry achieved, test-specific assertions pass
**FAIL:** PC6 entry blocked or assertions fail

---

## Section A: NWP Architecture Delta

**Disposition: Skip (derive negative)**

PkgC6 is **fused off** on NWP (FUSE_PKG_C_STATE=0). This test validates PC6 functionality
which is disabled on NWP by hardware fuse.

### DMR to NWP Delta Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| PkgC6 entry | Supported | **Blocked** (fuse=0) | Test scope changes |
| FUSE_PKG_C_STATE | 1 (enabled) | **0 (disabled)** | Hardware blocks PC6 |
| CBB PKG_C_STATE_LIMIT_REQ | Allows PC6 | **=0 (blocked)** | Firmware blocks PC6 |
| MSR 0x3F9 PC6 residency | Accumulates | **Always 0** | Counter unused |
| Deepest idle | PC6 | MC6 | Module C6 is deepest |

### Negative Test Derivation for NWP

**Verify SPD I3C errors handled without PC6 interaction**

This validates that the ZBB fuse is correctly applied and no unintended PC6 behavior occurs.

---

## Section B: Interactions

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | OS | Request deepest idle | MWAIT |
| 2 | uCode | Propagate C-state request | Q-channel |
| 3 | PCode | Check FUSE_PKG_C_STATE | Fuse |
| 4 | PCode | **Block PC6 (fuse=0)** | Internal |
| 5 | Module | Enter MC6 (deepest allowed) | Q-channel |
| 6 | Test | Verify negative assertion | CSR/MSR |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|-----|---------|-----------|
| 1 | OS | uCode | MWAIT C6S-P | CPU |
| 2 | uCode | PCode | PkgC request | Q-channel |
| 3 | PCode | Fuse | Read FUSE_PKG_C_STATE | Fuse |
| 4 | Fuse | PCode | **Return 0** | Fuse |
| 5 | PCode | uCode | Deny PC6, allow MC6 | Q-channel |
| 6 | Test | MSR | Read 0x3F9 | MSR |
| 7 | MSR | Test | **Return 0** | MSR |

---

## Section C: Interface Coverage Assessment

| Interface | DMR Coverage | NWP Negative Coverage | Notes |
|-----------|--------------|----------------------|-------|
| FUSE_PKG_C_STATE | N/A | **Critical** | Verify = 0 |
| MSR 0x3F9 | Yes | **Negative** | Verify = 0 always |
| MSR 0xE2 | Yes | **Negative** | Verify limit blocks PC6 |
| Q-channels | Yes | Partial | MC6 path still exercised |
| PKGC_CURRENT_STATE | Yes | **Negative** | Verify never = PC6 |

---

## Section D: NWP Specification References

- **NWP PM MAS S6.2**: FUSE_PKG_C_STATE=0 (PkgC6 disabled)
- **PNC PM HAS S8.14**: Package C-state architecture
- **KB Article**: [pkgc.md](KB/pm_features/core_c_states/pkgc.md)

---

## Section E: NWP Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Original test executed on NWP | Medium | Low | Document Skip disposition |
| Negative test missing | Medium | Medium | Derive and implement |
| Fuse verification gap | Low | High | Add fuse check to suite |

---

## Section F: Recommendations

1. **Disposition**: Skip (derive negative)
2. **Negative test**: Verify SPD I3C errors handled without PC6 interaction
3. **Fuse verification**: Add FUSE_PKG_C_STATE=0 check to NWP test prerequisites
4. **MC6 coverage**: Ensure equivalent MC6 test exists if applicable
5. **Document rationale**: Link this analysis to HSD ticket as reference

---

## User Notes

> Instructions for LLM: Read all notes chronologically. Apply corrections/clarifications
> to relevant sections. Do not modify notes - append new entries only.

*(No user notes yet - add feedback to refine this analysis)*
