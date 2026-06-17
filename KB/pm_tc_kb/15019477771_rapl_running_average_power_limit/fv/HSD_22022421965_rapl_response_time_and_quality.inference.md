# Deep Analysis: RAPL Response Time and Quality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421965 |
| **Title** | RAPL Response time and quality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | PL1/PL2 convergence time — power must converge within 5× tau |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **RAPL convergence quality**:
- Consumed power (measured via energy status) must converge to PL1 and PL2 within **5× the programmed tau** value
- Uses `pm.pmutils.cpu_rapl.py` functions: `pl1_limit_convergence` and `pl2_limit_convergence`

Test steps:
1. Run workload (e.g., PTU TDP `./ptu -ct 3`)
2. Set PL1/PL2 limit (must be above idle power to ensure convergence)
3. Measure convergence time to the set limit
4. Verify convergence ≤ 5× tau

On NWP: same RAPL PID control loop; tau fuses from `imh0.fuses.punit.*`; `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run cpu_rapl PMx | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 2 | Start workload above idle (PTU TDP) | `./ptu -ct 3` or equivalent on NWP |
| 3 | Call `pl1_limit_convergence(target_pl1)` | Set PL1 above idle power; measure convergence time |
| 4 | Verify convergence time ≤ 5× tau1 | Tau1 read from `IA32_PACKAGE_POWER_LIMIT.TIME_WINDOW_POWER_LIMIT1` |
| 5 | Call `pl2_limit_convergence(target_pl2)` | Set PL2; measure convergence time |
| 6 | Verify convergence time ≤ 5× tau2 | Tau2 from PL2 MSR time window field |

### NWP RAPL MSR Paths

| MSR | Path |
|-----|------|
| Package power limit | `IA32_PACKAGE_POWER_LIMIT` (MSR 0x610) |
| Package energy status | `IA32_PACKAGE_ENERGY_STATUS` (MSR 0x611) |
| Tau field | Bits [23:17] of MSR 0x610 (PL1 tau), bits [55:49] (PL2 tau) |

```python
# NWP convergence test using pmutils
import pm.pmutils.cpu_rapl as rapl
rapl.pl1_limit_convergence(target_watts=<above_idle>)
rapl.pl2_limit_convergence(target_watts=<above_idle>)
```

### NWP Key Note
- Avoid setting PL1/PL2 below idle power (convergence will not occur)
- NWP 96 cores (48/CBB × 2 CBBs) — total socket power must exceed limit for RAPL to activate
- `runPmx.py -x nwp.xml` (not `dmr.xml`)

### Pass Criteria
- PL1 convergence time ≤ 5× tau1
- PL2 convergence time ≤ 5× tau2
- Energy status MSR reflects convergence

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; use `pl1_limit_convergence` + `pl2_limit_convergence` from pmutils**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Run PTU workload; set PL1/PL2 above idle power; measure convergence ≤ 5× tau
3. NWP: 2 CBBs × 48 cores; tau from MSR 0x610; energy from MSR 0x611

**Priority**: Medium — `plc.feature.p2`; RAPL response time quality is a key correctness validation for power management accuracy
