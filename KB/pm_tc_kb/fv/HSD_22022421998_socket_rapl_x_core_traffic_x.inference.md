# TC: Socket RAPL x Core Traffic x IO Traffic

| Field | Value |
|-------|-------|
| **HSD ID** | [22022421998](https://hsdes.intel.com/appstore/article-one/#/22022421998) |
| **Title** | Socket Rapl x Core Traffic x IO Traffic |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL × Cross-products |
| **Sub-Feature** | RAPL enforcement under simultaneous CPU compute + IO traffic |
| **Parent TCD** | [22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Automation** | `python runPmx.py -x nwp.xml -p cpu_rapl -p cpu_traffic -p core_power -tM 6 -M 3` |
| **Owner** | mps |
| **Val Framework** | PMX, os-svos |

---

## Test Case Intent

Validates the **RAPL × Core + IO Traffic** cross-product scenario defined in [TCD 22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) §5 ("Socket RAPL remains correctly enforced under mixed activity"). Environment: NWP post-silicon (SVOS).

**Micro-architecture:** When CPU compute cores and IO devices generate simultaneous power draw, Socket RAPL must correctly account for total socket power (both core and uncore/IO contributions) and enforce PL1/PL2 limits through the NN-PID loop. The IMON telemetry aggregates all power domains; the PID output (`RAPL_PERF_LIMIT` via HPM 0x14) throttles CBB cores while IO traffic continues. This TC validates that RAPL enforcement is accurate and energy accounting is correct under mixed traffic patterns.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon, SVOS |
| Sockets | 1S minimum |
| BIOS knobs | Default RAPL configuration; PL1 = TDP (fused); TPMI unlocked |
| OS / Driver | Ubuntu/SVOS; PTU available; IO traffic generator available |
| PythonSV | `pm.pmutils.cpu_rapl` module available; `runPmx.py` accessible |
| Feature state | Socket RAPL enabled; no RAPL lock |
| NWP topology | 2 CBBs × 48 cores = 96 total; NIO root die; single NIO aggregates all power |
| Interface | **TPMI only** — legacy MSRs 0x610/0x611 deprecated on NWP |
| Traffic | CPU compute workload (PTU TDP) + IO traffic generator (DMA, PCIe, or equivalent) |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Launch PMx RAPL + traffic automation: `python runPmx.py -x nwp.xml -p cpu_rapl -p cpu_traffic -p core_power -tM 6 -M 3` | PMx initializes; plugins loaded; NWP topology detected (2 CBBs) | PMx startup error; plugin load failure |
| 2 | Start PTU TDP workload on all 96 cores: `./ptu -ct 3` | All cores loaded; CPU power contribution significant | PTU fails to start; insufficient load |
| 3 | Start IO traffic generator (DMA/PCIe workload) | IO traffic active; IO power contribution visible in IMON telemetry | IO generator fails; no IO power contribution |
| 4 | Read baseline socket power with both traffic active: `TPMI ENERGY_STATUS` | Total socket power = CPU power + IO power; exceeds idle significantly | Energy counter stale or not incrementing |
| 5 | Set RAPL PL1 below current total socket power via TPMI | PL1 accepted; PrimeCode begins throttling CPU cores | TPMI write rejected; PL1 not applied |
| 6 | Wait for PID convergence (≤ 5 × tau1) | Total socket power converges to PL1 target | Power does not converge; diverges or oscillates |
| 7 | Verify energy accounting accuracy under mixed traffic | `TPMI ENERGY_STATUS` reflects correct total socket power (CPU + IO) | Energy counter shows only CPU or only IO power |
| 8 | Check `perf_limit_reasons` for PL1 throttle indication | Bit[10] (PKG_PL1_INBAND) asserted while PL1 actively limiting | PL1 bit not asserted during active throttle |
| 9 | Stop IO traffic; CPU-only workload continues | Socket power drops (IO contribution removed); RAPL re-converges if PL1 still binding | Power does not adjust after IO traffic stops |
| 10 | Restart IO traffic with CPU still running | Socket power increases again; RAPL re-engages if total > PL1 | RAPL fails to re-engage; energy accounting incorrect |
| 11 | Stop all traffic; verify return to idle | Socket power drops below PL1; `perf_limit_reasons` PL1 bit clears | Power elevated; perf_limit_reasons stuck |

---

### Pass / Fail Criteria

**Bar:** Per [TCD 22022420806](https://hsdes.intel.com/appstore/article-one/#/22022420806) §5: Socket RAPL remains correctly enforced under mixed CPU + IO activity.

**PASS** when ALL of the following are true:
- Total socket power converges to PL1 within 5 × tau1 under combined CPU + IO traffic
- Energy accounting (TPMI ENERGY_STATUS) correctly reflects total socket power
- `perf_limit_reasons` bit[10] asserts during PL1 throttle and clears when power drops below limit
- RAPL dynamically adjusts when IO traffic starts/stops while CPU workload continues
- No dmesg errors, MCAs, or system hangs during test

**FAIL** when ANY of the following are true:
- Power does not converge to PL1 under mixed traffic
- Energy accounting excludes IO power contribution
- `perf_limit_reasons` incorrect
- System hang, MCA, or unexpected reset

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| `TPMI ENERGY_STATUS` (idx=7) | `sv.socket0.nio.punit.tpmi.energy_status.read()` | Counter incrementing; reflects total socket power |
| `TPMI PERF_STATUS` (idx=8) | `sv.socket0.nio.punit.tpmi.perf_status.read()` | Throttle counter > 0 during PL1 limit |
| `TPMI PL1_CONTROL` (idx=2) | `sv.socket0.nio.punit.tpmi.pl1_control.read()` | PWR_LIM matches programmed value |
| `perf_limit_reasons` | PMx readout | Bit[10] correct during throttle |
| `dmesg` | `dmesg \| grep -i 'mca\|error\|rapl'` | No unexpected errors |

### Post-Process

N/A — energy and convergence results captured inline by PMx plugins.

### References

- [TCD 22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806)
- [Socket RAPL KB — socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md)
- [NWP PM MAS — RAPL](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html)

---

## NWP Adaptation Notes

| DMR | NWP |
|-----|-----|
| `dmr.xml` / `spr.xml` | `nwp.xml` |
| 4 CBBs | 2 CBBs |
| MSR 0x610 for RAPL control | **Deprecated** — use TPMI only |
| `sv.socket0.imh0.punit.*` | `sv.socket0.nio.punit.*` |

**Disposition: Runnable_On_N-1** — Change XML config to `nwp.xml`. IO traffic generator must be NWP-compatible.
