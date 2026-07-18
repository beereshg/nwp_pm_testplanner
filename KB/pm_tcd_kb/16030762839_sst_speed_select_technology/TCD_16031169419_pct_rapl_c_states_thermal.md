# TCD 16031169419 — PCT × RAPL × C-states × thermal

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169419](https://hsdes.intel.com/appstore/article-one/#/16031169419) |
| **Title** | PCT × RAPL × C-states × thermal |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 — NWP PM PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Child TCs** | *(none yet — TC TBD)* |
| **Feature** | Power / SST — PCT cross-product: simultaneous RAPL PL1, C-state transitions, and thermal throttling interactions |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**PCT × RAPL × C-states × thermal** validates that PCT ordered throttling, CLOS-based frequency hierarchy, and HP/LP core assignment remain coherent under simultaneous RAPL power limiting, C-state entry/exit, and thermal throttling events. This is the cross-product stress TCD — individual feature paths are tested by sibling TCDs.

> **Architecture overview:** See [TPF 16030762939 — NWP PM PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) §2 Design Details for PCT architecture and CLOS mechanism.

### TC Coverage Map

| TC | Title | Scope |
|----|-------|-------|
| *(TC TBD)* | — | Full cross-product: PL1 stress + C-state cycling + thermal trip |

### NWP-Specific Deltas

- **2 CBBs**: ordered throttling distributes across 2 CBBs × 48 cores (not 4 × 32 as DMR)
- **RAPL PL1 via TPMI only**: MSR 0x610/0x638 deprecated on NWP — TPMI `SOCKET_RAPL_PL1_CONTROL` is the enforcement path
- **No SST-PP switching**: PCT operates on the single boot PP level (SST-PP ZBB'd on NWP) — eliminates PP × PCT × thermal interaction

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Direction | Role in Cross-Product |
|-----------|----------------|-----------|----------------------|
| TPMI | `SST_CP_CONTROL.SST_CP_PRIORITY_TYPE` | RW | = 1 (Ordered Throttling): LP cores throttled first under RAPL |
| TPMI | `SST_CP_STATUS.EXCURSION_TO_MIN` bits 11:8 | RO | Per-CLOS bitmask — set when RAPL forces CLOS group to minimum |
| TPMI | `SOCKET_RAPL_PL1_CONTROL.PWR_LIM` | RW | Socket PL1 power limit — reduced to trigger ordered throttle |
| MSR | `IA32_HWP_CAPABILITIES (0x771)` per core | RO | HP cores: highest_perf = P0max; LP cores: highest_perf = LP clip |
| MSR | `IA32_MPERF/APERF` per core | RO | Effective frequency measurement under throttle |
| DTS | `IA32_THERM_STATUS` per core | RO | Thermal status — PROCHOT, EMTTM active bits |
| sysfs | `/sys/bus/cpu/devices/cpuN/cpufreq/scaling_cur_freq` | RO | OS-visible effective frequency per core |
| sysfs | `/sys/devices/system/cpu/cpuN/cpuidle/stateN/usage` | RO | C-state residency counters |

---

## Section 3: Reset, Power, and Clocking

- **CLOS assignment is static**: HP/LP topology does NOT change when cores enter/exit C6. A core in C6 retains its CLOS[0] (HP) or CLOS[3] (LP) assignment.
- **RAPL PID loop**: 1 ms period. Ordered throttling distributes power budget per CLOS priority at each loop iteration.
- **Thermal response**: PROCHOT must reduce power within ~22 μs — overrides RAPL/PCT entirely. EMTTM is slower and acts as `min(PCT_limit, thermal_limit)`.
- **C-state wake**: core resumes at its CLOS-assigned frequency limit, not at a default. RAPL PID catches up within 1 ms.

---

## Section 4: Programming Model

This TCD validates the **interaction invariants**, not individual features.

### Invariant 1: Ordered Throttle Under PL1

When `SST_CP_PRIORITY_TYPE = 1` and RAPL PL1 < TDP:
1. LP CLOS[3] cores throttled first (frequency drops toward Pn)
2. HP CLOS[0] cores maintained at PCT TRL until LP at minimum
3. Only after LP at minimum, HP frequency reduced
4. `EXCURSION_TO_MIN[3]` set when LP hits floor; `EXCURSION_TO_MIN[0]` only if HP also hits floor

### Invariant 2: C-State Topology Stability

When HP cores enter C6 during mixed workload:
- CLOS assignment unchanged — HP core still HP when it wakes
- LP cores remain clipped at LP_CLIP ratio (not promoted)
- `intel-speed-select perf-profile info` topology unchanged
- No TRL toggling on C-state transitions

### Invariant 3: Thermal Override

When PROCHOT fires during PCT + RAPL stress:
- All cores clamped to PROCHOT response frequency regardless of CLOS
- PCT frequency hierarchy effectively overridden
- After PROCHOT de-assert: RAPL/PCT hierarchy resumes; brief deration period expected
- EMTTM (non-PROCHOT thermal): effective freq = `min(RAPL/PCT ordered limit, EMTTM limit)` per core

---

## Section 5: Operational Behavior

### Pass / Fail Bar

| Criterion | Threshold | Measurement |
|-----------|-----------|-------------|
| Ordered throttle LP-first | Under PL1 = 70% TDP + all-core stress: LP `scaling_cur_freq` < HP `scaling_cur_freq` for ≥ 90% of samples over 10 s | Per-core sysfs polling at 100 ms |
| HP frequency maintained | HP cores `APERF/MPERF` effective freq ≥ LP_CLIP ratio while LP at minimum | MSR read per core |
| EXCURSION_TO_MIN LP | `SST_CP_STATUS[11:8]` bit 3 = 1 (LP CLOS hit floor) under PL1 stress | TPMI register read |
| C-state topology stable | After 1000 C6 entry/exit cycles on HP cores: `intel-speed-select perf-profile info` HP module count unchanged | CLI output diff pre/post |
| CLOS assignment stable | HP core wakes from C6 and resumes at HP frequency (not LP clip) | `scaling_cur_freq` within 10 ms of wake ≥ LP_CLIP + 100 MHz |
| PROCHOT override | During PROCHOT assert: all cores `scaling_cur_freq` ≤ PROCHOT response ratio | sysfs read during thermal injection |
| PROCHOT recovery | Within 100 ms of PROCHOT de-assert: HP `scaling_cur_freq` > LP `scaling_cur_freq` | sysfs polling |
| No dmesg errors | Zero SST/PCT/thermal MCE or warning messages | `dmesg` scan |

### Scenario × Expected Outcome

| Scenario | Expected | TC |
|----------|----------|----| 
| PL1 = 70% TDP + all-core stress | LP throttled first; HP maintained; EXCURSION_TO_MIN[3] set | *(TC TBD)* |
| HP cores cycling C6 under PL1 stress | CLOS unchanged; HP resumes at HP frequency on wake | *(TC TBD)* |
| PROCHOT during PCT + PL1 | All cores clamped; hierarchy resumes after de-assert | *(TC TBD)* |
| EMTTM during ordered throttle | Effective freq = min(ordered limit, EMTTM limit) per core | *(TC TBD)* |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **All HP in C6 + PL1 stress** | All HP cores sleeping while LP under throttle — verify LP stays clipped (not promoted to HP freq) | ❌ Not covered | New TC needed |
| **Rapid C6 entry/exit during PROCHOT** | HP core oscillates C0↔C6 while PROCHOT active — verify no frequency spike above PROCHOT limit on wake | ❌ Not covered | Add as step to thermal TC |
| **PL1 ramp during C-state transition** | PL1 reduced while HP core is mid-C6-exit — verify RAPL catches up within 1 ms, no overshoot | ❌ Not covered | New TC needed |
| **Simultaneous PROCHOT + PL1 release** | PROCHOT de-asserts at same time PL1 restored to TDP — verify orderly frequency recovery | ❌ Not covered | New TC needed |
| **EMTTM on HP only** | Thermal event localized to HP die (CBB0) — verify HP throttled by EMTTM while LP on CBB1 unaffected | ❌ Not covered | New TC needed |

---

## Section 7: Security / Safety / Policy

- Cross-product stress test — all registers read-only from OS except PL1 control (requires root/CAP_SYS_ADMIN)
- PROCHOT injection requires hardware thermal injection capability or PythonSV DTS override

---

## Section 8: References

- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_CONTROL.SST_CP_PRIORITY_TYPE, ordered throttling
- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — CLOS assignment, frequency hierarchy
- [NWP PM MAS — PCT](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- Co-Design spec query (2026-07-18) — PCT × RAPL × C-state × thermal interaction invariants
- [PCT - Error Injection / Recovery TCD 16031169310](https://hsdes.intel.com/appstore/article-one/#/16031169310) — sibling for error status paths
- KB: KB/pm_features/sst/pct.md
