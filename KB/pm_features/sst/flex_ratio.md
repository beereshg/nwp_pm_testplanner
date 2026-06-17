# SST > Flex Ratio

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SST](sst_main.md)
> **Source Confidence**: High for mutex rules and reset-time P1 resolution (confirmed from SST HAS, DMR P-state/Reset HAS). Partial for PCT-specific propagation (CLOS config, LP clip, TDP/RAPL impact). See [Source Notes](#source-notes).

## Baseline (DMR)

**SST × Flex Ratio** defines compatibility rules between FlexRatio and SST sub-features, and the reset-time P1 resolution path when FlexRatio is active. Features competing for the P1 base-frequency path are mutex: dynamic SST-PP and SST-BF cannot coexist with FlexRatio. SST-TF and SST-CP are fully compatible.

**Topology (NWP)**: SST-TF/PCT × FlexRatio is the active NWP concern. Dynamic SST-PP and SST-BF are ZBB’d, so their mutex is moot, but the FlexRatio × SST-TF compatibility path and P1 resolution flow still apply.

```
Reset-time P1 resolution (Phase 5)
├── Read fused P1 (FUSE_SST_PP_P1_RATIO[STRAP[SST_PP_LEVEL]])
├── Read BIOS flex request (FLEX_RATIO_L.flex_ratio if enable=1)
├── Read VDM strap flex ratio (VDMdw1.flex_ratio)
├── Resolve: effective_P1 = min(BIOS_request, VDM_strap)
└── Write RESOLVED_P1 → MAX_NON_TURBO_RATIO[LIMIT_RATIO]

BIOS boot (after P1 resolution)
├── Programs SST-TF/PCT CLOS registers referencing effective P1
├── Enforces mutex: dynamic PP + BF disabled when FlexRatio active
└── OC lock (FLEX_RATIO_L.oc_lock): gates MSR 0x1AD TRL writes at runtime
```

**Boot activation**: P1 resolution at Primecode reset Phase 5. FlexRatio mutex on dynamic PP/BF enforced at BIOS CPL3 SST configuration time.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| MSR interface | CBB compute | FlexRatio read/write path; OC lock gates MSR 0x1AD TRL writes | FLEX_RATIO_L (0x194), MAX_NON_TURBO_RATIO | [DMR P-State HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html) |
| VDM strap interface | IMH-P | Soft-strap source for FlexRatio (VDMdw1.flex_ratio); takes priority over BIOS if lower | VDMdw1.flex_ratio | [DMR Reset HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Reset/dmr_cbb_reset.html) |
| Core FIVR + PLL | CBB compute | Enforces resolved P1 as guaranteed minimum frequency ceiling | MAX_NON_TURBO_RATIO applied by workpoint calc | [DMR Reset HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Reset/dmr_cbb_reset.html) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PrimeCode (IMH-P) | IMH-P | Resolves FlexRatio at reset: reads fused P1 + BIOS CR + VDM strap; writes MAX_NON_TURBO_RATIO | `PUnitIp::resolveFlexRatio()` in `punit.cpp` (L385–435) | Primecode source |
| PCode (CBB) | Root CBB | Blocks dynamic PP and BF P1 updates when FlexRatio active; uses reset-resolved P1 as authoritative | `sst_manager.cpp` P1 gate logic | [DMR P-State HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html) |
| BIOS | Pre-OS | Writes FLEX_RATIO_L; enforces mutex (disables dynamic PP/BF when flex active); programs CLOS using effective P1 | BIOS PM knobs | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Acode | Compute core | Observes resolved P1 from MAX_NON_TURBO_RATIO; CDYN-indexed workpoint calc applies effective P1 floor | Architecture reference | [DMR P-State HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html) |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR | 0x194 (FLEX_RATIO_L) | RW (BIOS) | FlexRatio enable + requested ratio + OC lock bit | [DMR P-State HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html) |
| TPMI SST | SST_TF_INFO_0.FEATURE_SUPPORTED (per PP level) | RO | Reflects whether SST-TF/PCT is active; compatible with FlexRatio | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| MSR | 0x1AD (PRIMARY_TURBO_RATIO_LIMIT) | RW | TRL ratios; writes blocked if FLEX_RATIO_L.oc_lock=1 | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| FlexRatio resolution sources | 2: BIOS FLEX_RATIO_L.flex_ratio and VDM soft strap VDMdw1.flex_ratio | Primecode `punit.cpp` |
| P1 resolution timing | Reset Phase 5 only — not updated at runtime | [DMR Reset HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Reset/dmr_cbb_reset.html) |
| SST-TF/PCT × FlexRatio | ✅ Compatible — TRL ratios are fuse-based, unaffected by flex P1 | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Dynamic SST-PP × FlexRatio | ❌ Mutex — both affect P1; dynamic PP disabled when flex active | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| SST-BF × FlexRatio | ❌ Mutex (ZBB’d on NWP regardless) | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## NWP Delta

### NWP Status: ⚠ Partial

Flex Ratio × SST cross-product. Applicable for the SST-TF/PCT portion; ZBB'd features (PP/CP/BF) × Flex Ratio interactions are out of scope.

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| Flex Ratio × SST-TF/PCT | ✅ Allowed | ✅ [SST HAS mutex table](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Flex Ratio × SST-CP | ✅ Allowed | ✅ [SST HAS mutex table](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Flex Ratio × Dynamic SST-PP | ❌ Mutex (but SST-PP ZBB'd on NWP anyway) | ✅ [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html), [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| Flex Ratio × SST-BF | ❌ Mutex (but SST-BF ZBB'd on NWP anyway) | ✅ [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html), [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| Flex Ratio × Static SST-PP | ✅ Allowed (but SST-PP ZBB'd on NWP) | ✅ [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| `FLEX_RATIO_DISABLE` fuse | Not used (equation = 0x0) | Primecode source comment |

## Legacy (Human-Curated Reference)

### Architecture Summary

This subflow covers the **cross-product between Flex Ratio and SST features**. The common SST HAS explicitly defines which SST features can coexist with Flex Ratio, and the DMR P-state/Reset HAS describes how Flex Ratio participates in reset-time P1 resolution. The common basis for these restrictions is that **Flex Ratio, AVX P1, SST-BF, and dynamic SST-PP all affect the P1/base-frequency resolving path**.

#### SST × Flex Ratio Compatibility Matrix *(confirmed: [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html))*

| Flex Ratio | Dynamic SST-PP | Static SST-PP | SST-BF | SST-TF | SST-CP |
|------------|:-:|:-:|:-:|:-:|:-:|
| **Disabled** | ✅ YES | ✅ YES | ✅ YES | ✅ YES | ✅ YES |
| **Enabled** | ❌ NO | ✅ YES | ❌ NO | ✅ YES | ✅ YES |

**Key takeaway**: Flex Ratio is **allowed with SST-TF and SST-CP** but **mutex with dynamic SST-PP and SST-BF**. Static SST-PP remains allowed. This is because AVX P1, FlexRatio, SST-BF, and dynamic SST-PP all can affect P1 base frequency, so a mutex is imposed.

#### Reset-Time P1 Resolution *(confirmed: [DMR Reset HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Reset/dmr_cbb_reset.html))*

During reset, the P1 resolution flow is:
1. `FUSED_P1 = FUSE_SST_PP_P1_RATIO[STRAP[SST_PP_LEVEL]]` — read fused P1 for current PP level
2. Flex Ratio request is resolved (from BIOS CR and/or VDM soft strap)
3. Resulting `RESOLVED_P1` is written to `MAX_NON_TURBO_RATIO[LIMIT_RATIO]`

#### Flex Ratio Blocks Dynamic P1 Updates *(confirmed: [DMR P-state HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html))*

When Flex Ratio is enabled:
- **Dynamic change of SST-PP level should not change P1** — use global P1 resolved at reset
- **No updates from SST-BF and dynamic SST-PP** to the P1 ratio
- The resolved P1 from reset is the authoritative P1 for the entire boot session

#### What Is Flex Ratio

Flex Ratio is a BIOS mechanism to set the effective guaranteed frequency (P1) to a value **lower** than the fused P1. Sources of flex ratio:
1. **BIOS knob** → writes `FLEX_RATIO_L` PCU CR with `enable=1` and requested ratio
2. **VDM soft strap** → `VDMdw1.flex_ratio` field (overrides BIOS if lower)

The Primecode firmware resolves the final effective P1 via `PUnitIp::resolveFlexRatio()`:
- Reads fused P1 from `SST_PP_P1_RATIOS_ARRAY`
- Reads BIOS flex request from `FLEX_RATIO_L.flex_ratio` (if `enable` bit set)
- Reads VDM strap flex ratio from `VDMdw1.flex_ratio`
- Resolves: if BIOS request < VDM strap → VDM strap takes priority *(source: [punit.cpp L385–435](c:\github\firmware.management.primecode.firmware\src\ip\punit\v2_0\punit.cpp))*

#### Impact on SST-TF/PCT Frequency Hierarchy *(inferred — not directly confirmed from HAS)*

When Flex Ratio lowers effective P1, the SST-TF/PCT frequency hierarchy is expected to be affected:

| Parameter | Without Flex Ratio | With Flex Ratio (lower P1) | Confidence |
|-----------|-------------------|---------------------------|------------|
| LP clip ratio (~P1) | Fused LP_CLIP_RATIO | ⚠ May still reference fused value | Unconfirmed |
| `SST_CLOS_CONFIG[0].min` (HP floor) | Fused P1 | ⚠ Depends on whether BIOS re-programs | Inferred |
| HP TRL ratio (SST_TF_INFO_2) | Fuse-defined | Unchanged — TRL ratios are fuse-based | Confirmed (SST HAS) |
| TDP | Based on fused P1 | Expected reduced — lower P1 → lower TDP | Inferred |
| Turbo headroom | Normal | Potentially increased | Inferred |

> **⚠ Needs verification**: Whether BIOS re-programs SST CLOS config min/max values and LP clip ratio when Flex Ratio changes P1. The SST HAS confirms Flex Ratio + SST-TF are allowed to coexist, and DMR Reset HAS confirms P1 resolution, but the CLOS config propagation path needs confirmation from BIOS FAS.

#### OC Lock Interaction

The `FLEX_RATIO_L.oc_lock` bit gates overclocking behavior:
- If `oc_lock = 1`, current TRL MSR `0x1AD` values define limits (cannot be raised at runtime)
- SST-TF/PCT TRL override (writing `SST_TF_INFO_2.RATIO_0` to MSR `0x1AD`) is expected to be subject to this lock
- *(source: [wp_calc_oc.cpp L324–325](c:\github\firmware.management.primecode.firmware\src\flow\wp_calc\wp_calc_oc\wp_calc_oc.cpp) — Primecode, not directly from HAS)*


### Execution Flow

```
1. Reset-Time P1 Resolution (confirmed: DMR Reset HAS)
   ├── FUSED_P1 = FUSE_SST_PP_P1_RATIO[STRAP[SST_PP_LEVEL]]
   ├── Read BIOS flex request (FLEX_RATIO_L.flex_ratio, if enable=1)
   ├── Read VDM strap flex ratio (VDMdw1.flex_ratio)
   ├── Resolve: min(BIOS request, VDM strap) → RESOLVED_P1
   └── Write RESOLVED_P1 → MAX_NON_TURBO_RATIO[LIMIT_RATIO]

2. BIOS Boot
   ├── Programs SST-TF/PCT CLOS registers (referencing effective P1)
   └── Mutex enforced: dynamic SST-PP and SST-BF disabled if Flex Ratio active

3. Primecode Init
   ├── resolveFlexRatio() → confirms effective P1
   └── Effective P1 feeds into P-state resolution, TDP calculation

4. Runtime (confirmed: DMR P-state HAS)
   ├── If Flex Ratio enabled: dynamic SST-PP level changes do NOT change P1
   ├── SST-TF/PCT operates with CLOS-based partitioning using RESOLVED_P1
   ├── HP cores: up to TRL ratio (fuse-based, not affected by flex)
   └── LP cores: clipped to LP_CLIP_RATIO (⚠ may or may not track flex P1)

5. Test Validation (22022462194)
   └── SST — Flex Ratio — CrossProduct
       ├── Verify SST-TF/PCT behavior with lowered P1
       ├── Check CLOS config adapts to effective P1
       └── Verify turbo ratios above P1 still function
```


### Key Registers & Interfaces

| Register | Description | Source |
|----------|-------------|--------|
| `MAX_NON_TURBO_RATIO[LIMIT_RATIO]` | Resolved P1 output from reset-time resolution | ✅ [DMR Reset HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Reset/dmr_cbb_reset.html) |
| `FLEX_RATIO_L` (PCU CR) | Flex ratio enable + ratio value + OC lock + OC extra voltage | ✅ Primecode source (`punit.cpp`) |
| `VDMdw1.flex_ratio` | VDM soft strap flex ratio override | ✅ Primecode source (`punit.cpp`) |
| `SST_PP_P1_RATIOS_ARRAY` (fuse) | Fused P1 ratios per SST-PP level (baseline for flex resolution) | ✅ Primecode source (`sst.cpp`), DMR Reset HAS |
| `FLEX_RATIO_DISABLE` (fuse) | GNR: disables flex ratio capability. DMR/NWP: fuse equation = 0x0 (not used) | ✅ Primecode fuses.xml |
| `SST_CLOS_CONFIG[0].min` | HP core floor — may reference P1 (flex or fused) | ⚠ Interaction not directly confirmed from HAS |
| MSR `0x1AD` (Turbo_Ratio_Limit) | Subject to `FLEX_RATIO_L.oc_lock` gating | ✅ Primecode `wp_calc_oc.cpp` |


### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [Intel SST HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | **SST × FlexRatio compatibility matrix** — authoritative mutex table |
| HAS | [DMR CBB P-state HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html) | Flex Ratio blocks dynamic PP/BF P1 updates |
| HAS | [DMR CBB Reset HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Reset/dmr_cbb_reset.html) | Reset-time P1 resolution (FUSED_P1 → RESOLVED_P1) |
| FAS | [DMR CBB P-state FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/P_State/p_state_fas.html) | Flex Ratio runtime enforcement details |
| HAS | [PCT HAS (Arch Common)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) | PCT frequency hierarchy — LP clip, HP TRL |
| HAS | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) | Turbo/TRL interaction with Flex Ratio |
| Primecode src | [punit.cpp::resolveFlexRatio()](c:\github\firmware.management.primecode.firmware\src\ip\punit\v2_0\punit.cpp) | Flex ratio resolution logic (fused P1, BIOS, VDM strap) |
| Primecode src | [wp_calc_oc.cpp](c:\github\firmware.management.primecode.firmware\src\flow\wp_calc\wp_calc_oc\wp_calc_oc.cpp) | OC lock interaction with TRL |
| Primecode src | [peach_prt_hal.hpp](c:\github\firmware.management.primecode.firmware\src\flow\peach_prt\v2_0\peach_prt_hal.hpp) | FLEX_RATIO_REG HAL definition |
| Parent | [PCT](pct.md) | PCT architecture, CLOS config, frequency hierarchy |
| Parent | [Pstate-Flex Ratio](../pstate_stack/pstate_flex_ratio.md) | Standalone Flex Ratio feature (non-SST context) |
| Comparison | [DMR vs NWP PM Comparison](../../dmr_vs_nwp_pm_comparison.html) | Feature-level support/ZBB matrix |


### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->


### Source Notes

| Claim Category | Confidence | Source |
|---------------|------------|--------|
| SST × Flex Ratio compatibility matrix (mutex rules) | ✅ Confirmed | [SST HAS — Cross Products table](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Flex Ratio + SST-TF allowed, + dynamic PP/BF disallowed | ✅ Confirmed | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| P1/base-frequency overlap is the reason for mutex | ✅ Confirmed | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — "AVX P1, FlexRatio, SST-BF, and dynamic SST-PP all can affect P1" |
| Reset-time P1 resolution (FUSED_P1 → RESOLVED_P1) | ✅ Confirmed | [DMR Reset HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Reset/dmr_cbb_reset.html) |
| Flex Ratio blocks dynamic PP/BF P1 updates at runtime | ✅ Confirmed | [DMR P-state HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html) |
| Flex Ratio resolution logic (fused P1, BIOS CR, VDM strap) | ✅ Confirmed | [punit.cpp L385–435](c:\github\firmware.management.primecode.firmware\src\ip\punit\v2_0\punit.cpp) (Primecode) |
| `FLEX_RATIO_L` register fields (enable, ratio, oc_lock) | ✅ Confirmed | Primecode source + register headers |
| `FLEX_RATIO_DISABLE` fuse = 0x0 on DMR | ✅ Confirmed | Primecode fuses.xml + source comment |
| OC lock gates TRL MSR 0x1AD | ✅ Confirmed | [wp_calc_oc.cpp L324–325](c:\github\firmware.management.primecode.firmware\src\flow\wp_calc\wp_calc_oc\wp_calc_oc.cpp) (Primecode, not HAS) |
| SST CLOS config adapts to flex P1 | ⚠ Inferred | Architecturally expected; not directly confirmed from BIOS FAS |
| LP clip ratio tracks flex P1 | ⚠ Unconfirmed | LP_CLIP_RATIO is fuse-based; unclear if BIOS adjusts |
| TDP reduction under flex ratio | ⚠ Inferred | Standard P1 → TDP relationship; not confirmed from specific HAS passage |
| NWP uses same resolveFlexRatio() path | ⚠ Inferred | Same Primecode v2_0 code; NWP DUT config not verified |
