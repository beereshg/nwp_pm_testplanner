# SoC Thermal > GPIO (Thermal GPIO Pins)

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing + Baseline topology (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: DMR exposes 5 thermal GPIO package bumps — `XX_PROCHOT_N` (input), `XX_THERMTRIP_N` (output-only since DMR, rxen_b=1), `XX_MEMTRIP_N` (output), `XX_MEMHOT_IN_N` (input), `XX_MEMHOT_OUT_N` (output) — providing the critical hardware interface between CPU and platform for thermal protection.

**Topology**:
```
Platform GPIO ──XX_PROCHOT_N───────────> IMH0 GPIO_S0 + PUNIT
Platform GPIO ──XX_MEMHOT_IN_N─────────> IMH0 GPIO_S0 + PUNIT
IMH0 Punit ────XX_THERMTRIP_N (output)─> Platform (DMR: output-only, rxen_b=1)
IMH0 Punit ────XX_MEMTRIP_N  (output)──> Platform
IMH0 Punit ────XX_MEMHOT_OUT_N (output)> Platform
IMH0 ──yy_prochot_n  (D2D)──> IMH1, CBB0..CBB3 (fast_throttle)
IMH0 ──yy_thermtrip_n (bidir D2D)──> IMH1, CBB0..CBB3 (HWRS)
IMH0 ──yy_memhot_n   (D2D)──> IMH1
```

**Key operational principle**: Each pin has fused `txen_b`/`rxen_b`/`die_id` controlling direction. PROCHOT GPIO fires CBB `fast_throttle` immediately (~20 nS HW) then PCode + PrimeCode apply freq limits. THERMTRIP is fully hardware (asynchronous, no firmware). MEMHOT/MEMTRIP managed by PrimeCode CLTT polling.

**Boot activation**: Thermtrip path active at PH1.2. PROCHOT fast-throttle active at power-on. PrimeCode PROCHOT_RESPONSE_POWER translation from PH2.52. MEMHOT/MEMTRIP from PH3+ (CLTT polling active).

DMR has **5 thermal GPIO pins** at the package level that provide the critical hardware interface between CPU and platform for thermal protection. These are physical bumps on the package connected through inter-die D2D wires to the internal die GPIO logic.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| IMH0 GPIO_S0 + Punit | IMH0 (Primary IMH) | Receives PROCHOT/MEMHOT_IN; drives THERMTRIP/MEMTRIP/MEMHOT_OUT; propagates to IMH1 and CBBs via D2D | `gpio_xxprochot_n_rxdata`, `xxthermtrip_n_tx`, `o_punit_interdie_prochot` | [DMR SoC Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#gpio-interface) |
| D2D GPIO (UCIe bumps) | IMH↔IMH1, IMH↔CBBs | Propagates thermal events inter-die | `yy_prochot_n`, `yy_thermtrip_n` (bidir), `yy_memhot_n` | [DMR SoC Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) |
| HWRS (CBB + IMH) | All dies | Hardware Reset Sequencer — receives thermtrip from DTS daisy-chain → shuts down PLLs/FIVRs/BGR | `scu_hwrs_thermtrip_out`, `early_dts_thermtrip` | [CBB Thermtrip HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermtrip/Thermtrip.html) |
| GPIO fuse array (per bump) | IMH0 | Controls `txen_b`/`rxen_b`/`die_id` for each thermal GPIO pin | Fuse fields per bump | HAS |
| Memory Controller (CLTT) | IMH die | DIMM temperature monitoring via TSOD polling → MEMHOT/MEMTRIP thresholds | CLTT thresholds per MC channel | DMR SoC Thermal HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core PMA | No thermal GPIO role; fires only in response to yy_prochot_n fast_throttle HW wire | — | — |
| PCode (CBB) | CBB Base Die | Receives `yy_prochot_n`; asserts `fast_throttle` to cores immediately; applies `PROCHOT_POWER_LIMITED_FREQ_LIMIT` HPM; de-asserts fast_throttle when freq applied | `IO_FASTPATH_THERMAL[0]`; fast_throttle wire | [CBB P-State Stack HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html) |
| PrimeCode (IMH) | IMH die | Translates `PROCHOT_RESPONSE_POWER` → per-CDYN-index freq limits; sends HPM to leaves; monitors CLTT for MEMHOT/MEMTRIP; updates `IA32_PACKAGE_THERM_STATUS.PROCHOT_STATUS` | `prochot.cpp`, `hot_vr.cpp`; HPM `PROCHOT_POWER_LIMITED_FREQ_LIMIT` | [PrimeCode src](../../../firmware.management.primecode.firmware) |
| BIOS / UEFI | Platform | Programs `POWER_CTL[DIS_PROCHOT_OUT, VR_THERM_ALERT_DISABLE]`; responsible for 500mS inter-socket shutdown after THERMTRIP | MSR 0x1FC; OKS PDG | [OKS PDG](https://cdrdv2.intel.com/v1/dl/getContent/788196) |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | RO/RWC | [2/3] `PROCHOT_STATUS`/`LOG` — live/sticky PROCHOT state; [23:16] TEMPERATURE | Intel SDM |
| MSR `POWER_CTL` | 0x1FC | RW | [21] `DIS_PROCHOT_OUT`; [22] `PROCHOT_RESPONSE`; [24] `VR_THERM_ALERT_DISABLE` | Intel SDM |
| TPMI `PROCHOT_RESPONSE_POWER` | Package | RW | [14:0] power limit (0.125 W/LSB) when PROCHOT asserted; [63] LOCK | [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/TPMI/DMR_TPMI.html) |
| Punit CR `THROTTLE_INDICATIONS` | Per-CBB | RO | `throttle_0` = live prochot wire state | CBB P-State Stack HAS |
| GPIO HW signals | Die-level | FW/debug | `gpio_xxprochot_n_rxdata`, `xxthermtrip_n_tx`/`rx`, `yy_thermtrip_n_tx/rx` | DMR SoC Thermal HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| PROCHOT CPU reaction budget | ~250 | nS | Package GPIO pin to frequency applied; met by HW fast_throttle | Legacy Architecture Summary |
| CBB fast_throttle assertion | ~20 | nS | D2D `yy_prochot_n` → CBB Punit HW; no firmware path | Legacy Execution Flow |
| Thermtrip package pin latency | ~30–100 | nS | DTS daisy-chain → HWRS → `XX_THERMTRIP_N`; asynchronous, no flops | Legacy Execution Flow |
| Platform inter-socket shutdown budget | 500 | mS | Platform must shutdown other sockets after `XX_THERMTRIP_N` assertion per OKS PDG | Legacy Execution Flow |
| PROCHOT_RESPONSE_POWER resolution | 0.125 | W/LSB | TPMI [14:0]; clipped to [PKG_MIN_POWER, TDP] | Legacy Key Registers |
| PCode fast_throttle de-assert | ~1 | slow-loop (~1 mS) | After `PROCHOT_POWER_LIMITED_FREQ_LIMIT` HPM applied | Legacy Execution Flow |

## NWP Delta

**GPIO thermal pins supported on NWP** with modifications per [NWP NIO GPIO HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/gpio/newport%20nio%20gpio%20has.html).

### PROCHOT_N
- **Input-only** — output usage removed (taken care by BMC instead), same as DMR
- Asynchronous signal from platform to NIO
- Single NIO die — no IMH-to-IMH PROCHOT wire needed

### THERMTRIP_N
- Daisy-chained, bidirectional for survivability across dice
- Wire-ORed between NIO and CBBs, sent to PCH for shutdown
- Single NIO die — no cross-die wire-OR aggregation needed (vs dual IMH in DMR)

### MEMHOT
- Supported, but **may be dropped** depending on customer requirements
- PMIC does not have VR_HOT output visible to platform — DIMM TSOD used as proxy

### Validation Impact
- PROCHOT: simpler topology (no IMH-to-IMH path)
- THERMTRIP: verify NIO daisy-chain only (no dual-IMH aggregation)
- MEMHOT: confirm customer requirement before test investment

## Legacy (Human-Curated Reference)

### Architecture Summary

DMR has **5 thermal GPIO pins** at the package level that provide the critical hardware interface between CPU and platform for thermal protection. These are physical bumps on the package connected through inter-die D2D wires to the internal die GPIO logic.

#### GPIO Pin Summary

| Pin | Direction | Purpose | Active | Pull |
|-----|-----------|---------|--------|------|
| `XX_PROCHOT_N` | Input only | Platform power capping due to thermal | Low | — |
| `XX_THERMTRIP_N` | Output only (DMR) | Catastrophic thermal shutdown indication | Low | Strong pull-up |
| `XX_MEMTRIP_N` | Output only | Critical memory temperature shutdown | Low | — |
| `XX_MEMHOT_IN_N` | Input only | Platform asserts memory hot condition | Low | — |
| `XX_MEMHOT_OUT_N` | Output only | CPU indicates memory temps are hot | Low | — |

#### SOC Connectivity

All 5 GPIO pins are received/driven at the **primary IMH die** (IMH0). Inter-die communication uses D2D wires (`yy_*` variants) to propagate signals between IMH0 ↔ IMH1 and IMH ↔ CBB dies:

```
                    Platform Board
                    ┌──────────────────────────┐
                    │  xx_PROCHOT_N (input)     │
                    │  xx_THERMTRIP_N (output)  │
                    │  xx_MEMTRIP_N (output)    │
                    │  xx_MEMHOT_IN_N (input)   │
                    │  xx_MEMHOT_OUT_N (output) │
                    └──────────┬───────────────┘
                               │ Package bumps
                    ┌──────────▼───────────────┐
                    │     IMH0 (Primary)        │
                    │  GPIO_S0 + PUNIT + HWRS   │
                    └──┬──────────────────┬────┘
                  D2D  │ yy_prochot_n     │ D2D
                  wires│ yy_thermtrip_n   │ wires
                       │ yy_memhot_n      │
                    ┌──▼──┐          ┌────▼───┐
                    │ IMH1│          │CBB0..3 │
                    │     │          │(PCode) │
                    └─────┘          └────────┘
```

#### Fuse Configuration (GPIO Bumps)

Thermal GPIO bump behavior is controlled by fuses that configure direction, enable, and polarity for each pin. Key fuse fields per GPIO bump:
- **`txen_b`**: Transmit enable (active low) — controls whether the die drives the GPIO
- **`rxen_b`**: Receive enable (active low) — controls whether the die receives the GPIO
- **`die_id`**: Selects which die (primary vs secondary IMH) drives the package bump
- **`i_thermtrip`**: Thermtrip input (tied to 0 on IMH0 rx path per DMR change)

### Execution Flow

#### XX_PROCHOT_N — Input Pin Assertion

PROCHOT is the platform's mechanism to request the SOC to reduce power for thermal reasons. DMR supports **input mode only** (like legacy).

**Entry Flow:**
1. **Platform asserts** `xxPROCHOT_N` = 0 (active low) on package bump
2. **IMH0 GPIO_S0** receives `gpio_xxprochot_n_rxdata` = 0
3. **IMH0 PUNIT** asserts `o_punit_interdie_prochot` = 1 on D2D wires to IMH1 and CBBs
4. **IMH PrimeCode** translates `PROCHOT_RESPONSE_POWER` to frequency limits:
   - Clips to `[PKG_MIN_POWER, TDP]`
   - Converts power → frequency ceiling for cores, IO fabric, memory fabric, CBB fabric
   - Sends HPM `PROCHOT_POWER_LIMITED_FREQ_LIMIT` to secondary IMH and leaf CBBs
5. **CBB fast_throttle**: CBB asserts fast_throttle wire to cores immediately upon seeing D2D prochot → core clock division + CCF serial debug mode
6. **CBB PCode**: Applies `PROCHOT_POWER_LIMITED_FREQ_LIMIT` per CDYN index ratio limits
7. **CBB PCode**: De-asserts fast_throttle wire once Core WP is applied
8. **PrimeCode updates**: `IA32_PACKAGE_THERM_STATUS.PROCHOT_STATUS` = 1, `PROCHOT_LOG` = 1

**Exit Flow:**
1. Platform de-asserts `xxPROCHOT_N` = 1
2. IMH0 de-asserts D2D prochot signals
3. IMH PrimeCode removes fabric frequency ceilings
4. CBB PCode removes core frequency ceilings
5. `IA32_PACKAGE_THERM_STATUS.PROCHOT_STATUS` = 0 (LOG stays sticky)

**Cross-Product — PkgC × Prochot**: Prochot does NOT wake from PkgC. During PkgC, cores are in C6 and fabric is clock-gated — prochot action cannot help. No PkgC wake triggered.

#### XX_THERMTRIP_N — Output Pin Assertion

Thermtrip is a catastrophic thermal shutdown event. The signal is **daisy-chained** through DTS thermtrip feedback across all dies.

**DMR Change — Output Only (Sighting [22021682591](https://hsdes.intel.com/appstore/article-one/#/article/22021682591)):**
- Originally bidirectional (shutdown all sockets when any socket trips)
- Customer complaints on SPR/EMR about false shutdowns from platform noise
- DMR disables rx path by tying `rxen_b = 1` for `xxTHERMTRIP_N`
- Inter-die `yy_thermtrip_n` bumps remain **bidirectional**
- Aligns DMR to GNR package thermtrip definition
- Platform responsible to shutdown other sockets within 500ms per OKS PDG

**Thermtrip Flow:**
1. **DTS detects** temperature exceeding thermtrip threshold (daisy-chained DTS→DTS)
2. **HWRS** (Hardware Reset Sequencer) receives `scu_hwrs_thermtrip_out` + `early_dts_thermtrip`
3. **HWRS triggers** FIVR shutdown + MBVR shutdown indication to platform
4. **CBB PCode** shuts down FIVRs and PLLs on CBB die
5. **IMH0** drives `xxTHERMTRIP_N` = 0 on package bump → platform initiates emergency shutdown
6. **Thermtrip is asynchronous** — no flops in outbound path for minimum latency (~30-100nS)

**Boot Sequence**: Thermtrip protection is active early:
- **PH1.2**: SOC DTS fuse pulling + DTS enabled → thermtrip protection active
- Strong pull-up required on thermtrip pin

#### XX_MEMTRIP_N — Output Pin Assertion

MEMTRIP indicates a critical memory device temperature requiring immediate shutdown.

**Flow:**
1. **Memory controller** detects DIMM temperature exceeds critical threshold (via CLTT thermal sensor polling)
2. **IMH PrimeCode** asserts `XX_MEMTRIP_N` = 0 on package bump
3. **Platform** initiates emergency shutdown to prevent DIMM damage

#### XX_MEMHOT_IN_N — Input Pin Assertion

MEMHOT_IN allows the platform to indicate that external memory conditions are thermally critical, requesting the CPU to throttle memory bandwidth.

**Flow:**
1. **Platform asserts** `XX_MEMHOT_IN_N` = 0 (thermal condition on DIMMs or platform memory subsystem)
2. **IMH0** receives assertion on GPIO bump
3. **IMH PrimeCode** throttles memory bandwidth (MC bandwidth limiting)
4. When platform de-asserts, PrimeCode removes memory throttle

#### XX_MEMHOT_OUT_N — Output Pin Assertion

MEMHOT_OUT indicates to the platform that the CPU's internal memory temperature sensors are reading hot.

**Flow:**
1. **IMH PrimeCode** monitors DIMM temperatures via CLTT (Closed Loop Thermal Throttling) thermal sensor polling
2. When temperature exceeds the MEMHOT threshold → asserts `XX_MEMHOT_OUT_N` = 0
3. **Platform** can take cooling action (increase fan speed, alert BMC)
4. When temperature drops below threshold → de-asserts `XX_MEMHOT_OUT_N` = 1

#### GPIO Fuse Verification Flow (Test Case Cue)

GPIO bump fuse configuration must be validated to ensure correct direction, enable, and die-assignment:
1. Read fuse values for each thermal GPIO bump (`txen_b`, `rxen_b`, `die_id`)
2. Verify **PROCHOT**: `rxen_b=0` (receive enabled), `txen_b=1` (transmit disabled) — input only
3. Verify **THERMTRIP**: `txen_b=0` (transmit enabled), `rxen_b=1` (receive disabled per DMR change) — output only at package level
4. Verify **MEMTRIP**: `txen_b=0` (output), `rxen_b=1` (not receiving)
5. Verify **MEMHOT_IN**: `rxen_b=0` (input), `txen_b=1` (not driving)
6. Verify **MEMHOT_OUT**: `txen_b=0` (output), `rxen_b=1` (not receiving)
7. Verify inter-die `yy_thermtrip_n` is bidirectional (`txen_b=0`, `rxen_b=0`)

### Key Registers & Interfaces

#### Package MSRs (Thermal Status — GPIO Observable)
| Register | Address | Key Fields |
|----------|---------|------------|
| `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | `PROCHOT_STATUS[2]` — live xxPROCHOT_N state; `PROCHOT_LOG[3]` — sticky since last SW clear |
| `POWER_CTL` | 0x1FC | `ENABLE_BIDIR_PROCHOT[0]`, `DIS_PROCHOT_OUT[21]`, `PROCHOT_RESPONSE[22]`, `PROCHOT_LOCK[23]`, `VR_THERM_ALERT_DISABLE[24]` |

#### TPMI Registers
| Register | Scope | Key Fields |
|----------|-------|------------|
| `PROCHOT_RESPONSE_POWER` | Package | `PROCHOT_RESPONSE_POWER[14:0]` — power limit in 0.125W units when xxPROCHOT_N asserted; `LOCK[63]` |

#### Punit CRs / IO Registers
| Register | Description |
|----------|-------------|
| `THROTTLE_INDICATIONS` | `throttle_0` — live prochot wire state; `throttle_0_semaphore` |
| `IO_FASTPATH_THERMAL[0]` | Set to 1 on prochot assertion for fast-path handler |
| `IO_PACKAGE_THERM_STATUS` | Punit CR mirror of `IA32_PACKAGE_THERM_STATUS` |

#### GPIO HW Signals (Die-Level)
| Signal | Die | Direction | Description |
|--------|-----|-----------|-------------|
| `gpio_xxprochot_n_rxdata` | IMH0 | Input | Package prochot bump receive data |
| `gpio_xxprochot_n_rxen_b` | IMH0 | Config | Prochot receive enable (active low) |
| `o_punit_interdie_prochot` | IMH0→D2D | Output | Inter-die prochot propagation |
| `i_punit_interdie_prochot` | D2D→IMH1 | Input | Secondary IMH prochot receive |
| `xxthermtrip_n_tx` | IMH0 | Output | Package thermtrip bump drive |
| `xxthermtrip_n_rx` | IMH0 | Input | Package thermtrip bump receive (disabled on DMR) |
| `yy_thermtrip_n_tx/rx` | IMH↔CBB | Bidir | Inter-die thermtrip daisy chain |
| `scu_hwrs_thermtrip_out` | HWRS | Output | HWRS thermtrip trigger |
| `early_dts_thermtrip` | DTS | Output | Early DTS thermtrip detection |

#### HPM Messages (GPIO-Related)
| Message | Direction | Purpose |
|---------|-----------|---------|
| `PROCHOT_POWER_LIMITED_FREQ_LIMIT` | Root→CBB | Per-CDYN-index IA ratio limits + `CBB_FABRIC_LIMIT` + `IMH_MEMORY_FABRIC_LIMIT` + `IMH_IO_FABRIC_LIMIT` |
| `DNS_EVENT_DELIVERY[VR_THERM_ALERT]` | Root→CBB | VR hot 97% — related to prochot escalation path |

#### Key Fuses (GPIO Bumps)
| Fuse / Config | Description |
|---------------|-------------|
| GPIO bump `txen_b` per pin | Transmit enable (active low) — controls drive direction |
| GPIO bump `rxen_b` per pin | Receive enable (active low) — controls receive direction |
| GPIO bump `die_id` per pin | Selects which die drives the package bump |
| `THERMAL_THROTTLE_UNLOCK` | Allow SW to disable EMTTM (not directly GPIO but gating control) |
| CLTT thresholds (per MC channel) | Memory temperature thresholds for MEMHOT/MEMTRIP assertion |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR SoC Thermal HAS — GPIO Interface](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#gpio-interface) | GPIO pin definitions, SOC connectivity diagrams |
| HAS | [DMR SoC Thermal HAS — Prochot Flow](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#prochot-flow) | Full prochot entry/exit, cross-product |
| HAS | [DMR SoC Thermal HAS — Thermtrip](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#thermtrip) | Thermtrip daisy chain, output-only change |
| HAS | [CBB Thermal Management HAS — VR Hot](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html#vr-thermal-alert-therm_alert) | VR Hot → PROCHOT escalation |
| HAS | [CBB Thermtrip HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermtrip/Thermtrip.html) | CBB die thermtrip daisy chain, FIVR/PLL shutdown |
| HAS | [CBB P-State Stack / Slow Limits](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html) | Prochot slow limits, PLR |
| HAS | [OKS PDG](https://cdrdv2.intel.com/v1/dl/getContent/788196?explicitVersion=true) | Platform 500ms shutdown requirement |
| Primecode src | `src/flow/prochot/prochot_common/v1_0/prochot.cpp` | Prochot fastpath handler, assertion/deassertion |
| Primecode src | `src/flow/prochot/prochot_tpmi/v2_0/prochot_tpmi.hpp` | Prochot TPMI, PF curve, HPM to leaves |
| Primecode src | `src/flow/hot_vr/v2_0/hot_vr.cpp` | VR Hot flow (escalation to PROCHOT path) |
| PCode src | `source/pcode/flows/slow_limits/fast_limits.h` | Fast limits (prochot, pmax) |
| PCode src | `source/pcode/hpm/hpm_manager.h` | HPM message dispatch (prochot, thermal) |
| Test scripts | `pm/pss/prochot/pm_mcp_prochot.py` | DMR Prochot PSS test |
| Test scripts | `pm/pss/vrhot/vr_hot.py` | DMR VR Hot PSS test (PROCHOT escalation) |

#### Test Case Details

**22022421480 — Verify GPIO_BUMP Thermals fuses**
- Read fuse/config values for all 5 thermal GPIO bumps (`txen_b`, `rxen_b`, `die_id`)
- Verify PROCHOT bump: input-only (rx enabled, tx disabled)
- Verify THERMTRIP bump: output-only at package level (tx enabled, rx disabled per DMR change)
- Verify inter-die `yy_thermtrip_n`: bidirectional (both tx and rx enabled)
- Verify MEMTRIP: output-only
- Verify MEMHOT_IN: input-only; MEMHOT_OUT: output-only
- Cross-check `die_id` assignment matches primary IMH (IMH0) for package bumps

**22022421481 — Verify XX_MEMHOT_IN_N input pin assertion**
- Inject MEMHOT_IN assertion from platform GPIO (or use DFX inject if available)
- Verify IMH0 receives the assertion (`gpio_xxmemhot_in_n_rxdata` = 0)
- Verify PrimeCode applies memory bandwidth throttle
- De-assert → verify throttle removed
- Check no side-effects on core/fabric frequency

**22022421482 — Verify XX_MEMHOT_OUT_N output pin assertion**
- Drive sustained memory-intensive workload to push DIMM temperatures above MEMHOT threshold
- Verify IMH PrimeCode asserts `XX_MEMHOT_OUT_N` = 0 when CLTT threshold exceeded
- Reduce workload → verify de-assertion when temperature drops
- Verify assertion/de-assertion timing relative to CLTT polling interval

**22022421483 — Verify XX_MEMTRIP_N output pin assertion**
- Use DFX/inject mechanism to force critical memory temperature exceeding MEMTRIP threshold
- Verify `XX_MEMTRIP_N` = 0 asserted on package bump
- Verify platform-side detection (if observable) — triggers emergency shutdown path
- ⚠️ Destructive test — system will shut down

**22022421484 — Verify XX_PROCHOT_N input pin assertion**
- Assert `xxPROCHOT_N` = 0 via platform GPIO header or DFX inject
- Verify `IA32_PACKAGE_THERM_STATUS.PROCHOT_STATUS[2]` = 1
- Verify `PROCHOT_LOG[3]` = 1 (sticky)
- Verify frequency ceiling applied: read PLR mailbox `PLATFORM` bit (bit 4) set
- Verify HPM `PROCHOT_POWER_LIMITED_FREQ_LIMIT` sent to CBBs
- De-assert → verify PROCHOT_STATUS clears, frequency ceiling removed
- Verify PROCHOT_LOG remains sticky until SW clears
- Verify PkgC × Prochot: assertion during PkgC does NOT wake the package

**22022421485 — Verify XX_THERMTRIP_N input/output pin assertion**
- Verify package-level `xxTHERMTRIP_N` is output-only (DMR change: rx disabled via `rxen_b=1`)
- Use DFX mechanism to force DTS temperature above thermtrip threshold on one die
- Verify DTS daisy-chain propagates through `yy_thermtrip_n` inter-die wires
- Verify HWRS triggers FIVR + MBVR shutdown sequence
- Verify `xxTHERMTRIP_N` asserted (driven low) on package bump
- Verify inter-die `yy_thermtrip_n` is bidirectional (any die can trigger shutdown of all dies)
- ⚠️ Destructive test — system will shut down

### Related Sightings

### NWP Delta

#### Topology Changes
- **Single NIO replaces dual IMH**: All 5 GPIO package bumps are received/driven on NIO only. No IMH0↔IMH1 D2D prochot/thermtrip wire split — NIO is the sole GPIO owner.
- **NIO→CBB D2D**: `yy_prochot_n` and `yy_thermtrip_n` inter-die wires route from NIO to 2 CBBs (vs DMR 4 CBBs). Fewer D2D wire fanout paths.
- **D2D bandwidth**: 32 GT/s UCIe (2× DMR) — tighter timing margins for prochot/thermtrip propagation latency from package bump to CBB fast_throttle.

#### Feature Carry-Over
- **PROCHOT**: Input-only carries over. PF curve fuses may differ on NIO.
- **THERMTRIP**: Output-only at package level carries over (DMR change preserved). Inter-die `yy_thermtrip_n` remains bidirectional.
- **MEMHOT_IN/OUT**: Carries over. NWP LPDDR6 uses **MR4-only for CLTT** (no TSOD support). MEMHOT assertion chain is MR4-sourced. Same IO_TELEMETRY register path and HPM aggregation as DMR. DMR Gen4 conversion ranges used until LPDDR6-specific ranges provided.
- **MEMTRIP**: Carries over. LPDDR6 DIMM temperature monitoring via MR4 (no TSOD fallback). Single sub-channel per MC (vs DMR 2) affects MR4 polling iteration.

#### NWP-Specific Risks
- NWP LPDDR6 CLTT is **MR4-only** (confirmed SERVERPMFW-24119) — no TSOD fallback. MEMHOT/MEMTRIP thresholds depend on MR4 conversion ranges (currently using DMR Gen4 ranges; LPDDR6-specific ranges pending).
- No accelerator dies (DSA/IAA/QAT/DLB removed) — `PROCHOT_CFC_FABRIC_COUNT` scope reduced; prochot frequency ceiling applies to fewer fabric domains.
- GPIO bump fuse configuration on NIO must be validated from scratch — NIO is a new die, fuse mapping differs from DMR IMH.
- `PROCHOT_RESPONSE_POWER` power-to-frequency translation: NIO fabric frequency table may differ from DMR IMH; PF curve fuses need validation.
- Verify NIO thermtrip daisy chain with only 2 CBBs — shorter chain, but new DTS placement topology.
