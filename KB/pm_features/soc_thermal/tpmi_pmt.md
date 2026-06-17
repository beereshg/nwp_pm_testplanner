# SoC Thermal > TPMI/PMT

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: TPMI (control/status) and PMT (telemetry/streaming) replace all DMR legacy PECI PCS thermal services. TPMI provides inband MMIO + OOB PECI access to thermal status registers; PMT streams temperature/margin counters to BMC. Both live in per-Punit SRAM (8 KB), discovered via OOBMSM VSEC.

**Topology**:
```
Inband SW (BIOS/OS) ──MMIO──> OOBMSM VSEC BAR ──HostDD/GPSB──> Punit TPMI SRAM (8 KB)
OOB SW (BMC)  ──────PECI Rd/WrEndpointCfg──────> OOBMSM ──────> (same SRAM)
BMC PMT watcher ────PECI telemetry──────────────> PMT aggregator
  TPMI features (thermal): OOB_PKG_CTLS (0x0F), OOB_DIE_CTLS (0x0E), PLR (0x0C), MISC_CTRL (0x06)
  Package-scope: Root IMH only  |  Die-scope: each die has own PFS entry
```

**Key operational principle**: `OPC_PKG_THERM_STATUS` (TPMI_ID 0x0F, index 2) mirrors `IA32_PACKAGE_THERM_STATUS` with independent OOB log bits — BMC can clear without affecting OS MSR view. `OPC_THERMAL_MONITOR` (index 4) lets BMC program EWMA decay factor for `THERMAL_MONITOR_STATUS`. Fastpath: SW write to TPMI SRAM sets `IO_FASTPATH_TPMI_LINEMASK` → PCode reads new config within one slow-loop.

**Boot activation**: TPMI SRAM zero'd by Punit MBIST at cold reset. PCode/PrimeCode initializes at PH2.x (CPL3). BIOS locks all features via `TPMI_SET_STATE(LOCK=1)` before OS boot; failure halts boot.

TPMI (Topology Aware Register and PM Capsule Interface) and PMT (Platform Monitoring Technology) are the **DMR-generation replacement** for legacy PECI PCS (Platform Control Services) for thermal observability. Starting on DMR, all PM-related PCS services are removed and replaced with TPMI (control/status) and PMT (telemetry/monitoring/streaming).

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| OOBMSM | Per IMH | PCIe device with VSEC_ID=0x42; exposes TPMI SRAM BAR and PECI endpoint; hosts HostDD, LTM security, TPMI Control Interface | VSEC, PFS, HostDD→GPSB | [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/TPMI/DMR_TPMI.html) |
| Punit TPMI SRAM | Per die | 8 KB SRAM holding all TPMI feature registers (OOB_PKG_CTLS, OOB_DIE_CTLS, PLR, MISC_CTRL, etc.); hardened RO vs RW per feature | `IO_FASTPATH_TPMI_LINEMASK`; `TPMI_WRITE_DISABLE` | TPMI HAS |
| PMT aggregator | Per die | Streams telemetry counters (PACKAGE_TEMPERATURE, MARGIN_TO_TCONTROL, THERMAL_CONSTRAINED_TIME) to BMC | PMT watcher API; PECI telemetry | TPMI HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core PMA | No TPMI/PMT role | — | — |
| PCode (CBB) | CBB Base Die | Initializes CBB-scoped TPMI SRAM (PLR, OOB_DIE_CTLS); handles fastpath on TPMI SRAM write; updates `CORE_PERF_LIMIT_REASONS` TPMI PLR entries | `IO_FASTPATH_TPMI_LINEMASK`; PLR TPMI CRs | TPMI HAS |
| PrimeCode (IMH) | IMH die | Initializes package-scoped TPMI SRAM (OOB_PKG_CTLS, MISC_CTRL); populates `OPC_PKG_THERM_STATUS` each slow-loop; handles `OPC_THERMAL_MONITOR` fastpath; updates PMT temperature/margin entries | `OPC_PKG_THERM_STATUS` (TPMI_ID 0x0F idx 2); `OPC_THERMAL_MONITOR` (idx 4); PMT entries | TPMI HAS + PrimeCode src |
| Ocode / FW | IMH die | Initializes `OOB_PKG_CTLS` and `OOB_DIE_CTLS` with `STATE=1, LOCK=1, IB_WRITE_BLOCK=1, IB_READ_BLOCK=1` → BMC-exclusive by default | TPMI init boot sequence | TPMI HAS |
| BIOS / UEFI | Platform | Discovers TPMI via VSEC_ID=0x42; programs PFS; locks all features via `TPMI_SET_STATE(LOCK=1)` before OS boot | MMIO discovery; LTM security rules | TPMI HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MMIO (TPMI SRAM) | OOBMSM BAR + PFS offset | RW (BIOS) / RO (OS) | `OPC_PKG_THERM_STATUS` (TPMI_ID 0x0F idx 2): thermal status/log for BMC; `OPC_THERMAL_MONITOR` (idx 4): EWMA decay config | [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/TPMI/DMR_TPMI.html) |
| PECI `Rd/WrEndpointCfg` | OOB (BMC) | RW | OOB access to same TPMI SRAM; same thermal status registers; `IB_WRITE_BLOCK=1` prevents inband OS writes to `OOB_PKG_CTLS` | Intel PECI spec |
| PMT watcher API | BMC / telemetry | RO stream | `PACKAGE_TEMPERATURE` (+ 64°C offset), `MARGIN_TO_TCONTROL` (S8.8), `TEMPERATURE_TARGET`, `THERMAL_CONSTRAINED_TIME` counter | TPMI HAS |
| `OPC_PKG_THERM_STATUS_LOG_CLEAR` | TPMI idx 3 | RW/1C | Write-1-to-clear OOB log bits (independent from MSR 0x1B1 log bits) | TPMI HAS |
| TPMI Control Interface | `TPMI_CONTROL_STATUS` 0x0 | RW | `COMMAND[7:0]` (0x10=GET_STATE, 0x11=SET_STATE); `STATUS_CODE[15:8]` (0x40=success); `LOCK` via SET_STATE | TPMI HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| TPMI SRAM size | 8 | KB | Per Punit; holds all TPMI feature registers | Legacy Architecture Summary |
| TPMI fastpath latency | ≤1 | slow-loop (~1 mS) | SW write → `IO_FASTPATH_TPMI_LINEMASK` set → PCode reads new config | Legacy Execution Flow |
| OPC_THERMAL_MONITOR time window | 2.3 × 2^N | mS | `DECAY_FACTOR[6:0]` N=0..127; BMC-configurable EWMA filter for THERMAL_MONITOR_STATUS | Legacy Key Registers |
| PMT update rate | ~1 | mS | PrimeCode slow-loop; PACKAGE_TEMPERATURE, MARGIN_TO_TCONTROL updated each iteration | Legacy Execution Flow |
| TPMI SRAM init (cold reset) | Punit MBIST | — | Zeros SRAM; PCode/PrimeCode reprograms at PH2.x | Legacy Boot Sequence |
| Legacy PCS indices replaced | 6 | — | PCS 2, 10, 16, 20, 32 → TPMI/PMT; PCS 20 → 2 TPMI entries | Legacy PCS Migration table |

## NWP Delta

**TPMI PMT is fully supported on NWP** — reused from DMR IMH2.

- OOBMSM and PMT flows reused from DMR IMH2/NIO
- TPMI register access unchanged
- PMT telemetry counters unchanged
- Single NIO die — one set of TPMI/PMT instances

### Validation Impact
- Same TPMI PMT test cases apply
- Single NIO simplifies PMT instance enumeration

## Legacy (Human-Curated Reference)

### Architecture Summary

TPMI (Topology Aware Register and PM Capsule Interface) and PMT (Platform Monitoring Technology) are the **DMR-generation replacement** for legacy PECI PCS (Platform Control Services) for thermal observability. Starting on DMR, all PM-related PCS services are removed and replaced with TPMI (control/status) and PMT (telemetry/monitoring/streaming).

This sub-feature validates the **thermal-specific** TPMI and PMT registers — the subset of the TPMI/PMT infrastructure that surfaces thermal status, margins, temperature, and filtering to OOB SW (BMC) and inband SW (OS).

#### TPMI vs PMT Split

| Interface | Purpose | Access Path | Storage | Thermal Registers |
|-----------|---------|-------------|---------|-------------------|
| **TPMI** | Control & status | MMIO via OOBMSM VSEC BAR; OOB via Rd/WrEndpointCfg | Punit SRAM (64-bit lines, 8KB on DMR) | `OPC_PKG_THERM_STATUS`, `OPC_PKG_THERM_STATUS_LOG_CLEAR`, `OPC_THERMAL_MONITOR` |
| **PMT** | Telemetry & monitoring | PMT watcher API; PECI-telemetry | Punit telemetry aggregator | `PACKAGE_TEMPERATURE`, `MARGIN_TO_TCONTROL`, `TEMPERATURE_TARGET`, `THERMAL_CONSTRAINED_TIME` |

#### DMR PCS → TPMI/PMT Migration (Thermal Subset)

| Legacy PCS Index | PCS Description | DMR Replacement | TPMI_ID / PMT Entry |
|------------------|-----------------|-----------------|----------------------|
| PCS 20 | Package Thermal Status | **TPMI** `OPC_PKG_THERM_STATUS` | TPMI_ID 0x0F (`OOB_PKG_CTLS`), Index 2 |
| PCS 20 | Thermal Monitor Filtering | **TPMI** `OPC_THERMAL_MONITOR` | TPMI_ID 0x0F (`OOB_PKG_CTLS`), Index 4 |
| PCS 2 | Package Temperature | **PMT** | PMT telemetry entry |
| PCS 10 | Aggregate Margin to Tcontrol | **PMT** | PMT telemetry entry |
| PCS 16 | Temperature Target | **PMT** | PMT telemetry entry |
| PCS 32 | Thermal Constrained Time | **PMT** | PMT telemetry entry |

#### TPMI Architecture on DMR

```
                   Inband SW (BIOS/OS)                      OOB SW (BMC)
                          │                                       │
                     MMIO R/W                              PECI Rd/WrEndpointCfg
                          │                                       │
              ┌───────────▼───────────────────────────────────────▼─────────┐
              │                    OOBMSM (per IMH)                        │
              │   ┌──────────┐  ┌─────────┐  ┌──────────────────────────┐  │
              │   │ HostDD   │  │   LTM   │  │ TPMI Control Interface  │  │
              │   │(MMIO→SB) │  │(Security│  │  TPMI_GET/SET_STATE     │  │
              │   └────┬─────┘  │  Rules) │  │  Opt-in/Opt-out         │  │
              │        │        └─────────┘  └──────────────────────────┘  │
              │        │ GPSB                                              │
              └────────┼──────────────────────────────────────────────────┘
                       │
         ┌─────────────┼──────────────┐
         ▼             ▼              ▼
    ┌─────────┐  ┌──────────┐  ┌──────────┐
    │ IMH0    │  │  CBB0    │  │  CBB1    │
    │ Punit   │  │  Punit   │  │  Punit   │
    │ (Root)  │  │  (Leaf)  │  │  (Leaf)  │
    │         │  │          │  │          │
    │ TPMI    │  │ TPMI     │  │ TPMI     │
    │ SRAM    │  │ SRAM     │  │ SRAM     │
    │ 8KB     │  │ 8KB      │  │ 8KB      │
    │         │  │          │  │          │
    │ PMT     │  │ PMT      │  │ PMT      │
    │ Telem   │  │ Telem    │  │ Telem    │
    └─────────┘  └──────────┘  └──────────┘
```

Key DMR delta: Each IMH has its own OOBMSM instance with separate BDF, VSEC, PFS, and LUT. SW enumerates both IMH0 and IMH1 TPMI devices independently. Package-scoped thermal registers (`OPC_*`) reside only on Root IMH.

---

### Execution Flow

#### TPMI Infrastructure Boot Sequence

1. **HW**: Punit MBIST zeros TPMI SRAM at cold reset
2. **PCode/PrimeCode (warm reset)**: Initializes TPMI SRAM per feature — programs default values from OSXML, locks RO registers via `TPMI_WRITE_DISABLE`
3. **PCode/PrimeCode (CPL3)**: Programs `TPMI_BUS_INFO` (BDF, PACKAGE_ID, PARTITION, CD_MASK)
4. **BIOS**: Discovers TPMI via VSEC_ID 0x42 → reads PFS → programs thermal registers → locks via `TPMI_SET_STATE(LOCK=1)` for all features
5. **BIOS**: Must lock all TPMI features before OS boot; failure → BIOS error, boot halts
6. **OS/BMC**: Discovers thermal TPMI registers via PFS, accesses via MMIO (inband) or PECI Rd/WrEndpointCfg (OOB)

#### Package Thermal Status via TPMI (OPC_PKG_THERM_STATUS)

PCode flow mirrors `IA32_PACKAGE_THERM_STATUS` (MSR 0x1B1) — see [Thermal Reporting](thermal_reporting.md):

1. Root IMH PrimeCode aggregates thermal telemetry from all leaves via `SOCKET_THERMAL` HPM
2. Computes `PKG_MAX_TEMPERATURE` = max(all die max temps)
3. Updates `OPC_PKG_THERM_STATUS` TPMI register (SRAM line index 2 in `OOB_PKG_CTLS`):
   - Same status/log bit definitions as MSR 0x1B1 bits [13:0]
   - OOB-independent log bits — cleared via `OPC_PKG_THERM_STATUS_LOG_CLEAR` (write-1-to-clear)
4. Status bits: `THERMAL_MONITOR_STATUS[0]`, `PROCHOT_STATUS[2]`, `OOS_STATUS[4]`, `THRESHOLD1/2_STATUS[6,8]`, `POWER_LIMITATION_STATUS[10]`, `PMAX_STATUS[12]`
5. Log bits: independent from MSR log bits — OOB can clear without affecting inband OS view

#### Thermal Monitor Filtering via TPMI (OPC_THERMAL_MONITOR)

BMC configures EWMA filter on `THERMAL_MONITOR_STATUS` to suppress transient throttle events:

1. BMC writes `OPC_THERMAL_MONITOR.ENABLE_EWMA[7]` = 1 to enable
2. BMC writes `OPC_THERMAL_MONITOR.DECAY_FACTOR[6:0]` = time window scalar
   - `time_window = 2.3 × 2^DECAY_FACTOR` ms
3. PrimeCode reads TPMI fastpath → applies EWMA filter:
   ```
   ALPHA = exp(-1 × DELTA_TIME / time_window)
   EWMA_STATUS = ((1 - ALPHA) × PREV) + (ALPHA × CURRENT)
   ```
4. `INBAND_LOCK[30]`: when set, inband SW writes to this register are blocked

#### PMT Temperature Registers

PrimeCode populates PMT entries each slow loop:

1. **Package Temperature**: `PKG_MAX_TEMP + 64` (°C, offset to prevent underflow) → same source as `PACKAGE_TEMPERATURE` CR (0xFB980)
2. **Margin to Tcontrol**: `(eff_tj_max - T_CONTROL_OFFSET + DTS_CONFIG3.TCONTROL_OFFSET) - PKG_MAX_TEMP` → S8.8 format, same source as `IA32_PACKAGE_THERM_MARGIN` (MSR 0x1A1)
3. **Temperature Target**: `REF_TEMP` = eff_tj_max - DTS_CAL_GUARDBAND, `FAN_TEMP_TARGET_OFST` = resolved T_CONTROL_OFFSET → same source as `IA32_TEMPERATURE_TARGET` (MSR 0x1A2)
4. **Thermal Constrained Time**: cumulative time CPU was thermally throttled below P1

#### TPMI Access Control for Thermal Features

| Feature | TPMI_ID | Default | Access Control |
|---------|---------|---------|----------------|
| `OOB_PKG_CTLS` (thermal status, filtering, DIMM temps) | 0x0F | Enabled | BMC-only: `IB_WRITE_BLOCK=1`, `IB_READ_BLOCK=1`, `LOCK=1` |
| `OOB_DIE_CTLS` (die-scoped controls) | 0x0E | Enabled | BMC-only: same as above |
| `PLR` (Perf Limit Reasons — thermal bits) | 0x0C | Enabled | opt-out |
| `MISC_CTRL` (PROCHOT_RESPONSE_POWER) | 0x06 | Enabled | opt-out |

`OOB_PKG_CTLS` and `OOB_DIE_CTLS` are initialized by Ocode with `STATE=1, LOCK=1, IB_WRITE_BLOCK=1, IB_READ_BLOCK=1, PCS_SELECT=0` — making them BMC-exclusive by default. Inband SW cannot opt-in.

---

### Key Registers & Interfaces

#### TPMI Registers (OOB_PKG_CTLS — TPMI_ID 0x0F)

| Register | Index | Access | Key Fields |
|----------|-------|--------|------------|
| `OPC_HEADER` | 0 | RO/V | `INTERFACE_VERSION[7:0]`, `MEMORY_CHANNELS[15:8]` |
| `OPC_PKGC_ENTRY_CONTROL` | 1 | RW | `PREVENT_PKGC[0]` |
| `OPC_PKG_THERM_STATUS` | 2 | RO/V | `THERMAL_MONITOR_STATUS[0]`, `LOG[1]`, `PROCHOT_STATUS[2]`, `LOG[3]`, `OOS_STATUS[4]`, `LOG[5]`, `THRESHOLD1_STATUS[6]`, `LOG[7]`, `THRESHOLD2_STATUS[8]`, `LOG[9]`, `POWER_LIMITATION_STATUS[10]`, `LOG[11]`, `PMAX_STATUS[12]`, `LOG[13]` |
| `OPC_PKG_THERM_STATUS_LOG_CLEAR` | 3 | RW (1C) | Write-1-to-clear corresponding log bits in `OPC_PKG_THERM_STATUS`. SW must wait until all bits = 0 before writing 1. PCode ignores writes of 0. |
| `OPC_THERMAL_MONITOR` | 4 | RW | `DECAY_FACTOR[6:0]` (time_window = 2.3 × 2^N ms), `ENABLE_EWMA[7]` (0=disable, 1=enable), `INBAND_LOCK[30]` (blocks inband writes) |
| `OPC_HWP_CAPABILITY` | 5 | RO/V | `HIGHEST_PERFORMANCE[7:0]`, `GUARANTEED_PERFORMANCE[15:8]`, `MOST_EFFICIENT_PERFORMANCE[23:16]`, `LOWEST_PERFORMANCE[31:24]` |
| `OPC_HWP_CONTROLS` | 6 | RW | `MIN[7:0]`, `MAX[15:8]`, `EPP[31:24]`, override bits `MIN[32]`, `MAX[33]`, `EPP[34]`, `ALT_EPB[43:40]` |
| `OPC_DIMM_TEMPS_[0..3]` | 7–10 | RW | 16 channels of DIMM temperature (U8.0), 4 channels per register, 2 DIMMs per channel (lower 8 = DIMM_0, upper 8 = DIMM_1) |

**Log bit independence**: `OPC_PKG_THERM_STATUS` log bits are independent from `IA32_PACKAGE_THERM_STATUS` (MSR 0x1B1) log bits. BMC clearing logs via `OPC_PKG_THERM_STATUS_LOG_CLEAR` does not affect the MSR view. This allows OOB and inband thermal monitoring to operate independently.

#### PMT Thermal Entries

| PMT Entry | Source | Format | Description |
|-----------|--------|--------|-------------|
| Package Temperature | `PACKAGE_TEMPERATURE` CR (0xFB980) | U8.0 + 64°C offset | Absolute package max temperature |
| Margin to Tcontrol | `IA32_PACKAGE_THERM_MARGIN` (0x1A1) backing | S8.8 | Margin to fan engagement point |
| Temperature Target | `IA32_TEMPERATURE_TARGET` (0x1A2) backing | Multi-field | REF_TEMP, FAN_TEMP_TARGET_OFST, TCC_OFFSET |
| Thermal Constrained Time | PCode cumulative counter | Counter | Total time thermally throttled below P1 |

PMT entries are read-only telemetry. BMC reads via PMT watcher API or PECI telemetry commands.

#### DMR TPMI PFS Configuration (Thermal-Relevant)

| Feature | TPMI_ID | NumEntries | EntrySize (32b) | Cap Offset (KB) | Scope |
|---------|---------|------------|-----------------|-----------------|-------|
| `MISC_CTRL` | 0x06 | 1 | 6 | 44K | Package (Root IMH only) |
| `PLR` | 0x0C | 3 | 10 | 48K | Die (CBB0, CBB1, IMH) |
| `OOB_DIE_CTLS` | 0x0E | 3 | 10 | 56K | Die |
| `OOB_PKG_CTLS` | 0x0F | 1 | 22 | 60K | Package (Root IMH only) |

PFS and LUT are identical between IMH0 (PFS 0) and IMH1 (PFS 1) except for port ID assignments:
- IMH0: `imh0`, `cbb0`, `cbb1`
- IMH1: `imh1`, `cbb2`, `cbb3`

#### TPMI Discovery Flow (SW)

```
1. Search for VSEC_ID = 0x42 in OOBMSM PCIe device extended config space
2. Read tBIR (=0x2 on DMR for 64-bit BAR) and Table_Offset from VSEC
3. BasePtr = BAR[tBIR] + Table_Offset  → PFS base address
4. Search PFS for TPMI_ID of interest (e.g. 0x0F for OOB_PKG_CTLS)
5. BasePtr[feature] = BasePtr + PFS.Cap_Offset
6. For each instance p in [0..NumEntries-1]:
     data = Read(BasePtr[feature] + p × EntrySize × 4 + 0)
     if data == 0xFFFFFFFFFFFFFFFF → invalid instance, skip
     else → valid, access registers at BasePtr[feature] + p × EntrySize × 4 + offset
```

#### DMR PortID and DieID

| Component | DieID | Role |
|-----------|-------|------|
| `imh0` | 8 | Primary IMH (Package Root) |
| `imh1` | 9 | Secondary IMH |
| `cbb0` | 0 | CBB connected to IMH0 |
| `cbb1` | 1 | CBB connected to IMH0 |
| `cbb2` | 2 | CBB connected to IMH1 |
| `cbb3` | 3 | CBB connected to IMH1 |

#### TPMI Fastpath

When SW writes a TPMI SRAM register (e.g. `OPC_THERMAL_MONITOR`):

1. HW updates SRAM line
2. HW sets `IO_FASTPATH_TPMI_LINEMASK` bit for that line
3. HW ORs into `IO_FASTPATH_TPMI_LINE_AGGREGATOR`
4. HW sets `IO_FASTPATH_MAILBOXES.TPMI_REQ` = 1
5. PCode fastpath handler reads modified line, applies new config (e.g. updates EWMA filter params)

#### TPMI Control Interface

| Register | Offset | Description |
|----------|--------|-------------|
| `TPMI_CONTROL_STATUS` | 0x0 | `RUN_BUSY[0]`, `OWNER[5:4]`, `CPL[6]`, `STATUS_CODE[15:8]` (0x40=success, 0x90=failure), `PACKET_LENGTH[31:16]` |
| `TPMI_COMMAND_DATA` | 0x8 | `COMMAND[7:0]` (0x10=GET_STATE, 0x11=SET_STATE), `DATA[63:32]` |
| `TPMI_CAPABILITIES` | 0x10 | 256-bit bitmask of supported TPMI_IDs |

#### HPM Messages (Thermal Telemetry Transport)

| Message | Direction | Thermal Fields |
|---------|-----------|----------------|
| `SOCKET_THERMAL` | Leaf → Root | `OOS_STATUS`, `MIN_TEMP`, `MAX_TEMP`, `MARGIN_TO_THROTTLE`, `MARGIN_TO_TCONTROL` |
| `SOCKET_THERMAL` | Root → Leaf | `THERMAL_MONITOR_ENABLE`, `DECAY` (filter config from OPC_THERMAL_MONITOR) |

#### Special Margin Codes (PMT)

| Code | Meaning |
|------|---------|
| `0x8000` (-128 in S8.8) | DTS not ready / thermal system not initialized |
| `0x8001` | Temperature calculation error |
| `0x8002` | Thermal sensor non-valid error |

---

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS (TPMI) | [TPMI HAS (Arch Common)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) | Master TPMI spec — VSEC, PFS, LUT, control interface, PCS transition, OPC/ODC register defs |
| HAS (DMR Thermal) | [DMR SoC Thermal HAS — Thermal Reporting](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | PACKAGE_THERM_STATUS algorithms, thermal monitor filtering, OOS detection |
| HAS (DVSEC MMIO) | [MISC_CTRL_BLOCK](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/DVSEC%20MMIO/dvsec_mmio.html#misc_ctrl) | TPMI MISC_CTRL linked-list structure for PROCHOT_RESPONSE_POWER |
| HAS (PLR) | [Perf Limit Reasons HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html#tpmi) | TPMI PLR thermal bits |
| HAS (CBB TPMI) | [CBB TPMI HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html) | CBB die-scoped TPMI features |
| HAS (PMT Telemetry) | [Primecode PMT Telemetry HAS](https://docs.intel.com/documents/primecode/has/PMT_Definitions/dmr_imh/pmt_telemetry.html) | IMH PMT entry definitions |
| HAS (CBB Telemetry) | [CBB Pcode Telemetry HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details) | CBB PMT entry definitions |
| HAS (OOBMSM) | [OOBMSM FW Gen4 FAS](https://docs.intel.com/documents/arch_datacenter/OOBMSM/Gen4/OOBMSM_FW_Gen4_FAS.html#tpmi-support) | DMR OOBMSM FW — TPMI support, LTM rules, PECI loopback |
| HAS (OOBMSM NWP) | [NWP OOBMSM FW Gen4 FAS](https://docs.intel.com/documents/arch_datacenter/OOBMSM/Gen4/OOBMSM_FW_Gen4_NWP_FAS.html) | NWP OOBMSM — PMT objects table, GPSB D2D mapping, PLDM sensors, Enhanced PMT Discovery, SoC Topology Aggregator |
| JSON (NWP PMT) | [Feature_Discovery_NWP.json](https://docs.intel.com/documents/arch_datacenter/OOBMSM/Gen4/assets/Feature_Discovery_NWP.json) | NWP Enhanced PMT Discovery machine-readable feature structures |
| HAS (DMR D2D) | [DMR D2D TPMI Register Access](https://docs.intel.com/documents/arch_datacenter/DMR/D2D/Telem_Mng_D2D_flows.html#tpmi-register-access-flow) | Cross-die TPMI register access flow |
| PFS/LUT (DMR) | [PFS IMH0](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/assets/PFS_DMR0_2p7.json), [PFS IMH1](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/assets/PFS_DMR1_2p7.json), [LUT IMH0](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/assets/LUT_DMR0_2p7.json), [LUT IMH1](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/assets/LUT_DMR1_2p7.json) | Machine-readable PFS/LUT JSON |
| Related KB | [Thermal Reporting](thermal_reporting.md) | MSR-side view of same data (0x1B1, 0x1A1, 0x1A2) |
| Related KB | [Thermal Interrupts](thermal_interrupts.md) | Interrupt generation from thermal status bit transitions |
| Related KB | [Prochot](prochot.md) | PROCHOT_RESPONSE_POWER TPMI register |
| Related KB | [CBB DTS Telemetry](cbb_dts_telemetry.md) | DTS sensor pipeline feeding thermal telemetry |

#### Validation Approach

- **Aggregate Margin to Tcontrol PMT Register** (22022421558): Read PMT margin-to-Tcontrol entry and verify it matches `(eff_tj_max - T_CONTROL_OFFSET + DTS_CONFIG3.TCONTROL_OFFSET) - PKG_MAX_TEMP` in S8.8 format. Cross-check against `IA32_PACKAGE_THERM_MARGIN` (MSR 0x1A1) — values must be consistent (same source, different access path). Vary temperature → verify margin tracks linearly. Verify special code `0x8000` when DTS not ready. Verify BMC can read via PMT watcher API. Verify value updates each PrimeCode slow loop.

- **Package Temperature PMT Register** (22022421576): Read PMT package temperature entry and verify it matches `PKG_MAX_TEMP + 64` (°C, U8.0 + offset). Cross-check against `PACKAGE_TEMPERATURE` CR (0xFB980) — must be identical. Vary thermal load → verify temperature tracks. Verify multi-die aggregation: Root IMH takes max across all dies. Verify BMC access via PECI telemetry. Verify value before DTS init returns expected default/invalid code.

- **Package Thermal Status TPMI Register** (22022421578): Read `OPC_PKG_THERM_STATUS` (TPMI_ID 0x0F, index 2) via OOB path. Verify all 14 status/log bits match `IA32_PACKAGE_THERM_STATUS` (MSR 0x1B1) bits [13:0]. Key tests:
  - `THERMAL_MONITOR_STATUS[0]` / `LOG[1]`: heat above eff_tj_max → verify status set; cool → verify clears. With EWMA enabled, verify filter.
  - `PROCHOT_STATUS[2]` / `LOG[3]`: assert xxPROCHOT_N → verify live status.
  - `OOS_STATUS[4]` / `LOG[5]`: trigger temp ≥ eff_tj_max + 10°C OR timer-based.
  - Log bit independence: clear logs via `OPC_PKG_THERM_STATUS_LOG_CLEAR` → verify MSR 0x1B1 log bits unaffected.
  - Verify `OPC_PKG_THERM_STATUS_LOG_CLEAR` write-1-to-clear semantics — PCode ignores input of 0. SW must wait until all bits = 0 before writing 1.
  - Verify BMC-only access (IB_READ_BLOCK=1, IB_WRITE_BLOCK=1 by default). Inband reads return 0xFF.

- **Temperature Target PMT Register** (22022421581): Read PMT temperature target entry and verify fields match `IA32_TEMPERATURE_TARGET` (MSR 0x1A2): `REF_TEMP` = eff_tj_max - DTS_CAL_GUARDBAND (GNR+: GB=0), `FAN_TEMP_TARGET_OFST` = resolved T_CONTROL_OFFSET fuse, `TCC_OFFSET`. Verify SST-PP level switches update REF_TEMP correctly. Verify PMT value is consistent with MSR 0x1A2 view.

- **Thermal Constrained Time PMT Register** (22022421583): Read PMT thermal constrained time counter. Apply sustained thermal load above eff_tj_max → verify counter increments (time CPU throttled below P1). Remove load → verify counter stops incrementing (but does not reset). Verify counter persists across non-reset events. Verify reset clears counter. Verify BMC readability via PMT watcher API.

- **Thermal Monitor Filtering TPMI Register** (22022421585): Write `OPC_THERMAL_MONITOR` (TPMI_ID 0x0F, index 4):
  - Set `ENABLE_EWMA[7]` = 1, program `DECAY_FACTOR[6:0]` → verify PrimeCode applies EWMA filter to `THERMAL_MONITOR_STATUS` in both `OPC_PKG_THERM_STATUS` and MSR 0x1B1.
  - Verify `time_window = 2.3 × 2^DECAY_FACTOR` ms behavior: short transient thermal events are suppressed from STATUS when filter is active.
  - Set `ENABLE_EWMA[7]` = 0 → verify raw unfiltered status reported.
  - Set `INBAND_LOCK[30]` = 1 → verify inband SW writes to this register are blocked.
  - Verify TPMI fastpath: write → `IO_FASTPATH_MAILBOXES.TPMI_REQ` fires → PCode picks up new filter config.
  - Verify BMC-only access enforced by default `IB_WRITE_BLOCK=1`.

---

### Related Sightings
<!-- No NWP TPMI/PMT thermal sightings identified yet — populate as they arise -->

---

### NWP Delta

> **Source**: [NWP OOBMSM FW Gen4 FAS](https://docs.intel.com/documents/arch_datacenter/OOBMSM/Gen4/OOBMSM_FW_Gen4_NWP_FAS.html) (Rev 1, May 21 2026)
> Items marked ✅ are confirmed from the NWP FAS. Items marked ❓ remain open.

#### Confirmed Changes (from NWP OOBMSM FAS)

| # | Area | NWP | DMR Baseline | Impact |
|---|------|-----|--------------|--------|
| 1 | **OOBMSM count** | ✅ Single OOBMSM on NIO die. No OOBMSM on CBBs. | Dual OOBMSM (one per IMH) | Single BDF for TPMI discovery — SW no longer enumerates two independent TPMI devices. All TPMI/PMT thermal registers under one OOBMSM. |
| 2 | **Die topology** | ✅ 1 NIO + 2 CBBs (CBBA, CBBB). 48 printed cores per CBB. 4 D2D instances connecting NIO↔CBBs. | 2 IMH + 4 CBBs (32 cores each) | PFS NumEntries for die-scope features reduced from 5 to 3 (NIO, CBBA, CBBB). |
| 3 | **DIMM temperature channels** | ✅ 32 DIMM instances (16 channels × 2 DIMMs per channel) via `OPC_DIMM_TEMPS_[0..3]` | 8 (SP) or 16 (AP) channels | `OPC_HEADER.MEMORY_CHANNELS` = 16. All 4 `OPC_DIMM_TEMPS_[0..3]` registers used. Confirms LPDDR6 16-channel config. |
| 4 | **PMT objects restructured** | ✅ 13 aggregators, 43 watchers, 7 crashlogs (see table below) | Different indices/counts for 4 CBBs | PMT object indices completely renumbered. All per-CBB objects duplicated for CBBA/CBBB only. |
| 5 | **QAT/CPM telemetry removed** | ✅ No QAT/CPM PMT objects | QAT/CPM aggregator/watcher present | PMT table shorter; no accelerator die telemetry. |
| 6 | **IMH-to-IMH removed** | ✅ All IMH-to-IMH relations removed (crashlog, MCTP streaming) | IMH0↔IMH1 D2D telemetry/crashlog | Simplifies D2D telemetry to NIO↔CBB only. |
| 7 | **IO-CA count** | ✅ Up to 32 IO-CAs (increased from DMR). `CHAS_ENABLED_MASK` used for enabled mask. | Fewer IO-CAs | D2D ULA & IO-CA aggregator buffer = 6992 bytes (vs DMR). IO-CA semantic space spans IO-CA0..IO-CA31. |
| 8 | **D2D GPSB for TPMI** | ✅ TPMI uses GPSB10 virtual connection. Available only on D2D[0] and D2D[3] (`TX-RX`). D2D[1] and D2D[2] = `INVALID`. | D2D[0]..D2D[3] all available | TPMI cross-die register access limited to D2D[0] and D2D[3] paths. |
| 9 | **D2D GPSB port IDs** | ✅ D2D[0] TPMI port=676, D2D[3] TPMI port=748. Telemetry D2D[0]=675, D2D[3]=747. Streaming D2D[0]=678, D2D[3]=749. | Different port IDs | Update any scripts using hardcoded GPSB port IDs. |
| 10 | **PLDM Type 2 thermal sensors** | ✅ NWP implements PLDM sensors for thermal (see table below). Simplified PLDM model (terminus locator + processor entity + sensors only). | DMR PLDM model | BMC uses PLDM for DTS temp, margin, TjMax, DIMM temps. New OOB thermal interface. |
| 11 | **Enhanced PMT Discovery** | ✅ NWP-specific feature structures with NWP GUIDs and capability attributes (see below). Machine-readable JSON spec: [Feature_Discovery_NWP.json](https://docs.intel.com/documents/arch_datacenter/OOBMSM/Gen4/assets/Feature_Discovery_NWP.json) | DMR feature structures | Feature IDs unchanged (0x01–0x0B). Accelerator Telemetry (0x04) NOT listed for NWP. NWP-specific GUIDs in each structure. |
| 12 | **SoC Topology Aggregator** | ✅ NWP layout: 26 dwords. CBB0/CBB1 masks (Aggregator, Watcher, Crashlog). Core mask per CBB = 128 bits (4 dwords for 48 cores). `Enabled MCDDR Mask` + `Enabled IO-CA Mask`. | DMR: CBB0–CBB3 masks, 64-bit core masks | Topology aggregator semantic space updated for NWP die topology. |
| 13 | **CPUID** | ✅ NWP: Family=0xF, Model=0x5 (Extended Family=0x4, Extended Model=0x0). Stepping=0x0. | DMR: Model=0x1 | PMT Product ID decode must use NWP CPUID. |

#### NWP PMT Objects Table (Thermal-Relevant Subset)

| Type | Index | GUID | Object | Buffer [bytes] | IB | OOB |
|------|-------|------|--------|----------------|----|-----|
| Aggregator | 0 | `0x13274820` | iMH PUNIT Telemetry Aggregator | 8192 | ✓ | ✓ |
| Aggregator | 1 | `0x47324885` | SoC Topology Aggregator | 104 | ✓ | ✓ |
| Aggregator | 2 | `0x13704938` | D2D ULA & IO-CA telemetry aggregator | 6992 | ✓ | ✓ |
| Aggregator | 3 | `0x14302515` | Per-core environmental aggregator CBBA | 12448 | ✓ | ✓ |
| Aggregator | 4 | `0x14151486` | Per-core performance aggregator CBBA | 11296→3104¹ | ✓ | ✓ |
| Aggregator | 7 | `0x14302515` | Per-core environmental aggregator CBBB | 12448 | ✓ | ✓ |
| Aggregator | 11 | `0x03074003` | CBB A PUNIT Telemetry | 12288 | ✓ | ✓ |
| Aggregator | 12 | `0x03074003` | CBB B PUNIT Telemetry | 12288 | ✓ | ✓ |
| Watcher | 7 | `0x4800D130` | TPMI Watcher | 48 cfg | ✓ | ✓ |

¹ Buffer sizes marked with `→` indicate HSD 13015122500 Non-POR reduction.

**Thermal-relevant PMT data** (package temp, margin, TjMax) lives in Aggregator index 0 (iMH PUNIT, GUID `0x13274820`) — same GUID as DMR but NWP-specific buffer layout/offsets.

#### NWP PLDM Type 2 Thermal Sensors

| Sensor | PLDM Name | Instances | Source | GPSB Access | Format |
|--------|-----------|-----------|--------|-------------|--------|
| DTS Package Temp | `pkg_temp_dts` | 2 (1/IMH) | PUNIT Aggregator `PACKAGE_TEMPERATURE.MARGIN_TO_TCONTROL` | PortID:0x13, MemRD, FID:0xF0, BAR:0x1, Offset:0x1028 | Int16 |
| Package Power Temp | `pkg_temp` | 2 (1/IMH) | PUNIT Aggregator `PACKAGE_TEMPERATURE.MARGIN_TO_TJMAX` | Same offset 0x1028 | Int16 |
| DIMM Temp | `dimm_temp_#ch_#dimNo` | 32 (16ch×2) | TPMI `OPC_DIMM_TEMPS_[0..3]` | PortID:0x13, CRRD, Offsets: 0xD530/0xD538/0xD540/0xD548 | Uint8 |
| DIMM TS0 Temp | `dimm_#ch_#No_ts0` | 32 (16ch×2) | GPSB `DIMM_TSOD_TEMP[0..1].dimm_temp_sensor0` | WIP | Uint8 |
| DIMM TS1 Temp | `dimm_#ch_#No_ts1` | 32 (16ch×2) | GPSB `DIMM_TSOD_TEMP[0..1].dimm_temp_sensor1` | WIP | Uint8 |
| Package TjMax | `inv_pkg_tjmax` | 2 (1/IMH) | PUNIT Aggregator `PACKAGE_TEMPERATURE.REF_TEMP` | PortID:0x13, MemRD, FID:0xF0, BAR:0x1, Offset:0x1028 | Uint8 |

#### NWP Enhanced PMT Discovery (Thermal-Relevant Features)

| Feature | ID | GUIDs | Thermal Significance |
|---------|----|-------|----------------------|
| Per Core Environmental Telemetry | 0x02 | `0x14302515` (MSM Agg), `0x03074002` (CBB PUNIT) | Workpoint histograms, current temp, DAS, stress level, FIVR health, energy, PEM status, C-state residency |
| Uncore Telemetry | 0x05 | `0x13704937` (OOBMSM), `0x13274820` (iMH PUNIT) | IO-CA telemetry, D2D ULA telemetry, PkgC residency |
| TPMI Control | 0x08 | `0x4800D130` (OOBMSM) | TPMI mailbox for OPC register access, lock capability |

#### NWP D2D Bridge Telemetry (Thermal-Adjacent)

NIO has 4 D2D instances connecting to 2 CBBs. D2D bridge telemetry monitors UBR/ULA counters for bandwidth utilization. Key topology mapping:

| D2D Instance | UFI Ports | UBR GPSB Port IDs | ULA GPSB Port IDs | Threshold (90%) |
|--------------|-----------|--------------------|--------------------|-----------------|
| D2D[0] | UFI0: UBR 0x497, UFI1: UBR 0x4B8 | ULA0: 0x3B4, ULA1: 0x3B5, ULA2: 0x3B6, ULA3: 0x3B7 | 72 (= 90% of 80B BL queue) |
| D2D[1] | UFI0: UBR 0x4A0, UFI1: UBR 0x4B9 | ULA0: 0x3B8..ULA3: 0x3BB | 72 |
| D2D[2] | UFI0: UBR 0x4A0, UFI1: UBR 0x4B9 | ULA0: 0x3BC..ULA3: 0x3BF | 72 |
| D2D[3] | UFI0: UBR 0x497, UFI1: UBR 0x4B8 | ULA0: 0x3C0..ULA3: 0x3C3 | 72 |

**Note**: Some D2D instances have crossed UFI channel→UBR mappings (e.g. D2D UFI0 → UBR port 1 and vice versa). OCODE TSS index must account for this crossing.

#### MCTP Bridge Table (NWP Static Endpoints)

| Hosting IP | Aggregators | Watchers | Crashlogs |
|-----------|-------------|----------|-----------|
| IMH PUNIT | 1 (idx 0) | 2 (idx 0-1) | 1 (idx 0) |
| IMH Primecode | 0 | 0 | 1 (idx 1) |
| OOB-MSM | 2 (idx 1-2) | 18 (idx 5-22) | 2 (idx 2-3) |
| S3M | 0 | 0 | 1 (idx 4) |
| OOB-AGGREGATOR | 8 (idx 3-10) | 8 (idx 31-38)¹ | 0 |
| CBB A PUNIT | 1 (idx 11) | 1 (idx 40¹) | 1 (idx 5) |
| CBB B PUNIT | 1 (idx 12) | 1 (idx 42¹) | 1 (idx 6) |

¹ Watcher indices for OOB-AGGREGATOR and CBB PUNITs may include IB/OOB sampler pairs.

#### Still Open (❓)

| Area | Question | Notes |
|------|----------|-------|
| TPMI PFS/LUT JSON | NWP-specific PFS/LUT files (equivalent to DMR `PFS_DMR0_2p7.json`)? | NWP FAS does not include PFS JSON links — check TPMI HAS for NWP PFS/LUT |
| TPMI SRAM size | Same 8KB on NIO? | Not explicitly stated in NWP FAS |
| OPC_PKG_THERM_STATUS bits | Same [13:0] definitions? Any new status bits for NIO? | FAS does not cover TPMI register bit definitions (that's TPMI HAS scope) |
| OPC_THERMAL_MONITOR formula | Same DECAY_FACTOR formula (2.3 × 2^N ms)? | Algorithm-level detail not in this FAS |
| TPMI ACPI (COR transition) | NWP follows DMR (VSEC/BAR) or COR (ACPI-based fixed MMIO)? | NWP FAS says TPMI supported — implies VSEC/BAR (DMR model) |
| DIMM TS0/TS1 GPSB access | GPSB register offsets for `DIMM_TSOD_TEMP` marked "WIP" in FAS | PLDM sensor implementation still in progress |
