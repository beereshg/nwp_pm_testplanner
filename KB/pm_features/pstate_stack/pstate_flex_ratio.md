# Pstate Stack > Pstate-Flex ratio

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: Flex Ratio (MSR 0x194) allows BIOS to cap the non-turbo P1 frequency below the fused P1 value. Effective P1 = min(fused_P1, flex_ratio). Turbo above flex ratio is still allowed if enabled. Used for power-constrained platforms, validation determinism, and manufacturing test.

**Topology**:
```
BIOS (POST) ──write FLEX_RATIO + enable bit──> MSR 0x194
PCode (boot init):
  effective_P1 = min(fused_P1, flex_ratio, SST_PP_P1, thermal_clip)
  └──> PLATFORM_INFO (MSR 0x0CE [15:8]) ─────────────────────> OS P1 discovery
  └──> HWP_CAPABILITIES.Guaranteed_Performance (MSR 0x771) ──> HWP OS interface
  └──> CPUID leaf 0x16 base frequency ────────────────────────> OS CPUID discovery
Runtime: flex ratio caps sustained (non-turbo) frequency; turbo above flex still allowed
```

**Key operational principle**: Flex ratio only limits P1, not turbo ratios. If flex ratio < fused P1, the core never sustains above flex ratio without turbo active. All three P1 discovery paths (PLATFORM_INFO, HWP_CAPABILITIES, CPUID leaf 0x16) must consistently report the flex-capped P1.

**Boot activation**: BIOS writes FLEX_RATIO during POST if platform requires it. PCode reads and applies during early init before CPL3. Immutable after PCode resolves P1.

Flex Ratio allows BIOS to set the maximum non-turbo frequency ratio below the fused P1 ratio. This is configured via MSR 0x194 (FLEX_RATIO), where BIOS writes the desired maximum non-turbo ratio and sets the flex ratio enable bit. When enabled, the effective P1 becomes min(fused_P1, flex_ratio), effectively capping the guaranteed frequency.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core FIVR + PLL | CBB Top Die | Sustains flex-ratio-capped P1 under all-core load; turbo above flex ratio permitted if enabled | GV control; ratio register | CBB PM HAS |
| Fuse register | IMH die | Stores manufacturing-characterized P1 ratio; flex ratio must be ≤ fused P1 (otherwise ignored) | Fuse read at boot | CBB PM HAS |
| MSR interface | Per-core | Delivers FLEX_RATIO (0x194) and publishes PLATFORM_INFO (0x0CE) to OS | MSR 0x194; MSR 0x0CE | Intel SDM |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | No direct flex ratio role; operates within flex-capped P1 during non-turbo sustained load | — | — |
| PCode (CBB) | CBB Base Die | Reads MSR 0x194 at boot; applies flex ratio as ceiling in P1 resolution (min of fused, flex, SST_PP, thermal); writes resolved P1 to PLATFORM_INFO; sets HWP_CAPABILITIES.Guaranteed_Performance | P1 resolution flow; `source/pcode/flows/autonomous_pstate/` | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) |
| PrimeCode (IMH) | IMH die | No direct flex ratio role; package-scope power limits may further constrain P1 headroom | HPM power limits | DMR SoC PM HAS |
| BIOS / UEFI | Platform | Writes FLEX_RATIO (MSR 0x194) with desired cap ratio + enable bit during POST if platform needs it | Boot-time MSR write | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `FLEX_RATIO` | 0x194 | RW | [15:8] desired flex ratio; [16] enable bit; BIOS-written at POST | Intel SDM |
| MSR `PLATFORM_INFO` | 0x0CE [15:8] | RO | Resolved P1 guaranteed ratio (reflects flex cap if active) | Intel SDM |
| MSR `IA32_HWP_CAPABILITIES` | 0x771 | RO | `GUARANTEED_PERFORMANCE[15:8]` = resolved P1 | Intel SDM |
| CPUID leaf 0x16 | CPUID | RO | Base frequency (GHz) = resolved P1 × 100 MHz | Intel SDM |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Flex ratio resolution | Boot-time | — | PCode computes effective P1 = min(fused, flex, SST_PP, thermal) once at boot | Legacy Execution Flow |
| Turbo above flex ratio | Allowed | — | Flex ratio caps P1 (sustained) only; turbo above flex still permitted | Legacy Architecture Summary |
| P1 reporting consistency | 3 paths | — | PLATFORM_INFO[15:8], HWP_CAPABILITIES.Guaranteed_Performance, CPUID leaf 0x16 must all agree | Legacy Execution Flow |
| Valid flex ratio range | ≤ fused_P1 | — | Flex ratio > fused P1 is ignored; no-op | Legacy Architecture Summary |

## NWP Delta

**Flex ratio is fully supported on NWP server** — reused from DMR.

- Flex ratio flows unchanged
- Same MSR_FLEX_RATIO (0x194) interface
- Same BIOS-programmable ratio override mechanism

### Validation Impact
- Same flex ratio test cases apply
- Verify flex ratio range with NWP fuse limits

## Legacy (Human-Curated Reference)

### Architecture Summary

Flex Ratio allows BIOS to set the maximum non-turbo frequency ratio below the fused P1 ratio. This is configured via MSR 0x194 (FLEX_RATIO), where BIOS writes the desired maximum non-turbo ratio and sets the flex ratio enable bit. When enabled, the effective P1 becomes min(fused_P1, flex_ratio), effectively capping the guaranteed frequency.

Flex Ratio is used in several scenarios: power-constrained platforms where the full P1 would exceed thermal limits, validation configurations requiring deterministic frequency behavior, and manufacturing test modes. The feature interacts with SST-PP (Speed Select Technology — Performance Profile) which may independently set a different P1 per performance level.

PCode reads the FLEX_RATIO MSR during boot and uses the flex ratio as a ceiling when resolving the effective P1. If turbo is enabled, turbo ratios above the flex ratio are still permitted (flex ratio only limits P1, not turbo). Validation confirms that the flex ratio correctly clamps P1 and that PERF_STATUS reflects the capped frequency under load.

### Execution Flow

1. **BIOS Configuration** — BIOS reads fused P1 ratio and platform power constraints. If flex ratio is needed, BIOS writes the desired ratio to MSR 0x194 and sets the enable bit.
2. **PCode Boot Processing** — PCode reads FLEX_RATIO MSR during initialization. The effective P1 is computed as min(fused_P1, flex_ratio, SST_PP_P1).
3. **P1 Reporting** — Effective P1 is reported via CPUID leaf 0x16 (base frequency) and MSR 0x0CE (PLATFORM_INFO) guaranteed ratio field.
4. **Runtime Behavior** — Under sustained all-core load, cores operate at the flex-ratio-capped P1 (not fused P1). Turbo above flex ratio is still allowed if turbo is enabled.
5. **Validation** — Test sets various flex ratios via BIOS knob, boots OS, runs all-core load, and verifies PERF_STATUS matches the configured flex ratio as the sustained frequency.

### Key Registers & Interfaces

| Register / MSR | Address | Description |
|----------------|---------|-------------|
| FLEX_RATIO | MSR 0x194 | Flex ratio value + enable bit |
| PLATFORM_INFO | MSR 0x0CE | Reports effective P1 (guaranteed ratio) |
| IA32_PERF_STATUS | MSR 0x198 | Current ratio reflects flex-capped P1 |
| CPUID leaf 0x16 | CPUID | Base frequency (reflects flex ratio) |
| SST_PP P1 | TPMI | SST-PP performance profile P1 override |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) | Flex ratio in P-state hierarchy |
| HAS | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) | Flex ratio interaction with turbo |
| MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP flex ratio specification |
| PCode src | `source/pcode/flows/autonomous_pstate/` | Flex ratio resolution logic |

### Related Sightings

No flex ratio sightings identified for NWP. DMR sightings related to flex ratio vs SST-PP P1 interaction should be monitored.

### NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| Flex Ratio MSR | MSR 0x194 | Same | No interface change |
| P1 resolution | min(fused, flex, SST_PP) | Same | Same resolution logic |
| Turbo above flex | Allowed | Same | Flex only caps P1, not turbo |
| BIOS knob | Supported | Supported | Same BIOS configuration |
