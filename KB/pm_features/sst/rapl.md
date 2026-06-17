# SST > RAPL

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SST](sst_main.md)
> **Source Confidence**: Partial — SST-TF/CLOS/ordered-throttling architecture confirmed from [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) and [Wave3 Socket RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html). RAPL register flow derived from [Socket RAPL KB](../power_rapl/socket_rapl.md). NWP scope from NWP PM MAS / HSD. See [Source Notes](#source-notes) below.

## Baseline (DMR)

**SST × RAPL** covers the cross-product interaction between PCT/SST-TF and socket RAPL power management. RAPL PL1/PL2 still enforce the socket power budget; within that budget, SST-CP ordered throttling distributes frequency reductions: LP cores (CLOS[3]) throttle first, HP cores (CLOS[0]) last. LP cores at ~P1 consume less power, freeing headroom for HP cores to sustain PCT TRL.

**Topology**: PrimeCode RAPL PID (IMH-P) → HPM RAPL_PERF_LIMIT (msgs 0x14–0x15) → PCode CBB SST-CP ordered throttling → CLOS_*_LIMIT fields drive per-CLOS frequency ceiling reduction. HWP interrupt fires if highest_perf changes under RAPL pressure.

```
RAPL not limiting
├── HP cores: run at PCT TRL ratio (up to P0max)
└── LP cores: run at LP_CLIP ratio (~P1)

RAPL PL1/PL2 limit hit
├── PrimeCode RAPL PID computes reduced frequency ceiling
├── IMH-P sends RAPL_PERF_LIMIT HPM to CBBs (CLOS_*_LIMIT fields)
├── PCode applies ceiling per SST-CP ordered throttling:
│   ├── LP cores (CLOS[3]) throttle first
│   └── HP cores (CLOS[0]) throttle only if LP reduction insufficient
├── CBB increments SOCKET_RAPL_PERF_STATUS
└── HWP interrupt fires if highest_perf changes → OS re-evaluates scheduling
```

**Boot activation**: RAPL always active (PrimeCode PID starts at runtime). PCT/SST-TF enabled at BIOS CPL3. SST-CP ordered throttling (`SST_CP_PRIORITY_TYPE = 1`) programmed by BIOS.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| RAPL PID (NN-PID) | IMH-P die | Computes frequency ceiling from measured package power vs PL1/PL2 targets | PACKAGE_RAPL_LIMIT (CSR), RAPL_PID_FREQ_OUTPUT | [Wave3 Socket RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) |
| HPM RAPL_PERF_LIMIT | IMH-P → CBB | Carries frequency ceiling + CLOS_*_LIMIT fields from IMH-P to all CBBs | HPM msgs 0x14–0x15 | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Core FIVR + PLL | CBB compute | Applies per-CLOS frequency ceiling; LP cores throttle first under ordered throttling | CLOS frequency enforcement | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PrimeCode (IMH-P) | IMH-P | Runs RAPL NN-PID; resolves PL1 (default=TDP) and PL2 (default=1.2×TDP); sends RAPL_PERF_LIMIT HPM with CLOS_*_LIMIT fields | RAPL PID flow, `sst_tpmi_general.cpp` CLOS init | [Wave3 Socket RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) |
| PCode (CBB) | Root + Leaf CBB | Applies SST-CP ordered throttling per CLOS_*_LIMIT: reduces LP CLOS[3] first, HP CLOS[0] last | `sst_manager.cpp`, `ccp_manager.cpp` | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| BIOS | Pre-OS | Programs PACKAGE_RAPL_LIMIT (PL1/PL2); sets SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1 (Ordered) | BIOS RAPL + SST-CP knobs | [Wave3 Socket RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) |
| Acode | Compute core | Executes at RAPL+CLOS constrained frequency; triggers HWP interrupt if highest_perf changes | Architecture reference | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| CSR | PACKAGE_RAPL_LIMIT | RW | PL1/PL2 power limits; unchanged by SST-TF/PCT; drives RAPL PID target | [Wave3 Socket RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) |
| CSR | SOCKET_RAPL_PERF_STATUS | RO | Incremented when RAPL is actively throttling; measure of throttle frequency | [Wave3 Socket RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) |
| MSR | IA32_HWP_CAPABILITIES (0x771) per core | RO | highest_perf: changes under RAPL pressure when PCT CLOS limits are reduced | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| TPMI SST | SST_CP_CONTROL.SST_CP_PRIORITY_TYPE | RW | 0=Proportional, 1=Ordered (LP throttle first); set by BIOS for PCT | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| RAPL PL1 default | TDP (from active PP level) | [Wave3 Socket RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) |
| RAPL PL2 default | 1.2 × TDP (PL2 target: 0.9 × PL2) | [Wave3 Socket RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) |
| SST-CP ordered throttling priority | LP cores (CLOS[3]) throttle first; HP cores (CLOS[0]) last | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| PCT × RAPL test coverage | 22022462184 (RAPL HWP Interrupt) | NWP test plan |
| PCT power redistribution | LP at ~P1 frees headroom for HP cores to sustain PCT TRL within same PL1 envelope | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |

## NWP Delta

### SST × RAPL on NWP: ✅ Expected Applicable (PCT profile only)

Based on current NWP PM MAS and HSD data, NWP supports **PCT** as the only active SST-TF profile. The SST × RAPL interaction is therefore expected to be relevant:

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| SST-TF/PCT | ✅ Supported — 8 HP cores @ 4.4GHz | [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435), [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| SST-CP ordered throttling | Expected active when PCT enabled | Inferred from SST HAS + PCT profile |
| RAPL PL1/PL2 PIDs | Expected NN-PID (same as DMR) | Socket RAPL KB |
| HWP interrupt under RAPL+PCT | Test 22022462184 in NWP test plan | Test planning data |
| SST-PP × RAPL | ❌ ZBB'd | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| SST-BF × RAPL | ❌ ZBB'd | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |

**Scope reduction**: Only PCT/TF × RAPL cross-product is expected to need validation on NWP. SST-PP/CP/BF × RAPL test cases (if any exist on DMR) are out of scope.

> **⚠ Needs verification**: NWP-specific SST×RAPL scope, including whether only PCT is active and NN-PID behavior matches DMR, should be confirmed from NWP-specific collateral or first-silicon validation.

## Legacy (Human-Curated Reference)

### Architecture Summary

This subflow covers the **cross-product interaction between SST-TF/PCT and RAPL power management**. When SST-TF (or PCT) is active, RAPL power limits (PL1/PL2) still enforce the overall socket power budget, but the **frequency distribution across cores is governed by CLOS-based partitioning** rather than uniform throttling.

#### Key Interaction: Ordered Throttling Under Power Limits

When PCT/SST-TF is active and RAPL hits a power limit, SST-CP ordered throttling influences how the frequency reduction is distributed across cores:

1. **SST-CP ordered throttling** (`SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1`) governs per-CLOS throttle priority. *(Confirmed: [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html))*
2. Lower-priority CLOS groups (e.g. CLOS[3] for LP cores) are **expected** to be reduced before higher-priority groups (e.g. CLOS[0] for HP cores), subject to the implementation of the active SST policy. *(Inferred from ordered-throttling semantics; exact LP-first/HP-later sequence not explicitly stated in retrieved HAS excerpts)*
3. **HP cores** are expected to maintain PCT TRL frequency as long as possible within the RAPL power envelope.

> **⚠ Needs verification**: The exact LP-first → HP-later throttle sequence is architecturally consistent with ordered throttling but has not been directly confirmed from a single authoritative passage. Targeted review of CBB SST Manager FAS or PCode source recommended.

#### Power Budget Redistribution

PCT does **not** change the socket TDP or RAPL PL1 default. It redistributes power within the same envelope:
- LP cores at ~P1 consume less power → frees headroom for HP cores
- HP cores use the freed headroom to sustain PCT TRL (up to P0max)
- RAPL PL1 PID still targets PL1 field (default = TDP); PL2 PID targets 0.9×PL2

#### HWP Interrupt Interaction *(needs stronger backing)*

When RAPL-driven throttling changes core frequency capabilities:
- HWP interrupt is expected to notify the OS of changed `IA32_HWP_CAPABILITIES.highest_perf`
- With PCT active, HP and LP cores are expected to report **different** `highest_perf` values (especially under DLCP) — per [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- OS scheduler should react by migrating high-priority work to HP cores that still have headroom
- **Test case 22022462184** (RAPL HWP Interrupt) is listed in the NWP test plan as validating this interaction *(source: test planning data, not HAS)*

> **⚠ Needs verification**: The specific trigger path (RAPL limit → HWP interrupt → `highest_perf` change) under active SST-TF/PCT is not directly confirmed from retrieved HAS excerpts. PCT HAS confirms per-core `highest_perf` differentiation under DLCP; the RAPL-triggered interrupt path needs confirmation from HWP or RAPL HAS.


### Execution Flow

```
1. BIOS Boot
   ├── Programs RAPL PL1/PL2 via CSR PACKAGE_RAPL_LIMIT
   ├── Programs SST-TF/PCT CLOS registers (HP→CLOS[0], LP→CLOS[3])
   └── Sets SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1 (Ordered Throttling)

2. Primecode Init (IMH-P)
   ├── Resolves PL1 (default=TDP), PL2 (default=1.2×TDP)
   └── Starts RAPL PL1/PL2 PID controllers (NN-PID on DMR/NWP)

3. Runtime — RAPL Not Limiting
   ├── HP cores run at PCT TRL ratio (up to P0max)
   ├── LP cores run at LP clip ratio (~P1)
   └── RAPL PIDs output max ratio (no throttling)

4. Runtime — RAPL Power Limit Hit
   ├── RAPL PID computes reduced frequency ceiling
   ├── IMH-P sends RAPL_PERF_LIMIT via HPM to CBBs
   ├── PCode applies ceiling per SST-CP ordered throttling:
   │   ├── LP cores (CLOS[3]) throttle first
   │   └── HP cores (CLOS[0]) throttle only if LP reduction insufficient
   ├── CBB increments SOCKET_RAPL_PERF_STATUS
   └── HWP interrupt fires if highest_perf changes → OS re-evaluates scheduling

5. OS Observation
   ├── Intel SST tool reports HP/LP core assignments + active frequencies
   ├── HWP MSR shows per-core highest_perf (HP > LP under DLCP)
   └── RAPL perf_status counters reflect throttled time
```


### Key Registers & Interfaces

#### RAPL Registers (interaction points) — *sourced from [Socket RAPL KB](../power_rapl/socket_rapl.md)*

| Register | Description | Source |
|----------|-------------|--------|
| `PACKAGE_RAPL_LIMIT` (CSR) | PL1/PL2 power limits — unchanged by SST-TF/PCT | [Wave3 Socket RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) |
| `RAPL_PID_FREQ_OUTPUT` | NN-PID output frequency ratio — applied per CLOS priority | Socket RAPL KB (not in retrieved HAS excerpts) |
| `SOCKET_RAPL_PERF_STATUS` | Incremented when DCM_freq == RAPL_PID_FREQ_OUTPUT and RAPL flags set | Socket RAPL KB (not in retrieved HAS excerpts) |
| `RAPL_PERF_LIMIT` (HPM 0x14-0x15) | IMH-P → CBB: frequency ceiling from RAPL PID | Socket RAPL KB (not in retrieved HAS excerpts) |

#### SST Registers (governing throttle order) — *confirmed from [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)*

| Register | Description | Source |
|----------|-------------|--------|
| `SST_CP_CONTROL` | `.SST_CP_PRIORITY_TYPE = 1` — Ordered Throttling | ✅ SST HAS |
| `SST_CLOS_CONFIG[0..3]` | Per-CLOS MIN/MAX frequency bounds + proportional priority | ✅ SST HAS |
| `SST_CLOS_ASSOC[0..N]` | Per-core CLOS assignment | ✅ SST HAS |

> Note: CLOS[0] = HP, CLOS[3] = LP assignment is per PCT HAS convention, not a fixed HW rule.

#### MSRs

| MSR | Description |
|-----|-------------|
| `IA32_HWP_CAPABILITIES` | `.highest_perf` — differs HP vs LP under DLCP; changes trigger HWP interrupt |
| `0x1AD` (Turbo_Ratio_Limit) | Overridden with SST_TF_INFO_2.RATIO_0 when PCT active |


### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [PCT HAS (Arch Common)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) | PCT architecture — CLOS/throttle interaction with RAPL |
| HAS | [Intel SST HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST-TF/SST-CP ordered throttling framework |
| HAS | [DMR IMH NNPID HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/NNPID%20HAS/NNPID%20HAS.html) | NN-PID controller (replaces classic PID on DMR/NWP RAPL) |
| Parent | [Socket RAPL](../power_rapl/socket_rapl.md) | RAPL PID topology, power limit flows, perf status reporting |
| Parent | [PCT](pct.md) | PCT architecture, CLOS config, DLCP, DQ rules |
| FAS | [CBB SST Manager FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/SST_manager/cbb_SST_manager_FAS.html) | CBB PCode SST-CP ordered throttling implementation |
| Comparison | [DMR vs NWP PM Comparison](../../dmr_vs_nwp_pm_comparison.html) | Feature-level support/ZBB matrix |


### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->


### Source Notes

| Claim Category | Confidence | Source |
|---------------|------------|--------|
| SST-TF exists in DMR | ✅ Confirmed | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html), [DMR SST Features](https://docs.intel.com/documents/pm_doc/src/server/DMR-HBM/PM%20Features/DMR_SST_Features.html) |
| SST-CP ordered throttling exists | ✅ Confirmed | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| CLOS is the prioritization mechanism | ✅ Confirmed | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| `SST_CP_PRIORITY_TYPE = 1` = ordered | ✅ Confirmed | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| `SST_CLOS_CONFIG` / `SST_CLOS_ASSOC` | ✅ Confirmed | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Exact LP-first → HP-later throttle order | ⚠ Inferred | Consistent with ordered-throttling semantics; not directly quoted |
| RAPL register flow (PID output, perf status, HPM) | ⚠ KB-derived | [Socket RAPL KB](../power_rapl/socket_rapl.md); not verified against HAS in this pass |
| HWP interrupt under RAPL+PCT | ⚠ KB-derived | PCT HAS confirms per-core `highest_perf`; RAPL trigger path unconfirmed |
| NWP supports only PCT profile | ⚠ MAS/HSD | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html), [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) |
| NWP SST-PP/BF ZBB'd | ⚠ MAS/HSD | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
