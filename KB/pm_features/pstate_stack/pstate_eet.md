# Pstate Stack > Pstate-EET

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: Energy Efficient Turbo (EET) dynamically attenuates the max turbo ratio when PCode detects low workload energy efficiency (high cache misses, low IPC, memory-bound). This saves power without significant performance impact on stall-dominated workloads. Attenuation aggressiveness is modulated by EPB/EPP settings.

**Topology**:
```
Core perf counters (IPC, cache misses, mem BW) ──SHORT_TELEM──> CBB PCode PEGA engine
  PEGA EET input: efficiency ratio = (instructions retired) / (unhalted cycles × energy proxy)
  If efficiency < threshold:
    EET turbo attenuation = proportional to efficiency deficit × EPB/EPP scaling factor
    Effective max turbo = P0n - attenuation
  Core PLL caps at EET-attenuated ratio (transparent to OS)
  PLR status (MSR 0x64F): EET logged as turbo limit reason
```

**Key operational principle**: EET is transparent to OS — it appears as if the core cannot reach max turbo. OS observes via PLR EET bit. EPB=0 (max perf) → minimum EET attenuation; EPB=15 (max savings) → aggressive EET. EET_CONFIG B2P mailbox sets enable and efficiency thresholds.

**Boot activation**: EET enabled by BIOS knob (B2P EET_CONFIG). Active from CPL3 handoff alongside PEGA.

Energy Efficient Turbo (EET) dynamically adjusts the maximum turbo frequency based on workload energy efficiency. When PCode detects that a workload's energy-per-instruction ratio is high (i.e., the workload is memory-bound or stalled frequently), EET reduces the turbo ratio to save power without significantly impacting performance, since the workload is not compute-bound.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core performance counters | CBB Top Die | Monitor IPC, cache miss rate, memory bandwidth utilization — raw inputs for EET efficiency ratio | SHORT_TELEM push (~102.4μS); unhalted cycles, instructions retired counters | ACP PM HAS |
| Core FIVR + PLL | CBB Top Die | Clamp to EET-attenuated turbo ratio when PEGA selects lower frequency | GV transition signals; ratio control | CBB PM HAS |
| APERF / MPERF | CBB Top Die | Track actual vs maximum frequency; EET attenuation visible as APERF < MPERF at full load | `APERF` CR; `MPERF` CR | Intel SDM |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | Provides workload telemetry (IPC, cache miss) to PCode via SHORT_TELEM; no direct EET control | SHORT_TELEM feedback | ACP PM HAS |
| PCode / PEGA (CBB) | CBB Base Die | Reads perf counter telemetry; computes workload efficiency ratio; applies EET attenuation scaled by EPB/EPP; sets EET-limited max turbo in PEGA resolver; sets PLR EET bit | PEGA EET input; `source/pcode/flows/pega/` | [CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) |
| PrimeCode (IMH) | IMH die | No direct EET role; propagates thermal/power limits that bound the EET-resolved turbo headroom | HPM power limit HPMs | DMR SoC PM HAS |
| BIOS / UEFI | Platform | Enables EET via BIOS knob; configures efficiency thresholds via B2P `EET_CONFIG` mailbox | B2P `EET_CONFIG` | DMR CBB PM HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| B2P mailbox `EET_CONFIG` | PCU BAR MMIO | WO (BIOS) | EET enable + efficiency threshold configuration | DMR CBB PM HAS |
| MSR `IA32_ENERGY_PERF_BIAS` | 0x1B0 | RW | [3:0] EPB hint (0=max perf, 15=max efficiency) — scales EET attenuation aggressiveness | Intel SDM |
| MSR `IA32_HWP_REQUEST` | 0x774 [31:24] | RW | EPP (0=max perf, 255=max efficiency) — finer-grained EET modulation when HWP enabled | Intel SDM |
| MSR `CORE_PERF_LIMIT_REASONS` | 0x64F | RO/RWC | EET attenuation logged as turbo limit reason bit — OS/tools observe via PLR | Intel SDM |
| MSR `IA32_PERF_STATUS` | 0x198 | RO | EET attenuation visible as lower-than-P0n current ratio under stall-dominated workloads | Intel SDM |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| EET attenuation update period | ~1 | mS | PCode PEGA slow-loop evaluates workload efficiency each iteration | Legacy Execution Flow |
| EPB range | 0 – 15 | — | 0=max performance (minimum EET); 15=max energy savings (maximum EET attenuation) | Legacy Key Registers |
| EPP range | 0 – 255 | — | 0=max performance; 255=max efficiency; 8-bit when HWP enabled | Legacy Key Registers |
| EET OS transparency | Transparent | — | OS sees lower APERF/MPERF ratio; PLR EET bit is the diagnostic | Legacy Architecture Summary |
| PLR EET bit | Set | — | In MSR 0x64F when EET is actively limiting turbo | Legacy Execution Flow |

## NWP Delta

**EET (Energy Efficient Turbo) is fully supported on NWP server** — reused from DMR.

- EET flows unchanged
- Same energy efficiency optimization algorithm
- Same MSR interfaces (IA32_ENERGY_PERF_BIAS interaction)

### Validation Impact
- Same EET test cases apply
- Verify EET behavior with NWP turbo ratio profile

## Legacy (Human-Curated Reference)

### Architecture Summary

Energy Efficient Turbo (EET) dynamically adjusts the maximum turbo frequency based on workload energy efficiency. When PCode detects that a workload's energy-per-instruction ratio is high (i.e., the workload is memory-bound or stalled frequently), EET reduces the turbo ratio to save power without significantly impacting performance, since the workload is not compute-bound.

EET operates within the PEGA framework as one of the autonomous P-state adjustment inputs. PCode monitors core performance counters (instructions retired, unhalted cycles, cache miss rates) to estimate workload efficiency. When efficiency drops below configurable thresholds, PCode attenuates the turbo ratio proportionally. The EPB (Energy Performance Bias) and EPP (Energy Performance Preference) settings influence how aggressively EET clips turbo.

The EET feature is transparent to the OS — it appears as if the core simply cannot reach the maximum turbo ratio. The actual EET attenuation is visible through Performance Limit Reasons (PLR) reporting, where EET shows as a turbo attenuation reason.

### Execution Flow

1. **BIOS Configuration** — BIOS enables EET via BIOS knob and configures EET aggressiveness thresholds.
2. **Workload Monitoring** — PCode continuously monitors per-core performance metrics: IPC (instructions per cycle), cache miss rate, memory bandwidth utilization.
3. **Efficiency Assessment** — PCode computes energy efficiency ratio. If the workload is memory-bound (low IPC, high cache misses), efficiency is flagged as low.
4. **Turbo Attenuation** — PCode reduces the effective maximum turbo ratio proportionally to the efficiency deficit. EPB/EPP settings modulate the attenuation aggressiveness.
5. **Frequency Adjustment** — Core P-state is adjusted down if current frequency exceeds the EET-attenuated turbo limit.
6. **PLR Reporting** — EET attenuation is logged in PLR status registers, visible via MSR 0x64F.

### Key Registers & Interfaces

| Register / MSR | Address | Description |
|----------------|---------|-------------|
| EET_CONFIG | B2P Mailbox | EET enable and threshold configuration |
| IA32_ENERGY_PERF_BIAS | MSR 0x1B0 | Energy Performance Bias hint (0–15) |
| IA32_HWP_REQUEST.EPP | MSR 0x774 bits [31:24] | Energy Performance Preference (0–255) |
| IA32_PERF_STATUS | MSR 0x198 | Current ratio reflects EET attenuation |
| PLR status | MSR 0x64F | EET listed as turbo limit reason |
| PEGA EET input | PCode internal | EET efficiency signal to PEGA engine |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) | EET within turbo framework |
| HAS | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) | EET interaction with P-state stack |
| HAS | [DMR CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) | PEGA EET integration |
| MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP EET specification |
| PCode src | `source/pcode/flows/autonomous_pstate/` | EET flow implementation |
| PCode src | `source/pcode/flows/pega/` | PEGA EET input processing |

### Related Sightings

No EET-specific sightings identified for NWP. EET turbo attenuation accuracy should be validated during NWP performance characterization.

### NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| EET support | Supported | Supported | Same efficiency-based turbo attenuation |
| PEGA integration | EET as PEGA input | Same | No change in PEGA EET signal path |
| EPB/EPP influence | Modulates EET aggressiveness | Same | Same MSR interface |
| PLR reporting | EET in PLR bits | Same | Same PLR bit definition |
