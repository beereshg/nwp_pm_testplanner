# TCD: CBB PCode Ring-Distress Consumption Algorithm

<!-- NEW 2026-07-19: Split from TCD 22022421197 (CBB CCF Distress Signal Path).
     Co-Design T2 ingest: FW algorithm correctness (PCode) has a different bar
     from HW signal generation (silicon). This TCD covers the PCode firmware side.
     HSD TCD creation pending — replace NEW with actual HSD ID when created. -->

| Field | Value |
|-------|-------|
| **TCD ID** | *(HSD creation pending)* |
| **Title** | CBB PCode Ring-Distress Consumption Algorithm |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420514 — CBB CCF Ring Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) |
| **Validation Phase** | **Alpha / Beta / PRQ** — Volume functional validation (multi-milestone) |
| **Feature** | CBB CCF Ring Frequency Scalability — PCode Distress-to-Workpoint Algorithm |
| **Child TCs** | [22022422905](https://hsdes.intel.com/appstore/article-one/#/22022422905) — PCode Algorithm for Distress Input |
| **Split from** | [22022421197](https://hsdes.intel.com/appstore/article-one/#/22022421197) — CBB CCF Distress Signal Path |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Architecture / Micro-architecture and Functionality

> **Architecture overview:** See [TPF 22022420514 — CBB CCF Ring Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) §2 Design Details
> for full-stack cross-layer diagram, dual-path architecture, and Interface & Register Matrix.

**CBB PCode Ring-Distress Consumption Algorithm** validates the **firmware-side** (CBB PCode) of the ring scalability feature: how PCode converts the distress signal into a ring frequency workpoint decision.

Given `ia_distress[3:0]` (0-15 grade) delivered by CCF PMA via PMSB CR_WR to `PUNIT_CR_RING_DISTRESS_STATUS`, CBB PCode:

1. Reads `ia_distress[3:0]` and `snoop_level[11:8]` from the distress status register
2. Converts `ia_distress` to `ia_ring_factor` (0..1) via `ring_distress_table[level][epb]`
3. Computes `distress_ccf_freq = max_ccp_req × ring_distress_table[level][epb]`
4. Computes `snoop_floor = snoop_distress_table[snoop_level][epb]`
5. Final ratio: `min(max(distress_ccf_freq, snoop_floor), rapl_ccf_freq, global_limits)`
6. Clamps to [MIN_RATIO, MAX_RATIO] from UFS_CONTROL
7. Issues GVFSM workpoint command if ratio changed

This TCD does **NOT** cover the silicon-side telemetry/distress generation — that is validated by the sibling TCD "CBB CCF Ring Scalability Telemetry & Distress Generation".

### PCode Algorithm Flow

```
PUNIT_CR_RING_DISTRESS_STATUS (0x1C8)
  ia_distress[3:0]     ← from CCF PMA (sibling TCD)
  snoop_level[11:8]    ← from CCF PMA (sibling TCD)
         |
         v
CBB PCode (slow-loop ~1 ms OR fast-path 200 µs)
  ┌──────────────────────────────────────────────┐
  │ distress_ccf_freq =                          │
  │   max_ccp_req × ring_distress_table[ia][epb] │
  │                                              │
  │ snoop_floor =                                │
  │   snoop_distress_table[snoop_level][epb]     │
  │                                              │
  │ ufs_ratio = max(distress_ccf_freq,           │
  │                 snoop_floor)                  │
  │                                              │
  │ final = min(ufs_ratio,                       │
  │             rapl_ccf_freq,                   │
  │             global_limits)                   │
  │                                              │
  │ clamp to [MIN_RATIO, MAX_RATIO]              │
  └──────────────────┬───────────────────────────┘
                     │ resolved ring workpoint
                     v
              CBB GVFSM → GV transition
```

### Trigger Paths

| Trigger | Period | When |
|---------|--------|------|
| Slow-loop | ~1 ms | Every PCode slow-loop iteration |
| Fast-path: distress state change | immediate | On ia_distress assertion or de-assertion |
| Fast-path: DistressCycleUpdate | 200 µs | Periodic fast sampling during active distress |

### Spec Refs (from Co-Design T2)

- "traffic collected from CBO pipe + central SBO, accumulated once per RSE, sent to Pcode through SB; Pcode decides whether GV is necessary and generates a new workpoint" — [cbb_ccf_pm.html](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/ip%20integration/ccf/cbb_ccf_pm.html)

---

## Section 5: Pass/Fail Bar

Given a rising distress/grade input from ring-scalability logic:
- PCode changes the resolved ring workpoint from baseline to a promoted workpoint on the next control opportunity
- `pcode.vars.ring.ia_ring_factor` > 0 under distress
- `pcode.vars.ring.resolved_ratios.max` reflects the promoted workpoint
- Ring frequency responds to distress level changes within slow-loop (~1ms) or fast-path (200µs)

Given a cleared/low distress input:
- PCode returns toward the lower workpoint according to the SB-fed control loop
- `ia_ring_factor` returns to 0; resolved ratio decreases

**FAIL:** `ia_ring_factor` stuck at 0 regardless of distress input; resolved workpoint unchanged under sustained distress; ring frequency does not respond to distress level changes.

---

## Section 6: TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422905 — CBB CCF PCode Algorithm for Distress Input](https://hsdes.intel.com/appstore/article-one/#/22022422905) | Distress policy: `ia_distress → ia_ring_factor → ia_promote_ring` workpoint; slow-loop + fast-path triggers; `pcode.vars.ring` observable internals | PEGA injection as stimulus; PCode vars readback |

---

## Section 7: Corner Cases

| Scenario | Expected Behavior |
|----------|------------------|
| Both SBO and CBO below threshold | No boost; `ia_ring_factor` = 0; algorithm in steady-state |
| Rapid load oscillation (burst < N_ON loops) | Hysteresis prevents thrashing; current freq held |
| Sustained load above HIGH_THRESHOLD for N_ON loops | CCF boost fires; `ia_ring_factor` > 0; `ia_promote_ring` computed |
| Max distress (ia_distress = 15) | `ia_ring_factor` = 1.0; maximum ring GV promotion |
| Workload drops; N_OFF loops below LOW_THRESHOLD | Boost removed; ring GV returns to autonomous BW-heuristic-driven freq |
| PEGA injection during active distress | PEGA overrides BW heuristic but distress workpoint may override PEGA if higher |
| UFS_CONTROL ratio lock (MAX=MIN) during distress | GV transitions suppressed; distress grade still generated but ratio clamped |

---

## Section 8: References

| Reference | Link |
|-----------|------|
| CBB CCF PM HAS | [cbb_ccf_pm.html](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/ip%20integration/ccf/cbb_ccf_pm.html) |
| CBB CCF PM HAS v1.0 | [cbb_ccf_pm.1.0.html](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.1.0.html) |
| DMR CBB Power Management | [dmr_cbb_power_management.html](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/cbb%20overview/dmr_cbb_power_management.html) |
| Parent TPF | [TPF 22022420514 — CBB CCF Ring Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) |
| Sibling TCD | TCD_NEW_telemetry_distress_generation.md — HW telemetry side |
| Split source | [TCD 22022421197 — CBB CCF Distress Signal Path](https://hsdes.intel.com/appstore/article-one/#/22022421197) |