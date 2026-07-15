# Deep Analysis: CBB CCF Ring C3

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422873](https://hsdes.intel.com/appstore/article-one/#/22022422873) |
| **Title** | CBB CCF Ring C3 |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CBB CCF -- Ring C3 deep CCF power-off state |
| **Parent TCD** | [22022421179](https://hsdes.intel.com/appstore/article-one/#/22022421179) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Validate CBB CCF Ring C3 entry and exit — the deep CCF power-off state that shuts down the Ring PLLs, drains the CCF ring fabric, gates VCCRING, and transitions the D2D UCIe link to L1. On NWP, Ring C3 requires PkgC6 as a prerequisite; since PkgC6 is fused off on customer silicon, full Ring C3 is tested on **HSLE/Simics only**. Silicon testing covers Fast Ring C3 (PkgC0 context) as the PMA-autonomous precursor.

**Ring C3 vs Fast Ring C3:**

| State | Trigger | CCF Power | VCCRING | Ring PLL | D2D | NWP Silicon |
|-------|---------|-----------|---------|----------|-----|-------------|
| Fast Ring C3 | PkgC0, PMA-autonomous (MC6) | Uclk tree gated | Retained | On | L0 | Supported |
| Ring C3 | PkgC6 prerequisite | Fully drained | Gated | **Off** | **L1** | HSLE/Simics only |

**Ring C3 entry sequence:** Fast Ring C3 fires first → D2D UCIe L1 entry handshake → CCF ring fully drained → RING PLLs shut down → VCCRING gated.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| Platform booted | BIOS CPL4 complete; PCode running | System not booted |
| BIOS: C-states + PkgCx enabled | CC6 and PkgC6 inducible (HSLE) or CC6/MC6 (silicon) | C-states disabled -- Ring C3 not reachable |
| HSLE/Simics: MWAIT injection supported | Simics magic instruction for `EAX=0x25` (C6S-P) available | Cannot induce PkgC6 |
| CBB TPMI and GPSB accessible | `ufs_status`, `opc_pkgc_entry_control`, `gpsb` paths valid | TPMI/GPSB not accessible in model |
| CC6/MC6 residency MSRs readable | `msr(0x3FD)`, `msr(0x664)` accessible | MSR access not available |
| No active IP holding D2D in L0 | All D2D traffic quiesced before Ring C3 entry | D2D stays in L0 -- L1 entry blocked |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Baseline: read `UFS_STATUS.CURRENT_RATIO`, `OPC_PKGC_ENTRY_CONTROL`, and CC6/MC6 residency on both CBBs | Non-zero ratio (pre-C3 baseline); OPC_PKGC_ENTRY_CONTROL readable | TPMI not initialized |
| 2 | **Silicon only — Fast Ring C3 precursor:** idle all module0 cores via MWAIT `EAX=0x23`; verify PMA engages Fast Ring C3 (per TC 22022422865) | Q-channels deassert; Uclk tree gated; VCCRING retained | Fast Ring C3 not triggered -- prerequisite for Ring C3 |
| 3 | **HSLE/Simics — Induce PkgC6:** all cores MWAIT `EAX=0x25` (C6S-P); wait for package-level idle | PkgC6 entry conditions met; Fast Ring C3 fires as prerequisite | PkgC6 not reached -- verify all cores idle and no active IP |
| 4 | **HSLE/Simics — D2D L1 entry:** verify UCIe D2D link enters L1 (`D2D_LINK_STATE = L1`) | D2D L1 handshake completes (v_change_request/ack exchanged); link idle | D2D stays in L0 -- L1 blocked by active traffic |
| 5 | **HSLE/Simics — CCF drain:** verify CCF ring fully drained (no in-flight transactions) | CCF drain complete; no pending AXI/UCIe transactions | Drain timeout -- stuck transaction holds CCF active |
| 6 | **HSLE/Simics — RING PLL shutdown:** verify `UFS_STATUS.CURRENT_RATIO = 0` (PLL off) and RING PLL disabled | CURRENT_RATIO = 0; RING PLL powered down | Ratio non-zero -- PLL not shut down; Ring C3 not fully entered |
| 7 | **HSLE/Simics — VCCRING gate:** verify FIVR VCCRING supply gated | VCCRING output zero / FIVR disabled | VCCRING retained -- full Ring C3 not achieved |
| 8 | **Exit — wake injection:** inject interrupt or workload to trigger Ring C3 exit; wait for full recovery | D2D L1 exit handshake; RING PLLs re-lock; CCF ratio restores to P0 (≈ 2.2 GHz) | PLL re-lock timeout; ratio stuck at 0 -- exit hang |
| 9 | Verify post-exit: `UFS_STATUS.CURRENT_RATIO` = pre-Ring-C3 baseline and `PLR_DIE_LEVEL = 0x0` | CCF frequency fully restored; no PLR from Ring C3 transition | Ratio below baseline -- PLL did not re-lock; PLR non-zero |
| 10 | Verify residency counters advanced: CC6 and MC6 reflect all idle cycles through Ring C3 | Residency counters incremented from baseline | Counters stale -- ring power states not accounted |

### Pass / Fail Criteria

**PASS (Silicon — Fast Ring C3 only):** Q-channels deassert; Uclk tree gated; VCCRING retained; clean exit to pre-C3 ratio; PLR = 0x0.

**PASS (HSLE/Simics — Full Ring C3):** D2D enters L1; CCF fully drained; RING PLLs off (`CURRENT_RATIO = 0`); VCCRING gated; exit restores to P0 (~2.2 GHz); PLR = 0x0; residency counters advanced.

**FAIL:** D2D L1 blocked; CCF drain timeout; RING PLL not shut down; CURRENT_RATIO != 0 during Ring C3; VCCRING not gated; exit hang (PLL re-lock failure); PLR non-zero.

### Post-Process

Save: UFS_STATUS.CURRENT_RATIO at each phase (baseline, Ring C3, post-exit), D2D link state log (HSLE), RING PLL state, VCCRING FIVR status, PLR_DIE_LEVEL for both CBBs, CC6/MC6 residency delta.

### Reference Documents

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#switching-between-fast-gv-drainless-gv) -- Ring C3 sequence, VCCRING gate, RING PLL shutdown, D2D L1 handshake
- [CBB CCP PM Integration HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCP%20HAS/cbb_cpp_has.html) -- CBB power states, UCIe D2D coordination
- [DMR SoC HAS](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/DMR_Overview_HAS.html#figure-hub-and-spoke) -- D2D L1 handshake protocol, CCF drain prerequisites
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html) -- UFS_STATUS.CURRENT_RATIO, OPC_PKGC_ENTRY_CONTROL
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html) -- GPSB telemetry during C3
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- Related TC: [22022422865 -- CBB CCF Fast Ring C3](https://hsdes.intel.com/appstore/article-one/#/22022422865) -- silicon-testable precursor

---

## Section A: NWP Disposition & Justification

**Disposition: Partial -- Fast Ring C3 on silicon; Full Ring C3 on HSLE/Simics only**

Ring C3 requires PkgC6 as a prerequisite. PkgC6 is fused off (`FUSE_PKG_C_STATE=0`) on NWP customer silicon. Full Ring C3 (RING PLLs off, VCCRING gated, D2D L1) can only be validated on HSLE/Simics where PkgC6 can be induced. On silicon, Fast Ring C3 (TC 22022422865) covers the PMA-autonomous precursor.

Tags: `CBB CCF`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### Key Register Paths (NWP)

| Register | NWP Path | Purpose |
|----------|----------|---------|
| UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status` | CURRENT_RATIO = 0 in Ring C3 |
| OPC_PKGC_ENTRY_CONTROL | `sv.socket0.cbbN.base.tpmi.opc_pkgc_entry_control` | Package C-state entry gate |
| PLR_DIE_LEVEL | `sv.socket0.cbbN.base.tpmi.plr_die_level` | Perf Limit Reason check |
| CC6 Residency | `pd.debug.access_to_msr(0x3FD, core=core)` | Per-core C6 residency |
| MC6 Residency | `pd.debug.access_to_msr(0x664, core=core)` | Per-module C6 residency |

### Idle Induction for Ring C3 (HSLE/Simics)

```python
# All cores MWAIT with EAX=0x25 (C6S-P) to induce PkgC6 -> Ring C3
for cbb in sv.sockets.cbbs:
    for module in cbb.computes.modules:
        for core in module.cores:
            core.thread0.write_reg("rax", 0x25)  # C6S-P = PkgC6 hint
            core.thread0.write_reg("rcx", 0x0)
cli.run_command("emu.engine.wait-for-cycle -relative 10000000")
# Verify Ring C3: CURRENT_RATIO = 0, D2D L1
ratio = sv.socket0.cbb0.base.tpmi.ufs_status.read() & 0x7F
print("Ring C3 ratio:", ratio, "-> expected 0 (PLL off)")
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Silicon: Fast Ring C3 | Follow TC 22022422865 (MWAIT EAX=0x23 on module0 cores) |
| 2 | HSLE: induce PkgC6 | MWAIT EAX=0x25 all cores; wait 10M cycles |
| 3 | Check Ring C3 entry | `ufs_status.read() & 0x7F` -- expect 0 (PLL off) |
| 4 | Check D2D L1 | D2D link state register -- expect L1 |
| 5 | Inject wake | Interrupt injection; verify recovery to ~0x16 (2.2 GHz) |

### Pass Criteria

Silicon: Fast Ring C3 per TC 22022422865. HSLE: CURRENT_RATIO = 0; D2D L1; VCCRING gated; exit restores to P0; PLR = 0x0.
---

## Section S: Script Implementation Details

**Script file:** `pm/Active_PM/CCF_GV/pmx_ccf_cbo.py`
**Library:** `pm/pmutils/ccf_utils.py`
**PMX option flag:** `--test_ccf_ring_c3`
**Run command:** `runPmx.py -x dmr.xml -p ccf_cbo_test -tM 60 -M 5 --test_ccf_ring_c3`

### Function Called

```python
# pmx_ccf_cbo.py → mainTest()
ccfu = diamondrapids.pm.pmutils.ccf_utils
ccfu.ccf_ring_c3_test(sktNum, rtime=100)
```

### Workload

**Workload type:** C-state injection (synthetic)

Workload: Ring C3 state machine injection via PEGA cstate (`op='c6sp'`). No external workload.
