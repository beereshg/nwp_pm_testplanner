# Fabric DVFS > DVFS

> **Status**: Enriched — full touchpoint enrichment (2026-05-28)
> **Parent**: [Fabric DVFS](fabric_dvfs_main.md)

## Baseline (DMR)

Fabric DVFS (also called **Uncore Frequency Scaling / UFS** or **FabricGV**) autonomously scales frequency and voltage across **3 independent fabric domains** per IMH die — IO Fabric (CFCIO, 400–2000 MHz), Memory Fabric (CFCMEM, 800–2000 MHz), and CBB CCF Ring (PCode-managed) — based on real-time bandwidth telemetry from mesh, memory controller, UBR, and D2D counters.

**Topology:** Each IMH die contains IO and Memory fabric domains managed by Primecode (IMH Punit). Memory Fabric is coordinated across IMH-P (root) and IMH-S (leaf) via HPM 0x22. CBB CCF Ring is managed independently per CBB by PCode, with opt-in coordination via HPM 0x1b (Uniform CBB Fabric Frequency mode). UCIe D2D PHY provides handshake for Memory Fabric GV only; IO Fabric requires no D2D handshake.

**Key operational principle:** Each slow-loop iteration (~1 ms), Primecode walks 6-level BW threshold LUTs per traffic type (MC RD/WR, CMS, CRS, UBR, D2D), resolves `max(mem_bw, ring_bw, mem_bound, D2D)` for Memory Fabric and `max(all 13 IO traffic types)` for IO Fabric, then clips results through the RAPL/RACL line equation (anchored at coreP1). A `bias_detector()` switches between IO-bias and CCF-bias memory frequency lines based on IO bandwidth levels. An HW-triggered IO Demand fastpath (<1 ms) rockets both fabrics to 1.8 GHz when MIO A2F ASF detects incoming IO traffic. ELC modes (Low/Mid/High) add a C0-utilization-driven floor/boost layer.

**Boot activation:** TPMI_INIT (PH1.x reset sequence) programs UFS_HEADER and UFS_CONTROL. BIOS programs ELC threshold fields and LOM/OPM mode before OS handoff. BW heuristics begin at the first slow-loop after boot.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| LJPLL (mem-uclk, io-uclk) | IMH | Fabric clock synthesis for CFCIO and CFCMEM; slow-drifting PLL | PLL ratio change: V-first (freq up); PLL-first (freq down) | DMR Fabric DVFS HAS v1.09 |
| FIVR (VCCCFCIO, VCCCFCMEM_E/W) | IMH | Per-domain voltage control; GV coordinated with LJPLL; East+West updated for Mem | FIVR voltage ramp; enable/disable | DMR Fabric DVFS HAS v1.09 |
| Resource Controller (RC) / Resource Adapter (RA) | IMH | GV arbitration; Primecode SCU → RC → RA SB transaction → FIVR + PLL; RA waits for UCIe ack | SB transaction; FIVR+LJPLL coordination | DMR Fabric DVFS HAS v1.09 |
| UCIe D2D PHY | IMH ↔ CBB | Memory Fabric GV handshake: v_change_request/ack + f_change_request/ack per stack; IO fabric has no D2D handshake | v_change_req, v_change_ack, f_change_req, f_change_ack | DMR Fabric DVFS HAS v1.09 |
| MIO A2F ASF | IMH | IO Demand fastpath trigger: detects IO traffic above threshold; fires edge to Punit fclk | ASF watermark assert; edge detect on fclk | FAS SERVERPMFW-2393 |
| SCF / CMS / CRS | IMH | IO and Memory mesh traffic counter telemetry (BW heuristics input) | CMS_MAX_TRAFFIC_COUNT, CRS_MAX_TRAFFIC_COUNT | DMR Fabric DVFS HAS v1.09 |
| UBR (UIO) | IMH | Per-agent IO BW counters (HIOP, IOMMU, CXL, UXI; req and data, A2F/F2A) | UBR_A2F_REQ/DATA_BW_COUNTER_{HIOP,IOMMU,CXL,UXI} | DMR Fabric DVFS HAS v1.09 |
| MC (Memory Controller) | IMH | DRAM RD/WR CAS count telemetry for Mem Fabric BW heuristics | MC_RDDATA_COUNT, MC_WRDATA_COUNT per channel | DMR Fabric DVFS HAS v1.09 |
| TPMI | IMH + CBB | OS-visible register interface per cluster (IMH: ID0=IO, ID1=Mem; CBB: ID0=CCF) | TPMI opcode; OOBMSM bridge | DMR Fabric DVFS HAS v1.09 |
| CBB CCF PLL + FIVR | CBB | CCF ring clock and voltage; managed by CBB PCode independently; sends CCF_DESIRED_RATIO via HPM 0x1b | CBB GVFSM; CCF desired ratio register | CBB PM HAS |
| HSF PLL | IMH | Coupled with Memory Fabric: 800 MHz @ Pn, 1.7 GHz boot ratio otherwise | HSF DFS coupling from Primecode | DMR Fabric DVFS HAS v1.09 |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Primecode (IMH Punit) | IMH | Mem + IO Fabric DVFS: BW heuristics slow-loop, RAPL/RACL line clip, bias_detector, IO Demand fastpath handler, HSF DFS, UFS_DISABLE fuse handling, cross-IMH coordination via HPM 0x22 | `mem_ufs_slow_loop()`; `io_ufs_slow_loop()`; `io_demand_fp_handler()`; `bias_detector()`; `ufs_init()` | `src/flow/ufs/` |
| PCode (CBB Punit) | CBB | CCF ring DVFS: autonomous freq/voltage via GVFSM; sends CCF_DESIRED_RATIO via HPM 0x1b; applies global resolved min; ELC Low per-CBB; RAPL CCF mesh boost line | CCF GV execution (GVFSM); HPM 0x1b Tx/Rx; ELC Low | `source/pcode/flows/autonomous_pstate/` |
| BIOS / UEFI | Platform | TPMI_INIT: UFS_HEADER/CONTROL init, ELC field programming, LOM/OPM mode; UFS_DISABLE fuse check | TPMI register init sequence; LOM/OPM BIOS knob | HSD 16029560555 |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| TPMI UFS_HEADER | Cluster offset 0x00 | RO | INTERFACE_VERSION=0x03, AUTONOMOUS_UFS_DISABLED, LOCAL_FABRIC_CLUSTER_ID_MASK, RATIO_UNIT (100 MHz) | DMR Fabric DVFS HAS v1.09 |
| TPMI UFS_STATUS | Cluster offset 0x00 | RO | CURRENT_RATIO [6:0], CURRENT_VOLTAGE [22:7] (U3.13), AGENT_TYPE flags, THROTTLE_COUNTER [63:32] | DMR Fabric DVFS HAS v1.09 |
| TPMI UFS_CONTROL | Cluster offset 0x01 | RW | UFS_THROTTLE_MODE [1:0], MAX_RATIO [14:8], MIN_RATIO [21:15], ELC_LOW_RATIO [28:22], UNIFORM_CBB_FABRIC_FREQ_MODE [30], ELC_LOW/HIGH_THRESHOLD, ELC_MID_RATIO [63:57] | DMR Fabric DVFS HAS v1.09 |
| TPMI UFS_ADV_CONTROL_1 | Cluster offset 0x02 | RW | SLOPE_1 [7:0] (S2.3), BASE_1 [15:8] (S7.0) — CCF Line / IO Line / CCF-bias Mem Line | DMR Fabric DVFS HAS v1.09 |
| TPMI UFS_ADV_CONTROL_2 | Cluster offset 0x03 | RW | SLOPE_2, BASE_2 — IO-bias Mem Line; UTILIZATION_THRESHOLD, HBM_BW_THRESHOLD | DMR Fabric DVFS HAS v1.09 |
| HPM 0x22 UFS_FREQUENCY | Root↔Leaf IMH | HPM | MEM_FABRIC_TARGET_RATIO, IO_FABRIC_TARGET_RATIO — cross-IMH Memory Fabric coordination | HPM Message Spec |
| HPM 0x35 ACTIVE_CYCLES_TELEMETRY | CBB→IMH | HPM | MEM_BOUND_CYCLES [39:16] (>>8), TOTAL_ACTIVE_CYCLES [63:40] (>>8) — Memory-bound ratio input | HPM Message Spec |
| HPM 0x36 MOST_ACTIVE_CORE_C0_TELEMETRY | CBB→IMH | HPM | CORE_C0_TIME [39:16], TOTAL_TIME [63:40] — ELC C0 utilization input | HPM Message Spec |
| HPM 0x1b CBB_CCF_FREQUENCY | CBB↔IMH | HPM | UPSTREAM_CCF_DESIRED_RATIO, DOWNSTREAM_CCF_RESOLVED_MIN_RATIO — Uniform CBB Fabric Frequency mode | HPM Message Spec |
| HPM 0x14-0x15 RAPL_PERF_LIMIT | IMH-P→all | HPM | RAPL_PID_FREQ_OUTPUT [63:56], RACL_PID_FREQ_OUTPUT [55:48] — consumed for RAPL/RACL line input | HPM Message Spec |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| UFS slow-loop period | ~1 | ms | BW heuristics + RAPL line + bias_detector executed each slow loop | DMR Fabric DVFS HAS v1.09 |
| IO Demand fastpath latency | < 1 | ms | MIO A2F ASF edge → FP handler → rocket IO+Mem to 1.8 GHz | FAS SERVERPMFW-2393 |
| IO Demand timer hold-off (default) | 2 | ms | IO_DEMAND_TIMER: hold rocketed freq before de-rocket via HPM 0x22 | DMR Fabric DVFS HAS v1.09 |
| IO Fabric freq range | 400 – 2000 | MHz | 400 MHz only when no IOs connected; P0 = 2.0 GHz | DMR Fabric DVFS HAS v1.09 |
| Memory Fabric freq range | 800 – 2000 | MHz | Pn = 800 MHz; P0 = 2.0 GHz | DMR Fabric DVFS HAS v1.09 |
| ELC Low C0 threshold (default) | 10 | % | Below: floor all fabrics at ELC_LOW_RATIO (1.2 GHz IO/Mem, 0.8 GHz CCF) | DMR Fabric DVFS HAS v1.09 |
| ELC High C0 threshold (default) | 95 | % | Above (+ EPB=Perf + not RAPL-limited): +1 bin (100 MHz) per slow-loop iteration | DMR Fabric DVFS HAS v1.09 |
| BW threshold LUT depth | 6 | levels | Per traffic type: MEM_FABRIC_MEMORY_BW_THRESHOLD[], IO_TRAFFIC_ROCKET_UP_THRESHOLD[] | DMR Fabric DVFS HAS v1.09 |
| HSF DFS coupling | 800 / 1700 | MHz | CFCMEM @ Pn → HSF 800 MHz; otherwise → HSF 1.7 GHz boot ratio | DMR Fabric DVFS HAS v1.09 |
| CCF ring freq target (NWP) | 2.2 | GHz | NWP must run CCF at 2.2 GHz for full BW (460 GB/s read+write) | NWP CBB HAS |
| D2D roundtrip latency (NWP) | 72 | cycles | @ 2 GHz; was 54 on DMR (16→32 GT/s PHY upgrade impact on GV handshake timing) | NWP CBB HAS |

## Legacy (Human-Curated Reference)

### Architecture Summary

Fabric DVFS autonomously scales frequency and voltage across **3 independent fabric domains** on each IMH die, plus the CBB CCF ring, based on real-time telemetry. It balances power efficiency against latency and bandwidth requirements — core-bound workloads get lower fabric frequencies (power savings), memory/IO-bound workloads get higher fabric frequencies (bandwidth).

### Three Fabric Domains (per IMH die)

| Domain | PLL | FIVR | Freq Range | Controller |
|--------|-----|------|------------|------------|
| **IO Fabric** (CFCIO) | Dedicated io-uclk LJPLL | VCCCFCIO | 400 MHz – 2.0 GHz (P0) | IMH Primecode |
| **Memory Fabric** (CFCMEM) | Shared mem-uclk LJPLL (East+West) | VCCCFCMEM_E + VCCCFCMEM_W | 800 MHz (Pn) – 2.0 GHz (P0) | IMH Primecode |
| **CCF Ring** (CBB) | CBB mesh PLL | CBB FIVR | Per CBB fuses | CBB Pcode |

- IO and Memory fabrics on the same IMH can run at **different frequencies** independently
- Memory fabric frequency is **aligned across IMH-P and IMH-S** via HPM 0x22 (root takes max of both IMH requests)
- IO fabric frequency is **per-die independent** — driven by local IO traffic
- 400 MHz IO mesh only available when no IOs connected to an IMH
- All use slow-drifting LJPLL for clock control; UCIe D2D PHY supports full fabric freq range

### Frequency Decision Pipeline

```
Telemetry Inputs              Heuristics               Resolution              Enforcement
┌───────────────┐     ┌──────────────────────┐    ┌──────────────────┐    ┌──────────────┐
│ CMS/CRS BW    │────►│ BW threshold freq    │───►│                  │    │              │
│ MC RD/WR      │────►│   selection (LUTs)   │    │ max(heuristic,   │    │ min(resolved,│
│ UBR D2D BW    │────►│                      │    │     ELC floor,   │    │   RAPL line, │
│ CBB mem_bound │────►│ Latency-based freq   │───►│     IO demand)   │───►│   thermal,   │───► WP
│ CBB C0_util   │────►│   (scalability)      │    │                  │    │   TPMI min/  │    CALC
│ IO demand FP  │────►│                      │    │                  │    │   max ratio)  │
│ RAPL PID out  │    │ ELC Low/Mid/High     │───►│                  │    │              │
└───────────────┘     └──────────────────────┘    └──────────────────┘    └──────────────┘
```

### Key DMR Deltas from GNR

- **3 fabric domains** instead of single mesh — IO, Memory, CCF ring are independent
- **D2D handshakes** for Memory Fabric GV via UCIe PHY (replaces GNR MDFI)
- **IO Demand fastpath** — HW fast-path with MIO A2F ASF watermark thresholding rockets IO/Mem fabric from LP state in <1ms
- **RAPL/RACL line connection** to IMH fabric frequencies — without this, IO-heavy Pmax.Max violates TDP. Must-have for product
- **Biased memory lines** — CCF-bias vs IO-bias memory frequency limit, with continuous `bias_detector()` switching
- **ELC modes** (Low/Mid/High) with CBB C0 utilization telemetry sent via HPM 0x36
- **Uniform CBB Fabric Frequency** mode — opt-in via TPMI bit, max-aggregates CCF ring freq across all CBBs
- **Perf P limit deprecated** — no inter-socket or die-to-die alignment needed
- **HSF DFS** — HSF PLL modulated with memory fabric (800 MHz when CFCMEM at Pn, 1.7 GHz otherwise)
- **MSR 0x620/0x621 deprecated** — TPMI is the only SW interface (same as GNR)

### Throttle Modes (UFS_CONTROL bits 1:0)

| Mode | min vs max | UFS Heuristics | RAPL Line | Use Case |
|------|-----------|----------------|-----------|----------|
| **0: Power Limited Ordered** (min=max) | Disabled | No | Latency-sensitive — fixed fabric freq |
| **0: Power Limited Ordered** (min<max) | Enabled | No | Autonomous within bounds, no RAPL throttle |
| **1: Power Limited Proportional** (min<max) | Enabled | Yes | Autonomous + RAPL proportional throttle |
| **1: Power Limited Proportional** (min=max) | Disabled | Yes | Fixed freq but RAPL proportional throttle |

---

### Execution Flow

### Memory Fabric DVFS (per-IMH, every slow loop ~1ms)

1. **CBB telemetry ingestion** — receive HPM 0x35 (`ACTIVE_CYCLES_TELEMETRY`) from each CBB. Compute max `MEMORY_BOUND_RATIO` and max `CBB_BOUND_RATIO` across CBBs
2. **Memory BW check** — for each MC channel, compute RD/WR delta counts → `UFS_MAX_MEMORY_TRAFFIC_DELTA_COUNT`. Walk through `MEM_FABRIC_MEMORY_BW_THRESHOLD[]` LUT (6 levels) to find `MEM_FABRIC_MEM_FREQ_REQ`. MCR vs DDR thresholds differ
3. **Mesh BW check** — compare `CMS_MAX_TRAFFIC_COUNT` delta against `FABRIC_RING_BW_UP/DN_THRESHOLD` (proportional to `current_mesh_ratio`). Walk through ring BW threshold LUT → `MEM_FABRIC_RING_FREQ_REQ`
4. **CBB memory-bound check** — if `MAX_MEMORY_BOUND_RATIO > MEMBOUND_THRESHOLD` (default 0.55), set `UP_DECISION_MASK.MEMORY_BOUND`, boost to `CBB_LATENCY_MEM_FABRIC_FREQ` (default 1.8 GHz)
5. **D2D BW check** — for each `UBR_D2D_TRAFFIC_TYPE` (REQ, NON_P2P_DATA, P2P_DATA), max across instances, walk through `UBR_D2D_UP_THRESHOLD[]` LUT (6 levels) → `MEM_FABRIC_D2D_FREQ_REQ`
6. **Resolve** — `MEM_FABRIC_FREQ_REQ = max(ring, mem, memory_bound, D2D)`
7. **HSF DFS** — if `MEM_FABRIC_FREQ_REQ == MEM_PN` (800 MHz) → HSF PLL to 800 MHz; else → HSF PLL to 1.7 GHz boot ratio
8. **RAPL/RACL line clipping** — compute `memFL` from bias_detector (see below), clip to `min(MEM_FABRIC_FREQ_REQ, memFL^)`
9. **Remote IMH coordination** — root IMH takes `max(local, remote)` via HPM 0x22 UFS_FREQUENCY, sends resolved freq back to leaf

### IO Fabric DVFS (per-IMH, every slow loop ~1ms)

1. **Telemetry collection** — for 13 IO traffic types (CMS, CRS, HIOP req/data, ACCEL req/data, IOMMU req, UXI_CXL req/data), compute max across instances, delta from previous
2. **Threshold walk** — for each traffic type with `ROCKET_ENABLE_MASK` bit set, walk through `IO_TRAFFIC_ROCKET_UP_THRESHOLD[]` LUT (6 levels) → `ROCKET_IO_FREQ[traffic_type]`
3. **Resolve** — `IO_FABRIC_FREQ_REQ = max(all ROCKET_IO_FREQ[traffic_type])`
4. **RAPL/RACL line clipping** — compute `ioFL` from IO line equation, clip to `min(IO_FABRIC_FREQ_REQ, ioFL^)`
5. No cross-IMH coordination needed for IO fabric (local only)

### RAPL/RACL → Fabric Frequency Limiting

This is a **must-have for DMR product** — without it, IO-heavy Pmax.Max scenarios violate TDP.

```
PIDout = min(RAPL_PID_FREQ_OUTPUT, RACL_PID_FREQ_OUTPUT)

IO Line:     ioFL  = io_base  + (io_slope  × PIDout)     // anchored at (coreP1, ioP0)
CCF Line:    ccfFL = ccf_base + (ccf_slope × PIDout)     // mimics CBB mesh boost
CCF-bias:    ccfBias_memFL = ccfBias_base + (ccfBias_slope × ccfFL)
IO-bias:     ioBias_memFL  = ioBias_base  + (ioBias_slope  × ioFL)

memFL = bias_detector(io2mem_BW, ioBias_memFL, ccfBias_memFL)
```

**Bias detector** — continuous function switching between IO-bias and CCF-bias memory lines based on `io2mem_BW` telemetry:
- `io2mem_BW ≥ io2mem_H` → `memFL = ioBias_memFL` (IO-dominated)
- `io2mem_BW ≤ io2mem_L` → `memFL = ccfBias_memFL` (CCF-dominated)
- Between: proportional blending between the two lines (avoids frequency jumps)

**Clipping rule**: `ioFL`, `ccfFL`, `memFL` are NOT clipped to min/max until the final step — allows fabric freq to continue reducing even after `coreFL` reaches `corePm`.

### IO Demand Fastpath (HW-triggered)

1. MIO A2F ASF detects incoming IO traffic above `IO_DEMAND_THRESHOLD` (per-agent configurable, 4 levels)
2. ASF stretches assertion ≥16 agent clocks → Punit edge-detects on fclk
3. Primecode FP handler fires: if not in PkgC6, immediately rockets IO + Mem fabric to `ROCKET_*_LATENCY_FREQ_VALUE` (default 1.8 GHz)
4. Sends HPM 0x22 `UFS_FREQUENCY` to remote IMH for P2P traffic
5. Arms `IO_DEMAND_TIMER` (default 2ms) — when expired, sends HPM 0x22 with IO freq=0 to de-rocket remote die

### Efficiency Latency Control (ELC)

Three regions based on max-aggregated CBB C0 utilization (HPM 0x36):

| Region | Condition | Behavior |
|--------|-----------|----------|
| **ELC Low** (Active Idle) | C0_util ≤ ELC_LOW_THRESHOLD (default 10%) | Floor all fabrics at ELC_RATIO (default 1.2 GHz IO/Mem, 0.8 GHz CCF) |
| **ELC Mid** | ELC_LOW < C0_util ≤ ELC_HIGH | Normal UFS heuristics + ELC_MID_RATIO floor (customer-tunable via TPMI) |
| **ELC High** (UFS Perf) | C0_util ≥ ELC_HIGH_THRESHOLD (default 95%) AND not RAPL-limited AND EPB=Perf | Increment fabric freqs by 1 bin (100 MHz) per iteration — use up TDP headroom |

**LOM vs OPM** (BIOS knob):
- **LOM** (Latency Optimized Mode, default) — ELC Low=High=0%, fabric runs at max within RAPL budget
- **OPM** (Optimized Power Mode, opt-in) — ELC Low/Mid/High enabled, up to 20% power savings with ~5% perf impact

### Uniform CBB Fabric Frequency (opt-in)

When `UFS_CONTROL.UNIFORM_CBB_FABRIC_FREQ_MODE=1`:
1. Each CBB sends local `CCF_DESIRED_RATIO` via HPM 0x1b to IMH
2. IMH-S resolves max across its CBBs, sends to IMH-P
3. IMH-P resolves global max, sends `DOWNSTREAM_CCF_RESOLVED_MIN_RATIO` back to all CBBs
4. Each CBB enforces `max(local_desired, global_min)` — unless electrical constraints require lower

### Fabric GV HW Flow (Memory Fabric — includes D2D)

1. Primecode writes target freq/voltage to Punit SCU
2. SCU → Resource Controller (RC) issues SB transaction to Resource Adapter (RA)
3. RA coordinates with East/West FIVR and mem-uclk LJPLL
4. **For freq increase**: voltage first (both East+West FIVR), then PLL ratio change
5. **For freq decrease**: PLL ratio first, then voltage decrease
6. RA handshakes with all UCIe D2D PHY stacks (v_change_request → ack, f_change_request → ack) — Memory fabric only
7. IO fabric GV is similar but **no D2D handshakes** needed

---

### Key Registers & Interfaces

### TPMI Registers (per-cluster, 2 clusters on IMH: ID0=IO, ID1=Mem; 1 cluster on CBB: ID0=CCF)

| Register | Index | Key Fields |
|----------|-------|------------|
| UFS_HEADER | 0 | INTERFACE_VERSION (0x03), LOCAL_FABRIC_CLUSTER_ID_MASK, AUTONOMOUS_UFS_DISABLED, RATIO_UNIT (100 MHz) |
| UFS_FABRIC_CLUSTER_OFFSET | 1 | Per-cluster 8-bit offset (IMH: 0x602, CBB: 0x2) |
| UFS_STATUS | 0 | CURRENT_RATIO [6:0], CURRENT_VOLTAGE [22:7] (U3.13), AGENT_TYPE_{CORE,CACHE,MEMORY,IO}, THROTTLE_COUNTER [63:32] |
| UFS_CONTROL | 1 | UFS_THROTTLE_MODE [1:0], MAX_RATIO [14:8], MIN_RATIO [21:15], ELC_LOW_RATIO [28:22], IDLE_POWER_CTRL_DISABLE [29], **UNIFORM_CBB_FABRIC_FREQ_MODE [30]**, ELC_LOW_THRESHOLD [38:32], ELC_HIGH_THRESHOLD_ENABLE [39], ELC_HIGH_THRESHOLD [46:40], **ELC_MID_RATIO [63:57]** |
| UFS_ADV_CONTROL_1 | 2 | SLOPE_1 [7:0] (S2.3), BASE_1 [15:8] (S7.0) — for CCF Line / IO Line / CCF-bias Mem Line |
| UFS_ADV_CONTROL_2 | 3 | SLOPE_2 [7:0] (S2.3), BASE_2 [15:8] (S7.0), UTILIZATION_THRESHOLD [23:16], HBM_BW_THRESHOLD [31:24] — for IO-bias Mem Line |

### HPM Messages

| Opcode | Name | Direction | Key Fields |
|--------|------|-----------|------------|
| 0x22 | `UFS_FREQUENCY` | Root↔Leaf IMH | MEM_FABRIC_TARGET_RATIO, IO_FABRIC_TARGET_RATIO |
| 0x35 | `ACTIVE_CYCLES_TELEMETRY` | CBB→IMH | MEM_BOUND_CYCLES [39:16] (>>8), TOTAL_ACTIVE_CYCLES [63:40] (>>8) |
| 0x36 | `MOST_ACTIVE_CORE_C0_TELEMETRY` | CBB→IMH | CORE_C0_TIME [39:16], TOTAL_TIME [63:40] |
| **0x1b** | `CBB_CCF_FREQUENCY` | CBB↔IMH | UPSTREAM_CCF_DESIRED_RATIO, DOWNSTREAM_CCF_RESOLVED_MIN_RATIO |
| 0x14-0x15 | `RAPL_PERF_LIMIT` | IMH-P→all | RAPL_PID_FREQ_OUTPUT [63:56], RACL_PID_FREQ_OUTPUT [55:48] — consumed for fabric freq limiting |

### IMH Telemetry Counters (Mem Fabric inputs)

| Counter | Source | Size | Description |
|---------|--------|------|-------------|
| CMS_MAX_TRAFFIC_COUNT [row][col] | SCF | 32-bit | Max transactions across all CMS directions/rings |
| D2D_BW_RX/TX [instance] | SCF | 32-bit | B2IMHD2D ingress/egress data count |
| MC_RDDATA_COUNT / MC_WRDATA_COUNT [mc] | MC | 32-bit | DRAM RD/WR CAS command counts |
| CBB_COMPUTE_BOUND_CYCLES / CBB_MEMORY_BOUND_CYCLES [CBB] | CBB HPM | 48-bit | Core scalability vs. memory-bound cycles |

### IMH Telemetry Counters (IO Fabric inputs)

| Counter | Source | Size | Description |
|---------|--------|------|-------------|
| CMS_MAX_TRAFFIC_COUNT / CRS_MAX_TRAFFIC_COUNT | SCF | 32-bit | Mesh/ring max traffic |
| UBR_A2F_REQ_BW_COUNTER_{HIOP,IOMMU,CXL,UXI} | UBR (UIO) | 48-bit | Per-agent A2F request BW |
| UBR_A2F_{NON_P2P,P2P}_DATA_BW_COUNTER_{HIOP,IOMMU,CXL,UXI} | UBR (UIO) | 48-bit | Per-agent A2F data BW |
| UBR_F2A_{REQ,NON_P2P_DATA,P2P_DATA}_BW_COUNTER_{HIOP,IOMMU,CXL,UXI} | UBR (UIO) | 48-bit | Per-agent F2A BW |

### Key Fuses (per IMH die, per SST_PP level k)

| Fuse | Width | Format | Description |
|------|-------|--------|-------------|
| CFC_MIN_RATIO_CFCIO | 7 | U7.0 | IO fabric min freq (default 0x4 = 400 MHz) |
| CFC_MIN_RATIO_CFCMEM | 7 | U7.0 | Mem fabric min freq (default 0x8 = 800 MHz) |
| SST_PP_k_CFCIO_P0_RATIO | 7 | U7.0 | IO fabric max freq (default 0x15 = 2.1 GHz) |
| SST_PP_k_CFCMEM_P0_RATIO | 7 | U7.0 | Mem fabric max freq (default 0x15 = 2.1 GHz) |
| SST_PP_k_CFCIO_UFS_LINE_{SLOPE,BASE}_{0,1} | 6/8 | S2.3/S7.0 | IO line slope + base |
| SST_PP_k_CFCMEM_UFS_LINE_{SLOPE,BASE}_{0,1} | 6/8 | S2.3/S7.0 | Mem line slope + base (0=CCF-bias, 1=IO-bias) |
| SST_PP_k_UFS_RAPL_{SLOPE,BASE}_{0,1} | 6/8 | S2.3/S7.0 | CBB CCF line slope + base (replicated on IMH for mesh boost mimicry) |
| CFCIO_VF_RATIO_POINT{0-5} / VOLTAGE_POINT{0-5} | 7/9 | U7.0/U1.8 | IO fabric V-F curve (6 points) |
| CFCMEM_VF_RATIO_POINT{0-5} / VOLTAGE_POINT{0-5} | 7/9 | U7.0/U1.8 | Mem fabric V-F curve (6 points) |

### Debug Hooks

| DFX Hook | Fabric |
|----------|--------|
| CBB Memory Bound Check disable | Memory |
| Mesh BW Check disable | Memory |
| CCF Mesh Boost Check disable | Memory |
| ELC Check disable | Both |
| PCIe/UXI/CXL/ACCL BW Check disable | IO |

### UFS Perfmons

| Perfmon Bit | Event |
|-------------|-------|
| IO_PCODE_PMU_COMM0[29] | MEM_UP_CCF_BIAS (io_BW < io2mem_L) |
| IO_PCODE_PMU_COMM1[22] | MEM_UP_OTHERS (incl. IO_BIAS) |
| IO_PCODE_PMU_COMM0[30] | MEM_DN_ALL |
| IO_PCODE_PMU_COMM1[21] | IO_UP_ANY |
| IO_PCODE_PMU_COMM1[23] | IO_DN_ALL |
| IO_PCODE_PMU_COMM1[26] | IO_DEMAND_FASTPATH |

---

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR Fabric DVFS HAS v1.09](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html) | Primary spec — Timothy Kam, May 2026 |
| HAS | [DMR Clock HAS — IMH die](https://docs.intel.com/documents/arch_datacenter/RCF/Clock/Xeon_2025_2026/Xeon_25_26_Clock_SOC_HAS.html#imh-die-links) | IMH clocking and voltage domains |
| HAS | [GNR HPM UFS HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/Hierarchical%20UFS/HPM_UFS.html) | GNR baseline for ELC/UFS Perf |
| HAS | [DMR RAPL — RACL/RAPL limits for fabric](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#throttling-cores-below-pm) | Integral windup + reverse IO line |
| HAS | [DMR IMH PM Telemetry HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Telemetry.html) | IMH telemetry counter specification |
| HAS | [DMR PM Fuse Specification](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_PM_Fuses/DMR_Fuse_Specification.html) | All PM fuses including fabric DVFS subset |
| HAS | [DMR PkgC HAS — IO_DEMAND × PkgC](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Idle_Flow/DMR_PkgC.html#io_demand-x-pkgc) | IO Demand × PkgC cross product |
| HAS | [Punit FP HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_FP_Requirements.html) | Fastpath register details |
| HAS | [DMR IMH 400MHz IO Mesh](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_IMH_400MHz_IO_Mesh.html) | 400 MHz IO mesh when no IOs connected |
| HAS | [CBB P-State Stack HAS — ELC Low](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html#efficiency-latency-control-mode) | CBB Pcode ELC Low implementation |
| HAS | [CBB P-State Stack HAS — RAPL limits](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html#rapl-limits-calculation) | CBB CCF mesh boost |
| HAS | [HPM Message Specification](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html) | HPM 0x22, 0x35, 0x36, 0x1b message formats |
| FAS | [Primecode MIO Low Latency Traffic Indicator](https://docs.intel.com/documents/primecode/fhas/DMR/UFS/SERVERPMFW-2393_MIO_Low_Latency.html) | IO Demand FAS |
| HSD | [14018676072](https://hsdes.intel.com/appstore/article/#/14018676072) | IO Demand implementation |
| HSD | [22020626797](https://hsdes.intel.com/appstore/article/#/22020626797) | IO Demand pseudocode revision |
| HSD | [22020621717](https://hsdes.intel.com/appstore/article/#/22020621717) | ELC High Mode pseudocode correction |
| HSD | [22020688780](https://hsdes.intel.com/appstore/article-one/article/22020688780) | IMH-S cannot check TDP_limited directly |
| HSD | [16029560555](https://hsdes.intel.com/appstore/article-one/#/16029560555) | BIOS must initialize ELC fields |
| HSD | [22021709715](https://hsdes.intel.com/appstore/article-one/#/article/22021709715) | Uniform CBB Fabric Frequency SOC HSD |
| HSD | [22021604248](https://hsdes.intel.com/appstore/article-one/#/22021604248) | ELC Mid Ratio — Primecode/Pcode/BIOS |
| HSD | [18039180935](https://hsdes.intel.com/appstore/article/#/18039180935) | IMH cannot access CBB TPMI → CCF slopes fused on IMH |
| Spreadsheet | [DMR Fabric DVFS data](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/assets/DMR_Fabric_DVFS.xlsx) | Thresholds, BW tables, register maps, fuse values |
| NWP MAS | [NWP IMH SOC PM MAS — UFS section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#uncore-frequency-scaling-ufs---zbb-for-customer) | Definitive: NIO UFS disabled for customer (fixed 2 GHz); HW present for debug |
| NWP PFHAS | [SERVERPMFW-24549 UFS Disable PFHAS](https://docs.intel.com/documents/primecode/fhas/NWP/SERVERPMFW-24549.html) | UFS_DISABLE fuse behavior, SPMFWREQ-927/928 |
| NWP Test | [SERVERPMFW-26354 UFS Disable Testplan](https://docs.intel.com/documents/primecode/testplan/NWP/SERVERPMFW-26354_UFS_Disable_testplan.html) | 4 IPC tests for UFS_DISABLE=1 |
| HSD | [14024641958](https://hsdes.intel.com/appstore/article/#/14024641958) | NIO power plane/freq domain implementation |
| HSD | [14024876702](https://hsdes.intel.com/appstore/article/#/14024876702) | NWP UFS customer posture |
| HSD | [14027054095](https://hsdes.intel.com/appstore/article/#/14027054095) | DMR/PMR: Add Primecode fuse UFS_DISABLE |
| NWP HAS | [NWP PnP Modeling HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/PnP/NWP_PnP_Modeling_HAS.html) | Confirms "In the absence of NIO UFS" — customer config modeling |
| NWP HAS | [NWP Firmware Architecture](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Firmware/FirmwareArch.html) | CBB PCode reused from DMR, independent from Primecode |
| NWP HAS | [NWP CBB Global HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/CBB/NWP_CBB.html) | CCF ring must run at 2.2 GHz for full BW; D2D 32 GT/s; no PD arch change |
| NWP HAS | [NWP CCF Delta HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/CCF/NWP_CCF.html) | CCF architecture delta — no DVFS changes mentioned |
| CBB HAS | [CBB PM HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) | CBB PCode PM spec — shared DMR/NWP |
| Source | `firmware.power.soc.pcode-cbb-b0/source/tpmi/Struct_all.os.xml` | UFS register structs including `UNIFORM_CBB_FABRIC_FREQ_MODE` |
| Source | `firmware.power.soc.pcode-cbb-b0/source/tpmi/AddressMap_TPMI.os.xml` | TPMI map for `UFS_HEADER`, `UFS_CONTROL`, `UFS_ADV_CONTROL_1/2`, `UFS_FABRIC_CLUSTER_OFFSET` |
| Source | `firmware.power.soc.pcode-cbb-b0/source/fuses/pcode_fuse.xml` | CBB fuse defaults for `UFS_FABRIC_CLUSTER_OFFSET=0x2`, `LOCAL_FABRIC_CLUSTER_ID_MASK=0x1` |
| Source | `firmware.power.soc.pcode-cbb-b0/verif/tests/ips/ccf/ring_ratio_resolution.rb` | Verification of `UNIFORM_CBB_FABRIC_FREQ_MODE` behavior |
| Source | `firmware.power.soc.pcode-cbb-b0/verif/simics_int/test/cbb/fw_tests/tpmi/s-tpmi-ufs.py` | TPMI read/write validation for CBB UFS registers |

### Cross Products

| Feature | Memory Fabric DVFS | IO Fabric DVFS |
|---------|-------------------|----------------|
| **ITD on Mem/IO Uclk** | ITD + GV must both be serviced | ITD + GV must both be serviced |
| **ITD on UCIe PHY** | Independent — no hangs | N/A |
| **PC6** | No GV before wake; entry→Pn; exit→active WP | Same |
| **PC2** | IO traffic may trigger mem fabric GV | IO demand × PC2 covered |
| **PkgS** | Warm reset has priority; in-progress GV completes first | Same |
| **ADR** | ADR has priority; requests boot ratio GV for flush | Same |
| **PEGA** | PEGA injected value always wins | Same |
| **Mem↔IO fabric** | IO traffic may increase mem fabric | Mem changes don't affect IO |
| **CBB Fabric** | D2D handshake must not hang | N/A |

### Related Sightings

## NWP Delta

### NIO Fabric DVFS — Disabled for Customer, HW Present for Debug

**From a NWP customer perspective, there is no UFS feature for the NIO die.** Both CFCMEM (Memory Mesh) and CFCIO (IO Mesh) run at a **fixed 2 GHz** frequency (pending post-Si process confirmation). This is controlled by the `UFS_DISABLE` fuse.

However, **the DVFS hardware is fully present on NIO** — NWP is based on DMR IMH2 and retains all the DVFS mechanisms. The `UFS_DISABLE` fuse allows Intel debug/validation teams to use DVFS for internal purposes (e.g., bringing up the SoC at a lower workpoint during A0 power-on and system validation).

**References:**
- [NWP IMH SOC PM MAS — UFS section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#uncore-frequency-scaling-ufs---zbb-for-customer)
- [HSD 14024641958](https://hsdes.intel.com/appstore/article/#/14024641958) — NIO power plane/freq domain implementation
- [HSD 14024876702](https://hsdes.intel.com/appstore/article/#/14024876702) — NWP UFS customer posture
- [SERVERPMFW-24549 UFS Disable PFHAS](https://docs.intel.com/documents/primecode/fhas/NWP/SERVERPMFW-24549.html)
- [SERVERPMFW-26354 UFS Disable Testplan](https://docs.intel.com/documents/primecode/testplan/NWP/SERVERPMFW-26354_UFS_Disable_testplan.html)

#### UFS_DISABLE Fuse Behavior

| `UFS_DISABLE` | Configuration | Behavior |
|---------------|--------------|----------|
| **1** (customer default) | Product / customer SKU | UFS algorithm disabled. Primecode sets `UFS_HEADER.AUTONOMOUS_UFS_DISABLED = 1` and requests fabric freq = fused P1 (`SST_PP_k_CFC_P1_RATIO` = 2 GHz). TPMI `UFS_CONTROL` MIN/MAX clipping still applies. RAPL/RACL PID can still limit fabric freq below P1. |
| **0** (debug/validation) | Intel internal debug | Full DMR UFS algorithm runs — BW heuristics, ELC, IO Demand, RAPL line, bias detector all active. See DMR sections above. |

**Firmware requirements** (SERVERPMFW-24549):

| Req ID | Requirement |
|--------|-------------|
| SPMFWREQ-927 | During TPMI_INIT reset sequence, if `UFS_DISABLE == 1`, FW shall set `UFS_HEADER.AUTONOMOUS_UFS_DISABLED` to 1 |
| SPMFWREQ-928 | While `UFS_DISABLE == 1`, UFS Flow shall request mesh fabric frequency equal to fuse P1 |

#### UFS_DISABLE Fuse Definition

```xml
<fuse>
  <name owner="PM" safe="1">UFS_DISABLE</name>
  <fuse_width>1</fuse_width>
  <desc>Disables Uncore Frequency Scaling, CFC fabrics will use the fused P1 as the target frequency.</desc>
  <encoding value="0" key="Enabled"/>
  <encoding value="1" key="Disabled"/>
  <encoding value="x" key="SKU_DEPENDENT"/>
  <class type="Feature" sub_class="PowerManagement"/>
  <feature>SOC_CONFIGURATION</feature>
</fuse>
```

#### Complete NWP Fuse Summary

| Fuse | Description | NWP Notes |
|------|-------------|----------|
| `UFS_DISABLE` | Disable UFS algorithm (1-bit) | Customer default = 1 (disabled) |
| `SST_PP_k_CFC_P1_RATIO` | Max mesh/fabric frequency (P1) | 2 GHz for customer config per MAS. "k" = SST-PP performance profile level |
| `CFC_MIN_RATIO` | Min mesh/fabric frequency | Shared across domains |
| `CFCIO_MIN_RATIO` | Min IO fabric frequency | IO fabric floor |
| `CFCMEM_MIN_RATIO` | Min memory fabric frequency | Memory fabric floor |
| `SST_PP_k_CFCIO_P0_RATIO` | Max IO fabric frequency (P0) | **Fused same value as P1** on NWP — no turbo headroom above P1 even with UFS enabled |

**Key notes:**
- `IO_FEATURE_DISABLE.ENABLE_UFS` is a **separate DFX bit** — not related to the `UFS_DISABLE` fuse. It exists for manual debug/DFX bypass of the UFS algorithm. Primecode must not use it as part of the `UFS_DISABLE` fuse behavior.
- Changes are **additive and platform-conditional** — the existing legacy UFS init flow is reused and extended with NWP-specific modifications. No impact to DMR/legacy flow.

#### NIO Feature Status Summary (Customer Config: UFS_DISABLE=1)

| Feature | Customer Status | Debug Status (UFS_DISABLE=0) |
|---------|----------------|------------------------------|
| IO Fabric (CFCIO) autonomous scaling | **Disabled** — fixed at P1 (2 GHz) | Active (full DMR algorithm) |
| Memory Fabric (CFCMEM) autonomous scaling | **Disabled** — fixed at P1 (2 GHz) | Active (full DMR algorithm) |
| IO Demand fastpath | **Disabled** — no freq change to rocket | Active |
| ELC Low/Mid/High | **Disabled** — no floor/boost | Active |
| BW threshold heuristics | **Disabled** | Active |
| RAPL/RACL → fabric freq limiting | **Active** — can still limit below P1 | Active (full line equations) |
| TPMI UFS_CONTROL MIN/MAX clipping | **Active** — clips the P1 request | Active |
| HPM 0x22 UFS_FREQUENCY | **N/A** — single NIO die | N/A (single die) |
| TPMI UFS_HEADER, UFS_STATUS registers | **Present** — AUTONOMOUS_UFS_DISABLED=1 | Present — AUTONOMOUS_UFS_DISABLED=0 |

### CBB CCF Ring DVFS — CONFIRMED Present

**CBB continues to support DVFS on NWP.** CBB PCode is reused from DMR ([NWP Firmware Architecture](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Firmware/FirmwareArch.html)): "The CBB Pcode is reused on NWP. It is responsible for Power Management of the CBB but is independent from the iMH Primecode."

### Source Code Evidence — Shared CBB TPMI/UFS Support

Direct inspection of the shared CBB firmware source tree `firmware.power.soc.pcode-cbb-b0` confirms that the **CBB TPMI/UFS DVFS interface is implemented in source**.

**Registers implemented in source**

- `UFS_HEADER`
- `UFS_CONTROL`
- `UFS_ADV_CONTROL_1`
- `UFS_ADV_CONTROL_2`
- `UFS_FABRIC_CLUSTER_OFFSET`

Concrete evidence:

- [source/tpmi/Struct_all.os.xml](C:/github/firmware.power.soc.pcode-cbb-b0/source/tpmi/Struct_all.os.xml)
  - `UFS_HEADER.INTERFACE_VERSION` reset = `0x3`
  - `UFS_HEADER.LOCAL_FABRIC_CLUSTER_ID_MASK`
  - `UFS_HEADER.AUTONOMOUS_UFS_DISABLED`
  - `UFS_HEADER.FUSION`
  - `UFS_HEADER.RATIO_UNIT`
  - `UFS_CONTROL.UNIFORM_CBB_FABRIC_FREQ_MODE`
- [source/tpmi/AddressMap_TPMI.os.xml](C:/github/firmware.power.soc.pcode-cbb-b0/source/tpmi/AddressMap_TPMI.os.xml)
  - `UFS_HEADER` @ `0xCDA8`
  - `UFS_FABRIC_CLUSTER_OFFSET` @ `0xCDB0`
  - `UFS_CONTROL` @ `0xCDC0`
  - `UFS_ADV_CONTROL_1` @ `0xCDC8`
  - `UFS_ADV_CONTROL_2` @ `0xCDD0`
- [source/fuses/pcode_fuse.xml](C:/github/firmware.power.soc.pcode-cbb-b0/source/fuses/pcode_fuse.xml)
  - `UFS_FABRIC_CLUSTER_OFFSET` default = `0x2`
  - `UFS_HEADER_LOCAL_FABRIC_CLUSTER_ID_MASK` default = `0x1`
  - This matches the expected **single local CBB cluster** model and **CBB offset = 2** interpretation.

**Verification evidence in code**

- [verif/tests/ips/ccf/ring_ratio_resolution.rb](C:/github/firmware.power.soc.pcode-cbb-b0/verif/tests/ips/ccf/ring_ratio_resolution.rb)
  - explicitly enables and disables `PCU_CR_UFS_CONTROL.UNIFORM_CBB_FABRIC_FREQ_MODE`
  - validates ring-ratio behavior changes when uniform mode is toggled
- [verif/simics_int/test/cbb/fw_tests/tpmi/s-tpmi-ufs.py](C:/github/firmware.power.soc.pcode-cbb-b0/verif/simics_int/test/cbb/fw_tests/tpmi/s-tpmi-ufs.py)
  - reads and writes `UFS_CONTROL`, `UFS_ADV_CONTROL_1`, and `UFS_ADV_CONTROL_2` through TPMI feature `UFS`
  - validates their effect on ring frequency limits

**Interpretation for Newport (NWP)**

- This repo demonstrates that **CBB DVFS/UFS support exists in shared CBB source**.
- It does **not** show explicit `NWP` / `Newport` project-specific branching in the attached CBB tree.
- Therefore the strongest defensible KB statement is:
  - **CBB TPMI/UFS support is present and compatible with the CBB DVFS register model expected by NWP**
  - **NWP customer disabling applies to the IMH autonomous UFS path**
  - **CBB support appears to come from shared CBB infrastructure, not a Newport-only fork**

The [NWP CBB Global HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/CBB/NWP_CBB.html) confirms CCF ring frequency is a live operating parameter:
> "NOTE: In order to meet full BW, CCF (ring clock) should run in **2.2 GHz**."

CCF ring must reach 2.2 GHz for full memory BW (460 GB/s read+write). The latency section references DMR "ring 2.7GHz", reinforcing that ring frequency scales dynamically.

CBB PCode independently manages:
- **Core P-states** (HWP, turbo) — retained
- **CCF ring frequency** (mesh GV via CBB GVFSM) — **retained**, autonomous based on mesh BW and core utilization
- **UFS-RAPL line** (CCF line) for mesh freq limiting — retained
- **CBB EMTTM/thermal** throttling — retained

NWP CBB physical changes:
- **D2D PHY: 16 GT/s → 32 GT/s** — D2D roundtrip 54 → 72 cycles (@ 2 GHz). Fabric GV D2D handshakes take longer.
- **Power delivery: no architectural change** — FIVR sizing increased for D2D BW only
- **Thermal: single diode** replaces multiple diodes
- **2 D2D stacks per CBB** (4 links each) — 8 D2D stacks total across SoC

### Impact on Test Cases

| Test | Original Scope | NWP Applicability |
|------|---------------|-------------------|
| IMH IO TPMI verification (22021980359) | IMH IO fabric cluster | **UFS_DISABLE=1**: verify AUTONOMOUS_UFS_DISABLED=1, ratio=P1. **UFS_DISABLE=0**: full test |
| IMH MEM TPMI verification (22021980803) | IMH MEM fabric cluster | Same as above |
| BIOS Configurations (22021980794) | All fabric domains | **Applicable** — CBB CCF + NIO (both configs) |
| PEGA-driven FabricGV (22021970176) | All fabric domains | **Applicable** — CBB CCF always; NIO only when UFS_DISABLE=0 |
| TPMI-driven FabricGV (22021970178) | All fabric domains | **Applicable** — CBB CCF always; NIO clipping test when UFS_DISABLE=1 |
| Out of Boundary Freq Check (22021970174) | All fabric domains | **Applicable** — verify TPMI clipping in both UFS_DISABLE states |
| CBB TPMI verification (22021980804) | CBB CCF ring cluster | **Fully applicable** — CBB DVFS unchanged |

#### NWP-Specific UFS_DISABLE Tests (SERVERPMFW-26354)

| Test | Objective | Execution |
|------|-----------|-----------|
| `ufs_disable_basic` | Verify AUTONOMOUS_UFS_DISABLED=1, IO/MEM ratio = fused P1 | Set UFS_DISABLE=1 → cold reset → check UFS_HEADER + ratios |
| `ufs_disable_algorithms` | Verify BW/ELC/IO_DEMAND stimuli don't change fabric ratio | Inject stimuli → confirm IO/MEM ratio stays at P1 |
| `ufs_disable_rapl_limiting` | Verify RAPL/RACL PID can still reduce fabric freq below P1 | Trigger RAPL limiting → confirm freq drops → release → confirm P1 returns |
| `ufs_disable_clipping` | Verify TPMI UFS_CONTROL MIN/MAX clips the P1 request | Set MAX<P1 → verify clip. Set MIN>P1 → verify clip. |
**Validation DUT applicability** (SERVERPMFW-24549):

| Die Config | IPC | EPC |
|-----------|-----|-----|
| IMH Root Die | Yes | Yes |
| IMH Leaf Die | Yes | Yes |
| Monolithic Die | Yes | — |
| IMH–IMH (multi-die) | N/A | — |
| IMH–CBB (multi-die) | N/A | — |

**EPC strategy:** Run [DMR DVFS/UFS testplan](https://docs.intel.com/documents/primecode/testplan/DMR/Initial%20Review/DVFS_UFS_testplan.html) with `UFS_DISABLE=0` CTE configuration to validate full DVFS HW in debug mode.

**CTE integration:** `UFS_DISABLE` check added to the global UFS checker.

**Linked requirements:**
- SERVERPMFW-24123: [REQUIREMENT][NWP][IMH][LTF] NIO: Power Plane/Freq domain implementation
- SERVERPMFW-24549: [PHAS][NWP][IMH] PM Features Updates PFHAS (revision 0.8, Pratik Bhogale, March 2026)
### Validation TODO
- [x] ~~Confirm NIO fabric fixed frequency from NWP IMH SOC PM MAS~~ — **2 GHz** (fused P1), pending post-Si process confirmation
- [x] ~~Confirm CBB CCF DVFS status~~ — **confirmed present**, CBB continues to support DVFS
- [x] ~~Verify whether NIO fabric GV HW exists~~ — **HW fully present** (DMR IMH2 baseline), disabled via `UFS_DISABLE` fuse for customer
- [ ] Post-Si: confirm NIO fixed freq is 2 GHz after process characterization
- [ ] Post-Si: validate `ufs_disable_basic` and `ufs_disable_clipping` on A0 silicon
- [ ] Verify IO_FEATURE_DISABLE.ENABLE_UFS DFX bit behavior is independent of UFS_DISABLE fuse
- [ ] Validate CBB CCF ring frequency range on NWP (DMR: up to 2.7 GHz; NWP BW needs ≥2.2 GHz)
- [ ] Run DMR EPC UFS test suite with UFS_DISABLE=0 to validate full DVFS HW in debug config
