# TPF 16030762939 — [NWP PM] PCT (Priority Core Turbo)

| Field | Value |
|-------|-------|
| **TPF ID** | [16030762939](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Title** | [NWP PM] PCT (Priority Core Turbo) |
| **Parent TP** | [16030762839 — [NWP PM] SST (Speed Select Technology)](https://hsdes.intel.com/appstore/article-one/#/16030762839) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-20 |

---

## Section 1: Feature Classification & Introduction

**PCT (Priority Core Turbo)** is a **silicon-heavy feature with firmware orchestration**. Hardware enforces HP/LP TRL differentiation via CLOS logic in Acode; firmware/BIOS/PCode configure and expose the capability. On NWP, PCT targets **8 HP cores** (~4.4 GHz) across 4 partitions of 96 total cores (2 CBBs × 48), with the remaining ~88 LP cores clipped to ~P1 (~2.3 GHz).

**Feature gating:** On NWP, PCT is opt-in via BIOS Partition Count knob (CAPID4.bit29 is NOT used — all NWP parts are PCT-capable). On GNR, CAPID4.bit29=1 auto-enables PCT.

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

### PCT Architecture — Full Stack (Policy built on SST-TF Enforcement)

<!-- raw-html -->
<div style="max-width:680px;font-family:'Segoe UI',Arial,sans-serif;font-size:12px;margin:16px 0;">

  <!-- OS / Tool Layer -->
  <div style="background:#e8f4fd;border:2px solid #2196f3;border-radius:8px 8px 0 0;padding:12px 18px;">
    <div style="font-weight:700;color:#1565c0;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">OS / Tool Layer</div>
    <div style="color:#1a237e;line-height:1.7;font-size:11.5px;">
      <code style="background:#fff;border:1px solid #90caf9;border-radius:3px;padding:1px 5px;">intel-speed-select</code> &nbsp;·&nbsp;
      <code style="background:#fff;border:1px solid #90caf9;border-radius:3px;padding:1px 5px;">cpufreq / cpuinfo_max_freq</code> &nbsp;·&nbsp;
      <code style="background:#fff;border:1px solid #90caf9;border-radius:3px;padding:1px 5px;">isst perf-profile info</code>
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- PCT Policy Layer -->
  <div style="background:#fff3e0;border:2px solid #ff9800;padding:12px 18px;">
    <div style="font-weight:700;color:#e65100;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">PCT Policy Layer &nbsp;<span style="font-weight:400;font-size:10px;color:#bf360c;">(BIOS programs)</span></div>
    <div style="color:#bf360c;line-height:1.8;font-size:11.5px;">
      BIOS Partition Count knob &nbsp;→&nbsp; <code style="background:#fff;border:1px solid #ffcc80;border-radius:3px;padding:1px 5px;">SST_CLOS_ASSOC[core]</code><br>
      HP cores &nbsp;→&nbsp; <strong>CLOS[0]</strong> &nbsp;&nbsp;·&nbsp;&nbsp; LP cores &nbsp;→&nbsp; <strong>CLOS[3]</strong><br>
      <code style="background:#fff;border:1px solid #ffcc80;border-radius:3px;padding:1px 5px;">SST_CLOS_CONFIG[0].max</code> &nbsp;=&nbsp; HP TRL &nbsp;&nbsp;·&nbsp;&nbsp;
      <code style="background:#fff;border:1px solid #ffcc80;border-radius:3px;padding:1px 5px;">SST_CLOS_CONFIG[3].max</code> &nbsp;=&nbsp; LP clip
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- SST-TF Enforcement Layer -->
  <div style="background:#f3e5f5;border:2px solid #9c27b0;padding:12px 18px;">
    <div style="font-weight:700;color:#6a1b9a;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">SST-TF Enforcement Layer &nbsp;<span style="font-weight:400;font-size:10px;color:#4a148c;">(PCode orchestrates)</span></div>
    <div style="color:#4a148c;line-height:1.8;font-size:11.5px;">
      PCode RAPL PID (1ms loop) &nbsp;→&nbsp; WP4_HP / WP4_LP per CDYN &nbsp;→&nbsp; PMSB sideband broadcast<br>
      Ordered throttle (<code style="background:#fff;border:1px solid #ce93d8;border-radius:3px;padding:1px 5px;">SST_CP_PRIORITY_TYPE=1</code>): LP frequency reduced first &nbsp;·&nbsp; HP maintained longer<br>
      Source: <code style="background:#fff;border:1px solid #ce93d8;border-radius:3px;padding:1px 5px;">SST_TF_INFO_0</code> (LP clip) &nbsp;·&nbsp; <code style="background:#fff;border:1px solid #ce93d8;border-radius:3px;padding:1px 5px;">SST_TF_INFO_2</code> (HP TRL per CDYN bucket)
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- Acode / Microcode Layer -->
  <div style="background:#e8f5e9;border:2px solid #4caf50;padding:12px 18px;">
    <div style="font-weight:700;color:#1b5e20;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Acode / Microcode Layer &nbsp;<span style="font-weight:400;font-size:10px;color:#2e7d32;">(per-core application)</span></div>
    <div style="color:#1b5e20;line-height:1.8;font-size:11.5px;">
      Applies CLOS frequency ceiling from WP4 broadcast per core<br>
      HP cores: P0max ceiling &nbsp;≈&nbsp; <strong>4.4 GHz</strong> &nbsp;&nbsp;·&nbsp;&nbsp; LP cores: LP_CLIP ceiling &nbsp;≈&nbsp; <strong>P1 ~2.3 GHz</strong>
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- HW Enforcement Layer -->
  <div style="background:#fce4ec;border:2px solid #f44336;border-radius:0 0 8px 8px;padding:12px 18px;">
    <div style="font-weight:700;color:#b71c1c;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">HW Enforcement Layer &nbsp;<span style="font-weight:400;font-size:10px;color:#c62828;">(silicon gates frequency)</span></div>
    <div style="color:#b71c1c;line-height:1.8;font-size:11.5px;">
      Core FIVR + PLL &nbsp;·&nbsp; CBB compute die &nbsp;·&nbsp; TPMI register decoder (HW)<br>
      Acode derating ratio enforced in silicon &nbsp;·&nbsp; Fuse-gated capability
    </div>
  </div>

  <!-- Key insight -->
  <div style="margin-top:12px;background:#f8f9fa;border-left:4px solid #607d8b;padding:10px 14px;border-radius:0 4px 4px 0;font-size:11px;color:#37474f;line-height:1.6;">
    <strong>Key insight:</strong> PCT is the <em>policy</em> (which cores are HP, which are LP) built on SST-TF <em>enforcement</em> (how frequency ceilings are applied at runtime). A bug in the policy layer (wrong CLOS assignment) produces different failure signatures than a bug in the enforcement layer (wrong WP4 calculation).
  </div>
</div>
<!-- /raw-html -->

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

### WP4 Broadcast Protocol (from CCP HAS / CCP PM MAS)

The WP4 broadcast is a **two-phase multicast** protocol executed by PCode every RAPL PID iteration (1 ms):

```
Phase 1 — Mask write (multicast):
  PCode writes WP4_MASK register for all cores in the target priority group.
  WP4_MASK[i] = 1 → core[i] will accept the subsequent WP4 update.
  WP4_MASK[i] = 0 → core[i] ignores the WP4 write (frequency unchanged).

Phase 2 — WP4 value write + GO command (multicast):
  PCode writes the resolved frequency target:
    HP cores: WP4_HP = MAX(TRL, FACT) per license for current CDYN bucket
    LP cores: WP4_LP = MIN(FACT, TRL) per license for current CDYN bucket
  Only cores with WP4_MASK[i] = 1 latch the new WP4 value.
  Accompanied by GO_INC or GO_DEC command — core/IP does NOT apply WP4
  until the corresponding GO command is received.

Ordering guarantee:
  Mask → WP4 → GO is strictly ordered by PMSB sideband protocol.
  GO_INC: frequency may increase (core will ramp up).
  GO_DEC: frequency must decrease (core will ramp down).
```

**Validation implication:** A race between WP4_MASK write and WP4 value write would cause a core to latch a stale frequency target. The PMSB strict ordering prevents this — but test the boundary: what happens if PCode issues GO before WP4 write completes? (Corner case for TCD 16031169376 — Ordered Throttle Priority.)

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

### Interface & Register Matrix

| Register / MSR | Field | Default | Feature effect | Tier validated |
|---|---|---|---|---|
| `SST_TF_INFO_0` (TPMI, R/O after PrimeCode Phase 5) | `LP_CLIP_RATIO_CDYN_[0..5]` | Fuse-programmed | LP frequency ceiling per CDYN bucket | PSS, FV |
| `SST_TF_INFO_2` (TPMI, R/O after Phase 5) | `TRL_RATIO_[0..5]` | Fuse-programmed | HP TRL per active HP count bucket | PSS, FV |
| `SST_TF_INFO_8` (TPMI, R/O) | `NUM_CORE_0` | Fuse | `max_partitions = NUM_CORE_0 / MAX_LPIDS` (=4 on NWP) | PSS, FV |
| `SST_TF_INFO_10` (TPMI) | `PCT_Module_Mask` | Fuse (DLCP) | PCT feature enable gate | FV, PV |
| `SST_CLOS_CONFIG[0].max` (TPMI, RW by BIOS) | `ratio` | 0 (disabled) | HP frequency ceiling = HP TRL | PSS, FV, PV |
| `SST_CLOS_CONFIG[3].max` (TPMI, RW by BIOS) | `ratio` | 0 (disabled) | LP frequency ceiling = LP_CLIP | PSS, FV, PV |
| `SST_CLOS_ASSOC[core]` (TPMI, RW by BIOS) | `clos_id` | 0 | HP=CLOS[0], LP=CLOS[3] per APIC-ID order | FV, PV |
| `SST_CP_CONTROL` (TPMI, RW by BIOS) | `priority_type` | 0 | 1 = Ordered Throttle (LP reduced first) | PSS, FV |
| `SST_PP_CONTROL` (TPMI, RW by BIOS) | `feature_state[1]` | 0 | 1 = SST-TF / PCT active | PSS, FV, PV |
| MSR `0x1AD` | HP TRL ratio | 0 | OS-visible HP turbo ratio limit written by BIOS | PV |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs affected |
|---|---|---|
| PCT disabled (BIOS knob `0` or fuse `PCT_Module_Mask=0`) | `SST_PP_CONTROL.feature_state[1]=0`; all cores get flat P0n TRL; `cpuinfo_max_freq` uniform across all cores | TCD 16031169217 (Disable), TCD 16031169214 (Discovery) |
| PCT enabled, N=1 partition (BIOS default) | 1 HP module per socket (first APIC-ID 0); 95 LP cores; ordered throttle active | TCD 22022420862 (BIOS Config), TCD 22022420858 (Functionality) |
| PCT enabled, N=1..4 partitions (custom via BIOS HP Module Select knob) | Up to 4 HP cores (one per partition); BIOS overrides APIC-ID default ordering | TCD 22022420862 (custom sweep) |
| SST-BF conflict | SST-BF is ZBB on NWP — mutually exclusive with PCT; if both configured, SST-BF takes precedence over PCT | All PCT TCDs |
| FV (post-silicon, no OS boot) | PythonSV direct TPMI register access; no `intel-speed-select`; no sysfs; ordered throttle validated via WP4 trace | TCD 22022420858 (Functionality) |

### Microarch→Scenario Coverage Matrix

| # | Element (from §2) | Category | Implied WHAT | Realized as TCD | Tier | Status |
|---|---|---|---|---|---|---|
| 1 | SST_TF_INFO_0.LP_CLIP_RATIO fuse load (Phase 5) | Register field (R/O) | LP clip value correctly loaded from fuse at reset | 22022420855 | FV, PSS | ✓ |
| 2 | SST_TF_INFO_2.TRL_RATIO fuse load (Phase 5) | Register field (R/O) | HP TRL value correctly loaded from fuse at reset | 22022420855 | FV, PSS | ✓ |
| 3 | SST_CLOS_CONFIG[0].max = HP TRL | Register field (RW) | BIOS write accepted; HP ceiling = TRL | 22022420855 | FV, PSS | ✓ |
| 4 | SST_CLOS_CONFIG[3].max = LP_CLIP | Register field (RW) | BIOS write accepted; LP ceiling = LP clip | 22022420855 | FV, PSS | ✓ |
| 5 | SST_CLOS_ASSOC[core] HP/LP assignment | Register field (RW) | Correct APIC-ID → CLOS[0/3] mapping | 22022420855, 22022420862 | FV, PV | ✓ |
| 6 | SST_CP_CONTROL.priority_type = 1 (Ordered Throttle) | Register field (RW) | Ordered throttle mode activates; LP throttled first | 16031169376 | FV, PSS | ✓ |
| 7 | SST_PP_CONTROL.feature_state[1] = 1 (enable) | Register field (RW) | PCT feature activation; frequency differentiation observed | 16031169297 | FV, PSS | ✓ |
| 8 | SST_PP_CONTROL.feature_state[1] = 0 (disable) | Register field (RW) | PCT disable → uniform P0n; no HP/LP differentiation | 16031169217 | PSS, PV | ✓ |
| 9 | WP4_MASK multicast → WP4 value → GO command | Cross-die interface | Strict PMSB ordering: mask then value then GO | 16031169376 | FV, PSS | ✓ |
| 10 | WP4_HP = MAX(TRL, FACT) per CDYN bucket | Algorithm | HP frequency target resolved correctly per active HP count | 22022420858 | FV, PSS | ✓ |
| 11 | WP4_LP = MIN(FACT, TRL) per CDYN bucket | Algorithm | LP frequency target correctly capped | 22022420858 | FV, PSS | ✓ |
| 12 | Ordered throttle Phase A: LP ↓ first | FSM state transition | Under PL1 pressure, LP frequency decreases before HP | 16031169376 | FV, PSS | ✓ |
| 13 | Ordered throttle Phase B: HP maintained | FSM state transition | HP frequency stable while LP > Pn floor | 16031169376 | FV, PSS | ✓ |
| 14 | Ordered throttle Phase C: HP ↓ last | FSM state transition | HP throttled only after LP hits Pn floor | 22022420858 | FV | ⚠️ PARTIAL |
| 15 | HP cores C6 → LP clip maintained | Cross-product (C-state) | LP_CLIP ratio unchanged when all HP idle | 16031169309 | FV, PSS | ✓ |
| 16 | HP bucket ratchet-up on partial HP C6 | Counter/algorithm | Fewer active HP → higher per-core TRL | 16031169309 | FV, PSS | ⚠️ PARTIAL |
| 17 | PCT_Module_Mask fuse gate (DLCP) | Fuse gate | PCT disabled when fuse = 0; enabled when = 1 | 16031169298 | FV | ✓ |
| 18 | SST-BF mutual exclusion (DQ rule) | Fuse gate | SST-BF ZBB takes precedence; PCT inactive if both set | 16031169298 | FV, PSS | ✓ |
| 19 | BIOS Partition Count knob (N=1..4) | BIOS knob | Valid range accepted; topology divided correctly | 22022420862 | PV | ✓ |
| 20 | BIOS Partition Count > max rejection | BIOS knob (boundary) | Invalid partition count rejected by BIOS | 16031169308 | FV, PSS | ✓ |
| 21 | Invalid SST_CLOS_CONFIG write (out-of-range ratio) | Error condition | Write rejected or clamped; no HW damage | 16031169308 | FV, PSS | ✓ |
| 22 | SST_CP_STATUS.EXCURSION_TO_MIN | Error condition | Excursion bit set when LP at floor and HP still throttled | 16031169310 | FV, PSS | ✓ |
| 23 | PCT × RAPL PL1 interaction (full spectrum) | Cross-product (RAPL) | PL1/PL2/PL4 all interact with ordered throttle correctly | 16031169419 | FV, PSS | ✓ |
| 24 | PCT × thermal throttle escalation | Cross-product (thermal) | Thermal overrides PCT priority ordering | 16031169376 | FV, PSS | ✓ |
| 25 | Enable → disable → re-enable lifecycle (stale CLOS) | FSM state transition | Stale CLOS_ASSOC after disable; re-enable from stale state | 16031169297 | FV, PSS | ⚠️ PARTIAL |
| 26 | `intel-speed-select` topology discovery | OS interface | OS tool discovers correct HP count, partition count, APIC IDs | 16031169214 | PV | ✓ |
| 27 | `cpuinfo_max_freq` per-core sysfs | OS interface | HP cores show P0max; LP cores show LP_CLIP in sysfs | 22022420862 | PV | ✓ |
| 28 | MSR 0x1AD HP TRL visibility | Register field (RW) | OS reads correct HP TRL from legacy MSR | 16031169214 | PV | ✓ |
| 29 | VMM HP/LP core assignment across VMs | Cross-product (virt) | SoC-wide PCT affects all VMs; VMM HP assignment correct | GAP | — | ⚠️ GAP |
| 30 | Core hotplug while PCT active | Cross-product (topology) | Online/offline HP/LP core; partition rebalancing | GAP | — | ⚠️ GAP |
| 31 | GO_INC/GO_DEC race (WP4 write before GO) | Cross-die interface (error) | Stale frequency target not latched; ordering enforced | GAP | — | ⚠️ GAP |

**Status summary:** 28/31 elements covered (✓ or PARTIAL); 3 gaps (G-14 VMM, hotplug, WP4 race — see §5).

---

## Section 3: Validation Strategy

PCT validation requires **three complementary tiers**. Same feature ≠ same validation. Feature overlap across tiers = expected. Validation overlap = false assumption.

> **Layer coverage:** The Microarch→Scenario Coverage Matrix in §2 maps each architectural element to its covering TCD(s) and tier. Unclaimed layers (OS/Tool and PCT Policy = PV-only; HW Enforcement = no PV coverage) are captured as accepted gaps in §5 (G-4, G-5).

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

## Section 4: Risks & Dependencies

### Active Risks

- **PSS model gap — Acode**: VP (Simics) simulates a simplified core; exact Acode frequency derating for HP vs LP is not modeled at RTL precision. PSS catches PCode/PrimeCode firmware bugs; Acode-level HP/LP enforcement must be validated on FV. Mitigation: HSLE XOS provides full-RTL Acode validation pre-silicon.
- **PSS model gap — cross-die HPM**: HSLE cannot model cross-die IMH↔CBB HPM protocol in isolation. Only HSLE XOS (both IMH and CBB RTL) covers this path. HSLE XOS is a **mandatory pre-silicon environment** for PCT — schedule risk if availability is constrained. Mitigation: plan HSLE XOS runs early in the PSS schedule.
- **NWP QDF dependency**: PCT requires `SST_TF_INFO_0.FEATURE_SUPPORTED = 1` on the test QDF. Parts where SST-TF fuses are not programmed will show PCT as unsupported. FV and PV tests must confirm QDF capability before execution.
- **PV driver dependency**: `intel-speed-select` tool and `intel_pstate` driver must be present and active on Ubuntu. `scaling_driver != intel_pstate` produces silent false-pass in PV frequency checks. Mitigation: add precondition guard to kayak test setup.
- **RAPL MSR deprecation**: MSR 0x610/0x638 are deprecated on NWP (BIOS HSD 14018460453). All RAPL PL1 tests must use TPMI `SOCKET_RAPL_PL1_CONTROL`. Any TC referencing the legacy MSR path will fail silently.
- **GNR vs NWP default**: CAPID4.bit29 auto-enables PCT on GNR but is NOT used on NWP. TCs written for GNR default-enabled path (TC 16030768619) are NWP POR-irrelevant but code-path validated.

### Accepted Coverage Limitations (by design — no new TCs required)

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G4** | Silicon TPMI decoder HW bug | FV only | Inherent silicon-level HW bug; not detectable in RTL model by design. FV is the only and sufficient catcher. |
| **G5** | Real fuse gating PCT wrong | FV only | Production fuses cannot be safely overridden in PSS or emulated in PV. FV on QDF-programmed parts is the correct and only detection path. |
| **G6** | `intel-speed-select` driver bug | PV only | Driver bugs require a booted Linux OS on real silicon; no PSS/FV equivalent. PV is the correct and only detection path. |
| **G12** | Cross-die IMH↔CBB HPM protocol | HSLE XOS only (PSS) | No lighter-weight pre-silicon alternative exists. HSLE XOS is mandatory and accepted as the single pre-silicon path for this class. |
| **G13** | Acode HP/LP frequency derating in VP | HSLE / HSLE XOS / FV only | VP core model is simplified by design; Acode behavior not modeled at RTL precision. VP passes silently on this class — accepted model gap with HSLE XOS as mitigation. |
| **G14** | PCT × FlexRatio / overclocking interaction | none | Low risk (L). FlexRatio / overclocking is not a server PCT use case on NWP. No customer scenario requires validation. *(Co-Design T1, 2026-07-18; spec: DMR Turbo HAS Cross Products)* |

### Co-Design T1 Gap Findings — New TCD Candidates (2026-07-18)

**Source:** Co-Design T1 coverage gap audit against PCT HAS, DMR Turbo HAS, Intel SST HAS.

| Candidate TCD | WHAT | Risk | Spec ref | Status |
|---------------|------|------|----------|--------|
| PCT State Transition Lifecycle | Enable→disable→re-enable with stale CLOS_ASSOC validation | H | SST HAS: Dynamic SST-PP; DMR Turbo HAS: TPMI Watcher Control | ⏳ Evaluate — partial coverage in TCD 16031169297 (stale state gaps tracked there) |
| PCT Cross-Product Interactions | PCT × RAPL (beyond Phase A/B), PCT × C-states, PCT × thermal escalation | H | SST HAS: Cross Products; RAPL HAS; Core C-states HAS; DMR Turbo HAS: Thermal | ⏳ Evaluate — some RAPL interaction in TCD 22022420858, but cross-product breadth needs dedicated TCD |
| PCT Virtualization & VMM Assignment | VMM HP/LP core assignment across VMs; SoC-wide PCT effect on VM frequency | H | PCT HAS: Virtualization; DMR Turbo HAS: BIOS/OS/VMM | ⏳ Evaluate — zero coverage today; requires VMM test environment |
| PCT Hotplug & Dynamic Topology | Core online/offline while PCT active; partition rebalancing | M | DMR Turbo HAS: Hotplug; GNR_SOC_PM_HAS | ⏳ Evaluate — depends on NWP hotplug POR status |
| PCT Error Injection & Recovery | WHEA/EINJ, parity, PCIe errors during PCT active state; recovery paths | M | DMR RAS HAS: Error Injection; PCT HAS: Error Handling; SST HAS: Error Handling | ⏳ Evaluate — RAS team may own this scope |

---

## Section 5: DFX Considerations

- **No PCT-specific debug registers**: PCT uses standard SST-TF TPMI registers. Debug visibility is through `sv.socket0.nio0.tpmi.sst_*` namednodes in PythonSV.
- **TPMI access paths**: `sv.socket0.nio0.tpmi.sst_clos_config_0` (HP ceiling), `sst_clos_config_3` (LP ceiling), `sst_clos_assoc_*` (per-core HP/LP assignment), `sst_tf_info_0/2` (source fuse values).
- **OS debug path**: `intel-speed-select perf-profile info` + `/sys/bus/cpu/devices/cpuN/cpufreq/cpuinfo_max_freq` per core. Discrepancy between sysfs and TPMI indicates BIOS or `intel_pstate` bug.
- **Power measurement for TDP convergence**: Requires real silicon RAPL power reading (`SOCKET_RAPL_ENERGY_STATUS` TPMI or `rapl_power_unit` + `energy_status` via `powercap`). Not available in PSS/emulation.
- **Phase C HP throttle debug**: Use `IA32_PERF_STATUS` (MSR 0x198) sampled across the throttle ramp. HP frequency drop must not precede LP reaching Pn floor — verify via timestamp-ordered register snapshots.

---

## Section 6: References

### Child TCDs (verified 2026-07-20)

| TCD ID | Title | Segment | Scope |
|--------|-------|---------|-------|
| [22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855) | PCT-CONTRACT-001 - BIOS CLOS Programming | FV + PSS | BIOS knob visibility, defaults, enable/disable HW state |
| [22022420858](https://hsdes.intel.com/appstore/article-one/#/22022420858) | PCT-OBS-001 - HP/LP Frequency Enforcement | FV + PSS | Runtime frequency enforcement: HP/LP CLOS, LP clip invariant, ordered throttle |
| [16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) | PCT-CONTRACT-002 - Runtime Toggle | FV + PSS | Runtime toggle via SST_PP_CONTROL, state transitions |
| [16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) | PCT-SCENARIO-004 - HP Core DQ Promotion | FV + PSS | FlexconPM DQ compliance, fuse mutexes (SST-BF, FCT) |
| [16031169308](https://hsdes.intel.com/appstore/article-one/#/16031169308) | PCT-CONTRACT-003 - Invalid Configuration Rejection | FV + PSS | Invalid BIOS configs, invalid TPMI writes, error rejection |
| [16031169309](https://hsdes.intel.com/appstore/article-one/#/16031169309) | PCT-SCENARIO-001 - LP Clip Holds During HP Idle | FV + PSS | HP C6 mixed workload: LP clip maintained when all HP idle |
| [16031169310](https://hsdes.intel.com/appstore/article-one/#/16031169310) | PCT-CONTRACT-004 - Error Status and CLOS Recovery | FV + PSS | Error injection, EXCURSION_TO_MIN, SST-CP error status |
| [16031169376](https://hsdes.intel.com/appstore/article-one/#/16031169376) | PCT-SCENARIO-003 - Ordered Throttle Priority | FV + PSS | Under thermal throttle, LP frequency-reduced before HP |
| [16031169419](https://hsdes.intel.com/appstore/article-one/#/16031169419) | PCT-SOAK-001 - Multi-Feature CLOS Integrity | FV + PSS | Cross-product: simultaneous RAPL PL1, C-state, thermal |
| [22022420862](https://hsdes.intel.com/appstore/article-one/#/22022420862) | PCT-CONTRACT-006 - Partition Sweep (PV) | PV | Ubuntu E2E: partition config, sweep, HP/LP cpufreq |
| [16031169214](https://hsdes.intel.com/appstore/article-one/#/16031169214) | PCT-ENUM-001 - Enumeration Consistency | PV | OS-level intel-speed-select discovery, APIC ID reporting |
| [16031169217](https://hsdes.intel.com/appstore/article-one/#/16031169217) | PCT-CONTRACT-005 - Disable State | PV + PSS | PCT disable produces uniform conventional turbo |

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
> **DLCP structural action — COMPLETED (2026-07-18):** TCD 16030982802 (DLCP) moved to dedicated DLCP TPF [16031169314](https://hsdes.intel.com/appstore/article-one/#/16031169314) under TP 16030762839. TPF 16031169315 is an empty duplicate created by accident — set to `rejected` status to close it. TCD 16030982802 is **no longer a child of this TPF**.