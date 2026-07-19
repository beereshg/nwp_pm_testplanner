# TCD: CBB CCF PM Idle Scenario

<!-- SPLIT: This TCD was split into TCD 16031169646 (CBB CCF Fast Ring C3) and TCD 16031169647 (CBB CCF Ring C3).
     HSD title: "[SPLIT] CBB CCF Idle states - see TCD 16031169646 and 16031169647"
     See: TCD_16031169646_cbb_ccf_fast_ring_c3.md and TCD_16031169647_cbb_ccf_ring_c3.md in this directory.
     This KB file is retained as source material reference only — do not push to HSD. -->

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421179](https://hsdes.intel.com/appstore/article-one/#/22022421179) |
| **Title** | CBB CCF PM Idle Scenario |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TP** | [22022420507 -- CBB CCF Active States](https://hsdes.intel.com/appstore/article-one/#/22022420507) |
| **Feature** | CBB CCF Idle States — Ring C3, Fast Ring C3 (idle entry & residency power saving) |
| **Validation Phase** | Alpha/Beta — CBB CCF idle state entry/exit and wake event handling |
| **KB last updated** | 2026-07-15 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB CCF PM Idle Scenario** validates the CBB CCF idle-state **entry and residency** (power-saving) on NWP silicon. The feature covers two idle-state power-saving scenarios:

1. **Fast Ring C3** — A shallow CCF idle state entered during PkgC0 where the CCF ring fabric is low-activity. Ring PLL may be retained; core and D2D states must be correctly managed.
2. **Ring C3** — The deep CCF power-off state entered during PkgC6. Shuts down Ring PLLs, drains the CCF ring fabric, gates VCCRING, and transitions the D2D UCIe link to L1.

> **Note:** Idle *exit* and GV recovery on wake events are covered by TCD 22022421209 "CBB CCF PM Idle Exit GV Recovery".

### CBB CCF Idle State Diagram

```
PkgC0 (Package Active)
  │
  ├── CCF Active          : Ring PLL on, fabric active, D2D L0
  │
  └── Fast Ring C3        : Low-activity idle; Ring PLL retained or gated
        └── Entry: BW heuristic below threshold, no pending traffic
        └── Exit:  Wake event (C-state request, frequency change)
        └── NWP:   Verify Ring PLL state, Global CLK Gating, Core state, D2D state

PkgC6 (Package C6)
  │
  └── Ring C3 (deep)      : Ring PLLs OFF, fabric drained, VCCRING gated, D2D L1
        └── Entry: All cores in C6, CCF fabric drain complete
        └── Exit:  Wake event → Ring PLL restart → fabric re-init → D2D L0 restore
        └── NWP:   ZBB (PkgC6 not exercised); focus on entry flow and register state
```

### NWP Context
- 2 CBBs per socket (cbb0, cbb1)
- Ring C3 entry is PkgC6-dependent (ZBB on NWP per platform constraints)
- Fast Ring C3 is exercisable during PkgC0 scenarios
- D2D UCIe link state transitions (L0↔L1) are validated as part of Ring C3

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| Ring PLL control | `base.cbb_pma.ring_pll_status` | Ring PLL enable/disable state during C3 entry/exit |
| Global CLK Gating | `base.ccf_pma.global_clk_gate` | Clock gate status during Fast Ring C3 |
| D2D UCIe link state | `base.d2d.ucie_link_state` | L0/L1 transition during Ring C3 |
| Core idle state | `base.cbb_pma.core_idle_status` | All-cores-idle prerequisite for Ring C3 |
| CCF PM state machine | `base.ccf_pma.pm_state` | Current CCF idle FSM state |
| PMSB wake event | `base.punit_pmsb.wake_event` | C-state wake event delivery to CCF |

**Interface Access Matrix:**

| Interface | MSR | TPMI | CSR | Notes |
|-----------|-----|------|-----|-------|
| Ring PLL status | -- | -- | R | Via PythonSV `base.cbb_pma` path |
| D2D UCIe state | -- | -- | R | Via PythonSV `base.d2d` path |
| CCF PM FSM | -- | -- | R | Observable via PythonSV |

---

## Section 3: Reset, Power, and Clocking

- Ring C3 requires full Ring PLL restart after wake — PLL lock time must be met before fabric re-init
- Fast Ring C3 retains Ring PLL; clock gating is applied at fabric level only
- Warm reset restores CCF to Active state; Ring C3 state is not preserved across reset
- VCCRING power domain is gated during Ring C3 — requires proper sequencing on entry/exit

---

## Section 4: Programming Model

```python
# Fast Ring C3 state check (PMX)
ccfu.ccf_fast_ring_c3_test(skt_num, 'cbbs', rtime=100, Log=log, verbose=None)

# Ring C3 state check (PMX)
ccfu.ccf_ring_c3_test(skt_num, rtime=100, Log=log, verbose=None)
```

Script: `diamondrapids/pm/Active_PM/CCF_GV/pmx_ccf_cbo.py`
Options: `--test_ccf_fast_ring_c3`, `--test_ccf_ring_c3`

---

## Section 5: Operational Behavior

**Fast Ring C3 test:**
1. Drive system to PkgC0 low-activity state
2. Verify CCF enters Fast Ring C3: check Ring PLL state, Global CLK Gating, Core state, D2D state
3. Verify exit on wake event — all states restore correctly

**Ring C3 test (PkgC6):**
1. Place all cores in C6 to trigger Ring C3 entry
2. Verify Ring PLL shutdown, fabric drain, VCCRING gate, D2D L1
3. Inject wake event → verify PLL restart, fabric re-init, D2D L0 restore
4. NWP: ZBB for PkgC6; validates entry flow and register state only

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| Wake event during Ring PLL restart | Queued; serviced after PLL lock |
| Fast Ring C3 with D2D traffic | CCF must exit Fast C3 immediately on D2D activity |
| Ring C3 entry with pending CCF request | Entry must be gated until fabric is fully drained |
| PkgC6 ZBB on NWP | Ring C3 deep state not exercised; only entry conditions validated |

---

## Section 7: Security / Safety / Policy

- Idle state transitions require ring 0 (PythonSV / PMX framework)
- Ring C3 gating respects all pending CCF requests before power-off
- D2D L1 entry follows UCIe specification for link state negotiation

---

## Section 8: References

| Type | Reference | Scope |
|------|-----------|-------|
| HAS | [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html) | CCF Ring C3 / Fast Ring C3 entry/exit flows, PLL shutdown, spine gating |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | CBB CCF ring power management, C-state coordination |
| HAS | [DMR PkgC Idle Flow HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Idle_Flow/DMR_PkgC.html) | PkgC6 entry/exit — Ring C3 trigger and wake event flow |
| HAS | [DMR CCB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) | CBB PM feature index |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP-specific PM delta; PkgC6 ZBB status |
| KB | KB/pm_features/fabric_dvfs/fabric_dvfs_main.md | CBB CCF ring DVFS, Fast Ring C3 (ELC Low / perf-idle state) |
| KB | KB/pm_features/core_c_states/pkgc.md | Package C-state coordination, Ring C3 trigger condition |
| KB | KB/pm_features/core_c_states/c6.md | Core C6 entry/exit flow — prerequisite for Ring C3 |
| PMX script | `diamondrapids/pm/Active_PM/CCF_GV/pmx_ccf_cbo.py` | `ccf_fast_ring_c3_test`, `ccf_ring_c3_test` |
| Related TCD | [22022421209 — CBB CCF PM Idle Exit GV Recovery](https://hsdes.intel.com/appstore/article-one/#/22022421209) | Idle exit / GV recovery (TC 22022422868 moved there) |
| Parent Sub-TP | [22022420507 — CBB CCF Active States](https://hsdes.intel.com/appstore/article-one/#/22022420507) | TP hierarchy context |

## TC Coverage

| TC ID | Title | Environment | Status |
|-------|-------|-------------|--------|
| [22022422865](https://hsdes.intel.com/appstore/article-one/#/22022422865) | CBB CCF Fast Ring C3 | silicon, virtual_platform | open |
| [22022422873](https://hsdes.intel.com/appstore/article-one/#/22022422873) | CBB CCF Ring C3 | silicon (ZBB on NWP) | open |
