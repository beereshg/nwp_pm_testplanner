# SoC Thermal > ACP (Autonomous Core Perimeter Thermal Management)

> **Status**: Enriched — HW/FW/OS touchpoint tables + KPI & Timing section populated (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: ACP (Autonomous Core Perimeter) is the core-level thermal management subsystem in DMR's three-tier hierarchical thermal control. It provides per-core autonomous temperature regulation via Acode microcode running inside the Core PMA, with PCode (CBB) acting as the inter-die coordinator and Root (PrimeCode/iMH) handling package-level reporting and fan control.

**Topology**:
```
Root PrimeCode (iMH)
  • Package MSRs, fan offset, pkg thermal interrupts, N-Strike PID (Mesh)
  • Disables N-Strike for Core when Core EMTTM active
       │ HPM: SOCKET_THERMAL (CBB→Root), DNS_EVENT_DELIVERY (Root→CBB)
       ▼
CBB PCode
  • CBB EMTTM PID ~1mS (CCF/Ring freq limiting)
  • Cross-throttle aggregation: core↔ring, core↔core (physical-neighbor aware)
  • Configures EMTTM_ALGO_MISC[CONTROL_TEMP] = eff_tj_max per core
  • VR HOT / PROCHOT detection; OOS detection
       │ PMSB CRs (SHORT_TELEM IOs), CROSS_CORE_THROTTLE_REQ
       ▼
Core ACP / Acode (per core, CBB top die)
  • Core EMTTM PID ~300μS — autonomous frequency control
  • ITD/TTD — voltage compensation driven by DTS DTD interrupts (±3°C)
  • Do-Not-Exceed / Hammer — instant throttle to LFM on DTD sticky (~nS)
  • Asserts CROSS_CORE_THROTTLE_REQ when self-help fails
       ▲
Core DTS Gen2.6 (per DCM, 2 per DCM)
  • SHORT_TELEM push ~102.4μS → PCode IO regs
  • DTD sticky / non-sticky threshold outputs
```

**Key operational principle**: Temperature is controlled by three nested feedback loops at decreasing response speed — HW Thermtrip/Hammer (~nS), Acode Core EMTTM PID (~300μS), and PCode CBB EMTTM PID (~1mS). Each loop operates autonomously within its scope; Acode requests cross-core throttle from PCode only when its own PID cannot converge. The temperature setpoint (`eff_tj_max`) is computed from SST_PP / SST_BF fuses ± C1E and TCC offsets and written by PCode into each core's `EMTTM_ALGO_MISC[CONTROL_TEMP]` register. ITD/TTD autonomously adjusts FIVR voltage targets based on DTS readings to exploit inversed-temperature dependency and reduce leakage power.

**Boot activation**: Base DTS and thermtrip become active at PH1.2 (fuse pull). PCode SA Thermal Puller and CBB EMTTM start at PH2.52 (slow loop). Core EMTTM and Acode ACP activate after PH3–5 (core reset exit) once the first valid SHORT_TELEM is received. The `eff_tj_max` is refined from worst-case `HIGHEST_TJ_MAX` to the actual SST/BF/C1E-resolved value after PH6 (BIOS/ucode wake).

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| DTS (Digital Temp Sensor) | CBB (per DCM, 2 per DCM) | Measures per-core, MLC, SSA-MLC temperatures; pushes SHORT_TELEM every ~102.4μS; DTD sticky alert triggers Do-Not-Exceed path | `IO_INTERRUPTS[25]` (DTD sticky alert → instant LFM), DTD non-sticky (bits 0,1 → ITD recalc), `DTS_TEMP_IA_CCP[N:0]` | [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) |
| Core PMA / ACP | CBB (per core) | Autonomous Core Perimeter — hosts Acode microcontroller; runs EMTTM PID (~300μS), ITD/TTD voltage compensation, Do-Not-Exceed/Hammer fast-throttle; asserts cross-core throttle request when self-help fails | `IO_ACODE_ALGO_VALUES1[MAX_ALLOWED_RATIO]` (MAR → PCode), `IO_INTERRUPT_ENABLE[25]` (DNE disable), `EMTTM_ALGO_MISC[CONTROL_TEMP]` (PCode writes TjMax target), `CORE_PMA_CR_CONFIG_10` | [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) |
| FIVR | CBB (base die, per-core / per-MLC domain) | Supplies VccCore and VCCMLC_SSA FIVRs; Acode autonomously adjusts voltage target for ITD/TTD compensation based on DTS readings | FIVR voltage target (internal), `IA_ITD_CUTOFF_V`, `IA_ITD_SLOPE`, `IA_ITD_SLOPE2`, `IA_ITD_CUTOFF_V2`, `ITD_CUTOFF_TJ` fuses | [DMR Thermal HAS — ITD](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#itd) |
| PMSB | CBB | Sideband infrastructure for cross-core throttle signaling from Acode to PCode and inter-CBB coordination | `PMSB_PCU_CR_VIRTUAL_SIG[13]` (CROSS_CORE_THROTTLE_REQ), `PMSB_PCU_CR_DTS_TEMP_IA_CCP[N:0]` (thermal telemetry), `CCP_X_Y` (physical location for neighbor calc) | [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) |
| PUnit | CBB | Power management controller; aggregates ACP cross-throttle requests; controls CCF/Ring FIVR ITD; applies `PROCHOT_POWER_LIMITED_FREQ_LIMIT` on PROCHOT | `PCU_CR_DTS_TEMP_IA_CCP[N:0]`, PROCHOT fast-throttle wire, `PCODE_SYSTEM_MODES_CONTROL[EMTTM_DISABLE]`, `FIRM_CONFIG[EMTTM_DISABLE]` | [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core PMA, CBB (per core) | Primary ACP implementer — autonomous EMTTM PID, ITD/TTD voltage compensation, DTD Do-Not-Exceed/Hammer, cross-core throttle request | Core EMTTM PID loop (~300μS); ITD/TTD recalc on DTD non-sticky interrupt (±3°C threshold, ~30-60μS); Hammer to LFM on DTD sticky; asserts `PMSB_PCU_CR_VIRTUAL_SIG[13]` (CROSS_CORE_THROTTLE_REQ) when convergence fails; reports MAR via `IO_ACODE_ALGO_VALUES1[MAX_ALLOWED_RATIO]` | [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) |
| PCode | CBB PUnit | Configures Acode control temp; handles cross-core throttle aggregation (physical-neighbor step-down); runs CBB EMTTM PID for CCF/Ring; manages EMTTM disable flow; handles VR HOT / PROCHOT paths | Writes `EMTTM_ALGO_MISC[CONTROL_TEMP] = eff_tj_max` on any TjMax change; cross-throttle: reads CCP_X_Y, applies Large_step (3 bins) to neighbors, Small_step (1 bin) to others; CBB EMTTM PID (~1mS); sets `PCODE_SYSTEM_MODES_CONTROL[EMTTM_DISABLE]` + `FIRM_CONFIG[EMTTM_DISABLE]` when THERMAL_THROTTLE_UNLOCK fuse set and OS clears IA32_MISC_ENABLE[18] | [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) |
| PrimeCode (iMH) | IMH die | Receives VR thermal alert from iMH GPIO poll; delivers DNS_EVENT_DELIVERY HPM to CBB for VR_THERM_ALERT; sends PROCHOT_POWER_LIMITED_FREQ_LIMIT HPM to CBB when yyPROCHOT asserted; resolves eff_tj_max via SST_PP / SST_BF fuses after PH6 | HPM: `DNS_EVENT_DELIVERY[VR_THERM_ALERT]` → CBB throttle to P1; HPM: `PROCHOT_POWER_LIMITED_FREQ_LIMIT` → CBB applies freq clamp; polls `SVID_VR_STATUS[ThermAlert]` (~97% VR thermal threshold) | [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) |
| BIOS | BIOS/UEFI | Programs per-SST-PP-level temperature targets (T_THROTTLE fuses resolved by PH6); programs TCC offset via MSR 0x1A2 or TPMI SST_PP_CONTROL; programs PROCHOT_RESPONSE_POWER | Writes `MSR 0x1A2[27:24]` (TJ_MAX_TCC_OFFSET) or `TPMI SST_PP_CONTROL.TJ_MAX_TCC_OFFSET`; PCode uses `max(MSR, TPMI)` value | DMR BIOS EDS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_THERM_STATUS` | 0x19C (per-core) | RO / RWC | Per-core thermal event status: [0] THERMAL_MONITOR_STATUS (EMTTM active), [2] PROCHOT_STATUS, [4] OUT_OF_SPEC, [14/15] CROSS_DOMAIN_LIMIT_STATUS/LOG; sticky log bits cleared by writing 0 | Intel SDM; DMR CBB PM HAS |
| MSR `IA32_TEMPERATURE_TARGET` | 0x1A2 (package) | RW (fields vary) | [23:16] REF_TEMP (effective TjMax, RO — read to get fused TjMax); [29:24] TJ_MAX_TCC_OFFSET (RO fused); [15:8] FAN_TEMP_TARGET_OFST (RW); BIOS programs TCC offset via this MSR or TPMI; PCode uses `max(MSR, TPMI)` value | Intel SDM; DMR Thermal HAS |
| MSR `IA32_MISC_ENABLE` | 0x1A0 (package) | RW | [18] THERMAL_MONITOR_ENABLE — master enable for EMTTM; when cleared (with THERMAL_THROTTLE_UNLOCK fuse=1), PCode disables both Acode EMTTM and HW Do-Not-Exceed. **DMR Edge only** — not allowed for SP/AP customers | Intel SDM; DMR Thermal HAS |
| MSR `MSR_POWER_CTL` | 0x1FC (package) | RW | [20] VR_THERM_ALERT_DISABLE — disables VR thermal alert throttle path; [1] C1E_ENABLE — enables C1E (when cleared, `TJ_MAX_C1E_DISABLED_OFFSET` fuse applied to reduce effective TjMax) | Intel SDM; DMR Thermal HAS |
| TPMI `SST_PP_CONTROL` | TPMI opcode (per SST-PP level) | RW | `TJ_MAX_TCC_OFFSET` field — alternative to MSR 0x1A2 for programming TCC offset; PCode takes `max(MSR 0x1A2[27:24], TPMI SST_PP_CONTROL.TJ_MAX_TCC_OFFSET)` | DMR TPMI HAS |
| CPUID Leaf 6 | EAX bit 3 | RO | EMTTM support flag — indicates whether EMTTM (Acode thermal control) is supported on this SKU | Intel SDM |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| **Control Loop Periods** | | | | |
| Core EMTTM PID (Acode) | ~300 | μS | Per-core autonomous thermal control loop; runs in Core PMA continuously in CC0 | DMR Thermal HAS; Legacy §Hierarchical Thermal Control |
| CBB EMTTM PID (PCode) | ~1 | mS | Slow loop — controls CCF/Ring frequency and aggregates cross-core throttle decisions | DMR Thermal HAS; Legacy §Hierarchical Thermal Control |
| DTS SHORT_TELEM push rate | ~102.4 | μS | Per DCM; Acode pushes Core + MLCSSA min/max temps to PUnit IO regs | DMR CBB Thermal Intg HAS |
| **Interrupt / Response Latencies** | | | | |
| DTD sticky → Hammer (Do-Not-Exceed) | ~nS | — | HW DTD asserts; core instantly forced to LFM; asynchronous, no flops on path | DMR Thermal HAS; Legacy §Hierarchical Thermal Control |
| DTD non-sticky → ITD/TTD recalc | ~30–60 | μS | ±3°C temperature crossing triggers Acode interrupt handler for voltage recalculation | DMR CBB Thermal Intg HAS |
| Thermtrip response | ~30–100 | nS | Asynchronous HW wire; no flops; PLLs and FIVRs shut down | Legacy §Thermtrip |
| PMax HW / PROCHOT wire response | ~500 | nS–μS | HW wire → PCode clock gating + frequency clamp applied | Legacy §Hierarchical Thermal Control |
| **Cross-Core Throttle Step Sizes** | | | | |
| Large_step (physical neighbors) | 3 | freq bins | PCode step-down applied to CCP_X_Y neighbors of over-temperature core | DMR Thermal HAS; Legacy §Cross-Core Throttle |
| Small_step (non-neighbors) | 1 | freq bin | PCode step-down applied to all other cores in same die | DMR Thermal HAS; Legacy §Cross-Core Throttle |
| **DTD Thresholds** | | | | |
| DTD non-sticky trigger delta | ±3 | °C | Threshold crossing (rise or fall) triggers ITD recalc interrupt in Acode | DMR CBB Thermal Intg HAS |
| **VR Thermal Alert** | | | | |
| VR thermal alert threshold | ~97 | % of VR capacity | `SVID_VR_STATUS[ThermAlert]` asserted; PrimeCode polls and delivers HPM to CBB → throttle to P1 | DMR Thermal HAS |
| **Boot Phase Gates** | | | | |
| eff_tj_max before PH6 | worst-case `HIGHEST_TJ_MAX` | — | PCode uses fuse worst-case until BIOS/ucode wake resolves SST_PP / SST_BF / C1E / TCC offset | Legacy §TjMax Resolution |
| UCIe one-time Boot ITD | PH2.40 | — | One-time ITD calc before D2D training; saves 11.7% UCIe power; reverts to worst-case after training | Legacy §ITD Flow at Boot |
| Dynamic ITD active from | PH2.52+ | — | Slow loop starts; all FIVR domains begin periodic temperature-driven ITD compensation | Legacy §ITD Flow at Boot |
| **ITD Algorithm** | | | | |
| ITD temperature trigger (interrupt path) | ±3 | °C above/below DTS | DTD non-sticky threshold for ACP interrupt-based ITD recalc | Legacy §ACP (VccCore) ITD |
| UCIe ITD power saving at boot | 11.7 | % | Reduction in UCIe FIVR power from one-time boot ITD vs worst-case fixed voltage | Legacy §UCIe (VCCC2IA) ITD |

## NWP Delta

**ACP is fully supported on NWP** — reused from DMR CBB with no changes.

- CBB runs ACP for core thermal management (PID controller, DTD HW interrupt, cross-core throttle)
- Core temperature targets and ACP EMTTM algorithm unchanged
- NWP CBB PM flows all leveraged from DMR — "no plans to add nor deprecate any CBB PM flow" (NWP PM MAS)
- 2 CBBs (vs 4) — fewer ACP instances to validate but same per-CBB behavior

### Validation Impact
- Fewer CBBs simplifies cross-throttle test matrix
- Core EMTTM + ACP autonomous control unchanged — same test cases apply

## Legacy (Human-Curated Reference)

### Architecture Summary

ACP is the **autonomous core-level thermal management** subsystem within DMR's hierarchical thermal control. Temperature management is split across three controllers, each with different scope and response speed:

#### Hierarchical Thermal Control

```
┌─────────────────────────────────────────────────────────┐
│  Root PrimeCode (iMH)                                   │
│  • Package-level thermal: N-Strike → PID (DMR) for Mesh │
│  • Reports: TjMax, Fan offset, THERM_MARGIN, pkg MSRs   │
│  • Triggers package interrupts via CBB                   │
│  • Disables N-Strike for Core when Core EMTTM active     │
└──────────────────────┬──────────────────────────────────┘
                       │ HPM: SOCKET_THERMAL, DNS_EVENT_DELIVERY
                       ▼
┌─────────────────────────────────────────────────────────┐
│  CBB PCode                                               │
│  • CBB EMTTM PID for CCF/Ring frequency limiting         │
│  • Cross-throttle: core↔ring, core↔core (physical-aware)│
│  • Configures core temperature target                    │
│  • Thermal telemetry to Root, interrupt distribution     │
│  • VR HOT / PROCHOT / OOS detection                      │
└──────────────────────┬──────────────────────────────────┘
                       │ PMSB CRs, Telemetry
                       ▼
┌─────────────────────────────────────────────────────────┐
│  Core (ACP) — Autonomous                                 │
│  • Core EMTTM PID: sustained temp control (~300μs loop)  │
│  • ITD/TTD: voltage compensation via DTS DTD alerts      │
│  • Do Not Exceed / Hammer: fast throttle to LFM (~nS)    │
│  • Cross Core Throttle Request when self-help fails      │
│  • DTS power management (reduced sampling in CC6)        │
└─────────────────────────────────────────────────────────┘
```

#### Temperature Target (Effective TjMax)

The target temperature for all thermal PIDs is:

```
eff_tj_max = eff_tj_max_sst - eff_tj_max_overall_offset

Where:
  eff_tj_max_sst = SST_BF_enabled ? SST_BF_CONFIG_[level]_T_THROTTLE
                                   : SST_PP_[level]_T_THROTTLE

  eff_tj_max_overall_offset = eff_tj_max_c1e_offset + eff_tj_max_msr_offset
                            - eff_tj_max_oc_offset

  eff_tj_max_c1e_offset = c1e_disabled ? fuse.TJ_MAX_C1E_DISABLED_OFFSET : 0

  eff_tj_max_msr_offset = max(MSR.IA32_TEMPERATURE_TARGET[TJ_MAX_TCC_OFFSET],
                              TPMI.SST_PP_CONTROL.TJ_MAX_TCC_OFFSET)

  eff_tj_max_oc_offset = OC_enabled ? OC_TJ_MAX_OFFSET : 0
```

**Variable sources** (ordered by write timing):
1. `SST_PP_[0..4]_T_THROTTLE` — per-SST-PP-level fuse, resolved at Ucode/BIOS wake (PH6)
2. `SST_BF_CONFIG_[0..4]_T_THROTTLE` — per-SST-BF fuse, overrides when BF enabled
3. `TJ_MAX_TCC_OFFSET` — written by BIOS via `MSR 0x1A2[27:24]` **or** TPMI `SST_PP_CONTROL`; PCode uses the larger of the two
4. `TJ_MAX_C1E_DISABLED_OFFSET` — fuse, applied only when `MSR POWER_CTL[C1E_ENABLE]` = 0
5. `OC_TJ_MAX_OFFSET` — from OC mailbox when OC enabled; **increases** headroom (decremented)

At early boot (before BIOS/ucode wake), PCode uses worst-case `fuse.HIGHEST_TJ_MAX` as TjMax. After PH6, SST/BF/C1E/TCC resolved.

#### Thermal Response Speed Hierarchy

| Mechanism | Speed | Controller | Action |
|-----------|-------|-----------|--------|
| Thermtrip | ~nS | HW wire | Shutdown — daisy-chain aggregation through DTS |
| Do Not Exceed / Hammer | ~nS | Core ACP (HW DTD) | Instant fast-throttle to LFM |
| PMax HW / PROCHOT | ~500ns-μS | HW wire → PCode | Clock gating + freq clamp |
| Core EMTTM PID | ~300μS | Core ACP (Acode) | Frequency reduction via PID |
| CBB EMTTM PID | ~1mS | CBB PCode (slow loop) | CCF/Ring frequency limiting |
| N-Strike / iMH PID | ~mS | Root PrimeCode | Mesh frequency control |
| RATL / EWMA | ~S | Root PrimeCode | Sustained power/temp averaging |

#### EMTTM Overview

EMTTM (Enhanced Multi-Thread Thermal Management) is a PID control loop that manages temperature by adjusting frequency. It runs at three levels:

- **Core EMTTM (ACP)**: Per-DCM PID (~300μS), monitors 2× IA Core + MLC + SSA-MLC temperatures. Squared error when temp > target for faster response: `if (error <= -1°C) then error = -error²`
- **CBB EMTTM**: Per-die PID (~1mS slow loop), controls CCF frequency. Cross-throttle domains: Big Core, Inf, D2D
- **iMH**: PID-based mesh control (replaced N-Strike for mesh in DMR)

#### CBB EMTTM Domains

| Domain | Action | Voltage | Temp Source | Scope |
|--------|--------|---------|-------------|-------|
| CCF | Frequency limit | VccR | `PCU_CR_DTS_TEMP_CCF[N:0]` | Package |
| Big Core | Cross-domain throttle | VccCore | `PCU_CR_DTS_TEMP_IA_CCP[N:0]` | DCM |
| Inf | Cross-domain throttle | VccInf | `PCU_CR_DTS_TEMP_SOC[2:0]_CR0/1` | Package |
| D2D | Cross-domain throttle | VccC2IA | `PCU_CR_DTS_TEMP_SOC[2:1]_CR[1:0]` | Package |

---

### Execution Flow

#### Core EMTTM (ACP) Flow

1. **PCode configures core target**: Writes `EMTTM_ALGO_MISC[CONTROL_TEMP] = eff_tj_max` on any change
2. **Core DTS samples**: 2 DTS per DCM, push SHORT_TELEM every ~102.4μS with min/max per domain
3. **Core EMTTM PID runs** (~300μS): Monitors min/max of all sub-domains (2× IA cores, MLC, SSA-MLC)
4. **Core adjusts frequency**: MAR (Max Allowed Ratio) exposed in `IO_ACODE_ALGO_VALUES1[MAX_ALLOWED_RATIO]`
   - `>90% × TjMax`: Core reports WP1 + 200MHz
   - `<90% × TjMax`: Core reports P0 (no throttle)
5. **If core can't converge** to `TjMax - Offset + DeltaT (~3°C)` after Hammer completes → asserts `CROSS_CORE_THROTTLE_REQ`

#### Cross-Core Throttle (Physical-Aware)

When any CCP asserts `CROSS_CORE_THROTTLE_REQ` (via `PMSB_PCU_CR_VIRTUAL_SIG[13]`):

```
1. Identify hot CCP physical location (X, Y from CCP_X_Y)
2. Mark thermal neighbors:
   X_neighbors = [X-1, X, X+1] (clipped to [0, X_MAX_LIMIT=3])
   Y_neighbors = [Y-1, Y, Y+1] (clipped to [0, Y_MAX_LIMIT=3])
3. For each CCP:
   If thermally_neighbor: stepdn = Large_step (default 3 bins)
   Else:                  stepdn = Small_step (default 1 bin)
4. Demote: CCP WP1 cross_throttle_ratio_limit = WP1 - stepdn (min: min_ratio)
5. When all CCPs de-assert: gradually promote (stepup++)
```

#### Core-Ring Cross Throttle

When ring is at min_ratio and still hot → core frequency reduced to help ring cool:

```
Core_Ratio_floor = Ring_EMTTM_PID_Limit + Core_Ring_Offset
Core_Ring_Offset = Min(Core_Max_Freq - Ring_Max_Freq, 0)
// Gradual: all cores treated as non-thermal-neighbors (Small_step)
```

#### Do Not Exceed / Hammer (Fast Path)

- DTS DTD sticky alert triggers `IO_INTERRUPTS[25]` → Acode responds in ~nS → Core forced to LFM
- Configured via fuse: `dtd_sticky_thr_h[8:0]` = TjMax + 7°C (format: `(temp + 64) × 2`, U8.1)
- Disable control: `IO_INTERRUPT_ENABLE[25]`

#### EMTTM Disable Flow

```
if (fuse.THERMAL_THROTTLE_UNLOCK = 1 AND
    MSR.IA32_MISC_ENABLE[THERMAL_MONITOR_ENABLE] = 0):
    set Pcode EMTTM Disable = 1
    set Acode EMTTM Enable  = 0
```

Disable knobs:
- Core: `CORE_PMA_CR_CONFIG_10[ADVANCED_THERMAL_CTRL] = 0` (disables BOTH Acode EMTTM AND HW Do Not Exceed)
- PCode: `PCODE_SYSTEM_MODES_CONTROL[EMTTM_DISABLE]`, `FIRM_CONFIG[EMTTM_DISABLE]`

> **Note**: EMTTM disable is only for DMR Edge (Carmel Beach, Linux/openSUSE). SW control NOT allowed for any -SP or -AP customer. Gated by `THERMAL_THROTTLE_UNLOCK` fuse.

#### Thermal Telemetry (CCP → PCode)

Each CCP pushes SHORT_TELEM every ~102.4μS:

| Telem ID | Field | Description |
|----------|-------|-------------|
| 0 | Domain0 Min Temp [8:0] | Min of all CCP cores (excl. MLCSSA/DLVR) |
| 1 | Domain0 Max Temp [8:0] | Max of all CCP cores |
| 2 | Domain1 Min Temp [8:0] | Min of second domain (PNC-Servers: MLCSSA) |
| 3 | Domain1 Max Temp [8:0] | Max of second domain |

Each includes Valid bit [11/27/43/59].

#### CBB Thermal Telemetry to Root

CBB sends `SOCKET_THERMAL` HPM with EWMA-filtered data:

| Field | Description |
|-------|-------------|
| `OOS` | Out-Of-Spec: `(Max_Temp > eff_tj_max + 10°C)` OR `(any domain max throttled AND Max_Temp > eff_tj_max for >20mS)` |
| `MIN_TEMP` | Min absolute temp (S9.6) — Root uses for VccInf min |
| `MAX_TEMP` | Max absolute temp (S9.6) |
| `MARGIN_TO_THROTTLE` | EWMA relative temp to eff_tj_max (negative = margin) |
| `MARGIN_TO_TCONTROL` | EWMA relative temp to eff_tj_max - Tcontrol offset (positive = margin) |

EWMA: `EWMA(t) = (1-α) × Current_Temp(t) + α × EWMA(t-1)`, α = 0.7

#### VR HOT Flow

1. **VR Thermal Alert** (~97%): iMH polls `SVID_VR_STATUS[ThermAlert]` → sends `DNS_EVENT_DELIVERY[VR_THERM_ALERT]` HPM to CBB → CBB throttles Core + Ring to P1. Disable: `MSR_POWER_CTL[VR_THERM_ALERT_DISABLE]`
2. **VR_HOT / PROCHOT** (100%): VR asserts xxPROCHOT → iMH asserts yyProchot to CBB → fast throttle wire triggers core clock division + CCF serial debug mode → PCode applies `PROCHOT_POWER_LIMITED_FREQ_LIMIT` → PCode de-asserts fast throttle wire once Core WP applied

#### ITD/TTD (Temperature-Dependent Voltage Compensation)

ITD (Inversed Temperature Dependency) and TTD (True Temperature Dependency / Negative ITD) dynamically compensate voltage for silicon temperature variations. Without dynamic compensation, a fixed worst-case guardband wastes significant power.

**Theory**: Transistor delay is a function of carrier mobility (↓ with temp) and threshold voltage (↓ with temp). These have opposing effects — the crossover point (ITD vs TTD regime) is determined per-process via post-Si fusing.

##### ITD Controllers & Domains

| Rail | VR Type | Controller | Domain | Notes |
|------|---------|-----------|--------|-------|
| VCCR_(EN,ES,WN,WS) | FIVR | CBB PCode | CCF/Ring | Per-CCF-FIVR-domain (4 top-die shadows × 2 FIVRs) |
| VCCCORE_i | FIVR | Core ACP (Acode) | Core | Per-core autonomous, interrupt-based + periodic |
| VCCC2IA | FIVR | CBB PCode (Base) | UCIe | Fixed target 0.7V, 40mV pk-pk AC noise budget |
| VCCMLC_SSA_E/W | FIVR | Core ACP (Acode) | MLC SRAM | Per-MLC, same ITD fuses as core (may split later) |
| VCCINF | MBVR | iMH PrimeCode | All | Shared rail — CBB sends min temp via `SOCKET_THERMAL` telemetry |
| VCCCFCMEM_*, VCCCFCIO, VCCFIXDIG_*, VCCUCIEA_* | FIVR | iMH | iMH-internal | See [DMR Thermal HAS ITD](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#itd) |

##### 2-Slope ITD Algorithm

```
calc_voltage_compensation(voltage, temperature):
    // Above TjMax — dedicated slope (mV/C guardband for EMTTM convergence ripples)
    if (temperature > ITD_CUTOFF_TJ):
        return ITD_SLOPE_ABOVE_CUTOFF_TJ * (temperature - ITD_CUTOFF_TJ)

    // Floor clipping (below floor_v, compensation is constant)
    if (voltage < itd_floor_v): voltage = itd_floor_v

    // Two-line calculation
    delta_v1 = ITD_CUTOFF_V1 - voltage
    itd_vcomp1 = delta_v1 * ITD_SLOPE1

    delta_v2 = ITD_CUTOFF_V2 - voltage
    itd_vcomp2 = delta_v2 * ITD_SLOPE2

    // Select line based on Vcross (intersection of 2 lines)
    itd_vcomp = (voltage < Vcross) ? itd_vcomp1 : itd_vcomp2

    // Negative ITD (TTD) gating
    if (itd_vcomp < 0 AND negative_itd_disable): return 0

    delta_temp = ITD_CUTOFF_TJ - temperature
    return itd_vcomp * delta_temp

// For a temperature range, worst case of both extremes
full_compensation(voltage, T_min, T_max):
    return max(calc(voltage, T_min), calc(voltage, T_max))
```

- **Positive compensation (ITD)**: Cold silicon needs higher voltage (mobility up, Vth up → net delay increase)
- **Negative compensation (TTD/NITD)**: Hot silicon below Vcross needs lower voltage (optional PnP optimization, gated by `TRUE_TD_ENABLE` / `NEGATIVE_ITD_DISABLED` fuse)

##### CCF Multi-V/F Curve ITD

Ring has 4 top-die shadows × 2 FIVRs = 8 independent FIVR domains. PCode calculates per-FIVR-domain ITD using each domain's local min/max DTS temperature, but shares the same ITD fuse set across all domains (silicon characteristics assumed uniform).

- Temp source: `PCU_CR_DTS_TEMP_CCF[N:0]` — each FIVR area has 2 DTS instances
- Fuses: `RING_ITD_CUTOFF_V`, `RING_ITD_CUTOFF_V2`, `RING_ITD_SLOPE`, `RING_ITD_SLOPE2`, `ITD_CUTOFF_TJ`, `TRUE_TD_ENABLE`

##### UCIe (VCCC2IA) ITD

UCIe D2D Phy requires fixed voltage ~0.7V with 40mV pk-pk AC noise budget at ≤16Gb/s. PCode controls temperature-dependent FIVR compensation.

- Temp source: `PCU_CR_DTS_TEMP_SOC(1/2)_CR[1:0]` (UCIe/VCCC2IA diodes)
- Fuses: `D2D_ITD_CUTOFF_V`, `D2D_ITD_CUTOFF_V2`, `D2D_ITD_SLOPE`, `D2D_ITD_SLOPE2`, `ITD_CUTOFF_TJ`
- **Boot ITD**: At UCIe MB bringup (PH2.40), PCode reads UCIe temps, calculates one-time ITD before D2D training. After training, reverts to worst-case ITD until periodic loop starts.
- **DMR A0 bugfix** (HSD [22021556158](https://hsdes.intel.com/appstore/article/#/22021556158)): D2D training errors from VCCIO DVFS → workaround: fixed boot voltage with ITD guardband baked in, bypass DVFS handshake, enable timer-based periodic retraining

##### ACP (VccCore) ITD — Core Autonomous

Core Acode manages ITD+TTD for VccCore FIVR autonomously:

1. **Periodic**: Temperature readout → voltage compensation folded into WP recalc
2. **Interrupt-based**: DTS DTD non-sticky alerts (bits 0,1) trigger recalc when temp crosses ±3°C threshold — response ~30-60μS

- Fuses (same for all CCPs): `IA_ITD_CUTOFF_V`, `IA_ITD_CUTOFF_V2`, `IA_ITD_SLOPE`, `IA_ITD_SLOPE2`, `ITD_CUTOFF_TJ`
- Formula: `Vcomp(ITD) = slope × (IP_V - Vcutoff) × (WC_temp - ITD_CutOff_Tj)`
- **DCM behavior**: Any core within a DCM raising an interrupt triggers recalc for both cores (shared PLL). If only voltage changes (no freq change), only the affected core changes V.
- **MLC SSA**: Core uses same ITD fuses for both Core and MLCSSA FIVRs (may split later per TR)
- **Disable**: `CORE_PMA_CR_CONFIG_10[FAST_TEMPERATURE_MANAGEMENT_EN]=0` disables interrupt-based ITD (periodic-only remains)

##### ITD Flow at Boot / Reset

| Phase | ITD State | Notes |
|-------|-----------|-------|
| Reset exit (before periodic) | Worst-case fixed ITD (safe temperature: `MIN_TEMPERATURE` for min, `ITD_CUTOFF_TJ` for max) | Ensures sufficient voltage at any temp |
| PH2.40 (UCIe MB training) | One-time ITD calc from actual temp | Saves 11.7% UCIe power; reverts to worst-case after training |
| PH2.52+ (slow loop starts) | Dynamic ITD active | All domains track temp periodically |
| Reset entry | Worst-case ITD set before PCode reset | Safe for next boot |
| PkgC6 | Same as active state | DTS stays alive in CBB C6 |
| Invalid temp readings | Assume worst case: `MIN_TEMPERATURE` (cold) and `ITD_CUTOFF_TJ` (hot) | |

##### ITD Disable Controls

| Method | Scope | Effect |
|--------|-------|--------|
| Set `ITD_SLOPE` fuses = 0 | All ITD | Disables all temperature-dependent compensation |
| Set `ITD_CUTOFF_TJ` = 0 | All ITD | Disables ITD compensation |
| Set `NEGATIVE_ITD_DISABLED=1` / `TRUE_TD_ENABLE=0` | TTD only | Disables voltage reduction for cold silicon |
| OC Mailbox (Misc. Turbo Control 0x18/0x19) bit 3 | TTD only | Dynamic disable of negative ITD |
| `CORE_PMA_CR_CONFIG_10[TRUE_TD_EN]=0` | Core TTD | ACP true TD disable |

#### Thermtrip

Thermtrip is the last-resort thermal protection — it instantly shuts down PLLs and FIVRs when silicon temperature exceeds the thermtrip threshold, preventing permanent damage.

##### Key Properties
- **Response time**: ~30-100nS (asynchronous, no flops on the wire)
- **Threshold**: Per-product, from QnR requirement. Maximum evaluated runaway: ~125°C ±10°C
- **Coverage**: Every DTS in the die participates — thermtrip daisy-chain cannot be disabled

##### DMR CBB Thermtrip Topology

The thermtrip daisy chain is organized as sub-chains per tile, ORed before the survivability filter:

```
  Top Die (Tiles)              Base Die
  ┌──────────┐
  │ Tile 0   │─── Core DTS Chain ──┐
  │  Core 0-3│─── CBO DTS Chain ───┤
  ├──────────┤                     │  ┌─────────────────────┐
  │ Tile 1   │─── Core DTS Chain ──┼─→│ Thermtrip Surv &    │
  │  Core 4-5│─── CBO DTS Chain ───┤  │ Aggregation Block   │──→ Punit
  ├──────────┤                     │  │  (OR all chains)    │     │
  │ Tile 2   │─── Core DTS Chain ──┤  └─────────────────────┘     │
  │  Core 6-7│─── CBO DTS Chain ───┘                              ▼
  └──────────┘                              To PLL, FIVR, BGR, etc.
                                            + GPIO → iMH
  Base Die:  AON DTS, DTS1, DTS2
             also feed into aggregation
```

- **Top→Base path**: `o_thermtrip_top2base_[0:2]` (active high, shaft) — one per tile
- **Base aggregation**: All tile chains + base DTS chains → OR → survivability filter → Punit
- **CBB↔iMH interface**: `YY_THERMTRIP_N` GPIO (bidirectional, open drain, active low)
  - TX: `TX_EN_B` = CBB thermtrip output
  - RX: `RX_DATA` = iMH thermtrip input

##### Thermtrip Actions

| Component | Action on Thermtrip |
|-----------|-------------------|
| **PLL** | 1. Gate output clock (~3 cycles latency). 2. Graceful shutdown via FSM (~30 ref clk cycles). If ref clock stops first, PLL may remain partially enabled until cold reset. |
| **FIVR** | Disable all output voltages |
| **BGR** | Bandgap reference shutdown |
| **Platform** | iMH receives via GPIO → platform-level shutdown sequence |

##### Thermtrip at Boot / Sleep

| State | Thermtrip Status |
|-------|-----------------|
| PH0 (InfPwrGood) | Not yet — DTS not enabled |
| PH1.2 (pd_fuse_infra reset, DTS fuse pull + DTSEnable) | **Thermtrip active** — only protection until EMTTM starts |
| PH2+ (EMTTM active) | Active — redundant with EMTTM |
| PkgC6 | **Active** — all CBB DTS remain enabled during PKGC6 |
| Disabled core | Thermtrip chain passes through disabled core DTS (supplied by VCCINF). If entire top tile disabled, shaft isolates signal to 0. |

##### COR CBB Thermtrip (Planar Topology)

COR uses a planar (non-tiled) topology with separate chains:
- Core Chain 1, Core Chain 2, CCF Chain, unCore Chain
- Each aggregated through OR → survivability filter → Punit

##### Sort Isolation

During wafer sort (per-die testing), thermtrip signals are isolated at shaft block entrances via `hvm_mode_sel` signal. This prevents cross-die interference during independent die testing.

#### DTS Topology & Diode Inventory

##### DMR CBB DTS Summary

| Die | DTS Instance | DTS Gen | Diode Count | Sensing Domains | Report Method |
|-----|-------------|---------|-------------|-----------------|---------------|
| Base | DTS0 (AON) | Gen1 | 1 | PAR PDN (VCCINF) | Thermal puller → PCode IOs |
| Base | DTS1 (south) | Gen1 | 6 | VCCINF, VCC2IA (UCIe DDA0/1, GPIO south, center) | Thermal puller → PCode IOs |
| Base | DTS2 (north) | Gen1 | 6 | VCCINF, VCC2IA (UCIe DDA0/1, GPIO north, ESE) | Thermal puller → PCode IOs |
| Base | CCF DTS[0..15] | Gen1 | 6 each | VCCR (LLC data, CBO north/south) | Thermal puller → min/max per CCF FIVR |
| Top (per DCM) | Core DTS0 | Gen2.6 | 15+1 | VccCore (7 diodes: OOO_int, OOO_vec, FMA, MEU×2, FE, alloc), VccMLCSSA (3: MLC×3), VccCore (5: MLC_shared, exe, MSID, FMAv1, OOO_vec2, MEU_exeint) | Core PMA push → SHORT_TELEM |
| Top (per DCM) | Core DTS1 | Gen2.6 | 15+1 | Same layout as DTS0 for iCore1 | Core PMA push → SHORT_TELEM |

**Totals**: Top die: 64 DTS (gen2.6), up to 512 diodes per die (32 DCMs × 16 diodes/core × 2 DTS). Base die: up to 15 DTS (gen1), ~85 diodes.

##### DTS Fuse Programming (Key Differences Top vs Base)

| Fuse | Base DTS (Gen1) | Core DTS (Gen2.6) |
|------|----------------|-------------------|
| `oneshotmodeen` | DTS0: 0x0 (continuous), DTS1/2: 0x1, CCF: 0x1 | 0x1 |
| `sleeptimer` (CC0) | DTS1/2: 0x6 (258.78μS), CCF: 0x0 (13.02μS) | 0x0 (minimal, ~13μS) |
| `sleeptimer1` (CC6) | N/A | 0x19 (1.034mS) — core switches via `i_timer_sel` |
| `catfilteren` | 0x1 (thermtrip filter enabled) | 0x1 |
| `active_diode_mask` | DTS0: 0x1, DTS1/2: 0x3F, CCF: 0x3F | N/A (uses `active_diode_mask_32`) |
| `active_diode_mask_32` | N/A | 0x7FFF (15 diodes) |
| `dtd_sticky_thr_h` | 9'h0 (not used by base) | `HIGHEST_TJ_MAX + 5°C` (Hammer threshold, format: U8.1+64D) |
| `rdcal_mask1` | N/A | 0x3FBF (Core diodes bits 7:1, 14:9 → Domain0 min/max) |
| `rdcal_mask2` | N/A | 0x101 (MLCSSA diodes bits 0,8 → Domain1 min/max) |

##### Core DCM Diode Layout (PNC)

Each DTS within a DCM connects 15 diodes (16th reserved for DLVR, not in DMR):

- **Domain0 (Core)** — `rdcal_mask1`: icore OOO_int, OOO_vec, FMA, MEU×2, FE, alloc_int, exe_vec, MSID, FMAv1, OOO_vec2, MLC_shared, MEU_exeint (13 diodes)
- **Domain1 (MLCSSA)** — `rdcal_mask2`: MLC SRAM diodes (2 diodes per DTS: bits 0, 8)
- Each DCM aggregates 2× DTS min/max → Core PMA pushes per-domain min/max via SHORT_TELEM

##### DTS Gen Version Comparison

| Property | Gen1 (Base) | Gen2.6 (Core Top) |
|----------|-------------|-------------------|
| Diode scan time | 13.24μS/diode | 2.56μS/diode |
| Max diodes | 6 | 16 (legacy) + 16 (shared) |
| DTD pins | 1 threshold | 4 thresholds |
| Configurable min/max | No | Yes (3 sets) |
| Retention support | No | Yes |
| Main clock | 100MHz | 400/200/100MHz (strap-selected) |
| Temperature histogram | No | No (Gen2.7+) |

#### PM GPIO & Interdie Thermal Signals

##### GPIO Signals (Package Level)

| Signal | Type | Target IP | Description |
|--------|------|-----------|-------------|
| `xxThermtrip_N` | In/Out | EBC | Wire OR'd in package from all dies |
| `xxMemtrip_N` | Output | EBC | Wire OR'd from all dies with memory |
| `xxProchot_N` | Input | Punit GPIO | PROCHOT on package master IO only |
| `xxMemhot_in_N` | Input | Punit GPIO | MemHot input on package master |
| `xxMemhot_out_N` | Output | Punit GPIO | MemHot output on package master |
| `xxPmax_trigger_IO` | In/Out | Punit adhoc | PMax GPIO on package master (no 4-wire standard) |
| `xxPM_FAST_WAKE_N` | In/Out | Punit GPIO | PkgC6 fast wake coordination |

##### Die-to-Die MDFC Punit Signals (Thermal-Relevant)

| Signal | Type | Description |
|--------|------|-------------|
| `i/o_punit_interdie_prochot` | In/Out | Cross-die PROCHOT: GPIO std → Punit root → MDFC → all dies |
| `i/o_punit_interdie_pmax_hard_throttle` | In/Out | PMax hard throttle from PMax-owner compute die to all dies |
| `i/o_punit_interdie_pmax_pwm_throttle` | In/Out | PMax soft PWM throttle from PMax-owner to all dies |
| `i/o_punit_interdie_fast_rapl` | In/Out | Fast RAPL throttle from IO HPM root to all dies |
| `dns_wake_in/out` | In/Out | PkgC6 subsystem idleness coordination, daisy-chained root→leafs |
| `MBVR_Qactive/Qreq_n/Qaccept_n/Qdeny` | In/Out | MBVR ramp coordination for SVID during PkgC flow |

#### ACP Configuration (PCode → Core PMA CRs)

At reset, PCode drives ACP configuration via PMA CRs (not A2P mailbox — removed since LNL):

| CR | Content | Notes |
|----|---------|-------|
| `CORE_PMA_CR_BOOT_CONFIG` | Misc SOC-specific boot config | |
| `CORE_PMA_CR_RUNTIME_CONFIG_0` | ITD slopes/cutoffs, thermal params, BCLK freq | ITD/TTD config for Acode |
| `CORE_PMA_CR_AVX_CONFIG_0` | AVX offsets + voltage guardband | |
| `CORE_PMA_CR_CDYN_INDEX_*_*` | ICCP Cdyn values (up to 16 in 8 regs) | `CORE_PMA_CR_CDYN_RATIO_0_1` through `_14_15` (offsets 0x3068-0x3084) |
| `CORE_PMA_CR_CONFIG_CTRL` | `CONFIG_DONE` bit — signals ACP config complete | Acode waits for this before starting |
| `CORE_PMA_CR_SMT_CONTROL` | `THREAD_MASK[3:0]` — enables SMT2/SMT4 per CCP | Legal: 0b0000, 0b0001, 0b0011, 0b1111 |
| `CORE_PMA_CR_LP_ENABLE` | `CORES_ENABLE_MASK[3:0]` — per-core enable | PCode must write to disabled modules too |
| `PMA_CR_RESOLUTION_CONTROL` | CSTATE_LIMIT, FLUSH_C6_DRAM, AUTODEM2C1EN, HWP_VOTING_RIGHTS, RELEASE_AUTO_WAKE_UP_BUDGET_REQ | PCode writes directly (no RMW) |
| `EMTTM_ALGO_MISC` | `CONTROL_TEMP[7:0]` = eff_tj_max | Updated on any eff_tj_max change |
| `CORE_PMA_CR_CONFIG_10` | `ADVANCED_THERMAL_CTRL[4]`, `TRUE_TD_EN[2]`, `FAST_TEMPERATURE_MANAGEMENT_EN[3]`, `PDP_PROTECTOR_DIS[6]` | Thermal control enables/disables |

#### Disabled DTS / Core Disable Thermal Handling

When a core DTS is bad, the core can be disabled to recover the part:

1. **Single core disabled in DCM**: Core PMA identifies via `CORE_PMA_CR_LP_ENABLE[CORES_ENABLE_MASK]`. Acode disables the associated DTS (`dtsenable=0, dtsenableovr=1`). Telemetry continues from the remaining core — temperature reports exclude the disabled core.
2. **Both cores disabled in DCM**: CCP temperature valids de-asserted. PCode must identify and ignore the module's temperature data.
3. **Thermtrip with disabled DTS**: DTS digital is supplied by VCCINF — thermtrip chain passes through even if core DTS disabled. If entire top tile disabled, shaft isolates signal to 0.
4. **Disabled LLC/CCF**: No special thermal treatment — even disabled LLC regions carry ring traffic and need temperature monitoring.

#### Boot Thermal Sequence

| Phase | Thermal State | Details |
|-------|--------------|--------|
| PH0 | InfPwrGood | No thermal monitoring yet |
| PH1.2 | SOC DTS fuse pull + DTSEnable | **Thermtrip active** — sole protection until EMTTM starts. DTS uses worst-case ITD (safe voltage: `MIN_TEMPERATURE` min, `ITD_CUTOFF_TJ` max) |
| PH2.2 | SA Thermal Puller unblocked | PMSB unblock → Punit starts pulling SOC/CCF DTS temps |
| PH2.40 | UCIe MB training | One-time ITD correction: PCode reads UCIe temps, calcs ITD before D2D training. After training → revert to worst-case until periodic loop |
| PH2.52 | Slow loop starts | Dynamic ITD + EMTTM active for all CBB domains |
| PH3-5 | Core reset exit | Core EMTTM + Acode ITD/TTD start after core telemetry valid |
| PH6 | Ucode/BIOS wake | eff_tj_max refined: Before this, PCode uses `HIGHEST_TJ_MAX` (worst-case). After: SST_PP/BF/C1E resolved |
| Reset entry | Worst-case ITD set | Safe for next boot |
| PkgC6 | All active | CBB DTS remain enabled, thermtrip functional, Core telemetry stops → PCode clears valids, applies decay model |

**Temperature operating range**: Servers: 0°C–110°C. Comms/IOTG: −40°C–105°C.

---

### Key Registers & Interfaces

#### Core MSRs

| MSR | Address | Scope | Key Fields |
|-----|---------|-------|------------|
| `IA32_THERM_STATUS` | 0x19C | Core | `THERMAL_MONITOR_STATUS[0]`, `PROCHOT_STATUS[2]`, `OOS_STATUS[4]`, `THRESHOLD1/2_STATUS[6/8]`, `TEMPERATURE[23:16]` (relative to TjMax), `VALID[31]` |
| `IA32_THERM_INTERRUPT` | 0x19B | Core | `HIGH/LOW_TEMP_INT_ENABLE[0:1]`, `PROCHOT_INT_ENABLE[2]`, `THRESHOLD1/2_REL_TEMP + INT_ENABLE` |
| `IA32_TEMPERATURE_TARGET` | 0x1A2 | Pkg-MC | `REF_TEMP` (fused TjMax), `TJ_MAX_TCC_OFFSET`, `FAN_TEMP_TARGET_OFST` |
| `IA32_MISC_ENABLE` | 0x1A0 | Pkg | `AUTO_THERMAL_CONTROL_CIRCUIT_ENABLE[3]` |
| `POWER_CTL` | 0x1FC | Pkg-MC | `C1E_ENABLE[1]`, `VR_THERM_ALERT_DISABLE[24]`, `ENABLE_BIDIR_PROCHOT[0]`, `DIS_PROCHOT_OUT[21]` |
| `CORE_PERF_LIMIT_REASONS` | — | Pkg | `THERMAL`, `PROCHOT`, `VR_THERMALERT` (status + log) |

#### Package Thermal MSRs (owned by iMH, reference)

| MSR | Address | Key Fields |
|-----|---------|------------|
| `IA32_PACKAGE_THERM_STATUS` | — | `THERMAL_MONITOR_STATUS`, `TEMPERATURE`, `OOS_STATUS/LOG`, `THRESHOLD1/2` |
| `MCP_THERMAL_REPORT_1` | 0x1A3 | `MARGIN_TO_THROTTLE[15:0]` (S10.6), `MARGIN_TO_TCONTROL[31:16]` (S10.6) |
| `MCP_THERMAL_REPORT_2` | 0x1A5 | `PACKAGE_ABSOLUTE_MAX_TEMPERATURE[15:0]` (S10.6) |
| `PACKAGE_THERM_MARGIN` | — | `THERM_MARGIN` (fan speed control) |

#### Core CRs (PCode → Core)

| CR | Key Fields | Notes |
|----|------------|-------|
| `EMTTM_ALGO_MISC` | `CONTROL_TEMP[7:0]` (S8.0) = eff_tj_max | PCode writes on any eff_tj_max change |
| `IO_ACODE_ALGO_VALUES1` | `MAX_ALLOWED_RATIO[9:0]` (16.67MHz units) | Core EMTTM output, observability only |
| `CORE_PMA_CR_CONFIG_10` | `ADVANCED_THERMAL_CTRL[4]` (en/dis), `TRUE_TD_EN[2]`, `FAST_TEMPERATURE_MANAGEMENT_EN[3]` | EMTTM + Hammer disable |
| `PMSB_PCU_CR_VIRTUAL_SIG` | `CROSS_CORE_THROTTLE_REQUEST[13]` | Core → PCode cross-throttle indication |

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
| `DNS_EVENT_DELIVERY[VR_THERM_ALERT]` | Root → CBB | VR thermal alert — throttle to P1 |
| `DNS_EVENT_DELIVERY[cross_die_throttle]` | Root → CBB | Die cross-throttle (not POR DMR) |
| `PROCHOT_POWER_LIMITED_FREQ_LIMIT` | Root → CBB | PROCHOT freq limit per CDYN index |
| `B2P_EXCHANGE` | Root → CBB | OC TjMax offset (opcode 0xAC) |

#### PECI/TPMI Telemetry

| PCS Cmd | Name | Mapped to PMT? | Description |
|---------|------|----------------|-------------|
| 2 | PKG_MAX_TEMP | No | Package temperature (T_avg) |
| 9 | READ_MODULE_TEMP | Yes | Max temps: DCM, CBB die, Ring |
| 10 | THERM_MARGIN | No | DTS2.0 thermal margin |
| 16 | TEMP_TARGET | Yes | Processor temperature target fields |
| 32 | TOTAL_THROTTLED_TIME | Yes | Total CPU thermally throttled time below P1 |

---

### Key Fuses

| Fuse | Default | Description |
|------|---------|-------------|
| `HIGHEST_TJ_MAX` | 0x69 (105°C) | Worst-case TjMax before SST/BF resolved |
| `TJ_MAX_C1E_DISABLED_OFFSET` | 0 | Extra offset if C1E disabled (U5.0) |
| `SST_PP_[0..4]_T_THROTTLE` | 0x69 | Per-SST-PP-level max temp threshold (U8.0) |
| `SST_BF_CONFIG_[0..4]_T_THROTTLE` | 0 | Per-SST-BF max temp when BF enabled (U8.0) |
| `SST_BF_CONFIG_[i]_T_CONTROL_OFFSET` | 0 | Fan temp offset per SST-BF level |
| `THERMAL_THROTTLE_UNLOCK` | 0 | If 1, allows SW to disable EMTTM |
| `OC_ENABLED` | 0 | Overclocking enable |
| `IA_MIN_RATIO` | — | Minimum ratio (Pm), does not vary by SST |
| `DTS.dtd_nsalert_thr_[0]` | — | Core Do Not Exceed / Hammer threshold |
| `DTS.dtd_sticky_thr_h[8:0]` | — | Static Do Not Exceed threshold (TjMax+7°C) |
| `MIN_TEMPERATURE` | — | Coldest ambient possible (for decay calcs, ITD worst-case min temp) |
| **ITD Fuses** | | |
| `{DOMAIN}_ITD_SLOPE` | — | Slope1 for lower voltage range (U-8.13, 1/°C) |  
| `{DOMAIN}_ITD_SLOPE_2` | — | Slope2 for higher voltage range (U-8.13, 1/°C) |
| `{DOMAIN}_ITD_CUTOFF_V` | — | Cutoff voltage for slope1 line (U1.8, Volt) |
| `{DOMAIN}_ITD_CUTOFF_V_2` | — | Cutoff voltage for slope2 line (U1.8, Volt) |
| `{DOMAIN}_ITD_FLOOR_V` | 0 | Below this voltage, ITD compensation clipped (U0.8) |
| `ITD_CUTOFF_TJ` | 100°C | Reference calibration temperature — no compensation at this temp (U7.0) |
| `ITD_VOLTAGE_SLOPE_ABOVE_CUTOFF_TJ` | 2.5mV/°C | Slope for voltage increase per °C above ITD_CUTOFF_TJ (U-6.12, shared all domains) |
| `NEGATIVE_ITD_DISABLED` / `TRUE_TD_ENABLE` | 0 | Disable negative ITD (TTD) compensation |
| `IA_ITD_CUTOFF_V/V2` | — | Core-specific ITD cutoff voltages (Acode) |
| `IA_ITD_SLOPE/SLOPE2` | — | Core-specific ITD slopes (Acode) |
| `RING_ITD_CUTOFF_V/V2` | — | CCF ring ITD cutoff voltages |
| `RING_ITD_SLOPE/SLOPE2` | — | CCF ring ITD slopes |
| `D2D_ITD_CUTOFF_V/V2` | — | UCIe D2D ITD cutoff voltages |
| `D2D_ITD_SLOPE/SLOPE2` | — | UCIe D2D ITD slopes |
| **DTS Configuration Fuses** | | |
| `DTS.oneshotmodeen` | 0x0 (DTS0), 0x1 (DTS1/2/CCF/Core) | One-shot vs continuous conversion |
| `DTS.sleeptimer` (CC0) | varies | Sleep between conversions: 0x0=13μS, 0x6=259μS, 0xB=5.2mS |
| `DTS.sleeptimer1` (CC6) | 0x19 (core) | Longer sleep in CC6: 0x19=1.034mS |
| `DTS.catfilteren` | 0x1 | Catastrophic filter enable (thermtrip glitch filter) |
| `DTS.active_diode_mask` | 0x3F (base 6-diode), 0x1 (DTS0) | Active diode bitmask (Gen1) |
| `DTS.active_diode_mask_32` | 0x7FFF (core) | Active diode bitmask (Gen2.6, 15 diodes) |
| `DTS.rdcal_mask1` | 0x3FBF (core) | Domain0 (Core) diode aggregate mask |
| `DTS.rdcal_mask2` | 0x101 (core) | Domain1 (MLCSSA) diode aggregate mask |
| `DTS.dtd_nsalert_thr_[0..3]` | varies | DTD non-sticky alert thresholds (0: DoNotExceed, 1: Hammer) |
| `DTS.dtd_sticky_thr_h` | `HIGHEST_TJ_MAX+5°C` | Static thermtrip/Hammer threshold (U8.1+64D format) |
| **Thermal Management Fuses** | | |
| `EMTTM_ENABLE` | 1 | Global EMTTM enable |
| `THERM_DECAY_RATE` | — | Temperature decay constant for PkgC invalid data |
| `OOS_THRESHOLD_OFFSET` | 10°C | Out-of-Spec threshold: TjMax + this offset |
| `OOS_TIMER` | 20mS | OOS assertion time threshold |
| `TCONTROL` | — | Fan ramp offset from TjMax (for thermal margin) |

---

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS (CBB Thermal) | [DMR CBB Thermal Management](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) | Primary spec — EMTTM, ACP, VR HOT, thermal reporting |
| HAS (Socket Thermal) | [Socket Thermal Mgmt](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | iMH-level thermal, N-Strike, interrupt handling |
| HAS (DMR SOC Thermal) | [DMR SOC Thermal](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | DMR-specific: PID mesh control, VR HOT flow, PROCHOT |
| HAS (ACP Core) | [Autonomous Core Perimeter PM](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html#acp-20-autonomous-thermal-management) | Core EMTTM, ITD/TTD specs |
| HAS (CBB Thermal Intg) | [DMR CBB Thermal Integration](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/DMR%20CBB%20Thermal%20Integration%20HAS/DMR%20CBB%20Thermal%20Integration%20HAS.html) | DTS topology, diode mapping, fuse config |
| HAS (ITD) | [DMR CBB ITD](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/ITD/ITD.html) | Voltage compensation |
| HAS (Thermtrip) | [CBB Thermtrip](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermtrip/Thermtrip.html) | Daisy-chain thermtrip |
| HAS (PM GPIO Interdie) | [DMR PM Interdie Signals](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Components/wave4_gpio_interdie.html#pm-gpio-signals) | GPIO + MDFC die-to-die PM wires |
| HAS (CCP PM Intg) | [LNL CCP PM Integration](https://docs.intel.com/documents/pm_doc/src/LNL/IP%20Integration/CCP/ccp_pm_integration.html) | ACP config CRs, Qchannels, DOMA/T2C, WP interface |
| HAS (PNC Thermal) | [PCORE Thermal Sensors HAS](https://intel.sharepoint.com/:x:/r/sites/TheLions/GFC/_layouts/15/Doc.aspx?sourcedoc=%7B681F10F6-CE95-42E5-8B2F-E11399D65D4B%7D) | PNC diode table (SharePoint) |
| HAS (GFC Thermal) | [Thermal HAS.docx](https://intel.sharepoint.com/:w:/r/sites/TheLions/GFC/_layouts/15/Doc.aspx?sourcedoc=%7B1C71BB85-036E-4E54-8CD5-92482007F2E6%7D) | GFC thermal diode topology (SharePoint) |
| FAS (Pcode Thermal) | [Pcode Thermal FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/Thermals/Thermal%20Management_FAS.html) | Pcode implementation spec |
| MAS (Punit Thermal) | [CBB Thermal MAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/MAS/Thermal/CBB_thermal_mas.html) | Register/IO details |
| MAS (NWP iMH DTS) | [NWP iMH SOC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#dtsthermal-diode-and-thermtrip-chaining) | NWP iMH DTS placement + thermtrip chaining |
| HSD | 14022524100 | EMTTM disable: core knob disables both Acode EMTTM + HW Do Not Exceed |
| HSD | 13010546442 | PNC cross-core throttle |
| HSD | 13011142129 | Punit CBB cross-core throttle |
| HSD | 13012403519 | Core rdcal_mask1/2 DCM domain aggregation |
| HSD | 22021556158 | DMR A0 UCIe ITD bugfix (D2D training DVFS) |
| HSD | 13010612929 | Disabled DTS in DCM — keep associated DTS disabled |

---

### Feature Interactions

| Feature | Interaction |
|---------|-------------|
| **SST-PP/BF** | Changes eff_tj_max via `SST_PP_[i]_T_THROTTLE` / `SST_BF_CONFIG_[i]_T_THROTTLE` fuses |
| **C1E** | Disabling C1E reduces thermal headroom → `TJ_MAX_C1E_DISABLED_OFFSET` subtracted from eff_tj_max |
| **OC** | OC_TJ_MAX_OFFSET increases headroom (decremented from overall offset) |
| **PkgC6** | Core DTS telemetry stops → PCode clears valid bits, applies temperature decay model. CBB SOC DTS remains active. |
| **ITD/TTD** | Core voltage compensation using DTS DTD non-sticky alerts; ITD corrects for cold silicon. CBB PCode handles CCF/UCIe ITD, iMH handles VccInf ITD. |
| **VR HOT** | Thermal Alert (97%) → P1 limit; PROCHOT (100%) → fast throttle + freq clamp. CBB doesn't own SVID directly — FIVR input voltage (VCCIN_EHV) VRs communicate via iMH HPM. |
| **PMax** | PMax HW fast throttle wire shared with PROCHOT path; CCF serial debug mode (CBO pipe: cmd every 3rd/5th/7th/../15th cycle). PMax crosses dies via `i/o_punit_interdie_pmax_hard_throttle` MDFC. |
| **Disabled Core/DTS** | Disabled core → Acode disables DTS (`dtsenable=0`), telemetry excludes it. Thermtrip chain passes through (VCCINF-supplied). Disabled tile → shaft isolates to 0. |
| **RTIL (Acode FW update)** | During runtime Acode image load: PCode takes over ITD correction directly to IA VR (Acode is dead during download). Cores moved to DLVR bypass. Not POR in DMR. |

---

#### Validation Approach
- **Temperature target**: Verify `EMTTM_ALGO_MISC[CONTROL_TEMP]` matches computed eff_tj_max across SST-PP levels, C1E enable/disable, TCC offset
- **Cross throttle**: Generate thermal load on one CCP, verify neighboring CCPs get larger step-down than distant CCPs
- **EMTTM disable**: Verify only works when `THERMAL_THROTTLE_UNLOCK` fuse = 1 AND `IA32_MISC_ENABLE[3]` = 0; confirm both Acode EMTTM and HW Do Not Exceed disabled
- **Thermal information**: Read `IA32_THERM_STATUS`, verify TEMPERATURE field relative to TjMax, VALID bit, threshold crossings
- **Freq reduction reason**: Verify `CORE_PERF_LIMIT_REASONS[THERMAL]` set when core EMTTM active, cleared when deactivated; check PLR_DIE_LEVEL TPMI CR

---

### Related Sightings
<!-- No NWP ACP thermal sightings identified yet — populate as they arise -->

---

### NWP Delta

> **Items to verify for NWP** (not yet confirmed — check NWP HAS when available):

| Area | Question | DMR Baseline |
|------|----------|--------------|
| Core EMTTM | Same PID tuning? Same ~300μS loop rate? | DMR: ~300μS, squared error when hot |
| Core type | PNC (PantherCove) or new core? Changes to ACP interface? | DMR: PNC core with `PMSB_PCU_CR_VIRTUAL_SIG[13]` for cross-throttle |
| Cross-throttle topology | Same X/Y physical layout? Max limits? | DMR: X_MAX=3, Y_MAX=3, large_step=3, small_step=1 |
| Eff TjMax computation | Same formula? New SST-PP levels? | DMR: SST_PP[0..4], SST_BF, C1E offset, TCC offset |
| DTS topology | Number of DTS (gen1/gen2) and diodes per die? | DMR: Top 64 DTS gen2 + 512 diodes; Base 15 DTS gen1 + 85 diodes |
| EMTTM disable fuse | `THERMAL_THROTTLE_UNLOCK` still Edge-only? | DMR: Edge (Carmel Beach) only |
| Do Not Exceed threshold | Same TjMax+7°C default? | DMR: `dtd_sticky_thr_h` = TjMax+7°C |
| SHORT_TELEM format | Same 64-bit packet with 4 telem IDs? | DMR: 4 × (9-bit temp + valid + telem_id) |
| VR HOT | Same SVID Thermal Alert + PROCHOT 2-stage flow? | DMR: 97% alert → P1; 100% VR_HOT → PROCHOT |
| Die cross-throttle | Enabled in NWP? (Not POR in DMR) | DMR: Not POR, HPM `DNS_EVENT_DELIVERY[cross_die_throttle]` plumbed |
| **ITD/TTD** | | |
| ITD domains | Same FIVR domains? NWP adds VCCC2C FIVR on NIO — new ITD domain needed? | DMR: VCCR (CCF), VCCCORE (ACP), VCCC2IA (UCIe), VCCMLC_SSA |  
| CCF multi-FIVR ITD | NWP has 2 CBBs → fewer CCF FIVR domains. Same 4-shadow × 2-FIVR? | DMR: 4 top-die shadows × 2 FIVRs = 8 domains per die |
| UCIe ITD boot | Same D2D MB training ITD handshake? Same 0.7V target? | DMR: One-time ITD at PH2.40, 0.7V, 40mV AC budget |
| UCIe A0 bugfix | Applicable to NWP A0? (D2D training VCCIO DVFS issue) | DMR A0: HSD 22021556158 — bypass DVFS, fixed boot voltage |
| ITD fuse set | Same slopes/cutoffs? NWP process may differ | DMR: 2-slope per domain, shared ITD_CUTOFF_TJ and SLOPE_ABOVE_CUTOFF |
| VccInf ITD | Still iMH-controlled? NWP NIO replaces iMH — who controls VCCINF ITD? | DMR: iMH controls VccInf ITD using CBB min temp from SOCKET_THERMAL |
| **Thermtrip** | | |
| Thermtrip topology | NWP top-die tile count? COR uses planar (non-tiled). Which does NWP use? | DMR: 3 tiles, daisy-chain per tile → OR → survivability → Punit |
| Thermtrip GPIO | `YY_THERMTRIP_N` still bidirectional? NIO→CBB path? | DMR: Open drain bidirectional GPIO to iMH |
| Thermtrip during PkgC | DTS still enabled in NWP PkgC6? | DMR: All CBB DTS enabled, thermtrip functional |
| Thermtrip latency | Same ~30-100nS? | DMR: ~30-100nS, async, no flops on wire |
| **DTS & Config** | | |
| DTS gen version | NWP top die still Gen2.6? Base still Gen1? | DMR: Top Gen2.6 (2.56μS/diode), Base Gen1 (13.24μS/diode) |
| Core diode count | Same 15 diodes/DTS? PNC reuse confirmed but check DLVR diode #16 | DMR: 15 active (diode #16 = DLVR prep, not connected) |
| CCF DTS count | NWP fewer CCF slices → fewer CCF DTS instances? | DMR: up to 16 CCF DTS (Gen1) |
| `rdcal_mask1/2` | Same Domain0/Domain1 diode groupings? | DMR: mask1=0x3FBF (Core), mask2=0x101 (MLCSSA) |
| `dtd_sticky_thr_h` (Hammer) | Same formula: `HIGHEST_TJ_MAX + 5°C`? (DMR doc says +5°C, some sections say +7°C) | DMR: HAS says `HIGHEST_TJ_MAX + 5°C` in fuse table; validation uses +7°C |
| Thermal puller | Same SA thermal puller for base DTS? NIO equivalent? | DMR: Punit SA thermal puller pulls SOC/CCF DTS |
| **ACP Config Interface** | | |
| A2P mailbox | Confirmed removed (since LNL)? | DMR/LNL: Removed. PCode writes PMA CRs directly |
| `CORE_PMA_CR_CONFIG_CTRL.CONFIG_DONE` | Same handshake? | DMR: PCode writes 1 after all ACP CRs configured |
| Cdyn index configuration | Same 16-level table via `CORE_PMA_CR_CDYN_RATIO_*`? | DMR: 8 regs × 2 ratios = 16 Cdyn levels, U4.12 ratio from fused base |
| Qchannel interface | Same 3 channels (CFC_CLK, CFC_PWR, INF)? | DMR: 3 Qchannels per CCP, 12 wires per CCP |
| **Interdie Signals** | | |
| PROCHOT cross-die | Same MDFC `i/o_punit_interdie_prochot`? NIO topology? | DMR: GPIO std → Punit root → MDFC → all dies |
| PMax cross-die | Same hard/soft/RAPL throttle MDFC signals? | DMR: 3 MDFC: hard_throttle, pwm_throttle, fast_rapl |
| Disabled DTS recovery | Same per-core disable via `LP_ENABLE`? | DMR: `CORE_PMA_CR_LP_ENABLE[CORES_ENABLE_MASK]` disables DTS, thermtrip chain passes through |
