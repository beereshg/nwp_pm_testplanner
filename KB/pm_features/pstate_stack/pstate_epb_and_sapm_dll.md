# Pstate Stack > Pstate-EPB and SAPM-DLL

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: EPB (Energy Performance Bias, MSR 0x1B0, 4-bit 0-15) and EPP (Energy Performance Preference, HWP_REQUEST[31:24], 8-bit 0-255) are OS power policy hints fed into the PEGA engine — they influence turbo aggressiveness, EET attenuation strength, and C-state promotion depth. SAPM-DLL manages DLL voltage offset during package C-state entry/exit to reduce leakage.

**Topology**:
```
OS ──IA32_ENERGY_PERF_BIAS (MSR 0x1B0)──────────────────────────> CBB PCode PEGA
OS ──IA32_HWP_REQUEST.EPP (MSR 0x774 [31:24]) (HWP enabled)────> PEGA inputs
BMC ──TPMI EPB registers (OOB)──────────────────────────────────> (same PEGA path)
  PEGA: EPB/EPP → scale EET attenuation + turbo aggressiveness + C-state depth
        EPB=0/EPP=0 → max performance (minimum energy savings)
        EPB=15/EPP=255 → max energy savings (aggressive EET + deeper C-states)
PkgC entry → PCode reduces DLL voltage offset (SAPM-DLL) → DLL re-lock on exit
```

**Key operational principle**: EPP provides finer granularity than EPB (256 vs 16 levels) and is preferred when HWP is enabled. Both can be set OOB via TPMI for datacenter power policy. SAPM-DLL voltage reduction is timed: PCode must wait for DLL re-lock confirmation before allowing core wake on C-state exit.

**Boot activation**: BIOS sets default EPB value (typically 4=balanced-performance). HWP enable (MSR 0x770) activates EPP path. SAPM-DLL config applied during early PCode init.

EPB (Energy Performance Bias) is an OS hint mechanism that tells PCode the system's preference along the power-vs-performance spectrum. Written via MSR 0x1B0 (IA32_ENERGY_PERF_BIAS), the 4-bit value ranges from 0 (maximum performance) to 15 (maximum energy savings). PCode uses EPB as an input to the PEGA engine, influencing turbo aggressiveness, EET attenuation thresholds, and C-state promotion depth.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| DLL (Delay-Locked Loop) | CBB / IMH die | Timing reference during active operation; voltage can be reduced by SAPM-DLL during pkg C-state; must re-lock before core wake | DLL lock signal; SAPM voltage control | CBB PM HAS |
| TPMI SRAM (OOB EPB) | Per IMH | OOB-accessible EPB register; BMC writes EPB via TPMI; same PEGA path as MSR 0x1B0 | TPMI MMIO; OOBMSM BAR | TPMI HAS |
| Core PLL + FIVR | CBB Top Die | Respond to EPB/EPP-influenced PEGA output; higher EPP → conservative turbo → FIVR/PLL at lower ratio | GV transition; ratio control | CBB PM HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | No direct EPB/EPP role; C-state depth influenced by EPB via PCode C-state promotion hints | — | — |
| PCode / PEGA (CBB) | CBB Base Die | Reads EPB (MSR 0x1B0) and EPP (HWP_REQUEST[31:24]) each PEGA evaluation; scales EET attenuation, turbo aggressiveness, and C-state promotion thresholds proportionally; manages SAPM-DLL voltage offset on pkg C-state entry/exit | PEGA EPB/EPP input; `source/pcode/flows/pega/`; SAPM-DLL config | [CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) |
| PrimeCode (IMH) | IMH die | No direct EPB role; SAPM-DLL management on IMH DLL during IMH-level low-power states | SAPM-DLL IMH | DMR SoC PM HAS |
| BIOS / UEFI | Platform | Sets default EPB at boot (typically 4=balanced); enables HWP (activates EPP path); configures SAPM-DLL voltage offset parameters via BIOS knobs | MSR 0x1B0 default; HWP enable | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_ENERGY_PERF_BIAS` | 0x1B0 | RW | [3:0] EPB (0=max perf, 15=max energy savings); per-core; Linux exposes via `energy_perf_bias` sysfs | Intel SDM |
| MSR `IA32_HWP_REQUEST` | 0x774 [31:24] | RW | EPP (0=max perf, 255=max efficiency); per-core; preferred over EPB when HWP enabled | Intel SDM |
| TPMI EPB | TPMI MMIO | RW (BMC) | OOB EPB write; same effect as MSR 0x1B0; BMC power policy control | TPMI HAS |
| MSR `IA32_PERF_STATUS` | 0x198 | RO | Current ratio reflects EPB/EPP influence on PEGA turbo selection | Intel SDM |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| EPB range | 0 – 15 | — | 4-bit; 0=max perf, 15=max energy savings; coarse granularity | Legacy Key Registers |
| EPP range | 0 – 255 | — | 8-bit; preferred over EPB when HWP enabled; finer granularity | Legacy Key Registers |
| EPB/EPP evaluation period | ~1 | mS | PEGA reads and applies EPB/EPP each slow-loop iteration | Legacy Execution Flow |
| SAPM-DLL re-lock wait | Platform-dependent | μS | PCode waits for DLL lock confirmation on C-state exit before core wake | Legacy Execution Flow |
| OOB EPB (TPMI) | Same as MSR | — | BMC writes TPMI EPB register; PCode treats same as MSR 0x1B0 | Legacy Architecture Summary |

## NWP Delta

**EPB (Energy Performance Bias) and SAPM DLL are fully supported on NWP server** — reused from DMR.

- EPB and SAPM DLL flows unchanged
- Same MSR interfaces (IA32_ENERGY_PERF_BIAS)
- Same DLL management for power savings

### Validation Impact
- Same EPB/SAPM DLL test cases apply

## Legacy (Human-Curated Reference)

### Architecture Summary

EPB (Energy Performance Bias) is an OS hint mechanism that tells PCode the system's preference along the power-vs-performance spectrum. Written via MSR 0x1B0 (IA32_ENERGY_PERF_BIAS), the 4-bit value ranges from 0 (maximum performance) to 15 (maximum energy savings). PCode uses EPB as an input to the PEGA engine, influencing turbo aggressiveness, EET attenuation thresholds, and C-state promotion depth.

EPP (Energy Performance Preference) is the HWP-era equivalent, encoded as an 8-bit field (bits [31:24]) in MSR 0x774 (IA32_HWP_REQUEST). EPP provides finer granularity (0–255) and is the preferred mechanism when HWP is enabled. Both EPB and EPP can be swept via OS power policy changes (Linux `energy_perf_bias` sysfs or Windows power plans) and via OOB TPMI interfaces.

SAPM-DLL (System Agent Power Management — DLL) controls the voltage offset applied to the system agent's DLL (Delay-Locked Loop) during low-power states. The DLL voltage can be reduced during idle periods to save power, with PCode managing the transition timing to ensure DLL lock is maintained. SAPM-DLL validation confirms that voltage offset transitions do not cause DLL unlock or system instability.

### Execution Flow

1. **BIOS Configuration** — BIOS sets default EPB value and enables HWP (which activates EPP). SAPM-DLL parameters are configured via BIOS knobs for DLL voltage offset and transition timing.
2. **OS EPB/EPP Write** — OS writes EPB via MSR 0x1B0 or EPP via HWP_REQUEST MSR 0x774 bits [31:24]. Linux exposes this via `energy_perf_bias` sysfs attribute.
3. **PCode Processing** — PCode reads EPB/EPP values and adjusts PEGA engine parameters: higher EPP = more energy-conservative turbo, deeper C-state promotion, stronger EET attenuation.
4. **OOB EPB Sweep** — BMC can write EPB via TPMI interface for out-of-band power policy control. Test sweeps all EPB values (0–15) via TPMI and validates PCode response.
5. **SAPM-DLL Transition** — During package C-state entry, PCode reduces DLL voltage offset. On C-state exit, PCode restores DLL voltage and waits for DLL re-lock before allowing core wake.
6. **Validation** — EPP sweep confirms linear frequency/power response across the 0–255 range. EPB sweep confirms correct mapping to PEGA behavior. SAPM-DLL tests confirm no DLL unlock events during transitions.

### Key Registers & Interfaces

| Register / MSR | Address | Description |
|----------------|---------|-------------|
| IA32_ENERGY_PERF_BIAS | MSR 0x1B0 | Energy Performance Bias (4-bit, 0–15) |
| IA32_HWP_REQUEST.EPP | MSR 0x774 [31:24] | Energy Performance Preference (8-bit, 0–255) |
| TPMI EPB | TPMI MMIO | OOB EPB write interface |
| SAPM_DLL_CONFIG | PCode internal | DLL voltage offset configuration |
| SAPM_PG_STATUS | PCode internal | SAPM power-gate status |
| IA32_PERF_STATUS | MSR 0x198 | Frequency reflects EPB/EPP influence |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) | EPB/EPP specification |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | SAPM-DLL configuration |
| HAS | [DMR CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) | PEGA EPB/EPP input processing |
| MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP EPB/EPP/SAPM specification |
| PCode src | `source/pcode/flows/hwpm/` | HWP EPP processing |
| PCode src | `source/pcode/flows/pega/` | PEGA EPB/EPP integration |

### Related Sightings

No EPB/EPP/SAPM-DLL sightings identified for NWP. EPP sweep non-linearity and SAPM-DLL unlock events are common DMR sightings to watch for.

### NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| EPB (MSR 0x1B0) | 4-bit, 0–15 | Same | No change |
| EPP (HWP_REQUEST) | 8-bit, 0–255 | Same | No change |
| OOB EPB via TPMI | Supported | Supported | Same TPMI interface |
| SAPM-DLL | DMR DLL offsets | NWP DLL offsets | Different voltage offset values per NWP characterization |
| PEGA integration | EPB/EPP as PEGA inputs | Same | No change in PEGA behavior |
