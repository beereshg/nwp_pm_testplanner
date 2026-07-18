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

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS | FV | PV | Notes |
|---|---|---|---|---|
| OS / Tool Layer (`intel-speed-select`, `cpufreq`, sysfs) | ❌ | ❌ | ✅ | Requires booted Ubuntu; TCDs: 16031169214, 16030717717/18 |
| PCT Policy Layer (BIOS partition count / `SST_CLOS_ASSOC` programming) | ❌ | ❌ | ✅ | BIOS programs CLOS assignments; all PCT PV TCDs |
| SST-TF Enforcement Layer (PCode WP4 broadcast, ordered throttle) | ✅ | ✅ | ✅ | PSS/FV: register-level; PV: indirectly via `cpuinfo_max_freq` |
| Acode / Microcode Layer (per-core frequency ceiling application) | ✅ | ✅ | ✅ | PSS model; FV functional; PV observes `cpuinfo_max_freq` |
| HW Enforcement Layer (FIVR, PLL, silicon frequency gates, fuse cap) | ✅ | ✅ | ❌ | RTL/model coverage; PV has no direct HW layer observability → §5 G-4 |

> **§3 pointer:** PCT Validation Strategy §3 maps to this table — PSS + FV own Enforcement/Acode/HW layers;
> PV owns OS/Tool + Policy layers; all three tiers share the SST-TF Enforcement layer.

### Agent Source Ownership

*Where to look when a frequency anomaly traces to a specific layer.*

| Layer / Agent | Key Artifact |
|---|---|
| PCT Policy Layer — BIOS (CPL3) | CPUPM FAS; BIOS PCT knob path (`EDKII → Socket Config → Advanced PM Config → PCT Configuration`) |
| SST-TF Enforcement — PCode (CBB) | `sst_manager.cpp`, `trl_manager.cpp` (CBB SST Manager FAS) |
| SST-TF Init — PrimeCode (IMH-P, Phase 5) | `sst_tpmi_general.cpp::sstTfInfoInit()` |
| Acode / Microcode Layer | RTL / Acode — no SW interface; debug via WP4 broadcast values in PCode NLog |

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

### Observability

| Observable | Type | Tool / Command | What it shows |
|---|---|---|---|
| `cpuinfo_max_freq` (per-core sysfs) | PV runtime | `cat /sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_max_freq` | HP vs LP frequency ceiling visible to OS |
| `intel-speed-select perf-profile info` | PV runtime | `intel-speed-select -d perf-profile info` | HP module list, partition count, feature enabled flag |
| `isst` HP count | PV runtime | `isst -d perf-profile info \| grep 'hp-count'` | Expected HP core count per config |
| TPMI `SST_TF_INFO_0/2` | FV / PSS | PythonSV: `sv.socket0.getbypath('imh0.sst_tf_info_0').read()` | Fuse-loaded LP clip / HP TRL ratios |
| TPMI `SST_CLOS_CONFIG[0/3].max` | FV / PSS | PythonSV TPMI read | BIOS-programmed HP/LP frequency ceilings |
| WP4_HP / WP4_LP broadcast value | PSS / FV | RAPL NLog / WP4 trace or PythonSV PMSB | Runtime ordered throttle targets per 1 ms RAPL PID loop |
| BIOS F2 debug serial log | PV | BIOS serial log | CLOS assignment + PCT knob readback at boot |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs affected |
|---|---|---|
| PCT disabled (BIOS knob `0` or fuse `PCT_Module_Mask=0`) | `SST_PP_CONTROL.feature_state[1]=0`; all cores get flat P0n TRL; `cpuinfo_max_freq` uniform across all cores | TCD 16031169217 (Disable), TCD 16031169214 (Discovery) |
| PCT enabled, N=1 partition (BIOS default) | 1 HP module per socket (first APIC-ID 0); 95 LP cores; ordered throttle active | TCD 22022420862 (BIOS Config), TCD 22022420858 (Functionality) |
| PCT enabled, N=1..4 partitions (custom via BIOS HP Module Select knob) | Up to 4 HP cores (one per partition); BIOS overrides APIC-ID default ordering | TCD 22022420862 (custom sweep) |
| SST-BF conflict | SST-BF is ZBB on NWP — mutually exclusive with PCT; if both configured, SST-BF takes precedence over PCT | All PCT TCDs |
| FV (post-silicon, no OS boot) | PythonSV direct TPMI register access; no `intel-speed-select`; no sysfs; ordered throttle validated via WP4 trace | TCD 22022420858 (Functionality) |

---

## Section 3: Validation Strategy

PCT validation requires **three complementary tiers**. Same feature ≠ same validation. Feature overlap across tiers = expected. Validation overlap = false assumption.

> **Layer coverage:** Stack-to-tier mapping is in §2 — Validation-Tier Layer Claim table. That table identifies which tier validates each PCT stack layer. Unclaimed layers (OS/Tool and PCT Policy = PV-only; HW Enforcement = no PV coverage) are captured as accepted gaps in §5 (G-4, G-5).

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
| **PCT × C-states: HP C6 mixed workload** | 22022420858 | HP cores entering C6 under mixed workload should trigger HP bucket ratchet-up (fewer active HP = higher per-core TRL). No TC validates HP bucket transition on partial HP C6. *(Co-Design T1, 2026-07-18; spec: Core C-states HAS, DMR Turbo HAS)* |
| **PCT × RAPL: all limit interactions** | 22022420858 | TC 22022422117 covers Phase A/B only. Full RAPL interaction includes: PL2 burst with PCT, PL4 clamp with PCT, RAPL enable/disable toggle while PCT active. No TC beyond Phase A/B. *(Co-Design T1, 2026-07-18; spec: RAPL HAS, SST HAS Cross Products)* |
| **PCT × Thermal: throttle escalation** | *(no TCD)* | Thermal events (EMTTM, DTS, TCC) interacting with PCT ordered throttle — does thermal override PCT priority ordering? Spec says yes but no TC validates. *(Co-Design T1, 2026-07-18; spec: DMR Turbo HAS: Thermal, SST HAS Cross Products)* |
| **State transition lifecycle** | 16031169297 | Enable → disable → re-enable lifecycle: stale CLOS_ASSOC after disable, re-enable from stale state. Gaps tracked in TCD 16031169297 §6 but no TC authored. *(Co-Design T1, 2026-07-18; spec: SST HAS Dynamic SST-PP, DMR Turbo HAS TPMI Watcher Control)* |
| **Virtualization: VMM HP/LP assignment** | *(no TCD)* | PCT is SoC-wide; all non-HP cores are LP-clipped regardless of VM. VMM should assign HP cores to frequency-sensitive VMs. No TC validates this. *(Co-Design T1, 2026-07-18; spec: PCT HAS Virtualization)* |
| **Hotplug / online-offline core** | *(no TCD)* | Onlining/offlining HP or LP cores at runtime while PCT active may break partition balance or CLOS assignment. No TC. *(Co-Design T1, 2026-07-18; spec: DMR Turbo HAS Hotplug)* |
| **Driver/tool robustness** | 22022420862, 16031169214 | Wrong `intel-speed-select` version, missing capability flag in driver, scaling_driver != intel_pstate — silent false-pass risk. No negative driver TC. *(Co-Design T1, 2026-07-18; spec: SST HAS Discovery/Control, PCT HAS OS/driver interface)* |
| **Topology corners** | 22022420862 | All-HP partition, all-LP partition, single-core partition, max partitions at boundary. TC 16030717718 sweeps but doesn't cover degenerate/extreme topologies. *(Co-Design T1, 2026-07-18; spec: PCT HAS Topology, CPUID/MADT)* |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs (post-reorg, verified 2026-07-18)

| TCD ID | Title | Segment | Scope |
|--------|-------|---------|-------|
| [22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855) | PCT - BIOS Enabling | FV + PSS | BIOS knob visibility, defaults, enable/disable HW state |
| [22022420858](https://hsdes.intel.com/appstore/article-one/#/22022420858) | PCT - Functionality | FV + PSS | Runtime frequency enforcement: HP/LP CLOS, LP clip invariant, ordered throttle |
| [16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) | PCT - TPMI Runtime Control | FV + PSS | Runtime toggle via SST_PP_CONTROL, state transitions |
| [16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) | PCT - DQ Rules & Negative Validation | FV + PSS | FlexconPM DQ compliance, fuse mutexes (SST-BF, FCT) |
| [16031169308](https://hsdes.intel.com/appstore/article-one/#/16031169308) | PCT - Negative / Boundary Validation | FV + PSS | Invalid BIOS configs, invalid TPMI writes, error rejection |
| [22022420862](https://hsdes.intel.com/appstore/article-one/#/22022420862) | PCT - PV BIOS Configuration | PV | Ubuntu E2E: partition config, sweep, HP/LP cpufreq |
| [16031169214](https://hsdes.intel.com/appstore/article-one/#/16031169214) | PCT - PV Discovery | PV | OS-level intel-speed-select discovery, APIC ID reporting |
| [16031169217](https://hsdes.intel.com/appstore/article-one/#/16031169217) | PCT - PV BIOS Disable | PV + PSS | PCT disable produces uniform conventional turbo |

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