# TC: Socket RAPL x PMAX

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422010](https://hsdes.intel.com/appstore/article-one/#/22022422010) |
| **Title** | Socket rapl x Pmax |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL × Cross-products |
| **Sub-Feature** | RAPL × PMAX concurrent limiter arbitration |
| **Parent TCD** | [22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Automation** | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| **Owner** | mps |
| **Val Framework** | PMX, os-svos, python-sv |

---

## Test Case Intent

Validates the **RAPL × PMAX** cross-product scenario defined in [TCD 22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) §5 ("effective frequency ceiling reflects the more restrictive active limiter"). Environment: NWP post-silicon (SVOS).

**Micro-architecture:** Socket RAPL and PMAX are independent power limiters. RAPL uses NN-PID feedback (1 ms loop) to enforce average power limits (PL1/PL2). PMAX is a hardware overcurrent protection circuit that detects instantaneous VccIN voltage droop (hundreds of nanoseconds) and triggers immediate frequency throttling to Psafe. When both are simultaneously active, the effective frequency ceiling should be min(RAPL output, PMAX ceiling). This TC validates that the arbitration is correct and that `perf_limit_reasons` correctly identifies the binding limiter.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon, SVOS |
| Sockets | 1S minimum |
| BIOS knobs | Default RAPL and PMAX configuration; TPMI unlocked |
| OS / Driver | Ubuntu/SVOS; PTU available |
| PythonSV | `pm.pmutils.cpu_rapl` module; PMAX register access via namednodes |
| Feature state | Both Socket RAPL and PMAX enabled |
| NWP topology | 2 CBBs; NIO root die; single VCCIN (NWP-SP) |
| Interface | TPMI for RAPL; CSR/PythonSV for PMAX threshold control |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Launch PMx: `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` | PMx initialized; RAPL defaults active | PMx error |
| 2 | Start PTU TDP workload: `./ptu -ct 3` | All 96 cores loaded; socket power exceeds TDP | PTU fails |
| 3 | Set RAPL PL1 = TDP (permissive — RAPL not actively limiting) | PL1 at TDP; power at or below TDP; RAPL not throttling | RAPL unexpectedly throttling |
| 4 | Trigger PMAX condition (lower PMAX threshold below current power) or inject PMAX via PythonSV | PMAX asserts; frequency immediately drops to PMAX ceiling | PMAX does not trigger |
| 5 | Check `perf_limit_reasons` | PMAX bit asserted; RAPL PL1 bit NOT asserted (PMAX is binding) | Wrong limiter indicated |
| 6 | Verify effective frequency = PMAX ceiling (not RAPL output) | Core frequency at PMAX-dictated level | Frequency at RAPL level or incorrect |
| 7 | Now set RAPL PL1 well below PMAX ceiling | RAPL becomes binding limiter | TPMI write rejected |
| 8 | Wait for PID convergence (≤ 5 × tau1) | Power converges to PL1; RAPL actively throttling | Power does not converge to PL1 |
| 9 | Check `perf_limit_reasons` | RAPL PL1 bit[10] asserted; PMAX bit may or may not be asserted depending on power level | Wrong limiter indicated |
| 10 | Verify effective frequency = RAPL output (more restrictive than PMAX) | Core frequency at RAPL-dictated level | Frequency at PMAX level or incorrect |
| 11 | Release PMAX condition (restore threshold) | Only RAPL remains active; no PMAX influence | PMAX stuck active |
| 12 | Restore PL1 = TDP; stop workload | System returns to idle; no limits active | Limits stuck |

---

### Pass / Fail Criteria

**Bar:** Per [TCD 22022420806](https://hsdes.intel.com/appstore/article-one/#/22022420806) §5: effective frequency ceiling reflects the more restrictive active limiter.

**PASS** when ALL of the following are true:
- When PMAX < RAPL: effective ceiling = PMAX; `perf_limit_reasons` shows PMAX as binding
- When RAPL < PMAX: effective ceiling = RAPL; `perf_limit_reasons` shows RAPL PL1 as binding
- Arbitration: min(PMAX, RAPL) correctly enforced at all times
- Transitions between binding limiters are clean (no glitch, no incorrect override)
- No MCAs, dmesg errors, or system hangs

**FAIL** when ANY of the following are true:
- Wrong limiter binding (RAPL overrides PMAX or vice versa when incorrect)
- `perf_limit_reasons` does not identify correct binding limiter
- Frequency ceiling does not match the more restrictive limiter
- System hang, MCA, or unexpected reset

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| `TPMI PL1_CONTROL` (idx=2) | `sv.socket0.nio.punit.tpmi.pl1_control.read()` | PWR_LIM matches programmed value |
| `TPMI ENERGY_STATUS` (idx=7) | `sv.socket0.nio.punit.tpmi.energy_status.read()` | Counter incrementing |
| `perf_limit_reasons` | PMx readout | Correct limiter bits asserted |
| PMAX status | `sv.socket0.nio.punit.ptpcfsms.*` | PMAX trigger status matches test condition |
| `dmesg` | `dmesg \| grep -i 'mca\|error\|pmax\|rapl'` | No unexpected errors |

### Post-Process

N/A — RAPL and PMAX status captured inline by PMx and register reads.

### References

- [TCD 22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806)
- [Socket RAPL KB — socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md)
- [PMAX KB — pmax.md](../../pm_features/power_rapl/pmax.md)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html)

---

## NWP Adaptation Notes

| DMR | NWP |
|-----|-----|
| `dmr.xml` | `nwp.xml` |
| 4 CBBs, dual VCCIN (AP) | 2 CBBs, single VCCIN (SP) |
| `sv.socket0.imh0.punit.ptpcfsms.*` | `sv.socket0.nio.punit.ptpcfsms.*` |
| Per-IMH PMAX detectors (DMR-AP) | Single NIO PMAX detector |

**Disposition: Runnable_On_N-1** — Change XML config. NWP single-VCCIN simplifies PMAX topology (one detector instead of two). RAPL × PMAX arbitration logic is identical.
