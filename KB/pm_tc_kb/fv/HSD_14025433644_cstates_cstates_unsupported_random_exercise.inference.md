# Deep Analysis: [Solar] CStates - CStates_unsupported_Random -- Exercise

| Field | Value |
|-------|-------|
| **HSD ID** | 14025433644 |
| **Title** | [Solar] CStates - CStates_unsupported_Random -- Exercise |
| **Date** | 2026-05-28 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Core C-States |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This Solar exercise test validates that the processor handles unsupported MWAIT encodings gracefully — no hangs, no bad behavior — when cores issue MWAIT hints that correspond to C-states not enumerated by BIOS. On NWP, the set of "unsupported" encodings differs from DMR (e.g., C6S-P/PkgC6-related codes are now ZBB rather than merely unsupported), but the resilience validation goal is identical. The Solar XML path must be updated from DMR-specific paths to NWP equivalents.

**Key Justification:**
- Unsupported MWAIT handling (falling back to C1 or C0) is an architectural requirement shared between DMR and NWP
- Solar framework supports NWP via updated XML paths; exercise phase is topology-independent
- Random unsupported MWAIT pattern adds stress; NWP 2-CBB/48-core topology handled automatically by Solar scope config

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon or VP at SVOS
- Solar tool installed; NWP Solar XMLs available under `/usr/lib/python3/dist-packages/nwp/pm/Solar/SOLAR_NWP_XMLS/`
- C-states enabled/disabled per BIOS/fuse configuration

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Configure BIOS C-state enable/disable | Same; use NWP BIOS knob names |
| 2 | Run Solar exercise with random unsupported MWAIT | Update XML path: `SOLAR_NWP_XMLS/Exercise/CSTATES/Cstates_unsupported_Mwait_random_exercise.xml` |
| 3 | Monitor for hangs or bad behavior | Same pass/fail criteria |
| 4 | Collect Solar log | `/logpath . /log_ip_disables` — same flags |

**NWP command (adapted):**
```bash
/usr/bin/solar/solar.sh /cfg /usr/lib/python3/dist-packages/nwp/pm/Solar/SOLAR_NWP_XMLS/Exercise/CSTATES/Cstates_unsupported_Mwait_random_exercise.xml /logpath . /log_ip_disables
```

### NWP Pass Criteria
- No platform hang or watchdog trigger during random unsupported MWAIT exercise
- No firmware MCA generated (unsupported MWAIT should be benign — fall to C0/C1)
- Solar log shows PASS with no error flags

---

## Section C: NWP Delta Impact Analysis

### Unsupported MWAIT Set

| Encoding | DMR Status | NWP Status | Notes |
|----------|-----------|-----------|-------|
| C7/C8 hints | Unsupported | Unsupported | Same behavior expected |
| C6S-P (0x20) | Supported | ZBB | Now in "unsupported" set on NWP |
| Ring C6 hints | Supported | ZBB | Now in "unsupported" set on NWP |
| Valid C6 (0x22) | Supported | Supported | Not in unsupported set |

### Topology

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBBs | 4 | 2 | Solar scope config covers NWP automatically |
| Solar XML set | DMR-specific | NWP-specific | Update path from `diamondrapids` → `nwp` |

---

## Section D: Key Registers & Validation Points

### Complete Register/Signal Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| Core state | `CORE_PMA_CR_CORE_STATUS` | CC_STATE | CC0 or CC1 after unsupported hint | Per core |
| Thread status | `CORE_PMA_CR_THREAD_STATUS` | TC_STATE | TC0 after recovery | Per core |
| Watchdog | PMU watchdog registers | Expiry | No expiry | Per socket |

### PythonSv Validation Commands (NWP)

```python
# After Solar exercise, verify all cores returned to active state
for cbb_idx in range(2):   # NWP has 2 CBBs
    for mod_idx in range(6):
        core_path = f"cbb{cbb_idx}.compute{mod_idx}"
        # Check core is responsive — no hang
        print(f"Verify {core_path}: no hang, cores returned to CC0")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP Solar XML availability** — Cstates_unsupported XML must exist for NWP | High | Port or create NWP Solar XML from DMR version |
| 2 | **ZBB C-state codes now "unsupported"** — NWP behavior for C6S-P/Ring C6 hints must be validated | Medium | Confirm NWP falls gracefully to C1 for these codes |
| 3 | **DMR path hardcoded in XML** — Solar XML may hardcode `diamondrapids` package path | Medium | Update XML package path to `nwp` equivalent |

---

## Section F: Recommendation

**Recommendation: ADAPT — Update Solar XML path from DMR to NWP**

The test intent (unsupported MWAIT resilience) is fully applicable to NWP. Main work is porting the Solar exercise XML from DMR-specific paths to NWP. The NWP set of "unsupported" encodings is slightly larger (includes ZBB'd C6S-P/Ring C6), which only increases coverage value.

Required adaptations:
1. Port `SOLAR_DMR_XMLS/Exercise/CSTATES/Cstates_unsupported_Mwait_random_exercise.xml` → NWP equivalent
2. Update package path from `diamondrapids` → `nwp` in Solar command
3. Validate that ZBB'd C-state codes (C6S-P, Ring C6) are handled gracefully

**Priority**: Medium — resilience test; important for stability but not blocking path
