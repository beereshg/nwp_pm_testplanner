# Fabric DVFS — Main Flow

> **Status**: Enriched — full touchpoint enrichment (2026-05-28)
> **Generated**: 2026-05-23 from nwp_pm_test_cases.json (7 TCs)

## Baseline (DMR)

Fabric DVFS dynamically scales frequency and voltage across three independent fabric domains per IMH die — IO Fabric (CFCIO, 400–2000 MHz), Memory Fabric (CFCMEM, 800–2000 MHz), and CBB CCF Ring (PCode-managed) — using real-time bandwidth telemetry. See [dvfs.md](dvfs.md) for full topology, execution flow, and register detail.

**Topology:** 3 fabric domains per IMH die. IO Fabric: per-die independent, 400–2000 MHz, LJPLL+FIVR, no D2D handshake needed. Memory Fabric: aligned across IMH-P/S via HPM 0x22, 800–2000 MHz, UCIe D2D handshake for GV. CBB CCF Ring: per-CBB, PCode-managed, coordinated via HPM 0x1b (Uniform mode opt-in).

**Key principle:** ~1 ms slow-loop: BW threshold LUT walk → `max()` resolution → RAPL/RACL line clip → GV via RC/RA/LJPLL. IO Demand fastpath (<1 ms, HW-triggered via MIO A2F ASF) rockets both fabrics to 1.8 GHz. ELC modes (Low/Mid/High) apply C0-utilization floor/boost.

> **GV Terminology:** "GV transition" = **working-point (gear/vector) transition** — the firmware/hardware sequence that moves a clock domain from one operating point (frequency + voltage pair) to another. Concretely: request new ratio → check policy/limits/fuses → adjust V or F first (V-first for freq-up; F-first for freq-down) → PLL/FLL settling → handshake/ack → status update at new workpoint. **Not** "Gear/Voltage" (that was a misexpansion). **Not** Geyserville (that is an unrelated legacy Intel SpeedStep brand). The GVFSM (GV Finite State Machine) in CBB PCode implements this sequence for the CCF ring domain.

**Boot:** TPMI_INIT (PH1.x) programs UFS_HEADER/CONTROL; BIOS programs ELC fields and LOM/OPM mode; heuristics begin at first slow-loop after boot.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| LJPLL (mem-uclk, io-uclk) | IMH | Fabric clock synthesis for CFCIO and CFCMEM; slow-drifting PLL | PLL ratio change: V-first (freq up); PLL-first (freq down) | DMR Fabric DVFS HAS v1.09 |
| FIVR (VCCCFCIO, VCCCFCMEM_E/W) | IMH | Per-domain voltage control; coordinated with LJPLL | FIVR voltage ramp; enable/disable | DMR Fabric DVFS HAS v1.09 |
| Resource Controller (RC) / Resource Adapter (RA) | IMH | GV arbitration; Primecode SCU → FIVR+PLL via SB transaction; RA waits for UCIe ack | SB transaction; FIVR+LJPLL coordination | DMR Fabric DVFS HAS v1.09 |
| UCIe D2D PHY | IMH ↔ CBB | Memory Fabric GV handshake: v_change_request/ack + f_change_request/ack; IO fabric has no D2D handshake | v_change_req, v_change_ack, f_change_req, f_change_ack | DMR Fabric DVFS HAS v1.09 |
| MIO A2F ASF | IMH | IO Demand fastpath trigger: ASF watermark → fclk edge → Primecode FP handler | ASF watermark assert; edge detect on fclk | FAS SERVERPMFW-2393 |
| SCF / CMS / CRS / UBR / MC | IMH | Mesh, IO, and DRAM RD/WR BW telemetry counters (all BW heuristics inputs) | CMS/CRS/UBR/MC count registers | DMR Fabric DVFS HAS v1.09 |
| TPMI | IMH + CBB | OS-visible register interface per cluster (IMH: ID0=IO, ID1=Mem; CBB: ID0=CCF) | UFS_HEADER, UFS_STATUS, UFS_CONTROL, UFS_ADV_CONTROL_1/2 | DMR Fabric DVFS HAS v1.09 + shared CBB source evidence |
| CBB CCF PLL + FIVR | CBB | CCF ring clock and voltage; managed by CBB PCode independently via GVFSM (GV = working-point transition FSM). V-first for freq-up; F-first for freq-down. PEGA events drive GVFSM to target ratio; UFS_STATUS.CURRENT_RATIO reflects locked workpoint. | CCF_DESIRED_RATIO via HPM 0x1b; CBB GVFSM busy/done; UFS_STATUS | CBB PM HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Primecode (IMH Punit) | IMH | Mem + IO Fabric DVFS: BW heuristics slow-loop, RAPL/RACL line clip, bias_detector, IO Demand fastpath handler, HSF DFS, UFS_DISABLE fuse handling, cross-IMH via HPM 0x22 | `mem_ufs_slow_loop()`; `io_ufs_slow_loop()`; `io_demand_fp_handler()`; `bias_detector()`; `ufs_init()` | `src/flow/ufs/` |
| PCode (CBB Punit) | CBB | CCF ring DVFS: autonomous freq/voltage via GVFSM; sends CCF_DESIRED_RATIO via HPM 0x1b; ELC Low per-CBB; RAPL CCF mesh boost line | CCF GV execution (GVFSM); HPM 0x1b Tx/Rx; ELC Low | `source/pcode/flows/autonomous_pstate/` |
| BIOS / UEFI | Platform | TPMI_INIT: UFS_HEADER/CONTROL init, ELC field programming, LOM/OPM mode selection; UFS_DISABLE fuse check | TPMI register init sequence; LOM/OPM BIOS knob | HSD 16029560555 |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| TPMI UFS_HEADER | Cluster offset 0x00 | RO | INTERFACE_VERSION=0x03, AUTONOMOUS_UFS_DISABLED, LOCAL_FABRIC_CLUSTER_ID_MASK, RATIO_UNIT (100 MHz) | DMR Fabric DVFS HAS v1.09 |
| TPMI UFS_STATUS | Cluster offset 0x00 | RO | CURRENT_RATIO [6:0], CURRENT_VOLTAGE [22:7] (U3.13), AGENT_TYPE flags, THROTTLE_COUNTER [63:32] | DMR Fabric DVFS HAS v1.09 |
| TPMI UFS_CONTROL | Cluster offset 0x01 | RW | UFS_THROTTLE_MODE [1:0], MAX_RATIO [14:8], MIN_RATIO [21:15], ELC_LOW_RATIO [28:22], UNIFORM_CBB_FABRIC_FREQ_MODE [30], ELC_LOW/HIGH_THRESHOLD, ELC_MID_RATIO [63:57] | DMR Fabric DVFS HAS v1.09 |
| TPMI UFS_ADV_CONTROL_1/2 | Cluster offset 0x02/0x03 | RW | SLOPE/BASE fields for CCF, IO, and Mem RAPL lines; UTILIZATION_THRESHOLD, HBM_BW_THRESHOLD | DMR Fabric DVFS HAS v1.09 |
| HPM 0x22 UFS_FREQUENCY | Root↔Leaf IMH | HPM | MEM_FABRIC_TARGET_RATIO, IO_FABRIC_TARGET_RATIO — cross-IMH coordination | HPM Message Spec |
| HPM 0x35 ACTIVE_CYCLES_TELEMETRY | CBB→IMH | HPM | MEM_BOUND_CYCLES, TOTAL_ACTIVE_CYCLES — Memory-bound ratio input | HPM Message Spec |
| HPM 0x36 MOST_ACTIVE_CORE_C0_TELEMETRY | CBB→IMH | HPM | CORE_C0_TIME, TOTAL_TIME — ELC C0 utilization input | HPM Message Spec |
| HPM 0x1b CBB_CCF_FREQUENCY | CBB↔IMH | HPM | UPSTREAM_CCF_DESIRED_RATIO, DOWNSTREAM_CCF_RESOLVED_MIN_RATIO — Uniform CBB freq mode | HPM Message Spec |
| HPM 0x14-0x15 RAPL_PERF_LIMIT | IMH-P→all | HPM | RAPL_PID_FREQ_OUTPUT [63:56], RACL_PID_FREQ_OUTPUT [55:48] — RAPL/RACL line input | HPM Message Spec |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| UFS slow-loop period | ~1 | ms | BW heuristics + RAPL line + bias_detector executed each slow loop | DMR Fabric DVFS HAS v1.09 |
| IO Demand fastpath latency | < 1 | ms | MIO A2F ASF edge → FP handler → rocket IO+Mem to 1.8 GHz | FAS SERVERPMFW-2393 |
| IO Demand timer hold-off | 2 | ms | IO_DEMAND_TIMER: hold rocketed freq before de-rocket via HPM 0x22 | DMR Fabric DVFS HAS v1.09 |
| IO Fabric freq range | 400 – 2000 | MHz | 400 MHz only when no IOs connected; P0 = 2.0 GHz | DMR Fabric DVFS HAS v1.09 |
| Memory Fabric freq range | 800 – 2000 | MHz | Pn = 800 MHz; P0 = 2.0 GHz | DMR Fabric DVFS HAS v1.09 |
| ELC Low C0 threshold (default) | 10 | % | Below: floor all fabrics at ELC_LOW_RATIO (1.2 GHz IO/Mem, 0.8 GHz CCF) | DMR Fabric DVFS HAS v1.09 |
| ELC High C0 threshold (default) | 95 | % | Above (+ EPB=Perf + not RAPL-limited): +1 bin (100 MHz) per slow-loop | DMR Fabric DVFS HAS v1.09 |
| CCF ring freq target (NWP) | 2.2 | GHz | NWP must run CCF at 2.2 GHz for full BW (460 GB/s read+write) | NWP CBB HAS |
| D2D roundtrip latency (NWP) | 72 | cycles | @ 2 GHz; was 54 on DMR (16→32 GT/s PHY upgrade impact) | NWP CBB HAS |

## Legacy (Human-Curated Reference)

### NWP Spec Context
| Field | Value |
|-------|-------|
| HAS ref | NWP HAS: No UFS. Mesh & CAB fixed at 2 GHz |
| MAS ref | NWP PM MAS: Entire Fabric DVFS ZBB'd. No UFS HSD. |
| NWP delta | ENTIRE FEATURE ZBB'd for customer. HW present for Intel debug. |
| NWP supported | False (customer) / True (Intel debug with `UFS_DISABLE=0`) |

### Architecture Summary

Fabric DVFS (Dynamic Voltage and Frequency Scaling), also called **Uncore Frequency Scaling (UFS)** or **FabricGV**, dynamically adjusts the frequency and voltage of three independent fabric domains per IMH die to balance power efficiency against throughput demand. On DMR, it is a core power-management feature; on **NWP, it is ZBB'd for customer SKUs** but the hardware is fully present for Intel debug/validation.

### Three Independent Fabric Domains (per IMH die)

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMH Die (Primecode Punit)                     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  IO Fabric   │  │  Memory      │  │  CBB CCF Ring        │   │
│  │  (CFCIO)     │  │  Fabric      │  │  (per-CBB, PCode)    │   │
│  │  400–2000 MHz│  │  (CFCMEM)    │  │  800–2000 MHz        │   │
│  │  Per-die     │  │  800–2000 MHz│  │  Independent per CBB  │   │
│  │  independent │  │  Aligned     │  │  Optional uniform     │   │
│  │              │  │  across dies │  │  mode via HPM 0x1b    │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  Slow loop: ~1 ms    IO Demand fastpath: <1 ms HW-triggered     │
│  RAPL/RACL line:     Biased memory lines: io2mem_BW switching    │
│  ELC modes:          Low / Mid / High (C0 utilization-driven)    │
└──────────────────────────────────────────────────────────────────┘
```

### Key DMR Capabilities (from enriched [dvfs.md](dvfs.md))

| Capability | Description |
|------------|-------------|
| **BW heuristics** | MC RD/WR, CMS, UBR, HIOP, ACCEL, IOMMU, UXI_CXL traffic counters → LUT walk |
| **IO Demand fastpath** | HW-triggered (MIO A2F ASF) rocket to 1.8 GHz in <1 ms |
| **RAPL/RACL line** | PID output → io/ccf/mem frequency ceiling with bias_detector switching |
| **ELC modes** | Low/Mid/High regions based on max CBB C0 utilization telemetry (HPM 0x36) |
| **D2D handshakes** | UCIe PHY RA coordination for Memory Fabric GV (not needed for IO) |
| **Uniform CBB freq** | Opt-in: aggregate CCF ring freq across all CBBs via HPM 0x1b |
| **HSF DFS** | HSF PLL couples with Memory Fabric (800 MHz @ Pn, 1.7 GHz otherwise) |

### FW Agent Responsibilities

| Agent | Scope | Role |
|-------|-------|------|
| **Primecode (IMH Punit)** | IMH Memory + IO fabrics | BW heuristics, RAPL/RACL line, D2D coordination, IO Demand fastpath |
| **PCode (CBB Punit)** | CBB CCF Ring | CCF frequency/voltage, independent from Primecode |
| **BIOS** | Initial configuration | TPMI register init, ELC fields, LOM/OPM mode selection |

### FW Agents
- **Agents**: Primecode (IMH), PCode (CBB), BIOS
- **Interfaces**: TPMI (UFS_HEADER/STATUS/CONTROL), HPM (0x22, 0x35, 0x36, 0x1b), B2P mailbox
- **HW Blocks**: mesh_pll, tpmi_bar, LJPLL, FIVR, Resource Controller/Adapter, UCIe D2D PHY
- **Sub-features**: UFS slow loop, IO Demand fastpath, RAPL/RACL line, ELC, Uniform CBB freq, HSF DFS

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR Fabric DVFS HAS v1.09](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html) | Primary spec — BW heuristics, RAPL line, IO Demand, ELC |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | CBB CCF ring DVFS |
| HAS | [DMR CCB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) | CBB PM feature index |
| HAS | [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html) | CCF GV execution flow |
| HAS | [CBB P-State Stack — ELC Low](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html#efficiency-latency-control-mode) | CBB PCode ELC Low implementation |
| HAS | [HPM Message Specification](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html) | HPM 0x22, 0x35, 0x36, 0x1b message formats |
| HAS | [DMR Clock HAS — IMH](https://docs.intel.com/documents/arch_datacenter/RCF/Clock/Xeon_2025_2026/Xeon_25_26_Clock_SOC_HAS.html#imh-die-links) | IMH clocking and voltage domains |
| HAS | [DMR RAPL — RACL/RAPL limits for fabric](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#throttling-cores-below-pm) | RAPL integral windup + reverse IO line |
| HAS | [DMR PkgC — IO_DEMAND × PkgC](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Idle_Flow/DMR_PkgC.html#io_demand-x-pkgc) | IO Demand × PkgC cross product |
| HAS | [DMR PM Fuse Specification](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_PM_Fuses/DMR_Fuse_Specification.html) | PM fuses including fabric DVFS subset |
| VT | [DMR CBB CCP/DVFS VT](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/VT/CCP_DVFS_VT/CCP_DVFS_VT.html) | CBB CCP/DVFS validation test plan |
| MAS | [NWP IMH SoC PM MAS — UFS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP: UFS disabled for customer, HW present for debug |
| PFHAS | [SERVERPMFW-24549 UFS Disable](https://docs.intel.com/documents/primecode/fhas/NWP/SERVERPMFW-24549.html) | UFS_DISABLE fuse behavior: SPMFWREQ-927/928 |
| Primecode src | `src/flow/ufs/` | IMH UFS slow-loop, IO Demand, RAPL line |
| PCode src | `source/pcode/flows/autonomous_pstate/` | CBB CCF ring DVFS |

### Related Sightings

| HSD | Title | Relevance |
|-----|-------|-----------|
| 14018676072 | IO Demand implementation | IO Demand fastpath design issue |
| 22020626797 | IO Demand pseudocode revision | IO Demand algorithm correction |
| 22020621717 | ELC High Mode pseudocode correction | ELC High algorithm fix |
| 22020688780 | IMH-S cannot check TDP_limited | Multi-die RAPL line gap |
| 18039180935 | IMH cannot access CBB TPMI | CCF slopes fused on IMH instead |
| 14024876702 | NWP UFS customer posture | NWP UFS disable decision |

## NWP Delta

### NWP Status: ❌ ZBB'd for Customer — HW Present for Debug

| Aspect | DMR (N-1) | NWP (Customer) | NWP (Intel Debug) | Source |
|--------|----------|----------------|-------------------|--------|
| IMH IO/MEM Fabric DVFS | Full UFS algorithm | **Disabled** — fixed 2 GHz | Full algorithm (UFS_DISABLE=0) | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| CBB CCF Ring DVFS | Full support | **✅ Present** — shared CBB TPMI/UFS support exists in source; explicit NWP-only branching not identified | ✅ Present | CBB shared source + CBB PCode reuse |
| UFS_DISABLE fuse | N/A | =1 (customer default) | =0 (debug override) | SERVERPMFW-24549 |
| IO Demand fastpath | HW-triggered | **Disabled** with UFS | Active with UFS_DISABLE=0 | |
| RAPL/RACL line | Active | N/A (no UFS algorithm) | Active with UFS_DISABLE=0 | |
| ELC modes | LOM/OPM configurable | N/A | Active with UFS_DISABLE=0 | |
| TPMI registers | Fully populated | `UFS_HEADER.AUTONOMOUS_UFS_DISABLED=1` | Fully populated | SPMFWREQ-927 |
| CBB source support | Full shared CBB TPMI/UFS implementation present | Present in source, not explicitly branded `NWP` | Present | Shared CBB repo inspection |

**Firmware Requirements (SERVERPMFW-24549):**
- **SPMFWREQ-927**: If `UFS_DISABLE == 1`, FW shall set `UFS_HEADER.AUTONOMOUS_UFS_DISABLED` to 1
- **SPMFWREQ-928**: While `UFS_DISABLE == 1`, UFS Flow shall request fabric freq = fused P1 (2 GHz)

### Newport/CBB Source-Code Conclusion

Inspection of the shared CBB firmware repo `firmware.power.soc.pcode-cbb-b0` confirms that the **CBB side of Fabric DVFS/UFS is implemented in source**:

- TPMI register blocks exist for `UFS_HEADER`, `UFS_CONTROL`, `UFS_ADV_CONTROL_1`, `UFS_ADV_CONTROL_2`, and `UFS_FABRIC_CLUSTER_OFFSET`
- `UNIFORM_CBB_FABRIC_FREQ_MODE` is explicitly modeled in the CBB `UFS_CONTROL` definition
- CBB fuse defaults encode the expected CBB mapping:
	- `LOCAL_FABRIC_CLUSTER_ID_MASK = 0x1`
	- `UFS_FABRIC_CLUSTER_OFFSET = 0x2`
- Verification collateral directly exercises CBB UFS TPMI reads/writes and uniform ring-frequency mode

**KB interpretation:**

- **Yes** — the source code supports the **CBB TPMI/UFS control plane** needed for Newport CBB DVFS
- **No explicit `NWP` fork/gating** was found in the attached CBB repo; this appears to be **shared CBB support**
- So for Newport the correct wording is: **CBB DVFS support exists in shared source; project/customer enablement is controlled by NWP platform policy, especially the IMH-side UFS disable path**

## Subflows (1)

| # | Subflow | Status | TCs | Segment | Notes |
|---|---------|--------|-----|---------|-------|
| 1 | [DVFS](dvfs.md) | Enriched | 7 | PSS | Full BW heuristics, RAPL line, IO Demand, ELC |
| | **Total** | 1/1 enriched | **7** | | |
