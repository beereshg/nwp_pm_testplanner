# HSD 14020416808: CState Fast C1E: registers_checks_silicon

| Field | Value |
|-------|-------|
| **HSD ID** | [14020416808](https://hsdes.intel.com/appstore/article/#/14020416808) |
| **Segment** | FV |
| **Feature** | Core C-States |
| **Sub-Feature** | Fast C1E |
| **Environment** | silicon, virtual_platform |
| **Status** | open |
| **Owner** | hmpicosm |
| **Command** | `runPmx.py -x dmr.xml -p cstates -H 1 -M 5` |
| **KB Article** | [KB/pm_features/core_c_states/fast_c1e.md](KB/pm_features/core_c_states/fast_c1e.md) |

### Version History

| Version | Date | Changes | Trigger |
|---------|------|---------|---------|
| v1 | 2026-05-29 | Initial generation | `enrich 14020416808` |

---

## Test Case

### Intent

Verify that Fast C1E control registers are correctly programmed on silicon after boot.
This register validation confirms BIOS/firmware properly initialized the C1E subsystem
and that the hardware is ready to execute C1E entry/exit flows.

### Pre-Conditions

1. Boot SVOS with C-states enabled via fuses/BIOS
2. Fast C1E BIOS knob enabled (`control_c1e.enable = 1`)
3. PythonSV environment available for register reads
4. Target: single socket, C-states enabled

### Test Steps

| Step | Action | Interface | Expected |
|------|--------|-----------|----------|
| 1 | Boot SVOS with C-states enabled | BIOS | System boots successfully |
| 2 | Import PythonSV module | PythonSV | `import pm.focused.cstate_focus as cf` |
| 3 | Read `control_c1e.enable` | CSR | Value = 1 (C1E enabled) |
| 4 | Read `io_c1e_wp.core_voltage` | CSR | Value at Vmin (deprecated — verify register exists) |
| 5 | Read `io_c1e_wp.core_frequency` | CSR | Value = 4 (400MHz LFM) (deprecated — verify register exists) |
| 6 | Read `acp_state.core_ratio` | CSR | Same as C1E WP ratio (deprecated) |
| 7 | Read `acp_state.core_voltage` | CSR | Same as C1E WP voltage (deprecated) |
| 8 | Read `acp_state.c1e_period` | CSR | Value = 1 when in C1E (deprecated) |
| 9 | Run `cf.check_cst_focus()` | PythonSV | All C1E register checks pass |

### Pass/Fail Criteria

**PASS:**
- `control_c1e.enable` = 1 (Fast C1E enabled)
- All deprecated register paths exist and return expected values (or gracefully report deprecation)
- `cf.check_cst_focus()` completes without assertion failures

**FAIL:**
- `control_c1e.enable` = 0 (C1E disabled unexpectedly)
- Register read failures or unexpected values
- `cf.check_cst_focus()` raises assertion errors

---

## Section A: NWP Architecture Delta

**Disposition: Revalidate**

Fast C1E is supported on NWP with the same PantherCove (PNC) core and Acode-managed WP calculation.
However, register paths may differ due to NWP topology (2 CBBs vs 4, NIO vs IMH).
The test must be updated to use NWP-specific register paths and verify module-level C1E scope.

### DMR → NWP Delta Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | 4 | 2 | Reduced iteration scope for CBB loops |
| C1E control register path | `sv.sockets.cbbs.computes.pmas.pmsb.control_c1e.enable` | Same path (verify) | Confirm path exists on NWP |
| Module PLL scope | Shared per DCM (2 cores) | Shared per module (2 cores) — **TBD** | Verify MC1E triggers when all module cores idle |
| io_c1e_wp registers | Deprecated in DMR | Likely removed in NWP | Update test to not assert on deprecated registers |
| acp_state registers | Deprecated in DMR | Likely removed in NWP | Update test to not assert on deprecated registers |
| Fast C1E entry latency | ~2 µs | Same (PNC core) | No timing change expected |
| PkgC6 interaction | C1E × PkgC6 cross-product | N/A — PkgC6 removed | Remove cross-product scenarios |

---

## Section B: Interactions

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS | Program MSR 0x1FC (POWER_CTL.C1E_ENABLE=1) | MSR |
| 2 | BIOS | Program Fast C1E BIOS knob | BIOS Setup |
| 3 | PCode | Propagate C1E enable to all PMAs | HPM |
| 4 | PMA | Set control_c1e.enable=1 | CSR |
| 5 | PMA | Pre-populate C1E LFM Work Point | Internal |
| 6 | Test | Read control_c1e.enable via PythonSV | CSR |
| 7 | Test | Verify C1E registers programmed correctly | CSR |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|-----|---------|-----------|
| 1 | BIOS | uCode | Write MSR 0x1FC C1E_ENABLE=1 | MSR |
| 2 | uCode | PCode | Notify C1E configuration | Mailbox |
| 3 | PCode | PMA | Broadcast C1E enable | HPM 0x16 |
| 4 | PMA | FIVR | Configure C1E voltage target | Internal |
| 5 | Test | PMA | Read control_c1e.enable | CSR |
| 6 | Test | PMA | Read io_c1e_wp.* (deprecated) | CSR |
| 7 | Test | ACP | Read acp_state.* (deprecated) | CSR |

---

## Section C: Interface Coverage Assessment

| Interface | Covered | Notes |
|-----------|---------|-------|
| MSR 0x1FC (POWER_CTL) | Indirect | BIOS programs; test reads result via CSR |
| CSR control_c1e.enable | Yes | Primary validation target |
| CSR io_c1e_wp.* | Partial | Deprecated registers — verify existence only |
| CSR acp_state.* | Partial | Deprecated registers — verify existence only |
| TPMI | No | Not used in this register check test |
| HPM messaging | No | Internal flow — not directly validated |
| MWAIT | No | Not exercised — register check only |

---

## Section D: NWP Specification References

- **PNC PM HAS §8.10**: Fast C1E architecture and entry/exit flows
- **PNC PM HAS §8.10.2**: C1E LFM Work Point (server vs client)
- **PNC PM HAS §8.10.3**: Slow C1E detection and timing
- **PNC PM HAS §8.10.5**: HW C1E promotion algorithm
- **PNC PM HAS §8.5.4**: CORE_PMA_CR_CONFIG_0 C1E enable bit
- **NWP PM MAS**: Module-level C1E scope (TBD — confirm shared PLL)
- **KB Article**: [fast_c1e.md](KB/pm_features/core_c_states/fast_c1e.md)

---

## Section E: NWP Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Deprecated register paths removed | High | Medium | Update test to skip deprecated registers; add NWP-specific paths |
| Register path differs on NWP | Medium | Medium | Verify paths with `namednodes.sv.socket0.search("control_c1e")` |
| Module PLL scope difference | Low | Low | Confirm MC1E behavior in NWP PM MAS |
| BIOS knob name change | Low | Medium | Verify BIOS setup options on NWP |
| Test command uses dmr.xml | High | High | Update to use nwp.xml or equivalent |

---

## Section F: Recommendations

1. **Update test command**: Replace `-x dmr.xml` with `-x nwp.xml` (or equivalent NWP config)
2. **Remove deprecated register assertions**: Mark `io_c1e_wp.*` and `acp_state.*` checks as deprecated or remove
3. **Add NWP register path validation**: Use PythonSV `search()` to discover correct C1E register paths on NWP
4. **Add CORE_PMA_CR_CONFIG_0 check**: This is the authoritative C1E enable bit read by uCode
5. **Cross-reference NWP PM MAS**: Confirm module-level C1E (MC1E) scope for shared PLL
6. **Remove PkgC6 cross-product tests**: PkgC6 is ZBB on NWP (FUSE_PKG_C_STATE=0)
7. **Add negative test for C1E disabled**: Verify `control_c1e.enable=0` when BIOS knob is off

---

## User Notes

> Instructions for LLM: Read all notes chronologically. Apply corrections/clarifications
> to relevant sections. Do not modify notes — append new entries only.

*(No user notes yet — add feedback to refine this analysis)*

