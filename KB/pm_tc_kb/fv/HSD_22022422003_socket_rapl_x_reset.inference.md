# TC: Socket RAPL x Reset

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422003](https://hsdes.intel.com/appstore/article-one/#/22022422003) |
| **Title** | Socket Rapl x Reset |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL × Cross-products |
| **Sub-Feature** | RAPL PID re-initialization and state correctness across cold/warm reset |
| **Parent TCD** | [22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Automation** | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| **Owner** | mps |
| **Val Framework** | PMX, os-svos |

---

## Test Case Intent

Validates the **RAPL × Reset** cross-product scenario defined in [TCD 22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) §5 ("Socket RAPL correctly reinitialized after warm reset; no stale limit persists"). Environment: NWP post-silicon (SVOS).

**Micro-architecture:** PrimeCode reinitializes Socket RAPL NN-PID controllers during **PH6 (Runtime init)** after reset. On cold reset, ENERGY_STATUS resets to 0 and RAPL defaults restore (PL1=TDP, PL2=1.2×TDP). On warm reset, ENERGY_STATUS is **not reset** (software must handle rollover), but PrimeCode re-arms the PID controllers. This TC validates that no stale RAPL limit or PID state persists across reset, and that enforcement resumes correctly.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon, SVOS |
| Sockets | 1S minimum |
| BIOS knobs | Default RAPL configuration; PL1 = TDP; TPMI unlocked |
| OS / Driver | Ubuntu/SVOS; PTU available |
| PythonSV | `pm.pmutils.cpu_rapl` module; `runPmx.py`; `flexconPM.py` accessible |
| Feature state | Socket RAPL enabled; ability to trigger warm/cold reset |
| NWP topology | 2 CBBs × 48 cores; NIO root die |
| Interface | **TPMI only** — legacy MSRs deprecated on NWP |
| Reset method | Cold reset (power cycle or ACPI S5→S0) and warm reset (ACPI reboot or platform warm reset) |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Boot system; launch PMx: `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` | PMx loaded; RAPL defaults active (PL1=TDP, PL2=1.2×TDP) | PMx error |
| 2 | Start PTU TDP workload; set PL1 below TDP via TPMI | RAPL actively throttling; `perf_limit_reasons` PL1 bit asserted | TPMI write rejected |
| 3 | Record pre-reset RAPL state: `TPMI PL1_CONTROL`, `ENERGY_STATUS`, `PERF_STATUS` | Values recorded for post-reset comparison | Register read failure |
| 4 | Trigger **cold reset** (power cycle) | System cold boots; OS comes up | Reset hangs; system does not boot |
| 5 | After cold reset: read `TPMI PL1_CONTROL` | PL1 restored to default (TDP); custom PL1 from step 2 not persisted | Stale custom PL1 value persists |
| 6 | After cold reset: read `TPMI ENERGY_STATUS` | Counter reset to 0 (cold reset clears energy counter) | Energy counter non-zero after cold reset |
| 7 | After cold reset: run PMx RAPL test | RAPL enforcement works correctly; PID converges normally | RAPL not functional; PID stuck |
| 8 | Set PL1 below TDP again; verify RAPL active | RAPL actively throttling post-cold-reset | RAPL not enforcing |
| 9 | Trigger **warm reset** (ACPI reboot) | System warm boots; OS comes up | Reset hangs |
| 10 | After warm reset: read `TPMI ENERGY_STATUS` | Counter **not reset** (warm reset does not clear energy counter); value ≥ pre-reset value | Energy counter unexpectedly reset to 0 |
| 11 | After warm reset: read `TPMI PL1_CONTROL` | PL1 at default (TDP); custom PL1 not persisted across warm reset | Stale custom PL1 persists |
| 12 | After warm reset: run PMx RAPL test | RAPL enforcement works; PID re-initialized during PH6 | RAPL not functional; stale PID state |
| 13 | Run FlexCon register verification: `flexconPM.py -c NWPSV.ini` | All RAPL registers at expected post-reset values | Register mismatch |

---

### Pass / Fail Criteria

**Bar:** Per [TCD 22022420806](https://hsdes.intel.com/appstore/article-one/#/22022420806) §5: Socket RAPL correctly reinitialized after warm reset; no stale limit persists.

**PASS** when ALL of the following are true:
- Cold reset: RAPL defaults restored (PL1=TDP); ENERGY_STATUS = 0; PID converges normally
- Warm reset: ENERGY_STATUS **not** cleared; RAPL defaults restored; PID re-initialized during PH6
- No stale custom PL1/PL2 limits persist across either reset type
- RAPL enforcement functional after both cold and warm reset
- FlexCon register verification passes
- No MCAs, dmesg errors, or system hangs

**FAIL** when ANY of the following are true:
- Stale RAPL limit persists after reset
- ENERGY_STATUS incorrectly reset on warm reset (or not reset on cold)
- RAPL PID does not re-initialize; enforcement broken post-reset
- FlexCon register mismatch
- System hang or MCA during/after reset

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| `TPMI PL1_CONTROL` (idx=2) | `sv.socket0.nio.punit.tpmi.pl1_control.read()` | Default after reset; no stale custom value |
| `TPMI ENERGY_STATUS` (idx=7) | `sv.socket0.nio.punit.tpmi.energy_status.read()` | = 0 after cold reset; ≥ pre-reset after warm reset |
| `TPMI PERF_STATUS` (idx=8) | `sv.socket0.nio.punit.tpmi.perf_status.read()` | Reset behavior per spec |
| `TPMI PL_INFO` (idx=9) | `sv.socket0.nio.punit.tpmi.pl_info.read()` | MAX_PL1 = TDP; MAX_PL2 = 1.2×TDP |
| `dmesg` | `dmesg \| grep -i 'mca\|error\|rapl'` | No unexpected errors |
| FlexCon | `flexconPM.py -c NWPSV.ini` | All checks pass |

### Post-Process

N/A — FlexCon provides register verification; RAPL results captured by PMx.

### References

- [TCD 22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806)
- [Socket RAPL KB — socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md)
- [NWP PM MAS — RAPL PH6 init, reset interaction](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html)
- Related DMR reset TCs: 14020745287 (Cold Reset + RAPL), 14020745288 (Warm Reset + RAPL)

---

## NWP Adaptation Notes

| DMR | NWP |
|-----|-----|
| `dmr.xml` | `nwp.xml` |
| `DMRSV.ini` | `NWPSV.ini` |
| 4 CBBs | 2 CBBs |
| `sv.socket0.imh0.punit.*` | `sv.socket0.nio.punit.*` |
| MSR 0x610 for RAPL | **Deprecated** — TPMI only |

**Disposition: Runnable_On_N-1** — Change XML config and FlexCon INI. Reset paths and PH6 RAPL init are identical.
