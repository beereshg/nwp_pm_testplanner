# SoC Thermal > CBB DTS & Telemetry

> **Status**: Enriched — HW/FW/OS touchpoint tables populated from MCP HAS query (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

DMR CBB uses two classes of Digital Temperature Sensors: **Core DTS Gen2.6** (top die, 2 per DCM, up to 15 diodes each across Core and MLCSSA domains) and **SOC/CCF DTS Gen1** (base die — 1 always-on AON sensor, 2 six-diode SOC sensors covering VCCINF and UCIe domains, and up to 16 six-diode CCF sensors one per CBO cluster). Core DTS operates autonomously via Acode: it pushes a 64-bit `SHORT_TELEM` message to PUnit IO registers every ~102.4μS containing Domain0 (Core) and Domain1 (MLCSSA) min/max temperatures with valid bits; it also drives DTD sticky/non-sticky threshold interrupts for Do-Not-Exceed and ITD/TTD recalc respectively. Base and CCF DTS are read by PCode's **SA Thermal Puller** via PMSB IOs, unblocked at PH2.2. PCode aggregates all telemetry into per-domain PCU CRs, applies an EWMA filter (α=0.7), detects OOS conditions, drives CBB EMTTM PIDs and ITD/TTD voltage compensation, and sends periodic **`SOCKET_THERMAL`** HPMs to Root (iMH). Root (PrimeCode) aggregates across CBBs and exposes the results to software via `IA32_PACKAGE_THERM_STATUS`, `MCP_THERMAL_REPORT_1/2`, PECI `READ_MODULE_TEMP`, and TPMI thermal telemetry registers.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core DTS Gen2.6 | CBB Top Die (per DCM, 2 per DCM) | Measures per-core and MLCSSA temperatures; runs in one-shot mode with ~13μS CC0 / ~1mS CC6 sleep; 15 active diodes per DTS; DTD sticky/non-sticky threshold outputs; participates in thermtrip top-tile chain | `SHORT_TELEM` push to PUnit IO regs (~102.4μS), `IO_INTERRUPTS[25]` (DTD sticky → DNE), DTD non-sticky bits 0/1 (±3°C → ITD recalc), `active_diode_mask_32=0x7FFF`, `rdcal_mask1` (Core domain), `rdcal_mask2` (MLCSSA domain) | [DMR CBB Thermal Intg HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/DMR%20CBB%20Thermal%20Integration%20HAS/DMR%20CBB%20Thermal%20Integration%20HAS.html) |
| SOC/Base DTS Gen1 (AON DTS0, DTS1 south, DTS2 north) | CBB Base Die | AON DTS0: always-on single-diode (VCCINF, continuous mode); DTS1/2: 6-diode one-shot (VCCINF + UCIe domains, 258.78μS sleep); feed Inf/D2D EMTTM domains and VccInf ITD min-temp to iMH; participate in base thermtrip chain | SA Thermal Puller (PMSB IOs) → `PCU_CR_DTS_TEMP_SOC[0..2]_CR0/1`; thermtrip daisy-chain wire; `oneshotmodeen`, `sleeptimer`, `active_diode_mask` fuses | [DMR CBB Thermal Intg HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/DMR%20CBB%20Thermal%20Integration%20HAS/DMR%20CBB%20Thermal%20Integration%20HAS.html) |
| CCF DTS Gen1 [0..15] | CBB Base Die (per CBO cluster) | Monitors LLC data arrays, CBO logic, and ring stop per CCF cluster; 6 diodes per instance; grouped by CCF FIVR domain for PID and ITD; participate in base thermtrip chain | SA Thermal Puller → `PCU_CR_DTS_TEMP_CCF[0..15]` (min/max per FIVR domain); thermtrip daisy-chain; 13.02μS one-shot sleep | [DMR CBB Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) |
| PMSB / SA Thermal Puller | CBB | Sideband infrastructure; PCode periodically reads base/CCF DTS temperatures via PMSB IOs; unblocked at PH2.2 | PMSB IO reads → PCU CRs; also carries `CROSS_CORE_THROTTLE_REQ` (from ACP) and other PM sideband messages | [CBB Thermal MAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/MAS/Thermal/CBB_thermal_mas.html) |
| Core PMA / ACP | CBB Top Die (per core) | Receives SHORT_TELEM output from Core DTS; runs EMTTM PID and ITD/TTD using DTS readings; forwards aggregated min/max via SHORT_TELEM push to PUnit | `IO_ACODE_ALGO_VALUES1[MAX_ALLOWED_RATIO]`, `EMTTM_ALGO_MISC[CONTROL_TEMP]`, `CORE_PMA_CR_CONFIG_10` | [ACP HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html) |
| PUnit | CBB | Aggregates all DTS telemetry from Core PMA (SHORT_TELEM) and PMSB puller (base/CCF DTS); applies EWMA filter (α=0.7); drives EMTTM PIDs; detects OOS; sends SOCKET_THERMAL HPM to Root | `PCU_CR_DTS_TEMP_IA_CCP[0..31]` (per-CCP), `PCU_CR_DTS_TEMP_CCF[0..15]`, `PCU_CR_DTS_TEMP_SOC[0..2]_CR0/1`; HPM `SOCKET_THERMAL` → iMH | [DMR CBB Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core PMA, CBB Top Die (per core) | Reads Core DTS Gen2.6 locally; runs EMTTM PID and ITD/TTD; pushes per-DCM SHORT_TELEM to PUnit; handles DTD interrupts for fast thermal events | **SHORT_TELEM push** (~102.4μS): Domain0 (Core) + Domain1 (MLCSSA) min/max temps with valid bits → PUnit IO regs; DTD sticky → Hammer to LFM; DTD non-sticky (±3°C) → ITD recalc (~30-60μS); reports `IA32_THERM_STATUS[THERMAL_MONITOR_STATUS]` | [ACP HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html) |
| PCode | CBB PUnit | Primary telemetry aggregator — reads base/CCF DTS via SA Thermal Puller (PMSB IOs) from PH2.2; receives Core SHORT_TELEM; stores per-domain temps in PCU CRs; applies EWMA filter; detects OOS; sends SOCKET_THERMAL HPM; drives CBB EMTTM PIDs and ITD | **SA Thermal Puller** (PMSB IOs, unblocked PH2.2): reads AON/DTS1/DTS2/CCF DTS; **EWMA** (α=0.7): `EWMA(t) = 0.3×Temp(t) + 0.7×EWMA(t-1)`; **OOS** detection: `Max_Temp > eff_tj_max+10°C` OR throttled AND `>eff_tj_max for >20mS`; **HPM SOCKET_THERMAL** → iMH (OOS, MIN/MAX_TEMP, margins); **temperature decay** on invalid CCP telemetry (CC6/disabled); enabled at PH1.2 (base DTS fuses pulled) | [DMR CBB Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html); [Pcode Thermal FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/Thermals/Thermal%20Management_FAS.html) |
| PrimeCode (iMH) | IMH die | Receives SOCKET_THERMAL HPM from each CBB; aggregates into package-level thermal status; drives OS-visible package MSRs; delivers thermal interrupts to cores | Receives `SOCKET_THERMAL` HPM (OOS, MIN/MAX_TEMP, MARGIN_TO_THROTTLE, MARGIN_TO_TCONTROL); updates `IA32_PACKAGE_THERM_STATUS`, `MCP_THERMAL_REPORT_1` (margins), `MCP_THERMAL_REPORT_2` (absolute max temp); sends `DNS_EVENT_DELIVERY[THERMAL_INTERRUPT]` to CBB (RR=1) for core thermal interrupt delivery; exposes data via PECI `READ_MODULE_TEMP` (cmd 9) and TPMI | [Socket Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) |
| BIOS | BIOS/UEFI | Programs DTS interrupt thresholds and fan temperature offsets at boot | Programs `IA32_THERM_INTERRUPT` threshold values; programs `IA32_TEMPERATURE_TARGET[FAN_TEMP_TARGET_OFST]` and `TJ_MAX_TCC_OFFSET` | DMR BIOS EDS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_THERM_STATUS` | 0x19C (per-core) | RO / RWC | [23:16] Digital Readout (relative temp to TjMax, RO); [0] THERMAL_MONITOR_STATUS (EMTTM throttle active); [1] THERMAL_MONITOR_LOG (sticky, clear-on-write-0); [4] OUT_OF_SPEC_STATUS; [14/15] CROSS_DOMAIN_LIMIT_STATUS/LOG; [31] VALID | Intel SDM; DMR CBB PM HAS |
| MSR `IA32_THERM_INTERRUPT` | 0x19B (per-core) | RW | Controls thermal interrupt generation: [0/1] HIGH/LOW_TEMP threshold enable; [2/3] PROCHOT/FORCEPR enable; [4] OOS interrupt enable; [8/16/24] THRESHOLD1/2 relative temps + enable bits | Intel SDM |
| MSR `IA32_TEMPERATURE_TARGET` | 0x1A2 (package) | RW (fields vary) | [23:16] REF_TEMP (fused TjMax, RO); [29:24] TJ_MAX_TCC_OFFSET (RO); [15:8] FAN_TEMP_TARGET_OFST (RW); [6:0] TCC_OFFSET_TIME_WINDOW (RATL, RO) | Intel SDM; DMR Thermal HAS |
| MSR `IA32_PACKAGE_THERM_STATUS` | 0x1B1 (package) | RO / RWC | Package-level thermal status aggregated by iMH: [23:16] TEMPERATURE (relative to pkg TjMax); [0/1] PKG_THERMAL_STATUS/LOG; [4/5] OOS_STATUS/LOG; [10/11] POWER_LIMIT_STATUS/LOG; sticky log bits clear-on-write-0 | Intel SDM; Socket Thermal HAS |
| MSR `MCP_THERMAL_REPORT_1` | 0x1A3 (package) | RO | [15:0] MARGIN_TO_THROTTLE (S10.6, negative = headroom available); [31:16] MARGIN_TO_TCONTROL (S10.6, positive = margin to fan engage) — EWMA-filtered values from SOCKET_THERMAL HPM | DMR Thermal HAS |
| MSR `MCP_THERMAL_REPORT_2` | 0x1A5 (package) | RO | [15:0] PACKAGE_ABSOLUTE_MAX_TEMPERATURE (S10.6) — highest absolute temperature across all CBBs | DMR Thermal HAS |
| MMIO `PP0_TEMPERATURE_0_0_0_MCHBAR_PCU` | 0x597C (MCHBAR) | RO | EWMA of maximum CCP temperature in °C — OS-accessible via MMIO; commonly read by OS thermal drivers | DMR CBB Thermal MAS |
| PECI `GetDIB` / `RdPkgConfig` cmd 9 | PECI addr (per socket) | RO (OOB) | `READ_MODULE_TEMP` — returns max temps: DCM, CBB die, Ring; used by BMC for fan control and platform thermal telemetry | DMR PECI Spec |
| TPMI (thermal telemetry group) | TPMI opcode (OOB MMIO) | RO (OOB RW) | GPSB_TELEM_CFG_0/1 and thermal watcher registers expose per-domain temperature telemetry and control to out-of-band agents (BMC) and host OS via MMIO; SAI-controlled access | DMR TPMI HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Core SHORT_TELEM push period | ~102.4 | μS | Per DCM; Core PMA hardware push to PUnit IO regs; both CC0 and light sleep states | PNC PM HAS §9.4.5; DMR CBB Thermal Intg HAS |
| Core DTS one-shot sleep (CC0) | ~13 | μS | `sleeptimer=0x0`; Gen2.6 DTS scan rate in active state | DMR CBB Thermal Intg HAS; `sleeptimer` fuse |
| Core DTS one-shot sleep (CC6) | ~1034 | μS | `sleeptimer1=0x19`; Gen2.6 DTS scan rate in CC6 | DMR CBB Thermal Intg HAS; `sleeptimer1` fuse |
| SOC DTS1/2 one-shot sleep | 258.78 | μS | `sleeptimer=0x6`; Gen1 DTS (VCCINF + UCIe domains) | DMR CBB Thermal Intg HAS; `sleeptimer` fuse |
| CCF DTS one-shot sleep | 13.02 | μS | `sleeptimer=0x0`; Gen1 DTS per CBO cluster | DMR CBB Thermal Intg HAS; `sleeptimer` fuse |
| AON DTS0 scan mode | continuous | — | `oneshotmodeen=0`; always-on single diode; never sleeps | DMR CBB Thermal Intg HAS |
| EWMA filter coefficient (α) | 0.7 | — | `EWMA(t) = 0.3×Temp(t) + 0.7×EWMA(t-1)`; applied to all domain temps before SOCKET_THERMAL HPM | DMR CBB Thermal Mgmt HAS |
| OOS temperature offset | +10 | °C above eff_tj_max | Condition 1: `Max_Temp > eff_tj_max + 10°C` triggers OOS flag | DMR CBB Thermal Mgmt HAS |
| OOS hold-off duration | >20 | mS | Condition 2: any domain max throttled AND `Max_Temp > eff_tj_max` sustained for >20mS | DMR CBB Thermal Mgmt HAS |
| DTD non-sticky interrupt threshold | ±3 | °C | Triggers ITD/TTD voltage recalc in Acode; ~30–60μS response | DMR CBB Thermal Intg HAS; `dtd_sticky_thr_h` fuse |
| DTD sticky interrupt response (Hammer) | ~nS | — | Core forced to LFM; `IO_INTERRUPTS[25]`; threshold = TjMax + 7°C | DMR CBB Thermal Intg HAS |
| DTD sticky threshold formula | TjMax + 7 | °C | `dtd_sticky_thr_h[8:0]` = `(temp + 64) × 2` (U8.1 format) | DMR CBB Thermal Intg HAS |
| Acode ITD recalc response (interrupt path) | ~30–60 | μS | DTD non-sticky → Acode interrupt handler → voltage recalc; faster than periodic path | DMR CBB Thermal Intg HAS |
| SA Thermal Puller unblock phase | PH2.2 | — | PMSB unblock → PCode begins reading base/CCF DTS; before this only AON thermtrip is active | DMR CBB Thermal Mgmt HAS |
| Base DTS thermtrip active from | PH1.2 | — | PCode pulls DTS fuses at PH1.2; thermtrip chain becomes active; only thermal protection until EMTTM starts | DMR CBB Thermal Mgmt HAS |
| CBB EMTTM + dynamic ITD active from | PH2.52 | — | Slow loop starts; EWMA initialized; all CBB ITD domains track temperature periodically | DMR CBB Thermal Mgmt HAS |
| Gen1 DTS diode scan time | 13.24 | μS/diode | Base die DTS (SOC/CCF); scan time per diode | DMR CBB Thermal Intg HAS |
| Gen2.6 DTS diode scan time | 2.56 | μS/diode | Core top die DTS; faster scan enables higher domain count | DMR CBB Thermal Intg HAS |
| Temperature decay activation | on invalid valid bits | — | Applies when CCP enters CC6 or DTS disabled; decays toward ambient at fused `THERM_DECAY_RATE`; prevents stale hot values | DMR CBB Thermal Mgmt HAS |

## NWP Delta

**CBB DTS telemetry is supported on NWP** with sensor topology changes.

### Topology Changes
- Single diode replaces multiple diodes used in DMR for some DTS instances
- DTS IP version and placement updated for NWP CBB
- DTS daisy-chaining for thermtrip preserved
- Telemetry flows (SHORT_TELEM push, SA Thermal Puller) reused from DMR

### Functional Changes
- 2 CBBs (vs 4) — fewer DTS aggregation paths
- EWMA filtering algorithm unchanged
- HPM SOCKET_THERMAL telemetry to Root unchanged

### Validation Impact
- DTS diode mapping needs NWP-specific verification (HSD 14027181891)
- Same telemetry pipeline — reuse DMR test infrastructure

## Legacy (Human-Curated Reference)

### Architecture Summary

CBB DTS & Telemetry covers the **Digital Temperature Sensors** distributed across the DMR CBB die and the **thermal telemetry pipeline** that delivers temperature data from sensors to PCode, Root (iMH), and OS-visible MSRs/TPMI. This is the sensing and reporting infrastructure underneath all thermal management features (EMTTM, ITD, Thermtrip, OOS).

#### Sensor Topology Overview

```
  Top Die (per DCM)                 Base Die
  ┌──────────────────┐              ┌────────────────────────────┐
  │  Core DTS0 (Gen2.6)  │         │  DTS0 (AON, Gen1) — 1 diode  │
  │    15 diodes         │         │  DTS1 (south, Gen1) — 6 diodes│
  │  Core DTS1 (Gen2.6)  │         │  DTS2 (north, Gen1) — 6 diodes│
  │    15 diodes         │         │  CCF DTS[0..15] (Gen1) — 6 ea │
  └──────┬───────────────┘         └─────────────┬──────────────────┘
         │ SHORT_TELEM push                      │ SA Thermal Puller
         │ (~102.4μS per DCM)                    │ (PMSB IOs)
         ▼                                       ▼
  ┌─────────────────────────────────────────────────────┐
  │  CBB PCode                                           │
  │  • Stores per-CCP/CCF/SOC temps in PCU CRs           │
  │  • Applies EWMA filter (α=0.7)                       │
  │  • Detects OOS, drives EMTTM PID, cross-throttle     │
  │  • Sends SOCKET_THERMAL HPM to Root                   │
  └───────────────────────┬─────────────────────────────┘
                          │ HPM: SOCKET_THERMAL
                          ▼
  ┌─────────────────────────────────────────────────────┐
  │  Root (iMH)                                          │
  │  • Package MSRs: IA32_PACKAGE_THERM_STATUS           │
  │  • THERM_MARGIN, MCP_THERMAL_REPORT_1/2              │
  │  • Thermal interrupt delivery                         │
  │  • PECI/TPMI readout for OS/BMC                       │
  └─────────────────────────────────────────────────────┘
```

#### DTS Types & Properties

| DTS Type | Gen | Location | Diodes | Scan Rate | Report Method | Thermtrip |
|----------|-----|----------|--------|-----------|---------------|-----------|
| DTS0 (AON) | Gen1 | Base (always-on domain) | 1 | Continuous (no sleep) | Thermal puller → PCode IOs | Yes (base chain) |
| DTS1 (south) | Gen1 | Base | 6 | One-shot, 258.78μS sleep | Thermal puller → PCode IOs | Yes (base chain) |
| DTS2 (north) | Gen1 | Base | 6 | One-shot, 258.78μS sleep | Thermal puller → PCode IOs | Yes (base chain) |
| CCF DTS[0..15] | Gen1 | Base (per CBO cluster) | 6 each | One-shot, 13.02μS sleep | Thermal puller → min/max per CCF FIVR | Yes (base chain) |
| Core DTS0/1 | Gen2.6 | Top (per DCM, 2 per module) | 15+1 each | One-shot, ~13μS CC0 / ~1mS CC6 | Core PMA push → SHORT_TELEM | Yes (top tile chain) |

**DMR totals**: Top die: 64 DTS (Gen2.6), ~512 diodes. Base die: up to 15 DTS (Gen1), ~85 diodes.

#### DTS Gen Version Comparison

| Property | Gen1 (Base) | Gen2.6 (Core Top) |
|----------|-------------|-------------------|
| Diode scan time | 13.24μS/diode | 2.56μS/diode |
| Max diodes | 6 | 16 (legacy) + 16 (shared) |
| DTD threshold pins | 1 (sticky only) | 4 (non-sticky + sticky) |
| Configurable min/max domains | No | Yes (3 domain sets via rdcal_mask) |
| Retention support | No | Yes |
| Main clock | 100MHz | 400/200/100MHz (strap-selected) |

#### Core DCM Diode Layout (PNC)

Each DTS within a PNC DCM connects 15 diodes (16th reserved for DLVR, not connected in DMR):

- **Domain0 (Core)** — `rdcal_mask1=0x3FBF`: OOO_int, OOO_vec, FMA, MEU×2, FE, alloc_int, exe_vec, MSID, FMAv1, OOO_vec2, MLC_shared, MEU_exeint (13 diodes)
- **Domain1 (MLCSSA)** — `rdcal_mask2=0x101`: MLC SRAM diodes (2 per DTS: bits 0, 8)
- Each DCM aggregates 2× DTS min/max → pushes per-domain min/max via SHORT_TELEM

#### SOC DTS Sensing Domains

| DTS | Diode | Power Domain | Physical Location |
|-----|-------|-------------|-------------------|
| DTS0 (AON) | D0 | VCCINF | PAR PDN (always-on) |
| DTS1 (south) | D0-D1 | VCCINF | GPIO south, center |
| DTS1 (south) | D2-D5 | VCC2IA | UCIe DDA0/1 south |
| DTS2 (north) | D0-D1 | VCCINF | GPIO north, ESE |
| DTS2 (north) | D2-D5 | VCC2IA | UCIe DDA0/1 north |

#### CBO Cluster DTS Sensing Domains

Each of the 16 CCF DTS instances (Gen1, 6 diodes) monitors one CBO cluster:

| Diode Range | Sensing Region | Notes |
|-------------|---------------|-------|
| D0-D2 | LLC data arrays | Hot spots in LLC SRAM |
| D3-D4 | CBO north/south | Coherence agent logic |
| D5 | Ring stop | Interconnect fabric at this slice |

CCF DTS are grouped by FIVR domain — PCode reads min/max per CCF FIVR domain for CCF EMTTM PID and ITD correction.

---

### Execution Flow

#### DTS Enable Sequence (Boot)

1. **PH0 (InfPwrGood)**: No DTS active
2. **PH1.2 (pd_fuse_infra reset)**: PCode pulls DTS fuses, sets `DTSEnable` for base DTS (AON, DTS1, DTS2, CCF). **Thermtrip becomes active** — sole thermal protection until EMTTM starts. DTS uses worst-case ITD (safe voltage: `MIN_TEMPERATURE` min, `ITD_CUTOFF_TJ` max)
3. **PH2.2 (SA Thermal Puller unblocked)**: PMSB unblock → PCode thermal puller starts reading base SOC/CCF DTS temps via PMSB IOs
4. **PH2.52 (Slow loop starts)**: CBB EMTTM + dynamic ITD active for all CBB domains. EWMA filter initialized.
5. **PH3-5 (Core reset exit)**: Core DTS enabled, Acode starts SHORT_TELEM push. Core EMTTM + ITD/TTD activate after first valid telemetry received by PCode.
6. **PH6 (Ucode/BIOS wake)**: eff_tj_max refined — before PH6, PCode uses worst-case `HIGHEST_TJ_MAX`. After: SST_PP/BF/C1E resolved.

#### CCP Thermal Telemetry Pipeline (Core → PCode → Root → OS)

```
Core DTS0/1 ──push──→ Core PMA ──SHORT_TELEM──→ PCode
   (per DCM)           (min/max per domain)        │
                                                   ├──→ PCU_CR_DTS_TEMP_IA_CCP[module] (per-CCP)
                                                   ├──→ EWMA filter → SOCKET_THERMAL HPM → Root
                                                   ├──→ EMTTM PID (CCF/Core cross-throttle)
                                                   └──→ OOS detection
```

##### SHORT_TELEM Format (64-bit)

| Bits | Field | Description |
|------|-------|-------------|
| [8:0] | Domain0 Min Temp | Min of all CCP core diodes (excl. MLCSSA) |
| [11] | Valid0 | Domain0 min valid |
| [24:16] | Domain0 Max Temp | Max of all CCP core diodes |
| [27] | Valid1 | Domain0 max valid |
| [40:32] | Domain1 Min Temp | Min of MLCSSA domain |
| [43] | Valid2 | Domain1 min valid |
| [56:48] | Domain1 Max Temp | Max of MLCSSA domain |
| [59] | Valid3 | Domain1 max valid |

Push rate: ~102.4μS per DCM.

##### SOC DTS Telemetry Pipeline (Base DTS → PCode)

```
AON DTS0 ──puller──→ PCU_CR_DTS_TEMP_SOC[0]_CR0 (1 diode, always-on)
DTS1     ──puller──→ PCU_CR_DTS_TEMP_SOC[1]_CR0/1 (6 diodes, VccInf + UCIe south)
DTS2     ──puller──→ PCU_CR_DTS_TEMP_SOC[2]_CR0/1 (6 diodes, VccInf + UCIe north)
```

SOC DTS data feeds:
- **Inf EMTTM domain** — `PCU_CR_DTS_TEMP_SOC[2:0]_CR0/1`
- **D2D EMTTM domain** — `PCU_CR_DTS_TEMP_SOC[2:1]_CR[1:0]` (UCIe diodes only)
- **Min temp → iMH** — via `SOCKET_THERMAL` HPM `MIN_TEMP` field (for VccInf ITD)

##### CCF DTS Telemetry Pipeline

```
CCF DTS[0..15] ──puller──→ PCU_CR_DTS_TEMP_CCF[0..N] (min/max per CCF FIVR domain)
```

CCF DTS data feeds:
- **CCF EMTTM domain** — frequency limiting via PID
- **CCF ITD** — per-FIVR-domain voltage compensation (4 shadows × 2 FIVRs = 8 domains per die)

#### CBB Thermal Telemetry to Root (SOCKET_THERMAL HPM)

PCode aggregates and EWMA-filters all temperature data, then sends `SOCKET_THERMAL` HPM to Root:

| Field | Format | Description |
|-------|--------|-------------|
| `OOS` | bool | Out-Of-Spec: `(Max_Temp > eff_tj_max + 10°C)` OR `(any domain max throttled AND Max_Temp > eff_tj_max for >20mS)` |
| `MIN_TEMP` | S9.6 | Min absolute temp — Root uses for VccInf ITD |
| `MAX_TEMP` | S9.6 | Max absolute temp |
| `MARGIN_TO_THROTTLE` | S9.6 | EWMA relative temp to eff_tj_max (negative = margin available) |
| `MARGIN_TO_TCONTROL` | S9.6 | EWMA relative temp to eff_tj_max − Tcontrol offset (positive = margin) |

**EWMA formula**: `EWMA(t) = (1−α) × Current_Temp(t) + α × EWMA(t−1)`, α = 0.7

#### Invalid Temperature Handling

When core enters CC6 or DTS becomes invalid:

1. PCode clears temperature valid bits for that CCP
2. **Temperature decay model** applied: temperature decays toward ambient at fused `THERM_DECAY_RATE` — prevents stale hot values from persisting
3. If all CCP telemetry invalid → CBB EMTTM holds last known state, cross-throttle frozen
4. On re-entry to CC0: new SHORT_TELEM received, valid bits re-asserted, decay stops

#### Disabled Core DTS Operation

| Scenario | DTS Behavior | Telemetry Effect | Thermtrip |
|----------|-------------|-----------------|-----------|
| Single core disabled in DCM | Acode disables DTS (`dtsenable=0, dtsenableovr=1`) | Remaining core DTS reports; disabled core excluded | Chain passes through (VCCINF-supplied) |
| Both cores disabled in DCM | Both DTS disabled | CCP valids de-asserted; PCode ignores module | Chain passes through |
| Entire top tile disabled | Shaft isolates thermtrip signal to 0 | No telemetry from tile | Isolated — no false triggers |
| Disabled LLC/CCF slice | CCF DTS remains enabled | Normal CCF temp reporting | Normal — ring traffic still flows |

#### AON DTS Special Behavior

- **Always-on**: DTS0 runs in continuous mode (`oneshotmodeen=0`), never sleeps
- **Single diode**: Only 1 diode in PAR PDN (VCCINF domain)
- **Purpose**: Provides a baseline VCCINF temperature even when all other DTS are in one-shot sleep or core is in CC6
- **Thermtrip**: Participates in base die chain — protects against VCCINF domain thermal runaway

---

### Key Registers & Interfaces

#### PCode Temperature CRs (Internal)

| CR | Description |
|----|-------------|
| `PCU_CR_DTS_TEMP_IA_CCP[0..31]` | Per-CCP core temperature (from SHORT_TELEM Domain0 max) |
| `PCU_CR_DTS_TEMP_CCF[0..15]` | Per-CCF-FIVR-domain min/max temperature |
| `PCU_CR_DTS_TEMP_SOC[0]_CR0` | AON DTS temperature |
| `PCU_CR_DTS_TEMP_SOC[1]_CR0/1` | DTS1 (south) temperatures — VccInf + UCIe |
| `PCU_CR_DTS_TEMP_SOC[2]_CR0/1` | DTS2 (north) temperatures — VccInf + UCIe |

#### OS-Visible MSRs

| MSR | Address | Scope | Key Fields |
|-----|---------|-------|------------|
| `IA32_THERM_STATUS` | 0x19C | Core | `TEMPERATURE[23:16]` (relative to TjMax), `VALID[31]`, `THERMAL_MONITOR_STATUS[0]`, `OOS_STATUS[4]` |
| `IA32_THERM_INTERRUPT` | 0x19B | Core | `HIGH/LOW_TEMP_INT_ENABLE[0:1]`, `THRESHOLD1/2_REL_TEMP + INT_ENABLE` |
| `IA32_TEMPERATURE_TARGET` | 0x1A2 | Pkg-MC | `REF_TEMP[23:16]` (fused TjMax), `TJ_MAX_TCC_OFFSET[27:24]`, `FAN_TEMP_TARGET_OFST[13:8]` |
| `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | Pkg | `TEMPERATURE`, `OOS_STATUS/LOG`, `THRESHOLD1/2` (package-level from iMH) |
| `MCP_THERMAL_REPORT_1` | 0x1A3 | Pkg | `MARGIN_TO_THROTTLE[15:0]` (S10.6), `MARGIN_TO_TCONTROL[31:16]` (S10.6) |
| `MCP_THERMAL_REPORT_2` | 0x1A5 | Pkg | `PACKAGE_ABSOLUTE_MAX_TEMPERATURE[15:0]` (S10.6) |

#### MMIO

| Register | Offset | Description |
|----------|--------|-------------|
| `PP0_TEMPERATURE_0_0_0_MCHBAR_PCU` | 0x597C | EWMA of Max CCP temperature (°C) |

#### HPM Messages

| Message | Direction | Purpose |
|---------|-----------|---------|
| `SOCKET_THERMAL` | CBB → Root | Periodic thermal telemetry (OOS, MIN/MAX_TEMP, margins) |
| `SOCKET_THERMAL` | Root → CBB | `THERMAL_MONITOR_ENABLE`, `DECAY` config |
| `DNS_EVENT_DELIVERY[THERMAL_INTERRUPT]` | Root → CBB | Trigger core thermal interrupts (RR=1) |

#### PECI/TPMI Telemetry

| PCS Cmd | Name | Mapped to PMT? | Description |
|---------|------|----------------|-------------|
| 2 | PKG_MAX_TEMP | No | Package temperature (T_avg) |
| 9 | READ_MODULE_TEMP | Yes | Max temps: DCM, CBB die, Ring |
| 10 | THERM_MARGIN | No | DTS2.0 thermal margin |
| 16 | TEMP_TARGET | Yes | Processor temperature target fields |

#### DTS Fuse Configuration

| Fuse | AON DTS0 | SOC DTS1/2 | CCF DTS[0..15] | Core DTS0/1 |
|------|----------|-----------|----------------|-------------|
| `oneshotmodeen` | 0x0 (continuous) | 0x1 | 0x1 | 0x1 |
| `sleeptimer` (CC0) | N/A | 0x6 (258.78μS) | 0x0 (13.02μS) | 0x0 (~13μS) |
| `sleeptimer1` (CC6) | N/A | N/A | N/A | 0x19 (1.034mS) |
| `catfilteren` | 0x1 | 0x1 | 0x1 | 0x1 |
| `active_diode_mask` | 0x1 | 0x3F | 0x3F | N/A |
| `active_diode_mask_32` | N/A | N/A | N/A | 0x7FFF (15 diodes) |
| `dtd_sticky_thr_h` | 9'h0 | 9'h0 | 9'h0 | `HIGHEST_TJ_MAX+5°C` |
| `rdcal_mask1` | N/A | N/A | N/A | 0x3FBF (Core domain) |
| `rdcal_mask2` | N/A | N/A | N/A | 0x101 (MLCSSA domain) |

---

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS (CBB Thermal Intg) | [DMR CBB Thermal Integration](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/DMR%20CBB%20Thermal%20Integration%20HAS/DMR%20CBB%20Thermal%20Integration%20HAS.html) | DTS topology, diode mapping, fuse config |
| HAS (CBB Thermal Mgmt) | [DMR CBB Thermal Management](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) | EMTTM, telemetry, EWMA, OOS |
| HAS (DMR SOC Thermal) | [DMR SOC Thermal](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | SOC-level thermal reporting |
| HAS (Socket Thermal) | [Socket Thermal Mgmt](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | iMH-level thermal, pkg MSRs |
| HAS (ACP Core) | [Autonomous Core Perimeter PM](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html#acp-20-autonomous-thermal-management) | Core DTS telemetry interface |
| HAS (PNC PM — local) | `KB/pm_features/PNC PM HAS 0.5_text.txt` | **Authoritative core-level spec**: §8.12 Core C6 DTS sleep timers, §9.4.5 SHORT_TELEM format/push rate, §11.8–11.9 THERM_STATUS/INTERRUPT uCode handling, §13 telemetry, §7 budget negotiation/WP, §2.2.8 Acode reset. Source for Sensor Topology Overview and DCM domain split (`rdcal_mask1/2`). |
| MAS (NWP iMH DTS) | [NWP iMH SOC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#dtsthermal-diode-and-thermtrip-chaining) | NWP iMH DTS placement + thermtrip chaining |
| FAS (Pcode Thermal) | [Pcode Thermal FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/Thermals/Thermal%20Management_FAS.html) | PCode thermal puller, EWMA implementation |
| MAS (Punit Thermal) | [CBB Thermal MAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/MAS/Thermal/CBB_thermal_mas.html) | Register/IO details |
| HSD | 13012403519 | Core rdcal_mask1/2 DCM domain aggregation |
| HSD | 13010612929 | Disabled DTS in DCM — keep associated DTS disabled |
| Related KB | [ACP Thermal](acp.md) | Full ACP/EMTTM/ITD details that consume this telemetry |

#### Validation Approach (from Test Case Cues)

- **AON DTS** (22022421456): Verify DTS0 continuous mode (`oneshotmodeen=0`), single diode reads valid temp in `PCU_CR_DTS_TEMP_SOC[0]_CR0`. Confirm AON DTS active during PkgC6 and across all power states. Compare with SOC DTS1/2 for sanity.
- **CBO Cluster DTS** (22022421458): Verify all 16 CCF DTS[0..15] instances read valid temps in `PCU_CR_DTS_TEMP_CCF[N]`. Check per-FIVR-domain min/max aggregation. Apply LLC workload → verify temp increase. Confirm disabled LLC slice DTS still reports (ring traffic still flows).
- **CCP Thermal Telemetry** (22022421461): Verify SHORT_TELEM packets from each DCM. Check Domain0 (Core) and Domain1 (MLCSSA) min/max temps and valid bits. Verify `PCU_CR_DTS_TEMP_IA_CCP[module]` updated. Verify EWMA filtering in `SOCKET_THERMAL` HPM. Check `MARGIN_TO_THROTTLE` and `MARGIN_TO_TCONTROL` signs match thermal state.
- **Core DTS** (22022421465): Verify 2 DTS per DCM (DTS0/1), 15 active diodes each (`active_diode_mask_32=0x7FFF`). Check `rdcal_mask1/2` domain partitioning. Verify CC0 vs CC6 sleep timer switching (`sleeptimer` → `sleeptimer1`). Apply core workload → verify temp tracks in `IA32_THERM_STATUS[TEMPERATURE]`.
- **Core Disabled DTS** (22022421468): Disable one core in DCM via fuse/knob → verify DTS for disabled core stops reporting (`dtsenable=0`), remaining core telemetry continues. Disable both cores → verify CCP valids de-asserted, PCode ignores module. Verify thermtrip chain passes through disabled core (VCCINF-supplied DTS digital). Verify disabled tile shaft isolation.
- **SOC DTS** (22022421469): Verify DTS1 (south) and DTS2 (north) read 6 diodes each across VCCINF + VCC2IA domains. Check SOC temps in `PCU_CR_DTS_TEMP_SOC[1..2]_CR0/1`. Verify UCIe diode temps feed D2D EMTTM domain. Verify min temp flows to iMH via `SOCKET_THERMAL[MIN_TEMP]` for VccInf ITD.
- **PSS CBB DTS Telemetry** (22022015466): End-to-end sanity: read all DTS categories (AON, SOC, CCF, Core), verify OS-visible MSRs (`IA32_THERM_STATUS`, `IA32_PACKAGE_THERM_STATUS`, `MCP_THERMAL_REPORT_1/2`) populated and consistent. Check PECI `READ_MODULE_TEMP` returns valid data. Verify `PP0_TEMPERATURE` MMIO register.

---

### Related Sightings
<!-- No NWP CBB DTS sightings identified yet — populate as they arise -->

---

### NWP Delta

> **Items to verify for NWP** (not yet confirmed — check NWP HAS when available):

| Area | Question | DMR Baseline |
|------|----------|--------------|
| DTS gen version | NWP top die still Gen2.6? Base still Gen1? | DMR: Top Gen2.6 (2.56μS/diode), Base Gen1 (13.24μS/diode) |
| Core diode count | Same 15 diodes/DTS? Check DLVR diode #16 status | DMR: 15 active (16th = DLVR prep, not connected) |
| CCF DTS count | NWP fewer CCF slices → fewer CCF DTS instances? | DMR: up to 16 CCF DTS |
| SOC DTS count | NWP NIO replaces iMH — base die DTS placement? | DMR: 3 base DTS (AON + DTS1 south + DTS2 north) |
| `rdcal_mask1/2` | Same Domain0/Domain1 diode groupings? | DMR: mask1=0x3FBF (Core), mask2=0x101 (MLCSSA) |
| DTS `dtd_sticky_thr_h` | Same formula? DMR docs say +5°C in fuse table vs +7°C in validation | DMR: `HIGHEST_TJ_MAX + 5°C` (fuse table); some docs say +7°C |
| AON DTS diodes | Still single diode? NWP may have different always-on domain | DMR: 1 diode in PAR PDN |
| Thermal puller | NWP NIO equivalent of SA thermal puller? | DMR: Punit SA thermal puller pulls SOC/CCF DTS via PMSB |
| SHORT_TELEM format | Same 64-bit packet with 4 telem IDs? | DMR: 4 × (9-bit temp + valid + telem_id) |
| EWMA α | Same α=0.7? | DMR: 0.7 |
| PECI/TPMI mapping | Same PCS commands? `READ_MODULE_TEMP` fields? | DMR: PCS 2/9/10/16/32 |
| PkgC6 DTS behavior | CBB DTS still active in PkgC6? Same decay model? | DMR: All CBB DTS remain enabled; core DTS stops → decay model |
| Disabled core DTS | Same `LP_ENABLE` mechanism? | DMR: `CORE_PMA_CR_LP_ENABLE[CORES_ENABLE_MASK]` |
| CCF disabled slice | Still monitored for thermal (ring traffic)? | DMR: Yes — even disabled LLC carries ring traffic |
