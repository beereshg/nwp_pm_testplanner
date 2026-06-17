# Memory Thermal > Memtrip

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [Memory Thermal](memory_thermal_main.md)

## Baseline (DMR)

### What is MEMTRIP?
MEMTRIP is the emergency thermal shutdown mechanism for DRAM. When DIMM temperature exceeds
`dimm_temp_memtrip_threshold`, the MC asserts `MEMTRIP#` which propagates via `THERMTRIP_CONFIG_CFG`
OR-tree to either `xxthermtrip_n` (full platform power-off, **enabled by default**) or `xxmemtrip_n`
(platform-level event). Memtrip→Thermtrip propagation is **armed by default** (bit default=1).

### Topology
- MC detects temp ≥ threshold → asserts `memtrip[0/1]` signal (one per MC channel group)
- `THERMTRIP_CONFIG_CFG` OR-tree: `memtrip0/1_to_xxthermtrip_n_en` → `xxthermtrip_n` → PSU power-off
- `memtrip0/1_to_xxmemtrip_n_en` → `xxmemtrip_n` → platform memtrip (controlled shutdown)
- Reset sequence arms trip at step 61 (`HWRS_RESET_COMPLETE`) via `scu_trip_enable`

### Operating Principle
Same temperature sources as MEMHOT (MR4/TSOD/PECI write `dimm_temp_snapshot`). MC compares against
8-bit `dimm_temp_memtrip_threshold` (default 0xFF = disabled) and 3-bit `mr4_temp_memtrip_threshold`.
BIOS must explicitly clear thermtrip enable bits to prevent full power-off.

### Boot-Time Init
Reset step 61: Primecode sets `scu_trip_enable` in `HWRS_SEQ_CONTROL`, arming all trip propagation.
BIOS programs thresholds and `THERMTRIP_CONFIG_CFG` routing enables.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| MC thermal engine | IMH | Compares `dimm_temp_snapshot` vs `dimm_temp_memtrip_threshold`; compares MR4 code vs `mr4_temp_memtrip_threshold`; asserts `memtrip[0/1]` | memtrip signal to Punit OR-tree | DMR DDR5/MCR HAS |
| Punit OR-tree | CBB PUnit | `THERMTRIP_CONFIG_CFG` routes memtrip → `xxthermtrip_n` (default enabled) or `xxmemtrip_n` | `memtrip0/1_to_xxthermtrip_n_en`, `memtrip0/1_to_xxmemtrip_n_en` | SoC PM HAS |
| Platform PSU | Platform | Receives `xxthermtrip_n` → immediate power cut; receives `xxmemtrip_n` → BMC-controlled shutdown | THERMTRIP# / MEMTRIP# platform pins | Platform HW spec |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Primecode reset handler | `src/flow/reset/` | Arms trip propagation at reset step 61 (`HWRS_RESET_COMPLETE`) via `scu_trip_enable` in `HWRS_SEQ_CONTROL` | Reset step 61 | Primecode reset sequence |
| Primecode CLTT | `src/flow/cltt/` | Writes `dimm_temp_snapshot` from MR4/PECI source; indirect driver of memtrip threshold comparison | `writeMcTemperatureRegisters()` | Primecode CLTT flow |
| BIOS | Platform init | Programs `dimm_temp_memtrip_threshold`, `mr4_temp_memtrip_threshold`, and `THERMTRIP_CONFIG_CFG` routing enables | `B2P WRITE_PCU_MISC_CONFIG`, THERMTRIP_CONFIG_CFG | NWP BIOS HAS |
| PCode | CBB PUnit | Receives thermtrip signal; logs in Machine Check / IERR telemetry | IERR / THERMTRIP logging | PCode flows |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MC `dimm_temp_thresh` bits [31:24] | MCHBAR GPSB | RW (BIOS) | `dimm_temp_memtrip_threshold` (8-bit, default 0xFF = disabled) | DMR DDR5/MCR HAS |
| MC `mr4_temp_memtrip_threshold` bits [14:12] | MCHBAR GPSB | RW (BIOS) | 3-bit MR4 code threshold for memtrip (default 0x6) | DMR DDR5/MCR HAS |
| `THERMTRIP_CONFIG_CFG` offset 0x4E0 | Punit GPSB | RW (BIOS) | Bits [4:7]: memtrip0/1→thermtrip/memtrip routing enables (default all=1) | SoC PM HAS |
| `HWRS_SEQ_CONTROL.scu_trip_enable` | Punit GPSB | RW (Primecode reset) | Arms trip propagation at reset step 61 | Primecode reset sequence |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| Default memtrip threshold | 0xFF (disabled; BIOS must program real value) | DMR DDR5/MCR HAS |
| MR4 code threshold | 0x6 (default) | DMR DDR5/MCR HAS |
| Memtrip→Thermtrip default | Enabled (bit default=1); BIOS must clear to prevent full power-off | THERMTRIP_CONFIG_CFG |
| Trip propagation arm point | Reset step 61 (`HWRS_RESET_COMPLETE`) | Primecode reset sequence |
| MEMTRIP disabled test | Verify no thermtrip when temp ≥ threshold with threshold=0xFF or routing bits cleared; CLTT throttle still active | NWP PM test plan |

## NWP Delta

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| Feature supported | ✅ Carried from DMR | NWP PM MAS |
| Thermtrip propagation | Same OR-tree mechanism; THERMTRIP_CONFIG_CFG bits identical | SoC PM HAS |
| IMH topology | Single NIO; memtrip[0/1] per MC channel group unchanged | NWP PM MAS |

## Legacy (Human-Curated Reference)

*All original content preserved below for reference.*

### Architecture Summary

**MEMTRIP** is the emergency thermal shutdown mechanism for DRAM. When DIMM temperature exceeds the absolute maximum operating threshold (`dimm_temp_memtrip_threshold`), the MC asserts a `MEMTRIP#` signal. This signal can propagate to a platform-level **THERMTRIP** (complete system power-off) to prevent permanent DRAM damage.

#### Signal Flow
1. **MC detects critical temperature** → asserts internal `memtrip[0/1]` signal (one per MC channel group)
2. **Punit THERMTRIP_CONFIG_CFG** OR-tree routes:
   - `memtrip0/1_to_xxthermtrip_n_en` → drives `xxthermtrip_n` pin → platform power-off
   - `memtrip0/1_to_xxmemtrip_n_en` → drives `xxmemtrip_n` pin → platform-level memtrip (not full thermtrip)
3. **Reset sequence** enables this propagation via `scu_trip_enable` in `HWRS_SEQ_CONTROL` at step 61 (HWRS_RESET_COMPLETE)

#### MR4-based Memtrip
When CLTT is in MR4 mode, Primecode firmware reads JEDEC MR4 temperature codes and converts to Celsius. The MR4 spec defines a 3-bit `mr4_temp_memtrip_threshold` field (bits 14:12, default 0x6) that maps MR4 temperature code → memtrip. When the MR4-reported temperature code meets or exceeds this threshold, the MC triggers a memtrip event.

#### PECI-based Memtrip
When CLTT is in PECI mode (`MR4_DISABLED_PECI_ENABLED`), the BMC pushes DIMM temperatures via TPMI. Primecode writes these to MC `dimm_temp_snapshot` registers. The MC compares against `dimm_temp_memtrip_threshold` (8-bit, default 0xFF = effectively disabled). If temp ≥ threshold, MC asserts memtrip.

#### Memtrip-to-Thermtrip Escalation
The `THERMTRIP_CONFIG_CFG` register (offset 0x4E0 in Punit) implements an OR-tree that aggregates multiple trip sources. Memtrip is one input alongside DTS thermtrip, PECI thermtrip, etc. When `memtrip0_to_xxthermtrip_n_en=1` (default), a memtrip assertion on MC channel 0 directly causes a full platform thermtrip — an immediate, unrecoverable power-down.

Key: Memtrip → Thermtrip is **enabled by default** (bit default = 1). To prevent memtrip from escalating to thermtrip, BIOS must explicitly clear these enable bits. The `HWRS_SEQ_CONTROL.scu_trip_enable` bit arms the entire trip propagation path during reset step 61.

#### Memtrip Disabled (Test: "Disables Memtrip MR4-based")
When Memtrip is disabled, the MC does not assert `memtrip#` even if DIMM temperature exceeds the memtrip threshold. The test verifies that: (a) MR4 temp at or above memtrip threshold does not trigger memtrip/thermtrip, and (b) normal CLTT throttling (THRT_MID/HI/CRIT) continues to operate. The disable path is tested by setting `dimm_temp_memtrip_threshold=0xFF` or clearing the relevant enable bits.

### Execution Flow

```
1. BIOS Configuration (Reset Phase 5)
   ├─ Programs MC thresholds: dimm_temp_thresh.dimm_temp_memtrip_threshold (8-bit)
   ├─ Programs MR4 threshold: mr4_temp_memtrip_threshold (3-bit code)
   ├─ Programs THERMTRIP_CONFIG_CFG.memtrip0/1_to_xxthermtrip_n_en
   ├─ Programs THERMTRIP_CONFIG_CFG.memtrip0/1_to_xxmemtrip_n_en
   └─ Primecode enables trip propagation: scu_trip_enable in HWRS_SEQ_CONTROL (step 61)

2. Temperature Source Path
   ├─ MR4 mode: MC reads MR4 → Primecode writes dimm_temp_snapshot → MC compares
   ├─ TSOD mode: MC reads TSOD via I3C → auto-populates dimm_temp_snapshot → MC compares
   └─ PECI mode: BMC pushes via TPMI → Primecode writes dimm_temp_snapshot → MC compares

3. MC Trip Detection
   ├─ MC compares dimm_temp_snapshot vs dimm_temp_memtrip_threshold
   ├─ (MR4 mode also checks MR4 code vs mr4_temp_memtrip_threshold)
   └─ If temp ≥ threshold → MC asserts memtrip signal

4. Punit OR-Tree Propagation (THERMTRIP_CONFIG_CFG)
   ├─ memtrip0_to_xxthermtrip_n_en=1 → memtrip0 → xxthermtrip_n → FULL POWER OFF
   ├─ memtrip1_to_xxthermtrip_n_en=1 → memtrip1 → xxthermtrip_n → FULL POWER OFF
   ├─ memtrip0_to_xxmemtrip_n_en=1 → memtrip0 → xxmemtrip_n → platform memtrip
   └─ memtrip1_to_xxmemtrip_n_en=1 → memtrip1 → xxmemtrip_n → platform memtrip

5. Platform Response
   ├─ THERMTRIP: Immediate, unrecoverable power-down (PSU cuts power)
   ├─ MEMTRIP: Platform-level memtrip — BMC logs event, may trigger controlled shutdown
   └─ Both logged in Machine Check / IERR telemetry
```

### Key Registers & Interfaces

#### MC Registers (per MC, MCHBAR GPSB)

| Register | Key Fields | Description |
|----------|-----------|-------------|
| `dimm_temp_thresh` | `dimm_temp_memtrip_threshold` (bits 31:24, 8-bit, default 0xFF) | Absolute max DIMM temp threshold for memtrip (Celsius). 0xFF = effectively disabled |
| `mr4_temp_memtrip_threshold` | bits 14:12 (3-bit, default 0x6) | MR4 temperature code threshold for memtrip (JEDEC MR4 encoding) |
| `dimm_temp_snapshot_0/1` | `dimm_temp_sch0/1` | Current DIMM temperature read by MC (Celsius, 0.5°C resolution) |
| `dimm_temp_ev_ctrl_0` | `temp_memhotout_sel` | Which threshold triggers MEMHOT_OUT (can select MemTrip level) |

#### Punit Registers (Punit GPSB, punit_MsgMem_p230_b2)

| Register | Key Fields | Description |
|----------|-----------|-------------|
| `THERMTRIP_CONFIG_CFG` (0x4E0) | `memtrip0_to_xxthermtrip_n_en` (bit 4, default 1) | Route MC0 memtrip → thermtrip output pin |
| `THERMTRIP_CONFIG_CFG` (0x4E0) | `memtrip1_to_xxthermtrip_n_en` (bit 5, default 1) | Route MC1 memtrip → thermtrip output pin |
| `THERMTRIP_CONFIG_CFG` (0x4E0) | `memtrip0_to_xxmemtrip_n_en` (bit 6, default 1) | Route MC0 memtrip → memtrip output pin |
| `THERMTRIP_CONFIG_CFG` (0x4E0) | `memtrip1_to_xxmemtrip_n_en` (bit 7, default 1) | Route MC1 memtrip → memtrip output pin |

#### HWRS / Reset Registers

| Register | Key Fields | Description |
|----------|-----------|-------------|
| `HWRS_SEQ_CONTROL` | `scu_trip_enable` | Arms memtrip/thermtrip propagation during reset (set at step 61) |
| `enable_xxmemtrip_n` | bit 10 in punit_MsgCr_p230_GPSB_d | Master enable for xxmemtrip_n output |

#### Temperature-to-Action Mapping (shared with Memhot)

| DIMM Temperature vs Threshold | MC / Platform Action |
|---|---|
| `Temp < Temp_Lo` | No throttle |
| `Temp_Lo ≤ Temp < Temp_Mid` | BW throttle at `THRT_MID` level |
| `Temp_Mid ≤ Temp < Temp_Hi` | BW throttle at `THRT_HI` level |
| `Temp_Hi ≤ Temp < Temp_MemTrip` | BW throttle at `THRT_CRIT` level + MEMHOT_OUT |
| **`Temp ≥ Temp_MemTrip`** | **MEMTRIP asserted → THERMTRIP (power-off)** |

#### Primecode Interfaces

| Interface | ID / Path | Description |
|-----------|----------|-------------|
| CLTT flow | `CLTT::writeMcTemperatureRegisters()` | Writes temps to MC dimm_temp_snapshot |
| CLTT flow | `CLTT::collectTempPeriodicallyMr4Mode()` | MR4 temp collection (1 ms periodic) |
| Reset seq | Step 61: `HWRS_RESET_COMPLETE` | Enables memtrip propagation (scu_trip_enable) |
| TPMI | `OPC_DIMM_TEMPS_0..3` | Published DIMM temps for OOB/PECI |
| Telemetry | `DDR_THERM_STATUS` | Reports current thermal throttle state |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR DDR5/MCR - MR4 CLTT](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html#mr4-based-cltt) | MR4 CLTT including memtrip thresholds |
| HAS | [DMR Thermal HAS (IMH)](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#itd) | IMH thermal management including trip |
| HAS | [Socket Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Cross-product socket thermal (thermtrip OR-tree) |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS — memory thermal |
| Primecode src | `src/flow/cltt/cltt_common/v2_0/cltt.hpp` / `cltt.cpp` | Core CLTT flow (MR4, TSOD, HPM, TPMI) |
| Primecode cfg | `src/cfgdata/*/ip_headers/mc_MsgMem_GPSB.hpp` | `dimm_temp_memtrip_threshold`, `mr4_temp_memtrip_threshold` |
| Primecode cfg | `src/cfgdata/*/ip_headers/punit_MsgMem_p230_b2_GPSB.hpp` | `THERMTRIP_CONFIG_CFG` fields |
| Reset seq | `src/cfgdata/nwp_imh/v1_0/reset_seq.xml` (step 61) | `scu_trip_enable` in HWRS_RESET_COMPLETE |
| Cross-ref | [MR4](mr4.md) | MR4-based temp source for memtrip |
| Cross-ref | [PECI](peci.md) | PECI-based temp source for memtrip |
| Cross-ref | [Memhot](memhot.md) | MEMHOT threshold band below memtrip |
| Cross-ref | [DDRIO](ddrio.md) | DDRIO thermal throttling |

#### Test Case Architecture Notes

| Test | What It Validates |
|------|-------------------|
| **Disables Memtrip MR4** (22022421425) | Disable memtrip → MR4 temp at/above memtrip threshold does NOT trigger memtrip/thermtrip; normal CLTT throttling still active |
| **MR4 based** (22022421434) | MR4 mode: raise MR4 code above `mr4_temp_memtrip_threshold` → verify memtrip assertion and expected platform response |
| **Memtrip to Thermtrip** (22022421437) | End-to-end: trigger memtrip → verify THERMTRIP_CONFIG_CFG OR-tree propagates to `xxthermtrip_n` pin → platform power-off |
| **PECI based** (22022421439) | PECI mode: push temp above `dimm_temp_memtrip_threshold` via TPMI → verify memtrip triggers |

### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->

