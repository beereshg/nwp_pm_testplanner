# Pstate Stack > Pstate-Guaranteed Ratio P1

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: P1 (Guaranteed Ratio) is the maximum frequency all cores can sustain indefinitely within TDP — the baseline performance commitment for capacity planning. PCode resolves P1 at boot from multiple inputs: fused P1, FLEX_RATIO, SST-PP level, and thermal clip; publishes the result to three discovery paths for OS and tooling.

**Topology**:
```
Fuse register (manufacturing P1) ──────────────────────────────┐
MSR FLEX_RATIO (0x194, BIOS-set) ─────────────────────────────┤
SST_PP level P1 (TPMI, if active) ────────────────────────────┤──> PCode P1 resolution
Thermal clip (platform Tjmax / cooling) ──────────────────────┘   effective_P1 = min(all)
                                                                        │
                  ┌─────────────────────────────────────────────────────┤
                  ▼                    ▼                                ▼
  PLATFORM_INFO (MSR 0x0CE [15:8])   HWP_CAPABILITIES.Guaranteed     CPUID leaf 0x16
         (OS boot discovery)          Performance (MSR 0x771 [15:8])  (base freq in GHz)
```

**Key operational principle**: All three P1 publication paths must consistently report the resolved P1. Turbo above P1 is still available (P1 is not a turbo cap). Under all-core sustained load, cores hold at P1; single-core turbo may go above. NWP removes SST-PP input (single P1 value per SKU).

**Boot activation**: PCode resolves P1 at early init; publishes before CPL3 handoff. BIOS reads PLATFORM_INFO to discover P1 for thermal planning.

The Guaranteed Ratio (P1) is the maximum frequency at which all cores can run indefinitely under worst-case workload within the platform's thermal and electrical design point. P1 is the most critical frequency operating point in the P-state stack — it defines the baseline performance guarantee that the OS and datacenter operators rely on for capacity planning.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Fuse register | IMH die | Stores manufacturing-characterized P1 ratio; basis for all P1 resolution | Fuse read at early init | CBB PM HAS |
| Core FIVR + PLL | CBB Top Die | Sustain P1 ratio indefinitely under all-core load; GV transition to P1 on power-limit entry | GV control | CBB PM HAS |
| MSR interface | Per-core | PLATFORM_INFO (0x0CE), HWP_CAPABILITIES (0x771), FLEX_RATIO (0x194) — all P1 resolution inputs/outputs | MSR bus | Intel SDM |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | No direct P1 resolution role; operates at PCode-set P1 under sustained load | — | — |
| PCode (CBB) | CBB Base Die | Reads fused P1, FLEX_RATIO (0x194), SST_PP level, thermal clip at boot; computes effective_P1 = min(all); writes PLATFORM_INFO[15:8]; sets HWP_CAPABILITIES.Guaranteed_Performance (MSR 0x771) | P1 resolution flow; `source/pcode/flows/autonomous_pstate/` | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) |
| PrimeCode (IMH) | IMH die | No direct P1 resolution role; propagates package-level power limits that may constrain sustained frequency | HPM power limits | DMR SoC PM HAS |
| BIOS / UEFI | Platform | Writes FLEX_RATIO if needed; reads PLATFORM_INFO to discover P1; programs thermal clip parameters | Boot-time; MSR 0x194; MSR 0x0CE read | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `PLATFORM_INFO` | 0x0CE [15:8] | RO | Resolved P1 guaranteed ratio — primary OS P1 discovery register | Intel SDM |
| MSR `IA32_HWP_CAPABILITIES` | 0x771 [15:8] | RO | `GUARANTEED_PERFORMANCE` field = P1 (when HWP enabled) | Intel SDM |
| CPUID leaf 0x16 | CPUID | RO | Processor Base Frequency (MHz) = P1 × 100 MHz; OS uses for capacity planning | Intel SDM |
| MSR `FLEX_RATIO` | 0x194 | RW | [15:8] optional P1 cap; [16] enable — set by BIOS if platform needs P1 below fused | Intel SDM |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| P1 resolution inputs | 4 | — | min(fused_P1, flex_ratio, SST_PP_P1, thermal_clip) — NWP removes SST_PP (single P1 per SKU) | Legacy Execution Flow |
| P1 publication paths | 3 | — | PLATFORM_INFO[15:8], HWP_CAPABILITIES.Guaranteed, CPUID leaf 0x16 — must all agree | Legacy Execution Flow |
| P1 resolution timing | Boot-time (once) | — | PCode resolves at early init; immutable until reboot | Legacy Execution Flow |
| Sustained all-core frequency | = P1 | — | Cores hold at P1 under all-core sustained load within TDP | Legacy Architecture Summary |
| NWP SST-PP removal | N/A | — | SST-PP removed on NWP → single P1 value per SKU; no per-level P1 variation | Legacy NWP Delta |

## NWP Delta

**Guaranteed ratio (P1) is fully supported on NWP server** — reused from DMR.

- Guaranteed ratio (P1) flows unchanged
- Same fuse-based P1 definition
- SST-PP removed on NWP → no per-SST-level P1 variation (single P1 value)
- SST-BF removed → no SST-BF high-priority core P1 boost

### Validation Impact
- Same P1 test cases apply
- Skip SST-PP/BF P1 cross-product tests (features removed on NWP)

## Legacy (Human-Curated Reference)

### Architecture Summary

The Guaranteed Ratio (P1) is the maximum frequency at which all cores can run indefinitely under worst-case workload within the platform's thermal and electrical design point. P1 is the most critical frequency operating point in the P-state stack — it defines the baseline performance guarantee that the OS and datacenter operators rely on for capacity planning.

P1 resolution is a multi-input process. The fused P1 ratio (from manufacturing characterization) is the starting point. This is then constrained by: Flex Ratio (MSR 0x194) if configured by BIOS, SST-PP (Speed Select Technology — Performance Profile) level if a non-default profile is selected, and thermal clip if the platform's cooling solution cannot sustain the fused P1 at worst-case ambient temperature.

The final effective P1 = min(fused_P1, flex_ratio, SST_PP_P1, thermal_clip). PCode computes this during boot and reports it via MSR 0x0CE (PLATFORM_INFO) bits [15:8] and CPUID leaf 0x16. Validation confirms that P1 resolves correctly for all combinations of flex ratio, SST-PP level, and thermal constraints.

### Execution Flow

1. **Fuse Read** — PCode reads the fused P1 ratio from manufacturing characterization fuses during early boot.
2. **Flex Ratio Check** — PCode reads MSR 0x194 (FLEX_RATIO). If enabled and lower than fused P1, flex ratio constrains P1.
3. **SST-PP Level Check** — PCode reads the active SST-PP performance level. Each level defines its own P1 ratio; if lower than the current candidate, it constrains P1.
4. **Thermal Clip Check** — PCode evaluates thermal design constraints. If the platform's Tjmax or cooling solution requires a lower sustainable frequency, thermal clip constrains P1.
5. **P1 Publication** — PCode writes the resolved P1 to PLATFORM_INFO (MSR 0x0CE) bits [15:8] and populates CPUID leaf 0x16 base frequency. HWP_CAPABILITIES (MSR 0x771) guaranteed_performance field is set to the resolved P1.
6. **Validation** — Test reads P1 from PLATFORM_INFO, CPUID, and HWP_CAPABILITIES. Confirms P1 matches expected min() of all inputs. Runs all-core load and verifies sustained frequency equals resolved P1.

### Key Registers & Interfaces

| Register / MSR | Address | Description |
|----------------|---------|-------------|
| PLATFORM_INFO | MSR 0x0CE [15:8] | Resolved guaranteed ratio (P1) |
| FLEX_RATIO | MSR 0x194 | Optional P1 override |
| IA32_HWP_CAPABILITIES | MSR 0x771 | Guaranteed performance field = P1 |
| CPUID leaf 0x16 | CPUID | Base frequency (P1 × bus clock) |
| SST_PP config | TPMI MMIO | SST-PP performance level P1 |
| Fused P1 | Fuse register | Manufacturing-characterized P1 ratio |
| Thermal clip | PCode internal | Thermal-constrained P1 limit |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) | P1 resolution rules |
| HAS | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) | P1 in turbo context |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | P1 resolution in CBB PM |
| MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP P1 specification |
| PCode src | `source/pcode/flows/autonomous_pstate/` | P1 resolution flow |

### Related Sightings

No P1 resolution sightings identified for NWP. DMR sightings related to P1 mismatch between PLATFORM_INFO and CPUID should be monitored.

### NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| P1 resolution logic | min(fused, flex, SST_PP, thermal) | Same | No change in resolution algorithm |
| Fused P1 values | DMR SKU-dependent | NWP SKU-dependent | Different fuse values per NWP SKU |
| SST-PP integration | Supported | Supported | Same SST-PP P1 override mechanism |
| Thermal clip | Platform-dependent | Platform-dependent | Different thermal limits per NWP platform |
