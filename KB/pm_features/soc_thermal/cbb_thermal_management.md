# SoC Thermal > CBB Thermal Management

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: CBB Thermal Management is the CBB-die layer of DMR's three-tier hierarchical thermal control — PCode EMTTM PID for CCF/Ring frequency limiting, cross-throttle coordination (core↔ring, core↔core, die↔die), and per-CBB temperature aggregation sent to Root via HPM.

**Topology**:
```
Core DTS ──SHORT_TELEM ~102.4 μS──> Acode (Core EMTTM PID ~300 μS)
                                      └── cross-core-throttle REQ ─> PCode
CBB SOC/CCF DTS ──SA Thermal Puller──> PCode (CBB EMTTM PID ~1 mS)
                                        ├── CCF/Ring freq ceiling ─> GPSS
                                        ├── VR HOT → P1 limit
                                        ├── PROCHOT fast-throttle handling
                                        └── HPM SOCKET_THERMAL ─────> PrimeCode (Root)
```

**Key operational principle**: PCode slow loop (~1 mS) uses a PID controller with squared-error acceleration (error ≤ −1°C → error ← −error²) to set a CCF/Ring frequency ceiling. Cross-throttle fires when a non-throttlable domain is hot, or when a throttlable domain is at min ratio and still above `eff_tj_max`. Temperature setpoint is `eff_tj_max = SST-PP_T_THROTTLE − (C1E_offset + TCC_offset)`.

**Boot activation**: SA Thermal Puller enabled at PH2.2 (PMSB unblock). CBB EMTTM slow loop starts at PH2.52. Core EMTTM (Acode) active from PH3+ (CCP telemetry).

DMR thermal management is hierarchically controlled by three levels:

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core DTS Gen2.6 | CBB Top Die (per core) | Per-core temperature input to Acode EMTTM and DTD interrupts | SHORT_TELEM ~102.4 μS; DTD sticky/non-sticky wires | [ACP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html) |
| SOC / CCF DTS | CBB Base Die | Temperature inputs to PCode SA Thermal Puller for CCF/Ring EMTTM and cross-throttle (D2D/Inf) | PMSB IOs, `PCU_CR_DTS_TEMP_CCF[N:0]`, `PCU_CR_DTS_TEMP_SOC[2:0]_CR0/CR1` | [CBB Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) |
| Punit / GPSS | CBB Base Die | Applies PID frequency ceiling to CCF/Ring domain; controls fast_throttle for PROCHOT/PMAX; receives cross-die throttle HPM | `fast_throttle` out; GPSS ratio update; `IO_FASTPATH_THERMAL` | [CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) |
| FIVR (VccR / VccCore) | CBB | Voltage supplies for CCF/Ring and cores; SVID VR thermal alert polled by PrimeCode | `SVID_VR_STATUS[ThermAlert]` (~97% VR capacity) | — |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | CBB Top Die (per core) | Runs Core EMTTM PID ~300 μS/DCM; DTD interrupt handling; requests cross-throttle via PMSB when at LFM and still above TjMax−offset | `CROSS_CORE_THROTTLE_REQ` PMSB_PCU_CR_VIRTUAL_SIG[13]; `CORE_PMA_CR_CONFIG_10[ADVANCED_THERMAL_CTRL]` | Legacy Architecture Summary |
| PCode (CBB) | CBB Base Die | Runs CBB EMTTM PID ~1 mS; self-throttle (CCF/Ring) + cross-throttle (Ring→Core, Core→Core); VR HOT handler; sends HPM SOCKET_THERMAL; updates per-core THERM_STATUS via PMA_CR | `eff_tj_max` calc; `THERM_STATUS_UPDATE` PMA_CR; `SOCKET_THERMAL` HPM; `VrThermalAlert::vr_thermal_alert_tx()` | [CBB Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) |
| PrimeCode (IMH) | IMH die | Receives SOCKET_THERMAL HPM from each CBB; aggregates package thermal status; drives OS MSRs; distributes thermal interrupts to cores | HPM `SOCKET_THERMAL` recv; `IA32_PACKAGE_THERM_STATUS`; `DNS_EVENT_DELIVERY[THERMAL_INTERRUPT]` (RR=1) | [Socket Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) |
| BIOS / UEFI | Platform | Programs TCC offset (`IA32_TEMPERATURE_TARGET`); sets EMTTM master enable (`IA32_MISC_ENABLE[3]`); programs VR HOT disable policy | Boot-time MSR programming | HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_THERM_STATUS` | 0x19C (per-core) | RO/RWC | [0/1] THERMAL_MONITOR_STATUS/LOG; [23:16] TEMPERATURE; [14/15] CROSS_DOMAIN_LIMIT_STATUS/LOG | Intel SDM |
| MSR `IA32_THERM_INTERRUPT` | 0x19B (per-core) | RW | [0] HIGH_TEMP_INT_EN; [14:8] THRESHOLD1_REL_TEMP; [22:16] THRESHOLD2_REL_TEMP | Intel SDM |
| MSR `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | RO/RWC | [0/1] THERMAL_MONITOR_STATUS/LOG; [23:16] TEMPERATURE (package level) | Intel SDM |
| MSR `IA32_TEMPERATURE_TARGET` | 0x1A2 | RW | [29:24] TJ_MAX_TCC_OFFSET; [23:16] REF_TEMP; [7] TCC_OFFSET_CLAMPING_BIT (RATL enable) | Intel SDM |
| MSR `IA32_MISC_ENABLE` | 0x1A0 | RW (vMSR) | [3] AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE — master TCC enable | Intel SDM |
| MSR `MSR_POWER_CTL` | 0x1FC | RW | [24] VR_THERM_ALERT_DISABLE | Intel SDM |
| HPM `SOCKET_THERMAL` | CBB→Root | Internal | OOS, MIN/MAX_TEMP, MARGIN_TO_THROTTLE, MARGIN_TO_TCONTROL per CBB | CBB PM HAS |
| MSR `MCP_THERMAL_REPORT_1` | 0x1A3 | RO | [15:0] MARGIN_TO_THROTTLE; [31:16] MARGIN_TO_TCONTROL (package, from PrimeCode) | Intel SDM |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Core EMTTM PID period | ~300 | μS | Acode per-DCM; fast-path DTD ~nS (no PID) | Legacy Architecture Summary |
| CBB EMTTM slow loop | ~1 | mS | PCode PID for CCF/Ring | Legacy Architecture Summary |
| IMH Thermal PID period | ~1 | mS | PrimeCode; Mem Fabric + IO Fabric independent loops | Legacy Architecture Summary |
| VR Thermal Alert throttle level | P1 (guaranteed ratio) | — | PrimeCode polls SVID_VR_STATUS[ThermAlert] (~97% VR capacity) → HPM DNS_EVENT_DELIVERY[VR_THERM_ALERT] | Legacy Execution Flow |
| SHORT_TELEM push rate (Core DTS) | ~102.4 | μS | Per-DCM; Domain0 (Core) + Domain1 (MLCSSA) min/max temps | Legacy Execution Flow |
| EWMA filter coefficient (α) | 0.7 | — | Applied to temperature readings for THERMAL_MONITOR_STATUS reporting | Legacy Execution Flow |
| OOS hold-off before assertion | 20 | mS | OOS requires sustained max throttle + temp > eff_tj_max, or temp > eff_tj_max+10°C | Legacy Execution Flow |
| Squared-error acceleration threshold | −1 | °C | CBB PCode EMTTM: error ≤ −1°C → error ← −error² | Legacy Execution Flow |
| Core DTS decay rate (PkgC) | 40 | °C/mS | Core valid bits cleared in PkgC; PCode decays toward ambient | Legacy Execution Flow |
| SA Thermal Puller enable | PH2.2 | — | PMSB unblock; SOC/CCF DTS readable by PCode | Legacy Boot Sequence |
| CBB EMTTM slow loop start | PH2.52 | — | PCode kernel enabled | Legacy Boot Sequence |

## NWP Delta

**CBB thermal management is fully supported on NWP** — reused from DMR CBB.

- CBB EMTTM PID for CCF/Ring frequency limiting unchanged
- Cross-throttle (core↔ring, core↔core) unchanged
- Temperature target configuration unchanged
- VR HOT / PROCHOT / OOS detection flows unchanged
- 2 CBBs (vs 4) — fewer cross-die thermal interactions

### Validation Impact
- Same CBB thermal management tests apply
- Simplified cross-CBB thermal interaction matrix (2 vs 4 CBBs)

## Legacy (Human-Curated Reference)

### Architecture Summary

DMR thermal management is hierarchically controlled by three levels:

1. **Root (PrimeCode / IMH)** — Package-level domain control (mainly mesh/fabric). PID-based thermal control for IMH fabric (Mem Fabric + IO Fabric independent loops). Kp=0.17, Ki=0.06.
2. **CBB (PCode)** — Die-level EMTTM PID for CCF/Ring, cross-throttle coordination, temperature target management, thermal reporting aggregation.
3. **Core (Acode/ACP)** — Autonomous core EMTTM, ITD/TTD voltage compensation, "Do Not Exceed" hammer fast throttle.

#### Control Response Hierarchy
| Mechanism | Response Time | Rate | Scope |
|-----------|-------------|------|-------|
| THA/DTD (Do Not Exceed) | ~nS/µS | Fast wire | Core → LFM |
| Fast Throttle (Prochot/PMAX) | ~µS | HW wire | Die-wide frequency clamp |
| Core EMTTM (Acode PID) | ~300µS | Slow loop | Per-DCM |
| CBB EMTTM (PCode PID) | ~1mS | Slow loop | CCF/Ring per-CBB |
| IMH Thermal (Primecode PID) | ~1mS | Slow loop | Fabric (Mem/IO) per-IMH |
| RATL / EWMA | ~Seconds | Sustained | Package reporting |

#### CBB EMTTM PID

The CBB PCode EMTTM algorithm uses a PID control loop to manage CBB temperature by setting a frequency limit on the CCF/Ring domain.

- **Temperature target**: `eff_tj_max = eff_tj_max_sst - (eff_tj_max_c1e_offset + eff_tj_max_msr_offset)`
- **Squared error acceleration**: When `error ≤ -1°C`, `error = -error²` (increases response rate)
- **Self-throttle**: Hot domain gets its own frequency limited by PID output
- **Cross-throttle**: Triggered when a non-throttlable domain is hot, OR when a throttlable domain is at min ratio and still hot

#### Temperature Target Calculation

```
// Offset calc
eff_tj_max_c1e_offset       = c1e_disabled ? fuse.TJ_MAX_C1E_DISABLED_OFFSET : 0
eff_tj_max_msr_offset       = MSR.IA32_TEMPERATURE_TARGET[TJ_MAX_TCC_OFFSET]
eff_tj_max_overall_offset   = eff_tj_max_c1e_offset + eff_tj_max_msr_offset

// eff TjMax calc
eff_tj_max_sst = CR.SST_PP_CONTROL[FEATURE_STATE][0]
                 ? SST_BF_CONFIG_[sst_pp_level]_T_THROTTLE
                 : CR.SST_PP_[sst_pp_level]_T_THROTTLE
eff_tj_max     = eff_tj_max_sst - eff_tj_max_overall_offset
```

#### CBB EMTTM Domains

| Domain | Action | Voltage Rail | Temperature Source | Scope |
|--------|--------|-------------|-------------------|-------|
| CCF | Frequency limit | VccR | PCU_CR_DTS_TEMP_CCF[N:0] | Package |
| Big Core | Cross Domain Throttle | VccCore | PCU_CR_DTS_TEMP_IA_CCP[N:0] | DCM |
| Inf | Cross Domain Throttle | VccInf | PCU_CR_DTS_TEMP_SOC[2:0]_CR0/CR1 | Package |
| D2D | Cross Domain Throttle | VccC2IA | PCU_CR_DTS_TEMP_SOC[2:1]_CR[1:0] | Package |

### Execution Flow

#### CBB EMTTM Self-Throttle Flow
1. **BIOS config**: BIOS sets TCC_OFFSET via pkg MSR `IA32_TEMPERATURE_TARGET[TJ_MAX_TCC_OFFSET]` → PrimeCode sends to CBB via HPM `SOCKET_THERMAL`
2. **PCode resolves eff_tj_max**: Combines SST_PP level, C1E offset, TCC offset, OC offset
3. **DTS sampling**: Punit thermal puller collects SOC/CCF DTS temperatures → IO registers; Core CCP telemetry pushes every ~102.4µS
4. **PID evaluation (1ms slow loop)**: PCode computes `error = eff_tj_max - max_domain_temp`; applies squared error if error ≤ -1°C
5. **Frequency limit**: PID output → CCF/Ring frequency ceiling via slow limits → GPSS
6. **Reporting**: PCode updates `IA32_THERM_STATUS.THERMAL_MONITOR_STATUS` (filtered through EWMA) per CCP via `THERM_STATUS_UPDATE` PMA_CR

#### CBB EMTTM Cross-Throttle Flow
1. **Detection**: Cross-throttle condition triggers when:
   - `max(temperatures of non_throttle_domains) > temperature_target`, OR
   - `(any domain temp > target) AND (domain already at min_ratio)`
2. **Core→Ring cross-throttle**: When ring is at min and hot, PCode lowers all core ratios: `Core Ratio Floor = Ring EMTTM PID Limit + Core_Ring_Offset`
3. **Core→Core cross-throttle**: Hot CCP writes `PMSB_PCU_CR_VIRTUAL_SIG[CROSS_CORE_THROTTLE_REQ]` (bit 13) → PCode applies physically-aware demotion (neighbor CCPs get larger step-down)

#### Die Cross-Throttle (Not POR for DMR)
- IMH→CBB: HPM `DNS_EVENT_DELIVERY[cross_die_throttle]`
- CBB→IMH: HPM `UPS_EVENT_DELIVERY[cross_die_throttle]`
- When `cross_die_throttle=1`, each throttlable IP injects `TjMax-offset` as its temperature to PID

#### EMTTM Disable
```
if (fuse.THERMAL_THROTTLE_UNLOCK = 1 AND MSR.IA32_MISC_ENABLE[THERMAL_MONITOR_ENABLE] = 0)
    then (set Pcode EMTTM Disable = 1; set Acode EMTTM Enable = 0)
```
- Disable knobs: Core via `CORE_PMA_CR_CONFIG_10[ADVANCED_THERMAL_CTRL]=0`; PCode via `IO_PCODE_SYSTEM_MODES_CONTROL[EMTTM_DISABLE]`
- SW EMTTM disable only allowed for DMR Edge (Carmel Beach), not SP/AP

#### VR Hot (CBB Side)

**VR Thermal Alert (97% TEMP_MAX):**
- PrimeCode polls `SVID_VR_STATUS[ThermAlert]` → sends HPM `DNS_EVENT_DELIVERY[VR_THERM_ALERT]` to CBBs
- CBB PCode: `VrThermalAlert::vr_thermal_alert_tx()` sets CCP+Ring to P1 via `slow_limits.set_ccp_limit(VR_THERMAL_ALERT_CCP_ID, guaranteed)`
- PLR: Sets `HOT_VR_PLR` (bit 26 fine-grain), `PLATFORM_PLR` (coarse bit 4)
- Disabled by `MSR_POWER_CTL[VR_THERM_ALERT_DISABLE]`

**VR_HOT (100% / Prochot):**
1. VR asserts `VR_HOT#` → ORed to `xxPROCHOT_N`
2. IMH asserts `yyProchot` D2D wire to CBBs → HW fast_throttle (Core clock division + CCF serial debug mode)
3. PCode applies `PROCHOT_POWER_LIMITED_FREQ_LIMIT` HPM limits per CDYN index
4. PCode masks fast_throttle wire once Core WP is applied

#### Thermal Reporting (CBB Side)

**Telemetry to Root**: CBB sends periodic HPM `SOCKET_THERMAL` message containing:
- `OOS`: `(max_temp > eff_tj_max+10°C) OR ((any domain max throttled) AND (max_temp > eff_tj_max) for >20ms)`
- `MIN_TEMP`, `MAX_TEMP`: Absolute temperatures S9.6 format (+64°C offset)
- `MARGIN_TO_THROTTLE`: EWMA of relative temp to eff_tj_max (negative = margin exists)
- `MARGIN_TO_TCONTROL`: EWMA of relative temp to eff_tj_max minus T_CONTROL_OFFSET

**Per-core THERM_STATUS**: PCode updates via `THERM_STATUS_UPDATE` PMA_CR per CCP:
- `THERMAL_MONITOR_STATUS/LOG`, `PROCHOT_STATUS/LOG`, `OOS_STATUS/LOG` (OOS tied to 0 at CBB), `THRESHOLD1/2_STATUS/LOG`, `POWER_LIMITATION_STATUS/LOG`, `CURRENT_LIMIT_STATUS/LOG`, `CROSS_DOMAIN_LIMIT_STATUS/LOG`

**Interrupt flow**:
| Trigger | Direction | Log Behavior |
|---------|-----------|-------------|
| THERMAL_MONITOR | Bidirectional | Set on 0→1 only |
| THRESHOLD 1/2 | Bidirectional | Set on both 0↔1 |
| PROCHOT | Bidirectional | Set on 0→1 only |
| POWER_LIMIT | Bidirectional | Set on 0→1 only |
| OOS | Bidirectional | Set on 0→1 only |
| CURRENT_LIMIT | No interrupt | Set on 0→1 only |
| CROSS_DOMAIN_LIMIT | No interrupt | Set on 0→1 only |

**Package interrupt distribution**: PrimeCode sends HPM `DNS_EVENT_DELIVERY[THERMAL_INTERRUPT]` (RR=1) → PCode multicasts `IO_DIRECT_CORE_EVENT_THERMINT` to all CCPs → CBB replies DNS_EVENT_DELIVERY (RR=0) as ack

#### Thermal Sampling

**Push (Core)**: CCP PMA pushes SHORT_TELEM every ~102.4µS with Domain0 (Cores) Min/Max Temp + Domain1 (MLCSSA) Min/Max Temp

**Pull (SOC DTS / CCF)**: Punit thermal puller reads DTS temperatures into IO registers

**During PkgC**: Core telemetry freezes; PCode clears valid bits and decays temperature:
- Max: `Decay(last_valid_temp → (max_pkg_temp - cross_ip_hot_gradient), rate)`
- Min: `Decay(last_valid_temp → ambient_or_cold_alert_threshold, rate)`
- Rates: Core = 40°C/ms, non-Core = 5°C/ms

#### Boot Sequence (Thermal)
1. **PH0**: Inf pwrgood
2. **PH1.2**: SOC DTS fuse pulling + DTS enabled → thermtrip protection active
3. **PH2.2**: SA thermal puller enabled (PMSB unblock)
4. **PH2.40**: UCIe MB bringup → one-time ITD correction → UCIe ITD back to safe WP
5. **PH2.52**: PCode kernel enabled (slow loop) → EMTTM operational
6. **PH3+**: Core DTS enabled, CCP telemetry active → full thermal management

#### ACP (Core Autonomous Thermal)
- **Core EMTTM**: DCM-scope PID, ~300µS recalc. Monitors min/max temp of 2×IA Core + MLC + SSAMLC
- **Do Not Exceed / Hammer**: DTS DTD sticky alert → fast throttle to LFM via `IO_INTERRUPTS[25]`
- **ITD/TTD**: DTS DTD non-sticky alerts trigger Acode recalc of voltage compensation
- **Cross Core Throttle Indication**: Core writes `PMSB_PCU_CR_VIRTUAL_SIG[CROSS_CORE_THROTTLE_REQ]` when at LFM and still above `TjMax-Offset+ΔT(~3°C)` after hammer delay

### Key Registers & Interfaces

#### Core-Scope MSRs
| Register | Address | Scope | Key Fields |
|----------|---------|-------|------------|
| `IA32_THERM_STATUS` | 0x19C | Core | THERMAL_MONITOR_STATUS[0], LOG[1], PROCHOT_STATUS[2], LOG[3], OOS_STATUS[4], LOG[5], THRESHOLD1/2_STATUS[6,8], LOG[7,9], POWER_LIMIT_STATUS[10], LOG[11], CURRENT_LIMIT[12], LOG[13], CROSS_DOMAIN[14], LOG[15], TEMPERATURE[23:16], RESOLUTION[30:27], VALID[31] |
| `IA32_THERM_INTERRUPT` | 0x19B | Core | HIGH_TEMP_INT_EN[0], LOW_TEMP_INT_EN[1], PROCHOT_INT_EN[2], OOS_INT_EN[4], THRESHOLD1_REL_TEMP[14:8], THRESHOLD1_INT_EN[15], THRESHOLD2_REL_TEMP[22:16], THRESHOLD2_INT_EN[23] |

#### Package-Scope MSRs
| Register | Address | Key Fields |
|----------|---------|------------|
| `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | THERM_MON[0], PROCHOT[2], OOS[4], THRESHOLD1/2[6,8], POWER_LIMIT[10], PMAX[12], TEMPERATURE[23:16], VALID[31] |
| `IA32_TEMPERATURE_TARGET` | 0x1A2 | REF_TEMP, TJ_MAX_TCC_OFFSET, FAN_TEMP_TARGET_OFST |
| `POWER_CTL` | 0x1FC | ENABLE_BIDIR_PROCHOT[0], C1E_ENABLE[1], DIS_PROCHOT_OUT[21], PROCHOT_RESPONSE[22], PROCHOT_LOCK[23], VR_THERM_ALERT_DISABLE[24] |
| `IA32_MISC_ENABLE` | 0x1A0 | AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE[3] |
| `MCP_THERMAL_REPORT_1` | 0x1A3 | MARGIN_TO_THROTTLE[15:0], MARGIN_TO_TCONTROL[31:16] |
| `MCP_THERMAL_REPORT_2` | 0x1A5 | PACKAGE_ABSOLUTE_MAX_TEMPERATURE[15:0] |
| `CORE_PERF_LIMIT_REASONS` | Pkg | Prochot, Thermal, VR_THERM_ALERT (resolved from CBB PLR) |

#### Core PMA CRs
| Register | Description |
|----------|-------------|
| `EMTTM_ALGO_MISC` | CONTROL_TEMP[7:0] = TjMax - TCC_OFFSET (S8.0); SOC_TEMPERATURE_OVERSHOOT[11:8] |
| `IO_ACODE_ALGO_VALUES1` | MAX_ALLOWED_RATIO[9:0] — Core EMTTM PID output |
| `CORE_PMA_CR_CONFIG_10` | ADVANCED_THERMAL_CTRL[4] — enable/disable Core EMTTM+Hammer |
| `PMSB_PCU_CR_VIRTUAL_SIG` | CROSS_CORE_THROTTLE_REQUEST[13] — Core requesting SOC cross-throttle help |

#### Punit CRs / IO Registers
| Register | Description |
|----------|-------------|
| `SVID_VR_STATUS0` | vr_hot_lsb, vr_settled_lsb — MBVR status polled by PrimeCode |
| `THROTTLE_INDICATIONS` | throttle_0 (live prochot wire), throttle_0_semaphore |
| `PCODE_PMU_COMM1` | pcu_freq_max_limit_vr_hot_cycles_lsb |
| `PP0_TEMPERATURE_0_0_0_MCHBAR_PCU` | TEMPERATURE[7:0] — EWMA max CCP temp (MCHBAR 0x597C) |

#### HPM Messages (Thermal)
| Message | Direction | Purpose |
|---------|-----------|---------|
| `SOCKET_THERMAL` | CBB→Root | OOS, MIN/MAX_TEMP, MARGIN_TO_THROTTLE/TCONTROL, DECAY/TIME_WINDOW, THERMAL_MONITOR_ENABLE |
| `DNS_EVENT_DELIVERY[VR_THERM_ALERT]` | Root→CBB | VR hot 97% — CBB throttles to P1 |
| `DNS_EVENT_DELIVERY[THERMAL_INTERRUPT]` | Root→CBB | Package thermal interrupt distribution (RR=1, ack RR=0) |
| `DNS_EVENT_DELIVERY[cross_die_throttle]` | Root→CBB | Die cross-throttle (not POR DMR) |
| `UPS_EVENT_DELIVERY[cross_die_throttle]` | CBB→Root | Die cross-throttle reverse (not POR DMR) |
| `PROCHOT_POWER_LIMITED_FREQ_LIMIT` | Root→CBB | Per-CDYN-index IA ratio limits + CBB_FABRIC_LIMIT |
| `B2P_EXCHANGE[OC_TJ_MAX_OFFSET]` | Root→CBB | OC TjMax value (not offset despite name) |
| `LEAF_PERF_STATUS` | CBB→Root | CBB PLR aggregation |

#### Key Fuses
| Fuse | Width | Description |
|------|-------|-------------|
| `HIGHEST_TJ_MAX` | 8 | Max allowed TjMax (worst-case before SST resolution) |
| `TJ_MAX_C1E_DISABLED_OFFSET` | 5 | Extra TjMax offset when C1E disabled |
| `SST_PP_[i]_T_THROTTLE` | 8 | Per SST-PP level temperature target |
| `SST_BF_CONFIG_[i]_T_THROTTLE` | 8 | Per SST-BF config temperature target |
| `THERMAL_THROTTLE_UNLOCK` | 1 | Allow SW to disable EMTTM |
| `OC_ENABLED` | 1 | Overclocking enable |
| `IA_MIN_RATIO` | 7 | Minimum operating ratio |
| `DTS.dtd_nsalert_thr_[0]` | — | Core "Do Not Exceed" threshold |
| `SST_BF_CONFIG_[i]_T_CONTROL_OFFSET` | 5 | Fan T-Control offset per SST-BF level |

#### PCode Slow Limits Interface (VR Thermal Alert)
| Enum | Value | Description |
|------|-------|-------------|
| `VR_THERMAL_ALERT_CCP_ID` | 1 | CCP slow limit type for VR hot |
| `VR_THERMAL_ALERT_RING_ID` | 1 | Ring slow limit type for VR hot |
| `CCP_SLR_VR_THERMAL_ALERT_ID` | 13 | CCP slow limit reason bit |
| `PEM_HOT_VR` | 26 | PEM telemetry limit reason bit |
| `HOT_VR_PLR` | 27 | Fine-grain PLR bit |
| `PLATFORM_PLR` | 4 | Coarse-grain PLR bit (Prochot + VR Therm Alert) |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [CBB Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) | Primary CBB thermal spec |
| HAS | [CBB Thermtrip HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermtrip/Thermtrip.html) | Thermtrip daisy chain |
| HAS | [CBB Thermal Integration HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/DMR%20CBB%20Thermal%20Integration%20HAS/DMR%20CBB%20Thermal%20Integration%20HAS.html) | DTS/diode topology, fuse config |
| HAS | [CBB ITD HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/ITD/ITD.html) | CBB ITD voltage compensation |
| HAS | [DMR SOC Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | IMH-level thermal (Prochot, VR Hot, DTS, ITD, EMTTM, reporting) |
| HAS | [Socket Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Package-level thermal management |
| HAS | [CBB HPM HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/HPM/hpm.html) | HPM message definitions |
| HAS | [CBB TPMI HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html) | CBB TPMI registers |
| HAS | [CBB P-State Stack / Slow Limits](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html) | Slow limits, PLR, prochot |
| FAS | [PCode Thermal FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/Thermals/Thermal%20Management_FAS.html) | PCode thermal implementation |
| MAS | [CBB Thermal MAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/MAS/Thermal/CBB_thermal_mas.html) | IO register list, thermal puller |
| HAS | [PLR HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html) | Perf limit reasons spec |
| HAS | [ACP Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html#acp-20-autonomous-thermal-management) | Core autonomous thermal |
| Primecode src | `src/flow/hot_vr/v2_0/hot_vr.cpp` | VR Hot flow (HPM DNS/UPS VR_THERM_ALERT) |
| Primecode src | `src/flow/prochot/prochot_common/v1_0/prochot.cpp` | Prochot fastpath handler, assertion/deassertion |
| Primecode src | `src/flow/prochot/prochot_tpmi/v2_0/prochot_tpmi.hpp` | Prochot TPMI, PF curve, HPM to leaves |
| PCode src | `source/pcode/flows/slow_limits/vr_thermal_alert/vr_thermal_alert.cpp` | VR thermal alert slow limit (P1 clamp) |
| PCode src | `source/pcode/flows/slow_limits/fast_limits.h` | Fast limits (prochot, pmax, simpl) |
| PCode src | `source/pcode/flows/thermals/thermal_report.h` | Thermal reporting, THERM_STATUS update |
| PCode src | `source/pcode/flows/slow_limits/plr/plr.cpp` | PLR resolution (fine/coarse grain) |
| PCode src | `source/pcode/flows/slow_limits/pem_telemetry.h` | PEM limit reason mapping |
| PCode src | `source/pcode/hpm/hpm_manager.h` | HPM message dispatch (prochot, thermal, VR hot) |
| Test scripts | `pm/pss/vrhot/vr_hot.py` | DMR VR Hot PSS test |
| Test scripts | `pm/pss/prochot/pm_mcp_prochot.py` | DMR Prochot PSS test |

### Related Sightings

### NWP Delta

#### Topology Changes
- **NWP has 2 CBBs (vs DMR 4)**: HPM fan-out for `DNS_EVENT_DELIVERY[VR_THERM_ALERT]`, `PROCHOT_POWER_LIMITED_FREQ_LIMIT`, and `SOCKET_THERMAL` telemetry covers fewer leaves. Cross-throttle CCP physical neighbor matrix is smaller.
- **Single NIO replaces dual IMH**: No IMH-to-IMH `UPS_VR_THERM_ALERT` path. Only NIO→CBB DNS path remains. `xxPROCHOT_N` GPIO received on NIO only.
- **D2D fast_throttle wire**: NIO→CBB only (32 GT/s UCIe, 2× DMR bandwidth) — tighter timing margins for prochot/VR_HOT propagation latency.

#### Feature Carry-Over (Not ZBB'd)
- **CBB EMTTM**: Full PID self-throttle + cross-throttle — 100% PCode reuse
- **VR Hot / VR Thermal Alert**: Carries over from DMR (confirmed not in NWP ZBB list)
- **Prochot**: Carries over, PF curve fuses may differ on NIO
- **Thermal Reporting** (`SOCKET_THERMAL`, `THERM_STATUS_UPDATE`): 100% PCode reuse
- **ACP / Core EMTTM**: PNC core reuse — autonomous thermal unchanged

#### Potential NWP-Specific Risks
- NWP adds `VCCC2C` FIVR rail on NIO — new VR instance that `readSvidHotVrStatus()` VR loop must correctly handle (checkIfDramVR/checkIfPsys filtering)
- NWP LPDDR6 replaces DDR5 — DRAM VR IDs differ; VR Hot polling loop must correctly skip LPDDR6 VRs
- No accelerator dies (DSA/IAA/QAT/DLB removed) — `PROCHOT_CFC_FABRIC_COUNT` and CFC actions scope reduced
- Die cross-throttle (`DNS_EVENT_DELIVERY[cross_die_throttle]`) was not POR on DMR — status on NWP TBD
