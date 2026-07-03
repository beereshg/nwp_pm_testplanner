# Deep Analysis: CBB CCF Fast Ring C3

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422865](https://hsdes.intel.com/appstore/article-one/#/22022422865) |
| **Title** | CBB CCF Fast Ring C3 |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CBB CCF -- Fast Ring C3 (PkgC0 idle power state) |
| **Parent TCD** | [22022421179](https://hsdes.intel.com/appstore/article-one/#/22022421179) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Validate CBB CCF Fast Ring C3, an autonomous low-power state entered when all cores in a DCM module reach MC6 (Module C6). Fast Ring C3 closes the Global Uclk tree drivers (clock gating), retaining VCCRING and the Ring PLL for fast wake latency. It fires in **PkgC0 context** with no PUNIT handshake, driven solely by the CBB PMA Q-channel logic.

**NWP scope:** Fast Ring C3 is **fully supported** on NWP silicon. Ring C3 (the deeper CCF power-down requiring PkgC6) is **ZBB'd** on NWP customer silicon (PkgC6 fused off) and is tested only on HSLE/Simics.

**Fast Ring C3 trigger:** All three Q-channels deasserted simultaneously: `cfcclk_qactive=0`, `cfcpwr_qactive=0`, `inf_qactive=0`. PMA autonomously fires without PUNIT involvement.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| System booted to XOS/SVOS | BIOS CPL4 complete; PCode GVFSM running | System hang or reset |
| Core C6 (CC6) enabled in BIOS | C-states enabled; `cpupower idle-set -e 2` on Linux | CC6 not reachable -- cores cannot trigger MC6 |
| No workload on test cores | All cores on test module must be idle | Cores stay in C0 -- Q-channels never deassert |
| MSR CC6 residency counter accessible | `pd.debug.access_to_msr(0x3FD, core=core)` readable | MSR not accessible on pre-silicon model |
| MC6 residency accessible | `pd.debug.access_to_msr(0x664, core=core)` readable | Module C6 counter not exposed |
| CBB GPSB accessible | `sv.socket0.cbb0.compute0.pma0.gpsb` readable | PMA GPSB not accessible in this model |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read baseline CC6 and MC6 residency counters on all cores of module0 | Counters accessible; note baseline values | Counters at max or unreadable -- pre-silicon model gap |
| 2 | Idle all cores in module0 of cbb0: MWAIT with `EAX=0x23` (C6S hint) | Cores enter CC6; MC6 residency counter increments | Cores stay in C0 -- C-states not enabled or platform too noisy |
| 3 | Wait ~10ms for Q-channels to deassert and Fast C3 to fire | PMA detects all Q-channels deasserted; Fast C3 sequence initiated | Q-channels never deassert -- active IP holding qactive |
| 4 | Read `GPSB.HWP_REQUEST_RESOLVED` on pma0 | Request shows reduced ratio consistent with CCF clock gate state | Request unchanged -- PMA not detecting idle state |
| 5 | Verify Global Uclk tree gated: check `GPSB` clock gate status register | Clock gate active on module0 (`cfcclk` tree closed) | Clock gate not asserted -- Fast C3 not engaged |
| 6 | Verify VCCRING retained (Fast C3 retains voltage) | FIVR VCCRING still powered; `UFS_STATUS.CURRENT_VOLTAGE` non-zero | Voltage dropped -- unexpected Ring C3 / deeper power state |
| 7 | Trigger core wakeup (interrupt or PythonSV write) | Fast re-enable of Uclk drivers in <10 cycles; cores return to C0 | Wake latency excessive or core stuck in C6 |
| 8 | Verify `PLR_DIE_LEVEL = 0x0` on cbb0 after exit | No spurious Performance Limit Reason from Fast C3 transition | PLR non-zero -- unexpected throttle event during C3 exit |
| 9 | Repeat for module1 of cbb0 and for cbb1 (both modules) | Same Fast C3 behavior on all modules; per-module independence confirmed | One module fails -- PMA asymmetry or stuck Q-channel |
| 10 | **HSLE/Simics only** — Ring C3 via PkgC6: idle all cores; verify D2D enters L1, Ring PLL powers down | D2D L1 state; `UFS_STATUS.CURRENT_RATIO = 0`; RING PLL disabled | D2D stays in L0 or PLL stays powered -- Ring C3 not reached |

### Pass / Fail Criteria

**PASS:** MC6 residency increments; PMA Fast C3 Q-channel assertion observed; Global Uclk tree clock-gated during module idle; VCCRING retained; fast wake on interrupt (<10 cycles); PLR = 0x0; per-module and per-CBB independence confirmed. HSLE: Ring C3 achieves D2D L1 and PLL powerdown.

**FAIL:** MC6 residency does not increment; Q-channels never deassert (stuck active IP); clock gate never asserted; VCCRING drops unexpectedly; wake fails or is excessively slow; PLR non-zero; Ring C3 fails D2D L1 handshake (HSLE only).

### Post-Process

Save: CC6/MC6 residency counters (before/during/after), HWP_REQUEST_RESOLVED, GPSB clock gate status, PLR_DIE_LEVEL for both CBBs, UFS_STATUS.CURRENT_VOLTAGE during C3, D2D link state (HSLE only).

### Reference Documents

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#switching-between-fast-gv-drainless-gv) -- Fast Ring C3 sequence, Q-channel logic, VCCRING retention
- [CBB CCP PM Integration HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCP%20HAS/cbb_cpp_has.html#vf-curves-grouping) -- CBB power states, PMA autonomous control
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details) -- GPSB telemetry, HWP_REQUEST_RESOLVED
- [DMR CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- [DMR SoC HAS](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/DMR_Overview_HAS.html#figure-hub-and-spoke) -- CCF ring topology, D2D L1 handshake
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP PKGC ZBB scope, Fast Ring C3 support

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable (Fast Ring C3) / HSLE-only (Ring C3)**

Fast Ring C3 (PkgC0 context) is supported on NWP silicon -- validate on real silicon. Ring C3 (PkgC6 prerequisite) requires PkgC6 which is fused off on NWP customer parts (FUSE_PKG_C_STATE=0) -- only testable on HSLE/Simics with UFS_DISABLE=0 override.

NWP has 2 CBBs, each with 2 compute dies, each with 6 modules x 8 cores = 96 cores per CBB. Each module (8 cores) can independently enter MC6 and trigger Fast Ring C3.

Tags: `CBB CCF`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### Key Register Paths (NWP)

| Register | NWP Path | Purpose |
|----------|----------|---------|
| GPSB HWP_REQUEST_RESOLVED | `sv.socket0.cbbN.compute0.pma0.gpsb.hwp_request_resolved` | Resolved HWP request -- CCF state |
| CC6 Residency | `pd.debug.access_to_msr(0x3FD, core=core)` | Per-core C6 residency |
| MC6 Residency | `pd.debug.access_to_msr(0x664, core=core)` | Per-module C6 residency |
| PLR_DIE_LEVEL | `sv.socket0.cbbN.base.tpmi.plr_die_level` | Perf Limit Reason |
| UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status` | CURRENT_RATIO + CURRENT_VOLTAGE |
| ACP_PERF_LIMIT | `sv.socket0.cbbN.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit` | ACP power limit |

### Idle Induction (Simics)

```python
# Force module0 cores into CC6S (MWAIT hint EAX=0x23)
for core_idx in range(8):  # 8 cores per module on NWP
    core = sv.socket0.cbb0.compute0.module0.cores[core_idx]
    core.thread0.write_reg("rax", 0x23)
    core.thread0.write_reg("rcx", 0x0)
# Hardware then sequences: CC6 -> MC6 -> Q-channels deassert -> Fast Ring C3
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Idle all cores in one module | MWAIT EAX=0x23 on all 8 cores of module0 |
| 2 | Wait for Q-channel assertion | `cli.run_command("emu.engine.wait-for-cycle -relative 1000000")` |
| 3 | Check GPSB state | `sv.socket0.cbb0.compute0.pma0.gpsb.hwp_request_resolved.read()` |
| 4 | Check MC6 counter | `pd.debug.access_to_msr(0x664, core=first_core)` -- expect > baseline |
| 5 | Verify PLR clean | `sv.socket0.cbb0.base.tpmi.plr_die_level.read()` -- expect 0x0 |

### Pass Criteria

MC6 counter increments; GPSB shows resolved low-power request; Uclk tree gated; VCCRING retained; PLR = 0x0; fast wake on interrupt.
