# TCD: CBB CCF VF Curves

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421174](https://hsdes.intel.com/appstore/article-one/#/22022421174) |
| **Title** | CBB CCF VF Curves |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TP** | [22022420512 -- CBB CCF Ring Scalability Feature Enabling](https://hsdes.intel.com/appstore/article-one/#/22022420512) |
| **Validation Phase** | **Alpha** — Feature enabling / path clearing (interface sanity check) |
| **Feature** | CBB CCF Active States -- GV management |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

CBB CCF VF Curves define the allowable **voltage-frequency operating relationship** for the CBB CCF ring. For each supported ratio, the corresponding minimum required voltage is determined by fused VF data, and runtime control logic ensures the active voltage and ratio remain consistent with that curve. VF and PF curves are represented as **6-point curves**, with interpolation between adjacent points when intermediate operating points are needed.

**Key architecture fact:** CBB CCF supports **8 VF curves** — one per FIVR in the CCF domain — rather than a single worst-case curve. This enables finer-grained control and avoids over-volting all voltage domains to satisfy only the worst-case instance. `UFS_STATUS.CURRENT_VOLTAGE` reports the **maximum voltage across all 8 CCF FIVRs** in **U3.13 format** (3 integer bits, 13 fractional bits). PCode updates both `CURRENT_RATIO` and `CURRENT_VOLTAGE` on every resolved operating-point change.

**Fuse clip behavior:** Software may write `UFS_CONTROL.MAX_RATIO` and `MIN_RATIO`, but Primecode silently clips the effective values to the fused min/max legal range before use. `UFS_STATUS.THROTTLE_COUNTER` increments once per 1 ms interval when the resolved frequency violates the programmed bound.

### VF Transition Rules

```
Frequency Increase (freq up) -- V-FIRST:
  1. GVFSM reads new target ratio from UFS_CONTROL
  2. Look up VF_table[new_ratio] -> required voltage
  3. V-FIRST: ramp all 8 CCF FIVRs to VF_table[new_ratio]
  4. Wait for FIVR settle
  5. PLL-SECOND: switch PLL to new ratio
  6. UFS_STATUS.CURRENT_RATIO  = new_ratio
  7. UFS_STATUS.CURRENT_VOLTAGE = max(8 FIVRs) in U3.13

Frequency Decrease (freq down) -- PLL-FIRST:
  1. PLL-FIRST: switch PLL to lower ratio
  2. UFS_STATUS.CURRENT_RATIO = new_ratio
  3. V-SECOND: reduce FIVR voltage to VF_table[new_ratio]
  4. UFS_STATUS.CURRENT_VOLTAGE = max(8 FIVRs) in U3.13
```

### Block Diagram

```
  Fuse-defined VF Curves (8 curves -- one per CCF FIVR)
  +-------------------------------------------------------------+
  | ratio -> min_voltage[FIVR_0..7]  (6-point curve per FIVR)  |
  | Unused points repeat previous or = 0 (end-of-curve)         |
  +---------------------------+---------------------------------+
                              |  Phase 5 init (fuse -> TPMI)
                              v
  +----------------------------------------------------------+
  | CBB PCode GVFSM                                          |
  |                                                          |
  | New target ratio arrives (BIOS/PEGA/BW heuristic/RAPL)  |
  |                                                          |
  | if ratio_up:  V-first (ramp 8 FIVRs) -> PLL switch      |
  | if ratio_down: PLL switch -> V-second (reduce 8 FIVRs)  |
  |                                                          |
  | OUT-OF-RANGE write: clip to fused [Pm_cap, P0_cap]       |
  +----------------------------+-----------------------------+
                               |
                               v  (each slow-loop ~1 ms)
  +----------------------------------------------------------+
  | UFS_STATUS (TPMI, per-CBB)                               |
  | CURRENT_RATIO   [6:0]     live PLL ratio                 |
  | CURRENT_VOLTAGE [22:7]    max(8 FIVRs) in U3.13         |
  | THROTTLE_COUNTER [63:32]  increments 1/ms on violation   |
  +----------------------------------------------------------+
```

### NWP VF Operating Points

| VF Point | Ratio | Freq | Voltage trend |
|----------|-------|------|--------------|
| Pm (min) | 0x08 | 800 MHz | Minimum supply (all 8 FIVRs) |
| Mid | 0x12 | 1800 MHz | Mid-range voltage |
| P1 | 0x14 | 2000 MHz | Near-max voltage |
| P0 (max) | 0x16 | 2200 MHz | Maximum supply (max across 8 FIVRs) |

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422863 -- CBB CCF VF Curves](https://hsdes.intel.com/appstore/article-one/#/22022422863) | VF curve fuse readback, FIVR voltage correctness at each ratio, V-first/PLL-first ordering |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| TPMI SST_PP_INFO_4 | `sv.socket0.cbbN.base.tpmi.sst_pp_info_4` | TRL ratios (P0 encoding) |
| TPMI SST_PP_INFO_11 | `sv.socket0.cbbN.base.tpmi.sst_pp_info_11` | P0/P1/Pm encoding |
| TPMI UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status` | CURRENT_RATIO [6:0], CURRENT_VOLTAGE [22:7] (U3.13) |
| TPMI UFS_CONTROL | `sv.socket0.cbbN.base.tpmi.ufs_control` | MAX_RATIO/MIN_RATIO for VF point lock |
| CBB GPSB | `sv.socket0.cbbN.compute0.pma0.gpsb` | PMA voltage monitoring |

---

## Section 3: Reset, Power, and Clocking

- CCF GV state resets on warm reset; BIOS re-programs UFS_CONTROL during TPMI_INIT at next boot
- RING PLL and FIVR initialize to boot ratio; PCode GVFSM takes control after PH6
- UFS_STATUS.CURRENT_RATIO reflects live PLL state; reads are always current (no caching)
- V-first for frequency increase; PLL-first for frequency decrease -- mandatory for stable operation

---

## Section 4: Programming Model

VF curve parameters are fused at manufacturing and propagated to TPMI during Phase 5 initialization. The `UFS_STATUS.CURRENT_VOLTAGE` field reports the instantaneous FIVR voltage in U3.13 fixed-point format (3 integer bits, 13 fractional bits). Validation uses TPMI ratio lock (MAX=MIN) to force each VF operating point in isolation.

---

## Section 5: Operational Behavior

The CBB CCF GVFSM runs autonomously each slow-loop (~1 ms) when in autonomous mode (MAX_RATIO > MIN_RATIO). The GVFSM:
1. Reads BW telemetry (CBO/SBO) and RAPL/RACL line from Primecode
2. Computes new CCF frequency target
3. Clamps to [MIN_RATIO, MAX_RATIO] from UFS_CONTROL
4. Executes V-first or PLL-first GV transition via FIVR + PLL
5. Updates UFS_STATUS.CURRENT_RATIO and CURRENT_VOLTAGE
6. Sends updated ratio to Primecode via HPM 0x1b

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| BIOS programs MAX < MIN | PCode reverts to fuse defaults; no GVFSM operation |
| Ratio request above P0 cap | Silently clamped to `UFS_HEADER.MAX_RATIO_CAP` (fuse-defined) |
| Ratio request below Pm floor | Silently clamped to `UFS_HEADER.MIN_RATIO_CAP` (fuse-defined) |
| Resolved freq violates bound | `UFS_STATUS.THROTTLE_COUNTER` increments 1x per 1 ms interval |
| Unused VF curve points | Repeat previous value or = 0 (end-of-curve semantics per fuse spec) |
| Per-FIVR voltage asymmetry | `CURRENT_VOLTAGE` reports max(8 FIVRs); individual FIVR voltages may differ |
| GVFSM stuck (busy bit set) | System hang risk; detect via UFS_STATUS GVFSM status bits |
| PEGA injection with HWP disabled | B2P mailbox rejects -- requires BIOS HWP enable |

---

## Section 7: Security / Safety / Policy

- TPMI UFS_CONTROL may be locked by BIOS before OS handoff; runtime modifications require BIOS unlock
- PEGA injection requires privilege level; restricted in production OS environments
- VF curves are fused at manufacturing; no runtime override is permitted for customer SKUs

---

## Section 8: References

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html) -- GVFSM, GV execution flow, V-first/F-first, 8-curve CCF VF support
- [GVFSM MAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/MAS/GVFSM/gvfsm_mas.html) -- GVFSM internal states, busy/done handshake, FIVR coordination
- [CBB P-State Stack HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html) -- CCF frequency managed by P-state stack; UFS_STATUS fields
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html) -- UFS_CONTROL, UFS_STATUS, UFS_HEADER field definitions; THROTTLE_COUNTER
- [Primecode Workpoint Architecture](https://docs.intel.com/documents/primecode/primecode_two/firmware%20architecture/flows%20-%20pm%20features/workpoint.html) -- TPMI init, UFS_CONTROL clip behavior, per-die register ownership
- [DMR PM Fuse Specification](https://docs.intel.com/documents/pm_doc/src/server/dmr/soc_pm_has/dmr_pm_fuses/dmr_fuse_specification.html) -- CBB CCF fused VF curve content, 8-curve structure, end-of-curve semantics
- [CBB CCP PM Integration HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCP%20HAS/cbb_cpp_has.html#vf-curves-grouping) -- VF curve grouping and per-FIVR structure
- [DMR Fabric DVFS HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html) -- CCF fabric frequency management context
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details) -- GPSB voltage telemetry
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- [Architectural TPMI Interface](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html#dmr-family) -- TPMI cluster layout
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP CCF ring scope
