# Memory Thermal > MR4

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [Memory Thermal](memory_thermal_main.md)

## Baseline (DMR)

### What is MR4 CLTT?
MR4-based CLTT uses per-DRAM die temperature sensors exposed via JEDEC DDR5 **Mode Register 4**
instead of DIMM TSOD sensors. Enables accurate DRAM junction temperature tracking, especially under
liquid cooling or non-uniform airflow. MC reads MR4 periodically (~128 ms); Primecode converts
3-bit JEDEC codes to Celsius (formula: `70 + 5 × mr4_code`) and writes `dimm_tsod_temp` MC registers.

### Topology
- MC → DDR mainband → MR4 read from each rank/sub-channel → `mr4temp_0/1` registers
- Primecode CLTT flow (1 ms timer): reads `mr4temp_*` → converts → writes `dimm_tsod_temp` → TPMI `OPC_DIMM_TEMPS`
- HPM `DIMM_TEMPERATURE_0/1` distributes to secondary IMH (multi-die)
- BIOS enables via `B2P WRITE_PCU_MISC_CONFIG[MR4_CLTT_ENABLE]`

### Operating Principle
MC takes MAX temp across DRAM devices per sub-channel. Primecode publishes to TPMI for OOB/PECI
readback. MC compares against thresholds and applies: BW throttle, 2× refresh, MEMHOT_OUT, or MEMTRIP.

### Boot-Time Init
BIOS programs thresholds (low/mid/high/memtrip), throttle levels, 2× refresh enables, selects CLTT
mode, and disables TSOD polling to prevent HW overwriting FW-written temperatures.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| MC CLTT engine | IMH | Reads MR4 via DDR mainband (~128 ms); takes per-sub-channel MAX; populates `mr4temp_0/1`; compares vs thresholds | DDR mainband MRR; `mr4temp_0/1` registers | DMR DDR5/MCR HAS §MR4-based CLTT |
| DDR5 DRAM | DIMM | Exposes per-die junction temperature via MR4[2:0] (3-bit JEDEC code); 2× refresh indicator | MR4 register over DDR mainband | JEDEC DDR5 spec |
| TPMI OPC block | IMH | Stores per-DIMM Celsius temps for OOB/PECI readback; target for HPM distribution | `OPC_DIMM_TEMPS` TPMI registers | DMR DDR5/MCR HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Primecode CLTT | `src/flow/cltt/` | 1 ms periodic: reads MC MR4 telemetry, converts JEDEC code to Celsius, writes MC dimm_tsod_temp, publishes TPMI, sends HPM | `collectTempPeriodicallyMr4Mode()`, `writeMcTemperatureRegisters()`, `publishTpmiTemps()`, `sendDimmTempOnHpm()` | Primecode CLTT flow |
| Primecode TPMI | `src/flow/tpmi/` | Exposes OPC_DIMM_TEMPS for OOB/BMC readback; accepts PECI writes if PECI mode enabled | `OpcTpmi::handleDimmTemps()` | Primecode TPMI handler |
| BIOS | Platform init | Selects CLTT mode, programs thresholds/throttle levels, disables TSOD polling | `B2P WRITE_PCU_MISC_CONFIG[MR4_CLTT_ENABLE]` | NWP BIOS HAS |
| PCode | CBB PUnit | Arbitrates MC thermal response with RAPL; MEMHOT/MEMTRIP routing via THERMTRIP_CONFIG_CFG | RAPL throttle integration | PCode flows |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| B2P mailbox `PCU_MISC_CONFIG` | `MR4_CLTT_ENABLE` bit | RW (BIOS) | Enables MR4-based CLTT mode | DMR DDR5/MCR HAS |
| TPMI `OPC_DIMM_TEMPS` | TPMI OPC offset | RW (BMC/OOB) / RO (read) | Per-DIMM temperatures in Celsius for OOB readback | DMR DDR5/MCR HAS |
| MC `dimm_temp_thresh` | MCHBAR GPSB | RW (BIOS) | Low/mid/high/memtrip throttle thresholds per DIMM | DMR DDR5/MCR HAS |
| MC `mr4temp_0/1` | MCHBAR GPSB | RO | Raw MR4 3-bit code per rank per sub-channel | DMR DDR5/MCR HAS |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| MR4 polling period | ~128 ms (MC hardware) | DMR DDR5/MCR HAS |
| Primecode CLTT timer | 1 ms periodic | Primecode CLTT flow |
| JEDEC MR4 conversion formula | temp_°C = 70 + 5 × mr4_code (`JEDEC_MIN_ENCODED_MR4=70`, `JEDEC_STEP_ENCODED_MR4=5`) | Primecode CLTT source |
| 2× refresh trigger | MR4 code ≥ 2× refresh threshold (BIOS programmed) | JEDEC DDR5 spec |
| Throttle BW window | 1–4 s (BIOS programmed `dimm_bw_thrt.throttle_bw_window`) | DMR DDR5/MCR HAS |
| NWP delta | Carried from DMR; NIO as sole IMH host | NWP PM MAS |

## NWP Delta

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| Feature supported | ✅ Carried from DMR | NWP PM MAS |
| IMH topology | Single NIO (NWP IMH); HPM `DIMM_TEMPERATURE` secondary-die path not applicable (single die) | NWP PM MAS |
| MR4 polling / conversion | Identical to DMR | DMR DDR5/MCR HAS |
| TPMI OPC_DIMM_TEMPS | NWP SP: 8 channels; NWP AP: up to 16 channels | OPC_HEADER.MEMORY_CHANNELS |

## Legacy (Human-Curated Reference)

*All original content preserved below for reference.*

### Architecture Summary

MR4-based CLTT (Closed Loop Thermal Throttling) uses **per-DRAM-device temperature sensors** exposed through the JEDEC DDR5 **Mode Register 4** instead of relying on DIMM TSOD sensors. MR4 sensors reside inside the DRAM die, tracking junction temperature more directly than TSOD — especially important under liquid cooling or non-uniform airflow where TSOD-to-DRAM delta can vary.

The feature involves three actors:

1. **Memory Controller (MC)** — periodically reads MR4 over the DDR mainband (~128 ms default), extracts per-rank 3-bit temperature codes, takes the per-sub-channel max, and populates `mr4temp_0/1` registers. The MC also applies throttle/refresh actions based on BIOS-programmed thresholds.
2. **Primecode firmware (CLTT flow)** — runs a 1 ms periodic timer that reads MR4 telemetry from MC registers, decodes JEDEC values to Celsius, writes results to `dimm_tsod_temp` MC registers, publishes to TPMI `OPC_DIMM_TEMPS`, and sends inter-die HPM messages for multi-die coordination.
3. **BIOS** — programs thresholds (low/mid/high/memtrip), throttle levels, 2x refresh enables, and selects the CLTT mode (MR4 vs TSOD vs PECI) via `B2P WRITE_PCU_MISC_CONFIG[MR4_CLTT_ENABLE]`.

#### JEDEC MR4 Temperature Encoding (DDR5)

| MR4[2:0] | Temp Range (Wide=0) | Temp Range (Wide=1) | Refresh Multiplier |
|-----------|---------------------|---------------------|-------------------|
| 0 (`LOW_TEMP`) | RFU | < 75 °C | 4× tREFI |
| 1 | < 80 °C | 75–80 °C | 4× tREFI |
| 2 | 80–85 °C | 80–85 °C | 2× tREFI |
| 3 | 85–90 °C | 85–90 °C | 1× tREFI (nominal) |
| 5 | > 95 °C | 95–100 °C | 0.5× tREFI |
| 6 | RFU | > 100 °C | 0.25× tREFI + AC derating |
| 7 (`HIGH_TEMP`) | RFU | RFU | Beyond operating limit |

Firmware conversion formula: **`temperature_celsius = 70 + 5 × mr4_encoded_value`** (constants: `JEDEC_MIN_ENCODED_MR4 = 70`, `JEDEC_STEP_ENCODED_MR4 = 5`).

### Execution Flow

```
1. BIOS Configuration
   ├─ Programs PCU_MISC_CONFIG[MR4_CLTT_ENABLE] via B2P mailbox
   ├─ Programs per-DIMM thresholds: low / mid / high / memtrip
   ├─ Programs throttle levels: THRT_MID / THRT_HIGH / THRT_CRIT
   ├─ Programs 2x refresh threshold and per-subch enables
   └─ Disables TSOD polling (to avoid overwriting FW-written temps)

2. MC Periodic MR4 Read (~128 ms)
   ├─ Reads MR4 over DDR mainband from each rank/sub-channel
   ├─ Takes MAX across DRAM devices per sub-channel
   └─ Populates mr4temp_0.mr4temp_rank0..3, mr4temp_1.mr4temp_rank0..3

3. Primecode CLTT Flow (1 ms periodic timer)
   ├─ CLTT::collectTempPeriodicallyMr4Mode()
   │   ├─ Reads MC telemetry entries (MC_W/E_MR4_TEMPxy)
   │   ├─ Takes MAX of all 4 ranks per DIMM
   │   └─ Converts via mr4TempToMaxCelsius() → Celsius
   ├─ CLTT::writeMcTemperatureRegisters() → writes dimm_tsod_temp0 via IOSF
   ├─ CLTT::publishTpmiTemps() → writes OPC_DIMM_TEMPS TPMI registers
   └─ CLTT::sendDimmTempOnHpm() → HPM DIMM_TEMPERATURE_0/1 to secondary IMH

4. MC Thermal Response
   ├─ Compares temps vs programmed thresholds
   ├─ Applies per-DIMM bandwidth throttling (1–4 s window)
   ├─ Triggers 2x refresh if temp ≥ 2x threshold
   ├─ Asserts MEMHOT_OUT if temp ≥ selected threshold
   └─ Asserts MEMTRIP if temp ≥ memtrip threshold

5. OS / Platform Observable
   ├─ TPMI OPC_DIMM_TEMPS readable via OOB/PECI
   ├─ DDR_THERM_STATUS.DDR_MAX_TEMPERATURE updated
   ├─ MEMHOT/MEMTRIP platform signals
   └─ Bandwidth reduction observable via PMONs
```

### Key Registers & Interfaces

#### MC Registers (per MC, MCHBAR GPSB)

| Register | Key Fields | Description |
|----------|-----------|-------------|
| `mr4temp_0` | `mr4temp_rank0..3` (3-bit each) | MR4 reading per rank, sub-channel 0 |
| `mr4temp_1` | `mr4temp_rank0..3` (3-bit each) | MR4 reading per rank, sub-channel 1 |
| `RANK_TEMPERATURE` | `SCH0_RANK0/1_TEMP`, `SCH1_RANK0/1_TEMP` (8-bit) | Temperature per rank per sub-channel (default 0x9) |
| `PM_CONFIG_THERM_STATUS` | `DISABLE_DRAM_TS`, `MIN_REF_RATE`, `MAX_REF_RATE`, `MR4_PERIOD` | MR4 polling config and refresh rate bounds |
| `thr_ctrl0` | `mr4_temp_low/mid/high_maxthreshold` | Per-DIMM throttle thresholds |
| `thr_ctrl0` | `mr4_temp_2xrefresh_threshold` | 2x refresh trigger threshold |
| `dimm_temp_ev_ctrl_0/1` | `thr_2xrefresh_en_sch0/1` | Per-DIMM per-subch 2x refresh enable |
| `dimm_bw_thrt` | `throttle_bw_window` | Throttle window length |
| `dimm_temp_thresh` | `dimm_temp_memtrip_threshold` | MEMTRIP threshold (shared per MC) |
| `dimm_temp_ev_ctrl_0/1` | `temp_memhotout_sel` | Threshold selection for MEMHOT_OUT |
| `memhot_ext_thrt` | `throttle_exmemhot_level` | External MEMHOT throttle level |
| `refresh_ctrl0` | `ref_2xrefsb_en` | Same-bank refresh in 2x mode |
| `dimm_temp_snapshot` | `dimm_temp_sch0/1`, `dimm_refresh_rate` | Snapshot of DIMM temp and refresh rate |

#### Primecode Interfaces

| Interface | ID / Path | Description |
|-----------|----------|-------------|
| HPM opcode | `DIMM_TEMPERATURE_0` (0x29) | Inter-die DIMM temp exchange (DIMM_TEMP_0..15) |
| HPM opcode | `DIMM_TEMPERATURE_1` (0x2A) | Inter-die DIMM temp exchange (continued) |
| TPMI register | `OPC_DIMM_TEMPS` | Published DIMM temps readable by BMC/PECI |
| B2P mailbox | `WRITE_PCU_MISC_CONFIG` | MR4_CLTT_ENABLE / CLTT_PECI_ENABLE bits |
| Telemetry entry | `MC_W/E_MR4_TEMPxy` | MC telemetry array entries for MR4 |
| Fuse | `MR4_CLTT` | Feature fuse for MR4 CLTT |
| Scratchpad | `SCRATCHPAD8[12]` | MR4 recovery bit |

#### PCode Trace Messages (MEMORY group)

| Trace Message | Fields | Description |
|--------------|--------|-------------|
| `DDR_MR4_RAW_RANK_TEMP_FROM_MC` | `DIMM0_MR4_RANK0/1_TEMP`, `DIMM1_MR4_RANK0/1_TEMP`, `CHANNEL_SELECT` | Raw MR4 values per rank per channel |
| `DDR_HOTTEST` | `ABSOLUTE`, `RELATIVE` | Hottest DIMM temp (max across all samples) |
| `DDR_ENERGY_STATUS` | `DATA` | DDR energy counter value |

#### CLTT Operating Modes

| Mode Enum | Description |
|-----------|-------------|
| `MR4_ENABLED` | MC reads MR4 → Primecode CLTT converts & distributes |
| `MR4_DISABLED_TSOD_ENABLED` | SPD I3C TSOD polling for DIMM temps |
| `MR4_DISABLED_PECI_ENABLED` | BMC pushes temps via PECI → TPMI OPC_DIMM_TEMPS |

#### PythonSV Validation Functions

| Function | Module | Description |
|----------|--------|-------------|
| `show_mr4_temp()` | `mc/dmr_mc_show.py` | Display DIMM temperatures per slot from MR4 |
| `show_mr4_refresh_rate_encoding()` | `mc/dmr_mc_show.py` | Show MR4 CLTT refresh settings |
| `show_twox_refresh()` | `mc/dmr_mc_show.py` | Show 2X Refresh CLTT configuration |
| `dmr_maint_harasser(..., mr4=True)` | `mc/dmr_maint_harasser.py` | Harass MR4 polling rate |
| `dmr_refresh_harasser(..., dimm_temp=True)` | `mc/dmr_refresh_harasser.py` | Harass refresh rate + MR4 2x temp toggling |
| `get_mr4_dimm_temp()` | `mc/dmr_mc_get.py` | Read MR4 DIMM temp for specific slot/subch |
| `is_mr4_wide_range()` | `mc/dmr_mc_info.py` | Check if DIMM supports MR4 wide range mode |
| `decode_mr4_to_temp_range()` | `mc/dmr_mc_ub.py` | Decode MR4 value to temperature range string |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR DDR5/MCR - MR4 CLTT](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html#mr4-based-cltt) | MR4 CLTT architecture |
| HAS | [DMR Thermal HAS (IMH)](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#itd) | IMH thermal management |
| HAS | [Socket Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Cross-product socket thermal |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS — memory thermal |
| Primecode src | `src/flow/cltt/cltt_common/v2_0/cltt.hpp` / `cltt.cpp` | Core CLTT flow (MR4 mode, TSOD mode, HPM, TPMI) |
| Primecode src | `src/flow/cltt/cltt_io_base/v1_0/pecicltt_mailbox_base.hpp` | PECI CLTT PCS mailbox handler |
| Primecode src | `src/flow/cltt/cltt_io/v1_0/pecicltt_mailbox.hpp` | IO-specific CLTT mailbox + reverse mapping |
| Primecode src | `src/flow/cltt/cltt_compute/v1_0/cltt_compute_leaf.hpp` | Compute-leaf CLTT (TSOD via SPD polling) |
| Primecode src | `src/ip/spd_i3c/v2_0/spd_i3c.hpp` | SPD I3C IP — `programClassicCLTT()` |
| Primecode src | `src/ip/fuse/v2_0/fuses.xml` | `MR4_CLTT` fuse feature definition |
| PCode src | Not in pcode-cbb-a0 | MR4 is entirely IMH-side (Primecode) — PCode only has trace defs |
| PCode trace | `source/trace/punit_trace.xml` | `DDR_MR4_RAW_RANK_TEMP_FROM_MC`, `DDR_HOTTEST` |
| Test scripts | `mc/dmr_mc_show.py::show_mr4_temp()` | PythonSV MR4 temp display |
| Test scripts | `mc/dmr_maint_harasser.py` | Maintenance harasser with MR4 toggle |
| Test scripts | `mc/dmr_refresh_harasser.py` | Refresh harasser with DIMM temp check |

### Related Sightings
<!-- No MR4-specific sightings catalogued yet — populate as NWP silicon debug progresses -->

