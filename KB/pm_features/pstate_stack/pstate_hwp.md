# Pstate Stack > Pstate-HWP

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: Hardware P-states (HWP) is the modern OS-to-PCode P-state interface. OS specifies a performance envelope (min/max/desired ratio + EPP) via MSR 0x774; PCode's PEGA engine autonomously selects the optimal frequency within that range considering ICCP, EET, thermal, and power limits. OOB (BMC) mode via TPMI overrides OS HWP request. NWP adds **P04 = P0n/4** as a firmware-enforced HWP minimum guardrail.

**Topology**:
```
OS ──IA32_HWP_REQUEST (MSR 0x774) [Min/Max/Desired/EPP]──────> PEGA engine
BMC ──TPMI HWP registers (OOB mode, overrides OS)────────────> (same PEGA path)
  PEGA: applies ICCP license cap + EET attenuation + thermal limit + power limit
  Resolved ratio clamped: max(P04, min(ICCP_cap, EET_cap, thermal_cap, Desired))
          │
  Core FIVR + PLL (GV transition, ~few μS)
  IA32_PERF_STATUS (MSR 0x198) reflects current operating ratio
  IA32_HWP_STATUS (MSR 0x777) reports HWP state changes
```

**Key operational principle**: HWP Native mode = OS writes MSR 0x774 directly (Linux intel_pstate driver). OOB mode = BMC writes TPMI HWP registers, PCode ignores MSR 0x774. P04 (NWP-specific) prevents HWP_REQUEST.MIN_PERFORMANCE from going below P0n/4 — firmware clamps any lower request to P04.

**Boot activation**: BIOS sets `IA32_PM_ENABLE[0]` = 1 to enable HWP (write-once per boot). Default HWP_REQUEST values programmed by BIOS. PEGA active from CPL3 handoff.

Hardware P-states (HWP) is the modern OS–hardware P-state interface, replacing legacy PERF_CTL-based control. With HWP, the OS specifies a desired performance range (minimum, maximum, desired ratio, and Energy Performance Preference) via MSR 0x774 (IA32_HWP_REQUEST), and PCode autonomously selects the optimal operating frequency within that range based on workload characteristics, power limits, and thermal constraints.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core FIVR + PLL | CBB Top Die | Execute GV voltage/frequency transition on PEGA-resolved HWP target; transition in ~few μS | GV done signal; ratio control | CBB PM HAS |
| TPMI SRAM (HWP OOB) | Per IMH | Stores OOB HWP request registers; BMC writes via OOBMSM; PCode reads and uses instead of MSR 0x774 in OOB mode | TPMI MMIO; OOBMSM VSEC BAR | TPMI HAS |
| Core perf counters | CBB Top Die | Workload characterization input to PEGA for autonomous HWP target selection (IPC, stall, memory BW) | SHORT_TELEM; unhalted cycles | ACP PM HAS |
| APIC LVT Thermal Interrupt | Per-core | Delivers HWP change notification when PEGA-selected ratio changes; `IA32_HWP_INTERRUPT.CHANGE_NOTIFICATION_EN` | LVT thermal vector | Intel SDM |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | Provides workload telemetry to PEGA for autonomous selection; no direct HWP request role | SHORT_TELEM | ACP PM HAS |
| PCode / PEGA (CBB) | CBB Base Die | Main HWP engine: reads HWP_REQUEST (or TPMI OOB), applies all constraints (ICCP, EET, thermal, power), enforces P04 minimum guardrail (NWP), commands FIVR+PLL for GV; updates PERF_STATUS; issues HWP change notification | `source/pcode/flows/hwpm/`; `source/pcode/flows/pega/` | [CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) |
| PrimeCode (IMH) | IMH die | No direct HWP per-core role; propagates package-scope power/thermal limits that constrain PEGA HWP headroom | HPM power limit HPMs | DMR SoC PM HAS |
| BIOS / UEFI | Platform | Enables HWP via `IA32_PM_ENABLE[0]`=1 (write-once); programs default HWP_REQUEST; selects Native vs OOB mode via BIOS knob | MSR 0x770 write; default HWP_REQUEST | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_PM_ENABLE` | 0x770 | RW | [0] HWP enable — write 1 once per boot; cannot disable without reboot | Intel SDM |
| MSR `IA32_HWP_CAPABILITIES` | 0x771 | RO | [7:0] Highest (P0n); [15:8] Guaranteed (P1); [23:16] Most Efficient (Pn); [31:24] Lowest | Intel SDM |
| MSR `IA32_HWP_REQUEST_PKG` | 0x772 | RW | Package-level HWP request override (applies to all cores unless overridden per-core) | Intel SDM |
| MSR `IA32_HWP_INTERRUPT` | 0x773 | RW | [0] CHANGE_NOTIFICATION_EN; [1] ENERGY_PERF_PREFERENCE_CHANGE_EN | Intel SDM |
| MSR `IA32_HWP_REQUEST` | 0x774 | RW | [7:0] Min_Perf (≥P04 on NWP); [15:8] Max_Perf; [23:16] Desired (0=auto); [31:24] EPP | Intel SDM |
| MSR `IA32_HWP_STATUS` | 0x777 | RO/RWC | HWP state change flag; cleared by SW | Intel SDM |
| TPMI HWP | TPMI MMIO | RW (BMC) | OOB HWP request; same fields as MSR 0x774; overrides OS in OOB mode | TPMI HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| GV transition latency | ~few | μS | Core FIVR + PLL transition per HWP target change | Legacy Execution Flow |
| PEGA HWP evaluation period | ~1 | mS | PCode slow-loop resolves optimal target from HWP_REQUEST + all constraints | Legacy Execution Flow |
| P04 minimum guardrail (NWP) | P0n ÷ 4 | ratio | Firmware clamps HWP_REQUEST.MIN_PERF ≥ P04; NWP PM MAS §3 | Legacy NWP Pstate Range table |
| HWP enable write-once | 1 per boot | — | IA32_PM_ENABLE[0] cannot be cleared without reboot | Intel SDM |
| EPP granularity | 256 | levels | 8-bit (0=max perf, 255=max efficiency); finer than EPB 4-bit | Legacy Key Registers |
| OOB mode override | Full | — | TPMI HWP request overrides OS MSR 0x774 completely | Legacy Architecture Summary |

## NWP Delta

**HWP (Hardware P-states) is fully supported on NWP server** — reused from DMR.

- Full HWP support: autonomous, EPP-guided, interrupt notification
- Same MSR interfaces (IA32_HWP_CAPABILITIES, IA32_HWP_REQUEST, IA32_HWP_STATUS)
- Same TPMI HWP registers
- PantherCove BigCore HWP algorithm unchanged

### Topology Impact
- 2 CBBs — fewer cores but same per-core HWP behavior
- SST-PP removed → no SST-PP level HWP cross-products
- Single NIO → simplified HWP coordination

### Validation Impact
- Same HWP test cases apply
- Skip SST-PP/BF HWP cross-product tests

## Legacy (Human-Curated Reference)

### Architecture Summary

Hardware P-states (HWP) is the modern OS–hardware P-state interface, replacing legacy PERF_CTL-based control. With HWP, the OS specifies a desired performance range (minimum, maximum, desired ratio, and Energy Performance Preference) via MSR 0x774 (IA32_HWP_REQUEST), and PCode autonomously selects the optimal operating frequency within that range based on workload characteristics, power limits, and thermal constraints.

HWP is enabled via MSR 0x770 (IA32_PM_ENABLE). Once enabled, PCode takes ownership of frequency selection using the PEGA engine. The OS's role shifts from directly commanding a specific P-state to providing a performance envelope and energy preference hints. PCode reads HWP_REQUEST fields (Min_Perf, Max_Perf, Desired_Perf, EPP) and combines them with internal inputs (ICCP license, EET, thermal, power limits) to determine the optimal operating point.

HWP supports two control modes: **Native mode** where the OS directly writes MSR 0x774, and **OOB mode** where the BMC controls HWP parameters via TPMI registers. In OOB mode, the OS's HWP_REQUEST writes are overridden by the OOB controller, allowing datacenter-level power management without OS cooperation. Both modes are validated for correct frequency response across the full min/max/EPP range.

#### NWP Pstate Range (from PM MAS §3)

The NWP PM MAS explicitly defines the HWP operating range across four named reference points:

| Point | Definition | Source |
|-------|------------|--------|
| **Pn** | Maximum efficiency ratio — LFM, best power (lowest operating frequency) | Xeon 25/26 RCF HAS §6.2.11.1 |
| **P1** | Guaranteed ratio — base/non-turbo maximum frequency | RCF HAS, HWP_CAPABILITIES.Guaranteed_Performance |
| **P0n** | Turbo Ratio Limit (TRL) — max turbo frequency the part supports | IA32_HWP_CAPABILITIES.Highest_Performance |
| **P04** | P0n ÷ 4 — one quarter of TRL; minimum HWP ratio guardrail | NWP PM MAS §3; RCF HAS |

> **P04 (P0n/4)** is a minimum ratio guardrail enforced by firmware — the HWP minimum performance field cannot be set below P0n/4. This prevents the hardware from entering frequency ranges below validated operation. For example, if P0n = 40 (4.0 GHz @ 100 MHz BCLK), P04 = 10 (1.0 GHz).
>
> Source: [NWP IMH SOC PM MAS §3 — PM Features Changes from DMR-AP/SP](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)

### Execution Flow

1. **BIOS Configuration** — BIOS enables HWP capability and sets default HWP_REQUEST values. HWP Native vs OOB mode is selected via BIOS knob.
2. **OS HWP Enable** — OS writes IA32_PM_ENABLE (MSR 0x770) bit 0 = 1 to activate HWP. Linux `intel_pstate` driver or `acpi-cpufreq` with HWP takes control.
3. **HWP Request** — OS writes desired performance range to IA32_HWP_REQUEST (MSR 0x774): Min_Perf, Max_Perf, Desired_Perf (0 = autonomous), EPP.
4. **PEGA Autonomous Selection** — PCode's PEGA engine reads HWP_REQUEST fields, combines with workload monitoring, thermal state, power limits, ICCP license, and EET to select the optimal target ratio.
5. **Frequency Transition** — PCode commands the core PLL/FIVR to the selected frequency/voltage. Transition completes in microseconds.
6. **Status Reporting** — IA32_PERF_STATUS (MSR 0x198) reports the current operating ratio. HWP_STATUS (MSR 0x777) reports any HWP-related status/error conditions.
7. **OOB Override** — If OOB mode is active, BMC writes TPMI HWP control registers. PCode uses OOB values instead of OS MSR values for frequency selection.

### Key Registers & Interfaces

| Register / MSR | Address | Description |
|----------------|---------|-------------|
| IA32_PM_ENABLE | MSR 0x770 | HWP enable (bit 0) |
| IA32_HWP_CAPABILITIES | MSR 0x771 | Highest/guaranteed/efficient/lowest ratios |
| IA32_HWP_REQUEST_PKG | MSR 0x772 | Package-level HWP request |
| IA32_HWP_INTERRUPT | MSR 0x773 | HWP interrupt configuration |
| IA32_HWP_REQUEST | MSR 0x774 | Per-core min/max/desired/EPP |
| IA32_HWP_STATUS | MSR 0x777 | HWP status/change indication |
| IA32_PERF_STATUS | MSR 0x198 | Current operating ratio |
| TPMI HWP | TPMI MMIO | OOB HWP control registers |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) | HWP MSR definitions and behavior |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | HWP in CBB PM context |
| HAS | [DMR CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) | PEGA HWP integration |
| MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP HWP specification |
| PCode src | `source/pcode/flows/hwpm/` | HWP flow implementation |
| PCode src | `source/pcode/flows/pega/` | PEGA HWP input processing |

### Related Sightings

HWP OOB mode override conflicts with OS-native HWP are a common DMR sighting pattern. Monitor for TPMI vs MSR priority issues on NWP.

### NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| HWP MSRs | 0x770–0x777 | Same | No MSR changes |
| Native mode | Supported | Supported | Same OS interface |
| OOB mode via TPMI | Supported | Supported | Same TPMI registers |
| PEGA integration | HWP as PEGA input | Same | No change |
| HWP harasser | Validated | Validated | Same stress methodology |
| Pstate range | Pn, P1, P0n | Pn, P1, P0n, **P04** | NWP explicitly adds P04 (= P0n/4) as minimum HWP guardrail — see PM MAS §3 |
