# Memory Thermal > Memhot

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [Memory Thermal](memory_thermal_main.md)

## Baseline (DMR)

### What is MEMHOT?
MEMHOT is a bidirectional platform signal (`MEMHOT#`, active low) communicating memory thermal stress
between CPU and platform. Two modes: **MEMHOT_IN** (platform → CPU: platform asserts MEMHOT# to signal
DRAM stress; MC applies external throttle level from `memhot_ext_thrt`) and **MEMHOT_OUT** (CPU → platform:
MC asserts MEMHOT# when DIMM temp ≥ selected threshold; platform can alert BMC or fan controller).
Optionally routes to PROCHOT# via `IO_FIRM_CONFIG.MEMHOT0/1_TO_PROCHOT_OUT_EN`.

### Topology
- MC per-DIMM temp comparison → MEMHOT_OUT pin → platform / fan / BMC
- Platform TSOD alert or BMC → MEMHOT_IN pin → MC external throttle
- MEMHOT→PROCHOT route: `pma_punit_temp_hot[0]` → xxprochot output → CPU freq throttle

### Operating Principle
MR4/TSOD/PECI temperature source writes `dimm_temp_snapshot`. MC compares vs `temp_memhotout_sel`
threshold. MEMHOT_IN assertion applies `memhot_ext_thrt.throttle_exmemhot_level` independently of
temperature-threshold throttling (THRT_MID/HI/CRIT).

### Boot-Time Init
BIOS programs throttle thresholds, levels, MEMHOT_OUT threshold select, external MEMHOT throttle level,
and optional PROCHOT routing. Feature can be disabled via BIOS knob.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| MC thermal engine | IMH | Compares `dimm_temp_snapshot` vs `temp_memhotout_sel` threshold; asserts MEMHOT_OUT; detects MEMHOT_IN; applies external throttle level | MEMHOT# pin (bidirectional); `dimm_temp_snapshot`, `memhot_ext_thrt` | DMR DDR5/MCR HAS |
| GPIO / IO pad | SoC | Routes MEMHOT# pin bidirectionally; routes to PROCHOT# when `IO_FIRM_CONFIG.MEMHOT0/1_TO_PROCHOT_OUT_EN=1` | `pma_punit_temp_hot[0]`, xxprochot | SoC GPIO HAS |
| TPMI OPC block | IMH | Exposes DIMM temps for MEMHOT threshold comparison when using PECI/MR4 CLTT | `OPC_DIMM_TEMPS` | DMR DDR5/MCR HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Primecode CLTT | `src/flow/cltt/` | Writes `dimm_temp_snapshot` from MR4/PECI source; drives MEMHOT_OUT comparison path | `writeMcTemperatureRegisters()` | Primecode CLTT flow |
| PCode | CBB PUnit | Reads MEMHOT assertion; routes MEMHOT→PROCHOT via `IO_FIRM_CONFIG`; integrates with PROCHOT throttle path | `IO_FIRM_CONFIG.MEMHOT0_TO_PROCHOT_OUT_EN` | PCode thermal flows |
| BIOS | Platform init | Programs all MEMHOT thresholds, throttle levels, PROCHOT routing, enable/disable | `dimm_temp_thresh`, `memhot_ext_thrt`, `IO_FIRM_CONFIG` | NWP BIOS HAS |
| BMC | Platform | Asserts MEMHOT_IN via TSOD alert output or platform thermal sensor | MEMHOT# pin assertion | Platform BMC FW |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MC `dimm_temp_ev_ctrl_0` | MCHBAR GPSB | RW (BIOS) | `temp_memhotout_sel`: selects which threshold (Lo/Mid/Hi/MemTrip) triggers MEMHOT_OUT | DMR DDR5/MCR HAS |
| MC `memhot_ext_thrt` | MCHBAR GPSB | RW (BIOS) | `throttle_exmemhot_level`: BW throttle applied when MEMHOT_IN asserted | DMR DDR5/MCR HAS |
| `IO_FIRM_CONFIG` | CBB PUnit GPSB | RW (BIOS/PCode) | `MEMHOT0/1_TO_PROCHOT_OUT_EN`: routes MEMHOT to PROCHOT# pin | SoC PM HAS |
| `IA_PERF_LIMIT_REASONS` | MSR 0x1B1 | RO (OS) | Reflects thermal throttle when MEMHOT routed to PROCHOT | IA32 Arch SDM |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| MEMHOT_IN external throttle level | BIOS programmed (`memhot_ext_thrt.throttle_exmemhot_level`) | DMR DDR5/MCR HAS |
| MEMHOT_OUT threshold | Selectable: Lo / Mid / Hi / MemTrip (`temp_memhotout_sel`) | DMR DDR5/MCR HAS |
| PROCHOT routing | Optional; `IO_FIRM_CONFIG.MEMHOT0/1_TO_PROCHOT_OUT_EN` | SoC PM HAS |
| MEMHOT disabled test | Verifies MEMHOT_IN ignored + MEMHOT_OUT suppressed; THRT_MID/HI/CRIT still active | NWP PM test plan TC |
| NWP delta | Carried from DMR | NWP PM MAS |

## NWP Delta

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| Feature supported | ✅ Carried from DMR | NWP PM MAS |
| IMH topology | Single NIO; MEMHOT# pin routing identical | NWP PM MAS |
| MEMHOT→PROCHOT routing | Same mechanism | IO_FIRM_CONFIG |

## Legacy (Human-Curated Reference)

*All original content preserved below for reference.*

### Architecture Summary

**MEMHOT** is a bidirectional platform signal (`MEMHOT#`, active low) that communicates memory thermal stress between the CPU and the platform/DIMM. It has two distinct modes:

#### MEMHOT_IN (External → CPU)
- **What**: The platform or DIMM asserts the `MEMHOT#` input pin to the CPU, signaling that DRAM is thermally stressed.
- **Source**: Typically driven by a DIMM's on-board thermal sensor (TSOD alert output) or a platform thermal sensor via the baseboard management controller.
- **CPU response**: The MC detects the `MEMHOT#` assertion and applies external MEMHOT throttling — reducing memory bandwidth according to `memhot_ext_thrt.throttle_exmemhot_level`. This throttle level is separate from the temperature-threshold-based throttle levels (THRT_MID/HI/CRIT).
- **Use case**: Platforms where DIMM-local sensors detect thermal events faster than CPU-side polling (MR4/TSOD).

#### MEMHOT_OUT (CPU → External)
- **What**: The CPU asserts the `MEMHOT#` output pin to the platform when DIMM temperature (as measured by MR4, TSOD, or PECI CLTT) exceeds a configurable threshold.
- **Trigger**: MC compares per-DIMM temperatures from `dimm_temp_snapshot` against the threshold selected by `dimm_temp_ev_ctrl_0.temp_memhotout_sel` (selectable: Lo, Mid, Hi, or MemTrip threshold).
- **Platform response**: The platform can use the `MEMHOT#` output to activate chassis fans, alert the BMC, or trigger other thermal mitigation. PCode can also route `MEMHOT` to the `PROCHOT#` output pin via `IO_FIRM_CONFIG.MEMHOT0_TO_PROCHOT_OUT_EN` / `MEMHOT1_TO_PROCHOT_OUT_EN` — this forces CPU frequency throttling when memory is hot.

#### MR4-based Memhot
When CLTT is in MR4 mode (`MR4_CLTT_ENABLE=1`), Primecode firmware reads JEDEC MR4 temperature codes from the MC, converts them to Celsius, and writes them to MC `dimm_temp_snapshot` registers. The MC then compares these temperatures against the BIOS-programmed thresholds. If temp ≥ the selected MEMHOT_OUT threshold, the MC asserts `MEMHOT#` output. Similarly, if temp ≥ a throttle threshold (Lo/Mid/Hi), the MC applies bandwidth throttling.

#### Memhot Disabled (Test: "Memhot Disables MR4-based")
When Memhot is disabled via BIOS knob, the MC ignores the `MEMHOT#` input and does not assert `MEMHOT#` output regardless of DIMM temperature. The test verifies that: (a) external MEMHOT_IN assertion does not trigger throttling, (b) MEMHOT_OUT is not asserted even when DIMM temps exceed thresholds, and (c) normal MR4-based temperature-threshold throttling (THRT_MID/HI/CRIT) still functions independently of the MEMHOT signal.

### Execution Flow

```
1. BIOS Configuration
   ├─ Programs MC throttle thresholds: dimm_temp_thresh (Lo/Mid/Hi/MemTrip)
   ├─ Programs throttle levels: dimm_temp_thrt_lmt (THRT_MID/HI/CRIT)
   ├─ Programs MEMHOT_OUT threshold select: dimm_temp_ev_ctrl_0.temp_memhotout_sel
   ├─ Programs external MEMHOT throttle: memhot_ext_thrt.throttle_exmemhot_level
   ├─ Optionally routes MEMHOT→PROCHOT: IO_FIRM_CONFIG.MEMHOT0/1_TO_PROCHOT_OUT_EN
   └─ Enables/disables MEMHOT feature via BIOS knob

2. Temperature Source (MR4 / TSOD / PECI)
   ├─ MR4 mode: MC reads MR4 → Primecode converts → writes dimm_temp_snapshot
   ├─ TSOD mode: MC reads TSOD via SPD I3C → auto-populates dimm_temp_snapshot
   └─ PECI mode: BMC pushes via TPMI → Primecode writes dimm_temp_snapshot

3. MEMHOT_OUT Path (CPU → Platform)
   ├─ MC compares dimm_temp_snapshot vs temp_memhotout_sel threshold
   ├─ If temp ≥ threshold → MC asserts MEMHOT# output pin
   ├─ If IO_FIRM_CONFIG.MEMHOT0_TO_PROCHOT_OUT_EN=1:
   │   └─ pma_punit_temp_hot[0] signal drives xxprochot output → CPU freq throttle
   └─ Platform detects MEMHOT# → fan/BMC response

4. MEMHOT_IN Path (Platform → CPU)
   ├─ Platform/DIMM asserts MEMHOT# input pin
   ├─ MC detects assertion
   ├─ MC applies memhot_ext_thrt.throttle_exmemhot_level throttle
   └─ Bandwidth reduction for duration of MEMHOT# assertion

5. OS / Platform Observable
   ├─ DDR_THERM_STATUS register updated
   ├─ Bandwidth reduction observable via PMONs
   ├─ MEMHOT# pin state observable via platform GPIO / BMC
   └─ If routed to PROCHOT: IA_PERF_LIMIT_REASONS reflects thermal throttle
```

### Key Registers & Interfaces

#### MC Registers (per MC, MCHBAR GPSB)

| Register | Key Fields | Description |
|----------|-----------|-------------|
| `dimm_temp_thresh` | `dimm_temp_low/mid/high_maxthreshold` | Throttle thresholds (Lo/Mid/Hi) |
| `dimm_temp_thresh` | `dimm_temp_memtrip_threshold` | MEMTRIP threshold (8-bit, default 0xFF) |
| `dimm_temp_thrt_lmt` | `THRT_MID`, `THRT_HI`, `THRT_CRIT` | Bandwidth throttle levels per threshold band |
| `dimm_temp_ev_ctrl_0` | `temp_memhotout_sel` | Selects which threshold triggers MEMHOT_OUT |
| `dimm_temp_snapshot_0/1` | `dimm_temp_sch0/1`, `dimm_refresh_rate` | Current DIMM temp and refresh rate |
| `memhot_ext_thrt` | `throttle_exmemhot_level` | Throttle level applied when external MEMHOT_IN asserted |
| `dimm_bw_thrt` | `throttle_bw_window` | Throttle BW window (1–4 s) |

#### PCode / CBB Punit Registers

| Register | Key Fields | Description |
|----------|-----------|-------------|
| `IO_FIRM_CONFIG` | `MEMHOT0_TO_PROCHOT_OUT_EN` (bit 6) | Routes pma_punit_temp_hot[0] → PROCHOT output |
| `IO_FIRM_CONFIG` | `MEMHOT1_TO_PROCHOT_OUT_EN` (bit 7) | Routes pma_punit_temp_hot[1] → PROCHOT output |
| `pcu_info.xml` | `wave3_memhot = 1` | Feature scope variable — Memhot enabled in Wave3 |

#### PMR/NWP THERMTRIP_CONFIG_CFG

| Register | Key Fields | Description |
|----------|-----------|-------------|
| `THERMTRIP_CONFIG_CFG` | `memtrip0_to_xxthermtrip_n_en` (bit 4) | Routes memtrip0 → thermtrip output |
| `THERMTRIP_CONFIG_CFG` | `memtrip1_to_xxthermtrip_n_en` (bit 5) | Routes memtrip1 → thermtrip output |
| `THERMTRIP_CONFIG_CFG` | `memtrip0_to_xxmemtrip_n_en` (bit 6) | Routes memtrip0 → memtrip output pin |
| `THERMTRIP_CONFIG_CFG` | `memtrip1_to_xxmemtrip_n_en` (bit 7) | Routes memtrip1 → memtrip output pin |

#### MC Throttle Threshold Behavior (shared with PECI/MR4/TSOD modes)

| DIMM Temperature Condition | MC Action |
|---|---|
| `Temp < 2x refresh threshold` | 1x refresh, no bandwidth throttle |
| `2x refresh ≤ Temp < Temp_Lo` | 2x refresh (if enabled), no BW throttle |
| `Temp_Lo ≤ Temp < Temp_Mid` | Throttle using `THRT_MID` |
| `Temp_Mid ≤ Temp < Temp_Hi` | Throttle using `THRT_HI` |
| `Temp_Hi ≤ Temp < Temp_MemTrip` | Throttle using `THRT_CRIT` + MEMHOT_OUT asserted |
| `Temp ≥ Temp_MemTrip` | Assert `MEMTRIP#` (see [Memtrip](memtrip.md)) |
| External `MEMHOT#` asserted | Throttle using `throttle_exmemhot_level` |

#### Primecode Interfaces

| Interface | ID / Path | Description |
|-----------|----------|-------------|
| CLTT flow | `CLTT::writeMcTemperatureRegisters()` | Writes temps to MC dimm_temp_snapshot |
| CLTT flow | `CLTT::collectTempPeriodicallyMr4Mode()` | MR4 temp collection (1 ms periodic) |
| CLTT flow | `CLTT::storeTpmiClttTemps()` | PECI CLTT temp storage |
| HPM opcode | `DIMM_TEMPERATURE_0/1` | Inter-die DIMM temp exchange |
| TPMI | `OPC_DIMM_TEMPS_0..3` | Published DIMM temps for OOB/PECI |
| B2P mailbox | `WRITE_PCU_MISC_CONFIG` | MR4/PECI CLTT enable bits |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR DDR5/MCR - MR4 CLTT](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html#mr4-based-cltt) | MR4 CLTT including MEMHOT architecture |
| HAS | [DMR Thermal HAS (IMH)](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#itd) | IMH thermal management |
| HAS | [Socket Thermal Mgmt HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Cross-product socket thermal |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS — memory thermal |
| Primecode src | `src/flow/cltt/cltt_common/v2_0/cltt.hpp` / `cltt.cpp` | Core CLTT flow (MR4, TSOD, HPM, TPMI) |
| Primecode src | `src/flow/cltt/cltt_io_base/v1_0/pecicltt_mailbox_base.hpp` | PECI CLTT PCS mailbox handler |
| Primecode cfg | `src/cfgdata/gnr_dev/v1_0/static/pcu_info.xml` | `MEMHOT0/1_TO_PROCHOT_OUT_EN` field definitions |
| Primecode cfg | `src/cfgdata/pmr_cnic_ioh/v1_0/ip_headers/mc_MsgMem_GPSB.hpp` | `dimm_temp_memtrip_threshold`, `mr4_temp_memtrip_threshold` |
| PCode cfg | `src/cfgdata/gnr_dev/v1_0/static/pcu_info.hpp` | `memhot0/1_to_prochot_out_en` bit definitions |
| Cross-ref | [MR4](mr4.md) | MR4-based temp source for MEMHOT |
| Cross-ref | [PECI](peci.md) | PECI-based temp source for MEMHOT |
| Cross-ref | [Memtrip](memtrip.md) | MEMTRIP escalation from MEMHOT thresholds |

#### Test Case Architecture Notes

| Test | What It Validates |
|------|-------------------|
| **MR4 Memhot_In** (22022421411) | MR4 mode: inject external MEMHOT# → verify MC applies `throttle_exmemhot_level` BW throttle |
| **MR4 Memhot_Out** (22022421412) | MR4 mode: raise DIMM MR4 temp above `temp_memhotout_sel` threshold → verify MEMHOT# output asserted |
| **Memhot Disables MR4** (22022421415) | Disable Memhot via BIOS → verify no MEMHOT_IN throttle and no MEMHOT_OUT assertion; MR4 threshold throttling (THRT_MID/HI/CRIT) still works |
| **Memhot_In** (22022421422) | TSOD/default mode: external MEMHOT# → BW throttle verification |
| **Memhot_Out** (22022421423) | TSOD/default mode: DIMM temp above threshold → MEMHOT# output assertion |

### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->

