# SoC Thermal — Main Flow

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: SoC Thermal is a 15-subflow feature providing three protection tiers — **EMTTM PID throttling** (continuous, 3 layers: Core 300μS / CBB 1mS / IMH 1mS), **PROCHOT** (platform-level power-to-freq profile), and **THERMTRIP** (last-resort async HW shutdown, ~30-100nS) — plus DTS telemetry, ITD voltage compensation, TPMI/PMT observability, and LVT thermal interrupts across Core, Ring, Fabric, Memory, and IO domains.

**Topology**:
```
DTS Sensors (Core Gen2.6 per CCP; SOC/CCF Gen1; IMH 19/die)
    │ SHORT_TELEM (~102.4μS core, ~1mS SOC/IMH)
    ├── Acode EMTTM PID (Core ~300μS) ──────────> Core freq ceiling
    ├── PCode EMTTM PID (CBB ~1mS) ─────────────> CCF/Ring freq ceiling
    │     SOCKET_THERMAL HPM ──────────────────→
    └── PrimeCode EMTTM PID (IMH ~1mS) ─────────> Mem/IO fabric ceiling
          └── IA32_PACKAGE_THERM_STATUS, TPMI OPC_*, PMT, LVT interrupts
GPIO: PROCHOT_N (input)→ IMH → HPM DNS_EVENT_DELIVERY → all dies (P-F profile)
GPIO: THERMTRIP_N (output) ← DTS daisy chain → async PLL/FIVR/BGR (~30-100nS)
SVID: IMH polls MBVR ThermAlert → HPM VR_THERM_ALERT → P1 clamp all dies
```

**Key operational principle**: All 3 EMTTM PID layers fire independently — Core ACode, CBB PCode, and IMH PrimeCode. Zero PCS services (all replaced by TPMI/PMT). OOB log bits (`OPC_PKG_THERM_STATUS`) independent from MSR 0x1B1 — BMC and OS manage their own sticky bits separately. ITD uses standardized 2-slope fuse algorithm across all FIVR/MBVR domains.

**Boot activation**: DTS active after MBIST. ITD fuses read at PH2.x. EMTTM PID active at PH2.52. TPMI/PMT initialized at PH2.52; BIOS locks before OS boot. THERMTRIP async hardware path active from power-on.

SoC Thermal is the full-stack thermal protection and monitoring feature spanning all die types in a multi-die SoC. It provides three layers of protection — continuous PID-based throttling (EMTTM), platform-level power capping (PROCHOT), and last-resort hardware shutdown (THERMTRIP) — plus telemetry, reporting, and voltage compensation (ITD) across Core, Ring, Fabric, Memory, and IO domains.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core DTS Gen2.6 | CBB top tile | Temperature source for all core EMTTM; 15+1 diodes per DTS, 2 per CCP → 64 per CBB | SHORT_TELEM (~102.4μS) | CBB Thermal HAS |
| IMH DTS Gen1 | IMH die | 19 sensors per IMH (MEM_W/E, D2D, MIO, Accel, Fabric, CGU); drives IMH EMTTM PID + ITD | SA Thermal Puller (~1mS); RC offsets | DMR SoC Thermal HAS |
| HPM bus (SOCKET_THERMAL) | IMH↔CBBs | Carries per-CBB min/max temps, margins, OOS status to Root IMH; carries `DNS_EVENT_DELIVERY` events back | HPM messages | HPM Message Specification |
| OOBMSM / TPMI SRAM | Per IMH | TPMI control/status registers (OPC_PKG_CTLS, OOB_DIE_CTLS, PLR, MISC_CTRL); PMT telemetry aggregator | VSEC, PFS, GPSB | TPMI HAS |
| GPIO (PROCHOT_N / THERMTRIP_N) | NIO/IMH0 | PROCHOT_N input from platform; THERMTRIP_N output to platform; MEMHOT/MEMTRIP secondary signals | Package bumps; D2D wires `prochot_n`, `yy_thermtrip_n` | DMR D2D Perimeter HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP (PantherCove) | Core EMTTM PID (~300μS) + Hammer fast-throttle; per-core ITD (VCCORE, VCCMLC_SSA); SHORT_TELEM push | `EMTTM_ALGO_MISC`; `CORE_PMA_CR_CONFIG_10` | ACP PM HAS |
| PCode (CBB) | CBB Base Die | CBB EMTTM PID for CCF/Ring (~1mS); base DTS sampling + EWMA; CBB ITD (VCCR, VCCC2IA, UCIe); VR Hot P1 clamp (`VrThermalAlert::vr_thermal_alert_tx()`); OOS/MCA; PLR; SOCKET_THERMAL HPM send | `IO_THERM_INTERRUPT`; `THERM_STATUS_UPDATE` PMA CR; `CORE_PERF_LIMIT_REASONS` | CBB Thermal Mgmt HAS |
| PrimeCode (IMH) | IMH die (Root + Leaf) | IMH EMTTM PID for Memory+IO fabrics; IMH DTS + ITD (VCCINF, CFCMEM, CFCIO); HPM SOCKET_THERMAL fan-in; PROCHOT power→freq 6-point profile; VR SVID bus master; pkg thermal status/interrupts/TPMI/PMT | `IA32_PACKAGE_THERM_STATUS`; `OPC_PKG_THERM_STATUS`; HPM `DNS_EVENT_DELIVERY` | DMR SoC Thermal HAS; Primecode spec |
| BIOS / UEFI | Platform | Programs `IA32_MISC_ENABLE[3]` (TCC enable); `POWER_CTL`; locks TPMI features (`TPMI_SET_STATE(LOCK=1)`) before OS boot; configures thresholds/timeouts | Boot-time MSR programming | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | RO/RWC | Package thermal status/log; TEMPERATURE[23:16]; OOS_STATUS[4]; PROCHOT_STATUS[2]; HW_FEEDBACK_NOTIFICATION_LOG[26] | Intel SDM |
| MSR `IA32_THERM_STATUS` | 0x19C | RO/RWC | Per-core temperature (relative to eff_tj_max); THERMAL_MONITOR_STATUS, threshold1/2, power limit | Intel SDM |
| MSR `IA32_TEMPERATURE_TARGET` | 0x1A2 | RW | REF_TEMP[23:16], FAN_TEMP_TARGET_OFST[15:8], TCC_OFFSET | Intel SDM |
| TPMI `OPC_PKG_THERM_STATUS` | TPMI_ID 0x0F idx 2 | RO (BMC) | BMC-exclusive thermal status with independent OOB log bits; EWMA filter via `OPC_THERMAL_MONITOR` | TPMI HAS |
| PMT telemetry entries | PMT watcher API | RO stream | PACKAGE_TEMPERATURE (+64°C), MARGIN_TO_TCONTROL (S8.8), THERMAL_CONSTRAINED_TIME | Primecode PMT Spec |
| PLR MSRs | 0x64F / TPMI PLR | RO/RWC | `THERMAL`[4], `HOT_VR`[26], `PROCHOT`[?] bits; per-core + package scope | PLR HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Core EMTTM PID loop (Acode) | ~300 | μS | Per-core PID; fastest thermal response tier | Legacy FW Agents table |
| CBB EMTTM PID loop (PCode) | ~1 | mS | CCF/Ring frequency ceiling per slow-loop | Legacy FW Agents table |
| IMH EMTTM PID loop (PrimeCode) | ~1 | mS | Memory+IO fabric frequency ceiling per slow-loop | Legacy FW Agents table |
| THERMTRIP assertion latency | 30–100 | nS | Async combinational path; DTS daisy chain → PLL/FIVR/BGR (no FW in path) | Legacy Thermtrip Architecture block |
| PROCHOT fast_throttle latency | ~20 | nS | VR_HOT# / PROCHOT_N pin → CBB Punit fast_throttle HW | Legacy Prochot / VR flows |
| SOCKET_THERMAL HPM period | ~1 | mS | Leaf CBB → Root IMH thermal telemetry update rate | Legacy Signal & Data Flow |
| EWMA filter coefficient (α) | 0.7 | — | Applied to per-CCP temperature for THERMAL_MONITOR_STATUS evaluation | Legacy Key Design Principles |
| OOS threshold (temp path) | +10 | °C above eff_tj_max | PKG_MAX_TEMP ≥ eff_tj_max + 10°C → OOS immediately | Legacy Architecture Summary |
| OOS threshold (timer path) | 20 | slow loops | Sustained max throttle for ≥ 20 consecutive loops → OOS | Legacy Architecture Summary |
| Total subflows | 15 | — | See Subflows table below | Legacy |
| Total test cases | 89 | — | FV=73, PSS=16 | Legacy Subflows table |

## NWP Delta

**SoC Thermal subsystem is fully supported on NWP** — all sub-features preserved with topology simplifications.

### Summary Table

| Feature | NWP Status | Key Delta |
|---------|-----------|-----------|
| ACP | Supported | No change; CBB runs ACP |
| CBB DTS/Telemetry | Supported | Single diode, DTS IP update |
| CBB EMTTM | Supported | No change |
| EMTTM PID | Supported | No change |
| GPIO Thermal Pins | Modified | PROCHOT input-only, THERMTRIP daisy-chain, MEMHOT TBD |
| IMH DTS Telemetry | Supported | Single NIO die, DTS update |
| IMH EMTTM | Supported | Single NIO, LPDDR6 |
| ITD | Supported | No change |
| MCA Thermal | Limited | eMCA gen2/de-escalation not present |
| TCC | Supported | No change, no SST-BF cross-product |
| Thermal Interrupts | Supported | No change |
| Thermal Reporting | Supported | No change |
| Thermtrip/Cattrip | Modified | Daisy-chain, single NIO die |
| TPMI PMT | Supported | No change |
| VR Thermal | Modified | PMIC sensor, VR_HOT not visible to platform |

### Architecture-Level Deltas
- **Single NIO die** (derivative of IMH2) replaces dual IMH → simplified thermal aggregation
- **2 CBBs** (vs 4) → fewer thermal management instances
- **LPDDR6** memory stack → different thermal characteristics vs DDR5
- **No SST-PP/BF/CP** → removes SST cross-products from thermal flows
- **No PkgC6** → removes PkgC thermal interaction tests

## Legacy (Human-Curated Reference)

### NWP Spec Context
| Field | Value |
|-------|-------|
| HAS ref | NWP HAS: Thermal Protection (ProcHot, Thermtrip, Memtrip), ITD on VCCFCFCAB, EMTTM/Thermal PID |
| MAS ref | NWP PM MAS: ProcHot/Thermtrip/Memtrip/ITD/EMTTM/VR Hot all supported |
| NWP delta | NWP keeps ProcHot/Thermtrip/Memtrip/ITD/EMTTM/VR Hot. Thermal HW Assist never enabled on DMR CBB. |
| NWP supported | True |

### Architecture Summary

SoC Thermal is the full-stack thermal protection and monitoring feature spanning all die types in a multi-die SoC. It provides three layers of protection — continuous PID-based throttling (EMTTM), platform-level power capping (PROCHOT), and last-resort hardware shutdown (THERMTRIP) — plus telemetry, reporting, and voltage compensation (ITD) across Core, Ring, Fabric, Memory, and IO domains.

#### Three-Tier Thermal Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PACKAGE / PLATFORM LEVEL                           │
│  GPIO Pins: PROCHOT_N (input), THERMTRIP_N (output), MEMHOT, MEMTRIP      │
│  VR Hot: SVID polling → P1 throttle → PROCHOT escalation                  │
│  TPMI/PMT: OPC_PKG_THERM_STATUS, PMT telemetry (temp/margin/target)       │
│  Reporting: MSR 0x1B1, 0x1A1, 0x1A2, 0x19C; LVT Thermal Interrupts       │
├─────────────────────────────────────────────────────────────────────────────┤
│                       IMH (Hub Die) — PrimeCode                            │
│  DTS: 19 sensors/die (MEM, D2D, MIO, Accel, Fabric, CGU)                  │
│  EMTTM PID: Memory + IO Fabric frequency ceiling                          │
│  Aggregation: HPM SOCKET_THERMAL fan-in from all leaves                    │
│  ITD: VCCINF, CFCMEM, CFCIO rail compensation                             │
│  PROCHOT: Power→frequency 6-point profile, HPM distribution               │
│  VR Hot: SVID bus master, MBVR status polling                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                     CBB (Compute Die) — PCode + ACode                      │
│  DTS: Base (AON, DTS1/2, CCF×16) + Top (Gen2.6, 64/die)                   │
│  EMTTM PID: Core + CCF/Ring frequency ceiling (~1mS PCode)                │
│  ACode EMTTM: Per-core PID + Hammer fast-throttle (~300μS)                 │
│  ITD: Core (VCCORE), Ring (VCCR), CCF (VCCC2IA), UCIe — 2-slope fuse alg  │
│  Thermtrip: DTS daisy chain → PLL/FIVR/BGR shutdown (~30-100nS async)     │
│  MCA: UCNA DIE_TOO_HOT when OOS (eff_tj_max + 10°C for 3mS)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Signal & Data Flow

```
                        DTS Sensors (Gen1/Gen2.6)
                               │
                    SHORT_TELEM (64-bit per CCP)
                               │
                         ┌─────▼─────┐
                         │  EWMA     │  α=0.7, configurable
                         │  Filter   │
                         └─────┬─────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ EMTTM PID    │  │ ITD 2-slope  │  │  Thermtrip   │
    │ (Throttle)   │  │ (V offset)   │  │  (Shutdown)  │
    │ Core→CBB→IMH │  │ Per-rail     │  │  Async HW    │
    └──────┬───────┘  └──────────────┘  └──────────────┘
           │
    ┌──────▼───────┐
    │ HPM Messages │  SOCKET_THERMAL, DNS_EVENT_DELIVERY
    │ Leaf → Root  │
    └──────┬───────┘
           │
    ┌──────▼───────────────────────────────────────┐
    │            Root Aggregation (IMH0)           │
    │  PKG_MAX_TEMP = max(all die max temps)       │
    │  THERMAL_MONITOR_STATUS (EWMA gated)         │
    │  OOS detection (tj_max + 10°C for 3mS)      │
    │  PROCHOT power→freq conversion               │
    └──────┬───────────────────────────────────────┘
           │
    ┌──────▼──────────────┐
    │   OS/BMC Reporting  │
    │  MSRs (0x1B1, 0x1A1,│
    │   0x1A2, 0x19C)     │
    │  TPMI OPC_*         │
    │  PMT telemetry      │
    │  LVT interrupts     │
    │  PLR registers      │
    └─────────────────────┘
```

#### Key Design Principles (DMR Baseline)

| Principle | Detail |
|-----------|--------|
| PID replaces N-Strike | All 3 EMTTM layers (Core ACode, CBB PCode, IMH PrimeCode) use PID — no bang-bang |
| PCS fully removed | 0 PCS services on DMR; all thermal observability via TPMI + PMT |
| PROCHOT input-only | Output removed since SPR; platform uses VR_HOT for external throttle signals |
| THERMTRIP output-only | At package level; bidirectional inter-die only |
| OOB independent logs | `OPC_PKG_THERM_STATUS` log bits independent from MSR 0x1B1 — BMC and OS each manage their own sticky bits |
| ITD standardized | 2-slope fuse algorithm across all FIVR domains — slopes × 2, cutoff, crossover, thresholds |
| HW Assist not enabled | Thermal HW Assist never enabled on DMR CBB (NWP same) |

### FW Agents

| Agent | Scope | Thermal Role |
|-------|-------|--------------|
| **ACode** | Core CCP (PantherCove) | Core EMTTM PID + Hammer fast-throttle (~300μS), per-core ITD (VCCORE, VCCMLC_SSA), cross-core throttle coordination |
| **PCode** | CBB die | CBB EMTTM PID for CCF/Ring (~1mS), base DTS sampling + EWMA, CBB ITD (VCCR, VCCC2IA, UCIe), VR Hot actions, OOS/MCA generation, PLR updates, CCP thermal status propagation |
| **PrimeCode** | IMH die (Root/Leaf) | IMH EMTTM PID for Memory+IO fabrics, IMH DTS + ITD (VCCINF, CFCMEM, CFCIO), HPM thermal aggregation, PROCHOT power→freq, VR SVID bus master, package thermal status/interrupts, TPMI/PMT updates, GPIO management |

#### Interfaces

| Interface | Direction | Purpose |
|-----------|-----------|---------|
| **HPM** | Leaf↔Root | `SOCKET_THERMAL` (temps, margins, OOS), `DNS_EVENT_DELIVERY` (thermal interrupts, VR alerts), `PROCHOT_POWER_LIMITED_FREQ_LIMIT` |
| **MSR** | FW→OS | `IA32_PACKAGE_THERM_STATUS` (0x1B1), `IA32_THERM_STATUS` (0x19C), `IA32_TEMPERATURE_TARGET` (0x1A2), `IA32_PACKAGE_THERM_MARGIN` (0x1A1), `IA32_PACKAGE_THERM_INTERRUPT` (0x1B2) |
| **TPMI** | FW→OOB/OS | `OPC_PKG_THERM_STATUS`, `OPC_THERMAL_MONITOR`, `PROCHOT_RESPONSE_POWER` (MISC_CTRL), PLR |
| **PMT** | FW→OOB | Package temp, margin to Tcontrol, temp target, thermal constrained time |
| **SVID** | PrimeCode→VR | VR thermal alert polling (STATUS1.ThermAlert), temperature zone read |
| **D2D wires** | Die↔Die | `prochot_n`, `fast_throttle`, `yy_thermtrip_n` (bidir) |
| **GPIO** | SoC↔Platform | `xxPROCHOT_N` (input), `xxTHERMTRIP_N` (output), `xxMEMHOT_IN/OUT`, `xxMEMTRIP` |
| **GPSB** | PCode→Core | `U2C_DIRECT_EVENTS` / `U2C_BROADCAST_EVENTS` for interrupt injection |

#### HW Blocks

| Block | Location | Sensors/Resources |
|-------|----------|-------------------|
| Core DTS Gen2.6 | CBB top tile | 15+1 diodes per DTS, 2 per CCP → 64 per CBB die |
| Base DTS Gen1 | CBB base die | AON (continuous), DTS1/2 (SOC), CCF × 16 |
| IMH DTS | IMH die | 19 per die (MEM_W/E, D2D, MIO, Accel, Fabric, CGU) |
| FIVR | CBB + IMH | 42 per DMR CBB (Core×32 + Ring×8 + fixed); IMH: VCCINF, CFCMEM, CFCIO |
| MBVR | Package | VCCIN_EHV stack; polled via SVID for ThermAlert |
| DTS Daisy Chain | CBB | Core tiles + CBO virtual tiles → Punit thermtrip |
| Thermtrip Surv Block | CBB + IMH | Async PLL/FIVR/BGR shutdown on daisy chain trip |
| GPIO | NIO/IMH0 | 5 package thermal bumps |
| OOBMSM | Per IMH | TPMI VSEC BAR, PMT watcher, LTM security |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR SoC Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | Master thermal HAS: EMTTM, Prochot, VR Hot, DTS, ITD, Thermal Reporting, OOS |
| HAS | [DMR CBB ITD HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/ITD/ITD.html#itd-ttd-domains) | CBB ITD/TTD domains, 2-slope fuse algorithm |
| HAS | [CBB Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) | CBB EMTTM PID, cross-throttle, VR Hot actions |
| HAS | [CBB Thermtrip HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermtrip/Thermtrip.html) | DTS daisy chains, async shutdown, FIVR IFDIM |
| HAS | [Socket Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Wave3 common thermal architecture |
| HAS | [ITD HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/ITD/ITD_HAS.html) | ITD common architecture, N-slope algorithm |
| HAS | [ACP PM HAS — Thermal](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html) | Core ACode thermal PID, Hammer, ITD/TTD |
| HAS | [TPMI HAS (Arch Common)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) | TPMI VSEC/PFS/LUT, OPC/ODC registers, PCS transition |
| HAS | [PROCHOT HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/PROCHOT/prochot_top.html) | GNR/DMR PROCHOT architecture |
| HAS | [PM Interrupt Arch HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/pm_interrupt_arch/pm_interrupt_arch.html) | LVT thermal interrupt delivery, multi-die HPM |
| HAS | [Perf Limit Reasons HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html) | PLR MSR + TPMI bits for thermal/prochot/VR hot |
| HAS | [DMR Telemetry HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Telemetry.html) | Telemetry aggregation, PMT entries |
| HAS | [HPM Message Specification](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html) | SOCKET_THERMAL, DNS_EVENT_DELIVERY, PROCHOT_FREQ_LIMIT |
| HAS | [Primecode Firmware Specification](https://docs.intel.com/documents/primecode/has/DMR/index.html) | IMH FW flows |
| HAS | [DMR D2D PM Perimeter HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/D2D/DMR_D2D_Perimeter.html) | GPIO pins, D2D thermal wires, fast_throttle |
| HAS | [DMR Punit Register HPM Scoping](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Punit_registers.html) | MSR scope categorization (pkg-scope, die-scope) |
| HAS | [OOBMSM FW Gen4 FAS](https://docs.intel.com/documents/arch_datacenter/OOBMSM/Gen4/OOBMSM_FW_Gen4_FAS.html#tpmi-support) | TPMI support, LTM rules, Ocode |
| HAS | [Primecode PMT Spec](https://docs.intel.com/documents/primecode/has/common/PMT/Primecode_PMT_Specification.html) | PMT telemetry definitions |
| HAS | [CBB TPMI HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html) | CBB die-scoped TPMI features |
| HAS | [CBB Pcode Telemetry HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html) | CBB PMT entries |
| HAS (NWP) | [NWP Telemetry & Manageability HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Manageability%20and%20Telemetry/Telemetry_and_Manageability_HAS.html) | NWP telemetry |
| HAS (NWP) | [NWP IMH Punit Telemetry](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Manageability%20and%20Telemetry/Telemetry_and_Manageability_HAS.html#imh-punit-telemetry) | NWP IMH thermal telemetry |
| HAS (NWP) | [NWP CBB Telemetry Aggregator HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/NWP_CBB_Telemetry/TelemetryAggregator_CBB_NWP.html) | NWP CBB telemetry |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS — thermal flows |

### NWP Delta Summary

> Consolidated from all 15 subflow NWP Delta sections. Each item links to the originating subflow.

#### Topology Changes (Impact: High)

| Change | DMR Baseline | NWP | Affected Subflows |
|--------|--------------|-----|-------------------|
| Hub die | Dual IMH (IMH0 root, IMH1 leaf) | Single NIO | [GPIO](gpio.md), [Prochot](prochot.md), [Thermtrip](thermtrip.md), [VR](vr.md), [TPMI/PMT](tpmi_pmt.md) |
| CBB count | 4 (cbb0–3) | 2 | [CBB Thermal Mgmt](cbb_thermal_management.md), [Thermal Interrupts](thermal_interrupts.md), [Thermtrip](thermtrip.md) |
| Core count per CBB | 32 CCPs | 24 CCPs | [Thermtrip](thermtrip.md), [VR](vr.md), [CBB DTS](cbb_dts_telemetry.md) |
| FIVR count per CBB | 42 (Core×32 + Ring×8 + fixed) | 34 (Core×24 + Ring×8 + fixed) | [Thermtrip](thermtrip.md) |
| OOBMSM instances | 2 (one per IMH) | 1 (on NIO) | [TPMI/PMT](tpmi_pmt.md) |
| UCIe D2D speed | 16 GT/s | 32 GT/s (2×) | [Prochot](prochot.md), [CBB Thermal Mgmt](cbb_thermal_management.md) |
| Memory type | DDR5 | LPDDR6 | [GPIO](gpio.md), [VR](vr.md), [TPMI/PMT](tpmi_pmt.md) |
| Accelerator dies | DSA/IAA/QAT/DLB | None | [Prochot](prochot.md), [VR](vr.md) |

#### Feature Carry-Forward (Impact: Low — validate only)

- **EMTTM**: All 3 PID layers (Core ACode, CBB PCode, IMH PrimeCode) 100% reuse. PID params (Kp=0.17, Ki=0.06) — confirm if tuned. ([EMTTM](emttm.md), [CBB Thermal Mgmt](cbb_thermal_management.md), [IMH Thermal Mgmt](imh_thermal_management.md))
- **Thermal Reporting**: Same register structure (MSR 0x1B1/0x1A1/0x1A2/0x19C). EWMA α=0.7 and OOS threshold (eff_tj_max + 10°C, 3mS timer) unchanged. ([Thermal Reporting](thermal_reporting.md))
- **ITD**: 2-slope fuse algorithm unchanged; all domain ITD (Core, Ring, CCF, VCCINF, CFCMEM, CFCIO, UCIe) carried forward. ([ITD](itd.md))
- **PROCHOT**: Input-only, P-F 6-point profile, PBM budget scaling unchanged. ([Prochot](prochot.md))
- **VR Hot**: SVID polling → P1 throttle → PROCHOT escalation. PLR bits (HOT_VR=26, PLATFORM=4) same. ([VR](vr.md))
- **Thermtrip**: HW async shutdown, daisy chain, inter-die `yy_thermtrip_n` unchanged. ([Thermtrip](thermtrip.md))
- **Thermal Interrupts**: LVT delivery, HPM DNS_EVENT_DELIVERY, C6 pend behavior same. ([Thermal Interrupts](thermal_interrupts.md))
- **MCAs**: UCNA DIE_TOO_HOT unchanged. ([MCAs](mcas.md))

#### NWP-Specific Items (Impact: High — new validation needed)

| Item | Subflow | Notes |
|------|---------|-------|
| **VCCFCFCAB** — new NWP FIVR rail | [ITD](itd.md) | New test case 22022458470. DTS sources, fuse set unknown — NWP HAS needed |
| **NIO GPIO ownership** | [GPIO](gpio.md) | Single NIO owns all 5 package bumps — fuse config validation from scratch |
| **TPMI PFS/LUT** | [TPMI/PMT](tpmi_pmt.md) | NWP-specific PFS table (2 CBBs + NIO topology). OOBMSM BDF on NIO |
| **LPDDR6 MEMHOT/MEMTRIP** | [GPIO](gpio.md) | Different integration than DDR5; verify TSOD/MC signaling |
| **LPDDR6 DIMM temps** | [TPMI/PMT](tpmi_pmt.md) | OPC_DIMM_TEMPS channel count and OPC_HEADER.MEMORY_CHANNELS on NWP |
| **MBVR topology** | [VR](vr.md) | NIO is single SVID bus master; MBVR IDs may differ with LPDDR6 |
| **DTS floorplan** | [CBB DTS](cbb_dts_telemetry.md), [IMH DTS](imh_dts_telemetry.md) | Fewer CCPs → different DTS mapping; verify DTS gen versions |
| **FHM_STATUS range** | [Thermtrip](thermtrip.md) | MAX_CCP_INDEX 0-23 (vs 0-31); FIVR IFDIM repeaters ~260 (vs 342) |
| **D2D prochot/fast_throttle** | [CBB Thermal Mgmt](cbb_thermal_management.md), [Prochot](prochot.md) | 32 GT/s UCIe — tighter timing; NIO↔2 CBBs (vs IMH↔4 CBBs) |
| **`LOCK_THERM_INT` / `THERM_EVENT_FFM`** | [Thermal Interrupts](thermal_interrupts.md) | Deprecated on DMR — status on NWP TBD |
| **DTS bugs** | [MCAs](mcas.md) | Gen1 DDR_A rawcode=0 and Gen2.6 CDC timing bug — NWP DTS IP version TBD |

### Related Sightings
<!-- Populate from subflow Related Sightings sections as they arise -->

### Subflows (15)

| # | Subflow | TCs | FW Agents | Key Registers | One-Line Summary |
|---|---------|-----|-----------|---------------|------------------|
| 1 | [ACP](acp.md) | 5 | ACode, PCode | `EMTTM_ALGO_MISC`, `IA32_THERM_STATUS`, `CORE_PMA_CR_CONFIG_10` | Core-level PID thermal throttle + Hammer fast-throttle + ITD/TTD |
| 2 | [CBB DTS & Telemetry](cbb_dts_telemetry.md) | 7 | PCode, PrimeCode | `PCU_CR_DTS_TEMP_IA_CCP`, `PCU_CR_DTS_TEMP_CCF`, `SOCKET_THERMAL` HPM | DTS sensor sampling, EWMA filtering, HPM transport to Root |
| 3 | [CBB Thermal Management](cbb_thermal_management.md) | 5 | PCode, ACode | `EMTTM_ALGO_MISC`, `CORE_PERF_LIMIT_REASONS`, slow limits | CBB EMTTM PID for CCF/Ring + cross-throttle + VR Hot actions |
| 4 | [EMTTM](emttm.md) | 2 | ACode, PCode, PrimeCode | `IA32_PACKAGE_THERM_STATUS`, `FIRM_CONFIG`, PLR | Three-layer PID throttling: Core (~300μS), CBB (~1mS), IMH (~1mS) |
| 5 | [GPIO](gpio.md) | 6 | PrimeCode, PCode | `POWER_CTL`, GPIO fuses, `IA32_PACKAGE_THERM_STATUS` | Package GPIO: PROCHOT_N in, THERMTRIP_N out, MEMHOT/MEMTRIP |
| 6 | [IMH DTS & Telemetry](imh_dts_telemetry.md) | 8 | PrimeCode | `PACKAGE_TEMPERATURE`, RC offsets, `IA32_PACKAGE_THERM_MARGIN` | IMH 19-sensor DTS array, RC telemetry pullers, ITD rail mapping |
| 7 | [IMH Thermal Management](imh_thermal_management.md) | 3 | PrimeCode | `FIRM_CONFIG`, `IA32_PACKAGE_THERM_MARGIN`, `DTS_CONFIG3` | IMH PID throttling of Memory + IO fabrics, cold-action TDP |
| 8 | [ITD](itd.md) | 14 | PrimeCode, PCode, ACode | `RESCTRL_CR_VOLTAGE_OFFSET`, `CORE_PMA_CR_RUNTIME_CONFIG_0`, ITD fuses | 2-slope voltage compensation across Core/Ring/Fabric/UCIe/MEM |
| 9 | [MCAs](mcas.md) | 1 | PCode | `IA32_MC_STATUS`, `IA32_THERM_STATUS[OOS]` | UCNA MCA on DIE_TOO_HOT (OOS: eff_tj_max + 10°C for 3mS) |
| 10 | [Prochot](prochot.md) | 5 | PrimeCode, PCode | TPMI `PROCHOT_RESPONSE_POWER`, `POWER_CTL`, HPM freq limits | PROCHOT_N input → power-to-freq 6-point profile, multi-die HPM |
| 11 | [TPMI/PMT](tpmi_pmt.md) | 6 | PrimeCode, PCode | `OPC_PKG_THERM_STATUS`, `OPC_THERMAL_MONITOR`, PMT entries | TPMI+PMT replace PCS for thermal status, filtering, margins, temp |
| 12 | [Thermal Interrupts](thermal_interrupts.md) | 9 | PCode, PrimeCode | `IA32_THERM_INTERRUPT`, `IA32_PACKAGE_THERM_INTERRUPT`, APIC LVT | LVT thermal interrupt generation on status transitions, multi-die HPM |
| 13 | [Thermal Reporting](thermal_reporting.md) | 11 | PrimeCode, PCode | `IA32_PACKAGE_THERM_STATUS`, `IA32_PACKAGE_THERM_MARGIN`, `MCP_THERMAL_REPORT` | Multi-die aggregation, EWMA, OOS, THERMAL_MONITOR_STATUS, margins |
| 14 | [Thermtrip](thermtrip.md) | 3 | None (HW) | GPIO fuses, FHM_STATUS, `PMAX_OVUV_HI_STATUS` | Last-resort HW shutdown: DTS daisy chain → PLL/FIVR/BGR off (~30-100nS) |
| 15 | [VR](vr.md) | 4 | PrimeCode, PCode | `SVID STATUS1[ThermAlert]`, `POWER_CTL[VR_THERM_ALERT_DISABLE]`, PEM | VR thermal alert → P1 throttle; VR_HOT → PROCHOT escalation |

| Segment | Count |
|---------|-------|
| FV | 73 |
| PSS | 16 |
| **Total** | **89** |
