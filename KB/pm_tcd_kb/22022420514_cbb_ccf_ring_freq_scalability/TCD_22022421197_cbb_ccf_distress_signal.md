# TCD: CBB CCF Distress Signal

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421197](https://hsdes.intel.com/appstore/article-one/#/22022421197) |
| **Title** | CBB CCF Distress Signal |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420514 -- CBB CCF Ring Frequency Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) |
| **Feature** | CBB CCF Ring Frequency Scalability |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB CCF Distress Signal** is generated when the CCF ring is congested: high SBO (snoop back-pressure) occupancy or high CBO miss rates cause CBB PCode to assert a distress signal to IMH/NIO Primecode via an HPM message. Primecode responds by requesting a CCF frequency boost, which CBB GVFSM fulfills.

### Distress Signal Flow

```
CCF congestion (SBO high / CBO pressure)
  -> CBB PCode threshold exceeded
  -> Distress bit asserted in HPM 0x1b (UPSTREAM_CCF_DESIRED_RATIO boosted)
  -> IMH Primecode receives HPM message
  -> IMH updates CCF frequency request
  -> CBB GVFSM receives boosted target, transitions to higher ratio
  -> Congestion relieves -> distress clears (hysteresis)
```

### Distress Threshold Behavior

- Distress only fires when SBO occupancy > configured threshold for hysteresis window
- De-asserts after N slow-loops below threshold (prevents oscillation)
- Per-CBB: each CBB generates distress independently based on its own congestion

### Block Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│  CCF Congestion Path                                                     │
│                                                                          │
│  ┌──────────────┐    ┌─────────────┐    ┌──────────────────────────────┐ │
│  │  96 Cores    │───►│  CCF Ring   │───►│  Back-pressure detected      │ │
│  │  (2 CBBs)    │    │  Congested  │    │  SBO occupancy > threshold   │ │
│  │  high snoop  │    │  Snoop BW   │    │  CBO miss rate high          │ │
│  └──────────────┘    │  saturated  │    └──────────────┬───────────────┘ │
│                      └─────────────┘                   │                │
│                                                        │                │
│                              ┌─────────────────────────┘                │
│                              │                                          │
│                    ┌─────────▼──────────┐                               │
│                    │  CBB PCode         │                               │
│                    │  Distress Assert   │ ──── HPM 0x1b ────────────►  │
│                    │  UPSTREAM_CCF_     │         │                     │
│                    │  DESIRED_RATIO↑    │         │                     │
│                    └────────────────────┘         │                     │
│                                                   │                     │
└───────────────────────────────────────────────────┼─────────────────────┘
                                                    │
┌───────────────────────────────────────────────────▼─────────────────────┐
│  IMH / NIO (Primecode)                                                   │
│  Receives HPM 0x1b → updates CCF freq request → CBB GVFSM boosts ratio  │
└──────────────────────────────────────────────────────────────────────────┘
```

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422894 -- CBB CCF Distress Signal](https://hsdes.intel.com/appstore/article-one/#/22022422894) | Distress assert/deassert, IMH response | Congestion injection, HPM delivery, freq boost |
| [22022422895 -- CBB CCF Snoop Scalability/Distress](https://hsdes.intel.com/appstore/article-one/#/22022422895) | Snoop throughput scaling | 96-core coherency workload, distress under full load |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| HPM 0x1b | `UPSTREAM_CCF_DESIRED_RATIO` | Distress-boosted CCF freq request to Primecode |
| SBO counter | CBB GPSB / TPMI | Snoop back-pressure measurement driving distress |
| UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status.current_ratio` | CCF ratio after distress boost |
| PLR_DIE_LEVEL | `sv.socket0.cbbN.base.tpmi.plr_die_level` | Perf Limit Reason (must be 0x0 during clean operation) |

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

Distress signal has hysteresis to prevent frequency thrashing: N loops above threshold to assert, M loops below to de-assert. Under sustained high-coherency workload (96 cores, NWP), the CCF ring should stabilize at or near P0 (2.2 GHz). Distress is CBB-scoped; cbb0 and cbb1 operate independently.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Distress at idle | False positive -- threshold too low or SBO counter stuck |
| No distress under max load | Threshold too high or HPM path broken |
| Distress stuck after workload ends | Hysteresis timer not expiring; check threshold config |
| Both CBBs distress together | Cross-CBB coupling -- distress not per-CBB scoped |

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
