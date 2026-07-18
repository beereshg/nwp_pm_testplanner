# TC: Socket RAPL x SST TF

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422015](https://hsdes.intel.com/appstore/article-one/#/22022422015) |
| **Title** | Socket rapl x SST TF |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL × Cross-products |
| **Sub-Feature** | RAPL × SST-TF/PCT — RAPL enforcement with SST frequency partitioning active |
| **Parent TCD** | [22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) |
| **NWP Disposition** | **Runnable_On_N-1** (reduced scope — SST-TF/PCT only; SST-PP/BF/CP/HGS ZBB) |
| **Automation** | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| **Owner** | mps |
| **Val Framework** | PMX, os-svos, python-sv |

---

## Test Case Intent

Validates the **RAPL × SST-TF/PCT** cross-product scenario defined in [TCD 22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) §5 ("RAPL interaction validated only for supported NWP SST / PCT path"). Environment: NWP post-silicon (SVOS).

**Micro-architecture:** On NWP, only **SST-TF (Turbo Frequency)** via **PCT (Priority Core Turbo)** is supported. SST-TF creates HP (High Priority) and LP (Low Priority) core partitions with differentiated TRL ceilings. When Socket RAPL is simultaneously active, the RAPL NN-PID loop computes a frequency ceiling that may be lower than the SST-TF TRL — RAPL should uniformly constrain all cores (HP and LP) without violating the RAPL power budget. This TC validates that RAPL correctly limits total package power even when SST-TF has elevated HP core turbo ratios, and that `perf_limit_reasons` correctly identifies the binding limiter.

**NWP scope reduction:** SST-PP, SST-BF, SST-CP (standalone), and HGS are **ZBB on NWP** — only SST-TF/PCT cross-product is exercised.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon, SVOS |
| Sockets | 1S minimum |
| BIOS knobs | SST-TF enabled; PCT partition count configured (e.g., 2 partitions); RAPL defaults; TPMI unlocked |
| OS / Driver | Ubuntu/SVOS; `intel-speed-select` tool installed; PTU available |
| PythonSV | `pm.pmutils.cpu_rapl` module; SST TPMI register access |
| Feature state | Socket RAPL enabled; SST-TF/PCT active (HP+LP partitions visible) |
| NWP topology | 2 CBBs × 48 cores = 96 total; HP and LP modules per PCT configuration |
| Interface | TPMI for RAPL; SST TPMI for PCT/TF status |
| ZBB excluded | SST-PP, SST-BF, SST-CP, HGS — all ZBB on NWP |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Boot with SST-TF/PCT enabled (BIOS knob) | OS boots; `intel-speed-select perf-profile info` shows active profile with HP/LP modules | SST-TF not active; no HP/LP partitioning |
| 2 | Verify SST topology: `intel-speed-select perf-profile info` | HP modules have elevated TRL ceiling; LP modules have lower clip | Wrong TRL values or no partitioning |
| 3 | Launch PMx: `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` | PMx initialized; RAPL defaults active (PL1=TDP) | PMx error |
| 4 | Start PTU TDP workload across all 96 cores | All cores loaded; HP cores running at elevated TRL; LP cores at clip | PTU fails; SST frequency differentiation not visible |
| 5 | Set RAPL PL1 below current total socket power via TPMI | RAPL begins throttling; PID computes frequency ceiling | TPMI write rejected |
| 6 | Wait for PID convergence (≤ 5 × tau1) | Total socket power converges to PL1 target | Power does not converge |
| 7 | Verify RAPL limits both HP and LP cores | HP cores throttled below their TRL ceiling; LP cores also constrained; total power = PL1 | HP cores bypass RAPL limit; total power exceeds PL1 |
| 8 | Check `perf_limit_reasons` | RAPL PL1 bit[10] asserted; SST does not override RAPL enforcement | Wrong limiter indicated |
| 9 | Verify HP/LP frequency differentiation still maintained under RAPL throttle | HP cores still get relatively higher frequency than LP (proportional throttle) | All cores at same frequency (SST partitioning lost) |
| 10 | Raise RAPL PL1 to TDP (RAPL permissive) | RAPL disengages; HP cores return to full SST-TF TRL; LP at clip | RAPL still throttling; SST TRL not restored |
| 11 | Verify `perf_limit_reasons` PL1 bit clears | PL1 bit cleared; SST operating normally without RAPL constraint | PL1 bit stuck |
| 12 | Stop workload | System idle; no limits active | Limits stuck |

---

### Pass / Fail Criteria

**Bar:** Per [TCD 22022420806](https://hsdes.intel.com/appstore/article-one/#/22022420806) §5: RAPL interaction validated only for supported NWP SST / PCT path.

**PASS** when ALL of the following are true:
- RAPL correctly limits total package power with SST-TF/PCT active
- HP and LP cores are both constrained by RAPL — no HP core bypasses RAPL power limit
- Frequency differentiation (HP > LP) is maintained under RAPL throttle (proportional)
- When RAPL is permissive (PL1 ≥ TDP), SST-TF TRL values fully restored
- `perf_limit_reasons` correctly identifies RAPL as binding limiter
- No MCAs, dmesg errors, or system hangs

**FAIL** when ANY of the following are true:
- RAPL fails to constrain HP cores; total power exceeds PL1 with SST-TF active
- SST frequency partitioning lost during RAPL throttle (all cores same freq)
- SST TRL not restored when RAPL disengages
- `perf_limit_reasons` incorrect
- System hang, MCA, or unexpected reset

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| `TPMI PL1_CONTROL` (idx=2) | `sv.socket0.nio.punit.tpmi.pl1_control.read()` | PWR_LIM matches programmed value |
| `TPMI ENERGY_STATUS` (idx=7) | `sv.socket0.nio.punit.tpmi.energy_status.read()` | Counter incrementing |
| `SST_HEADER.CAPABILITY_MASK` | SST TPMI readout | SST-TF feature active |
| `intel-speed-select perf-profile info` | OS tool | HP/LP modules correctly reported |
| `perf_limit_reasons` | PMx readout | RAPL PL1 bit correct |
| `dmesg` | `dmesg \| grep -i 'mca\|error\|sst\|rapl'` | No unexpected errors |

### Post-Process

N/A — SST topology and RAPL results captured inline by PMx and `intel-speed-select`.

### References

- [TCD 22022420806 — Socket RAPL Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806)
- [Socket RAPL KB — socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md)
- [SST KB — sst_main.md](../../pm_features/sst/sst_main.md)
- [Intel SST HAS — RAPL × SST interaction](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html)

---

## NWP Adaptation Notes

| DMR | NWP |
|-----|-----|
| `dmr.xml` | `nwp.xml` |
| Full SST stack (PP/BF/CP/TF/HGS) | **SST-TF/PCT only** — PP/BF/CP/HGS are ZBB |
| 4 CBBs | 2 CBBs |
| `sv.socket0.imh0.punit.*` | `sv.socket0.nio.punit.*` |

**Disposition: Runnable_On_N-1 (reduced scope)** — Only SST-TF/PCT cross-product is exercisable on NWP. Change XML config. SST-PP/BF/CP/HGS cross-product scenarios are not applicable.
