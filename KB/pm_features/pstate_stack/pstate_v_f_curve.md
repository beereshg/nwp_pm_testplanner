# Pstate Stack > Pstate-V-F curve

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: The V/F (Voltage-Frequency) curve defines the required core voltage at every frequency operating point. PCode constructs the curve by linearly interpolating between fused VID anchor points (Pn, P1, P0). On each GV transition: voltage leads frequency upward (voltage first), frequency leads voltage downward (frequency first) to maintain reliability margins. AVS/DLVR enable runtime adaptive voltage reduction below nominal for efficiency.

**Topology**:
```
Fuse VID anchors (Pn VID, P1 VID, P0 VID) ─> PCode V/F table (linear interpolation)
GV upward transition (P-state increase):
  1. PCode commands FIVR to new_VID (voltage first)
  2. Wait FIVR settle time
  3. PCode commands Core PLL to new_ratio (frequency step)
GV downward transition (P-state decrease):
  1. PCode commands Core PLL to new_ratio (frequency first)
  2. PCode commands FIVR to new_VID (voltage follows)
AVS/DLVR feedback loop:
  light workload (low switching) → DLVR reduces voltage below nominal V/F curve
  heavy workload (AVX, high Cdyn) → DLVR ensures full margin voltage maintained
```

**Key operational principle**: The V/F curve is the safety envelope — PCode must never allow core frequency without adequate voltage. AVS adaptive voltage operates within the curve's safe headroom. Near TDP validation verifies V/F stability when package power approaches TDP — no droops or frequency instability allowed.

**Boot activation**: PCode reads fuse VIDs and constructs V/F table at early init before CPL3 handoff. FIVR initialized before any frequency transition.

The Voltage-Frequency (V/F) curve defines the voltage required at each frequency operating point for reliable core operation. PCode constructs the V/F curve from fused VID (Voltage Identification) points programmed during manufacturing characterization. These fused points represent voltage values at specific frequency anchors (typically Pn, P1, and P0), with PCode interpolating voltages for intermediate frequency points.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core FIVR (Fully Integrated VR) | CBB Top Die | Converts PCode VID command to core supply voltage; fast response required for GV transitions; nominal V/F curve enforced | VID bus from PCode; voltage rail to Core | CBB PM HAS |
| DLVR (Digital LVR) | CBB Top Die | Adaptive voltage regulator; can reduce voltage below nominal V/F curve for efficiency gains; AVS feedback loop | DLVR sense; adaptive VID offset | CBB PM HAS |
| VID fuse register | IMH die | Stores manufacturing-characterized voltage anchor points (VIDs) at Pn, P1, P0 frequencies; basis for V/F interpolation | Fuse read at boot | CBB PM HAS |
| Core PLL | CBB Top Die | Generates core clock at target ratio; frequency transitions coordinated with FIVR for GV margin safety | PLL ratio control; lock signal | CBB PM HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | No direct V/F management role; operates at PCode-set voltage/frequency; AVX workload can trigger higher Cdyn, may require DLVR voltage adjustment | — | — |
| PCode (CBB) | CBB Base Die | Reads fuse VID anchors at boot; builds interpolated V/F table; on each GV: looks up target VID, commands FIVR before frequency increase / after frequency decrease; manages AVS/DLVR adaptive voltage offset | V/F lookup + GV sequence; `source/pcode/flows/autonomous_pstate/` | [CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) |
| PrimeCode (IMH) | IMH die | No direct V/F role; IMH-side power limits constrain the turbo headroom within which the V/F curve operates | HPM power limits | DMR SoC PM HAS |
| BIOS / UEFI | Platform | Configures AVS enable/disable; V/F curve offset knobs; Near TDP test configuration; thermal limits that constrain V/F operation at high frequency | BIOS knobs; AVS config | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| VID fuses | Fuse registers (read via BIOS/tools) | RO | Manufacturing-characterized VID anchor points; exposed via BIOS diagnostics and PCode telemetry | CBB PM HAS |
| MSR `IA32_PERF_STATUS` | 0x198 | RO | Current operating ratio; corresponds to V/F operating point | Intel SDM |
| MSR `PLATFORM_INFO` | 0x0CE [15:8] | RO | P1 guaranteed ratio = key V/F anchor point for OS | Intel SDM |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| GV transition direction rule | Voltage-first up, frequency-first down | — | Safety: never run at higher freq with lower-than-required voltage | Legacy Execution Flow |
| V/F anchor points | Pn, P1, P0 | VID / ratio pairs | Linear interpolation between anchors covers all intermediate P-states | Legacy Architecture Summary |
| DLVR adaptive range | Below nominal V/F | — | Can reduce voltage below nominal curve during light workloads for efficiency | Legacy Architecture Summary |
| NWP fused VIDs | NWP characterization | — | Different voltage values vs DMR; same algorithm; NWP FIVR IP may differ | Legacy NWP Delta |
| Near TDP validation | At TDP power load | — | V/F stability test: no droops or frequency glitches when package power ≈ TDP | Legacy Architecture Summary |

## NWP Delta

**V/F curve (Voltage-Frequency) management is fully supported on NWP server** — reused from DMR.

- V/F curve management unchanged
- Same fuse-based V/F points
- Same runtime V/F optimization (ITD voltage offset, Cdyn-based adjustment)
- PantherCove V/F characteristics reused

### Topology Impact
- SST-PP removed → no per-SST-level V/F profile variation
- Same per-core V/F behavior

### Validation Impact
- Same V/F curve test cases apply
- Skip SST-PP V/F cross-product tests

## Legacy (Human-Curated Reference)

### Architecture Summary

The Voltage-Frequency (V/F) curve defines the voltage required at each frequency operating point for reliable core operation. PCode constructs the V/F curve from fused VID (Voltage Identification) points programmed during manufacturing characterization. These fused points represent voltage values at specific frequency anchors (typically Pn, P1, and P0), with PCode interpolating voltages for intermediate frequency points.

Adaptive Voltage Scaling (AVS) and DLVR (Digital Linear Voltage Regulator) allow PCode to dynamically adjust the V/F curve at runtime based on workload characteristics and silicon margin. When the workload is light (low switching activity), PCode can reduce voltage below the nominal V/F curve to save power. When the workload is heavy (high switching activity, AVX), PCode may increase voltage to maintain reliability margins.

SST-PP (Speed Select Technology — Performance Profile) can modify the V/F curve per performance level. Each SST-PP level may define different P1 and turbo ratios with corresponding voltage adjustments, effectively shifting the V/F curve for the selected profile. The "Near TDP" test validates that core operation near the TDP power envelope correctly follows the V/F curve without voltage droops or frequency instability.

### Execution Flow

1. **Fuse Read** — PCode reads fused VID points at manufacturing-characterized frequency anchors (Pn, P1, P01 voltage values).
2. **V/F Curve Construction** — PCode interpolates between fused VID points to build the complete V/F curve across the entire Pn–P0 frequency range.
3. **AVS/DLVR Calibration** — PCode performs runtime voltage calibration using adaptive algorithms. DLVR adjusts the voltage regulator output for optimal efficiency.
4. **SST-PP Override** — If an SST-PP performance profile is active, PCode applies the profile's V/F curve modifications (different anchor voltages for the selected P1/turbo ratios).
5. **Runtime Voltage Tracking** — During frequency transitions, PCode looks up the target voltage from the V/F curve and commands the FIVR to the new voltage before (upward) or after (downward) the frequency change.
6. **Validation** — V/F fuse test reads all fused VID points and validates they match expected characterization values. Near TDP test runs sustained workload near TDP power and confirms voltage/frequency stability.

### Key Registers & Interfaces

| Register / MSR | Address | Description |
|----------------|---------|-------------|
| VID fuses | Fuse registers | Fused voltage points at Pn, P1, P0 |
| IA32_PERF_STATUS | MSR 0x198 | Current operating ratio |
| VID_STATUS | PCode internal | Current core voltage ID |
| FIVR_CONFIG | PCode internal | FIVR voltage regulator control |
| DLVR_CONFIG | PCode internal | Digital LVR adaptive voltage |
| SST_PP_VF | TPMI MMIO | SST-PP V/F curve overrides |
| PLATFORM_INFO | MSR 0x0CE | P1 ratio (V/F anchor point) |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) | V/F curve in P-state context |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | FIVR/DLVR voltage management |
| HAS | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) | Turbo V/F points |
| MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP V/F specification |
| PCode src | `source/pcode/flows/autonomous_pstate/` | V/F curve construction and lookup |

### Related Sightings

V/F curve fuse mismatch (fused VID vs expected characterization) and DLVR adaptive voltage oscillation are known DMR sighting patterns. Monitor on NWP.

### NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| V/F curve construction | Fused VID interpolation | Same | Same algorithm |
| AVS/DLVR | Supported | Supported | Same adaptive voltage |
| FIVR | DMR FIVR IP | NWP FIVR IP | Different FIVR implementation, same interface |
| SST-PP V/F override | Supported | Supported | Same SST-PP mechanism |
| Fused VID values | DMR characterization | NWP characterization | Different voltage points per NWP process |
