# TCD: CCB CCF PCODE Algorithm for Distress Input

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421205](https://hsdes.intel.com/appstore/article-one/#/22022421205) |
| **Title** | CCB CCF PCODE Algorithm for Distress Input |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420514 -- CBB CCF Ring Frequency Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) |
| **Feature** | CBB CCF Ring Frequency Scalability |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB PCode Distress Algorithm** processes distress inputs (SBO back-pressure and CBO occupancy) and converts them into CCF GVFSM frequency-boost decisions using threshold-based hysteresis. The algorithm prevents CCF frequency thrashing under bursty workloads while ensuring rapid response to sustained congestion.

### Algorithm Logic

```
Each slow-loop (~1 ms):
  distress_level = max(SBO_occupancy, CBO_pressure)
  if distress_level > HIGH_THRESHOLD for N_ON consecutive loops:
    request CCF boost to P0 (2.2 GHz)
  elif distress_level < LOW_THRESHOLD for N_OFF consecutive loops:
    return to autonomous BW-heuristic-driven freq
  else:
    hold current freq (hysteresis window)
```

### Hysteresis Parameters

| Parameter | Controls | Effect |
|-----------|---------|--------|
| HIGH_THRESHOLD | Distress assertion | Above: triggers boost |
| LOW_THRESHOLD | Distress de-assertion | Below for N loops: boost removed |
| N_ON | Assertion latency | Loops above threshold before boost fires |
| N_OFF | De-assertion hold | Loops below threshold before boost removed |

### Block Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│  CBB PCode Distress Algorithm (runs each ~1 ms slow-loop)                │
│                                                                          │
│   SBO_occupancy ──┐                                                      │
│                   ├──► max() or weighted-sum ──► distress_level          │
│   CBO_pressure ───┘                                  │                  │
│                                                      │                  │
│                              ┌───────────────────────▼────────────────┐ │
│                              │  Threshold Comparator                  │ │
│                              │                                        │ │
│                              │  distress_level > HIGH_THRESHOLD?      │ │
│                              │      Yes (N_ON loops) → BOOST          │ │
│                              │      No                                │ │
│                              │  distress_level < LOW_THRESHOLD?       │ │
│                              │      Yes (N_OFF loops) → RAMP DOWN     │ │
│                              │      No → HOLD current freq            │ │
│                              └───────────────────┬────────────────────┘ │
│                                                  │                      │
│              ┌───────────────────────────────────┘                      │
│              │                                                          │
│   ┌──────────▼─────────────┐    ┌────────────────────────────────────┐  │
│   │  GVFSM                 │    │  HPM 0x1b                          │  │
│   │  CCF ring freq boost   │    │  UPSTREAM_CCF_DESIRED_RATIO        │  │
│   │  → P0 (2.2 GHz) at max │    │  → IMH/NIO Primecode               │  │
│   └────────────────────────┘    └────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
        N_ON/N_OFF hysteresis prevents frequency oscillation
```

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422905 -- CBB CCF PCODE Algorithm](https://hsdes.intel.com/appstore/article-one/#/22022422905) | Threshold, hysteresis, magnitude | Controlled load ramp, oscillation test |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| UFS_ADV_CONTROL_1/2 | Slope, base, threshold fields | Distress threshold programming |
| SBO counter | CBB GPSB | Primary distress input |
| HPM 0x1b | `UPSTREAM_CCF_DESIRED_RATIO` | Algorithm output to Primecode |
| UFS_STATUS | `current_ratio` | Observable algorithm output |

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

The distress algorithm runs as part of the CBB PCode slow-loop. It combines SBO and CBO inputs via a max() or weighted-sum function (implementation-defined). The output is an updated `UPSTREAM_CCF_DESIRED_RATIO` in HPM 0x1b. The algorithm must be validated to prevent both under-response (too slow to relieve congestion) and oscillation (frequency thrashing).

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Below threshold (both SBO and CBO) | No boost; algorithm in steady-state |
| Rapid load oscillation at 10 Hz | Algorithm holds boost through oscillation (hysteresis prevents thrashing) |
| Max distress (both inputs at max) | CCF boosted to P0 (2.2 GHz); full boost magnitude |
| Only one input above threshold | Algorithm may still boost if that input is above HIGH_THRESHOLD |

---

## Section 7: Security / Safety / Policy

- TPMI registers may be locked by BIOS before OS handoff; runtime writes require BIOS unlock
- Distress thresholds should be validated against platform power policy to avoid CCF frequency instability
- PMON counter access requires appropriate privilege level (OS/VMM controlled)

---

## Section 8: References

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html)
- [CBB Telemetry Aggregator HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details)
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
