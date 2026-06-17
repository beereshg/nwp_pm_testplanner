# SST > Cross-Product

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SST](sst_main.md)
> **Source Confidence**: Mixed — SST cross-product framework and FlexRatio interaction matrix directly confirmed from SST HAS. C6 power redistribution and PkgC state persistence behaviors are architecturally inferred. See [Source Notes](#source-notes).

## Baseline (DMR)

**SST Cross-Product** covers interactions between SST sub-features and other PM features (C-states, PkgC, RAPL, FlexRatio, HWP). Features that share the P1 base-frequency path (dynamic SST-PP, SST-BF, FlexRatio) are mutually exclusive; SST-TF and SST-CP remain compatible with FlexRatio.

**Topology (NWP)**: Only SST-TF/PCT is active on NWP. The two original cross-product test cases (SST-CP×PBF×C6, PP×PkgC) reference ZBB’d features and are removed from NWP scope. Active NWP cross-products (PCT×C6, PCT×RAPL, PCT×HWP, PCT×SST-PP) are validated through sibling subflows.

```
Boot sequence
├── BIOS enables SST-TF/PCT: HP→CLOS[0], LP→CLOS[3]
├── BIOS programs RAPL PL1/PL2 (socket power envelope unchanged by SST)
└── FlexRatio mutex enforced: dynamic PP and BF remain disabled when Flex active

Runtime interactions (NWP-applicable)
├── PCT × C6: HP cores enter C6 idle; CLOS state must restore on wakeup
├── PCT × RAPL: PL1/PL2 limit hit → LP cores throttle first (SST-CP ordered priority)
├── PCT × HWP: SST event triggers HWP_CAPABILITIES recompute per module
└── PCT × PkgC: SST TPMI register state must survive PkgC entry/exit [gap — no NWP TC]
```

**Boot activation**: Enabled at BIOS CPL3 via SST-TF knob. RAPL and C-states are always co-active.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| TPMI SRAM | IMH-P | Stores SST CLOS/PP registers; NVM-backed, survives PkgC | SST_CLOS_CONFIG_*, SST_PP_CONTROL, SST_PP_STATUS | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Core FIVR + PLL | CBB compute die | Enforces per-CLOS frequency min/max limits via workpoint calc | CLOS ratio enforcement | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Package C-state controller | IMH-P | PkgC entry/exit; TPMI NVM preserves SST state | OPC_PKGC_ENTRY_CONTROL | [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PCode (CBB) | Root + Leaf CBB | SST-CP ordered throttling during RAPL limit; CLOS frequency arbitration | `sst_manager.cpp::update_cfgs()`, `ccp_manager.cpp` | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| PrimeCode (IMH-P) | IMH-P | TPMI SST register init and state persistence across reset/PkgC | `sst_tpmi_general.cpp::tpmiInit()`, `repopulateSstVarsFromTpmiReg()` | Primecode source |
| Acode | Compute core | C6 entry/exit; CLOS assignment preserved on core wakeup | Architecture reference | [DMR PkgC HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Idle_Flow/DMR_PkgC.html) |
| BIOS | Pre-OS | Enables SST-TF/PCT; programs CLOS assignments; enforces FlexRatio mutex; sets PkgC policy | CLOS/TF BIOS knobs | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| TPMI SST | SST_CP_CONTROL, SST_CLOS_CONFIG_0..3 | RW | CLOS priority type and per-CLOS min/max frequency bounds | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| TPMI SST | SST_PP_CONTROL.current_config_index | RW | Active PP level; state must persist across PkgC | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| CSR | PACKAGE_RAPL_LIMIT | RW | PL1/PL2 power limits; unchanged by SST; must match active PP-level TDP post-PkgC | [Socket RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| SST state persistence across PkgC | All TPMI SST registers survive via TPMI NVM | [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) |
| FlexRatio mutex | Dynamic SST-PP + SST-BF disabled when FlexRatio active | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| PCT × C6 test coverage | 22022422104, 22021970028 (via PCT subflow) | NWP test plan |
| PCT × RAPL test coverage | 22022462184 (via RAPL subflow) | NWP test plan |
| PCT × PkgC coverage | No dedicated NWP TC — identified gap | NWP cross-product landscape |

## NWP Delta

### NWP Status: Scope Revised -- ZBB'd features removed

Both original test cases referenced ZBB'd features on NWP and have been removed from `nwp_pm_test_cases.json`:
- `SST-CP-PBF-HP-C6 Harasser` (16025655021) -- SST-CP and SST-BF (PBF) are ZBB'd
- `PP x PkgC Cross Product` (16025659319) -- SST-PP is ZBB'd

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| SST-CP x PBF x C6 | N/A -- features ZBB'd, test removed | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| PP x PkgC | N/A -- SST-PP ZBB'd, test removed | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| PCT x PkgC / PCT x C-state | **Gap** -- no dedicated test case | Potential cross-product gap for NWP |

### Identified Gap: PCT x PkgC

No test validates **PCT x PkgC**: what happens to PCT CLOS configuration, HP/LP assignments, and TPMI register state across PkgC entry/exit cycles. Consider adding a dedicated test case for NWP.

## Legacy (Human-Curated Reference)

### Architecture Summary

This subflow covers **cross-product interactions between SST sub-features and other PM features** (C-states, PkgC, RAPL, FlexRatio, HWP). These interactions validate that simultaneously active PM features do not conflict or produce unexpected behavior when SST is enabled.

> **Note on confidence**: The SST HAS explicitly documents cross-product interactions and a FlexRatio compatibility matrix. However, detailed runtime behaviors (C6 power redistribution, PkgC state persistence) are architecturally expected but not directly confirmed from the retrieved HAS excerpts. Claims below are marked accordingly.

#### SST FlexRatio Cross-Product Matrix (Confirmed)

The [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) explicitly defines which SST features are compatible with FlexRatio enabled:

| SST Feature | FlexRatio Enabled | Notes |
|-------------|-------------------|-------|
| Dynamic SST-PP | **NO** | PP switching disabled when flex ratio active |
| Static SST-PP | **YES** | Static config allowed |
| SST-BF | **NO** | PBF base frequency boost disabled |
| SST-TF | **YES** | Turbo Frequency compatible |
| SST-CP | **YES** | CLOS priority compatible |

*(Source: Intel SST HAS, Cross Products section)*

#### SST × RAPL Interaction (Confirmed)

The [DMR RAPL FHAS](https://docs.intel.com/documents/primecode/fhas/DMR/RAPL/SERVERPMFW-1024.html) explicitly lists SST under cross-product validation alongside Reset, P-state stack, PkgC, and UFS. The SST HAS further states:

> *"The RAPL budget balancer in SST-PP prioritization algorithm must account for the core count of the current SST-PP config level."*

#### DMR Test Case 1: SST-CP x PBF x HP-C6 Harasser (DMR-only)

> **NWP**: Not applicable — SST-CP and SST-BF (PBF) are ZBB'd on NWP. Test removed from NWP scope.

**Feature interaction**: SST-CP (CLOS-based core priority) + SST-BF/PBF (Priority Based Frequency) + C6 idle state on HP cores + stress workload ("harasser") on LP cores.

**What it validates** (on DMR):
- When HP cores (CLOS[0/1]) with guaranteed BF boost enter C6 idle, their freed power budget should become available
- LP cores running a harasser workload should not exhibit unexpected frequency spikes or throttling
- SST-CP ordered throttling should remain consistent across C6 entry/exit transitions
- PBF frequency guarantees should restore correctly when HP cores wake from C6

> **⚠ Inferred**: The C6 power redistribution and frequency restoration behaviors are architecturally expected from CLOS semantics but were not directly confirmed from specific HAS passages.

**Architecture path**:
1. BIOS enables SST-CP + SST-BF -> HP cores get elevated base frequency via PBF
2. OS scheduler parks HP cores -> HP cores enter C6
3. PCode detects C6 -> redistributes power headroom
4. LP cores running harasser -> should stay within CLOS[2/3] frequency bounds
5. HP cores wake -> PBF base frequency guarantee must restore

#### DMR Test Case 2: PP x PkgC Cross Product (DMR-only)

> **NWP**: Not applicable — SST-PP is ZBB'd on NWP. Test removed from NWP scope.

**Feature interaction**: SST-PP (Performance Profile) + PkgC (Package C-state).

**What it validates** (on DMR):
- SST-PP configuration persists correctly across PkgC entry/exit cycles
- PP-level TDP changes do not corrupt PkgC entry/exit thresholds
- After PkgC exit, the active PP level's TDP, P1, and TRL ratios are correctly restored
- No PkgC residency regression when SST-PP is active

> **⚠ Inferred**: PP state persistence across PkgC is expected standard TPMI register behavior but was not directly confirmed from specific HAS passages.

**Architecture path**:
1. BIOS/OS sets active SST-PP level (TDP config N)
2. System goes idle -> enters PkgC (C6/C2)
3. External event wakes package -> PkgC exit
4. Primecode/PCode restores SST-PP state -> verify TDP, P1, TRL match pre-PkgC values
5. OS reads TPMI SST registers -> verify config consistency


### NWP Cross-Product Landscape

Since NWP supports only **PCT/SST-TF** (all other SST features ZBB'd), the two original test cases (16025655021, 16025659319) have been **removed from NWP scope**. The relevant NWP cross-product coverage comes entirely from sibling subflows:

| Cross-Product | DMR Status | NWP Status | Coverage |
|--------------|------------|------------|----------|
| SST-CP x PBF x C6 | Active | N/A (ZBB'd) | DMR-only (16025655021) |
| PP x PkgC | Active | N/A (ZBB'd) | DMR-only (16025659319) |
| **PCT x C6** | Active | **Active** | Covered by [PCT](pct.md): 22022422104, 22021970028 |
| **PCT x RAPL** | Active | **Active** | Covered by [RAPL](rapl.md): 22022462184 |
| **PCT x HWP** | Active | **Active** | Covered by [HWP Cross-Product](hwp_cross_product.md) |
| **PCT x SST-PP** | Active | **Active** (basic) | Covered by [PCT](pct.md): 22022422110 |
| **PCT x PkgC** | Active | **Gap** | No dedicated test case |


### Execution Flow

#### SST-CP x PBF x C6 Flow (DMR reference)
```
1. BIOS Boot
   +-- Enable SST-CP: program SST_CP_CONTROL.SST_CP_PRIORITY_TYPE
   +-- Enable SST-BF: set BF cores with guaranteed base frequency
   +-- Assign HP cores -> CLOS[0/1], LP cores -> CLOS[2/3]

2. OS Runtime
   +-- Schedule high-priority workload on HP cores (BF-boosted)
   +-- Schedule harasser workload on LP cores
   +-- Park HP cores -> enter C6

3. C6 Entry
   +-- PCode detects HP core C6 -> power headroom freed
   +-- LP cores remain at CLOS[2/3] max frequency (not boosted)
   +-- Validate: no unexpected LP frequency change

4. C6 Exit
   +-- HP cores wake -> PBF base frequency guarantee restores
   +-- Validate: CLOS assignments and BF config intact
```

#### PP x PkgC Flow (DMR reference)
```
1. BIOS Boot
   +-- Program SST-PP active level (TDP config)
   +-- Set PkgC policy (enabled)

2. Runtime
   +-- All cores idle -> PkgC entry
   +-- PkgC state reached (C6/C2)
   +-- External event -> PkgC exit

3. Post-PkgC Validation
   +-- Read SST-PP TPMI registers -> verify active level matches pre-PkgC
   +-- Read TDP, P1, TRL -> verify restored correctly
   +-- Compare RAPL PL1/PL2 -> verify match PP-level TDP
```


### Key Registers & Interfaces

#### SST-CP x PBF Registers

| Register | Description | Source |
|----------|-------------|--------|
| `SST_CP_CONTROL` | `.SST_CP_PRIORITY_TYPE` -- Proportional(0) or Ordered(1) throttling | Confirmed: [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| `SST_CLOS_CONFIG[0..3]` | Per-CLOS MIN/MAX frequency bounds | Confirmed: [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| `SST_CLOS_ASSOC[0..N]` | Per-core CLOS assignment | Confirmed: [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| `SST_PP_CONTROL` | `.feature_state[0]` -- SST-BF enable | Confirmed: [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

#### PP x PkgC Registers

| Register | Description | Source |
|----------|-------------|--------|
| `SST_PP_CONTROL` | `.current_config_index` -- active PP level | Confirmed: [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| `SST_PP_STATUS` | `.config_lock`, `.active_level` | Confirmed: [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| `OPC_PKGC_ENTRY_CONTROL` | `.PREVENT_PKGC[0]` -- TPMI PkgC gate | Confirmed: [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) |
| `PACKAGE_RAPL_LIMIT` (CSR) | PL1/PL2 -- must match active PP-level TDP after PkgC exit | Confirmed: [Socket RAPL KB](../power_rapl/socket_rapl.md) |


### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [Intel SST HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST-CP, SST-BF, SST-PP, SST-TF framework + cross-product matrix |
| HAS | [PCT HAS (Arch Common)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) | PCT x C6 interaction (no C6 requirement for HP cores) |
| HAS | [DMR PkgC HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Idle_Flow/DMR_PkgC.html) | PkgC entry/exit, IO_DEMAND x PkgC |
| HAS | [TPMI HAS (Arch Common)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) | OPC_PKGC_ENTRY_CONTROL, TPMI register persistence |
| FHAS | [DMR RAPL FHAS](https://docs.intel.com/documents/primecode/fhas/DMR/RAPL/SERVERPMFW-1024.html) | Lists SST as RAPL cross-product |
| Parent | [SST-CP](sst_cp.md) | CLOS priority, ordered throttling (ZBB'd standalone on NWP) |
| Parent | [PP](pp.md) | SST-PP TDP config switching (ZBB'd on NWP) |
| Parent | [PCT](pct.md) | PCT x C6 test cases (22022422104, 22021970028) |
| Parent | [RAPL](rapl.md) | SST x RAPL cross-product |
| Parent | [HWP Cross-Product](hwp_cross_product.md) | SST x HWP cross-product |
| Comparison | [DMR vs NWP PM Comparison](../../dmr_vs_nwp_pm_comparison.html) | Feature-level support/ZBB matrix |

> Both original test cases have been **removed from NWP scope** because the underlying SST features (SST-CP, SST-BF, SST-PP) are ZBB'd on NWP.

| ~~16025655021~~ | ~~SST-CP-PBF-HP-C6 Harasser~~ | PV | ~~Runnable_On_N-1~~ | **Removed** -- SST-CP/BF ZBB'd |
| ~~16025659319~~ | ~~PP x PkgC Cross Product~~ | PV | ~~Runnable_On_N-1~~ | **Removed** -- SST-PP ZBB'd |

#### NWP-Applicable Cross-Product Coverage (via sibling subflows)

All positive-path SST cross-product coverage for NWP comes from sibling subflows:

| NWP Cross-Product | Subflow | Test Case(s) |
|-------------------|---------|-------------|
| PCT x C6 (all HP cores idle) | [PCT](pct.md) | 22022422104, 22021970028 |
| PCT x RAPL (HWP interrupt) | [RAPL](rapl.md) | 22022462184 |
| PCT x HWP (capabilities, OOB) | [HWP Cross-Product](hwp_cross_product.md) | 22022452981, 22022455929, 22022462193 |
| PCT x SST-PP (basic checks) | [PCT](pct.md) | 22022422110 |


### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->


### Source Notes

| Claim Category | Confidence | Source |
|---------------|------------|--------|
| SST cross-product framework exists | **Confirmed** | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) -- explicit Cross Products section |
| FlexRatio compatibility matrix (PP/BF/TF/CP) | **Confirmed** | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) -- explicit table |
| RAPL budget balancer accounts for SST-PP core count | **Confirmed** | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) -- explicit statement |
| SST listed as RAPL cross-product | **Confirmed** | [DMR RAPL FHAS](https://docs.intel.com/documents/primecode/fhas/DMR/RAPL/SERVERPMFW-1024.html) |
| SST-CP ordered throttling mechanism | **Confirmed** | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| SST-BF (PBF) base frequency boost | **Confirmed** | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| SST-PP config registers (PP_CONTROL, PP_STATUS) | **Confirmed** | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| OPC_PKGC_ENTRY_CONTROL register | **Confirmed** | [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) |
| SST-CP/BF/PP ZBB'd on NWP | **Confirmed** | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html), [HSD 22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) |
| PCT x C6 covered by sibling tests | **Confirmed** | [PCT KB](pct.md) -- tests 22022422104, 22021970028 |
| Power redistribution on HP C6 entry | **Inferred** | Architecturally expected from CLOS semantics; not directly confirmed from HAS passage |
| PP state persistence across PkgC | **Inferred** | Standard TPMI register behavior; not directly confirmed from HAS passage |
| PCT x PkgC gap | **Assessment** | No test case found in current SST test suite |
| C6 power redistribution details | **Inferred** | Plausible but not directly confirmed from current retrieved material |
| PkgC restore/persistence semantics | **Inferred** | Reasonable test objective but not confirmed from specific HAS passage |
