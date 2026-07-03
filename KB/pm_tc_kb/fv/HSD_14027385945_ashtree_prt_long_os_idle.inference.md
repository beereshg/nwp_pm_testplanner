# Deep Analysis: AshTree PRT Long OS Idle

| Field | Value |
|-------|-------|
| **HSD ID** | 14027385945 |
| **Title** | AshTree PRT Long OS Idle |
| **Date** | 2026-05-28 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Core C-States |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

AshTree PRT Long OS Idle validates TSC monotonicity during extended OS idle (no PEGA injection, no traffic) — the "deep idle" scenario where all cores are at CC6 or MC6 for extended periods. TSC continuity across C6 entry/exit (CTC freeze + restore by PMA) is an architectural requirement fully applicable to NWP. The adaptation is limited to updating PMX XML from `dmr.xml` to `nwp.xml`.

**Key Justification:**
- Long OS idle exercises MC6 (module C6) — supported on NWP; MLC flushed state
- TSC continuity after MC6 exit is a PMA/uCode protocol requirement identical in DMR and NWP
- No PEGA or traffic, so the test is self-contained; NWP topology change is via XML only

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon at SVOS or Linux
- PMX framework with `nwp.xml`; no PEGA injection configured
- TSC polling script ready

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Boot NWP at SVOS (OS idle state) | Same |
| 2 | Run long idle PMX module with NWP config | `-x nwp.xml -p long_os_idle -tM 720 -M 10` |
| 3 | Monitor TSC via MSR 0x10 on all cores | Loop over 2 CBBs (not 4) |
| 4 | Check TSC monotonicity throughout idle | No backward jump after CC6/MC6 exits |
| 5 | Run minimum 12 hours | Same duration requirement |

**NWP PMX command:**
```bash
runPmx.py -x nwp.xml -p long_os_idle -tM 720 -M 10 --retry_count 2
```

### NWP Pass Criteria
- TSC (MSR 0x10) strictly monotonically increasing across all C6/MC6 exit events
- MSR 0x3FD (CC6 residency) increments consistently during idle periods
- No firmware MCA or platform hang during 12h idle run

---

## Section C: NWP Delta Impact Analysis

### MC6 Scope

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| MC6 | Supported | Supported | Core idle progression to MC6 tested on NWP |
| PkgC6 | Supported | ZBB | Long idle will reach MC6/PC0 max (not PC6) on NWP |
| Ring C6 | Supported | ZBB | CCF idle depth limited to Ring C3 on NWP |
| CBBs | 4 | 2 | TSC polling loop reduced |

---

## Section D: Key Registers & Validation Points

### Complete Register/Signal Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| TSC | MSR `0x10` | Full 64-bit | Monotonically increasing | Per core |
| CC6 residency | MSR `0x3FD` | Full | Large value (long idle) | Per core |
| MC6 state | `CORE_ACODE_CR_ACODE_STATUS` | MC6 indicator | Set during idle | Per module |
| CTC sync | CTC snapshot | — | Consistent with TSC after C6 exit | Per core |

### PythonSv Validation Commands (NWP)

```python
# Poll TSC during long idle on NWP (2 CBBs)
for cbb_idx in range(2):      # NWP has 2 CBBs (not 4)
    for mod_idx in range(6):  # 6 modules per CBB on NWP
        print(f"cbb{cbb_idx}.compute{mod_idx}: monitor MSR 0x10 across MC6 exits")

# Check CC6 residency after idle soak
# sv.socket0.cbb0.compute0.module0.msr_read(0x3FD)  # CC6 residency
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **PkgC6 ZBB** — long idle max depth is MC6 + PC0, not PC6 | Low | Reduces scope slightly but TSC test still valid |
| 2 | **Ring C6 ZBB** — CCF stays at Ring C3 max | Low | Adjust expected CCF idle depth; Ring C3 still a valid deep CCF state |
| 3 | **12h silicon time** — schedule with 14027385944 for back-to-back runs | Medium | Coordinate silicon access |

---

## Section F: Recommendation

**Recommendation: ADAPT — Update PMX XML to nwp.xml**

Minimal adaptation needed. Long OS idle is one of the simplest TSC monotonicity tests. Change `dmr.xml` → `nwp.xml`. Acknowledge PkgC6/Ring C6 ZBB reduces max idle depth but does not invalidate the TSC monotonicity requirement under CC6/MC6.

Required adaptations:
1. Replace `-x dmr.xml` with `-x nwp.xml`
2. Update expected max idle depth: MC6/PC0 (not PC6)

**Priority**: High — long-duration deep idle coverage; validates uCode TSC restore after extended C6
