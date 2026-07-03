# Deep Analysis: AshTree PRT Solar C-States/P-States/DVFS

| Field | Value |
|-------|-------|
| **HSD ID** | 14027385946 |
| **Title** | AshTree PRT Solar C-States/P-States/DVFS |
| **Date** | 2026-05-28 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Core C-States |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This AshTree PRT test combines Solar C-state and P-state transitions with DVFS (Dynamic Voltage Frequency Scaling) under stress to validate TSC monotonicity across all concurrent PM events. DVFS and C-state/P-state coordination are fully supported on NWP; the primary adaptation is replacing DMR Solar XML paths with NWP equivalents and excluding MeshGV frequency bins (absent on NWP) from DVFS verification. TSC monotonicity is an unconditional architectural requirement.

**Key Justification:**
- DVFS (VF change during C-state exit) exercises the most stress on TSC continuity — fully applicable to NWP
- Solar C-state/P-state stress framework ports to NWP with XML path update
- MeshGV is absent on NWP → remove MeshGV scope from DVFS frequency checks; core/ring DVFS remains full scope

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon at SVOS
- Solar tool with NWP XMLs; PMX with `nwp.xml`
- DVFS stress enabled (P-state sweep + C-state injection)

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Boot SVOS | Same |
| 2 | Run Solar CStates/PStates/DVFS with NWP config | Update XML path to `SOLAR_NWP_XMLS/...CStates_PStates_DVFS.xml` |
| 3 | Run concurrent DVFS via PMX | `runPmx.py -x nwp.xml -p cpu_traffic -p dvfs_stress -tM 720 -M 10` |
| 4 | Poll TSC on all cores continuously | 2 CBBs × 6 modules × 8 cores |
| 5 | Validate no backward TSC jumps | Critical check after each DVFS transition |
| 6 | Run 12 hours minimum | Same duration |

### NWP Pass Criteria
- TSC strictly monotonically increasing across all C-state + P-state + DVFS events
- No TSC backward jump after any VF transition, C6 entry/exit, or DVFS step
- No firmware MCA; Solar and PMX both report PASS

---

## Section C: NWP Delta Impact Analysis

### DVFS and C-State Scope

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Core DVFS (VF sweep) | Supported | Supported | Primary stress — no change |
| Ring DVFS | Supported | Supported | Ring C3 max idle depth (not Ring C6) |
| MeshGV DVFS | Supported | **Absent** | Remove MeshGV from DVFS sweep scope |
| PkgC6 | Supported | ZBB | Max C-state during DVFS: PC0 (not PC6) |
| CBBs | 4 | 2 | Loop bounds: `range(2)` |
| Solar XML path | `SOLAR_DMR_XMLS` | `SOLAR_NWP_XMLS` | Update path |

---

## Section D: Key Registers & Validation Points

### Complete Register/Signal Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| TSC | MSR `0x10` | 64-bit | Strictly increasing across all events | Per core |
| CC6 residency | MSR `0x3FD` | Full | Non-zero (C6 exercised) | Per core |
| P-state request | MSR `0x199` (IA32_PERF_CTL) | Requested ratio | Changes during DVFS sweep | Per thread |
| P-state status | MSR `0x198` (IA32_PERF_STATUS) | Current ratio | Follows requests | Per thread |
| VF point | TPMI `ptpcfsms.socket_p1_control` | Frequency ratio | Changes during DVFS | Per socket |

### PythonSv Validation Commands (NWP)

```python
# Poll TSC and P-state status during DVFS + C-state stress on NWP
prev_tsc = {}
for cbb_idx in range(2):     # NWP has 2 CBBs
    for mod_idx in range(6):
        for core_idx in range(8):
            key = f"cbb{cbb_idx}.compute{mod_idx}.module{core_idx}"
            # tsc = msr_read(key, 0x10)  # TSC
            # p_state = msr_read(key, 0x198)  # Current P-state
            print(f"{key}: monitor TSC monotonicity + P-state across DVFS transitions")

# Check TPMI P-state control (socket-level DVFS)
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_p1_control.show()
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP Solar DVFS XML** — CStates_PStates_DVFS XML must be ported | High | Adapt DMR Solar XML; remove MeshGV scope |
| 2 | **MeshGV frequency bins** — TSC check code may reference MeshGV frequency steps | Medium | Update DVFS sweep list to exclude MeshGV |
| 3 | **12h silicon access** — coordinate with 14027385944 and 14027385945 | Medium | Run all three PRT tests in sequence |

---

## Section F: Recommendation

**Recommendation: ADAPT — Port Solar DVFS XML; remove MeshGV scope**

Most comprehensive AshTree PRT test. Covers TSC monotonicity under the highest-stress combination: concurrent C-state transitions + P-state sweeps + DVFS. Key NWP adaptation: remove MeshGV from DVFS sweep; update Solar XML path to NWP.

Required adaptations:
1. Port `CStates_PStates_DVFS.xml` Solar XML from DMR to NWP (remove MeshGV scope)
2. Update Solar package path to `nwp`
3. Update PMX command to `-x nwp.xml`

**Priority**: High — most stress coverage of TSC monotonicity under concurrent PM events; run as final PRT test after 14027385944 and 14027385945
