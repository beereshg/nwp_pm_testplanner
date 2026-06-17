# Memory Thermal > PECI

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [Memory Thermal](memory_thermal_main.md)

## Baseline (DMR)

### What is PECI CLTT?
PECI-based CLTT is the mode where an **external platform controller (BMC)** supplies DIMM temperature
values to the CPU for memory thermal management. Intended for platforms where TSOD/MR4 polling is
unsuitable. BMC pushes temps via TPMI `OPC_DIMM_TEMPS`; Primecode validates `CLTT_PECI_ENABLE`, clips
to 0–127°C, writes MC `dimm_temp_snapshot`, and distributes via HPM to secondary IMH.

### Topology
- BMC/PLDM → TPMI `OPC_DIMM_TEMPS_[0..3]` → Primecode `handleDimmTemps()` → MC `dimm_temp_snapshot`
- MC compares vs thresholds → throttle / 2× refresh / MEMHOT / MEMTRIP
- Primecode → HPM `DIMM_TEMPERATURE_0/1` → remote IMH (multi-die)
- Legacy: PECI PCS-14 `WRPKGCONFIG` alternate write path (GNR-compatible)

### Operating Principle
Mutually exclusive with MR4/TSOD modes. BIOS disables TSOD polling to prevent HW overwriting
FW-written temps. Primecode rejects writes unless `CLTT_PECI_ENABLE` set (unauthorized = error 0x90).

### Boot-Time Init
BIOS programs `B2P WRITE_PCU_MISC_CONFIG[CLTT_PECI_ENABLE]`, thresholds/levels, disables TSOD polling,
programs `OPC_HEADER.MEMORY_CHANNELS` (DMR-AP: 16, DMR-SP: 8).

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| TPMI OPC block | IMH | Receives BMC-written DIMM temps; exposes `OPC_DIMM_TEMPS_[0..3]`; triggers Primecode handler | TPMI write interrupt to Primecode | DMR DDR5/MCR HAS |
| MC CLTT engine | IMH | Compares `dimm_temp_snapshot` (written by Primecode) vs thresholds; applies throttle/refresh/MEMHOT/MEMTRIP | `dimm_temp_snapshot_0/1`, threshold registers | DMR DDR5/MCR HAS |
| PECI interface | SoC | Legacy PCS-14 alternate write path for GNR-compatible BMC flows | PECI RDPKGCONFIG/WRPKGCONFIG PCS-14 | PECI HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Primecode TPMI handler | `src/flow/tpmi/` | Triggered on TPMI `OPC_DIMM_TEMPS` write; validates CLTT_PECI_ENABLE; calls CLTT::storeTpmiClttTemps() | `OpcTpmi::handleDimmTemps()` | Primecode TPMI handler |
| Primecode CLTT | `src/flow/cltt/` | Clips temps (max 127°C); writes `dimm_temp_snapshot` via IOSF; sends HPM to secondary IMH; publishes TPMI readback | `writeMcTemperatureRegisters()`, `sendDimmTempOnHpm()`, `publishTpmiTemps()` | Primecode CLTT flow |
| BIOS | Platform init | Enables PECI CLTT, programs thresholds, disables TSOD polling, programs MEMORY_CHANNELS | `CLTT_PECI_ENABLE`, `OPC_HEADER.MEMORY_CHANNELS` | NWP BIOS HAS |
| BMC | Platform | Enumerates valid channels from `OPC_HEADER.MEMORY_CHANNELS`; periodically pushes DIMM temps via TPMI | `OPC_DIMM_TEMPS_[0..3]` writes | Platform BMC FW |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| B2P mailbox `PCU_MISC_CONFIG` | `CLTT_PECI_ENABLE` bit | RW (BIOS) | Enables PECI CLTT mode; gates Primecode acceptance of BMC temp writes | DMR DDR5/MCR HAS |
| TPMI `OPC_DIMM_TEMPS_[0..3]` | TPMI OPC offset | RW (BMC) | Per-DIMM U8.0 temperatures (0–127°C); 2 DIMMs per 16-bit word per channel | DMR DDR5/MCR HAS |
| TPMI `OPC_HEADER.MEMORY_CHANNELS` | TPMI OPC offset | RO | Number of valid memory channels (DMR-AP: 16, SP: 8) | DMR DDR5/MCR HAS |
| PECI PCS-14 | PECI `WRPKGCONFIG` index 14 | RW (BMC, legacy) | Alternate temp write path; same security gate applies | PECI HAS |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| Temperature format | U8.0 °C, clipped to 0–127°C | Primecode CLTT source |
| Security gate | `CLTT_PECI_ENABLE` must be set; unauthorized writes return error 0x90 | Primecode TPMI handler |
| Memory channels (DMR-SP) | 8 channels (`OPC_HEADER.MEMORY_CHANNELS`) | DMR DDR5/MCR HAS |
| Memory channels (DMR-AP) | 16 channels | DMR DDR5/MCR HAS |
| Mutual exclusion | PECI CLTT mode disables TSOD polling; mutually exclusive with MR4/TSOD | DMR DDR5/MCR HAS |
| PECI disabled test | Verifies BMC writes rejected when CLTT_PECI_ENABLE=0 | NWP PM test plan |

## NWP Delta

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| Feature supported | ✅ Carried from DMR | NWP PM MAS |
| MEMORY_CHANNELS | NWP SP: 8 channels; NWP AP: up to 16 | OPC_HEADER.MEMORY_CHANNELS |
| HPM secondary-die distribution | Not applicable for single-die NWP | NWP PM MAS |
| PECI PCS-14 path | Available for GNR-compatible BMC | PECI HAS |

## Legacy (Human-Curated Reference)

*All original content preserved below for reference.*

### Architecture Summary

PECI-based CLTT (Closed Loop Thermal Throttling with PECI) is the mode where an **external platform controller** (typically the BMC) supplies DIMM temperature values to the CPU for memory thermal management. This is intended for platforms where normal DIMM TSOD polling is unavailable or unsuitable — e.g., DIMMs without TSOD, SPD-I3C not connected, or platform-estimated temperatures.

The feature involves four actors:

1. **BMC / Platform Controller** — estimates or measures DIMM temperatures externally, then pushes them to the CPU via TPMI OPC registers (DMR) or legacy PECI PCS-14 (GNR and earlier).
2. **Primecode firmware (CLTT flow + TPMI handler)** — receives BMC-written temperatures from TPMI `OPC_DIMM_TEMPS` registers, validates the PECI CLTT enable, clips values to 0–127°C, and forwards to MC temperature registers. Also distributes temps to secondary die via HPM.
3. **Memory Controller (MC)** — treats PECI-provided temperatures identically to TSOD/MR4 sources: compares against programmed low/mid/high/memtrip thresholds and applies bandwidth throttling, 2x refresh, MEMHOT, or MEMTRIP.
4. **BIOS** — programs MC throttle thresholds and levels, enables PECI CLTT mode via `B2P WRITE_PCU_MISC_CONFIG[CLTT_PECI_ENABLE]`, and must disable TSOD polling to prevent HW from overwriting FW-written temperatures.

#### Data Flow Summary

```
BMC/PLDM → TPMI OPC_DIMM_TEMPS_[0..3] → Primecode handleDimmTemps()
    → storeTpmiClttTemps() → writeMcTemperatureRegisters() → MC dimm_temp_snapshot_0/1
    → MC compares vs thresholds → throttle / 2x refresh / MEMHOT / MEMTRIP

Also: Primecode → sendDimmTempOnHpm() → remote IMH (multi-die)
      Primecode → publishTpmiTemps() → TPMI (readback for OOB)
      PECI RDPKGCONFIG PCS-14 → clttDimmTempPcsRead() → returns max DIMM temp
      PECI WRPKGCONFIG PCS-14 → clttDimmTempPcsWrite() → alternate write path
```

#### PECI CLTT vs MR4 / TSOD

| Property | PECI CLTT | MR4 CLTT | TSOD CLTT |
|----------|-----------|----------|-----------|
| Temp source | BMC-estimated, pushed via TPMI/PECI | MC reads DDR5 MR4 via mainband | MC reads TSOD via SPD I3C |
| Enable bit | `PCU_MISC_CONFIG[CLTT_PECI_ENABLE]` | `PCU_MISC_CONFIG[MR4_CLTT_ENABLE]` | Default BIOS config |
| Temp format | U8.0 (°C, 0–127 range) | 3-bit JEDEC MR4 code → converted | U8.0 from TSOD |
| Polling | BMC-driven (external push) | MC periodic (~128 ms) | MC periodic via I3C |
| Mode enum | `MR4_DISABLED_PECI_ENABLED = 1` | `MR4_ENABLED = 0` | `MR4_DISABLED_TSOD_ENABLED = 2` |
| Mutual exclusion | Mutually exclusive with TSOD/MR4 | Mutually exclusive with PECI/TSOD | Mutually exclusive with MR4/PECI |

#### Security Gate

PECI CLTT is **opt-in**. Primecode rejects PCS-14 writes and TPMI temperature writes unless `PCU_MISC_CONFIG[CLTT_PECI_ENABLE]` is set. Unauthorized writes return error code `0x90`.

### Execution Flow

```
1. BIOS Configuration
   ├─ Programs PCU_MISC_CONFIG[CLTT_PECI_ENABLE] via B2P mailbox
   ├─ Programs per-DIMM thresholds: low / mid / high / memtrip
   ├─ Programs throttle levels: THRT_MID / THRT_HI / THRT_CRIT
   ├─ Programs throttle BW window (dimm_bw_thrt.throttle_bw_window)
   ├─ Disables TSOD polling (to avoid HW overwriting FW-written temps)
   └─ Programs OPC_HEADER.MEMORY_CHANNELS (DMR-AP: 16, DMR-SP: 8)

2. BMC Writes DIMM Temperatures via TPMI
   ├─ BMC enumerates valid channels from OPC_HEADER.MEMORY_CHANNELS
   ├─ BMC writes OPC_DIMM_TEMPS_[0..3] with per-DIMM U8.0 temps
   │   ├─ OPC_DIMM_TEMPS_0: channels 0–3 (16 bits/channel: DIMM0[7:0], DIMM1[15:8])
   │   ├─ OPC_DIMM_TEMPS_1: channels 4–7
   │   ├─ OPC_DIMM_TEMPS_2: channels 8–11
   │   └─ OPC_DIMM_TEMPS_3: channels 12–15
   └─ BMC writes periodically based on platform thermal policy

3. Primecode TPMI Handler Processes Temps
   ├─ OpcTpmi::handleDimmTemps() triggered by TPMI write
   │   ├─ Validates CLTT_PECI_ENABLE + CLTT_MR4_ENABLE from PCU_MISC_CONFIG
   │   ├─ Reads TPMI OPC_DIMM_TEMPS line data
   │   └─ Calls CLTT::storeTpmiClttTemps() to store per-DIMM temps
   ├─ CLTT::writeMcTemperatureRegisters()
   │   ├─ Clips temps to MAX_DIMM_TEMPERATURE (127°C)
   │   ├─ Writes dimm_temp_snapshot_0/1 via IOSF (per MC per DIMM)
   │   └─ Sets dimm_temp_sensor_valid = 1
   ├─ CLTT::sendDimmTempOnHpm()
   │   └─ Sends HPM DIMM_TEMPERATURE_0/1 to remote IMH (multi-die)
   └─ CLTT::publishTpmiTemps()
       └─ Writes back to TPMI OPC_DIMM_TEMPS (readback for OOB consumers)

4. Legacy PECI PCS-14 Path (alternate / GNR-compatible)
   ├─ WRPKGCONFIG PCS-14: clttDimmTempPcsWrite()
   │   ├─ Checks CLTT_PECI_ENABLE — rejects with 0x90 if disabled
   │   ├─ Clips temperature to 0–127°C
   │   └─ DimmReverseMapping maps I3C→MC logical ID for correct channel
   └─ RDPKGCONFIG PCS-14: clttDimmTempPcsRead()
       ├─ Returns max DIMM temperature for the channel
       ├─ Same value in bits [7:0] and [15:8]
       └─ Returns 0x0 if no DIMM populated; 0x90 if channel invalid

5. MC Thermal Response
   ├─ Reads dimm_temp_snapshot_0/1 (max of valid per-DIMM sensors)
   ├─ Adds DIMM_TEMP_EV_OFST[DIMM_TEMP_OFFSET] to raw temperature
   ├─ Compares against thresholds:
   │   ├─ < 2x refresh threshold → 1x refresh, no throttle
   │   ├─ ≥ 2x refresh threshold → 2x refresh (if enabled)
   │   ├─ ≥ Temp_Lo → applies THRT_MID bandwidth limit
   │   ├─ ≥ Temp_Mid → applies THRT_HI bandwidth limit
   │   ├─ ≥ Temp_Hi → applies THRT_CRIT bandwidth limit
   │   └─ ≥ Temp_MemTrip → asserts MEMTRIP#
   └─ Bandwidth throttle formula:
       timeframe = CHN_TEMP_CFG[BW_LIMIT_TF] << 5
       num_transactions = DIMM_TEMP_THRT_LMT << 3

6. OS / Platform Observable
   ├─ TPMI OPC_DIMM_TEMPS readable via OOB for BMC verification
   ├─ DDR_THERM_STATUS.DDR_MAX_TEMPERATURE updated
   ├─ MEMHOT/MEMTRIP platform signals
   └─ Bandwidth reduction observable via PMONs
```

### Key Registers & Interfaces

#### TPMI Registers (OPC Package Control)

| Register | Bits | Access | Description |
|----------|------|--------|-------------|
| `OPC_DIMM_TEMPS_0` | `[63:0]` | RW | DIMM temps channels 0–3 (U8.0, 16 bits/ch: DIMM0[7:0] + DIMM1[15:8]) |
| `OPC_DIMM_TEMPS_1` | `[63:0]` | RW | DIMM temps channels 4–7 |
| `OPC_DIMM_TEMPS_2` | `[63:0]` | RW | DIMM temps channels 8–11 |
| `OPC_DIMM_TEMPS_3` | `[63:0]` | RW | DIMM temps channels 12–15 |
| `OPC_HEADER` | `MEMORY_CHANNELS` | RO | Number of supported memory channels (AP: 16, SP: 8) |

#### MC Registers (per MC, MCHBAR GPSB)

| Register | Key Fields | Description |
|----------|-----------|-------------|
| `dimm_temp_snapshot_0` | `dimm_temp_sch0[7:0]`, `dimm_temp_sch1[15:8]`, `dimm_refresh_rate[20:19]` | DIMM0 temp and refresh rate per sub-channel |
| `dimm_temp_snapshot_1` | `dimm_temp_sch0[7:0]`, `dimm_temp_sch1[15:8]`, `dimm_refresh_rate[20:19]` | DIMM1 temp and refresh rate per sub-channel |
| `dimm_temp_thresh` | `dimm_temp_low/mid/high_maxthreshold`, `dimm_temp_memtrip_threshold` | Throttle and memtrip thresholds |
| `dimm_temp_thrt_lmt` | `THRT_MID`, `THRT_HI`, `THRT_CRIT` | Bandwidth throttle levels per threshold band |
| `dimm_bw_thrt` | `throttle_bw_window` | Throttle window length |
| `dimm_temp_ev_ofst` | `DIMM_TEMP_OFFSET` | Offset added to raw DIMM temp before threshold comparison |
| `dimm_tsod_temp` | `dimm_temp_sensor_valid`, temp data | FW-written temp + valid bit (legacy naming; used for all CLTT modes) |
| `chn_temp_cfg` | `BW_LIMIT_TF` | Throttle time frame for bandwidth limiting |

#### Primecode Interfaces

| Interface | ID / Path | Description |
|-----------|----------|-------------|
| TPMI handler | `OpcTpmi::handleDimmTemps()` | Entry point for BMC-written DIMM temps |
| CLTT flow | `CLTT::storeTpmiClttTemps()` | Stores TPMI-provided temps into CLTT state |
| CLTT flow | `CLTT::writeMcTemperatureRegisters()` | Writes temps to MC dimm_temp_snapshot via IOSF |
| CLTT flow | `CLTT::sendDimmTempOnHpm()` | HPM inter-die temp distribution |
| CLTT flow | `CLTT::publishTpmiTemps()` | Writes back to TPMI OPC for OOB readback |
| PCS handler | `regPcsMbox()` → `DDR_DIMM_DIGITAL_THRM` | Registers PCS-14 opcode handler |
| PCS handler | `clttDimmTempPcsRead()` | RDPKGCONFIG PCS-14 read handler |
| PCS handler | `clttDimmTempPcsWrite()` | WRPKGCONFIG PCS-14 write handler |
| Reverse mapping | `DimmReverseMapping` class | I3C → MC logical DIMM ID mapping for PCS writes |
| HPM opcode | `DIMM_TEMPERATURE_0` (0x29) | Inter-die DIMM temp (DIMM_TEMP_0..15) |
| HPM opcode | `DIMM_TEMPERATURE_1` (0x2A) | Inter-die DIMM temp (continued) |
| B2P mailbox | `WRITE_PCU_MISC_CONFIG` | `CLTT_PECI_ENABLE` / `MR4_CLTT_ENABLE` bits |
| TPMI constant | `TPMI_OPC_TEMP_REGS = 4` | Number of OPC_DIMM_TEMPS registers |
| Temp constant | `MAX_DIMM_TEMPERATURE = 127` | Clip ceiling for PCS/TPMI temp writes |

#### MC Throttle Threshold Behavior

| DIMM Temperature Condition | MC Action |
|---|---|
| `Temp < 2x refresh threshold` | 1x refresh, no bandwidth throttle |
| `2x refresh ≤ Temp < Temp_Lo` | 2x refresh (if enabled), no BW throttle |
| `Temp_Lo ≤ Temp < Temp_Mid` | Throttle using `THRT_MID` |
| `Temp_Mid ≤ Temp < Temp_Hi` | Throttle using `THRT_HI` |
| `Temp_Hi ≤ Temp < Temp_MemTrip` | Throttle using `THRT_CRIT` |
| `Temp ≥ Temp_MemTrip` | Assert `MEMTRIP#` |

#### PCS-14 Error Codes

| Condition | Error Code |
|-----------|-----------|
| `CLTT_PECI_ENABLE` not set | `0x90` |
| Invalid / out-of-range channel index | `0x90` |
| No DIMM populated in channel (read) | `0x0` |

#### CLTT Operating Modes

| Mode Enum | Value | Description |
|-----------|-------|-------------|
| `MR4_ENABLED` | 0 | MC reads MR4 → Primecode converts & distributes |
| `MR4_DISABLED_PECI_ENABLED` | 1 | BMC pushes temps via TPMI / PECI PCS-14 |
| `MR4_DISABLED_TSOD_ENABLED` | 2 | SPD I3C TSOD polling for DIMM temps |

#### PythonSV Validation Functions

| Function | Module | Description |
|----------|--------|-------------|
| `cltt.py --peci` | `pm/cltt.py` | PECI CLTT validation mode — enables via BIOS mailbox bit 6 |
| `Memtrip.py --peci` | `pm/Memtrip.py` | Memtrip test with PECI temp injection |
| `verify_temps_vs_tpmi()` | `pm/mem_thermals_debug.py` | Compare MC temps against TPMI OPC values |
| `read_tpmi_data()` | `pm/mem_thermals_debug.py` | Read TPMI OPC_DIMM_TEMPS registers |
| `set_thresholds()` | `pm/mem_thermals_debug.py` | Program MC throttle thresholds |
| `pldm.py` | `pm/pldm.py` | GPSB source mapping for `opc_dimm_temps_0..3` |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR DDR5/MCR - PECI CLTT](https://docs.intel.com/documents/pm_doc/src/server/dmr/IP_PM_Features/DMR_DDR5_MCR.html) | PECI-based CLTT architecture |
| HAS | [DMR DDR5/MCR - PECI CLTT (alt)](https://docs.intel.com/documents/pm_doc/src/server/dmr/IP%20Specific%20PM%20Features/DMR_DDR5_MCR.html) | Alternate path — PECI and MR4 CLTT |
| HAS | [Common Memory Thermals](https://docs.intel.com/documents/pm_doc/src/server/gnr/Features/memory_thermal/memory_thermals.html) | CLTT w/ PECI, PCS-14, thresholds (GNR/common) |
| HAS | [DMR Memory Overview](https://docs.intel.com/documents/arch_datacenter/dmr/overview/memory.html) | Memory Thermal Management overview |
| HAS | [TPMI OPC Registers](https://docs.intel.com/documents/pm_doc/src/server/arch_common/tpmi/tpmi.html) | PCS→TPMI transition, OPC_DIMM_TEMPS definitions |
| HAS | [DMR CEA SOP PM HAS](https://docs.intel.com/documents/arch_datacenter/dmr_d_has/cea%20system%20on%20package%20%28sop%29%20has/cea%20sop%20pm%20has/cea_sop_pm_has.html) | PECI-based CLTT / DMR TPMI access |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS — memory thermal |
| Primecode src | `src/flow/cltt/cltt_common/v2_0/cltt.hpp` / `cltt.cpp` | Core CLTT flow — storeTpmiClttTemps, writeMcTemperatureRegisters, publishTpmiTemps |
| Primecode src | `src/flow/cltt/cltt_io_base/v1_0/pecicltt_mailbox_base.hpp` | PECI CLTT PCS-14 mailbox handler — regPcsMbox(), clttDimmTempPcsHandler() |
| Primecode src | `src/flow/cltt/cltt_io/v1_0/pecicltt_mailbox.hpp` | IO-specific CLTT mailbox — clttDimmTempPcsRead/Write, DimmReverseMapping |
| Primecode src | `src/flow/mailbox/tpmi_handlers/oob_package_control/v2_0/` | OpcTpmi::handleDimmTemps() — TPMI DIMM temp entry point |
| PCode src | Not in pcode-cbb-a0 | PECI CLTT is entirely IMH-side (Primecode) — PCode only has `convert_temperature_to_peci_format()` utility |
| Test scripts | `pm/cltt.py` | PECI CLTT validation (`--peci` mode) |
| Test scripts | `pm/Memtrip.py` | Memtrip with PECI temp injection (`--peci` mode) |
| Test scripts | `pm/mem_thermals_debug.py` | Debug utilities — verify_temps_vs_tpmi, read_tpmi_data, set_thresholds |
| Test scripts | `pm/pldm.py` | GPSB source mapping for OPC DIMM temp registers |

### Related Sightings
<!-- No PECI CLTT-specific sightings catalogued yet — populate as NWP silicon debug progresses -->

