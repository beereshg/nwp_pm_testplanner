# Power/RAPL > Memory PM (MemCLOS / DRC + CLTT)

> **Status**: Restructured — NWP delta enriched from MCP HAS/MAS query
> **Parent**: [Power / RAPL](power_rapl_main.md)

## Baseline (DMR)

Memory PM encompasses two distinct mechanisms: 1. **MemCLOS / DRC (Dynamic Resource Controller)** — firmware-based memory bandwidth QoS that throttles low-priority cores to protect high-priority workload memory access 2. **CLTT (Closed Loop Thermal Throttling)** — MR4-based thermal throttling of DRAM to prevent overheating

## HW Touchpoints

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| | | | | |

## FW Touchpoints

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| | | | | |

## OS Interfaces

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| | | | | |

## NWP Delta

**Memory PM is REMOVED on NWP** — not supported due to LPDDR6 memory controller and simplified PM flows.

### Removed Features
- APD/PPD (Adaptive/Pre-emptive Power Down)
- LPM1/LPM2/LPM3 (Low Power Modes)
- SSR (Self-Refresh with temperature compensation)
- DRAM self-refresh management
- Memory power gating sequences

### Rationale
- NWP uses LPDDR6 memory stack with fundamentally different power management model
- LPDDR6 controller handles power states internally

### Validation Impact
- **All Memory PM test cases are N/A on NWP**
- Memory thermal management may still apply (see memory_thermal/)

## Legacy (Human-Curated Reference)

### Architecture Summary

Memory PM encompasses two distinct mechanisms:
1. **MemCLOS / DRC (Dynamic Resource Controller)** — firmware-based memory bandwidth QoS that throttles low-priority cores to protect high-priority workload memory access
2. **CLTT (Closed Loop Thermal Throttling)** — MR4-based thermal throttling of DRAM to prevent overheating

#### MemCLOS / DRC Overview

DRC is an **inbuilt RDT (Resource Director Technology)** feature implemented in Punit firmware. It replaces the need for complex OS-level RDT software with a closed-loop PID controller that:
- Monitors MC perfmon counters (RPQ occupancy, CAS counters, or WPQ occupancy)
- Detects memory bandwidth saturation against a configurable set point
- Throttles low-priority cores via MBE (Memory Bandwidth Enforcement) hardware — adjusting leaky bucket drain rate time windows per CLOS

**Key value**: Customers get memory QoS without kernel-level RDT software changes — firmware handles it autonomously in milliseconds.

#### MemCLOS Mapping Hierarchy

```
Thread → PQR_ASSOC MSR (CLOSID) → CLOS-to-MCLOS mapping → MemCLOS ID (0-3)
                                                                │
                                                     Priority + Min/Max attributes
                                                                │
                                                    PID controller output
                                                                │
                                              MBE time window per CLOS → HW throttle
```

- **4 MemCLOS IDs** (MCLOS 0-3), each with priority (0x0=highest, 0xF=lowest) and min/max MBA time window bounds
- **16 RDT CLOS IDs** mapped to 4 MemCLOS IDs via `DRC_CLOS_TO_MCLOS` register

#### MBE Hardware (Memory Bandwidth Enforcement)

MBE uses a **leaky bucket / rate meter** per thread to track memory bandwidth:
- Transactions fill the bucket; drain rate is controlled by time window value
- When bucket exceeds threshold → 16 discrete throttle levels applied to core at uop allocation boundary
- **GNR**: Leaky Bucket Counter rate meter
- **DMR**: Linear Rate Monitor (LRM) — different HW but same Pcode interface
- **Distress handling**: When severe overload, MS2IDI throttles credits to 0 (pure HW, not Pcode)

#### PID Controller

```
MC Perfmon Counter → EWMA LP Filter → PID Controller → Time Window Balancer → MBE delay per CLOS
         ↑                                    ↑                                        │
    Set Point (limit)                 proportional/integral              Per-MemCLOS priority
                                        derivative terms                  weighting + min/max
```

PID input computation:
```
delta_t = current_tsc - last_sampled_tsc
For each MC channel i:
    perfmon_delta[i] = curr_perfmon_cnt[i] - prev_perfmon_cnt[i]
    sum_perfmon_delta += perfmon_delta[i]
final_perfmon_cnt = sum_perfmon_delta × delta_t⁻¹ × perfmon_scale_factor
final_pid_input = final_perfmon_cnt - set_point
```

EWMA filter smooths the PID input:

$$Throttling\_Budget(n) = (final\_perfmon\_cnt - SetPoint - Throttling\_Budget(n-1)) \times (1 - \alpha) + Throttling\_Budget(n-1)$$

$$\alpha = e^{-(Time\_Delta / Time\_Window)}$$

#### Gen-to-Gen Evolution

| Aspect | SPR (Wave3) | GNR (Wave4) | DMR | NWP |
|--------|------------|-------------|-----|-----|
| **SW Interface** | OS Mailbox (Cmd 0xD0) | TPMI DRC registers | TPMI | TBD — likely TPMI |
| **MBE HW** | Leaky bucket (per CHA write) | Leaky bucket (DMA-based write) | Linear Rate Monitor (LRM) | TBD |
| **Perfmon scale (RPQ)** | `ddr_freq_mult × 4` | `ddr_freq_mult × 8 × 2` | TBD | TBD |
| **SNC support** | No | Yes — 1 PID per Cdie | TBD | TBD |
| **Root/Leaf split** | N/A (single die) | Root PrimeCode PID → Leaf PCode MBE writes | Root/Leaf HPM | TBD |
| **Granularity** | Per core | Per thread + IO | TBD | TBD |

#### GNR/DMR Root-Leaf HPM Architecture

```
┌──────────────────────────────────────────┐
│  Root PrimeCode (iMH / IO die)           │
│  • Owns TPMI DRC registers               │
│  • Runs PID controller (1 per SNC domain)│
│  • Computes time window per MemCLOS       │
│  • Sends DRC_CONFIG HPM to leaves         │
│  • Sends MEMCLOS_TIMEWINDOW HPM to leaves │
│  • Receives BW_PERFMON_STATISTICS from    │
│    leaves                                 │
└──────────────┬───────────────────────────┘
               │ HPM: DRC_CONFIG, DRC_CONTROL
               ▼
┌──────────────────────────────────────────┐
│  Leaf PCode (CBB / Cdie)                 │
│  • Configures MC perfmon counters         │
│  • Reads perfmon, computes max delta      │
│  • Sends BW_PERFMON_STATISTICS HPM to root│
│  • Receives time window values from root  │
│  • Writes MBE delay_time_window registers │
│    per CLOS per CHA (up to 16 writes/CHA)│
└──────────────────────────────────────────┘
```

---

### Execution Flow

#### DRC Enable & Configuration

1. **Discovery**: SW reads `DRC_HEADER.DRC_FEATURE_AVAILABLE` (fuse-gated) and `INTERFACE_VERSION`
2. **Enable**: SW writes `DRC_CONTROL.DRC_EN = 1`, optionally sets `DRC_POLICY` (0 = proportional priority PID)
3. **Map CLOS→MCLOS**: SW writes `DRC_CLOS_TO_MCLOS` — maps 16 RDT CLOSIDs to 4 MCLOSIDs
4. **Set attributes**: SW writes `DRC_ATTRIBUTES_MCLOS_0..3` — priority (0x0-0xF), min/max MBA throttle windows, enable bit
5. **Configure events**: SW writes `DRC_CONFIG0` (DDR) or `DRC_CONFIG1` (DDRT, mutually exclusive) — event select, set point, filter time window, optionally multiple set points (v2)
6. **Root sends HPM**: `DRC_CONFIG` with sub-commands `MEMCLOS_CONFIG` (event+enable) and `CLOS_MEMCLOS_MAPPING` to all leaves
7. **Leaves configure perfmon**: Program `pmoncntrcfg_4` with selected event (RPQ=0x80/0x0, WPQ=0x84/0x0, CAS=0x05/0xFF)
8. **Closed loop runs**: Leaf reads perfmon → sends `BW_PERFMON_STATISTICS` HPM to root → root runs PID → root sends `MEMCLOS_TIMEWINDOW` HPM to leaves → leaves write MBE registers

#### DRC Disable

1. SW writes `DRC_CONTROL.DRC_EN = 0`
2. PCode enters **SAFE STATE**: disables `rbe_valid` in `mbe_config`, sets all `MBE_DELAYVALUE_*` to `0x01010101` (TW=1, delay=1 per CLOS)

#### Time Window Distribution Algorithm

```
total_threshold_limit = pid_output × 4 (number of MemCLOS)
total_priority = Σ all MCLOS priorities
total_min = Σ all MCLOS min values

If total_threshold_limit > total_min:
    For each CLOS:
        threshold_new[CLOS] = MAX(MIN[CLOS], 1)    // HW bug guard
        threshold_new[CLOS] += (priority[CLOS] / total_priority) × remaining_budget
Else:
    threshold_new[CLOS] = (MIN[CLOS] × total_threshold_limit) / total_min

Clip to MAX, apply LPF:
    final[CLOS] = prev[CLOS] + (new - prev[CLOS]) × LPF_factor    // LPF ≈ 0.9
```

---

### Key Registers & Interfaces

#### TPMI DRC Registers (GNR+ / Wave4+)

| Register | Index | Key Fields | Notes |
|----------|-------|------------|-------|
| `DRC_HEADER` | 0 | `DRC_FEATURE_AVAILABLE[8]`, `INTERFACE_VERSION[7:0]` (v2) | Discovery; v2 adds multiple set points |
| `DRC_CONTROL` | 1 | `DRC_EN[0]`, `DRC_POLICY[15:8]` (0=proportional PID) | Feature enable |
| `DRC_CLOS_TO_MCLOS` | 2 | `CLOSn_MCLOS[1:0]` × 16 CLOSIDs | Maps 16 CLOS → 4 MCLOS |
| `DRC_ATTRIBUTES_MCLOS_0..3` | 3-6 | `ATTR_EN[31]`, `MCLOS_MAX[23:16]`, `MCLOS_MIN[15:8]`, `MCLOS_CONFIGURATION[3:0]` | Per-MCLOS priority (0x0=HP, 0xF=LP) + min/max |
| `DRC_CONFIG0` | 7 | `EVENT_EN[31]`, `EVENT[23:16]`, `FILTER_TIME[15:8]`, `SET_POINT[7:0]`, `SET_POINT1..3` (v2) | DDR event config; set_point scales max counter value |
| `DRC_CONFIG1` | 8 | Same as CONFIG0 | DDRT events (mutually exclusive with CONFIG0) |
| `DRC_STATUS` | 9 | `DRC_FEATURE_EN[0]`, `MCLOS0..3_THROTTLED[1:4]`, `DRC_POLICY_STS[15:8]` | Throttle status per MCLOS |

#### Legacy OS Mailbox (SPR and earlier)

| Sub-command | Code | Purpose |
|-------------|------|---------|
| `CLOSToMEMCLOS` | 50 | Map CLOSID → MCLOSID |
| `MEM_CLOS_ATTRIBUTES` | 51 | Per-MCLOS priority, min, max |
| `MEM_CLOS_CONFIG0` | 52 | DDR event config + set point |
| `MEM_CLOS_CONFIG1` | 53 | DDRT event config |
| `MEM_CLOS_EN` | 54 | Feature enable + discovery |

All via mailbox command `0xD0`.

#### MC Perfmon Events

| Event | Code (Wave4) | Code (Wave3) | Description |
|-------|-------------|-------------|-------------|
| RPQ Occupancy | 0x80, mask 0x0 | 0x80, mask 0x0 | Read Pending Queue — default event |
| WPQ Occupancy | 0x84, mask 0x0 | 0x82, mask 0x0 | Write Pending Queue |
| CAS Counter | 0x05, mask 0xFF | 0x05, mask 0xFF | Total CAS (captures non-temporal writes that RPQ misses) |

#### HPM Messages (Root ↔ Leaf)

| Message | Direction | Sub-command | Purpose |
|---------|-----------|-------------|---------|
| `DRC_CONFIG` | Root → Leaf | `MEMCLOS_CONFIG` (0) | Event ID + enable per DDR/DDRT |
| `DRC_CONFIG` | Root → Leaf | `CLOS_MEMCLOS_MAPPING` (1) | 16 CLOSID→MCLOSID mapping |
| `DRC_CONTROL` | Root → Leaf | `MEMCLOS_TIMEWINDOW` (1) | 4 time window values (1 per MCLOS) |
| `DRC_CONTROL` | Leaf → Root | `BW_PERFMON_STATISTICS` (0) | Max perfmon delta from leaf MC |

#### MBE Hardware Registers

| Register | Key Fields | Notes |
|----------|------------|-------|
| `mbe_delay_time_window` (Wave4) | `time_window_ddr[31:24]`, `delay_ddr[23:16]`, `time_window_cr[15:8]`, `delay_ddrt[7:0]` | Per CLOS (16 instances) |
| `mbe_settings` | `hw_mbe_feedback_enable[1]`, `disable_cascade_delay[2]`, `thread_min_or_max[0]` | One-time MBE config |
| `mbe_config` | `rbe_valid` | MBE master enable |

---

### Fuses

| Fuse | Description |
|------|-------------|
| `HWDRC_ENABLE` | Enables DRC feature (ICX/SPR: `MEMCLOS_ENABLE`) |

---

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [MemCLOS DRC HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/MemCLOS/MemCLOS_DRC.html) | Primary spec — PID algorithm, registers, HPM flow |
| DRC Specs | [DRC SharePoint](https://intel.sharepoint.com/:f:/r/sites/RDT_Enabling/Shared%20Documents/CNDA_RDT_Specs/DRC) | ACPI/MMIO table, arch specs |
| RDT Landing | [goto.intel.com/rdtSpecs](https://goto.intel.com/rdtSpecs) | RDT specifications |
| MBE Rate Meters | [DMR RDT HAS — Rate Meters](https://docs.intel.com/documents/arch_datacenter/DMR/RDT%20and%20QoS/DMR%20RDT%20HAS.html#overview-of-rate-meters) | LRM (DMR) rate meter details |
| MBA HAS | [DMR RDT HAS — MBA](https://docs.intel.com/documents/arch_datacenter/DMR/RDT%20and%20QoS/DMR%20RDT%20HAS.html#memory-bandwidth-allocation-mba) | MBA hardware spec |
| MC Perfmon | [Gen5 MC IP MAS — PMON](https://docs.intel.com/documents/iparch/mc/MAS/Gen5/Releases/MAS/Gen5_MC_IP_MAS_DFX/Gen5_MC_IP_MAS_DFX.html#pmon) | MC perfmon events |
| SCF B2IDI | [SCF Gen3 B2IDI HAS](https://docs.intel.com/documents/cicg_ip/SCF/gen3/releases/R2004/B2IDI/HAS/assets/SCF_GEN3_R2004_B2IDI_HAS_1p0.pdf) | MBE hardware IP details |
| HSD | 22019891805 | DRC_CONFIG multiple setpoints (interface v2) |
| Primecode src | `src/flow/` (DRC/MemCLOS) | PID controller, time window balancer |
| PCode src | CBB leaf | Perfmon reads, MBE register writes |

---

### Feature Interactions

| Feature | Interaction |
|---------|-------------|
| **SNC (Sub-NUMA Clustering)** | GNR+: 1 PID per Cdie/SNC domain. Without SNC-aware DRC, LP cores get incorrectly throttled across SNC boundaries |
| **RDT MBA** | DRC coexists with RDT MBA — DRC overrides MBE time windows dynamically; static MBA settings from BIOS/ucode are the baseline before DRC enable |
| **DDRT (Optane)** | Separate CONFIG1 register; mutually exclusive with DDR CONFIG0 enable. Set point halved when both DDR+DDRT populated |

---

#### Validation Approach
- **Discovery**: Verify `DRC_HEADER.DRC_FEATURE_AVAILABLE` reflects fuse, `INTERFACE_VERSION` = 2
- **Throttling status**: Enable DRC, apply memory load, check `DRC_STATUS.MCLOSn_THROTTLED` bits for LP MCLOS
- **Negative checks**: Attempt enable when fuse disabled, set both CONFIG0+CONFIG1 EVENT_EN (should error), write invalid set points
- **CLTT**: Verify MR4-based thermal throttling activates at DRAM temperature thresholds

---

### Related Sightings
<!-- No NWP MemCLOS/CLTT sightings identified yet — populate as they arise -->

---

### NWP Delta

#### Confirmed (from SERVERPMFW-24119 NWP MC & CLTT PFHAS)

| Area | NWP Status | Detail |
|------|-----------|--------|
| CLTT temperature source | ✅ **MR4-only** | LPDDR6 uses MR4 for CLTT temperatures. **TSOD is not supported** on NWP LPDDR6. No I3C TSOD configuration performed by PrimeCode. |
| MR4 default | ✅ Enabled | Fuse `MR4_CLTT_ENABLE = 1` (default). BIOS mailbox `CLTT_MR4_ENABLE` (bit 5) and `CLTT_PECI_ENABLE` (bit 6, takes precedence). |
| MR4 temp registers | ✅ Same path | MR4 temperature read from `IO_TELEMETRY` registers in PUnit. Same bit encoding and conversion factor as DMR. |
| MR4 conversion ranges | ⚠️ Temporary | DMR Gen4 DDR MC HAS conversion ranges used until architecture provides NWP LPDDR6-specific MR4/MR109 ranges. |
| MR4 aggregation | ✅ Same HPM | PrimeCode aggregates DIMM temp data on root IO die via HPM message (same as DMR). |
| I3C TSOD | ❌ **Removed** | No TSOD support on LPDDR6. PrimeCode will NOT program `SB_I3C_PUNIT_DEST_ID`. No I3C TSOD configuration. |
| Sub-channel topology | ✅ **Single sub-channel** | NWP has 1 sub-channel per MC (DMR had 2). Affects MR4 Temperature Polling iteration, MC Fuse Programming, Buddy Channel Ingress, Patrol TAD Rule Programming. |
| APD (Autonomous Power Down) | ❌ **ZBB** | NWP PM MAS §3: "No APD/PPD" — not validated on NWP. |
| PPD (Pre-charge Power Down) | ❌ **ZBB** | NWP PM MAS §3: "No APD/PPD" — not validated on NWP. |
| LPM1 / LPM2 / LPM3 (Low Power Modes) | ❌ **ZBB** | NWP PM MAS §3: "No LPM1/LPM2/LPM3" — LPDDR6 low-power modes are not scoped for NWP validation. |
| Self Refresh (SR/SSR/DSREF) | ❌ **All disabled** | PkgC disabled on NWP → all SR modes disabled. `AIPM_MC_SHALLOW_SELF_REFRESH_DISABLE = 1`. `PKG_C_STATE_LIMIT_REQ.c_state_max_limit = 0` (C0/C1 only). |
| Auto Idle | ❌ **Disabled** | PrimeCode disables MC Auto Idle through dispatcher when SSR resolved as disabled in CPL3. |
| SSR BIOS bits | ❌ Not honored | BIOS mailbox `DRAM_SSR_DISABLE` (bit 9) and `IERR_ADR_FIX_ENABLE` (bit 12) not honored on NWP. |
| ADDDC mailbox | ❌ **ZBB'd** | `ADDDC_QUIESCE` (opcode 0x81) returns unsupported. NWP does not support ADDDC. |

#### Still Open (not addressed by SERVERPMFW-24119)

| Area | Question | GNR/DMR Baseline |
|------|----------|------------------|
| MBE HW type | LRM (like DMR) or new rate meter design? | DMR: Linear Rate Monitor; GNR: Leaky Bucket |
| TPMI interface | Same DRC register layout and indices 0-9? | GNR: TPMI DRC v2 with multiple set points |
| SNC support | How many SNC domains / PIDs? | GNR: 1 PID per Cdie |
| Root/Leaf split | Same HPM message format (DRC_CONFIG, DRC_CONTROL)? | GNR: Root PrimeCode PID → Leaf PCode MBE |
| Perfmon scale factors | RPQ/WPQ/CAS scale factors for NWP MC clocking? | GNR: `ddr_freq_mult × 8 × 2` for RPQ |
| DDR speed/gear | LPDDR6 gear ratio affecting Hclk conversion? | GNR: Gear8 (Hclk = DQ_rate/8) |
| DDRT/CXL events | CXL memory QoS via DRC? | GNR: DDRT (Optane) only; CXL TBD |
| Thread granularity | Per-thread MBE like GNR or per-core? | GNR: per thread + IO |

#### Collateral
- [SERVERPMFW-24119 NWP MC & CLTT PFHAS](https://docs.intel.com/documents/primecode/fhas/NWP/SERVERPMFW-24119_NWP_Memory_Controller_Changes.html)
- [DMR CLTT HAS - MR4](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html#mr4-based-cltt)
- [Gen4 DDR MC HAS - CLTT/MR4 ranges](https://docs.intel.com/documents/cicg_ip/DDR/gen4/releases/2101/HAS/DDR_GEN4_HAS_parent.html#fully-configurable-2x-refresh-cltt-and-memtrip-for-mr4)
- [Gen6 LPDDR6 MC IP HAS](https://docs.intel.com/documents/iparch/mc/HAS/Gen6/Releases/LPDDR6/lpddr6.html)
