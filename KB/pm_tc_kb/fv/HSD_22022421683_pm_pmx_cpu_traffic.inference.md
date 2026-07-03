# Deep Analysis: pm_pmx_cpu_traffic

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421683 |
| **Title** | pm_pmx_cpu_traffic |
| **Date** | 2026-05-28 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Socket RAPL > PMX Cross-Product (CPU Traffic) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test validates Socket RAPL power limiting while the system is under CPU traffic stress, confirming that the RAPL control loop correctly tracks and enforces PL1/PL2 limits even under sustained compute load. The PMX framework drives cpu_traffic workload while the cpu_rapl module monitors power limiting convergence. The test checks that energy status increments accurately and that RAPL throttling engages correctly when limits are reached.

**Key Justification:**
- Socket RAPL and the PMX framework are both supported on NWP (PMSS_NWP_READINESS_CHECK tagged)
- NWP has 2 CBBs × 48 cores = 96 cores; cpu_traffic workload applies at whatever scale NWP PMX supports
- The only required adaptation is substituting `nwp.xml` for `dmr.xml` in the PMX invocation
- Platform RAPL (Psys) is ZBB on NWP — any Psys assertions in the cross-product must be excluded

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon or VP at SVOS boot
- PMX framework installed; `nwp.xml` present with cpu_rapl and cpu_traffic module definitions
- PythonSv / namednodes accessible for register validation
- BIOS knobs `TurboPowerLimitLock` and `TurboPowerLimitCsrLock` **disabled** (to allow dynamic limit writes)

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Launch PMX with cpu_traffic + cpu_rapl modules | `python runPmx.py -x nwp.xml -p cpu_rapl -p cpu_traffic -tM 6 -M 3` — change `dmr.xml` → `nwp.xml` |
| 2 | Confirm PMX-reported power under traffic exceeds default PL1 baseline | Same pass criterion |
| 3 | Verify RAPL throttling engages: perf_limit_reasons shows `rapl_pl1` or `rapl_pl2` | Read `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons` |
| 4 | Verify energy status increments monotonically during workload | Read `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status` before and after |
| 5 | Confirm power drops back below PL1 after RAPL engages, within 5× tau | Same criterion as DMR |
| 6 | Exclude Psys assertions | Skip any Platform RAPL (Psys) checks — ZBB on NWP |

### NWP Pass Criteria
- PMX reports PASS (no RAPL errors, no platform hang)
- Energy status is monotonically increasing during traffic
- `perf_limit_reasons.rapl_pl1` or `rapl_pl2` bit is set while traffic holds power above the limit
- Power converges to PL1 within 5× tau after RAPL engages

---

## Section C: NWP Delta Impact Analysis

### Topology

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBBs | 4 | 2 | cpu_traffic load is distributed across fewer CBBs; PMX load may be proportionally lower |
| Cores/CBB | 32 | 48 | More cores per CBB; total 96 cores available for traffic |
| PMX XML | `dmr.xml` | `nwp.xml` | Mandatory — NWP PMX module definitions are in nwp.xml |
| Platform RAPL | Supported | ZBB | Exclude Psys from any assertion checks |
| SMT | Yes | No | Single-threaded cores on NWP; cpu_traffic workload may behave differently |

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| RAPL PL1 | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control` | `power_limit_1` | ≤ fused TDP | IMH |
| RAPL PL2 | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl2_control` | `power_limit_2` | ≤ 1.25× TDP typical | IMH |
| Energy status | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status` | `total_energy_consumed` | Monotonically increasing | IMH |
| Perf limit | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons` | `rapl_pl1`/`rapl_pl2` | Set during traffic above limit | IMH |

### PythonSv Validation Commands (NWP)

```python
# NWP RAPL cross-product with CPU traffic
rapl = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms

# Capture energy before and after workload
e_before = rapl.socket_rapl_energy_status.read()
# (run workload / PMX for N seconds)
e_after = rapl.socket_rapl_energy_status.read()
assert e_after > e_before, "Energy status did not increment"

# Check RAPL throttling engaged
plr = rapl.perf_limit_reasons.read()
print(f"perf_limit_reasons = 0x{plr:08x}")
# Bit for rapl_pl1/rapl_pl2 should be set if power exceeded limit

# Check PL1/PL2 values
rapl.socket_rapl_pl1_control.show()
rapl.socket_rapl_pl2_control.show()
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **nwp.xml module coverage** — confirm cpu_traffic and cpu_rapl PMX modules are defined in `nwp.xml` | High | Blocker if module missing; file NWP PMX gap HSD |
| 2 | **No TCD steps** — HSD test_steps contains only the template placeholder, no actual flow | Medium | Test relies on PMX infrastructure; PMX pass/fail criterion is sufficient |
| 3 | **Platform RAPL ZBB** — any Psys checks in cross-product framework must be gated | Low | Easy exclusion; PMX framework may handle this via nwp.xml config |

---

## Section F: Recommendation

**Recommendation: ADAPT — Change `-x dmr.xml` to `-x nwp.xml`**

Socket RAPL × CPU traffic is fully valid on NWP. The only required change is the PMX XML path. No algorithm changes needed; the RAPL control loop and energy reporting work identically on NWP at the IMH level.

Required adaptations:
1. Replace `dmr.xml` with `nwp.xml` in PMX invocation
2. Exclude any Psys / Platform RAPL assertions (ZBB on NWP)
3. Verify `nwp.xml` contains cpu_rapl and cpu_traffic module definitions

**Priority**: High — PMSS_NWP_READINESS_CHECK tagged; p2 priority
