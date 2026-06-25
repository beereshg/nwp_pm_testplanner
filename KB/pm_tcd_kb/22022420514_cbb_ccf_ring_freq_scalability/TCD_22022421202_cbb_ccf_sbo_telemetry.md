# TCD: CBB CCF SBO Telemetry

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421202](https://hsdes.intel.com/appstore/article-one/#/22022421202) |
| **Title** | CBB CCF SBO Telemetry |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420514 -- CBB CCF Ring Frequency Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) |
| **Feature** | CBB CCF Ring Frequency Scalability |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB CCF SBO Telemetry** captures snoop back-pressure in the CBO mesh via the Snoop Back-pressure Oracle (SBO). High SBO occupancy indicates that coherency traffic is overwhelming the CCF ring capacity, which PCode uses as a signal to boost CCF frequency. SBO is one of two distress inputs (alongside CBO occupancy) driving the CCF frequency boost algorithm.

### SBO Telemetry Flow

1. SBO measures snoop occupancy: fraction of cycles where snoop queue is highly occupied
2. CBB PCode reads SBO counter each slow-loop
3. If SBO > threshold: distress path engaged, CCF freq boosted
4. SBO input contributes to `UPSTREAM_CCF_DESIRED_RATIO` in HPM 0x1b

### NWP Context

- NWP: 96 cores driving coherency; SBO pressure can be very high under NUMA workloads
- SBO is per-CBB: each CBB's SBO responds to its own snoop back-pressure independently

### Block Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│  CBB Die                                                                 │
│                                                                          │
│  ┌───────────────────────────────────┐                                   │
│  │  CBO Mesh (Snoop traffic)         │                                   │
│  │  48 cache boxes per CBB           │                                   │
│  │  High coherency → snoop queue full│                                   │
│  └─────────────────┬─────────────────┘                                   │
│                    │ snoop occupancy                                     │
│  ┌─────────────────▼─────────────────┐                                   │
│  │  SBO (Snoop Back-pressure Oracle) │                                   │
│  │  Measures: snoop queue depth      │                                   │
│  │  Output: SBO_occupancy counter    │                                   │
│  └─────────────────┬─────────────────┘                                   │
│                    │ counter value                                       │
│  ┌─────────────────▼─────────────────┐                                   │
│  │  CBB PCode Slow-Loop              │                                   │
│  │  Compare SBO vs threshold         │                                   │
│  │  if SBO > HIGH_THRESHOLD for N:   │                                   │
│  │    assert distress / boost freq   │                                   │
│  └─────────────────┬─────────────────┘                                   │
│                    │                                                     │
│  ┌─────────────────▼─────────────────┐                                   │
│  │  GVFSM → CCF ring ratio boost     │ ◄── UFS_STATUS.CURRENT_RATIO↑    │
│  │  HPM 0x1b UPSTREAM_DESIRED_RATIO↑ │ ──► IMH Primecode                │
│  └───────────────────────────────────┘                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422900 -- CBB CCF SBO Telemetry](https://hsdes.intel.com/appstore/article-one/#/22022422900) | Counter correctness, threshold response | SBO increments under coherency, triggers freq boost |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| SBO counter | CBB GPSB / TPMI telemetry | Snoop back-pressure occupancy |
| UFS_ADV_CONTROL_1 | Slope/base for SBO distress line | SBO threshold configuration |
| HPM 0x1b | `UPSTREAM_CCF_DESIRED_RATIO` | SBO-driven boost to Primecode |
| UFS_STATUS | `current_ratio` | CCF freq after SBO-triggered boost |

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

SBO telemetry is hysteretic: N consecutive loops above threshold before triggering frequency boost, M below before reverting. The SBO threshold is programmed via `UFS_ADV_CONTROL_1` SLOPE/BASE fields. Under sustained high-NUMA workload, SBO should stabilize above threshold and hold CCF at P0.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| SBO = 0 at idle | Normal -- no snoop back-pressure |
| SBO not incrementing under coherency workload | Counter path broken or wrong metric |
| SBO threshold too low | Spurious boosts; CCF never drops to low-power |
| SBO threshold too high | CCF under-boosts; coherency stalls under load |

---

## Section 7: Security / Safety / Policy

- TPMI registers may be locked by BIOS before OS handoff; runtime writes require BIOS unlock
- Distress thresholds should be validated against platform power policy to avoid CCF frequency instability
- PMON counter access requires appropriate privilege level (OS/VMM controlled)

---

## Section 8: References

- [CBB Telemetry Aggregator HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details)
- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html)
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
