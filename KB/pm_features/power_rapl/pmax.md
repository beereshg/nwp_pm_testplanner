# Power/RAPL > PMAX (Multi-Threshold PMax Detection & PL4)

> **Status**: Restructured — NWP delta enriched from MCP HAS/MAS query
> **Parent**: [Power / RAPL](power_rapl_main.md)

## Baseline (DMR)

PMax is a **hardware overcurrent/overvoltage protection** circuit that detects when socket power exceeds Pmax.App (the maximum power for realistic applications). It senses FIVR input-domain VccIN voltage within hundreds of nanoseconds to microseconds and triggers immediate frequency throttling to reduce power to a safe level (Psafe).

## HW Touchpoints

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| | | | | |

## FW Touchpoints

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| | | | | |

## OS Interfaces

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| | | | | |

## NWP Delta

**PMAX (Multi-Threshold PMAX Detector) is supported on NWP** — reused from DMR.

- Multi-threshold PMAX detector logic with fast droop protector is reused
- Di/Dt slope detector mechanism unchanged
- PMAX detection and enforcement by Punit/Pcode

### Validation Impact
- Same PMAX test cases apply
- Verify PMAX thresholds in NWP single-NIO topology

## Legacy (Human-Curated Reference)

### Architecture Summary

PMax is a **hardware overcurrent/overvoltage protection** circuit that detects when socket power exceeds Pmax.App (the maximum power for realistic applications). It senses FIVR input-domain VccIN voltage within hundreds of nanoseconds to microseconds and triggers immediate frequency throttling to reduce power to a safe level (Psafe).

#### Key DMR Differentiators from GNR
- **Dual VCCIN**: DMR-AP has 2 independent VRs (VCCIN_0 for North iMH + CBB0/1, VCCIN_1 for South iMH + CBB2/3) → 2 independent PMax detectors, one per iMH
- **Per-iMH action**: Each iMH takes PMax action independently based on its own VR sense — only dies on the triggered VCCIN rail throttle
- **Multi-threshold (MT)**: 4 fuse-programmable trip thresholds — 3 filtered VccIN levels for MT PMax + 1 for Fast Droop Detection (FDD)
- **Individual frequency ceilings**: Primecode calculates ceilings for core, CBB fabric, iMH IO fabric, and iMH Memory fabric per domain
- **DMR-SP special**: Single VCCIN on IMH_P, IOH die connected via direct D2D wires (Option 2a POR) for fast throttle — not HPM

#### PMax Trigger Topology (DMR-AP)
```
VCCIN_0 VR ──→ PMax Detector (iMH_P) ──→ CBB0, CBB1  (hard/soft throttle)
                     │                        │
                     └── PMAX_TRIGGER_IO GPIO ─┘ (output to platform if enabled)

VCCIN_1 VR ──→ PMax Detector (iMH_S) ──→ CBB2, CBB3  (hard/soft throttle)
                     │                        │
                     └── PMAX_TRIGGER_IO GPIO ─┘

External PMAX_TRIGGER_IO (input) ──→ OR'd with both PMax detectors → both iMHs act
```

#### Throttle Types

| Level | Wire | Threshold | Action |
|-------|------|-----------|--------|
| **Hard Throttle** | PmaxTrigXnnnH (Vtrip 0) | Lowest voltage = highest overcurrent | Instant fast-throttle to Psafe via D2D wire; 50ns response. Core clock gating + freq clamp |
| **Soft Throttle L1** | PmaxTrigL1XnnnH (Vtrip 1) | Medium voltage | PWM proportional throttle via D2D YY_FAST_THROTTLE_IN_1 |
| **Soft Throttle L2** | PmaxTrigL2XnnnH (Vtrip 2) | Highest voltage = softest | PWM proportional throttle, lightest duty cycle |
| **FDD** | FDDTrig | Fast Droop Detection OV/UV | Architectural throttle (not clock throttle). Uses separate throttle aggregator path |

#### PL4 Overview

PL4 is the **hard power limit** that must never be exceeded — distinct from PMax detection (which reacts after the fact). PL4 allows customers to dynamically set a maximum instantaneous power limit. PrimeCode converts the PL4 power into voltage offsets for PMax detector trip points, effectively raising them to trigger earlier and prevent exceeding PL4.

$$P_{L4} = P_{Vccin} + P_{nonVccin}$$
$$P_{L4,Vccin0} = (PL4 - P_{nonVccin}) \times FUSED\_PL4\_SCALE\_FACTOR\_IMH0$$

#### FIVR Energy Reporting Overview

Fine-grained per-domain energy reporting for both FIVRs (on CBB and iMH) and MBVRs. Uses HVM-calibrated $I_{in}$ telemetry per FIVR domain with VRCI I_IN_ACCUMULATOR/I_IN_NUM_SAMPLES registers. Internal-only feature (disabled at PRQ via `DOMAIN_ENERGY_REPORTING_ENABLE` fuse) due to Mistletoe PRT security concerns.

Key equation:
$$I_{in,FIVR} = I_{IN,AVG} \times \frac{VR\_MAX\_IOUT}{255} \times 2^{I\_OUT\_EXP} \text{ mA}$$
$$P_{domain} = I_{in,FIVR} \times V_2 \quad\text{where}\quad V_2 = V_1 - I_1 \times R_{LL}$$

---

### Execution Flow

#### PMax Hard Throttle (per-iMH)

1. **Post-reset init**: Each iMH PrimeCode calculates Psafe frequency ceilings for all domains using power-frequency profile fuses:
   ```
   PSAFE_POWER = (1 + TDP_TO_PSAFE_MULTIPLIER) × TDP_POWER
   IA_FREQ_CEILING[cdyn] = EXTRAPOLATION(PF_CURVE, PSAFE_POWER)
   MEMCFC_FREQ_CEILING = EXTRAPOLATION(PF_CURVE, PSAFE_POWER)
   IOCFC_FREQ_CEILING = EXTRAPOLATION(PF_CURVE, PSAFE_POWER)
   CBBCFC_FREQ_CEILING = EXTRAPOLATION(PF_CURVE, PSAFE_POWER)
   ```
2. PrimeCode sends Psafe ceilings to leaf CBBs via HPM `PMAX_FREQUENCY_LIMIT` (RR=1)
3. **Hard PMax triggers**: Punit drives D2D `FAST_THROTTLE_IN_0` wire → all associated CBBs instantly clock-throttle cores
4. PrimeCode sends `PMAX_INST_PWR_CONTROLLED_FREQ_LIMIT` HPM (RR=1) to leaf CBBs with Psafe freq ceilings
5. CBB Pcode enforces frequency ceiling on cores and fabric
6. CBB Pcode ACKs with `PMAX_INST_PWR_CONTROLLED_FREQ_LIMIT` (RR=0)
7. iMH PrimeCode de-asserts D2D fast throttle wire
8. PrimeCode clears semaphores: `IO_THERM_INDICATIONS.GLOBAL_PMAX_SEMAPHORE=0`, `GLOBAL_PMAX_RESET=1`
9. PrimeCode clears throttle: `IO_THROTTLE_INDICATIONS.THROTTLE_1_SEMAPHORE=0`, `THROTTLE_1_RESET=1`
10. After 500μs, soft throttle algorithm kicks in for frequency walk-back

#### PMax Soft Throttle (per-iMH)

Two parallel flows:
1. **Hardware flow**: Punit samples PmaxTrigL1/L2 signals, generates PWM D2D signal `YY_FAST_THROTTLE_IN_1`. Punit maintains `IO_ACCUMULATED_THROTTLE_CYCLES` counter. If counter > `IO_THROTTLE_FP_THRESHOLD` → fastpath fires
2. **Firmware flow**: PrimeCode reads accumulated throttle cycles. Algorithm:
   ```
   ratio = IO_ACCUMULATED_THROTTLE_CYCLES / ELAPSED_TIME
   if ratio <= THRESHOLD_1 (default 5%):
       if UP_HYSTERESIS_TIMER expired (default 500μs):
           freq_ceiling += FREQ_INC (default 1)  # walk back
   if ratio > THRESHOLD_2 (default 8%):
       if DOWN_HYSTERESIS_TIMER expired (default 500μs):
           freq_ceiling -= FREQ_DEC (default 1)  # penalize more
   ```
3. New freq ceiling sent to CBBs via HPM `PMAX_INST_PWR_CONTROLLED_FREQ_LIMIT`

#### PL4 Dynamic Change Flow

1. BIOS writes PL4 via TPMI `Power_Limit_Control4` register → PrimeCode fastpath
2. Root iMH sends `PL4_CONFIG` HPM to secondary iMH
3. Enter PL4 safe zone: all domains to min frequency. Wait for HPM ACKs from all leaf dies
4. Each iMH calculates its share: $PL4_{Vccin0} = (PL4 - P_{nonVccin}) \times SCALE\_FACTOR\_IMH0$
5. Calculate dynamic trip current: $I_{trip} = \frac{V_{ccin} - \sqrt{V_{ccin}^2 - 4 R_{ll} P_{Vccin}}}{2 R_{ll}}$, clipped to IccMaxApp fuse
6. Calculate voltage offset: $V_{offset} = (IccMaxApp_{fused} - I_{cc,trip}) \times R_{ll}$
7. Convert offsets to DAC encoding: $V_{encoding} = V_{offset} / 0.002$ (2mV resolution)
8. Write PMAX_CONFIG1 register with MT0/MT1/MT2/FDD offsets
9. Frequency walk-back to appropriate limits

#### CBB Throttle Mechanism

- **PMax/MT-PMax**: Clock throttling on cores via throttle aggregator
- **FDD**: Architectural throttling (different from clock throttle)
- Controlled by `bgr_infra_N_fuse.bgr_infra_N_fuse_throttle_agg_pick_fast_throttle_output = 0x1` and `..._pick_droop_throttle_output = 0x1` (N=0-3)

---

### Key Registers & Interfaces

#### Punit Registers (per iMH)

| Register | Key Fields | Description |
|----------|-----------|-------------|
| IO_THROTTLE_PWM_CONFIG | THROTTLE_TIMER_PERIOD[9:0], FAST_PMAX0_MAPPING[12:10], FAST_PMAX1_MAPPING[15:13] | PWM throttle configuration — timer period and PMax signal→throttle level mapping |
| IO_THROTTLE_PWM_LENGTH | THRT_LEN_0[9:0], THRT_LEN_1[19:10], THRT_LEN_2[29:20] | Duration of throttle for each PWM level in X1 clocks. THRT_LEN_2 > THRT_LEN_0 |
| IO_THROTTLE_FP_THRESHOLD | THROTTLE_FP_THRESHOLD[31:0] | Fastpath asserted when IO_ACCUMULATED_THROTTLE_CYCLES exceeds this (default 0x40) |
| IO_MT_PMAX_CONTROLLER_CONFIG | ENABLE_SIRP_MT_PMAX_THROTTLE[0], DISABLE_MT_PMAX[2], THROTTLE_THRESHOLD_FP_ENABLE[3], LPF_LENGTH[6:4] | Master enable/disable for MT PMax + SIRP + fastpath |
| IO_THROTTLE_SIGNALS_OVERRIDE | THROTTLE_1_HW_DISABLE[9], THROTTLE_1_HW_INJECT[25], LOCAL_PMAX_PWM_HW_INJECT[28], GLOBAL_PROCHOT_HW_INJECT[31] | DFx inject/disable for PMax hard throttle, soft throttle, prochot |
| IO_ACCUMULATED_THROTTLE_CYCLES | ACCUM_THROTTLE_CYCLES[31:0] | Accumulated X1 clocks with PWM throttle asserted. Cleared by Pcode |
| IO_FASTPATH_THERMAL | THROTTLE_FILTERED_RISE_EVENTS_1 | PMax hard throttle detection bit (filtered rise events) |
| IO_THROTTLE_INDICATIONS | THROTTLE_1_SEMAPHORE, THROTTLE_1_RESET, THROTTLE_PWM | PMax event state machine control |
| IO_THERM_INDICATIONS | GLOBAL_PMAX_SEMAPHORE, GLOBAL_PMAX_RESET | Cross-die PMax coordination |

#### TPMI Registers (per iMH, TPMI_ID=0x3)

| Register | Bits | Access | Description |
|----------|------|--------|-------------|
| PMAX_HEADER | [7:0] INTERFACE_REVISION, [63:8] RSVD | RO | Version number |
| PMAX_STATUS | [31:0] PMAX_CONFIG_STATUS, [32] VALID | RO | Calibration error status populated by Punit after Phase 5 |
| PMAX_CONTROL | [6:0] PMAX_VTRIP_0_OFFSET (signed, 2mV resolution), [32] PMAX_GPIO_TRANSMITTER_ENABLE, [33] PMAX_GPIO_TRIGGER_ENABLE, [35:34] PMAX_DISABLE_MASK (00=enabled, 11=fully disabled), [63] LOCK | RW_L | BIOS-programmed PMax control per iMH |

#### PL4 TPMI Register (Power_Limit_Control4, idx 5)

| Field | Bits | Access | Description |
|-------|------|--------|-------------|
| PWR_LIM | [17:0] | RW_L | PL4 power limit (units per POWER_UNIT) |
| PWR_LIM_EN | [62] | RW_L | Enable/Disable PL4 |
| LOCK | [63] | RW_L | Lock until next reset |

#### PMAX_CONFIG1 (Punit IP register — PrimeCode writes)

| Bits | Field | Description |
|------|-------|-------------|
| 6:0 | MT0_OFFSET | Vtrip 0 offset (signed magnitude, 2mV/bit). Hard throttle threshold |
| 14:8 | MT1_OFFSET | Vtrip 1 offset (soft throttle L1) |
| 22:16 | MT2_OFFSET | Vtrip 2 offset (soft throttle L2) |
| 30:24 | FDD_OFFSET | Fast Droop Detection offset |

#### IA32_PACKAGE_THERM_STATUS (MSR 0x1B1, PCU CR 0xfb984)

| Bits | Access | Field | Description |
|------|--------|-------|-------------|
| 12 | RO/V | PMAX_STATUS | PMax detector asserted (up to 1ms delay). Deasserted when throttle released |
| 13 | RW/0C/V | PMAX_LOG | Sticky log — set on 0→1 transition of PMAX_STATUS. Write-0-to-clear |

#### HPM Messages

| Message | Direction | Key Fields |
|---------|-----------|------------|
| PMAX_FREQUENCY_LIMIT | Root iMH → CBBs | Psafe freq ceilings per Cdyn index + fabric limits (sent at init) |
| PMAX_INST_PWR_CONTROLLED_FREQ_LIMIT | Root iMH ↔ CBBs | Runtime freq ceilings: CDYN_INDEX_LIMIT[0-5], CBB_FABRIC_LIMIT, IMH_MEMORY_FABRIC_LIMIT, IMH_IO_FABRIC_LIMIT, RR bit |
| PL4_CONFIG | Root iMH → Leaf iMH | PL4 power value for secondary die (dual VCCIN) |

#### Fuses (Power-Frequency Profile)

| Fuse | Width | Scope | Description |
|------|-------|-------|-------------|
| SOCKET_VIRUS_POWER_FREQUENCY_CURVE_POWER_POINT_j | 10 | Pkg | Power points in PF curve (6 points, U10.0) |
| SOCKET_VIRUS_POWER_FREQUENCY_CURVE_IA_CDYN_INDEX_i_FREQUENCY_POINT_j | 7 | Pkg | IA ratio per Cdyn level (6×6=36 fuses, U7.0) |
| SOCKET_VIRUS_POWER_FREQUENCY_CURVE_MEMCFC_FREQUENCY_POINT_j | 7 | Pkg | Memory fabric ratio (6 fuses, U7.1) |
| SOCKET_VIRUS_POWER_FREQUENCY_CURVE_IOCFC_FREQUENCY_POINT_j | 7 | Pkg | IO fabric ratio (6 fuses, U7.2) |
| SOCKET_VIRUS_POWER_FREQUENCY_CURVE_CBBCFC_FREQUENCY_POINT_j | 7 | Pkg | CBB fabric ratio (6 fuses, U7.3) |
| TDP_TO_PSAFE_MULTIPLIER | 8 | Pkg | Psafe = (1 + this) × TDP. Default 0x33 (~0.4) |

#### Fuses (PL4-Specific)

| Fuse | Width | Scope | Description |
|------|-------|-------|-------------|
| SOCKET_PL4_POWER_DEFAULT | 10 | Pkg | Default PL4 power (U10) |
| SOCKET_NON_VCCIN_POWER | 13 | Per iMH | Non-VccIN partition power (U10.3) |
| SOCKET_PARTITION_ICC_MAX | 10 | Per iMH | Per-iMH IccMax (1A units) |
| SOCKET_PARTITION_ICC_MAX_APP | 10 | Per iMH | Per-iMH IccMax for application (1A units) |
| SCALING_FACTOR_VTRIP1 | 7 | Per iMH | Voffset1 = Voffset0 × (1 - SF1) |
| SCALING_FACTOR_VTRIP2 | 7 | Per iMH | Voffset2 = Voffset0 × (1 - SF2) |
| PL4_SCALE_FACTOR | 7 | Per iMH | PL4 power split N/S (U0.7, default 0x40 = 0.5) |

#### Interface Matrix

| Register/Parameter | MSR | IN_TPMI | OOB_TPMI | CSR | Fuses | MB |
|--------------------|-----|---------|----------|-----|-------|----|
| PMAX_CONTROL | — | RW_L (BIOS) | — | — | — | — |
| PMAX_STATUS | — | RO | — | — | — | — |
| PMAX_DISABLE_MASK | — | RW_L | — | — | — | — |
| PMAX_VTRIP_0_OFFSET | — | RW_L | — | — | — | — |
| PMAX_GPIO_TRANSMITTER_ENABLE | — | RW_L | — | — | — | — |
| PMAX_GPIO_TRIGGER_ENABLE | — | RW_L | — | — | — | — |
| Power_Limit_Control4 (PL4) | — | RW_L | — | — | — | — |
| IA32_PACKAGE_THERM_STATUS | RO/V (0x1B1) | — | — | RO/V (PCU CR) | — | — |
| IO_THROTTLE_SIGNALS_OVERRIDE | — | — | — | RW | — | — |
| IO_MT_PMAX_CONTROLLER_CONFIG | — | — | — | RW | — | — |
| IO_THROTTLE_PWM_CONFIG | — | — | — | RW | — | — |
| IO_ACCUMULATED_THROTTLE_CYCLES | — | — | — | RW | — | — |
| PMAX_CONFIG1 | — | — | — | RW (IP) | — | — |
| PF Curve fuses | — | — | — | — | RO (Pkg) | — |
| PL4 fuses | — | — | — | — | RO (per iMH) | — |
| PLR.MT_PMAX (coarse) | — | RW0C | RW0C | — | — | PLR_MAILBOX |
| PEM.MT_PMAX | — | — | PMT | — | — | — |
| PMAX_FREQUENCY_LIMIT HPM | — | — | — | — | — | HPM |
| PMAX_INST_PWR_CONTROLLED_FREQ_LIMIT HPM | — | — | — | — | — | HPM |

---

### FIVR Energy Reporting

#### Per-Die FIVR Domains

| Die | FIVR Domains | Grouping |
|-----|-------------|----------|
| CBB | 32× VCCCORE | 2 groups |
| CBB | 8× VCCR | 1 group |
| CBB | 1× VCCMLC | 1 |
| CBB | 1× VCCC2IA (D2D) | 1 |
| iMH | 1× VCCFIXDIG_W, 1× VCCFIXDIG_E | 1 each |
| iMH | 1× VCCFIXDIG_MIO_1/3/4 | 1 each |
| iMH | 2× VCCUCIeA [NW/NE], 2× [SW/SE] | 1 each pair |
| iMH | 2× VCCCFCMEM_W/E | 1 |
| iMH | 1× VCCCFCIO | 1 |

#### MBVR Rails (iMH — IMON via SVID, ~1ms interval)
VCCANA, VCCDDR_HV, VCCINF, VCCIN_EHV, VCCFA_EHV

#### VR Type Equations

| VR Type | Power Equation | Examples |
|---------|----------------|----------|
| FIVR | $P_{in} = I_{in} \times (V_1 - I_1 \times R_{LL})$ | VCCCORE, VCCR, VCCFIXDIG |
| MBVR w/DC_LL | $P_{in} = I_1 \times (V_1 - I_1 \times R_{LL})$ | VCCIN_EHV, VCCDDR_HV |
| MBVR w/o DC_LL | $P_{in} = I_1 \times V_1$ | VCCANA, VCCINF, VCCFA_EHV |

#### Scalars per FIVR Domain (I_OUT_EXP=10 for all DMR FIVRs)

| Domain | Die | MAX_I_OUT |
|--------|-----|-----------|
| VCCFIXDIG_E | IMH | 22 |
| VCCFIXDIG_W | IMH | 27 |
| VCCUCIeA_NW/NE | IMH | 13 |
| VCCUCIeA_SW/SE | IMH | 18 |
| VCCFIXDIG_MIO_1/3/4 | IMH | 18 |
| VCCCFCMEM_E/W | IMH | 45 |
| VCCCFCIO | IMH | 91 |
| VCCMLC | CBB | 13 |
| VCCC2IA | CBB | 13 |
| VCCR | CBB | 31 |
| VCCCORE | CBB | 40 |

#### Data Exposure
- CBB FIVRs: Pcode exposes via PMT (OOB-MSM). See [CBB Telemetry HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html)
- iMH FIVRs + MBVRs: PrimeCode exposes via PMT (OOB-MSM)
- V₂ communicated to CBBs via HPM `RAPL_PERF_LIMIT.FIVR_INPUT_VOLTAGE`
- Feature disabled at PRQ via `DOMAIN_ENERGY_REPORTING_ENABLE` fuse (internal-only, security)

---

### BIOS Configuration

#### PMax TPMI Control (per iMH instance)
BIOS writes PMAX_CONTROL via TPMI ID=0x3:
- **PMAX_VTRIP_0_OFFSET[6:0]**: Signed, 2mV resolution. Adjusts hard throttle trip point
- **PMAX_GPIO_TRANSMITTER_ENABLE[32]**: CPU PMax event → platform GPIO assertion
- **PMAX_GPIO_TRIGGER_ENABLE[33]**: Platform GPIO → CPU PMax trigger (external input)
- **PMAX_DISABLE_MASK[35:34]**: `00`=full MT PMax, `01`=disable hard only, `10`=disable soft only, `11`=fully disabled

On TPMI write → Pcode fastpath:
- Copies TRIGGER_ENABLE/TRANSMITTER_ENABLE to PCU_CR_PMAX_GPIO_TRIGGER
- Sets `PMAX_CONFIG[LOCK] = NOT(DISABLE_MASK[0] AND DISABLE_MASK[1])`

#### Dual VCCIN Trip Level Adjustment
BIOS reads both VCCIN loadlines and independently programs iMH0/iMH1 PMAX_CONTROL offsets. Different platform loadlines → different offsets per iMH.

---

### Cross Products

| Feature | PMax Impact |
|---------|-------------|
| **PkgC** | PMax detector disabled during PkgC entry, re-enabled during exit. See [PkgC HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Idle_Flow/DMR_PkgC.html#pmax-detector) |
| **Fast RAPL** | PrimeCode/Pcode always picks min(PMax ceiling, Fast RAPL ceiling) |
| **SIMPL** | PrimeCode/Pcode always picks min(PMax ceiling, SIMPL ceiling) |
| **RACL** | Independent — RACL is per-iMH local, PMax is per-iMH local. Both can limit simultaneously |
| **Thermals/Prochot** | Soft throttle can occur while Prochot is in progress — test both simultaneously |
| **Fabric GV** | Soft throttle can occur during Fabric GV transitions |
| **Fast VMode** | Legacy IccMax protection via MBVR current-limiting mode — no PrimeCode changes needed, purely platform |

---

### DMR-SP PMax Connectivity

**POR Option 2a**: Direct D2D wire from IMH root to IOH leaf.
- IMH_P is PMax root (has VccIN), IOH is PMax leaf (no VccIN)
- `o_punit_interdie_pmax_hard_throttle` and `o_punit_interdie_pmax_pwm_throttle` wires from IMH to IOH
- Fast and effectual — conforms to Xeon multi-die PMax architecture (GNR, CPX)
- IOH power reduction needed to reach Psafe: ~41.8W dynamic (75% TDP total reduction with IOH)

Feature HSD: [22020996043](https://hsdes.intel.com/appstore/article/#/22020996043)

---

### Source References

#### Primecode (iMH-level firmware)
| # | File | Description |
|---|------|-------------|
| 1 | `src/flow/pmax/pmax_common/v2_0/pmax_common.cpp` | PMax common flow — Psafe calculation, frequency ceiling computation |
| 2 | `src/flow/pmax/pmax_common/v2_0/pmax_common_flow.cpp` | PMax flow orchestration — hard/soft throttle state machine |
| 3 | `src/flow/pmax/pmax_common/v2_0/pmax_health.cpp` | PMax health — OV/UV detection monitoring |
| 4 | `src/flow/pmax/pmax_compute/v1_0/pmax_compute.cpp` | PMax compute-domain flow (core freq ceilings) |
| 5 | `src/flow/pmax/pmax_io/v1_0/pmax_io.cpp` | PMax I/O domain flow (IO/Mem fabric freq ceilings) |
| 6 | `src/flow/pmax/pmax_hpm/v1_1/pmax_hpm_evt_io.cpp` | PMax HPM event handler for I/O domain |
| 7 | `src/flow/pmax/pmax_tpmi/v1_0/pmax_common_tpmi.cpp` | PMax TPMI interface — BIOS knob processing |
| 8 | `src/flow/pmax/pmax_global_state/v1_1/pmax_global_state.cpp` | PMax global state aggregation across dies |
| 9 | `src/ip/pmax/v2_0/pmax_ip.cpp` | PMax IP driver — register access, config, calibration |
| 10 | `src/ip/pmax/v2_0/fuses_pmax.xml` | PMax fuse definitions (v2, DMR) |
| 11 | `src/cfgdata/dmr_io/v1_0/pmax_topology.cpp` | PMax CFC topology + Psafe freq mesh indexing |
| 12 | `src/flow/energy_report/v2_0/energy_report.cpp` | FIVR energy report flow (v2) |
| 13 | `src/flow/energy_report/fivr_mapping/v1_5/fivr_energy_mapping.hpp` | FIVR energy mapping per domain |
| 14 | `src/cfgdata/dmr_io/v1_0/fivr_energy_mapping.hpp` | FIVR energy mapping tables (DMR) |

#### Pcode (CBB die-level firmware)
| # | File | Description |
|---|------|-------------|
| 1 | `source/pcode/flows/slow_limits/fast_limits.h` | Primary PMax handler — soft_pmax, hard_pmax, HPM receiver |
| 2 | `source/pcode/flows/slow_limits/fast_limits.cpp` | Soft/hard PMax request processing, save/restore for FW-update |
| 3 | `source/pcode/hpm/hpm_manager.cpp` | HPM dispatch — PMAX_FREQUENCY_LIMIT + PMAX_INST_PWR handlers |
| 4 | `source/pcode/flows/workpoint_calc/workpoint_calc.cpp` | Calls commit_pmax() for ring/fabric domains |
| 5 | `source/pcode/flows/slow_limits/pem_telemetry.h` | PEM telemetry for PMax counters (PEM_MTPMAX) |
| 6 | `source/pcode/flows/telemetry_pd_fivr_energy.cpp` | FIVR domain energy reporting (reads DOMAIN_ENERGY_REPORTING_ENABLE fuse) |
| 7 | `source/pcode/flows/telemetry_pd_uvov_monitor.cpp` | PMax OV/UV telemetry monitor |

---

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| PMax HAS | [DMR MT PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PMax.html) | Primary spec — MT PMax, PL4, BIOS config, cross products, dual VCCIN, DMR-SP connectivity |
| GNR PMax | [GNR MT PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/Multi-Threshold%20PMAX%20Detector/mt_pmax.html) | Legacy gen reference |
| PMax Detector MAS | [DMR PMax Detector MAS](https://docs.intel.com/documents/arch_datacenter/PMAX/DMR/DMR%20PMax%20Detector%20MAS/DMR%20PMax%20Detector%20MAS.html) | IP-level MAS |
| PMax Detector HAS | [DMR PMax Detector HAS](https://docs.intel.com/documents/arch_datacenter/PMAX/DMR/DMR%20PMAX%20Detector%20HAS/DMR%20PMax%20Detector%20HAS.html) | IP-level HAS |
| Integration Guide | [PMax Integration Guide](https://docs.intel.com/documents/arch_datacenter/PMAX/DMR/DMR%20PMAX%20Detector%20IntegrationGuide%20gen6/DMR%20PMAX%20Detector%20IntegrationGuide%20gen6.html) | Integration guide gen6 |
| FIVR Energy HAS | [Fine-Grained Energy Reporting](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Fine%20grained%20energy%20reporting/DMR_fivrenergy_report.html) | FIVR/MBVR per-domain energy, calibration, telemetry equations |
| CBB Throttle | [CBB Throttle Aggregator MAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Power%20Delivery%20MAS/PD%20IPs/Throttle%20Aggregator%20MAS/Throttle%20Aggregator%20MAS.html) | Clock vs architectural throttle muxes |
| Dual VCCIN PPT | [DMR POR-1 Dual VCCIN](https://intel.sharepoint.com/:p:/r/sites/DiamondRapids/IMH_FE/_layouts/15/Doc.aspx?sourcedoc=%7B737B3F35-ECF6-4177-BD33-6D95C80DA668%7D) | Dual VCCIN overview presentation |
| Dual VCCIN HSD | [22014810103](https://hsdes.intel.com/appstore/article/#/22014810103) | PM FW for Dual VCCIN feature tracking |
| DMR-SP IOH HSD | [22020996043](https://hsdes.intel.com/appstore/article/#/22020996043) | DMR-SP PMax connection to IOH die |
| Jira | [SERVERPMFW-154](https://jira.devtools.intel.com/browse/SERVERPMFW-154) | PMax firmware tracking |
| HSD | [14018253120](https://hsdes.intel.com/appstore/article-one/#/article/14018253120) | PMax feature article |
| CBB P-State HAS | [CBB P-State Stack](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html#pmax) | CBB PMax handling |
| CBB Telemetry | [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html) | FIVR energy registers per CBB |
| PkgC HAS | [DMR PkgC](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Idle_Flow/DMR_PkgC.html#pmax-detector) | PMax detector enable/disable during PkgC |
| Thermal HAS | [DMR Thermal](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#ia32_package_therm_status) | IA32_PACKAGE_THERM_STATUS PMAX bits |
| RACL KB | [racl.md](racl.md) | Per-iMH current limiter — independent from PMax |
| Socket RAPL KB | [socket_rapl.md](socket_rapl.md) | RAPL PID freq ceiling — min'd with PMax ceiling |
| SIMPL KB | [simpl.md](simpl.md) | SIMPL DFC ceiling — min'd with PMax ceiling |

---

---

### Related Sightings
<!-- No NWP PMax sightings cataloged yet -->

---

### NWP Delta

NWP inherits DMR MT PMax architecture. Key NWP-specific areas to validate:
- **Dual vs Single VCCIN**: Confirm NWP platform VCCIN topology. If single VCCIN (like DMR-SP), PMax connectivity to IOH via Option 2a wires must be verified
- **PMax detector IP**: Verify NWP silicon has PMax detector with all 4 thresholds (MT0/MT1/MT2/FDD)
- **Power-Frequency profile fuses**: Verify NWP binsplit provides PF curve fuses (6 power points × 6 Cdyn levels + 3 fabric domains). Psafe multiplier defaults
- **PL4 fuses**: Per-iMH PL4_SCALE_FACTOR, SOCKET_PARTITION_ICC_MAX_APP, SCALING_FACTOR_VTRIP1/2
- **D2D fast throttle timing**: Verify 50ns response requirement for hard throttle across D2D wire. Latency may differ with NWP D2D fabric
- **CBB throttle aggregator fuses**: Verify `bgr_infra_N_fuse.pick_fast_throttle_output` and `pick_droop_throttle_output` set to 0x1 on NWP
- **FIVR energy reporting**: Verify NWP FIVR domain count (may differ from DMR if different CBB chop or iMH FIVR config). Check scalars (MAX_I_OUT per domain)
- **PMAX_TRIGGER_IO GPIO**: Verify NWP platform routes GPIO bidirectional pin correctly for both input (external trigger) and output (CPU trigger to platform)
- **TPMI PMAX_CONTROL**: Verify per-iMH instantiation and BIOS programming of VTRIP_0_OFFSET, GPIO enables, DISABLE_MASK
- **IA32_PACKAGE_THERM_STATUS**: Verify PMAX_STATUS[12] and PMAX_LOG[13] bits reflect hardware PMax events correctly

---

### Validation Starting Points

1. **TPMI register check**: Read PMAX_CONTROL and PMAX_STATUS per iMH via PythonSV TPMI path. Verify VALID bit set, CAL_ERR = 0 (calibration passed)
2. **Fuse check**: Read PF curve fuses (SOCKET_VIRUS_POWER_FREQUENCY_CURVE_*) and verify non-zero. Read TDP_TO_PSAFE_MULTIPLIER (expect ~0x33)
3. **DFx inject hard throttle**: Set `IO_THROTTLE_SIGNALS_OVERRIDE.THROTTLE_1_HW_INJECT = 1` → verify instant freq drop to Psafe. Check IA32_PACKAGE_THERM_STATUS.PMAX_STATUS = 1
4. **DFx inject soft throttle**: Set `IO_THROTTLE_SIGNALS_OVERRIDE.LOCAL_PMAX_PWM_HW_INJECT = 1` → verify PWM throttle counter increments in IO_ACCUMULATED_THROTTLE_CYCLES
5. **PL4 dynamic**: Write TPMI Power_Limit_Control4 with lower PL4 → verify PMAX_CONFIG1 offsets update (MT0/MT1/MT2 shift)
6. **Disable mask**: Set PMAX_CONTROL.PMAX_DISABLE_MASK = 0x3 → verify no throttle action on DFx inject
7. **PLR**: During PMax event, read PLR_MAILBOX_DATA — verify MT_PMAX bit set
8. **PEM**: Verify PEM event PEM_MTPMAX fires during PMax throttle
9. **GPIO bidirectional**: Test PMAX_GPIO_TRANSMITTER_ENABLE → verify GPIO asserts on internal PMax event. Test PMAX_GPIO_TRIGGER_ENABLE → verify external assert triggers PMax on both iMHs
10. **Cross-feature**: Run PMax inject while Fast RAPL is limiting → verify min(PMax, Fast RAPL) enforced
