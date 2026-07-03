# Deep Analysis: [Solar]_CStates-CStates_unsupported--Verify

| Field | Value |
|-------|-------|
| **HSD ID** | 14025433677 |
| **Title** | [Solar]_CStates-CStates_unsupported--Verify |
| **Date** | 2026-05-28 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Core C-States |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This Solar verify test confirms that unsupported MWAIT encodings do not cause hangs or incorrect C-state machine behavior, using a deterministic (non-random) MWAIT sequence. The verify phase complements the exercise phase (14025433644) by checking state consistency after the stimulus. On NWP, the Solar XML path requires porting from DMR-specific paths; the verification logic itself is topology-independent.

**Key Justification:**
- Verify phase provides deterministic coverage of specific unsupported MWAIT encodings
- NWP C-state machine handles unsupported hints identically to DMR (fall to C0/C1)
- Solar scope parameters adapt automatically to NWP CBB/core count via XML config

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon or VP at SVOS
- Solar tool with NWP XML paths
- C-states configured per BIOS

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Configure BIOS C-state settings | Same as DMR |
| 2 | Run Solar verify (deterministic unsupported MWAIT) | Update path to `SOLAR_NWP_XMLS/Verify/CSTATES/Cstates_unsupported_Mwait_verify.xml` |
| 3 | Check no hangs or bad behavior | Same pass criteria |
| 4 | Collect log with ip_disables | `/logpath . /log_ip_disables` unchanged |

**NWP command (adapted):**
```bash
/usr/bin/solar/solar.sh /cfg /usr/lib/python3/dist-packages/nwp/pm/Solar/SOLAR_NWP_XMLS/Verify/CSTATES/Cstates_unsupported_Mwait_verify.xml /logpath . /log_ip_disables
```

### NWP Pass Criteria
- No hang or platform reset during unsupported MWAIT verify sequence
- No firmware MCA; Solar reports PASS
- All cores return to CC0 after each unsupported hint

---

## Section C: NWP Delta Impact Analysis

### Topology

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBBs | 4 | 2 | Solar XML scope parameter handles automatically |
| C6S-P, Ring C6 | Supported | ZBB | These codes now unsupported on NWP → additional verify coverage |
| Solar XML path | `diamondrapids/pm/Solar/SOLAR_DMR_XMLS` | `nwp/pm/Solar/SOLAR_NWP_XMLS` | Path update required |

---

## Section D: Key Registers & Validation Points

### Complete Register/Signal Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| Core state | `CORE_PMA_CR_CORE_STATUS` | CC_STATE | CC0 after each unsupported hint | Per core |
| C-state machine | MSR `0xE2` | C-state enable bits | Unchanged by unsupported hints | Per socket |
| Watchdog | Platform WD | Expiry | None | Socket level |

### PythonSv Validation Commands (NWP)

```python
# Verify all NWP cores are in CC0 after unsupported MWAIT verify sequence
for cbb_idx in range(2):   # NWP has 2 CBBs
    for mod_idx in range(6):
        for core_idx in range(8):
            path = f"cbb{cbb_idx}.compute{mod_idx}.module{core_idx}"
            print(f"Check {path}: CORE_PMA_CR_CORE_STATUS == CC0")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP Solar XML porting** — Verify XML must be created for NWP | High | Mirror DMR XML structure with NWP topology params |
| 2 | **Ordering vs exercise** — run exercise (14025433644) before verify | Low | Solar standard practice; verify assumes no residual bad state |

---

## Section F: Recommendation

**Recommendation: ADAPT — Port Solar verify XML from DMR to NWP**

Deterministic verify phase of the unsupported MWAIT resilience test. Same adaptation as exercise phase: port Solar XML and update package path. Run after exercise (14025433644).

Required adaptations:
1. Port `Cstates_unsupported_Mwait_verify.xml` from DMR to NWP
2. Update Solar package path to `nwp`

**Priority**: Medium — verify phase paired with exercise; schedule together
