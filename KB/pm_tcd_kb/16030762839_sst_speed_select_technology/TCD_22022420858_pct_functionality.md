# TCD: PCT - Functionality

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420858](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **Title** | PCT - Functionality |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TP** | [16030762839](https://hsdes.intel.com/appstore/article-one/#/16030762839) |
| **KB last updated** | 2026-06-22 |
| **Scope distinct from** | TCD 22022420855 (PCT - Enabling & Discovery) |

## Feature Overview

See KB/pm_features/sst/pct.md for architecture baseline.

## Architecture / Micro-architecture and Functionality

### Why PCT Exists

Intel Xeon CPU+GPU/accelerator systems dedicate specific cores to GPU service. These GPU-serving
cores need maximum turbo (P0max) while remaining cores stay active at reduced frequency — without
requiring the traditional P0half C6 sleep trick. PCT uses SST-TF's CLOS infrastructure to enforce
HP/LP core frequency partitioning at runtime, with PCode running the standard SST-TF flow unchanged.

### Block Decomposition

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │  Boot Time (BIOS CPL3)                                                  │
 │  ┌──────────────┐  programs    ┌─────────────────────────────────────┐  │
 │  │  BIOS        ├─────────────►│  TPMI SRAM (NIO die)               │  │
 │  │  PCT knobs   │  per CBB     │  SST_CLOS_CONFIG[0].max = HP TRL    │  │
 │  │  Partition   │  dielet      │  SST_CLOS_CONFIG[3].max = LP clip   │  │
 │  │  Count, Core │  (cbb0,cbb1) │  SST_CLOS_ASSOC[core]: HP→CLOS[0]  │  │
 │  │  Selection   │              │  SST_CP_CONTROL.PRIORITY_TYPE = 1   │  │
 │  └──────────────┘              │  SST_PP_CONTROL.feature_state[1]=1  │  │
 │                                └────────────┬────────────────────────┘  │
 └────────────────────────────────────────────┼────────────────────────────┘
                                               │ PCode reads at runtime
 ┌─────────────────────────────────────────────▼────────────────────────────┐
 │  Runtime: PCode SST-TF FSM (per CBB Root Punit)                         │
 │                                                                          │
 │  1. Read SST_CLOS_ASSOC[core] → assign each core to HP or LP group      │
 │  2. Compute WP4_HP = SST_TF_INFO_2.RATIO_0  (HP turbo ceiling)          │
 │     Compute WP4_LP = SST_TF_INFO_0.LP_CLIP_RATIO_0  (LP clip ceiling)   │
 │  3. Broadcast WP4 per CLOS group to all cores via PMSB sideband         │
 │  4. Under RAPL PL1 + SST_CP_PRIORITY_TYPE=1 (Ordered Throttling):       │
 │       Step A: Reduce LP cores toward WP4_LP minimum                     │
 │       Step B: Maintain HP cores at WP4_HP while LP still above min      │
 │       Step C: Only when LP at min → reduce HP                           │
 │                                                                          │
 │  sst_manager.cpp::update_cfgs()  /  trl_manager.cpp::load_hp_clos_trl() │
 └───────────────────────┬──────────────────────────────────────────────────┘
                         │ WP4 (Workpoint 4) per core
 ┌───────────────────────▼──────────────────────────────────────────────────┐
 │  ACP / Core PMA (per CBB compute die)                                   │
 │  Receives WP4 from PCode; computes final operating frequency per core:  │
 │    Core_freq = min(WP4, WP1, Electrical_limits, ICCP_license)           │
 │  HP core: WP4 ceiling = HP TRL → operates at ~4.4 GHz (NWP)            │
 │  LP core: WP4 ceiling = LP_CLIP → operates at ~P1 ≈ 2.3 GHz (typical)  │
 └───────────────────────┬──────────────────────────────────────────────────┘
                         │ Frequency target
 ┌───────────────────────▼──────────────────────────────────────────────────┐
 │  Core FIVR + PLL (per CBB compute, 2 cores per DCM share FIVR)          │
 │  Enforces the frequency set by ACP. Voltage managed by FIVR per CLOS.   │
 │  HP cores get P0max voltage headroom; LP cores at lower V/F point.      │
 └──────────────────────────────────────────────────────────────────────────┘
```

### Key Blocks and Roles

| Block | Die | Role in PCT Functionality |
|-------|-----|--------------------------|
| TPMI SRAM (SST) | NIO (IMH-P) | Stores CLOS config and CLOS assoc per CBB dielet; PCode reads at runtime; writable by BIOS and Intel SST tool |
| PCode Root Punit | CBB | SST-TF FSM: computes per-CLOS WP4 limits; runs ordered throttling under RAPL; no PCT-specific logic — identical to SST-TF |
| ACP / Core PMA | CBB compute | Receives WP4 from PCode; applies ICCP license and electrical limits; final frequency resolver per core |
| Core FIVR + PLL | CBB compute | Physical V/F enforcement; 2 cores per DCM share one FIVR |
| BIOS | Platform | Programs CLOS registers at CPL3; manages PCT knobs; reprogram on every boot |
| Intel SST tool | OS | Runtime TPMI writes to SST_PP_CONTROL.feature_state[1]; toggle HP/LP without reboot |
| RAPL PID | CBB Root Punit | 1ms loop; distributes throttling per SST_CP_PRIORITY_TYPE; LP first under ordered throttling |
| HWP reporting | CBB | IA32_HWP_CAPABILITIES.highest_perf per core: HP = P0max, LP = LP_CLIP; used by OS for core discovery |

### Frequency Hierarchy (from PCT HAS Table 3-2, NWP values)

| Level | Description | NWP Value | Who operates here |
|-------|-------------|-----------|-------------------|
| P0max / F3 | PCT HP frequency | ~4.4 GHz (POR-1) | HP cores (8 on NWP) |
| P0half | Half-core turbo (requires C6) | — | Not used with PCT active |
| P0n | All-core turbo | ~3.6 GHz (typical) | Conventional turbo (no PCT) |
| F2 / LP_CLIP | LP clip ceiling (≥P1, fused) | ~P1 ≈ 2.3 GHz | LP cores (88 on NWP) |
| P1 | Guaranteed all-core | — | Minimum LP bound |
| Pn | Minimum | — | Floor |

### FSM: Ordered Throttling Under RAPL

```
RAPL PID detects power > PL1:
  ├─ Compute total throttle needed (deficit)
  ├─ Phase A — LP throttle first:
  │     Reduce LP cores: freq → WP4_LP_MIN (LP_CLIP minimum)
  │     While LP > LP_MIN: deficit absorbed from LP budget
  ├─ Phase B — HP protected:
  │     HP cores maintain WP4_HP (PCT TRL) while LP still above min
  └─ Phase C — HP throttle (only if LP at minimum and deficit remains):
        Reduce HP frequency below WP4_HP
  
SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1 enables Phase A/B/C ordering
SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 0 = proportional (both LP and HP throttle equally)
```

### External Dependencies

| Dependency | Impact if missing |
|-----------|-------------------|
| SST_TF fuses (LP_CLIP, HP TRL ratios) | PCode has no frequency targets; TPMI INFO registers = 0 |
| BIOS PCT Partition Count knob | PCT remains disabled (Partition Count = 0 default on DMR/NWP) |
| SST_PP_CONTROL.feature_state[1] = 1 | CLOS enforcement inactive; all cores at conventional turbo |
| RAPL PL1 active | Ordered throttling not exercised; functionality limited to structural verification |
| SST_CP_PRIORITY_TYPE = 1 | Ordered throttling does not work; LP and HP throttle proportionally |
| MADT correct ordering | HP partition selection assigns wrong cores |

### NWP Topology (for loop bounds in test scripts)

- **CBBs**: 2 (`cbb0`, `cbb1`) → loop `range(2)`
- **Cores per CBB**: 48 (24 DCMs × 2 PNC cores) → loop `range(48)`
- **Total cores**: 96 — HP: 8 (CLOS[0]), LP: 88 (CLOS[3])
- **PCT frequency target**: ~4.4 GHz (not ~4.6 GHz as on GNR) — turbo freq check must use NWP value
- **RAPL PL1 register**: TPMI `SOCKET_RAPL_PL1_CONTROL` (MSR 0x610/0x638 deprecated on DMR/NWP)
- **SST-BF**: ZBB'd on NWP — DQ mutex tests show no interference, not active conflict

### Functional Scenarios (derived from linked TC titles)

| TC Group | Scenario | Architectural mechanism exercised |
|----------|----------|----------------------------------|
| Turbo frequency check (×2) | HP cores achieve ~4.4 GHz; LP clipped at ~P1 | PCode WP4 broadcast; ACP resolves HP/LP separately; verify via IA32_PERF_STATUS |
| Default HP core selection (×2) | 8 HP cores in correct partition positions | MADT-based partition algorithm; CLOS_ASSOC assignment; HWP_CAPABILITY.highest_perf per core |
| TDP convergence | LP throttles first under RAPL PL1 | Ordered Throttling FSM (PRIORITY_TYPE=1); RAPL PID interaction |
| All HP cores in C6 (×2) | LP cannot exceed CLOS[3].max even when HP idle | CLOS max ceiling enforced regardless of HP idle state |
| Default Disabled | PCT off = conventional P0n/P0half | SST_PP_CONTROL.feature_state[1]=0; no CLOS differentiation; MSR 0x1AD not overridden |
| Default Enabled | Auto-activation when Partition Count > 0 | BIOS programs CLOS at CPL3; feature_state[1]=1; HP/LP split visible in TPMI |
| BIOS Menu | Knob visibility and range validation | PCT HP Partition Count (1–16); PCT Core Selection (0–255); hidden when SST-TF not fused |
| BIOS Negative Validation | Graceful rejection of invalid config | Partition Count > max (SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS) → BIOS skips PCT |
| DQ Rules (FlexconPM) | SST-BF + PCT mutex enforced | On NWP SST-BF ZBB'd; verify SST_PP_CONTROL.feature_state[0]=0 and [1]=1 coexist |
| TPMI register check | TPMI values match spec post-activation | CLOS_CONFIG[0/3], CLOS_ASSOC, SST_CP_CONTROL, SST_TF_INFO_0/2 match expected values |
| TPMI runtime enable/disable (×2) | SST tool toggle without reboot | TPMI write to SST_PP_CONTROL.feature_state[1]; HWP_CAPABILITY.highest_perf changes per core |
| TPMI runtime negative (×1) | Invalid runtime config rejected | Out-of-range CLOS_ASSOC, illegal feature_state combo rejected gracefully |

### Micro-architecture relevant to Functionality testing

```
Frequency hierarchy (PCT HAS Table 3-2):
  P0max / F3 (HP target) : ~4.4 GHz (NWP, POR-1)   ← HP cores operate here
  P0half                 : ~3.9 GHz (half cores in C6)
  P0n  (all-core turbo)  : ~3.6 GHz
  F2 / LP_CLIP           : ~P1 ≈ 2.3 GHz            ← LP cores clipped here
  P1   (guaranteed)      : base all-core frequency
  Pn   (minimum)         : lowest operating frequency

Key CLOS registers per CBB dielet (NWP: cbb0 + cbb1):
  SST_CLOS_CONFIG[0].max = SST_TF_INFO_2.RATIO_0     ← HP frequency ceiling
  SST_CLOS_CONFIG[3].max = SST_TF_INFO_0.LP_CLIP_RATIO_0  ← LP frequency ceiling
  SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1 (Ordered Throttling)
  SST_CLOS_ASSOC[core]: HP → CLOS[0], LP → CLOS[3]

Ordered Throttling (TDP convergence):
  When RAPL PL1 enforced + PCT active (PRIORITY_TYPE=1):
    1. LP cores drop frequency first → toward LP_CLIP minimum
    2. HP cores maintained at PCT TRL while LP still above minimum
    3. Only after LP at minimum → HP begins to reduce
  Register: SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1
```

### Functional Scenarios (derived from TC titles)

| TC Group | Scenario | What is verified |
|----------|----------|-----------------|
| Turbo frequency check (×2) | HP cores achieve F3 with all cores active | IA32_PERF_STATUS (0x198) on HP cores shows ~4.4 GHz; LP cores show LP clip |
| Default HP core selection (×2) | CLOS assignment matches partition algorithm | SST_CLOS_ASSOC: 8 HP cores in CLOS[0]; 88 LP cores in CLOS[3]; first 2 per partition |
| TDP convergence | Ordered throttling under RAPL PL1 | LP frequency drops first; HP maintained longer; SST_CP_PRIORITY_TYPE=1 |
| All HP cores in C6 (×2) | LP frequency when HP budget freed | LP cores may not exceed CLOS[3].max even when HP cores idle |
| Default Disabled | PCT off = conventional turbo | SST_PP_CONTROL.feature_state[1]=0; MSR 0x1AD not overridden; no CLOS differentiation |
| Default Enabled | PCT active when Partition Count > 0 | SST_PP_CONTROL.feature_state[1]=1; 8 HP cores at boot |
| BIOS Menu | BIOS knob visibility and range | PCT HP Partition Count (1–16), PCT Core Selection (0–255); hidden when not capable |
| BIOS Negative Validation | Invalid PCT config gracefully rejected | Partition Count > SST_TF_INFO_8.NUM_CORE_0/MAX_LPIDS → BIOS skips PCT |
| DQ Rules (FlexconPM) | SST-BF + PCT mutex | On NWP SST-BF ZBB'd; verify no interference; DQ rule not violated |
| TPMI register check | SST TPMI values match spec after activation | SST_CLOS_CONFIG[0/3], SST_CLOS_ASSOC, SST_CP_CONTROL all match programmed values |
| TPMI runtime enable/disable (×2) | SST tool toggle without reboot | SST_PP_CONTROL.feature_state[1] toggled; HWP_CAPABILITY.highest_perf updates per core |
| TPMI runtime negative | Invalid runtime config rejected | Illegal CLOS_ASSOC writes, out-of-range partition count rejected gracefully |

### NWP-specific considerations
- **No SST-BF conflict**: SST-BF is ZBB'd on NWP, so mutex tests verify no residual interference
- **RAPL PL1 via TPMI**: `SOCKET_RAPL_PL1_CONTROL` (not MSR 0x610/0x638, deprecated on DMR/NWP)
- **2 CBBs only**: Loop bounds: `for cbb_idx in range(2)` / `for core_idx in range(48)`
- **NWP PCT frequency target**: ~4.4 GHz (POR-1); turbo frequency check must use this as reference

## Interfaces and Protocols - Key Functional Registers

> These are the registers and interfaces verified for correct functional behavior.

| Interface | Register | Functional Purpose |
|-----------|----------|--------------------|
| TPMI | SST_CLOS_CONFIG[0].max | HP frequency ceiling = SST_TF_INFO_2.RATIO_0 |
| TPMI | SST_CLOS_CONFIG[3].max | LP clip ceiling = SST_TF_INFO_0.LP_CLIP_RATIO_0 |
| TPMI | SST_CP_CONTROL.SST_CP_PRIORITY_TYPE | Must = 1 (Ordered Throttling) for correct TDP behavior |
| TPMI | SST_CLOS_ASSOC_* | HP = CLOS[0], LP = CLOS[3] |
| TPMI | SST_PP_CONTROL.feature_state[1] | 1 = PCT/SST-TF active; 0 = disabled |
| MSR | IA32_HWP_CAPABILITIES (0x771) | HP cores: highest_perf = P0max; LP cores: highest_perf = LP clip |
| MSR | IA32_PERF_STATUS (0x198) | Current operating ratio; HP should reach F3, LP should be clipped |
| MSR | 0x1AD PRIMARY_TURBO_RATIO_LIMIT | Must equal SST_TF_INFO_2.RATIO_0 (HP TRL) |
| TPMI | SST_TF_INFO_1.num_core_0 | Max HP modules supported by silicon |

## Programming Model - Preconditions for Functionality Tests

> Same enabling sequence as TCD 22022420855, but treated as precondition here.

| Step | Actor | Register | Value |
|------|-------|----------|-------|
| 1 | PrimeCode Phase 5 | SST_TF_INFO_0.LP_CLIP_RATIO_0 | LP ceiling fused |
| 2 | PrimeCode Phase 5 | SST_TF_INFO_2.RATIO_0 | HP TRL (~4.4 GHz on NWP) |
| 3 | BIOS CPL3 | SST_CLOS_CONFIG[0/3] | HP ceiling / LP ceiling programmed |
| 4 | BIOS CPL3 | SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1 | Ordered Throttling |
| 5 | BIOS CPL3 | SST_CLOS_ASSOC[core] | HP=CLOS[0], LP=CLOS[3] |
| 6 | BIOS CPL3 | SST_PP_CONTROL.feature_state[1] = 1 | PCT active |

## Operational Behavior - Functional Scenarios

### Normal Operating Mode (PCT Active)
- HP cores (8 on NWP) operate at SST_TF_INFO_2.RATIO_0 (~4.4 GHz)
- LP cores (88 on NWP) clipped at SST_TF_INFO_0.LP_CLIP_RATIO_0 (~P1)
- PCode enforces CLOS limits per workpoint calculation
- No C6 requirement: LP cores remain active at clipped frequency

### TDP Convergence Under PCT (Ordered Throttling)
When RAPL PL1 is active with PCT enabled (SST_CP_PRIORITY_TYPE = 1):
1. LP cores drop frequency first toward LP_CLIP minimum
2. HP cores maintain PCT frequency while LP cores still have headroom
3. Only after LP cores reach minimum, HP cores begin to reduce
4. Verify: RAPL-induced throttling hits LP cores first, HP cores last

### All HP Cores in C6 Scenario
When all HP cores enter C6:
- LP cores may access the power/frequency budget freed by idle HP cores
- Verify LP cores do not exceed their CLOS clip limit

### PCT Default Disabled (DMR/NWP)
- PCT Partition Count = 0 at boot → system operates in conventional turbo mode
- MSR 0x1AD reflects P0half/P0n (not PCT TRL)
- SST_PP_CONTROL.feature_state[1] = 0
- Verify: no HP/LP CLOS differentiation

### PCT Runtime Enable/Disable (TPMI)
- Intel SST tool can set SST_PP_CONTROL.feature_state[1] at runtime
- Disable: feature_state[1] = 0 → all cores revert to conventional turbo
- Enable: reprogram CLOS + set feature_state[1] = 1
- Verify: HWP_CAPABILITY.highest_perf changes per core after toggle

### BIOS Negative Validation
- PCT Partition Count > maximum allowed (> SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS) → BIOS must reject
- PCT Core Selection offset > partition size → BIOS defaults to 0 (first core)
- PCT enabled on SKU where SST-TF not fused → BIOS must skip PCT programming

### DQ Rule Enforcement
- SST-BF + PCT simultaneously enabled → platform must reject or prioritize one
- On NWP: SST-BF is ZBB'd, so this mutex is not exercised; verify PCT operates without SST-BF interference

## Test Cases Under This TCD

| HSD ID | Title | Status | Val Environment |
|--------|-------|--------|-----------------|
| [22022422104](https://hsdes.intel.com/appstore/article-one/#/22022422104) | PCT - All HP cores in C6 | open | virtual_platform |
| [22022422105](https://hsdes.intel.com/appstore/article-one/#/22022422105) | PCT - Default HP core selection | open | virtual_platform |
| [22022422110](https://hsdes.intel.com/appstore/article-one/#/22022422110) | PCT - SST-PP x PCT Basic Checks | rejected | virtual_platform |
| [22022422116](https://hsdes.intel.com/appstore/article-one/#/22022422116) | PCT - Turbo frequency check | open | virtual_platform |
| [22022422117](https://hsdes.intel.com/appstore/article-one/#/22022422117) | PCT - Verify TDP convergence | open | virtual_platform |
| [16030715676](https://hsdes.intel.com/appstore/article-one/#/16030715676) | [PSS]PCT - All HP cores in C6 | open | — |
| [16030715678](https://hsdes.intel.com/appstore/article-one/#/16030715678) | [PSS]PCT - BIOS Menu | open | — |
| [16030715680](https://hsdes.intel.com/appstore/article-one/#/16030715680) | [PSS]PCT - BIOS Negative Validation | open | — |
| [16030715682](https://hsdes.intel.com/appstore/article-one/#/16030715682) | [PSS]PCT - DQ Rules (FlexconPM) | open | — |
| [16030715684](https://hsdes.intel.com/appstore/article-one/#/16030715684) | [PSS]PCT - Default Disabled | open | — |
| [16030715686](https://hsdes.intel.com/appstore/article-one/#/16030715686) | [PSS]PCT - Default HP core selection | open | — |
| [16030715690](https://hsdes.intel.com/appstore/article-one/#/16030715690) | [PSS]PCT - TPMI register check (FlexconPM) | open | — |
| [16030715692](https://hsdes.intel.com/appstore/article-one/#/16030715692) | [PSS]PCT - Turbo frequency check | open | — |
| [16030715694](https://hsdes.intel.com/appstore/article-one/#/16030715694) | [PSS]PCT - enable/disable | open | — |
| [16030768619](https://hsdes.intel.com/appstore/article-one/#/16030768619) | PCT - Default Enabled | open | — |
| [16030768620](https://hsdes.intel.com/appstore/article-one/#/16030768620) | PCT - TPMI runtime enable/disable | open | — |
| [16030768621](https://hsdes.intel.com/appstore/article-one/#/16030768621) | PCT - TPMI runtime negative validation | open | — |

## References

- [PCT (Priority Core Turbo) HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — Ordered Throttling, HP/LP frequency behavior, default disabled on DMR
- [Priority Core Turbo Technology White Paper](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/IC_PCT.html) — GPU use case, C6 vs PCT freq behavior
- [Diamond Rapids Server (DMR) Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) — PCT default disabled, DQ rules
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST-TF CLOS enforcement, ordered throttling
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT scope
- [CCB HSD 14026595435](https://hsdes.intel.com/appstore/article-one/#/14026595435) — 8 HP cores, ~4.4 GHz target
- KB: KB/pm_features/sst/pct.md
