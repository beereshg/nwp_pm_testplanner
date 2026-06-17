# SoC Thermal > MCAs (Thermal Firmware MCAs)

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: PCode generates a firmware UCNA MCA ("DIE_TOO_HOT") when DTS temperature exceeds `eff_tj_max + 10°C` sustained for ≥3mS — the last software-visible warning before thermtrip. System continues running; EMTTM is already at max throttle.

**Topology**:
```
  Temperature rising ──────────────────────────────────────────────────────────>

  Core EMTTM PID  →  CBB EMTTM PID  →  OOS check (+10°C + 3mS timer)  →  DIE_TOO_HOT  →  Thermtrip
  (~300μS)            (~1mS)             PCode thermal_report.cpp           UCNA MCA         HW ~nS
  freq limit          CCF limit          OUT_OF_SPEC_STATUS=1 → SOCKET_THERMAL → iMH         shutdown
                                         IA32_PACKAGE_THERM_STATUS[OOS]
```

**Key operational principle**: OOS timer (`thermal_breach_time`) accumulates when `soc_max_temperature ≥ eff_tj_max + 10°C`; resets on recovery. Known false positives: Gen1 DTS rawcode=0 → ~150°C; Gen2.6 DTS CDC timing bug (saturated 0x1FF = 191°C). UCNA threshold mitigation: PrimeCode `ucna_threshold` pcudata variable (default=2 consecutive events).

**Boot activation**: OOS/MCA detection active once PCode slow loop starts at PH2.52.

PCode generates a firmware **UCNA (Uncorrectable Non-Actionable) MCA** — logged as **"DIE_TOO_HOT"** — when a DTS temperature reading exceeds a critical threshold, indicating the die has reached or exceeded a dangerous temperature that EMTTM could not control. This is distinct from thermtrip (hardware shutdown) — the MCA is a software-visible error notification that the system was dangerously hot.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| DTS Gen1 (SA Thermal Puller) | CBB Base Die | SOC/CCF temperature readings evaluated by PCode for OOS threshold; Gen1 rawcode=0 bug → false 150°C | `PCU_CR_DTS_TEMP_IA_CCP`, `PCU_CR_DTS_TEMP_SOC`, `PCU_CR_DTS_TEMP_CCF` | CBB Thermal Mgmt HAS |
| DTS Gen2.6 | CBB Top Die (per core) | Core temperature; CDC timing bug can saturate min/max registers → 0x1FF = 191°C (NVL HSD 14025678245) | SHORT_TELEM Domain0 min/max | ACP PM HAS |
| CBB MCA Bank | CBB Base Die | Hardware machine-check bank written by PCode with DIE_TOO_HOT UCNA error code; OS-visible | `IA32_MC_STATUS`, `IA32_MC_ADDR`, `IA32_MC_MISC` | Intel SDM / MCA HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core PMA | No direct DIE_TOO_HOT role; Core EMTTM PID runs before OOS path; provides SHORT_TELEM Core DTS input | — | — |
| PCode (CBB) | CBB Base Die | Evaluates OOS condition each slow loop; logs DIE_TOO_HOT UCNA MCA; sends `OUT_OF_SPEC_STATUS=1` in `SOCKET_THERMAL` HPM | `thermal_report.cpp`; `thermal_interface.h` (OOS::temperature_offset=10°C, OOS::thermal_timer_threshold=3mS); `thermal_sampling.cpp` | PCode src |
| PrimeCode (IMH) | IMH die | Receives `SOCKET_THERMAL[OUT_OF_SPEC_STATUS]`; propagates to `IA32_PACKAGE_THERM_STATUS[OOS_STATUS]` and `IA32_THERM_STATUS[OOS_STATUS]`; UCNA threshold mitigation (`ucna_threshold` pcudata var, default=2 consecutive events) | Socket Thermal HAS; PrimeCode pcudata | PrimeCode src |
| BIOS / UEFI | Platform | No active role at MCA time; OS (WHEA/mcelog) handles UCNA notification; platform firmware handles post-thermtrip shutdown | Platform MCA handling | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_MC_STATUS` | Per MCA bank | RO | DIE_TOO_HOT UCNA error code; visible in `mcelog` / WHEA; system continues running | Intel SDM |
| MSR `IA32_THERM_STATUS` | 0x19C (per-core) | RO/RWC | [4/5] `OUT_OF_SPEC_STATUS`/`LOG` — per-core OOS state | Intel SDM |
| MSR `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | RO/RWC | [4/5] `OUT_OF_SPEC_STATUS`/`LOG` — package OOS; [23:16] TEMPERATURE | Intel SDM |
| PCode internal (`pcudata`) | `pcode.var.thermals` | Debug RO | `soc_minmax_temp.maxT()`, `thermal_breach_time`, `ucna_threshold` variable | Legacy Key Registers |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| OOS temperature offset | +10 | °C | OOS when max_temp ≥ eff_tj_max + 10°C (`OOS::temperature_offset`) | Legacy Execution Flow |
| OOS timer threshold (PCode) | 3 | mS | Sustained breach before OOS asserted and UCNA MCA logged | Legacy Execution Flow |
| UCNA threshold mitigation | 2 | consecutive events | PrimeCode `ucna_threshold` pcudata variable (default=2); prevents single-glitch false positive | Legacy Execution Flow |
| DTS Gen1 false temperature (rawcode=0) | ~150 | °C | rawcode=0 → (0x1AC−64)/2 ≈ 150°C; DTS IP fuse/RTL bug | Legacy Execution Flow |
| DTS Gen2.6 saturated temperature (CDC bug) | 0x1FF → 191 | °C | CDC timing corruption of min/max registers; NVL HSD 14025678245; HW fix targets DMR B0 | Legacy Sighting Reference |

## NWP Delta

**MCA thermal errors are supported on NWP** with limitations.

- Error reporting via MCA banks is supported
- Some advanced features (eMCA gen2, de-escalation) are **not present** in NWP
- Basic thermal MCA reporting (OOS, Thermtrip, PROCHOT) preserved

### Validation Impact
- Basic MCA thermal error tests apply
- Skip eMCA gen2 and de-escalation tests on NWP
- Verify MCA bank configuration on NIO (single die)

## Legacy (Human-Curated Reference)

### Architecture Summary

PCode generates a firmware **UCNA (Uncorrectable Non-Actionable) MCA** — logged as **"DIE_TOO_HOT"** — when a DTS temperature reading exceeds a critical threshold, indicating the die has reached or exceeded a dangerous temperature that EMTTM could not control. This is distinct from thermtrip (hardware shutdown) — the MCA is a software-visible error notification that the system was dangerously hot.

#### Thermal MCA Context in the Hierarchy

```
  Temperature rising
  ──────────────────────────────────────────────────────────→
  
  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────────┐  ┌──────────┐
  │ Core EMTTM │→ │ CBB EMTTM  │→ │ OOS Status │→ │ DIE_TOO_HOT  │→ │Thermtrip │
  │ PID ~300μS │  │ PID ~1mS   │  │ to iMH HPM │  │ UCNA MCA     │  │ HW ~nS   │
  │ freq limit │  │ CCF limit  │  │ eff_tj+10°C│  │ FW detected  │  │ shutdown │
  └────────────┘  └────────────┘  └────────────┘  └───────────────┘  └──────────┘
  Normal operation                 Warning         Error logged       Last resort
```

#### OOS (Out-Of-Spec) Detection — The MCA Trigger

PCode evaluates OOS in every slow-loop iteration (`thermal_report.report_tx`):

```
oos_temperature = eff_tj_max + OOS::temperature_offset   // +10°C (from thermal_interface.h)

if (soc_max_temperature >= oos_temperature):
    thermal_breach_time += time_delta
    if (thermal_breach_time >= OOS::thermal_timer_threshold):  // 3mS in PCode
        oos_check = true
else:
    thermal_breach_time = 0                                    // reset on recovery
```

The `oos_check` flag (OR'd with `emttm_oos_timer_expired`) is sent to iMH via `SOCKET_THERMAL` HPM `OUT_OF_SPEC_STATUS` bit. PCode also logs the DIE_TOO_HOT UCNA MCA when a DTS reports a temperature exceeding the threshold.

#### DIE_TOO_HOT MCA Characteristics

| Property | Value |
|----------|-------|
| **MCA Type** | UCNA (Uncorrectable Non-Actionable) |
| **Source** | PCode firmware (CBB) |
| **Trigger** | DTS temperature exceeds critical threshold |
| **System Impact** | MCA logged to `IA32_MC_STATUS` — system continues running |
| **OS Visibility** | `IA32_MC_STATUS` UCNA, visible in `mcelog` / WHEA |
| **Throttling** | EMTTM already at max throttle; MCA is informational |

#### Temperature Data Flow to MCA

```
DTS sensor ──→ Thermal puller (base) ──→ PCU_CR_DTS_TEMP_*
              or SHORT_TELEM (core)
                    │
                    ▼
            ThermalSamplingFlow::sample_*_temps_tx()
                    │
                    ▼
            soc_minmax_temp (all CBB max)
                    │
                    ▼
            ThermalReport::send_updated_report_to_imh()
                    │
                    ├──→ OOS check: soc_max_temp >= eff_tj_max + 10°C ?
                    │       Yes + timer expired → OOS_STATUS=1 in SOCKET_THERMAL HPM
                    │
                    └──→ DIE_TOO_HOT: temp > threshold → UCNA MCA logged
```

---

### Execution Flow

#### Normal Path (No MCA)

1. **DTS samples** temperature from diodes (Gen1: puller, Gen2.6: push)
2. **PCode `ThermalSamplingFlow`** reads/receives temperatures each slow loop
3. **PCode `ThermalReport`** calculates `soc_max_temperature` = max over all CBB domains
4. **OOS check**: `soc_max_temperature < eff_tj_max + 10°C` → no MCA, OOS_STATUS=0
5. **HPM sent** to iMH: `SOCKET_THERMAL[OUT_OF_SPEC_STATUS=0, MAX_TEMP, margins]`

#### MCA Path (DIE_TOO_HOT)

1. DTS reports temperature exceeding critical threshold (e.g., >115°C when TjMax=105°C)
2. PCode detects `soc_max_temperature >= eff_tj_max + 10°C` sustained for ≥3mS
3. PCode logs **DIE_TOO_HOT UCNA MCA** to machine check bank
4. PCode sends `SOCKET_THERMAL[OUT_OF_SPEC_STATUS=1]` to iMH
5. iMH propagates to `IA32_PACKAGE_THERM_STATUS[OOS_STATUS]` and `IA32_THERM_STATUS[OOS_STATUS]`
6. OS receives UCNA — `mcelog` records "DIE_TOO_HOT"

#### Invalid Temperature Path (Known DMR A0 Sighting)

A known failure mode (not a real overtemp) triggers DIE_TOO_HOT:

1. **DTS rawcode corruption** → DTS reports 0 rawcode → converts to ~150°C (`(0x1AC−64)/2`)
2. Temperature jumps instantaneously from ~40°C to 150°C (no ramp)
3. PCode sees 150°C > eff_tj_max + 10°C → logs DIE_TOO_HOT MCA
4. System is NOT actually hot — false positive caused by DTS IP bug

**Root causes identified**:
- **Gen1 DTS (iMH base, DDR_A)**: Rawcode of 0 published — DTS fuse/RTL bug causing ADC rawcode to report zero. Not related to one-shot mode.
- **Gen2.6 DTS (CBB core)**: CDC timing bug in dts-clk → cri-clk domain crossing corrupts min/max registers. Saturated value 0x1FF (191°C) observed. Known NVL issue HSD 14025678245 — HW fix targets DMR B0.
- **Mitigation**: PrimeCode UCNA threshold patch — only trigger UCNA after `N` consecutive DIE_TOO_HOT events (configurable via `pcudata` variable `ucna_threshold`, default=2)

---

### Key Registers & Interfaces

#### MCA Registers

| Register | Description |
|----------|-------------|
| `IA32_MC_STATUS` | Machine check status — contains MCA error code, UCNA indication |
| `IA32_MC_ADDR` | Faulting address (not meaningful for thermal MCA) |
| `IA32_MC_MISC` | Additional MCA info |

#### Thermal Status Registers (MCA-Adjacent)

| MSR/CR | Address | Key Fields |
|--------|---------|------------|
| `IA32_THERM_STATUS` | 0x19C | `OOS_STATUS[4]` — per-core Out-Of-Spec status |
| `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | `OOS_STATUS` — package-level OOS (from iMH) |
| `IA32_TEMPERATURE_TARGET` | 0x1A2 | `REF_TEMP[23:16]` — fused TjMax reference |

#### PCode Internal State

| Variable | Description |
|----------|-------------|
| `soc_minmax_temp.maxT()` | Current max temperature across all CBB domains |
| `OOS::temperature_offset` | 10°C — OOS threshold offset above eff_tj_max |
| `OOS::thermal_timer_threshold` | 3mS — sustained breach time before OOS asserted |
| `thermal_breach_time` | Accumulated time above OOS threshold |
| `emttm_oos_timer_expired` | EMTTM-driven OOS flag (OR'd with timer-based OOS) |

#### HPM Messages

| Message | Direction | Relevant Fields |
|---------|-----------|-----------------|
| `SOCKET_THERMAL` | CBB → Root | `OUT_OF_SPEC_STATUS` — OOS flag sent to iMH |

#### DTS Observability (Debug)

| Register/Variable | What It Shows |
|-------------------|--------------|
| `PCU_CR_DTS_TEMP_IA_CCP[N]` | Per-CCP temperature — which CCP is hot |
| `PCU_CR_DTS_TEMP_SOC[0..2]_CR0/1` | SOC DTS temperatures — base die sensors |
| `PCU_CR_DTS_TEMP_CCF[N]` | CCF DTS temperatures — ring/LLC sensors |
| `pcode.var.thermals` (pcudata) | PCode internal min/max values — debug aid |
| `punit_regs` (pcudata) | Punit register snapshot at time of MCA |

---

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS (CBB Thermal Mgmt) | [DMR CBB Thermal Management](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) | OOS definition, thermal reporting |
| FAS (PCode Thermal) | [Pcode Thermal FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/Thermals/Thermal%20Management_FAS.html) | PCode implementation — OOS timer, MCA generation |
| PCode src | `source/pcode/flows/thermals/thermal_report.cpp` | OOS detection + HPM send logic |
| PCode src | `source/pcode/flows/thermals/thermal_interface.h` | OOS constants: `temperature_offset=10°C`, `thermal_timer_threshold=3mS` |
| PCode src | `source/pcode/flows/thermals/thermal_sampling.cpp` | Temperature collection from DTS IOs |
| Related KB | [ACP Thermal](acp.md) | EMTTM, eff_tj_max calculation, DTS topology |
| Related KB | [CBB DTS & Telemetry](cbb_dts_telemetry.md) | DTS sensor types, telemetry pipeline |
| HSD | 14025678245 | NVL Gen2.6 DTS IP CDC timing bug — min/max register corruption |

#### Validation Approach

- **Inject invalid temperature**: Use TAP overrides to inject a temperature above `eff_tj_max + 10°C` (e.g., 150°C) into a DTS sensor. Verify PCode generates DIE_TOO_HOT UCNA MCA within the timer threshold.
- **Verify MCA fields**: Check `IA32_MC_STATUS` for UCNA type, confirm error code indicates thermal origin.
- **Verify OOS propagation**: Confirm `SOCKET_THERMAL[OUT_OF_SPEC_STATUS=1]` sent to iMH. Confirm `IA32_PACKAGE_THERM_STATUS[OOS_STATUS]` and `IA32_THERM_STATUS[OOS_STATUS]` bits set.
- **Recovery**: Remove temperature injection → verify `thermal_breach_time` resets, OOS clears, no further MCAs generated.
- **Below threshold**: Inject temperature at `eff_tj_max + 9°C` → verify NO MCA generated (below 10°C offset).
- **Brief spike**: Inject temperature above threshold for <3mS then remove → verify NO MCA (timer not expired).
- **Multiple DTS domains**: Test injection on SOC DTS (base), CCF DTS, and Core DTS (top) separately — each should independently trigger DIE_TOO_HOT when exceeding threshold.
- **Disabled core**: Disable a core, inject on remaining core — verify MCA still triggers from the enabled sensor only.

---

### Related Sightings

| HSD | Status | Summary |
|-----|--------|---------|
| (from pm_sighting_query_results) | Active/Debug | DIE_TOO_HOT from DDR_A DTS rawcode=0 (150°C false positive) on iMH Gen1 DTS. Root cause: DTS IP fuse/RTL bug. Follows part. |
| (from pm_sighting_query_results) | Active/Debug | DIE_TOO_HOT from CBB Gen2.6 core DTS — CDC timing bug corrupts min/max registers. Saturated 0x1FF (191°C). Related to NVL HSD 14025678245. |

> **NWP Risk**: Both DTS IP bugs may carry forward if same DTS IP versions are reused. Verify DTS IP revision in NWP tapeout.

---

### NWP Delta

> **Items to verify for NWP** (not yet confirmed — check NWP HAS when available):

| Area | Question | DMR Baseline |
|------|----------|--------------|
| OOS threshold | Same `eff_tj_max + 10°C`? | DMR: 10°C offset (fuse `OOS_THRESHOLD_OFFSET`) |
| OOS timer | Same 3mS PCode timer? (HAS says 20mS for HPM OOS bit) | DMR: `OOS::thermal_timer_threshold = 3mS` in PCode |
| MCA type | Still UCNA? | DMR: UCNA — no system impact, informational |
| UCNA threshold | PrimeCode `ucna_threshold` mitigation carried forward? | DMR: Configurable via pcudata, default=2 consecutive events |
| Gen2.6 CDC fix | DTS IP CDC bug fixed in NWP's DTS IP version? | DMR A0: Known bug (NVL HSD 14025678245), HW fix targets B0 |
| Gen1 DTS rawcode | NWP NIO uses different DTS? Same rawcode=0 risk? | DMR: Gen1 iMH DTS rawcode=0 → false 150°C |
| MCA bank | Same machine check bank for thermal UCNA? | DMR: Firmware MCA bank (PCode-generated) |
| OS visibility | Same `mcelog` / WHEA path? | DMR: Standard UCNA → OS logging |
