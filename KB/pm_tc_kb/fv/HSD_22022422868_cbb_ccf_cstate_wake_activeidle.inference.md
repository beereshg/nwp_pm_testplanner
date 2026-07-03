# Deep Analysis: CBB CCF PM Cstate Wake Events Across Active Idle

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422868](https://hsdes.intel.com/appstore/article-one/#/22022422868) |
| **Title** | CBB CCF PM Cstate wake events across Activeidle |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CBB CCF -- Active Idle wake event handling |
| **Parent TCD** | [22022421179](https://hsdes.intel.com/appstore/article-one/#/22022421179) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Validate that the CBB CCF ring correctly handles wake events that arrive during **Active Idle** — the transient window where all cores have issued a MWAIT C-state hint but the Q-channel deassert sequence (CFC_CLK / CFC_PWR / INF qactive) has not yet completed. Wake events must abort Active Idle cleanly: Q-channels re-assert, core power-up resumes, PICLET replays queued interrupts, and the CCF ring restores to its pre-idle frequency without spurious PLR or stuck state.

**Active Idle definition:** All cores have deasserted `core_active` and the PMA is transitioning Q-channels toward zero. A wake event (timer, interrupt, or PEGA injection) during this window triggers immediate abort — the CCF ring never fully powers down and must recover within the normal wake latency.

**NWP scope:** MC6 is the deepest idle state on NWP (PkgC6 fused off). Active Idle / wake event behavior in MC6 context is the primary validation target on silicon. PkgC6 cross-product scenarios are not applicable on NWP customer parts.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| Platform booted to XOS/SVOS | BIOS CPL4 complete; PCode running | System not booted |
| BIOS: C-states enabled | CC6 reachable; MonitorMWait enabled | Cores cannot enter MC6 -- no Active Idle possible |
| CPU governor: powersave | Allows CC6 entry under zero load | Governor holds cores in C0 |
| No sustained workload | All test cores at idle baseline before injection | Active IP prevents Q-channel deassert |
| CC6/MC6 residency MSRs accessible | `msr(0x3FD)`, `msr(0x664)` readable | MSR access fails -- pre-silicon model gap |
| CBB GPSB accessible | `sv.socket0.cbb0.compute0.pma0.gpsb` readable | GPSB path not valid |
| PEGA/pmutil available | `pega_mailbox.pega_pstate()` importable | Interrupt injection not available |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Baseline: read CC6 residency (`MSR 0x3FD`), MC6 residency (`MSR 0x664`), and `UFS_STATUS.CURRENT_RATIO` on cbb0 module0 | Non-zero residency counters; baseline CCF ratio recorded | MSR unreadable or ratio = 0 |
| 2 | **Phase 1 — Clean Active Idle:** idle all cores in module0 via MWAIT `EAX=0x23`; wait 10ms for Q-channels to deassert fully | MC6 residency increments; Q-channels deassert; Fast Ring C3 engages | MC6 counter stale -- cores not reaching MC6 |
| 3 | Verify Active Idle state: read `GPSB.HWP_REQUEST_RESOLVED` and CCF clock gate status | GPSB shows low-power resolved state; Uclk tree gated | No state change -- Active Idle not engaged |
| 4 | **Phase 2 — Timer wake during Active Idle:** re-idle all cores; inject ARAT timer interrupt mid-transition (before Q-channel deassert completes) | Timer fires during Active Idle window; Q-channels immediately re-assert; no stuck state | Q-channels stuck deasserted -- abort failed |
| 5 | Verify post-timer-wake CCF state: `UFS_STATUS.CURRENT_RATIO` and `GPSB.HWP_REQUEST_RESOLVED` | CCF ratio restores to pre-idle baseline value; GPSB reflects active state | CCF stuck at low ratio -- wake did not restore freq |
| 6 | **Phase 3 — External interrupt wake:** re-idle cores; inject external interrupt via PEGA mailbox during Q-channel transition | Interrupt delivery aborts Active Idle; PICLET queues and replays interrupt; no ordering errors | PICLET drops interrupt -- wake event lost |
| 7 | Verify PICLET interrupt replay: read interrupt delivery counter or use PEGA inject-and-check API | Interrupt received by correct core; no duplicate or missed delivery | Interrupt not received -- PICLET replay broken |
| 8 | **Phase 4 — Repeat on cbb1 and module1:** run phases 1-3 on cbb1 and on module1 of cbb0 | Same behavior; per-module and per-CBB independence confirmed | One module/CBB asymmetry -- PMA state stuck |
| 9 | Verify residency counters after full test: CC6 and MC6 both advanced from baseline | Residency reflects all idle cycles across phases; no rollback | Counters unchanged -- HW not accounting C-state residency |
| 10 | Verify `PLR_DIE_LEVEL = 0x0` on both CBBs throughout all phases | No spurious Performance Limit Reason from Active Idle transitions | PLR non-zero -- unexpected throttle from CCF state transitions |

### Pass / Fail Criteria

**PASS:** All phases complete without hang; MC6 residency increments; Q-channels re-assert on wake; CCF ratio restores to pre-idle value; PICLET delivers interrupts correctly; no duplicate/missed events; PLR = 0x0; per-module and per-CBB independence confirmed.

**FAIL:** Stuck Q-channel (never re-asserts); wrong or stale residency counter; CCF frequency does not restore; PICLET drops or duplicates interrupt; PLR non-zero; system hang during any phase.

### Post-Process

Save: CC6/MC6 counters (baseline, mid-test, post-test), GPSB state at each phase, UFS_STATUS.CURRENT_RATIO pre/during/post Active Idle, PLR_DIE_LEVEL for both CBBs, PICLET delivery confirmation log.

### Reference Documents

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html) -- Active Idle Q-channel deassert sequence, wake abort flow
- [CBB CCP PM Integration HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCP%20HAS/cbb_cpp_has.html) -- PICLET interrupt replay, CFC Q-channel logic
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details) -- GPSB HWP_REQUEST_RESOLVED, CBB power telemetry
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- [PEGA Architecture](https://wiki.ith.intel.com/display/ServerPcode/PEGA) -- PEGA mailbox interrupt injection API
- [DMR SoC HAS](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/DMR_Overview_HAS.html#figure-hub-and-spoke) -- Hub-and-spoke topology, D2D context

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable on NWP silicon (Active Idle / MC6 context)**

MC6 is the deepest idle state on NWP (PkgC6 fused off). Active Idle and wake event handling in the MC6 context is fully testable on NWP silicon. PkgC6 scenarios are limited to HSLE/Simics.

NWP topology: 2 CBBs × 2 computes × 6 modules × 8 cores = 96 cores per CBB. Each module (8 cores) independently enters MC6 and can trigger Active Idle.

Tags: `CBB CCF`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### Key Register Paths (NWP)

| Register | NWP Path | Purpose |
|----------|----------|---------|
| CC6 Residency | `pd.debug.access_to_msr(0x3FD, core=core)` | Per-core C6 residency |
| MC6 Residency | `pd.debug.access_to_msr(0x664, core=core)` | Per-module C6 residency |
| GPSB HWP_REQUEST_RESOLVED | `sv.socket0.cbbN.compute0.pma0.gpsb.hwp_request_resolved` | PMA resolved request |
| UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status` | CURRENT_RATIO [6:0] |
| PLR_DIE_LEVEL | `sv.socket0.cbbN.base.tpmi.plr_die_level` | Perf Limit Reason |
| ACP_PERF_LIMIT | `sv.socket0.cbbN.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit` | ACP power limit |

### Idle Induction (Simics)

```python
# Idle all 8 cores in module0 of cbb0 via MWAIT C6S hint
for core in sv.socket0.cbb0.compute0.module0.cores:
    core.thread0.write_reg("rax", 0x23)  # C6S MWAIT hint
    core.thread0.write_reg("rcx", 0x0)
cli.run_command("emu.engine.wait-for-cycle -relative 5000000")
# Verify Q-channels deasserted -> Active Idle engaged
```

### Interrupt Injection (PEGA)

```python
from diamondrapids.pm.pss.mailbox import pega_mailbox
# Inject synthetic interrupt during Active Idle window
pega_mailbox.pega_pstate(iagv=0, meshgv=0, memgv=0, iogv=0, rearm=1)
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Baseline snapshot | Read MSR 0x3FD, 0x664, UFS_STATUS on both CBBs |
| 2 | Idle module0 | MWAIT EAX=0x23 × 8 cores; wait 5M cycles |
| 3 | Check Q-channel state | `sv.socket0.cbb0.compute0.pma0.gpsb.hwp_request_resolved.read()` |
| 4 | Wake injection | PEGA or timer interrupt mid-transition |
| 5 | Verify recovery | UFS_STATUS.CURRENT_RATIO = baseline; PLR = 0x0 |

### Pass Criteria

MC6 increments; Active Idle engaged; wake aborts cleanly; CCF ratio restores; PICLET delivers correctly; PLR = 0x0.
