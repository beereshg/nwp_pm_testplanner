# TCD: CBB CCF PM Idle Exit GV Recovery

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421209](https://hsdes.intel.com/appstore/article-one/#/22022421209) |
| **Title** | CBB CCF PM x CState |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420507 — CBB CCF Active States](https://hsdes.intel.com/appstore/article-one/#/22022420507) |
| **Feature** | CBB CCF PM Idle Exit — C-state wake event GV recovery flow |
| **Validation Phase** | Alpha/Beta — idle exit GV transition correctness |
| **KB last updated** | 2026-07-18 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB CCF PM Idle Exit GV Recovery** validates that when the CCF ring is in **Active Idle** (Fast Ring C3 / ELC Low / perf-idle state at `CFC_MIN_RATIO`), incoming **C-state wake events** correctly trigger the CBB-local GVFSM to execute a GV ramp-up transition, restoring the ring to the appropriate active working point.

This TCD is the idle-*exit* counterpart to TCD 22022421179 (which covers idle *entry* and residency). The key validation concern is that no wake event is lost during the idle→active transition, and that the GVFSM completes the GV step to the correct target ratio before the fabric processes pending work.

### Active Idle State and GV Recovery Flow

```
CCF in Active Idle (ELC Low / Fast Ring C3)
  Ring ratio = CFC_MIN_RATIO (e.g. 0.8 GHz on NWP)
  GVFSM idle, CBB_RING_FASTC3_RESIDENCY accumulating

  ─── C-state wake event arrives ──────────────────────────────────
  │  Sources:
  │    (a) Core C-state exit (CC6→CC1→CC0) — demand traffic imminent
  │    (b) Frequency-change request from BW heuristic / PEGA injection
  │    (c) HPM 0x1b DOWNSTREAM_CCF_RESOLVED_MIN_RATIO update from IMH
  │
  ├─► CBB PCode detects wake event → issues GVFSM GV step
  │     V-first (freq up): FIVR ramp → PLL ratio change
  │     UFS_STATUS.CURRENT_RATIO tracks new working point
  │
  └─► CCF reaches target ratio → fabric active, traffic serviced
        PASS: ratio matches expected target, no events lost
        FAIL: ratio stuck at CFC_MIN_RATIO, or wrong ratio achieved
```

### Multiple Simultaneous Wake Events

```
Concurrent scenario (tested by cbb_ccf_cstate_x_wake_event_test):
  Event A: Core C-state wake (highest priority)
  Event B: BW-based frequency request (normal priority)

  Expected: highest-priority event wins; lower-priority request
            is absorbed into the same GV step or queued;
            no event is silently dropped
```

### NWP Context
- 2 CBBs per socket; each CBB independently manages its own CCF ring GV
- Active Idle = system in PkgC0, ELC Low mode, CCF at `CFC_MIN_RATIO`
- Ring C3 (PkgC6) exit is **ZBB on NWP** — this TCD targets the Active Idle exit only
- NWP D2D PHY upgrade (16→32 GT/s) increases roundtrip latency to 72 cycles at 2 GHz — wake event delivery timing differs from DMR

---

## Section 2: Interfaces and Protocols

| Interface | Register / Signal | Direction | Purpose |
|-----------|------------------|-----------|---------|
| `UFS_STATUS.CURRENT_RATIO` | TPMI offset 0x00 | R | Reflects locked CCF working-point ratio after GV step |
| `UFS_CONTROL.MIN_RATIO` | TPMI offset 0x01 | RW | Floor ratio (CFC_MIN_RATIO in ELC Low) |
| `CBB_RING_FASTC3_RESIDENCY` | CSR | R | Cycle count accumulated in Fast Ring C3 — should stop incrementing on wake |
| `base.ccf_pma.pm_state` | CSR | R | CCF PM FSM state — must leave idle state on wake |
| HPM 0x1b `UPSTREAM_CCF_DESIRED_RATIO` | HPM wire | CBB→IMH | CCF frequency intent after GV ramp |
| HPM 0x1b `DOWNSTREAM_CCF_RESOLVED_MIN_RATIO` | HPM wire | IMH→CBB | Min-ratio floor (may trigger wake) |
| PEGA injection | SW trigger | Host→CBB | Injects artificial GV request for test isolation |

### Interface Access Matrix

| Interface | MSR | TPMI | CSR | Notes |
|-----------|-----|------|-----|-------|
| UFS_STATUS (ratio) | — | R | — | `sv.sockets.socketN.cbbs.cbbX.tpmi.ufs.ufs_status` |
| Fast C3 residency | — | — | R | `sv.sockets.socketN.cbbs.cbbX.base.ccf_pma.ring_fastc3_residency` |
| CCF PM FSM | — | — | R | `sv.sockets.socketN.cbbs.cbbX.base.ccf_pma.pm_state` |

---

## Section 3: Reset, Power, and Clocking

- On Active Idle exit: ring PLL is already retained (Fast Ring C3 does not shut PLL); GV step is a ratio change only — no PLL restart required
- On Ring C3 exit (PkgC6, ZBB on NWP): PLL restart needed before GV ramp — not the focus of this TCD
- VCCRING remains powered during Active Idle (Fast Ring C3) — only ratio is reduced
- Warm reset clears all idle state; GV recovery flow restarts from boot defaults

---

## Section 4: Programming Model

```python
# C-state wake events across Active Idle (PMX)
# Tests multiple wake event types while CCF is in Active Idle / Fast Ring C3
ccfu.cbb_ccf_cstate_x_wake_event_test(skt_num, 'cbbs', Log=log, verbose=None)
```

Script: `diamondrapids/pm/Active_PM/CCF_GV/pmx_ccf_cbo.py`
Option: `--test_ccf_cstate_x_wake_event`

**Test flow (inferred from function name and feature context):**
1. Confirm CCF is in Active Idle (Fast Ring C3) — ratio at `CFC_MIN_RATIO`, residency counter accumulating
2. Inject C-state wake event (type X, iterated across supported wake event types)
3. Verify GVFSM executes GV step: `UFS_STATUS.CURRENT_RATIO` changes to expected target
4. Verify `CBB_RING_FASTC3_RESIDENCY` stops incrementing (CCF left idle)
5. Verify no event is dropped (concurrent events both serviced)
6. Restore CCF to idle, repeat for next wake event type

---

## Section 5: Operational Behavior

### Normal (Pass) Scenario
```
Pre-condition : CCF in Active Idle, CURRENT_RATIO = CFC_MIN_RATIO
Stimulus      : Inject wake event (C-state exit or BW request or HPM update)
Expected      : GVFSM executes V-first GV step
                CURRENT_RATIO = target_ratio (> CFC_MIN_RATIO)
                CBB_RING_FASTC3_RESIDENCY stops incrementing
                pm_state exits idle
```

### Failure Modes
```
FAIL A: CURRENT_RATIO remains at CFC_MIN_RATIO after wake event
        Root cause: GVFSM not triggered, wake event lost or masked

FAIL B: Wrong target ratio achieved
        Root cause: GV step used wrong workpoint (wrong ia_ring_factor or
                    incorrect DOWNSTREAM_CCF_RESOLVED_MIN_RATIO applied)

FAIL C: Event B lost when Event A and Event B arrive simultaneously
        Root cause: Event arbitration bug in CBB PCode ring-scalability logic
```

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| Single C-state wake event (type A) | GVFSM ramps to correct target ratio |
| Concurrent C-state + BW request | Both processed; no event silently dropped |
| Wake event during prior GV step (in-flight) | New event queued; GVFSM completes current step first or merges |
| Wake event with DOWNSTREAM min-ratio = CFC_MIN_RATIO | No GV step triggered (already at floor) |
| Active Idle entered and exited rapidly (< 1 ms) | GVFSM must handle fast toggle without getting stuck |
| NWP 2 CBBs: wake events arrive on different CBBs simultaneously | Each CBB independently handles its own GV step |

---

## Section 7: Security / Safety / Policy

- GV recovery test requires ring 0 (PythonSV / PMX framework)
- PEGA injection used for test isolation — released via `pega.release(1)` in test teardown
- HPM 0x1b traffic during test must not interfere with IMH fabric DVFS; test is CBB-local

---

## Section 8: References

| Type | Reference | Scope |
|------|-----------|-------|
| HAS | [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html) | CCF GV execution flow, Active Idle exit, GVFSM |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | CBB ring GV, ELC Low, perf-idle state |
| HAS | [CBB P-State Stack — ELC Low](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html#efficiency-latency-control-mode) | ELC Low implementation: floor ratio, Active Idle entry |
| HAS | [HPM Message Specification](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html) | HPM 0x1b CCF frequency coordination message |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM delta, D2D latency change (72 cycles @ 2 GHz) |
| KB | KB/pm_features/fabric_dvfs/fabric_dvfs_main.md | ELC Low threshold, CFC_MIN_RATIO, CCF ring GV algorithm |
| KB | KB/pm_features/core_c_states/pkgc.md | PkgC wake event delivery path to CBB |
| Related TCD | [22022421179 — CBB CCF PM Idle Scenario](https://hsdes.intel.com/appstore/article-one/#/22022421179) | Idle entry & residency (Fast Ring C3, Ring C3) |
| Related TCD | [22022421197 — CBB CCF Ring Frequency Scalability](https://hsdes.intel.com/appstore/article-one/#/22022421197) | Active GV transitions (distress, BW heuristic) |
| PMX script | `diamondrapids/pm/Active_PM/CCF_GV/pmx_ccf_cbo.py` | `cbb_ccf_cstate_x_wake_event_test` |
| Parent Sub-TP | [22022420514 — CBB CCF Ring Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) | TP hierarchy context |

## TC Coverage

| TC ID | Title | Environment | Status |
|-------|-------|-------------|--------|
| [22022422868](https://hsdes.intel.com/appstore/article-one/#/22022422868) | CBB CCF PM Cstate wake events across Activeidle | silicon, virtual_platform | open |
