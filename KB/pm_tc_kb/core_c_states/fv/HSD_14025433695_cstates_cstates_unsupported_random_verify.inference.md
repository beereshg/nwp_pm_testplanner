# Deep Analysis: [Solar] CStates - CStates_unsupported_Random -- Verify

| Field | Value |
|-------|-------|
| **HSD ID** | 14025433695 |
| **Title** | [Solar] CStates - CStates_unsupported_Random -- Verify |
| **Date** | 2026-05-28 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Core C-States |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This Solar verify test combines random unsupported MWAIT patterns with post-exercise state consistency checking. Random ordering stresses the C-state machine more broadly than deterministic verify (14025433677). The test is directly applicable to NWP after Solar XML path update and scope reconfiguration from DMR CBB/core topology to NWP (2 CBBs, 48 cores).

**Key Justification:**
- Random unsupported MWAIT verify provides broader coverage than deterministic sequence
- NWP handles unsupported MWAIT hints with the same fall-through mechanism (→ C0/C1)
- Solar scope adapts to NWP automatically with correct XML topology parameters

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon or VP at SVOS
- NWP Solar XML paths available
- Prerequisite: exercise phase (14025433644) passed

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Boot SVOS with C-states enabled/disabled per BIOS | Same |
| 2 | Run Solar random unsupported MWAIT verify | Update path: `SOLAR_NWP_XMLS/Verify/CSTATES/Cstates_unsupported_Mwait_random_verify.xml` |
| 3 | Check no hangs or bad behavior | Same criteria |
| 4 | Check Solar log for PASS | `/logpath . /log_ip_disables` |

**NWP command (adapted):**
```bash
/usr/bin/solar/solar.sh /cfg /usr/lib/python3/dist-packages/nwp/pm/Solar/SOLAR_NWP_XMLS/Verify/CSTATES/Cstates_unsupported_Mwait_random_verify.xml /logpath . /log_ip_disables
```

### NWP Pass Criteria
- No hang during random unsupported MWAIT verify
- No firmware MCA; Solar reports PASS
- Platform stable; all cores return to CC0 between hints

---

## Section C: NWP Delta Impact Analysis

### Coverage Change

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Random MWAIT space | DMR C-state encodings | NWP C-state encodings (ZBB'd = additional unsupported) | Slightly broader "unsupported" set on NWP |
| CBB scope | 4 CBBs | 2 CBBs | Solar XML scope reconfigured |
| Solar XML | `SOLAR_DMR_XMLS` | `SOLAR_NWP_XMLS` | Path update |

---

## Section D: Key Registers & Validation Points

### Complete Register/Signal Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| Core state | `CORE_PMA_CR_CORE_STATUS` | CC_STATE | CC0 after verify | Per core |
| C-state counters | MSR `0x3FD`, `0x778` | Residency | Valid (no counter corruption) | Per core |
| Platform stability | Watchdog, MCA status | All | No trigger | Socket |

### PythonSv Validation Commands (NWP)

```python
# Spot-check residency counters on NWP after verify
for cbb_idx in range(2):   # NWP has 2 CBBs
    for mod_idx in range(6):
        print(f"cbb{cbb_idx}.compute{mod_idx}: check CC6/CC1 residency — no corruption")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP Solar XML** — random verify XML must be ported | High | Mirror DMR structure with NWP params |
| 2 | **Dependency on exercise phase** — run 14025433644 first | Low | Standard Solar test sequencing |

---

## Section F: Recommendation

**Recommendation: ADAPT — Port Solar random verify XML to NWP**

Third in the unsupported MWAIT trio (14025433644 exercise → 14025433677 verify → 14025433695 random verify). Port all three Solar XMLs together for efficiency.

Required adaptations:
1. Port `Cstates_unsupported_Mwait_random_verify.xml` to NWP
2. Update Solar package path to `nwp`

**Priority**: Medium — complete the unsupported MWAIT test triplet
