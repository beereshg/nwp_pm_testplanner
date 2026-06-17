# SoC Thermal > IMH DTS & Telemetry

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: 19 Digital Thermal Sensors (DTS) on each IMH die monitor all IP stacks — DDR, D2D, MIO, Accelerator, Mem/IO Fabric, CGU — feeding PrimeCode for thermal throttling, ITD voltage compensation, and OS thermal telemetry.

**Topology**:
```
IMH DTS (19/die) ──RC 0x7E00/0x7E04──> PrimeCode DTS pipeline
  Domain groups:                          │── EWMA filter
   DDR (4 DTS, RC_MEM_W/E)                │── EMTTM PID (Mem + IO fabric freq)
   D2D (5 DTS, RC_CFCMEM_EW)             │── ITD voltage offset (RESCTRL_CR_VOLTAGE_OFFSET)
   MIO (3 DTS, RC_MIO_EW)                └── HPM SOCKET_THERMAL → OS MSRs
   Accel (1 DTS, RC_CFCIO)
   Mem/IO Fabric (4+1 DTS, RC_CFCIO/MEM)
   CGU AON DTS (last in thermtrip chain)
```

**Key operational principle**: Raw DTS code −64 = absolute °C. EWMA smoothed each slow loop (~1 mS). DTS_CAL_GUARDBAND=0 for DMR/GNR+ (no correction). Disabled DTS (fuse DISABLED_MODULE_DTS_MASK) → module disabled. If DTS < MIN_ACCURATE_TEMP → substitute ITD_MIN_OVERRIDE_TEMP.

**Boot activation**: SOC DTS fuse pull + DTS enabled at PH1.2 (thermtrip protection active). PrimeCode EWMA loop from PH2.52.

Digital Thermal Sensors (DTS) on the IMH die provide accurate temperature monitoring across all IP stacks. Each DTS is paired with Remote Sensors (RS) and feeds temperature data into Primecode for thermal management, ITD compensation, and telemetry reporting.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| IMH DTS (19 per die, Gen1) | IMH die | Temperature monitoring for all IP stacks; feeds EMTTM PID, ITD, telemetry | RC 0x7E00/0x7E04; 5 RC channels: RC_CFCMEM_EW, RC_CFCIO, RC_MEM_W/E, RC_MIO_EW | [DMR SoC Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#dmr-imh-dts) |
| Remote Diode / TRSD | Inside each IP (DDR PHY, UCIe adaptor, MIO ctrl, Accel) | Remote sensor for DTS; 1–6 RS per DTS instance for area efficiency | Diode connected to DTS analog front-end | [DMR Thermal HAS — ITD Mapping](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#dmr-itd-mapping) |
| CGU AON DTS | IMH Base (CGU) | Always-on thermtrip sensor; last in daisy chain; active in all power states including PkgC6 | `i_thermtrip` tied to 0 for first DTS; AON terminates chain | Legacy Architecture Summary |
| FIVR / MBVR rails (IMH) | IMH die | Voltage rails that receive ITD compensation from PrimeCode based on DTS readings | `RESCTRL_CR_VOLTAGE_OFFSET.OFFSET` per RC channel | [RC HAS](https://docs.intel.com/documents/sysip_pm/resource_controller/TRM/TRM.html#voltage_offset) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core PMA | No IMH DTS role; only reads CBB core DTS via SHORT_TELEM | — | — |
| PCode (CBB) | CBB Base Die | Disabled DTS mask check for CBB DTS; provides min temp via SOCKET_THERMAL for VCCINF ITD | `DISABLED_MODULE_DTS_MASK` fuse; `PCU_CR_DTS_TEMP_CCF`; SOCKET_THERMAL min temp | Legacy Architecture Summary |
| PrimeCode (IMH) | IMH die | Reads all 19 IMH DTS via RC; applies EWMA filter; feeds EMTTM PID and ITD; populates `PACKAGE_TEMPERATURE`, `MCP_THERMAL_REPORT_1/2`; populates HPM `SOCKET_THERMAL` | RC_read(0x7E00/7E04); `PACKAGE_TEMPERATURE` PCU CR 0xfb980 | [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) |
| BIOS / UEFI | Platform | Programs DTS fuse configuration; `DTS_CAL_GUARDBAND` (=0 DMR), `MIN_ACCURATE_TEMP`, `ITD_MIN_OVERRIDE_TEMP`, `DISABLED_MODULE_DTS_MASK` | Fuse programming at HVM | HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | RO/RWC | [23:16] TEMPERATURE — margin to TjMax (from IMH DTS max via PrimeCode) | Intel SDM |
| MSR `MCP_THERMAL_REPORT_1` | 0x1A3 | RO | [15:0] Margin to Throttle; [31:16] Margin to Tcontrol (aggregated from IMH DTS) | Intel SDM |
| MSR `MCP_THERMAL_REPORT_2` | 0x1A5 | RO | Absolute max temperature across package (from IMH DTS aggregation) | Intel SDM |
| MSR `IA32_TEMPERATURE_TARGET` | 0x1A2 | RW | [23:16] REF_TEMP = EFFECTIVE_TJMAX − DTS_CAL_GUARDBAND (written by PrimeCode) | Intel SDM |
| HPM `SOCKET_THERMAL` | IMH→Root | FW-internal | Max temp, margins, OOS status; sourced from IMH DTS aggregation by PrimeCode | [Socket Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| DTS count per IMH die | 19 | — | 5 domain groups: DDR(4), D2D(5), MIO(3), Accel(1), Mem/IO Fabric(4+1), CGU AON(1) | Legacy Architecture Summary |
| DTS rawcode offset | +64 | °C | absolute_temp = rawcode − 64; prevents underflow for cold readings | Legacy Execution Flow |
| EWMA update rate | ~1 | mS | Per PrimeCode slow loop; smooths transient noise before EMTTM PID and ITD | Legacy Execution Flow |
| DTS calibration guardband | 0 | °C | DTS_CAL_GB = 0 for GNR+ / DMR; no correction term applied | Legacy Execution Flow |
| MIN_ACCURATE_TEMP fallback | `ITD_MIN_OVERRIDE_TEMP` | °C | PrimeCode substitutes override when DTS reads below MIN_ACCURATE_TEMP | Legacy Architecture Summary |
| Remote diodes per DTS | 1–6 | — | Varies by IP: DDR PHY (3/channel), UCIe adaptor (3/X6 module), MIO ctrl (1–2) | Legacy Architecture Summary |

## NWP Delta

**IMH DTS telemetry is supported on NWP** via single NIO die (derivative of DMR IMH2).

### Topology Changes
- Single NIO die replaces dual IMH — one set of DTS instances
- DTS IP and diode placement updated for NWP NIO topology
- DTS-AON (Always-On) in CGU — last in thermtrip chain, single diode (diode #0)
- DTS daisy-chaining for thermtrip: `i_thermtrip` tied to 0 for first DTS, DTS-AON is final
- Glitch filter (`catfilteren`) enabled by default for all NIO DTS instances
- `oneshotmodeen` fuse = 0 for DTS

### Key NWP HSD
- HSD 14027181891: NIO DTS and remote diode placement update

### Validation Impact
- Verify NIO-specific DTS/TRSD locations per HSD 14027181891
- Single NIO simplifies: no cross-IMH DTS aggregation
- DTS-AON thermtrip chain terminates in NIO (not propagated to second IMH)

## Legacy (Human-Curated Reference)

### Architecture Summary

Digital Thermal Sensors (DTS) on the IMH die provide accurate temperature monitoring across all IP stacks. Each DTS is paired with Remote Sensors (RS) and feeds temperature data into Primecode for thermal management, ITD compensation, and telemetry reporting.

**IMH1 DTS placement summary (19 DTS per IMH die):**

| IP Stack | DTS Count/IMH | RS Location | DTS Location | Notes |
|----------|---------------|-------------|--------------|-------|
| Memory (DDR) | 4 | Inside DDR PHY | In SOC | 1 DTS per 2 DDR channels; 3 RS per DDR channel |
| D2D (UCIe) | 5 | Inside UCIe adaptor | In SOC | 4x one DTS per UCIe X6 module (3 RS each); 1x DTS with 6 RS |
| MIO | 3 | Inside controller | Controller misc block | 1 DTS + 1-2 RS per UIO stack |
| Accelerator | 1 | Inside accelerator | Accelerator misc block | 1 DTS + 1 RS |
| Memory Fabric | 4 | — | — | — |
| IO Fabric | 1 | Inside CA tile block | In SOC | 1 RS per CA tile; DTS shared opportunistically |
| CGU | 1 | Inside CGU | Inside CGU | AON DTS; last in CATTRIP daisy chain |
| **Total** | **19** | | | |

**IMH2 differences**: See [IMH2_DTS_RD_MAPPING](https://intel.sharepoint.com/sites/DiamondRapids/IMH_FE/Shared%20Documents/PM/exe/Temp/misc/IMH2_DTS_RD_mapping_WIP.xlsx?web=1) for IMH2-specific DTS placement and RS mapping (additional accelerator DTS, different MIO layout).

### Execution Flow

#### DTS Processing Pipeline
1. **Raw temperature read**: Each DTS reports temperature via its Resource Adapter through RC registers
   - DTS data pulled from RC register at offset `0x7E00` (primary) and `0x7E04` (secondary) per IP domain
   - RC channels: `RC_CFCMEM_EW`, `RC_CFCIO`, `RC_MEM_W`, `RC_MEM_E`, `RC_MIO_EW`
2. **Offset removal**: `absolute_temp = dts_temp_data - 64` (DTS adds 64°C offset to prevent underflow)
3. **EWMA filtering**: `filtered_temp = EWMA(absolute_temp)` — smooths transient noise for stable thermal control
4. **No correction needed**: GNR onwards the fused quadratic and intercept terms are zero (`DTS_CAL_GB = 0`), so no DTS calibration correction is applied — same for DMR
5. **Temperature reported** to:
   - Local PID thermal control loop (fabric frequency ceiling)
   - ITD compensation algorithm (voltage offset per rail)
   - HPM `SOCKET_THERMAL` message to root die (max temp, margin to throttle, margin to Tcontrol)
   - Package-level reporting registers (`PACKAGE_TEMPERATURE`, `IA32_PACKAGE_THERM_STATUS`)

#### Disabled DTS Handling
- If a DTS is "bad" (inaccurate), the corresponding module/core gets disabled and the part is recovered
- Controlled by `DISABLED_MODULE_DTS_MASK` fuse (per-module bitmask; `1` = ignore DTS)
- Disabled DTS mask must be a subset of `CORE_DISABLE_MASK` for all SST levels
- Inherited from GNR — see [HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html#disabled-dts-starting-gnr)

#### Temperature below MIN_ACCURATE_TEMP
- If DTS reports below `FUSE.MIN_ACCURATE_TEMP`, Primecode uses `FUSE.ITD_MIN_OVERRIDE_TEMP` instead
- Prevents unreliable cold readings from corrupting ITD compensation

### Key Registers & Interfaces

| Register / Interface | Scope | Access | Purpose |
|---|---|---|---|
| RC offset `0x7E00` / `0x7E04` | Per DTS | MEM | Raw DTS temperature readout per IP domain |
| `PACKAGE_TEMPERATURE` (PCU CR 0xfb980) | Package | RW | Package temp = absolute temp + 64°C |
| `IA32_PACKAGE_THERM_STATUS[23:16]` (MSR 0x1B1) | Package | RO | Temperature relative to TJ_MAX |
| `IA32_TEMPERATURE_TARGET[23:16]` (MSR 0x1A4) | Package | RW | REF_TEMP = EFFECTIVE_TJMAX - DTS_CAL_GUARDBAND |
| `IA32_PACKAGE_THERM_MARGIN[15:0]` (MSR 0x1A1) | Package | RW | Margin to Tcontrol (8.8 format) |
| `MCP_THERMAL_REPORT_1` (MSR 0x1A3) | Package | RW | Margin to throttle + margin to Tcontrol (D-line) |
| `MCP_THERMAL_REPORT_2` (MSR 0x1A5) | Package | RW | Absolute max temperature (D-line) |
| HPM `SOCKET_THERMAL` | Die→Root | HPM | Reports OOS, min/max temp, margin to throttle/Tcontrol |
| `DTS_CAL_GUARDBAND` fuse | Die | Fuse | DTS calibration guardband (U3.4, value is 0 for DMR) |
| `MIN_ACCURATE_TEMP` fuse | Die | Fuse | Below this, DTS readings unreliable (S6.0) |
| `ITD_MIN_OVERRIDE_TEMP` fuse | Die | Fuse | Override temp when DTS < MIN_ACCURATE_TEMP (S6.0) |
| `DISABLED_MODULE_DTS_MASK` fuse | CBB Die | Fuse | Bitmask of disabled DTS per module |

#### DTS-to-Rail Mapping (ITD)
Each DTS feeds into specific FIVR/MBVR rails for ITD compensation. Key RC channels and their DTS associations:

| DTS Name | RC Channel | Rails Covered |
|---|---|---|
| `dts_ddr_a/b/c/d` | `RC_MEM_W` / `RC_MEM_E` | `VCCFIXDIG_E/W`, `VCCINF` |
| `dts_catile_a/b/c/d` | `RC_CFCIO` | `VCCCFCIO`, `VCCCFCMEM_W/E` |
| `dts_center` | `RC_CFCIO` | `VCCCFCIO` |
| `dts_ucie_a/b/c/d` | `RC_CFCMEM_EW` | `VCCCFCMEM_W/E`, `VCCUCIEA_NW/NE/SW/SE` |
| `dts_imh_ucie` | `RC_CFCMEM_EW` | `VCCCFCMEM_W/E`, `VCCUCIEA_SW/SE` |
| `dts_miomisc_uio_0/1/2` | `RC_MIO_EW` | `VCCFIXDIG_MIO_1/3/4` |
| `dts_acc_misc` | `RC_CFCIO` | `VCCFIXDIG_E` |
| `cgu_dts` | `RC_CFCMEM_EW` | `VCCINF` only |

Full mapping tables: [DMR Thermal HAS — ITD Mapping](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#dmr-itd-mapping)

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR SoC Thermal HAS — IMH DTS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#dmr-imh-dts) | DTS placement, processing, disabled DTS |
| HAS | [DMR SoC Thermal HAS — ITD Mapping](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#dmr-itd-mapping) | DTS-to-rail mapping tables (IMH1 + IMH2) |
| HAS | [Socket Thermal Mgmt — Disabled DTS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html#disabled-dts-starting-gnr) | GNR+ disabled DTS recovery feature |
| SharePoint | [IMH2 DTS RD Mapping (WIP)](https://intel.sharepoint.com/sites/DiamondRapids/IMH_FE/Shared%20Documents/PM/exe/Temp/misc/IMH2_DTS_RD_mapping_WIP.xlsx?web=1) | IMH2-specific DTS placement |
| Primecode src | TODO | |
| PCode src | TODO | |
| Test scripts | TODO | |

### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->

### NWP Delta
- NWP inherits DMR DTS placement architecture; verify NWP die-specific DTS count and IP stack mapping
- DTS calibration guardband remains 0 (no correction needed, same as GNR/DMR)
- IMH2-specific DTS mapping may differ — confirm against NWP IMH variant
- EWMA filter parameters for DTS processing — verify if NWP tunes differently from DMR
