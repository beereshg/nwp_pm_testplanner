# TCD: CBB CCF CBO Telemetry

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421194](https://hsdes.intel.com/appstore/article-one/#/22022421194) |
| **Title** | CBB CCF CBO Telemetry |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420514 -- CBB CCF Ring Frequency Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) |
| **Feature** | CBB CCF Ring Frequency Scalability |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB CCF CBO Telemetry** captures CBO (Cache Box) mesh traffic — cache lookup rates, read/write bandwidth, and miss rates — and feeds these values into the CBB PCode CCF DVFS slow-loop (~1 ms period). The BW threshold LUT walk uses CBO traffic intensity to decide when to boost or reduce the CCF ring frequency.

### CBO Telemetry Flow

1. CBO mesh counters accumulate per-cycle (RD/WR transactions)
2. CBB PCode slow-loop reads CBO counters each ~1 ms
3. BW threshold LUT walk: compare current BW to pre-configured thresholds
4. If BW above threshold → request CCF frequency increase via GVFSM
5. If BW below low threshold for N loops → reduce CCF frequency

### NWP Context

- NWP: 2 CBBs x 48 cores; CBO telemetry per-CBB and independent
- HPM 0x35 (`MEM_BOUND_CYCLES`) carries memory-bound fraction to Primecode for ELC

### Block Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     CBB Die (~1 ms slow-loop)                            │
│                                                                          │
│  ┌───────────────────┐     ┌────────────────────────────────────────┐    │
│  │  CBO Mesh         │     │  CBB PCode Slow-Loop                  │    │
│  │  (48 cache boxes) │────►│  1. Read CBO RD/WR counters           │    │
│  │                   │     │  2. BW threshold LUT walk             │    │
│  │ RD/WR transactions│     │  3. Compute CCF freq target           │    │
│  └───────────────────┘     └───────────────┬────────────────────────┘    │
│                                           │                              │
│              ┌────────────────────────────┘                              │
│              │                                                           │
│   ┌──────────▼──────────┐   ┌─────────────────────────────────────────┐  │
│   │  GVFSM              │   │  HPM 0x35 → Primecode (IMH/NIO)         │  │
│   │  CCF frequency      │   │  MEM_BOUND_CYCLES  → ELC Low decision  │  │
│   │  transition         │   │  TOTAL_ACTIVE_CYCLES                    │  │
│   └──────────┬──────────┘   └─────────────────────────────────────────┘  │
│              │                                                           │
│   ┌──────────▼──────────┐                                                │
│   │ UFS_STATUS           │  ◄── Observed via sv.socket0.cbbN.base.tpmi  │
│   │ CURRENT_RATIO        │                                               │
│   └─────────────────────┘                                                │
└──────────────────────────────────────────────────────────────────────────┘
```

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422889 -- CBB CCF CBO Telemetry](https://hsdes.intel.com/appstore/article-one/#/22022422889) | Counter correctness, DVFS response | CBO counters increment, CCF ratio responds to BW demand |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| CBO counters | CBB TPMI / GPSB | Per-CBB cache BW measurement |
| HPM 0x35 | `MEM_BOUND_CYCLES` | Memory-bound fraction to Primecode ELC |
| UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status.current_ratio` | CCF frequency response to CBO BW |
| UFS_ADV_CONTROL | `sv.socket0.cbbN.base.tpmi.ufs_adv_control_1` | BW threshold slope/base for CCF |

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

CBO telemetry is sampled by CBB PCode every slow-loop cycle (~1 ms). The BW decision is hysteretic: N consecutive loops above threshold before frequency increase, M consecutive below before decrease. This prevents oscillation under bursty traffic.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| CBO idle (no cache traffic) | Telemetry near-zero; CCF at low-power freq |
| Memory-bound workload | MEM_BOUND_CYCLES high; ELC High activates |
| BW spike shorter than 1ms | May not trigger CCF boost (below slow-loop resolution) |

---

## Section 7: Security / Safety / Policy

- TPMI registers may be locked by BIOS before OS handoff; runtime writes require BIOS unlock
- Distress thresholds should be validated against platform power policy to avoid CCF frequency instability
- PMON counter access requires appropriate privilege level (OS/VMM controlled)

---

## Section 8: References

- [CBB Telemetry Aggregator HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details)
- [Fabric DVFS HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html)
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
