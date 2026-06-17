# SoC Thermal > Thermtrip

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: Thermtrip (CATTRIP) is DMR's last-resort catastrophic thermal protection — an asynchronous, fully hardware-driven shutdown triggered when silicon exceeds the thermtrip threshold (~125°C ±10°C), preventing permanent damage.

**Topology**:
```
Core/CCF DTS daisy-chain (per tile) ─> Thermtrip Survivability Block ─> CBB Punit HWRS
AON DTS (CBB Base, always-on) ───────/                                    |
                                                                          ├─ PLLs/FIVRs/BGR shutdown (local, ~30–100 nS)
                                                                          └─ YY_THERMTRIP_N (D2D GPIO, bidir) ─> IMH0
IMH SOC DTS chains ──────────────────────────────────────────────────> IMH Punit HWRS
                                                                          └─ MBVR shutdown + XX_THERMTRIP_N ─> Platform
```

**Key operational principle**: No flops on the thermtrip wire — pure combinational path from DTS to HWRS. DTS chains within each die are daisy-chained and OR-aggregated by the Thermtrip Survivability Block. HWRS triggers die-local shutdown (PLLs, FIVRs, BGR) within ~30–100 nS. In DMR, package `XX_THERMTRIP_N` is **output-only** (rxen_b=1) — input disabled since DMR to prevent false platform shutdowns from external noise.

**Boot activation**: Thermtrip active at PH1.2 (SOC DTS fuse pull + DTS enabled). Remains active through PkgC6 — all DTS stay enabled in deep sleep, so protection is continuous.

Thermtrip (CATTRIP) is the **last-resort catastrophic thermal protection** mechanism that triggers an emergency shutdown when silicon temperature exceeds the thermtrip threshold, preventing permanent damage. It is entirely hardware-driven — **asynchronous, no flops in the outbound path** — for minimum latency (~30-100nS).

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core/CCF DTS daisy-chain (per tile) | CBB Top Die | Combinational thermtrip sensing per tile; OR-aggregated in Survivability Block | `scu_hwrs_thermtrip_out`, `early_dts_thermtrip` | Legacy Architecture Summary |
| AON DTS | CBB Base Die | Always-on thermtrip sensor; last in daisy chain; active in all power states including PkgC6 | `i_thermtrip_aon_en` | Legacy Architecture Summary |
| Thermtrip Survivability Block | CBB / IMH | OR-aggregates all DTS chains on the die; drives HWRS | `scu_hwrs_thermtrip_out` | Legacy Architecture Summary |
| HWRS (Hardware Reset Sequencer) | CBB / IMH | Receives thermtrip → shuts down PLLs, FIVRs, BGR; drives inter-die GPIO | `yy_thermtrip_n` D2D GPIO (bidir); `O_punit_thermtrip` | Legacy Architecture Summary |
| D2D GPIO (UCIe) | IMH↔CBB, IMH↔IMH | Propagates thermtrip to all dies within the socket | `yy_thermtrip_n` (bidirectional) | Legacy Architecture Summary |
| IMH0 Package GPIO | IMH0 | Drives `XX_THERMTRIP_N` package bump to platform (output-only in DMR, rxen_b=1) | `xxthermtrip_n_tx`, rxen_b=1 | Legacy Sighting 22021682591 |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core PMA | No role — thermtrip is fully hardware; fires before Acode can respond | — | HAS |
| PCode (CBB) | CBB Base Die | No role — HWRS acts directly; PCode is shutdown along with the die | — | HAS |
| PrimeCode (IMH) | IMH die | No role — thermtrip is fully hardware on IMH as well | — | HAS |
| BIOS / UEFI | Platform | Must coordinate shutdown of other sockets within 500 mS after XX_THERMTRIP_N assertion per OKS PDG | Platform-level power sequencing | [OKS PDG](https://cdrdv2.intel.com/v1/dl/getContent/788196) |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| GPIO | `XX_THERMTRIP_N` (package bump) | Output-only (DMR) | Active-low; driven by IMH0 on thermtrip; rxen_b=1 disables input to prevent false shutdown from platform noise | Legacy Sighting 22021682591 |
| D2D GPIO | `YY_THERMTRIP_N` (inter-die bump) | Bidirectional | Any die thermtrip propagates to all dies within socket | Legacy Architecture Summary |
| MSR | None (thermtrip is pre-firmware) | — | No OS-visible register for thermtrip event at time of assertion; observed post-reset via MCA log | — |
| PECI | Machine-check / CATERR log | RO | Post-thermtrip platform log; identifies which socket/die tripped | Intel PECI spec |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Thermtrip assertion latency | ~30–100 | nS | DTS chain → Survivability Block → HWRS → PLL/FIVR shutdown; no flops on path | Legacy Architecture Summary |
| Thermtrip threshold | ~125 | °C ±10°C | Product-specific; BJT diode calibrated; derived from QnR requirement | Legacy Key Properties |
| Inter-die propagation (yy_thermtrip_n) | ~nS | — | D2D GPIO bump; bidirectional; triggers all dies in socket | Legacy Architecture Summary |
| Platform inter-socket shutdown budget | 500 | mS | Platform must shutdown other sockets within 500 mS after XX_THERMTRIP_N per OKS PDG | Legacy Execution Flow |
| Boot activation | PH1.2 | — | SOC DTS fuse pull + DTS enabled; thermtrip protection active before significant heating | Legacy Boot Sequence |
| PkgC6 protection gap | 0 | — | All DTS enabled in PkgC6; thermtrip continuous with no sleep-state gap | Legacy Execution Flow |
| PLL shutdown latency (gate output) | ~3 | PLL output clock cycles | Thermtrip sampled via rank-3 metaflop in PLL output clock domain | Legacy Execution Flow |
| PLL shutdown latency (graceful FSM) | ~30 | reference clock cycles | Thermtrip sampled via rank-2 metaflop in reference clock domain | Legacy Execution Flow |

## NWP Delta

**Thermtrip/Cattrip is supported on NWP** with topology changes per [NWP NIO GPIO HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/gpio/newport%20nio%20gpio%20has.html).

### Topology Changes
- Single NIO die — no cross-IMH thermtrip wire-OR needed (vs dual IMH in DMR)
- `THERMTRIP_N` is daisy-chained across DTS instances within NIO
- Bidirectional for survivability — each die can sense remote die thermtrip
- Wire-ORed between NIO and 2 CBBs → sent to PCH for shutdown
- DTS-AON is last in thermtrip chain (in CGU), `i_thermtrip_aon_en` = 1

### Functional Changes
- Thermtrip is **completely HW** — no PrimeCode involvement (same as DMR)
- Each local HWRS propagates Cattrip_b to all FIVRs/PLLs within the die
- HWRS triggers on: xxTHERMTRIP_n assertion, local DTS daisy-chain, or Punit cattrip/thermtrip signals
- Glitch filter (`catfilteren`) enabled by default for all NIO DTS instances

### Validation Impact
- Verify NIO DTS daisy-chain terminates correctly at DTS-AON
- Verify NIO→CBB thermtrip wire-OR propagation (2 paths vs 4 in DMR)
- No cross-IMH thermtrip path to test
- HSD 14027181891: verify updated DTS/TRSD placement

## Legacy (Human-Curated Reference)

### Architecture Summary

Thermtrip (CATTRIP) is the **last-resort catastrophic thermal protection** mechanism that triggers an emergency shutdown when silicon temperature exceeds the thermtrip threshold, preventing permanent damage. It is entirely hardware-driven — **asynchronous, no flops in the outbound path** — for minimum latency (~30-100nS).

#### Key Properties
- **Threshold**: Product-specific, derived from QnR requirement, calibrated per BJT diode. Maximum evaluated runaway temperature ~125°C ±10°C.
- **Asynchronous**: No flops on the thermtrip wire — pure combinational path from DTS to shutdown
- **Strong pull-up** required on the thermtrip pin
- **Always active**: Thermtrip protection is enabled early in boot (PH1.2) and stays active through PkgC6 (all DTS remain enabled in C6)

#### DTS Daisy Chain Architecture

Thermtrip detection uses **daisy-chained DTS thermtrip feedback** within each die, then OR-aggregated before reaching the Punit:

```
CBB Die (Top + Base):
┌─────────────────────────────────────────────────────┐
│  Top Die                                             │
│  ┌──────┐  ┌──────┐  ┌──────┐                       │
│  │Tile 0│  │Tile 1│  │Tile 2│                        │
│  │Core  │  │Core  │  │Core  │                        │
│  │Chain │  │Chain │  │Chain │                        │
│  └──┬───┘  └──┬───┘  └──┬───┘                       │
│     │thermtrip_top2base_0/1/2 (via Shaft)            │
├─────┼──────────┼─────────┼──────────────────────────┤
│  Base Die                                            │
│  ┌──┴───┐  ┌──┴───┐  ┌──┴───┐                       │
│  │CBO   │  │CBO   │  │CBO   │  ┌─────┐             │
│  │Chain │  │Chain │  │Chain │  │AON  │             │
│  └──┬───┘  └──┬───┘  └──┬───┘  │DTS  │             │
│     └──────────┴─────────┴──────┴──┬──┘             │
│                                     │                │
│              Thermtrip Surv & Aggr Block             │
│                      │                               │
│                  Punit                               │
│              ┌───┴───────┐                           │
│              │ PLL, FIVR,│                           │
│              │ BGR, etc. │                           │
│              └───────────┘                           │
│                      │                               │
│               YY_THERMTRIP_N GPIO (inter-die, bidir) │
└─────────────────────────────────────────────────────┘
```

**Sub-chain structure** (to meet latency target):
- Each **Core Tile** DTS forms a separate thermtrip chain
- Each **CCF DTS "virtual tile"** (CCF DTS blocks physically correlated to a core tile) forms a separate chain
- All chains are **OR-aggregated** in the Thermtrip Survivability Block before driving Punit
- Punit distributes the thermtrip output to IPs (PLLs, FIVRs, BGR) and to inter-die/package GPIO

#### SOC-Level Thermtrip Connectivity (DMR)

```
                       xxTHERMTRIP_N (package bump)
                    ┌─────────┴──────────┐
                    │    IMH0 (Primary)   │
                    │  Punit + HWRS       │
                    │  xxthermtrip_n_tx   │ ← drives package bump (output only)
                    │  xxthermtrip_n_rx   │ ← DISABLED (rxen_b=1, DMR change)
                    │  i_thermtrip        │ ← tied to 0
                    └──┬──────────┬──────┘
               D2D    │yy_thermtrip_n (bidir)
                    ┌──▼──┐  ┌───▼────┐
                    │IMH1 │  │CBB0..3 │
                    │Punit│  │Punit   │
                    │HWRS │  │Surv Blk│
                    └─────┘  └────────┘
```

#### DMR Change: Package Thermtrip Output Only

**Sighting [22021682591](https://hsdes.intel.com/appstore/article-one/#/article/22021682591)**

- **Original spec**: `xxTHERMTRIP_N` was bidirectional — to shutdown all sockets quickly when any socket trips
- **Problem**: Customers on SPR/EMR reported false system shutdowns due to **platform noise** (no actual thermal excursion)
- **DMR change**: Disabled rx path by tying `rxen_b = 1` for `xxTHERMTRIP_N` → **output only** at package level
- **Inter-die bumps** (`yy_thermtrip_n`) **remain bidirectional** — any die can trigger shutdown of all dies within the same socket
- Aligns DMR to GNR package thermtrip definition
- Platform responsible to shutdown other sockets within **500ms** per [OKS PDG](https://cdrdv2.intel.com/v1/dl/getContent/788196?explicitVersion=true)

#### Thermtrip Disable

Thermtrip can be **disabled for debug purposes only** via DFX mechanisms:
- DTS-level: Fuse or DFX override to disable individual DTS thermtrip contribution
- Die-level: DFX hook to mask thermtrip assertion from specific chains
- ⚠️ **Never disabled in production** — disabling thermtrip removes catastrophic thermal protection and may result in permanent silicon damage

### Execution Flow

#### Thermtrip Assertion Flow

1. **DTS detects** temperature exceeding thermtrip threshold on any DTS in the daisy chain
2. **DTS chain propagates** thermtrip assertion asynchronously through the daisy chain (no flops)
3. **Thermtrip Survivability Block** OR-aggregates all chains on the die
4. **HWRS** (Hardware Reset Sequencer) receives `scu_hwrs_thermtrip_out` + `early_dts_thermtrip`
5. **Die-local shutdown actions** (immediate, ~30-100nS):

   **CBB Die Actions:**
   - **PLL shutdown**: 
     1. Gate PLL output clock (thermtrip sampled in PLL output clock domain via rank-3 metaflop → ~3 PLL output clock cycles)
     2. Gracefully shutdown PLL FSM (thermtrip sampled in reference clock domain via rank-2 metaflop → ~30 reference clock cycles)
     3. If reference clock stops before full shutdown, PLL may remain partially enabled until cold reset
   - **FIVR shutdown**: All FIVRs on the die disabled (see [CBB FIVR Shutdown Inventory](#cbb-fivr-shutdown-inventory) below)
   - **BGR shutdown**: Bandgap reference disabled

   **IMH Die Actions:**
   - HWRS triggers FIVR supplies shutdown
   - HWRS sends indication to platform to shutdown MBVRs
   - `O_punit_thermtrip` → asserts `xxthermtrip_n_tx` on package bump

6. **Inter-die propagation**: `yy_thermtrip_n` D2D wire propagates to all other dies → each die performs its own local shutdown
7. **Package bump assertion**: IMH0 drives `xxTHERMTRIP_N` = 0 → platform initiates emergency system shutdown

#### Thermtrip Sources (Various)

| Source | Die | Chain | Description |
|--------|-----|-------|-------------|
| Core DTS (per tile) | CBB Top | Core Tile Chain | Each core tile has DTS → thermtrip chain |
| CCF DTS (virtual tile) | CBB Top | CBO Chain | CCF/CBO DTS correlated to core tile position |
| AON DTS | CBB Base | Always-on | Always-on DTS, active even in deep power-down |
| SOC DTS (various) | IMH | SOC chains | Memory, D2D, MIO, Accelerator, Fabric, CGU DTS |
| CGU DTS | CBB/IMH | Last in chain | CGU DTS is last in the CAT Trip daisy chain |
| Inter-die yy_thermtrip_n | D2D GPIO | Bidirectional | Other die asserted thermtrip |

#### Thermtrip Availability at Reset (Boot Sequence)

Thermtrip must be ready **before significant heating components are powered**:

1. **CBB Resources up**: Fuse Controller, DRNG, DFX Aggr, VCCINF, XTAL, BCLK, S5 voltages
2. **Boot FSM** `pd_fuse_infra` out of reset → BandGap circuit ramping
3. **DTSEnable asserted** to all CBB (SOC level) controlled DTS → **Thermtrip is ready for assertion** (BCLK already toggling, fuses downloaded)
4. Next CBB resources: SAPLL, D2D SB, ESE, Pclk, Punit, Pcode, TopFuseSense, FIVR PLL, SA DRNG, MiniSAF, CCFPMA, TopSBCLK, EarlyShafts, MISCShafts, CorePMA, FIVRVCCR, RingPLL, FIVRD2D, D2DMB

In the overall boot:
- **PH1.2**: SOC DTS fuse pulling + DTS enabled → thermtrip protection active
- **PH2.2**: SA thermal puller enabled (PMSB unblock)
- **PH2.52**: PCode kernel enabled → EMTTM operational (but thermtrip already active since PH1.2)

#### Thermtrip During Sleep (PkgC6)

All DTS remain enabled during CBB PkgC6 → **thermtrip is fully functional in sleep states**. No gap in thermal protection.

#### Isolation at Sort

During die sort (individual die testing), thermtrip signals must be isolated at shaft block entrances:
- Isolation control: `hvm_mode_sel` signal
- Relevant isolation: `dts1/i_thermtrip` (input) and `dts1/o_thermtrip` (driver)

#### CBB FIVR Shutdown Inventory

On thermtrip, **all FIVRs on the CBB die are disabled** simultaneously. Per the [FIVR IFDIM MAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Power%20Delivery%20MAS/FIVR%20IFDIM/FIVR%20IFDIM%20MAS/FIVR%20IFDIM%20MAS.html), the CBB base die contains **42 FIVR instances** distributed across the following domains:

| FIVR Domain | Count (DMR) | Scope | Description |
|-------------|-------------|-------|-------------|
| VccCore | 32 per CBB | Per core module | Core supply — one FIVR per core module (CCP) |
| VccR | 8 per CBB | Per ring/fabric slice | Ring/CFC fabric supply — 8 partitions across fabric slices |
| VccMLC | 1 per CBB | MLC/SSA | Mid-Level Cache SRAM supply |
| VccC2IA (D2D) | 1 per CBB | D2D UCIe Analog | Die-to-die UCIe PHY analog supply |

The FIVR IFDIM feature characterizes the impedance of the MBVR→FIVR power delivery network by pulling step current from all 42 FIVR instances simultaneously via a synchronized 8.33 MHz usync clock. The usync signal is distributed from a single generator in `par_base_pll_farm` through **342 repeater flops** (optimized from naïve 1008) to achieve ≤2.5nS skew across all FIVR instances.

**FIVR usync topology** (relevant to thermtrip shutdown uniformity):
- Usync generator → par_base_pll_farm (8 repeaters)
- → par_base_fabric_slice_0..3 (42+60+60+36 = 198 repeaters) — distribution trunks
- → par_ccf_fabric_main (48 repeaters) — CCF/ring FIVRs
- → par_base_fivr_channel_s0..s3 (12+28+28+12 = 80 repeaters) — core module FIVRs
- → par_base_fabric_sa_center (8 repeaters) — center fabric FIVR

During thermtrip, the Punit drives a single `O_punit_thermtrip` signal that reaches all FIVRs. Because the FIVR disable path is asynchronous (no flops), all 42 FIVRs are disabled within the ~30-100nS thermtrip latency budget regardless of their physical distance from the Punit.

**FIVR Health Monitor (FHM) telemetry** provides post-event validation of FIVR state via PMT registers:

| Register | SB Address | Scope | Thermtrip-Relevant Fields |
|----------|------------|-------|---------------------------|
| `FHM_STATUS_0` | 0x2E828 | Core modules 0-31 | 2-bit FIVR HI per core module (00=Green, 01=Yellow, 10=Red) |
| `FHM_STATUS_1` | 0x2E830 | Core modules 16-31 | 2-bit FIVR HI per core module |
| `FHM_STATUS_2` | 0x2E838 | MLC, D2D, Ring | `FIVR_HI_MLC0/1`, `FIVR_HI_D2D0/1` — non-core FIVR domains |
| `PMAX_OVUV_HI_STATUS` | 0x2E870 | PMAX detector | OV/UV fault counters — may spike during thermtrip shutdown |

### CBB Thermal Telemetry Observability

The CBB Punit exposes thermal telemetry via PMT (Platform Monitoring Technology) registers, providing observability into the DTS temperatures that feed the thermtrip daisy chains. These registers are critical for **pre-thermtrip diagnosis** (understanding thermal state leading to trip) and **post-mortem analysis** (reconstructing failure from telemetry snapshots).

#### CBB Temperature Registers (PMT)

| Register | SB Address | Format | Description |
|----------|------------|--------|-------------|
| `CBB_TEMP_TARGET` | 0x2E880 | Mixed | Composite: Margin to Tcontrol (S10.6), Effective TjMax (U8.0), Effective TCC Offset (U8.0) |
| `READ_MODULE_TEMP_CBB` | 0x2E880[47:32] | S10.6 | CBB die temperature relative to eff TjMax |
| `READ_MODULE_TEMP_CCF` | 0x2E888[15:0] | S10.6 | CCF/Ring temperature relative to eff TjMax |
| `READ_MODULE_TEMP_MAX_CCP` | 0x2E888[47:32] | S10.6 | Hottest core module (CCP) temperature + index [53:48] |
| `READ_MODULE_TEMP_MIN_CCP` | 0x2E890[15:0] | S10.6 | Coldest core module (CCP) temperature + index [21:16] |
| `TOTAL_CBB_THROTTLED_TIME` | 0x2E890[63:32] | ms | Accumulated time operating below P1 due to thermal |

**Usage for thermtrip analysis:**
- `READ_MODULE_TEMP_MAX_CCP` identifies the hottest core module — likely the DTS chain that triggered thermtrip
- `MAX_CCP_INDEX` field (bits 53:48) pinpoints exactly which CCP module was hottest
- `TOTAL_CBB_THROTTLED_TIME` non-zero before thermtrip indicates EMTTM was actively throttling but failed to prevent thermal runaway
- `CBB_TEMP_TARGET.EFF_TJ_MAX` and `EFF_TCC_OFFSET` show the effective thermal budget at time of trip
- Temperature values are relative to TjMax: **negative = margin remaining, zero/positive = at or above TjMax**

#### CBB Telemetry Sampler

The Punit telemetry aggregator supports configurable sampling of the entire telemetry register space via two sampler channels (SAMPLER_0, SAMPLER_1). For thermtrip debug:
- Configure `SAMPLER_0_CONTROL.SAMPLE_PERIOD_TIMER` to ~1ms periodic sampling
- Select temperature registers via `SAMPLER_0_SELECT` bit mask
- After thermtrip, read `SAMPLED_0_TIMESTAMP` and `SAMPLED_0_DATA_*` for the last snapshot before shutdown
- ⚠️ Sampled data is only valid if the sampler was configured and running before the thermtrip event

### Key Registers & Interfaces

#### GPIO Signals (Thermtrip)
| Signal | Die | Direction | Description |
|--------|-----|-----------|-------------|
| `xxTHERMTRIP_N` | IMH0 pkg bump | Output only (DMR) | Package thermtrip indication to platform |
| `xxthermtrip_n_tx` | IMH0 → bump | Output | Package thermtrip drive (from `O_punit_thermtrip`) |
| `xxthermtrip_n_rx` | Bump → IMH0 | Input (DISABLED) | Disabled via `rxen_b=1` per DMR change |
| `yy_thermtrip_n_tx` | Die → D2D | Output | Inter-die thermtrip drive |
| `yy_thermtrip_n_rx` | D2D → Die | Input | Inter-die thermtrip receive |
| `O_punit_thermtrip` | Punit | Output | Punit thermtrip output to GPIO + IPs |
| `O_thermtrip` | Surv Block | Output | Aggregated thermtrip from DTS chains |
| `i_thermtrip` | Punit | Input | External thermtrip input (tied to 0 on IMH0) |
| `scu_hwrs_thermtrip_out` | HWRS | Output | HWRS thermtrip trigger for die shutdown |
| `early_dts_thermtrip` | DTS | Output | Early DTS thermtrip detection signal |

#### Top/Base Shaft Interface (CBB)
| Signal | Direction | Description |
|--------|-----------|-------------|
| `o_thermtrip_top2base_0` | Top → Base | Tile 0 thermtrip chain from Top die DTS |
| `o_thermtrip_top2base_1` | Top → Base | Tile 1 thermtrip chain from Top die DTS |
| `o_thermtrip_top2base_2` | Top → Base | Tile 2 thermtrip chain from Top die DTS |
| `i_thermtrip_top2base_0/1/2` | Top → Base | Corresponding base die inputs |

#### GPIO Cell Configuration
| Config | Value (DMR) | Description |
|--------|-------------|-------------|
| `TX_EN_B` (package) | 0 | Transmit enabled — IMH0 drives thermtrip |
| `RX_EN_B` (package) | 1 | Receive disabled — output only per DMR change |
| `TX_EN_B` (inter-die) | 0 | Transmit enabled — all dies can assert |
| `RX_EN_B` (inter-die) | 0 | Receive enabled — all dies monitor |

#### Key Fuses / Thresholds
| Fuse / Parameter | Description |
|-------------------|-------------|
| Thermtrip threshold (per BJT diode) | Product-specific, calibrated per DTS (~125°C ±10°C) |
| `DTS_MAX` | Max allowed temperature from DTS sensors (fused) |
| `HIGHEST_TJ_MAX` | Worst-case TjMax before SST resolution |
| DFX thermtrip disable hooks | Debug-only disable of individual DTS chain contributions |
| Sort isolation (`hvm_mode_sel`) | Controls shaft isolation for per-die sort testing |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR SoC Thermal HAS — Thermtrip](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#thermtrip) | SOC-level thermtrip, GPIO connectivity, output-only change |
| HAS | [CBB Thermtrip HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermtrip/Thermtrip.html) | CBB die daisy chain topology, PLL/FIVR shutdown, latency, availability at reset |
| HAS | [CBB Thermal Integration HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/DMR%20CBB%20Thermal%20Integration%20HAS/DMR%20CBB%20Thermal%20Integration%20HAS.html) | DTS/diode topology, fuse config |
| HAS | [iMH Thermtrip GPIO](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Components/wave4_gpio_interdie.html#pm-gpio-signals) | IMH GPIO pin signals |
| HAS | [Socket Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Package-level thermal management |
| HAS | [OKS PDG](https://cdrdv2.intel.com/v1/dl/getContent/788196?explicitVersion=true) | Platform 500ms shutdown requirement |
| Sighting | [22021682591](https://hsdes.intel.com/appstore/article-one/#/article/22021682591) | DMR change to make xxTHERMTRIP_N output only |
| PCode src | `source/pcode/flows/thermals/` | CBB thermal/thermtrip handlers |
| HAS | [NWP CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/NWP_CBB_Telemetry/TelemetryAggregator_CBB_NWP.html) | NWP CBB thermal telemetry registers (PMT temperature, FHM, throttle time) |
| HAS | [DMR CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html) | DMR CBB telemetry baseline — NWP derives from this |
| MAS | [FIVR IFDIM MAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Power%20Delivery%20MAS/FIVR%20IFDIM/FIVR%20IFDIM%20MAS/FIVR%20IFDIM%20MAS.html) | CBB base die FIVR topology (42 instances, 342 usync repeaters), IFDIM characterization |
| Excel | [NWP CBB Telemetry Excel](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/NWP_CBB_Telemetry/assets/CBB_PUNIT_Telemetry_NWP.xlsx) | NWP CBB telemetry register definitions (machine-readable) |

#### Test Case Details

**22022421666 — Verify Thermtrip Disable**
- Use DFX mechanism to disable thermtrip on one or more DTS chains
- Verify thermtrip does NOT assert when disabled DTS exceeds threshold
- Verify thermtrip DOES assert from a non-disabled DTS chain (partial disable validation)
- Verify disable only works via DFX hooks (not accessible to production SW)
- Re-enable and confirm thermtrip protection is restored
- Verify sort isolation mode (`hvm_mode_sel`) correctly isolates shaft thermtrip inputs

**22022421671 — Verify Thermtrip shuts down all FIVRs and MBVRs**
- Inject thermtrip condition (DFX temperature override or DTS inject)
- Verify **CBB die**: all PLLs gated within ~3 PLL output clock cycles, full PLL shutdown within ~30 reference clock cycles
- Verify **CBB die**: all FIVRs disabled (VccR, VccCore, VccInf rails)
- Verify **CBB die**: BGR (Bandgap Reference) disabled
- Verify **IMH die**: HWRS triggers FIVR supply shutdown
- Verify **IMH die**: HWRS asserts indication to platform for MBVR shutdown
- Verify `xxTHERMTRIP_N` is driven low on package bump
- Verify platform detects assertion and initiates system-level emergency shutdown
- ⚠️ Destructive test — system will shut down

**22022421672 — Verify functionality of thermtrip pin from various sources**
- Trigger thermtrip from each DTS chain source independently:
  - Core Tile DTS (one per tile on CBB Top die)
  - CBO/CCF DTS (virtual tile chains on CBB)
  - AON DTS (always-on DTS on CBB Base die)
  - SOC DTS on IMH (Memory DTS, D2D/UCIe DTS, MIO DTS, Accelerator DTS, Fabric DTS, CGU DTS)
  - Inter-die `yy_thermtrip_n` assertion from another die
- Verify each source propagates correctly through daisy chain → Thermtrip Surv Block → Punit → package bump
- Verify `xxTHERMTRIP_N` is output only (no rx response when platform drives the pin low externally)
- Verify inter-die `yy_thermtrip_n` is bidirectional: assertion from any die triggers shutdown on all connected dies
- Verify latency is within ~30-100nS from DTS assertion to package bump assertion
- ⚠️ Destructive test — system will shut down per source

### Related Sightings

### NWP Delta

#### Topology Changes
- **Single NIO replaces dual IMH**: `xxTHERMTRIP_N` package bump is driven by NIO only. No IMH0↔IMH1 `yy_thermtrip_n` path — NIO is the sole package-level thermtrip GPIO owner.
- **NIO→CBB D2D**: `yy_thermtrip_n` inter-die wires route from NIO to 2 CBBs (vs DMR 4 CBBs). Shorter daisy chain → fewer aggregation points.
- **UCIe D2D bandwidth**: 32 GT/s (2× DMR) — thermtrip propagation latency from die to die may have tighter margins.

#### CBB Die Changes (NWP vs DMR)

The NWP CBB die (N0 stepping) has a **reduced core count** that directly impacts thermtrip chain topology and FIVR shutdown inventory:

| Parameter | DMR CBB | NWP CBB | Impact on Thermtrip |
|-----------|---------|---------|---------------------|
| Core modules (CCP) | 32 | 24 | Fewer DTS chains contributing to Top die thermtrip aggregation |
| Cores | 64 (2 per CCP) | 48 (2 per CCP) | Fewer per-core DTS sources |
| Threads | 128 (2 per core) | 48 (1 per core, SMT off) | No thermtrip impact — DTS is per-core |
| CBOs | 64 | 32 | Fewer CCF/CBO virtual tile chains |
| VccCore FIVRs | 32 | 24 | Fewer FIVRs to shutdown on thermtrip |
| VccR (Ring) FIVRs | 8 | 8 | Same — ring topology unchanged |
| VccMLC FIVRs | 1 | 1 | Same |
| VccC2IA (D2D) FIVRs | 1 | 1 | Same |
| **Total base die FIVRs** | **42** | **34** | Fewer FIVRs to disable — reduced IFDIM usync repeater count |
| Telemetry Product ID | — | 0x0AF (NWP N0) | Different GUID for PMT telemetry decode |

**FIVR IFDIM changes for NWP**: With 24 CCP (vs 32), the usync repeater topology on the NWP CBB base die is reduced. Fewer fabric_slice partitions are populated, and the total repeater count drops from 342 (DMR) to an estimated ~260. The IFDIM characterization sequence is identical but covers fewer FIVR instances.

**FHM Status register mapping**: NWP `FHM_STATUS_0` covers core modules 0-23 (vs DMR 0-31). `FHM_STATUS_1` has spare bits. `FHM_STATUS_2` is unchanged (MLC, D2D domains).

#### NWP CBB Thermal Telemetry Changes

The NWP CBB telemetry register space at SB address base 0x2E800 is functionally identical to DMR but with NWP-specific fields:

| Register | Change from DMR | NWP Detail |
|----------|-----------------|------------|
| `CBB_TEMP_TARGET` | Same structure | Same fields: MARGIN_TO_TCONTROL, EFF_TJ_MAX, EFF_TCC_OFFSET |
| `READ_MODULE_TEMP_MAX_CCP` | MAX_CCP_INDEX range | Index 0-23 (NWP) vs 0-31 (DMR) — validates with CCP count |
| `READ_MODULE_TEMP_MIN_CCP` | MIN_CCP_INDEX range | Index 0-23 (NWP) vs 0-31 (DMR) |
| `TOTAL_CBB_THROTTLED_TIME` | Same | Time below P1 due to thermal (ms) |
| `PEM_STATUS` / `PEM_COUNTER_*` | Same bit definitions | Includes `PEM_PER_CORE_THERMAL` for per-module EMTTM limit |
| `GLOBAL_ID.PRODUCT_ID` | NWP-specific | 0x0AF = NWP N0 (vs DMR CBB product ID) |

#### Feature Carry-Over
- **Output-only at package level**: DMR change (rxen_b=1) carries forward to NWP.
- **Inter-die bidirectional**: `yy_thermtrip_n` remains bidirectional between NIO and CBBs.
- **CBB PLL/FIVR/BGR shutdown**: 100% PCode reuse — identical shutdown actions (fewer FIVRs due to 24 CCPs).
- **DTS daisy chain within CBB**: PNC core reuse — same Top/Base shaft topology.
- **PkgC6 thermtrip availability**: All DTS remain enabled — no gap.
- **FIVR IFDIM characterization**: Same methodology, reduced FIVR count; usync generator and trigger synchronizer architecture unchanged.
- **Telemetry aggregator**: Same PMT register structure; only PRODUCT_ID and CCP index ranges differ.

#### NWP-Specific Risks
- NIO is a new die — DTS placement, chain topology, and thermtrip latency need validation from scratch.
- NWP removes accelerator IPs (DSA/IAA/QAT/DLB) — fewer DTS contributing to NIO thermtrip chains. Verify no stale chain endpoints.
- NWP LPDDR6 replaces DDR5 — DDR PHY DTS placement differs; verify DTS chain covers LPDDR6 PHY thermal hotspots.
- CGU DTS on NIO must remain last in the CAT Trip daisy chain (per spec).
- Sort isolation (`hvm_mode_sel`) must be validated for NIO shaft blocks (new die).
- **FIVR IFDIM usync repeater topology** must be re-validated for NWP CBB base die layout — fewer CCP partitions means different repeater routing.
- **FHM_STATUS register decode** must use NWP product GUID (0x0AF) — using DMR decode XML will show incorrect module mapping.
- **MAX_CCP_INDEX** in thermtrip analysis: NWP range is 0-23; ensure debug scripts don't assume DMR range 0-31.
