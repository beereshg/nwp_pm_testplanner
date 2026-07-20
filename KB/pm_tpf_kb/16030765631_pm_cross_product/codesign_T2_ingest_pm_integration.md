# Co-Design T2 Ingest — PM Integration Testing (TPF 22022562325)

**Date:** 2026-07-20
**TPF:** 22022562325 — PM Integration Testing
**Parent TP:** 16030765631 — [NWP PM] PM Cross Product

## Query 1: NWP PM cross-product stress testing methodology

### Key Findings

1. **Cross-product scenarios** validate PM feature interactions across IPs, stacks, and domains:
   - Reset × PM state transitions (Q-ch/P-ch handshakes, supply sequencing)
   - Power domain crossings (NIO ↔ CBB, NIO ↔ C2C stack)
   - Feature interactions (clock gating + idle indication + DVFS)
   - Supply sequencing order enforcement
   - ACPI state transitions (G3, S0, S5)

2. **Three-tool integration methodology:**
   - **PMX Stress:** Directed, deterministic — rapidly toggles power states, clock gating across domains
   - **Solar Random PM:** Randomized — injects unpredictable PM events to find corner cases
   - **Sideband Harasser:** Injects noise/spurious events on sideband signals during PM transitions

3. **Domains covered:**
   - NIO (IMH) SoC power domains (core, uncore, memory, IO)
   - CBB domains (power + clock, reused from DMR with NWP mods)
   - C2C stack (wrapper, idle indication aggregation, clock gating)
   - Platform (ACPI states, supply sequencing)
   - Reset (warm/surprise reset + PM interactions)
   - Sideband/Debug (debug overrides, clock gating disable, sideband robustness)

## Query 2: RAPL/RACL/PC6/HWP interaction bug classes

### NWP Feature Support Status

| Feature | NWP Status |
|---|---|
| Socket RAPL | Supported |
| Fast RAPL | Supported |
| RACL | Supported |
| Platform RAPL (Psys) | NOT supported (fused off) |
| DRAM RAPL | NOT supported (fused off) |
| PkgC6 | NOT supported (fused off) |
| Core C-states | C0, C1, C1e, C6 |
| HWP / DVFS / Legacy P-states | Supported |

### Key Bug Classes

1. **Priority inversion / frequency arbitration** — RACL limits one partition; incorrect propagation
2. **Race conditions during state transitions** — C6 exit storm power spike, HWP/DVFS/RAPL sync
3. **Incorrect limit enforcement** — RAPL/RACL not propagated to all cores/partitions
4. **Telemetry mismatches** — LEAF_PERF_STATUS / PLR not reflecting actual limiter
5. **Reset initialization** — RAPL/RACL state machines not reinitializing after warm/cold reset

### Key Interaction Summary

| Feature 1 | Feature 2 | Interaction |
|---|---|---|
| RAPL | RACL | Arbitration: min freq enforced; partition-level throttling |
| RAPL/RACL | DVFS/HWP | Frequency requests clipped by active limiters |
| RAPL/RACL | C-state | C6 relaxes limits; C6 exit causes spikes |
| RAPL/RACL | Legacy P-state | Legacy requests must be clipped |
| RAPL/RACL | Reset | Limits must re-initialize correctly |
| HWP | Legacy P-state | OS/HW arbitration, both subject to limits |
