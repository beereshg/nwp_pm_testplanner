# Deep Analysis: pm_pmx_core_power

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421681 |
| **Title** | pm_pmx_core_power |
| **Date** | 2026-05-28 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Socket RAPL > PMX Cross-Product |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This PMX cross-product test exercises Socket RAPL under core power workloads (cpu_rapl PMX module with core-power traffic), validating that RAPL power limiting responds correctly to changing core activity. Socket RAPL is fully supported on NWP. The test adapts by substituting `nwp.xml` for `dmr.xml`; the RAPL control and energy status registers are at the IMH (imh0) level on NWP, not duplicated across CBBs.

**Key Justification:**
- Socket RAPL is on NWP critical path (p2 priority, PMSS_NWP_READINESS_CHECK tagged)
- Core power workload coverage applies to NWP 96-core topology (2 CBBs × 48 cores)
- RAPL throttling response is firmware-driven (Primecode) — same control loop on NWP

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon at SVOS
- PMX framework with `nwp.xml`; cpu_rapl and core_power PMX modules

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run PMX cpu_rapl with core power workload | `runPmx.py -x nwp.xml -p cpu_rapl -p core_power -tM 6 -M 3` |
| 2 | Monitor RAPL energy status during workload | Read `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status` |
| 3 | Verify RAPL throttling engages when PL1/PL2 exceeded | Check perf_limit_reasons via TPMI |
| 4 | Check no firmware MCA | Same criteria |

### NWP Pass Criteria
- PMX reports PASS; RAPL energy status increments correctly under core power load
- RAPL throttling engages within expected tau window when PL1 exceeded
- No firmware MCA or hang

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| RAPL scope | Socket-level at IMH | Same | No change to register paths |
| CBB count | 4 | 2 | Core power load distributed over 2 CBBs |
| PMX XML | `dmr.xml` | `nwp.xml` | Mandatory substitution |
| Platform RAPL (Psys) | Supported | ZBB | Psys verification excluded |

---

## Section D: Key Registers & Validation Points

### Complete Register/Signal Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| RAPL PL1 | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control` | `power_limit_1` | Default TDP | IMH |
| RAPL Energy | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status` | `total_energy_consumed` | Incrementing | IMH |
| Perf limit | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons` | `rapl_pl1` | Set during throttle | IMH |

### PythonSv Validation Commands (NWP)

```python
# Monitor RAPL energy status on NWP
rapl = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms
print("PL1:", rapl.socket_rapl_pl1_control.read())
print("Energy:", rapl.socket_rapl_energy_status.read())
print("Perf limits:", rapl.perf_limit_reasons.read())
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **nwp.xml PMX module** — verify cpu_rapl and core_power modules defined in `nwp.xml` | High | Check NWP PMX XML for module definitions |
| 2 | **Platform RAPL ZBB** — exclude Psys registers from verification | Low | Straightforward exclusion |

---

## Section F: Recommendation

**Recommendation: ADAPT — Change `-x dmr.xml` to `-x nwp.xml`**

Minimal adaptation. Socket RAPL fully supported on NWP. PMX module substitution is the only required change.

Required adaptations:
1. Replace `-x dmr.xml` with `-x nwp.xml`
2. Exclude Platform RAPL (Psys) checks

**Priority**: High — PMSS NWP Readiness Check tagged; p2 priority
