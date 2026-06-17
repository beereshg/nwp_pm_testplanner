# SoC Thermal > ITD (Inverse Temperature Dependence)

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: ITD dynamically adjusts per-domain FIVR/MBVR voltage based on silicon temperature, eliminating worst-case static voltage guardband. Uses a 2-slope piecewise algorithm per domain, distributed across all three thermal control agents.

**Topology**:
```
Acode (Core PMA) ── Core/MLCSSA ITD (~300μS periodic + ~30–60μS interrupt on DTD ±3°C)
  └── RESCTRL_CR_VOLTAGE_OFFSET → VccCore, VCCMLC_SSA FIVRs

CBB PCode ── CCF ITD (8 FIVR domains, ~1mS), UCIe ITD (one-time at PH2.40)
  └── PCU_CR_DTS_TEMP_CCF → RESCTRL_CR_VOLTAGE_OFFSET → VccR, VCCC2IA FIVRs

IMH PrimeCode ── VCCINF (MBVR, uses CBB min-temp from HPM), CFCMEM_W/E, CFCIO (GV)
                  FIXDIG / UCIEA (fixed rails, ITD_SLOPE=0 in production)
  └── IMH DTS → RESCTRL_CR_VOLTAGE_OFFSET per RC channel
```

**Key operational principle**: V_comp = slope × (ITD_CUTOFF_V − V) × (ITD_CUTOFF_TJ − Temp). Two slopes: slope1 below V_X, slope2 above. TRUE_TD_ENABLE fuse gates TTD (negative comp for hot silicon). DMR uses RC `RESCTRL_CR_VOLTAGE_OFFSET.OFFSET` directly (no new WP through Dispatcher) for voltage-only corrections.

**Boot activation**: Static worst-case voltage until PH2.40 (one-time UCIe ITD before D2D training). Dynamic IMH/CBB ITD from PH2.52. Core Acode ITD from PH3+.

ITD (Inverse Temperature Dependence) dynamically compensates voltage for silicon temperature variations. Without dynamic compensation, a fixed worst-case guardband wastes significant power.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core DTS Gen2.6 | CBB Top Die (per core) | Temperature input to Acode ITD for VccCore/MLCSSA; DTD non-sticky (±3°C) triggers interrupt-based ITD recalc | SHORT_TELEM Domain0/1; DTD non-sticky[0,1] | [ACP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html) |
| CCF / SOC DTS Gen1 | CBB Base Die | Temperature inputs to CBB PCode for VccR (8 domains) and VCCC2IA ITD | `PCU_CR_DTS_TEMP_CCF[N]`, `PCU_CR_DTS_TEMP_SOC(1/2)_CR[1:0]` | CBB Thermal Mgmt HAS |
| FIVR (per domain) | CBB/IMH | Voltage rails receiving ITD compensation via RC RESCTRL_CR_VOLTAGE_OFFSET | `RESCTRL_CR_VOLTAGE_OFFSET.OFFSET` per RC | [RC TRM HAS](https://docs.intel.com/documents/sysip_pm/resource_controller/TRM/TRM.html#voltage_offset) |
| IMH DTS (19/die) | IMH die | Temperature sources for PrimeCode ITD on VCCCFCMEM_W/E, VCCCFCIO, VCCINF | RC 0x7E00/0x7E04; 5 RC channels | DMR Thermal HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core PMA) | CBB Top Die | Autonomous ITD+TTD for VccCore and VCCMLC_SSA; periodic (~300μS) + interrupt-based (~30–60μS) on DTD non-sticky ±3°C threshold | `CORE_PMA_CR_RUNTIME_CONFIG_0` (ITD slopes/cutoffs); `CORE_PMA_CR_CONFIG_10[TRUE_TD_EN, FAST_TEMPERATURE_MANAGEMENT_EN]` | [ACP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html) |
| PCode (CBB) | CBB Base Die | ITD for VccR CCF (8 FIVR domains) and VCCC2IA UCIe; one-time boot ITD at PH2.40 before D2D training (saves ~11.7% UCIe power) | `PCU_CR_DTS_TEMP_CCF`; `D2D_ITD_SLOPE/SLOPE2` fuses; `RESCTRL_CR_VOLTAGE_OFFSET` | DMR Thermal HAS |
| PrimeCode (IMH) | IMH die | ITD for VCCINF (MBVR, uses CBB min temp via SOCKET_THERMAL HPM), VCCCFCMEM_W/E, VCCCFCIO (GV rails); VCCFIXDIG/VCCUCIEA fixed (ITD_SLOPE=0); RC V_OFFSET mechanism (no new WP) | `RESCTRL_CR_VOLTAGE_OFFSET.OFFSET`; HPM `SOCKET_THERMAL` min_temp receive | PrimeCode src |
| BIOS / UEFI | Platform | Programs ITD fuses at HVM (slope1/2, cutoff V/V2/V_X, ITD_CUTOFF_TJ); sets `TRUE_TD_ENABLE`; no runtime ITD control from OS | Fuse programming | HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_TEMPERATURE_TARGET` | 0x1A2 | RW | [29:24] TCC offset → eff_tj_max → `ITD_CUTOFF_TJ` baseline reference for all ITD domains | Intel SDM |
| OC Mailbox (Misc. Turbo Ctrl) | 0x18/0x19 bit 3 | RW | Dynamic disable of negative ITD (TTD) at runtime via OC mailbox | Legacy Execution Flow |
| `RESCTRL_CR_VOLTAGE_OFFSET.OFFSET` | Per-domain RC | FW-RW | Per-RC voltage compensation written by ITD algorithm; indirectly observable via SVID/PMBus voltage | [RC TRM HAS](https://docs.intel.com/documents/sysip_pm/resource_controller/TRM/TRM.html#voltage_offset) |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Core ITD recalc (interrupt) | ~30–60 | μS | DTD non-sticky ±3°C threshold → Acode ITD recalc; fast path | Legacy Execution Flow |
| Core ITD recalc (periodic) | ~300 | μS | Folded into Acode WP recalc per DCM | Legacy Architecture Summary |
| CBB/IMH ITD update period | ~1 | mS | PCode/PrimeCode slow loop | Legacy Architecture Summary |
| UCIe boot ITD power saving | ~11.7 | % UCIe power | One-time PH2.40 ITD vs worst-case fixed boot voltage; reverts to WC after training | Legacy Execution Flow |
| VccR ITD domain count | 8 | — | 4 top-die shadows × 2 FIVRs; independent ITD per domain | Legacy Architecture Summary |
| NWP new ITD domain | VCCFCFCAB | — | New CAB digital domain for NWP; ITD support added (MAS §3) | Legacy ITD Domains table |

## NWP Delta

**ITD (Intel Thermal Director) is fully supported on NWP** — no changes from DMR.

- ITD applies voltage correction to domains (CCF, UCIe) using RC register voltage offset
- `RESCTRL_CR_VOLTAGE_OFFSET[0].offset` mechanism unchanged
- VccInf temperature reporting for ITD unchanged
- Fuses (slope1, slope2) unchanged from DMR/GNR
- ITD is not exposed to customers — no enable/disable feature; can only be "disabled" by modifying slope fuses

### Validation Impact
- Same ITD test cases apply
- Verify voltage offset via RC register on NWP CBB

## Legacy (Human-Curated Reference)

### Architecture Summary

ITD (Inverse Temperature Dependence) dynamically compensates voltage for silicon temperature variations. Without dynamic compensation, a fixed worst-case guardband wastes significant power.

**Theory**: Transistor delay is a function of carrier mobility (↓ with temp) and threshold voltage (↓ with temp). These have opposing effects — the crossover point (ITD vs TTD regime) is determined per-process via post-Si fusing.

- **Positive compensation (ITD)**: Cold silicon needs higher voltage (mobility up, Vth up → net delay increase)
- **Negative compensation (TTD/NITD)**: Hot silicon below Vcross needs lower voltage (optional PnP optimization, gated by `TRUE_TD_ENABLE` / `NEGATIVE_ITD_DISABLED` fuse)

#### Hierarchical ITD Control

ITD is distributed across three controllers matching DMR's hierarchical thermal architecture:

```
┌─────────────────────────────────────────────────────────┐
│  Root PrimeCode (iMH)                                   │
│  • VCCINF ITD (MBVR, Dispatcher WP → SVID Controller)   │
│  • VCCCFCMEM_W/E ITD (FIVR, Dispatcher + RC V_OFFSET)   │
│  • VCCCFCIO ITD (FIVR, Dispatcher + RC V_OFFSET)         │
│  • VCCFIXDIG_* ITD (FIVR, RC V_OFFSET)                  │
│  • VCCUCIEA_* ITD (FIVR, RC V_OFFSET)                   │
│  Uses RC RESCTRL_CR_VOLTAGE_OFFSET.OFFSET for all FIVR   │
└──────────────────────┬──────────────────────────────────┘
                       │ HPM: SOCKET_THERMAL (min temp from CBB)
                       ▼
┌─────────────────────────────────────────────────────────┐
│  CBB PCode                                               │
│  • VCCR (CCF/Ring) ITD — 4 top-die shadows × 2 FIVRs    │
│  • VCCC2IA (UCIe D2D) ITD — Fixed ~0.7V target           │
│  • Sends CBB min temp to Root for VCCINF ITD              │
└──────────────────────┬──────────────────────────────────┘
                       │ PMSB CRs, PMA CRs
                       ▼
┌─────────────────────────────────────────────────────────┐
│  Core ACP (Acode) — Autonomous                           │
│  • VCCCORE ITD — Per-core, interrupt + periodic           │
│  • VCCMLC_SSA ITD — Same fuses as core (may split later)  │
│  • DTS DTD non-sticky alerts for fast recalc (~30-60μS)   │
└─────────────────────────────────────────────────────────┘
```

#### ITD Domains

| Rail | VR Type | Controller | Domain | GV | Dual-Slope | Notes |
|------|---------|-----------|--------|-----|-----------|-------|
| VCCR_(EN,ES,WN,WS) | FIVR | CBB PCode | CCF/Ring | GV | Yes | 4 top-die shadows × 2 FIVRs = 8 domains |
| VCCCORE_i | FIVR | Core ACP (Acode) | Core | GV | Yes | Per-core autonomous, interrupt-based + periodic |
| VCCMLC_SSA_E/W | FIVR | Core ACP (Acode) | MLC SRAM | GV | Yes | Same ITD fuses as core (may split later) |
| VCCC2IA | FIVR | CBB PCode (Base) | UCIe D2D | Fixed | Yes | Fixed target 0.7V, 40mV pk-pk AC noise budget |
| VCCINF | MBVR | iMH PrimeCode | Infrastructure | Fixed | No | Shared rail — CBB sends min temp via `SOCKET_THERMAL` |
| VCCCFCMEM_W/E | FIVR | iMH PrimeCode | Memory fabric | GV | Yes | Dispatcher + RC V_OFFSET |
| VCCCFCIO | FIVR | iMH PrimeCode | IO fabric | GV | Yes | Dispatcher + RC V_OFFSET |
| VCCFIXDIG_E/W/MIO_* | FIVR | iMH PrimeCode | MC, DDR PHY, Accel | Fixed | No | Fused at Vhot — no ITD compensation |
| VCCUCIEA_NW/NE/SW/SE | FIVR | iMH PrimeCode | UCIe PHY Analog | Fixed | No | Fused at Vhot — no ITD compensation |
| **VCCFCFCAB** | FIVR | iMH PrimeCode | CAB (Customer Accelerator Block) | GV | TBD | **NWP-specific new domain.** MAS §3: "ITD on new digital domain [VCCFCFCAB]. [no change to ITD support on existing DMR rails]". Test cases: 22022458470 (FV), 22021974407 (PSS) |

#### 2-Slope ITD Algorithm

DMR uses a **2-line piecewise ITD** algorithm with a crossover point at `Vcross`:

```
# PrimeCode pseudo-code (applies to iMH-controlled rails)

for TEMP in DTS_DOMAIN_ARRAY:
    if (TEMP < FUSED_MIN_ACCURATE_TEMP): TEMP = FUSED_ITD_MIN_OVERRIDE_TEMP
    MAX_TEMP = MAX(TEMP, MAX_TEMP)
    MIN_TEMP = MIN(TEMP, MIN_TEMP)

# Temperature delta from cutoff
DELTA_TEMP_HOT  = FUSE.ITD_CUTOFF_TJ - MAX_TEMP
DELTA_TEMP_COLD = FUSE.ITD_CUTOFF_TJ - MIN_TEMP

# Voltage delta — select slope based on cutoff
CUTOFF_V  = (UNCOMPENSATED_V < FUSE.ITD_CUTOFF_V_X) ? FUSE.ITD_CUTOFF_V : FUSE.ITD_CUTOFF_V_2
DELTA_VOLT = CUTOFF_V - UNCOMPENSATED_V

# Select slope
ITD_SLOPE = (UNCOMPENSATED_V < FUSE.ITD_CUTOFF_V_X) ? FUSE.ITD_SLOPE_1 : FUSE.ITD_SLOPE_2

# Calculate voltage compensation
if (DELTA_VOLT > 0 AND DELTA_TEMP_COLD > 0):
    # ITD range: cold silicon, below cutoff voltage
    VOLT_COMP_VALUE = ITD_SLOPE * DELTA_VOLT * DELTA_TEMP_COLD

elif (FUSE.TRUE_TD_ENABLE AND DELTA_VOLT <= 0 AND DELTA_TEMP_HOT > 0):
    # TTD range: hot silicon but voltage above cutoff (negative compensation)
    VOLT_COMP_VALUE = ITD_SLOPE * DELTA_VOLT * DELTA_TEMP_HOT

else:
    # Above ITD_CUTOFF_TJ or TTD disabled — no compensation
    VOLT_COMP_VALUE = 0

# Ship to RC register (DMR change: no new WP, just voltage offset)
RESCTRL_CR_VOLTAGE_OFFSET.OFFSET = VOLT_COMP_VALUE
```

> **DMR Delta from Legacy**: DMR uses RC `RESCTRL_CR_VOLTAGE_OFFSET.OFFSET` register for voltage-only ITD corrections instead of creating new WPs through the Dispatcher. This simplifies the flow — any voltage-only change due to temperature goes directly to the RC register.

---

### Execution Flow

#### Per-Domain ITD Flows

##### ACP (VccCore) ITD — Core Autonomous

Core Acode manages ITD+TTD for VccCore FIVR autonomously with two paths:

1. **Periodic**: Temperature readout → voltage compensation folded into WP recalc (~300μS)
2. **Interrupt-based**: DTS DTD non-sticky alerts (bits 0,1) trigger recalc when temp crosses ±3°C threshold — response ~30-60μS

**DCM behavior**: Any core within a DCM raising an interrupt triggers recalc for both cores (shared PLL). If only voltage changes (no freq change), only the affected core changes V.

**MLC SSA**: Core uses same ITD fuses for both Core and MLCSSA FIVRs (may split later per TR).

##### CCF (VccRing) ITD — CBB PCode

Ring has 4 top-die shadows × 2 FIVRs = 8 independent FIVR domains. PCode calculates per-FIVR-domain ITD using each domain's local min/max DTS temperature, sharing the same ITD fuse set.

- Temp source: `PCU_CR_DTS_TEMP_CCF[N:0]` — each FIVR area has 2 DTS instances
- Fuses: `RING_ITD_CUTOFF_V/V2`, `RING_ITD_SLOPE/SLOPE2`, `ITD_CUTOFF_TJ`, `TRUE_TD_ENABLE`

##### UCIe (VCCC2IA) ITD — CBB PCode

UCIe D2D Phy requires fixed voltage ~0.7V with 40mV pk-pk AC noise budget at ≤16Gb/s.

- Temp source: `PCU_CR_DTS_TEMP_SOC(1/2)_CR[1:0]` (UCIe/VCCC2IA diodes)
- Fuses: `D2D_ITD_CUTOFF_V/V2`, `D2D_ITD_SLOPE/SLOPE2`, `ITD_CUTOFF_TJ`
- **Boot ITD**: At UCIe MB bringup (PH2.40), PCode reads UCIe temps, calculates one-time ITD before D2D training. After training, reverts to worst-case until periodic loop starts (saves ~11.7% UCIe power).
- **DMR A0 bugfix** (HSD [22021556158](https://hsdes.intel.com/appstore/article/#/22021556158)): D2D training errors from VCCIO DVFS → workaround: fixed boot voltage with ITD guardband baked in, bypass DVFS handshake, enable timer-based periodic retraining

##### Inf (VccInf) ITD — iMH PrimeCode

- Only MBVR where ITD occurs in DMR is VccInf
- Root IMH alone does the ITD correction using Dispatcher WP → SVID Controller
- Needs min temperature across all dies → CBB sends min temp via `SOCKET_THERMAL` HPM
- VCCINF is non-GV (fixed-frequency) — baseline voltage from `ACTIVE_VID` fuse

##### VCCCFCMEM / VCCCFCIO ITD — iMH PrimeCode

- GV-supported FIVR rails, controlled by Dispatcher + RC `RESCTRL_CR_VOLTAGE_OFFSET.OFFSET`
- Dual-slope ITD fuse support
- PrimeCode checks voltage against `VMAX` for near-TDP guard

##### VCCFIXDIG / VCCUCIEA ITD — iMH PrimeCode

- Fixed-frequency FIVR rails
- **Fused at Vhot — no ITD compensation expected** (ITD_SLOPE = 0 in production fusing)
- Test case verifies fuse checkout confirms zero slope

#### ITD Flow at Boot / Reset

| Phase | ITD State | Notes |
|-------|-----------|-------|
| Reset exit (before periodic) | Worst-case fixed ITD | Safe temp: `MIN_TEMPERATURE` for cold, `ITD_CUTOFF_TJ` for hot |
| PH1.2 (DTS fuse pull) | DTS enabled, thermtrip active | No ITD yet — boot voltage includes static guardband |
| PH2.40 (UCIe MB training) | One-time ITD calc from actual temp | Saves 11.7% UCIe power; reverts to worst-case after training |
| PH2.52+ (slow loop starts) | Dynamic ITD active | All domains track temp periodically |
| PH3-5 (Core reset exit) | ACP ITD starts | Core Acode ITD/TTD active after config complete |
| Reset entry | Worst-case ITD set before PCode reset | Safe for next boot |
| PkgC6 | Same as active state | DTS stays alive in CBB C6; ITD updates via RC V_OFFSET |

##### PkgC6 × ITD Interaction

- Thermal telemetry flows in PkgC6 — PrimeCode computes ITD but does NOT cause wakes to apply it
- If ITD update arrives coincident with PkgC wake → RC may exit with "stale" WP, then applies updated Active WP after completing wake
- PkgC Entry WP voltage includes delta ITD between worst-case and boot-active:
  ```
  IDLE_VOLTAGE = VF-curve @ MIN_RATIO (or BOOT_VOLTAGE for fixed-freq)
  ITD_WORST_CASE = ITD @ coldest temperature for idle voltage
  ITD_ACTIVE_CASE = ITD @ post-boot temperature for idle voltage
  PKGC_ENTRY_WP_VOLTAGE = IDLE_VOLTAGE + (ITD_WORST_CASE - ITD_ACTIVE_CASE)
  ```

#### ITD Disable

| Method | Scope | Effect |
|--------|-------|--------|
| Set `ITD_SLOPE` + `ITD_SLOPE_2` fuses = 0 | Per-domain | Zero compensation for that domain |
| Set `ITD_CUTOFF_TJ` = 0 | All domains | No temperature delta → zero compensation |
| Set `NEGATIVE_ITD_DISABLED=1` / `TRUE_TD_ENABLE=0` | TTD only | Disables negative voltage compensation for hot silicon |
| OC Mailbox (Misc. Turbo Control 0x18/0x19) bit 3 | TTD only | Dynamic disable of negative ITD |
| `CORE_PMA_CR_CONFIG_10[TRUE_TD_EN]=0` | Core TTD only | ACP true TD disable |
| `CORE_PMA_CR_CONFIG_10[FAST_TEMPERATURE_MANAGEMENT_EN]=0` | Core ITD | Disables interrupt-based ITD (periodic-only remains) |

---

### Key Registers & Interfaces

#### RC Voltage Offset (DMR-specific ITD mechanism)

| Register | Description |
|----------|-------------|
| `RESCTRL_CR_VOLTAGE_OFFSET.OFFSET` | Per-RC voltage offset for ITD compensation. PrimeCode writes `VOLT_COMP_VALUE` directly instead of creating new WPs. See [RC HAS](https://docs.intel.com/documents/sysip_pm/resource_controller/TRM/TRM.html#voltage_offset) |

#### Core CRs (PCode → Core ACP Config)

| CR | Key Fields | Notes |
|----|------------|-------|
| `CORE_PMA_CR_RUNTIME_CONFIG_0` | ITD slopes/cutoffs, thermal params, BCLK freq | ITD/TTD config for Acode |
| `CORE_PMA_CR_CONFIG_10` | `TRUE_TD_EN[2]`, `FAST_TEMPERATURE_MANAGEMENT_EN[3]` | TTD enable, interrupt-based ITD enable |
| `EMTTM_ALGO_MISC` | `CONTROL_TEMP[7:0]` (S8.0) = eff_tj_max | Temperature target |

#### Temperature Sources per Domain

| Domain | Temp Source Register | DTS Type |
|--------|---------------------|----------|
| Core (VccCore) | Core PMA SHORT_TELEM (Domain0 min/max) | Gen2.6 |
| MLC SSA | Core PMA SHORT_TELEM (Domain1 min/max) | Gen2.6 |
| CCF (VccR) | `PCU_CR_DTS_TEMP_CCF[N:0]` | Gen1 (puller) |
| UCIe (VCCC2IA) | `PCU_CR_DTS_TEMP_SOC(1/2)_CR[1:0]` | Gen1 (puller) |
| Inf (VccInf) | CBB `SOCKET_THERMAL` HPM → iMH min temp | Gen1 (aggregated) |
| CFCMEM/CFCIO | iMH DTS via Resource Adapters | Gen1 (puller) |
| FIXDIG/UCIEA | iMH DTS via Resource Adapters | Gen1 (puller) |

#### HPM Messages (ITD-Relevant)

| Message | Direction | ITD Purpose |
|---------|-----------|-------------|
| `SOCKET_THERMAL` | CBB → Root | CBB min temp → used by iMH for VccInf ITD |
| `B2P_EXCHANGE` (0xAC) | Root → CBB | OC TjMax offset — affects ITD_CUTOFF_TJ baseline |

#### DTS-to-Rail Mapping (IMH1 — Key Rails)

| DTS Name | RC | Rails Covered |
|----------|----|---------------|
| `cgu_dts` | RC_CFCMEM_EW | VCCINF only |
| `dts_ddr_a/b/c/d` | RC_MEM_W/E | VCCCFCMEM_W/E, VCCFIXDIG_E/W |
| `dts_catile_a/b/c/d` | RC_CFCIO | VCCCFCIO, VCCINF |
| `dts_center` | RC_CFCIO | VCCCFCIO |
| `dts_ucie_a/b/c/d` | RC_CFCMEM_EW | VCCCFCMEM_W/E, VCCUCIEA_NW/NE/SW/SE |
| `dts_imh_ucie` | RC_CFCMEM_EW | VCCCFCMEM_W/E, VCCUCIEA_SW/SE |
| `dts_miomisc_uio_0/1/2` | RC_MIO_EW | VCCFIXDIG_MIO_1/3/4 |
| `dts_acc_misc` | RC_CFCIO | VCCFIXDIG_E |

---

### Key Fuses

| Fuse | Width | Scope | Format | Description |
|------|-------|-------|--------|-------------|
| `{DOMAIN}_ITD_SLOPE` | 5 | Die | U-8.13 | Slope1 for lower voltage range (°C/V) |
| `{DOMAIN}_ITD_SLOPE_2` | 5 | Die | U-8.13 | Slope2 for higher voltage range (°C/V) |
| `{DOMAIN}_ITD_CUTOFF_V` | 9 | Die | U1.8 | Cutoff voltage for slope1 line |
| `{DOMAIN}_ITD_CUTOFF_V_2` | 9 | Die | U1.8 | Cutoff voltage for slope2 line (used when V > V_X) |
| `{DOMAIN}_ITD_CUTOFF_V_X` | 9 | Die | U1.8 | Crossover voltage between slope1 and slope2 |
| `ITD_CUTOFF_TJ` | 7 | Die | U7.0 | Reference temp — no compensation at this temp |
| `ITD_VOLTAGE_SLOPE_ABOVE_CUTOFF_TJ` | — | Die | U-6.12 | Slope for V increase above ITD_CUTOFF_TJ (shared all domains, ~2.5mV/°C) |
| `MIN_ACCURATE_TEMP` | 7 | Die | S6.0 | Below this, DTS unreliable — use `ITD_MIN_OVERRIDE_TEMP` |
| `ITD_MIN_OVERRIDE_TEMP` | 7 | Die | S6.0 | Temperature to use when DTS below `MIN_ACCURATE_TEMP` |
| `TRUE_TD_ENABLE` | 1 | Die | — | If 1, enables TTD (negative voltage compensation for hot silicon) |
| `NEGATIVE_ITD_DISABLED` | 1 | Die | — | If 1, disables negative ITD (TTD) |
| `ENABLE_TCONTROL_PROGRAMMING` | 1 | Die | — | If 1, enables DTS_CONFIG3 register |
| **Per-Domain Fuses** | | | | |
| `IA_ITD_CUTOFF_V/V2`, `IA_ITD_SLOPE/SLOPE2` | — | Die | — | Core-specific (Acode) |
| `RING_ITD_CUTOFF_V/V2`, `RING_ITD_SLOPE/SLOPE2` | — | Die | — | CCF ring-specific |
| `D2D_ITD_CUTOFF_V/V2`, `D2D_ITD_SLOPE/SLOPE2` | — | Die | — | UCIe D2D-specific |

---

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS (CBB ITD) | [DMR CBB ITD HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/ITD/ITD.html) | Primary CBB ITD spec — 2-slope algorithm, CCF/UCIe domains |
| HAS (DMR SOC Thermal) | [DMR SOC Thermal](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | iMH ITD flow, DTS mapping tables, PkgC6 × ITD, MBVR ITD |
| HAS (CBB Thermal) | [DMR CBB Thermal Management](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) | ACP ITD overview, boot ITD sequence |
| HAS (RC V_OFFSET) | [RC HAS VOLTAGE_OFFSET](https://docs.intel.com/documents/sysip_pm/resource_controller/TRM/TRM.html#voltage_offset) | RC register used by ITD in DMR |
| HAS (ACP Core) | [Autonomous Core Perimeter PM](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html#acp-20-autonomous-thermal-management) | Core EMTTM/ITD/TTD |
| HAS (CBB Thermal Intg) | [DMR CBB Thermal Integration](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/DMR%20CBB%20Thermal%20Integration%20HAS/DMR%20CBB%20Thermal%20Integration%20HAS.html) | DTS topology, diode mapping |
| MAS (NWP iMH DTS) | [NWP iMH SOC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#dtsthermal-diode-and-thermtrip-chaining) | NWP iMH DTS placement + thermtrip chaining |
| FAS (Pcode Thermal) | [Pcode Thermal FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/Thermals/Thermal%20Management_FAS.html) | Pcode implementation |
| HSD | 22021556158 | DMR A0 UCIe ITD bugfix (D2D training DVFS) |

---

#### Validation Approach (by Test Case)

| Test | What to Verify |
|------|----------------|
| **Fuse checkout** (22022421521) | Read all ITD fuses (`{DOMAIN}_ITD_SLOPE/SLOPE2/CUTOFF_V/V2/V_X`, `ITD_CUTOFF_TJ`, `TRUE_TD_ENABLE`, `MIN_ACCURATE_TEMP`). Confirm non-zero slopes for active domains, zero slopes for domains fused at Vhot (VCCFIXDIG, VCCUCIEA). |
| **ACP (VccCore)** (22022421522) | Inject temperature change → verify Acode recalculates `VOLT_COMP_VALUE` via interrupt path (~30-60μS) and periodic path (~300μS). Check `RESCTRL_CR_VOLTAGE_OFFSET`. Verify DCM behavior: interrupt on one core triggers recalc for both. |
| **CCF (VccRing)** (22022421524) | Apply thermal load to CCF → verify per-FIVR-domain ITD compensation. Check 8 independent FIVR domains track their local DTS independently. Verify `PCU_CR_DTS_TEMP_CCF[N:0]` → V_OFFSET. |
| **Core MLC SSA** (22022421525) | Verify MLC SSA FIVR gets ITD compensation using same fuse set as Core. Check Domain1 SHORT_TELEM temp feeds into compensation. |
| **ITD disable** (22022421528) | Set `ITD_SLOPE` = 0 → verify zero compensation. Set `TRUE_TD_ENABLE` = 0 → verify only positive (cold) ITD remains. Verify `CORE_PMA_CR_CONFIG_10` disable controls. |
| **ITD during reset** (22022421534) | Verify worst-case ITD applied at boot before periodic loop. Check UCIe one-time ITD at PH2.40. Verify safe voltage at reset entry. |
| **Inf (VccInf)** (22022421535) | Verify iMH reads CBB min temp from `SOCKET_THERMAL` HPM → calculates MBVR ITD → issues Dispatcher WP to SVID Controller. |
| **UCIe (VCCC2IA)** (22022421536) | Verify fixed-voltage domain ITD around 0.7V target. Check D2D training phase one-time ITD. Verify PH2.40 boot ITD flow. |
| **VCCCFCIO** (22022421538) | Verify iMH ITD for IO fabric FIVR using `dts_catile_*` and `dts_center` DTS inputs via RC V_OFFSET. |
| **VCCCFCMEM** (22022421540) | Verify iMH ITD for memory fabric FIVR using `dts_ddr_*` and `dts_ucie_*` DTS inputs. Dual-slope supported. |
| **VCCFIXDIG** (22022421542) | Verify fused at Vhot → ITD_SLOPE = 0 → no compensation. This is expected-zero test. |
| **VCCUCIEA** (22022421546) | Verify fused at Vhot → ITD_SLOPE = 0 → no compensation. This is expected-zero test. |
| **VCCFCFCAB** (22022458470, 22021974407) | Verify FIVR AB rail ITD. NWP-specific rail — check NWP fuse spec for domain definition. |

---

### Related Sightings

| HSD | Description |
|-----|-------------|
| 22021556158 | DMR A0: D2D training errors from VCCIO DVFS. Workaround: fixed boot voltage with ITD guardband, bypass DVFS handshake, timer-based periodic retraining. |

---

### NWP Delta

> **Items to verify for NWP** (not yet confirmed — check NWP HAS when available):

| Area | Question | DMR Baseline |
|------|----------|--------------|
| ITD domains | NWP NIO replaces iMH — who controls VCCINF/CFCMEM/CFCIO ITD? Same RC V_OFFSET mechanism? | DMR: iMH PrimeCode uses `RESCTRL_CR_VOLTAGE_OFFSET.OFFSET` |
| **VCCFCFCAB** | **Confirmed** — NWP PM MAS §3 explicitly lists "ITD on new digital domain [VCCFCFCAB]" as a supported NWP PM feature. CAB = Customer Accelerator Block (NIO die). Controlled by iMH PrimeCode via FIVR + RC V_OFFSET (same mechanism as VCCCFCMEM/VCCCFCIO). DTS sources and fuse set are NWP-specific — check NWP thermal fuse spec and `ThermData.xlsx` for DTS mapping. | DMR: Does not exist — NWP-specific new rail |
| CCF multi-FIVR | NWP has 2 CBBs → fewer CCF FIVR domains. Same 4-shadow × 2-FIVR? | DMR: 4 top-die shadows × 2 FIVRs = 8 domains per die |
| UCIe ITD boot | Same D2D MB training ITD handshake? Same 0.7V target? | DMR: One-time ITD at PH2.40, 0.7V, 40mV AC budget |
| UCIe A0 bugfix | Applicable to NWP A0? (D2D training VCCIO DVFS issue) | DMR A0: HSD 22021556158 |
| ITD fuse set | Same slopes/cutoffs? NWP process may differ | DMR: 2-slope per domain, shared ITD_CUTOFF_TJ |
| VccInf ITD | NIO replaces iMH — still Dispatcher WP → SVID? | DMR: iMH controls, uses CBB min temp from SOCKET_THERMAL |
| DTS mapping | NWP iMH DTS topology — same DTS-to-rail mapping? | DMR: See IMH1/IMH2 mapping tables in SOC Thermal HAS |
| Dual-slope enablement | Which NWP domains get dual slope? | DMR: CCF, CFCMEM, CFCIO, D2D have dual slope; FIXDIG/UCIEA have none |
| Core ITD fuses | Same `IA_ITD_CUTOFF_V/V2`, `IA_ITD_SLOPE/SLOPE2`? | DMR: Shared across all CCPs |
