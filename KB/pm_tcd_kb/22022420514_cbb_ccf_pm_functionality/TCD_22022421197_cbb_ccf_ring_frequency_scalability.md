# TCD: CBB CCF Distress Signal Path

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421197](https://hsdes.intel.com/appstore/article-one/#/22022421197) |
| **Title** | CBB CCF Distress Signal Path |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420514 — CBB CCF Ring Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) |
| **Validation Phase** | **Alpha / Beta / PRQ** — Volume functional validation (multi-milestone) |
| **Feature** | CBB CCF Ring Frequency Scalability — Distress Signal Path |
| **Child TCs** | [22022422894](https://hsdes.intel.com/appstore/article-one/#/22022422894) — Distress Signal to PUnit<br>[22022422895](https://hsdes.intel.com/appstore/article-one/#/22022422895) — Snoop Scalability/Distress<br>[22022422905](https://hsdes.intel.com/appstore/article-one/#/22022422905) — PCode Algorithm for Distress Input |
| **KB last updated** | 2026-07-18 |

## Section 1: Architecture / Micro-architecture and Functionality

> **Architecture overview:** See [TPF 22022420514 — CBB CCF Ring Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) §2 Design Details
> for full-stack cross-layer diagram, dual-path architecture, NonAutoGV execution mechanism, and Interface & Register Matrix.

The **CBB CCF Distress Signal Path** (ring frequency scalability) drives CCF ring GV (Gear Voltage) transitions using two complementary telemetry inputs, both processed by CBB-local PCode:

1. **CBO Bandwidth (BW) path** — CBO mesh read/write counters feed a BW threshold LUT walk; if bandwidth exceeds the configured threshold for N slow-loops, CBB PCode requests a CCF ring GV boost via GVFSM. This is the primary **bandwidth-driven** scaling path.
2. **SBO Distress path** — SBO snoop back-pressure occupancy feeds the ring-scalability logic, generating **IA_DISTRESS** when occupancy exceeds threshold. IA_DISTRESS is delivered to the CBB-local PUNIT, where CBB PCode computes an `ia_ring_factor` (0..1) and drives an `ia_promote_ring` workpoint via GVFSM. This is the **congestion-driven** scaling path.

Both paths are **entirely CBB-local** — IMH/NIO Primecode does **not** decide whether the CBB ring boosts. **HPM 0x1b (`CBB_CCF_FREQUENCY`)** is the CCF frequency-coordination message (carrying `UPSTREAM_CCF_DESIRED_RATIO` and `DOWNSTREAM_CCF_RESOLVED_MIN_RATIO`) and is **not** the carrier of the distress signal.

### CBO Bandwidth Telemetry Path

```
CBO mesh counters accumulate per-cycle (RD/WR transactions)
  -> CBB PCode slow-loop reads CBO counters each ~1 ms
  -> BW threshold LUT walk: compare current BW to pre-configured thresholds
  -> if BW > HIGH_THRESHOLD for N loops: GVFSM boosts CCF ring ratio
  -> if BW < LOW_THRESHOLD for M loops: GVFSM reduces CCF ring ratio

Secondary output (ELC signaling, unrelated to ring GV):
  HPM 0x35 (MEM_BOUND_CYCLES / TOTAL_ACTIVE_CYCLES) -> IMH Primecode -> ELC decision
  [ELC path is separate from ring frequency scaling]
```

### Distress Signal Flow (SBO path, corrected)

```
SBO snoop back-pressure occupancy exceeds threshold
  -> Ring-scalability logic generates IA_DISTRESS
  -> CBB-local PUNIT receives IA_DISTRESS
  -> CBB PCode: ia_distress[3:0] -> ia_ring_factor (0..1)
  ->            ia_promote_ring = (maxcore_ratios - ia_to_ring_downbin) x ia_ring_factor
  -> CBB GVFSM executes GV transition (CCF ratio increases)
  -> Congestion relieves -> IA_DISTRESS de-asserts (hysteresis)

HPM 0x1b (CBB_CCF_FREQUENCY) -- runs in parallel, separate concern:
  UPSTREAM_CCF_DESIRED_RATIO        CBB -> IMH  (frequency intent)
  DOWNSTREAM_CCF_RESOLVED_MIN_RATIO IMH -> CBB  (min-ratio floor)
  [CCF frequency coordination only -- NOT the distress signal path]
```

### Distress Threshold Behavior

- Distress only fires when SBO occupancy > configured threshold for hysteresis window
- De-asserts after N slow-loops below threshold (prevents oscillation)
- Per-CBB: each CBB generates distress independently based on its own congestion

### Unified Block Diagram (Both Paths)

```
┌─────────────────────────────────────────────────────────────────┐
│  CBB Die  (all decisions local)                                 │
│                                                                 │
│   ┌─────────────────┐    ┌─────────────────┐               │
│   │  48 CBO mesh    │    │  SBO (snoop BW)  │               │
│   │  RD/WR counters │    │  occupancy ctr  │               │
│   └────────┬────────┘    └────────┬────────┘               │
│           │ BW            │ snoop occ.                    │
│   ┌────────▼────────┐    ┌────────▼────────┐               │
│   │  BW Threshold  │    │  Ring-Scalab. │               │
│   │  LUT Walk      │    │  Logic        │               │
│   └────────┬────────┘    └────────┬────────┘               │
│           │ GV target      │ IA_DISTRESS                   │
│           │            ┌────▼─────────────┐               │
│           │            │  CBB-local PUNIT  │               │
│           │            └────┬─────────────┘               │
│           │                │ ia_distress                   │
│           │            ┌────▼─────────────┐               │
│           │            │  CBB PCode       │               │
│           │            │  workpoint calc  │               │
│           │            └────┬─────────────┘               │
│           │                │ GV target (ia_promote_ring)   │
│           └─────────────────┬┘                             │
│                           │                               │
│                ┌──────────▼──────┐                             │
│                │  CBB GVFSM      │                             │
│                │  CCF ratio ↑    │                             │
│                └─────────────────┘                             │
│                                                                 │
│  ════════════ HPM 0x1b (freq coordination) ═════════════════► │
│  ════════════ HPM 0x35 (ELC signaling) ═════════════════════► │
│            [both to IMH/NIO Primecode - frequency coordination and ELC only]│
└─────────────────────────────────────────────────────────────────┘
```

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422894 — CBB CCF Distress Signal to PUnit](https://hsdes.intel.com/appstore/article-one/#/22022422894) | Distress signal path: CCF PMA → PMSB → PCode receives `ia_distress[3:0]` + `snoop_level[11:8]`; 4-bit grade (0–15) via `CR_WR 0x1C8` using 7-threshold logistic regression | `cbb_ccf_distress_to_punit_test` — checks `disable_ring_ee=0` per core, reads `ring_distress_status` grade under varying load |
| [22022422895 — CBB CCF Snoop Scalability/Distress](https://hsdes.intel.com/appstore/article-one/#/22022422895) | Snoop distress path: `ring_distress_status.snoop_level[11:8]` valid + responsive to snoop load; `group` field toggles (Group=0 IA / Group=1 Snoop) | `cbb_ccf_pcode_to_distress_input_test` (snoop side) |
| [22022422905 — CBB CCF PCode Algorithm for Distress Input](https://hsdes.intel.com/appstore/article-one/#/22022422905) | Distress policy: `ia_distress → ia_ring_factor → ia_promote_ring` workpoint; slow-loop + fast-path (200 µs DistressCycleUpdate) | PEGA injection, resolved ratio vars via `pcode.vars.ring` |

> **Related TCs under other TCDs:** CBO Telemetry ([22022422889](https://hsdes.intel.com/appstore/article-one/#/22022422889), parent TCD 22022421194), SBO Telemetry ([22022422900](https://hsdes.intel.com/appstore/article-one/#/22022422900), parent TCD 22022421202), PMON ([22022422886](https://hsdes.intel.com/appstore/article-one/#/22022422886), parent TCD 22022421190).

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| HPM 0x1b | `UPSTREAM_CCF_DESIRED_RATIO` / `DOWNSTREAM_CCF_RESOLVED_MIN_RATIO` | CCF frequency coordination (CBB ↔ IMH — NOT distress carrier) |
| HPM 0x35 | `MEM_BOUND_CYCLES`, `TOTAL_ACTIVE_CYCLES` | CBO-derived ELC signaling to Primecode (separate from ring GV path) |
| CBO counters | CBB TPMI / GPSB | Per-CBB cache BW measurement (RD/WR transactions); input to BW threshold LUT walk |
| SBO counter | CBB GPSB / TPMI | Snoop back-pressure occupancy; primary distress telemetry input |
| UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status.current_ratio` | Observable CCF ratio after any boost |
| UFS_ADV_CONTROL_1/2 | slope, base, threshold fields | BW threshold / distress threshold / hysteresis programming (N_ON, N_OFF, HIGH/LOW thresholds) |
| PLR_DIE_LEVEL | `sv.socket0.cbbN.base.tpmi.plr_die_level` | Perf Limit Reason (must be 0x0 during clean operation) |
| pcode.vars.ring | `resolved_ratios.max/.guaranteed/.min`, `ia_distress`, `ia_ring_factor` | PCode algorithm internal state — distress grade and ring factor observable via PythonSV |

---

## Section 3: Reset, Power, and Clocking

- CCF ring frequency state is reset on warm reset; PCode re-initializes UFS_CONTROL from BIOS-programmed TPMI values
- BIOS programs UFS_HEADER and UFS_CONTROL during TPMI_INIT (PH1.x) before OS handoff
- Telemetry counters reset on cold reset; warm-reset behavior depends on implementation (software must handle rollover)

---

## Section 4: Programming Model

- BIOS programs UFS_CONTROL (MAX_RATIO, MIN_RATIO, ELC thresholds) via TPMI before OS boot
- CBB PCode reads BIOS-programmed values and runs the slow-loop autonomously
- OS can modify UFS_CONTROL fields at runtime via TPMI writes (subject to BIOS lock)
- PMON event selection via MSR writes; counter read via TPMI or direct register access

---

## Section 5: Operational Behavior

CBB PCode samples both CBO and SBO telemetry every slow-loop cycle (~1 ms). There are two parallel scaling paths:

- **CBO BW path**: If CBO mesh bandwidth exceeds the `UFS_ADV_CONTROL` HIGH_THRESHOLD for N consecutive loops, PCode requests a CCF ring GV boost via GVFSM. De-boosts after M loops below LOW_THRESHOLD (hysteresis). Prevents oscillation under bursty cache traffic.
- **SBO distress path**: If SBO snoop occupancy exceeds threshold, the ring-scalability logic generates IA_DISTRESS. CBB PCode converts `ia_distress[3:0]` (0-15 grade) into `ia_ring_factor` (0..1) and computes `ia_promote_ring` as the new workpoint. GVFSM transitions to the result. Distress de-asserts after N_OFF loops below threshold.

Both paths are CBB-scoped: cbb0 and cbb1 operate independently. Under sustained high-coherency workload (96 cores, NWP), both paths may fire simultaneously. The ring GV target is the maximum of both paths' outputs.

The ring scalability algorithm samples distress on slow-loop (~1 ms) and on fast-path at DistressCycleUpdate = 200 µs.

---

## Section 6: Corner Cases & Error Handling

### CBO BW path corner cases

| Scenario | Expected Behavior |
|----------|------------------|
| CBO idle (no cache traffic) | CBO counters near-zero; CCF at low-power freq via BW path |
| Memory-bound workload | `MEM_BOUND_CYCLES` high; ELC High may activate (separate from ring GV) |
| BW spike shorter than 1ms | May not trigger CCF BW boost (below slow-loop resolution) |
| BW threshold too low | Spurious boosts; CCF never drops to low-power freq |

### SBO distress path corner cases

| Scenario | Expected Behavior |
|----------|------------------|
| SBO = 0 at idle | Normal — no snoop back-pressure; no distress |
| SBO not incrementing under coherency workload | Counter path broken or wrong metric |
| Distress at idle | False positive — SBO threshold too low or counter stuck |
| No distress under max load | Threshold too high or IA_DISTRESS path broken |
| Distress stuck after workload ends | Hysteresis timer not expiring; check N_OFF / LOW_THRESHOLD config |

### PCode distress policy / hysteresis corner cases

| Scenario | Expected Behavior |
|----------|------------------|
| Both SBO and CBO below threshold | No boost; `ia_ring_factor` = 0; algorithm in steady-state |
| Rapid load oscillation (burst < N_ON loops) | Hysteresis prevents thrashing; current freq held |
| Sustained load above HIGH_THRESHOLD for N_ON loops | CCF boost fires; `ia_ring_factor` > 0; `ia_promote_ring` computed |
| Max distress (ia_distress = 15) | `ia_ring_factor` = 1.0; maximum ring GV promotion |
| Workload drops; N_OFF loops below LOW_THRESHOLD | Boost removed; ring GV returns to autonomous BW-heuristic-driven freq |

---

## Section 7: Security / Safety / Policy

- TPMI registers may be locked by BIOS before OS handoff; runtime writes require BIOS unlock
- Distress thresholds should be validated against platform power policy to avoid CCF frequency instability
- PMON counter access requires appropriate privilege level (OS/VMM controlled)

---

## Section 8: References

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html)
- [CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html)
- [Fabric DVFS KB](../KB/pm_features/fabric_dvfs/fabric_dvfs_main.md)
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
