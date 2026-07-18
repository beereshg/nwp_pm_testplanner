# TC: RAPL Response Time and Quality

| Field | Value |
|-------|-------|
| **HSD ID** | [22022421965](https://hsdes.intel.com/appstore/article-one/#/22022421965) |
| **Title** | RAPL Response time and quality |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | PL1/PL2 NN-PID convergence time and response quality |
| **Parent TCD** | [22022420798 — Socket RAPL Algorithm & Functionality Verification](https://hsdes.intel.com/appstore/article-one/#/22022420798) |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Automation** | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| **Owner** | mps |
| **Val Framework** | os-svos, python-sv |

---

## Test Case Intent

Validates the **PL1/PL2 NN-PID convergence time and response quality** scenario defined in [TCD 22022420798 — Socket RAPL Algorithm & Functionality Verification](https://hsdes.intel.com/appstore/article-one/#/22022420798) §5 ("PL1 response time: 3–5 × τ; PL2 response time: ~8 ms; frequency oscillation ≤ ±1 bin; steady-state error < 1%"). Environment: NWP post-silicon (SVOS).

**Micro-architecture:** Socket RAPL enforces package power limits via NN-PID control loops running in **PrimeCode (NIO die)** at 1 ms cadence. Power telemetry (IMON via SVID) feeds the PID; the min-resolved output (`RAPL_PID_FREQ_OUTPUT`) is distributed via HPM 0x14 to CBB×2 PCode, which enforces frequency ceilings. This TC measures convergence time — the interval from PL1/PL2 activation to when measured power settles at the target ± error margin — and validates response quality (no oscillation > ±1 bin).

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon, SVOS |
| Sockets | 1S minimum |
| BIOS knobs | Default RAPL configuration; PL1 = TDP (fused), PL2 = 1.2 × TDP; TPMI unlocked |
| OS / Driver | Ubuntu/SVOS; `intel_pstate` driver loaded; PTU available |
| PythonSV | `pm.pmutils.cpu_rapl` module available; `runPmx.py` accessible |
| Feature state | Socket RAPL enabled (default); no platform-level RAPL lock |
| Workload | PTU TDP workload (`./ptu -ct 3`) driving >100% TDP power consumption |
| Starting state | System at idle or under steady-state workload before limit change |
| NWP topology | 2 CBBs × 48 cores = 96 total cores; NIO root die runs PrimeCode NN-PID |
| Interface | **TPMI only** — legacy MSRs 0x610/0x611/0x606 are deprecated on NWP (reads=0, writes silently dropped) |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Launch PMx RAPL automation: `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` | PMx initializes; `cpu_rapl` plugin loaded; NWP topology detected (2 CBBs) | PMx startup error; plugin load failure |
| 2 | Start PTU TDP workload on all 96 cores: `./ptu -ct 3` | All cores loaded; socket power exceeds TDP; `TPMI ENERGY_STATUS` counter incrementing | PTU fails to start; insufficient load; energy counter stale |
| 3 | Read current tau1 value: `TPMI PL1_CONTROL.TIME_WINDOW` (bits [24:18]) | Tau1 reported (default 1 s, range 1–5 s) | TIME_WINDOW = 0 or out of valid range |
| 4 | Call `pl1_limit_convergence(limit=<target_pl1>)` with target above idle power but below TDP | Function sets PL1 via TPMI; monitors ENERGY_STATUS over time; reports convergence time | Function error; TPMI write rejected |
| 5 | Verify PL1 convergence time ≤ 5 × tau1 | Convergence time reported ≤ 5 × tau1 (e.g., ≤ 5 s for tau1 = 1 s) | Convergence time exceeds 5 × tau1; "PL1 did not converge" message |
| 6 | Verify PL1 steady-state power error < 1% of target | `abs(measured_power - target_pl1) / target_pl1 < 0.01` | Steady-state error ≥ 1% |
| 7 | Read tau2 value: `TPMI PL2_CONTROL.TIME_WINDOW` (bits [24:18]) | Tau2 reported (default 16 ms, range 11.7–39 ms) | TIME_WINDOW = 0 or out of valid range |
| 8 | Call `pl2_limit_convergence(limit=<target_pl2>)` with target above idle power | Function sets PL2 via TPMI; monitors convergence | Function error; TPMI write rejected |
| 9 | Verify PL2 convergence time ≤ 5 × tau2 | Convergence time reported ≤ 5 × tau2 (e.g., ≤ 80 ms for tau2 = 16 ms) | Convergence time exceeds 5 × tau2 |
| 10 | Verify PL2 steady-state power error < 1% of target | `abs(measured_power - target_pl2) / target_pl2 < 0.01` | Steady-state error ≥ 1% |
| 11 | Monitor core frequency oscillation at PL1 steady state | Core frequency ripple ≤ ±1 bin (±100 MHz) at convergence | Frequency oscillation > ±1 bin |
| 12 | Check `perf_limit_reasons` bit[10] (PKG_PL1_INBAND) during PL1 throttle | Bit asserted while PL1 is actively limiting power | Bit not asserted during active throttle |
| 13 | Stop PTU workload; verify power returns to idle | Socket power drops below PL1; `perf_limit_reasons` PL1 bit clears | Power remains elevated; perf_limit_reasons stuck |

---

### Pass / Fail Criteria

**Bar:** Per [TCD 22022420798](https://hsdes.intel.com/appstore/article-one/#/22022420798) §5:
- PL1 response time: 3–5 × τ
- PL2 response time: ~8 ms
- Frequency oscillation at steady state: ≤ ±1 bin (100 MHz)
- Steady-state power error: < 1% of target power limit

**PASS** when ALL of the following are true:
- PL1 convergence time ≤ 5 × tau1
- PL2 convergence time ≤ 5 × tau2
- Steady-state power error < 1% for both PL1 and PL2
- Core frequency oscillation ≤ ±1 bin (100 MHz) at steady state
- `perf_limit_reasons` bit[10] correctly asserts during PL1 throttle and clears when power drops below limit
- No dmesg errors, MCAs, or system hangs during test

**FAIL** when ANY of the following are true:
- PL1 or PL2 convergence time exceeds 5 × tau
- Steady-state power error ≥ 1%
- Frequency oscillation > ±1 bin
- `perf_limit_reasons` bit[10] behavior incorrect
- System hang, MCA, or unexpected reset

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| `TPMI ENERGY_STATUS` (idx=7) | `sv.socket0.nio.punit.tpmi.energy_status.read()` | Counter incrementing; non-zero after workload |
| `TPMI PERF_STATUS` (idx=8) | `sv.socket0.nio.punit.tpmi.perf_status.read()` | `PWR_LIMIT_THROTTLE_CTR` > 0 during PL1 throttle |
| `TPMI PL1_CONTROL` (idx=2) | `sv.socket0.nio.punit.tpmi.pl1_control.read()` | `PWR_LIM` matches programmed value; `TIME_WINDOW` in valid range |
| `TPMI PL_INFO` (idx=9) | `sv.socket0.nio.punit.tpmi.pl_info.read()` | `MAX_PL1` = TDP (fused); `MAX_PL2` = 1.2 × TDP |
| `perf_limit_reasons` | PMx `perf_limit_reasons` readout | Bit[10] (PKG_PL1_INBAND) behavior correct |
| `dmesg` | `dmesg \| grep -i 'mca\|error\|rapl'` | No unexpected errors |
| `PACKAGE_RAPL_LIMIT_CFG` | `sv.socket0.nio.punit.package_rapl_limit_cfg.read()` | PL1/PL2 fields match TPMI programming |

### Post-Process

N/A — convergence results captured inline by `pl1_limit_convergence` / `pl2_limit_convergence` functions.

### References

- [TCD 22022420798 — Socket RAPL Algorithm & Functionality Verification](https://hsdes.intel.com/appstore/article-one/#/22022420798)
- [Socket RAPL KB — socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md)
- [NWP PM MAS — RAPL](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [Intel RAPL HAS — TPMI register definitions](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html)
- [DMR IMH PM HAS §7.3 — NN-PID controller](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html)

---

## NWP Adaptation Notes

| DMR | NWP |
|-----|-----|
| `dmr.xml` | `nwp.xml` |
| 4 CBBs (`range(4)`) | 2 CBBs (`range(2)`) |
| `sv.socket0.imh0.punit.*` | `sv.socket0.nio.punit.*` |
| MSR 0x610 / 0x611 for RAPL control | **Deprecated** — use TPMI only |
| IMH-P root + IMH-S leaf | NIO root (single NIO) |
| PL1 limit must be above idle for both DMR and NWP | Same — avoid setting PL1/PL2 below idle power |

**Disposition: Runnable_On_N-1** — Change `dmr.xml` → `nwp.xml` in the `runPmx.py` command line. The `pl1_limit_convergence` and `pl2_limit_convergence` functions in `pm.pmutils.cpu_rapl` are platform-generic and will use the correct TPMI path for NWP. No script code changes needed beyond the XML config swap.
