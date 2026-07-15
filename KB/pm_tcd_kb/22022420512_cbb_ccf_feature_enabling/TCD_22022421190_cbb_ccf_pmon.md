# TCD: CBB CCF PMON

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421190](https://hsdes.intel.com/appstore/article-one/#/22022421190) |
| **Title** | CBB CCF PMON |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TP** | [22022420512 -- CBB CCF Ring Scalability Feature Enabling](https://hsdes.intel.com/appstore/article-one/#/22022420512) |
| **Validation Phase** | **Alpha** — Feature enabling / path clearing (interface sanity check) |
| **Feature** | CBB CCF Ring Frequency Scalability |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB CCF PMON** provides hardware performance monitoring of the CBB CCF (Coherent Compute Fabric) ring. PMON counters measure ring activity: bandwidth utilization, snoop traffic rates, stall cycles, and frequency-state occupancy. On NWP, PMON is the primary tool for CCF ring performance characterization.

### PMON Counter Types

| Counter | Source | Measures |
|---------|--------|---------|
| CBO Lookup | Cache Box (CBO) | Cache lookup rate, miss rate, demand BW |
| SBO Snoop | Snoop Back-pressure Oracle | Snoop back-pressure occupancy |
| CLR PMON | CCF ring cluster | Ring bandwidth, transaction count |
| Fast C3 Residency | CCF PMA | Cycles in Fast Ring C3 (power-gated Uclk) |

### NWP-Specific Context

- NWP: 2 CBBs x 48 cores = 96 total; each CBB has independent PMON counters
- CCF ring target: 2.2 GHz (ratio 0x16) for full 460 GB/s bandwidth
- PMON counters are inputs to the CCF DVFS BW heuristics and distress algorithm
- Fast C3 residency counter: unique to NWP PMA; not present on DMR in same form

### Block Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CBB Die                                          │
│                                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐    ┌─────────────────────┐ │
│  │  CBO     │   │  SBO     │   │  CLR     │    │  CCF PMA            │ │
│  │ (Cache   │   │ (Snoop   │   │ (Ring    │    │ Fast C3 Residency   │ │
│  │  Box)    │   │  Back-   │   │  Cluster)│    │ Counter             │ │
│  │ Lookup   │   │  pressure│   │  PMON    │    │                     │ │
│  │ Counters │   │ Counter) │   │  Unit    │    │ cfcclk_qactive=0    │ │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘    └──────────┬──────────┘ │
│       │              │              │                      │            │
│       └──────────────┴──────────────┴──────────────────────┘            │
│                              │                                          │
│                    ┌─────────▼─────────┐                                │
│                    │  CBB PCode PMON   │                                │
│                    │  Event Mux        │                                │
│                    │  Counter Array    │                                │
│                    └─────────┬─────────┘                                │
│                              │                                          │
│                    ┌─────────▼─────────┐                                │
│                    │  TPMI / MSR Read  │◄─── PythonSV / OS PMU         │
│                    │  (per-CBB)        │     sv.socket0.cbbN.base.tpmi │
│                    └───────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────┘
```

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422886 -- CBB CCF PMON](https://hsdes.intel.com/appstore/article-one/#/22022422886) | Counter correctness | Increment under workload, event mux, per-CBB independence |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| PMON MSR | Per-core MSR (event select) | Program PMON event source |
| CBB TPMI | `sv.socket0.cbbN.base.tpmi.ufs_status` | Current CCF ratio during PMON observation |
| CBB GPSB | `sv.socket0.cbbN.compute0.pma0.gpsb` | PMA telemetry including Fast C3 residency |
| HPM 0x35 | `ACTIVE_CYCLES_TELEMETRY` | MEM_BOUND_CYCLES delivered to Primecode |

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

PMON counters accumulate monotonically during ring activity. The Fast C3 residency counter increments only when `cfcclk_qactive=0` (Global Uclk tree gated). Counters must be reset via PMU control before each measurement window to avoid overflow confusion.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Counter overflow (32-bit wrap) | Software must handle rollover; clear before measurement window |
| Zero counter at idle | Expected for BW/snoop counters; Fast C3 counter may be non-zero |
| PMON event not connected to CCF | Zero count even under high load -- indicates wrong event select |

---

## Section 7: Security / Safety / Policy

- TPMI registers may be locked by BIOS before OS handoff; runtime writes require BIOS unlock
- Distress thresholds should be validated against platform power policy to avoid CCF frequency instability
- PMON counter access requires appropriate privilege level (OS/VMM controlled)

---

## Section 8: References

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details)
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
