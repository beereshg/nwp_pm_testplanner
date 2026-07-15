# TCD: CBB CCF HPM Messages to Primecode

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421199](https://hsdes.intel.com/appstore/article-one/#/22022421199) |
| **Title** | CBB CCF Message To Punit *(HSD title; content describes CBB → IMH/NIO Primecode HPM messages)* |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420514 -- CBB CCF Ring Frequency Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) |
| **Feature** | CBB CCF Ring Frequency Scalability |
| **KB last updated** | 2026-07-10 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB CCF HPM Messages to Primecode** validates the HPM (Hierarchical Power Management) cross-die message channel from **CBB PCode to IMH/NIO Primecode**. This TCD is a **cross-die interface validation** — it is distinct from the local ring-scalability distress feature (TCD 22022421197) which tests CBB-local congestion detection and GV response. This TCD tests whether the correct values are generated, transported, and consumed by Primecode for its **Fabric DVFS** and **ELC** decisions.

> **Title note**: The HSD title says "Message To Punit" but the feature is CBB PCode → IMH/NIO **Primecode**, not the CBB-local PUNIT. The "Punit" in the title refers to Primecode (the IMH PM controller), not the CBB-local PUnit.

Three key HPM messages carry CBB state for Primecode ELC and fabric DVFS decisions:

### HPM Message Summary

| HPM | Name | Content | Primecode Use |
|-----|------|---------|--------------|
| 0x1b | CBB_CCF_FREQUENCY | `UPSTREAM_CCF_DESIRED_RATIO`, `DOWNSTREAM_CCF_RESOLVED_MIN_RATIO` | Fabric DVFS — Primecode takes **max(all CBB desired ratios)** as the CCF floor and distributes it back as `DOWNSTREAM_CCF_RESOLVED_MIN_RATIO` |
| 0x35 | ACTIVE_CYCLES_TELEMETRY | `MEM_BOUND_CYCLES`, `TOTAL_ACTIVE_CYCLES` | ELC: memory-bound fraction for ELC Low decision |
| 0x36 | MOST_ACTIVE_CORE_C0_TELEMETRY | `CORE_C0_TIME`, `TOTAL_TIME` | ELC High/Mid: C0 utilization input |

### Uniform CBB Mode

When `UFS_CONTROL.UNIFORM_CBB_FABRIC_FREQ_MODE=1`, HPM 0x1b coordinates CCF frequency across all CBBs via Primecode:
- Each CBB sends its **desired CCF ratio** (the minimum ratio it needs) via `UPSTREAM_CCF_DESIRED_RATIO`
- Primecode resolves the **maximum** of all CBB desired ratios — this is the highest demand that must be satisfied by the whole fabric
- Primecode distributes this floor back to all CBBs as `DOWNSTREAM_CCF_RESOLVED_MIN_RATIO`
- Result: all CBBs run at or above the most demanding CBB's requested ratio

In non-Uniform mode, each CBB manages its own CCF GV locally without cross-CBB coordination.

### Block Diagram

```
┌──────────────────────┐         ┌──────────────────────────────────────────┐
│  CBB PCode (each CBB)│         │  IMH / NIO Primecode                     │
│                      │         │                                          │
│  ┌────────────────┐  │         │  ┌──────────────────────────────────┐    │
│  │ CCF GV Decision│  │HPM 0x1b │  │ Fabric DVFS Slow-Loop            │    │
│  │ UPSTREAM_CCF_  ├──┼────────►├──┤ max(all CBB desired ratios)      │    │
│  │ DESIRED_RATIO  │  │◄────────┼──┤ → DOWNSTREAM_RESOLVED_MIN_RATIO  │    │
│  └────────────────┘  │         │  └──────────────────────────────────┘    │
│                      │         │                                          │
│  ┌────────────────┐  │HPM 0x35 │  ┌──────────────────────────────────┐    │
│  │ Memory BW      ├──┼────────►├──┤ ELC Low decision                 │    │
│  │ MEM_BOUND_     │  │         │  │ MEM_BOUND_CYCLES / TOTAL         │    │
│  │ CYCLES         │  │         │  └──────────────────────────────────┘    │
│  └────────────────┘  │         │                                          │
│                      │HPM 0x36 │  ┌──────────────────────────────────┐    │
│  ┌────────────────┐  │         │  │ ELC High/Mid decision            │    │
│  │ C0 Utilization ├──┼────────►├──┤ CORE_C0_TIME / TOTAL_TIME       │    │
│  │ CORE_C0_TIME   │  │         │  └──────────────────────────────────┘    │
│  └────────────────┘  │         │                                          │
└──────────────────────┘         └──────────────────────────────────────────┘
```

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422896 -- CBB CCF Message To Punit](https://hsdes.intel.com/appstore/article-one/#/22022422896) | HPM correctness, ELC response | HPM content verification, ELC High activation |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| HPM 0x1b | `UPSTREAM_CCF_DESIRED_RATIO` [7:0] | CBB CCF freq request to Primecode |
| HPM 0x35 | `MEM_BOUND_CYCLES` [31:0], `TOTAL_ACTIVE_CYCLES` [63:32] | Memory-bound fraction |
| HPM 0x36 | `CORE_C0_TIME` [31:0], `TOTAL_TIME` [63:32] | C0 utilization for ELC |
| UFS_CONTROL | `UNIFORM_CBB_FABRIC_FREQ_MODE` [30] | Enable Uniform mode |

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

HPM messages are sent each CBB slow-loop (~1 ms). Under Uniform mode:
- Each CBB sends its `UPSTREAM_CCF_DESIRED_RATIO` via HPM 0x1b
- Primecode takes the **maximum** of all CBB desired ratios — the highest CCF frequency demand in the system
- This maximum is distributed back to all CBBs as `DOWNSTREAM_CCF_RESOLVED_MIN_RATIO` — the floor all CBBs must meet

Under non-Uniform mode, each CBB manages CCF independently. HPM 0x35 (`MEM_BOUND_CYCLES`) and 0x36 (`CORE_C0_TIME`) are sampled per slow-loop and used by Primecode's ELC algorithm to determine whether ELC Low (memory-bound) or ELC High/Mid (compute-bound) conditions apply.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| HPM message not received by Primecode | CCF not responding to BW -- check HPM infrastructure |
| HPM 0x36 stale (not updating) | ELC High mode never activates under full load |
| Uniform mode CBBs disagree | Resolved ratio wrong -- HPM aggregation error |

---

## Section 7: Security / Safety / Policy

- TPMI registers may be locked by BIOS before OS handoff; runtime writes require BIOS unlock
- Distress thresholds should be validated against platform power policy to avoid CCF frequency instability
- PMON counter access requires appropriate privilege level (OS/VMM controlled)

---

## Section 8: References

- [HPM Message Specification](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html)
- [Fabric DVFS HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html)
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
