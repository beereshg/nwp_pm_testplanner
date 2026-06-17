# Memory Thermal > DDRIO

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [Memory Thermal](memory_thermal_main.md)

## Baseline (DMR)

### What is DDRIO Thermal?
DDRIO temperature compensation keeps DDR PHY electrical and timing behavior stable as voltage and
temperature (VT) drift occurs. The DDRIO is a tall HIP with **10°C+ internal temperature gradients**.
Three mechanisms work together: RCOMP (periodic impedance calibration ~127 ms / 40–45 µs worst-case),
RX DQS Drift Compensation (crossover tracking), and DTS Temperature Code Distribution.

### Topology
- DDRIO PHY: 3 remote DTS diodes per MC (IOV/IOC placement) → DTS temp codes → COMP FSM
- PCode (CBB PUnit): owns `MemorySubSystem` driver, sends DDRIO PM messages for RCOMP coordination
- Primecode (IMH PUnit): maps DDRIO DTS → ITD domains (`ITD_VCCDDRD_0..3`), programs fuses via GPSB
- **DDRIO power feeds Socket RAPL** (not DRAM RAPL)

### Operating Principle
Hardware PDC timer (∼127 ms) triggers RCOMP FSM: 4-stage calibration (DQODT, CMDDRV, CLKDRV, DQDRV).
DTS distributes temperature codes to analog consumers (RXDQSCOMP, LDO/PLL, ICOMP, VCCDDRA).
RCOMP and OPPSR are mutually exclusive; PCode must disable RCOMP (≤15 µs) before enabling OPPSR.

### Boot-Time Init
Primecode `DDRIOIp::programDDRIOFuses()` and `programDDRIOBiosSaiPolicy()` run at BIOS phase.
BIOS programs `ddrintf_pdc_ctl.pdc_tmr_exp` (∼127 ms) and PM update enables.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| DDRIO PHY | IMH | DDR5 PHY with RCOMP FSM; 3 remote DTS diodes/MC; drives RCOMP, crossover drift, DTS distribution | RCOMP FSM completion signal to MC; DTS temp codes to COMP consumers | DMR DDR5/MCR HAS §DDRIO |
| MC CLTT engine | IMH | Coordinates RCOMP with C-state entry; issues COMP update after RCOMP completion; tracks rcomp_valid | QREQn, rcomp_valid, pme/pmx_phyupd_en | DMR DDR5/MCR HAS |
| ITD thermal domain | IMH | Aggregates DDRIO DTS → ITD_VCCDDRD_0..3; feeds SA aggregate domain | DTS temp codes from MC0–3 | ITD HAS (Wave3 Common) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PCode | `source/pcode/flows/memory/memory_subsystem.cpp` | Controls RCOMP enable/disable, sends DDRIO PM messages (RCOMP/DVFS_EARLY_RCOMP/SAGV), coordinates RCOMP↔OPPSR | `disable_rcomp_and_check_readiness_for_oppsr_enable()`, `hsd13013947115_manual_comp_cstate()` | PCode MemorySubSystem driver |
| PCode | `source/pcode/flows/memory/memory_subsystem.cpp` | Reads DDRIO temperature for RAPL power accounting | `get_ip_temperature()` → `thermals.get_MEMSS_minmax_temp()` | PCode MemorySubSystem driver |
| Primecode | `src/ip/ddrio/` | Maps DDRIO DTS to ITD thermal domains; programs DDRIO fuses via GPSB; manages BIOS SAI policy | `programDDRIOFuses()`, `programDDRIOBiosSaiPolicy()` | Primecode DDRIOIp |
| BIOS | Platform init | Programs PDC timer, DfxDdrioXoverDriftComp knob, PM entry/exit auto-update enables | `ddrintf_pdc_ctl.pdc_tmr_exp`, `pme_phyupd_en`, `pmx_phyupd_en` | NWP BIOS HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| RCOMP period (BIOS knob) | `ddrintf_pdc_ctl.pdc_tmr_exp` | RW (BIOS) | Periodic compensation timer, ~127 ms | DMR DDR5/MCR HAS |
| XoverDriftComp knob | `DfxDdrioXoverDriftComp` | RW (BIOS) | 0=Disable, 1=Enable, 2=Auto RX DQS drift compensation | NWP BIOS HAS |
| DDRIO temp readback | `get_ip_temperature()` TPMI/GPSB | RO | DDRIO die temperature for RAPL power accounting | PCode MemorySubSystem |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| RCOMP period | ~127 ms (PDC timer) | DMR DDR5/MCR HAS |
| RCOMP duration (worst case) | 40–45 µs | DMR DDR5/MCR HAS |
| Max RCOMP disable time | 15 µs (before enabling OPPSR) | HSD 13011934947 |
| Max OPPSR disable time | 2 µs | PCode MemorySubSystem |
| C6 QDENY timer target | 50–60 µs (range 42–84 µs), must exceed RCOMP window by ≥10 µs | DMR DDR5/MCR HAS |
| DDRIO internal temp gradient | 10°C+ across tall HIP | DMR DDR5/MCR HAS |
| NWP delta | Carried from DMR; NIO (NWP IMH) as sole memory host | NWP PM MAS |

## NWP Delta

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| Feature supported | ✅ Carried from DMR | NWP PM MAS |
| IMH topology | Single NIO (NWP IMH) replaces DMR dual-die IMH; DDRIO DTS paths unchanged | NWP PM MAS |
| RCOMP / DTS mechanisms | Identical to DMR | DMR DDR5/MCR HAS |
| RCOMP ↔ OPPSR timing | Same constraints apply | PCode MemorySubSystem |

## Legacy (Human-Curated Reference)

*All original content preserved below for reference.*

### Architecture Summary

DDRIO temperature compensation keeps DDR PHY electrical and timing behavior stable as voltage and temperature (VT) drift occurs during operation. The DDRIO is a tall HIP with **10°C+ internal temperature gradients**, making active compensation essential for signal integrity at DDR5 data rates.

Three compensation mechanisms work together:

1. **RCOMP (Resistor Compensation / Periodic Compensation)** — closed-loop calibration that retrains drive impedance and termination resistance. PCode manages RCOMP enable/disable and coordinates with C-state entry/exit. Hardware runs RCOMP approximately every **127 ms**, taking up to **40–45 µs** worst case per cycle.
2. **RX DQS Drift Compensation (Crossover)** — tracks VT-induced timing drift between DQ and DQS paths. Since DDR5 has no periodic host-DIMM retraining, this compensates DQS PI offsets to maintain setup/hold margin as temperature changes. Controlled by BIOS knob `DfxDdrioXoverDriftComp`.
3. **DTS Temperature Code Distribution** — SOC/DTS pushes temperature codes to DDRIO COMP block, which distributes them to analog consumers (RXDQSCOMP, LDO/PLL, ICOMP, VCCDDRA logic) for temperature-dependent analog adjustments.

The feature spans three firmware actors:

- **PCode (CBB PUnit)** — owns the `MemorySubSystem` driver that controls RCOMP enable/disable (`ddrintf_pdc_ctl.pdc_en`), sends DDRIO PM messages (RCOMP, DVFS early RCOMP, SAGV comp), manages RCOMP↔OPPSR timing constraints, handles manual compensation during C-states, and reads DDRIO temperature for RAPL power accounting.
- **Primecode (IMH PUnit)** — maps DDRIO DTS sensors to ITD thermal domains (`ITD_VCCDDRD_0..3`), programs DDRIO fuses via GPSB, and manages BIOS SAI policy. DDRIO temperature feeds into the `SA` aggregate thermal domain.
- **DDRIO PHY Hardware** — runs RCOMP FSM autonomously, manages crossover drift compensation, houses 3 remote DTS diodes per MC, and signals completion to MC for PHY update.

#### Key Architectural Rules

- **DDRIO is CPU thermal domain** — DDRIO power feeds into **Socket RAPL**, NOT DRAM RAPL. For non-VRoD configs, DDRIO estimated power must be subtracted from DRAM VR PMON.
- **RCOMP and OPPSR are mutually exclusive** — PCode must disable RCOMP before enabling OPPSR (15 µs max RCOMP disable, 2 µs max OPPSR disable).
- **C6 entry requires RCOMP coordination** — QDENY timer must exceed RCOMP computation window by ≥10 µs (target 50–60 µs, range 42–84 µs).

### Execution Flow

```
1. BIOS Configuration
   ├─ Programs DDRIO fuses via Primecode DDRIOIp::programDDRIOFuses()
   ├─ Programs BIOS SAI policy via DDRIOIp::programDDRIOBiosSaiPolicy()
   ├─ Configures DfxDdrioXoverDriftComp knob (0=Disable, 1=Enable, 2=Auto)
   ├─ Programs periodic comp timer: ddrintf_pdc_ctl.pdc_tmr_exp (~127 ms)
   └─ Programs PM entry/exit auto-update: pme_phyupd_en, pmx_phyupd_en

2. RCOMP Periodic Compensation (~127 ms + 40 µs cycle)
   ├─ Hardware PDC timer expires → RCOMP FSM activates
   ├─ Calibration sequence:
   │   ├─ Stage 1: DQODT (termination)
   │   ├─ Stage 2: CMDDRV (command drive)
   │   ├─ Stage 3: CLKDRV (clock drive)
   │   └─ Stage 4: DQDRV (data drive)
   ├─ Pull-down first (external precision resistor as reference)
   ├─ Then pull-up (using pull-down as reference)
   ├─ Computed codes → COMP shadow registers → FUB shadow registers
   ├─ COMP signals completion to MC
   └─ MC issues COMP update → effective values updated

3. DTS Temperature Code Distribution
   ├─ SOC/DTS reads 3 remote diodes per MC (IOV/IOC placement)
   ├─ DTS writes temp codes via GPSB or PLL CRI bus
   │   ├─ dts_temp_sel=0 → ddrpll_dts_temp (PLL DTS)
   │   └─ dts_temp_sel=1 → ddrcomp_dts_temp (COMP DTS)
   ├─ COMP FSM distributes to consumers:
   │   ├─ bit 0: rxdqscomp (DQS compensation)
   │   ├─ bit 1: ldo_lcpll (PLL LDO)
   │   ├─ bit 2: ldo_deskew (deskew LDO)
   │   ├─ bit 3: icomp_global (global current comp)
   │   └─ bit 4: ldo_vccddra (VCCDDRA LDO)
   └─ Temperature formula: [8:1] - 64 = °C

4. RX DQS Crossover Drift Compensation
   ├─ During init COMP: FSM records reference transition point
   ├─ During periodic COMP: sweeps PI codes, finds transition
   ├─ Majority voting on transition detection
   ├─ Generates PI offset code for VT drift correction
   └─ Distributes offset to DQS PIs in deskew CBB

5. PCode RCOMP Management (MemorySubSystem driver)
   ├─ Sends DDRIO PM messages for RCOMP coordination:
   │   ├─ RCOMP (0x8) — trigger compensation
   │   ├─ DVFS_EARLY_RCOMP (0x9) — early RCOMP during DVFS
   │   ├─ PRESAGV_COMP_EN (0xA) — pre-SAGV compensation
   │   └─ POSTSAGV_COMP_EN (0xB) — post-SAGV compensation
   ├─ RCOMP ↔ OPPSR coordination:
   │   ├─ disable_rcomp_and_check_readiness_for_oppsr_enable()
   │   ├─ Max RCOMP disable: 15 µs (HSD 13011934947)
   │   └─ Max OPPSR disable: 2 µs
   ├─ Manual C-state compensation:
   │   ├─ hsd13013947115_manual_comp_cstate()
   │   └─ Uses FORCECOMPUPDATE / FORCECOMP registers
   ├─ DVFS voltage adjustment:
   │   └─ hsd13012758704_set_ddrphy_voltages() → DDRCRVCCCLK, DDRCRVCCIOG
   └─ Reads get_ip_temperature() → thermals.get_MEMSS_minmax_temp()

6. C-State Entry/Exit Interaction
   ├─ C6 entry (QREQn 1→0): DDRIO starts RCOMP if rcomp_valid=0
   ├─ QDENY timer > RCOMP computation window + valid window (50–60 µs)
   ├─ If rcomp_valid=1: skip recompute, proceed to C6
   ├─ rcomp_valid_window: stretches post-update validity
   ├─ Auto PM update: pme_phyupd_en/pmx_phyupd_en
   └─ Wait controls: pme_phyupd_wait / pmx_phyupd_wait

7. Primecode Thermal Integration
   ├─ ThermalTopology maps DDRIO DTS to ITD domains:
   │   ├─ MC0_TEMP_C0R34 → ra_ra_dts_0_ddrio_0 → ITD_VCCDDRD_0
   │   ├─ MC1_TEMP_C0R56 → ra_ra_dts_0_ddrio_1 → ITD_VCCDDRD_1
   │   ├─ MC2_TEMP_C9R34 → ra_ra_dts_0_ddrio_2 → ITD_VCCDDRD_2
   │   └─ MC3_TEMP_C9R56 → ra_ra_dts_0_ddrio_3 → ITD_VCCDDRD_3
   ├─ All 4 DDRIO sensors aggregate into SA domain
   ├─ PCode publishes TEMPERATURE_DDRIO trace (S7.8 °C: MAX_TEMP, MIN_TEMP)
   └─ DDRIO power → Socket RAPL (NOT DRAM RAPL)
```

### Key Registers & Interfaces

#### DDRIO PHY Registers (per MC, MCHBAR)

| Register | Key Fields | Description |
|----------|-----------|-------------|
| `ddrintf_pdc_ctl` | `pdc_en` (bit 0) | Master periodic RCOMP enable |
| `ddrintf_pdc_ctl` | `pdc_upd_en[1:0]` | RCOMP update enable per subchannel |
| `ddrintf_pdc_ctl` | `pdc_tmr_exp[31:17]` | Periodic RCOMP / drift / weak-lock interval (~127 ms) |
| `ddrintf_pdc_ctl` | `rcomp_valid_window[16:9]` | Stretches RCOMP validity after update |
| `ddrintf_pdc_ctl` | `pme_phyupd_en` / `pmx_phyupd_en` | Auto RCOMP update on PM entry/exit |
| `ddrintf_pdc_ctl` | `pme_phyupd_wait` / `pmx_phyupd_wait` | Wait for RCOMP before PM transition |
| `PHYPMOVRD` | `ENPERIODICCOMP`, `DISCSTATEEXITCOMP` | PCode-facing RCOMP enable / C-state exit comp |
| `PHYPMSTATUS2` | `COMPCTRLFSMSTATE` | RCOMP FSM state (0 = idle) |
| `COMPCONTROL` | `FORCECOMPUPDATE`, `FORCECOMP` | Force manual compensation update |
| `ddrcomp_dts_ctl1` | `dts_temp_sel`, `dts_valid`, `dts_tempcode_sel` | DTS temp code source and validity |
| `ddrcomp_dts_ctl1` | `dts_tempcode_en[4:0]` | Consumer enable (rxdqscomp, ldo_lcpll, ldo_deskew, icomp, ldo_vccddra) |
| `ddrpll_dts_temp` | `dts_temp0/1/2` | PLL DTS temperature values (3 sensors) |
| `ddrcomp_dts_temp` | `dts_temp0/1/2` | COMP DTS temperature values (3 sensors) |

#### DDRIO Voltage Registers (DVFS)

| Register | Description |
|----------|-------------|
| `DDRCRVCCCLK` (DDRDATA / DDRCCC) | VCCCLK voltage for data/CCC lanes |
| `DDRCRVCCIOG` (DDRDATA / DDRCCC) | VCCIOG voltage for I/O |
| `PG_CTRL1` | `VCCSAG_PRAMPICTL` — SAG power gate ramp control |
| `PG` | `VCCSAGRAMPUP` — SAG voltage ramp up |

#### DDRIO Error Registers (validation)

| Register Path | Error Fields | Description |
|---------------|-------------|-------------|
| `ddrio.ddrcomp.ddrcomp_dts_ctl1` | `dts_temp0_err`, `dts_temp1_err`, `dts_temp2_err` | DTS temperature read errors |
| `ddrio.ddrclk_ch0.ddrclk_xover_ctl2_N` | `drift_comp_err` | Clock crossover drift comp error |
| `ddrio.ddrcc_ch0.ddrcc_xover_ctl2_N` | `drift_comp_err` | CC crossover drift comp error |
| `ddrio.ddrd_nN_ch0.ddrd_nN_xover_ctl2` | `drift_comp_err` | Data crossover drift comp error |
| `ddrio.ddrcomp.ddrcomp_rx_retrain2` | `rxdqscomp_flag_cal_err` | RX DQS comp calibration error |
| `ddrio.ddrcomp.ddrcomp_ldocal_ctl1` | `ldocal_flag_err` | LDO calibration error |

#### DDRIO PM Messages (PCode → DDRIO)

| Message | Opcode | Description |
|---------|--------|-------------|
| `DDRIO_PM_MESSAGE_ACTIVE` | 0x0 | DDRIO active state |
| `DDRIO_PM_MESSAGE_DDQGOFF` | 0x2 | Data queue gate off |
| `DDRIO_PM_MESSAGE_IOGOFF` | 0x3 | I/O gate off |
| `DDRIO_PM_MESSAGE_SAGOFF` | 0x6 | SAG power off |
| `DDRIO_PM_MESSAGE_RCOMP` | 0x8 | Trigger RCOMP compensation |
| `DDRIO_PM_MESSAGE_DVFS_EARLY_RCOMP` | 0x9 | Early RCOMP during DVFS |
| `DDRIO_PM_MESSAGE_PRESAGV_COMP_EN` | 0xA | Pre-SAGV compensation enable |
| `DDRIO_PM_MESSAGE_POSTSAGV_COMP_EN` | 0xB | Post-SAGV compensation enable |
| `DDRIO_PM_MESSAGE_SWITCH_DVFS_POINT` | 0xC | DVFS point switch |
| `DDRIO_PM_MESSAGE_RAMP_VDDQ_TX_FIVR` | 0xD | VDDQ TX FIVR ramp |
| `MCA_DDRIO_COMMAND_TIMEOUT` | 0x12 | DDRIO command timeout MCA |

#### RCOMP Calibration Stages

| Stage | Target | Description |
|-------|--------|-------------|
| 1 | DQODT | DQ on-die termination impedance |
| 2 | CMDDRV | Command drive strength |
| 3 | CLKDRV | Clock drive strength |
| 4 | DQDRV | Data drive strength |

#### PCode Interfaces

| Interface | Function | Description |
|-----------|----------|-------------|
| MemorySubSystem | `apply_rcomp_hsd_13011934947(bool)` | Enable/disable RCOMP via PHYPMOVRD.ENPERIODICCOMP |
| MemorySubSystem | `enable_rcomp_hsd_13011934947_tx()` | Periodic TX to re-enable RCOMP after timed disable |
| MemorySubSystem | `disable_rcomp_and_check_readiness_for_oppsr_enable()` | RCOMP↔OPPSR coordination (HSD 13011934947) |
| MemorySubSystem | `hsd13013947115_manual_comp_cstate()` | Manual comp during C-state (FORCECOMPUPDATE/FORCECOMP) |
| MemorySubSystem | `hsd13012758704_set_ddrphy_voltages()` | DVFS voltage adjust (DDRCRVCCCLK, DDRCRVCCIOG) |
| MemorySubSystem | `get_ip_temperature()` | Returns MEMSS min/max temp for RAPL |
| ThermalSamplingFlow | `get_MEMSS_minmax_temp()` | Central DDRIO temperature database |

#### Primecode Interfaces

| Interface | ID / Path | Description |
|-----------|----------|-------------|
| DDRIOIp class | `src/ip/ddrio/v2_0/ddrio.hpp` | DDRIO IP — fuse programming, GPSB register access |
| DDRIOIp | `programDDRIOFuses()` | Write fuse data to DDRIO via GPSB |
| DDRIOIp | `programDDRIOBiosSaiPolicy()` | SAI access control policy |
| DDRIOIp | `read32bitReg()` / `write32bitReg()` | IOSF sideband register access |
| ThermalTopology | `src/cfgdata/*/thermal_topology.cpp` | Maps DTS sensors to DDRIO ITD domains |
| ITD domains | `ITD_VCCDDRD_0..3` | 4 simple thermal domains, one per MC pair |

#### PCode Trace Messages

| Trace Message | Fields | Description |
|--------------|--------|-------------|
| `TEMPERATURE_DDRIO` | `MAX_TEMP` [15:0], `MIN_TEMP` [31:16] | DDRIO domain max/min temp (S7.8 °C) |

#### Timing Constants

| Constant | Value | Description |
|----------|-------|-------------|
| PDC timer interval | ~127 ms | Periodic RCOMP trigger |
| RCOMP processing (worst case) | 40–45 µs | Full 4-stage calibration |
| RCOMP processing (best case) | < 100 ns | If `rcomp_valid` still asserted |
| Max RCOMP disable window | 15 µs | `hsd_13011934947_MAX_TIME_FOR_RCOMP_DISABLE_TSC` |
| Max OPPSR disable window | 2 µs | `hsd_13011934947_MAX_TIME_FOR_OPPSR_DISABLE_TSC` |
| C6 QDENY timer target | 50–60 µs | Must exceed RCOMP window + valid window |
| C6 QDENY timer range | 42–84 µs | Min/max from HAS |

#### PythonSV Validation Functions

| Function | Module | Description |
|----------|--------|-------------|
| `check_ddrio_errors()` | `mc/dmr_mc_show.py` | Check DDRIO PHY error fields (drift_comp_err, dts_temp_err, etc.) |
| `check_ddrio_errors()` | `mc/dmr_mc_is.py` | Interactive version of error check |
| `Xover_DMR_VT_Drift.py` | `users/diromero/xover/` | VT drift analysis — reads PLL/COMP DTS temperatures |

#### DDRIO DTS Sensor Mapping

| Primecode Name | DTS Instance | Uncore Name | ITD Domain |
|---------------|-------------|-------------|------------|
| `MC0_TEMP_C0R34` | `ra_ra_dts_0_ddrio_0` | `ddr_a_c0r34_ddrio` | `ITD_VCCDDRD_0` |
| `MC1_TEMP_C0R56` | `ra_ra_dts_0_ddrio_1` | `ddr_b_c0r56_ddrio` | `ITD_VCCDDRD_1` |
| `MC2_TEMP_C9R34` | `ra_ra_dts_0_ddrio_2` | `ddr_a_c9r34_ddrio` | `ITD_VCCDDRD_2` |
| `MC3_TEMP_C9R56` | `ra_ra_dts_0_ddrio_3` | `ddr_b_c9r56_ddrio` | `ITD_VCCDDRD_3` |

#### BIOS Knobs

| Knob | Values | Description |
|------|--------|-------------|
| `DfxDdrioXoverDriftComp` | 0=Disable, 1=Enable, 2=Auto | Crossover drift compensation control |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DDR PHY Gen4 HAS](https://docs.intel.com/documents/iparch/ddrphy/has/Gen4/releases/R2302/HAS/DdrPhyGen4Has.html) | RCOMP, DTS temp distribution, crossover drift comp |
| HAS | [DMR Memory Power & Thermal](https://docs.intel.com/documents/pm_doc/src/server/dmr/ip_pm_features/dmr_ddr5_mcr.html) | DDRIO temperature compensation in DDR5 MCR context |
| HAS | [DMR CBB ITD/TTD](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/ITD/ITD.html) | ITD_VCCDDRD_0..3 domain definitions, dynamic TD compensation |
| HAS | [DMR Thermal HAS (IMH)](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#itd) | IMH thermal management with DDRIO sensors |
| HAS | [Socket Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Cross-product socket thermal |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS — memory thermal |
| Primecode src | `src/ip/ddrio/v2_0/ddrio.hpp` / `ddrio.cpp` | DDRIOIp class — fuse programming, GPSB access |
| Primecode src | `src/cfgdata/*/thermal_topology.cpp` | DDRIO DTS → ITD domain mapping |
| Primecode src | `src/doc/thermals.dox` | DDRIO thermal architecture documentation |
| Primecode src | `src/doc/mem_controller.dox` | "DDRIO is part of CPU thermal domain" |
| Primecode src | `src/doc/socket_rapl.dox` | DDRIO power in Socket RAPL |
| PCode src | `source/pcode/drivers/sa/memory_subsystem.h` / `.cpp` | MemorySubSystem RCOMP, DVFS, temp compensation |
| PCode src | `source/pcode/flows/thermals/thermal_sampling.h` | ThermalSamplingFlow — DDRIO temp database |
| PCode trace | `source/trace/punit_trace_orig.xml` | `TEMPERATURE_DDRIO` trace message |
| Test scripts | `mc/dmr_mc_show.py::check_ddrio_errors()` | DDRIO PHY error checking |
| Test scripts | `pm/Active_PM/Thermal_Management/.../thermalManagement.py` | DDRIO DTS sensor mapping |
| Test scripts | `users/diromero/xover/Xover_DMR_VT_Drift.py` | VT drift temperature analysis |

### Related Sightings
<!-- No DDRIO temp-comp-specific sightings catalogued yet — populate as NWP silicon debug progresses -->
<!-- Known HSD workarounds in PCode: HSD 13011934947 (RCOMP/OPPSR), HSD 13013662172 (alt RCOMP), HSD 13013947115 (manual comp C-state), HSD 13012758704 (DVFS voltages), HSD 13011309473 (SAG ramp) -->

