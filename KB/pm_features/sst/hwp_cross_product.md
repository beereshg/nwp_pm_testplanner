# SST > HWP Cross-Product

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SST](sst_main.md)
> **Source Confidence**: High — Cross-product logic from PCode `sst_manager.cpp` (`update_cfgs`), Primecode `pstate_stack.dox` (§pm_recalc_capabilities), Primecode SST common (`sst.cpp`). NWP scope inferred from [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) SST scope.

## Baseline (DMR)

**SST × HWP Cross-Product** defines how HWP (Hardware P-states) interacts with SST state changes. Every SST event (PP level switch, TF/BF enable/disable, FCT/OC change) triggers HWP_CAPABILITIES recomputation per module. Critical gate: if HWP is disabled (`MISC_PWR_MGMT2.ENABLE_HWP = 0`), PCode blocks ALL SST runtime changes and locks PP to the boot level.

**Topology**: SST event (TPMI write) → PCode `update_cfgs()` gate → TRL array reload (WP calc) → HWP_CAPABILITIES update per module → PREQ/HWPREQ recalculation → Leaf reports to Root.

```
SST event → HWP capabilities flow
├── PCode checks ENABLE_HWP gate (if 0: block all SST changes, clear capability bits)
├── PrimeCode WP calc getSstTfFromFuses() pulls new SST fuses for current PP level
├── TRL arrays updated (wp_calc_fct.cpp reads SST_PP_TURBO_RATIO_LIMIT_RATIOS_ARRAY fuses)
├── HWP capabilities recomputed per module:
│   ├── Highest_Perf = new max ratio (P0max for HP cores under PCT)
│   └── Guaranteed_Perf = new P1 (from active PP level)
├── PREQ/HWPREQ recalculated and clipped against new capability limits
└── Leaf reports updated capabilities to Root via HPM for PCS

HWP disabled → SST gate
└── ENABLE_HWP=0 → CAPABILITY_MASK[CP] cleared
              → SST_PP_HEADER.ALLOWED_LEVEL_MASK frozen to boot level
              → SST_BF_INFO_0.FEATURE_SUPPORTED cleared (all PP levels)
              → SST_TF_INFO_0.FEATURE_SUPPORTED cleared (all PP levels)
```

**Boot activation**: HWP enabled at BIOS CPL3 (prerequisite for SST-TF/PCT). SST runtime capabilities re-evaluated by `update_cfgs()` if HWP state changes.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| HWP MSR interface | CBB compute | Gate register: HWP disabled → all SST runtime blocked | MISC_PWR_MGMT2.ENABLE_HWP (MSR 0x1A0 bit 18) | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST capability | IMH-P | Capability mask, allowed PP level, TF/BF feature-supported bits — gated by HWP state | SST_HEADER.CAPABILITY_MASK, SST_PP_HEADER.ALLOWED_LEVEL_MASK | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Core FIVR + PLL | CBB compute | Applies updated HWP_CAPABILITIES (Highest_Perf, Guaranteed_Perf) after each SST event | HWP_CAPABILITIES per module | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PCode (CBB Root) | Root CBB | SST runtime gate: checks ENABLE_HWP before any SST state change; clears capability bits if HWP off | `sst_manager.cpp::update_cfgs()` | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| PrimeCode WP calc | IMH-P | Pulls new SST fuses on SST event; updates TRL arrays; recomputes HWP capabilities per module | `getSstTfFromFuses()`, `wp_calc_fct.cpp`, `wp_calc_inits.cpp` | Primecode source |
| PCode (CBB Leaf) | Leaf CBB | Recalculates PREQ/HWPREQ against new capability limits; reports updated capabilities to Root via HPM | WP calc leaf path | Primecode source |
| BIOS | Pre-OS | Enables HWP (mandatory prerequisite for SST runtime); programs CLOS and PP level under HWP mode | BIOS PM knobs | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR | MISC_PWR_MGMT2.ENABLE_HWP (0x1A0 bit 18) | RW | HWP enable gate — must be 1 for SST runtime changes to take effect | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_HEADER.CAPABILITY_MASK | RO | CP bit cleared if HWP off; OS must check before enabling SST-CP | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| MSR | IA32_HWP_CAPABILITIES (0x771) per module | RO | Highest_Perf, Guaranteed_Perf; recomputed after each SST event | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI | SOCKET_RAPL_PL1_CONTROL | RW | OOB mode: PL1 drives CLOS_*_LIMIT fields via RAPL_PERF_LIMIT HPM (msgs 0x14–0x15) | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| SST→HWP recalc trigger events | PP change, TF enable/disable, BF enable/disable, FCT/OC change | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| HWP disabled behavior | PP locked to boot level; CP/BF/TF capability cleared; ALLOWED_LEVEL_MASK frozen | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| RAPL OOB PL1 → CLOS_*_LIMIT | Via RAPL_PERF_LIMIT HPM messages 0x14–0x15 | SST HAS + PCode HPM XML |
| PCT × HWP test coverage | 22022452981, 22022455929, 22022462193 (via HWP Cross-Product subflow) | NWP test plan |

## NWP Delta

### NWP Status: ⚠ Partial

HWP × SST cross-product. Applicable for SST-TF/PCT × HWP interactions (HWP_CAPABILITIES, FlexRatio, OOB mode). PCT-specific HWP behavior (different `highest_perf` for HP vs LP cores) is the primary NWP-relevant interaction.

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| HWP × SST-TF/PCT | ✅ Applicable | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — per-core `highest_perf` differentiation |
| HWP × SST-PP/CP/BF | ❌ Out of scope (ZBB'd) | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |

## Legacy (Human-Curated Reference)

### Architecture Summary

**SST × HWP cross-product** covers the interactions between SST sub-features (PP, TF, BF, CP) and the HWP (Hardware P-states) framework. When SST changes the operating point — such as switching PP level, enabling/disabling TF or BF — the HWP capabilities (Highest_Perf, Guaranteed_Perf, Most_Efficient_Perf) must be recomputed for each module, and PREQ/HWPREQ must be recalculated against the new capability limits. A critical gate: **if HWP is disabled** (`MISC_PWR_MGMT2.ENABLE_HWP = 0`), PCode disables all runtime SST changes — SST_CP capability is cleared, BF/TF are marked unsupported, and the allowed PP level mask is locked to the boot level.

#### Key Interactions

| SST Event | HWP Impact |
|-----------|------------|
| PP level change | P1 ratio changes → Guaranteed_Perf changes → HWP capabilities updated → PREQ recalc |
| SST-TF enable/disable | Max ratio changes for HP cores → Highest_Perf changes → capabilities recalc |
| SST-BF enable/disable | Guaranteed ratio changes for BF cores → capabilities recalc |
| FCT/Overclocking change | TRL arrays updated via `getSstTfFromFuses()` → max turbo changes → capabilities recalc |
| HWP disabled (by BIOS) | All SST runtime changes blocked — PP locked to boot level, CP/BF/TF cleared |
| OOB Mode | OOB writes to TPMI `SOCKET_RAPL_PL1_CONTROL` interact with CLOS limits — RAPL PL1 drives `CLOS_*_LIMIT` |

#### FlexRatio Interaction
When SST-PP level changes, the P1 ratio for the new level is read from fuses (`SST_PP_%I_%J_P1_RATIO`). This new P1 becomes the guaranteed ratio in HWP_CAPABILITIES. If turbo is disabled (fuse, BIOS, or DFX), `max_ratio = guaranteed_ratio` (P1), collapsing the turbo headroom.


### Execution Flow

1. SST feature change triggers event in Base IA class
2. `Primecode::WorkpointCalc::getSstTfFromFuses()` pulls new SST fuses for current PP level
3. TRL arrays updated via `wp_calc_fct.cpp` — reads `SST_PP_TURBO_RATIO_LIMIT_RATIOS_ARRAY` fuses
4. HWP capabilities recomputed per module (Highest = new max ratio, Guaranteed = new P1)
5. PREQ/HWPREQ recalculated and clipped against new capabilities
6. Leaf sends updated capabilities to Root for PCS reporting (HPM)


### Key Registers & Interfaces

| Register | Relationship |
|----------|-------------|
| `MISC_PWR_MGMT2.ENABLE_HWP` | Gate — if 0, SST runtime changes blocked |
| `SST_HEADER.CAPABILITY_MASK` | CP bit cleared when HWP disabled |
| `SST_PP_HEADER.ALLOWED_LEVEL_MASK` | Locked to boot level when HWP disabled |
| `SST_BF_INFO_0.FEATURE_SUPPORTED` | Cleared per-level when HWP disabled |
| `SST_TF_INFO_0.FEATURE_SUPPORTED` | Cleared per-level when HWP disabled or turbo hard-disabled |
| HWP_CAPABILITIES (per module) | Updated when SST changes P1/max ratios |


### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST-PP/TF/BF register specs |
| PCode SST mgr | `source/pcode/flows/sst/sst_manager.cpp` | `update_cfgs()` — HWP gate logic |
| Primecode WP calc | `src/flow/wp_calc/wp_calc_oc/wp_calc_oc.cpp` | `getSstTfFromFuses()` — TRL update on SST change |
| Primecode WP calc inits | `src/flow/wp_calc/wp_calc_inits/v2_0/wp_calc_inits.cpp` | SST fuse pull at init |
| Primecode WP calc FCT | `src/flow/wp_calc/wp_calc_fct/wp_calc_fct.cpp` | TRL array population from SST fuses |
| Primecode pstate doc | `src/doc/pstate_stack.dox` | §pm_recalc_capabilities — SST→HWP flow diagram |
| PCode HPM RAPL msg | `source/hpm/hpm_msgs.xml` | `RAPL_PERF_LIMIT` — CLOS_*_LIMIT fields |


### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->
