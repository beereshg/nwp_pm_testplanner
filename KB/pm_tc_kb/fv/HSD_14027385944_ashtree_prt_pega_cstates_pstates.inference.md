# Deep Analysis: AshTree PRT_PEGA CStates / PStates

| Field | Value |
|-------|-------|
| **HSD ID** | 14027385944 |
| **Title** | AshTree PRT_PEGA CStates / PStates |
| **Date** | 2026-05-28 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Core C-States |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

AshTree PRT validates TSC (Time Stamp Counter) monotonicity during concurrent C-state and P-state transitions under PEGA injection stress (38M+ INTx/sec). TSC monotonicity is an architectural requirement that applies identically to NWP. The test adapts by substituting `nwp.xml` for `dmr.xml`, reducing PMX CPU traffic/PEGA scope from 4 CBBs to 2 CBBs, and removing MeshGV-specific frequency checks (MeshGV is not in NWP). The 12-hour duration requirement is unchanged.

**Key Justification:**
- TSC monotonicity is a fundamental architectural guarantee — NWP must pass this test
- C-state + P-state concurrent stress (via PEGA + cpu_traffic) exercises C6/C1E exit interrupt handling
- NWP has 2 CBBs (not 4) and 48 cores/CBB (not 32); PMX topology handled via `nwp.xml`

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon at SVOS (silicon preferred; VP for intent check)
- PMX framework with `nwp.xml`; PEGA injection enabled
- PTAT monitoring tool available
- 12-hour test window allocated

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Boot NWP at SVOS | Same |
| 2 | Start PTAT monitoring | `/usr/local/ptat/ptat -mon -filter 0x0f -id` — unchanged |
| 3 | Run PMX with PEGA cross-product | `-x nwp.xml` (not `dmr.xml`); `-tM 720 -M 10 --retry_count 2` unchanged |
| 4 | Concurrently poll TSC on all cores | MSR 0x10 reads; check monotonicity throughout |
| 5 | Run for minimum 12 hours | Same duration |
| 6 | Collect log; check TSC monotonicity | No backward jumps in MSR 0x10 |

**NWP PMX command:**
```bash
runPmx.py -x nwp.xml -p cpu_traffic -p pega_cross -tM 720 -M 10 --retry_count 2
```

### NWP Pass Criteria
- MSR 0x10 (TSC) is strictly monotonically increasing on ALL active cores throughout 12h run
- No firmware MCA, watchdog, or platform hang
- PTAT reports consistent thermal monitoring data
- PMX PASS reported at end of run

---

## Section C: NWP Delta Impact Analysis

### TSC Scope

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBBs | 4 | 2 | TSC polling loop: `range(2)` not `range(4)` |
| Cores/CBB | 32 | 48 | More cores polled per CBB — more comprehensive per-CBB TSC coverage |
| MeshGV | Present | **Absent** | Skip MeshGV frequency check in TSC validation; DVFS still tested at core level |
| PkgC6 | Supported | ZBB | PkgC6 C-state contributions to TSC excluded |

### PEGA Injection

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| PEGA interrupts | 38M+/sec | Same rate expected | NWP PEGA supports same injection rate |
| pega_cross PMX module | DMR-tuned | May need NWP update | Verify `pega_cross` module addresses NWP interrupt targets correctly |

---

## Section D: Key Registers & Validation Points

### Complete Register/Signal Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| TSC | MSR `0x10` | Full 64-bit | Strictly increasing; no backward jump | Per core, periodic polling |
| CC6 residency | MSR `0x3FD` | Full | Incrementing (C6 exercised) | Per core |
| CC1 residency | MSR `0x778` | Full | Incrementing (C1E exercised) | Per core |
| APIC | Local APIC Timer | Count | Consistent with TSC pace | Per core |

### PythonSv Validation Commands (NWP)

```python
import time

# TSC monotonicity spot-check on NWP (2 CBBs, 48 cores each)
prev_tsc = {}
for cbb_idx in range(2):      # NWP has 2 CBBs
    for mod_idx in range(6):
        for core_idx in range(8):
            key = (cbb_idx, mod_idx, core_idx)
            # Read TSC via MSR 0x10 — use MSR tool or namednodes if exposed
            # tsc_val = sv.socket0.getbypath(f"cbb{cbb_idx}...").msr_read(0x10)
            # assert tsc_val >= prev_tsc.get(key, 0), f"TSC went backward at {key}"
            prev_tsc[key] = 0  # placeholder
            print(f"cbb{cbb_idx}.compute{mod_idx}.module{core_idx}: poll MSR 0x10 for monotonicity")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **pega_cross NWP compatibility** — PMX pega_cross module may target DMR interrupt controllers | High | Verify PEGA injection addresses NWP APIC topology; update pega_cross if needed |
| 2 | **12-hour silicon slot** — requires continuous silicon access | Medium | Schedule during dedicated silicon validation window |
| 3 | **MeshGV checks removed** — TSC validation during DVFS must exclude MeshGV | Low | Confirm NWP TSC validation script doesn't reference MeshGV frequency bins |

---

## Section F: Recommendation

**Recommendation: ADAPT — Update PMX XML to nwp.xml; verify pega_cross module targets NWP topology**

TSC monotonicity under concurrent C-state/P-state/PEGA stress is a critical NWP validation. The main adaptation is `nwp.xml` substitution and pega_cross module NWP verification. Duration (12h) is unchanged.

Required adaptations:
1. Replace `-x dmr.xml` with `-x nwp.xml`
2. Verify `pega_cross` PMX module supports NWP interrupt topology
3. Remove MeshGV frequency bins from TSC pass/fail criteria

**Priority**: High — long-running TSC monotonicity test; must run early in NWP silicon bring-up to detect latent C-state/interrupt interaction bugs
