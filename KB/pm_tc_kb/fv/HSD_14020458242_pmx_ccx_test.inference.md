# Deep Analysis: PMX ccx_test

| Field | Value |
|-------|-------|
| **HSD ID** | 14020458242 |
| **Title** | PMX ccx_test |
| **Date** | 2026-05-28 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Core C-States |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PMX ccx_test is a self-checking PMX test module that exercises the full C-state state machine (C0/C1/C6 entries, exits, residency counters) under concurrent PM activity. Core C-states are fully supported on NWP with 2 CBBs and 48 cores per CBB; the test adapts by substituting `nwp.xml` for `dmr.xml` and reducing loop bounds from 4 CBBs to 2.

**Key Justification:**
- Core C-states (C0/C1/C1E/C6) are on NWP critical path — all sub-states present
- PMX framework supports NWP via `nwp.xml` configuration
- ccx_residency_test.py validates state machine integrity independent of CBB count; NWP requires only topology config change

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon or VP platform at SVOS
- PMX tool installed; `nwp.xml` available
- NGA default flow running; FlexCon checks passing
- Pre-test self-check steps validated independently

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Configure NGA flow (FlexCon default) | Same — NWP supports NGA flow |
| 2 | Run PMX ccx_test with NWP config | Change `-x dmr.xml` → `-x nwp.xml`: `runPmx.py -x nwp.xml -p cstates -H 1 -M 5` |
| 3 | Alternatively run directly | `python /usr/lib/python3/dist-packages/nwp/pm/Idle_PM/cstates/ccx_residency_test.py` |
| 4 | Validate residency counters | Check MSR 0x3FD (CC6), 0x778 (CC1) for non-zero counts on all active cores |
| 5 | Check self-checking pass/fail output | All PMX tests are self-checking — PASS reported in log |

### NWP Pass Criteria
- PMX reports PASS for all ccx_test sub-tests
- CC6/CC1 residency counters increment correctly on both CBBs (cbb0, cbb1)
- No firmware MCA or hang during C-state transitions

---

## Section C: NWP Delta Impact Analysis

### Topology

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | 4 | 2 | Loop bounds in test reduced; `-x nwp.xml` handles automatically |
| Cores/CBB | 32 | 48 | More cores per CBB — residency test covers larger domain per CBB |
| Module count | 8 per CBB | 6 per CBB | Module iteration in ccx_residency_test.py must use NWP module count |
| PkgC6 | Supported | ZBB | ccx_test scoped to CC6 (core) — PkgC6 not exercised |

### Environment

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| SVOS/PMX | Supported | Supported | No change |
| Virtual Platform | Available | Available | Intent-check on VP before silicon |

---

## Section D: Key Registers & Validation Points

### Complete Register/Signal Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| C6 Residency | MSR `0x3FD` | Full value | Non-zero after C6 exercise | Per core |
| C1 Residency | MSR `0x778` | Full value | Non-zero after C1 exercise | Per core |
| Core Status | `CORE_PMA_CR_CORE_STATUS` | — | CC0 after wakeup | Per core |
| C-State Enable | MSR `0xE2` | `C1_AUTO_DEMOTE_EN`, `C6_ENABLE` | Both set per BIOS knobs | Per socket |

### PythonSv Validation Commands (NWP)

```python
# Check C6 and C1 residency on all NWP cores (2 CBBs, 48 cores each)
for cbb_idx in range(2):
    for mod_idx in range(6):        # 6 modules per CBB on NWP
        for core_idx in range(8):   # 8 cores per module
            path = f"cbb{cbb_idx}.compute{mod_idx}.module{core_idx}"
            core = sv.socket0.getbypath(path)
            # MSR reads via namednodes (if exposed) or via tool
            print(f"{path}: check CC6/CC1 residency counters")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **PMX nwp.xml availability** — ccx_test requires NWP-specific XML config | High | Verify `nwp.xml` includes cstates PMX module; create if missing |
| 2 | **Module count mismatch** — ccx_residency_test.py may hardcode DMR module count | Medium | Check script for `range(8)` module loops; adjust to NWP `range(6)` |
| 3 | **VP vs silicon** — intent check on VP before silicon run | Low | Standard pre-silicon checkout flow |

---

## Section F: Recommendation

**Recommendation: ADAPT — Minor XML config and module count adjustment**

Change `-x dmr.xml` to `-x nwp.xml` and verify ccx_residency_test.py module loop bounds match NWP (6 modules/CBB, not 8). The core state machine logic and residency counter checks are identical between DMR and NWP.

Required adaptations:
1. Substitute `nwp.xml` for `dmr.xml` in PMX command line
2. Verify/update ccx_residency_test.py module iteration to use NWP topology
3. Validate on VP before silicon run

**Priority**: High — foundational C-state test; validates state machine integrity for all other C-state TCs
