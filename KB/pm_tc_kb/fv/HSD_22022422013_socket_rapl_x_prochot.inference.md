# TC: Socket RAPL x PROCHOT

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422013](https://hsdes.intel.com/appstore/article-one/#/22022422013) |
| **Title** | Socket rapl x Prochot |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL × Cross-products |
| **Sub-Feature** | RAPL × PROCHOT simultaneous throttle arbitration |
| **Parent TCD** | [22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Automation** | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| **Owner** | mps |
| **Val Framework** | PMX, os-svos |

---

## Test Case Intent

Validates the **RAPL × PROCHOT** cross-product scenario defined in [TCD 22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) §5 ("thermal / external throttling coexists with Socket RAPL without invalid state"). Environment: NWP post-silicon (SVOS).

**Micro-architecture:** PROCHOT# is an external platform thermal throttle signal (or injected via PythonSV). When asserted, PCode immediately throttles cores to Pm (minimum operating frequency). RAPL operates independently — the NN-PID loop continues computing frequency ceilings based on power telemetry. When both are active, PROCHOT dominates frequency (Pm), while RAPL continues power budget enforcement. After PROCHOT de-asserts, only RAPL remains active. This TC validates that the two throttle mechanisms coexist correctly and that `perf_limit_reasons` reports both reasons simultaneously.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon, SVOS |
| Sockets | 1S minimum |
| BIOS knobs | Default RAPL configuration; PROCHOT enabled (default) |
| OS / Driver | Ubuntu/SVOS; PTU available |
| PythonSV | `pm.pmutils.cpu_rapl` module; PROCHOT injection via namednodes |
| Feature state | Socket RAPL enabled; PROCHOT mechanism enabled |
| NWP topology | 2 CBBs; NIO root die |
| Interface | TPMI for RAPL; PythonSV for PROCHOT inject |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Launch PMx: `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` | PMx initialized; RAPL defaults active | PMx error |
| 2 | Start PTU TDP workload: `./ptu -ct 3` | All 96 cores loaded; socket power > idle | PTU fails |
| 3 | Set RAPL PL1 below TDP via TPMI to create active RAPL throttle | RAPL actively throttling; PL1 bit asserted in `perf_limit_reasons` | RAPL not engaging |
| 4 | Verify RAPL-only throttle: read `perf_limit_reasons` | PL1 bit[10] asserted; PROCHOT bit NOT asserted | Wrong bits asserted |
| 5 | Record RAPL-limited core frequency | Frequency at RAPL-dictated ceiling (above Pm) | Frequency unexpected |
| 6 | Inject PROCHOT via PythonSV: `sv.socket0.nio.punit.prochot_trigger.write(1)` | PROCHOT asserted; cores throttle to Pm immediately | PROCHOT inject fails |
| 7 | Check `perf_limit_reasons` with both active | Both PROCHOT bit AND PL1 bit[10] asserted simultaneously | Only one limiter reported |
| 8 | Verify core frequency = Pm (PROCHOT dominates frequency) | Frequency at Pm (below RAPL output); PROCHOT overrides | Frequency above Pm; PROCHOT not effective |
| 9 | Verify RAPL PID still active (not stalled) | RAPL PID loop continues running; `ENERGY_STATUS` incrementing; RAPL computing output | RAPL PID stalled during PROCHOT |
| 10 | Release PROCHOT: `sv.socket0.nio.punit.prochot_trigger.write(0)` | PROCHOT de-asserted; cores restore frequency | PROCHOT stuck asserted |
| 11 | Verify RAPL resumes as sole limiter | Frequency returns to RAPL-dictated ceiling (above Pm); `perf_limit_reasons` shows PL1 only, PROCHOT cleared | Frequency stuck at Pm; RAPL not resuming |
| 12 | Stop workload; verify idle | Power drops; no limits active; `perf_limit_reasons` cleared | Limits stuck |

---

### Pass / Fail Criteria

**Bar:** Per [TCD 22022420806](https://hsdes.intel.com/appstore/article-one/#/22022420806) §5: thermal / external throttling coexists with Socket RAPL without invalid state.

**PASS** when ALL of the following are true:
- PROCHOT + RAPL simultaneously active: `perf_limit_reasons` reports both reasons
- PROCHOT dominates frequency to Pm while RAPL continues power enforcement
- After PROCHOT release: RAPL resumes as sole limiter; frequency restores to RAPL ceiling
- RAPL PID does not stall during PROCHOT assertion
- No MCAs, dmesg errors, or system hangs

**FAIL** when ANY of the following are true:
- `perf_limit_reasons` does not report both limiters simultaneously
- Frequency does not drop to Pm during PROCHOT
- RAPL stalls or becomes non-functional during/after PROCHOT
- After PROCHOT release, frequency stuck at Pm or RAPL not resuming
- System hang, MCA, or unexpected reset

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| `TPMI ENERGY_STATUS` (idx=7) | `sv.socket0.nio.punit.tpmi.energy_status.read()` | Counter incrementing during PROCHOT (RAPL PID not stalled) |
| `TPMI PL1_CONTROL` (idx=2) | `sv.socket0.nio.punit.tpmi.pl1_control.read()` | PWR_LIM unchanged during PROCHOT |
| `perf_limit_reasons` | PMx readout | Both PROCHOT and PL1 bits correct |
| `MSR 0x19C` (IA32_THERM_STATUS) | `sv.socket0.cbb0.compute0.module0.core0.threads[0].ia32_therm_status.read()` | PROCHOT_STATUS bit asserted during inject |
| `dmesg` | `dmesg \| grep -i 'mca\|error\|prochot\|rapl'` | No unexpected errors |

### Post-Process

N/A — throttle state captured inline by PMx and register reads.

### References

- [TCD 22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806)
- [Socket RAPL KB — socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md)
- [NWP PM MAS — RAPL, Prochot](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [Intel RAPL HAS — PROCHOT interaction](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html)

---

## NWP Adaptation Notes

| DMR | NWP |
|-----|-----|
| `dmr.xml` | `nwp.xml` |
| `sv.socket0.imh0.punit.prochot_trigger` | `sv.socket0.nio.punit.prochot_trigger` |
| 4 CBBs | 2 CBBs |
| MSR 0x610 for RAPL | **Deprecated** — TPMI only |

**Disposition: Runnable_On_N-1** — Change XML config and PROCHOT inject register path. PROCHOT × RAPL arbitration logic is identical.
