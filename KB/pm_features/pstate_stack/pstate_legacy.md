# Pstate Stack > Pstate Legacy

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: Legacy P-state (EIST/SpeedStep) is the pre-HWP OS-directed frequency control mode. The OS writes the exact target ratio directly to `IA32_PERF_CTL` (MSR 0x199); PCode executes the GV (Geyserville) voltage/frequency transition. Active when HWP is not enabled (MSR 0x770[0] = 0). Linux uses `acpi-cpufreq` driver with `scaling_governor`.

**Topology**:
```
BIOS: populates ACPI _PSS table (P0..Pn available P-states)
OS scaling_governor ──writes ratio──> IA32_PERF_CTL (MSR 0x199)
  PCode: validates ratio vs turbo/thermal/power limits
         commands Core FIVR + PLL via Fast GV path
  Core operates at target ratio
  IA32_PERF_STATUS (MSR 0x198) reflects current ratio
  IA32_APERF (0xE8): unhalted cycles at actual freq
  IA32_MPERF (0xE7): cycles at P0 (max) rate → APERF/MPERF = effective/max ratio
  TSC: invariant (constant rate regardless of P-state)
```

**Key operational principle**: In legacy mode, PCode executes the OS-requested ratio but still enforces thermal/power/turbo caps — if the requested ratio exceeds limits, PCode clamps to the allowed maximum and sets PLR bits. APERF/MPERF ratio provides the OS with effective frequency utilization even when clamped. Fast GV enables faster voltage/frequency transitions than legacy GV.

**Boot activation**: BIOS enables legacy P-states via `IA32_MISC_ENABLE[16]` (EIST enable). ACPI _PSS table populated with available P-states. PCode initializes P-state range at CPL3 handoff.

Legacy P-state is the pre-HWP OS-directed frequency control mechanism. In legacy mode, the OS directly writes the desired frequency ratio to MSR 0x199 (IA32_PERF_CTL), and PCode transitions the core to that exact ratio (subject to turbo/power/thermal limits). This is in contrast to HWP where PCode autonomously selects the frequency within a range.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core FIVR + PLL | CBB Top Die | Execute GV voltage/frequency transition to OS-requested ratio; Fast GV path reduces transition latency | GV done signal; ratio control | CBB PM HAS |
| IA32_APERF counter | Per-core | Count actual unhalted cycles at current frequency; APERF/MPERF ratio = effective frequency utilization | APERF CR (MSR 0xE8) | Intel SDM |
| IA32_MPERF counter | Per-core | Count cycles at P0 (max) rate regardless of actual frequency; denominator for effective frequency ratio | MPERF CR (MSR 0xE7) | Intel SDM |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | Executes at PCode-directed ratio; no direct P-state request role in legacy mode | — | — |
| PCode (CBB) | CBB Base Die | Reads IA32_PERF_CTL each evaluation; validates ratio vs turbo/thermal/power limits; commands Core FIVR+PLL via Fast GV; updates PERF_STATUS; sets PLR bits if clamped | P-state flow; `source/pcode/flows/autonomous_pstate/` | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) |
| PrimeCode (IMH) | IMH die | No direct legacy P-state role; package-level power limits propagated as turbo/P-state headroom constraint | HPM power limits | DMR SoC PM HAS |
| BIOS / UEFI | Platform | Enables EIST (`IA32_MISC_ENABLE[16]`); populates ACPI _PSS table; programs turbo enable/disable; configures Fast GV mode | Boot-time; ACPI _PSS; MSR 0x1A0 | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_PERF_CTL` | 0x199 | RW | [15:8] Target ratio — OS-directed P-state request; PCode executes GV to this ratio (subject to limits) | Intel SDM |
| MSR `IA32_PERF_STATUS` | 0x198 | RO | Current operating ratio (reflects actual freq after limits applied) | Intel SDM |
| MSR `IA32_MPERF` | 0xE7 | RO (accumulated) | Unhalted cycles at P0 rate; APERF/MPERF = effective/max freq ratio | Intel SDM |
| MSR `IA32_APERF` | 0xE8 | RO (accumulated) | Unhalted cycles at actual frequency; numerator for effective freq ratio | Intel SDM |
| ACPI `_PSS` table | ACPI | RO (OS enumeration) | Lists available P-states (Pn through P0) with frequency, power, latency; used by `acpi-cpufreq` driver | ACPI Spec |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| GV transition latency (Fast GV) | ~few | μS | Fast Geyserville enabled; significantly faster than legacy GV | Legacy Execution Flow |
| TSC | Invariant | — | TSC ticks at constant rate regardless of P-state; required for OS wall-clock | Legacy Key Registers |
| APERF / MPERF ratio | 0 – 1.0 | — | 1.0 = running at max freq; < 1.0 = throttled or C-state; effective freq utilization metric | Legacy Architecture Summary |
| P-state range | Pn – P0 | — | Full range from most-efficient (Pn) to maximum (P0/turbo); OS selects via PERF_CTL | Legacy Architecture Summary |
| EIST disable | IA32_MISC_ENABLE[16] = 0 | — | Disables legacy P-state control; core runs at P1 | Legacy Key Registers |

## NWP Delta

**Legacy P-states (SpeedStep/EIST) are fully supported on NWP server** — reused from DMR.

- Legacy P-state flows unchanged
- Same MSR interfaces for backward compatibility
- EIST enable/disable via IA32_MISC_ENABLE unchanged

### Validation Impact
- Same legacy P-state test cases apply

## Legacy (Human-Curated Reference)

### Architecture Summary

Legacy P-state is the pre-HWP OS-directed frequency control mechanism. In legacy mode, the OS directly writes the desired frequency ratio to MSR 0x199 (IA32_PERF_CTL), and PCode transitions the core to that exact ratio (subject to turbo/power/thermal limits). This is in contrast to HWP where PCode autonomously selects the frequency within a range.

Legacy mode is active when HWP is not enabled (MSR 0x770 bit 0 = 0). The OS uses ACPI _PSS (Performance Supported States) objects to enumerate available P-states and writes to PERF_CTL to request transitions. Linux exposes this via the `acpi-cpufreq` driver with `scaling_governor` (performance, powersave, ondemand, etc.). Legacy P-state validation covers a wide range of scenarios: BIOS configurations (turbo enable/disable, various BIOS knobs), interface validation (PERF_CTL writes reflected in PERF_STATUS), Fast GV (fast geyserville voltage/frequency transitions), counter accuracy (TSC, APERF/MPERF/PCNT/ACNT counters), complex scenarios (multi-core, mixed workloads), and Solar stress testing.

Fast GV configuration controls the speed of voltage/frequency transitions. When Fast GV is enabled, transitions complete in fewer microseconds, reducing the latency of P-state changes. Counter accuracy validation ensures that performance monitoring counters (TSC for wall-clock, APERF for actual cycles, MPERF for maximum cycles) accurately track time spent at each frequency for OS scheduler and power management decisions.

### Execution Flow

1. **BIOS Configuration** — BIOS configures legacy P-state parameters: turbo enable/disable, P-state range, Fast GV mode, and ACPI _PSS table population.
2. **OS Enumeration** — OS reads ACPI _PSS to enumerate available P-states (Pn through P0). Linux `acpi-cpufreq` driver loads and exposes `scaling_available_frequencies`.
3. **P-state Request** — OS governor selects target P-state and writes ratio to IA32_PERF_CTL (MSR 0x199).
4. **PCode Transition** — PCode reads PERF_CTL, validates the ratio against current limits (turbo, thermal, power), and commands the core PLL/FIVR to the target frequency/voltage.
5. **Status Update** — IA32_PERF_STATUS (MSR 0x198) reflects the new operating ratio. APERF/MPERF counters begin tracking at the new frequency.
6. **Counter Validation** — TSC maintains constant rate (invariant TSC). APERF counts actual unhalted cycles. MPERF counts at the P0 rate. PCNT/ACNT track package-level activity.
7. **Stress Testing** — Solar stress exercises rapid P-state transitions under heavy load to validate stability across all frequency/voltage points.

### Key Registers & Interfaces

| Register / MSR | Address | Description |
|----------------|---------|-------------|
| IA32_PERF_CTL | MSR 0x199 | Legacy P-state request (write target ratio) |
| IA32_PERF_STATUS | MSR 0x198 | Current operating ratio |
| IA32_MPERF | MSR 0xE7 | Maximum performance counter |
| IA32_APERF | MSR 0xE8 | Actual performance counter |
| IA32_TIME_STAMP_COUNTER | MSR 0x10 | Invariant TSC |
| PLATFORM_INFO | MSR 0x0CE | P1, Pn ratios |
| FAST_GV_CONFIG | PCode/BIOS | Fast Geyserville transition speed |
| ACPI _PSS | ACPI table | OS-enumerable P-state list |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) | Legacy P-state MSR definitions |
| HAS | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) | Turbo interaction with legacy mode |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | Fast GV configuration |
| MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP legacy P-state specification |
| PCode src | `source/pcode/flows/autonomous_pstate/` | Legacy P-state flow |
| Primecode src | `src/flow/turbo/` | Turbo ratio limit enforcement |

### Related Sightings

Legacy P-state counter accuracy (APERF/MPERF ratio drift) and Fast GV transition glitches are common DMR sighting patterns. Monitor on NWP bring-up.

### NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| PERF_CTL/STATUS | MSR 0x199/0x198 | Same | No MSR changes |
| Fast GV | Supported | Supported | Same fast transition mechanism |
| Counter accuracy | TSC/APERF/MPERF | Same | Same counter architecture |
| ACPI _PSS | BIOS-populated | Same | Same ACPI interface |
| Solar stress | Validated on DMR | Carry forward | Same stress methodology |
