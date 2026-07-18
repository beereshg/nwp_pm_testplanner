# TPF 16030762939 — [NWP PM] PCT (Priority Core Turbo)

| Field | Value |
|-------|-------|
| **TPF ID** | [16030762939](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Title** | [NWP PM] PCT (Priority Core Turbo) |
| **Parent TP** | [16030762839 — [NWP PM] SST (Speed Select Technology)](https://hsdes.intel.com/appstore/article-one/#/16030762839) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Feature Classification & Introduction

**PCT (Priority Core Turbo)** is a **silicon-heavy feature with firmware orchestration**. Hardware enforces HP/LP TRL differentiation via CLOS logic in Acode; firmware/BIOS/PCode configure and expose the capability. On NWP, PCT targets **8 HP cores** (~4.4 GHz) across 4 partitions of 96 total cores (2 CBBs × 48), with the remaining ~88 LP cores clipped to ~P1 (~2.3 GHz).

**Feature gating:** On NWP, PCT is opt-in via BIOS Partition Count knob (CAPID4.bit29 is NOT used — all NWP parts are PCT-capable). On GNR, CAPID4.bit29=1 auto-enables PCT.

### Firmware Agent Responsibilities

| Agent | Role | Key Artifact |
|-------|------|-------------|
| PrimeCode (IMH-P) | Phase 5: reads SST_TF fuses; writes SST_TF_INFO_0/1/2/8/10 TPMI registers | `sst_tpmi_general.cpp::sstTfInfoInit()` |
| BIOS (CPL3) | Reads partition count knob; programs CLOS_CONFIG[0/3], CLOS_ASSOC, SST_CP_CONTROL, SST_PP_CONTROL; overrides MSR 0x1AD | CPUPM FAS, BIOS PCT knob path |
| PCode (CBB) | Enforces CLOS-based frequency limits per core; runs RAPL PID (1ms); applies ordered throttle under PL1 | `sst_manager.cpp`, `trl_manager.cpp` |
| Acode (core microcode) | Executes at PCode-assigned CLOS ratio; HP = P0max ceiling, LP = LP_CLIP ceiling | RTL / Acode — no SW interface |

### NWP Architecture Constants

| Parameter | Value | Source |
|-----------|-------|--------|
| Total cores | 96 (2 CBBs × 48 per CBB) | NWP topology |
| HP cores (default) | 8 (2 per partition × 4 partitions) | HSD 14026595435 |
| LP cores | ~88 (CLOS[3]) | NWP topology |
| HP TRL target | ~4.4 GHz (SST_TF_INFO_2.ratio_0) | HSD 14026595435 |
| LP clip | ~P1 ~2.3 GHz (SST_TF_INFO_0.lp_clip_ratio_0) | PCT HAS |
| Max partitions | SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS (typically 4) | PCT HAS |
| RAPL PID period | 1 ms | CBB SST Manager FAS |
| SST-BF | ZBB on NWP — mutually exclusive with PCT | NWP MAS |
| RAPL PL1 register | TPMI SOCKET_RAPL_PL1_CONTROL (MSR 0x610/0x638 deprecated on NWP) | BIOS HSD 14018460453 |

---

## Section 2: Design Details

### PCT Reset / Boot to OS Flow

```
PrimeCode Phase 5 (reset exit)
  ├── Reads SST_TF_CONFIG fuse arrays
  │     LP_CLIP_RATIO_CDYN_INDEX[0..5]   → SST_TF_INFO_0.LP_CLIP_RATIO_[0..5]
  │     TRL_NUMCORE[0..2]                → SST_TF_INFO_1.NUM_CORE_[0..2]
  │     TRL_RATIOS_CDYN_RATIO[0..2]      → SST_TF_INFO_2.RATIO_[0..5]
  │     PCT_Module_Mask (DLCP)           → SST_TF_INFO_10
  └── TPMI SST_TF_INFO_* registers now valid; HP TRL and LP clip immutable

BIOS CPL3 (after PrimeCode Phase 5)
  ├── Read PCT Partition Count knob
  │     EDKII → Socket Config → Advanced PM Config → PCT Configuration
  │     max_partitions = SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS  [= 4 on NWP]
  ├── Divide 96 cores (2 CBBs × 48) into N partitions of 24
  ├── Assign HP/LP per core:
  │     First APIC-ID per partition → CLOS[0] (HP)
  │     All others                  → CLOS[3] (LP)
  └── Program SST_TF TPMI registers:
        SST_CLOS_CONFIG[0].max   = SST_TF_INFO_2.ratio_0       [HP TRL ~4.4 GHz]
        SST_CLOS_CONFIG[3].max   = SST_TF_INFO_0.lp_clip_ratio_0  [LP ~P1]
        SST_CP_CONTROL.priority_type = 1                        [Ordered Throttle]
        SST_PP_CONTROL.feature_state[1] = 1                     [SST-TF active]
        MSR 0x1AD                = SST_TF_INFO_2.ratio_0        [HP TRL for OS]

OS boot (PV path — Ubuntu)
  └── intel-speed-select discovers topology:
        HP module count, APIC IDs, feature enabled flag
      cpufreq / IA32_HWP_CAPABILITIES: HP = P0max, LP = LP_clip per core
```

### CLOS Architecture — HP/LP Enforcement

```
Per-cycle resolution (PCode RAPL PID, 1ms loop):
  Input: active HP count, CDYN level, SST_TF_INFO_0/2, RAPL PL1 budget

  Normal (no PL1 pressure):
    WP4_HP = SST_TF_INFO_2.RATIO_0  [HP TRL by active HP count bucket]
    WP4_LP = SST_TF_INFO_0.LP_CLIP_RATIO_0

  Ordered Throttle (SST_CP_PRIORITY_TYPE=1, PL1 exceeded):
    Phase A: LP frequency ↓ first     [WP4_LP reduced]
    Phase B: HP maintained at TRL     [while LP > Pn floor]
    Phase C: HP frequency ↓ last      [only after LP at Pn floor]
    → HP is throttled last, not exempt

  Broadcast: WP4_HP + WP4_LP + MASK_HIGH/LOW via PMSB sideband → Acode
```

### Frequency Hierarchy (NWP Values)

| Level | Approx Freq | Who gets it | Condition |
|-------|------------|-------------|-----------|
| P0max / F3 | ~4.4 GHz | HP cores (CLOS[0]) | PCT active, HP TRL bucket |
| P0n (all-core) | ~3.6 GHz | All cores | PCT disabled |
| F2 / LP_CLIP | ~P1 ~2.3 GHz | LP cores (CLOS[3]) | PCT active, always clipped |
| Pn | Floor | All cores | Power-limited Phase C floor |

### HP Core Selection Algorithm

BIOS assigns HP positions by APIC ID order (MADT order: P-cores first, then compute atoms):

```
For partition P in range(N):
    partition_offset = P × (96 / N)          # e.g. 0, 24, 48, 72 for N=4
    HP core = core at APIC-sorted index [partition_offset]   ← CLOS[0]
    LP cores = all others in partition                       ← CLOS[3]

Custom config override (BIOS knob "PCT HP Module Select"):
    User specifies HP module position within each partition
    BIOS programs SST_CLOS_ASSOC directly per user selection
```

---

## Section 3: Validation Strategy

PCT validation requires **three complementary tiers**. Same feature ≠ same validation. Feature overlap across tiers = expected. Validation overlap = false assumption.

### Tier Definitions

| Tier | Environment | Interface | What it validates |
|------|-------------|-----------|------------------|
| PSS | VP (Simics) · HSLE · HSLE XOS | PythonSV → TPMI model | Will PCT work BEFORE tape-out? Firmware flows, RTL behavior, cross-die protocol |
| FV | Post-silicon NWP | PythonSV → namednodes → TPMI direct | Does hardware implement PCT correctly? Silicon + registers + PCode + real power |
| PV | Post-silicon NWP + Ubuntu | `intel-speed-select` → sysfs → TPMI | Can OS correctly use/expose PCT? BIOS + driver + OS tool |

### Why PSS ≠ FV ≠ PV

**PSS vs FV (time axis — pre-silicon vs post-silicon):**
- Firmware bug in PCode TPMI write → PSS catches 6+ months before silicon; FV confirms on real HW
- Silicon TPMI decoder hardware bug → PSS may miss (RTL model may not have same layout bug); FV is the only catcher
- Model gap in VP → PSS passes silently; FV reveals true behavior

**PSS vs PV (interface axis — zero overlap):**
- PSS runs minimal boot — no Linux OS, no `intel-speed-select`, no sysfs, no SST tool
- PV cannot run pre-silicon (requires booted Ubuntu on real silicon)
- There is **zero content overlap** between PSS and PV

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|-------------|----------|-----------|-----------|----|----|
| PCode TPMI write logic wrong | ✅ | ⚠️ | ✅ | ✅ | indirect |
| PrimeCode HPM message to CBB wrong | ✅ | ❌ | ✅ | ✅ | indirect |
| CBB PCode misreads CLOS config | ❌ | ✅ | ✅ | ✅ | indirect |
| Acode applies wrong ratio to HP cores | ❌ | ✅ | ✅ | ✅ | indirect |
| IMH↔CBB HPM protocol bug | ❌ | ❌ | ✅ | ✅ | indirect |
| Silicon TPMI decoder HW bug | ❌ | ❌ | ❌ | ✅ | indirect |
| Real fuse gating PCT wrong | ❌ | ❌ | ❌ | ✅ | indirect |
| intel-speed-select driver bug | ❌ | ❌ | ❌ | ❌ | ✅ |
| SST tool misparse capability | ❌ | ❌ | ❌ | ❌ | ✅ |
| NWP 2-CBB topology in driver | ❌ | ❌ | ❌ | ❌ | ✅ |
| TDP convergence (real power) | ❌ | ❌ | ❌ | ✅ | ✅ |
| BIOS negative validation | ✅ safe | ❌ | ❌ | ❌ risky | ❌ |

### Scenario Coverage Across Tiers

| Test Scenario | PSS | FV | PV | Unique value |
|--------------|-----|----|----|-------------|
| Discovery / TPMI capability check | ✅ | ✅ | ✅ | All 3 required — model / silicon HW / OS driver are independent paths |
| Default HP core selection | ✅ | ✅ | ✅ | 3-layer: RTL model / silicon TPMI / OS sysfs |
| All HP cores in C6, LP still clipped | ✅ | ✅ | — | HW-level; HSLE XOS validates PCode+Acode+HPM pre-silicon |
| Enable / Disable | ✅ | ✅ | ✅ | Model disable / HW register / OS driver enforcement — 3 distinct bug classes |
| Partition count sweep | — | — | ✅ | Driver stress — requires full intel-speed-select; not pre-silicon |
| Turbo frequency check | ✅ | ✅ | — | PSS: PCode TRL table application; FV: real silicon freq/power |
| TDP convergence (RAPL PL1) | — | ✅ | — | FV-unique — requires real silicon power measurement |
| Phase C HP throttle (severe PL1) | — | ✅ | — | FV-unique — LP at floor, HP must also throttle |
| DQ Rules / Fuse (FlexconPM) | ✅ | ✅ | — | PSS: safe fuse override injection; FV: confirms on real fuses |
| BIOS negative validation | ✅ | — | — | PSS-unique — invalid BIOS values tested safely on emulation |

---

## Section 5: Risks & Dependencies

- **PSS model gap — Acode**: VP (Simics) simulates a simplified core; exact Acode frequency derating for HP vs LP is not modeled at RTL precision. PSS catches PCode/PrimeCode firmware bugs; Acode-level HP/LP enforcement must be validated on FV. Mitigation: HSLE XOS provides full-RTL Acode validation pre-silicon.
- **PSS model gap — cross-die HPM**: HSLE cannot model cross-die IMH↔CBB HPM protocol in isolation. Only HSLE XOS (both IMH and CBB RTL) covers this path. Mitigation: HSLE XOS is the mandatory pre-silicon cross-die validation environment for PCT.
- **NWP QDF dependency**: PCT requires `SST_TF_INFO_0.FEATURE_SUPPORTED = 1` on the test QDF. Parts where SST-TF fuses are not programmed will show PCT as unsupported. FV and PV tests must confirm QDF capability before execution.
- **PV driver dependency**: `intel-speed-select` tool and `intel_pstate` driver must be present and active on Ubuntu. `scaling_driver != intel_pstate` produces silent false-pass in PV frequency checks.
- **RAPL MSR deprecation**: MSR 0x610/0x638 are deprecated on NWP (BIOS HSD 14018460453). All RAPL PL1 tests must use TPMI `SOCKET_RAPL_PL1_CONTROL`. Any TC referencing the legacy MSR path will fail silently.
- **GNR vs NWP default**: CAPID4.bit29 auto-enables PCT on GNR but is NOT used on NWP. TCs written for GNR default-enabled path (TC 16030768619) are NWP POR-irrelevant but code-path validated.

---

## Section 6: DFX Considerations

- **No PCT-specific debug registers**: PCT uses standard SST-TF TPMI registers. Debug visibility is through `sv.socket0.nio0.tpmi.sst_*` namednodes in PythonSV.
- **TPMI access paths**: `sv.socket0.nio0.tpmi.sst_clos_config_0` (HP ceiling), `sst_clos_config_3` (LP ceiling), `sst_clos_assoc_*` (per-core HP/LP assignment), `sst_tf_info_0/2` (source fuse values).
- **OS debug path**: `intel-speed-select perf-profile info` + `/sys/bus/cpu/devices/cpuN/cpufreq/cpuinfo_max_freq` per core. Discrepancy between sysfs and TPMI indicates BIOS or `intel_pstate` bug.
- **Power measurement for TDP convergence**: Requires real silicon RAPL power reading (`SOCKET_RAPL_ENERGY_STATUS` TPMI or `rapl_power_unit` + `energy_status` via `powercap`). Not available in PSS/emulation.
- **Phase C HP throttle debug**: Use `IA32_PERF_STATUS` (MSR 0x198) sampled across the throttle ramp. HP frequency drop must not precede LP reaching Pn floor — verify via timestamp-ordered register snapshots.

---

## Section 7: Common Corner Cases

Corner cases that span multiple TCDs under this TPF:

| Corner Case | Affected TCDs | Expected Behavior |
|-------------|--------------|-------------------|
| **LP clip when all HP in C6** | 22022420858 (Functionality), PSS 16030715676 | `CLOS_CONFIG[3].max` is HW-enforced; HP C6 does NOT release LP clip. LP cores still clipped. Critical invariant — verified at both FV and PSS level. |
| **Ordered throttle Phase C — HP throttle** | 22022420858 | When PL1 < (LP_floor × 96 cores), HP must throttle too. TC 22022422117 covers Phase A/B only. Phase C has no TC — coverage gap. |
| **CAPID4.bit29 not used on NWP** | 22022420855 (Enabling), 22022420858 | Unlike GNR, NWP never reads CAPID4.bit29 for PCT enable. BIOS Partition Count knob = 0 is the default-disabled state. TC 16030715684 verifies this. |
| **SST-BF ZBB passively satisfied** | All TCDs | SST-BF and PCT are architecturally mutually exclusive (DQ rule). On NWP, SST-BF is ZBB — mutual exclusion never exercised. DQ validation (TC 22022422118) confirms no interference. |
| **TPMI stale state on PCT disable** | 22022420858, 22022420862 | On runtime disable (`SST_PP_CONTROL.feature_state[1]=0`), `CLOS_ASSOC` entries persist in TPMI but `SST_CP_ENABLE` goes to 0. OS tools must report no HP/LP differentiation. |
| **Max partition count boundary** | 22022420862 | BIOS must reject partition count > `SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS`. TC 16030717718 sweeps valid range only — max+1 rejection is a gap. |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Segment | Scope |
|--------|-------|---------|-------|
| [22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855) | PCT - Enabling & Discovery | FV | TPMI register baseline; BIOS capability discovery; CAPID4.bit29 (GNR) |
| [22022420858](https://hsdes.intel.com/appstore/article-one/#/22022420858) | PCT - Functionality | FV + PSS | HP/LP behavior; C6 interaction; TDP convergence; RAPL ordered throttle |
| [22022420862](https://hsdes.intel.com/appstore/article-one/#/22022420862) | PCT - Ubuntu E2E Functional Test | PV | OS-level: partition config, sweep, disable via BIOS knob + kayak |
| [22022420862](https://hsdes.intel.com/appstore/article-one/#/22022420855) | PCT - Fuse | FV | FlexconPM DQ rules; fuse-gated behavior (TC 22022422118) |

> **Note**: [TCD 22022420862](https://hsdes.intel.com/appstore/article-one/#/22022420862) was renamed from "PCT - Fuse" to "PCT - Ubuntu E2E Functional Test" (2026-07-18). Fuse validation is covered by TC 22022422118 under TCD 22022420858.

### References

- [PCT (Priority Core Turbo) HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [Priority Core Turbo Technology White Paper](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/IC_PCT.html)
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — CLOS config, SST_CP_CONTROL, ordered throttle (§Ordered Throttling)
- [DMR Turbo HAS — PCT section](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html)
- [NWP PM MAS — PCT section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [CBB SST Manager FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/SST_manager/cbb_SST_manager_FAS.html)
- [CCB HSD 14026595435](https://hsdes.intel.com/appstore/article-one/#/14026595435) — NWP 8 HP cores, 4.4 GHz target
- [BIOS HSD 14018460453](https://hsdes.intel.com/appstore/article-one/#/14018460453) — MSR 0x610/0x638 deprecated on NWP
- KB feature ref: KB/pm_features/sst/pct.md
- Sibling TPF: [16030762839 — NWP PM SST](https://hsdes.intel.com/appstore/article-one/#/16030762839)
